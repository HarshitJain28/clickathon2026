---
id: metric.recipient_conversion_k_factor
kind: metric
status: verified
confidence: medium
source: out/03_status_sharing/analysis/q03.md — verified share_id join (recipient_cta_clicked ⊆ link_opened) and recipient_is_new_user segmentation
last_verified: 2026-08-02
links: [table.link_opened, table.recipient_cta_clicked, known_issue.d1_windowfunnel_loses_conversions, known_issue.d3_capture_quality_flag_contradicts_itself, metrics.index]
---

# Recipient → new-application K-factor

**Definition:** of recipients who open a shared visa-status link
(`link_opened`), what fraction go on to click the "start your own
application" CTA (`recipient_cta_clicked`)? Measured at the `share_id`
grain (not per-open), since `recipient_cta_clicked` is a share-level event
and `link_opened` fans out (2,310 opens over only 922 distinct `share_id`s
— links get reopened). The underlying join,
`recipient_cta_clicked.share_id ⊆ link_opened.share_id`, is **100%
verified** by set membership (per
[D1](../known_issues.md#d1--windowfunnel-loses-52-of-conversions--critical),
never `windowFunnel`).

## ⚠ Must be read through the `recipient_is_new_user` data-quality finding

`recipient_is_new_user` (on `link_opened`) is **not stable per `share_id`**:
when a link is reopened, different opens of the same share sometimes carry
`true` and sometimes `false`. **472 of 922 shares (51.2%) show both values**
— the same shape of self-contradiction as
[D3](../known_issues.md#d3--capture-quality-flag-contradicts-itself--critical)'s
`is_crossed_failed_attempt_threshold`. Segmenting to shares where the flag
is internally consistent across every open ("pure") isolates the real
signal:

| Segment | Distinct shares | Converted to CTA click | Conversion |
|---|---:|---:|---:|
| **Pure new-user** (`true` on every open) | 299 | 114 | **38.13%** |
| **Pure existing-user** (`false` on every open) | 151 | **0** | **0.00%** |
| Mixed / conflicting flag | 472 | 149 | 31.57% |

**Headline:** the K-factor is real and large for genuinely new-user
recipients (**~34–38%**), and effectively **zero** for recipients the
platform already recognizes as existing users. Not one of the 151
unambiguous existing-user shares converted — consistent with the CTA
("start your own application") being irrelevant to them.

The looser "ever flagged new-user at least once" cut (771 shares, including
the 472 mixed ones) gives 34.11% (263/771) vs. 23.92% (149/623) for
"any-existing-user" — report the **pure split above**, not this looser cut,
since mixed shares mechanically pull both rates toward each other.

**Always report the 51.2% flag-conflict rate alongside any single K-factor
number from this pair of tables** — a bare "38%" or "34%" without that
caveat overstates confidence in `recipient_is_new_user`.

**Scope:** Status Sharing spec 03 sample, 2026-06-08 06:00 → 2026-07-01
09:21, 922 distinct opened shares / 263 distinct shares with a CTA click.
Standalone flow — does not join `application_started` (0% `application_id`
overlap, D2, on the 3 sharer-side tables; the two recipient-side tables
carry no `application_id` at all).
