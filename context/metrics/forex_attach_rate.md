---
id: metric.forex_attach_rate
kind: metric
status: verified
confidence: high
source: out/05_instant_forex/analysis/q01.md — verified overall + by-destination attach rate; out/05_instant_forex/analysis/q03.md — verified full-funnel set membership, drop location; out/05_instant_forex/analysis/q04.md — verified monotonicity, currency/device/geo skew
last_verified: 2026-08-02
links: [table.forex_offer_shown, table.forex_purchased, table.currency_selected, table.amount_entered, table.forex_added_to_cart, known_issue.d1_windowfunnel_loses_conversions, known_issue.d2_application_id_join_format, metrics.index]
---

# Instant Forex attach rate

**Definition:** `uniqExact(forex_purchased.user_id) /
uniqExact(forex_offer_shown.user_id)`, computed by **set membership**
(`forex_purchased.user_id ⊆ forex_offer_shown.user_id` — exact, no
fan-out, both tables 1-row-per-user per D6 — valid per
[D1](../known_issues.md#d1--windowfunnel-loses-52-of-conversions--critical),
never `windowFunnel`). Confirmed 100% timestamp-monotonic
(`forex_purchased.timestamp ≥ forex_offer_shown.timestamp` on all 546
matched pairs, `analysis/q04.md`) — this funnel, unlike the main visa
funnel, has no ordering trap. Spec 05 (Instant Forex Add-on) only.

## Overall and full-funnel step-through

| Stage | Users | Step-through | Drop-off | Users lost |
|---|---:|---:|---:|---:|
| `forex_offer_shown` | 2,900 | — | — | — |
| `currency_selected` | 1,033 | 35.62% | **64.38%** | **1,867** |
| `amount_entered` | 1,033 | 100% | 0% | 0 |
| `forex_added_to_cart` | 725 | 70.18% | 29.82% | 308 |
| `forex_purchased` | 546 | 75.31% | 24.69% | 179 |
| **Overall attach rate** | **546 / 2,900** | — | — | **18.83%** |

The funnel is **perfectly nested** end-to-end (every downstream stage's
users are a 100% subset of the prior stage). The leak is overwhelmingly
concentrated at the very first step — **`forex_offer_shown →
currency_selected`** loses 64.38% of users, more than 2.6× the combined
loss of every later step. Once a user picks a currency they always enter
an amount (100% step-through); `currency_selected` and `amount_entered`
are a confirmed 1:1 pairing, not a row-count coincidence
(`analysis/q03.md`).

## By `destination` (n=174–240 offers each)

| destination | shown | purchased | attach rate |
|---|---:|---:|---:|
| **US** | 236 | 58 | **24.58%** (best) |
| SG | 199 | 46 | 23.12% |
| TH | 223 | 51 | 22.87% |
| MY | 193 | 42 | 21.76% |
| FR | 196 | 40 | 20.41% |
| GB | 210 | 40 | 19.05% |
| EG | 174 | 32 | 18.39% |
| JP | 199 | 36 | 18.09% |
| AE | 190 | 34 | 17.89% |
| GR | 240 | 42 | 17.50% |
| ID | 224 | 37 | 16.52% |
| TR | 203 | 30 | 14.78% |
| VN | 217 | 31 | 14.29% |
| **AU** | 196 | 27 | **13.78%** (worst) |

~11pp spread, no obvious geographic clustering (top 4 span US/SG/TH/MY
across three continents). Only 14 of the platform's 27 destinations appear
in this sample — treat as directional, not exhaustive.

## By `to_currency` — coarser than `destination`, one blend

Tracks `destination` almost exactly, with one wrinkle: **EUR** (18.81%,
n=436) blends two Eurozone destinations, FR (20.41%, n=196) and GR
(17.5%, n=240) — masking a 3pp destination-level gap. Every other
currency maps 1:1 to a destination (USD↔US, THB↔TH, etc). Report
currency-level attach rates with this caveat, not as a proxy for a single
market.

## Segment skew

- **Device (mild, ~2.7pp spread):** ios best 19.77% (n=1,234), android
  18.82%, Desktop 17.55%, web-user-b2c worst 17.08% (n=527).
- **Geo (mild-to-moderate, ~6.4pp spread across 7 observed
  `geoip_country_code`s):** AE best 21.51% (n=279), SG 19.87%, IN 19.01%
  (India is 61.7% of all offers shown — 1,789/2,900 — so the pooled
  18.83% figure is effectively India-weighted), AU 17.89%, SA 17.71%, US
  15.25%, GB worst 15.11% (n=139).

## Caveats

- Per [D2](../known_issues.md#d2--spec-application_id-wont-join--critical),
  this spec's `application_id` has 0% overlap with `application_started`
  — this metric is standalone within spec 05's own 5 tables, not
  comparable to `funnel_conversion` or joinable to insurance/plan add-ons
  or other specs.
- Sample: `out/05_instant_forex` only, 2026-06-08 06:00 → 2026-06-28
  23:12 — a 3-week window, not full H1 2026. Per-destination/geo/device
  cells are small (96–1,234); read gaps under ~5pp as directional, not
  conclusive.
