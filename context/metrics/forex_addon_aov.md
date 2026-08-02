---
id: metric.forex_addon_aov
kind: metric
status: verified
confidence: medium
source: out/05_instant_forex/analysis/q02.md — verified addon_value_inr distribution among forex_purchased attachers and forex_added_to_cart cart-adders
last_verified: 2026-08-02
links: [table.forex_purchased, table.forex_added_to_cart, known_issue.d7_revenue_currency_unaggregatable, metrics.index]
---

# Instant Forex add-on AOV (`addon_value_inr`)

**Definition:** distribution of `forex_purchased.addon_value_inr` among
"attachers" — the 546 users who actually paid for the forex add-on. Live
query, all 546 rows, 100% `from_currency = INR` (no cross-currency mixing
per [D7](../known_issues.md#d7--revenue-is-unaggregatable-across-9-currencies)).
Spec 05 (Instant Forex Add-on) only.

## Distribution among attachers (`forex_purchased`, n=546)

| Stat | Value (INR) |
|---|---:|
| min | 4,245 |
| p10 | 10,188.5 |
| p25 | 16,560.75 |
| **median (p50)** | **31,685** |
| mean | 40,587.77 |
| p75 | 56,488.75 |
| p90 | 85,086 |
| p95 | 108,754.25 |
| max | 130,911 |
| population stddev | 30,415.32 |

Right-skewed: mean (₹40,588) sits well above median (₹31,685), driven by
a long tail of high-value add-ons up to ₹130,911. **Report median or a
trimmed measure, not mean, as the typical AOV uplift** — a bare mean
overstates the typical order.

## Pre-payment shape is nearly identical

`forex_added_to_cart` (n=725, users who added the add-on to cart whether
or not they went on to pay) shows a near-identical shape: min ₹4,135,
median ₹31,911, mean ₹39,601.71, max ₹134,453. The value distribution
does not shift meaningfully between "added to cart" and "actually paid" —
see [forex_added_to_cart.md](../tables/forex_added_to_cart.md).

## Caveats

- Single currency in this sample (`from_currency = INR`, 100% of rows);
  per D7, re-check the currency split before aggregating if a later
  sample introduces non-INR rows.
- This is the add-on's **own** value line only. No joined "with-addon vs.
  without-addon" order-total comparison against `purchase_completed.value`
  has been computed — per D2, `forex_purchased.application_id` has 0%
  overlap with `application_started`, so this flow cannot be joined to
  the main visa purchase to build such a comparison.
- Sample: `out/05_instant_forex` only, 2026-06-08 06:00 → 2026-06-28
  23:12.
