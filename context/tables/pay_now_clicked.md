---
id: table.pay_now_clicked
kind: table
status: verified
confidence: high
source: clickathon DB — system.tables, system.columns, profiling queries; out/01_express_checkout/analysis/q02.md — K1 re-test using spec 01's new columns
last_verified: 2026-08-02
links: [doc.envelope, table.purchase_completed, known_issue.k1_ios_webkit_otp, spec.01_express_checkout]
---

# `pay_now_clicked`

Checkout intent. `base_context.md` files this as "supporting", but it sits
**inside the funnel** between document upload and purchase and belongs in any
checkout analysis.

| | |
|---|---:|
| Rows | **14,739** |
| Distinct users / applications | 14,739 |
| Time range | 2026-01-01 00:32:37 → 2026-07-01 01:53:34 |
| Step-through from `document_uploaded` | **72.09%** |
| → `purchase_completed` | **47.86%** |

Envelope: see [the envelope](index.md). Event-specific columns below.

| Column | Type | Values |
|---|---|---|
| `payment_method` | `Nullable(String)` | `applePay` · `card` · `netbanking` · `upi` · `wallet` |
| `amount` | `Nullable(Float64)` | same multi-currency caveat as `purchase_completed.value` |
| `currency` | `Nullable(String)` | 9 currencies |
| `coupon_applied` | `Nullable(UInt8)` | |
| `plan_selected` | `Nullable(String)` | `black` · `express` · `standard` — **undocumented** |

## Checkout completion by platform

The `pay_now_clicked → purchase_completed` rate is where
[K1](../known_issues.md) was supposed to show up. It does the
opposite: iOS 49.88% vs Mac OS X 43.77%, and in the UAE iOS reaches 70.78% vs
Android 43.55%. K1 is **refuted**.

Roughly **half of all payment intents fail to convert** (47.86%) — a large,
genuinely unexplained leak that no known issue accounts for.
[Spec 01 Express Checkout](../known_issues.md) adds
`otp_attempts` / `otp_success`, the first instrumentation able to explain it.

**2026-08-02 — that re-test has run, on Express Checkout's own tables**
(`out/01_express_checkout/analysis/q02.md`, not this table): OTP failures
there are 100% iOS-concentrated, a real but narrow finding scoped to Express
Checkout (D2 blocks joining it back to this table). It does not explain this
table's own 52.14% leak — that remains open. See
[known_issues.md](../known_issues.md) → K1.
