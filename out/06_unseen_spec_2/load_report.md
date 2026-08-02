# Load report — 06_unseen_spec_2

Cited known_issues.md ids: D2, D1, D7, D8
Cited but not loader-actionable (no fix block): D1, D7, D8
## coupon_field_shown (created)
- rows loaded: 2100
- normalized `application_id` per D2
- D2 verify on `application_id`: overlap_pct = 0.0% -> STOP -- report as finding, analyse table standalone only

## coupon_entered (created)
- rows loaded: 848
- normalized `application_id` per D2
- D2 verify on `application_id`: overlap_pct = 0.0% -> STOP -- report as finding, analyse table standalone only

## coupon_applied (created)
- rows loaded: 580
- normalized `application_id` per D2
- D2 verify on `application_id`: overlap_pct = 0.0% -> STOP -- report as finding, analyse table standalone only

## coupon_rejected (created)
- rows loaded: 268
- normalized `application_id` per D2
- D2 verify on `application_id`: overlap_pct = 0.0% -> STOP -- report as finding, analyse table standalone only

## discount_shown (created)
- rows loaded: 580
- normalized `application_id` per D2
- D2 verify on `application_id`: overlap_pct = 0.0% -> STOP -- report as finding, analyse table standalone only

## checkout_with_coupon (created)
- rows loaded: 987
- normalized `application_id` per D2
- D2 verify on `application_id`: overlap_pct = 0.0% -> STOP -- report as finding, analyse table standalone only
