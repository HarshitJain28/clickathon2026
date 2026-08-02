---
id: table.resumed_at_step
kind: table
status: verified
confidence: high
source: out/04_abondon_checkout_recovery_2/ddl.sql + justification.md (schema); out/04_abondon_checkout_recovery_2/load_report.md — rows loaded, D2 overlap_pct; out/04_checkout_recovery_3/ddl.sql + justification.md + load_report.md — independent resubmission 2026-08-02, identical row count and D2 verdict; out/04_checkout_recovery_3/analysis/q02.md — live count check resolves duplicate-load question (row count itself, not the step-through, still unjoined — see page body)
last_verified: 2026-08-02
links: [doc.envelope, doc.relationship, known_issue.d2_application_id_join_format, known_issue.d1_windowfunnel_loses_conversions, known_issue.k5_whatsapp_nudge, tables.index, table.reminder_cta_clicked, table.reconverted, metric.recovery_rate]
---

# `resumed_at_step`

Spec 04 (Abandoned Checkout Recovery). Fires when the user actually
returns to the funnel after a nudge — the genuine "return to the funnel"
event `known_issues.md` → K5 flagged as missing. Its own moment, logically
distinct from `reminder_cta_clicked` (tapping the nudge) even though both
have 268 rows in this sample. → `CREATE TABLE`, not an `ALTER`. See
`out/04_abondon_checkout_recovery_2/justification.md` "CREATE vs ALTER
call".

| | |
|---|---:|
| Rows | **268** (verified — `load_report.md`) |
| Distinct users | 268 (1 per user, per profile.md) |
| Distinct `application_id` | 268 (100% unique, per profile.md) |
| Sample time span | 2026-06-08 06:01 → 2026-07-01 00:00 (profile.md file-level span; not separately profiled per event) |
| Step-through ← `reminder_cta_clicked` | 268 / 268 = **100%** — unverified row-count ratio; no set-membership check has confirmed the same `user_id`/`application_id` set is involved |
| Step-through → `reconverted` | 93 / 268 = **34.70%** — unverified row-count ratio |

This table carries only a **subset** of the shared 30-column envelope (see
[the envelope](index.md)): `id`, `timestamp`, `user_id`, `application_id`,
`device_type`, `os`, `app_version`, `client_lib`, `geoip_country_code`,
`city`, `destination`, plus `drop_step` and `channel` (inherited context —
see [abandonment_detected.md](abandonment_detected.md) and
[reminder_sent.md](reminder_sent.md)). Other envelope columns were not
observed for this event and were deliberately not added.

| Column | Type | Values |
|---|---|---|
| `drop_step` | `LowCardinality(String)` | 4 values: `document_uploaded`(92) / `application_started`(70) / `destination_card_clicked`(58) / `pay_now_clicked`(48) — this table leads its sort key on `drop_step` (not `channel`), unlike the 3 nudge-lifecycle tables, because "the user returns to the funnel" is defined relative to the step dropped from |
| `channel` | `LowCardinality(String)` | 3 values: `push`(132) / `whatsapp`(78) / `email`(58) |

## ⚠ `application_id` does not join `application_started` — 0% overlap

`application_id` was normalized on ingest per D2 (32-char hex → 36-char
hyphenated UUID). The mandatory D2 overlap-check then ran against
`application_started` and returned **`overlap_pct = 0.0%`** (verified —
`load_report.md`, 2026-08-02) → per D2's action table, **STOP**: analyse
this table **standalone only**. See [known_issues.md](../known_issues.md)
→ D2.

## Physical layout deviates from the 8 baseline tables — intentionally, and differs from its nudge-lifecycle siblings

`ENGINE = MergeTree`, `ORDER BY (toDate(timestamp), drop_step, user_id,
id)` — does not lead with the random `id` UUID, per known_issues.md D8.
Unlike `reminder_sent`/`reminder_opened`/`reminder_cta_clicked` (which lead
on `channel`), this table leads on `drop_step` because its business
meaning is defined relative to the step returned to, making it the
natural join key back to `abandonment_detected` — same choice as that
table. See `justification.md` "ORDER BY / PARTITION BY reasoning".

## K5 (WhatsApp nudge) — this is the return event K5 said was missing

`known_issues.md` → K5 was previously unverifiable in part because "no
returning users exist" ([D6](../known_issues.md#d6--no-repeat-users)).
This table is the genuine return-to-funnel event that resolves that
blocker at the instrumentation level. **Still not computed:** whether
resumption differs by `channel` (e.g. does a WhatsApp nudge produce more
resumptions than push) — `analysis/q02.md`/`q03.md` re-tested K5's
channel/timing effect on final recovery, but both queries chain straight
from `reminder_cta_clicked`/`reminder_sent` to `reconverted`, bypassing
this table entirely, so `resumed_at_step`'s own role (as distinct from
`reminder_cta_clicked`'s) remains unverified. See
[reminder_sent.md](reminder_sent.md) for the channel funnel that **was**
verified, and [known_issues.md](../known_issues.md) → K5 for the full
verdict.

## ⚠ 2026-08-02 — spec resubmitted as `04_checkout_recovery_3`, same data — row count now confirmed, step-through still open

`out/04_checkout_recovery_3` re-profiled/re-justified/re-loaded this exact
table a second time — `ddl.sql` uses `CREATE TABLE IF NOT EXISTS` (no-op,
table already existed), `load_report.md` reports the **identical** row
count (268) and D2 verdict (`overlap_pct = 0.0%`, STOP). Whether this
second load's `INSERT` step re-inserted the same 268 rows a second time
(doubling the true live count to 536) was an open question this wiki
could not resolve without live DB access.

**Row-count duplication resolved 2026-08-02 (source: `analysis/q02.md`).**
The file's live count check across all 6 spec-04 tables confirmed
`resumed_at_step` at exactly **268**, matching the documented figure with
no growth — no duplication. See [known_issues.md](../known_issues.md) →
D2 and the same resolution on
[abandonment_detected.md](abandonment_detected.md) and its 4 sibling
pages. **Not resolved:** this table's own step-through ratios
(`reminder_cta_clicked → resumed_at_step` = 100%, `→ reconverted` =
34.70%) — every set-membership join run so far skips this table
entirely, so those two ratios remain unverified row-count ratios (see D1
addendum in [known_issues.md](../known_issues.md)).

## Other risks carried forward (see `justification.md` for full reasoning)

- **D1** — no query has joined through this table specifically yet
  (`analysis/q02.md`/`q03.md` bypass it); treat its step-through ratios as
  directional only. Its row count is confirmed non-duplicated (see above).
- **D2** — see above; `application_id` 0% overlap, standalone only.
- **D9** — `device_type` mixes casing, exactly as documented
  platform-wide.
- **D6** — 268 rows, 268 distinct `user_id` — no repeat users here.
