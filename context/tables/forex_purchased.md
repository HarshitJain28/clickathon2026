---
id: table.forex_purchased
kind: table
status: verified
confidence: high
source: out/05_instant_forex/ddl.sql + justification.md (schema); out/05_instant_forex/load_report.md — rows loaded, D2 overlap_pct; out/05_instant_forex/analysis/q01.md — verified overall + by-destination attach rate; out/05_instant_forex/analysis/q02.md — addon_value_inr distribution among attachers; out/05_instant_forex/analysis/q03.md — verified full-funnel set membership; out/05_instant_forex/analysis/q04.md — verified monotonicity, currency/device/geo skew
last_verified: 2026-08-02
links: [doc.envelope, doc.relationship, known_issue.d2_application_id_join_format, known_issue.d1_windowfunnel_loses_conversions, tables.index, table.forex_added_to_cart, table.forex_offer_shown, metric.forex_attach_rate, metric.forex_addon_aov]
---

# `forex_purchased`

Spec 05 (Instant Forex Add-on). **The conversion event for this add-on** —
fires when the forex purchase is paid, "alongside the visa" per `spec.md`,
but instrumented as its **own client event**, not as attributes appended to
`purchase_completed`'s payload: it has its own row/moment, its own
`application_id` population, and its own event-specific fields
(`amount`, `addon_value_inr`), with a fully separate row count (546 vs.
`purchase_completed`'s 7,054) — not a 1:1 peer-attribute relationship. →
`CREATE TABLE`, not an `ALTER`. See
`out/05_instant_forex/justification.md` "CREATE vs ALTER call".

| | |
|---|---:|
| Rows | **546** (verified — `load_report.md`) |
| Distinct users | 546 (1 per user, per profile.md) |
| Distinct `application_id` | 546 (100% unique, per profile.md) |
| Sample time span | 2026-06-08 06:00 → 2026-06-28 23:12 (profile.md file-level span; not separately profiled per event) |
| Step-through ← `forex_added_to_cart` | 546 / 725 = **75.31%** — **verified** by set-membership join, per `analysis/q03.md`, 2026-08-02 |
| Overall attach rate ← `forex_offer_shown` (PM's headline question) | 546 / 2,900 = **18.83%** — **verified** by `uniqExact(user_id)` set-membership join (exact, no fan-out) and 100% timestamp monotonicity, per `analysis/q01.md` and `q04.md`, 2026-08-02; see [forex_offer_shown.md](forex_offer_shown.md) and [metrics/forex_attach_rate.md](../metrics/forex_attach_rate.md) |

This table carries only a **subset** of the shared 30-column envelope (see
[the envelope](index.md)): `id`, `timestamp`, `user_id`, `application_id`,
`device_type`, `os`, `app_version`, `client_lib`, `geoip_country_code`,
`city`, `destination`.

| Column | Type | Values |
|---|---|---|
| `destination` | `FixedString(2)` | 14 values, e.g. `US`(58)/`TH`(51)/`SG`(46) |
| `from_currency` | `FixedString(3)` | single value across all rows: `INR` |
| `to_currency` | `FixedString(3)` | 13 values, e.g. `EUR`(82)/`USD`(58)/`THB`(51) — see [known_issues.md](../known_issues.md) → D7 |
| `amount` | `UInt16` | 100% present, 6 distinct values, range `[200, 1500]` |
| `addon_value_inr` | `Float64` | 100% present, 99.6% unique, range `[4245.0, 130911.0]` — the paid add-on value in INR; the PM's AOV-uplift question runs off this column, see D7 caveat below |

## Attach rate: verified, with a real ~11pp spread by `destination`

**2026-08-02 (source: `analysis/q01.md`, `q04.md`).** Overall attach rate
546/2,900 = **18.83%** is confirmed (not a ratio artifact) by a live
`uniqExact(user_id)` join, exact with no fan-out, plus 100% timestamp
monotonicity across all 546 matched pairs. By `destination` (n=174–240
offers each): best **US** 24.58%, SG 23.12%, TH 22.87% — worst **AU**
13.78%, VN 14.29%, TR 14.78% — about 11pp spread, no obvious geographic
clustering. Device skew is mild (ios best 19.77%, web-user-b2c worst
17.08%, ~2.7pp spread); geo skew mild-to-moderate (AE best 21.51%, GB
worst 15.11%, ~6.4pp spread across 7 observed geos; India alone is 61.7%
of all offers shown, so the pooled 18.83% figure is effectively
India-weighted). `to_currency` tracks `destination` almost exactly, except
**EUR blends two destinations** (FR 20.41% + GR 17.5%) into one 18.81%
figure — report currency-level attach rates with this caveat. See
[metrics/forex_attach_rate.md](../metrics/forex_attach_rate.md) for the
full breakdown.

## AOV among attachers: right-skewed, median ₹31,685

**2026-08-02 (source: `analysis/q02.md`).** Distribution of
`addon_value_inr` across all 546 `forex_purchased` rows (100%
`from_currency = INR`, no cross-currency mixing per D7): min ₹4,245,
median ₹31,685, mean ₹40,587.77, max ₹130,911, population stddev
₹30,415.32. Mean sits well above median — a long tail of high-value
add-ons drives it up, so **median (not mean) is the safer "typical AOV
uplift" figure to report.** Nearly identical shape to
[forex_added_to_cart](forex_added_to_cart.md)'s pre-payment distribution
(median ₹31,911) — the value doesn't shift between cart-add and payment.
See [metrics/forex_addon_aov.md](../metrics/forex_addon_aov.md).

## ⚠ `application_id` does not join `application_started` — 0% overlap

`application_id` was normalized on ingest per D2. The mandatory D2
overlap-check then ran against `application_started` and returned
**`overlap_pct = 0.0%`** (verified — `load_report.md`, 2026-08-02) → per D2's
action table, **STOP**: analyse this table **standalone only**, the same
verdict specs 01–04 all got. See [known_issues.md](../known_issues.md) →
D2.

## Physical layout deviates from the 8 baseline tables — intentionally

`ENGINE = MergeTree`, `ORDER BY (toDate(timestamp), destination, user_id,
id)` — does not lead with the random `id` UUID, per known_issues.md D8. See
`justification.md` "ORDER BY / PARTITION BY reasoning".

## Other risks carried forward (see `justification.md` for full reasoning)

- **D1** — both step-through ratios above, including the PM's headline
  attach-rate metric, are now **verified** by set membership
  (`uniqExact(user_id)` across `forex_offer_shown`/`forex_purchased`,
  after confirming 100% timestamp monotonicity, per D1's fix) — see
  `analysis/q01.md`, `q03.md`, `q04.md`, 2026-08-02.
- **D2** — see above; `application_id` 0% overlap, standalone only.
  Independently re-confirmed by all 4 of `analysis/q01.md`–`q04.md`, none
  of which found a working `application_id` path — every finding above is
  scoped to the forex flow standalone.
- **D6** — 546 rows, 546 distinct `user_id` — no repeat users. Retention/
  repeat-attach questions about the same user across multiple forex
  purchases cannot be answered from this data.
- **D7** — `addon_value_inr` is a revenue-shaped field. `analysis/q02.md`
  confirms 100% of these 546 rows are `from_currency = INR`, so the AOV
  figures above are single-currency and not mixed; report any AOV/uplift
  figure with its currency scope named explicitly regardless, per D7's
  "never aggregate `value` without `GROUP BY currency`" fix, in case a
  non-INR `from_currency` appears in a later sample. This table is *not*
  `purchase_completed` and its `addon_value_inr` should not be summed
  together with `purchase_completed.value` without stating that these are
  two separate revenue lines — no such joined comparison has been
  computed (`analysis/q02.md`'s scope note).
- **D9** — `device_type` mixes casing exactly as documented platform-wide.
