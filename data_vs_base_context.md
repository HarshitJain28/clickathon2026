# Data vs. `base_context.md` — Stage 0 Bootstrap Findings

**Reference document. Not part of the LLM wiki.**
Records *why* we bootstrap the context layer from data, and *what* we found when
we did.

| | |
|---|---|
| **Run date** | 2026-08-01 |
| **Source of truth** | ClickHouse Cloud service `78f5870d-894f-4405-bf4f-542014537dcb` (org *Edelweiss*), database `clickathon` |
| **Access** | ClickHouse MCP server |
| **Data profiled** | 8 tables, 2,480,481 rows, 2025-12-31 → 2026-07-01 (H1 2026) |
| **Document tested** | `Atlys/base_context.md` |
| **Output** | `context/` LLM wiki |

---

## 1. Why bootstrap from data at all

The problem statement warns us directly:

> *"Fair warning: the base context layer you receive is not perfect. Treat it
> with suspicion."*

And one of the four judging criteria is **context freshness**:

> *"when a new table lands, does your Analytics Agent actually reason with the
> updated context, or is it working from a stale snapshot?"*

If the Instrumentation and Analytics Agents read a wrong context file, **every
downstream output inherits the error** — and inherits it invisibly, because a
confident insight built on a wrong premise looks exactly like a correct one.

So Stage 0 runs **before anything else**: take every factual claim in
`base_context.md`, test it against the live database, and record the verdict with
its evidence.

### The division of authority

| | Authoritative for | Example |
|---|---|---|
| **The database** | What *exists* — schemas, columns, formats, distributions, whether a claimed effect is visible | "27 destinations exist" |
| **`base_context.md`** | *Business intent* — why a metric matters, who consumes it, what a bug means | "conversion is the north-star", "K1 is an OTP autofill bug" |

Data cannot tell you a metric is "the headline number reported to leadership".
So we keep the document's intent and replace its facts.

### Method

For every claim, four steps:

1. **Extract the claim** — e.g. *"iOS users abandon at the pay step"*
2. **Write a query that would prove or disprove it** — `pay_now_clicked → purchase_completed` grouped by `os`
3. **Run it against `clickathon`** via ClickHouse MCP
4. **Record the verdict + the actual numbers** — `verified` / `refuted` / `unverifiable`

Every claim in the resulting wiki carries the number that proves it. A judge can
re-run any of it.

---

## 2. Summary of differences

| Category | Tested | Held up | Wrong / unusable |
|---|---:|---:|---:|
| Known issues (K1–K7) | 7 | **1** | 6 (5 refuted, 1 unverifiable) |
| Metric definitions | 6 | 3 | 3 |
| Entity descriptions | 5 | 2 | 3 |
| Scale / structural claims | 4 | 1 | 3 |
| Recommended query method | 1 | 0 | **1 (critical)** |

**Total: 9 data traps (D1–D9) opened, 5 of 7 known issues refuted.**

---

## 3. The critical differences

> These three fail **silently** — no error, just wrong numbers.

### 3.1 The recommended funnel method loses 52% of conversions

**`base_context.md` §7 says:** *"Prefer `windowFunnel`/`sequenceMatch` over
per-table row dumps."*
**§6 says:** *"funnel order is by `timestamp` ascending within a `user_id` /
`application_id`"*

**The data says:** timestamps are **not monotonic** along the funnel. On the
7,054 applications that completed every stage:

| Ordering check | Holds |
|---|---:|
| `document_uploaded` after `application_started` | 95.5% |
| `purchase_completed` after `application_started` | 97.6% |
| `purchase_completed` after `document_uploaded` | **52.2%** |

Running both methods on the same data:

| Stage | Set membership (correct) | `windowFunnel` | Lost |
|---|---:|---:|---:|
| card clicked | 1,000,000 | 1,000,000 | — |
| app started | 154,413 | 154,413 | — |
| doc uploaded | 20,446 | 19,523 | 4.5% |
| **purchased** | **7,054** | **3,366** | **52.3%** |

**Impact:** following the document literally reports **2.18%** conversion
instead of the true **4.57%** — off by more than 2×. And `windowFunnel` doesn't
error; it returns a plausible number.

**Resolution:** count funnel stages by **set membership**, never by sequence
functions, on these 8 tables. Valid because the funnel is perfectly nested.

### 3.2 Incoming spec events won't join to the database

| Source | Example `application_id` | Format |
|---|---|---|
| `clickathon.application_started` | `78577aff-b013-df04-7378-94976315aad2` | 36-char hyphenated UUID |
| `specs/*/events.ndjson` | `d09c8c32765b96d17f130a9c5dbf7b4a` | **32-char unhyphenated hex** |

All five specs use the 32-char form. Additionally, sampled spec `user_id`s
matched **zero** of the 1,000,000 users in `destination_card_clicked`.

**Impact:** a new feature table joined as-is returns **zero rows without
erroring** — which reads as *"this feature has no funnel impact."* This is the
highest-risk failure mode for the **unseen 6th spec**: confident,
well-formatted, entirely empty analysis.

**Resolution:** normalize `application_id` on ingest, then **assert join overlap
before declaring any new table ready.** If overlap is 0% after normalizing,
report that as a finding and analyse the table standalone.

### 3.3 The capture-quality flag contradicts itself

**`base_context.md` §2 says:** `is_crossed_failed_attempt_threshold` is *"a proxy
for capture quality"*, implying it derives from `retry_count` vs a threshold
(`failed_attempt_threshold`, constant = 3).

**The data says** otherwise — cross-tabulated over all 20,446 uploads:

| `retry_count` | not crossed | crossed |
|---:|---:|---:|
| 0 | 12,686 | **1,642** ← crossed with *zero* retries |
| 1 | 3,299 | 421 |
| 2 | 1,453 | 157 |
| 3 | **709** ← at threshold, *not* flagged | 79 |

**71.4% of all flagged events had zero retries**, and 709 uploads that hit the
stated threshold were not flagged.

**Impact:** `passport_capture_pass_rate` (88.76%) computes cleanly and cannot be
trusted. K2 — the one confirmed issue — is measured with this flag, so its
magnitude inherits the doubt (its trend is independently corroborated).

**Resolution:** always report both the flag and a retry-derived rate; divergence
is itself the finding.

---

## 4. Known issues — 5 of 7 refuted

| ID | Claim in `base_context.md` | What the data shows | Verdict |
|---|---|---|---|
| **K2** | Android capture failures since Apr 2026, "being monitored" | Jan 5.96% → Jun **33.54%**, inflecting exactly at April. iOS flat (8–10%). | ✅ **Verified — badly understated** |
| K1 | iOS WebKit OTP regression; Gulf users most exposed | iOS is the **best** high-volume platform (49.88%). UAE: iOS **70.78%** vs Android **43.55%** | ❌ Refuted (inverted) |
| K3 | Non-Latin MRZ passports need more retries | Highest retries: Philippines 0.541, Germany 0.528 — both Latin. Bangladesh 0.480, Nepal 0.455, Pakistan 0.454. | ❌ Refuted (by proxy) |
| K4 | Schengen summer slot scarcity (Apr–Jun) | Schengen tracks the rest within ±0.3pp; in May/June it is **better** | ❌ Refuted as Schengen-specific |
| K6 | SUMMER20 promo ran in Q2 | Runs all 6 months (59, 54, **64**, 58, 61, **37**). One of 4 coupons at equal volume and discount. | ❌ Refuted |
| K7 | App 7.45.x rolled out mid-quarter | All 5 versions at ~20% share in **every** month, including January. No S-curve. | ❌ Refuted |
| K5 | WhatsApp nudge lifts returns (Feb 2026) | No channel column exists; no repeat users exist | ⚠️ **Unverifiable** (≠ refuted) |

### Why this matters

If the Analytics Agent says *"iOS checkout is down — this is the known K1 OTP
bug"*, it has invented a causal story the data contradicts. Five of the seven
stock explanations available to it are false.

**K4 is the most damaging refuted issue**, because it is a *"this is expected,
not a bug"* label. Applied to what is actually a **portfolio-wide 20% conversion
decline across H1** (4.91% → 3.93%), it suppresses investigation of a real,
unexplained problem.

**K5 is unverifiable, not false.** Absence of evidence here is absence of
instrumentation. Spec 04 (Abandoned Checkout Recovery) introduces both a
`channel` field and a genuine return event — once instrumented, re-testing K5 is
the first analysis to run.

---

## 5. Other differences found

| # | `base_context.md` claim | Measured reality |
|---|---|---|
| D4 | "Conversion rate = purchases ÷ **sessions**" — the headline metric | `app_session_id` is unique per row: 1,000,000 rows = 1,000,000 "sessions" = 1,000,000 users. **Not a session.** The metric is really purchases ÷ card-clicks = 0.71%. |
| D5 | "Conversion" | Defined **twice** in §4, ~200 words apart, with different denominators — **0.71% vs 4.57%, a 6.4× gap**, never reconciled. |
| D6 | "A user may browse many destinations and start **multiple applications**" | Every one of 1,000,000 users has **exactly 1** event; every one of 154,413 applicants has **exactly 1** application. Retention/LTV/repeat analysis is impossible. |
| D7 | "Revenue per conversion = `value`, in the event's `currency`" | 9 currencies, ~150× magnitude spread (INR avg 5,035 vs SGD avg 33), **no FX rate column anywhere**. `sum(value)` returns a meaningless number. |
| D8 | Sort key `ORDER BY (id, …)` noted as "a legacy of the event-table template" | Stated but treated as harmless. `id` is a **random UUID**, so the primary index cannot prune on any real predicate — every query scans full granules. |
| D9 | `visa_type` and `purpose` both documented | Never noted that they encode the same concept with divergent vocabularies: **`tourist` vs `tourism`**. Joining splits the largest segment. |
| — | "`application_started` carries **`visa_issuance_eta_days`** (an integer number of days)" | **No such column.** The real column is `eta_shown`, a `Nullable(String)` with mixed units: `24 hours`, `3-5 days`, `5-7 days`, `7-10 days`. §3 of the same document names it correctly — the document contradicts itself. |
| — | "**120+ destinations**" | **27** |
| — | "**700K+ applications annually**" | 154,413 in 6 months ≈ 309K/yr |
| — | "Each destination belongs to a **region** (GCC, SEA, Schengen…)" | **No region column exists in any table.** Any region cut requires a hand-maintained mapping. |
| — | "events *before* [application_started] carry an empty `application_id`" | 154,413 of 1,000,000 `destination_card_clicked` rows (15.4%) carry one — exactly the converters. |
| — | `on_time_delivery_rate` defined | Correctly self-flagged as not computable — **and** its denominator column doesn't exist either. Doubly uncomputable. |

### Columns the document never mentions

`scan_mode`, `failed_attempt_threshold`, `page_version`, `is_guest_browse`,
`coupon_name`, `discount_amount`, `insurance_added`, `plan_selected`,
`duplicate_id` (2.99% of rows), `is_back_filled` (1.98% of rows).

Most significant: **`purchase_completed` carries a full add-on economy** —
insurance (22.06% attach rate, avg 1,349.69), plan tiers
(`standard`/`express`/`black`), and named coupons — that the context layer is
entirely silent on. This matters for Spec 05 (Instant Forex), which is not a
novel pattern but a *third* add-on alongside two that already exist.

---

## 6. What held up

For balance — the document is not uniformly wrong:

| Claim | Verdict |
|---|---|
| `ORDER BY (id, timestamp, user_id)` on all 8 tables | ✅ confirmed |
| `user_id` is a 28-char string | ✅ confirmed (min = max = 28) |
| `destination` is a 2-char ISO code | ✅ confirmed |
| ~2.5M rows total | ✅ 2,480,481 |
| `destination_card_clicked` = 1,000,000 rows | ✅ exact |
| Funnel stage order (card → app → doc → purchase) | ✅ confirmed as a *set* relationship |
| Join keys (`user_id`, `application_id`) | ✅ confirmed — funnel is perfectly nested, 100% |
| `passport_capture_pass_rate` formula | ✅ computes — but see D3 |
| Mobile-heavy, iOS-first | ✅ directionally confirmed |
| `on_time_delivery_rate` "not computable from the funnel tables here" | ✅ correctly self-flagged |

---

## 7. Verified baseline

The numbers the wiki now carries, which the Analytics Agent reasons from:

**The funnel (set membership, H1 2026):**

| Stage | Distinct users | Step-through |
|---|---:|---:|
| `destination_card_clicked` | 1,000,000 | — |
| `application_started` | 154,413 | 15.44% |
| `document_uploaded` | 20,446 | **13.24%** ← biggest leak |
| `pay_now_clicked` | 14,739 | 72.09% |
| `purchase_completed` | 7,054 | **47.86%** ← second leak |

- **Funnel conversion (default): 4.57%** — purchases ÷ applications started
- Card → purchase: 0.71%
- Mean application → purchase: 110.5 minutes
- Conversion trend H1: 4.91% → 4.79% → 4.53% → 4.92% → 4.48% → **3.93%** (20% relative decline, **unexplained**)

**Undocumented but real:** insurance attach 22.06% · coupon usage 17.96% ·
paid-search share 22.30% · auth-to-application 84.0% (29,377 users authenticate
and never apply)

---

## 8. Conclusion

`base_context.md` is a reasonable description of **Atlys the business** and an
unreliable description of **this dataset**. Its business framing was kept; its
factual claims were replaced with measurements.

The single most valuable output of Stage 0 is not the corrected numbers — it is
the **nine data traps**, because they are permanent guard rails. They describe
properties of the *data*, not of the document, so they stay true on every future
iteration and for the unseen 6th spec. Without them recorded, a fresh agent
re-discovers each trap, or falls into it and reports confident, wrong numbers.

They also serve as **anti-regression locks**: `base_context.md` still exists, and
the unseen spec may well repeat its claims. A recorded, evidenced refutation
stops a future agent "helpfully correcting" the wiki back to the wrong value.

**Full detail with queries and evidence:** `context/known_issues.md`
