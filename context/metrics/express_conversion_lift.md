---
id: metric.express_conversion_lift
kind: metric
status: verified
confidence: medium
source: out/01_express_checkout/analysis/q01.md — set-membership comparison of express_checkout_selected→express_payment_confirmed vs pay_now_clicked→purchase_completed
last_verified: 2026-08-02
links: [metric.step_through_rate, metric.funnel_conversion, table.express_payment_confirmed, table.pay_now_clicked, doc.known_issues]
---

# Express conversion lift

**Formula:** `express_payment_confirmed` users ÷ `express_checkout_selected`
users, compared against `purchase_completed` users ÷ `pay_now_clicked` users
(the standard-checkout equivalent step). Both computed by `uniqExact` set
membership on `user_id` (per [known_issues.md](../known_issues.md) D1), not
`windowFunnel` or row-count ratios.

## Current value

| Flow | Users | Rate |
|---|---:|---:|
| Express (`express_checkout_selected` → `express_payment_confirmed`) | 836 / 1,007 | **83.02%** |
| Standard (`pay_now_clicked` → `purchase_completed`) | 7,054 / 14,739 | **47.86%** |

**Lift: +35.2 percentage points, 1.73× (+73% relative).**

Restricting the standard-checkout rate to Express's exact sample window
(2026-06-08→2026-06-28: 858/1,792 = 47.88%) gives essentially the same
baseline — the gap is not a time-window artifact.

## ⚠ Not a randomized or matched comparison

- `application_id` does not join Express Checkout's 5 tables to the main
  funnel ([known_issues.md](../known_issues.md) D2, 0% overlap,
  re-confirmed table-by-table) — the two populations cannot be verified as
  comparable cohorts (device, geo, funnel stage reached).
- **Likely selection bias:** Express is opt-in — only 61.0% of users shown
  the button selected it (see
  [express_checkout_shown.md](../tables/express_checkout_shown.md)). Users
  who choose a saved-method, one-tap flow may already skew toward higher
  purchase intent than the general `pay_now_clicked` population. This dataset
  cannot separate self-selection from a pure product/UX effect.
- Sample size: Express n=1,007 vs standard n=14,739 — directionally solid but
  a 3-week sample vs a 6-month baseline.
- Both flows share a similar unexplained leak pattern: Express has a ~101-row
  gap between `otp_success=true` (937) and `express_payment_confirmed` (836)
  that no column explains, mirroring the standard flow's own unexplained
  ~52% `pay_now_clicked → purchase_completed` leak. Neither leak changes the
  headline comparison above.

**Report as:** "Express converts 83.02% vs standard's 47.86% (+35.2pp) in
this sample — likely inflated by opt-in selection bias; not a controlled
comparison." Never as a bare "Express is 1.73× better."
