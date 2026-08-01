---
id: table.express_checkout_selected
kind: table
status: verified
confidence: high
source: out/01_express_checkout/ddl.sql + justification.md (schema); load_report.md — rows loaded, D2 overlap_pct; analysis/q04.md — verified set-membership step-through
last_verified: 2026-08-02
links: [doc.envelope, doc.relationship, known_issue.d2_application_id_join_format, tables.index]
---

# `express_checkout_selected`

Spec 01 (Express Checkout). User taps the Express button — a distinct
occurrence from `pay_now_clicked`, on a flow that explicitly skips the
standard payment form. See `out/01_express_checkout/justification.md`.

| | |
|---|---:|
| Rows | **1,007** (verified — `load_report.md`) |
| Distinct users | 1,007 (1 per user, per profile.md) |
| Step-through from `express_checkout_shown` | **61.03%** (1,007 / 1,650 — **verified** exact set-membership subset, `analysis/q04.md`, 2026-08-02) |
| Step-through → `saved_method_used` / `otp_entered` | 1,007 / 1,007 = **100%** in this sample (row-count ratio) |

This table carries only a **subset** of the shared 30-column envelope (see
[the envelope](index.md)): `id`, `timestamp`, `user_id`, `application_id`,
`device_type`, `os`, `app_version`, `client_lib`, `geoip_country_code`, `city`,
`destination`.

| Column | Type | Values |
|---|---|---|
| `saved_method_type` | `LowCardinality(String)` | 3 values: `card upi wallet` — 100% present |

**Not `Enum8`:** `pay_now_clicked.payment_method`'s domain (`applePay card
netbanking upi wallet`) is larger and not closed platform-wide, so an enum here
risks insert-time rejection the moment Express adds a method. Note also:
Express's observed `saved_method_type` domain (`card`/`upi`/`wallet`) is a
**strict subset** of `pay_now_clicked.payment_method` — Express appears not to
support Apple Pay or netbanking today. Worth confirming with product before
comparing the two columns 1:1.

## ⚠ `application_id` does not join `application_started` — 0% overlap

Same D2 finding as the other 4 tables in this spec: normalized on ingest, but
overlap-check against `application_started` returned **`overlap_pct = 0.0%`**
(verified — `load_report.md`, 2026-08-01) → **STOP**, analyse standalone. See
[known_issues.md](../known_issues.md) → D2.

## Other risks carried forward

- **D8** — `ORDER BY (toDate(timestamp), device_type, user_id, id)`, does not
  lead with `id`.
- **D9** — `device_type` casing mixes `ios`/`android`/`web-user-b2c` vs `Desktop`.
- **D6** — 1,007 rows, 1,007 distinct `user_id` — no repeat users.
