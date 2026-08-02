---
id: table.reconverted
kind: table
status: verified
confidence: high
source: out/04_abondon_checkout_recovery_2/ddl.sql + justification.md (schema); out/04_abondon_checkout_recovery_2/load_report.md — rows loaded, D2 overlap_pct; out/04_checkout_recovery_3/ddl.sql + justification.md + load_report.md — independent resubmission 2026-08-02, identical row count and D2 verdict; out/04_checkout_recovery_3/analysis/q01.md — verified overall + by-drop_step recovery rate, resolves duplicate-load question; out/04_checkout_recovery_3/analysis/q02.md — verified recovery-rate-by-channel, resolves duplicate-load question
last_verified: 2026-08-02
links: [doc.envelope, doc.relationship, known_issue.d2_application_id_join_format, known_issue.d1_windowfunnel_loses_conversions, known_issue.k5_whatsapp_nudge, tables.index, table.resumed_at_step, table.abandonment_detected, table.purchase_completed, metric.recovery_rate]
---

# `reconverted`

Spec 04 (Abandoned Checkout Recovery). Fires when the user completes
payment after a nudge — the recovery outcome, and the PM's headline
metric's numerator (denominator: `abandonment_detected`). The one event
most tempting to fold into `purchase_completed` (same business concept:
payment succeeds), but `purchase_completed`'s real column list
(`value`/`currency`/`coupon_applied`/`coupon_name`/`discount_amount`/
`insurance_added`/`insurance_amount`/`plan_selected`) does not appear here
(n=93; only the envelope subset + `drop_step` + `channel`), and
conversely this table's `drop_step`/`channel` have no place on
`purchase_completed`. Different grain/purpose ("recovery outcome
attributed to a nudge" vs. "revenue at time of payment"). → `CREATE
TABLE`, not an `ALTER` on `purchase_completed`. See
`out/04_abondon_checkout_recovery_2/justification.md` "CREATE vs ALTER
call".

| | |
|---|---:|
| Rows | **93** (verified — `load_report.md`) |
| Distinct users | 93 (1 per user, per profile.md) |
| Distinct `application_id` | 93 (100% unique, per profile.md) |
| Sample time span | 2026-06-08 06:01 → 2026-07-01 00:00 (profile.md file-level span; not separately profiled per event) |
| Step-through ← `resumed_at_step` | 93 / 268 = **34.70%** — unverified row-count ratio through `resumed_at_step` specifically; **but** `reminder_cta_clicked → reconverted` (also 268 → 93) **is verified** via `analysis/q02.md`/`q03.md`'s direct join, bypassing `resumed_at_step` |
| **Overall recovery rate** ← `abandonment_detected` | 93 / 2,300 = **4.04%** — **verified**, the PM's headline metric (`analysis/q01.md`, direct `user_id` join, 93/93 ⊆ 2,300, `drop_step` agrees on every matched row) |

This table carries only a **subset** of the shared 30-column envelope (see
[the envelope](index.md)): `id`, `timestamp`, `user_id`, `application_id`,
`device_type`, `os`, `app_version`, `client_lib`, `geoip_country_code`,
`city`, `destination`, plus `drop_step` and `channel` (inherited context —
see [abandonment_detected.md](abandonment_detected.md) and
[reminder_sent.md](reminder_sent.md)). Other envelope columns — and
notably none of `purchase_completed`'s revenue/add-on columns — were
observed for this event and were deliberately not added.

| Column | Type | Values |
|---|---|---|
| `drop_step` | `LowCardinality(String)` | 4 values: `document_uploaded`(31) / `application_started`(25) / `pay_now_clicked`(19) / `destination_card_clicked`(18) |
| `channel` | `LowCardinality(String)` | 3 values: `push`(53) / `whatsapp`(21) / `email`(19) |

## Recovery rate by channel (of `reminder_sent`) — verified, 2026-08-02

| Channel | Sent | Reconverted | Recovery rate (of sent) |
|---|---:|---:|---:|
| **push** | 1,138 | 53 | **4.66%** |
| whatsapp | 484 | 21 | 4.34% |
| email | 678 | 19 | 2.80% |

Push and WhatsApp land within half a point of each other on end-to-end
recovery rate despite WhatsApp's much higher open rate (46.28% vs 28.30% —
see [reminder_sent.md](reminder_sent.md)); email trails on every step.
**Verified** by `analysis/q02.md`'s live set-membership join
(`reminder_sent → reminder_opened → reminder_cta_clicked → reconverted`
on `user_id`, exact reproduction, no fan-out) — this is the K5 re-test.
See [known_issues.md](../known_issues.md) → K5 and
[metrics/recovery_rate.md](../metrics/recovery_rate.md). By `drop_step`
instead, recovery rate is flat 4.45%–4.80% for the first three steps and
worst (2.62%) for `destination_card_clicked` — see
[abandonment_detected.md](abandonment_detected.md) (`analysis/q01.md`).

## ⚠ `application_id` does not join `application_started` — 0% overlap

`application_id` was normalized on ingest per D2 (32-char hex → 36-char
hyphenated UUID). The mandatory D2 overlap-check then ran against
`application_started` and returned **`overlap_pct = 0.0%`** (verified —
`load_report.md`, 2026-08-02) → per D2's action table, **STOP**: analyse
this table **standalone only**. See [known_issues.md](../known_issues.md)
→ D2.

## Physical layout deviates from the 8 baseline tables — intentionally

`ENGINE = MergeTree`, `ORDER BY (toDate(timestamp), drop_step, user_id,
id)` — does not lead with the random `id` UUID, per known_issues.md D8,
matching `abandonment_detected`/`resumed_at_step`'s template (the
numerator/denominator pair leads on the same key). See
`justification.md` "ORDER BY / PARTITION BY reasoning".

## Not folded into `purchase_completed` — deliberate, see justification.md

A real payment event may also fire elsewhere for revenue accounting, but
this table's grain and purpose differ enough (recovery attribution vs.
revenue-at-payment) that treating it as a peer `CREATE TABLE`, not an
`ALTER` on `purchase_completed`, was the call — see
`out/04_abondon_checkout_recovery_2/justification.md` "CREATE vs ALTER
call" for the full column-by-column reasoning. Reconciling whether/how
`reconverted` rows also appear in `purchase_completed` (same physical
payment, two different events) is unresolved analysis-layer work — no
`analysis/qNN.md` file has checked it yet.

## ⚠ 2026-08-02 — spec resubmitted as `04_checkout_recovery_3`, same data — duplicate-load question now resolved

`out/04_checkout_recovery_3` re-profiled/re-justified/re-loaded this exact
table a second time — `ddl.sql` uses `CREATE TABLE IF NOT EXISTS` (no-op,
table already existed), `load_report.md` reports the **identical** row
count (93) and D2 verdict (`overlap_pct = 0.0%`, STOP). Whether this
second load's `INSERT` step re-inserted the same 93 rows a second time
(doubling the true live count to 186, and with it the PM's headline
recovery-rate denominator/numerator pair) was an open question this wiki
could not resolve without live DB access.

**Resolved 2026-08-02 (source: `analysis/q01.md`, `q02.md`).** Both files
independently re-checked this table's live row count — `q01.md`:
`count() = uniqExact(user_id) = 93` with no growth vs. the documented
figure; `q02.md`'s join also reproduces exactly 93 reconversions with no
fan-out. No duplication occurred. See [known_issues.md](../known_issues.md)
→ D2 and the same resolution on
[abandonment_detected.md](abandonment_detected.md) and its 4 sibling
pages.

## Other risks carried forward (see `justification.md` for full reasoning)

- **D1** — overall recovery rate, recovery-by-drop_step, and
  recovery-by-channel are now verified by set-membership join
  (`analysis/q01.md`, `q02.md`, 2026-08-02); the `resumed_at_step →`
  step specifically remains an unverified row-count ratio (see
  [resumed_at_step.md](resumed_at_step.md)).
- **D2** — see above; `application_id` 0% overlap, standalone only.
- **D9** — `device_type` mixes casing, exactly as documented
  platform-wide.
- **D6** — 93 rows, 93 distinct `user_id` — no repeat users here.
