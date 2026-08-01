---
id: doc.log
kind: changelog
status: verified
confidence: high
source: git history of this wiki
last_verified: 2026-08-02
links: [doc.index, doc.known_issues]
---

# Context changelog

Append-only, newest first. Every entry names the evidence behind the change.
Git history is the authoritative diff; this is the readable summary.

## 2026-08-02 — Spec 02 (Group / Family) analysis consolidated

Four `analysis/qNN.md` files from the Analysis Agent
(`out/02_group_family/analysis/q01.md`–`q04.md`) folded into the wiki — the
first live-query evidence for this spec's PM questions, closing the "not yet
resolved" gap left by the previous entry below.

- **q01 — completion rate by group size:** verified by set membership
  (`group_submitted.group_id ⊆ group_started.group_id`, per D1, not
  `windowFunnel`). Falls **monotonically**, 69.47% (size 2) → 31.11% (size
  6), a 38pp spread — resolves D1's open "no analysis/qNN.md exists yet"
  caveat on `group_started`/`group_submitted`. Also found `traveller_removed`
  rate scales with `group_size` (0.42% → 18.4%).
- **q02 — add/remove churn:** 3,495 `traveller_added` rows (avg 2.91/group)
  vs. 70 `traveller_removed` rows (69/1,200 groups, 5.75%) — net 3,425
  travellers added. All 70 removed `group_id`s verified present in both
  `group_started` and `traveller_added` (100% set membership) — removals are
  consistent, not orphaned.
- **q03 — is `docs_complete` the big-group bottleneck?** No — it barely
  moves with `group_size` (81.15%→78.41%, 2.7pp spread) and is at best
  weakly/inconsistently predictive of submission within a size bucket.
  `group_size` itself remains the dominant driver, reproducing q01's table
  independently.
- **q04 — which destinations/segments drive group applications?** No single
  destination dominates (~14pp spread across 14 destinations); `device_type`
  flat; `geoip_country_code` dominated by `IN` for volume reasons only.
  `group_size` dwarfs every other cut tested.
- All 4 questions independently re-confirmed **D2's 0% `application_id`
  overlap** — each stayed within the group flow's own tables, joined on
  `group_id` (spec-local key) instead, and none found a working path back to
  `application_started`.

Updated `tables/group_started.md` (completion-by-size table, D1 resolved,
docs_complete finding), `tables/group_submitted.md` (verified step-through,
D1 resolved), `tables/traveller_added.md` (churn + docs_complete sections),
`tables/traveller_removed.md` (churn + group_size-correlation section),
`tables/index.md` (‡ footnote, bolded verified step-through),
`known_issues.md` (D1 addendum, D2 spec-02 independent-re-confirmation
addendum), `relationship.md` (Group section churn/completion note, "Entities
the incoming specs will add" note), `index.md` (source citation). Added new
page `metrics/group_completion_rate_by_size.md` (a genuinely reusable
definition — computed independently by 3 of the 4 questions) and its
`metrics/index.md` row.

**Not yet resolved:** the `travellers_submitted` vs. `group_size`
reconciliation flagged on `group_submitted.md` (do the two figures typically
match at submit time, and what does a mismatch mean?) — none of q01–q04
addressed it; still open for a future analysis pass. The broader
`co_travelers` (on `application_started`) vs. this spec's `group_size`
conflict also remains unresolved at the analysis layer, as before.

Evidence: `out/02_group_family/analysis/q01.md`, `q02.md`, `q03.md`,
`q04.md`.

## 2026-08-02 — Spec 02 (Group / Family Applications) instrumented

Instrumentation Agent output for `02_group_family`
(`out/02_group_family/`: `ddl.sql`, `justification.md`, `profile.md`,
`load_report.md`) folded into the wiki. 4 new tables created, 0 altered, 0
materialized views. **New entity: Group** (`group_id`, `group_size`) — the
first new entity added since spec 01.

- `group_started` (1,200 rows), `traveller_added` (3,495), `traveller_removed`
  (70), `group_submitted` (688) — 5,453 rows total. Row counts verified live
  via `load_report.md`. New pages `tables/group_started.md`,
  `tables/traveller_added.md`, `tables/traveller_removed.md`,
  `tables/group_submitted.md`.
- All 4 use a **subset** of the shared 30-column envelope, `ENGINE =
  MergeTree`, `PARTITION BY toYYYYMM(timestamp)`, and (per known_issues.md
  D8) `ORDER BY (toDate(timestamp), group_size, group_id, id)` — a further
  substitution beyond spec 01's `(..., device_type, user_id, id)` template,
  because `group_id`/`user_id` are 1:1-collinear in this dataset and the
  PM's questions are phrased per-group. `group_id` is `FixedString(32)`, a
  deliberate deviation from the plain-`String` identifier style, justified
  by the column-policy's spec-local-key carve-out (`group_id` joins nothing
  outside this spec's own 4 tables).
- No `ALTER TABLE`: no event in this spec shares a moment/grain with an
  existing table's event. No materialized view: all 4 source tables are
  70–3,495 rows in the profiled sample — full scans stay cheap.
- **D2 — 0% overlap, confirmed a third time.** All 4 tables' `application_id`
  was normalized on ingest, then the mandatory overlap-check against
  `application_started` returned **`overlap_pct = 0.0%`**
  (`out/02_group_family/load_report.md`) — same STOP verdict as spec 01's 5
  tables. Analyse the group flow standalone. Updated `known_issues.md` D2's
  verdict table and `relationship.md`'s new "Group" entity section.
- **`co_travelers` conflict flagged in `relationship.md`, checked, not
  resolved.** `group_size`/`travellers_submitted` live only in the 4 new
  tables (no parallel schema-level model of `co_travelers` was created), but
  the two figures can legitimately diverge for the same `application_id` —
  reconciling which is authoritative is unresolved analysis-layer work.
- **`traveller_added`/`traveller_removed` break the "no repeat users"
  pattern** (D6) by design — one group owner performs multiple add/remove
  actions (`traveller_added`: 1,200 distinct users over 3,495 rows;
  `traveller_removed`: 69 over 70). Flagged on both table pages and in
  `relationship.md`.
- `group_started → group_submitted` step-through (688/1,200 = 57.33%) is a
  **row-count ratio only**, not a verified set-membership join — no
  `analysis/qNN.md` files exist yet for this spec (question_extractor.py has
  not run), so nothing was consolidated from the Analysis Agent this pass.
  Per D1, this funnel-shaped question needs a monotonicity check or
  set-membership count before trusting a `windowFunnel` result.
- Carried-forward caveats cited by `justification.md` and recorded on each
  table page: **D1** (funnel-shaped question, non-monotonic-timestamp risk),
  **D8** (followed — no table reverted to the legacy `id`-leading sort key),
  **D9** (`device_type` casing, `destination` UPPERCASE), **K7** (`app_version`
  carries no temporal signal — do not read a rollout effect into it).

Updated `tables/index.md` (4 new rows, Total → 2,491,441 rows, physical-layout
note), `index.md` (17 tables, 2,491,441 total rows, engine/sort-key rows),
`relationship.md` (new "Group" entity section, join map `group_id` entry,
"Entities the incoming specs will add" marked instrumented), `known_issues.md`
(D2 verdicts table + dated addendum).

**Not yet resolved:** the K1-style re-test this spec's own risks call for
(D1's monotonicity check on `group_started → group_submitted`, and D2's
re-test with a fresh sample) has not been run — the Context Agent has no
live DB access and no `analysis/qNN.md` file exists yet for this spec.

Evidence: `out/02_group_family/ddl.sql`, `justification.md`, `profile.md`,
`load_report.md`.

## 2026-08-02 — Spec 01 (Express Checkout) analysis consolidated

Four `analysis/qNN.md` files from the Analysis Agent
(`out/01_express_checkout/analysis/q01.md`–`q04.md`) folded into the wiki —
the first live-query evidence for this spec's PM questions.

- **q01** (Express vs standard conversion lift): Express checkout→success
  converts **83.02%** (836/1,007, verified set membership) vs standard
  **47.86%** (7,054/14,739) — **+35.2pp / 1.73×**. New page
  `metrics/express_conversion_lift.md` (its selection-bias and small-n
  caveats carried over verbatim); `tables/index.md` and
  `tables/express_payment_confirmed.md` cross-linked.
- **q02** (K1 re-test on the OTP step): `known_issues.md` K1 given a new,
  dated, narrower verdict *alongside* — not replacing — its 2026-08-01
  refutation. Express's `otp_entered.otp_success` shows OTP failures **100%
  iOS-concentrated** (70/70 failures; iOS 83.64% success vs 100% on every
  other platform); conditional on success, iOS's downstream confirmation
  rate recovers to be in line with Android. Updated `known_issues.md` K1,
  `tables/otp_entered.md`, `tables/express_payment_confirmed.md`,
  `tables/pay_now_clicked.md`.
- **q03** (Express payment latency): `express_payment_confirmed
  .payment_latency_ms` mean 2,305.5ms / median 2,341.5ms (836 rows) — added
  to `tables/express_payment_confirmed.md`. No standard-checkout baseline
  exists; the nearest proxy (timestamp subtraction on
  `pay_now_clicked`/`purchase_completed`) is invalid because D1's
  non-monotonic-timestamp trap is **now confirmed to extend to
  `pay_now_clicked → purchase_completed`** (only 52.55% of matched pairs
  monotonic) — added as a dated addendum to `known_issues.md` D1.
- **q04** (segment adoption): verified `express_checkout_shown →
  express_checkout_selected` (61.03%) as an exact set-membership subset, not
  a row-count ratio — geo shows the clearest skew (AU/SA/SG ~5–8pp above
  AE), device and saved-method type essentially flat. Added to
  `tables/express_checkout_shown.md`.

Cross-cutting update: `tables/index.md`'s footnote now marks 2 of the 3
Express Checkout step-through transitions as **verified** joins (was: all
3 unverified row-count ratios) — `→ saved_method_used`/`→ otp_entered`
(100%) remains unverified. `relationship.md`'s Application section notes all
4 questions independently re-confirmed D2 (0% overlap) by working around it
via `user_id` joins within Express Checkout's own tables — no question found
a usable `application_id` path back to the main funnel. No new entities.

**Not yet resolved:** the ~101-row unexplained gap between `otp_success=true`
(937) and `express_payment_confirmed` (836) — corroborated by q01 and q02
but still not explained by any column in this spec; flagged for a future
analysis pass.

Evidence: `out/01_express_checkout/analysis/q01.md`–`q04.md`.

## 2026-08-01 — Spec 01 (Express Checkout) instrumented

Instrumentation Agent output for `01_express_checkout` (`out/01_express_checkout/`:
`ddl.sql`, `justification.md`, `profile.md`, `load_report.md`) folded into the
wiki. 5 new tables created, 0 altered:

- `express_checkout_shown` (1,650 rows), `express_checkout_selected` (1,007),
  `saved_method_used` (1,007, envelope subset only — no event-specific
  columns), `otp_entered` (1,007), `express_payment_confirmed` (836). Row
  counts verified live via `load_report.md`.
- All 5 use a **subset** of the shared 30-column envelope, and (per
  `known_issues.md` D8) correctly use `MergeTree` +
  `ORDER BY (toDate(timestamp), device_type, user_id, id)` +
  `LowCardinality(String)` categoricals — not the 8 baseline tables'
  `id`-leading sort key.
- No `ALTER TABLE`: no event in this spec shares a moment/grain with an
  existing table (see `justification.md` "CREATE vs ALTER call").
- No new entity: unlike specs 02/03, Express Checkout is a sequence of events
  against the existing Application/User entities (`relationship.md` updated).

**Key risk carried forward — D2, confirmed broken, not just a formatting
issue:** `application_id` was normalized on ingest (32-char hex → 36-char
hyphenated UUID) for all 5 tables, then D2's mandatory overlap-check ran
against `application_started` and returned **`overlap_pct = 0.0%` on all 5**
(`load_report.md`) → **STOP** per D2's action table. `known_issues.md` D2 and
`relationship.md` (Application entity) both updated with this dated verdict;
none of these 5 tables should be joined to the main funnel via
`application_id` until re-tested.

**K1 (iOS WebKit OTP regression) is now directly instrumentable** —
`otp_entered.otp_success`/`otp_attempts` and `express_payment_confirmed` exist
for the first time — but the re-test itself was **not** run (`load_report.md`
only executed the D2 check for this spec; the Context Agent has no live DB
access). Flagged in `known_issues.md` K1 as the next analysis to run —
cuttable by `otp_entered.os` alone, no `application_id` join required.

Also flagged, not yet a known_issues.md entry: an unexplained ~101-row gap
between `otp_entered` (1,007, 937 successful) and `express_payment_confirmed`
(836) that `otp_success=false` (70 rows) doesn't fully account for — see
`tables/otp_entered.md`.

`tables/index.md` regenerated (13 tables, 2,485,988 total rows).

Evidence: `out/01_express_checkout/justification.md`, `ddl.sql`,
`profile.md`, `load_report.md`.

## 2026-08-01 — Stage 0 bootstrap

First verification pass of the handwritten `base_context.md` against the live
`clickathon` database (2,480,481 rows, H1 2026), via ClickHouse MCP. Every
factual claim was turned into a query, run, and given a verdict.

**Known issues — 5 of 7 refuted:**

| Issue | Verdict |
|---|---|
| K2 Passport scan model update | **verified** — Android failure 5.96% → 33.54%, far worse than documented |
| K1 iOS WebKit OTP regression | **refuted** — iOS converts *best*; UAE iOS 70.78% vs Android 43.55% |
| K3 MRZ OCR non-Latin | **refuted** — highest retries are Latin-script issuers |
| K4 Schengen summer scarcity | **refuted** — decline is portfolio-wide, not Schengen-specific |
| K6 SUMMER20 Q2 campaign | **refuted** — runs all 6 months, one of 4 equal coupons |
| K7 App 7.45 rollout | **refuted** — all 5 versions uniform in every month |
| K5 WhatsApp nudge | **unverifiable** — no channel column, no repeat users |

**Data traps opened: 9 (D1–D9).** Three are critical and fail silently:

- **D1** — `base_context.md` recommends `windowFunnel`, which returns 3,366
  purchases instead of the true 7,054 (only 52.2% of purchases post-date their
  own document upload)
- **D2** — spec `application_id` is 32-char hex vs the DB's 36-char UUID; joins
  return zero rows without erroring
- **D3** — `is_crossed_failed_attempt_threshold` doesn't track `retry_count`
  (71.4% of flagged events have zero retries)

**Structure:** `index.md`, `SCHEMA.md`, `log.md`, `business.md`,
`relationship.md` (entities folded in), `known_issues.md` (traps + verdicts),
`tables/` (8 pages + envelope), `metrics/` (7 pages).
