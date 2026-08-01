---
id: doc.log
kind: changelog
status: verified
confidence: high
source: git history of this wiki
last_verified: 2026-08-01
links: [doc.index, doc.known_issues]
---

# Context changelog

Append-only, newest first. Every entry names the evidence behind the change.
Git history is the authoritative diff; this is the readable summary.

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
