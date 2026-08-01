# Event Profile — rows: 5507, parse_errors: 0, duplicate_ids: 0, unparseable_timestamps: 0, time_span: 2026-06-08T06:00:00+00:00 to 2026-06-28T23:11:00+00:00

## Event Type Counts

| event | rows |
|---|---|
| express_checkout_shown | 1650 |
| express_checkout_selected | 1007 |
| otp_entered | 1007 |
| saved_method_used | 1007 |
| express_payment_confirmed | 836 |

## express_checkout_shown (n=1650, id_duplicates: 0)

| field | present | type | distinct values / range |
|---|---|---|---|
| app_version | 100% | string:1650 | distinct: 3 (0.2% unique) LC — 7.45.2(572); 7.44.0(559); 7.46.0(519) |
| application_id | 100% | string:1650 | distinct: 1650 (100% unique) — (>1000 distinct, omitted) |
| city | 100% | string:1650 | distinct: 7 (0.4% unique) LC — Mumbai(1007); Dubai(153); Singapore(147); New York(122); Sydney(81); London(75); Riyadh(65) |
| client_lib | 100% | string:1650 | distinct: 2 (0.1% unique) LC — mobile-rn(1332); web-js(318) |
| currency | 100% | string:1650 | distinct: 7 (0.4% unique) LC — INR(1007); AED(153); SGD(147); USD(122); AUD(81); GBP(75); SAR(65) |
| destination | 100% | string:1650 | distinct: 14 (0.8% unique) LC — JP(141); AU(129); US(128); SG(123); FR(120); GB(119); AE(116); TH(116); ID(115); TR(115); ...(4) |
| device_type | 100% | string:1650 | distinct: 4 (0.2% unique) LC — ios(702); android(538); web-user-b2c(318); Desktop(92) |
| eligible | 100% | bool:1650 | distinct: 1 (0.1% unique) — true(1650) |
| geoip_country_code | 100% | string:1650 | distinct: 7 (0.4% unique) LC — IN(1007); AE(153); SG(147); US(122); AU(81); GB(75); SA(65) |
| os | 100% (6.8% null) | string:1538 | distinct: 4 (0.2% unique) LC — iOS(702); Android(426); Mac OS X(223); Windows(187) |
| shown_amount | 100% | float:1650 | distinct: 1479 (89.6% unique) — range: [1502.0, 9000.0] |
| user_id | 100% | string:1650 | distinct: 1650 (100% unique) — (>1000 distinct, omitted) |

## express_checkout_selected (n=1007, id_duplicates: 0)

| field | present | type | distinct values / range |
|---|---|---|---|
| app_version | 100% | string:1007 | distinct: 3 (0.3% unique) LC — 7.45.2(354); 7.44.0(339); 7.46.0(314) |
| application_id | 100% | string:1007 | distinct: 1007 (100% unique) — (>1000 distinct, omitted) |
| city | 100% | string:1007 | distinct: 7 (0.7% unique) LC — Mumbai(606); Singapore(94); Dubai(88); New York(76); Sydney(55); London(46); Riyadh(42) |
| client_lib | 100% | string:1007 | distinct: 2 (0.2% unique) LC — mobile-rn(822); web-js(185) |
| destination | 100% | string:1007 | distinct: 14 (1.4% unique) LC — JP(95); GB(80); TH(78); AU(76); ID(75); US(72); SG(70); AE(68); MY(68); TR(68); ...(4) |
| device_type | 100% | string:1007 | distinct: 4 (0.4% unique) LC — ios(428); android(338); web-user-b2c(185); Desktop(56) |
| geoip_country_code | 100% | string:1007 | distinct: 7 (0.7% unique) LC — IN(606); SG(94); AE(88); US(76); AU(55); GB(46); SA(42) |
| os | 100% (6.9% null) | string:938 | distinct: 4 (0.4% unique) LC — iOS(428); Android(269); Mac OS X(137); Windows(104) |
| saved_method_type | 100% | string:1007 | distinct: 3 (0.3% unique) LC — card(342); upi(337); wallet(328) |
| user_id | 100% | string:1007 | distinct: 1007 (100% unique) — (>1000 distinct, omitted) |

## otp_entered (n=1007, id_duplicates: 0)

| field | present | type | distinct values / range |
|---|---|---|---|
| app_version | 100% | string:1007 | distinct: 3 (0.3% unique) LC — 7.45.2(354); 7.44.0(339); 7.46.0(314) |
| application_id | 100% | string:1007 | distinct: 1007 (100% unique) — (>1000 distinct, omitted) |
| city | 100% | string:1007 | distinct: 7 (0.7% unique) LC — Mumbai(606); Singapore(94); Dubai(88); New York(76); Sydney(55); London(46); Riyadh(42) |
| client_lib | 100% | string:1007 | distinct: 2 (0.2% unique) LC — mobile-rn(822); web-js(185) |
| destination | 100% | string:1007 | distinct: 14 (1.4% unique) LC — JP(95); GB(80); TH(78); AU(76); ID(75); US(72); SG(70); AE(68); MY(68); TR(68); ...(4) |
| device_type | 100% | string:1007 | distinct: 4 (0.4% unique) LC — ios(428); android(338); web-user-b2c(185); Desktop(56) |
| geoip_country_code | 100% | string:1007 | distinct: 7 (0.7% unique) LC — IN(606); SG(94); AE(88); US(76); AU(55); GB(46); SA(42) |
| os | 100% (6.9% null) | string:938 | distinct: 4 (0.4% unique) LC — iOS(428); Android(269); Mac OS X(137); Windows(104) |
| otp_attempts | 100% | int:1007 | distinct: 3 (0.3% unique) — range: [1, 3] |
| otp_success | 100% | bool:1007 | distinct: 2 (0.2% unique) — true(937); false(70) |
| user_id | 100% | string:1007 | distinct: 1007 (100% unique) — (>1000 distinct, omitted) |

## saved_method_used (n=1007, id_duplicates: 0)

| field | present | type | distinct values / range |
|---|---|---|---|
| app_version | 100% | string:1007 | distinct: 3 (0.3% unique) LC — 7.45.2(354); 7.44.0(339); 7.46.0(314) |
| application_id | 100% | string:1007 | distinct: 1007 (100% unique) — (>1000 distinct, omitted) |
| city | 100% | string:1007 | distinct: 7 (0.7% unique) LC — Mumbai(606); Singapore(94); Dubai(88); New York(76); Sydney(55); London(46); Riyadh(42) |
| client_lib | 100% | string:1007 | distinct: 2 (0.2% unique) LC — mobile-rn(822); web-js(185) |
| destination | 100% | string:1007 | distinct: 14 (1.4% unique) LC — JP(95); GB(80); TH(78); AU(76); ID(75); US(72); SG(70); AE(68); MY(68); TR(68); ...(4) |
| device_type | 100% | string:1007 | distinct: 4 (0.4% unique) LC — ios(428); android(338); web-user-b2c(185); Desktop(56) |
| geoip_country_code | 100% | string:1007 | distinct: 7 (0.7% unique) LC — IN(606); SG(94); AE(88); US(76); AU(55); GB(46); SA(42) |
| os | 100% (6.9% null) | string:938 | distinct: 4 (0.4% unique) LC — iOS(428); Android(269); Mac OS X(137); Windows(104) |
| user_id | 100% | string:1007 | distinct: 1007 (100% unique) — (>1000 distinct, omitted) |

## express_payment_confirmed (n=836, id_duplicates: 0)

| field | present | type | distinct values / range |
|---|---|---|---|
| app_version | 100% | string:836 | distinct: 3 (0.4% unique) LC — 7.45.2(295); 7.44.0(280); 7.46.0(261) |
| application_id | 100% | string:836 | distinct: 836 (100% unique) — 000c06bc633c33a6c2c656f9194702a8(1); 0015cbeb116f8bfecb12419bf555dfe7(1); 004827d8dab7c18457e95cafffc165b7(1); 01150588d7ee0b960a9eb48d674f7bca(1); 013613b7aec66fcf0316867c68e936b0(1); 0155a7cd7358a775ccfb25479aeb329e(1); 016fba843b7dcfa14c125a7f5d6c4808(1); 020b7359d144c432b2ebc71aac648d38(1); 0231ee3aee84eeb10936d6fa4aee4f13(1); 024fe5acb25c7354a4fbcdf4c4f49064(1); ...(826) |
| city | 100% | string:836 | distinct: 7 (0.8% unique) LC — Mumbai(509); Singapore(71); Dubai(70); New York(62); Sydney(50); London(39); Riyadh(35) |
| client_lib | 100% | string:836 | distinct: 2 (0.2% unique) LC — mobile-rn(666); web-js(170) |
| destination | 100% | string:836 | distinct: 14 (1.7% unique) LC — JP(81); TH(69); ID(67); AU(65); GB(65); AE(61); SG(59); US(57); TR(55); FR(54); ...(4) |
| device_type | 100% | string:836 | distinct: 4 (0.5% unique) LC — ios(316); android(303); web-user-b2c(170); Desktop(47) |
| geoip_country_code | 100% | string:836 | distinct: 7 (0.8% unique) LC — IN(509); SG(71); AE(70); US(62); AU(50); GB(39); SA(35) |
| os | 100% (7.4% null) | string:774 | distinct: 4 (0.5% unique) LC — iOS(316); Android(241); Mac OS X(119); Windows(98) |
| payment.amount | 100% | float:836 | distinct: 799 (95.6% unique) — range: [1509.0, 8997.0] |
| payment.currency | 100% | string:836 | distinct: 7 (0.8% unique) LC — INR(509); SGD(71); AED(70); USD(62); AUD(50); GBP(39); SAR(35) |
| payment.latency_ms | 100% | int:836 | distinct: 743 (88.9% unique) — range: [607, 3999] |
| user_id | 100% | string:836 | distinct: 836 (100% unique) — 05GXLekTgyxsRnZAV6n3Gd5jAoVW(1); 0KM982fGXWHp1GORBpr7Buw2rL2U(1); 0MyJSb8AnYdJk6EagoNSwbepr7GE(1); 0RwqC2HTmKM6dvn8JpVSoJmZoLt7(1); 0SRTeTTwWnfumOqrKEooKmiUX4GW(1); 0VFW7GohMyk1URbA8dlLDMt9YOeY(1); 0WbgyXNbBU5pgyAQ6GWOazIyQ9AU(1); 0Z8hqui82S2GE1PbyvFtkPBWAYR6(1); 0ZWEfeklRg53ZENn7DJmztAAw6wk(1); 0bTEmPl3E4loyAp3nmxU24zBlR3r(1); ...(826) |

## Field × Event Grid

| field | ECS | ECS2 | OE | SMU | EPC |
|---|---|---|---|---|---|
| app_version | yes | yes | yes | yes | yes |
| application_id | yes | yes | yes | yes | yes |
| city | yes | yes | yes | yes | yes |
| client_lib | yes | yes | yes | yes | yes |
| destination | yes | yes | yes | yes | yes |
| device_type | yes | yes | yes | yes | yes |
| geoip_country_code | yes | yes | yes | yes | yes |
| os | yes | yes | yes | yes | yes |
| user_id | yes | yes | yes | yes | yes |
| currency | yes | no | no | no | no |
| eligible | yes | no | no | no | no |
| otp_attempts | no | no | yes | no | no |
| otp_success | no | no | yes | no | no |
| payment.amount | no | no | no | no | yes |
| payment.currency | no | no | no | no | yes |
| payment.latency_ms | no | no | no | no | yes |
| saved_method_type | no | yes | no | no | no |
| shown_amount | yes | no | no | no | no |

**Legend:** ECS=express_checkout_shown; ECS2=express_checkout_selected; OE=otp_entered; SMU=saved_method_used; EPC=express_payment_confirmed

