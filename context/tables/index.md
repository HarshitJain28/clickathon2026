---
id: tables.index
kind: index
status: verified
confidence: high
source: clickathon DB — system.tables, system.columns, profiling queries on the 8 baseline tables; out/01_express_checkout/load_report.md — rows loaded for the 5 Express Checkout tables; out/01_express_checkout/analysis/q01.md, q02.md, q04.md — verified set-membership step-through for 2 of the 3 transitions; out/02_group_family/load_report.md — rows loaded and D2 overlap_pct for the 4 Group/Family tables; out/02_group_family/analysis/q01.md, q03.md — verified set-membership step-through by group_size; out/03_status_sharing/load_report.md — rows loaded and D2 overlap_pct for 3 of the 5 Status Sharing tables; out/03_status_sharing/analysis/q01.md–q04.md — verified share-flow step-through, channel mix, K-factor, destination spread
last_verified: 2026-08-02
links: [doc.index, doc.relationship, doc.known_issues]
---

# Tables

Twenty-two event tables in `clickathon`: 8 baseline tables + 5 from spec 01
(Express Checkout) + 4 from spec 02 (Group / Family Applications) + 5 from
spec 03 (Visa Status Sharing). **No views or materialized views exist.** The
8 baseline tables share the 30-column envelope defined below; the 14 spec
tables each use a smaller subset of it (see each page). Every page covers
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
| [group_started](group_started.md) | group flow | 1,200 | 1,200 | — |
| [traveller_added](traveller_added.md) | group flow (fan-out) | 3,495 | 1,200† | — |
| [traveller_removed](traveller_removed.md) | group flow (churn) | 70 | 69† | — |
| [group_submitted](group_submitted.md) | **group conversion** | 688 | 688 | **57.33%**‡ |
| [share_clicked](share_clicked.md) | share flow | 1,600 | 1,600 | — |
| [channel_selected](channel_selected.md) | share flow | 1,144 | 1,144 | 71.5%§ |
| [link_generated](link_generated.md) | share flow | 1,144 | 1,144 | n/a§ |
| [link_opened](link_opened.md) | share flow (recipient) | 2,310 | n/a†† | n/a§ |
| [recipient_cta_clicked](recipient_cta_clicked.md) | **share K-factor** | 305 | n/a†† | 13.2%§ |

`††` `link_opened`/`recipient_cta_clicked` carry **no `user_id` column at
all** (recipient-side, per D6 — the constraint doesn't apply since there's
no column to check); "Users" is not applicable, not zero. See D6.

`†` `traveller_added`/`traveller_removed` break the "one row per user"
pattern the other 15 tables share — a group owner can add/remove multiple
co-travellers, so distinct users is lower than row count. See D6 and each
table's page.

`‡` `group_submitted`'s step-through from `group_started` (688/1,200 =
57.33%) is now a **verified** set-membership join (`group_submitted.group_id
⊆ group_started.group_id` by construction, per D1), per the Analysis
Agent's `analysis/q01.md` and `q03.md` (2026-08-02, independently
reproduced by both). It also falls **monotonically** by `group_size`: from
69.47% (size 2) to 31.11% (size 6) — see
[group_started.md](group_started.md) and
[metrics/group_completion_rate_by_size.md](../metrics/group_completion_rate_by_size.md).
All 4 Group/Family tables' `application_id` returned **0% overlap** against
`application_started` (D2 verify, `load_report.md`, 2026-08-02,
independently re-confirmed by all 4 of `analysis/q01.md`–`q04.md`, none of
which found a working `application_id` path) — same STOP verdict as spec
01; treat as a standalone flow, not joinable to the main funnel.

`§` Spec 03 (Status Sharing) step-through: `share_clicked → channel_selected`
(71.5%) is now a **verified** set-membership join on `share_id`
(`analysis/q01.md`, 2026-08-02), flat across `status_shared` (70.1%–73.3%,
no monotonic pattern) — see
[metrics/share_completion_rate.md](../metrics/share_completion_rate.md).
`channel_selected` and `link_generated` have byte-for-byte identical column
sets, exactly 1,144 rows each, and are now **confirmed** (not just flagged)
to hold the exact same 1,144 `share_id`s in every status bucket —
functionally a 1:1 pairing (`analysis/q01.md`). The recipient-side leg
(`link_opened → recipient_cta_clicked`) is also **verified** 100% by set
membership (`analysis/q03.md`) — see
[metrics/recipient_conversion_k_factor.md](../metrics/recipient_conversion_k_factor.md)
for the resulting K-factor (~38% pure-new-user / 0% pure-existing-user,
after correcting for a `recipient_is_new_user` self-contradiction found in
51.2% of shares — a D3-shaped flag issue). **Still unverified:** the
sharer-side ↔ recipient-side leg itself (e.g. `link_generated.share_id` vs.
`link_opened.share_id`) — no `analysis/qNN.md` file has checked it yet.
Channel mix (WhatsApp 54.6% of selections, also the top new-user-open
channel at 61.5%) and destination spread (AU leads raw reach, AE leads
conversion efficiency at 16.37%) are also now verified — see
[channel_selected.md](channel_selected.md),
[link_opened.md](link_opened.md), and
[recipient_cta_clicked.md](recipient_cta_clicked.md).
⚠ 3 of the 5 Status Sharing tables' `application_id`
(`share_clicked`/`channel_selected`/`link_generated`) returned **0%
overlap** against `application_started` (D2 verify, `load_report.md`,
2026-08-02, independently re-confirmed by all 4 of `analysis/q01.md`–
`q04.md`, none of which found a working `application_id` path) — same STOP
verdict as specs 01 and 02; treat as a standalone flow. `link_opened`/
`recipient_cta_clicked` carry no `application_id` at all.

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

**Total: 2,497,944 rows** (2,480,481 baseline + 5,507 Express Checkout +
5,453 Group/Family + 6,503 Status Sharing). Data window: 2025-12-31 23:41 →
2026-07-01 03:01 (baseline); Express Checkout sample: 2026-06-08 →
2026-06-28; Group/Family sample: 2026-06-08 → 2026-06-28; Status Sharing
sample: 2026-06-08 06:00 → 2026-07-01 09:21 (per profile.md).

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

**The 4 Group/Family tables (spec 02) also follow D8, with a further
substitution.** `ENGINE = MergeTree`, `ORDER BY (toDate(timestamp),
group_size, group_id, id)` — `group_size` and `group_id` replace spec 01's
`device_type`/`user_id` because `group_id`/`user_id` are 1:1-collinear here
and the PM's questions are phrased per-group, not per-user (`group_size` is
also the PM's most-cited dimension for this spec). See
[group_started](group_started.md) for the full reasoning.

**The 5 Status Sharing tables (spec 03) also follow D8, each substituting
its own leading discriminator.** `ENGINE = MergeTree` throughout;
`share_clicked` → `(toDate(timestamp), status_shared, user_id, id)`;
`channel_selected`/`link_generated` → `(toDate(timestamp), channel,
user_id, id)`; the 2 recipient-side tables (no `user_id`) →
`(toDate(timestamp), channel, share_id, id)` and `(toDate(timestamp),
destination, share_id, id)` respectively. See
[share_clicked](share_clicked.md) and its 4 sibling pages.

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
