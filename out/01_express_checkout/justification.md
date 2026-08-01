# Justification — Spec 01 Express Checkout

## Overview

| Object | Kind | Source event(s) | Rows | ORDER BY / key | Notes |
|---|---|---|---:|---|---|
| `express_checkout_shown` | CREATE TABLE | `express_checkout_shown` | 1,650 | `(device_type, toDate(timestamp), user_id, id)` | Own grain: button render moment |
| `express_checkout_selected` | CREATE TABLE | `express_checkout_selected` | 1,007 | `(device_type, toDate(timestamp), user_id, id)` | Own grain: tap moment |
| `saved_method_used` | CREATE TABLE | `saved_method_used` | 1,007 | `(device_type, toDate(timestamp), user_id, id)` | No event-specific fields in profile — envelope only |
| `otp_entered` | CREATE TABLE | `otp_entered` | 1,007 | `(device_type, toDate(timestamp), user_id, id)` | NOT merged into `pay_now_clicked` — see below |
| `express_payment_confirmed` | CREATE TABLE | `express_payment_confirmed` | 836 | `(device_type, toDate(timestamp), user_id, id)` | Nested `payment.*` flattened |
| — | MATERIALIZED VIEW | — | n/a | n/a | **Not built** — see decision below |

No `ALTER TABLE` statements were emitted for this spec.

---

## CREATE vs ALTER call (per event)

All five events were evaluated against the "same moment/grain as an existing table" test from the instrumentation brief.

- **`express_checkout_shown`, `express_checkout_selected`, `saved_method_used`, `otp_entered`, `express_payment_confirmed`** — each is a distinct step in a brand-new client flow with its own timestamp and its own row count (1650 → 1007 → 1007 → 1007 → 836, a strictly narrowing funnel), not an attribute bolted onto an existing table's row. `instrumentation_notes.md`'s stated convention ("one table per event, auto-created by the client event SDK") applies directly. **→ CREATE TABLE** for all five.

- **Special consideration: `otp_entered` vs `pay_now_clicked`.** `tables/pay_now_clicked.md` explicitly says *"Spec 01 Express Checkout adds `otp_attempts` / `otp_success`, the first instrumentation able to explain [the 47.86% pay-intent leak]."* This is the kind of sentence the brief says to treat as a direct instruction, so it was weighed as a possible ALTER candidate. It was rejected because the grain doesn't match: `pay_now_clicked` has 14,739 rows (one per "Pay Now" tap, any payment method) while `otp_entered` has 1,007 (one per OTP submission, Express-only flow — a subset of users with a saved method). These are not the same occurrence at the same moment; Express users skip the full payment form entirely (per spec.md, "reuses the saved method, collects only an OTP"), so there is no `pay_now_clicked` row for an Express payment to attach an OTP column to. The context-page sentence is read as *narrative* pointing at what this spec instruments, not as an instruction to co-locate the columns on the old table. **→ kept as its own `CREATE TABLE otp_entered`.**

- **Special consideration: `express_payment_confirmed` vs `purchase_completed`.** Both represent "payment succeeds," but field sets differ entirely (nested `payment.amount/currency/latency_ms` vs `purchase_completed`'s `value/currency/coupon_*/insurance_*/plan_selected`), row counts differ (836 vs 7,054 total purchases), and no context page instructs a merge (unlike the `purchase_completed.md` sentence that *does* instruct spec 05's forex add-on to join that table). Absent that instruction here, forcing Express confirmations into `purchase_completed` would silently null out most of that table's add-on columns for every Express row and vice versa. **→ kept as its own `CREATE TABLE express_payment_confirmed`.**

- Checked `relationship.md`'s "Entities the incoming specs will add" section for entity conflicts (it flags spec 02's `group_id` vs `co_travelers`, spec 03's `share_id`): spec 01 introduces no new entity of that kind (`saved_method_type`, `otp_*`, `payment.*` are attributes of the checkout step, not a new joinable entity), so no conflict to reconcile here.

---

## Column choices

Columns included are exactly the union of fields the profiler observed present per event, plus `id`/`timestamp`/`user_id` (implied by the profile header — `rows`, `id_duplicates: 0`, `unparseable_timestamps: 0` are computed over every row, so both exist and parse on 100% of rows). No column from the shared 30-column envelope that the profiler did **not** report (e.g. `app_session_id`, `funnel_type`, `co_travelers`, `is_guest`, `gclid`, `citizenship`, `latitude`/`longitude`, `locale`, `is_back_filled`, `duplicate_id`) was invented — this spec's raw envelope subset is narrower than the full 30 columns, and the brief prohibits adding fields not in spec or profile.

### `id`, `timestamp`
`UUID` / `DateTime`, NOT NULL — matches the envelope convention (`tables/index.md`); confirmed present/parseable on 100% of rows via the profile header's `id_duplicates: 0, unparseable_timestamps: 0`.

### `user_id`
`String` NOT NULL. 100% present, 0% null on every event (profile: `distinct: N (100% unique)` where N = row count, i.e. no nulls, no blanks). Kept plain `String`, not `FixedString`, because — unlike `relationship.md`'s stated fact for the *existing* 8 tables ("exactly 28 characters everywhere") — this profile does not report a length statistic for this spec's `user_id`, so a fixed length cannot be asserted from evidence in hand. Per `schema-types-avoid-nullable`, NOT NULL because presence is 100%/0% null across all 5 events.

### `application_id`
`String` NOT NULL (post-D2-normalization), not `Nullable`. Profile shows 100% present, 0% null across **all five** events (e.g. `express_payment_confirmed`: `distinct: 836 (100% unique)` out of n=836). Unlike the shared envelope's `Nullable(String)` (which is nullable because pre-application events like `destination_card_clicked` legitimately lack it), every event in this spec fires only after a user has an application and reaches checkout, so the evidence supports NOT NULL — an application of `schema-types-avoid-nullable`. **D2 applies**: sampled values are 32-char unhyphenated hex (e.g. `000c06bc633c33a6c2c656f9194702a8`, confirmed in `express_payment_confirmed`'s profile row), so ingestion MUST normalize with
```sql
concat(substring(raw_id,1,8),'-',substring(raw_id,9,4),'-',substring(raw_id,13,4),
       '-',substring(raw_id,17,4),'-',substring(raw_id,21,12)) AS application_id
```
before load. **Mandatory pre-deployment overlap check** (adapted from D2), run once per new table before declaring it ready:
```sql
SELECT round(100.0 * uniqExactIf(application_id, application_id IN (
         SELECT application_id FROM clickathon.application_started))
       / uniqExact(application_id), 2) AS overlap_pct
FROM clickathon.express_checkout_shown
-- repeat for express_checkout_selected, saved_method_used, otp_entered, express_payment_confirmed
```
Per D2's table: >90% → proceed; 1–90% → proceed but state coverage in every insight; 0% → stop, report as finding, analyze standalone.

### `device_type`
`LowCardinality(String)` NOT NULL. 100% present every event, 4 distinct values (`ios`, `android`, `web-user-b2c`, `Desktop`) with the profiler's `LC` hint (well under the 10K/10% threshold in `schema-types-lowcardinality`). Not `FixedString` — values are variable-length and not a fixed-format code (mixed casing per D9, `Desktop` vs `ios`). Not `Enum` — `client_lib`/`device_type` values already mix casing conventions (D9), a sign the upstream vocabulary isn't tightly governed; an Enum would reject a legitimately-emitted new casing variant at insert time.

### `os`
`LowCardinality(Nullable(String))`. Every event shows <100% presence within the "present" bucket — profiler reports e.g. `os | 100% (6.8% null) | string:1538` for `express_checkout_shown` — i.e. the field is always sent but is null 6.8–7.4% of the time depending on event, mirroring the shared envelope's own `os` column (`Nullable(String)`, "5.95% NULL" per `tables/index.md`). Nullable here is semantic (per `schema-types-avoid-nullable`'s own example set — `os` unknown is a real state, not a default-able 0/''). 4 distinct values, LC hint → `LowCardinality`.

### `app_version`
`LowCardinality(String)` NOT NULL. 100% present, 3 distinct values in-sample (`7.45.2`, `7.44.0`, `7.46.0`), all 6 characters. Rejected `FixedString(6)` despite every sampled value being 6 chars: unlike ISO country/currency codes, semantic-versioning strings are not a *permanently* fixed-width format — a future minor/patch reaching double digits (`7.100.0`, `7.9.10`) would exceed 6 chars and break ingestion. `LowCardinality(String)` per `schema-types-lowcardinality`'s explicit guidance ("reserve FixedString for strictly fixed-length data... for most low-cardinality text, LowCardinality outperforms FixedString"). Also recall K7: `app_version` carries no temporal signal and is assigned uniformly at random — a caveat carried forward for any analysis, not a schema concern.

### `client_lib`
`LowCardinality(String)` NOT NULL. 100% present, 2 distinct (`mobile-rn`, `web-js`), LC hint.

### `geoip_country_code`
`LowCardinality(String)` NOT NULL, **not** `FixedString(2)`. 100% present, 7 distinct values in-sample, all 2-char ISO codes (`IN`, `AE`, `SG`, `US`, `AU`, `GB`, `SA`). Even though every value observed here is 2 chars, `tables/index.md` documents that this exact column carries a 5-char `OTHER` catch-all value elsewhere in the shared pipeline (`geoip_country_code | ... | AE AU GB IN OM OTHER QA SA SG US`) — the disqualifying case the brief specifically warns to check for. Since this spec reuses the same geoip enrichment pipeline as the other 8 tables, that catch-all is a live risk even though it didn't appear in this 5,507-row sample. `LowCardinality(String)` chosen over `FixedString`.

### `city`
`LowCardinality(String)` NOT NULL. 100% present, 7 distinct (`Mumbai`, `Dubai`, `Singapore`, `New York`, `Sydney`, `London`, `Riyadh`), LC hint. Genuinely variable-length free-form city names → rule 2 of the string-type decision (LowCardinality, not FixedString/Enum).

### `destination`
`FixedString(2)` NOT NULL. 100% present every event, values in-sample are 2-char ISO-2 codes (`JP`, `AU`, `US`, `SG`, `FR`, `GB`, `AE`, `TH`, `ID`, `TR`, etc.). Unlike `geoip_country_code`, `relationship.md` documents this column's **complete** value set as exactly 27 fixed 2-char ISO-2 codes with **no catch-all bucket** mentioned anywhere (`AE AU CA CH EG ES FR GB GR HK ID IT JP KR LK MA MV MY OM QA SA SG TH TR US VN ZA` — all 2 chars). This is the genuine "real fixed-format code" case the brief calls out (ISO country codes) — `FixedString(2)` chosen per `schema-types-lowcardinality`'s FixedString carve-out.

### `currency` (on `express_checkout_shown`) / `payment_currency` (on `express_payment_confirmed`)
`FixedString(3)` NOT NULL. 100% present, values (`INR`, `AED`, `SGD`, `USD`, `AUD`, `GBP`, `SAR`) are all exactly 3 characters — standard ISO-4217 codes, matching `purchase_completed.currency`'s known 9-value set (`AED AUD GBP INR OMR QAR SAR SGD USD`, all 3 chars). No catch-all documented for this column anywhere in the wiki (unlike `geoip_country_code`). `FixedString(3)` per the same rule as `destination`.

### `eligible`
`UInt8 DEFAULT 1` NOT NULL. 100% present, but only ever `true` in-sample (`distinct: 1 (0.1% unique) — true(1650)`) — the event semantically only fires for eligible users, so the "false" branch simply never emits an event. Kept as a UInt8 flag (matching the envelope's `is_guest`/`is_referral` 0/1 convention) rather than dropped, in case a future client version starts logging ineligible impressions too; `DEFAULT 1` reflects the only value ever observed.

### `shown_amount`
`Float64` NOT NULL. 100% present, 89.6% unique, range `[1502.0, 9000.0]` — matches the `Float64` convention used for money elsewhere (`purchase_completed.value`, `pay_now_clicked.amount`).

### `saved_method_type`
`LowCardinality(String)` NOT NULL. 100% present, 3 distinct (`card`, `upi`, `wallet`), LC hint. Considered `Enum8('card'=1,'upi'=2,'wallet'=3)` since the set looks closed today, but rejected: the closely-related `pay_now_clicked.payment_method` column (same conceptual field, one table over) already carries **5** values (`applePay`, `card`, `netbanking`, `upi`, `wallet`) — direct evidence that this vocabulary grows over time in this codebase. An Enum would break ingestion the day `applePay`/`netbanking` support is added to Express. Per `schema-types-enum`'s own guidance table ("values may change frequently → LowCardinality(String)").

### `otp_attempts`
`UInt8` NOT NULL. 100% present, range `[1, 3]`, 3 distinct — fits `UInt8` (0–255) with large headroom; per `schema-types-minimize-bitwidth`, no reason to use a wider int.

### `otp_success`
`UInt8` NOT NULL (0/1). 100% present, boolean with 2 distinct values (`true(937)`, `false(70)`) — no nulls, so kept NOT NULL unlike the envelope's `is_*` flags (which are `Nullable(UInt8)` because they're not always known). Matches numeric-flag convention used throughout the existing 8 tables.

### `payment_amount`
`Float64` NOT NULL. 100% present, range `[1509.0, 8997.0]`, 95.6% unique — same convention as `shown_amount`/`purchase_completed.value`.

### `payment_latency_ms`
`UInt16` NOT NULL. 100% present, range `[607, 3999]` — fits comfortably under `UInt16`'s 65,535 ceiling; `UInt32` would be wasted width per `schema-types-minimize-bitwidth`.

---

## ORDER BY / PARTITION BY reasoning (all 5 tables)

`ORDER BY (device_type, toDate(timestamp), user_id, id)`, `PARTITION BY toYYYYMM(timestamp)`, `ENGINE = MergeTree`.

- **D8 compliance**: none of the new tables repeat `ORDER BY (id, timestamp, user_id)`. `id` (a random UUID) is moved to the *last* position, matching D8's own prescribed fix and `schema-pk-cardinality-order`'s "Last: High cardinality (event_id, uuid)" guidance.
- **`device_type` leads**, per `schema-pk-cardinality-order` ("Order columns low-to-high cardinality") and `schema-pk-prioritize-filters` ("prioritize columns frequently used in query filters"): it's the lowest-cardinality column with 0% nulls (4 values, always present — unlike `os`, which has the same cardinality but 6–7% nulls, making it a weaker leading key), and it's the segment cited twice in the spec's "Questions the PM will ask" (platform-level OTP/confirmation-rate cuts; adoption by device).
- **`toDate(timestamp)` second**, per `schema-pk-cardinality-order`'s explicit tip ("use `toDate(timestamp)` instead of raw `DateTime`... reduces index size from 32-bit to 16-bit") and because most PM questions are time-scoped (e.g. rollout trend, latency over time).
- **`user_id` third**: higher cardinality than `device_type`/date, but the primary join key for every cross-table funnel question (per `relationship.md`'s join map) and per `schema-pk-prioritize-filters`.
- **`id` last**: highest cardinality, kept only as a final tie-breaker, never a filter target — matches `schema-pk-cardinality-order`'s ordering table.
- **`PARTITION BY toYYYYMM(timestamp)`** kept identical to the existing 8 tables: the spec's 3-week sample and the live DB's 6-month window both bound this to a handful of partitions, well inside `schema-partition-low-cardinality`'s 100–1,000-value healthy range.

---

## Materialized view decision

**Not built.** The spec's "Questions the PM will ask" are (1) checkout→success conversion lift vs standard checkout, (2) OTP/confirmation-rate cuts by device/os/geo, (3) latency, (4) segment adoption. All four require joining across `express_checkout_shown` → ... → `express_payment_confirmed` (and, for question 1, against `pay_now_clicked`/`purchase_completed` too) using **set-membership** counts per D1 (windowFunnel/sequenceMatch are known to silently drop conversions on this dataset — D1 is a hard rule regardless of which tables are involved). `query-mv-incremental` frames its case around aggregations that would otherwise "scan billions of rows... every dashboard load"; these five tables sample at 836–1,650 rows each, so a plain `GROUP BY`/`uniqExact` query already runs in milliseconds and re-scanning the raw table on every query is not the billions-of-rows problem the rule is written for. An incremental MV also only accumulates *new* inserts (per the rule's "existing data not automatically included" caveat) and would need a manual backfill anyway, while the cross-table nature of every PM question here doesn't fit `query-mv-incremental`'s single-stream aggregation shape (a cross-table `query-mv-refreshable`-style view was also considered and rejected for the same reason: refreshable MVs suit expensive scheduled joins, but these joins are still cheap at this row count). **If and when this feature's production volume grows into the hundreds of thousands of rows/day**, revisit an hourly rollup (`toStartOfHour(timestamp), device_type` grain, `AggregatingMergeTree`) — flagged here as a forward note, not built now for lack of evidence it's needed.

---

## Risks / caveats to carry forward

- **D2 (application_id format)**: mandatory overlap-check query above must be run against `application_started` before any of these 5 tables is joined into a funnel; if `overlap_pct` comes back 0%, stop and report standalone per D2's table.
- **D1 (windowFunnel/sequenceMatch)**: any funnel analysis spanning `express_checkout_shown → ... → express_payment_confirmed` (or into `pay_now_clicked`/`purchase_completed`) must use set-membership counts, not `windowFunnel`, and should first verify monotonicity within these new tables (`countIf(t_later >= t_earlier)/count()`, D1's guard) before trusting timestamp order — do not assume it holds just because it wasn't disproven for the 8 existing tables.
- **D9 (casing/vocabulary collisions)**: `device_type` here reuses the same mixed-casing values (`ios`, `Desktop`) as the existing envelope; `destination` is UPPERCASE while `citizenship` (not in this spec, but relevant if joined against `application_started`) is lowercase — normalize case before any cross-column comparison.
- **K1 (iOS WebKit OTP regression) is REFUTED** (`known_issues.md`) — do not attribute any iOS `otp_success`/confirmation-rate gap found in this new data to K1 without re-deriving it; `pay_now_clicked.md` explicitly says these new `otp_attempts`/`otp_success` columns are "the first instrumentation able to explain [K1's claimed mechanism] directly" — treat this as an open question to re-test, not a foregone conclusion either way.
- **Entity check (relationship.md)**: `saved_method_type` and the `payment.*` fields introduce no new joinable entity (no `group_id`/`share_id`-style key), so no conflict with `co_travelers` or other existing columns — confirmed, not just assumed.
- **Volume caveat**: all row counts above are from the profiler's sample (5,507 rows total, 2026-06-08 to 2026-06-28); production volume and the true `express_checkout_shown → express_payment_confirmed` step-through rate should be re-measured once real traffic lands, the same way `tables/index.md`'s step-through percentages were derived for the 8 existing tables.
