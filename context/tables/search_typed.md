---
id: table.search_typed
kind: table
status: verified
confidence: high
source: clickathon DB — system.tables, system.columns, profiling queries
last_verified: 2026-08-01
links: [doc.envelope, doc.relationship]
---

# `search_typed`

Supporting. User types a destination search.

| | |
|---|---:|
| Rows | **599,630** |
| Distinct users | 599,630 (1 per user) |
| Rows with `application_id` | 92,440 |
| Time range | **2025-12-31 23:41:56** → 2026-06-30 23:56:08 |

**100% of these users also appear in `destination_card_clicked`** — verified.
Note this is the only table whose data starts before 2026-01-01.

| Column | Type | Values |
|---|---|---|
| `search_term` | `Nullable(String)` | free text |
| `results_count` | `Nullable(UInt16)` | |
| `source` | `Nullable(String)` | `home_search` · `search_bar` · `suggestion` |

Pairs with `destination_card_clicked.flow = 'search'` for search-driven discovery
analysis. `results_count = 0` is the natural zero-result-search signal.
