# Event Profile — rows: 6503, parse_errors: 0, duplicate_ids: 0, unparseable_timestamps: 0, time_span: 2026-06-08T06:00:00+00:00 to 2026-07-01T09:21:00+00:00

## Event Type Counts

| event | rows |
|---|---|
| link_opened | 2310 |
| share_clicked | 1600 |
| channel_selected | 1144 |
| link_generated | 1144 |
| recipient_cta_clicked | 305 |

## link_opened (n=2310, id_duplicates: 0)

| field | present | type | distinct values / range |
|---|---|---|---|
| channel | 100% | string:2310 | distinct: 4 (0.2% unique) LC — whatsapp(1273); copy_link(423); email(396); sms(218) |
| destination | 100% | string:2310 | distinct: 14 (0.6% unique) LC — AU(223); VN(187); TH(175); GB(173); AE(171); FR(170); GR(167); TR(166); ID(162); MY(156); ...(4) |
| recipient_is_new_user | 100% | bool:2310 | distinct: 2 (0.1% unique) — true(1390); false(920) |
| share_id | 100% | string:2310 | distinct: 922 (39.9% unique) — 001a9ac88db527d278975b558d82eb08(4); 003ac519c8d331e78924b96965a5ff60(4); 0066880d897ed3194e4ea258b3457856(4); 0088c826486292c65d9ffa63970b1f9c(4); 0154b12ad94cb45f415dbccf568c16d0(4); 01fcf7102f8c302883bac6edaa7fd291(4); 04f36690969ee4cd8736853c06ddb85b(4); 0513d19a67aff4166ce0c4d8608451b7(4); 05fd30bbf4d449b97255f950340f7aa2(4); 071d473aebf8b476a766d5f12bedb514(4); ...(912) |

## share_clicked (n=1600, id_duplicates: 0)

| field | present | type | distinct values / range |
|---|---|---|---|
| app_version | 100% | string:1600 | distinct: 3 (0.2% unique) LC — 7.46.0(537); 7.45.2(532); 7.44.0(531) |
| application_id | 100% | string:1600 | distinct: 1600 (100% unique) — (>1000 distinct, omitted) |
| city | 100% | string:1600 | distinct: 7 (0.4% unique) LC — Mumbai(956); Singapore(170); Dubai(157); New York(92); London(79); Sydney(78); Riyadh(68) |
| client_lib | 100% | string:1600 | distinct: 2 (0.1% unique) LC — mobile-rn(1306); web-js(294) |
| destination | 100% | string:1600 | distinct: 14 (0.9% unique) LC — AU(147); TR(126); MY(124); ID(121); GR(120); EG(118); VN(118); AE(117); GB(113); TH(112); ...(4) |
| device_type | 100% | string:1600 | distinct: 4 (0.2% unique) LC — ios(682); android(522); web-user-b2c(294); Desktop(102) |
| geoip_country_code | 100% | string:1600 | distinct: 7 (0.4% unique) LC — IN(956); SG(170); AE(157); US(92); GB(79); AU(78); SA(68) |
| os | 100% (5.6% null) | string:1511 | distinct: 4 (0.2% unique) LC — iOS(682); Android(433); Windows(206); Mac OS X(190) |
| share_id | 100% | string:1600 | distinct: 1600 (100% unique) — (>1000 distinct, omitted) |
| status_shared | 100% | string:1600 | distinct: 3 (0.2% unique) LC — submitted(562); processing(525); approved(513) |
| user_id | 100% | string:1600 | distinct: 1600 (100% unique) — (>1000 distinct, omitted) |

## channel_selected (n=1144, id_duplicates: 0)

| field | present | type | distinct values / range |
|---|---|---|---|
| app_version | 100% | string:1144 | distinct: 3 (0.3% unique) LC — 7.44.0(386); 7.45.2(381); 7.46.0(377) |
| application_id | 100% | string:1144 | distinct: 1144 (100% unique) — (>1000 distinct, omitted) |
| channel | 100% | string:1144 | distinct: 4 (0.3% unique) LC — whatsapp(625); copy_link(214); email(194); sms(111) |
| city | 100% | string:1144 | distinct: 7 (0.6% unique) LC — Mumbai(687); Dubai(118); Singapore(118); New York(66); Sydney(54); London(51); Riyadh(50) |
| client_lib | 100% | string:1144 | distinct: 2 (0.2% unique) LC — mobile-rn(935); web-js(209) |
| destination | 100% | string:1144 | distinct: 14 (1.2% unique) LC — AU(109); TH(90); AE(89); VN(89); ID(85); FR(82); GB(81); TR(81); MY(80); GR(79); ...(4) |
| device_type | 100% | string:1144 | distinct: 4 (0.3% unique) LC — ios(499); android(365); web-user-b2c(209); Desktop(71) |
| geoip_country_code | 100% | string:1144 | distinct: 7 (0.6% unique) LC — IN(687); AE(118); SG(118); US(66); AU(54); GB(51); SA(50) |
| os | 100% (5.1% null) | string:1086 | distinct: 4 (0.3% unique) LC — iOS(499); Android(307); Windows(143); Mac OS X(137) |
| share_id | 100% | string:1144 | distinct: 1144 (100% unique) — (>1000 distinct, omitted) |
| status_shared | 100% | string:1144 | distinct: 3 (0.3% unique) LC — submitted(394); processing(385); approved(365) |
| user_id | 100% | string:1144 | distinct: 1144 (100% unique) — (>1000 distinct, omitted) |

## link_generated (n=1144, id_duplicates: 0)

| field | present | type | distinct values / range |
|---|---|---|---|
| app_version | 100% | string:1144 | distinct: 3 (0.3% unique) LC — 7.44.0(386); 7.45.2(381); 7.46.0(377) |
| application_id | 100% | string:1144 | distinct: 1144 (100% unique) — (>1000 distinct, omitted) |
| channel | 100% | string:1144 | distinct: 4 (0.3% unique) LC — whatsapp(625); copy_link(214); email(194); sms(111) |
| city | 100% | string:1144 | distinct: 7 (0.6% unique) LC — Mumbai(687); Dubai(118); Singapore(118); New York(66); Sydney(54); London(51); Riyadh(50) |
| client_lib | 100% | string:1144 | distinct: 2 (0.2% unique) LC — mobile-rn(935); web-js(209) |
| destination | 100% | string:1144 | distinct: 14 (1.2% unique) LC — AU(109); TH(90); AE(89); VN(89); ID(85); FR(82); GB(81); TR(81); MY(80); GR(79); ...(4) |
| device_type | 100% | string:1144 | distinct: 4 (0.3% unique) LC — ios(499); android(365); web-user-b2c(209); Desktop(71) |
| geoip_country_code | 100% | string:1144 | distinct: 7 (0.6% unique) LC — IN(687); AE(118); SG(118); US(66); AU(54); GB(51); SA(50) |
| os | 100% (5.1% null) | string:1086 | distinct: 4 (0.3% unique) LC — iOS(499); Android(307); Windows(143); Mac OS X(137) |
| share_id | 100% | string:1144 | distinct: 1144 (100% unique) — (>1000 distinct, omitted) |
| status_shared | 100% | string:1144 | distinct: 3 (0.3% unique) LC — submitted(394); processing(385); approved(365) |
| user_id | 100% | string:1144 | distinct: 1144 (100% unique) — (>1000 distinct, omitted) |

## recipient_cta_clicked (n=305, id_duplicates: 0)

| field | present | type | distinct values / range |
|---|---|---|---|
| cta | 100% | string:305 | distinct: 1 (0.3% unique) LC — start_own_application(305) |
| destination | 100% | string:305 | distinct: 14 (4.6% unique) LC — AE(28); FR(26); TH(26); AU(24); TR(24); VN(23); MY(22); GR(21); ID(21); EG(20); ...(4) |
| share_id | 100% | string:305 | distinct: 263 (86.2% unique) — c06c3e570e4eaaaa93d293904ee0c941(3); c7200904e06dafedf7f37df5bbddbe52(3); f297f579d1c00182ad218d2c74f70d00(3); 0066880d897ed3194e4ea258b3457856(2); 0067a0a2e8014bc1b7a50a0f7292d6ba(2); 0511bd30e9d72f67d2e6eeb52b08b1b0(2); 061725c158e558ac2fda94bafd206eb8(2); 1a78df1736fe0b774d631c0993e43baf(2); 1b7b94973c498781c51d83d113e31499(2); 2a82925cad1d33b89a40ef73d63f3ab4(2); ...(253) |

## Field × Event Grid

| field | LO | SC | CS | LG | RCC |
|---|---|---|---|---|---|
| destination | yes | yes | yes | yes | yes |
| share_id | yes | yes | yes | yes | yes |
| app_version | no | yes | yes | yes | no |
| application_id | no | yes | yes | yes | no |
| channel | yes | no | yes | yes | no |
| city | no | yes | yes | yes | no |
| client_lib | no | yes | yes | yes | no |
| device_type | no | yes | yes | yes | no |
| geoip_country_code | no | yes | yes | yes | no |
| os | no | yes | yes | yes | no |
| status_shared | no | yes | yes | yes | no |
| user_id | no | yes | yes | yes | no |
| cta | no | no | no | no | yes |
| recipient_is_new_user | yes | no | no | no | no |

**Legend:** LO=link_opened; SC=share_clicked; CS=channel_selected; LG=link_generated; RCC=recipient_cta_clicked

