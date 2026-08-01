# Event Profile — rows: 5453, parse_errors: 0, duplicate_ids: 0, unparseable_timestamps: 0, time_span: 2026-06-08T06:01:00+00:00 to 2026-06-28T23:10:00+00:00

## Event Type Counts

| event | rows |
|---|---|
| traveller_added | 3495 |
| group_started | 1200 |
| group_submitted | 688 |
| traveller_removed | 70 |

## traveller_added (n=3495, id_duplicates: 0)

| field | present | type | distinct values / range |
|---|---|---|---|
| app_version | 100% | string:3495 | distinct: 3 (0.1% unique) LC — 7.45.2(1199); 7.46.0(1162); 7.44.0(1134) |
| application_id | 100% | string:3495 | distinct: 1200 (34.3% unique) — (>1000 distinct, omitted) |
| city | 100% | string:3495 | distinct: 7 (0.2% unique) LC — Mumbai(2097); Dubai(351); Singapore(343); London(192); Sydney(181); New York(172); Riyadh(159) |
| client_lib | 100% | string:3495 | distinct: 2 (0.1% unique) LC — mobile-rn(2837); web-js(658) |
| destination | 100% | string:3495 | distinct: 14 (0.4% unique) LC — MY(317); TH(310); US(288); TR(274); EG(261); AE(260); ID(246); GB(237); SG(236); FR(232); ...(4) |
| device_type | 100% | string:3495 | distinct: 4 (0.1% unique) LC — ios(1441); android(1137); web-user-b2c(658); Desktop(259) |
| docs_complete | 100% | bool:3495 | distinct: 2 (0.1% unique) — true(2795); false(700) |
| geoip_country_code | 100% | string:3495 | distinct: 7 (0.2% unique) LC — IN(2097); AE(351); SG(343); GB(192); AU(181); US(172); SA(159) |
| group_id | 100% | string:3495 | distinct: 1200 (34.3% unique) — (>1000 distinct, omitted) |
| group_size | 100% | int:3495 | distinct: 5 (0.1% unique) — range: [2, 6] |
| os | 100% (6.3% null) | string:3274 | distinct: 4 (0.1% unique) LC — iOS(1441); Android(916); Windows(476); Mac OS X(441) |
| relation | 100% | string:3495 | distinct: 5 (0.1% unique) LC — friend(727); spouse(712); child(708); sibling(707); parent(641) |
| traveller_index | 100% | int:3495 | distinct: 6 (0.2% unique) — range: [0, 5] |
| user_id | 100% | string:3495 | distinct: 1200 (34.3% unique) — (>1000 distinct, omitted) |

## group_started (n=1200, id_duplicates: 0)

| field | present | type | distinct values / range |
|---|---|---|---|
| app_version | 100% | string:1200 | distinct: 3 (0.2% unique) LC — 7.45.2(409); 7.44.0(398); 7.46.0(393) |
| application_id | 100% | string:1200 | distinct: 1200 (100% unique) — (>1000 distinct, omitted) |
| city | 100% | string:1200 | distinct: 7 (0.6% unique) LC — Mumbai(726); Dubai(121); Singapore(118); London(68); Sydney(59); New York(58); Riyadh(50) |
| client_lib | 100% | string:1200 | distinct: 2 (0.2% unique) LC — mobile-rn(969); web-js(231) |
| destination | 100% | string:1200 | distinct: 14 (1.2% unique) LC — TH(112); MY(103); US(100); TR(89); AE(88); EG(87); GB(87); ID(82); FR(81); SG(77); ...(4) |
| device_type | 100% | string:1200 | distinct: 4 (0.3% unique) LC — ios(484); android(395); web-user-b2c(231); Desktop(90) |
| geoip_country_code | 100% | string:1200 | distinct: 7 (0.6% unique) LC — IN(726); AE(121); SG(118); GB(68); AU(59); US(58); SA(50) |
| group_id | 100% | string:1200 | distinct: 1200 (100% unique) — (>1000 distinct, omitted) |
| group_size | 100% | int:1200 | distinct: 5 (0.4% unique) — range: [2, 6] |
| os | 100% (6.3% null) | string:1124 | distinct: 4 (0.3% unique) LC — iOS(484); Android(319); Windows(162); Mac OS X(159) |
| user_id | 100% | string:1200 | distinct: 1200 (100% unique) — (>1000 distinct, omitted) |

## group_submitted (n=688, id_duplicates: 0)

| field | present | type | distinct values / range |
|---|---|---|---|
| app_version | 100% | string:688 | distinct: 3 (0.4% unique) LC — 7.45.2(244); 7.46.0(228); 7.44.0(216) |
| application_id | 100% | string:688 | distinct: 688 (100% unique) — 007b4af7f2f0a42e11cfc48e8d04f37a(1); 00e3be06458aed2b54ac9cce8bf5b7c9(1); 01c25577167f1c13b25b67d003ff3c54(1); 02104176199aae8553b180a62fbfd8db(1); 021dcfb4b68f2a6297de37722c697f91(1); 023a7cc341d169a6318054a1b5a6fd48(1); 02884c2f16c9e644d7572734798029c2(1); 028df7d0bd74821b7fd05bee83904d87(1); 0291eb0ae58ce8ab55817e2560e23e06(1); 0350698943cfa54479f28686692bdac5(1); ...(678) |
| city | 100% | string:688 | distinct: 7 (1.0% unique) LC — Mumbai(419); Dubai(73); Singapore(64); London(35); Riyadh(33); New York(32); Sydney(32) |
| client_lib | 100% | string:688 | distinct: 2 (0.3% unique) LC — mobile-rn(558); web-js(130) |
| destination | 100% | string:688 | distinct: 14 (2.0% unique) LC — MY(57); TH(57); GB(53); ID(53); EG(52); US(52); TR(50); FR(49); SG(48); AE(47); ...(4) |
| device_type | 100% | string:688 | distinct: 4 (0.6% unique) LC — ios(271); android(234); web-user-b2c(130); Desktop(53) |
| geoip_country_code | 100% | string:688 | distinct: 7 (1.0% unique) LC — IN(419); AE(73); SG(64); GB(35); SA(33); AU(32); US(32) |
| group_id | 100% | string:688 | distinct: 688 (100% unique) — 0061a57cf3164ee203747d0438adb47f(1); 00ef2fa748125f9a7769b2910b98952b(1); 018f1b5ee57945790c1ba41e7134e96d(1); 01fcc5eda51d04f29167716814ba6112(1); 02191812b9a52f609cedcb6e77c494b9(1); 02604a21f4aaebe1d9ead0f83f4cbc84(1); 0278a87664427554783639e500157d54(1); 02901220b6a7f7cb67abc9876c42d805(1); 02b497cd313873de785e8bd20bf3eead(1); 02c378726c8d6945064fb655498c10b7(1); ...(678) |
| group_size | 100% | int:688 | distinct: 5 (0.7% unique) — range: [2, 6] |
| os | 100% (6.5% null) | string:643 | distinct: 4 (0.6% unique) LC — iOS(271); Android(189); Windows(94); Mac OS X(89) |
| travellers_submitted | 100% | int:688 | distinct: 6 (0.9% unique) — range: [1, 6] |
| user_id | 100% | string:688 | distinct: 688 (100% unique) — 08XPyMerzcBikSv3RkbZ8L7HyJzJ(1); 0BIkTIXo9MyuPWe4dVxYcWdnFHu2(1); 0L9qe14YE8y3nnFZRGB6kPcD2I5G(1); 0LaiAVNL00nPObb684zWvGpspRAr(1); 0NT6zdB2oBU5Ncl4pgbSmiPhG7RW(1); 0OhxOwGGRJu3ORdtPxvWCfxlrDeF(1); 0Zr4xGcQrS2q4vi1RUCXGxsab6Rj(1); 0avp5WAZIbR3nb7dSCwSkKPXZYhe(1); 0ffQUXRvFdiMyuGvmw2JwGsETQsp(1); 0saBwtX8CR7RgXDykcqBEGqdRXm0(1); ...(678) |

## traveller_removed (n=70, id_duplicates: 0)

| field | present | type | distinct values / range |
|---|---|---|---|
| app_version | 100% | string:70 | distinct: 3 (4.3% unique) LC — 7.44.0(30); 7.46.0(25); 7.45.2(15) |
| application_id | 100% | string:70 | distinct: 69 (98.6% unique) — 021dcfb4b68f2a6297de37722c697f91(2); 063cb520bb2410ef056823887425ae5e(1); 0a4ad688a0302a0d65538842b5e616af(1); 104176841df700fdc1293f8334a8787e(1); 188bd6f006a3f7dc79a96543c2e5608d(1); 1c34cb16d6780e900f44a159a92eaeaf(1); 1dd13742e269a650ceeca23b84226c76(1); 232bc398cb33a05f19693f4d0a2365bb(1); 2da99012082cc66c368fd201bba2d9b9(1); 308c371d6417492f3955767080cef298(1); ...(59) |
| city | 100% | string:70 | distinct: 7 (10% unique) LC — Mumbai(41); Dubai(7); Singapore(6); Sydney(6); New York(4); Riyadh(4); London(2) |
| client_lib | 100% | string:70 | distinct: 2 (2.9% unique) LC — mobile-rn(57); web-js(13) |
| destination | 100% | string:70 | distinct: 14 (20% unique) — TH(9); AU(7); EG(7); ID(7); AE(6); JP(6); TR(5); FR(4); GB(4); SG(4); ...(4) |
| device_type | 100% | string:70 | distinct: 4 (5.7% unique) LC — ios(29); android(21); web-user-b2c(13); Desktop(7) |
| geoip_country_code | 100% | string:70 | distinct: 7 (10% unique) LC — IN(41); AE(7); AU(6); SG(6); SA(4); US(4); GB(2) |
| group_id | 100% | string:70 | distinct: 69 (98.6% unique) — aaa29d595778f3fe8a13e2cef2fc454f(2); 02ad1485c12711ef3622fae099c667c9(1); 094cccce6bdb73809df9aa44b0d0be30(1); 0a9aa8c42a4506b5608ff10ba0705ef6(1); 0c7e578ae659440b68dd5124ae84a525(1); 163406d00357ea8f54ed682fdc3be365(1); 1e8ee24d710a00baafc3524ac6c0d61a(1); 21efc6d377f1cd108526e16a38993419(1); 2219a836c1ae0d0c46c3bc475bee8aba(1); 28ef98cc1e679dafaff5302eff94a4cb(1); ...(59) |
| group_size | 100% | int:70 | distinct: 5 (7.1% unique) — range: [2, 6] |
| os | 100% (4.3% null) | string:67 | distinct: 4 (5.7% unique) LC — iOS(29); Android(18); Mac OS X(12); Windows(8) |
| traveller_index | 100% | int:70 | distinct: 6 (8.6% unique) — range: [0, 5] |
| user_id | 100% | string:70 | distinct: 69 (98.6% unique) — FtE340IwZiAQ8Zn70o8LBS0q1oUQ(2); 0avp5WAZIbR3nb7dSCwSkKPXZYhe(1); 2aCZIahED0wVAtV4XvaNWMJvYbiT(1); 3eJlAcc9QOgFbPCOECfkWllBlCVl(1); 44g7OsEGMDSukPKnkUNHg7DeWqJq(1); 4mr0kCZU6vv6UfsghGMFVvi3TTVP(1); 4wTNkl7SUZcTViLQsfMv49QDE1Gb(1); 7uAUl3nVk4jENHXucC6gbc2uhTZb(1); 7xLUYsOTS3mBottSwhhhLqGgrx0D(1); AW0L0A539lqw6J82ukcp9Y0Tt5Lj(1); ...(59) |

## Field × Event Grid

| field | TA | GS | GS2 | TR |
|---|---|---|---|---|
| app_version | yes | yes | yes | yes |
| application_id | yes | yes | yes | yes |
| city | yes | yes | yes | yes |
| client_lib | yes | yes | yes | yes |
| destination | yes | yes | yes | yes |
| device_type | yes | yes | yes | yes |
| geoip_country_code | yes | yes | yes | yes |
| group_id | yes | yes | yes | yes |
| group_size | yes | yes | yes | yes |
| os | yes | yes | yes | yes |
| user_id | yes | yes | yes | yes |
| traveller_index | yes | no | no | yes |
| docs_complete | yes | no | no | no |
| relation | yes | no | no | no |
| travellers_submitted | no | no | yes | no |

**Legend:** TA=traveller_added; GS=group_started; GS2=group_submitted; TR=traveller_removed

