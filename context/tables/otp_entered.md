---
id: table.otp_entered
kind: table
status: verified
confidence: high
source: out/01_express_checkout/ddl.sql + justification.md (schema); load_report.md — rows loaded, D2 overlap_pct
last_verified: 2026-08-01
links: [doc.envelope, doc.relationship, known_issue.d2_application_id_join_format, known_issue.k1_ios_webkit_otp, tables.index]
---

# `otp_entered`

Spec 01 (Express Checkout). OTP submission during express checkout — a new
occurrence, its own step with its own timestamp; **not** folded into
`pay_now_clicked` (nothing in that table's column list or
`instrumentation_notes.md` ties OTP fields to the Pay Now tap).

**This is the first instrumentation able to test [K1](../known_issues.md)
(iOS WebKit OTP regression) directly** — `pay_now_clicked.md` had flagged this
as a gap; that gap is now closed at the schema level.

| | |
|---|---:|
| Rows | **1,007** (verified — `load_report.md`) |
| Distinct users | 1,007 (1 per user, per profile.md) |
| Step-through from `express_checkout_selected` | 1,007 / 1,007 = **100%** in this sample (row-count ratio, not a verified join) |
| Step-through → `express_payment_confirmed` | 836 / 1,007 = **83.02%** (row-count ratio; see "unexplained gap" below) |

This table carries only a **subset** of the shared 30-column envelope (see
[the envelope](index.md)): `id`, `timestamp`, `user_id`, `application_id`,
`device_type`, `os`, `app_version`, `client_lib`, `geoip_country_code`, `city`,
`destination`.

| Column | Type | Values |
|---|---|---|
| `otp_attempts` | `UInt8` | 100% present, range `[1, 3]`, distinct 3 |
| `otp_success` | `Bool` | 100% present; `true` 937 (93.0%) / `false` 70 (7.0%) |

## K1 — not yet re-tested, now instrumentable

`known_issues.md` K1 ("iOS WebKit OTP regression — users abandon at the pay
step") was **refuted** on `pay_now_clicked → purchase_completed` (iOS
converts *best*, especially in the Gulf). `otp_success` and confirmation rate
cut by `os` are the first columns able to test the underlying mechanism
directly, on their own merits — **but that re-test has not been run**: the
Context Agent has no live DB access, and `load_report.md` for this spec only
ran the D2 overlap check, not a K1 query. This is the next analysis to run
before K1's verdict can be updated. See [known_issues.md](../known_issues.md) → K1.

## ⚠ `application_id` does not join `application_started` — 0% overlap

Same D2 finding as the other 4 tables in this spec: normalized on ingest, but
overlap-check against `application_started` returned **`overlap_pct = 0.0%`**
(verified — `load_report.md`, 2026-08-01) → **STOP**, analyse standalone. See
[known_issues.md](../known_issues.md) → D2.

## Unexplained gap into `express_payment_confirmed`

1,007 `otp_entered` rows but only 836 `express_payment_confirmed` rows — a
171-row (17%) drop, while `otp_success = false` accounts for only 70 of those
rows. There is an unexplained ~101-row gap between a successful OTP and a
confirmed payment that no column here currently explains — the express-flow
analogue of the existing, unexplained `pay_now_clicked → purchase_completed`
leak (D-issue not yet opened; flagged here per `justification.md` for the
Analytics Agent to investigate).

## Other risks carried forward

- **D1** — do not use `windowFunnel`/`sequenceMatch` across this flow (or
  against `pay_now_clicked`/`purchase_completed`) without first checking
  monotonicity; the existing funnel showed only 52.2% of `purchase_completed`
  post-dating `document_uploaded`. Use set-membership counts unless
  `monotonic_share` ≥ ~0.99.
- **D6** — 1,007 rows, 1,007 distinct `user_id` — no repeat users. "Does a
  user retry Express after a failed OTP" is unanswerable from this dataset.
