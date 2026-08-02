---
id: table.discount_shown
kind: table
status: verified
confidence: high
source: out/06_unseen_spec_2/ddl.sql + justification.md (schema); out/06_unseen_spec_2/load_report.md — rows loaded, D2 overlap_pct; out/06_unseen_spec_2/analysis/q02.md — the coupon_applied→checkout_with_coupon join that bypasses this table
last_verified: 2026-08-02
links: [doc.envelope, doc.relationship, known_issue.d2_application_id_join_format, known_issue.d1_windowfunnel_loses_conversions, known_issue.d7_revenue_unaggregatable, tables.index, table.coupon_applied, table.checkout_with_coupon]
---

# `discount_shown`

Spec 06 (sealed, unseen — Promo / Coupon at Checkout). Fires when the
discounted price is rendered back to the user after a coupon is applied —
its own client-side render moment, distinct from `coupon_applied`'s
validation-success moment even though the two share the identical 580 row
count in this sample. → `CREATE TABLE`, not an `ALTER`. See
`out/06_unseen_spec_2/justification.md` "CREATE vs ALTER call".

| | |
|---|---:|
| Rows | **580** (verified — `load_report.md`) |
| Distinct users | 580 (1 per user, per profile.md) |
| Distinct `application_id` | 580 (100% unique, per profile.md) |
| Sample time span | 2026-06-08 06:00 → 2026-06-28 23:11 (profile.md file-level span; not separately profiled per event) |
| Step-through ← `coupon_applied` | 580 / 580 = **100%** — byte-identical row count; **unverified**, flagged by `justification.md` as a likely 1:1 pairing not yet confirmed by a live join — see [coupon_applied.md](coupon_applied.md) |
| Step-through → `checkout_with_coupon` (coupon subset only) | 366 / 580 = **63.10%** — unverified row-count ratio (`checkout_with_coupon`'s 366 non-null-`coupon_code` rows vs. this table's 580, per `profile.md`) |

This table carries the same envelope subset as its siblings (see
[the envelope](index.md)): `id`, `timestamp`, `user_id`, `application_id`,
`device_type`, `os`, `app_version`, `client_lib`, `geoip_country_code`,
`city`, `destination`, plus:

| Column | Type | Values |
|---|---|---|
| `cart_value` | `Float64` | 100% present, 97.4% unique, range `[1546.0, 8997.0]` — identical range to `coupon_applied` |
| `currency` | `FixedString(3)` | 7 values, same domain as siblings |
| `coupon_code` | `LowCardinality(String)` | 100% present, 5 distinct values, identical distribution to `coupon_applied`: `FREESHIP`(131)/`SUMMER20`(123)/`FIRST10`(118)/`ATLYS15`(112)/`WELCOME`(96) |
| `discount_amount` | `Float64` | 100% present, mixed `int`/`float` representation (`int:227, float:353`), 55.0% unique, range `[0, 1793.0]` — identical distribution to `coupon_applied`'s own `discount_amount`, see [known_issues.md](../known_issues.md) → D7 |

No `discount_type` on this table (it exists only on `coupon_applied`) —
`profile.md` shows this event does not carry it.

## Same 1:1 row count and matching distributions as `coupon_applied` — flagged, still not confirmed

`discount_shown` and [coupon_applied](coupon_applied.md) share not just
580/580 row counts but identical `city`/`coupon_code`/`cart_value`/
`discount_amount` distributions in `profile.md` — a strong signal this is
a true 1:1 pairing (every applied coupon immediately renders its discount),
same shape as spec 03's `channel_selected`/`link_generated` and spec 05's
`currency_selected`/`amount_entered`, both later confirmed by live joins.
**Still not confirmed here, even after this spec's first analysis run:**
all 4 of `out/06_unseen_spec_2/analysis/q01.md`–`q04.md` are now in, but
none of them join this table at all. `q02.md`'s conversion-lift check goes
directly from `coupon_applied` (580 rows) to `checkout_with_coupon` (63.10%
step-through, 366/580) — it **skips over `discount_shown` entirely**, the
same "jump past the intermediate table" pattern
[known_issues.md](../known_issues.md) already documents for spec 04's
`reminder_cta_clicked`/`reminder_sent` → `reconverted` bypassing
[resumed_at_step](resumed_at_step.md). This table's own position in the
funnel chain — both its 1:1 pairing with `coupon_applied` and its
relationship to `checkout_with_coupon` — remains open for a future
analysis question.

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

## Other risks carried forward (see `justification.md` for full reasoning)

- **D1** — step-through ratios above remain row-count only; this spec's
  first analysis run (`analysis/q01.md`–`q04.md`) did not join this table
  at all (see "Same 1:1 row count..." above) — still needs its own
  set-membership check.
- **D2** — see above; `application_id` 0% overlap, standalone only.
- **D6** — 580 rows, 580 distinct `user_id` — no repeat users.
- **D7** — `cart_value`/`discount_amount` span multiple currencies; never
  aggregate without `GROUP BY currency`.
- **D9** — `device_type` mixes casing exactly as documented platform-wide.
