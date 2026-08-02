---
id: metric.coupon_conversion_lift
kind: metric
status: verified
confidence: medium
source: out/06_unseen_spec_2/analysis/q02.md — verified checkout_with_coupon reach rate for coupon-entering users vs. the no-coupon baseline
last_verified: 2026-08-02
links: [table.checkout_with_coupon, table.coupon_applied, table.coupon_rejected, table.coupon_field_shown, table.coupon_entered, known_issue.d1_windowfunnel_loses_conversions, known_issue.d2_application_id_join_format, metric.coupon_apply_rate, metrics.index]
---

# Coupon conversion lift

**Formula:** reach rate into `checkout_with_coupon` for users who engaged
the coupon field (`coupon_entered`) vs. users who never did (the
no-coupon baseline), both computed by **set-membership** join on
`user_id` ([known_issues.md](../known_issues.md) D1), not a row-count
ratio. Spec 06 (Promo/Coupon at Checkout, sealed/unseen) only.

## Current value — the lift is negative, not positive

| Cohort | Users | Reached `checkout_with_coupon` | Rate |
|---|---:|---:|---:|
| Coupon-entering (`coupon_entered`, 848) | 848 | 366 | **43.16%** |
| — of which `coupon_applied` (580) | 580 | 366 | 63.10% |
| — of which `coupon_rejected` (268) | 268 | 0 | **0.00%** |
| No-coupon baseline (saw `coupon_field_shown`, never reached `coupon_entered`) | 1,252 | 621 | **49.60%** |

**The no-coupon baseline converts ~6.4 percentage points *higher* than
the coupon-entering cohort (49.60% vs. 43.16%)** — the opposite of a
"coupon → higher conversion" hypothesis. `checkout_with_coupon`'s 987
rows split exactly into 366 coupon + 621 no-coupon with zero
cross-contamination in either direction (`analysis/q02.md`, 2026-08-02).
The reversal is driven almost entirely by coupon rejection being a hard
stop: **100% of the 268 rejected users drop out completely**, never
reaching `checkout_with_coupon` in any form; only appliers who succeed
(580 of them) convert onward, and even they convert at 63.10%, not
enough to offset the rejects dragging the coupon-entering cohort's blended
rate down to 43.16%.

## Caveats

- **Not a controlled or matched comparison.** Per D2, this spec's
  `application_id` has 0% overlap with `application_started` — cohort
  composition (device, geo, pre-existing intent) between the
  coupon-entering and no-coupon populations cannot be verified as
  comparable.
- Baseline population (1,252) is scoped to users who saw
  `coupon_field_shown` but never reached `coupon_entered` — not the full
  purchase population; see `analysis/q02.md` for the exact join logic.
- Sample: `out/06_unseen_spec_2` only, 2026-06-08 06:00 → 2026-06-28
  23:11, a 3-week window — read as directional, not a platform-wide claim.
- Per [D7](../known_issues.md#d7--revenue-is-unaggregatable-across-9-currencies),
  no revenue/margin comparison is made here — see
  [coupon_applied.md](../tables/coupon_applied.md) for the currency-scoped
  discount-cost breakdown (`analysis/q03.md`).

**Report as:** "In this sample, users who engage the coupon field convert
to checkout at a *lower* rate (43.16%) than those who never do (49.60%)
— coupon rejection, not coupon use itself, drives the gap." Never as a
bare "coupons lift conversion."
