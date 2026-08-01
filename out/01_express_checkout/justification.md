# Justification — Spec 01: Express Checkout

## Overview

| Object | Kind | Source event(s) | Rows | ORDER BY / key | Notes |
|---|---|---|---:|---|---|
| `express_checkout_shown` | CREATE TABLE | `express_checkout_shown` | 1,650 | `(toDate(timestamp), device_type, user_id, id)` | Top of the express flow; button rendered. |
| `express_checkout_selected` | CREATE TABLE | `express_checkout_selected` | 1,007 | `(toDate(timestamp), device_type, user_id, id)` | User taps Express. |
| `saved_method_used` | CREATE TABLE | `saved_method_used` | 1,007 | `(toDate(timestamp), device_type, user_id, id)` | No event-specific columns observed — envelope subset only. |
| `otp_entered` | CREATE TABLE | `otp_entered` | 1,007 | `(toDate(timestamp), device_type, user_id, id)` | First instrumentation able to test K1 directly. |
| `express_payment_confirmed` | CREATE TABLE | `express_payment_confirmed` | 836 | `(toDate(timestamp), device_type, user_id, id)` | Conversion event for the express flow; nested `payment.*` flattened. |
| — | ALTER TABLE | none | n/a | — | No event in this spec shares a moment/grain with an existing table (see below). |
| — | MATERIALIZED VIEW | none | n/a | — | Not built — see "Materialized view decision". |

All 5 tables: `ENGINE = MergeTree`, `PARTITION BY toYYYYMM(timestamp)`.

---

## CREATE vs ALTER call

Per event, checked against every existing table's column list in `ddl.sql` and
`instrumentation_notes.md`'s "one table per event, auto-created by the client
event SDK" convention:

- **`express_checkout_shown`** — fires when the Express button is rendered at
  checkout, before any tap. No existing table writes a row at this moment
  (`pay_now_clicked` only fires on the *standard* Pay Now tap). → **CREATE TABLE**.
- **`express_checkout_selected`** — fires when the user taps Express. This is
  a distinct occurrence from `pay_now_clicked` (a different button, on a
  different flow that explicitly *skips* the standard payment form per
  spec.md's "What it does") — not the same moment as any existing row-write.
  → **CREATE TABLE**.
- **`saved_method_used`** — the saved instrument being loaded is a new
  occurrence with no analogue in the 8 existing tables. → **CREATE TABLE**.
- **`otp_entered`** — OTP submission is a new occurrence. `pay_now_clicked.md`
  notes spec 01 "adds `otp_attempts`/`otp_success`, the first instrumentation
  able to explain" the payment leak, but that is a statement about analytical
  value, not an instruction to alter `pay_now_clicked` — nothing in
  `pay_now_clicked`'s column list or `instrumentation_notes.md` describes OTP
  fields as attributes attached to the Pay Now tap; they belong to their own
  step, with their own timestamp, in the express flow. → **CREATE TABLE**.
- **`express_payment_confirmed`** — payment success in the express flow.
  Distinct row population from `purchase_completed` (own `application_id`
  set, own nested `payment.*` shape) and no context-wiki sentence ties it to
  `purchase_completed`'s grain the way `purchase_completed.md` explicitly ties
  spec 05 (Instant Forex) to its add-on columns ("should be instrumented
  consistently with them"). No such sentence exists for spec 01. → **CREATE TABLE**.

No ALTER candidates were found for this spec.

## Column policy

Columns are exactly the fields profile.md shows present for each event (Field
× Event Grid). Envelope fields not observed for any of the 5 events —
`app_session_id`, `device`, `geoip_subdivision_1_code`, `client_ip`,
`latitude`/`longitude`, `locale`/`language`, `funnel_type`, `co_travelers`,
`is_guest`/`is_referral`/`is_enterprise`, `gclid`/`fbclid`/`gad_source`,
`citizenship`, `is_back_filled`, `duplicate_id` — are **not** added, per the
column policy (an unobserved column is an invented column). This means
`saved_method_used` carries no event-specific columns at all: profile.md
shows it has zero fields beyond the 9 common ones (`app_version`,
`application_id`, `city`, `client_lib`, `destination`, `device_type`,
`geoip_country_code`, `os`, `user_id`) plus the envelope's `id`/`timestamp`
row identity.

## Column choices (all 5 tables share the same envelope subset)

- **`id UUID`, `timestamp DateTime`** — structural row identity/time, implied
  by profile.md's per-event `id_duplicates: 0` and file-level `time_span`,
  matching the existing tables' convention. Not nullable (existing tables'
  convention; also skill `schema-types-avoid-nullable`).
- **`user_id String`** — 100% present, 0% null in every event's profile row,
  100% unique per event (own grain). Matches the existing tables' exact
  `user_id String` type (join-key type match, `relationship.md` §1/§3).
- **`application_id Nullable(String)`** — 100% present in this spec's sample
  with no null noted, but typed `Nullable(String)` anyway to match
  `application_started.application_id`'s exact type, because this is the
  join key back into the main funnel (`relationship.md` §3 join map) — per
  the join-key-type-matching rule, join keys must match the existing
  column's type even when local nullability looks avoidable.
  **Critical caveat:** see risks below — **D2**.
- **`device_type`, `os`, `app_version`, `client_lib`, `geoip_country_code`,
  `city`, `destination`** — see "String-type decision" below.
- Event-specific columns:
  - `shown_amount Float64` (`express_checkout_shown`) — 100% present, 89.6%
    unique, continuous range [1502.0, 9000.0]; matches the existing
    money-column convention (`value`/`amount`/`insurance_amount` are all
    `Float64` in `ddl.sql`). Non-nullable: 0% null observed.
  - `currency` (`express_checkout_shown`) — see String-type decision.
  - `saved_method_type` (`express_checkout_selected`) — see String-type
    decision.
  - `otp_attempts UInt8` (`otp_entered`) — range [1, 3], distinct 3; `UInt8`
    is the smallest type that fits (skill `schema-types-minimize-bitwidth`).
    Non-nullable: 100% present, 0% null.
  - `otp_success Bool` (`otp_entered`) — boolean, distinct 2 (true/false),
    100% present, 0% null → `Bool` non-nullable (skill
    `schema-types-native-types`: "Booleans → Bool or UInt8, avoid String").
  - `payment_amount Float64`, `payment_currency`, `payment_latency_ms UInt16`
    (`express_payment_confirmed`) — profile.md's dotted `payment.amount` /
    `payment.currency` / `payment.latency_ms` are flattened to underscored
    typed columns rather than left as JSON, per skill
    `schema-json-when-to-use`: this is a fixed, known 3-field shape (not a
    dynamic schema), so "use typed columns" applies, not the JSON type.
    `payment_latency_ms` range is [607, 3999] → `UInt16` (smallest type that
    fits comfortably above the observed max, skill
    `schema-types-minimize-bitwidth`). Both non-nullable: 100% present, 0%
    null.
  - `eligible Bool` (`express_checkout_shown`) — profiled at 100% presence,
    distinct 1 (`true` only). spec.md's prose only calls out `shown_amount`/
    `currency` for this event, but the column policy is "exactly the fields
    observed in profile.md", and `eligible` is a real, 100%-present field in
    the profiler's grid — so it is included as non-nullable `Bool` rather
    than silently dropped for not matching the spec's prose description.

## String-type decision (per column)

- **`device_type`** (`ios`/`android`/`web-user-b2c`/`Desktop`, 4 values,
  0.2–0.5% unique across events) → `LowCardinality(String)`. Ragged casing
  (`Desktop` vs `ios`) rules out `FixedString`; low, stable cardinality plus
  known_issues.md **D8**'s explicit instruction ("`LowCardinality(String)`
  for all categoricals ... 4 device types ... — all tiny") makes
  `LowCardinality(String)` the direct call. Non-nullable: 100% present, 0%
  null in every event.
- **`os`** (`iOS`/`Android`/`Mac OS X`/`Windows`, 4 values) →
  `LowCardinality(Nullable(String))`. Same cardinality argument as
  `device_type`, but profile.md shows a genuine null rate (6.8–7.4% per
  event, consistent with the existing envelope's 5.95% null) — nullability
  here is semantic (SDK didn't report OS), not just "no data seen yet", so
  `Nullable` is kept per skill `schema-types-avoid-nullable`'s carve-out.
- **`app_version`** (`7.45.2`/`7.44.0`/`7.46.0`, 3 values, 0.2–0.4% unique) →
  `LowCardinality(String)`, not `FixedString`. All three sampled values are
  the same length (6 chars), but there is no wiki statement guaranteeing the
  version string format is permanently fixed-width (a future two-digit patch
  release, e.g. `7.47.10`, would be 7 chars) — the "confirmed fixed length"
  bar from the string-type policy isn't met, so `LowCardinality(String)` is
  the safe low-cardinality choice, matching D8's spirit.
- **`client_lib`** (`mobile-rn`/`web-js`, 2 values) → `LowCardinality(String)`.
  Tiny, stable set; no fixed-length guarantee either.
- **`geoip_country_code`** (7 values in this sample: `IN AE SG US AU GB SA`) →
  `LowCardinality(String)`, **not** `FixedString(2)` despite every sampled
  value being 2 chars. `tables/index.md`'s envelope documents this exact
  column platform-wide as `AE AU GB IN OM OTHER QA SA SG US` — the `OTHER`
  catch-all is a real, longer value used elsewhere for this column even
  though it doesn't appear in this spec's 7-value sample. A `FixedString(2)`
  column would corrupt or reject that bucket. `LowCardinality(String)` also
  matches D8's explicit instruction ("10 geos ... all tiny").
- **`city`** (7 values, e.g. `Mumbai`, `New York`) → `LowCardinality(String)`.
  Variable length (`Dubai` vs `New York`), genuinely low cardinality (0.4–0.8%
  unique) → the textbook `LowCardinality` case per the skill's own rule
  (city/country *names*, not fixed codes).
- **`destination`** (14 values in this sample, subset of the platform's 27
  ISO-2 codes) → `LowCardinality(String)`. The general skill would allow
  `FixedString(2)` for a confirmed 2-char code, but known_issues.md **D8**
  names `destination` by number ("27 destinations ... all tiny") as one of
  the columns to make `LowCardinality(String)`, and this is a known_issues.md
  mandatory constraint for new tables — followed literally over the general
  skill default, for consistency with every other new-table categorical here.
- **`currency`** / **`payment_currency`** (7 values in each sample: `INR AED
  SGD USD AUD GBP SAR`, all ISO-3 codes) → `LowCardinality(String)`. Same D8
  reasoning as `destination`/`geoip_country_code`: D8 explicitly names "9
  currencies — all tiny" as a `LowCardinality(String)` categorical; followed
  literally rather than switching to `FixedString(3)`, both for D8-compliance
  and because `purchase_completed.currency`/`pay_now_clicked.currency` (the
  columns these will eventually be compared against in cross-flow analysis)
  are plain `Nullable(String)` with no fixed-length guarantee documented
  anywhere in the wiki.
- **`saved_method_type`** (`card`/`upi`/`wallet`, 3 values, 0.3% unique) →
  `LowCardinality(String)`. Genuinely small closed-looking set, but **not**
  `Enum8`: `pay_now_clicked.payment_method` (the closest existing analogue)
  has a *different*, larger domain (`applePay`/`card`/`netbanking`/`upi`/
  `wallet`) that isn't closed across the platform, and skill
  `schema-types-enum`'s guidance is "values may change frequently →
  LowCardinality(String)" — an `Enum` here risks an insert-time rejection the
  moment Express adds a new saved-method type (e.g. `applePay`), a real cost
  for no proven benefit over `LowCardinality`.

No column in this spec qualifies for `Enum8`/`Enum16`: per skill
`schema-types-enum`, Enum requires confidence that "no new value will appear
upstream without a schema change." Every categorical here (`device_type`,
`saved_method_type`, `currency`, etc.) is a live product surface still being
built (spec.md is describing a brand-new feature), so treating any of their
value sets as closed and versioned would be an unfounded guess.

## ORDER BY / PARTITION BY reasoning

All 5 tables use:
```
PARTITION BY toYYYYMM(timestamp)
ORDER BY (toDate(timestamp), device_type, user_id, id)
```

- `PARTITION BY toYYYYMM(timestamp)` matches the existing 8 tables and stays
  well inside skill `schema-partition-low-cardinality`'s 100–1,000-partition
  guidance (6 months of data → 6 partitions).
- `ORDER BY` deliberately does **not** lead with `id` (a random UUID), unlike
  the 8 existing tables — known_issues.md **D8** is explicit that new tables
  "must not inherit" that anti-pattern, and gives the template
  `(toDate(timestamp), destination, user_id, id)`.
- This spec substitutes `device_type` for `destination` as the second key,
  per skill `schema-pk-prioritize-filters` ("prioritize columns frequently
  used in query filters") and `schema-pk-cardinality-order` (low cardinality
  first): spec.md's own "Questions the PM will ask" name `device_type`/`os`
  twice ("Is there a platform where OTP / payment fails more... Cut
  `otp_success` and confirmation rate by `device_type`/`os`/
  `geoip_country_code`" and "Which segments adopt Express most (device,
  geo, saved-method type)"), never `destination` — `device_type` is the
  higher-value filter column for this spec's actual queries, and unlike
  `os` it has 0% null in every event, so it also indexes cleanly.
- `toDate(timestamp)` (not raw `DateTime`) leads per
  `schema-pk-cardinality-order`'s tip, since every anticipated query
  (funnel trend, monthly rollups) filters at day/month granularity, not
  second precision.
- `user_id` before `id`: both are ~100%-unique per table, but `user_id` is a
  genuine cross-table join/filter column (`relationship.md` §3); `id` is
  never filtered on, so it goes last per `schema-pk-cardinality-order`'s
  "Last: High cardinality (if needed): event_id, uuid".
- 4 key columns total, within the skill's "4–5 key columns" guidance
  (`schema-pk-plan-before-creation`).

## Materialized view decision

**Not built.** Every source table here is small in the profiled sample
(836–1,650 rows) — orders of magnitude below the 2,480,481-row baseline the
8 existing tables carry, and below the scale skill `query-mv-incremental`
targets ("read thousands of rows instead of billions... full aggregation on
every dashboard load" scanning "billions of rows"). A direct `GROUP BY`
against any of these 5 tables is already a cheap full scan; pre-aggregating
now would add write-path complexity (a `-State`/`-Merge` AggregatingMergeTree
pair per rollup) for a query cost that isn't a problem yet. If Express
Checkout volume grows to be a large share of the ~1,000,000-row top-of-funnel
scale, revisit an hourly/daily rollup MV for the "checkout → success
conversion" and "OTP/payment failure by platform" cuts — at that point
`query-mv-incremental`'s incremental-aggregation pattern (`countState`/
`uniqState` in the MV, `-Merge` at query time) is the right template.

## Risks / caveats to carry forward

- **D2** — the raw application_id in this spec's NDJSON is the 32-char
  unhyphenated hex form (confirmed directly in profile.md's
  `express_payment_confirmed.application_id` sample, e.g.
  `000c06bc633c33a6c2c656f9194702a8`, verified 32 characters), not the
  36-char hyphenated UUID `application_started.application_id` uses. All 5
  tables' `application_id` must be normalized on ingest (insert dashes at
  8-4-4-4-12), and the mandatory overlap-check query from D2 must be run
  against `application_started` for each table before any cross-table join
  or funnel-lift analysis is trusted. Until that overlap check runs, treat
  express-checkout-to-standard-funnel joins as unverified.
- **D1** — do not use `windowFunnel`/`sequenceMatch` across
  `express_checkout_shown → ... → express_payment_confirmed` (or against
  `pay_now_clicked`/`purchase_completed`) without first running D1's
  monotonicity check (`countIf(t_later >= t_earlier) / count()`); the
  existing funnel showed only 52.2% of `purchase_completed` rows post-date
  `document_uploaded`, so time-ordering must not be assumed for this new
  funnel either. Use set-membership counts (D1's fix) unless monotonic_share
  is verified ≥ ~0.99.
- **D8** — followed for physical layout on all 5 tables (see ORDER BY
  reasoning above); flagged here only so a reviewer can confirm none of the
  new tables silently reverted to the legacy `(id, timestamp, user_id)` key.
- **D7** — `shown_amount`, `payment_amount` span the same multi-currency set
  as `purchase_completed.value` (`currency`/`payment_currency` show 7 codes
  in this sample, a subset of the platform's 9). Never `sum`/`avg` these
  without `GROUP BY currency`/`payment_currency`.
- **D9** — `device_type` mixes casing (`ios`, `android`, `web-user-b2c` vs
  `Desktop`) exactly as documented platform-wide; any cross-table
  segment-adoption comparison must not assume case-normalized equality.
- **D6** — every event in this profile has exactly one row per `user_id`
  (e.g. `express_checkout_shown`: 1,650 rows, 1,650 distinct `user_id`); no
  repeat users. Any "does a user retry Express after a failed OTP" question
  is therefore unanswerable from this dataset and should be refused with an
  explanation, not answered with a join that silently returns zero repeats.
- **K1** — refuted (iOS is the *best*-converting high-volume platform on the
  existing `pay_now_clicked → purchase_completed` step, especially in the
  Gulf). `otp_entered`/`express_payment_confirmed` are the first columns able
  to test the underlying mechanism directly — analyze `otp_success` and
  confirmation rate by `os` on their own merits, but do not frame any result
  as confirming or refuting K1 by association; test it fresh.
- `relationship.md` §1 ("Entities the incoming specs will add") was checked
  for conflicts: unlike spec 02 (`group_id` vs `co_travelers`) and spec 03
  (`share_id` with no `user_id`), spec 01 introduces no new entity — Express
  Checkout is instrumented as a sequence of events against the existing
  `Application`/`User` entities, so no parallel model was created.
  `relationship.md` §3's join map should be extended, once D2's normalization
  is verified, to include these 5 tables' `application_id` alongside
  `document_uploaded`/`pay_now_clicked`/`purchase_completed`.
- New observation (not yet a known_issues.md entry): `saved_method_type`'s
  observed domain (`card`/`upi`/`wallet`) is a strict subset of
  `pay_now_clicked.payment_method`'s domain (`applePay`/`card`/`netbanking`/
  `upi`/`wallet`) — Express appears not to support Apple Pay or netbanking
  today. Worth confirming with product before reading "Express adoption by
  saved-method type" against the full standard-checkout payment-method mix,
  since the two columns are not directly comparable 1:1.
- New observation: in this sample, `otp_entered` has 1,007 rows but
  `express_payment_confirmed` has only 836 — a 171-row (17%) drop, while
  `otp_success = false` accounts for only 70 of those rows. There is an
  unexplained ~101-row gap between a successful OTP and a confirmed payment
  that no column here currently explains; worth surfacing to the Analytics
  Agent as the express-flow analogue of the existing unexplained
  `pay_now_clicked → purchase_completed` leak.
