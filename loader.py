#!/usr/bin/env python3
"""Loader.

Deterministic ingestion script — the missing link between the Instrumentation
Agent's `ddl.sql` and a queryable ClickHouse table. Not an LLM agent: data
inserts are high-stakes, so nothing here is guessed by a model.

For a given spec, this script:

1. Executes `ddl.sql` as-is, in file order (idempotent, matches the
   Instrumentation Agent's own contract for that file): `CREATE TABLE`,
   `ALTER TABLE ... ADD COLUMN`, and `CREATE MATERIALIZED VIEW` all run
   through the same statement loop before any data is touched, so an MV
   defined in this file sees every row this run is about to insert.
2. Reads `events.ndjson`, buckets each row by its own `event` field (which
   already equals its target table name — the one-table-per-event convention
   `instrumentation_notes.md` documents), and flattens one level of nested
   objects (`payment.amount` -> `payment_amount`) to match `ddl.sql`'s column
   naming.
3. Loads every table that has a bucket of rows, whether this spec's `ddl.sql`
   `CREATE`d it fresh or only `ALTER`d it -- column names/types are read back
   from the live schema (`system.columns`) after DDL runs, so a table altered
   in this spec (not created here) still gets its full, current column set
   instead of being silently skipped.
4. For any column whose live type is exactly `UUID`, auto-hyphenates a raw
   32-char hex id into the 36-char form ClickHouse's UUID type requires --
   this is a generic type-shape fix (every UUID column needs this to insert
   at all), independent of anything documented in known_issues.md.
5. For any known_issues.md entry cited in this spec's `justification.md`
   "Risks / caveats to carry forward" section that has a loader-actionable
   fix block (see context/SCHEMA.md's "Loader-actionable fix blocks" rule),
   applies its `-- normalize:` expression -- executed in ClickHouse itself
   via arrayMap, never reimplemented in Python -- to any table with a
   matching column, then runs its `-- verify:` query after load.
6. For any `CREATE MATERIALIZED VIEW ... TO <target> AS SELECT ... FROM
   <source>` in `ddl.sql` whose `<source>` table was NOT created fresh by
   this same spec (i.e. it already held rows from an earlier spec's load),
   backfills `<target>` from `<source>`'s pre-existing rows before this
   run's own inserts happen -- MVs are incremental-only in ClickHouse and
   never backfill historical data on their own (see
   `.skills/clickhouse-best-practices/rules/query-mv-incremental.md`).
7. Writes `load_report.md` into the output directory: rows loaded per table
   (and whether each was created or altered), which normalizations fired,
   verification query results and verdicts, and any MV backfills performed.

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
    CREATE TABLE in ddl_text. Used to know which tables this spec created
    fresh (as opposed to only ALTERed) -- see parse_ddl_altered_tables and
    parse_ddl_materialized_views for the other two DDL kinds. Actual insert
    column lists are read back from the live schema after DDL runs (see
    get_live_columns), not from this parse, so an ALTERed table's new
    columns are always included."""
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


def parse_ddl_altered_tables(ddl_text):
    """Return the set of table names targeted by `ALTER TABLE
    clickathon.<table> ADD COLUMN ...` in ddl_text -- tables this spec
    extends rather than creates."""
    comment_free = "\n".join(re.sub(r"--.*$", "", line) for line in ddl_text.splitlines())
    return set(
        re.findall(
            r"ALTER TABLE clickathon\.(\w+)\s+ADD COLUMN",
            comment_free,
            re.I,
        )
    )


def parse_ddl_materialized_views(ddl_text):
    """Return [{'mv': name, 'target': table, 'source': table_or_None,
    'select': select_sql}, ...] for every `CREATE MATERIALIZED VIEW ...
    TO clickathon.<target> AS SELECT ... FROM clickathon.<source> ...` in
    ddl_text. `source` is None if the SELECT's FROM can't be identified
    (e.g. a join) -- callers should skip backfill rather than guess."""
    comment_free = "\n".join(re.sub(r"--.*$", "", line) for line in ddl_text.splitlines())
    views = []
    for m in re.finditer(
        r"CREATE MATERIALIZED VIEW(?:\s+IF NOT EXISTS)?\s+clickathon\.(\w+)\s+TO\s+clickathon\.(\w+)\s+AS\s+(SELECT.*?);",
        comment_free,
        re.S | re.I,
    ):
        mv_name, target, select_sql = m.group(1), m.group(2), m.group(3).strip()
        src_m = re.search(r"FROM\s+clickathon\.(\w+)", select_sql, re.I)
        source = src_m.group(1) if src_m else None
        views.append({"mv": mv_name, "target": target, "source": source, "select": select_sql})
    return views


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


def get_live_columns(client, table):
    """Read a table's current column list/order/types straight from
    ClickHouse (`system.columns`), post-DDL. Authoritative for both a table
    CREATEd by this spec and one only ALTERed by it -- unlike parse_ddl_tables
    (which only sees this spec's own CREATE TABLE bodies), this always
    reflects the table's real, current shape."""
    result = client.query(
        "SELECT name, type FROM system.columns "
        "WHERE database = 'clickathon' AND table = {table:String} "
        "ORDER BY position",
        parameters={"table": table},
    )
    return [(row[0], row[1]) for row in result.result_rows]


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
    altered_tables = parse_ddl_altered_tables(ddl_text)
    mv_defs = parse_ddl_materialized_views(ddl_text)
    real_ids = set(re.findall(r"^## ([DK]\d+)\b", known_issues_text, re.M))
    cited_ids = [i for i in parse_cited_ids(justification_text) if i in real_ids]
    fix_blocks = parse_known_issues(known_issues_text)
    applicable_fixes = {i: fix_blocks[i] for i in cited_ids if i in fix_blocks}
    skipped_fixes = [i for i in cited_ids if i not in fix_blocks]

    buckets = bucket_events(events_path)
    # An event has a load target only if this spec CREATEd a table of that
    # name, or ALTERed an existing one of that name. Anything else is an
    # event the Instrumentation Agent folded into a DIFFERENT table as new
    # columns (ALTER TABLE <other> ADD COLUMN, sourced from this event) --
    # there is no `clickathon.<event>` table to insert into, and its rows
    # would be an UPDATE of existing rows rather than an INSERT. Those are
    # reported as not-loaded rather than attempted; see the load report.
    unmapped = {
        ev: len(rows)
        for ev, rows in buckets.items()
        if ev not in tables and ev not in altered_tables
    }

    client = get_client()
    for stmt in split_ddl_statements(ddl_text):
        client.command(stmt)

    report = {
        "tables": {},
        "cited_ids": cited_ids,
        "skipped_fixes": skipped_fixes,
        "materialized_views": [],
        "unmapped_events": unmapped,
        "altered_tables": sorted(altered_tables),
    }

    # MVs are incremental-only in ClickHouse (see query-mv-incremental.md) --
    # they never backfill on their own. A source table this spec CREATEd has
    # zero pre-existing rows (nothing to backfill: this run's own inserts,
    # below, will be caught by the MV trigger since it already exists by
    # now). A source table this spec did NOT create may already hold rows
    # from an earlier spec's load, which the MV -- just created -- will
    # never see unless backfilled explicitly, now, before this run adds more.
    for mv in mv_defs:
        source = mv["source"]
        backfilled = bool(source) and source not in tables
        table_report = {"mv": mv["mv"], "target": mv["target"], "source": source, "backfilled": backfilled}
        if backfilled:
            client.command(f"INSERT INTO clickathon.{mv['target']} {mv['select']}")
        report["materialized_views"].append(table_report)

    # Load every table with rows to insert, whether this spec's ddl.sql
    # CREATEd it fresh or only ALTERed it -- an ALTER-only table has no
    # CREATE TABLE body in this spec's ddl.sql (so isn't in `tables`), but
    # its bucket of new rows still needs loading with the table's full,
    # current (post-ALTER) column set.
    table_order = list(tables.keys())
    for t in sorted(altered_tables) + sorted(buckets.keys()):
        # Skip events with no table of their own (see `unmapped` above):
        # querying system.columns for them returns nothing and the insert
        # dies with UNKNOWN_TABLE, taking the whole pipeline down.
        if t in unmapped:
            continue
        if t not in table_order:
            table_order.append(t)

    for table in table_order:
        rows = buckets.get(table, [])
        kind = "created" if table in tables else ("altered" if table in altered_tables else "existing")
        table_report = {"kind": kind, "rows_loaded": 0, "normalized": [], "verified": []}

        if not rows:
            report["tables"][table] = table_report
            continue

        columns = get_live_columns(client, table)
        col_names = [c[0] for c in columns]

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
    if report["unmapped_events"]:
        lines.append("")
        lines.append("## Events not loaded")
        altered = report.get("altered_tables") or []
        for ev, n in report["unmapped_events"].items():
            lines.append("")
            lines.append(f"### `{ev}` — {n} rows NOT loaded")
            lines.append(
                f"No `clickathon.{ev}` table exists: this spec's ddl.sql neither "
                f"CREATEd nor ALTERed a table of that name."
            )
            if altered:
                lines.append(
                    f"This spec ALTERed {', '.join('`' + t + '`' for t in altered)} — "
                    f"so this event's fields were most likely added there as new "
                    f"columns. Those columns therefore exist but are **empty**: "
                    f"landing these rows is an UPDATE of existing rows keyed on a "
                    f"shared id, not an INSERT, which this loader does not do."
                )
                lines.append(
                    "Before treating those columns as populated, verify the join "
                    "actually holds (every spec so far has had a 0% overlap "
                    "surprise here):"
                )
                lines.append("")
                lines.append("```sql")
                for t in altered:
                    lines.append(
                        f"-- how many `{ev}` user_ids exist in {t}?\n"
                        f"SELECT count() FROM clickathon.{t}\n"
                        f"WHERE user_id IN (<user_ids from {ev} events>);"
                    )
                lines.append("```")
                lines.append(
                    "If the overlap is high, backfill those columns with an "
                    "`ALTER TABLE ... UPDATE`. If it is zero, the event is "
                    "disjoint and should be re-instrumented as its own standalone "
                    "table instead."
                )
    if report["materialized_views"]:
        lines.append("## Materialized views")
        for mv in report["materialized_views"]:
            if mv["backfilled"]:
                lines.append(
                    f"- `{mv['mv']}` -> `{mv['target']}`: backfilled from pre-existing "
                    f"`{mv['source']}` rows (source table predates this spec)"
                )
            elif mv["source"]:
                lines.append(
                    f"- `{mv['mv']}` -> `{mv['target']}`: no backfill needed "
                    f"(`{mv['source']}` created fresh by this spec, MV catches this run's inserts)"
                )
            else:
                lines.append(
                    f"- `{mv['mv']}` -> `{mv['target']}`: source table not identified from "
                    f"SELECT (e.g. a join) -- backfill skipped, verify manually"
                )
        lines.append("")

    for table, t in report["tables"].items():
        lines.append(f"## {table} ({t['kind']})")
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
