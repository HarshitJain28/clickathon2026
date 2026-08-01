# Justification — Spec 02: Group / Family Applications

## Overview

| Object | Kind | Source event(s) | Rows | ORDER BY / key | Notes |
|---|---|---|---:|---|---|
| `group_started` | CREATE TABLE | `group_started` | 1,200 | `(toDate(timestamp), group_size, group_id, id)` | Group flow begins; creates `group_id`. |
| `traveller_added` | CREATE TABLE | `traveller_added` | 3,495 | `(toDate(timestamp), group_size, group_id, id)` | One row per co-traveller add; repeat `user_id` by design (see risks). |
| `traveller_removed` | CREATE TABLE | `traveller_removed` | 70 | `(toDate(timestamp), group_size, group_id, id)` | Rare churn event. |
| `group_submitted` | CREATE TABLE | `group_submitted` | 688 | `(toDate(timestamp), group_size, group_id, id)` | Group submitted; conversion event for this flow. |
| — | ALTER TABLE | none | n/a | — | No event in this spec shares a moment/grain with an existing table (see below). |
| — | MATERIALIZED VIEW | none | n/a | — | Not built — see "Materialized view decision". |

All 4 tables: `ENGINE = MergeTree`, `PARTITION BY toYYYYMM(timestamp)`.

---

## CREATE vs ALTER call

Per event, checked against every existing table's column list in `ddl.sql`
(baseline + spec 01), `instrumentation_notes.md`'s "one table per event,
auto-created by the client event SDK" convention, and each existing table's
own context-wiki page (`application_started.md`, `purchase_completed.md`) for
an explicit instrumentation-tie instruction (the kind `purchase_completed.md`
gives for spec 05's forex add-on — "should be instrumented consistently with
them"). No such sentence exists tying any of this spec's 4 events to an
existing table's grain:

- **`group_started`** — fires when the group flow begins. `application_id` is
  present on 100% of its rows (profile.md), meaning it always occurs *after*
  an application already exists, but `application_started.md` says nothing
  about a group sub-flow, and `application_started`'s own column list
  (`purpose`, `eta_shown`, `flow`) has no group-shaped analogue — this is a
  distinct, later occurrence (opting into the group flow), not the same
  moment as application creation. → **CREATE TABLE**.
- **`traveller_added`** — a co-traveller is added to a group. Its own
  timestamp, its own row per add, no existing table writes a row at this
  moment. → **CREATE TABLE**.
- **`traveller_removed`** — symmetric to `traveller_added`, its own
  occurrence (a drop action), no existing analogue. → **CREATE TABLE**.
- **`group_submitted`** — the group is submitted together. Distinct row
  population from `purchase_completed`/`pay_now_clicked` (no payment fields
  here, no shared column with either table's list) and no context-wiki
  sentence ties it to an existing table's grain. → **CREATE TABLE**.

No ALTER candidates were found for this spec.

## Column policy

Columns are exactly the fields profile.md's Field × Event Grid shows present
for each event. Envelope fields not observed for any of the 4 events —
`app_session_id`, `device`, `geoip_subdivision_1_code`, `client_ip`,
`latitude`/`longitude`, `locale`/`language`, `funnel_type`, `co_travelers`,
`is_guest`/`is_referral`/`is_enterprise`, `gclid`/`fbclid`/`gad_source`,
`citizenship`, `is_back_filled`, `duplicate_id` — are **not** added, per the
column policy (an unobserved column is an invented column), exactly as spec
01 handled its own unobserved-envelope-field list.

## Column choices

- **`id UUID`, `timestamp DateTime`** — structural row identity/time,
  implied by profile.md's per-event `id_duplicates: 0` and file-level
  `time_span`, matching the existing tables' convention. Not nullable
  (existing tables' convention; also skill `schema-types-avoid-nullable`).
- **`user_id String`** — 100% present, 0% null in every event's profile row.
  Matches the existing tables' exact `user_id String` type (join-key type
  match, `relationship.md` §1/§3, "universal, non-null everywhere").
- **`application_id Nullable(String)`** — 100% present in this spec's
  sample with no null noted, but typed `Nullable(String)` anyway to match
  `application_started.application_id`'s exact type, because it is (in
  principle) the join key back into the main funnel (`relationship.md` §3
  join map) — per the join-key-type-matching rule, join keys must match the
  existing column's type even when local nullability looks avoidable.
  **Critical caveat: see D2 below — this join is unverified for this spec.**
- **`group_id FixedString(32)`** and **`group_size UInt8`** — see
  "String-type decision" and the numeric reasoning below. Present 100%,
  0% null, across all 4 events (Field × Event Grid).
- **`device_type`, `os`, `app_version`, `client_lib`, `geoip_country_code`,
  `city`, `destination`** — see "String-type decision" below.
- **`traveller_index UInt8`** (`traveller_added`, `traveller_removed`) —
  100% present in both events, range `[0, 5]`, distinct 6 → `UInt8` is the
  smallest type that comfortably fits (skill `schema-types-minimize-bitwidth`).
  Non-nullable: 0% null observed in either event's profile row.
- **`docs_complete Bool`** (`traveller_added` only) — 100% present, distinct 2
  (`true`/`false`), 0% null → `Bool` non-nullable, per skill
  `schema-types-native-types` ("Booleans → Bool or UInt8, avoid String") and
  matching spec 01's `otp_success`/`eligible` precedent.
- **`relation LowCardinality(String)`** (`traveller_added` only) — see
  "String-type decision" below.
- **`travellers_submitted UInt8`** (`group_submitted` only) — 100% present,
  range `[1, 6]`, distinct 6 → `UInt8`, non-nullable (0% null observed).

## String-type decision (per column)

- **`device_type`** (`ios`/`android`/`web-user-b2c`/`Desktop`, 4 values,
  0.1–5.7% unique across events) → `LowCardinality(String)`. Ragged casing
  (`Desktop` vs `ios`) rules out `FixedString`; low, stable cardinality plus
  known_issues.md **D8**'s explicit instruction ("`LowCardinality(String)`
  for all categoricals ... 4 device types ... — all tiny") makes this the
  direct call. Non-nullable: 100% present, 0% null in every event.
- **`os`** (`iOS`/`Android`/`Mac OS X`/`Windows`, 4 values) →
  `LowCardinality(Nullable(String))`. Same cardinality argument as
  `device_type`, but profile.md shows a genuine null rate in every event
  (6.3% `traveller_added`, 6.3% `group_started`, 6.5% `group_submitted`, 4.3%
  `traveller_removed` — consistent with the platform envelope's documented
  5.95% null) — nullability here is semantic (SDK didn't report OS), not
  absence of data yet, so `Nullable` is kept per skill
  `schema-types-avoid-nullable`'s carve-out.
- **`app_version`** (`7.45.2`/`7.44.0`/`7.46.0`, 3 values, 0.1–4.3% unique) →
  `LowCardinality(String)`, not `FixedString`. All three sampled values are
  the same length (6 chars), but there is no wiki statement guaranteeing the
  version string is permanently fixed-width (a future two-digit patch, e.g.
  `7.47.10`, would be 7 chars) — the "confirmed fixed length" bar isn't met,
  so `LowCardinality(String)` is the safe choice, matching D8's spirit and
  known_issues.md **K7**'s finding that `app_version` carries no temporal
  signal (it's a synthetic random tag, not a controlled rollout field).
- **`client_lib`** (`mobile-rn`/`web-js`, 2 values) → `LowCardinality(String)`.
  Tiny, stable set; no fixed-length guarantee either.
- **`geoip_country_code`** (7 values in this sample: `IN AE SG GB AU US SA`) →
  `LowCardinality(String)`, **not** `FixedString(2)` despite every sampled
  value being 2 chars. `tables/index.md`'s envelope documents this exact
  column platform-wide as `AE AU GB IN OM OTHER QA SA SG US` — the `OTHER`
  catch-all is a real, longer value used elsewhere for this column even
  though it doesn't appear in this spec's 7-value sample. A `FixedString(2)`
  column would corrupt or reject that bucket. `LowCardinality(String)` also
  matches D8's explicit instruction ("10 geos ... all tiny").
- **`city`** (7 values, e.g. `Mumbai`, `New York`, `Dubai`) →
  `LowCardinality(String)`. Variable length (`Dubai` 5 chars vs `New York` 8
  chars), genuinely low cardinality (0.1–10% unique depending on event) — the
  textbook `LowCardinality` case per the skill's own rule (city names, not
  fixed codes).
- **`destination`** (14 values in this sample, subset of the platform's 27
  ISO-2 codes) → `LowCardinality(String)`. The general skill would allow
  `FixedString(2)` for a confirmed 2-char code, but known_issues.md **D8**
  names `destination` by number ("27 destinations ... all tiny") as one of
  the columns to make `LowCardinality(String)` — a mandatory constraint for
  new tables — followed literally over the general skill default, for
  consistency with every other new-table categorical here and with spec 01.
- **`relation`** (`friend`/`spouse`/`child`/`sibling`/`parent`, 5 values,
  0.1–8.6% unique) → `LowCardinality(String)`, **not** `FixedString`: sampled
  byte lengths are ragged (`child`=5, `friend`/`spouse`/`parent`=6,
  `sibling`=7 — no uniform width). **Not `Enum8` either**: this is a live,
  newly-built product surface (spec.md describes a brand-new feature) and
  nothing in the wiki states the relation taxonomy is closed and versioned —
  per skill `schema-types-enum`, "values may change frequently →
  LowCardinality(String)" applies, matching the same reasoning spec 01 used
  to reject `Enum` for `saved_method_type`. An `Enum` here risks an
  insert-time rejection the moment product adds e.g. `partner` or `colleague`.
- **`group_id`** → `FixedString(32)`, a deliberate deviation from the
  otherwise-plain-`String` identifier style. Every sampled value shown in
  profile.md for `group_started`, `group_submitted`, and `traveller_removed`
  (e.g. `0061a57cf3164ee203747d0438adb47f`, `aaa29d595778f3fe8a13e2cef2fc454f`)
  is exactly 32 lowercase-hex characters — a raw, unhyphenated-UUID-shaped
  string, uniform across every sample with no ragged exception observed.
  Per the column-policy's join-key rule, `FixedString` is normally
  disqualified for identifiers because it null-pads short values and can
  silently mismatch a `String` counterpart — **but that rule exists to
  protect joins against an existing column** (`user_id`, `application_id`).
  `group_id` joins nothing outside this spec's own 4 new tables (it is a
  brand-new entity per `relationship.md` §"Entities the incoming specs will
  add"), so the policy's explicit carve-out ("`FixedString` is only
  permissible for keys that exist solely within this spec's new tables ...
  with justification") applies directly. Kept non-nullable: 100% present,
  0% null in every event. *Caveat:* this is inferred from a handful of
  displayed samples per event (the profiler omits the full list past ~10
  entries), not an exhaustive scan — if a future `group_id` deviates from 32
  hex chars, inserts will reject it; flagged in "Risks" below.
- **`group_size`** → `UInt8` (not a string decision, but noted here for
  completeness): int, range `[2, 6]`, distinct 5, 100% present, 0% null in
  every event → smallest integer type that fits (skill
  `schema-types-minimize-bitwidth`), non-nullable.

No column in this spec qualifies for `Enum8`/`Enum16`: per skill
`schema-types-enum`, Enum requires confidence that "no new value will appear
upstream without a schema change." Every categorical here (`device_type`,
`relation`, etc.) belongs to a brand-new feature still being built, so
treating any value set as closed and versioned would be an unfounded guess —
same conclusion spec 01 reached for its own categoricals.

## ORDER BY / PARTITION BY reasoning

All 4 tables use:
```
PARTITION BY toYYYYMM(timestamp)
ORDER BY (toDate(timestamp), group_size, group_id, id)
```

- `PARTITION BY toYYYYMM(timestamp)` matches the existing 8 baseline tables
  and spec 01, and stays well inside skill
  `schema-partition-low-cardinality`'s 100–1,000-partition guidance (the
  profiled sample spans 2026-06-08→2026-06-28, well under a handful of
  monthly partitions even extended to the platform's H1 2026 window).
- `ORDER BY` deliberately does **not** lead with `id` (a random UUID), per
  known_issues.md **D8**'s explicit instruction that new tables "must not
  inherit" that anti-pattern.
- `toDate(timestamp)` leads, per `schema-pk-cardinality-order`'s tip: every
  anticipated query (group completion trend, monthly rollups) filters at
  day/month granularity, not second precision.
- `group_size` is second (low cardinality — only 5 distinct values, `[2,6]`,
  in every event's profile), per `schema-pk-cardinality-order` (low
  cardinality early) and `schema-pk-prioritize-filters` (filter columns that
  exclude large fractions of rows): spec.md's own "Questions the PM will
  ask" cites group size **twice** — "Completion rate ... by group size —
  where do large groups fall off?" and "Is per-traveller document
  completion the bottleneck for **big groups**?" — more than any other
  dimension (`destination`/segments is asked once). This mirrors spec 01's
  method of substituting the PM's most-cited dimension for the D8 template's
  default second column.
- `group_id` is third — a spec-specific, higher-cardinality entity key
  needed for the PM's own cross-event questions ("how many travellers are
  added vs removed **per group**"), which require grouping/filtering by
  `group_id` across `traveller_added`/`traveller_removed`/`group_submitted`.
- **`user_id` is deliberately excluded from the key** — a deviation from
  spec 01's template, which kept `user_id` third. Evidence: in every one of
  the 4 profiled events, `group_id` and `user_id` have **identical distinct
  counts** (`group_started`: 1,200/1,200; `traveller_added`: 1,200/1,200;
  `traveller_removed`: 69/69; `group_submitted`: 688/688), meaning each
  group is owned by exactly one user in this dataset — the two columns are
  functionally collinear here, so including both would add ordering
  overhead without additional pruning benefit. `group_id` was kept over
  `user_id` because the PM's questions are phrased per-group, not per-user.
- `id` goes last — never filtered on, per `schema-pk-cardinality-order`'s
  "Last: High cardinality (if needed): event_id, uuid".
- 4 key columns total, within the skill's "4–5 key columns" guidance
  (`schema-pk-plan-before-creation`).

## Materialized view decision

**Not built.** All 4 source tables are small in the profiled sample (70–3,495
rows) — orders of magnitude below the 2,480,481-row baseline and below the
scale skill `query-mv-incremental` targets ("read thousands of rows instead
of billions... full aggregation on every dashboard load" scanning "billions
of rows"). Even the PM's most repeat-prone question — completion rate
(`group_started` → `group_submitted`) by `group_size` — is a `GROUP BY` over
at most 1,200 rows; a direct scan is already cheap, and pre-aggregating now
would add write-path complexity (a `-State`/`-Merge` AggregatingMergeTree
pair) for a query cost that isn't a problem yet. This is the same conclusion
and threshold spec 01 used for its own 836–1,650-row tables. If group-flow
volume grows to a meaningful share of the ~1,000,000-row top-of-funnel scale,
revisit an hourly/daily rollup MV for "completion rate by group_size" and
"add/remove churn per group" — at that point `query-mv-incremental`'s
incremental-aggregation pattern (`countState`/`uniqState` in the MV, `-Merge`
at query time) is the right template.

## Risks / caveats to carry forward

- **D2** — this spec's raw `application_id` is confirmed 32-char
  unhyphenated hex (e.g. `group_submitted`'s
  `007b4af7f2f0a42e11cfc48e8d04f37a`, verified 32 characters in profile.md),
  not the 36-char hyphenated UUID `application_started.application_id` uses.
  All 4 tables' `application_id` must be normalized on ingest (insert dashes
  at 8-4-4-4-12), and the mandatory overlap-check query from D2 must be run
  against `application_started` for each table before any cross-table join
  or funnel-lift analysis is trusted. Until that overlap check runs, treat
  group-flow-to-standard-funnel joins as unverified — spec 01's 5 tables all
  independently came back at **0.0%** overlap, so a 0% result here would not
  be a surprise and must be checked, not assumed away.
- **D1** — the PM's "completion rate (group_started → group_submitted) by
  group size" question is a funnel-shaped ask. Do not use
  `windowFunnel`/`sequenceMatch` for it without first running D1's
  monotonicity check (`countIf(t_later >= t_earlier) / count()`); the
  existing main funnel showed only 52.2% of `purchase_completed` rows
  post-date `document_uploaded`, so time-ordering must not be assumed for
  this new flow either. Use set-membership counts (D1's fix, valid here
  because `group_submitted`'s `group_id`s are a subset of `group_started`'s
  by construction) unless monotonic_share is verified ≥ ~0.99.
- **D8** — followed for physical layout on all 4 tables (see ORDER BY
  reasoning above); flagged here only so a reviewer can confirm none of the
  new tables reverted to the legacy `(id, timestamp, user_id)` key.
- **D9** — `device_type` mixes casing (`ios`, `android`, `web-user-b2c` vs
  `Desktop`) exactly as documented platform-wide; `destination` is UPPERCASE
  ISO-2. Any cross-table segment comparison must not assume case-normalized
  equality without checking first.
- **K7** — `app_version`'s 3 values here (`7.44.0`/`7.45.2`/`7.46.0`) carry
  no temporal signal platform-wide (confirmed uniform ~20% share every
  month); do not read a version-cut difference in group-flow adoption as a
  rollout effect.
- `relationship.md`'s "Entities the incoming specs will add" section flags
  that this spec's `Group` entity (`group_id`, `group_size`) "conflicts with
  the existing `co_travelers` column, which already models co-traveller
  count on the application" and instructs "reconcile before instrumenting;
  don't create a parallel model." This was checked: `group_size` and
  `travellers_submitted` live only in these 4 new tables (no column was
  added to or duplicated from `application_started`), so no parallel model
  of `co_travelers` was created at the schema level. However the semantic
  overlap is real and unresolved at the analysis layer — `co_travelers` is
  set once at `application_started` while `group_size`/`travellers_submitted`
  reflect the live group flow (travellers can be added/removed after
  `application_started` fires), so the two counts can legitimately diverge
  for the same `application_id`. Reconciling which figure is authoritative
  for "how many people are on this application" is analysis-layer work the
  Analytics Agent should do before comparing them, not something this schema
  can resolve by itself.
- `traveller_added` and `traveller_removed` do **not** follow the "one row
  per user" shape most baseline tables have (per D6's "no repeat users"
  finding on the *main* funnel). Evidence: `traveller_added` has 3,495 rows
  but only 1,200 distinct `user_id` (34.3% unique) — the same owning user
  legitimately generates multiple `traveller_added` rows (one per
  co-traveller added to their own group), and `traveller_removed` similarly
  has 70 rows over 69 distinct users (one user has 2 removal rows). This is
  expected given the feature (one group owner performs several add/remove
  actions), not a violation of D6's "no repeat users" claim about repeat
  *application-level* events — but an analyst assuming
  `uniqExact(user_id) == count()` on these two tables (true on every
  baseline table) would be wrong here; call this out explicitly in any
  group-flow analysis.
