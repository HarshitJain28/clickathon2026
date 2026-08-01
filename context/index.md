---
id: doc.index
kind: index
status: verified
confidence: high
source: clickathon@78f5870d (ClickHouse Cloud), verified against base_context.md
last_verified: 2026-08-01
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
| Tables | 8 raw event tables, **no views or materialized views** |
| Total rows | 2,480,481 |
| Data window | 2025-12-31 23:41 → 2026-07-01 03:01 (H1 2026) |
| Engine | `SharedMergeTree` on all 8 |
| Partitioning | `PARTITION BY toYYYYMM(timestamp)` on all 8 |
| Sort key | `ORDER BY (id, timestamp, user_id)` on all 8 ⚠ see D8 |

## Contents

| File | What's in it |
|---|---|
| [SCHEMA.md](SCHEMA.md) | **The rules** — taxonomy, frontmatter, update workflow, lint |
| [business.md](business.md) | Business model, funnel, verified scale and trend |
| [relationship.md](relationship.md) | Entities, join map, key formats, join integrity |
| [known_issues.md](known_issues.md) | **Data traps (D1–D9) + known-issue verdicts (K1–K7)** |
| [tables/](tables/index.md) | 8 table pages + the shared 30-column envelope |
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
