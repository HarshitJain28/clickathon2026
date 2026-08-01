---
id: table.group_started
kind: table
status: verified
confidence: high
source: out/02_group_family/ddl.sql + justification.md (schema); load_report.md — rows loaded, D2 overlap_pct; out/02_group_family/analysis/q01.md, q04.md — verified set-membership step-through by group_size, destination/segment cuts
last_verified: 2026-08-02
links: [doc.envelope, doc.relationship, known_issue.d2_application_id_join_format, known_issue.d1_windowfunnel_loses_conversions, tables.index, metric.group_completion_rate_by_size]
---

# `group_started`

Spec 02 (Group / Family Applications). Fires when a user opts into the group
flow — **creates the `group_id` entity**. `application_id` is present on
100% of rows (profile.md), meaning this always happens *after* an
application already exists, but no existing table's grain matches this
moment (`application_started`'s own column list — `purpose`, `eta_shown`,
`flow` — has no group-shaped analogue). → `CREATE TABLE`, not an `ALTER`.
See `out/02_group_family/justification.md` "CREATE vs ALTER call".

| | |
|---|---:|
| Rows | **1,200** (verified — `load_report.md`) |
| Distinct users | 1,200 (1 per user, per profile.md) |
| Distinct `group_id` | 1,200 (1 per row — this is where `group_id` originates) |
| Sample time span | 2026-06-08 → 2026-06-28 (profile.md file-level span; not separately profiled per event) |
| Step-through → `group_submitted` | 688 / 1,200 = **57.33%** — **verified** set-membership join (`group_submitted.group_id ⊆ group_started.group_id` by construction), per `analysis/q01.md`/`q03.md`, 2026-08-02 |

This table carries only a **subset** of the shared 30-column envelope (see
[the envelope](index.md)): `id`, `timestamp`, `user_id`, `application_id`,
`device_type`, `os`, `app_version`, `client_lib`, `geoip_country_code`,
`city`, `destination`. Other envelope columns (`app_session_id`,
`funnel_type`, `co_travelers`, `gclid`, `citizenship`, `duplicate_id`,
`is_back_filled`, etc.) were not observed for this event and were
deliberately not added — an unobserved column is an invented column.

| Column | Type | Values |
|---|---|---|
| `group_id` | `FixedString(32)` | 32-char lowercase-hex, 100% present, 0% null, 1,200/1,200 unique — the group entity's key, created here |
| `group_size` | `UInt8` | 100% present, 0% null, range `[2, 6]`, distinct 5 |

## `group_id` is `FixedString(32)`, not `String` — deliberate deviation

Every sampled value across this table and its 3 siblings (`traveller_added`,
`traveller_removed`, `group_submitted`) is exactly 32 lowercase-hex
characters with no ragged exception observed (profile.md). `FixedString` is
normally disqualified for identifiers because it silently mismatches a
`String` counterpart on join — but `group_id` joins nothing outside this
spec's own 4 tables (a brand-new entity, unlike `application_id`/`user_id`),
so the column-policy's carve-out for spec-local keys applies. See
`justification.md` "String-type decision". *Caveat:* inferred from a handful
of displayed samples per event (profiler omits the full list past ~10
entries) — a future `group_id` deviating from 32 hex chars would be rejected
on insert.

## ⚠ `application_id` does not join `application_started` — 0% overlap

`application_id` was normalized on ingest per D2 (32-char hex → 36-char
hyphenated UUID). The mandatory D2 overlap-check then ran against
`application_started` and returned **`overlap_pct = 0.0%`** (verified —
`load_report.md`, 2026-08-02) → per D2's action table, **STOP**: analyse
this table **standalone only**, the same verdict spec 01's 5 tables got. See
[known_issues.md](../known_issues.md) → D2.

## Completion rate falls monotonically as `group_size` grows — verified 2026-08-02

Set-membership completion rate (`group_submitted.group_id ⊆ group_started.group_id`
by construction — no `windowFunnel`, per D1) by `group_size`, from
`analysis/q01.md` and independently reproduced by `q03.md`:

| `group_size` | Started | Submitted | Completion |
|---:|---:|---:|---:|
| 2 | 475 | 330 | **69.47%** |
| 3 | 283 | 166 | **58.66%** |
| 4 | 238 | 120 | **50.42%** |
| 5 | 114 | 44 | **38.60%** |
| 6 | 90 | 28 | **31.11%** |

38pp spread from smallest to largest group — more than halving completion.
`q04.md` checked other segments (`device_type`, `geoip_country_code`,
`destination`) on this same table and found `group_size` dwarfs all of them
(destination spread only ~14pp, device_type flat, `geoip_country_code`
dominated by `IN` for volume reasons, not a differential-conversion effect).
See [group_completion_rate_by_size](../metrics/group_completion_rate_by_size.md).

A likely contributing mechanism, also from `q01.md`: `traveller_removed`
(mid-flow churn before submit) scales sharply with `group_size` — only
0.42% of size-2 groups ever have a removal event, vs **18.4% of size-5 and
17.8% of size-6 groups** — and average `traveller_added` rows per group
rises from 1.91 (size 2) to 5.04 (size 6). Correlational, not proof of
causation — this spec instruments only two funnel moments
(`group_started`/`group_submitted`) plus the fan-out events, so there is no
intermediate step to say precisely *where* inside the flow large groups
abandon.

`q03.md` separately tested whether `traveller_added.docs_complete` (not
`group_size`) is the bottleneck for big groups: it isn't — `docs_complete`
barely moves with `group_size` (81.15% at size 2 → 78.41% at size 6, a
2.7-point spread) and, within a size bucket, having all travellers'
`docs_complete = true` is at best weakly predictive of submission for large
groups (4–6pp) and inverted for small ones. `group_size` remains the
dominant driver. See [traveller_added.md](traveller_added.md).

## Physical layout deviates from the 8 baseline tables — and from spec 01's template

`ENGINE = MergeTree`, `ORDER BY (toDate(timestamp), group_size, group_id,
id)` — does not lead with the random `id` UUID, per known_issues.md D8.
Unlike spec 01's 5 tables (which keyed on `..., device_type, user_id, id`),
this spec substitutes `group_size` (the PM's most-cited dimension — asked
about twice in spec.md) and `group_id` (needed for cross-event grouping by
[traveller_added](traveller_added.md)/[traveller_removed](traveller_removed.md)/
[group_submitted](group_submitted.md)) in place of `user_id`, because
`group_id` and `user_id` are 1:1-collinear in this dataset — every group is
owned by exactly one user (1,200/1,200 distinct in both columns here). See
`justification.md` "ORDER BY / PARTITION BY reasoning".

## `co_travelers` conflict — flagged, not resolved

`relationship.md`'s "Entities the incoming specs will add" flagged that
`Group` (`group_id`, `group_size`) conflicts with the existing
`application_started.co_travelers` column. Checked at the schema level:
`group_size` lives only in these 4 new tables — no column was added to or
duplicated from `application_started`, so no parallel model was created
here. But the two figures can legitimately diverge for the same
`application_id` (`co_travelers` is set once at `application_started`;
`group_size`/`travellers_submitted` reflect the live, mutable group flow) —
reconciling which is authoritative is unresolved analysis-layer work. See
`justification.md` "Risks / caveats" and [relationship.md](../relationship.md) → "Group".

## Other risks carried forward (see `justification.md` for full reasoning)

- **D1** — the PM's "completion rate (`group_started` → `group_submitted`)
  by group size" question is funnel-shaped. **Resolved 2026-08-02:**
  `analysis/q01.md`/`q03.md` computed it correctly, by set-membership
  (valid here because `group_submitted`'s `group_id`s are a subset of
  `group_started`'s by construction), not `windowFunnel` — see the
  completion-rate table above.
- **D9** — `device_type` mixes casing (`ios`, `android`, `web-user-b2c` vs
  `Desktop`); `destination` is UPPERCASE ISO-2, exactly as documented
  platform-wide.
- **K7** — `app_version`'s 3 values here (`7.44.0`/`7.45.2`/`7.46.0`) carry
  no temporal signal platform-wide; do not read a version-cut difference in
  group-flow adoption as a rollout effect.
- **D6** — 1,200 rows, 1,200 distinct `user_id` — no repeat users here
  (unlike [traveller_added](traveller_added.md)/
  [traveller_removed](traveller_removed.md), see their pages).
