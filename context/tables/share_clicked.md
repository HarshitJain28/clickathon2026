---
id: table.share_clicked
kind: table
status: verified
confidence: high
source: out/03_status_sharing/ddl.sql + justification.md (schema); out/03_status_sharing/load_report.md — rows loaded, D2 overlap_pct; out/03_status_sharing/analysis/q01.md — verified set-membership step-through by status_shared
last_verified: 2026-08-02
links: [doc.envelope, doc.relationship, known_issue.d2_application_id_join_format, known_issue.d1_windowfunnel_loses_conversions, tables.index, metric.share_completion_rate]
---

# `share_clicked`

Spec 03 (Visa Status Sharing). Fires when a sharer taps "share" on their own
application status — **origin of the new `Share` entity** (`share_id`). Does
not coincide with any existing table's event (all fire earlier in the
journey, none carry `status_shared`/`share_id`). → `CREATE TABLE`, not an
`ALTER`. See `out/03_status_sharing/justification.md` "CREATE vs ALTER call".

| | |
|---|---:|
| Rows | **1,600** (verified — `load_report.md`) |
| Distinct users | 1,600 (1 per user, per profile.md) |
| Distinct `share_id` | 1,600 (1 per row — this is where `share_id` originates) |
| Sample time span | 2026-06-08 06:00 → 2026-07-01 09:21 (profile.md file-level span; not separately profiled per event) |
| Step-through → `channel_selected` | 1,144 / 1,600 = **71.5%** — **verified** set-membership join on `share_id` (`channel_selected.share_id ⊆ share_clicked.share_id`), flat across `status_shared` (70.11%–73.33%) — `analysis/q01.md`, 2026-08-02 |

This table carries only a **subset** of the shared 30-column envelope (see
[the envelope](index.md)): `id`, `timestamp`, `user_id`, `application_id`,
`app_version`, `city`, `client_lib`, `destination`, `device_type`,
`geoip_country_code`, `os`. Other envelope columns (`app_session_id`,
`funnel_type`, `co_travelers`, `gclid`, `citizenship`, `duplicate_id`,
`is_back_filled`, etc.) were not observed for this event and were
deliberately not added — an unobserved column is an invented column (see
justification.md's note that `spec.md` claims "full envelope" but only a
9–13 column subset was actually observed).

| Column | Type | Values |
|---|---|---|
| `share_id` | `FixedString(32)` | 32-char lowercase-hex, 100% present, 0% null, 1,600/1,600 unique — the `Share` entity's key, created here |
| `status_shared` | `LowCardinality(String)` | 3 values: `submitted`(562) / `processing`(525) / `approved`(513) — the PM's #1 cut for this table |

## `share_id` is `FixedString(32)`, not `String` — deliberate deviation

Every sampled value across this table and its 4 siblings (`channel_selected`,
`link_generated`, `link_opened`, `recipient_cta_clicked`) is exactly 32
lowercase-hex characters, 100% present, zero nulls. `FixedString` is normally
disqualified for identifiers (silent mismatch against a `String`
counterpart on join), but `share_id` joins nothing outside this spec's own 5
tables — a brand-new entity, unlike `application_id`/`user_id` — so the
column-policy carve-out for spec-local keys applies, mirroring the precedent
already set for `group_id` (spec 02). See `justification.md` "Column
choices".

## ⚠ `application_id` does not join `application_started` — 0% overlap

`application_id` was normalized on ingest per D2 (32-char hex → 36-char
hyphenated UUID). The mandatory D2 overlap-check then ran against
`application_started` and returned **`overlap_pct = 0.0%`** (verified —
`load_report.md`, 2026-08-02) → per D2's action table, **STOP**: analyse
this table **standalone only**, the same verdict specs 01 and 02 got. See
[known_issues.md](../known_issues.md) → D2.

## Physical layout deviates from the 8 baseline tables — intentionally

`ENGINE = MergeTree`, `ORDER BY (toDate(timestamp), status_shared, user_id,
id)` — does not lead with the random `id` UUID, per known_issues.md D8.
`status_shared` (not `device_type`/`group_size` as in specs 01/02) takes the
#2 slot because it is this table's own leading discriminator and the PM's
first question for this spec ("does `status_shared` correlate with share
rate"). See `justification.md` "ORDER BY / PARTITION BY reasoning".

## Share-flow completion rate, by `status_shared` — verified 2026-08-02

Per `analysis/q01.md`, computed by set-membership join on `share_id` (D1 —
never `windowFunnel`): overall **71.5%** (1,144/1,600) complete the flow
(`share_clicked` → `channel_selected`/`link_generated`), and the rate is
essentially flat across `status_shared`:

| `status_shared` | Shares | Completed | Completion rate |
|---|---:|---:|---:|
| submitted | 562 | 394 | 70.11% |
| approved | 513 | 365 | 71.15% |
| processing | 525 | 385 | 73.33% |

**No — approved applications are not shared/completed more.** The 3.2pp
band (70.1%–73.3%) shows no monotonic pattern (`processing`, not `approved`,
is highest) and is well within what 513–562-row samples produce by chance.
An independent applications-per-status "share rate" (shares ÷ applications
at that status) **cannot be computed** — `status_shared` only exists on
this spec's own 3 sharer-side tables, and D2's 0% `application_id` overlap
blocks joining to `application_started`. See
[metrics/share_completion_rate.md](../metrics/share_completion_rate.md).

## Other risks carried forward (see `justification.md` for full reasoning)

- **D1** — `share_clicked → channel_selected`/`link_generated` is now a
  **verified** set-membership join (`analysis/q01.md`, 2026-08-02 — see
  above). The sharer-side ↔ recipient-side leg (this table's `share_id`s
  against `link_opened`'s) has **not** been checked by any `analysis/qNN.md`
  file yet — still an open item. No monotonicity check
  (`countIf(t_later >= t_earlier)/count()`) has been run either.
- **D9** — `device_type` mixes casing (`ios`, `android`, `web-user-b2c` vs
  `Desktop`), exactly as documented platform-wide.
- **D6** — 1,600 rows, 1,600 distinct `user_id` — no repeat users here,
  consistent with the sharer-side of this spec (unlike the recipient-side
  tables, which carry no `user_id` at all).
- `spec.md` claims sharer events "carry the full envelope"; only a 9–13
  column subset was actually observed (profile.md) — see justification.md's
  caveat. Treat as a follow-up `ALTER TABLE ADD COLUMN` if a future profile
  shows more columns, not something to add speculatively now.
