---
id: table.purchase_completed
kind: table
status: verified
confidence: high
source: clickathon DB — system.tables, system.columns, profiling queries
last_verified: 2026-08-01
links: [doc.envelope, metric.revenue_per_conversion, metric.funnel_conversion, contradiction.c12_revenue_currency_mixing, spec.05_instant_forex]
---

# `purchase_completed`

Funnel stage 4 — **the conversion event.**

| | |
|---|---:|
| Rows | **7,054** |
| Distinct users / applications | 7,054 |
| Time range | 2026-01-01 01:39:27 → 2026-07-01 00:08:53 |
| Step-through from `pay_now_clicked` | **47.86%** |
| Application → purchase | **4.57%** |

Envelope: see [the envelope](index.md). Event-specific columns below.

| Column | Type | Notes |
|---|---|---|
| `value` | `Nullable(Float64)` | **9 currencies — never aggregate without grouping by `currency`** |
| `currency` | `Nullable(String)` | `AED AUD GBP INR OMR QAR SAR SGD USD` |
| `coupon_applied` | `Nullable(UInt8)` | 1,267 purchases (17.96%) |
| `coupon_name` | `Nullable(String)` | `''` · `ATLYS15` · `FIRST10` · `SUMMER20` · `WELCOME` — **undocumented** |
| `discount_amount` | `Nullable(Float64)` | ~₹500 average across all coupons — **undocumented** |
| `insurance_added` | `Nullable(UInt8)` | **22.06% attach rate** — **undocumented** |
| `insurance_amount` | `Nullable(Float64)` | avg 1,349.69 when attached |
| `plan_selected` | `Nullable(String)` | `black` · `express` · `standard` — **undocumented** |

## The undocumented add-on economy

`base_context.md` documents only `value`, `currency`, `insurance_amount`,
`coupon_applied`. The table actually carries a **full add-on and plan-tier
model** — `plan_selected`, `insurance_added`, `coupon_name`, `discount_amount` —
that the context layer is entirely silent on.

This matters for [spec 05 Instant Forex](../known_issues.md): forex is
not a novel pattern, it is a **third** add-on alongside insurance and plan tiers.
It should be instrumented consistently with them, and analysed against the 22.06%
insurance attach rate as a baseline.

## ⚠ Revenue is not aggregatable

INR averages 5,035 and SGD averages 33 — a ~150× spread, with no FX rate column.
`sum(value)` and `avg(value)` across the table are meaningless but return clean
numbers. See [known_issues.md](../known_issues.md).
