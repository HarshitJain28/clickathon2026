---
id: metric.conversion_rate
kind: metric
status: refuted
confidence: high
source: base_context.md §4; denominator invalidated by clickathon DB app_session_id profiling
last_verified: 2026-08-01
links: [metric.funnel_conversion, contradiction.c4_session_not_a_session, contradiction.c11_conversion_dual_definition]
---

# Conversion rate (÷ sessions) — **definition invalid as written**

## What `base_context.md` says

> "**Conversion rate** = completed purchases ÷ **sessions**. A session is a single
> app-open / web visit. **This is the headline number reported to leadership.**"

## Why it is invalid

`app_session_id` is **not a session**. In `destination_card_clicked` there are
1,000,000 rows, 1,000,000 distinct `app_session_id`, and 1,000,000 distinct
`user_id` — all identical, zero nulls. It is a per-row identifier, so no session
can contain more than one event.
See [known_issues.md](../known_issues.md).

Evaluated literally: 7,054 ÷ 1,000,000 = **0.71%**, which is arithmetically just
purchases ÷ destination-card-clicks.

## Resolution

Report this figure — it is a legitimate top-of-funnel rate — but **under an
honest name**:

> **Purchases per destination-card-click: 0.71%**

Never label it "per session" and never call it *the* conversion rate. For the
default conversion metric use
[`funnel_conversion`](funnel_conversion.md) (4.57%).

If a true session metric is ever required, it needs sessionization
instrumentation that does not exist in this dataset.
