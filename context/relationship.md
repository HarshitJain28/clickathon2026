---
id: doc.relationship
kind: relationship
status: verified
confidence: high
source: clickathon DB — set-membership joins, cardinality and key-format profiling across all 8 tables; out/01_express_checkout/load_report.md — D2 overlap_pct for the 5 Express Checkout tables; out/01_express_checkout/analysis/q01.md–q04.md — independent re-confirmation; out/02_group_family/load_report.md — D2 overlap_pct for the 4 Group/Family tables; out/02_group_family/analysis/q01.md–q04.md — independent re-confirmation, group completion-rate and churn analysis
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

### Entities the incoming specs will add

- **Group** (spec 02) — **instrumented 2026-08-02, see "Group" above.** The
  `co_travelers` conflict flagged here was checked (no parallel schema-level
  model was created) but remains unresolved at the analysis layer.
  **2026-08-02:** all 4 of the Analysis Agent's PM-question answers for this
  spec independently worked around the broken `application_id` join by
  joining on `group_id` (spec-local key) instead — none found a usable path
  back to `Application`. See `out/02_group_family/analysis/q01.md`–`q04.md`
  and the completion-rate/churn findings added above.
- **Share** (spec 03) — `share_id`. Recipient events carry **no `user_id`**, a
  join topology nothing in this dataset currently supports.

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
- **`application_id`** — joins `application_started` → `document_uploaded`,
  `pay_now_clicked`, `purchase_completed`. **Not** usable as a join key for
  spec 01's 5 tables or spec 02's 4 tables — both independently verified 0%
  overlap (D2).
- **`group_id`** — spec-local (spec 02 only). Joins `group_started` →
  `traveller_added`/`traveller_removed`/`group_submitted`. Does not join
  `application_id` or `user_id`.

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
