---
id: metric.revenue_per_conversion
kind: metric
status: verified
confidence: medium
source: clickathon DB — purchase_completed GROUP BY currency
last_verified: 2026-08-01
links: [table.purchase_completed, contradiction.c12_revenue_currency_mixing, spec.05_instant_forex]
---

# Revenue per conversion

**Formula:** `value` on `purchase_completed`, **grouped by `currency`.**

## ⚠ Never aggregate without the currency group-by

Nine currencies with a ~150× magnitude spread and **no FX rate column anywhere**.
A global `avg(value)` or `sum(value)` returns a clean, meaningless number.
See [known_issues.md](../known_issues.md).

| Currency | Purchases | Avg value | Sum |
|---|---:|---:|---:|
| INR | 3,791 (53.7%) | 5,035.39 | 19,089,149 |
| AED | 1,163 | 306.22 | 356,132 |
| USD | 961 | 44.44 | 42,710 |
| GBP | 293 | 58.81 | 17,232 |
| AUD | 277 | 65.79 | 18,225 |
| SAR | 212 | 299.79 | 63,555 |
| QAR | 152 | 197.04 | 29,951 |
| OMR | 119 | 68.70 | 8,176 |
| SGD | 86 | 33.17 | 2,853 |

## Canonical query

```sql
SELECT currency, count() AS purchases, round(avg(value), 2) AS avg_value
FROM clickathon.purchase_completed
GROUP BY currency ORDER BY purchases DESC
```

For a single headline figure, report **INR only** (53.7% of purchases) and state
the scope. A blended number requires an FX dimension table that does not exist.

## `value` is not the whole order

`base_context.md` treats `value` as the revenue figure. The table also carries
**`insurance_amount`** (22.06% attach, avg 1,349.69) and **`discount_amount`**
(~500 avg on the 17.96% of orders with a coupon). True realised revenue per order
is closer to `value + insurance_amount`, and gross-vs-net depends on whether
`value` is pre- or post-discount — **undetermined; verify before reporting AOV.**

[Spec 05 Instant Forex](../known_issues.md) adds a third add-on and
introduces `addon_value_inr` (already INR-normalized) plus `fx_rate` — the
natural foundation for the missing FX dimension.
