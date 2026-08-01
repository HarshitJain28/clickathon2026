---
id: table.express_checkout_shown
kind: table
status: verified
confidence: high
source: out/01_express_checkout/ddl.sql + justification.md (schema); load_report.md — rows loaded, D2 overlap_pct; analysis/q04.md — verified set-membership step-through, segment adoption
last_verified: 2026-08-02
links: [doc.envelope, doc.relationship, known_issue.d2_application_id_join_format, tables.index]
---

# `express_checkout_shown`

Spec 01 (Express Checkout). Top of the express flow — the Express button is
rendered at checkout, before any tap. Not the same moment as `pay_now_clicked`,
which only fires on the *standard* Pay Now tap — see
`out/01_express_checkout/justification.md` "CREATE vs ALTER call".

| | |
|---|---:|
| Rows | **1,650** (verified — `load_report.md`) |
| Distinct users | 1,650 (1 per user, per profile.md) |
| Sample time span | 2026-06-08 → 2026-06-28 (profile.md file-level span; not separately profiled per event) |
| Step-through → `express_checkout_selected` | 1,007 / 1,650 = **61.03%** (**verified — exact set-membership subset**, `analysis/q04.md`, 2026-08-02: 100% of `selected` users are a subset of `shown` users) |

This table carries only a **subset** of the shared 30-column envelope (see
[the envelope](index.md)): `id`, `timestamp`, `user_id`, `application_id`,
`device_type`, `os`, `app_version`, `client_lib`, `geoip_country_code`, `city`,
`destination`. Other envelope columns (`app_session_id`, `funnel_type`,
`co_travelers`, `gclid`, `citizenship`, etc.) were not observed for this event
and were deliberately not added — an unobserved column is an invented column.

| Column | Type | Values |
|---|---|---|
| `shown_amount` | `Float64` | 100% present, 89.6% unique, range `[1502.0, 9000.0]` |
| `currency` | `LowCardinality(String)` | 7 codes: `INR AED SGD USD AUD GBP SAR` |
| `eligible` | `Bool` | 100% present; distinct 1 (`true` only) in this sample |

## ⚠ `application_id` does not join `application_started` — 0% overlap

`application_id` was normalized on ingest per D2 (32-char hex → 36-char
hyphenated UUID). The mandatory D2 overlap-check then ran against
`application_started` and returned **`overlap_pct = 0.0%`** (verified —
`load_report.md`, 2026-08-01) → per D2's action table, **STOP**: analyse this
table **standalone only**. Do not join it to the main application/user funnel
via `application_id` until re-tested. See [known_issues.md](../known_issues.md) → D2.

## Physical layout deviates from the 8 baseline tables — intentionally

`ENGINE = MergeTree`, `ORDER BY (toDate(timestamp), device_type, user_id, id)` —
does **not** lead with the random `id` UUID, per known_issues.md D8's explicit
instruction that new tables must not repeat that anti-pattern. Categoricals use
`LowCardinality(String)` per the same entry.

## Segment adoption — verified (`analysis/q04.md`, 2026-08-02)

"Adoption" = `express_checkout_selected` users ÷ `express_checkout_shown`
users in each segment, within the sample window (2026-06-08→2026-06-28):

- **Device:** flat — `android` 62.83% (338/538), `ios` 60.97% (428/702),
  `Desktop` 60.87% (56/92), `web-user-b2c` 58.18% (185/318). Spread only
  ~4.7pp — device is not a strong differentiator.
- **Geo:** `AU` highest (67.9%, n=81), then `SA` (64.62%, n=65), `SG`
  (63.95%, n=147); `AE` lowest (57.52%, n=153). `IN` is the only geo with a
  large enough base (n=1,007, 60.18%) to trust closely — the rest (n=65–153)
  are directional only.
- **Saved-method type** (share of the 1,007 selections, not a rate): `card`
  33.96%, `upi` 33.47%, `wallet` 32.57% — an even three-way split.

Bottom line: geo shows the clearest (still modest) skew; device and
saved-method type show little segmentation. Caveat: standalone-flow analysis
only (D2 blocks joining to the main funnel or user demographics beyond these
5 tables).

## Other risks carried forward (see `justification.md` for full reasoning)

- **D7** — `shown_amount` spans the same multi-currency set as
  `purchase_completed.value` (7 codes here, subset of the platform's 9). Never
  `sum`/`avg` without `GROUP BY currency`.
- **D9** — `device_type` mixes casing (`ios`, `android`, `web-user-b2c` vs
  `Desktop`) exactly as documented platform-wide.
- **D6** — 1,650 rows, 1,650 distinct `user_id` — no repeat users, consistent
  with the rest of the dataset.
