---
id: metric.passport_capture_pass_rate
kind: metric
status: verified
confidence: low
source: clickathon DB — document_uploaded flag counts; reliability undermined by C10
last_verified: 2026-08-01
links: [table.document_uploaded, contradiction.c10_capture_threshold_flag_broken, known_issue.k2_passport_scan_model_update]
---

# Passport-capture pass rate

**Formula:** uploads with `is_crossed_failed_attempt_threshold = 0` ÷ total uploads.

**Current value: 88.76%** (18,147 ÷ 20,446), H1 2026.

```sql
SELECT round(100.0 * countIf(is_crossed_failed_attempt_threshold = 0) / count(), 2)
FROM clickathon.document_uploaded
```

## ⚠ Computes cleanly; **confidence is low**

The formula from `base_context.md` runs without error against real columns. The
**underlying flag is internally inconsistent**:

- 1,642 uploads are flagged as having crossed the failed-attempt threshold while
  having `retry_count = 0` — **71.4% of all flagged events**.
- 709 uploads reach `retry_count = 3`, equal to the constant
  `failed_attempt_threshold = 3`, and are **not** flagged.

See [known_issues.md](../known_issues.md). Report this
metric **with its caveat attached**, never as a bare number.

## Recommended dual reporting

```sql
SELECT
  round(100.0 * countIf(is_crossed_failed_attempt_threshold = 0) / count(), 2) AS pass_rate_flag,
  round(100.0 * countIf(retry_count < failed_attempt_threshold) / count(), 2) AS pass_rate_retry_derived
FROM clickathon.document_uploaded
```

Divergence between the two columns is itself the finding.

## Segment worth surfacing

Broken out by month and OS, this metric carries the dataset's clearest product
signal: Android capture failure rising 5.96% → 33.54% across H1, inflecting in
April. See [K2](../known_issues.md) — the trend is
robust even though the absolute level is not.
