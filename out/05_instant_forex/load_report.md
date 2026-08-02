# Load report — 05_instant_forex

Cited known_issues.md ids: D2, D6, D8, D9, D1, D7
Cited but not loader-actionable (no fix block): D6, D8, D9, D1, D7
## forex_offer_shown (created)
- rows loaded: 2900
- normalized `application_id` per D2
- D2 verify on `application_id`: overlap_pct = 0.0% -> STOP -- report as finding, analyse table standalone only

## currency_selected (created)
- rows loaded: 1033
- normalized `application_id` per D2
- D2 verify on `application_id`: overlap_pct = 0.0% -> STOP -- report as finding, analyse table standalone only

## amount_entered (created)
- rows loaded: 1033
- normalized `application_id` per D2
- D2 verify on `application_id`: overlap_pct = 0.0% -> STOP -- report as finding, analyse table standalone only

## forex_added_to_cart (created)
- rows loaded: 725
- normalized `application_id` per D2
- D2 verify on `application_id`: overlap_pct = 0.0% -> STOP -- report as finding, analyse table standalone only

## forex_purchased (created)
- rows loaded: 546
- normalized `application_id` per D2
- D2 verify on `application_id`: overlap_pct = 0.0% -> STOP -- report as finding, analyse table standalone only
