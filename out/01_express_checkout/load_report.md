# Load report — 01_express_checkout

Cited known_issues.md ids: D2, D1, D8, D7, D9, D6, K1
Cited but not loader-actionable (no fix block): D1, D8, D7, D9, D6, K1

## express_checkout_shown
- rows loaded: 1650
- normalized `application_id` per D2
- D2 verify on `application_id`: overlap_pct = 0.0% -> STOP -- report as finding, analyse table standalone only

## express_checkout_selected
- rows loaded: 1007
- normalized `application_id` per D2
- D2 verify on `application_id`: overlap_pct = 0.0% -> STOP -- report as finding, analyse table standalone only

## saved_method_used
- rows loaded: 1007
- normalized `application_id` per D2
- D2 verify on `application_id`: overlap_pct = 0.0% -> STOP -- report as finding, analyse table standalone only

## otp_entered
- rows loaded: 1007
- normalized `application_id` per D2
- D2 verify on `application_id`: overlap_pct = 0.0% -> STOP -- report as finding, analyse table standalone only

## express_payment_confirmed
- rows loaded: 836
- normalized `application_id` per D2
- D2 verify on `application_id`: overlap_pct = 0.0% -> STOP -- report as finding, analyse table standalone only
