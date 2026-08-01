---
id: table.saved_method_used
kind: table
status: verified
confidence: high
source: out/01_express_checkout/ddl.sql + justification.md (schema); load_report.md — rows loaded, D2 overlap_pct
last_verified: 2026-08-01
links: [doc.envelope, doc.relationship, known_issue.d2_application_id_join_format, tables.index]
---

# `saved_method_used`

Spec 01 (Express Checkout). The saved payment instrument being loaded for the
express flow — a new occurrence with no analogue in the 8 existing tables.

| | |
|---|---:|
| Rows | **1,007** (verified — `load_report.md`) |
| Distinct users | 1,007 (1 per user, per profile.md) |
| Step-through from `express_checkout_selected` | 1,007 / 1,007 = **100%** in this sample (row-count ratio, not a verified join) |

This table carries only a **subset** of the shared 30-column envelope (see
[the envelope](index.md)): `id`, `timestamp`, `user_id`, `application_id`,
`device_type`, `os`, `app_version`, `client_lib`, `geoip_country_code`, `city`,
`destination`.

**No event-specific columns.** `profile.md` shows zero fields beyond the 9
envelope-subset columns (`app_version`, `application_id`, `city`, `client_lib`,
`destination`, `device_type`, `geoip_country_code`, `os`, `user_id`) plus row
identity — per the column policy (an unobserved column is an invented column),
none were added. This table is an envelope subset only.

## ⚠ `application_id` does not join `application_started` — 0% overlap

Same D2 finding as the other 4 tables in this spec: normalized on ingest, but
overlap-check against `application_started` returned **`overlap_pct = 0.0%`**
(verified — `load_report.md`, 2026-08-01) → **STOP**, analyse standalone. See
[known_issues.md](../known_issues.md) → D2.

## Other risks carried forward

- **D8** — `ORDER BY (toDate(timestamp), device_type, user_id, id)`, does not
  lead with `id`.
- **D6** — 1,007 rows, 1,007 distinct `user_id` — no repeat users.
