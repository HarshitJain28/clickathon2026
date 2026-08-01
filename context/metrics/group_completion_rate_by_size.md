---
id: metric.group_completion_rate_by_size
kind: metric
status: verified
confidence: high
source: out/02_group_family/analysis/q01.md, q03.md — verified set-membership step-through by group_size (independently reproduced by both files); out/02_group_family/load_report.md — group_started/group_submitted row counts
last_verified: 2026-08-02
links: [table.group_started, table.group_submitted, table.traveller_added, table.traveller_removed, known_issue.d1_windowfunnel_loses_conversions, known_issue.d2_application_id_join_format, metrics.index]
---

# Group completion rate, by `group_size`

**Definition:** `uniqExact(group_submitted.group_id) / uniqExact(group_started.group_id)`,
computed by **set membership** (`group_submitted.group_id ⊆ group_started.group_id`
by construction — valid per [D1](../known_issues.md#d1--windowfunnel-loses-52-of-conversions--critical),
never `windowFunnel`), segmented by `group_size` as recorded on `group_started`
(the size chosen at group creation, not `group_submitted.travellers_submitted`,
the size at submit time — the two can diverge, see
[group_started.md](../tables/group_started.md) "`co_travelers` conflict").

| `group_size` | Groups started | Groups submitted | Completion rate |
|---:|---:|---:|---:|
| 2 | 475 | 330 | **69.47%** |
| 3 | 283 | 166 | **58.66%** |
| 4 | 238 | 120 | **50.42%** |
| 5 | 114 | 44 | **38.60%** |
| 6 | 90 | 28 | **31.11%** |
| **Overall** | **1,200** | **688** | **57.33%** |

Completion falls **monotonically** as `group_size` grows — a 38.4pp spread
(more than halving) from the smallest to the largest groups. This is the
dominant segment effect on group-flow completion: `analysis/q04.md` checked
`destination` (~14pp spread, no outlier), `device_type` (flat), and
`geoip_country_code` (dominated by `IN` for volume reasons, not a
differential-conversion effect) on the same tables, and none come close.
`analysis/q03.md` also ruled out `traveller_added.docs_complete` as the
driver (only a 2.7-point spread by `group_size`, and weakly/inconsistently
predictive of submission within a size bucket).

**Scope:** Group/Family spec 02 sample only, 2026-06-08 → 2026-06-28 (the
only Group/Family data currently loaded) — treat as directional, not a
full-population estimate. Per [D2](../known_issues.md#d2--spec-application_id-wont-join--critical),
this cannot be joined to the main funnel via `application_id` (0% overlap,
all 4 tables) — it is a standalone group-flow metric, not comparable to
`funnel_conversion`.
