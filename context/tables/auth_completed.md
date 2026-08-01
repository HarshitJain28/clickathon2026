---
id: table.auth_completed
kind: table
status: verified
confidence: high
source: clickathon DB — system.tables, system.columns, profiling queries
last_verified: 2026-08-01
links: [doc.envelope, doc.relationship, entity.user]
---

# `auth_completed`

Supporting. User finishes login/signup. **The only table that is a superset of
the funnel.**

| | |
|---|---:|
| Rows | **183,790** |
| Distinct users | 183,790 (1 per user) |
| Users who also started an application | 154,413 (**84.0%**) |
| Users who authenticated and never applied | **29,377** |
| `is_new_user = 1` | 100,892 (54.9%) |
| Time range | 2026-01-01 00:01:31 → 2026-06-30 23:59:15 |

| Column | Type | Values |
|---|---|---|
| `auth_method` | `Nullable(String)` | `apple` · `email` · `google` · `otp` |
| `is_new_user` | `Nullable(UInt8)` | |
| `attempts` | `Nullable(UInt8)` | |

## The 29,377-user gap

Every other funnel table is perfectly nested inside its predecessor. This one is
not: 29,377 users authenticated — a high-intent action — and never started an
application. `base_context.md` does not mention this segment.

It is a **genuine, un-analysed drop-off cohort** and one of the more promising
unprompted findings available in this dataset. `auth_method` and `attempts` are
the natural first cuts.
