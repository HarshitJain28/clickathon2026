---
id: metric.recovery_rate
kind: metric
status: verified
confidence: high
source: out/04_checkout_recovery_3/analysis/q01.md — verified overall + by-drop_step recovery rate; out/04_checkout_recovery_3/analysis/q02.md — verified recovery-rate-by-channel (K5 re-test); out/04_checkout_recovery_3/analysis/q03.md — verified timing (hours_since_drop) has no effect
last_verified: 2026-08-02
links: [table.abandonment_detected, table.reminder_sent, table.reconverted, known_issue.d1_windowfunnel_loses_conversions, known_issue.d2_application_id_join_format, known_issue.k5_whatsapp_nudge, metrics.index]
---

# Abandoned-checkout recovery rate

**Definition:** `uniqExact(reconverted.user_id) / uniqExact(abandonment_detected.user_id)`,
computed by **set membership** (`reconverted.user_id ⊆
abandonment_detected.user_id` — 100% verified, per
[D1](../known_issues.md#d1--windowfunnel-loses-52-of-conversions--critical),
never `windowFunnel`). Spec 04 (Abandoned Checkout Recovery) only.

## Overall and by `drop_step`

| `drop_step` | Abandoned | Reconverted | Recovery rate |
|---|---:|---:|---:|
| `application_started` | 521 | 25 | **4.80%** |
| `pay_now_clicked` | 397 | 19 | 4.79% |
| `document_uploaded` | 696 | 31 | 4.45% |
| `destination_card_clicked` | 686 | 18 | **2.62%** (worst) |
| **Overall** | **2,300** | **93** | **4.04%** |

`application_started`/`pay_now_clicked` are a near-tie (n=521/397 — a
1-user swing flips the ranking); `destination_card_clicked` — the
earliest, lowest-intent drop point — recovers at roughly half the rate of
the other three.

## By channel (of `reminder_sent`) — the K5 re-test

| Channel | Sent | Opened | Open rate | Clicked (of opened) | Reconverted | Recovery rate (of sent) |
|---|---:|---:|---:|---:|---:|---:|
| WhatsApp | 484 | 224 | **46.28%** (best) | 34.82% | 21 | 4.34% |
| **Push** | 1,138 | 322 | 28.30% | 40.99% | 53 | **4.66%** (best) |
| Email | 678 | 144 | 21.24% | 40.28% | 19 | 2.80% (worst on every step) |

WhatsApp wins the open step by a wide margin but converts opens into
clicks/reconversions at the *lowest* rate of the three; push — weaker at
attracting opens — ends up best end-to-end. This settles
[known_issues.md](../known_issues.md) → K5: a nudge does recover
abandoners, but WhatsApp is not the standout channel once the full funnel
is measured.

## By timing (`hours_since_drop`) — no effect

| Sent at | Sent | Recovery rate (of sent) |
|---|---:|---:|
| 1h | 433 | 3.46% |
| 3h | 484 | 4.13% |
| 6h | 496 | **4.84%** (best) |
| 24h | 469 | 3.62% |
| 48h | 418 | 4.07% |

Range is only 3.46%–4.84% with no monotonic pattern — every bucket sits
within ~1 standard error of the pooled 4.04% base rate (binomial SE
~0.9–1.0pp, n≈420–500/bucket). Send timing does not meaningfully move
recovery rate at this sample size.

## Caveats

- Per [D2](../known_issues.md#d2--spec-application_id-wont-join--critical),
  this spec's `application_id` has 0% overlap with `application_started`,
  and `user_id` has **not** been overlap-checked against the main funnel
  either — this metric is standalone within spec 04's own 6 tables, not
  comparable to `funnel_conversion`.
- The `reminder_cta_clicked → resumed_at_step → reconverted` leg is
  **not** independently verified — every joined query so far reaches
  `reconverted` directly from `reminder_cta_clicked`/`reminder_sent`,
  bypassing `resumed_at_step`. See
  [resumed_at_step.md](../tables/resumed_at_step.md).
- Sample: full live spec-04 table contents, window 2026-06-08 06:01 →
  2026-07-01 00:00. n is small per cut (18–53 reconversions per segment) —
  read rankings as directional, especially near-ties.
- See also [abandonment_detected.md](../tables/abandonment_detected.md)'s
  "Recovery targeting does not match the real funnel's actual worst
  drop-offs" finding (`analysis/q04.md`) — this metric measures recovery
  *of what gets flagged*, which is a small and disproportionately
  late-stage-weighted slice of all non-converters.
