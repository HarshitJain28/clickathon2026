---
id: tables.index
kind: index
status: verified
confidence: high
source: clickathon DB — system.tables, system.columns, profiling queries on all 8 tables
last_verified: 2026-08-01
links: [doc.index, doc.relationship, doc.known_issues]
---

# Tables

Eight raw event tables in `clickathon`. **No views or materialized views exist.**
All share the 30-column envelope defined below; the individual pages cover only
each table's event-specific columns.

| Table | Role | Rows | Users | Step-through |
|---|---|---:|---:|---:|
| [destination_card_clicked](destination_card_clicked.md) | funnel 1 | 1,000,000 | 1,000,000 | — |
| [application_started](application_started.md) | funnel 2 | 154,413 | 154,413 | 15.44% |
| [document_uploaded](document_uploaded.md) | funnel 3 | 20,446 | 20,446 | **13.24%** |
| [pay_now_clicked](pay_now_clicked.md) | checkout | 14,739 | 14,739 | 72.09% |
| [purchase_completed](purchase_completed.md) | **conversion** | 7,054 | 7,054 | 47.86% |
| [search_typed](search_typed.md) | supporting | 599,630 | 599,630 | — |
| [landing_page_scrolled](landing_page_scrolled.md) | supporting | 499,786 | 499,786 | — |
| [auth_completed](auth_completed.md) | supporting | 183,790 | 183,790 | — |

**Total: 2,480,481 rows.** Data window: 2025-12-31 23:41 → 2026-07-01 03:01.

---

## The shared event envelope

All 8 tables carry these 30 columns identically, then add event-specific ones.

| Column | Type | Notes |
|---|---|---|
| `id` | `UUID` | **not nullable**; leads the sort key (see D8) |
| `timestamp` | `DateTime` | **not nullable**; second precision; partition source |
| `user_id` | `String` | **not nullable**; exactly 28 chars everywhere |
| `application_id` | `Nullable(String)` | 36-char hyphenated UUID when present |
| `app_session_id` | `Nullable(String)` | **not a session** — unique per row (D4) |
| `device` | `Nullable(String)` | |
| `device_type` | `Nullable(String)` | `Desktop` · `android` · `ios` · `web-user-b2c` |
| `os` | `Nullable(String)` | `Android` · `Linux` · `Mac OS X` · `Windows` · `iOS` — **5.95% NULL** |
| `app_version` | `Nullable(String)` | `7.42.0` · `7.43.1` · `7.44.0` · `7.45.2` · `7.46.0` — **no temporal signal (K7)** |
| `client_lib` | `Nullable(String)` | `mobile-rn` · `web-js` |
| `geoip_country_code` | `Nullable(String)` | `AE AU GB IN OM OTHER QA SA SG US` |
| `geoip_subdivision_1_code` | `Nullable(String)` | |
| `city` | `Nullable(String)` | |
| `client_ip` | `Nullable(String)` | |
| `latitude` / `longitude` | `Nullable(Float64)` | |
| `locale` / `language` | `Nullable(String)` | |
| `funnel_type` | `Nullable(String)` | `b2c` · `b2c_afc` · `b2c_black` |
| `co_travelers` | `Nullable(UInt8)` | on **all 8 tables**, not just applications |
| `is_guest` / `is_referral` / `is_enterprise` | `Nullable(UInt8)` | 0/1 flags |
| `gclid` / `fbclid` / `gad_source` | `Nullable(String)` | `gclid` present ⇒ paid search (22.30% of purchases) |
| `citizenship` | `Nullable(String)` | 11 values, **lowercase** |
| `destination` | `Nullable(String)` | 27 values, **UPPERCASE** ISO-2 |
| `is_back_filled` | `Nullable(UInt8)` | **1.98%** of rows |
| `duplicate_id` | `Nullable(String)` | **2.99%** of rows carry one |

`duplicate_id` and `is_back_filled` are undocumented data-quality fields —
decide explicitly whether to filter them, don't ignore them.

## Physical layout (identical on all 8)

```sql
ENGINE = SharedMergeTree
PARTITION BY toYYYYMM(timestamp)
ORDER BY (id, timestamp, user_id)
SETTINGS index_granularity = 8192
```

⚠ Leading with the random `id` UUID defeats the primary index. Do **not**
replicate on new tables — see [known_issues.md](../known_issues.md) → D8.

## Two corrections to base_context's table model

1. **`pay_now_clicked` is a funnel stage, not "supporting".** It sits between
   document upload and purchase and holds the second-largest leak — 52% of
   payment intents never convert.
2. **`auth_completed` is a superset, not a peer.** 29,377 of its users never
   started an application — an un-analysed cohort.

## Columns base_context.md never mentions

`scan_mode`, `failed_attempt_threshold`, `page_version`, `is_guest_browse`,
`coupon_name`, `discount_amount`, `insurance_added`, `plan_selected`,
`duplicate_id`, `is_back_filled`. The add-on economy on `purchase_completed`
(insurance 22.06% attach, plan tiers, coupons) is the most significant omission.
