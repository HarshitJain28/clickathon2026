---
id: table.abandonment_detected
kind: table
status: verified
confidence: high
source: out/04_abondon_checkout_recovery_2/ddl.sql + justification.md (schema); out/04_abondon_checkout_recovery_2/load_report.md — rows loaded, D2 overlap_pct; out/04_checkout_recovery_3/ddl.sql + justification.md + load_report.md — independent resubmission 2026-08-02, identical row count and D2 verdict; out/04_checkout_recovery_3/analysis/q01.md — verified set-membership recovery rate by drop_step, resolves duplicate-load question; out/04_checkout_recovery_3/analysis/q04.md — segment cuts (device/geo/destination), recovery-targeting mismatch vs. real funnel drop-offs, resolves duplicate-load question
last_verified: 2026-08-02
links: [doc.envelope, doc.relationship, known_issue.d2_application_id_join_format, known_issue.d1_windowfunnel_loses_conversions, known_issue.d8_sort_key_defeats_primary_index, known_issue.k5_whatsapp_nudge, tables.index, table.reminder_sent, table.reconverted, metric.recovery_rate]
---

# `abandonment_detected`

Spec 04 (Abandoned Checkout Recovery). Fires when a system-side detector
notices a user dropped out of the funnel — not the same instant as any of
the 4 existing funnel tables it references
(`destination_card_clicked`/`application_started`/`document_uploaded`/`pay_now_clicked`);
its own column `drop_step` *names* which of those 4 the user last touched,
it does not duplicate a row on that table. → `CREATE TABLE`, not an
`ALTER`. See `out/04_abondon_checkout_recovery_2/justification.md`
"CREATE vs ALTER call".

| | |
|---|---:|
| Rows | **2,300** (verified — `load_report.md`) |
| Distinct users | 2,300 (1 per user, per profile.md) |
| Distinct `application_id` | 2,300 (100% unique, per profile.md) |
| Sample time span | 2026-06-08 06:01 → 2026-07-01 00:00 (profile.md file-level span; not separately profiled per event) |
| Step-through → `reconverted` (PM's headline recovery metric) | 93 / 2,300 = **4.04%** — **verified** by set-membership join on `user_id` (100% of `reconverted` ⊆ `abandonment_detected`, `drop_step` agrees on every matched row — `analysis/q01.md`, 2026-08-02) |

This table carries only a **subset** of the shared 30-column envelope (see
[the envelope](index.md)): `id`, `timestamp`, `user_id`, `application_id`,
`device_type`, `os`, `app_version`, `client_lib`, `geoip_country_code`,
`city`, `destination`. Other envelope columns (`app_session_id`,
`funnel_type`, `co_travelers`, `gclid`, `citizenship`, `duplicate_id`,
`is_back_filled`, etc.) were not observed for this event and were
deliberately not added — an unobserved column is an invented column.

| Column | Type | Values |
|---|---|---|
| `drop_step` | `LowCardinality(String)` | 4 values, literally the 4 existing funnel table names: `document_uploaded`(696) / `destination_card_clicked`(686) / `application_started`(521) / `pay_now_clicked`(397) — the PM's primary cut for this table |

## ⚠ `application_id` does not join `application_started` — 0% overlap

`application_id` was normalized on ingest per D2 (32-char hex → 36-char
hyphenated UUID). The mandatory D2 overlap-check then ran against
`application_started` and returned **`overlap_pct = 0.0%`** (verified —
`load_report.md`, 2026-08-02) → per D2's action table, **STOP**: analyse
this table **standalone only**, the same verdict specs 01–03 all got. See
[known_issues.md](../known_issues.md) → D2.

`justification.md` flags a follow-up worth running before assuming this
flow is entirely unjoinable: unlike `application_id`, this spec's
`user_id` values are well-formed 28-character strings matching
`relationship.md`'s documented format exactly. A `user_id`-based overlap
check against `application_started`/`destination_card_clicked` has **still
not** been run — none of `analysis/q01.md`–`q04.md` performed it either;
`q04.md` explicitly notes its funnel-mismatch comparison "trusts
`drop_step`'s label semantics and compares independent population
*counts*, not a verified cross-table join." That check remains the first
open join-integrity test for this spec.

## Recovery funnel step-through — partially verified (2026-08-02)

| Stage | Rows | Ratio from previous stage | Status |
|---|---:|---:|---|
| `abandonment_detected` | 2,300 | — | — |
| `reminder_sent` | 2,300 | 100% | unverified row-count ratio |
| `reminder_opened` | 690 | 30.00% | **verified** — `analysis/q02.md`/`q03.md` join `reminder_sent → reminder_opened` on `user_id`, exact reproduction, no fan-out |
| `reminder_cta_clicked` | 268 | 38.84% | **verified** — same chain, `→ reminder_cta_clicked` |
| `resumed_at_step` | 268 | 100% | unverified row-count ratio — no query has joined through this table specifically (see [resumed_at_step.md](resumed_at_step.md)) |
| `reconverted` | 93 | 34.70% | **verified** — chain reaches `reconverted` directly from `reminder_cta_clicked`/`reminder_sent` (bypassing `resumed_at_step`), exact match, no fan-out |
| **Overall recovery rate** (`reconverted` ÷ `abandonment_detected`) | | **4.04%** | **verified** — `analysis/q01.md`, direct `user_id` join, 93/93 ⊆ 2,300 |

**By `drop_step` (verified, `analysis/q01.md`):** recovery rate is
roughly flat across the first 3 steps (4.45%–4.80%) and clearly worse for
the earliest one:

| `drop_step` | Abandoned | Reconverted | Recovery rate |
|---|---:|---:|---:|
| `application_started` | 521 | 25 | **4.80%** |
| `pay_now_clicked` | 397 | 19 | 4.79% |
| `document_uploaded` | 696 | 31 | 4.45% |
| `destination_card_clicked` | 686 | 18 | **2.62%** (worst) |

`application_started`/`pay_now_clicked` are a near-tie (a 1-user swing
flips the ranking); `destination_card_clicked` — the earliest, lowest-intent
drop point — recovers at roughly half the rate of the other three. See
[metrics/recovery_rate.md](../metrics/recovery_rate.md). The
`abandonment_detected → reminder_sent` step and the `resumed_at_step` leg
specifically remain **unverified row-count ratios** — no query has checked
them directly. See [reminder_sent.md](reminder_sent.md) (channel breakdown)
and [reconverted.md](reconverted.md).

## Physical layout deviates from the 8 baseline tables — intentionally

`ENGINE = MergeTree`, `ORDER BY (toDate(timestamp), drop_step, user_id,
id)` — does not lead with the random `id` UUID, per known_issues.md D8.
`drop_step` (4 values) takes the #2 slot because it's this table's own
leading discriminator and the PM's primary cut ("reconversion rate by
`drop_step`") — see `justification.md` "ORDER BY / PARTITION BY
reasoning".

## K5 (WhatsApp nudge) — re-tested with a live query, 2026-08-02

`known_issues.md` → K5 was previously **unverifiable** because no
`channel` column and no genuine "return to the funnel" event existed
anywhere. This spec's `reminder_sent`/`reminder_opened`/
`reminder_cta_clicked` carry `channel`, and `resumed_at_step` is the
return event. **Re-tested** via `analysis/q02.md`'s live set-membership
join: WhatsApp does drive the best *open* rate (46.28%), but **push** wins
end-to-end recovery-of-sent (4.66% vs. WhatsApp's 4.34%) — see
[reminder_sent.md](reminder_sent.md) for the full channel funnel and
[known_issues.md](../known_issues.md) → K5 for the full verdict.
`analysis/q03.md` additionally found timing (`hours_since_drop`) has no
measurable effect on recovery rate.

## Recovery targeting does not match the real funnel's actual worst drop-offs — new finding, `analysis/q04.md`

`drop_step` records which of the 4 real funnel tables the user last
touched before being flagged for recovery. Comparing the flag rate against
each transition's true population of non-progressors (live counts:
1,000,000 / 154,413 / 20,446 / 14,739 on
`destination_card_clicked`/`application_started`/`document_uploaded`/`pay_now_clicked`):

| `drop_step` (= last real-funnel stage touched) | Flagged for recovery | True non-progressors at that transition | Flag rate | Recovery rate of flagged |
|---|---:|---:|---:|---:|
| `destination_card_clicked` (never started an application) | 686 | 845,587 | **0.081%** | 2.62% |
| `application_started` (never uploaded a document) | 521 | 133,967 | **0.39%** | 4.80% |
| `document_uploaded` (never clicked pay-now) | 696 | 5,707 | **12.20%** | 4.45% |
| `pay_now_clicked` (never purchased) | 397 | 7,685 | **5.17%** | 4.79% |

The real funnel's two biggest leaks — card-click→application-start
(845,587 lost) and application-start→document-upload (133,967 lost, "the
biggest leak" per [tables/index.md](index.md)) — together **98.6% of all
non-converters in the whole funnel** — get flagged for recovery at only
0.08%/0.39%. The system instead concentrates recovery effort on the two
*smaller* late-stage leaks (12.2%/5.2% flag rates, 30–150× higher).
Recovery rate *of what does get flagged* is fairly flat (2.6%–4.8%) across
all four steps, so this is a **targeting/detection-coverage** story, not a
"recovery works better there" story. **Caveat:** this compares independent
population *counts* by `drop_step` label, not a verified cross-table join
of the same users — `user_id` has never been overlap-checked against the
main funnel (see below), so treat this as directional evidence of a
targeting gap, not a precise coverage percentage.

## ⚠ 2026-08-02 — spec resubmitted as `04_checkout_recovery_3`, same data — duplicate-load question now resolved

`out/04_checkout_recovery_3` profiled, justified, and loaded this exact
same 6-table family a second time. Its `ddl.sql` uses `CREATE TABLE IF NOT
EXISTS` — a no-op on structure, since all 6 tables already existed from
`out/04_abondon_checkout_recovery_2` — and its `justification.md` cited
the identical D1/D2/D6/D8/D9 risk set with no new findings. Its
`load_report.md` reported the **exact same row count** for this table
(2,300) and the **exact same** D2 verdict (`overlap_pct = 0.0%`, STOP),
raising an open question this wiki could not resolve without live DB
access: had the resubmission's `INSERT` step re-inserted the same 2,300
rows a second time?

**Resolved 2026-08-02 (source: `analysis/q01.md`, `q04.md`).** Both files
independently ran a live `count()`/`uniqExact(user_id)` against this table
and got exactly **2,300** either way (and `reconverted` exactly 93 either
way) — no duplication. `q04.md`: *"re-checked the row counts directly:
`count() = uniqExact(user_id) = 2,300` on `abandonment_detected` and
`93/93` on `reconverted`, with no growth vs. the documented figures... the
live table holds exactly one copy of the data."* See
[known_issues.md](../known_issues.md) → D2 and the same resolution on
[reminder_sent.md](reminder_sent.md) and its 4 sibling pages.

## Other risks carried forward (see `justification.md` for full reasoning)

- **D1** — `abandonment_detected → reconverted` (overall + by `drop_step`)
  and the `reminder_sent → reminder_opened → reminder_cta_clicked →
  reconverted` chain are now verified by set-membership join
  (`analysis/q01.md`–`q03.md`, 2026-08-02); the `abandonment_detected →
  reminder_sent` step and the `resumed_at_step` leg remain unverified row-
  count ratios.
- **D2** — see above; `application_id` 0% overlap, standalone only.
- **D8** — confirmed **not** replicated — leads with `toDate(timestamp)` +
  a real filter column.
- **D9** — `device_type` mixes casing (`ios`/`android`/`web-user-b2c` vs
  `Desktop`), exactly as documented platform-wide.
- **D6** — 2,300 rows, 2,300 distinct `user_id` — no repeat users on this
  table, consistent with the other origin tables in specs 01–03.
