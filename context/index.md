---
id: doc.index
kind: index
status: verified
confidence: high
source: clickathon@78f5870d (ClickHouse Cloud), verified against base_context.md; out/01_express_checkout/load_report.md — rows loaded for the 5 Express Checkout tables; out/02_group_family/load_report.md — rows loaded and D2 overlap_pct for the 4 Group/Family tables; out/02_group_family/analysis/q01.md–q04.md — group completion-rate by size, churn analysis; out/03_status_sharing/load_report.md — rows loaded and D2 overlap_pct for 3 of the 5 Status Sharing tables; out/03_status_sharing/analysis/q01.md–q04.md — share-flow completion rate, channel mix, recipient K-factor, destination spread; out/04_abondon_checkout_recovery_2/load_report.md — rows loaded and D2 overlap_pct for all 6 Abandoned Checkout Recovery tables; out/04_checkout_recovery_3/load_report.md — identical row counts and D2 verdict on independent resubmission of the same 6 tables; out/04_checkout_recovery_3/analysis/q01.md–q04.md — resolves the duplicate-load question (no duplication found), verified recovery rate by drop_step/channel/timing (K5 re-test), recovery-targeting mismatch finding (see known_issues.md → D2, K5, tables/index.md)
last_verified: 2026-08-02
links: [doc.schema, doc.business, doc.relationship, doc.known_issues, doc.log]
---

# Atlys Context Wiki

Living context layer for the Atlys agentic analytics system. Maintained by the
Context Agent; read by the Instrumentation and Analytics Agents.

**Read this file first**, then the `index.md` of the directory you need. Never
scan the whole wiki — the indexes exist so you load only what a task requires.

## Ground rule: the database is the source of truth

Where the handwritten `base_context.md` and the live database disagree, **the
database wins**, and the disagreement is recorded in
[known_issues.md](known_issues.md). `base_context.md` remains authoritative only
for *business intent* — why a metric matters, who reads it — which cannot be
derived from data.

## Verified environment

| Item | Value |
|---|---|
| Service | `78f5870d-894f-4405-bf4f-542014537dcb` (org *Edelweiss*, aws ap-south-1) |
| Database | `clickathon` |
| Tables | 28: 8 baseline raw event tables + 5 from spec 01 (Express Checkout) + 4 from spec 02 (Group / Family) + 5 from spec 03 (Visa Status Sharing) + 6 from spec 04 (Abandoned Checkout Recovery), **no views or materialized views** |
| Total rows | 2,503,863 (2,480,481 baseline + 5,507 Express Checkout + 5,453 Group/Family + 6,503 Status Sharing + 5,919 Abandoned Checkout Recovery, verified via `load_report.md`) — the Abandoned Checkout Recovery figure was independently re-loaded 2026-08-02 under `out/04_checkout_recovery_3` with byte-identical row counts; whether that run also re-inserted the same rows (doubling the true total) was an open question, **now resolved 2026-08-02**: all 4 of `out/04_checkout_recovery_3/analysis/q01.md`–`q04.md` independently ran live counts and found no duplication — see [known_issues.md](known_issues.md) → D2 |
| Data window | 2025-12-31 23:41 → 2026-07-01 03:01 (H1 2026 baseline); Express Checkout sample 2026-06-08 → 2026-06-28; Group/Family sample 2026-06-08 → 2026-06-28; Status Sharing sample 2026-06-08 06:00 → 2026-07-01 09:21; Abandoned Checkout Recovery sample 2026-06-08 06:01 → 2026-07-01 00:00 |
| Engine | `SharedMergeTree` on the 8 baseline tables; `MergeTree` on the 20 spec tables (spec 01 + spec 02 + spec 03 + spec 04) |
| Partitioning | `PARTITION BY toYYYYMM(timestamp)` on all 28 |
| Sort key | `ORDER BY (id, timestamp, user_id)` on the 8 baseline tables ⚠ see D8; the 5 Express Checkout tables use D8's fix `(toDate(timestamp), device_type, user_id, id)`; the 4 Group/Family tables use a further D8-compliant variant `(toDate(timestamp), group_size, group_id, id)`; the 5 Status Sharing tables each substitute their own leading discriminator (`status_shared`/`channel`/`destination`); the 6 Abandoned Checkout Recovery tables substitute `drop_step` (3 tables) or `channel` (3 tables) — see [tables/index.md](tables/index.md) |

## Contents

| File | What's in it |
|---|---|
| [SCHEMA.md](SCHEMA.md) | **The rules** — taxonomy, frontmatter, update workflow, lint |
| [business.md](business.md) | Business model, funnel, verified scale and trend |
| [relationship.md](relationship.md) | Entities, join map, key formats, join integrity |
| [known_issues.md](known_issues.md) | **Data traps (D1–D9) + known-issue verdicts (K1–K7)** |
| [tables/](tables/index.md) | 22 table pages + the shared 30-column envelope |
| [metrics/](metrics/index.md) | 7 metric pages with verified formulas and values |
| [log.md](log.md) | Changelog |

## Frontmatter contract

| Field | Meaning |
|---|---|
| `id` | Stable unique key, e.g. `table.purchase_completed`. Never reused. |
| `kind` | `index` · `schema` · `business` · `relationship` · `known_issues` · `table` · `metric` · `changelog` |
| `status` | `verified` · `refuted` · `unverifiable` · `unverified` |
| `confidence` | `high` · `medium` · `low` |
| `source` | Where the claim came from **and** the evidence backing it |
| `last_verified` | ISO date of last check against live data, or `null` |
| `links` | `id`s of related pages |

## Reading priority

1. **Instrumentation Agent** → [tables/index.md](tables/index.md) (envelope + DDL rules), [known_issues.md](known_issues.md) D2 & D8, [relationship.md](relationship.md) (key formats)
2. **Analytics Agent** → [metrics/index.md](metrics/index.md), [known_issues.md](known_issues.md), [business.md](business.md)
3. **Context Agent** → [SCHEMA.md](SCHEMA.md), [log.md](log.md), every index

> ⛔ **Before writing any query, read [known_issues.md](known_issues.md) D1–D3.**
> Three traps return clean, plausible, **wrong** numbers with no error:
> `windowFunnel` loses 52% of conversions · spec `application_id` joins return
> zero rows · the capture-quality flag contradicts itself.
