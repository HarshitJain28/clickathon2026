---
id: metric.on_time_delivery_rate
kind: metric
status: unverifiable
confidence: low
source: base_context.md §4; no backing columns exist in clickathon DB
last_verified: 2026-08-01
links: [contradiction.c9_eta_days_column_missing, table.application_started, spec.03_status_sharing]
---

# On-time delivery rate — **NOT COMPUTABLE**

## What `base_context.md` says

> "**On-time delivery rate** = applications issued on or before
> `visa_issuance_eta_days` ÷ applications issued. (Reported by the fulfilment
> team from post-purchase systems; not computable from the funnel tables here.)"

## Two independent blockers

1. **The numerator does not exist.** There is no issuance event, issuance date,
   or application-status column in any of the 8 tables. Post-payment is out of
   scope for this dataset by design.
2. **The denominator column does not exist either.** `visa_issuance_eta_days` is
   not a real column — the real one is `eta_shown`, a categorical string
   (`24 hours`, `3-5 days`, …), not an integer day count.
   See [known_issues.md](../known_issues.md).

## Verdict

**Unverifiable, and correctly flagged as such by `base_context.md` itself** —
which is to its credit. Retained here so the Analytics Agent has a documented
answer rather than a silent failure.

## Required response when asked

> "On-time delivery cannot be computed from this dataset. It requires visa
> issuance data from post-purchase fulfilment systems, which are out of scope
> here. The closest available signal is `eta_shown` — the ETA *displayed to the
> user* at application start — which records what was promised, not what was
> delivered."

Do not substitute `eta_shown` for delivery performance. It is a promise, not an
outcome.

[Spec 03 Status Sharing](../known_issues.md) introduces
`status_shared` (`submitted`/`processing`/`approved`) — the first post-purchase
status signal to enter this system, and a partial path toward making this metric
computable.
