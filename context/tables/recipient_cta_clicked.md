---
id: table.recipient_cta_clicked
kind: table
status: verified
confidence: high
source: out/03_status_sharing/ddl.sql + justification.md (schema); out/03_status_sharing/load_report.md — rows loaded; out/03_status_sharing/analysis/q03.md — verified share_id join to link_opened, K-factor by recipient_is_new_user; out/03_status_sharing/analysis/q04.md — destination CTA-rate efficiency
last_verified: 2026-08-02
links: [doc.envelope, doc.relationship, known_issue.d1_windowfunnel_loses_conversions, known_issue.d3_capture_quality_flag_contradicts_itself, tables.index, table.link_opened, metric.recipient_conversion_k_factor]
---

# `recipient_cta_clicked`

Spec 03 (Visa Status Sharing). Fires when the recipient taps the CTA — a
later and optional moment than `link_opened` (305 of 2,310 opens, 13.2%,
have a corresponding CTA click). **The K-factor numerator** — measures
recipients who go on to start their own application. → `CREATE TABLE`. See
`out/03_status_sharing/justification.md` "CREATE vs ALTER call".

| | |
|---|---:|
| Rows | **305** (verified — `load_report.md`) |
| Distinct `share_id` | 263 (86.2% unique) |
| Users | **N/A — no `user_id` column exists on this table** (recipient-side) |
| Sample time span | 2026-06-08 06:00 → 2026-07-01 09:21 (profile.md file-level span; not separately profiled per event) |
| Step-through ← `link_opened` | 305 / 2,310 = **13.2%** row-count ratio (opens, not shares); the **verified**, set-membership, share-grain K-factor is **38.13%** (pure new-user) / **0.00%** (pure existing-user) — see below and `analysis/q03.md` |

This table carries **no envelope columns**, matching `link_opened` — see
that page for the recipient-side "no `user_id`" reasoning.

| Column | Type | Values |
|---|---|---|
| `share_id` | `FixedString(32)` | 100% present, 0% null, 86.2% unique (some shares produce >1 CTA click) — see [share_clicked.md](share_clicked.md) for the type reasoning |
| `destination` | `FixedString(2)` | 14 values observed, ISO-2 uppercase — see [link_opened.md](link_opened.md) for the type reasoning |
| `cta` | `LowCardinality(String)` | **single observed value** (`start_own_application`, 305/305) — same shape as `document_uploaded.doc_type` ([relationship.md](../relationship.md): "single-valued and therefore useless as a cut"). Kept as a real column since it is observed, but excluded from the ORDER BY key for lack of discriminating power. |

## The K-factor — computed and verified 2026-08-02 (`analysis/q03.md`)

This table is described in `justification.md` as "the K-factor numerator" —
recipients who convert into their own funnel entry. The join it depends on,
`recipient_cta_clicked.share_id ⊆ link_opened.share_id`, is **100%
verified** by live set membership (all 263 distinct `share_id`s here are
present among `link_opened`'s 922).

Because `recipient_is_new_user` (on `link_opened`) is **not stable per
`share_id`** across reopens (472/922 shares, 51.2%, show conflicting values
— a D3-shaped self-contradiction, see [link_opened.md](link_opened.md)),
the K-factor is best read on the "pure" (internally-consistent) segments:

| Segment | Distinct shares | Converted to CTA click | Conversion |
|---|---:|---:|---:|
| **Pure new-user** (`true` on every open) | 299 | 114 | **38.13%** |
| **Pure existing-user** (`false` on every open) | 151 | **0** | **0.00%** |
| Mixed / conflicting flag | 472 | 149 | 31.57% |

**Headline: ~34–38% of genuinely-new-user opened shares go on to click
"start your own application"; effectively 0% for recipients the platform
already recognizes.** Not one of the 151 unambiguously-existing-user shares
converted — consistent with the CTA's copy. The looser "ever flagged
new-user at least once" cut (771 shares, including mixed) gives 34.11%
(263/771) vs. 23.92% (149/623) for "any-existing-user" — the pure split
above is the more trustworthy read since mixed shares mechanically pull
both toward each other. See
[metrics/recipient_conversion_k_factor.md](../metrics/recipient_conversion_k_factor.md).

## Destination spread — two answers depending on definition (`analysis/q04.md`)

By raw reach (opens), **AU** leads (see [link_opened.md](link_opened.md)).
By **conversion efficiency** (`recipient_cta_clicked` ÷ `link_opened` per
destination — this table's own K-factor numerator/denominator pair), **AE
(UAE)** leads at **16.37%** (28/171), ahead of US (15.32%) and FR (15.29%);
AU itself is mid-pack on this cut (10.76%). Full 14-destination table:

| Destination | Opens | CTA clicks | CTA rate |
|---|---:|---:|---:|
| AE | 171 | 28 | **16.37%** |
| US | 124 | 19 | 15.32% |
| FR | 170 | 26 | 15.29% |
| TH | 175 | 26 | 14.86% |
| EG | 137 | 20 | 14.60% |
| TR | 166 | 24 | 14.46% |
| MY | 156 | 22 | 14.10% |
| ID | 162 | 21 | 12.96% |
| GR | 167 | 21 | 12.57% |
| SG | 148 | 18 | 12.16% |
| VN | 187 | 23 | 12.30% |
| GB | 173 | 19 | 10.98% |
| AU | 223 | 24 | 10.76% |
| JP | 151 | 14 | 9.27% |

**Method note:** this table computes each destination's rate independently
against `link_opened`'s own `destination` column (both tables carry it
directly) — it does **not** join `link_opened` ↔ `recipient_cta_clicked` on
`share_id` per row, sidestepping the still-unverified sharer-side ↔
recipient-side leg of D1 (the `link_opened → recipient_cta_clicked` join
itself is verified — see above — but this particular query didn't need it).

## Physical layout deviates from the 8 baseline tables — intentionally

`ENGINE = MergeTree`, `ORDER BY (toDate(timestamp), destination, share_id,
id)` — does not lead with the random `id` UUID, per known_issues.md D8.
`destination` takes the #2 slot (PM Q4: "which destinations spread most");
`cta` is excluded from the key as single-valued today. See
`justification.md` "ORDER BY / PARTITION BY reasoning".

## Other risks carried forward (see `justification.md` for full reasoning)

- **D1** — the 13.2% figure above remains a row-count ratio (305 rows /
  2,310 rows); the **share-grain** K-factor computed above (38.13%
  pure-new-user / 0% pure-existing-user) uses a different denominator
  (distinct shares, not opens) and is the verified, set-membership-based
  figure — `analysis/q03.md`, 2026-08-02. Report the share-grain figure for
  K-factor claims, not the raw 13.2% row ratio.
- **D3-shaped finding** — `recipient_is_new_user` (measured on `link_opened`)
  self-contradicts across reopens of the same share; see
  [link_opened.md](link_opened.md).
- No `application_id`/D2 risk applies — this table carries neither column.
