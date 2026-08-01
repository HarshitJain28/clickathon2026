---
id: table.traveller_removed
kind: table
status: verified
confidence: high
source: out/02_group_family/ddl.sql + justification.md (schema); load_report.md — rows loaded, D2 overlap_pct; out/02_group_family/analysis/q01.md, q02.md — churn analysis, group_size correlation, set-membership check against group_started/traveller_added
last_verified: 2026-08-02
links: [doc.envelope, doc.relationship, known_issue.d2_application_id_join_format, known_issue.d6_no_repeat_users, tables.index]
---

# `traveller_removed`

Spec 02 (Group / Family Applications). Symmetric to
[traveller_added](traveller_added.md) — a co-traveller is dropped from a
group. Its own occurrence, no existing analogue → `CREATE TABLE`. See
`out/02_group_family/justification.md` "CREATE vs ALTER call". Rare churn
event — smallest of the 4 new tables.

| | |
|---|---:|
| Rows | **70** (verified — `load_report.md`) |
| Distinct users | 69 (98.6% of rows — one user has 2 removal rows) |
| Distinct `group_id` | 69 (98.6% — one group has 2 removal rows) |
| Sample time span | 2026-06-08 → 2026-06-28 (profile.md file-level span; not separately profiled per event) |

This table carries only a **subset** of the shared 30-column envelope (see
[the envelope](index.md)): `id`, `timestamp`, `user_id`, `application_id`,
`device_type`, `os`, `app_version`, `client_lib`, `geoip_country_code`,
`city`, `destination`. Other envelope columns were not observed for this
event and were deliberately not added.

| Column | Type | Values |
|---|---|---|
| `group_id` | `FixedString(32)` | 32-char lowercase-hex, 100% present, 0% null — links back to [group_started](group_started.md) |
| `group_size` | `UInt8` | 100% present, 0% null, range `[2, 6]`, distinct 5 |
| `traveller_index` | `UInt8` | 100% present, 0% null, range `[0, 5]`, distinct 6 |

## Removals are consistent, not orphaned — and scale with `group_size` — verified 2026-08-02 (`analysis/q01.md`, `q02.md`)

Every one of the 70 removed `group_id`s is confirmed present in both
`group_started` and [traveller_added](traveller_added.md) (69/69, 100% —
verified set membership) — removal events are consistent with a prior add,
not orphaned. Only **5.75% of groups (69/1,200)** ever have a removal, and
just **2.00% of add-events (70/3,495)** are later offset by one — the
dominant group-flow pattern is pure addition, not churn. Where removal does
occur it's almost always a single event: 68 groups had exactly 1, only 1
group had 2 (this table's own repeat-user row, see below).

The share of groups with a removal **rises sharply with `group_size`**:
0.42% at size 2 vs **18.4% at size 5** and **17.8% at size 6** — mid-flow
churn is far more common in larger groups, one plausible contributor to the
completion-rate drop documented on [group_started.md](group_started.md).

## ⚠ Breaks the "no repeat users" pattern

70 rows over 69 distinct `user_id` — one user has 2 removal rows. Same
expected repeat-user shape as [traveller_added](traveller_added.md) (one
group owner can perform multiple add/remove actions); not a violation of D6
on the main funnel, but do not assume `uniqExact(user_id) == count()` here.
See [known_issues.md](../known_issues.md) → D6.

## ⚠ `application_id` does not join `application_started` — 0% overlap

Same D2 finding as the other 3 tables in this spec: normalized on ingest,
overlap-check against `application_started` returned **`overlap_pct =
0.0%`** (verified — `load_report.md`, 2026-08-02) → **STOP**, analyse
standalone. See [known_issues.md](../known_issues.md) → D2.

## Physical layout

`ENGINE = MergeTree`, `ORDER BY (toDate(timestamp), group_size, group_id,
id)` — same D8-compliant key as all 4 tables in this spec. See
[group_started](group_started.md) for the full reasoning.

## Other risks carried forward

- **D1** — do not use `windowFunnel`/`sequenceMatch` on this flow without
  first checking monotonicity; use set-membership counts unless
  `monotonic_share` ≥ ~0.99.
- **D9** — `device_type` mixes casing; `destination` is UPPERCASE ISO-2.
- **K7** — `app_version` carries no temporal signal platform-wide.
- Small n (70 rows) — any segment cut on this table is directional only.
