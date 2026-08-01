---
id: table.group_submitted
kind: table
status: verified
confidence: high
source: out/02_group_family/ddl.sql + justification.md (schema); load_report.md — rows loaded, D2 overlap_pct; out/02_group_family/analysis/q01.md, q03.md — verified set-membership step-through by group_size
last_verified: 2026-08-02
links: [doc.envelope, doc.relationship, known_issue.d2_application_id_join_format, known_issue.d1_windowfunnel_loses_conversions, tables.index, metric.group_completion_rate_by_size]
---

# `group_submitted`

Spec 02 (Group / Family Applications). The group is submitted together —
**the conversion event for the group flow**. Distinct row population from
`purchase_completed`/`pay_now_clicked` (no payment fields here, no shared
column with either table's list), and no context-wiki sentence ties it to an
existing table's grain → `CREATE TABLE`. See
`out/02_group_family/justification.md` "CREATE vs ALTER call".

| | |
|---|---:|
| Rows | **688** (verified — `load_report.md`) |
| Distinct users | 688 (1 per user, per profile.md) |
| Distinct `group_id` | 688 (1 per row) |
| Sample time span | 2026-06-08 → 2026-06-28 (profile.md file-level span; not separately profiled per event) |
| Step-through from `group_started` | 688 / 1,200 = **57.33%** — **verified** set-membership join, per `analysis/q01.md`/`q03.md`, 2026-08-02; falls monotonically by `group_size`, from 69.47% (size 2) to 31.11% (size 6) — see [group_started.md](group_started.md) |

This table carries only a **subset** of the shared 30-column envelope (see
[the envelope](index.md)): `id`, `timestamp`, `user_id`, `application_id`,
`device_type`, `os`, `app_version`, `client_lib`, `geoip_country_code`,
`city`, `destination`. Other envelope columns were not observed for this
event and were deliberately not added.

| Column | Type | Values |
|---|---|---|
| `group_id` | `FixedString(32)` | 32-char lowercase-hex, 100% present, 0% null — links back to [group_started](group_started.md) |
| `group_size` | `UInt8` | 100% present, 0% null, range `[2, 6]`, distinct 5 |
| `travellers_submitted` | `UInt8` | 100% present, 0% null, range `[1, 6]`, distinct 6 |

## `travellers_submitted` vs `group_size` — not yet reconciled

Both live on this row; `group_size` is set at [group_started](group_started.md)
while `travellers_submitted` reflects the group's actual composition at
submit time, after any [traveller_added](traveller_added.md)/
[traveller_removed](traveller_removed.md) churn. Whether they typically
match, and what a mismatch means for "completion rate by group size", is
unanalysed — flagged for the Analytics Agent, same status as the broader
`co_travelers` conflict (see [group_started](group_started.md)).

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

- **D1** — "completion rate (`group_started` → `group_submitted`) by group
  size" is funnel-shaped. **Resolved 2026-08-02:** `analysis/q01.md`/`q03.md`
  computed it by set-membership (valid here — this table's `group_id`s are a
  subset of `group_started`'s by construction), not `windowFunnel`. See
  [group_started.md](group_started.md) for the full by-size table.
- **D9** — `device_type` mixes casing; `destination` is UPPERCASE ISO-2.
- **K7** — `app_version` carries no temporal signal platform-wide.
- **D6** — 688 rows, 688 distinct `user_id` — no repeat users here (unlike
  [traveller_added](traveller_added.md)/[traveller_removed](traveller_removed.md)).
