---
id: table.link_generated
kind: table
status: verified
confidence: high
source: out/03_status_sharing/ddl.sql + justification.md (schema); out/03_status_sharing/load_report.md — rows loaded, D2 overlap_pct; out/03_status_sharing/analysis/q01.md — confirms 1:1 pairing with channel_selected
last_verified: 2026-08-02
links: [doc.envelope, doc.relationship, known_issue.d2_application_id_join_format, known_issue.d1_windowfunnel_loses_conversions, tables.index, table.channel_selected, table.link_opened]
---

# `link_generated`

Spec 03 (Visa Status Sharing). Fires when the share link is actually
created. → `CREATE TABLE`, not an `ALTER` — see
`out/03_status_sharing/justification.md` "CREATE vs ALTER call" and the
identical-schema note below.

| | |
|---|---:|
| Rows | **1,144** (verified — `load_report.md`) |
| Distinct users | 1,144 (1 per user, per profile.md) |
| Distinct `share_id` | 1,144 (1 per row, 100% unique) |
| Sample time span | 2026-06-08 06:00 → 2026-07-01 09:21 (profile.md file-level span; not separately profiled per event) |
| Step-through → `link_opened` | not directly comparable: `link_opened` has no `user_id`/joins on `share_id` instead, and its 922 distinct `share_id`s vs. this table's 1,144 have **not** been set-membership checked by any `analysis/qNN.md` file yet (the sharer-side ↔ recipient-side leg remains open — see [link_opened.md](link_opened.md)) |

This table carries only a **subset** of the shared 30-column envelope (see
[the envelope](index.md)): `id`, `timestamp`, `user_id`, `application_id`,
`app_version`, `city`, `client_lib`, `destination`, `device_type`,
`geoip_country_code`, `os`.

| Column | Type | Values |
|---|---|---|
| `share_id` | `FixedString(32)` | 32-char lowercase-hex, 100% present, 0% null, 1,144/1,144 unique — see [share_clicked.md](share_clicked.md) for the type reasoning |
| `channel` | `LowCardinality(String)` | 4 values: `whatsapp`(625) / `copy_link`(214) / `email`(194) / `sms`(111) |
| `status_shared` | `LowCardinality(String)` | 3 values: `submitted`(394) / `processing`(385) / `approved`(365) |

## ✅ Identical column set to `channel_selected` — 1:1 pairing confirmed

See [channel_selected.md](channel_selected.md) — byte-for-byte identical
column set and row count (1,144 each). Kept as two tables per `spec.md`'s
per-event convention. **Resolved 2026-08-02** (`analysis/q01.md`): the two
tables hold the exact same 1,144 `share_id`s in every `status_shared`
bucket — confirmed 1:1 pairing, functionally the same funnel step for
step-through purposes.

## ⚠ `application_id` does not join `application_started` — 0% overlap

`application_id` was normalized on ingest per D2. The mandatory D2
overlap-check then ran against `application_started` and returned
**`overlap_pct = 0.0%`** (verified — `load_report.md`, 2026-08-02) → per D2's
action table, **STOP**: analyse this table **standalone only**. See
[known_issues.md](../known_issues.md) → D2.

## Physical layout deviates from the 8 baseline tables — intentionally

`ENGINE = MergeTree`, `ORDER BY (toDate(timestamp), channel, user_id, id)` —
does not lead with the random `id` UUID, per known_issues.md D8. Same key
shape as `channel_selected` (PM Q2: channel mix). See `justification.md`
"ORDER BY / PARTITION BY reasoning".

## Other risks carried forward (see `justification.md` for full reasoning)

- **D1** — 1:1 pairing with `channel_selected` verified 2026-08-02
  (`analysis/q01.md` — see above). The link onward to `link_opened` (922
  distinct `share_id`s vs. this table's 1,144) has **not** been checked by
  any `analysis/qNN.md` file yet.
- **D9** — `device_type` mixes casing exactly as documented platform-wide.
- **D6** — 1,144 rows, 1,144 distinct `user_id` — no repeat users.
