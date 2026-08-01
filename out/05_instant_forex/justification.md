# Justification — Spec 05 Instant Forex Add-on

## Overview

| Object | Kind | Source event(s) | Rows | ORDER BY / key | Notes |
|---|---|---|---:|---|---|
| `forex_offer_shown` | CREATE TABLE | `forex_offer_shown` | 2,900 | `(destination, toDate(timestamp), user_id, id)` | Top-of-forex-funnel; carries `fx_rate`. |
| `currency_selected` | CREATE TABLE | `currency_selected` | 1,033 | `(destination, toDate(timestamp), user_id, id)` | Engagement step; no monetary fields. |
| `amount_entered` | CREATE TABLE | `amount_entered` | 1,033 | `(destination, toDate(timestamp), user_id, id)` | Adds `amount` (INR entered). |
| `forex_added_to_cart` | CREATE TABLE | `forex_added_to_cart` | 725 | `(destination, toDate(timestamp), user_id, id)` | Cart-commit moment; adds `addon_value_inr`. |
| `purchase_completed` (altered) | ALTER TABLE | `forex_purchased` | n/a (546 of 7,054 existing rows populate the new columns) | unchanged (`id, timestamp, user_id`, legacy) | Forex paid alongside the visa; 5 nullable `forex_*` columns added, mirroring `insurance_added`/`insurance_amount`. |
| — | MATERIALIZED VIEW | — | — | — | **Not built** — see below. |

---

## CREATE vs ALTER call, per event

- **`forex_offer_shown`** — the offer rendering is its own moment (page/UI render), not co-incident with any existing table's write. No existing table represents "an offer was shown." → **CREATE TABLE**, own grain.
- **`currency_selected`** — a distinct user-engagement action (picking a currency), separate in time from the offer render and from any existing event. → **CREATE TABLE**.
- **`amount_entered`** — the user typing an amount is a funnel/engagement step prior to any commitment, analogous to `landing_page_scrolled`/`search_typed` (supporting, pre-commitment events) in the existing 8 tables — no existing table shares this grain. → **CREATE TABLE**.
- **`forex_added_to_cart`** — "added to the order" is a cart-mutation moment. None of the 8 existing tables model a cart (no `pay_now_clicked`-equivalent for add-ons); it precedes payment and is not the same instant as `pay_now_clicked` (which fires when Pay Now is tapped, potentially covering the whole order including forex, at a later moment). No existing table shares this grain. → **CREATE TABLE**.
- **`forex_purchased`** — spec.md states the user "pays for it alongside the visa," i.e. at the exact moment `purchase_completed` fires (payment success). `purchase_completed.md` (context wiki) says explicitly: *"forex is not a novel pattern, it is a **third** add-on alongside insurance and plan tiers. It should be instrumented consistently with them."* That is a direct instrumentation instruction. `purchase_completed` already carries the peer pattern `insurance_added`/`insurance_amount` for exactly this kind of same-transaction add-on. → **ALTER TABLE purchase_completed ADD COLUMN** (no parallel table).

---

## `forex_offer_shown` / `currency_selected` / `amount_entered` / `forex_added_to_cart` (CREATE TABLE)

### Column choices

- **`id`, `timestamp`, `user_id`**: not nullable, per the envelope contract in `tables/index.md` ("`id` not nullable… `timestamp` not nullable… `user_id` not nullable, exactly 28 chars everywhere" — confirmed independently in `relationship.md`). `user_id` → `FixedString(28)` (not `LowCardinality`/`Enum`-eligible: 100% unique per profile.md, but the length is a confirmed constant, so `FixedString(28)` beats plain `String`, per the String-type decision rule #4).
- **`application_id`**: `Nullable(FixedString(36))`. Per known_issues.md **D2**, the spec's raw `application_id` arrives as 32-char unhyphenated hex (profile.md confirms `distinct: 2900/1033/725 (100% unique)`, sample values like `004fe3e8993c03e0973bbfcab2878f71` = 32 chars), but the live DB uses the 36-char hyphenated UUID. The ingestion path (client SDK → landing table) MUST normalize with:
  ```sql
  concat(substring(raw_id,1,8),'-',substring(raw_id,9,4),'-',substring(raw_id,13,4),
         '-',substring(raw_id,17,4),'-',substring(raw_id,21,12)) AS application_id
  ```
  so the stored value is always the 36-char hyphenated form — hence `FixedString(36)`, `Nullable` because other envelope-only events elsewhere in the platform sometimes carry no `application_id` (e.g. `destination_card_clicked` pre-application), even though this profile shows 100% presence for all 4 forex events. **Mandatory pre-deployment check (D2):**
  ```sql
  SELECT round(100.0 * uniqExactIf(application_id, application_id IN (
           SELECT application_id FROM clickathon.application_started))
         / uniqExact(application_id), 2) AS overlap_pct
  FROM clickathon.forex_offer_shown  -- repeat per new table
  ```
  If `overlap_pct` is 0%, stop and report as a finding rather than proceeding.
- **`device_type`, `os`, `app_version`, `client_lib`, `geoip_country_code`, `city`** → `LowCardinality(Nullable(String))`. All are confirmed low-cardinality in profile.md (e.g. `device_type`: distinct 4, 0.1–0.7% unique; `os`: distinct 4, 5.9–6.3% null; `app_version`: distinct 3; `client_lib`: distinct 2; `geoip_country_code`: distinct 7; `city`: distinct 7) — all well under the 1000-distinct/10%-of-present-rows `low_cardinality` gate, and all are **variable-length** strings (`New York`, `web-user-b2c`, `Mac OS X`, `Singapore`…), which per `schema-types-lowcardinality`'s own guidance ("reserve FixedString for strictly fixed-length data… for most low-cardinality text, LowCardinality outperforms FixedString") rules out `FixedString`. `os`/`city`/others are `Nullable` because profile.md shows nonzero null % for `os` (5.9–6.3%) and because the shared envelope documents these as `Nullable(String)` platform-wide.
- **`geoip_country_code`** is `LowCardinality`, **not `FixedString(2)`**, even though every sampled value here (`IN`, `SG`, `AE`, `US`, `GB`, `AU`, `SA`) is 2 chars: `tables/index.md`'s envelope page documents the full value set as `AE AU GB IN OM OTHER QA SA SG US`, which includes a 5-char `OTHER` catch-all bucket. That disqualifies fixed-width storage platform-wide even though it doesn't appear in this profile sample — a real future row could carry `OTHER` and break a `FixedString(2)` column.
- **`destination`** → `FixedString(2)`, unlike `geoip_country_code`. Profile.md shows 14 distinct values here, all clean 2-char ISO-2 codes (`GR`, `US`, `ID`, `TH`, `VN`…). `relationship.md`'s authoritative full list of all 27 destination values (`AE AU CA CH EG ES FR GB GR HK ID IT JP KR LK MA MV MY OM QA SA SG TH TR US VN ZA`) confirms **every** value is exactly 2 chars with **no catch-all bucket** (unlike `geoip_country_code`'s `OTHER`) — so `FixedString(2)` is safe here, per the String-type decision rule #1.
- **`from_currency`, `to_currency`** → `FixedString(3)`, not nullable. All observed values (`INR`, `EUR`, `USD`, `IDR`, `THB`, `VND`, `GBP`, `TRY`, `JPY`, `SGD`, `AUD`, `MYR`, `AED`, `EGP`, …) are exactly 3 characters — real ISO-4217 currency codes, a genuinely fixed-width format, no ragged exception observed across any of the 4 tables' profile sections. Per the String-type decision rule #1, this beats both `LowCardinality` (which the raw `low_cardinality` hint would suggest: `from_currency` distinct 1, `to_currency` distinct 13, both well under the ratio gate) and plain `String`. Not nullable: 100% presence in every event section of profile.md, and these are core payload fields of the event (not enrichment lookups like `city`/`geoip_country_code` that can legitimately fail), so `Nullable` is not semantically required — per `schema-types-avoid-nullable`.
- **`fx_rate`** (only on `forex_offer_shown`) → `Float64`, not nullable (100% present, range `[0.0379, 89.9827]` per profile.md — needs float precision, not an integer type). Kept `Float64` rather than `Decimal` to stay consistent with the existing platform's money/rate columns (`value`, `insurance_amount`, `discount_amount` are all `Float64` in `ddl.sql`) so the Analytics Agent doesn't have to cross-cast types when joining forex figures against existing revenue columns — a deliberate consistency choice, not an unexamined default.
- **`amount`** (on `amount_entered`, `forex_added_to_cart`) → `UInt16`, not nullable. Profile.md shows an integer range `[200, 1500]` with only 6 distinct values, 100% presence in both tables — comfortably fits `UInt16` (`schema-types-minimize-bitwidth`), and is a required payload field once the event fires.
- **`addon_value_inr`** (on `forex_added_to_cart`) → `Float64`, not nullable. Profile.md range `[4135.0, 134453.0]`, distinct 720/725 (99.3% unique) — a continuous money value, 100% present. Kept `Float64` for the same cross-table consistency reason as `fx_rate`.
- Envelope columns **not evidenced in this profile at all** (`app_session_id`, `device`, `geoip_subdivision_1_code`, `client_ip`, `latitude`/`longitude`, `locale`/`language`, `funnel_type`, `co_travelers`, `is_guest`/`is_referral`/`is_enterprise`, `gclid`/`fbclid`/`gad_source`, `citizenship`, `is_back_filled`, `duplicate_id`) are included at their **baseline type** (plain `Nullable(String)`/`Nullable(UInt8)`/`Nullable(Float64)`, matching `ddl.sql`'s existing convention) rather than upgraded, because the profiler reports **0% presence** for them in this event stream — there is no local statistic to justify a `LowCardinality`/`FixedString`/`Enum` choice, and inventing one would violate the "never guess" rule. They are still included because `spec.md` explicitly says "Envelope as usual," and `instrumentation_notes.md` confirms the client SDK auto-emits the full shared envelope on every table regardless of which fields end up populated for a given event. **Caveat carried forward:** confirm with the client SDK owner whether these columns are genuinely never populated for forex events (structural) or just outside this 6,237-row sample window.

### ORDER BY / PARTITION BY reasoning

`ORDER BY (destination, toDate(timestamp), user_id, id)`, `PARTITION BY toYYYYMM(timestamp)`:

- Per **`schema-pk-cardinality-order`**, low-cardinality columns lead. `destination` (14 distinct in this profile, 27 platform-wide) is lower cardinality than the ~20-day-to-6-month date range these tables will accumulate, so it leads, matching that rule's own worked example (`country` before `event_date`).
- Per **`schema-pk-prioritize-filters`**, `destination` is the PM's explicitly stated primary cut ("Attach rate… by `destination`," "Which destinations / currencies attach best") — it must be in the `ORDER BY` prefix or every attach-rate-by-destination query becomes a full scan.
- `toDate(timestamp)` next, per `schema-pk-cardinality-order`'s "date second" guidance and to support the time-window questions (drop-off trend, funnel-stage timing).
- `user_id` next (high cardinality, needed to join back to `application_started`/`purchase_completed` for the funnel/attach-rate questions) then `id` last.
- This explicitly avoids the **D8** trap: none of the 8 existing tables' `ORDER BY (id, timestamp, user_id)` pattern (random UUID leading) is repeated here — `id` is pushed to the tail per `known_issues.md` D8's explicit instruction that "new tables must not inherit this."
- `PARTITION BY toYYYYMM(timestamp)` kept consistent with the existing 8 tables (per `schema-partition-lifecycle`, time-aligned partitioning supports the same retention/drop-partition operations as the rest of the platform) and stays within `schema-partition-low-cardinality`'s 100–1,000-partition guidance (bounded to ~12/year). `schema-partition-start-without` was considered — the current sample is only ~6,237 rows over 20 days, arguably too small to need partitioning yet — but rejected in favor of matching the platform-wide lifecycle convention now, since the forex tables will accumulate on the same H1/H2 cadence as the other 8 and a later retro-fit of partitioning requires a table rebuild.

### Materialized view decision

**Not built**, for any of the 4 new tables individually. The PM's questions (attach rate, AOV distribution, drop-off location, destination/segment skew) require: (a) simple `uniqExact`/`count` set-membership joins across `forex_offer_shown` → `amount_entered`/`forex_added_to_cart` → the altered `purchase_completed` (same pattern as `known_issues.md` D1's funnel fix — a handful of scalar subqueries, not a repeated heavy aggregation), and (b) a distribution (`quantile`/histogram) over `addon_value_inr`, which needs to inspect raw values, not a pre-aggregate. Per `query-mv-incremental`, incremental MVs earn their keep when a query would otherwise "scan billions of rows" on every dashboard load; here the entire forex event volume is 6,237 rows across ~20 days — a full scan costs microseconds, so pre-aggregation buys nothing. Per `query-mv-refreshable`, refreshable MVs are for complex multi-table joins cached for sub-millisecond latency; the forex funnel is a small nested set-membership count, not a complex join. If forex volume grows by orders of magnitude and a live "attach-rate-by-destination-by-hour" dashboard tile is built, revisit with an incremental MV using `uniqState`/`uniqMerge`.

### Risks / caveats to carry forward

- **D2** (application_id format): mandatory overlap-check query above must be run against each new table before it is declared ready; if 0%, report as a finding and analyze the table standalone.
- **D9** (casing/vocabulary collisions): `destination` (UPPER) vs `citizenship` (lower) collision already exists platform-wide; not newly introduced here but any cross-column comparison in Analytics Agent queries must normalize case.
- **Entity conflict check** (`relationship.md`): the "Entities the incoming specs will add" section flags spec 02's `group_id`/`group_size` as conflicting with `co_travelers`, and spec 03's `share_id` as having no `user_id`. Spec 05 introduces no new entity beyond currency-pair/amount fields on the existing user/application grain — no conflict found.
- **D1** (`windowFunnel` unreliability): any attach-rate/funnel analysis across these 4 tables + `purchase_completed` must use set-membership counts, not `windowFunnel`/`sequenceMatch`, until monotonicity is verified per D1's `countIf(t_later >= t_earlier)` check.
- **Volume caveat**: this profile is a 20-day, 6,237-row sample (2026-06-08 to 2026-06-28) versus the platform's 6-month window — segment cuts (e.g. by `destination`) may have small per-cell counts; state n alongside any rate.

---

## `purchase_completed` (ALTER TABLE)

### Column choices

- **`forex_added`** → `Nullable(UInt8)` — mirrors `insurance_added`'s exact type (`Nullable(UInt8)` flag), per the explicit instruction to match the table's existing add-on typing convention rather than introduce a foreign style.
- **`forex_from_currency`, `forex_to_currency`** → `Nullable(String)`, **not** `FixedString(3)`. Even though the new standalone forex tables use `FixedString(3)` (a deliberate upgrade justified above), `purchase_completed` is one of the **8 existing production tables**, whose entire column set is plain `String`/`Nullable(String)` with no `LowCardinality`/`FixedString`/`Enum` anywhere (confirmed in `ddl.sql`). The task instructs matching "the SAME nullability/typing convention as that table's other add-on columns… so the new columns don't stick out as a foreign style in an otherwise-consistent table" — so these stay plain `Nullable(String)`, matching `plan_selected`/`coupon_name`.
- **`forex_amount`, `forex_addon_value_inr`** → `Nullable(Float64)`, mirroring `insurance_amount`'s exact type.
- **Naming**: prefixed `forex_*` rather than reusing bare `currency`/`value`/`amount` because `purchase_completed` already has `currency` (the visa payment's currency, 9 values `AED AUD GBP INR OMR QAR SAR SGD USD`) and `value` (the visa payment amount) — reusing those names for the forex leg would be exactly the kind of silent vocabulary collision flagged in **D9**, since the two pairs mean different things (visa payment currency vs. forex conversion currency pair) despite similar names.

### ORDER BY / PARTITION BY reasoning

N/A — `ALTER TABLE ADD COLUMN` does not change `purchase_completed`'s existing `ORDER BY (id, timestamp, user_id)` / `PARTITION BY toYYYYMM(timestamp)`. Per `schema-pk-plan-before-creation`, `ORDER BY` is immutable in ClickHouse — even though this table repeats the D8 anti-pattern (`id` leading), it cannot be fixed without a full rebuild/migration, and this task does not ask for a rebuild of an existing production table, only additive columns.

### Materialized view decision

**Not built.** The forex-attach-rate-vs-insurance-attach-rate comparison the context wiki calls for ("analysed against the 22.06% insurance attach rate as a baseline") is a one-time/periodic comparison (two `countIf`/`avg` aggregates over `purchase_completed`, 7,054 rows) — trivially cheap as a direct query, not a repeated dashboard load at scale that would justify `query-mv-incremental`, and not a multi-table join that would justify `query-mv-refreshable`.

### Risks / caveats to carry forward

- **D2**: `forex_purchased` rows carry `application_id` in the spec's 32-char unhyphenated form (profile.md confirms 100% present, 100% unique, 32-char samples like `004fe3e8993c03e0973bbfcab2878f71`). Since these values land as new columns on the *existing* `purchase_completed` table (already keyed by the DB's own 36-char hyphenated `application_id`), the ingestion pipeline that populates `forex_*` columns must match forex rows to `purchase_completed` rows via the **same normalization** as D2, then verify:
  ```sql
  SELECT round(100.0 * countIf(forex_added IS NOT NULL AND application_id IN (
           SELECT application_id FROM clickathon.application_started))
         / countIf(forex_added IS NOT NULL), 2) AS overlap_pct
  FROM clickathon.purchase_completed
  ```
  If this returns 0%, forex purchases cannot be joined to their applications and must be analyzed standalone (or via `user_id`, which is not subject to the D2 format mismatch).
- **D7** (revenue not aggregatable across 9 currencies): `forex_addon_value_inr` is explicitly INR-denominated (per its name and profile.md's `addon_value_inr` field, range up to 134,453), so — unlike `value` — it does **not** need a `GROUP BY currency` guard. But do not sum it together with `value` (which is multi-currency) without first converting `value` to INR or filtering `currency = 'INR'`.
- **Baseline (K2-style) risk**: 546 of 7,054 `purchase_completed` rows (7.7%) will have non-null `forex_*` columns; any `avg`/`sum` over these columns must use `countIf(forex_added = 1)` as the denominator, not `count()` over the whole table, to avoid diluting the attach-rate/AOV figures with the 92.3% of rows that never saw the add-on.
