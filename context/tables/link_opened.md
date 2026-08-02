---
id: table.link_opened
kind: table
status: verified
confidence: high
source: out/03_status_sharing/ddl.sql + justification.md (schema); out/03_status_sharing/load_report.md — rows loaded; out/03_status_sharing/analysis/q02.md — channel mix and new-user open rate; out/03_status_sharing/analysis/q03.md — verified share_id join to recipient_cta_clicked, recipient_is_new_user data-quality finding; out/03_status_sharing/analysis/q04.md — destination spread
last_verified: 2026-08-02
links: [doc.envelope, doc.relationship, known_issue.d1_windowfunnel_loses_conversions, known_issue.d3_capture_quality_flag_contradicts_itself, tables.index, table.link_generated, table.recipient_cta_clicked, metric.recipient_conversion_k_factor]
---

# `link_opened`

Spec 03 (Visa Status Sharing). Fires when a **recipient** (not the sharer)
opens the share link. Different actor, different grain, **no `user_id` at
all** — cannot be an attribute of any sharer-side table. → `CREATE TABLE`.
See `out/03_status_sharing/justification.md` "CREATE vs ALTER call".

| | |
|---|---:|
| Rows | **2,310** (verified — `load_report.md`) |
| Distinct `share_id` | 922 (39.9% unique — recipients can reopen the same link; fan-out expected on this table, same shape as `traveller_added`/`traveller_removed`, spec 02) |
| Users | **N/A — no `user_id` column exists on this table** (recipient-side, per `spec.md`: "recipient events are keyed by `share_id`", confirmed by `profile.md` showing no envelope columns) |
| Sample time span | 2026-06-08 06:00 → 2026-07-01 09:21 (profile.md file-level span; not separately profiled per event) |
| Step-through ← `link_generated` | **not comparable by row count** — 2,310 opens vs. 1,144 links generated reflects the same-link-reopened fan-out, not a conversion rate; a real step-through needs a set-membership check on `share_id` against the sharer-side tables — **still not run** by any `analysis/qNN.md` file (see D1 note below; this table's own downstream join to `recipient_cta_clicked` *has* been verified — see below) |

This table carries **no envelope columns** — `spec.md` states recipient
events "are keyed by `share_id`", and `profile.md` confirms only 4 columns
exist on this event, none of them envelope fields.

| Column | Type | Values |
|---|---|---|
| `share_id` | `FixedString(32)` | 100% present, 0% null, 39.9% unique (fan-out) — see [share_clicked.md](share_clicked.md) for the type reasoning; **not yet set-membership checked** against the sharer-side tables' `share_id` |
| `channel` | `LowCardinality(String)` | 4 values: `whatsapp`(1273) / `copy_link`(423) / `email`(396) / `sms`(218) |
| `destination` | `FixedString(2)` | 14 values observed in this sample, ISO-2 uppercase — see the destination type note below |
| `recipient_is_new_user` | `Bool` | 100% present, 0% null; `true`(1390) / `false`(920) — a genuine K-factor / viral-acquisition signal: is the recipient new to the platform? |

## `destination` is `FixedString(2)` here — a deliberate divergence from specs 01/02

Every sampled value across all 5 of this spec's tables is a 2-char ISO-2
code, and `relationship.md`'s full 27-value enumeration has no ragged
exception for `destination` (unlike `geoip_country_code`, which keeps an
`OTHER` catch-all). Per the `FixedString` carve-out for strictly
fixed-length data, `FixedString(2)` was chosen instead of the blanket
`LowCardinality(String)` specs 01/02 used for this column. Not used as a
join key, so the join-key type-match constraint doesn't apply. See
`justification.md` "Per-column string-type reasoning".

## Channel mix and new-user opens — verified 2026-08-02 (`analysis/q02.md`)

WhatsApp leads both on volume and on new-user efficiency:

| Channel | Total opens | New-user opens | New-user rate |
|---|---:|---:|---:|
| **whatsapp** | 1,273 | **783** | **61.51%** |
| copy_link | 423 | 254 | 60.05% |
| email | 396 | 233 | 58.84% |
| sms | 218 | 120 | 55.05% |

WhatsApp drives 56.3% of all new-user opens (783/1,390) and has the highest
per-open new-user rate of the four channels — not winning on volume alone.
Ranking matches the sharer-side `channel_selected` mix (see
[channel_selected.md](channel_selected.md)). Caveat: "opens" counts every
open event (2,310 opens over only 922 distinct `share_id`s — reopening is
included), not distinct recipients; a distinct-shares cut would read a bit
lower but is very unlikely to flip the channel ranking given WhatsApp's
lead.

## Destination spread (raw reach) — verified 2026-08-02 (`analysis/q04.md`)

By opens, **AU** leads (223 of 2,310, 14 destinations observed), across 86
distinct shares opened and 135 new-user opens — both also the highest of
any destination. VN (187 opens) and TH (175 opens) follow. See
[recipient_cta_clicked.md](recipient_cta_clicked.md) for the *efficiency*
cut (opens → CTA click rate), where AE, not AU, leads.

## `recipient_is_new_user` is not stable per `share_id` — data-quality finding, 2026-08-02

Per `analysis/q03.md`: when a link is reopened, different opens of the
*same* `share_id` sometimes carry `recipient_is_new_user = true` and
sometimes `false`. **472 of 922 distinct shares (51.2%) show both values
across their opens** — the same shape of self-contradiction as the known
`is_crossed_failed_attempt_threshold` flag ([D3](../known_issues.md#d3--capture-quality-flag-contradicts-itself--critical)).
Any K-factor or new-user-conversion metric built on this flag should
segment shares into "pure" (consistent across every open) vs. "mixed"
rather than trusting a single per-open value — see
[recipient_cta_clicked.md](recipient_cta_clicked.md) and
[metrics/recipient_conversion_k_factor.md](../metrics/recipient_conversion_k_factor.md)
for the resulting segmented rates.

## ⚠ Fan-out breaks the "one row per user" pattern most tables share

There is no `user_id` to even check, but 2,310 rows against only 922
distinct `share_id` (39.9% unique) means a meaningful share of links are
opened multiple times — analogous to `traveller_added`/`traveller_removed`
(spec 02, see [known_issues.md](../known_issues.md) → D6), except D6 itself
only constrains `user_id` uniqueness, which doesn't apply here. Any
per-share metric (e.g. "recipient conversion") must decide explicitly
whether to count opens or distinct shares opened.

## Physical layout deviates from the 8 baseline tables — intentionally

`ENGINE = MergeTree`, `ORDER BY (toDate(timestamp), channel, share_id, id)`
— does not lead with the random `id` UUID, per known_issues.md D8.
`user_id` doesn't exist on this table, so `share_id` (the only entity key
present) takes the slot ahead of the trailing `id`. See `justification.md`
"ORDER BY / PARTITION BY reasoning".

## Other risks carried forward (see `justification.md` for full reasoning)

- **D1** — the join **onward** to `recipient_cta_clicked` is now
  **verified**: `recipient_cta_clicked.share_id ⊆ link_opened.share_id` is
  100% (all 263 distinct `share_id`s behind a CTA click are present among
  this table's 922 distinct `share_id`s) — `analysis/q03.md`, 2026-08-02.
  The join **upstream** to the sharer-side tables (`link_generated` etc.)
  remains **unverified** — still open work for the next Analysis Agent pass.
- **D3-shaped finding** — `recipient_is_new_user` self-contradicts across
  reopens of the same share (51.2% of shares) — see above.
- No `application_id`/D2 risk applies — this table carries neither column.
