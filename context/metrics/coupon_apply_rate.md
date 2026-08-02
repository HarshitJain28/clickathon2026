---
id: metric.coupon_apply_rate
kind: metric
status: verified
confidence: high
source: out/06_unseen_spec_2/analysis/q01.md — verified field_shown→coupon_applied apply rate, valid/rejected partition, top reject reasons; out/06_unseen_spec_2/analysis/q04.md — verified success rate by device/geo/destination segment
last_verified: 2026-08-02
links: [table.coupon_field_shown, table.coupon_entered, table.coupon_applied, table.coupon_rejected, known_issue.d1_windowfunnel_loses_conversions, known_issue.d2_application_id_join_format, metrics.index]
---

# Coupon apply rate

**Definition:** `uniqExact(coupon_applied.user_id) /
uniqExact(coupon_field_shown.user_id)`, computed by **set-membership**
join on `user_id` (per [known_issues.md](../known_issues.md) D1), not a
row-count ratio. Spec 06 (Promo/Coupon at Checkout, sealed/unseen) only.

## Current value

| Stage | Users | Step-through |
|---|---:|---:|
| `coupon_field_shown` | 2,100 | — |
| `coupon_entered` | 848 | 40.38% |
| `coupon_applied` | 580 | 68.40% of entered (**27.62%** of shown) |
| `coupon_rejected` | 268 | 31.60% of entered |

**Overall apply rate (field_shown → applied): 27.62%.** Confirmed an
exact, non-overlapping partition (`analysis/q01.md`, 2026-08-02): every
one of the 848 `coupon_entered` users resolves to exactly one of
`coupon_applied` (580) / `coupon_rejected` (268) — 580 + 268 = 848 with 0
users appearing in both outcomes. All 3 downstream tables' users are also
a confirmed 100%-nested subset of `coupon_field_shown`'s 2,100.

## Top reject reasons (of 268 rejections, verified — `analysis/q01.md`)

| Reason | Count | Share |
|---|---:|---:|
| `min_cart_not_met` | 80 | 29.85% |
| `already_used` | 75 | 27.99% |
| `expired` | 60 | 22.39% |
| `invalid_code` | 53 | 19.78% |

No reason dominates — all four sit within a ~10pp band.

## By coupon code and segment (`analysis/q04.md`)

Overall success rate (applied ÷ entered) = 580/848 = 68.4%. `EXPIRED5`
fails **100% of the time in every device/geo/destination cut** (149
attempts, 0 applied) — a permanently-expired code, not a segment effect.
The other 5 live codes (`ATLYS15`, `FIRST10`, `FREESHIP`, `SUMMER20`,
`WELCOME`) cluster in a broad 60–100% success band per segment, no clean
universal winner or loser.

- **By `device_type`** (most reliable cut, n=9–73/cell): `FREESHIP` is
  notably weaker on Desktop (57.1%, n=14) than elsewhere it appears
  (84–90%); `ATLYS15` and `WELCOME` both dip to 69.2% on android
  (same rate, same n=39 — a pattern, not yet enough evidence to call
  causal). `ios`/`web-user-b2c` are consistently the strongest device
  segments.
- **By geo/destination:** India (`IN`) dominates volume (70–93
  attempts/code, ~7–10× any other geo) with 78–91% success for the 5 live
  codes. Outside India, per-code cells drop to n=2–20 — too thin to call
  individual code/geo or code/destination pairs reliably.

## Caveats

- Per [D2](../known_issues.md#d2--spec-application_id-wont-join--critical),
  this spec's `application_id` has 0% overlap with `application_started`
  — standalone within spec 06's own 6 tables, not comparable to
  `funnel_conversion` or other specs.
- Sample: `out/06_unseen_spec_2` only, 2026-06-08 06:00 → 2026-06-28
  23:11, a 3-week window.
- No monotonicity check has run on this spec's own timestamps
  ([D1](../known_issues.md#d1--windowfunnel-loses-52-of-conversions--critical))
  — set membership, not `windowFunnel`, is what's confirmed here.
