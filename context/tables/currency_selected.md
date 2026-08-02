---
id: table.currency_selected
kind: table
status: verified
confidence: high
source: out/05_instant_forex/ddl.sql + justification.md (schema); out/05_instant_forex/load_report.md — rows loaded, D2 overlap_pct; out/05_instant_forex/analysis/q03.md — verified set-membership pairing with amount_entered and step-through from forex_offer_shown
last_verified: 2026-08-02
links: [doc.envelope, doc.relationship, known_issue.d2_application_id_join_format, known_issue.d1_windowfunnel_loses_conversions, tables.index, table.forex_offer_shown, table.amount_entered]
---

# `currency_selected`

Spec 05 (Instant Forex Add-on). Fires when the user engages with the
currency picker on the forex offer — a later, optional moment than
`forex_offer_shown` (only 1,033 of 2,900 shown-events, 35.62%, have a
corresponding row here). → `CREATE TABLE`, not an `ALTER`. See
`out/05_instant_forex/justification.md` "CREATE vs ALTER call".

| | |
|---|---:|
| Rows | **1,033** (verified — `load_report.md`) |
| Distinct users | 1,033 (1 per user, per profile.md) |
| Distinct `application_id` | 1,033 (100% unique, per profile.md) |
| Sample time span | 2026-06-08 06:00 → 2026-06-28 23:12 (profile.md file-level span; not separately profiled per event) |
| Step-through ← `forex_offer_shown` | 1,033 / 2,900 = **35.62%** — **verified** by `uniqExact(user_id)` set-membership join (100% nested), per `analysis/q03.md`, 2026-08-02. This is **the single biggest leak in the whole forex funnel** — of the two segments `q03.md` compared (offer→amount_entered vs. added_to_cart→purchased), this step accounts for the entire 64.38%/1,867-user drop between `forex_offer_shown` and `amount_entered` |

This table carries only a **subset** of the shared 30-column envelope (see
[the envelope](index.md)): `id`, `timestamp`, `user_id`, `application_id`,
`device_type`, `os`, `app_version`, `client_lib`, `geoip_country_code`,
`city`, `destination`. No `amount`/`addon_value_inr`/`fx_rate` — not in
`profile.md` for this event.

| Column | Type | Values |
|---|---|---|
| `destination` | `FixedString(2)` | 14 values, e.g. `US`(99)/`GR`(83)/`TH`(83) |
| `from_currency` | `FixedString(3)` | single value across all rows: `INR` |
| `to_currency` | `FixedString(3)` | 13 values, e.g. `EUR`(161)/`USD`(99)/`THB`(83) — see [known_issues.md](../known_issues.md) → D7 |

## Row count coincides exactly with `amount_entered` — now CONFIRMED, not just a coincidence

Both `currency_selected` and [amount_entered](amount_entered.md) have
exactly **1,033 rows**, and `profile.md`'s per-field breakdowns (`city`,
`device_type`, `geoip_country_code`) show identical counts across the two
tables (e.g. `Mumbai`(626) in both). **2026-08-02 (source:
`analysis/q03.md`):** a live `uniqExact(user_id)` set-membership join
confirms this is a true 1:1 pairing — every one of the 1,033
`currency_selected` users has a matching `amount_entered` row (100%
step-through, direct membership check, not a row-count coincidence) —
matching the pattern spec 03's `channel_selected`/`link_generated` turned
out to have (`out/03_status_sharing/analysis/q01.md`). Once a user picks a
currency, they always enter an amount.

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

- **D1** — step-through from `forex_offer_shown` is now **verified** by set
  membership, per `analysis/q03.md`, 2026-08-02.
- **D2** — see above; `application_id` 0% overlap, standalone only.
  Independently re-confirmed by all 4 of `analysis/q01.md`–`q04.md`.
- **D6** — 1,033 rows, 1,033 distinct `user_id` — no repeat users.
- **D9** — `device_type` mixes casing exactly as documented platform-wide.
