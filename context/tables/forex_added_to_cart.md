---
id: table.forex_added_to_cart
kind: table
status: verified
confidence: high
source: out/05_instant_forex/ddl.sql + justification.md (schema); out/05_instant_forex/load_report.md — rows loaded, D2 overlap_pct; out/05_instant_forex/analysis/q02.md — addon_value_inr distribution among cart-adders; out/05_instant_forex/analysis/q03.md — verified set-membership step-through both directions
last_verified: 2026-08-02
links: [doc.envelope, doc.relationship, known_issue.d2_application_id_join_format, known_issue.d1_windowfunnel_loses_conversions, tables.index, table.amount_entered, table.forex_purchased, metric.forex_addon_aov]
---

# `forex_added_to_cart`

Spec 05 (Instant Forex Add-on). Fires when the forex add-on is added to
cart, its own moment distinct from `amount_entered` and from
`purchase_completed`. → `CREATE TABLE`, not an `ALTER`. See
`out/05_instant_forex/justification.md` "CREATE vs ALTER call".

| | |
|---|---:|
| Rows | **725** (verified — `load_report.md`) |
| Distinct users | 725 (1 per user, per profile.md) |
| Distinct `application_id` | 725 (100% unique, per profile.md) |
| Sample time span | 2026-06-08 06:00 → 2026-06-28 23:12 (profile.md file-level span; not separately profiled per event) |
| Step-through ← `amount_entered` | 725 / 1,033 = **70.18%** — **verified** by set-membership join, per `analysis/q03.md`, 2026-08-02 |
| Step-through → `forex_purchased` | 546 / 725 = **75.31%** — **verified** by set-membership join, per `analysis/q03.md`, 2026-08-02 (this is the smaller of the funnel's two drops — 24.69%/179 users lost, vs. 64.38%/1,867 at `forex_offer_shown → currency_selected`) |

This table carries only a **subset** of the shared 30-column envelope (see
[the envelope](index.md)): `id`, `timestamp`, `user_id`, `application_id`,
`device_type`, `os`, `app_version`, `client_lib`, `geoip_country_code`,
`city`, `destination`.

| Column | Type | Values |
|---|---|---|
| `destination` | `FixedString(2)` | 14 values, e.g. `US`(76)/`TH`(61)/`GR`(60) |
| `from_currency` | `FixedString(3)` | single value across all rows: `INR` |
| `to_currency` | `FixedString(3)` | 13 values, e.g. `EUR`(112)/`USD`(76)/`THB`(61) — see [known_issues.md](../known_issues.md) → D7 |
| `amount` | `UInt16` | 100% present, 6 distinct values, range `[200, 1500]` |
| `addon_value_inr` | `Float64` | 100% present, 99.3% unique, range `[4135.0, 134453.0]` — the priced add-on value in INR; see D7 caveat below |

## AOV distribution nearly identical to `forex_purchased`

**2026-08-02 (source: `analysis/q02.md`).** Among all 725 users who add the
add-on to cart (whether or not they go on to pay): min ₹4,135, median
₹31,911, mean ₹39,601.71, max ₹134,453 — right-skewed, and **not
meaningfully different in shape** from `forex_purchased`'s attacher
distribution (median ₹31,685, mean ₹40,587.77) — see
[metrics/forex_addon_aov.md](../metrics/forex_addon_aov.md). The value
distribution does not shift between "added to cart" and "actually paid."

## ⚠ `application_id` does not join `application_started` — 0% overlap

`application_id` was normalized on ingest per D2. The mandatory D2
overlap-check then ran against `application_started` and returned
**`overlap_pct = 0.0%`** (verified — `load_report.md`, 2026-08-02) → per D2's
action table, **STOP**: analyse this table **standalone only**. See
[known_issues.md](../known_issues.md) → D2.

## Physical layout deviates from the 8 baseline tables — intentionally

`ENGINE = MergeTree`, `ORDER BY (toDate(timestamp), destination, user_id,
id)` — does not lead with the random `id` UUID, per known_issues.md D8. See
`justification.md` "ORDER BY / PARTITION BY reasoning".

## Other risks carried forward (see `justification.md` for full reasoning)

- **D1** — both step-through ratios above are now **verified** by set
  membership, per `analysis/q03.md`, 2026-08-02.
- **D2** — see above; `application_id` 0% overlap, standalone only.
  Independently re-confirmed by all 4 of `analysis/q01.md`–`q04.md`.
- **D6** — 725 rows, 725 distinct `user_id` — no repeat users.
- **D7** — `addon_value_inr` is a revenue-shaped field. `analysis/q02.md`
  confirms 100% of these 725 rows are `from_currency = INR`, so no
  cross-currency mixing occurred in this sample; report any AOV/uplift
  figure with its currency scope named explicitly regardless, per D7's
  "never aggregate `value` without `GROUP BY currency`" fix, in case a
  non-INR `from_currency` appears in a later sample.
- **D9** — `device_type` mixes casing exactly as documented platform-wide.
