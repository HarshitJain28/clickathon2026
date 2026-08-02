# Load report — 04_checkout_recovery_3

Cited known_issues.md ids: D1, D2, D6, D8, D9
Cited but not loader-actionable (no fix block): D1, D6, D8, D9
## abandonment_detected (created)
- rows loaded: 2300
- normalized `application_id` per D2
- D2 verify on `application_id`: overlap_pct = 0.0% -> STOP -- report as finding, analyse table standalone only

## reminder_sent (created)
- rows loaded: 2300
- normalized `application_id` per D2
- D2 verify on `application_id`: overlap_pct = 0.0% -> STOP -- report as finding, analyse table standalone only

## reminder_opened (created)
- rows loaded: 690
- normalized `application_id` per D2
- D2 verify on `application_id`: overlap_pct = 0.0% -> STOP -- report as finding, analyse table standalone only

## reminder_cta_clicked (created)
- rows loaded: 268
- normalized `application_id` per D2
- D2 verify on `application_id`: overlap_pct = 0.0% -> STOP -- report as finding, analyse table standalone only

## resumed_at_step (created)
- rows loaded: 268
- normalized `application_id` per D2
- D2 verify on `application_id`: overlap_pct = 0.0% -> STOP -- report as finding, analyse table standalone only

## reconverted (created)
- rows loaded: 93
- normalized `application_id` per D2
- D2 verify on `application_id`: overlap_pct = 0.0% -> STOP -- report as finding, analyse table standalone only
