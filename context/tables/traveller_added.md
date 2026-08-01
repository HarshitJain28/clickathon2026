---
id: table.traveller_added
kind: table
status: verified
confidence: high
source: out/02_group_family/ddl.sql + justification.md (schema); load_report.md — rows loaded, D2 overlap_pct; out/02_group_family/analysis/q01.md, q02.md, q03.md — churn analysis, group_size correlation, docs_complete bottleneck test
last_verified: 2026-08-02
links: [doc.envelope, doc.relationship, known_issue.d2_application_id_join_format, known_issue.d6_no_repeat_users, tables.index, metric.group_completion_rate_by_size]
---

# `traveller_added`

Spec 02 (Group / Family Applications). A co-traveller is added to a group —
its own timestamp, own row per add. No existing table writes a row at this
moment, so this is a `CREATE TABLE`, not an `ALTER`. See
`out/02_group_family/justification.md` "CREATE vs ALTER call".

| | |
|---|---:|
| Rows | **3,495** (verified — `load_report.md`) |
| Distinct users (group owners) | **1,200** (34.3% of rows — see "repeat users" below) |
| Distinct `group_id` | 1,200 |
| Rows per group | 2.91 average (3,495 / 1,200) |
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
| `traveller_index` | `UInt8` | 100% present, 0% null, range `[0, 5]`, distinct 6 — smallest type that fits |
| `relation` | `LowCardinality(String)` | 5 values: `friend`(727) `spouse`(712) `child`(708) `sibling`(707) `parent`(641) — not `Enum8`: this is a live, newly-built feature with no closed/versioned taxonomy, same reasoning spec 01 used for `saved_method_type` |
| `docs_complete` | `Bool` | 100% present, 0% null — `true`(2,795) `false`(700) |

## Add/remove churn — verified 2026-08-02 (`analysis/q02.md`)

Across all 1,200 groups, 3,495 add rows (avg **2.91/group**) vs. only 70
removal rows in the sibling table — **3,425 travellers net-added**. Churn is
real but small: **5.75% of groups (69/1,200)** had at least one removal, and
only **2.00% of add-events (70/3,495)** were later offset by one. Every
removed `group_id` in [traveller_removed](traveller_removed.md) is confirmed
present in both this table and `group_started` (69/69, 100% — verified set
membership, not orphaned events). The dominant pattern is pure addition:
94.25% of groups never remove a co-traveller once added, and where churn
does occur it's almost always a single removal (only 1 group removed twice).

**Rows-added and removal-rate both scale with `group_size`** (`analysis/q01.md`):
average `traveller_added` rows per group rises from 1.91 (size 2) to 5.04
(size 6), and the share of groups with a `traveller_removed` event rises
from 0.42% (size 2) to 18.4% (size 5) / 17.8% (size 6) — see
[group_started.md](group_started.md) for the completion-rate context this
correlates with.

## `docs_complete` is not the group-size completion bottleneck — tested 2026-08-02 (`analysis/q03.md`)

Per-traveller `docs_complete = true` rate by `group_size` barely moves:
81.15% (2) → 80.52% (3) → 80.32% (4) → 77.78% (5) → 78.41% (6) — only a
2.7-point spread, no meaningful degradation as groups get bigger. Within a
size bucket, grouping by `group_id` and flagging "all added travellers'
`docs_complete = true`" is at best weakly predictive of `group_submitted`
for large groups (+4.5 to +11.9pp at size 4–6) and **inverted** for small
ones (−5.3 to −7.7pp at size 2–3, i.e. submission is *higher* when docs are
*not* all complete). Even a size-6 group with 100% `docs_complete` submits
only 37.5% of the time, far below a size-2 group's 66.98% baseline
regardless of doc status. Conclusion: `group_size` itself, not
`docs_complete`, is the dominant driver of the `group_started →
group_submitted` drop-off — see [group_started.md](group_started.md).

## ⚠ Breaks the "no repeat users" pattern — read before `uniqExact` checks

Unlike every baseline table (see [known_issues.md](../known_issues.md) → D6,
"no repeat users"), this table has **3,495 rows but only 1,200 distinct
`user_id`** (34.3% unique). The same owning `user_id` legitimately generates
multiple rows — one per co-traveller added to their own group. This is
expected given the feature (one group owner performs several add actions),
**not** a violation of D6's claim about repeat *application-level* events on
the main funnel — but an analyst assuming `uniqExact(user_id) == count()`
(true on every baseline table) would be wrong here. Same pattern on
[traveller_removed](traveller_removed.md).

## ⚠ `application_id` does not join `application_started` — 0% overlap

Same D2 finding as the other 3 tables in this spec: normalized on ingest
(32-char hex → 36-char hyphenated UUID), but the overlap-check against
`application_started` returned **`overlap_pct = 0.0%`** (verified —
`load_report.md`, 2026-08-02) → **STOP**, analyse standalone. See
[known_issues.md](../known_issues.md) → D2.

## Physical layout

`ENGINE = MergeTree`, `ORDER BY (toDate(timestamp), group_size, group_id,
id)` — same D8-compliant key as all 4 tables in this spec (does not lead
with the random `id` UUID). See [group_started](group_started.md) for the
full `group_size`-over-`user_id` reasoning.

## Other risks carried forward (see `justification.md` for full reasoning)

- **D1** — do not use `windowFunnel`/`sequenceMatch` on this flow without
  first checking monotonicity; use set-membership counts unless
  `monotonic_share` ≥ ~0.99.
- **D9** — `device_type` mixes casing (`ios`, `android`, `web-user-b2c` vs
  `Desktop`); `destination` is UPPERCASE ISO-2.
- **K7** — `app_version`'s 3 values carry no temporal signal platform-wide;
  do not read a version-cut difference as a rollout effect.
- `co_travelers` (on `application_started`) vs this table's `group_size` /
  [group_submitted](group_submitted.md)'s `travellers_submitted` can
  legitimately diverge for the same `application_id` — see
  [group_started](group_started.md) "`co_travelers` conflict".
