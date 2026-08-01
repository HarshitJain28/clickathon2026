---
id: table.destination_card_clicked
kind: table
status: verified
confidence: high
source: clickathon DB — system.tables, system.columns, profiling queries
last_verified: 2026-08-01
links: [doc.envelope, doc.relationship, metric.conversion_rate, entity.destination]
---

# `destination_card_clicked`

Funnel stage 1. User taps a destination card.

| | |
|---|---:|
| Rows | **1,000,000** |
| Distinct users | 1,000,000 (**exactly 1 row per user**) |
| Rows with `application_id` | 154,413 (15.44%) |
| Time range | 2026-01-01 00:00:35 → 2026-06-30 23:59:40 |
| Compressed / uncompressed | 100.4 MB / 283.9 MB |

Envelope: see [the envelope](index.md). Event-specific columns below.

| Column | Type | Values |
|---|---|---|
| `visa_type` | `Nullable(String)` | `business` · `medical` · `tourist` · `transit` |
| `card_type` | `Nullable(String)` | `arrival_card` · `eta_card` · `visa_card` |
| `page_version` | `Nullable(String)` | `v3` · `v4` — **undocumented in base_context** |
| `flow` | `Nullable(String)` | `deeplink` · `explore` · `search` |
| `is_guest_browse` | `Nullable(UInt8)` | **undocumented in base_context** |

## Notes

- The 154,413 rows carrying `application_id` are **exactly** the users who
  reached `application_started` — this column marks converters, and is not
  "empty before application start" as `base_context.md` §2 claims.
- `visa_type` says `tourist` where `application_started.purpose` says `tourism` —
  see [known_issues.md](../known_issues.md).
- Largest table; the natural denominator for top-of-funnel rates.
