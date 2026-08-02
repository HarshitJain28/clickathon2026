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

## 2026-08-02 — Spec `05_instant_forex`: 4 analysis questions consolidated

`out/05_instant_forex/analysis/q01.md`–`q04.md` (all 4 present) answer the
PM's headline questions for the Instant Forex Add-on: **q01** — overall
attach rate `forex_purchased` ÷ `forex_offer_shown` = 546/2,900 =
**18.83%**, verified by exact `uniqExact(user_id)` set-membership join, no
fan-out, plus by-`destination` breakdown (best US 24.58%, worst AU
13.78%, ~11pp spread). **q02** — AOV distribution among the 546 attachers:
right-skewed, median ₹31,685, mean ₹40,587.77 (100% INR), nearly identical
to `forex_added_to_cart`'s pre-payment shape (median ₹31,911) — mean
overstates the typical uplift, use median. **q03** — full 5-stage funnel
(`forex_offer_shown → currency_selected → amount_entered →
forex_added_to_cart → forex_purchased`) confirmed **perfectly nested** by
live joins; the funnel's loss is overwhelmingly concentrated at the very
first step (`forex_offer_shown → currency_selected`, 64.38%/1,867 users
lost) vs. only 24.69%/179 lost at `forex_added_to_cart → forex_purchased`;
`currency_selected`/`amount_entered`'s identical row count is confirmed a
true 1:1 pairing (100% step-through), not a coincidence. **q04** —
confirms 100% timestamp monotonicity (no ordering trap in this funnel,
unlike the main visa funnel); adds `to_currency` skew (EUR blends FR+GR,
a 3pp gap masked), mild device skew (ios best 19.77%), and mild-moderate
geo skew (AE best 21.51%, India = 61.7% of volume).

This upgrades all 5 table pages' step-through figures from "unverified
row-count ratio" to **verified** (per D1's set-membership fix), resolves
`currency_selected.md`'s "unconfirmed pairing" note to confirmed, and adds
two new metric pages: [metrics/forex_attach_rate.md](metrics/forex_attach_rate.md)
and [metrics/forex_addon_aov.md](metrics/forex_addon_aov.md). Updated
`known_issues.md` → D1 (funnel verified, perfectly nested + monotonic)
and → D2 (independently re-confirmed by all 4 questions, no working
`application_id` path found — same STOP verdict stands). Updated
`relationship.md` → "Forex Add-on" section and `tables/index.md`'s ¶
footnote to match. Evidence:
`out/05_instant_forex/analysis/q01.md`–`q04.md`.

**Caveat carried forward, not resolvable by this agent:** none of the 4
questions checked whether this spec's `user_id` overlaps
`application_started`/`destination_card_clicked` via `user_id` rather than
the broken `application_id` — an open question this wiki cannot run
itself (no live DB access), echoing the same still-unrun check noted for
spec 04's Recovery flow.

## 2026-08-02 — Spec `05_instant_forex` instrumented — 5 new tables, no analysis yet

`out/05_instant_forex`'s `ddl.sql`/`justification.md`/`profile.md`/
`load_report.md` introduce 5 new `CREATE TABLE` statements (no `ALTER`s, no
materialized views): `forex_offer_shown` (2,900 rows, origin, only table
carrying `fx_rate`), `currency_selected` (1,033), `amount_entered` (1,033,
adds `amount`), `forex_added_to_cart` (725, adds `addon_value_inr`), and
`forex_purchased` (546, **conversion event** for this add-on). Mints no
new entity/key — joins on the existing `user_id`/`application_id` envelope
columns plus `destination`/`from_currency`/`to_currency`, the same
topology as spec 04 (Recovery). All 5 tables follow D8's sort-key fix
(`ORDER BY (toDate(timestamp), destination, user_id, id)`, `MergeTree`)
and deliberately upgrade `destination` to `FixedString(2)` rather than
`LowCardinality(String)` — a checked exception to specs 01–04's pattern,
justified in `justification.md`'s "Column choices". Created 5 new table
pages (`forex_offer_shown.md`, `currency_selected.md`, `amount_entered.md`,
`forex_added_to_cart.md`, `forex_purchased.md`), added a "Forex Add-on"
entity section to `relationship.md`, and added a row + narrative paragraph
to `known_issues.md` → D2.

**Key risks carried forward** (per `justification.md`'s citations —
D2/D6/D8/D9/D1/D7): **D2 — `application_id` 0% overlap on all 5 tables**
(`load_report.md`, verified) — same STOP verdict as specs 01–04; analyse
standalone. **D6** — no repeat users (`distinct(user_id) == row count` on
all 5). **D8** — sort key correctly avoids the baseline anti-pattern.
**D9** — `device_type` reproduces the `Desktop`/`ios` casing collision.
**D7** — `addon_value_inr` is revenue-shaped; report with `from_currency`
scope named (INR-only in this sample). **D1** — the PM's headline
attach-rate question (`forex_offer_shown` → `forex_purchased`, currently
an unverified row-count ratio at 18.83%) must be computed by set
membership, not `windowFunnel`, once an analysis question runs.

**No PM questions answered this pass** — `out/05_instant_forex/analysis/`
does not exist yet (question_extractor.py / the Analysis Agent has not run
for this spec). Noted as an open item: the attach-rate metric, the
`currency_selected`/`amount_entered` row-count coincidence (1,033 each,
unconfirmed as a true 1:1 pairing), and the `user_id` overlap check
against the main funnel (not yet run, same open item spec 04 still
carries) are all still unverified.

Evidence: `out/05_instant_forex/ddl.sql`, `justification.md`, `profile.md`,
`load_report.md`. Regenerated `tables/index.md` (33 tables total, 2,510,100
rows), `index.md`, and `relationship.md`'s entity/join-map sections.

## 2026-08-02 — Spec `04_checkout_recovery_3` analysis consolidated — duplicate-load question resolved, K5 re-tested, recovery rate verified

`out/04_checkout_recovery_3`'s `ddl.sql`/`justification.md`/`profile.md`/
`load_report.md` re-confirm the same 6-table Abandoned Checkout Recovery
family already documented (`abandonment_detected`, `reminder_sent`,
`reminder_opened`, `reminder_cta_clicked`, `resumed_at_step`,
`reconverted`) — no new tables, no `ALTER`s, same D1/D2/D6/D8/D9 risk set
as the prior consolidation (see the entry below). This run's
`analysis/` directory now has 4 question files
(`q01.md`–`q04.md`), the first ever produced for spec 04, and this pass
consolidates their findings into the 6 table pages, `tables/index.md`,
`known_issues.md`, `index.md`, and a new `metrics/recovery_rate.md` page.

**PM questions answered, headline findings:**
- **q01 — recovery rate by `drop_step`:** verified (`user_id` set-membership
  join, 93/93 `reconverted` ⊆ 2,300 `abandonment_detected`). Flat
  4.45%–4.80% for `application_started`/`pay_now_clicked`/`document_uploaded`,
  worst at 2.62% for `destination_card_clicked`. Overall 4.04%. Also
  independently re-confirmed the live row counts of `abandonment_detected`
  (2,300) and `reconverted` (93) are not doubled.
- **q02 — which channel recovers best:** verified (`user_id` join,
  `reminder_sent → reminder_opened → reminder_cta_clicked → reconverted`,
  no fan-out). WhatsApp wins open rate (46.28%) but **push** wins
  end-to-end recovery-of-sent (4.66% vs. 4.34%) — the K5 (WhatsApp nudge)
  re-test: partially confirmed, WhatsApp drives engagement but is not the
  best channel overall. Also independently re-checked all 6 tables' live
  row counts against the documented figures — no duplication.
- **q03 — does timing (`hours_since_drop`) matter:** verified, no
  meaningful effect — recovery rate ranges only 3.46%–4.84% across
  1h/3h/6h/24h/48h delays, no monotonic pattern, within ~1 SE of the
  pooled base rate. Also independently re-confirmed `reminder_sent`'s live
  row count (2,300, not 4,600).
- **q04 — segment cuts + bonus (does recovery target the real funnel's
  worst drop-offs):** device/geo/destination cuts are mostly flat and
  small-n. **New finding:** recovery does *not* target the real funnel's
  actual worst drop-offs — the two biggest real leaks (845,587 and
  133,967 non-progressors) get flagged for recovery at only 0.08%/0.39%,
  while two much smaller late-stage leaks get flagged at 12.2%/5.2%
  (30–150× higher) — a targeting/detection-coverage gap, not a "recovery
  works better there" story. Also independently re-confirmed
  `abandonment_detected`/`reconverted` live counts.

**Duplicate-load question resolved.** All 4 files independently ran live
`count()`/`uniqExact(user_id)` against these 6 tables and found the exact
documented figures (2,300/2,300/690/268/268/93) — no duplication. The
`out/04_checkout_recovery_3` resubmission did not double any table's true
row count; the platform-wide 2,503,863-row total stands confirmed.

**Still open:** the `abandonment_detected → reminder_sent` step and the
`reminder_cta_clicked → resumed_at_step → reconverted` leg specifically —
every joined query reaches `reconverted` directly, bypassing
`resumed_at_step`, so its own step-through ratios remain unverified. The
`user_id` overlap-check against the main funnel (flagged as a follow-up in
`justification.md`) also still has not been run by any `analysis/qNN.md`
file.

**Evidence:** `out/04_checkout_recovery_3/ddl.sql`,
`out/04_checkout_recovery_3/justification.md`,
`out/04_checkout_recovery_3/profile.md`,
`out/04_checkout_recovery_3/load_report.md`,
`out/04_checkout_recovery_3/analysis/q01.md`–`q04.md`. Pages touched: all
6 spec-04 table pages, `tables/index.md`, `known_issues.md` (D1 addendum,
D2 resolution, K5 re-test verdict), `index.md`, new
`metrics/recovery_rate.md` + `metrics/index.md`.

## 2026-08-02 — Spec 04 resubmitted as `04_checkout_recovery_3` — same 6 tables, no new tables, open duplicate-load question

`out/04_checkout_recovery_3` re-profiles, re-justifies, and re-loads the
identical 6-table Abandoned Checkout Recovery family already documented
under `out/04_abondon_checkout_recovery_2` (`abandonment_detected`,
`reminder_sent`, `reminder_opened`, `reminder_cta_clicked`,
`resumed_at_step`, `reconverted`). `ddl.sql` uses `CREATE TABLE IF NOT
EXISTS` — no new tables created, no `ALTER`s, no new columns, no change to
the 28-table count. Per SCHEMA.md's create-vs-update rule, no new page was
created (never `_v2`); instead all 6 existing table pages, `tables/index.md`,
`known_issues.md`, `relationship.md`, and this wiki's root `index.md` were
updated in place: their `source` frontmatter now also cites this spec's
`ddl.sql`/`justification.md`/`load_report.md`, and each carries a new note
flagging an **open, unresolved question** — `load_report.md` from this run
reports byte-identical row counts (2,300/2,300/690/268/268/93) and an
identical D2 verdict (`overlap_pct = 0.0%` on all 6, STOP) to the original
load, but neither run's `load_report.md` states whether this resubmission's
`INSERT` step was idempotent (no new rows) or a genuine duplicate re-insert
(silently doubling each table's true live row count, and with it the
platform-wide 2,503,863-row total). `CREATE TABLE IF NOT EXISTS` only
guarantees the DDL is skipped, not the load. This wiki has no live DB
access to resolve it with a `SELECT count()`, and no `analysis/qNN.md`
file exists for this spec (under either output directory) to settle it by
live query either.

**Risks carried forward, evidence from `out/04_checkout_recovery_3/
justification.md` and `load_report.md`:** identical D1/D2/D6/D8/D9 set as
the original spec 04 run — no new risk, no new finding beyond the
duplicate-load question above. The still-outstanding `user_id` overlap
check against the main funnel (flagged as this spec's first
join-integrity test, per `known_issues.md` → D2 and `relationship.md` →
"Recovery") has still not been run.

**No PM questions answered** — `out/04_checkout_recovery_3/analysis` does
not exist; nothing to consolidate from the Analysis Agent for this spec.

## 2026-08-02 — Spec 04 (Abandoned Checkout Recovery) instrumented

6 new tables created (no `ALTER`s): `abandonment_detected` (2,300 rows),
`reminder_sent` (2,300), `reminder_opened` (690), `reminder_cta_clicked`
(268), `resumed_at_step` (268), `reconverted` (93) — new pages under
[tables/](tables/index.md), all `status: verified` via `load_report.md`
row counts. None share grain with an existing table or with each other's
business concept closely enough to warrant folding (`reconverted` was
checked column-by-column against `purchase_completed` and kept separate —
see [reconverted.md](tables/reconverted.md)). All 6 use `ENGINE =
MergeTree`, D8-compliant `ORDER BY (toDate(timestamp), drop_step|channel,
user_id, id)` — no new anti-pattern. `tables/index.md` and
[index.md](index.md) regenerated (28 tables, 2,503,863 total rows).
Added a new **Recovery** entity section to
[relationship.md](relationship.md) (no new spec-local key — joins on
existing `user_id`/`application_id` plus `drop_step`/`channel`).

**Risks carried forward, evidence from `out/04_abondon_checkout_recovery_2/
justification.md` and `load_report.md`:**
- **D2** — all 6 tables' `application_id` returned **0.0% overlap**
  against `application_started` (`load_report.md`, 2026-08-02) — the same
  STOP verdict as specs 01–03. Analyse standalone. New, not yet run:
  `justification.md` flags that this spec's `user_id` (well-formed,
  unlike its `application_id`) has **not** been overlap-checked against
  the main funnel — the first join-integrity test this spec should get.
- **D8** — confirmed not replicated; D9 casing collision noted as usual.
- **D1** — no monotonicity/set-membership check has run on the 6-table
  recovery chain; every step-through figure documented is a row-count
  ratio from `profile.md`/`load_report.md`, not a verified join.
- **K5 (WhatsApp nudge)** — updated from "unverifiable — not instrumented"
  to "now instrumented, re-test pending": this spec's `channel` column and
  `resumed_at_step` return event resolve both of K5's original blockers.
  The re-test itself (a real query, not row-count ratios) has **not**
  been run — no live DB access here, and `load_report.md` only ran the D2
  check for this spec. The row-count-ratio picture in the meantime:
  WhatsApp leads on open rate (46.28%) but push edges it out on
  end-to-end recovery-of-sent (4.66% vs. 4.34%; email lowest at 2.80%) —
  see [reminder_sent.md](tables/reminder_sent.md).

**No `analysis/qNN.md` files exist yet for this spec** — the
`analysis/` directory hasn't been created (question_extractor.py /
Analysis Agent haven't run for spec 04 yet), so nothing to consolidate
this pass. Once they exist, the first analyses to run are: (1) the K5
re-test by real set-membership/monotonicity join, not row-count ratio;
(2) the `user_id` overlap check against `application_started` flagged
above.

Evidence: `out/04_abondon_checkout_recovery_2/ddl.sql`,
`out/04_abondon_checkout_recovery_2/justification.md`,
`out/04_abondon_checkout_recovery_2/profile.md`,
`out/04_abondon_checkout_recovery_2/load_report.md`.

## 2026-08-02 — Spec 03 (Visa Status Sharing) analysis consolidated

Consolidated 4 PM-question answers (`out/03_status_sharing/analysis/q01.md`–
`q04.md`) into the wiki — no new tables or `ALTER`s this pass, only
knowledge updates. All 5 table pages
([share_clicked](tables/share_clicked.md),
[channel_selected](tables/channel_selected.md),
[link_generated](tables/link_generated.md),
[link_opened](tables/link_opened.md),
[recipient_cta_clicked](tables/recipient_cta_clicked.md)) updated;
[relationship.md](relationship.md) → "Share"; [known_issues.md](known_issues.md)
D1, D2, D3; two new metric pages.

**Headline findings, by question:**
- **q01** (share rate by `status_shared`): share-flow completion is **71.5%**
  overall (1,144/1,600), verified by set-membership join on `share_id` (not
  row-count ratio) — and essentially flat across status (70.11%–73.33%, no
  monotonic pattern, `processing` highest not `approved`). **No, approvals
  are not shared/completed more.** Also confirms `channel_selected` and
  `link_generated` hold the exact same 1,144 `share_id`s — the 1:1 pairing
  flagged at instrumentation time is now confirmed. New page:
  [metrics/share_completion_rate.md](metrics/share_completion_rate.md).
- **q02** (channel mix / new-user opens): WhatsApp dominates both channel
  selection (54.63%) and new-user opens (61.51% new-user rate, 56.3% of all
  new-user opens) — wins on efficiency, not just volume.
- **q03** (recipient K-factor): verifies `recipient_cta_clicked.share_id ⊆
  link_opened.share_id` **100%** by set membership — closes one of the two
  open D1 join edges for this spec (the other, sharer-side ↔ recipient-side,
  remains open). Surfaces a **new data-quality finding**:
  `recipient_is_new_user` is not stable per `share_id` — 472/922 shares
  (51.2%) show conflicting values across reopens, the same self-contradicting
  shape as D3's `is_crossed_failed_attempt_threshold` (added as a D3
  addendum). Segmenting to internally-consistent shares gives a K-factor of
  **38.13%** (pure new-user) vs. **0.00%** (pure existing-user). New page:
  [metrics/recipient_conversion_k_factor.md](metrics/recipient_conversion_k_factor.md).
- **q04** (destination spread): two correct answers depending on definition
  — **AU** leads raw reach (223 opens), **AE** leads conversion efficiency
  (16.37% opens→CTA rate, vs. AU's 10.76%).

**Key risks carried forward, updated:**
- **D1** — 2 of 3 `share_id` join edges now verified (sharer-side internal:
  `q01.md`; recipient-side internal: `q03.md`); the sharer-side ↔
  recipient-side edge itself is still unverified — open work.
- **D2** — the 0% `application_id` overlap (`load_report.md`) is now
  independently re-confirmed by all 4 analysis questions, none of which
  found a working path back to `application_started` — same pattern as
  specs 01 and 02.
- **D3** — extended (not replaced) to cover `recipient_is_new_user`'s
  self-contradiction, a new instance of the same flag-integrity trap on a
  different table/column.

**Evidence:** `out/03_status_sharing/analysis/q01.md`–`q04.md` (all 4 read
before writing, per SCHEMA.md's consolidation practice), cross-checked
against `out/03_status_sharing/load_report.md` and `justification.md` for
consistency. No open caveat resolved by this pass: the sharer-side ↔
recipient-side `share_id` join remains unverified — flagged in D1,
`relationship.md`, and every affected table page for the next Analysis
Agent pass.

## 2026-08-02 — Spec 03 (Visa Status Sharing) instrumented

Five new `CREATE TABLE` statements, no `ALTER`s, no materialized view (6,503
total rows — too small to warrant pre-aggregation). New `Share` entity
(`share_id`, `FixedString(32)`, spec-local, mirroring `group_id`'s
precedent). New pages: [share_clicked](tables/share_clicked.md) (1,600
rows), [channel_selected](tables/channel_selected.md) (1,144),
[link_generated](tables/link_generated.md) (1,144, byte-for-byte identical
column set to `channel_selected` — flagged as a possible 1:1 pairing, not
resolved), [link_opened](tables/link_opened.md) (2,310, recipient-side, no
`user_id`), [recipient_cta_clicked](tables/recipient_cta_clicked.md) (305,
recipient-side, the spec's K-factor numerator). All 5 follow D8 (no
new table leads its sort key with a random `id`), each substituting its own
leading discriminator (`status_shared`/`channel`/`destination`) per
`justification.md`.

**Key risks carried forward:**
- **D2** — `application_id` normalized and D2-verified on the 3 sharer-side
  tables (`share_clicked`/`channel_selected`/`link_generated`):
  **`overlap_pct = 0.0%`** on all 3 against `application_started` → **STOP**,
  analyse standalone (`out/03_status_sharing/load_report.md`, 2026-08-02) —
  the same verdict specs 01 and 02 got, now confirmed a fourth time. The 2
  recipient-side tables carry no `application_id` at all.
- **D1** — the sharer-side ↔ recipient-side `share_id` join and every
  step-through figure in this spec (share → channel select → link generate
  → open → recipient CTA) are **unverified row-count ratios only** — no
  set-membership check has run.
- **`analysis/` does not exist yet for this spec** — question_extractor.py
  and the Analysis Agent have not run for spec 03. No PM questions were
  answered this pass; nothing to consolidate from `analysis/qNN.md` files.
  Next Analysis Agent pass should prioritize: (1) set-membership verifying
  the `share_id` join between sharer- and recipient-side tables, (2)
  checking whether `channel_selected`/`link_generated` are truly a 1:1
  pairing, (3) computing the K-factor from `recipient_cta_clicked`, (4) the
  `status_shared` vs. share-rate cut the PM's Q1 asks for.

**Also updated:** `tables/index.md` (5 new rows, total rows 2,491,441 →
**2,497,944**, 17 → **22** tables), `context/index.md` (same rollup),
`relationship.md` (new "Share" entity section, `share_id` join-map entry,
"Entities the incoming specs will add" bullet marked instrumented),
`known_issues.md` (D2 verdicts table + narrative addendum for spec 03).

**Evidence:** `out/03_status_sharing/ddl.sql`,
`out/03_status_sharing/justification.md`, `out/03_status_sharing/profile.md`,
`out/03_status_sharing/load_report.md`.

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
