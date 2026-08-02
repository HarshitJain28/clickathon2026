---
id: metrics.index
kind: index
status: verified
confidence: high
source: derived from frontmatter of metrics/*.md
last_verified: 2026-08-02
links: [doc.index, pattern.funnel_computation]
---

# Metrics

Every metric from `base_context.md` §4, re-derived against live data. Values are
H1 2026 (2026-01-01 → 2026-07-01).

| Metric | Value | Status | Confidence |
|---|---:|---|---|
| [funnel_conversion](funnel_conversion.md) — **the default** | **4.57%** | verified | high |
| [step_through_rate](step_through_rate.md) | per stage | verified | high |
| [drop_off_rate](drop_off_rate.md) | per stage | verified | high |
| [revenue_per_conversion](revenue_per_conversion.md) | per currency | verified | medium |
| [passport_capture_pass_rate](passport_capture_pass_rate.md) | 88.76% | verified | **low** |
| [conversion_rate](conversion_rate.md) (÷ sessions) | 0.71% | **refuted** | high |
| [on_time_delivery_rate](on_time_delivery_rate.md) | — | **unverifiable** | low |
| [express_conversion_lift](express_conversion_lift.md) | +35.2pp (83.02% vs 47.86%) | verified | medium |
| [group_completion_rate_by_size](group_completion_rate_by_size.md) | 69.47%→31.11% (size 2→6), 57.33% overall | verified | high |
| [share_completion_rate](share_completion_rate.md) | 71.5% overall, flat 70.1%–73.3% by status | verified | high |
| [recipient_conversion_k_factor](recipient_conversion_k_factor.md) | ~38% pure-new-user, 0% pure-existing-user | verified | medium |

## Three rules for reporting any of these

1. **Name the denominator.** "Conversion" is defined two ways in
   `base_context.md`, 6.4× apart ([known_issues.md](../known_issues.md)).
   Default to `funnel_conversion` and say what it is over.
2. **Compute funnels by set membership.** `windowFunnel` loses 52% of
   conversions ([known_issues.md](../known_issues.md)).
   See [known_issues.md](../known_issues.md).
3. **Group revenue by currency.** Nine currencies, no FX rate
   ([known_issues.md](../known_issues.md)).

## Metrics `base_context.md` should have but doesn't

Real, measurable, and currently undocumented:

- **Insurance attach rate** — 22.06% of purchases, avg 1,349.69
- **Coupon usage rate** — 17.96% of purchases
- **Paid-search share** — 22.30% of purchases carry a `gclid`
- **Plan mix** — `standard` / `express` / `black` on both checkout tables
- **Auth-to-application rate** — 84.0%; 29,377 users authenticate and never apply
