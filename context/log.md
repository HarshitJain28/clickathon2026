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
