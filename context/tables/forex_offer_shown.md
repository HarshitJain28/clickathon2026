---
id: table.forex_offer_shown
kind: table
status: verified
confidence: high
source: out/05_instant_forex/ddl.sql + justification.md (schema); out/05_instant_forex/load_report.md — rows loaded, D2 overlap_pct; out/05_instant_forex/analysis/q01.md — verified attach rate by destination; out/05_instant_forex/analysis/q03.md — verified full-funnel set membership; out/05_instant_forex/analysis/q04.md — verified monotonicity + segment skew
last_verified: 2026-08-02
links: [doc.envelope, doc.relationship, known_issue.d2_application_id_join_format, known_issue.d1_windowfunnel_loses_conversions, known_issue.d8_sort_key_defeats_primary_index, tables.index, table.currency_selected, table.forex_purchased, metric.forex_attach_rate]
---

# `forex_offer_shown`

Spec 05 (Instant Forex Add-on). Origin of the forex funnel — fires when the
forex add-on offer is rendered at checkout, alongside the visa purchase.
Its own row/moment, distinct from `purchase_completed` (own
`application_id` population, own event-specific fields, own row count —
2,900 vs. 7,054) — not the same instant as any existing baseline or spec
table's event. → `CREATE TABLE`, not an `ALTER`. See
`out/05_instant_forex/justification.md` "CREATE vs ALTER call".

| | |
|---|---:|
| Rows | **2,900** (verified — `load_report.md`) |
| Distinct users | 2,900 (1 per user, per profile.md) |
| Distinct `application_id` | 2,900 (100% unique, per profile.md) |
| Sample time span | 2026-06-08 06:00 → 2026-06-28 23:12 (profile.md file-level span; not separately profiled per event) |
| Step-through → `forex_purchased` (PM's headline attach-rate question) | 546 / 2,900 = **18.83%** — **verified** by `uniqExact(user_id)` set-membership join (`forex_purchased.user_id ⊆ forex_offer_shown.user_id`, 546/546 exact, no fan-out, both tables confirmed 1-row-per-user) and by 100% timestamp monotonicity (`forex_purchased.timestamp ≥ forex_offer_shown.timestamp` on all 546 matched pairs), per `analysis/q01.md` and `q04.md`, 2026-08-02 |

This table carries only a **subset** of the shared 30-column envelope (see
[the envelope](index.md)): `id`, `timestamp`, `user_id`, `application_id`,
`device_type`, `os`, `app_version`, `client_lib`, `geoip_country_code`,
`city`, `destination`. Other envelope columns (`app_session_id`,
`funnel_type`, `co_travelers`, `gclid`, `citizenship`, `duplicate_id`,
`is_back_filled`, etc.) were not observed for this event and were
deliberately not added — an unobserved column is an invented column.

| Column | Type | Values |
|---|---|---|
| `destination` | `FixedString(2)` | 14 of the platform's 27 destinations observed, e.g. `GR`(240)/`US`(236)/`ID`(224)/`TH`(223)/`VN`(217) — the PM's #1 cut ("by destination") and this spec's leading sort-key discriminator |
| `from_currency` | `FixedString(3)` | single value across all rows: `INR` |
| `to_currency` | `FixedString(3)` | 13 values, e.g. `EUR`(436)/`USD`(236)/`IDR`(224) — see [known_issues.md](../known_issues.md) → D7 for the currency-aggregation caveat |
| `fx_rate` | `Float64` | 100% present, 100% unique, range `[0.0379, 89.9827]` — **only this table carries `fx_rate`**, the rate shown at offer time |

## Attach rate is verified, and the funnel is perfectly nested

**2026-08-02 (source: `analysis/q01.md`, `q03.md`, `q04.md`).** The full
5-stage chain `forex_offer_shown → currency_selected → amount_entered →
forex_added_to_cart → forex_purchased` is now confirmed **perfectly
nested** by live `uniqExact(user_id)` set-membership joins — every
downstream stage's users are a 100% subset of the prior stage, all the way
back to this table — and 100% timestamp-monotonic (`q04.md`). See
[metrics/forex_attach_rate.md](../metrics/forex_attach_rate.md) for the
full by-`destination`/device/geo breakdown (best: US 24.58%; worst: AU
13.78%) and [currency_selected.md](currency_selected.md) for where the
funnel's big drop actually happens (only 35.62% of offers reach
`currency_selected`, vs. a comparatively small loss thereafter).

## ⚠ `application_id` does not join `application_started` — 0% overlap

`application_id` was normalized on ingest per D2 (32-char hex → 36-char
hyphenated UUID). The mandatory D2 overlap-check then ran against
`application_started` and returned **`overlap_pct = 0.0%`** (verified —
`load_report.md`, 2026-08-02) → per D2's action table, **STOP**: analyse
this table **standalone only**, the same verdict specs 01–04 all got. See
[known_issues.md](../known_issues.md) → D2.

## Physical layout deviates from the 8 baseline tables — intentionally

`ENGINE = MergeTree`, `ORDER BY (toDate(timestamp), destination, user_id,
id)` — does not lead with the random `id` UUID, per known_issues.md D8.
`destination` takes the #2 slot because it's the spec's own PM-cited
dimension ("attach rate … by `destination`", "which destinations attach
best") — see `justification.md` "ORDER BY / PARTITION BY reasoning". Note
this spec deliberately upgrades `destination` to `FixedString(2)` rather
than `LowCardinality(String)` (unlike specs 01–04's leading discriminators)
— see `justification.md`'s "Column choices" for the reasoning.

## Other risks carried forward (see `justification.md` for full reasoning)

- **D1** — the headline attach-rate question (`forex_offer_shown` →
  `forex_purchased`) is a multi-step funnel; **now verified** by
  `uniqExact(user_id)` set membership (after confirming 100% timestamp
  monotonicity), not `windowFunnel`/`sequenceMatch` — see `analysis/q01.md`,
  `q03.md`, `q04.md`, 2026-08-02.
- **D2** — see above; `application_id` 0% overlap, standalone only.
  Independently re-confirmed by all 4 of `analysis/q01.md`–`q04.md`, none of
  which found a working `application_id` path — every finding is scoped to
  the forex flow standalone.
- **D6** — 2,900 rows, 2,900 distinct `user_id` — no repeat users, consistent
  with the rest of the dataset. Retention/repeat-attach questions about the
  same user across multiple forex purchases cannot be answered from this
  data.
- **D7** — `fx_rate` is not itself a revenue field, but see
  [forex_purchased](forex_purchased.md)'s `addon_value_inr` for the
  revenue-shaped column this spec introduces.
- **D9** — `device_type` mixes casing (`ios`/`android`/`web-user-b2c` vs
  `Desktop`) exactly as documented platform-wide.
