# Justification — Instant Forex Add-on (spec 05)

## Overview

| Object | Kind | Source event(s) | Rows | ORDER BY / key | Notes |
|---|---|---|---:|---|---|
| `forex_offer_shown` | CREATE TABLE | `forex_offer_shown` | 2,900 | `(toDate(timestamp), destination, user_id, id)` | Origin of the forex funnel; only table carrying `fx_rate` |
| `currency_selected` | CREATE TABLE | `currency_selected` | 1,033 | `(toDate(timestamp), destination, user_id, id)` | No `amount`/`addon_value_inr` (not in profile for this event) |
| `amount_entered` | CREATE TABLE | `amount_entered` | 1,033 | `(toDate(timestamp), destination, user_id, id)` | Adds `amount` |
| `forex_added_to_cart` | CREATE TABLE | `forex_added_to_cart` | 725 | `(toDate(timestamp), destination, user_id, id)` | Adds `addon_value_inr` |
| `forex_purchased` | CREATE TABLE | `forex_purchased` | 546 | `(toDate(timestamp), destination, user_id, id)` | **Conversion event** for this add-on |

No `ALTER TABLE` and no `MATERIALIZED VIEW` were produced for this spec — see the
per-object sections below for why.

---

## CREATE vs ALTER call

All 5 spec events (`forex_offer_shown`, `currency_selected`, `amount_entered`,
`forex_added_to_cart`, `forex_purchased`) are **new occurrences at their own
grain** — each fires at a distinct moment in the checkout flow (offer render →
currency engagement → amount entry → cart add → payment), each is its own row
with its own `id`/`timestamp`, and none of them coincide with the moment an
existing baseline table's event fires. In particular:

- `forex_purchased` is *not* the same row/moment as `purchase_completed`. The
  spec describes forex as paid "alongside the visa" (a bundled checkout
  experience), but it is instrumented as its own client event with its own
  fields (`amount`, `addon_value_inr`) rather than as attributes appended to
  `purchase_completed`'s payload — the profiler shows it as a fully separate
  event type with its own row count (546, vs. `purchase_completed`'s 7,054),
  so it is not a 1:1 peer-attribute relationship.
- None of the 5 events' fields are described in `spec.md` as arriving on an
  existing table's row; each is its own named client event.

This matches `instrumentation_notes.md`'s stated convention — "one table per
event, auto-created by the client event SDK" — so all 5 get `CREATE TABLE`,
none get `ALTER TABLE`.

**No new entity/key was minted.** Unlike spec 02 (`group_id`) and spec 03
(`share_id`), this spec's 5 tables join each other purely via the existing
envelope columns `user_id` and `application_id` — the same topology
`relationship.md` describes for spec 04 (Recovery). No spec-local
`FixedString` key was introduced for this reason.

---

## Column choices

Columns are exactly the fields the profiler shows per event (see the Field ×
Event Grid in `profile.md`) plus the mandatory envelope keys (`id`,
`timestamp`, `user_id`, `application_id`). No column absent from `profile.md`
(e.g. `app_session_id`, `latitude`/`longitude`, `locale`/`language`,
`funnel_type`, `co_travelers`, `is_guest`/`is_referral`/`is_enterprise`,
`gclid`/`fbclid`/`gad_source`, `citizenship`, `is_back_filled`,
`duplicate_id`, `geoip_subdivision_1_code`, `client_ip`, `device`) was added,
even though the 8 baseline tables carry them — this spec's raw sample simply
does not emit them. (Note, not a known-issues citation: if the client SDK is
expected to add these later, that is a follow-up schema migration, not
something to guess into this DDL now.)

- **`id`, `timestamp`, `user_id`**: not nullable, matching the envelope
  (`id`/`timestamp`/`user_id` are non-null on all 8 baseline tables per
  `tables/index.md`); `user_id` is 100% present with `distinct == row count`
  on every one of the 5 tables (e.g. 2,900/2,900 on `forex_offer_shown`),
  consistent with `known_issues.md` → **D6** (no repeat users) rather than an
  invented assumption.
- **`application_id`**: `Nullable(String)`, matching `application_started`'s
  type exactly, per the rule that join keys must match the type of the
  column they join to — even though this spec's sample shows 100% presence
  (no nulls), `Nullable(String)` is kept for join-type compatibility, not
  local null-rate evidence. **The sampled values are 32-char unhyphenated
  hex** (e.g. `004fe3e8993c03e0973bbfcab2878f71`), the exact shape
  `known_issues.md` → **D2** flags as the format that fails to join
  `application_started`'s 36-char hyphenated UUIDs — see Risks below.
- **`device_type`**: `LowCardinality(String)`, not nullable (profiler shows
  100% present, no null% noted). 4 distinct values
  (`ios`/`android`/`web-user-b2c`/`Desktop`), well under the low-cardinality
  hint's 1,000-absolute/10%-of-present threshold. Not `FixedString` — values
  are variable-length (`ios`=3 chars vs `web-user-b2c`=12 chars). Not `Enum`
  — per the skill's `schema-types-enum` guidance, Enum needs confidence the
  set is closed and none of the 8 production tables use Enum for this exact
  column; mismatch risk (a 5th device type appearing) isn't worth the
  insert-time validation here.
- **`os`**: `LowCardinality(Nullable(String))` — profiler shows "100%
  (6.1%-6.3% null)" across all 5 events, matching the envelope's documented
  "5.95% NULL" for `os` (`tables/index.md`), so `Nullable` is semantically
  required here (unlike `device_type`). 4 distinct values
  (`iOS`/`Android`/`Mac OS X`/`Windows`) → low-cardinality hint fires.
- **`app_version`**: `LowCardinality(String)`, not nullable (100% present,
  no null%). 3 distinct values in every event's profile
  (`7.44.0`/`7.45.2`/`7.46.0`) — hint fires. Per `known_issues.md` → K7, this
  column carries no temporal signal; that doesn't change its type, just a
  caveat for analysis.
- **`client_lib`**: `LowCardinality(String)`, not nullable. 2 distinct
  values (`mobile-rn`/`web-js`) — hint fires strongly (0.1-0.3% unique).
- **`geoip_country_code`**: `LowCardinality(String)`, not nullable. Sample
  shows 7 distinct values (`IN`/`SG`/`AE`/`US`/`GB`/`AU`/`SA`), all 2 chars —
  looks `FixedString`-eligible at first glance, **but** `tables/index.md`'s
  envelope documents this column's full platform-wide domain as `AE AU GB IN
  OM OTHER QA SA SG US` — the `OTHER` bucket is a real, longer value used
  elsewhere on the platform for this same column, even though this spec's
  sample didn't happen to draw it. Per the String-type decision rules, this
  disqualifies `FixedString` outright; `LowCardinality(String)` is used
  instead.
- **`city`**: `LowCardinality(String)`, not nullable. 7 distinct values
  (`Mumbai`/`Singapore`/`Dubai`/`New York`/`London`/`Sydney`/`Riyadh`),
  visibly variable-length (`Dubai`=5 chars vs `New York`=8 chars) — hint
  fires and `FixedString` is not applicable (ragged lengths).
- **`destination`**: `FixedString(2)`, not nullable. All 14 sampled values
  (`GR`/`US`/`ID`/`TH`/`VN`/`GB`/`TR`/`JP`/`SG`/`AU`/…) are exactly 2 chars,
  and `relationship.md`'s full documented domain (27 destinations: `AE AU
  CA CH EG ES FR GB GR HK ID IT JP KR LK MA MV MY OM QA SA SG TH TR US VN
  ZA`) is **also** uniformly 2 chars with no `OTHER`-style exception recorded
  anywhere for this specific column (unlike `geoip_country_code`). This is
  exactly the "real fixed-format code: ISO country codes" case the skill's
  `schema-types-lowcardinality.md` calls out ("Reserve FixedString for
  strictly fixed-length data (e.g., 2-char country codes)") — a deliberate,
  checked upgrade over the LowCardinality-for-every-categorical pattern used
  by specs 01-04, not a reflexive default.
- **`from_currency`** / **`to_currency`**: `FixedString(3)`, not nullable.
  `from_currency` is a single value (`INR`) across all 6,237 rows; `to_currency`
  has 13 distinct values (`EUR`/`USD`/`IDR`/`THB`/`VND`/`GBP`/`TRY`/`JPY`/
  `SGD`/`AUD`/`AED`/`EGP`/`MYR`), every one exactly 3 chars — the skill's own
  example list for `FixedString` names "ISO currency codes" directly. No
  `OTHER`-style catch-all is documented anywhere in the wiki for a currency
  column (the closest analogue, `purchase_completed.currency`, is described
  in `known_issues.md` → D7 as "9 currencies, no FX rate" with no mention of
  a catch-all bucket), so the trap that disqualified `geoip_country_code`
  does not apply here.
- **`fx_rate`** (`forex_offer_shown` only): `Float64`, not nullable. Profiler
  reports it as `float:2900` (100% present) with range `[0.0379, 89.9827]` —
  a 4-order-of-magnitude spread (weak-currency rates like INR→VND sit near
  the low end, INR→JPY-style rates near the high end) that needs `Float64`'s
  precision; matches the envelope's own use of `Float64` for other
  continuous numeric fields (`latitude`/`longitude`).
- **`amount`** (`amount_entered`, `forex_added_to_cart`, `forex_purchased`):
  `UInt16`, not nullable. Profiler shows `int:1033`/`int:725`/`int:546`
  (100% present in each), range `[200, 1500]` — exceeds `UInt8`'s 255 max,
  so per the skill's `schema-types-minimize-bitwidth` guidance the smallest
  type that fits is `UInt16`.
- **`addon_value_inr`** (`forex_added_to_cart`, `forex_purchased`):
  `Float64`, not nullable. Profiler reports `float:725`/`float:546` (100%
  present), ranges `[4135.0, 134453.0]` and `[4245.0, 130911.0]` — kept as
  the observed `float` JSON type rather than guessed down to an integer.

**Nullable columns are minimized versus the baseline's all-`Nullable`
style** (`os`/`application_id` only) — a deliberate application of the
skill's `schema-types-avoid-nullable` rule (HIGH impact), justified per
column by the profiler's explicit null percentages (or lack thereof), not an
unexamined default.

---

## ORDER BY / PARTITION BY reasoning

All 5 tables use:

```
ENGINE = MergeTree
PARTITION BY toYYYYMM(timestamp)
ORDER BY (toDate(timestamp), destination, user_id, id)
```

- **`PARTITION BY toYYYYMM(timestamp)`**: matches every existing table
  (baseline + specs 01-04) and stays within the skill's
  `schema-partition-low-cardinality` bound (100-1,000 partitions) — the
  spec's 3-week sample plus a full-year deployment horizon yields at most a
  few dozen monthly partitions.
- **`toDate(timestamp)` leads**, not the random `id` UUID — this is D8's
  mandatory fix ("new tables must not inherit" the baseline's
  `(id, timestamp, user_id)` defeated-index pattern) and its own worked
  example is literally `ORDER BY (toDate(timestamp), destination, user_id,
  id)`. It also satisfies `schema-pk-prioritize-filters` (time-range is the
  near-universal filter for funnel/attach-rate analysis) and the skill's own
  tip under `schema-pk-cardinality-order` to prefer `toDate(timestamp)` over
  raw `DateTime` for index compactness.
- **`destination` second**: the spec's own PM questions name it explicitly
  — "Attach rate: … overall and by `destination`" and "Which destinations …
  attach best" — making it the highest-value segment filter, and it is
  low-cardinality (14 observed / 27 platform-wide) per
  `schema-pk-cardinality-order`. This mirrors the established convention
  (spec 01 → `device_type`, spec 02 → `group_size`, spec 03 → `status_shared`/
  `channel`/`destination`, spec 04 → `drop_step`/`channel`) of substituting
  the PM's most-cited dimension as the second sort key.
- **`user_id` third, `id` last**: matches the skill's cardinality-order
  guideline (medium-high, then highest-cardinality last) and lets any
  per-user analysis (e.g. joining `forex_offer_shown` → `forex_purchased`
  on `user_id`, per D6/D1's set-membership fix) use the index.

---

## Materialized view decision

**Not proposed.** The skill's `query-mv-incremental` rule frames incremental
MVs as a fix for aggregations that would otherwise "scan 7 days of data
every time (billions of rows)" — reading pre-aggregated thousands of rows
instead of billions. This spec's tables top out at 2,900 rows
(`forex_offer_shown`) down to 546 (`forex_purchased`); a live `GROUP BY
destination` over the full table is already a sub-second scan of a few
thousand granule-sized rows. Building an `AggregatingMergeTree` + MV here
would add ingestion-path complexity (background merge overhead, `-State`/
`-Merge` function discipline) with no read-latency problem to solve at this
volume. If this add-on's volume grows by orders of magnitude, the attach-rate
and AOV-by-destination queries named in `spec.md` would be the natural
first incremental-MV candidates to revisit.

---

## Risks / caveats to carry forward

- **D2** — `application_id` on all 5 tables is present as sampled 32-char
  unhyphenated hex (e.g. `004fe3e8993c03e0973bbfcab2878f71`), the exact
  format `known_issues.md` documents as failing to join
  `application_started`'s 36-char hyphenated UUIDs with zero rows and no
  error. Every one of specs 01-04 hit `overlap_pct = 0.0%` on this same
  check. **Before any deployment or analysis is trusted**, run the mandatory
  D2 normalize-and-verify query against all 5 new tables; until that runs,
  treat this add-on as a standalone flow not joinable to the main funnel via
  `application_id`.
- **D6** — all 5 tables show `distinct(user_id) == row count` in
  `profile.md` (e.g. 546/546 on `forex_purchased`), consistent with the
  platform-wide "no repeat users" pattern. Retention/repeat-attach questions
  about the *same* user across multiple forex purchases cannot be answered
  from this data and should be refused with an explanation, not answered
  with zeros.
- **D8** — this spec's sort key intentionally does **not** replicate the
  baseline's `(id, timestamp, user_id)` pattern that defeats the primary
  index; see "ORDER BY / PARTITION BY reasoning" above for the fix applied.
- **D9** — `device_type` values observed here (`Desktop`, `ios`, `android`,
  `web-user-b2c`) reproduce the exact case-mixing `known_issues.md` flags
  (`Desktop` vs `ios`) — any cross-table `device_type` comparison or
  aggregation must normalize case first, the same fix D9 prescribes.
- **D1** — the spec's headline "attach rate: `forex_offer_shown` →
  `forex_purchased`" question is a multi-step funnel exactly like the ones
  D1 warns about. Compute it by `uniqExact(user_id)` set membership across
  the two tables (and check monotonicity of `timestamp` first, per D1's
  guidance for new feature tables — `countIf(t_later >= t_earlier) /
  count()`), **not** `windowFunnel`/`sequenceMatch`, which is documented to
  silently discard up to 52% of true conversions on this platform's data.
- **D7** — `addon_value_inr` is a revenue-shaped field; although
  `from_currency` is INR-only in this sample (100% of rows), the spec's own
  AOV-uplift question should still be reported with its currency scope
  named explicitly, consistent with D7's "never aggregate `value` without
  `GROUP BY currency`" fix, in case a non-INR `from_currency` appears later.

No entity or column conflict with `relationship.md` was found: this spec
introduces no new entity (unlike Group/`group_id` or Share/`share_id`) and
its `user_id`/`application_id` usage matches the existing join map exactly,
the same pattern `relationship.md` describes for spec 04 (Recovery).

Also worth flagging (not yet a `known_issues.md` entry): unlike the 8
baseline tables, none of this spec's 5 raw events carry `duplicate_id` or
`is_back_filled` — the two undocumented data-quality envelope columns. This
may simply mean the client SDK hasn't wired them into this newer event
family yet; if so, a later `ALTER TABLE ... ADD COLUMN` would be the right
fix once observed, not a column invented now.
