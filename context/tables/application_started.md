---
id: table.application_started
kind: table
status: verified
confidence: high
source: clickathon DB — system.tables, system.columns, profiling queries
last_verified: 2026-08-01
links: [doc.envelope, entity.application, metric.funnel_conversion, contradiction.c9_eta_days_column_missing]
---

# `application_started`

Funnel stage 2. User starts an application. **`application_id` is created here.**

| | |
|---|---:|
| Rows | **154,413** |
| Distinct users | 154,413 (**exactly 1 application per user**) |
| Distinct `application_id` | 154,413 |
| Time range | 2026-01-01 00:09:38 → 2026-07-01 00:20:24 |
| Step-through from stage 1 | **15.44%** |

Envelope: see [the envelope](index.md). Event-specific columns below.

| Column | Type | Values |
|---|---|---|
| `purpose` | `Nullable(String)` | `business` · `medical` · `tourism` · `transit` |
| `eta_shown` | `Nullable(String)` | `24 hours` (15,521) · `3-5 days` (61,656) · `5-7 days` (46,315) · `7-10 days` (30,921) |
| `flow` | `Nullable(String)` | `deeplink` · `explore` · `search` |

`co_travelers` and `destination` are envelope columns, present on all 8 tables —
not specific to this one, despite `base_context.md` implying otherwise.

## ⚠ `visa_issuance_eta_days` does not exist

`base_context.md` §2 claims this table carries `visa_issuance_eta_days` as an
integer. It does not. The real column is **`eta_shown`**, a categorical string
with mixed units. See [known_issues.md](../known_issues.md).

## Notes

- The **denominator for [`funnel_conversion`](../metrics/funnel_conversion.md)**,
  the default conversion metric.
- Stage 2 → 3 is the funnel's worst leak: only 13.24% of applications reach a
  document upload.
