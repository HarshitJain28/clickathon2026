---
id: table.amount_entered
kind: table
status: verified
confidence: high
source: out/05_instant_forex/ddl.sql + justification.md (schema); out/05_instant_forex/load_report.md — rows loaded, D2 overlap_pct; out/05_instant_forex/analysis/q03.md — verified set-membership step-through both directions
last_verified: 2026-08-02
links: [doc.envelope, doc.relationship, known_issue.d2_application_id_join_format, known_issue.d1_windowfunnel_loses_conversions, tables.index, table.currency_selected, table.forex_added_to_cart]
---

# `amount_entered`

Spec 05 (Instant Forex Add-on). Fires when the user enters the amount to
convert, its own moment distinct from `currency_selected`. → `CREATE
TABLE`, not an `ALTER`. See `out/05_instant_forex/justification.md`
"CREATE vs ALTER call".

| | |
|---|---:|
| Rows | **1,033** (verified — `load_report.md`) |
| Distinct users | 1,033 (1 per user, per profile.md) |
| Distinct `application_id` | 1,033 (100% unique, per profile.md) |
| Sample time span | 2026-06-08 06:00 → 2026-06-28 23:12 (profile.md file-level span; not separately profiled per event) |
| Step-through ← `currency_selected` | 1,033 / 1,033 = **100%** — **verified** by `uniqExact(user_id)` set-membership join, a true 1:1 pairing, per `analysis/q03.md`, 2026-08-02 (see [currency_selected.md](currency_selected.md)'s "now CONFIRMED" note) |
| Step-through → `forex_added_to_cart` | 725 / 1,033 = **70.18%** — **verified** by set-membership join, per `analysis/q03.md`, 2026-08-02 |

This table carries only a **subset** of the shared 30-column envelope (see
[the envelope](index.md)): `id`, `timestamp`, `user_id`, `application_id`,
`device_type`, `os`, `app_version`, `client_lib`, `geoip_country_code`,
`city`, `destination`.

| Column | Type | Values |
|---|---|---|
| `destination` | `FixedString(2)` | 14 values, e.g. `US`(99)/`GR`(83)/`TH`(83) |
| `from_currency` | `FixedString(3)` | single value across all rows: `INR` |
| `to_currency` | `FixedString(3)` | 13 values, e.g. `EUR`(161)/`USD`(99)/`THB`(83) — see [known_issues.md](../known_issues.md) → D7 |
| `amount` | `UInt16` | 100% present, 6 distinct values, range `[200, 1500]` — the INR amount entered to convert |

## ⚠ `application_id` does not join `application_started` — 0% overlap

`application_id` was normalized on ingest per D2. The mandatory D2
overlap-check then ran against `application_started` and returned
**`overlap_pct = 0.0%`** (verified — `load_report.md`, 2026-08-02) → per D2's
action table, **STOP**: analyse this table **standalone only**. See
[known_issues.md](../known_issues.md) → D2.

## Physical layout deviates from the 8 baseline tables — intentionally

`ENGINE = MergeTree`, `ORDER BY (toDate(timestamp), destination, user_id,
id)` — does not lead with the random `id` UUID, per known_issues.md D8. See
`justification.md` "ORDER BY / PARTITION BY reasoning".

## Other risks carried forward (see `justification.md` for full reasoning)

- **D1** — both step-through ratios above are now **verified** by set
  membership, per `analysis/q03.md`, 2026-08-02.
- **D2** — see above; `application_id` 0% overlap, standalone only.
  Independently re-confirmed by all 4 of `analysis/q01.md`–`q04.md`.
- **D6** — 1,033 rows, 1,033 distinct `user_id` — no repeat users.
- **D9** — `device_type` mixes casing exactly as documented platform-wide.
