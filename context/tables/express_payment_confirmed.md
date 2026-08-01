---
id: table.express_payment_confirmed
kind: table
status: verified
confidence: high
source: out/01_express_checkout/ddl.sql + justification.md (schema); load_report.md — rows loaded, D2 overlap_pct
last_verified: 2026-08-01
links: [doc.envelope, doc.relationship, known_issue.d2_application_id_join_format, known_issue.k1_ios_webkit_otp, tables.index]
---

# `express_payment_confirmed`

Spec 01 (Express Checkout). Payment success in the express flow — the
**conversion event for Express**. Distinct row population from
`purchase_completed` (own `application_id` set, own nested `payment.*` shape);
no context-wiki sentence ties its grain to `purchase_completed`'s the way
spec 05 (Instant Forex) is explicitly tied to `purchase_completed`'s add-on
columns, so it is its own table, not an `ALTER`.

| | |
|---|---:|
| Rows | **836** (verified — `load_report.md`) |
| Distinct users | 836 (1 per user, per profile.md) |
| Step-through from `otp_entered` | 836 / 1,007 = **83.02%** (row-count ratio, not a verified join; see "unexplained gap" on [otp_entered](otp_entered.md)) |

This table carries only a **subset** of the shared 30-column envelope (see
[the envelope](index.md)): `id`, `timestamp`, `user_id`, `application_id`,
`device_type`, `os`, `app_version`, `client_lib`, `geoip_country_code`, `city`,
`destination`.

| Column | Type | Notes |
|---|---|---|
| `payment_amount` | `Float64` | flattened from `payment.amount`; 100% present, 95.6% unique, range `[1509.0, 8997.0]` |
| `payment_currency` | `LowCardinality(String)` | flattened from `payment.currency`; 7 codes: `INR SGD AED USD AUD GBP SAR` |
| `payment_latency_ms` | `UInt16` | flattened from `payment.latency_ms`; 100% present, range `[607, 3999]` |

The source event's nested `payment.*` object was flattened to typed columns
(fixed, known 3-field shape) rather than kept as JSON.

## ⚠ `application_id` does not join `application_started` — 0% overlap

Same D2 finding as the other 4 tables in this spec: normalized on ingest, but
overlap-check against `application_started` returned **`overlap_pct = 0.0%`**
(verified — `load_report.md`, 2026-08-01) → **STOP**, analyse standalone. See
[known_issues.md](../known_issues.md) → D2.

## Other risks carried forward

- **D7** — `payment_amount` spans the same multi-currency set as
  `purchase_completed.value` (7 codes here, subset of the platform's 9). Never
  `sum`/`avg` without `GROUP BY payment_currency`.
- **D9** — `device_type` casing mixes `ios`/`android`/`web-user-b2c` vs `Desktop`.
- **D6** — 836 rows, 836 distinct `user_id` — no repeat users.
- **K1** — see [otp_entered](otp_entered.md); `otp_success`/confirmation rate
  by `os` on this table is the first direct test of K1, not yet run.
