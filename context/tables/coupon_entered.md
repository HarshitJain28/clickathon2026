---
id: table.coupon_entered
kind: table
status: verified
confidence: high
source: out/06_unseen_spec_2/ddl.sql + justification.md (schema); out/06_unseen_spec_2/load_report.md — rows loaded, D2 overlap_pct; out/06_unseen_spec_2/analysis/q01.md — verified applied/rejected partition; out/06_unseen_spec_2/analysis/q04.md — verified success rate by device/geo/destination segment
last_verified: 2026-08-02
links: [doc.envelope, doc.relationship, known_issue.d2_application_id_join_format, known_issue.d1_windowfunnel_loses_conversions, known_issue.k6_summer20_campaign, metric.coupon_apply_rate, tables.index, table.coupon_field_shown, table.coupon_applied, table.coupon_rejected]
---

# `coupon_entered`

Spec 06 (sealed, unseen — Promo / Coupon at Checkout). Fires when the user
submits a coupon code for validation — a later, optional moment than
`coupon_field_shown` (only 848 of 2,100 shown-events, 40.38%, have a
corresponding row here). → `CREATE TABLE`, not an `ALTER`. See
`out/06_unseen_spec_2/justification.md` "CREATE vs ALTER call".

| | |
|---|---:|
| Rows | **848** (verified — `load_report.md`) |
| Distinct users | 848 (1 per user, per profile.md) |
| Distinct `application_id` | 848 (100% unique, per profile.md) |
| Sample time span | 2026-06-08 06:00 → 2026-06-28 23:11 (profile.md file-level span; not separately profiled per event) |
| Step-through ← `coupon_field_shown` | 848 / 2,100 = **40.38%** — now **verified** by set-membership join (`analysis/q01.md`), see [coupon_field_shown.md](coupon_field_shown.md) |
| Step-through → `coupon_applied` / `coupon_rejected` | 580 + 268 = **848 = 100%** of this table — **verified** (`analysis/q01.md`, 2026-08-02): a live `uniqExact(user_id)` join confirms an exact, non-overlapping partition, every one of the 848 users appears in exactly one of the two outcomes, 0 in both |
| Success rate (applied ÷ entered) | 580 / 848 = **68.40%** — verified; see [metrics/coupon_apply_rate.md](../metrics/coupon_apply_rate.md) for the by-code/device/geo breakdown (`analysis/q04.md`) |

This table carries the same envelope subset as `coupon_field_shown` (see
[the envelope](index.md)): `id`, `timestamp`, `user_id`, `application_id`,
`device_type`, `os`, `app_version`, `client_lib`, `geoip_country_code`,
`city`, `destination`, plus:

| Column | Type | Values |
|---|---|---|
| `cart_value` | `Float64` | 100% present, 95.2% unique, range `[1509.0, 8997.0]` |
| `currency` | `FixedString(3)` | 7 values, same domain as `coupon_field_shown` |
| `coupon_code` | `LowCardinality(String)` | 100% present, **6 distinct values** (the full spec domain): `FREESHIP`(155)/`EXPIRED5`(149)/`SUMMER20`(141)/`ATLYS15`(140)/`FIRST10`(140)/`WELCOME`(123) — the PM's central cut for this spec ("which codes drive volume"). Note `EXPIRED5` appears here and on `coupon_rejected` only — it never reaches `coupon_applied`/`discount_shown`/`checkout_with_coupon`, consistent with an expired code always being rejected |

`SUMMER20`'s presence here (141 of 848, 16.6%) is the same code
[known_issues.md](../known_issues.md) → K6 already found to be an
"always-on" code rather than a seasonal campaign, on the main
`purchase_completed` table — this spec's narrower 3-week sample is not
itself a K6 re-test (no verification query has run against this table for
K6), just a consistent-looking coincidence worth noting before assuming
otherwise.

## Every entered code resolves to applied-or-rejected — now confirmed

`coupon_applied` (580) + `coupon_rejected` (268) = 848, exactly this
table's row count. **Confirmed 2026-08-02** (`analysis/q01.md`): a live
`uniqExact(user_id)` join across all three tables verified this is
genuinely the same 848 `user_id`s partitioned two ways, with 0 entries
resolving to both outcomes or neither — not merely a row-count
coincidence, unlike `discount_shown`/`coupon_applied`'s still-unconfirmed
580/580 pairing (see [discount_shown.md](discount_shown.md)).

## By coupon code and segment (`analysis/q04.md`, 2026-08-02)

`EXPIRED5` fails **100% of the time in every device/geo/destination cut**
(149 attempts, 0 applied) — consistent with it being a permanently-expired
code rather than a segment-dependent failure. The other 5 live codes
cluster in a broad 60–100% success band per segment. By `device_type`
(the most reliable cut, n=9–73/cell): `FREESHIP` is notably weaker on
Desktop (57.1%, n=14) than elsewhere (84–90%); `ATLYS15`/`WELCOME` both
dip to 69.2% on android; `ios`/`web-user-b2c` are consistently strongest.
India (`IN`) dominates geo volume (70–93 attempts/code) with 78–91%
success; other geos/destinations are too thin (n<20/cell) to trust
individually. See
[metrics/coupon_apply_rate.md](../metrics/coupon_apply_rate.md) for the
full table.

## ⚠ `application_id` does not join `application_started` — 0% overlap

`application_id` was normalized on ingest per D2. The mandatory D2
overlap-check then ran against `application_started` and returned
**`overlap_pct = 0.0%`** (verified — `load_report.md`, 2026-08-02) → per
D2's action table, **STOP**: analyse this table **standalone only**. See
[known_issues.md](../known_issues.md) → D2.

## Physical layout deviates from the 8 baseline tables — intentionally

`ENGINE = MergeTree`, `ORDER BY (toDate(timestamp), coupon_code, user_id,
id)` — does not lead with the random `id` UUID, per known_issues.md D8.
`coupon_code` takes the #2 slot here (unlike `coupon_field_shown`, which
has no code yet) because it's now available and is the PM's central
dimension — see `justification.md` "ORDER BY / PARTITION BY reasoning".

## Other risks carried forward (see `justification.md` for full reasoning)

- **D1** — set-membership partition and success rate above are now
  **verified** (`analysis/q01.md`, `q04.md`); no monotonicity check has
  run on this spec's own timestamps, so ordering claims remain unconfirmed.
- **D2** — see above; `application_id` 0% overlap, standalone only.
- **D6** — 848 rows, 848 distinct `user_id` — no repeat users.
- **D7** — `cart_value` spans multiple currencies; never aggregate without
  `GROUP BY currency`.
- **D9** — `device_type` mixes casing exactly as documented platform-wide.
