---
id: table.reminder_cta_clicked
kind: table
status: verified
confidence: high
source: out/04_abondon_checkout_recovery_2/ddl.sql + justification.md (schema); out/04_abondon_checkout_recovery_2/load_report.md — rows loaded, D2 overlap_pct; out/04_checkout_recovery_3/ddl.sql + justification.md + load_report.md — independent resubmission 2026-08-02, identical row count and D2 verdict; out/04_checkout_recovery_3/analysis/q02.md — verified click-rate-by-channel via set-membership join, resolves duplicate-load question
last_verified: 2026-08-02
links: [doc.envelope, doc.relationship, known_issue.d2_application_id_join_format, known_issue.d1_windowfunnel_loses_conversions, tables.index, table.reminder_opened, table.resumed_at_step, metric.recovery_rate]
---

# `reminder_cta_clicked`

Spec 04 (Abandoned Checkout Recovery). Fires when the user taps through
the nudge's CTA — the third step of the nudge lifecycle, its own
moment/row-count (268). → `CREATE TABLE`, not an `ALTER`. See
`out/04_abondon_checkout_recovery_2/justification.md` "CREATE vs ALTER
call".

| | |
|---|---:|
| Rows | **268** (verified — `load_report.md`) |
| Distinct users | 268 (1 per user, per profile.md) |
| Distinct `application_id` | 268 (100% unique, per profile.md) |
| Sample time span | 2026-06-08 06:01 → 2026-07-01 00:00 (profile.md file-level span; not separately profiled per event) |
| Step-through ← `reminder_opened` | 268 / 690 = **38.84%** — **verified** by set-membership join on `user_id` (`analysis/q02.md`/`q03.md`, exact reproduction, no fan-out) |
| Step-through → `resumed_at_step` | 268 / 268 = **100%** — unverified row-count ratio; every joined qNN query so far skips straight from this table to `reconverted`, never confirming membership through `resumed_at_step` itself — same row count as `resumed_at_step` but a logically distinct moment (tapping the nudge vs. actually landing back in the flow — see `justification.md` "CREATE vs ALTER call") |

This table carries only a **subset** of the shared 30-column envelope (see
[the envelope](index.md)): `id`, `timestamp`, `user_id`, `application_id`,
`device_type`, `os`, `app_version`, `client_lib`, `geoip_country_code`,
`city`, `destination`, plus `drop_step` and `channel` (inherited context —
see [reminder_sent.md](reminder_sent.md)). Other envelope columns were not
observed for this event and were deliberately not added.

| Column | Type | Values |
|---|---|---|
| `channel` | `LowCardinality(String)` | 3 values: `push`(132) / `whatsapp`(78) / `email`(58) |
| `drop_step` | `LowCardinality(String)` | 4 values: `document_uploaded`(92) / `application_started`(70) / `destination_card_clicked`(58) / `pay_now_clicked`(48) |

## Click rate by channel (of `reminder_opened`) — verified, 2026-08-02

| Channel | Opened | Clicked | Click rate |
|---|---:|---:|---:|
| **push** | 322 | 132 | **40.99%** |
| email | 144 | 58 | 40.28% |
| whatsapp | 224 | 78 | 34.82% |

Push and email convert an open into a click at a slightly higher rate than
WhatsApp, even though WhatsApp leads on raw open rate — **verified** by
`analysis/q02.md`'s live set-membership join. See
[reminder_sent.md](reminder_sent.md) for the full channel funnel and the
K5 verdict in [known_issues.md](../known_issues.md).

## ⚠ `application_id` does not join `application_started` — 0% overlap

`application_id` was normalized on ingest per D2 (32-char hex → 36-char
hyphenated UUID). The mandatory D2 overlap-check then ran against
`application_started` and returned **`overlap_pct = 0.0%`** (verified —
`load_report.md`, 2026-08-02) → per D2's action table, **STOP**: analyse
this table **standalone only**. See [known_issues.md](../known_issues.md)
→ D2.

## Physical layout deviates from the 8 baseline tables — intentionally

`ENGINE = MergeTree`, `ORDER BY (toDate(timestamp), channel, user_id,
id)` — does not lead with the random `id` UUID, per known_issues.md D8,
matching `reminder_sent`/`reminder_opened`'s template. See
`justification.md` "ORDER BY / PARTITION BY reasoning".

## ⚠ 2026-08-02 — spec resubmitted as `04_checkout_recovery_3`, same data — duplicate-load question now resolved

`out/04_checkout_recovery_3` re-profiled/re-justified/re-loaded this exact
table a second time — `ddl.sql` uses `CREATE TABLE IF NOT EXISTS` (no-op,
table already existed), `load_report.md` reports the **identical** row
count (268) and D2 verdict (`overlap_pct = 0.0%`, STOP). Whether this
second load's `INSERT` step re-inserted the same 268 rows a second time
(doubling the true live count to 536) was an open question this wiki
could not resolve without live DB access.

**Resolved 2026-08-02 (source: `analysis/q02.md`).** The file's live
count check across all 6 spec-04 tables confirmed `reminder_cta_clicked`
at exactly **268**, matching the documented figure with no growth — no
duplication. See [known_issues.md](../known_issues.md) → D2 and the same
resolution on [abandonment_detected.md](abandonment_detected.md) and its
4 sibling pages.

## Other risks carried forward (see `justification.md` for full reasoning)

- **D1** — the `reminder_opened → reminder_cta_clicked` step (and the
  chain onward to `reconverted`, skipping `resumed_at_step`) is now
  verified by set-membership join (`analysis/q02.md`, `q03.md`,
  2026-08-02).
- **D2** — see above; `application_id` 0% overlap, standalone only.
- **D9** — `device_type` mixes casing, exactly as documented
  platform-wide.
- **D6** — 268 rows, 268 distinct `user_id` — no repeat users here.
