---
id: metric.step_through_rate
kind: metric
status: verified
confidence: high
source: clickathon DB — set-membership stage counts
last_verified: 2026-08-01
links: [metric.drop_off_rate, pattern.funnel_computation, doc.business]
---

# Step-through rate

**Formula:** distinct users at stage N+1 ÷ distinct users at stage N, by set
membership (**not** time-ordered — see
[known_issues.md](../known_issues.md)).

## Verified values — H1 2026

| Transition | Users | Step-through |
|---|---:|---:|
| card clicked → application started | 1,000,000 → 154,413 | **15.44%** |
| application started → document uploaded | 154,413 → 20,446 | **13.24%** |
| document uploaded → pay now clicked | 20,446 → 14,739 | **72.09%** |
| pay now clicked → purchased | 14,739 → 7,054 | **47.86%** |

## Where the funnel actually breaks

The two leaks worth a PM's attention:

1. **application → document upload (13.24%)** — 86.8% of started applications
   never upload a passport. The largest absolute loss in the funnel, and
   `base_context.md` does not mention it at all.
2. **pay now → purchase (47.86%)** — half of all payment intents fail. No known
   issue explains it; [K1](../known_issues.md), which claimed
   to, is refuted.

Because the funnel is perfectly nested (100% of each stage's users appear
upstream), these rates are exact, not approximations.
