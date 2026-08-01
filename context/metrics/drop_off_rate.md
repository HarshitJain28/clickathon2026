---
id: metric.drop_off_rate
kind: metric
status: verified
confidence: high
source: clickathon DB — set-membership stage counts
last_verified: 2026-08-01
links: [metric.step_through_rate, pattern.funnel_computation]
---

# Drop-off rate

**Formula:** `1 − step_through_rate` for the stage — i.e.
`1 − (distinct users at stage N+1 ÷ distinct users at stage N)`.

The exact complement of [step-through rate](step_through_rate.md); the two are
the same measurement with opposite framing. Use drop-off when the narrative is
about loss, step-through when it is about progression — never both in one table.

## Verified values — H1 2026

| Stage transition | Drop-off | Users lost |
|---|---:|---:|
| card clicked → application started | **84.56%** | 845,587 |
| application started → document uploaded | **86.76%** | 133,967 |
| document uploaded → pay now clicked | 27.91% | 5,707 |
| pay now clicked → purchased | **52.14%** | 7,685 |

## Computation rule

Count by **set membership**, not `windowFunnel`. The time-ordered method
overstates late-funnel drop-off dramatically — it reports 82.8% drop at the final
stage instead of the true 52.14%.
See [known_issues.md](../known_issues.md).

`base_context.md` specifies "within the window" — with only 6 months of data and
one event per user, windowing has no practical effect here. Revisit if
multi-event users are ever loaded.
