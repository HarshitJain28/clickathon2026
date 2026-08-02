---
id: table.channel_selected
kind: table
status: verified
confidence: high
source: out/03_status_sharing/ddl.sql + justification.md (schema); out/03_status_sharing/load_report.md — rows loaded, D2 overlap_pct; out/03_status_sharing/analysis/q01.md — verified set-membership step-through, confirms 1:1 pairing with link_generated; out/03_status_sharing/analysis/q02.md — channel mix
last_verified: 2026-08-02
links: [doc.envelope, doc.relationship, known_issue.d2_application_id_join_format, known_issue.d1_windowfunnel_loses_conversions, tables.index, table.share_clicked, table.link_generated, metric.share_completion_rate]
---

# `channel_selected`

Spec 03 (Visa Status Sharing). Fires when the sharer picks a channel — a
later and *optional* moment than `share_clicked` (1,144 of 1,600
`share_clicked` rows, 71.5%, have a corresponding `channel_selected`, so it
is not the same instant). → `CREATE TABLE`, not an `ALTER`. See
`out/03_status_sharing/justification.md` "CREATE vs ALTER call".

| | |
|---|---:|
| Rows | **1,144** (verified — `load_report.md`) |
| Distinct users | 1,144 (1 per user, per profile.md) |
| Distinct `share_id` | 1,144 (1 per row, 100% unique) |
| Sample time span | 2026-06-08 06:00 → 2026-07-01 09:21 (profile.md file-level span; not separately profiled per event) |
| Step-through ← `share_clicked` | 1,144 / 1,600 = **71.5%** — **verified** set-membership join on `share_id`, flat across `status_shared` (70.11%–73.33%) — `analysis/q01.md`, 2026-08-02 |

This table carries only a **subset** of the shared 30-column envelope (see
[the envelope](index.md)): `id`, `timestamp`, `user_id`, `application_id`,
`app_version`, `city`, `client_lib`, `destination`, `device_type`,
`geoip_country_code`, `os`.

| Column | Type | Values |
|---|---|---|
| `share_id` | `FixedString(32)` | 32-char lowercase-hex, 100% present, 0% null, 1,144/1,144 unique — see [share_clicked.md](share_clicked.md) for the type reasoning |
| `channel` | `LowCardinality(String)` | 4 values: `whatsapp`(625) / `copy_link`(214) / `email`(194) / `sms`(111) — the PM's channel-mix cut |
| `status_shared` | `LowCardinality(String)` | 3 values: `submitted`(394) / `processing`(385) / `approved`(365) — same domain as `share_clicked.status_shared` |

## ✅ Identical column set to `link_generated` — 1:1 pairing confirmed

`channel_selected` and [link_generated](link_generated.md) are byte-for-byte
identical in column set (`app_version, application_id, channel, city,
client_lib, destination, device_type, geoip_country_code, os, share_id,
status_shared, user_id`) and both have exactly **1,144 rows**
(`profile.md`). Kept as two separate tables, matching `spec.md`'s per-event
convention (analogous to the baseline's `pay_now_clicked` /
`purchase_completed` being near-adjacent, similarly-shaped events kept
separate) — this does not qualify for "ALTER an existing table" since both
are new to this spec. **Resolved 2026-08-02** (`analysis/q01.md`): the two
tables hold the **exact same set of 1,144 `share_id`s in every
`status_shared` bucket** (counts match exactly: 394/394 submitted, 365/365
approved, 385/385 processing) — confirming every `channel_selected` row
pairs 1:1 with a `link_generated` row. Functionally these may be treated as
the same funnel step for step-through purposes, though they remain two
tables in the schema.

## Channel mix — verified 2026-08-02 (`analysis/q02.md`)

WhatsApp dominates channel selection: 625/1,144 (54.63%), followed by
`copy_link` 214 (18.71%), `email` 194 (16.96%), `sms` 111 (9.70%). The same
ranking holds on the recipient side (`link_opened.channel`) — see
[link_opened.md](link_opened.md).

## ⚠ `application_id` does not join `application_started` — 0% overlap

`application_id` was normalized on ingest per D2. The mandatory D2
overlap-check then ran against `application_started` and returned
**`overlap_pct = 0.0%`** (verified — `load_report.md`, 2026-08-02) → per D2's
action table, **STOP**: analyse this table **standalone only**. See
[known_issues.md](../known_issues.md) → D2.

## Physical layout deviates from the 8 baseline tables — intentionally

`ENGINE = MergeTree`, `ORDER BY (toDate(timestamp), channel, user_id, id)` —
does not lead with the random `id` UUID, per known_issues.md D8. `channel`
takes the #2 slot (PM Q2: channel mix). See `justification.md` "ORDER BY /
PARTITION BY reasoning".

## Other risks carried forward (see `justification.md` for full reasoning)

- **D1** — step-through from `share_clicked` is now a **verified**
  set-membership join (`analysis/q01.md`, 2026-08-02 — see above). The link
  onward to the recipient-side tables (`link_opened`/`recipient_cta_clicked`)
  has **not** been checked.
- **D9** — `device_type` mixes casing exactly as documented platform-wide.
- **D6** — 1,144 rows, 1,144 distinct `user_id` — no repeat users.
