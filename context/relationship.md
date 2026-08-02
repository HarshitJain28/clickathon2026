---
id: doc.relationship
kind: relationship
status: verified
confidence: high
source: clickathon DB — set-membership joins, cardinality and key-format profiling across all 8 tables; out/01_express_checkout/load_report.md — D2 overlap_pct for the 5 Express Checkout tables; out/01_express_checkout/analysis/q01.md–q04.md — independent re-confirmation; out/02_group_family/load_report.md — D2 overlap_pct for the 4 Group/Family tables; out/02_group_family/analysis/q01.md–q04.md — independent re-confirmation, group completion-rate and churn analysis; out/03_status_sharing/load_report.md — D2 overlap_pct for 3 of the 5 Status Sharing tables; out/03_status_sharing/analysis/q01.md–q04.md — independent re-confirmation, share-flow completion rate, K-factor; out/04_abondon_checkout_recovery_2/load_report.md — D2 overlap_pct for all 6 Abandoned Checkout Recovery tables; out/04_checkout_recovery_3/load_report.md — identical D2 overlap_pct on independent resubmission, raises open duplicate-load question; out/05_instant_forex/load_report.md — D2 overlap_pct for all 5 Instant Forex tables; out/05_instant_forex/analysis/q01.md–q04.md — independent re-confirmation, verified full-funnel step-through, attach rate by destination/currency/device/geo, AOV
last_verified: 2026-08-02
links: [doc.business, doc.known_issues, tables.index]
---

# Entities and relationships

What the domain objects are, how they join, and the key formats that make joins
work or silently fail. All figures measured against `clickathon`, H1 2026.

---

## 1. Entities

### User

A traveller. `user_id` is **non-null on every row of all 8 tables**, and is
**exactly 28 characters** everywhere.

**⚠ Exactly one event per user.** Verified: all 1,000,000 users in
`destination_card_clicked` have exactly 1 row; all 154,413 users in
`application_started` have exactly 1 application. No repeat users exist anywhere.

`base_context.md` §2 says "a user may browse many destinations and start multiple
applications" — **false for this dataset.** Retention, repeat purchase, LTV, and
win-back analysis are therefore **impossible**, not merely empty. Say so rather
than returning zeros. See [known_issues.md](known_issues.md) → D6.

Cohort sizes:

| Cohort | Users |
|---|---:|
| Clicked a destination card | 1,000,000 |
| Authenticated | 183,790 |
| **Authenticated but never applied** | **29,377** ← undocumented, un-analysed |
| Started an application | 154,413 |
| Purchased | 7,054 |

Attributes: `citizenship` (11 values, **lowercase**), `is_guest`, `is_new_user`
(54.9% new), `is_referral`, `is_enterprise`.

### Application

One visa application, created at `application_started`. **154,413 exist**, one
per applying user.

**⚠ Identifier format — the highest-risk join in the system:**

| Context | Format | Length |
|---|---|---|
| **Database** | hyphenated UUID `78577aff-b013-df04-7378-94976315aad2` | 36 |
| **Incoming spec NDJSON** | unhyphenated hex `d09c8c32765b96d17f130a9c5dbf7b4a` | 32 |

These do not join. A new spec table joined as-is returns **zero rows without
erroring**. Normalize on ingest — see [known_issues.md](known_issues.md) → D2.

**Spec 01 (Express Checkout) confirms this is not just a formatting problem.**
Its 5 new tables (`express_checkout_shown`, `express_checkout_selected`,
`saved_method_used`, `otp_entered`, `express_payment_confirmed`) had
`application_id` normalized on ingest (dashes inserted, 32→36 chars) per D2's
fix, then the mandatory overlap-check ran against `application_started` —
**`overlap_pct = 0.0%` on all 5 tables** (`out/01_express_checkout/load_report.md`,
2026-08-01). Per D2's own action table, this is **STOP**: these tables do not
join the main Application/User funnel via `application_id` even after
normalization, and must be analysed standalone until re-tested. See
[known_issues.md](known_issues.md) → D2 for the dated verdict.

Attributes: `destination`, `purpose` (`business`/`medical`/`tourism`/`transit`),
`co_travelers`, `funnel_type` (`b2c`/`b2c_afc`/`b2c_black`), `flow`, and
**`eta_shown`** — a categorical **string** (`24 hours`, `3-5 days`, `5-7 days`,
`7-10 days`), *not* the integer `visa_issuance_eta_days` that `base_context.md`
describes. That column does not exist.

Mean time from application start to purchase: **110.5 minutes**.

### Destination

Target country, ISO-2 **uppercase**, in the `destination` column (present on all
8 tables).

**27 destinations, not "120+":**
`AE AU CA CH EG ES FR GB GR HK ID IT JP KR LK MA MV MY OM QA SA SG TH TR US VN ZA`

**⚠ Region is not a column.** `base_context.md` references GCC / SEA / Schengen /
Americas — none of these exist in any table. Any region cut is an
analyst-supplied mapping and must be labelled as such. Working assumption used
in this wiki (an assumption, **not** a data fact): `schengen = FR, ES, IT, GR, CH`.

**Do not confuse `destination` with `citizenship`** — both are country codes but
differ in case and meaning:

| Column | Meaning | Case | Values |
|---|---|---|---|
| `destination` | travelling **to** | **UPPER** (`IN`) | 27 |
| `citizenship` | passport held | **lower** (`in`) | 11 |

Comparing them without normalizing case yields silent zero matches.

### Document

The passport captured at KYC, in `document_uploaded`. **20,446 documents**, one
per user. `doc_type` is **single-valued** (`passport_front`) and therefore
useless as a cut.

**⚠ Its quality flag is internally inconsistent** —
`is_crossed_failed_attempt_threshold` does not track `retry_count`.
See [known_issues.md](known_issues.md) → D3.

### Group

A family/group travel unit, created at `group_started` (spec 02). **1,200
groups** exist in the profiled sample (2026-06-08 → 2026-06-28), one per
group-starting user. Key: `group_id`, `FixedString(32)` — a **spec-local**
key that does not join `application_id` or `user_id` outside this spec's own
4 tables.

Row counts (spec 02 sample):

| Table | Rows | Distinct `group_id` |
|---|---:|---:|
| `group_started` (origin) | 1,200 | 1,200 |
| `traveller_added` | 3,495 | 1,200 |
| `traveller_removed` | 70 | 69 |
| `group_submitted` | 688 | 688 |

**⚠ `application_id` does not join `application_started` — 0% overlap.**
Even though `application_id` is present on 100% of rows across all 4 tables,
the mandatory D2 overlap-check against `application_started` returned
**`overlap_pct = 0.0%`** on all 4 (`out/02_group_family/load_report.md`,
2026-08-02) — the same STOP verdict spec 01's 5 tables got. Analyse the
group flow standalone until re-tested. See
[known_issues.md](known_issues.md) → D2.

**⚠ Conflicts with `co_travelers`.** `application_started.co_travelers`
(envelope column, set once at application creation) and this entity's
`group_size`/`travellers_submitted` (live, mutable group-flow counts) can
legitimately diverge for the same `application_id`. Checked at the schema
level — no column was added to or duplicated from `application_started`, so
no parallel model exists in the schema — but reconciling which count is
authoritative is unresolved analysis-layer work
(`out/02_group_family/justification.md` "Risks / caveats").

**`traveller_added`/`traveller_removed` break the "no repeat users"
pattern** (see [known_issues.md](known_issues.md) → D6): both have repeat
`user_id`s by design — one group owner performs multiple add/remove actions
(`traveller_added`: 3,495 rows / 1,200 distinct users; `traveller_removed`:
70 rows / 69 distinct users) — unlike every baseline table and spec 01's 5
tables, all of which have exactly one row per user.

**Completion rate falls monotonically as `group_size` grows — verified
2026-08-02** (`out/02_group_family/analysis/q01.md`, `q03.md`, both by
verified set membership, not `windowFunnel`, per D1): 69.47% at size 2 down
to 31.11% at size 6, a 38pp spread that dwarfs every other segment cut
tested (`destination` ~14pp, `device_type` flat, `geoip_country_code`
volume-concentration only — `q04.md`). Add/remove churn is real but small
(`q02.md`): 3,495 adds vs. 70 removals (**3,425 net-added**), only 5.75% of
groups (69/1,200) ever have a removal, and every removed `group_id` is
confirmed present in both `group_started` and `traveller_added` (100% set
membership — removals are consistent, not orphaned). Removal rate itself
rises sharply with `group_size` (0.42% at size 2 → 18.4% at size 5), a
plausible contributor to the completion-rate gap. See
[group_started.md](tables/group_started.md),
[traveller_added.md](tables/traveller_added.md),
[traveller_removed.md](tables/traveller_removed.md), and
[metrics/group_completion_rate_by_size.md](metrics/group_completion_rate_by_size.md).

Attributes: `group_size` (`UInt8`, range `[2, 6]`), `relation`
(`friend`/`spouse`/`child`/`sibling`/`parent`, `traveller_added` only),
`docs_complete` (`Bool`, `traveller_added` only), `travellers_submitted`
(`UInt8`, range `[1, 6]`, `group_submitted` only). See
[tables/group_started.md](tables/group_started.md) and its 3 sibling pages.

### Share

A visa-status share, created at `share_clicked` (spec 03). **1,600 shares**
exist in the profiled sample (2026-06-08 06:00 → 2026-07-01 09:21), one per
sharer. Key: `share_id`, `FixedString(32)` — a **spec-local** key that does
not join `application_id`, `user_id`, or `group_id` outside this spec's own
5 tables.

Row counts (spec 03 sample):

| Table | Rows | Distinct `share_id` | Has `user_id`? |
|---|---:|---:|---|
| `share_clicked` (origin) | 1,600 | 1,600 | yes |
| `channel_selected` | 1,144 | 1,144 | yes |
| `link_generated` | 1,144 | 1,144 | yes |
| `link_opened` (recipient-side) | 2,310 | 922 | **no** |
| `recipient_cta_clicked` (recipient-side, K-factor) | 305 | 263 | **no** |

**⚠ Recipient-side events carry no `user_id` at all** — confirmed exactly as
this section anticipated before instrumentation (see below): `link_opened`
and `recipient_cta_clicked` are keyed only by `share_id`, per `spec.md` and
`profile.md` (neither shows any of the 30 envelope columns). This is a join
topology nothing else in this dataset uses — the sharer-side tables join
each other and the main funnel via `user_id`/`application_id`, but there is
no column to join sharer-side rows to recipient-side rows on **except
`share_id` itself**. **2026-08-02 update:** two of the three `share_id`
join edges are now **verified** by set membership
(`out/03_status_sharing/analysis/q01.md`, `q03.md`) —
`share_clicked → channel_selected`/`link_generated` (sharer-side, 71.5%) and
`link_opened → recipient_cta_clicked` (recipient-side, 100%). **The
sharer-side ↔ recipient-side edge itself** (e.g. `link_generated.share_id`
vs. `link_opened.share_id`) **remains unverified** — no `analysis/qNN.md`
file has checked it yet. See [known_issues.md](known_issues.md) → D1.

**⚠ `application_id` does not join `application_started` — 0% overlap on
the 3 sharer-side tables.** `application_id` is present on 100% of rows
across `share_clicked`/`channel_selected`/`link_generated` (the two
recipient-side tables carry no `application_id` at all). The mandatory D2
overlap-check ran against `application_started` and returned
**`overlap_pct = 0.0%`** on all 3 (`out/03_status_sharing/load_report.md`,
2026-08-02) — the same STOP verdict specs 01 and 02 got. **2026-08-02 —
independently re-confirmed by all 4 of the Analysis Agent's questions for
spec 03** (`out/03_status_sharing/analysis/q01.md`–`q04.md`), each of which
stayed within the share flow's own 5 tables (joined on `share_id`, `user_id`,
or a table's own `destination`/`channel` column instead) rather than
attempting the broken `application_id` join. Analyse the share flow
standalone. See [known_issues.md](known_issues.md) → D2.

Attributes: `status_shared` (`submitted`/`processing`/`approved`,
sharer-side), `channel` (`whatsapp`/`copy_link`/`email`/`sms`),
`recipient_is_new_user` (`Bool`, `link_opened` only — a real K-factor /
viral-acquisition signal), `cta` (single-valued today,
`start_own_application`, `recipient_cta_clicked` only). See
[tables/share_clicked.md](tables/share_clicked.md) and its 4 sibling pages.

### Recovery

An abandoned-checkout recovery attempt, originating at
`abandonment_detected` (spec 04). **2,300 detected drops** exist in the
profiled sample (2026-06-08 06:01 → 2026-07-01 00:00), one per dropping
user. No new key/entity id is minted here — the 6 tables join each other
on the existing `user_id`/`application_id` envelope columns plus two
shared context columns, `drop_step` and `channel`, rather than a
spec-local key like `group_id`/`share_id`.

Row counts (spec 04 sample):

| Table | Rows | Distinct `user_id` |
|---|---:|---:|
| `abandonment_detected` (origin) | 2,300 | 2,300 |
| `reminder_sent` | 2,300 | 2,300 |
| `reminder_opened` | 690 | 690 |
| `reminder_cta_clicked` | 268 | 268 |
| `resumed_at_step` | 268 | 268 |
| `reconverted` | 93 | 93 |

**⚠ `application_id` does not join `application_started` — 0% overlap on
all 6 tables.** `application_id` is present on 100% of rows across every
one of the 6 tables. The mandatory D2 overlap-check ran against
`application_started` and returned **`overlap_pct = 0.0%`** on all 6
(`out/04_abondon_checkout_recovery_2/load_report.md`, 2026-08-02) — the
same STOP verdict specs 01–03 got. Analyse the recovery flow standalone
until re-tested. See [known_issues.md](known_issues.md) → D2.

**Unlike specs 01–03, this spec's own `justification.md` flags a
follow-up not yet run:** its `user_id` values are well-formed 28-char
strings matching this document's stated format exactly, and — unlike
`application_id` — have **not** been overlap-checked against
`application_started`/`destination_card_clicked`. `load_report.md` only
ran the D2 check on `application_id`; no `analysis/qNN.md` file exists yet
for this spec to have run the `user_id` check either. This is the
first join-integrity test that should be run for this spec, before
assuming the flow is standalone by default the way specs 01–03 turned
out to be.

**The 6-table step-through chain (recovery funnel) is currently only
row-count ratios**, not verified set membership — no `analysis/qNN.md`
file exists yet for this spec. Overall: `reconverted` ÷
`abandonment_detected` = 93/2,300 = **4.04%**, the PM's headline recovery
metric. Per-channel: WhatsApp opens best (46.28% vs. push 28.30%, email
21.24%) but push edges WhatsApp on end-to-end recovery-of-sent (4.66% vs.
4.34%; email lowest at 2.80%). See
[abandonment_detected.md](tables/abandonment_detected.md) and
[reminder_sent.md](tables/reminder_sent.md) for the full breakdown, and
[known_issues.md](known_issues.md) → K5, which this spec's `channel` and
`resumed_at_step` columns now make re-testable (not yet re-tested — no
live query has run).

**⚠ 2026-08-02 — resubmitted under a new output directory,
`out/04_checkout_recovery_3`, with byte-identical row counts and D2
verdict.** `ddl.sql` uses `CREATE TABLE IF NOT EXISTS`, so no new tables
were created, but whether the accompanying load re-inserted the same rows
on top of the original load (doubling each table's true live count) is
**not stated** by either run's `load_report.md` — an open question, not
yet resolvable without a live query. See
[known_issues.md](known_issues.md) → D2 and
[tables/abandonment_detected.md](tables/abandonment_detected.md) for the
full reasoning, carried on all 6 table pages. The row counts above should
be treated as unverified against this possibility.

Attributes: `drop_step` (`document_uploaded`/`destination_card_clicked`/
`application_started`/`pay_now_clicked` — which of the 4 existing funnel
tables the user last touched before dropping), `channel`
(`push`/`email`/`whatsapp`, on 5 of the 6 tables — absent from
`abandonment_detected`), `hours_since_drop` (`UInt8`, range `[1, 48]`,
`reminder_sent` only). See
[tables/abandonment_detected.md](tables/abandonment_detected.md) and its
5 sibling pages.

### Forex Add-on

An instant-forex add-on purchase, originating at `forex_offer_shown` (spec
05). **2,900 offers shown** in the profiled sample (2026-06-08 06:00 →
2026-06-28 23:12), one per offered user. No new key/entity id is minted
here — like Recovery (spec 04), the 5 tables join each other on the
existing `user_id`/`application_id` envelope columns plus the shared
context columns `destination`/`from_currency`/`to_currency`, rather than a
spec-local key like `group_id`/`share_id`.

Row counts (spec 05 sample):

| Table | Rows | Distinct `user_id` |
|---|---:|---:|
| `forex_offer_shown` (origin) | 2,900 | 2,900 |
| `currency_selected` | 1,033 | 1,033 |
| `amount_entered` | 1,033 | 1,033 |
| `forex_added_to_cart` | 725 | 725 |
| `forex_purchased` (**conversion**) | 546 | 546 |

**⚠ `application_id` does not join `application_started` — 0% overlap on
all 5 tables.** `application_id` is present on 100% of rows across every
one of the 5 tables. The mandatory D2 overlap-check ran against
`application_started` and returned **`overlap_pct = 0.0%`** on all 5
(`out/05_instant_forex/load_report.md`, 2026-08-02) — the same STOP
verdict specs 01–04 got. Analyse the forex flow standalone. **2026-08-02:**
independently re-confirmed by all 4 of the Analysis Agent's questions for
this spec (`out/05_instant_forex/analysis/q01.md`–`q04.md`), each of which
stayed within the forex flow's own 5 tables (joined on `user_id` instead,
safe per D6) — no question found a working path back to
`application_started` or the main funnel. See
[known_issues.md](known_issues.md) → D2.

**The 5-table step-through chain (forex funnel) is now verified by set
membership, not row-count ratios** (source: `out/05_instant_forex/
analysis/q01.md`, `q03.md`, `q04.md`, 2026-08-02) — confirmed **perfectly
nested** end-to-end and 100% timestamp-monotonic. Overall attach rate:
`forex_purchased` ÷ `forex_offer_shown` = 546/2,900 = **18.83%**, the PM's
headline attach-rate metric, verified by exact `uniqExact(user_id)` join.
By `destination`: best US 24.58%, worst AU 13.78% (~11pp spread, 14 of 27
destinations observed). `currency_selected` and `amount_entered` share an
identical row count (1,033) and are now **confirmed** a true 1:1 pairing
(100% step-through, direct set-membership join) — the same pattern spec
03's `channel_selected`/`link_generated` turned out to have. The funnel's
big leak (64.38%, 1,867 users) is concentrated entirely at
`forex_offer_shown → currency_selected` — the added-to-cart→purchased
step loses only 24.69%. AOV among the 546 attachers is right-skewed
(median ₹31,685, mean ₹40,587.77, INR only, per D7). See
[forex_offer_shown.md](tables/forex_offer_shown.md) and its 4 sibling
pages, [metrics/forex_attach_rate.md](metrics/forex_attach_rate.md), and
[metrics/forex_addon_aov.md](metrics/forex_addon_aov.md).

Attributes: `destination` (`FixedString(2)`, this spec's leading sort-key
discriminator — a deliberate upgrade from `LowCardinality(String)`),
`from_currency` (`FixedString(3)`, single-valued `INR` in this sample),
`to_currency` (`FixedString(3)`, 13 values), `fx_rate` (`Float64`,
`forex_offer_shown` only), `amount` (`UInt16`, on 3 of the 5 tables),
`addon_value_inr` (`Float64`, revenue-shaped, on 2 of the 5 tables — see
[known_issues.md](known_issues.md) → D7). See
[tables/forex_offer_shown.md](tables/forex_offer_shown.md) and its 4
sibling pages.

### Entities the incoming specs will add

- **Group** (spec 02) — **instrumented 2026-08-02, see "Group" above.** The
  `co_travelers` conflict flagged here was checked (no parallel schema-level
  model was created) but remains unresolved at the analysis layer.
  **2026-08-02:** all 4 of the Analysis Agent's PM-question answers for this
  spec independently worked around the broken `application_id` join by
  joining on `group_id` (spec-local key) instead — none found a usable path
  back to `Application`. See `out/02_group_family/analysis/q01.md`–`q04.md`
  and the completion-rate/churn findings added above.

**Share (spec 03) — instrumented 2026-08-02, see "Share" above.** The
"recipient events carry no `user_id`" topology anticipated here before
instrumentation is confirmed exactly as expected. **2026-08-02:** all 4 of
the Analysis Agent's PM-question answers for this spec independently
worked around the broken `application_id` join (`out/03_status_sharing/
analysis/q01.md`–`q04.md`) — share-flow completion rate is 71.5% overall,
flat by `status_shared`; channel mix is WhatsApp-dominant (54.6% selection
share, also top new-user-open channel); the recipient K-factor is ~38%
pure-new-user / 0% pure-existing-user (after correcting for a
`recipient_is_new_user` self-contradiction in 51.2% of shares); AU leads
destination reach, AE leads destination conversion efficiency. **Still
open:** the sharer-side ↔ recipient-side `share_id` join itself (as opposed
to the two same-side edges, both now verified) has not been
set-membership checked by any analysis question yet.

**Recovery (spec 04) — instrumented 2026-08-02, see "Recovery" above.**
Unlike Group/Share, this spec mints no new spec-local key — its 6 tables
join on the existing `user_id`/`application_id` envelope columns plus
`drop_step`/`channel`. No `analysis/qNN.md` file exists yet for this
spec, so (unlike specs 01–03) none of its step-through figures are
verified set-membership joins yet — see "Recovery" above for the
row-count-ratio figures available today and the still-open `user_id`
overlap check.

**Forex Add-on (spec 05) — instrumented 2026-08-02, see "Forex Add-on"
above.** Like Recovery, this spec mints no new spec-local key — its 5
tables join on the existing `user_id`/`application_id` envelope columns
plus `destination`/`from_currency`/`to_currency`. **2026-08-02:** all 4 of
the Analysis Agent's PM-question answers for this spec independently
worked around the broken `application_id` join by joining on `user_id`
instead (safe per D6) — none found a usable path back to `Application`.
The full funnel (including the PM's headline attach-rate metric) is now
verified by set membership: 18.83% overall attach rate, best destination
US (24.58%), worst AU (13.78%); the `currency_selected`/`amount_entered`
row-count coincidence is confirmed a true 1:1 pairing; AOV among
attachers is right-skewed (median ₹31,685). See
`out/05_instant_forex/analysis/q01.md`–`q04.md` and the findings added
above.

**Spec 01 (Express Checkout) — instrumented, 2026-08-01, no new entity.**
Checked against this list per `out/01_express_checkout/justification.md`:
unlike spec 02 and spec 03, Express Checkout introduces no new entity — it is
a sequence of 5 events (`express_checkout_shown` → `express_checkout_selected`
→ `saved_method_used` → `otp_entered` → `express_payment_confirmed`) against
the existing `Application`/`User` entities, so no parallel model was created.
Its `application_id` join to `Application` is present in schema but **not
usable** — see the 0% overlap finding above and in `known_issues.md` → D2.
**2026-08-02:** all 4 of the Analysis Agent's PM-question answers for this
spec independently worked around this by joining Express Checkout's own
tables on `user_id` instead (safe per D6) — none found a usable
`application_id` path back to `Application`. See
`out/01_express_checkout/analysis/q01.md`–`q04.md`.

### Entities `base_context.md` describes that do not exist

**Session.** `app_session_id` is unique per row — in `destination_card_clicked`
there are 1,000,000 rows, 1,000,000 distinct `app_session_id`, and 1,000,000
distinct `user_id`, zero nulls. It is a row identifier, not a session. Any
metric defined "÷ sessions" is dividing by a row count.
See [known_issues.md](known_issues.md) → D4.

---

## 2. Join integrity — verified by set membership

| Relationship | Result |
|---|---|
| `application_started.user_id` ⊆ `destination_card_clicked.user_id` | **100%** (154,413 / 154,413) |
| `document_uploaded.user_id` ⊆ `application_started.user_id` | **100%** (20,446 / 20,446) |
| `purchase_completed.user_id` ⊆ `application_started.user_id` | **100%** (7,054 / 7,054) |
| `search_typed.user_id` ⊆ `destination_card_clicked.user_id` | **100%** (599,630 / 599,630) |
| `auth_completed.user_id` ⊆ `application_started.user_id` | **84.0%** (154,413 / 183,790) |

**The funnel is perfectly nested. Joins on `user_id` and `application_id` are
safe and lossless.** The risk is not the join — it's the time ordering (§4).

`auth_completed` is the one superset: 29,377 users authenticated but never
applied — a real, undocumented top-of-funnel cohort.

## 3. Join map

- **`user_id`** — universal, non-null everywhere. Joins any table to any table.
  Spec 04's 6 tables carry a well-formed `user_id` that has **not yet** been
  overlap-checked against the main funnel — see "Recovery" above.
- **`application_id`** — joins `application_started` → `document_uploaded`,
  `pay_now_clicked`, `purchase_completed`. **Not** usable as a join key for
  spec 01's 5 tables, spec 02's 4 tables, spec 03's 3 sharer-side tables,
  spec 04's 6 tables, or spec 05's 5 tables — all independently verified 0%
  overlap (D2).
- **`group_id`** — spec-local (spec 02 only). Joins `group_started` →
  `traveller_added`/`traveller_removed`/`group_submitted`. Does not join
  `application_id` or `user_id`.
- **`share_id`** — spec-local (spec 03 only). Intended to join
  `share_clicked`/`channel_selected`/`link_generated` (sharer-side) →
  `link_opened`/`recipient_cta_clicked` (recipient-side). **2026-08-02:**
  both same-side edges are **verified** by set membership
  (`share_clicked → channel_selected`/`link_generated`, 71.5%,
  `analysis/q01.md`; `link_opened → recipient_cta_clicked`, 100%,
  `analysis/q03.md`) — the **sharer-side ↔ recipient-side edge itself**
  remains **unverified**. Does not join `application_id`, `user_id`, or
  `group_id`.

Where `application_id` appears:

| Table | Distinct applications |
|---|---:|
| `application_started` (origin) | 154,413 |
| `auth_completed` | 154,413 |
| `destination_card_clicked` | 154,413 (of 1,000,000 rows) |
| `search_typed` | 92,440 |
| `landing_page_scrolled` | 77,362 |
| `document_uploaded` | 20,446 |
| `pay_now_clicked` | 14,739 |
| `purchase_completed` | 7,054 |

Note it is **not** empty on pre-application events as `base_context.md` claims —
it is present on exactly the 154,413 card clicks that led to an application.

## 4. ⚠ Funnel order is NOT reliable by timestamp

`base_context.md` §6 asserts "funnel order is by `timestamp` ascending". Measured
on the 7,054 applications that completed the full funnel:

| Ordering check | Holds |
|---|---:|
| `document_uploaded` after `application_started` | 95.5% |
| `purchase_completed` after `application_started` | 97.6% |
| `purchase_completed` after `document_uploaded` | **52.2%** |

Nearly half of all purchases carry a timestamp *earlier* than their own document
upload. **Never use `windowFunnel` / `sequenceMatch` on these tables** — it
silently discards 52% of conversions. See [known_issues.md](known_issues.md) → D1
for the correct method.

## 5. Segment cuts available

`device_type`, `os` (**5.95% null**), `geoip_country_code`, `destination`,
`citizenship`, `co_travelers`, `funnel_type`, `app_version`, `client_lib`, and
acquisition via `gclid` presence (22.30% of purchases).
