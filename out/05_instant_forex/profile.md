# Event Profile — rows: 6237, parse_errors: 0, duplicate_ids: 0, unparseable_timestamps: 0, time_span: 2026-06-08T06:00:00+00:00 to 2026-06-28T23:12:00+00:00

## Event Type Counts

| event | rows |
|---|---|
| forex_offer_shown | 2900 |
| amount_entered | 1033 |
| currency_selected | 1033 |
| forex_added_to_cart | 725 |
| forex_purchased | 546 |

## forex_offer_shown (n=2900, id_duplicates: 0)

| field | present | type | distinct values / range |
|---|---|---|---|
| app_version | 100% | string:2900 | distinct: 3 (0.1% unique) LC — 7.46.0(1022); 7.45.2(940); 7.44.0(938) |
| application_id | 100% | string:2900 | distinct: 2900 (100% unique) — (>1000 distinct, omitted) |
| city | 100% | string:2900 | distinct: 7 (0.2% unique) LC — Mumbai(1789); Singapore(297); Dubai(279); New York(177); London(139); Sydney(123); Riyadh(96) |
| client_lib | 100% | string:2900 | distinct: 2 (0.1% unique) LC — mobile-rn(2373); web-js(527) |
| destination | 100% | string:2900 | distinct: 14 (0.5% unique) LC — GR(240); US(236); ID(224); TH(223); VN(217); GB(210); TR(203); JP(199); SG(199); AU(196); ...(4) |
| device_type | 100% | string:2900 | distinct: 4 (0.1% unique) LC — ios(1234); android(951); web-user-b2c(527); Desktop(188) |
| from_currency | 100% | string:2900 | distinct: 1 (0.0% unique) LC — INR(2900) |
| fx_rate | 100% | float:2900 | distinct: 2899 (100.0% unique) — range: [0.0379, 89.9827] |
| geoip_country_code | 100% | string:2900 | distinct: 7 (0.2% unique) LC — IN(1789); SG(297); AE(279); US(177); GB(139); AU(123); SA(96) |
| os | 100% (6.1% null) | string:2724 | distinct: 4 (0.1% unique) LC — iOS(1234); Android(775); Mac OS X(380); Windows(335) |
| to_currency | 100% | string:2900 | distinct: 13 (0.4% unique) LC — EUR(436); USD(236); IDR(224); THB(223); VND(217); GBP(210); TRY(203); JPY(199); SGD(199); AUD(196); ...(3) |
| user_id | 100% | string:2900 | distinct: 2900 (100% unique) — (>1000 distinct, omitted) |

## amount_entered (n=1033, id_duplicates: 0)

| field | present | type | distinct values / range |
|---|---|---|---|
| amount | 100% | int:1033 | distinct: 6 (0.6% unique) — range: [200, 1500] |
| app_version | 100% | string:1033 | distinct: 3 (0.3% unique) LC — 7.44.0(355); 7.45.2(341); 7.46.0(337) |
| application_id | 100% | string:1033 | distinct: 1033 (100% unique) — (>1000 distinct, omitted) |
| city | 100% | string:1033 | distinct: 7 (0.7% unique) LC — Mumbai(626); Singapore(119); Dubai(104); New York(60); Sydney(52); London(40); Riyadh(32) |
| client_lib | 100% | string:1033 | distinct: 2 (0.2% unique) LC — mobile-rn(856); web-js(177) |
| destination | 100% | string:1033 | distinct: 14 (1.4% unique) LC — US(99); GR(83); TH(83); ID(79); FR(78); MY(75); GB(73); SG(73); VN(73); AE(70); ...(4) |
| device_type | 100% | string:1033 | distinct: 4 (0.4% unique) LC — ios(441); android(348); web-user-b2c(177); Desktop(67) |
| from_currency | 100% | string:1033 | distinct: 1 (0.1% unique) LC — INR(1033) |
| geoip_country_code | 100% | string:1033 | distinct: 7 (0.7% unique) LC — IN(626); SG(119); AE(104); US(60); AU(52); GB(40); SA(32) |
| os | 100% (6.3% null) | string:968 | distinct: 4 (0.4% unique) LC — iOS(441); Android(283); Mac OS X(130); Windows(114) |
| to_currency | 100% | string:1033 | distinct: 13 (1.3% unique) LC — EUR(161); USD(99); THB(83); IDR(79); MYR(75); GBP(73); SGD(73); VND(73); AED(70); JPY(65); ...(3) |
| user_id | 100% | string:1033 | distinct: 1033 (100% unique) — (>1000 distinct, omitted) |

## currency_selected (n=1033, id_duplicates: 0)

| field | present | type | distinct values / range |
|---|---|---|---|
| app_version | 100% | string:1033 | distinct: 3 (0.3% unique) LC — 7.44.0(355); 7.45.2(341); 7.46.0(337) |
| application_id | 100% | string:1033 | distinct: 1033 (100% unique) — (>1000 distinct, omitted) |
| city | 100% | string:1033 | distinct: 7 (0.7% unique) LC — Mumbai(626); Singapore(119); Dubai(104); New York(60); Sydney(52); London(40); Riyadh(32) |
| client_lib | 100% | string:1033 | distinct: 2 (0.2% unique) LC — mobile-rn(856); web-js(177) |
| destination | 100% | string:1033 | distinct: 14 (1.4% unique) LC — US(99); GR(83); TH(83); ID(79); FR(78); MY(75); GB(73); SG(73); VN(73); AE(70); ...(4) |
| device_type | 100% | string:1033 | distinct: 4 (0.4% unique) LC — ios(441); android(348); web-user-b2c(177); Desktop(67) |
| from_currency | 100% | string:1033 | distinct: 1 (0.1% unique) LC — INR(1033) |
| geoip_country_code | 100% | string:1033 | distinct: 7 (0.7% unique) LC — IN(626); SG(119); AE(104); US(60); AU(52); GB(40); SA(32) |
| os | 100% (6.3% null) | string:968 | distinct: 4 (0.4% unique) LC — iOS(441); Android(283); Mac OS X(130); Windows(114) |
| to_currency | 100% | string:1033 | distinct: 13 (1.3% unique) LC — EUR(161); USD(99); THB(83); IDR(79); MYR(75); GBP(73); SGD(73); VND(73); AED(70); JPY(65); ...(3) |
| user_id | 100% | string:1033 | distinct: 1033 (100% unique) — (>1000 distinct, omitted) |

## forex_added_to_cart (n=725, id_duplicates: 0)

| field | present | type | distinct values / range |
|---|---|---|---|
| addon_value_inr | 100% | float:725 | distinct: 720 (99.3% unique) — range: [4135.0, 134453.0] |
| amount | 100% | int:725 | distinct: 6 (0.8% unique) — range: [200, 1500] |
| app_version | 100% | string:725 | distinct: 3 (0.4% unique) LC — 7.44.0(255); 7.45.2(235); 7.46.0(235) |
| application_id | 100% | string:725 | distinct: 725 (100% unique) — 004fe3e8993c03e0973bbfcab2878f71(1); 007c38886d16aed2de434179f09ade2a(1); 00e7fdbe5a10e182ad3b9986067c4ad1(1); 013e33f02b7dd87e9bd0b60fc5894959(1); 017416f0748930b5f6c789c78e9fa604(1); 01a1ac189d9f4e60dfa6919d0b304642(1); 020cd9b632eabfaa8054b5d03ad1f67e(1); 025f95736208e0f3d5e709e7fc7a40ae(1); 02986e45ed50deb57d9c4dae0c146655(1); 041741f7177f5bde6dfef93753673f96(1); ...(715) |
| city | 100% | string:725 | distinct: 7 (1.0% unique) LC — Mumbai(451); Dubai(78); Singapore(73); New York(37); Sydney(33); London(27); Riyadh(26) |
| client_lib | 100% | string:725 | distinct: 2 (0.3% unique) LC — mobile-rn(606); web-js(119) |
| destination | 100% | string:725 | distinct: 14 (1.9% unique) LC — US(76); TH(61); GR(60); SG(55); MY(53); FR(52); GB(51); ID(51); JP(48); AE(47); ...(4) |
| device_type | 100% | string:725 | distinct: 4 (0.6% unique) LC — ios(324); android(237); web-user-b2c(119); Desktop(45) |
| from_currency | 100% | string:725 | distinct: 1 (0.1% unique) LC — INR(725) |
| geoip_country_code | 100% | string:725 | distinct: 7 (1.0% unique) LC — IN(451); AE(78); SG(73); US(37); AU(33); GB(27); SA(26) |
| os | 100% (5.9% null) | string:682 | distinct: 4 (0.6% unique) LC — iOS(324); Android(194); Mac OS X(91); Windows(73) |
| to_currency | 100% | string:725 | distinct: 13 (1.8% unique) LC — EUR(112); USD(76); THB(61); SGD(55); MYR(53); GBP(51); IDR(51); JPY(48); AED(47); TRY(45); ...(3) |
| user_id | 100% | string:725 | distinct: 725 (100% unique) — 01GJyYNUc6ts8U382l1DgPaLMXPO(1); 06XTYYhhujFXblqMXopRLyvx3ywO(1); 08U56juQUR24vficIPsleynGxHeZ(1); 0F0Ku4EJ9IPpjmM4VrhAULenACCI(1); 0Ni70I0yUD5zS7eCqcnlLyytreBe(1); 0P2OawzgPIRa3rJIOcOV875dD3vC(1); 0PtEAbt3bL7x5S5OEZQKtmoaQGbr(1); 0QIr1u7kMvoxkVYhQvM6PtYakE53(1); 0Tz77OjU1xTuzfi7RlnXvyDF1bMr(1); 0cRbz2XLtez3S5aMF8a4M17cIGVR(1); ...(715) |

## forex_purchased (n=546, id_duplicates: 0)

| field | present | type | distinct values / range |
|---|---|---|---|
| addon_value_inr | 100% | float:546 | distinct: 544 (99.6% unique) — range: [4245.0, 130911.0] |
| amount | 100% | int:546 | distinct: 6 (1.1% unique) — range: [200, 1500] |
| app_version | 100% | string:546 | distinct: 3 (0.5% unique) LC — 7.44.0(196); 7.45.2(176); 7.46.0(174) |
| application_id | 100% | string:546 | distinct: 546 (100% unique) — 004fe3e8993c03e0973bbfcab2878f71(1); 00e7fdbe5a10e182ad3b9986067c4ad1(1); 017416f0748930b5f6c789c78e9fa604(1); 020cd9b632eabfaa8054b5d03ad1f67e(1); 041741f7177f5bde6dfef93753673f96(1); 0456961f64f3540ca45e3c77163d3ede(1); 04c617b087d53dd3d38162cd6d6c9c93(1); 064fc3f2c59cf99021e1a5a8f018f5dd(1); 06c337b81352f66322151840f0d7bf4f(1); 0712df2447c6283a1a9a50314313016a(1); ...(536) |
| city | 100% | string:546 | distinct: 7 (1.3% unique) LC — Mumbai(340); Dubai(60); Singapore(59); New York(27); Sydney(22); London(21); Riyadh(17) |
| client_lib | 100% | string:546 | distinct: 2 (0.4% unique) LC — mobile-rn(456); web-js(90) |
| destination | 100% | string:546 | distinct: 14 (2.6% unique) LC — US(58); TH(51); SG(46); GR(42); MY(42); FR(40); GB(40); ID(37); JP(36); AE(34); ...(4) |
| device_type | 100% | string:546 | distinct: 4 (0.7% unique) LC — ios(244); android(179); web-user-b2c(90); Desktop(33) |
| from_currency | 100% | string:546 | distinct: 1 (0.2% unique) LC — INR(546) |
| geoip_country_code | 100% | string:546 | distinct: 7 (1.3% unique) LC — IN(340); AE(60); SG(59); US(27); AU(22); GB(21); SA(17) |
| os | 100% (5.9% null) | string:514 | distinct: 4 (0.7% unique) LC — iOS(244); Android(147); Mac OS X(64); Windows(59) |
| to_currency | 100% | string:546 | distinct: 13 (2.4% unique) LC — EUR(82); USD(58); THB(51); SGD(46); MYR(42); GBP(40); IDR(37); JPY(36); AED(34); EGP(32); ...(3) |
| user_id | 100% | string:546 | distinct: 546 (100% unique) — 01GJyYNUc6ts8U382l1DgPaLMXPO(1); 06XTYYhhujFXblqMXopRLyvx3ywO(1); 08U56juQUR24vficIPsleynGxHeZ(1); 0F0Ku4EJ9IPpjmM4VrhAULenACCI(1); 0Ni70I0yUD5zS7eCqcnlLyytreBe(1); 0P2OawzgPIRa3rJIOcOV875dD3vC(1); 0PtEAbt3bL7x5S5OEZQKtmoaQGbr(1); 0QIr1u7kMvoxkVYhQvM6PtYakE53(1); 0Tz77OjU1xTuzfi7RlnXvyDF1bMr(1); 0qmvfmEa1K3oKAs375aE7ziE0X5b(1); ...(536) |

## Field × Event Grid

| field | FOS | AE | CS | FATC | FP |
|---|---|---|---|---|---|
| app_version | yes | yes | yes | yes | yes |
| application_id | yes | yes | yes | yes | yes |
| city | yes | yes | yes | yes | yes |
| client_lib | yes | yes | yes | yes | yes |
| destination | yes | yes | yes | yes | yes |
| device_type | yes | yes | yes | yes | yes |
| from_currency | yes | yes | yes | yes | yes |
| geoip_country_code | yes | yes | yes | yes | yes |
| os | yes | yes | yes | yes | yes |
| to_currency | yes | yes | yes | yes | yes |
| user_id | yes | yes | yes | yes | yes |
| amount | no | yes | no | yes | yes |
| addon_value_inr | no | no | no | yes | yes |
| fx_rate | yes | no | no | no | no |

**Legend:** FOS=forex_offer_shown; AE=amount_entered; CS=currency_selected; FATC=forex_added_to_cart; FP=forex_purchased

