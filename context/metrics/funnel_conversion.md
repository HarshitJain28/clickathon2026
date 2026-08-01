---
id: metric.funnel_conversion
kind: metric
status: verified
confidence: high
source: clickathon DB — set-membership count, purchase_completed vs application_started
last_verified: 2026-08-01
links: [table.application_started, table.purchase_completed, contradiction.c11_conversion_dual_definition, pattern.funnel_computation]
---

# Funnel conversion — **the default conversion metric**

**Formula:** distinct `purchase_completed` users ÷ distinct `application_started` users.

**Current value: 4.57%** (7,054 ÷ 154,413), H1 2026.

```sql
SELECT round(100.0 * (SELECT uniqExact(user_id) FROM clickathon.purchase_completed)
                   / (SELECT uniqExact(user_id) FROM clickathon.application_started), 2) AS pct
```

## Why this is the default

`base_context.md` defines "conversion" twice with a 6.4× gap
([known_issues.md](../known_issues.md)). This one is chosen
as the unqualified default because:

- Its denominator is a **real, well-formed entity** (an application), unlike
  "sessions", which [do not exist](../known_issues.md).
- It is the denominator `base_context.md` says the drop-off dashboards already use.

**Always name the denominator when reporting.** Say "4.57% of started
applications convert", never a bare "conversion is 4.57%".

## ⚠ Must be computed by set membership

`windowFunnel` returns **3,366** purchases instead of 7,054 — a reported 2.18%
instead of 4.57%. See [known_issues.md](../known_issues.md) and
use [known_issues.md](../known_issues.md).

## Trend — declining across H1

| Month | 2026-01 | 02 | 03 | 04 | 05 | 06 |
|---|---:|---:|---:|---:|---:|---:|
| Conversion | 4.91% | 4.79% | 4.53% | 4.92% | 4.48% | **3.93%** |

A **20% relative decline** over six months, affecting all destination groups
roughly equally. This is unexplained by any known issue — K4 was being used to
explain it away, and is [refuted](../known_issues.md).
Treat it as an open question worth raising unprompted.
