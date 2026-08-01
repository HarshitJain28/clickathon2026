---
id: table.landing_page_scrolled
kind: table
status: verified
confidence: high
source: clickathon DB — system.tables, system.columns, profiling queries
last_verified: 2026-08-01
links: [doc.envelope, doc.relationship]
---

# `landing_page_scrolled`

Supporting. User scrolls a landing page.

| | |
|---|---:|
| Rows | **499,786** |
| Distinct users | 499,786 (1 per user) |
| Rows with `application_id` | 77,362 |
| Time range | 2026-01-01 00:01:50 → 2026-07-01 00:01:48 |

| Column | Type | Values |
|---|---|---|
| `scroll_depth_pct` | `Nullable(UInt8)` | |
| `time_on_page_s` | `Nullable(UInt16)` | |
| `page_version` | `Nullable(String)` | `v3` · `v4` |

`page_version` also exists on `destination_card_clicked`. Before drawing any
v3-vs-v4 conclusion, **check it for the same uniform-random distribution that
invalidated `app_version`** — see [K7](../known_issues.md).
