---
id: tables.index
kind: index
status: verified
confidence: high
source: clickathon DB — system.tables, system.columns, profiling queries on the 8 baseline tables; out/01_express_checkout/load_report.md — rows loaded for the 5 Express Checkout tables; out/01_express_checkout/analysis/q01.md, q02.md, q04.md — verified set-membership step-through for 2 of the 3 transitions; out/02_group_family/load_report.md — rows loaded and D2 overlap_pct for the 4 Group/Family tables; out/02_group_family/analysis/q01.md, q03.md — verified set-membership step-through by group_size; out/03_status_sharing/load_report.md — rows loaded and D2 overlap_pct for 3 of the 5 Status Sharing tables; out/03_status_sharing/analysis/q01.md–q04.md — verified share-flow step-through, channel mix, K-factor, destination spread; out/04_abondon_checkout_recovery_2/load_report.md — rows loaded and D2 overlap_pct for the 6 Abandoned Checkout Recovery tables; out/04_checkout_recovery_3/load_report.md — identical row counts and D2 verdict on independent resubmission; out/04_checkout_recovery_3/analysis/q01.md–q04.md — resolves the duplicate-load question (no duplication), verified recovery rate by drop_step/channel/timing (K5 re-test), recovery-targeting mismatch finding; out/05_instant_forex/load_report.md — rows loaded and D2 overlap_pct for the 5 Instant Forex tables; out/05_instant_forex/analysis/q01.md–q04.md — verified full-funnel set-membership step-through, attach rate by destination/currency/device/geo, AOV
last_verified: 2026-08-02
links: [doc.index, doc.relationship, doc.known_issues]
---

# Tables

Thirty-three event tables in `clickathon`: 8 baseline tables + 5 from spec
01 (Express Checkout) + 4 from spec 02 (Group / Family Applications) + 5
from spec 03 (Visa Status Sharing) + 6 from spec 04 (Abandoned Checkout
Recovery) + 5 from spec 05 (Instant Forex Add-on). **No views or
materialized views exist.** The 8 baseline tables share the 30-column
envelope defined below; the 25 spec tables each use a smaller subset of it
(see each page). Every page covers only its own event-specific columns.

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
| [abandonment_detected](abandonment_detected.md) | recovery flow (origin) | 2,300 | 2,300 | — |
| [reminder_sent](reminder_sent.md) | recovery flow (nudge) | 2,300 | 2,300 | 100%‖ |
| [reminder_opened](reminder_opened.md) | recovery flow (nudge) | 690 | 690 | 30.00%‖ |
| [reminder_cta_clicked](reminder_cta_clicked.md) | recovery flow (nudge) | 268 | 268 | 38.84%‖ |
| [resumed_at_step](resumed_at_step.md) | recovery flow (return) | 268 | 268 | 100%‖ |
| [reconverted](reconverted.md) | **recovery conversion** | 93 | 93 | 34.70%‖ (**4.04%** overall vs. `abandonment_detected`) |
| [forex_offer_shown](forex_offer_shown.md) | forex flow (origin) | 2,900 | 2,900 | — |
| [currency_selected](currency_selected.md) | forex flow | 1,033 | 1,033 | 35.62%¶ |
| [amount_entered](amount_entered.md) | forex flow | 1,033 | 1,033 | 100%¶ |
| [forex_added_to_cart](forex_added_to_cart.md) | forex flow | 725 | 725 | 70.18%¶ |
| [forex_purchased](forex_purchased.md) | **forex conversion** | 546 | 546 | 75.31%¶ (**18.83%** overall vs. `forex_offer_shown`) |

`¶` Spec 05 (Instant Forex Add-on) step-through figures were originally
**unverified row-count ratios** from `profile.md`/`load_report.md`.
**2026-08-02 update:** all of them are now **verified** exact
set-membership joins on `user_id`, per the Analysis Agent's live queries
(`analysis/q01.md`, `q03.md`, `q04.md`) — the full 5-stage chain is
confirmed **perfectly nested** end-to-end and 100% timestamp-monotonic
(unlike the main visa funnel, this one has no ordering trap). The
overwhelming majority of the funnel's loss (64.38%, 1,867 users)
concentrates at the very first step, `forex_offer_shown →
currency_selected`. `currency_selected` and `amount_entered` share an
identical row count (1,033) and identical per-field breakdowns in
`profile.md`; this is now **confirmed** a true 1:1 pairing (100%
step-through, direct set-membership join), the same pattern spec 03's
`channel_selected`/`link_generated` turned out to have — see
[currency_selected.md](currency_selected.md). The PM's headline attach-rate
metric (`forex_purchased` ÷ `forex_offer_shown` = **18.83%**) is also
verified, with a real ~11pp spread by `destination` (best US 24.58%,
worst AU 13.78%) — see
[metrics/forex_attach_rate.md](../metrics/forex_attach_rate.md). AOV
among the 546 attachers is right-skewed (median ₹31,685, mean
₹40,587.77, INR only) — see
[metrics/forex_addon_aov.md](../metrics/forex_addon_aov.md). ⚠ All 5
Instant Forex tables' `application_id` returned **0% overlap** against
`application_started` (D2 verify, `load_report.md`, 2026-08-02,
independently re-confirmed by all 4 of `analysis/q01.md`–`q04.md`, none
of which found a working `application_id` path) — same STOP verdict as
specs 01–04; treat as a standalone flow, not joinable to the main funnel.
See [forex_offer_shown.md](forex_offer_shown.md) and its 4 sibling
pages.

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

`‖` Spec 04 (Abandoned Checkout Recovery) step-through figures were
originally **unverified row-count ratios** from `profile.md`/
`load_report.md`. **2026-08-02 update:** most are now **verified** by the
Analysis Agent's live set-membership joins
(`out/04_checkout_recovery_3/analysis/q01.md`–`q04.md`) — the headline PM
metric (overall recovery rate, `reconverted` ÷ `abandonment_detected` =
93/2,300 = **4.04%**), its breakdown by `drop_step` (flat 4.45%–4.80% for
the first 3 steps, worst at 2.62% for `destination_card_clicked`), and the
`reminder_sent → reminder_opened → reminder_cta_clicked → reconverted`
chain (channel + timing cuts) are all confirmed by direct `user_id` joins,
not ratios. **Still unverified:** the `abandonment_detected → reminder_sent`
step and the `resumed_at_step` leg specifically (every joined query so far
skips straight from `reminder_cta_clicked`/`reminder_sent` to
`reconverted`) — see [resumed_at_step.md](resumed_at_step.md). This was
also the re-test material for [known_issues.md](../known_issues.md) → K5
(WhatsApp nudge): **now re-tested** — WhatsApp opens best (46.28%) but
**push** wins end-to-end recovery-of-sent (4.66% vs. 4.34%), so K5's
"WhatsApp nudge" claim is only partially confirmed. See
[metrics/recovery_rate.md](../metrics/recovery_rate.md). ⚠ All 6
Abandoned Checkout Recovery tables' `application_id` returned **0%
overlap** against `application_started` (D2 verify, `load_report.md`,
2026-08-02) — same STOP verdict as specs 01–03; treat as a standalone
flow. `justification.md` also flags that this spec's `user_id` (unlike
its `application_id`) is well-formed and has **still not** been overlap-
checked against the main funnel — none of `analysis/q01.md`–`q04.md`
performed that check either. A newly confirmed finding
(`analysis/q04.md`): recovery flags are **not** targeting the real
funnel's actual worst drop-offs — the two biggest real leaks (845,587 and
133,967 lost users) get flagged at only 0.08%/0.39%, while the two
smaller late-stage leaks get flagged at 12.2%/5.2% — see
[abandonment_detected.md](abandonment_detected.md).

⚠ **2026-08-02 — spec 04 resubmitted under a new output directory,
`out/04_checkout_recovery_3`.** `ddl.sql` uses `CREATE TABLE IF NOT
EXISTS` (no new tables created — the 28-table count above is unchanged),
and its `load_report.md` reports **byte-identical** row counts and D2
verdicts to the original load for all 6 tables. Whether this resubmission
also re-inserted the same rows a second time (silently doubling each
table's true live count, and with it the totals below) was an open
question needing a live query to settle.

**Resolved 2026-08-02 (source: `out/04_checkout_recovery_3/analysis/
q01.md`–`q04.md`).** All 4 files independently ran live
`count()`/`uniqExact(user_id)` queries against these 6 tables and got
figures matching the documented row counts exactly (2,300/2,300/690/268/
268/93) — **no duplication occurred**. `q02.md` explicitly re-checked all
6 tables at once; `q01.md`/`q04.md` independently re-confirmed
`abandonment_detected`/`reconverted`; `q03.md` independently re-confirmed
`reminder_sent`. See [known_issues.md](../known_issues.md) → D2 and
[abandonment_detected.md](abandonment_detected.md) for the full
reasoning. The row counts in the table above and the totals below are now
**confirmed**, not merely unverified-against-duplication.

**Total: 2,510,100 rows** (2,480,481 baseline + 5,507 Express Checkout +
5,453 Group/Family + 6,503 Status Sharing + 5,919 Abandoned Checkout
Recovery + 6,237 Instant Forex, per
`out/04_abondon_checkout_recovery_2/load_report.md` and
`out/05_instant_forex/load_report.md`, the Abandoned Checkout Recovery
figure confirmed non-duplicated by
`out/04_checkout_recovery_3/analysis/q01.md`–`q04.md`, 2026-08-02). Data
window: 2025-12-31 23:41 → 2026-07-01 03:01 (baseline); Express Checkout
sample: 2026-06-08 → 2026-06-28; Group/Family sample: 2026-06-08 →
2026-06-28; Status Sharing sample: 2026-06-08 06:00 → 2026-07-01 09:21;
Abandoned Checkout Recovery sample: 2026-06-08 06:01 → 2026-07-01 00:00;
Instant Forex sample: 2026-06-08 06:00 → 2026-06-28 23:12 (per
profile.md).

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

**The 6 Abandoned Checkout Recovery tables (spec 04) also follow D8, split
between two leading discriminators.** `ENGINE = MergeTree` throughout;
`abandonment_detected`/`resumed_at_step`/`reconverted` →
`(toDate(timestamp), drop_step, user_id, id)` (keyed by the funnel step
dropped from/returned to — the natural join key across the
numerator/denominator pair); `reminder_sent`/`reminder_opened`/
`reminder_cta_clicked` → `(toDate(timestamp), channel, user_id, id)`
(keyed by nudge channel — the PM's "which channel recovers best"
question). See [abandonment_detected](abandonment_detected.md) and its 5
sibling pages.

**The 5 Instant Forex tables (spec 05) also follow D8, all substituting
`destination`.** `ENGINE = MergeTree` throughout; `ORDER BY
(toDate(timestamp), destination, user_id, id)` on all 5 — the PM's own
questions name `destination` explicitly ("attach rate … by `destination`",
"which destinations attach best"). This spec also deliberately upgrades
`destination` from `LowCardinality(String)` (specs 01–04's pattern) to
`FixedString(2)` — a checked, justified exception, not a reflexive
default; see [forex_offer_shown](forex_offer_shown.md) for the reasoning.

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
