---
id: table.reminder_sent
kind: table
status: verified
confidence: high
source: out/04_abondon_checkout_recovery_2/ddl.sql + justification.md (schema); out/04_abondon_checkout_recovery_2/load_report.md — rows loaded, D2 overlap_pct; out/04_checkout_recovery_3/ddl.sql + justification.md + load_report.md — independent resubmission 2026-08-02, identical row count and D2 verdict; out/04_checkout_recovery_3/analysis/q02.md — verified channel funnel (K5 re-test), resolves duplicate-load question; out/04_checkout_recovery_3/analysis/q03.md — verified timing (hours_since_drop) has no effect, resolves duplicate-load question
last_verified: 2026-08-02
links: [doc.envelope, doc.relationship, known_issue.d2_application_id_join_format, known_issue.d1_windowfunnel_loses_conversions, known_issue.k5_whatsapp_nudge, tables.index, table.abandonment_detected, table.reminder_opened, metric.recovery_rate]
---

# `reminder_sent`

Spec 04 (Abandoned Checkout Recovery). Fires when a nudge is sent to a
detected drop-off — the first of a 3-step nudge lifecycle
(send → open → click), each its own moment/row-count, none coinciding with
any existing table's event. → `CREATE TABLE`, not an `ALTER`. See
`out/04_abondon_checkout_recovery_2/justification.md` "CREATE vs ALTER
call".

| | |
|---|---:|
| Rows | **2,300** (verified — `load_report.md`) |
| Distinct users | 2,300 (1 per user, per profile.md) |
| Distinct `application_id` | 2,300 (100% unique, per profile.md) |
| Sample time span | 2026-06-08 06:01 → 2026-07-01 00:00 (profile.md file-level span; not separately profiled per event) |
| Step-through ← `abandonment_detected` | 2,300 / 2,300 = **100%** — unverified row-count ratio (every detected drop appears to get a reminder; no set-membership check has joined the two tables directly — see [abandonment_detected.md](abandonment_detected.md)) |
| Step-through → `reminder_opened` | 690 / 2,300 = **30.00%** — **verified** by set-membership join on `user_id` (`analysis/q02.md`/`q03.md`, exact reproduction, no fan-out) |

This table carries only a **subset** of the shared 30-column envelope (see
[the envelope](index.md)): `id`, `timestamp`, `user_id`, `application_id`,
`device_type`, `os`, `app_version`, `client_lib`, `geoip_country_code`,
`city`, `destination`, plus `drop_step` (inherited context — see
[abandonment_detected.md](abandonment_detected.md)). Other envelope
columns were not observed for this event and were deliberately not added.

| Column | Type | Values |
|---|---|---|
| `channel` | `LowCardinality(String)` | 3 values: `push`(1,138) / `email`(678) / `whatsapp`(484) — the PM's #1 cut for the nudge-lifecycle tables |
| `hours_since_drop` | `UInt8` | 100% present, 0% null, range `[1, 48]`, 5 distinct values — PM's timing cut |

## Channel funnel — verified, 2026-08-02 (K5 re-test)

| Channel | Sent | Opened | Open rate | Clicked | Click rate (of opened) | Reconverted | Recovery rate (of sent) |
|---|---:|---:|---:|---:|---:|---:|---:|
| whatsapp | 484 | 224 | **46.28%** | 78 | 34.82% | 21 | 4.34% |
| push | 1,138 | 322 | 28.30% | 132 | **40.99%** | 53 | **4.66%** |
| email | 678 | 144 | 21.24% | 58 | 40.28% | 19 | 2.80% |

**Verified** by live set-membership join on `user_id`
(`analysis/q02.md`) — `reminder_sent → reminder_opened →
reminder_cta_clicked → reconverted`, and the numbers match the
row-count-ratio picture exactly (no fan-out; every `reminder_opened`
row's `channel` matches its paired `reminder_sent` row's `channel`,
690/690). WhatsApp leads clearly on open rate (46.28% vs push 28.30%,
email 21.24%) but converts opens to clicks/reconversions at the *lowest*
rate of the three (34.82% vs ~40%); push — weaker at attracting opens —
ends up best end-to-end (4.66% vs. WhatsApp's 4.34%), with email lowest
throughout. This is the K5 re-test: WhatsApp drives engagement, but is
not the best channel for final recovery. See
[known_issues.md](../known_issues.md) → K5 and
[metrics/recovery_rate.md](../metrics/recovery_rate.md).

## Timing (`hours_since_drop`) — verified, no effect (`analysis/q03.md`)

| Sent at | Sent | Opened | Open rate | Clicked | Reconverted | Recovery rate (of sent) |
|---|---:|---:|---:|---:|---:|---:|
| 1h | 433 | 141 | 32.56% | 49 | 15 | 3.46% |
| 3h | 484 | 135 | 27.89% | 53 | 20 | 4.13% |
| 6h | 496 | 153 | 30.85% | 60 | 24 | **4.84%** (best) |
| 24h | 469 | 141 | 30.06% | 52 | 17 | 3.62% |
| 48h | 418 | 120 | 28.71% | 54 | 17 | 4.07% |
| **Overall** | **2,300** | **690** | 30.00% | **268** | **93** | 4.04% |

Verified by the same set-membership join (`analysis/q03.md`). Recovery
rate ranges only 3.46%–4.84% across all five delays with **no monotonic
pattern** — every bucket sits within ~1 standard error of the pooled
4.04% base rate (binomial SE ~0.9–1.0pp, n≈420–500/bucket), consistent
with sampling noise rather than a real "send sooner/later" effect. Timing
does not matter for this metric.

## ⚠ `application_id` does not join `application_started` — 0% overlap

`application_id` was normalized on ingest per D2 (32-char hex → 36-char
hyphenated UUID). The mandatory D2 overlap-check then ran against
`application_started` and returned **`overlap_pct = 0.0%`** (verified —
`load_report.md`, 2026-08-02) → per D2's action table, **STOP**: analyse
this table **standalone only**. See [known_issues.md](../known_issues.md)
→ D2.

## Physical layout deviates from the 8 baseline tables — intentionally

`ENGINE = MergeTree`, `ORDER BY (toDate(timestamp), channel, user_id,
id)` — does not lead with the random `id` UUID, per known_issues.md D8.
`channel` (3 values) takes the #2 slot because it's this table's own
leading discriminator and the PM's cut for "which channel recovers best" —
see `justification.md` "ORDER BY / PARTITION BY reasoning".

## ⚠ 2026-08-02 — spec resubmitted as `04_checkout_recovery_3`, same data — duplicate-load question now resolved

`out/04_checkout_recovery_3` re-profiled/re-justified/re-loaded this exact
table a second time — `ddl.sql` uses `CREATE TABLE IF NOT EXISTS` (no-op,
table already existed), `load_report.md` reports the **identical** row
count (2,300) and D2 verdict (`overlap_pct = 0.0%`, STOP). Whether this
second load's `INSERT` step re-inserted the same 2,300 rows a second time
(doubling the true live count to 4,600) was an open question this wiki
could not resolve without live DB access.

**Resolved 2026-08-02 (source: `analysis/q02.md`, `q03.md`).** Both files
independently re-checked this table's live row count as part of their
join and got exactly **2,300**, matching the documented figure with no
growth — no duplication. See [known_issues.md](../known_issues.md) → D2
and the same resolution on [abandonment_detected.md](abandonment_detected.md)
and its 4 sibling pages.

## Other risks carried forward (see `justification.md` for full reasoning)

- **D1** — the `→ reminder_opened` step and the full channel/timing
  funnels are now verified by set-membership join (`analysis/q02.md`,
  `q03.md`, 2026-08-02); the `abandonment_detected →` step remains an
  unverified row-count ratio.
- **D2** — see above; `application_id` 0% overlap, standalone only.
- **D9** — `device_type` mixes casing (`ios`/`android`/`web-user-b2c` vs
  `Desktop`), exactly as documented platform-wide.
- **D6** — 2,300 rows, 2,300 distinct `user_id` — no repeat users here.
