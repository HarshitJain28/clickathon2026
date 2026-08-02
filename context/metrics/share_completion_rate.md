---
id: metric.share_completion_rate
kind: metric
status: verified
confidence: high
source: out/03_status_sharing/analysis/q01.md — verified set-membership step-through by status_shared; out/03_status_sharing/load_report.md — share_clicked/channel_selected/link_generated row counts
last_verified: 2026-08-02
links: [table.share_clicked, table.channel_selected, table.link_generated, known_issue.d1_windowfunnel_loses_conversions, known_issue.d2_application_id_join_format, metrics.index]
---

# Share-flow completion rate, by `status_shared`

**Definition:** `uniqExact(channel_selected.share_id) / uniqExact(share_clicked.share_id)`,
computed by **set membership** (`channel_selected.share_id ⊆
share_clicked.share_id` — valid per
[D1](../known_issues.md#d1--windowfunnel-loses-52-of-conversions--critical),
never `windowFunnel`), segmented by `status_shared` as recorded on
`share_clicked`. `link_generated` tracks `channel_selected` exactly (same
1,144 `share_id`s in every bucket — see
[channel_selected.md](../tables/channel_selected.md)), so either table gives
the same numerator.

| `status_shared` | Shares (`share_clicked`) | Completed (`channel_selected`) | Completion rate |
|---|---:|---:|---:|
| submitted | 562 | 394 | 70.11% |
| approved | 513 | 365 | 71.15% |
| processing | 525 | 385 | 73.33% |
| **Overall** | **1,600** | **1,144** | **71.5%** |

**No monotonic pattern by status** — the 3.2pp band (70.1%–73.3%) is within
what 513–562-row samples produce by chance, and `processing` (not
`approved`) is highest. **Approvals do not get shared/completed more than
other statuses.**

**Not the same thing as a "share rate."** A true share rate (shares ÷
applications at each status) needs an independent count of
applications-per-status, which does not exist in this dataset — `status_shared`
is only recorded on this spec's own 3 sharer-side tables, and per
[D2](../known_issues.md#d2--spec-application_id-wont-join--critical) this
spec's `application_id` has 0% overlap with `application_started`. This
metric is scoped to the share flow's own funnel, not applications overall.

**Scope:** Status Sharing spec 03 sample only, 2026-06-08 06:00 →
2026-07-01 09:21 — treat as directional, not a full-population estimate.
Standalone per D2; not comparable to `funnel_conversion`.
