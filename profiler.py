#!/usr/bin/env python3
"""Deterministic NDJSON event profiler. Stdlib only."""

import argparse
import json
import sys
from collections import Counter, OrderedDict
from datetime import datetime, timezone
from pathlib import Path

JSON_TYPE_ORDER = ["string", "int", "float", "bool", "null", "object", "array"]

# A field is "low_cardinality" only when its distinct values are both few in
# absolute terms (<1000) AND rare relative to how often the field appears.
# A field that's 100% unique (e.g. user_id in a 300-row event) must never
# qualify just because 300 < 1000 -- that was the original bug.
LOW_CARDINALITY_RATIO = 0.10


def json_type(v):
    if v is None:
        return "null"
    if isinstance(v, bool):
        return "bool"
    if isinstance(v, int):
        return "int"
    if isinstance(v, float):
        return "float"
    if isinstance(v, str):
        return "string"
    if isinstance(v, list):
        return "array"
    if isinstance(v, dict):
        return "object"
    return "unknown"


def stringify_value(v):
    if isinstance(v, (dict, list)):
        return json.dumps(v, sort_keys=True, separators=(",", ":"))
    if isinstance(v, bool):
        return "true" if v else "false"
    if v is None:
        return "null"
    return str(v)


def parse_timestamp(ts):
    if not isinstance(ts, str) or not ts:
        return None
    s = ts.strip()
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(s)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def flatten_row(row):
    """Return dict of field-path -> value, flattened exactly one level deep."""
    flat = {}
    for k, v in row.items():
        if k in ("event", "id", "timestamp"):
            continue
        if isinstance(v, dict):
            for nk, nv in v.items():
                flat[f"{k}.{nk}"] = nv
        else:
            flat[k] = v
    return flat


def load_rows(path):
    rows = []
    parse_errors = 0
    total_lines = 0
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            if not stripped:
                continue
            total_lines += 1
            try:
                obj = json.loads(stripped)
                if not isinstance(obj, dict):
                    raise ValueError("not an object")
            except (ValueError, json.JSONDecodeError):
                parse_errors += 1
                continue
            rows.append(obj)
    return rows, parse_errors, total_lines


def compute_field_stats(rows_for_event):
    """rows_for_event: list of flattened dicts. Returns ordered dict field -> stats."""
    n = len(rows_for_event)
    all_fields = set()
    for r in rows_for_event:
        all_fields.update(r.keys())

    field_stats = {}
    for field in all_fields:
        present_count = 0
        null_count = 0
        types_seen = Counter()
        value_counts = Counter()
        numeric_values = []
        all_numeric = True
        any_non_null = False

        for r in rows_for_event:
            if field not in r:
                continue
            present_count += 1
            v = r[field]
            if v is None:
                null_count += 1
                types_seen["null"] += 1
                all_numeric = False
                continue
            any_non_null = True
            t = json_type(v)
            types_seen[t] += 1
            if t not in ("int", "float"):
                all_numeric = False
            else:
                numeric_values.append(v)
            value_counts[stringify_value(v)] += 1

        presence_pct = (present_count / n * 100.0) if n else 0.0
        null_pct = (null_count / present_count * 100.0) if present_count else 0.0
        distinct = len(value_counts)

        top_values = None
        if distinct <= 1000:
            ranked = sorted(value_counts.items(), key=lambda kv: (-kv[1], kv[0]))
            top10 = ranked[:10]
            top_values = [[val, cnt] for val, cnt in top10]
            if distinct > 10:
                remaining = distinct - 10
                top_values.append(["...", remaining])

        numeric_range = None
        if all_numeric and present_count > 0 and len(numeric_values) == present_count - null_count and len(numeric_values) > 0:
            numeric_range = (min(numeric_values), max(numeric_values))

        non_null_types = [t for t in types_seen if t != "null"]
        is_string_only = non_null_types == ["string"]
        distinct_ratio = (distinct / present_count) if present_count else 0.0
        hint = (
            "low_cardinality"
            if (is_string_only and distinct < 1000 and distinct_ratio <= LOW_CARDINALITY_RATIO)
            else None
        )

        field_stats[field] = {
            "presence_pct": presence_pct,
            "null_pct": null_pct,
            "types_seen": OrderedDict(
                (t, types_seen[t]) for t in JSON_TYPE_ORDER if t in types_seen
            ),
            "distinct": distinct,
            "distinct_ratio": distinct_ratio,
            "top_values": top_values,
            "numeric_range": numeric_range,
            "hint": hint,
        }
    return field_stats


def fmt_num(v):
    if isinstance(v, float):
        if v == int(v) and abs(v) < 1e15:
            return f"{v:.1f}"
        return repr(v)
    return str(v)


def fmt_pct(v):
    if v == int(v):
        return str(int(v))
    return f"{v:.1f}"


def detect_shape_drift(raw_rows):
    """Return {field: {"object": n, "scalar": n}} for top-level keys whose
    value is a dict in some rows and a non-null non-dict in others."""
    shape_counts = {}
    for r in raw_rows:
        for k, v in r.items():
            if k in ("event", "id", "timestamp") or v is None:
                continue
            counts = shape_counts.setdefault(k, {"object": 0, "scalar": 0})
            counts["object" if isinstance(v, dict) else "scalar"] += 1
    return {
        k: c for k, c in shape_counts.items() if c["object"] > 0 and c["scalar"] > 0
    }


def build_profile(rows, parse_errors, total_lines):
    total_parsed = len(rows)

    # ids appearing more than once (global)
    id_counter = Counter()
    for r in rows:
        rid = r.get("id")
        if rid is not None:
            id_counter[stringify_value(rid)] += 1
    dup_id_count = sum(1 for c in id_counter.values() if c > 1)

    # timestamps
    min_ts = None
    max_ts = None
    bad_timestamp_count = 0
    for r in rows:
        dt = parse_timestamp(r.get("timestamp"))
        if dt is None:
            bad_timestamp_count += 1
            continue
        if min_ts is None or dt < min_ts:
            min_ts = dt
        if max_ts is None or dt > max_ts:
            max_ts = dt

    # group by event
    event_rows = OrderedDict()
    event_counts = Counter()
    for r in rows:
        ev = r.get("event")
        if not isinstance(ev, str) or not ev:
            ev = "_unknown"
        event_counts[ev] += 1
        event_rows.setdefault(ev, []).append(r)

    events_sorted = sorted(event_counts.items(), key=lambda kv: (-kv[1], kv[0]))

    per_event_stats = OrderedDict()
    per_event_id_dupes = OrderedDict()
    per_event_shape_drift = OrderedDict()
    for ev, _ in events_sorted:
        raw = event_rows[ev]
        flat_rows = [flatten_row(r) for r in raw]
        per_event_stats[ev] = compute_field_stats(flat_rows)

        ev_id_counter = Counter()
        for r in raw:
            rid = r.get("id")
            if rid is not None:
                ev_id_counter[stringify_value(rid)] += 1
        per_event_id_dupes[ev] = sum(1 for c in ev_id_counter.values() if c > 1)

        per_event_shape_drift[ev] = detect_shape_drift(raw)

    # grid: field -> set of events covering it
    field_events = {}
    for ev, stats in per_event_stats.items():
        for field in stats:
            field_events.setdefault(field, set()).add(ev)

    grid_fields = sorted(
        field_events.keys(), key=lambda f: (-len(field_events[f]), f)
    )

    return {
        "total_parsed": total_parsed,
        "parse_errors": parse_errors,
        "total_lines": total_lines,
        "dup_id_count": dup_id_count,
        "bad_timestamp_count": bad_timestamp_count,
        "min_ts": min_ts,
        "max_ts": max_ts,
        "events_sorted": events_sorted,
        "per_event_stats": per_event_stats,
        "per_event_id_dupes": per_event_id_dupes,
        "per_event_shape_drift": per_event_shape_drift,
        "grid_fields": grid_fields,
        "field_events": field_events,
    }


def abbreviate_event_names(event_names):
    """Return dict event -> abbreviation, and legend list of (abbr, full)."""
    abbr_map = {}
    used = set()
    for ev in event_names:
        parts = ev.split("_")
        candidate = "".join(p[0] for p in parts if p).upper()
        if not candidate:
            candidate = ev[:3].upper()
        base = candidate
        i = 1
        while candidate in used:
            i += 1
            candidate = f"{base}{i}"
        used.add(candidate)
        abbr_map[ev] = candidate
    legend = [(abbr_map[ev], ev) for ev in event_names]
    return abbr_map, legend


def render_markdown(profile):
    lines = []
    total_parsed = profile["total_parsed"]
    parse_errors = profile["parse_errors"]
    dup_id_count = profile["dup_id_count"]
    bad_timestamp_count = profile["bad_timestamp_count"]
    min_ts = profile["min_ts"]
    max_ts = profile["max_ts"]

    min_ts_str = min_ts.isoformat() if min_ts else "n/a"
    max_ts_str = max_ts.isoformat() if max_ts else "n/a"

    lines.append(
        f"# Event Profile — rows: {total_parsed}, parse_errors: {parse_errors}, "
        f"duplicate_ids: {dup_id_count}, unparseable_timestamps: {bad_timestamp_count}, "
        f"time_span: {min_ts_str} to {max_ts_str}"
    )
    lines.append("")

    events_sorted = profile["events_sorted"]
    lines.append("## Event Type Counts")
    lines.append("")
    lines.append("| event | rows |")
    lines.append("|---|---|")
    for ev, cnt in events_sorted:
        lines.append(f"| {ev} | {cnt} |")
    lines.append("")

    per_event_stats = profile["per_event_stats"]
    per_event_id_dupes = profile["per_event_id_dupes"]
    per_event_shape_drift = profile["per_event_shape_drift"]
    for ev, cnt in events_sorted:
        stats = per_event_stats[ev]
        id_dupes = per_event_id_dupes[ev]
        header = f"## {ev} (n={cnt}, id_duplicates: {id_dupes})"
        lines.append(header)
        lines.append("")

        drift = per_event_shape_drift[ev]
        if drift:
            for field in sorted(drift.keys()):
                c = drift[field]
                lines.append(
                    f"> ⚠ shape drift: `{field}` is an object in {c['object']} rows "
                    f"and a non-object scalar in {c['scalar']} rows of this event — "
                    f"see both `{field}` and `{field}.*` entries below."
                )
            lines.append("")

        lines.append("| field | present | type | distinct values / range |")
        lines.append("|---|---|---|---|")
        for field in sorted(stats.keys()):
            s = stats[field]
            present_str = f"{fmt_pct(s['presence_pct'])}%"
            if s["null_pct"] > 0:
                present_str += f" ({fmt_pct(s['null_pct'])}% null)"

            type_str = ", ".join(
                f"{t}:{c}" for t, c in s["types_seen"].items() if t != "null"
            )
            if not type_str:
                type_str = "null"

            distinct_str = f"{s['distinct']} ({fmt_pct(s['distinct_ratio'] * 100)}% unique)"
            if s["hint"] == "low_cardinality":
                distinct_str += " LC"

            if s["numeric_range"] is not None:
                lo, hi = s["numeric_range"]
                val_str = f"range: [{fmt_num(lo)}, {fmt_num(hi)}]"
            elif s["top_values"] is not None:
                pieces = []
                for val, c in s["top_values"]:
                    pieces.append(f"{val}({c})")
                val_str = "; ".join(pieces)
            else:
                val_str = "(>1000 distinct, omitted)"

            cell = f"distinct: {distinct_str} — {val_str}"
            lines.append(f"| {field} | {present_str} | {type_str} | {cell} |")
        lines.append("")

    # grid
    event_names = [ev for ev, _ in events_sorted]
    abbr_map, legend = abbreviate_event_names(event_names)
    grid_fields = profile["grid_fields"]
    field_events = profile["field_events"]

    lines.append("## Field × Event Grid")
    lines.append("")
    header_cells = ["field"] + [abbr_map[ev] for ev in event_names]
    lines.append("| " + " | ".join(header_cells) + " |")
    lines.append("|" + "---|" * len(header_cells))
    for field in grid_fields:
        row_cells = [field]
        covered = field_events[field]
        for ev in event_names:
            row_cells.append("yes" if ev in covered else "no")
        lines.append("| " + " | ".join(row_cells) + " |")
    lines.append("")

    lines.append("**Legend:** " + "; ".join(f"{a}={full}" for a, full in legend))
    lines.append("")

    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description="Deterministic NDJSON event profiler")
    parser.add_argument("input", help="path to events.ndjson")
    parser.add_argument("out_dir", nargs="?", default=".", help="output directory")
    args = parser.parse_args()

    input_path = Path(args.input)
    try:
        rows, parse_errors, total_lines = load_rows(input_path)
    except OSError as e:
        print(f"error: cannot read {input_path}: {e}", file=sys.stderr)
        return 1

    if total_lines > 0 and parse_errors / total_lines > 0.10:
        print(
            f"error: {parse_errors}/{total_lines} lines failed to parse (>10%)",
            file=sys.stderr,
        )
        return 1

    profile = build_profile(rows, parse_errors, total_lines)
    md = render_markdown(profile)

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "profile.md"
    out_path.write_text(md, encoding="utf-8", newline="\n")

    print(f"wrote {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
