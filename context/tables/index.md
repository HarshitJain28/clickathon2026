---
id: tables.index
kind: index
status: verified
confidence: high
source: clickathon DB — system.tables, system.columns, profiling queries on the 8 baseline tables; out/01_express_checkout/load_report.md — rows loaded for the 5 Express Checkout tables; out/01_express_checkout/analysis/q01.md, q02.md, q04.md — verified set-membership step-through for 2 of the 3 transitions
last_verified: 2026-08-02
links: [doc.index, doc.relationship, doc.known_issues]
---

# Tables

Thirteen event tables in `clickathon`: 8 baseline tables + 5 new tables from
spec 01 (Express Checkout). **No views or materialized views exist.** The 8
baseline tables share the 30-column envelope defined below; the 5 Express
Checkout tables use a smaller subset of it (see each page). Every page covers
only its own event-specific columns.

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
| [express_checkout_shown](express_checkout_shown.md) | express checkout | 1,650 | 1,650 | — |
| [express_checkout_selected](express_checkout_selected.md) | express checkout | 1,007 | 1,007 | 61.03%* |
| [saved_method_used](saved_method_used.md) | express checkout | 1,007 | 1,007 | 100%* |
| [otp_entered](otp_entered.md) | express checkout | 1,007 | 1,007 | 100%* |
| [express_payment_confirmed](express_payment_confirmed.md) | **express conversion** | 836 | 836 | 83.02%* |

`*` Express Checkout step-through figures were originally row-count ratios
from `load_report.md`, not verified set-membership joins (D1). **2026-08-02
update:** two of the three transitions are now **verified** exact
set-membership joins on `user_id`, per the Analysis Agent's live queries —
`express_checkout_shown → express_checkout_selected` (61.03%, 100% of
`selected` is a subset of `shown` — `analysis/q04.md`) and
`express_checkout_selected`/`otp_entered → express_payment_confirmed`
(83.02%, exact 1:1 join, safe per D6 — `analysis/q01.md`, `q02.md`). The
`→ saved_method_used` / `→ otp_entered` step (100%) remains an unverified
row-count ratio — see each table's page. ⚠ All 5 Express Checkout tables'
`application_id` returned **0% overlap** against `application_started` (D2
verify, `load_report.md`, re-confirmed independently by `analysis/q01.md`–
`q04.md`) — they do not join to the main funnel; treat as a standalone flow.

**Total: 2,485,988 rows** (2,480,481 baseline + 5,507 Express Checkout).
Data window: 2025-12-31 23:41 → 2026-07-01 03:01 (baseline); Express Checkout
sample: 2026-06-08 → 2026-06-28.

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

## Physical layout (identical on the 8 baseline tables)

```sql
ENGINE = SharedMergeTree
PARTITION BY toYYYYMM(timestamp)
ORDER BY (id, timestamp, user_id)
SETTINGS index_granularity = 8192
```

⚠ Leading with the random `id` UUID defeats the primary index. Do **not**
replicate on new tables — see [known_issues.md](../known_issues.md) → D8.

**The 5 Express Checkout tables (spec 01) correctly do not replicate this.**
They use `ENGINE = MergeTree`, `ORDER BY (toDate(timestamp), device_type,
user_id, id)`, and `LowCardinality(String)` for every categorical — D8's
template, applied for the first time. See each table's page.

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
