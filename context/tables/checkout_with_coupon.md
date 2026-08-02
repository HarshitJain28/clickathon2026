---
id: table.checkout_with_coupon
kind: table
status: verified
confidence: high
source: out/06_unseen_spec_2/ddl.sql + justification.md (schema); out/06_unseen_spec_2/load_report.md — rows loaded, D2 overlap_pct; out/06_unseen_spec_2/analysis/q02.md — verified conversion-lift comparison (reversed); out/06_unseen_spec_2/analysis/q03.md — verified per-code discount-amount reconciliation gap vs. coupon_applied
last_verified: 2026-08-02
links: [doc.envelope, doc.relationship, known_issue.d2_application_id_join_format, known_issue.d1_windowfunnel_loses_conversions, known_issue.d7_revenue_unaggregatable, metric.coupon_conversion_lift, metric.coupon_apply_rate, tables.index, table.discount_shown, table.coupon_applied]
---

# `checkout_with_coupon`

Spec 06 (sealed, unseen — Promo / Coupon at Checkout). **The conversion
event for this spec's mini-funnel** — fires when the user proceeds to
checkout, whether or not a coupon was ever applied. Carries its own
`cart_value`/`discount_amount`/`final_value` for every checkout in this
spec's own 2026-06-08→2026-06-28 sample (987 rows) — a materially
different population and window from `pay_now_clicked` (14,739 rows,
2026-01-01→2026-07-01). `justification.md` explicitly rejected merging
this into `pay_now_clicked`/`purchase_completed` (both of which already
carry their own, separately-populated `coupon_applied`/`discount_amount`
columns) on three grounds: no instruction anywhere calls for a schema-level
merge, 0-for-25 precedent across specs 01–05 (all new tables, none
ALTER'd), and this grain mismatch. → `CREATE TABLE`, not an `ALTER`. See
`out/06_unseen_spec_2/justification.md` "CREATE vs ALTER call".

| | |
|---|---:|
| Rows | **987** (verified — `load_report.md`) |
| Distinct users | 987 (1 per user, per profile.md) |
| Distinct `application_id` | 987 (100% unique, per profile.md) |
| Sample time span | 2026-06-08 06:00 → 2026-06-28 23:11 (profile.md file-level span; not separately profiled per event) |
| With a coupon code | 366 / 987 = **37.1%** (`coupon_code` non-null, 5 distinct codes — `EXPIRED5` never appears here, consistent with it always being rejected upstream) |
| No coupon, baseline checkout | 621 / 987 = **62.9%** (`coupon_code IS NULL`, per `profile.md`) — the PM's conversion-lift baseline population |
| Step-through ← `coupon_applied` (coupon subset only) | 366 / 580 = **63.10%** — **verified** by a direct `user_id` join (`analysis/q02.md`, 2026-08-02); this join runs `coupon_applied` → `checkout_with_coupon` directly, **skipping `discount_shown` entirely** — see [discount_shown.md](discount_shown.md) |
| No-coupon baseline reach rate | 621 / 1,252 = **49.60%** — **verified** (`analysis/q02.md`); of the 1,252 users who saw `coupon_field_shown` but never reached `coupon_entered`, 621 still reach this table with `coupon_code IS NULL` |

This table carries the same envelope subset as its siblings (see
[the envelope](index.md)): `id`, `timestamp`, `user_id`, `application_id`,
`device_type`, `os`, `app_version`, `client_lib`, `geoip_country_code`,
`city`, `destination`, plus:

| Column | Type | Values |
|---|---|---|
| `cart_value` | `Float64` | 100% present, 94.5% unique, range `[1502.0, 9000.0]` |
| `currency` | `FixedString(3)` | 7 values, same domain as siblings |
| `coupon_code` | `LowCardinality(Nullable(String))` | **62.9% NULL** = the no-coupon baseline (`spec.md`'s own documented meaning, matching `known_issues.md`'s worked "`discount_percent`/NULL = no discount" example), 5 distinct non-null values when present — the PM's headline conversion-lift split runs off exactly this column |
| `discount_amount` | `Float64` | 100% present (even on no-coupon rows — profiler shows `int:769, float:218` across all 987, so no-coupon rows record a numeric value, presumably `0`; not independently confirmed) — see [known_issues.md](../known_issues.md) → D7 |
| `final_value` | `Float64` | 100% present, 93.9% unique, range `[1286.0, 9000.0]` — the post-discount checkout total, this table's own PM-relevant revenue field |

## PM's conversion-lift split — computed, and the answer is a reversal

**2026-08-02 (source: `analysis/q02.md`):** `coupon_code IS NULL` (621
rows) vs. `coupon_code IS NOT NULL` (366 rows) is exactly the segmentation
`spec.md`'s conversion-lift question and this table's `Nullable`-leading
sort key were both built around — now computed, by set-membership `user_id`
join (D1-safe), not a row-count ratio:

| Cohort | Users | Reached this table | Rate |
|---|---:|---:|---:|
| Coupon-entering (`coupon_entered`, 848) | 848 | 366 | **43.16%** |
| — of which `coupon_applied` (580) | 580 | 366 | 63.10% |
| — of which `coupon_rejected` (268) | 268 | 0 | **0.00%** |
| No-coupon baseline (1,252) | 1,252 | 621 | **49.60%** |

**The lift is negative:** the no-coupon baseline reaches checkout ~6.4
percentage points *more* often than the coupon-entering cohort (49.60% vs.
43.16%) — the opposite of a "coupon → higher conversion" hypothesis. This
987-row table's 366 coupon / 621 no-coupon split is confirmed a clean,
non-fan-out partition with zero cross-contamination in either direction.
The reversal traces almost entirely to coupon rejection being a hard stop
— see [coupon_rejected.md](coupon_rejected.md). Full reasoning and caveats:
[metrics/coupon_conversion_lift.md](../metrics/coupon_conversion_lift.md).

## ⚠ `application_id` does not join `application_started` — 0% overlap

`application_id` was normalized on ingest per D2. The mandatory D2
overlap-check then ran against `application_started` and returned
**`overlap_pct = 0.0%`** (verified — `load_report.md`, 2026-08-02) → per
D2's action table, **STOP**: analyse this table **standalone only**, the
same verdict specs 01–05 all got. See [known_issues.md](../known_issues.md)
→ D2.

## Physical layout deviates from the 8 baseline tables — intentionally, and requires `allow_nullable_key`

`ENGINE = MergeTree`, `ORDER BY (toDate(timestamp), coupon_code, user_id,
id)`, `SETTINGS index_granularity = 8192, allow_nullable_key = 1` — does
not lead with the random `id` UUID, per known_issues.md D8. This is the
only one of this spec's 6 tables (and the only table in the platform so
far) requiring `allow_nullable_key`: its leading column, `coupon_code`, is
`Nullable` by design, because the column that "excludes large numbers of
rows" for this table's dominant query (coupon vs. `coupon_code IS NULL`
baseline) *is* `coupon_code`, null-inclusive. See `justification.md`
"ORDER BY / PARTITION BY reasoning".

## Both `pay_now_clicked`/`purchase_completed` and this table describe coupon signals — unreconciled

Same caveat as [coupon_applied.md](coupon_applied.md): nothing at the
schema level ties `pay_now_clicked.coupon_applied`/
`purchase_completed.coupon_applied`/`coupon_name`/`discount_amount` to
this table's `coupon_code`/`discount_amount`/`final_value` — reconciling
which source is authoritative for any coupon-attach or discount-total
metric is unresolved analysis-layer work.

**A second, narrower reconciliation gap confirmed 2026-08-02
(`analysis/q03.md`):** this table's own `discount_amount`, grouped by
`coupon_code`, does not match `coupon_applied`'s for the same codes — e.g.
`SUMMER20` totals ₹47,262 here (366-row, checkout-only population) vs.
₹87,088 on [coupon_applied.md](coupon_applied.md) (580-row,
apply-time population). `analysis/q03.md` treats `coupon_applied` as the
"discount actually granted" source of truth for margin-cost reporting;
this table's `discount_amount` should not be substituted for it without
noting the gap.

## Other risks carried forward (see `justification.md` for full reasoning)

- **D1** — the conversion-lift split and `coupon_applied → checkout_with_coupon`
  step above are now **verified** by set membership (`analysis/q02.md`);
  the `discount_shown →` leg specifically remains unverified (see
  [discount_shown.md](discount_shown.md)).
- **D2** — see above; `application_id` 0% overlap, standalone only.
- **D6** — 987 rows, 987 distinct `user_id` — no repeat users.
- **D7** — `cart_value`/`discount_amount`/`final_value` span at least 7
  currencies (`INR SGD AED USD GBP AUD SAR`) in this sample; never
  `sum()`/`avg()` any of the three without `GROUP BY currency` — this is
  exactly the shape of the "margin cost: total `discount_amount`" question
  `spec.md` asks for, which D7 warns returns a clean but meaningless
  cross-currency number.
- **D9** — `device_type` mixes casing exactly as documented platform-wide.
