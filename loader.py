#!/usr/bin/env python3
"""Loader.

Deterministic ingestion script — the missing link between the Instrumentation
Agent's `ddl.sql` and a queryable ClickHouse table. Not an LLM agent: data
inserts are high-stakes, so nothing here is guessed by a model.

For a given spec, this script:

1. Executes `ddl.sql` as-is (idempotent, matches the Instrumentation Agent's
   own contract for that file).
2. Reads `events.ndjson`, buckets each row by its own `event` field (which
   already equals its target table name — the one-table-per-event convention
   `instrumentation_notes.md` documents), and flattens one level of nested
   objects (`payment.amount` -> `payment_amount`) to match `ddl.sql`'s column
   naming.
3. For any column whose DDL type is exactly `UUID`, auto-hyphenates a raw
   32-char hex id into the 36-char form ClickHouse's UUID type requires --
   this is a generic type-shape fix (every UUID column needs this to insert
   at all), independent of anything documented in known_issues.md.
4. For any known_issues.md entry cited in this spec's `justification.md`
   "Risks / caveats to carry forward" section that has a loader-actionable
   fix block (see context/SCHEMA.md's "Loader-actionable fix blocks" rule),
   applies its `-- normalize:` expression -- executed in ClickHouse itself
   via arrayMap, never reimplemented in Python -- to any table with a
   matching column, then runs its `-- verify:` query after load.
5. Writes `load_report.md` into the output directory: rows loaded per table,
   which normalizations fired, verification query results and verdicts.

A 0% (or any other) verification result is a *finding*, not a failure -- it
is recorded and the script still exits 0. Only a technical failure (DB
unreachable, insert error, malformed DDL) is a non-zero exit.

Usage:
    python loader.py <spec_dir> [--out-dir DIR] [--context-dir DIR]

<spec_dir> must contain events.ndjson (e.g. ps/Atlys/specs/01_express_checkout).
<out_dir> must contain ddl.sql and justification.md (default: out/<spec_dir name>).
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parent
CONTEXT_DIR = REPO_ROOT / "context"

load_dotenv(REPO_ROOT / ".env")

HEX32_RE = re.compile(r"^[0-9a-f]{32}$")


# ---------------------------------------------------------------------------
# ddl.sql parsing -- table/column/type extraction only, not a SQL parser.
# ---------------------------------------------------------------------------


def split_top_level(s, sep=","):
    """Split on `sep` at paren-depth 0, e.g. so `LowCardinality(Nullable(String))`
    or `Decimal(18,2)` don't get split on their internal commas."""
    parts, depth, current = [], 0, []
    for ch in s:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        if ch == sep and depth == 0:
            parts.append("".join(current))
            current = []
        else:
            current.append(ch)
    parts.append("".join(current))
    return parts


def parse_ddl_tables(ddl_text):
    """Return {table_name: [(column_name, column_type), ...]} for every
    CREATE TABLE in ddl_text. ALTER TABLE / MATERIALIZED VIEW statements are
    intentionally out of scope -- populating new columns on existing rows is
    a mutation, not an insert-only load, and deserves separate handling."""
    tables = {}
    for m in re.finditer(
        r"CREATE TABLE IF NOT EXISTS clickathon\.(\w+)\s*\((.*?)\)\s*ENGINE",
        ddl_text,
        re.S,
    ):
        table, body = m.group(1), m.group(2)
        body = re.sub(r"--[^\n]*", "", body)
        columns = []
        for segment in split_top_level(body):
            segment = segment.strip()
            if not segment:
                continue
            parts = segment.split(None, 1)
            if len(parts) != 2:
                continue
            name, col_type = parts[0], parts[1].strip()
            columns.append((name, col_type))
        tables[table] = columns
    return tables


def split_ddl_statements(ddl_text):
    """Split into individual statements. Comments are stripped line-by-line
    BEFORE splitting on ';' -- splitting first is unsafe because comment
    prose can itself contain a literal ';' (e.g. "already cheap; see
    justification.md"), which would cut a comment line in half and leave a
    `--`-less fragment behind that reads as (invalid) SQL instead of being
    recognized as a comment to discard."""
    comment_free = "\n".join(re.sub(r"--.*$", "", line) for line in ddl_text.splitlines())
    return [s.strip() for s in comment_free.split(";") if s.strip()]


# ---------------------------------------------------------------------------
# events.ndjson -- event-name-is-table-name, one level of dict flattening.
# ---------------------------------------------------------------------------


def flatten(row):
    flat = {}
    for k, v in row.items():
        if isinstance(v, dict):
            for sk, sv in v.items():
                flat[f"{k}_{sk}"] = sv
        else:
            flat[k] = v
    return flat


def bucket_events(events_path):
    buckets = {}
    with open(events_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            table = row.get("event")
            if not table:
                continue
            buckets.setdefault(table, []).append(flatten(row))
    return buckets


# ---------------------------------------------------------------------------
# justification.md -- which known_issues.md ids apply to this spec.
# ---------------------------------------------------------------------------


def parse_cited_ids(justification_text):
    m = re.search(
        r"## Risks / caveats to carry forward\n(.*?)(?:\n## |\Z)",
        justification_text,
        re.S,
    )
    if not m:
        return []
    return re.findall(r"^- \*\*([DK]\d+)\b", m.group(1), re.M)


# ---------------------------------------------------------------------------
# known_issues.md -- loader-actionable fix blocks, per context/SCHEMA.md's
# "Loader-actionable fix blocks" rule: `-- normalize: raw_id -> <expr> AS
# <column>` and `-- verify: <query with <new_table> placeholder>`.
# ---------------------------------------------------------------------------


def parse_fix_fence(fence):
    lines = fence.splitlines()
    entry = {}
    i, n = 0, len(lines)
    while i < n:
        line = lines[i]
        if line.startswith("-- normalize:"):
            collected = [line.split("-- normalize:", 1)[1].strip()]
            i += 1
            while i < n and lines[i].strip().startswith("--"):
                collected.append(lines[i].strip()[2:].strip())
                i += 1
            expr_text = " ".join(p for p in collected if p)
            m = re.match(r"raw_id\s*->\s*(.*)\s+AS\s+(\w+)\s*$", expr_text)
            if m:
                entry["normalize"] = {"expr": m.group(1).strip(), "column": m.group(2)}
            continue
        if line.startswith("-- verify:"):
            i += 1
            verify_lines = []
            while i < n and lines[i].strip():
                verify_lines.append(lines[i])
                i += 1
            if verify_lines:
                entry["verify"] = "\n".join(verify_lines).strip()
            continue
        i += 1
    return entry


def parse_known_issues(known_issues_text):
    entries = {}
    for section in re.split(r"\n(?=## )", known_issues_text):
        hm = re.match(r"## ([DK]\d+)\b", section)
        if not hm:
            continue
        for fence in re.findall(r"```sql\n(.*?)```", section, re.S):
            fix = parse_fix_fence(fence)
            if fix:
                entries[hm.group(1)] = fix
    return entries


# ---------------------------------------------------------------------------
# Value coercion.
# ---------------------------------------------------------------------------


def hex32_to_uuid(value):
    if isinstance(value, str) and HEX32_RE.match(value):
        return f"{value[0:8]}-{value[8:12]}-{value[12:16]}-{value[16:20]}-{value[20:32]}"
    return value


def coerce_datetime(value):
    if not isinstance(value, str):
        return value
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return datetime.fromisoformat(value.split(".")[0])


def apply_uuid_shape_fix(columns, rows):
    """Generic, type-driven: any column declared exactly `UUID` gets its raw
    32-char hex value hyphenated. Not tied to known_issues.md -- a `UUID`
    column simply can't insert without this, regardless of spec."""
    uuid_cols = [name for name, col_type in columns if col_type.strip() == "UUID"]
    datetime_cols = [name for name, col_type in columns if col_type.strip() == "DateTime"]
    if not uuid_cols and not datetime_cols:
        return rows
    fixed = []
    for row in rows:
        row = dict(row)
        for col in uuid_cols:
            if col in row:
                row[col] = hex32_to_uuid(row[col])
        for col in datetime_cols:
            if col in row:
                row[col] = coerce_datetime(row[col])
        fixed.append(row)
    return fixed


def apply_known_issue_normalizer(client, expr, raw_values):
    """Batch-evaluate a known_issues.md `-- normalize:` expression via
    ClickHouse's own SQL engine (arrayMap) -- never reimplemented in Python,
    per context/SCHEMA.md's loader-actionable fix block rule."""
    idx_values = [(i, v) for i, v in enumerate(raw_values) if v is not None]
    if not idx_values:
        return raw_values
    indices, values = zip(*idx_values)
    result = client.query(
        f"SELECT arrayMap(raw_id -> {expr}, {{raw_ids:Array(String)}}) AS out",
        parameters={"raw_ids": list(values)},
    )
    normalized = result.result_rows[0][0]
    out = list(raw_values)
    for i, nv in zip(indices, normalized):
        out[i] = nv
    return out


# ---------------------------------------------------------------------------
# Verdict thresholds -- context/known_issues.md D2's own table (>90% proceed,
# 1-90% proceed with caveat, 0% stop). Applied to any loader-run verify query
# that returns a single `overlap_pct`-style percentage.
# ---------------------------------------------------------------------------


def verdict_for(overlap_pct):
    if overlap_pct is None:
        return "unknown"
    if overlap_pct > 90:
        return "proceed"
    if overlap_pct > 0:
        return "proceed (state coverage in every insight)"
    return "STOP -- report as finding, analyse table standalone only"


# ---------------------------------------------------------------------------
# Main pipeline.
# ---------------------------------------------------------------------------


def get_client():
    import clickhouse_connect

    host = os.environ.get("CLICKHOUSE_HOST")
    if not host:
        raise RuntimeError(
            "CLICKHOUSE_HOST not set -- add CLICKHOUSE_HOST/PORT/USER/PASSWORD/"
            "DATABASE to .env (see .env.example)"
        )
    return clickhouse_connect.get_client(
        host=host,
        port=int(os.environ.get("CLICKHOUSE_PORT", "8443")),
        username=os.environ.get("CLICKHOUSE_USER", "default"),
        password=os.environ.get("CLICKHOUSE_PASSWORD", ""),
        database=os.environ.get("CLICKHOUSE_DATABASE", "clickathon"),
        secure=os.environ.get("CLICKHOUSE_SECURE", "true").lower() != "false",
    )


def run(spec_dir: Path, out_dir: Path, context_dir: Path) -> dict:
    events_path = spec_dir / "events.ndjson"
    ddl_path = out_dir / "ddl.sql"
    justification_path = out_dir / "justification.md"
    known_issues_path = context_dir / "known_issues.md"

    for p in (events_path, ddl_path, justification_path, known_issues_path):
        if not p.exists():
            raise FileNotFoundError(str(p))

    ddl_text = ddl_path.read_text(encoding="utf-8")
    justification_text = justification_path.read_text(encoding="utf-8")
    known_issues_text = known_issues_path.read_text(encoding="utf-8")

    tables = parse_ddl_tables(ddl_text)
    real_ids = set(re.findall(r"^## ([DK]\d+)\b", known_issues_text, re.M))
    cited_ids = [i for i in parse_cited_ids(justification_text) if i in real_ids]
    fix_blocks = parse_known_issues(known_issues_text)
    applicable_fixes = {i: fix_blocks[i] for i in cited_ids if i in fix_blocks}
    skipped_fixes = [i for i in cited_ids if i not in fix_blocks]

    buckets = bucket_events(events_path)

    client = get_client()
    for stmt in split_ddl_statements(ddl_text):
        client.command(stmt)

    report = {
        "tables": {},
        "cited_ids": cited_ids,
        "skipped_fixes": skipped_fixes,
    }

    for table, columns in tables.items():
        rows = buckets.get(table, [])
        col_names = [c[0] for c in columns]
        table_report = {"rows_loaded": 0, "normalized": [], "verified": []}

        if not rows:
            report["tables"][table] = table_report
            continue

        rows = apply_uuid_shape_fix(columns, rows)

        for issue_id, fix in applicable_fixes.items():
            norm = fix.get("normalize")
            if not norm or norm["column"] not in col_names:
                continue
            raw_values = [r.get(norm["column"]) for r in rows]
            normalized_values = apply_known_issue_normalizer(client, norm["expr"], raw_values)
            for row, nv in zip(rows, normalized_values):
                row[norm["column"]] = nv
            table_report["normalized"].append({"issue": issue_id, "column": norm["column"]})

        insert_rows = [[row.get(name) for name in col_names] for row in rows]
        client.insert(f"clickathon.{table}", insert_rows, column_names=col_names)
        table_report["rows_loaded"] = len(insert_rows)

        for issue_id, fix in applicable_fixes.items():
            verify = fix.get("verify")
            norm = fix.get("normalize")
            if not verify or not norm or norm["column"] not in col_names:
                continue
            # known_issues.md's template already writes "clickathon." before
            # the placeholder (e.g. "FROM clickathon.<new_table>") -- only
            # the bare table name is substituted in.
            verify_sql = verify.replace("<new_table>", table)
            result = client.query(verify_sql)
            pct = None
            if result.result_rows and result.result_rows[0]:
                pct = float(result.result_rows[0][0])
            table_report["verified"].append(
                {"issue": issue_id, "column": norm["column"], "overlap_pct": pct, "verdict": verdict_for(pct)}
            )

        report["tables"][table] = table_report

    return report


def render_report(spec_name: str, report: dict) -> str:
    lines = [f"# Load report — {spec_name}", ""]
    if report["cited_ids"]:
        lines.append(f"Cited known_issues.md ids: {', '.join(report['cited_ids'])}")
    if report["skipped_fixes"]:
        lines.append(
            f"Cited but not loader-actionable (no fix block): {', '.join(report['skipped_fixes'])}"
        )
    lines.append("")
    for table, t in report["tables"].items():
        lines.append(f"## {table}")
        lines.append(f"- rows loaded: {t['rows_loaded']}")
        for n in t["normalized"]:
            lines.append(f"- normalized `{n['column']}` per {n['issue']}")
        for v in t["verified"]:
            pct = "n/a" if v["overlap_pct"] is None else f"{v['overlap_pct']}%"
            lines.append(f"- {v['issue']} verify on `{v['column']}`: overlap_pct = {pct} -> {v['verdict']}")
        lines.append("")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Loader: create/load a spec's tables into ClickHouse, "
        "applying any known_issues.md-cited normalizations and verification checks"
    )
    parser.add_argument("spec_dir", type=Path, help="folder containing events.ndjson")
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=None,
        help="Instrumentation Agent output dir containing ddl.sql and "
        "justification.md (default: out/<spec_dir name>)",
    )
    parser.add_argument(
        "--context-dir",
        type=Path,
        default=None,
        help="context wiki root, for known_issues.md (default: context/)",
    )
    args = parser.parse_args()

    spec_dir = args.spec_dir.resolve()
    out_dir = (args.out_dir or REPO_ROOT / "out" / spec_dir.name).resolve()
    context_dir = (args.context_dir or CONTEXT_DIR).resolve()

    try:
        report = run(spec_dir, out_dir, context_dir)
    except Exception as e:
        print(f"error: loader failed: {e}", file=sys.stderr)
        return 1

    report_text = render_report(out_dir.name, report)
    (out_dir / "load_report.md").write_text(report_text, encoding="utf-8")
    print(report_text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
