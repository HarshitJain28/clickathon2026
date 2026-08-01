---
id: doc.known_issues
kind: known_issues
status: verified
confidence: high
source: clickathon DB — every claim below tested by query; see each entry for evidence; out/01_express_checkout/load_report.md — D2 verdict for spec 01's 5 tables; out/01_express_checkout/analysis/q01.md–q04.md — K1 re-test, D1 extension; out/02_group_family/load_report.md — D2 verdict for spec 02's 4 tables; out/02_group_family/analysis/q01.md–q04.md — D1/D2 re-confirmation, group_completion_rate_by_size
last_verified: 2026-08-02
links: [doc.relationship, doc.business, metrics.index, tables.index]
---

# Known issues and data traps

Everything that is wrong, suspicious, or will trip up a query. Two parts:

- **Part A — Data traps (D1–D9):** properties of the *data* that break queries.
  Permanent guard rails. **Read D1–D3 before writing any query.**
- **Part B — Known issues (K1–K7):** the product claims from `base_context.md` §5,
  each re-tested. **5 of 7 are refuted.**

---

# Part A — Data traps

> These fail **without erroring**. They return clean, plausible, wrong numbers.

## D1 — `windowFunnel` loses 52% of conversions ⛔ CRITICAL

`base_context.md` §7 says *"Prefer `windowFunnel`/`sequenceMatch`"*. On this data
that is wrong, because timestamps are not monotonic along the funnel (only 52.2%
of purchases post-date their own document upload).

Both methods, same data:

| Stage | Set membership (correct) | `windowFunnel` | Lost |
|---|---:|---:|---:|
| card clicked | 1,000,000 | 1,000,000 | — |
| app started | 154,413 | 154,413 | — |
| doc uploaded | 20,446 | 19,523 | 4.5% |
| **purchased** | **7,054** | **3,366** | **52.3%** |

Reports 2.18% conversion instead of the true 4.57%.

**✅ Fix — count by set membership:**

```sql
SELECT
  (SELECT uniqExact(user_id) FROM clickathon.destination_card_clicked) AS s1_card_clicked,
  (SELECT uniqExact(user_id) FROM clickathon.application_started)      AS s2_app_started,
  (SELECT uniqExact(user_id) FROM clickathon.document_uploaded)        AS s3_doc_uploaded,
  (SELECT uniqExact(user_id) FROM clickathon.pay_now_clicked)          AS s4_pay_clicked,
  (SELECT uniqExact(user_id) FROM clickathon.purchase_completed)       AS s5_purchased
```

Valid because the funnel is **perfectly nested** (100% of each stage's users
appear upstream). For segmented funnels, anchor on the stage owning the
dimension and semi-join with `IN`.

Time-ordered functions remain valid **within** a table, and for new feature
tables **after** verifying monotonicity:
```sql
SELECT countIf(t_later >= t_earlier) / count() AS monotonic_share FROM ...
-- below ~0.99 → use set membership
```

**2026-08-02 addendum (source: `out/01_express_checkout/analysis/q03.md`):**
the non-monotonic-timestamp trap is **confirmed to extend beyond
`document_uploaded → purchase_completed`** to `pay_now_clicked →
purchase_completed` as well — only **52.55%** of the 7,054 matched
`user_id` pairs have `purchase_completed.timestamp ≥
pay_now_clicked.timestamp`. Even restricted to the "monotonic" 3,707 pairs,
the naive average gap is ~76.9 minutes (median ~69 min) — not a payment-step
latency at all, but the whole application-session gap (consistent with
`relationship.md`'s 110.5-minute app-start-to-purchase figure). This means
`pay_now_clicked`/`purchase_completed` timestamps cannot be used as a
`shown → confirmed` payment-latency proxy for comparison against Express's
own `payment_latency_ms` — see
[express_payment_confirmed.md](tables/express_payment_confirmed.md).

**2026-08-02 addendum (source: `out/02_group_family/analysis/q01.md`,
`q03.md`):** spec 02's `group_started → group_submitted` completion-rate
question is the same funnel shape and was computed correctly — by set
membership (`group_submitted.group_id ⊆ group_started.group_id` by
construction), not `windowFunnel` — by both files independently. No
monotonicity percentage was computed for this pair (unlike the
`document_uploaded`/`pay_now_clicked` → `purchase_completed` checks above,
which have real timestamp columns to test); set membership was used
directly since it holds by construction here. See
[group_started.md](tables/group_started.md).

## D2 — Spec `application_id` won't join ⛔ CRITICAL

| Source | Example | Length |
|---|---|---|
| Database | `78577aff-b013-df04-7378-94976315aad2` | 36 (hyphenated UUID) |
| Spec NDJSON | `d09c8c32765b96d17f130a9c5dbf7b4a` | **32 (unhyphenated hex)** |

All five specs use the 32-char form. A join returns **zero rows, no error** —
which reads as "this feature has no funnel impact". Sampled spec `user_id`s also
matched **0** of the 1,000,000 loaded users.

This is the biggest risk for the **unseen 6th spec**: confident, well-formatted,
entirely empty analysis.

**✅ Fix — normalize on ingest, then assert overlap:**

```sql
-- normalize: raw_id -> concat(substring(raw_id,1,8),'-',substring(raw_id,9,4),'-',substring(raw_id,13,4),
--       '-',substring(raw_id,17,4),'-',substring(raw_id,21,12)) AS application_id

-- verify: MANDATORY overlap check before declaring the table ready
SELECT round(100.0 * uniqExactIf(application_id, application_id IN (
         SELECT application_id FROM clickathon.application_started))
       / uniqExact(application_id), 2) AS overlap_pct
FROM clickathon.<new_table>
```

| `overlap_pct` | Action |
|---|---|
| > 90% | proceed |
| 1–90% | proceed, **state coverage** in every insight |
| **0%** | **stop.** Report as a finding. Analyse the table standalone only. |

### D2 verdicts by spec

| Spec | Tables checked | `overlap_pct` | Verdict | Date |
|---|---|---:|---|---|
| **01 — Express Checkout** | `express_checkout_shown`, `express_checkout_selected`, `saved_method_used`, `otp_entered`, `express_payment_confirmed` | **0.0%** (all 5) | **STOP** — analyse standalone | 2026-08-01 |
| **02 — Group / Family** | `group_started`, `traveller_added`, `traveller_removed`, `group_submitted` | **0.0%** (all 4) | **STOP** — analyse standalone | 2026-08-02 |

Source: `out/01_express_checkout/load_report.md`. The normalize step ran
(dashes inserted, 32→36 chars) and the verify query ran against
`application_started` for all 5 tables — **none matched**. This confirms D2
is not merely a formatting mismatch for this spec: even correctly-normalized
`application_id`s from Express Checkout do not overlap the loaded
`application_started` population. Do not join any of these 5 tables to the
main funnel via `application_id` until re-tested with a fresh sample. See
[relationship.md](relationship.md) and each table's page under
[tables/](tables/index.md) for the same finding.

**2026-08-02 — independently re-confirmed by 4 of the Analysis Agent's
questions** (`out/01_express_checkout/analysis/q01.md`–`q04.md`), each of
which stayed within Express Checkout's own tables (joined on `user_id`
instead, safe per D6) rather than attempting the broken `application_id`
join. No question found a working path around the 0% overlap.

**2026-08-02 — spec 02 (Group / Family) confirms the same pattern a third
time.** Source: `out/02_group_family/load_report.md`. The normalize step ran
on all 4 tables and the verify query ran against `application_started` —
**none matched** (`overlap_pct = 0.0%` on all 4). Do not join
`group_started`/`traveller_added`/`traveller_removed`/`group_submitted` to
the main funnel via `application_id`. See [relationship.md](relationship.md)
→ "Group" and [tables/group_started.md](tables/group_started.md) and its 3
sibling pages.

**2026-08-02 — independently re-confirmed by all 4 of the Analysis Agent's
questions for spec 02** (`out/02_group_family/analysis/q01.md`–`q04.md`),
each of which stayed within the Group/Family flow's own 4 tables (joined on
`group_id` instead, spec-local key, safe) rather than attempting the broken
`application_id` join. No question found a working path back to
`application_started` or the main funnel — every finding in q01–q04 is
scoped to the group flow standalone, as D2 requires.

## D3 — Capture-quality flag contradicts itself ⛔ CRITICAL

`is_crossed_failed_attempt_threshold` is described as a capture-quality proxy. It
does not track `retry_count` (and `failed_attempt_threshold` is constant `3`):

| `retry_count` | not crossed | crossed |
|---:|---:|---:|
| 0 | 12,686 | **1,642** ← crossed with *zero* retries |
| 1 | 3,299 | 421 |
| 2 | 1,453 | 157 |
| 3 | **709** ← at threshold, *not* flagged | 79 |

**71.4% of all flagged events had zero retries.** So
`passport_capture_pass_rate` (88.76%) computes cleanly and **cannot be trusted**.

**✅ Fix — report both signals; divergence is itself the finding:**

```sql
SELECT
  round(100.0*countIf(is_crossed_failed_attempt_threshold = 0)/count(),2) AS pass_rate_flag,
  round(100.0*countIf(retry_count < failed_attempt_threshold)/count(),2)  AS pass_rate_retry_derived
FROM clickathon.document_uploaded
```

## D4 — "Sessions" are not sessions

`app_session_id` is unique per row: `destination_card_clicked` has 1,000,000 rows
= 1,000,000 distinct `app_session_id` = 1,000,000 distinct `user_id`, zero nulls.

So `base_context.md`'s headline metric (*purchases ÷ sessions*) is really
purchases ÷ card-clicks = **0.71%**.

**✅ Fix:** use `funnel_conversion` (÷ applications = **4.57%**) as the default,
and report 0.71% honestly as *"purchases per destination-card-click"*.

## D5 — "Conversion" is defined twice, 6.4× apart

`base_context.md` §4 gives two definitions, both called "conversion":

| Definition | Value |
|---|---:|
| ÷ sessions | **0.71%** |
| ÷ applications started | **4.57%** |

**✅ Fix:** retire the bare word. Default to `funnel_conversion` (4.57%) and
**always name the denominator** in reported figures.

## D6 — No repeat users

Every user has exactly 1 event; every applicant exactly 1 application. No
exceptions across 1,000,000 rows.

**✅ Fix:** retention / repeat-purchase / LTV / win-back questions must be
**refused with an explanation**, not answered with zeros:

> "This dataset contains exactly one event per user (1,000,000 users, 1,000,000
> card clicks), so repeat-visit behaviour cannot be measured."

## D7 — Revenue is unaggregatable across 9 currencies

INR averages 5,035 (3,791 purchases); SGD averages 33 (86 purchases). **No FX
rate column exists anywhere.** `sum(value)` returns ~19.6M of an undefined unit.

**✅ Fix:** never aggregate `value` without `GROUP BY currency`. For one headline
figure, report **INR only** (53.7% of purchases) and state the scope.

Also: `value` is not the whole order — `insurance_amount` (22.06% attach, avg
1,349.69) and `discount_amount` (~500 on 17.96% of orders) exist separately.
Whether `value` is pre- or post-discount is **undetermined — verify before
reporting AOV.**

## D8 — The sort key defeats the primary index

All 8 tables use `ORDER BY (id, timestamp, user_id)` where `id` is a **random
UUID**. No query filters by `id`, so only the monthly partition prunes — every
query scans full granules.

**✅ Fix:** the 8 given tables are left as-is (they are the baseline), but **new
tables must not inherit this.** Lead with real filter columns:

```sql
ENGINE = MergeTree
PARTITION BY toYYYYMM(timestamp)
ORDER BY (toDate(timestamp), destination, user_id, id)
```
Plus `LowCardinality(String)` for all categoricals (27 destinations, 10 geos,
4 device types, 9 currencies — all tiny).

## D9 — Vocabulary and casing collisions

| Collision | Detail |
|---|---|
| `visa_type` vs `purpose` | `tourist` vs **`tourism`** for the same concept. Other 3 values match. |
| `destination` vs `citizenship` | UPPER vs lower case country codes |
| `device_type` | mixes both: `Desktop` vs `ios` |

**✅ Fix:** `multiIf(v IN ('tourist','tourism'), 'tourism', v)`; normalize case
before any cross-column comparison.

### Also undocumented, but real

`scan_mode`, `failed_attempt_threshold`, `page_version`, `is_guest_browse`,
`coupon_name`, `discount_amount`, `insurance_added`, `plan_selected`,
`duplicate_id` (**2.99%** of rows), `is_back_filled` (**1.98%**). The add-on
economy on `purchase_completed` is the most analytically significant of these.

Scale claims also fail: **27 destinations, not "120+"**; 154,413 applications in
6 months (~309K/yr), not "700K+". Both are true of Atlys the company, false of
this dataset.

---

# Part B — Known issues (K1–K7)

**Do not cite a known issue as an explanation without checking its verdict.**
Five of seven are refuted — attributing a movement to them would be attributing
it to something the data says isn't happening.

| ID | Claim | Verdict |
|---|---|---|
| **K2** | Android capture failures since Apr 2026 | ✅ **verified — understated** |
| K1 | iOS WebKit OTP regression | ❌ refuted on main funnel; ⚠️ **new, narrower OTP-step regression confirmed** (Express Checkout, iOS-only) — 2026-08-02 |
| K3 | MRZ OCR weaker on non-Latin passports | ❌ refuted (by proxy) |
| K4 | Schengen summer slot scarcity | ❌ refuted as Schengen-specific |
| K6 | SUMMER20 Q2 campaign | ❌ refuted |
| K7 | App 7.45 rollout | ❌ refuted |
| K5 | WhatsApp nudge (Feb 2026) | ⚠️ **unverifiable** — not instrumented |

## K2 — Passport scan model update ✅ VERIFIED, and understated

> *"Some Android devices report more capture failures since [early April]; being monitored."*

| Month | Android fail % | iOS fail % |
|---|---:|---:|
| 2026-01 | 5.96% | 8.21% |
| 2026-02 | 9.68% | 9.08% |
| 2026-03 | 8.46% | 8.28% |
| 2026-04 | **11.69%** | 8.33% |
| 2026-05 | **23.43%** | 8.09% |
| 2026-06 | **33.54%** | 10.16% |

Android failure rose **5.6×**, inflecting exactly at April. iOS flat throughout.
By June, **one in three Android captures fails**, still accelerating.

"Some devices… being monitored" describes a watch item; this is a severe
regression. **Highest-priority product finding in the dataset — surface it
unprompted** in any document-upload or funnel analysis covering April onward.

*Caveat:* measured via the flag from [D3](#d3--capture-quality-flag-contradicts-itself--critical),
so the **trend is robust** (monotonic, Android-only, correctly timed) but the
**absolute rate** inherits that doubt. Note `retry_count` stays flat at ~0.46
throughout — itself corroborating D3.

## K1 — iOS WebKit OTP regression ❌ REFUTED on main funnel; ⚠️ narrower OTP-step regression confirmed 2026-08-02 (see update below)

> *"…users abandon at the pay step. Payment-heavy geos (Gulf card users) are most exposed."*

`pay_now_clicked → purchase_completed`, by OS:

| OS | Pay clicks | Rate |
|---|---:|---:|
| Linux | 108 | 51.85% |
| **iOS** | **6,401** | **49.88%** |
| Windows | 2,562 | 47.19% |
| Android | 3,594 | 46.77% |
| **Mac OS X** | 1,300 | **43.77%** |

iOS is the **best** high-volume platform. And in the Gulf, where exposure was
said to be worst:

| Geo | iOS | Android |
|---|---:|---:|
| **AE** | **70.78%** (n=900) | 43.55% (n=512) |
| SA | 53.80% | 47.66% |
| OM | 55.56% | 50.00% |
| QA | 42.74% | 51.76% |

In the UAE iOS beats Android by **27 points**. The prediction is inverted,
most strongly where it was said to be worst.

**Do not attribute any iOS payment drop to K1.** Spec 01 adds `otp_attempts` /
`otp_success` — the first columns able to test the mechanism directly.

Note the real unexplained leak: **52% of all payment intents never convert**, and
no known issue accounts for it.

**2026-08-01 update — spec 01 (Express Checkout) is now instrumented and
loaded** (`otp_entered`: 1,007 rows, 937 `otp_success=true` / 70 `false`;
`express_payment_confirmed`: 836 rows — see
[otp_entered.md](tables/otp_entered.md)). The columns needed for a direct K1
re-test now exist. **The re-test itself has not been run** — the Context
Agent has no live DB access, and `out/01_express_checkout/load_report.md`
only ran the D2 overlap check for this spec, not a K1 query. Cutting
`otp_success` / confirmation rate by `os` on `otp_entered` is the next
analysis to run, and does not require the `application_id` join (D2 is broken
for this spec — see above), only `otp_entered`'s own `os` column. Update this
entry with a dated verdict once that query runs.

**2026-08-02 update — re-test run, ✅ new dated verdict (source:
`out/01_express_checkout/analysis/q02.md`).** Cutting `otp_entered.otp_success`
by `device_type`/`os` on the Express Checkout sample (1,007 rows,
2026-06-08→2026-06-28):

| device_type | n | otp_success rate | confirmed | confirmation rate |
|---|---:|---:|---:|---:|
| **ios** | 428 | **83.64%** | 316 | 73.83% |
| android | 338 | 100% | 303 | 89.64% |
| web-user-b2c | 185 | 100% | 170 | 91.89% |
| Desktop | 56 | 100% | 47 | 83.93% |

**Every one of the 70 OTP failures in this sample occurred on `device_type =
'ios'` / `os = 'iOS'`** — all three other platforms show 100% `otp_success`.
By `geoip_country_code` the pattern is volume-weighted by where iOS traffic
sits, not a distinct geo effect (no country shows the near-total concentration
device/OS does) — device/OS is the driver. Conditional on `otp_success =
true`, iOS's confirmation rate recovers to 88.27%, in line with Android
(89.64%) — the gap lives almost entirely **at the OTP step itself**, not in a
separate downstream iOS payment-confirmation problem.

**This does not overturn K1's original refutation** — on the *main* funnel's
`pay_now_clicked → purchase_completed` step (different table, different
population, no OTP-specific columns), iOS still converts best (49.88% vs
Android 46.77%, +27pp over Android in the UAE). Both verdicts stand side by
side, per this wiki's never-delete-a-refuted-claim rule: the broad "users
abandon at the pay step, Gulf-exposed" claim is refuted; a narrow, real,
iOS-only OTP-step regression is newly confirmed in Express Checkout. Caveats:
small standalone sample (1,007 rows, 3-week window); per D2 this cannot be
joined to the main funnel, so this finding is scoped to Express Checkout only,
not generalized platform-wide. See [otp_entered.md](tables/otp_entered.md) and
[express_payment_confirmed.md](tables/express_payment_confirmed.md).

## K3 — MRZ OCR on non-Latin passports ❌ REFUTED (by proxy)

No script/MRZ column exists; `citizenship` used as proxy.

| Citizenship | Uploads | Avg retries |
|---|---:|---:|
| ph | 98 | **0.541** |
| de | 108 | **0.528** |
| us | 175 | 0.491 |
| **bd** | 179 | 0.480 |
| **np** | 99 | 0.455 |
| **pk** | 745 | 0.454 |
| in | 14,417 | 0.452 |

The two **highest** retry rates are Philippines and Germany — both Latin script.
The non-Latin proxies sit mid-to-low; Bangladesh has the lowest failure rate
(7.82%).

*Confidence medium:* citizenship is imperfect for MRZ script, and n is small
(99–745). This shows **no measurable effect at this granularity**, not proven
absence. Proper testing needs MRZ-script / OCR-confidence instrumentation.

## K4 — Schengen summer scarcity ❌ REFUTED as Schengen-specific

Application → purchase, Schengen (`FR ES IT GR CH`) vs rest:

| Month | Schengen | Other |
|---|---:|---:|
| 2026-01 | 5.15% | 4.91% |
| 2026-02 | 4.02% | 4.79% |
| 2026-03 | 5.27% | 4.53% |
| 2026-04 | 4.87% | 4.92% |
| 2026-05 | **4.53%** | 4.48% |
| 2026-06 | **4.21%** | 3.93% |

In the claimed Apr–Jun window Schengen tracks the rest within ±0.3pp, and in
May/June is **better**.

What *is* real: a **portfolio-wide conversion decline across H1** (4.91% → 3.93%,
a 20% relative drop), unexplained. K4 was being used to explain it away — a
label that suppresses investigation of a genuine problem.

## K6 — SUMMER20 Q2 campaign ❌ REFUTED

| Month | SUMMER20 | ATLYS15 | FIRST10 | WELCOME |
|---|---:|---:|---:|---:|
| 2026-01 | 59 | 42 | 50 | 51 |
| 2026-02 | 54 | 40 | 41 | 48 |
| 2026-03 | **64** | 50 | 52 | 54 |
| 2026-04 | 58 | 71 | 45 | 42 |
| 2026-05 | 61 | 56 | 67 | 65 |
| 2026-06 | **37** | 65 | 42 | 53 |

All three assertions fail: it runs **all 6 months** (peak in March, trough in
June — inside the claimed window); volume is indistinguishable from three other
coupons; average discount (~₹500) and `value` match the others.

**SUMMER20 is an always-on code, not a seasonal campaign.** Total coupon usage:
1,267 / 7,054 = 17.96%.

## K7 — App 7.45 rollout ❌ REFUTED

| Month | 7.42.0 | 7.43.1 | 7.44.0 | **7.45.2** | 7.46.0 |
|---|---:|---:|---:|---:|---:|
| 2026-01 | 27,851 | 27,987 | 28,086 | **27,991** | 27,633 |
| 2026-03 | 32,964 | 32,628 | 33,049 | **32,637** | 32,718 |
| 2026-06 | 39,373 | 39,223 | 39,824 | **39,578** | 39,354 |

All five versions sit at **~20% share in every month**, including January. A real
rollout produces an S-curve; nothing resembling one exists. 7.46.0 — *newer* than
7.45.2 — is equally present in January.

**`app_version` is assigned uniformly at random and carries no temporal signal.**
Usable as a synthetic A/B segment; **never** as a release timeline. Check
`page_version` (`v3`/`v4`) for the same defect before making any page-version claim.

## K5 — WhatsApp nudge ⚠️ UNVERIFIABLE

Two independent blockers: **no channel/campaign column exists** anywhere in the
30-column envelope, and **no returning users exist** ([D6](#d6--no-repeat-users)),
so "returns to the funnel for previously-dropped users" describes behaviour that
is structurally absent.

**Unverifiable ≠ refuted.** This is missing instrumentation, not evidence of no
effect. Report as "not instrumented", never as "no effect".

Spec 04 (Abandoned Checkout Recovery) introduces both `channel` and a genuine
return event (`resumed_at_step`) — **once instrumented, re-testing K5 is the
first analysis to run.** Update this entry then.
