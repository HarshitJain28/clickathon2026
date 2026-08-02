---
id: table.coupon_applied
kind: table
status: verified
confidence: high
source: out/06_unseen_spec_2/ddl.sql + justification.md (schema); out/06_unseen_spec_2/load_report.md — rows loaded, D2 overlap_pct; out/06_unseen_spec_2/analysis/q01.md — verified applied/rejected partition; out/06_unseen_spec_2/analysis/q02.md — verified applied→checkout_with_coupon step (bypasses discount_shown); out/06_unseen_spec_2/analysis/q03.md — verified per-code discount cost breakdown
last_verified: 2026-08-02
links: [doc.envelope, doc.relationship, known_issue.d2_application_id_join_format, known_issue.d1_windowfunnel_loses_conversions, known_issue.d7_revenue_unaggregatable, known_issue.k6_summer20_campaign, metric.coupon_apply_rate, metric.coupon_conversion_lift, tables.index, table.coupon_entered, table.discount_shown, table.checkout_with_coupon]
---

# `coupon_applied`

Spec 06 (sealed, unseen — Promo / Coupon at Checkout). Fires when a
submitted coupon code is validated and successfully applied to the cart —
the "success" branch of `coupon_entered`, sibling to `coupon_rejected`'s
"failure" branch. Carries `discount_type`/`discount_amount`, its own
event-specific fields not present on `coupon_entered`. → `CREATE TABLE`,
not an `ALTER` onto `purchase_completed`'s existing `coupon_applied
Nullable(UInt8)` flag/`discount_amount` column — different grain, different
sample population (580 rows here vs. 7,054 on `purchase_completed`), no
shared row identity. See `out/06_unseen_spec_2/justification.md` "CREATE
vs ALTER call".

| | |
|---|---:|
| Rows | **580** (verified — `load_report.md`) |
| Distinct users | 580 (1 per user, per profile.md) |
| Distinct `application_id` | 580 (100% unique, per profile.md) |
| Sample time span | 2026-06-08 06:00 → 2026-06-28 23:11 (profile.md file-level span; not separately profiled per event) |
| Step-through ← `coupon_entered` | 580 / 848 = **68.40%** — now **verified** by set-membership join (`analysis/q01.md`) |
| Step-through → `discount_shown` | 580 / 580 = **100%** — byte-identical row count; **still unverified** — no `analysis/qNN.md` file has joined these two tables directly (see "Same 1:1 row count..." below) |
| Step-through → `checkout_with_coupon` | 366 / 580 = **63.10%** — **verified** by a direct `user_id` join (`analysis/q02.md`, 2026-08-02) — this join runs straight from `coupon_applied` to `checkout_with_coupon`, **skipping `discount_shown` entirely** (see [discount_shown.md](discount_shown.md)) |

This table carries the same envelope subset as its siblings (see
[the envelope](index.md)): `id`, `timestamp`, `user_id`, `application_id`,
`device_type`, `os`, `app_version`, `client_lib`, `geoip_country_code`,
`city`, `destination`, plus:

| Column | Type | Values |
|---|---|---|
| `cart_value` | `Float64` | 100% present, 97.4% unique, range `[1546.0, 8997.0]` |
| `currency` | `FixedString(3)` | 7 values, same domain as siblings |
| `coupon_code` | `LowCardinality(String)` | 100% present, **5 distinct values** — `FREESHIP`(131)/`SUMMER20`(123)/`FIRST10`(118)/`ATLYS15`(112)/`WELCOME`(96). `EXPIRED5` never appears here — it only ever reaches `coupon_rejected`, consistent with expired codes always failing validation |
| `discount_type` | `LowCardinality(String)` | 2 values: `percent`(353) / `flat`(227) |
| `discount_amount` | `Float64` | 100% present, mixed `int`/`float` representation (`int:227, float:353` per profiler), 55.0% unique, range `[0, 1793.0]` — see [known_issues.md](../known_issues.md) → D7 |

## Same 1:1 row count as `discount_shown` — still flagged, still not confirmed

`coupon_applied` and [discount_shown](discount_shown.md) both have exactly
**580 rows**, and `profile.md`'s per-field breakdowns (`city`,
`device_type`, `coupon_code`, `cart_value` range) are identical across the
two tables — the same shape spec 03's `channel_selected`/`link_generated`
turned out to be a true 1:1 pairing (confirmed by
`out/03_status_sharing/analysis/q01.md`) and spec 05's
`currency_selected`/`amount_entered` similarly confirmed
(`out/05_instant_forex/analysis/q03.md`). **Not resolved by this spec's
first analysis run:** all 4 of `analysis/q01.md`–`q04.md` are now in, but
none of them joined `coupon_applied` directly against `discount_shown` —
`q02.md`'s conversion-lift join goes straight from `coupon_applied` to
`checkout_with_coupon` (63.10% step-through), the same "skip the
intermediate table" shape spec 04's analysis showed for
`reminder_cta_clicked`/`reminder_sent` → `reconverted` bypassing
`resumed_at_step`. This 580/580 pairing remains a first-look candidate for
a future `uniqExact(user_id)` check.

## Margin cost by coupon code — verified (`analysis/q03.md`, 2026-08-02)

Per known-issue **D7**, `discount_amount` spans 7 currencies with no FX
rate — totals below are grouped by currency, INR (361 of 580 uses, 62.2%)
used as the headline:

| Code | Uses (INR) | Total discount (₹) | Avg discount/use (₹) | Type |
|---|---:|---:|---:|---|
| SUMMER20 | 82 | 87,088 | 1,062.05 | percent |
| FIRST10 | 78 | 41,639 | 533.83 | percent |
| FREESHIP | 78 | 0 | 0 | flat |
| ATLYS15 | 68 | 55,330 | 813.68 | percent |
| WELCOME | 55 | 16,500 | 300.00 (fixed) | flat |

Volume and margin erosion don't line up 1:1: **SUMMER20** is the single
biggest cost driver on both axes (highest volume *and* highest total/avg
discount) — note per [known_issues.md](../known_issues.md) → K6, SUMMER20
is an always-on code rather than a seasonal campaign, so this volume isn't
a one-off spike. **FREESHIP** ties for 2nd-highest volume but records
**₹0** `discount_amount` on every use in every currency — flagged to the
PM as either a genuine no-cost perk or a possible instrumentation gap.
**ATLYS15** has low volume but disproportionately high total discount
(₹813.68/use). By currency, grand totals across all 5 codes (do not sum
across rows): INR 200,557 / SGD 29,423 / USD 20,740 / AED 20,535 / AUD
14,490 / GBP 13,954 / SAR 11,742.

**Reconciliation gap with `checkout_with_coupon`:** that table carries its
own independently-populated `coupon_code`/`discount_amount` for a
different, smaller population (366 with-coupon rows vs. 580 here) and
gives noticeably different per-code INR totals (e.g. SUMMER20 ₹47,262 on
`checkout_with_coupon` vs. ₹87,088 here) — the two sources are **not
reconciled** at the schema level (see "Both `pay_now_clicked`/
`purchase_completed`..." below and
[checkout_with_coupon.md](checkout_with_coupon.md)); `analysis/q03.md`
uses this table (`coupon_applied`) as the "discount actually granted"
source of truth.

## ⚠ `application_id` does not join `application_started` — 0% overlap

`application_id` was normalized on ingest per D2. The mandatory D2
overlap-check then ran against `application_started` and returned
**`overlap_pct = 0.0%`** (verified — `load_report.md`, 2026-08-02) → per
D2's action table, **STOP**: analyse this table **standalone only**. See
[known_issues.md](../known_issues.md) → D2.

## Physical layout deviates from the 8 baseline tables — intentionally

`ENGINE = MergeTree`, `ORDER BY (toDate(timestamp), coupon_code, user_id,
id)` — does not lead with the random `id` UUID, per known_issues.md D8.
See `justification.md` "ORDER BY / PARTITION BY reasoning".

## Both `pay_now_clicked`/`purchase_completed` and this table describe coupon signals — unreconciled

`pay_now_clicked.coupon_applied` (`Nullable(UInt8)`) and
`purchase_completed.coupon_applied`/`coupon_name`/`discount_amount` are
separately-populated baseline columns from the original load. Nothing at
the schema level ties them to this table's `coupon_code`/`discount_amount`
— the two could describe the same real-world checkout inconsistently, the
same shape of unresolved question `relationship.md` already carries for
spec 02's `co_travelers` vs. `group_size`. Reconciling which source is
authoritative for any coupon-attach or discount-total metric is
analysis-layer work, not resolved by this DDL.

## Other risks carried forward (see `justification.md` for full reasoning)

- **D1** — the `coupon_entered`→`coupon_applied`→`checkout_with_coupon`
  path above is now **verified** by set membership (`analysis/q01.md`,
  `q02.md`); the `→ discount_shown` leg remains an unverified row-count
  ratio.
- **D2** — see above; `application_id` 0% overlap, standalone only.
- **D6** — 580 rows, 580 distinct `user_id` — no repeat users.
- **D7** — `cart_value`/`discount_amount` span multiple currencies; never
  aggregate without `GROUP BY currency` — this is exactly the shape of the
  "margin cost: total `discount_amount`" question `spec.md` asks for.
- **D9** — `device_type` mixes casing exactly as documented platform-wide.
