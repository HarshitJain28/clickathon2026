---
id: table.coupon_rejected
kind: table
status: verified
confidence: high
source: out/06_unseen_spec_2/ddl.sql + justification.md (schema); out/06_unseen_spec_2/load_report.md — rows loaded, D2 overlap_pct; out/06_unseen_spec_2/analysis/q01.md — verified reject-reason breakdown and applied/rejected partition; out/06_unseen_spec_2/analysis/q04.md — verified EXPIRED5 0% success across all segments
last_verified: 2026-08-02
links: [doc.envelope, doc.relationship, known_issue.d2_application_id_join_format, known_issue.d1_windowfunnel_loses_conversions, metric.coupon_apply_rate, metric.coupon_conversion_lift, tables.index, table.coupon_entered, table.coupon_applied]
---

# `coupon_rejected`

Spec 06 (sealed, unseen — Promo / Coupon at Checkout). Fires when a
submitted coupon code fails validation — the "failure" branch of
`coupon_entered`, sibling to `coupon_applied`'s "success" branch. Its own
`reject_reason` field is not present on any other table in this spec. →
`CREATE TABLE`, not an `ALTER`. See
`out/06_unseen_spec_2/justification.md` "CREATE vs ALTER call".

| | |
|---|---:|
| Rows | **268** (verified — `load_report.md`) |
| Distinct users | 268 (1 per user, per profile.md) |
| Distinct `application_id` | 268 (100% unique, per profile.md) |
| Sample time span | 2026-06-08 06:00 → 2026-06-28 23:11 (profile.md file-level span; not separately profiled per event) |
| Step-through ← `coupon_entered` | 268 / 848 = **31.60%** — now **verified** by set-membership join (`analysis/q01.md`, 2026-08-02); together with `coupon_applied`'s 68.40% this is a confirmed exact, non-overlapping partition of all 848 `coupon_entered` users — see [coupon_entered.md](coupon_entered.md) |
| Downstream reach into `checkout_with_coupon` | 0 / 268 = **0%** — **verified** (`analysis/q02.md`, 2026-08-02): every one of the 268 rejected users drops out completely, none ever appear in `checkout_with_coupon` — the hard stop behind [metrics/coupon_conversion_lift.md](../metrics/coupon_conversion_lift.md)'s reversed-lift finding |

This table carries the same envelope subset as its siblings (see
[the envelope](index.md)): `id`, `timestamp`, `user_id`, `application_id`,
`device_type`, `os`, `app_version`, `client_lib`, `geoip_country_code`,
`city`, `destination`, plus:

| Column | Type | Values |
|---|---|---|
| `cart_value` | `Float64` | 100% present, 97.4% unique, range `[1509.0, 8973.0]` |
| `currency` | `FixedString(3)` | 7 values, same domain as siblings |
| `coupon_code` | `LowCardinality(String)` | 100% present, **6 distinct values** — `EXPIRED5`(149) dominates, then `ATLYS15`(28)/`WELCOME`(27)/`FREESHIP`(24)/`FIRST10`(22)/`SUMMER20`(18). `EXPIRED5` accounts for 55.6% of all rejections and never appears on `coupon_applied`/`discount_shown`/`checkout_with_coupon` — consistent with an always-expired code |
| `reject_reason` | `LowCardinality(String)` | 4 values: `min_cart_not_met`(80)/`already_used`(75)/`expired`(60)/`invalid_code`(53) — the PM's explicit "top reject reasons" cut, and this table's own leading sort-key discriminator |

## PM's "top reject reasons" question — verified (`analysis/q01.md`, 2026-08-02)

`min_cart_not_met` (29.85%, 80 rows) and `already_used` (27.99%, 75 rows)
are the two most common reasons, narrowly ahead of `expired` (22.39%, 60
rows) and `invalid_code` (19.78%, 53 rows) — all four sit within a ~10pp
band, no single reason dominates. Now confirmed by a live query, not just
`profile.md`'s row-count breakdown.

## `EXPIRED5` fails 100% of the time, in every segment (`analysis/q04.md`)

`EXPIRED5` accounts for 149 of the 848 `coupon_entered` attempts and
**0** of them ever reach `coupon_applied` — a 0% success rate that holds
across **every** device/geo/destination cut checked, consistent with a
permanently-expired code rather than a segment-dependent failure. See
[metrics/coupon_apply_rate.md](../metrics/coupon_apply_rate.md).

## ⚠ `application_id` does not join `application_started` — 0% overlap

`application_id` was normalized on ingest per D2. The mandatory D2
overlap-check then ran against `application_started` and returned
**`overlap_pct = 0.0%`** (verified — `load_report.md`, 2026-08-02) → per
D2's action table, **STOP**: analyse this table **standalone only**. See
[known_issues.md](../known_issues.md) → D2.

## Physical layout deviates from the 8 baseline tables — intentionally, and from its `coupon_entered`/`coupon_applied` siblings

`ENGINE = MergeTree`, `ORDER BY (toDate(timestamp), reject_reason,
user_id, id)` — does not lead with the random `id` UUID, per
known_issues.md D8. Unlike `coupon_entered`/`coupon_applied`/
`discount_shown`/`checkout_with_coupon` (which lead on `coupon_code`, 5–6
values), this table leads on `reject_reason` (4 values) — both because the
PM explicitly asks for "top reject reasons" and because it's the
lower-cardinality choice for this specific table (`coupon_code` here has 6
distinct values, one more than `reject_reason`'s 4). See
`justification.md` "ORDER BY / PARTITION BY reasoning".

## Other risks carried forward (see `justification.md` for full reasoning)

- **D1** — step-through, downstream-reach, and reject-reason figures
  above are now **verified** by set membership (`analysis/q01.md`,
  `q02.md`, `q04.md`).
- **D2** — see above; `application_id` 0% overlap, standalone only.
- **D6** — 268 rows, 268 distinct `user_id` — no repeat users.
- **D7** — `cart_value` spans multiple currencies; never aggregate without
  `GROUP BY currency`.
- **D9** — `device_type` mixes casing exactly as documented platform-wide.
