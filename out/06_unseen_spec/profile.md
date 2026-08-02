# Event Profile — rows: 5363, parse_errors: 0, duplicate_ids: 0, unparseable_timestamps: 0, time_span: 2026-06-08T06:00:00+00:00 to 2026-06-28T23:11:00+00:00

## Event Type Counts

| event | rows |
|---|---|
| coupon_field_shown | 2100 |
| checkout_with_coupon | 987 |
| coupon_entered | 848 |
| coupon_applied | 580 |
| discount_shown | 580 |
| coupon_rejected | 268 |

## coupon_field_shown (n=2100, id_duplicates: 0)

| field | present | type | distinct values / range |
|---|---|---|---|
| app_version | 100% | string:2100 | distinct: 3 (0.1% unique) LC — 7.44.0(724); 7.46.0(691); 7.45.2(685) |
| application_id | 100% | string:2100 | distinct: 2100 (100% unique) — (>1000 distinct, omitted) |
| cart_value | 100% | float:2100 | distinct: 1840 (87.6% unique) — range: [1501.0, 9000.0] |
| city | 100% | string:2100 | distinct: 7 (0.3% unique) LC — Mumbai(1275); Singapore(217); Dubai(192); New York(139); London(103); Sydney(94); Riyadh(80) |
| client_lib | 100% | string:2100 | distinct: 2 (0.1% unique) LC — mobile-rn(1721); web-js(379) |
| currency | 100% | string:2100 | distinct: 7 (0.3% unique) LC — INR(1275); SGD(217); AED(192); USD(139); GBP(103); AUD(94); SAR(80) |
| destination | 100% | string:2100 | distinct: 14 (0.7% unique) LC — AU(165); AE(163); TH(163); FR(158); ID(153); US(152); JP(150); GB(146); TR(146); GR(144); ...(4) |
| device_type | 100% | string:2100 | distinct: 4 (0.2% unique) LC — ios(874); android(688); web-user-b2c(379); Desktop(159) |
| geoip_country_code | 100% | string:2100 | distinct: 7 (0.3% unique) LC — IN(1275); SG(217); AE(192); US(139); GB(103); AU(94); SA(80) |
| os | 100% (6.2% null) | string:1969 | distinct: 4 (0.2% unique) LC — iOS(874); Android(557); Mac OS X(276); Windows(262) |
| user_id | 100% | string:2100 | distinct: 2100 (100% unique) — (>1000 distinct, omitted) |

## checkout_with_coupon (n=987, id_duplicates: 0)

| field | present | type | distinct values / range |
|---|---|---|---|
| app_version | 100% | string:987 | distinct: 3 (0.3% unique) LC — 7.46.0(336); 7.44.0(333); 7.45.2(318) |
| application_id | 100% | string:987 | distinct: 987 (100% unique) — 00b15b85794f4dd101aa8907ab20d349(1); 00b26f0951b1632e3e15087666d41176(1); 013d018fb3cd5d6b817452b5f3778963(1); 019dd0558d3c070d7fdcc240c51753e7(1); 0262dfb2d7c3a93a94c39678cbabccaf(1); 0267bcaf68d15f52e2ca4e10fe916cfb(1); 034f97dc791a66c55a727b80111a1ac5(1); 035f3ad01850c5ec55719fc7e1d2743a(1); 03f1a7924fcc2943fe6c13d2cdf21558(1); 042ea47e0f4a3bf3d40d59001fdfd76e(1); ...(977) |
| cart_value | 100% | float:987 | distinct: 933 (94.5% unique) — range: [1502.0, 9000.0] |
| city | 100% | string:987 | distinct: 7 (0.7% unique) LC — Mumbai(605); Singapore(90); Dubai(87); New York(75); London(48); Sydney(47); Riyadh(35) |
| client_lib | 100% | string:987 | distinct: 2 (0.2% unique) LC — mobile-rn(817); web-js(170) |
| coupon_code | 100% (62.9% null) | string:366 | distinct: 5 (0.5% unique) LC — FREESHIP(80); SUMMER20(75); FIRST10(72); ATLYS15(71); WELCOME(68) |
| currency | 100% | string:987 | distinct: 7 (0.7% unique) LC — INR(605); SGD(90); AED(87); USD(75); GBP(48); AUD(47); SAR(35) |
| destination | 100% | string:987 | distinct: 14 (1.4% unique) LC — JP(80); FR(78); TH(76); US(76); AE(75); GR(72); VN(72); AU(68); GB(68); MY(68); ...(4) |
| device_type | 100% | string:987 | distinct: 4 (0.4% unique) LC — ios(427); android(315); web-user-b2c(170); Desktop(75) |
| discount_amount | 100% | int:769, float:218 | distinct: 203 (20.6% unique) — range: [0, 1768.0] |
| final_value | 100% | float:987 | distinct: 927 (93.9% unique) — range: [1286.0, 9000.0] |
| geoip_country_code | 100% | string:987 | distinct: 7 (0.7% unique) LC — IN(605); SG(90); AE(87); US(75); GB(48); AU(47); SA(35) |
| os | 100% (6.2% null) | string:926 | distinct: 4 (0.4% unique) LC — iOS(427); Android(254); Mac OS X(132); Windows(113) |
| user_id | 100% | string:987 | distinct: 987 (100% unique) — 02vIAS8566AckZwQLKqxJ4avrr3J(1); 05u9xfEa2GSY6K8wD37rmgvCvM9a(1); 07Dx9GtkKnrMey3YdZWVCCF7Bydz(1); 0CO6n6HkAhvpbw7if8oZjO5SS2rq(1); 0FglGuUGysIhEFmQhad2LQ7vW1Dq(1); 0FpFqXhX3x1W51o3HfOIPLB9TJ2x(1); 0NOXQEkOFh7Cag9UtcWytTB7WsIb(1); 0VTaKPvum7R3sKDtqlg6p5BgLaLl(1); 0VralA4v2odA0qRm1fMD4LXAPkTl(1); 0VxxkIZ9vZ1Ee7YG0aIJBISwKGAJ(1); ...(977) |

## coupon_entered (n=848, id_duplicates: 0)

| field | present | type | distinct values / range |
|---|---|---|---|
| app_version | 100% | string:848 | distinct: 3 (0.4% unique) LC — 7.46.0(299); 7.45.2(277); 7.44.0(272) |
| application_id | 100% | string:848 | distinct: 848 (100% unique) — 00335255518a05dd929416e25e114bfd(1); 009608a6f942c218c3c786972b7e3575(1); 0267bcaf68d15f52e2ca4e10fe916cfb(1); 02f795f87b52dc607955e154b6112f35(1); 0342eebf5ebdb046f5190d7abb4c0028(1); 042ea47e0f4a3bf3d40d59001fdfd76e(1); 04762805d7320a5bb5614bd13975061a(1); 04a208dc7d06e4ea48a9f2b7c08d7674(1); 04a6929a4d081cf8a34b278947f87929(1); 04cf12536bede3fa740e62f8c0cb77c2(1); ...(838) |
| cart_value | 100% | float:848 | distinct: 807 (95.2% unique) — range: [1509.0, 8997.0] |
| city | 100% | string:848 | distinct: 7 (0.8% unique) LC — Mumbai(510); Singapore(88); Dubai(76); New York(56); London(43); Sydney(43); Riyadh(32) |
| client_lib | 100% | string:848 | distinct: 2 (0.2% unique) LC — mobile-rn(701); web-js(147) |
| coupon_code | 100% | string:848 | distinct: 6 (0.7% unique) LC — FREESHIP(155); EXPIRED5(149); SUMMER20(141); ATLYS15(140); FIRST10(140); WELCOME(123) |
| currency | 100% | string:848 | distinct: 7 (0.8% unique) LC — INR(510); SGD(88); AED(76); USD(56); AUD(43); GBP(43); SAR(32) |
| destination | 100% | string:848 | distinct: 14 (1.7% unique) LC — AU(74); ID(67); TH(67); US(66); AE(65); GR(60); EG(59); FR(59); GB(58); SG(58); ...(4) |
| device_type | 100% | string:848 | distinct: 4 (0.5% unique) LC — ios(364); android(264); web-user-b2c(147); Desktop(73) |
| geoip_country_code | 100% | string:848 | distinct: 7 (0.8% unique) LC — IN(510); SG(88); AE(76); US(56); AU(43); GB(43); SA(32) |
| os | 100% (7.3% null) | string:786 | distinct: 4 (0.5% unique) LC — iOS(364); Android(202); Windows(113); Mac OS X(107) |
| user_id | 100% | string:848 | distinct: 848 (100% unique) — 02vIAS8566AckZwQLKqxJ4avrr3J(1); 04uYSx1ak9xsGNzPZk0zSoBqknVC(1); 059nODrWN8dfaKaDPwWYwvUWe6PC(1); 0BX9nQ4o315YStPUiEH98uG6c2dm(1); 0ZmwK9mJz0cOAk0m6j4kQaD30DDm(1); 0bj6pcLxdHAOGKN1tTzk7bZmbY1E(1); 0uIjsjDEpm3zKC04vFMueKZSxTKh(1); 0wMVRLzeWlZuOMznfo898E1wzKue(1); 15sjmewJQ25dFGRgQltQPfGSAqxZ(1); 1HZScxbOoqhWRF386vk0TdAiQOuD(1); ...(838) |

## coupon_applied (n=580, id_duplicates: 0)

| field | present | type | distinct values / range |
|---|---|---|---|
| app_version | 100% | string:580 | distinct: 3 (0.5% unique) LC — 7.46.0(203); 7.45.2(191); 7.44.0(186) |
| application_id | 100% | string:580 | distinct: 580 (100% unique) — 009608a6f942c218c3c786972b7e3575(1); 0267bcaf68d15f52e2ca4e10fe916cfb(1); 02f795f87b52dc607955e154b6112f35(1); 0342eebf5ebdb046f5190d7abb4c0028(1); 042ea47e0f4a3bf3d40d59001fdfd76e(1); 04762805d7320a5bb5614bd13975061a(1); 04a6929a4d081cf8a34b278947f87929(1); 04cf12536bede3fa740e62f8c0cb77c2(1); 04e241263f5f7a2638e20cc8fe174007(1); 0574414d1ccc5abebd91c79b352d6a99(1); ...(570) |
| cart_value | 100% | float:580 | distinct: 565 (97.4% unique) — range: [1546.0, 8997.0] |
| city | 100% | string:580 | distinct: 7 (1.2% unique) LC — Mumbai(361); Singapore(56); Dubai(51); New York(35); London(30); Sydney(26); Riyadh(21) |
| client_lib | 100% | string:580 | distinct: 2 (0.3% unique) LC — mobile-rn(472); web-js(108) |
| coupon_code | 100% | string:580 | distinct: 5 (0.9% unique) LC — FREESHIP(131); SUMMER20(123); FIRST10(118); ATLYS15(112); WELCOME(96) |
| currency | 100% | string:580 | distinct: 7 (1.2% unique) LC — INR(361); SGD(56); AED(51); USD(35); GBP(30); AUD(26); SAR(21) |
| destination | 100% | string:580 | distinct: 14 (2.4% unique) LC — AU(52); GB(46); GR(45); ID(45); JP(45); AE(44); TH(44); US(43); SG(41); MY(39); ...(4) |
| device_type | 100% | string:580 | distinct: 4 (0.7% unique) LC — ios(254); android(174); web-user-b2c(108); Desktop(44) |
| discount_amount | 100% | int:227, float:353 | distinct: 319 (55.0% unique) — range: [0, 1793.0] |
| discount_type | 100% | string:580 | distinct: 2 (0.3% unique) LC — percent(353); flat(227) |
| geoip_country_code | 100% | string:580 | distinct: 7 (1.2% unique) LC — IN(361); SG(56); AE(51); US(35); GB(30); AU(26); SA(21) |
| os | 100% (7.4% null) | string:537 | distinct: 4 (0.7% unique) LC — iOS(254); Android(131); Windows(80); Mac OS X(72) |
| user_id | 100% | string:580 | distinct: 580 (100% unique) — 02vIAS8566AckZwQLKqxJ4avrr3J(1); 04uYSx1ak9xsGNzPZk0zSoBqknVC(1); 0BX9nQ4o315YStPUiEH98uG6c2dm(1); 0ZmwK9mJz0cOAk0m6j4kQaD30DDm(1); 0bj6pcLxdHAOGKN1tTzk7bZmbY1E(1); 0uIjsjDEpm3zKC04vFMueKZSxTKh(1); 15sjmewJQ25dFGRgQltQPfGSAqxZ(1); 1HZScxbOoqhWRF386vk0TdAiQOuD(1); 1JE1Wqfnq7l4s2MIkyygZwoA6k2y(1); 1MAo5X1H189VkuHMG59nkXAPF22L(1); ...(570) |

## discount_shown (n=580, id_duplicates: 0)

| field | present | type | distinct values / range |
|---|---|---|---|
| app_version | 100% | string:580 | distinct: 3 (0.5% unique) LC — 7.46.0(203); 7.45.2(191); 7.44.0(186) |
| application_id | 100% | string:580 | distinct: 580 (100% unique) — 009608a6f942c218c3c786972b7e3575(1); 0267bcaf68d15f52e2ca4e10fe916cfb(1); 02f795f87b52dc607955e154b6112f35(1); 0342eebf5ebdb046f5190d7abb4c0028(1); 042ea47e0f4a3bf3d40d59001fdfd76e(1); 04762805d7320a5bb5614bd13975061a(1); 04a6929a4d081cf8a34b278947f87929(1); 04cf12536bede3fa740e62f8c0cb77c2(1); 04e241263f5f7a2638e20cc8fe174007(1); 0574414d1ccc5abebd91c79b352d6a99(1); ...(570) |
| cart_value | 100% | float:580 | distinct: 565 (97.4% unique) — range: [1546.0, 8997.0] |
| city | 100% | string:580 | distinct: 7 (1.2% unique) LC — Mumbai(361); Singapore(56); Dubai(51); New York(35); London(30); Sydney(26); Riyadh(21) |
| client_lib | 100% | string:580 | distinct: 2 (0.3% unique) LC — mobile-rn(472); web-js(108) |
| coupon_code | 100% | string:580 | distinct: 5 (0.9% unique) LC — FREESHIP(131); SUMMER20(123); FIRST10(118); ATLYS15(112); WELCOME(96) |
| currency | 100% | string:580 | distinct: 7 (1.2% unique) LC — INR(361); SGD(56); AED(51); USD(35); GBP(30); AUD(26); SAR(21) |
| destination | 100% | string:580 | distinct: 14 (2.4% unique) LC — AU(52); GB(46); GR(45); ID(45); JP(45); AE(44); TH(44); US(43); SG(41); MY(39); ...(4) |
| device_type | 100% | string:580 | distinct: 4 (0.7% unique) LC — ios(254); android(174); web-user-b2c(108); Desktop(44) |
| discount_amount | 100% | int:227, float:353 | distinct: 319 (55.0% unique) — range: [0, 1793.0] |
| geoip_country_code | 100% | string:580 | distinct: 7 (1.2% unique) LC — IN(361); SG(56); AE(51); US(35); GB(30); AU(26); SA(21) |
| os | 100% (7.4% null) | string:537 | distinct: 4 (0.7% unique) LC — iOS(254); Android(131); Windows(80); Mac OS X(72) |
| user_id | 100% | string:580 | distinct: 580 (100% unique) — 02vIAS8566AckZwQLKqxJ4avrr3J(1); 04uYSx1ak9xsGNzPZk0zSoBqknVC(1); 0BX9nQ4o315YStPUiEH98uG6c2dm(1); 0ZmwK9mJz0cOAk0m6j4kQaD30DDm(1); 0bj6pcLxdHAOGKN1tTzk7bZmbY1E(1); 0uIjsjDEpm3zKC04vFMueKZSxTKh(1); 15sjmewJQ25dFGRgQltQPfGSAqxZ(1); 1HZScxbOoqhWRF386vk0TdAiQOuD(1); 1JE1Wqfnq7l4s2MIkyygZwoA6k2y(1); 1MAo5X1H189VkuHMG59nkXAPF22L(1); ...(570) |

## coupon_rejected (n=268, id_duplicates: 0)

| field | present | type | distinct values / range |
|---|---|---|---|
| app_version | 100% | string:268 | distinct: 3 (1.1% unique) LC — 7.46.0(96); 7.44.0(86); 7.45.2(86) |
| application_id | 100% | string:268 | distinct: 268 (100% unique) — 00335255518a05dd929416e25e114bfd(1); 04a208dc7d06e4ea48a9f2b7c08d7674(1); 0639edb35d0937c303346add40b8ec1c(1); 06570cbb48f15bb0a3a83e0912718bdc(1); 06ab119084a974ce6263bfbf6b250156(1); 06ea651c6623660c647d16829af060f0(1); 081b4adaa1778ff4ae8bdc2524c7f5bd(1); 0b873b938cb1dd159ac52ef3e419edd7(1); 0bf69a03ebf5972a18dcf3cc03a7dd8c(1); 0c8aa31deb5a0e7d8dc6df217684e9e0(1); ...(258) |
| cart_value | 100% | float:268 | distinct: 261 (97.4% unique) — range: [1509.0, 8973.0] |
| city | 100% | string:268 | distinct: 7 (2.6% unique) LC — Mumbai(149); Singapore(32); Dubai(25); New York(21); Sydney(17); London(13); Riyadh(11) |
| client_lib | 100% | string:268 | distinct: 2 (0.7% unique) LC — mobile-rn(229); web-js(39) |
| coupon_code | 100% | string:268 | distinct: 6 (2.2% unique) LC — EXPIRED5(149); ATLYS15(28); WELCOME(27); FREESHIP(24); FIRST10(22); SUMMER20(18) |
| currency | 100% | string:268 | distinct: 7 (2.6% unique) LC — INR(149); SGD(32); AED(25); USD(21); AUD(17); GBP(13); SAR(11) |
| destination | 100% | string:268 | distinct: 14 (5.2% unique) LC — EG(23); TH(23); TR(23); US(23); AU(22); ID(22); AE(21); FR(21); VN(20); SG(17); ...(4) |
| device_type | 100% | string:268 | distinct: 4 (1.5% unique) LC — ios(110); android(90); web-user-b2c(39); Desktop(29) |
| geoip_country_code | 100% | string:268 | distinct: 7 (2.6% unique) LC — IN(149); SG(32); AE(25); US(21); AU(17); GB(13); SA(11) |
| os | 100% (7.1% null) | string:249 | distinct: 4 (1.5% unique) LC — iOS(110); Android(71); Mac OS X(35); Windows(33) |
| reject_reason | 100% | string:268 | distinct: 4 (1.5% unique) LC — min_cart_not_met(80); already_used(75); expired(60); invalid_code(53) |
| user_id | 100% | string:268 | distinct: 268 (100% unique) — 059nODrWN8dfaKaDPwWYwvUWe6PC(1); 0wMVRLzeWlZuOMznfo898E1wzKue(1); 1ewgCmg6QlRBqREHwN0nyZAwkx76(1); 1h0md2a8ETtpmCRUoAfwldhWBWEl(1); 1hqzjsyiOJ9y2IFsFfugynuio9GY(1); 1n1MHiFdYcy1ogTqJCVIIbEcghBH(1); 2LKZDPDIUWkolhuwTqJWg16Dr4e0(1); 2cPLYnqVOqtUufeMr7QfKzm6AqYN(1); 2d7koCGswt6bXyQYXIGMJ7kIiFLs(1); 2pUOAz7QQCDoDzn1yt0obnjVKsor(1); ...(258) |

## Field × Event Grid

| field | CFS | CWC | CE | CA | DS | CR |
|---|---|---|---|---|---|---|
| app_version | yes | yes | yes | yes | yes | yes |
| application_id | yes | yes | yes | yes | yes | yes |
| cart_value | yes | yes | yes | yes | yes | yes |
| city | yes | yes | yes | yes | yes | yes |
| client_lib | yes | yes | yes | yes | yes | yes |
| currency | yes | yes | yes | yes | yes | yes |
| destination | yes | yes | yes | yes | yes | yes |
| device_type | yes | yes | yes | yes | yes | yes |
| geoip_country_code | yes | yes | yes | yes | yes | yes |
| os | yes | yes | yes | yes | yes | yes |
| user_id | yes | yes | yes | yes | yes | yes |
| coupon_code | no | yes | yes | yes | yes | yes |
| discount_amount | no | yes | no | yes | yes | no |
| discount_type | no | no | no | yes | no | no |
| final_value | no | yes | no | no | no | no |
| reject_reason | no | no | no | no | no | yes |

**Legend:** CFS=coupon_field_shown; CWC=checkout_with_coupon; CE=coupon_entered; CA=coupon_applied; DS=discount_shown; CR=coupon_rejected

