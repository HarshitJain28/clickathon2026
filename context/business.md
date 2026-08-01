---
id: doc.business
kind: business
status: verified
confidence: medium
source: base_context.md (intent) + clickathon DB (all figures)
last_verified: 2026-08-01
links: [doc.relationship, entity.user, entity.application, metric.funnel_conversion, contradiction.c2_dataset_scale]
---

# Business overview

Atlys is a digital visa platform. Travellers discover visa requirements for a
destination, start an application, upload a passport, and pay. The north-star is
**conversion**: turning a card tap into a paid application.

*(Business framing above is from `base_context.md` and is intent, not a data claim —
it cannot be verified from event data. Everything below is measured.)*

## The funnel, as measured

```
destination_card_clicked → application_started → document_uploaded → purchase_completed
```

`pay_now_clicked` sits between document upload and purchase in practice, and
belongs in any checkout analysis even though `base_context.md` files it as
"supporting".

| Stage | Distinct users | Step-through from previous |
|---|---:|---:|
| 1. `destination_card_clicked` | 1,000,000 | — |
| 2. `application_started` | 154,413 | 15.44% |
| 3. `document_uploaded` | 20,446 | 13.24% |
| 4. `pay_now_clicked` | 14,739 | 72.09% |
| 5. `purchase_completed` | 7,054 | 47.86% |

- **Card → purchase: 0.71%**
- **Application → purchase: 4.57%** (the denominator the drop-off dashboards use)
- Median time application → purchase: **110.5 minutes** average

The funnel is **perfectly nested**: 100% of users at each stage are present at
every prior stage. Verified — see [relationship.md](relationship.md).

The biggest single leak is **stage 2 → 3** (application started → document
uploaded), where 86.8% of applications die. `base_context.md` does not mention this.

## Verified scale — H1 2026

| Claim in `base_context.md` | Measured | Verdict |
|---|---|---|
| "120+ destinations" | **27** distinct `destination` values | [refuted](known_issues.md) |
| "700K+ applications annually" | 154,413 in 6 months (~309K/yr run rate) | not reproduced in this dataset |
| "~2.5M rows" | 2,480,481 | ✓ |
| "iOS-first, large Android base, meaningful web cohort" | iOS 6,401 / Android 3,594 / web+desktop 3,862 pay-clicks | ✓ directionally |

Destinations present (27): `AE AU CA CH EG ES FR GB GR HK ID IT JP KR LK MA MV MY
OM QA SA SG TH TR US VN ZA`

**Region grouping is not derivable.** `base_context.md` references regions (GCC,
SEA, Schengen, Americas) but **no region column exists in any table**. Any region
cut must be a hand-maintained mapping — see
[known_issues.md](known_issues.md).

## Seasonality — measured, and it is not what the context says

Application → purchase conversion by month:

| Month | All destinations | Schengen only |
|---|---:|---:|
| 2026-01 | 4.91% | 5.15% |
| 2026-02 | 4.79% | 4.02% |
| 2026-03 | 4.53% | 5.27% |
| 2026-04 | 4.92% | 4.87% |
| 2026-05 | 4.48% | 4.53% |
| 2026-06 | 3.93% | 4.21% |

Conversion is on a **broad downward trend across H1** (4.91% → 3.93%), affecting
all destinations roughly equally. Schengen is not distinctly worse in summer —
in May and June it is *better* than the rest. This refutes K4.

## Out of scope

Post-payment (submission, embassy processing, issuance, refunds) is handled by
other systems. No table here contains it. Note that
[spec 03 Status Sharing](known_issues.md) depends on exactly this
out-of-scope domain.
