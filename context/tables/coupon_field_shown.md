---
id: table.coupon_field_shown
kind: table
status: verified
confidence: high
source: out/06_unseen_spec_2/ddl.sql + justification.md (schema); out/06_unseen_spec_2/load_report.md — rows loaded, D2 overlap_pct; out/06_unseen_spec_2/analysis/q01.md — verified field_shown→entered→applied/rejected set-membership nesting and apply rate
last_verified: 2026-08-02
links: [doc.envelope, doc.relationship, known_issue.d2_application_id_join_format, known_issue.d1_windowfunnel_loses_conversions, known_issue.d8_sort_key_defeats_primary_index, known_issue.d7_revenue_unaggregatable, metric.coupon_apply_rate, tables.index, table.coupon_entered, table.checkout_with_coupon]
---

# `coupon_field_shown`

Spec 06 (sealed, unseen — Promo / Coupon at Checkout). Origin of the coupon
mini-funnel — fires when the coupon-code input field renders at checkout,
before any code has been typed. Its own client-side moment, distinct from
the two existing baseline tables that already carry coupon-shaped columns
(`pay_now_clicked.coupon_applied`, `purchase_completed.coupon_applied`/
`coupon_name`/`discount_amount`) — those describe a flag/attribute on an
existing row, not this table's own render event, with its own
`application_id` population and a materially different sample window. →
`CREATE TABLE`, not an `ALTER`. See
`out/06_unseen_spec_2/justification.md` "CREATE vs ALTER call".

| | |
|---|---:|
| Rows | **2,100** (verified — `load_report.md`) |
| Distinct users | 2,100 (1 per user, per profile.md) |
| Distinct `application_id` | 2,100 (100% unique, per profile.md) |
| Sample time span | 2026-06-08 06:00 → 2026-06-28 23:11 (profile.md file-level span; not separately profiled per event) |
| Step-through → `coupon_entered` | 848 / 2,100 = **40.38%** — now a **verified** set-membership join on `user_id` (`analysis/q01.md`, 2026-08-02): 100% of `coupon_entered`/`coupon_applied`/`coupon_rejected` users are a confirmed subset of this table's 2,100 |
| Field_shown → `coupon_applied` (apply rate) | 580 / 2,100 = **27.62%** — verified, direct set-membership join; see [metrics/coupon_apply_rate.md](../metrics/coupon_apply_rate.md) |

This table carries a **subset** of the shared 30-column envelope (see
[the envelope](index.md)): `id`, `timestamp`, `user_id`, `application_id`,
`device_type`, `os`, `app_version`, `client_lib`, `geoip_country_code`,
`city`, `destination` — the same subset spec 05 (Instant Forex) used, per
`profile.md`'s "observed fields only" policy. Plus two columns of its own:

| Column | Type | Values |
|---|---|---|
| `cart_value` | `Float64` | 100% present, 87.6% unique, range `[1501.0, 9000.0]` — the pre-discount cart total at this step |
| `currency` | `FixedString(3)` | 7 values observed: `INR`(1,275)/`SGD`(217)/`AED`(192)/`USD`(139)/`GBP`(103)/`AUD`(94)/`SAR`(80), a subset of the platform's documented 9 — see [known_issues.md](../known_issues.md) → D7 |

No `coupon_code` on this table — it fires before any code is typed, the
top of this spec's own funnel.

## 2026-08-02 — first analysis run for this spec (4 questions)

All 4 of `out/06_unseen_spec_2/analysis/q01.md`–`q04.md` are now in. The
full 6-event chain's set-membership nesting is confirmed
(`coupon_entered`/`coupon_applied`/`coupon_rejected` all 100% subsets of
this table, `q01.md`) — but per [known_issues.md](../known_issues.md) →
D1, no monotonicity check has run on this spec's own **timestamps** yet,
so treat any *ordering* claim (as opposed to membership) as still
unconfirmed. Headline apply rate (field_shown → `coupon_applied`) is
**27.62%** — see
[metrics/coupon_apply_rate.md](../metrics/coupon_apply_rate.md). See
[coupon_entered.md](coupon_entered.md), [coupon_applied.md](coupon_applied.md),
[coupon_rejected.md](coupon_rejected.md), [discount_shown.md](discount_shown.md),
and [checkout_with_coupon.md](checkout_with_coupon.md) for the rest of
the findings — notably a **reversed** conversion-lift result (coupon
users convert *lower*, not higher, than the no-coupon baseline; see
[metrics/coupon_conversion_lift.md](../metrics/coupon_conversion_lift.md)).

## ⚠ `application_id` does not join `application_started` — 0% overlap

`application_id` was normalized on ingest per D2 (32-char hex → 36-char
hyphenated UUID, e.g. the spec-NDJSON form observed in this spec's sample).
The mandatory D2 overlap-check then ran against `application_started` and
returned **`overlap_pct = 0.0%`** (verified — `load_report.md`,
2026-08-02) → per D2's action table, **STOP**: analyse this table
**standalone only**, the same verdict specs 01–05 all got. See
[known_issues.md](../known_issues.md) → D2.

## Physical layout deviates from the 8 baseline tables — intentionally

`ENGINE = MergeTree`, `ORDER BY (toDate(timestamp), device_type, user_id,
id)` — does not lead with the random `id` UUID, per known_issues.md D8.
`device_type` (4 values) takes the #2 slot because this table has no
`coupon_code` yet and `device_type` is the lowest-cardinality column
available (ahead of `currency`/`city`/`geoip_country_code` at 7 each, and
`destination` at 14) — see `justification.md` "ORDER BY / PARTITION BY
reasoning".

## Other risks carried forward (see `justification.md` for full reasoning)

- **D1** — the full 6-event chain (`coupon_field_shown → coupon_entered →
  coupon_applied`/`coupon_rejected → discount_shown → checkout_with_coupon`)
  must be computed by `uniqExact(user_id)` set membership once analysed,
  never `windowFunnel`/`sequenceMatch` — no monotonicity check has run yet
  for this spec's own timestamps.
- **D2** — see above; `application_id` 0% overlap, standalone only.
- **D6** — 2,100 rows, 2,100 distinct `user_id` — no repeat users.
- **D7** — `cart_value` spans at least 7 currencies in this sample; never
  `sum()`/`avg()` it without `GROUP BY currency`.
- **D9** — `device_type` mixes casing (`ios`/`android`/`web-user-b2c` vs
  `Desktop`), exactly as documented platform-wide.
