---
id: table.document_uploaded
kind: table
status: verified
confidence: high
source: clickathon DB — system.tables, system.columns, profiling queries
last_verified: 2026-08-01
links: [doc.envelope, entity.document, metric.passport_capture_pass_rate, contradiction.c10_capture_threshold_flag_broken, known_issue.k2_passport_scan_model_update]
---

# `document_uploaded`

Funnel stage 3. Passport image submitted.

| | |
|---|---:|
| Rows | **20,446** |
| Distinct users | 20,446 |
| Time range | 2026-01-01 00:59:01 → 2026-07-01 03:01:34 |
| Step-through from stage 2 | **13.24%** ← worst leak in the funnel |

Envelope: see [the envelope](index.md). Event-specific columns below.

| Column | Type | Values |
|---|---|---|
| `doc_type` | `Nullable(String)` | **`passport_front` only** — single-valued, useless as a cut |
| `capture_mode` | `Nullable(String)` | `camera` · `gallery` · `qr` |
| `scan_mode` | `Nullable(String)` | `auto` · `manual` — **undocumented in base_context** |
| `retry_count` | `Nullable(UInt8)` | 0–3 |
| `failed_attempt_threshold` | `Nullable(UInt8)` | **constant 3** — **undocumented in base_context** |
| `is_crossed_failed_attempt_threshold` | `Nullable(UInt8)` | 2,299 crossed / 18,147 not |

## ⚠ Two warnings before using this table

1. **The quality flag is internally inconsistent.** 71.4% of "crossed" events
   have `retry_count = 0`, and 709 events at `retry_count = 3` are not flagged.
   See [known_issues.md](../known_issues.md).
2. **A severe Android regression lives here.** Capture failure on Android went
   5.96% (Jan) → 33.54% (Jun), inflecting in April.
   See [K2](../known_issues.md) — the single most
   actionable finding in the dataset.
