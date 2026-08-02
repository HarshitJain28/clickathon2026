# Event Profile — rows: 5919, parse_errors: 0, duplicate_ids: 0, unparseable_timestamps: 0, time_span: 2026-06-08T06:01:00+00:00 to 2026-07-01T00:00:00+00:00

## Event Type Counts

| event | rows |
|---|---|
| abandonment_detected | 2300 |
| reminder_sent | 2300 |
| reminder_opened | 690 |
| reminder_cta_clicked | 268 |
| resumed_at_step | 268 |
| reconverted | 93 |

## abandonment_detected (n=2300, id_duplicates: 0)

| field | present | type | distinct values / range |
|---|---|---|---|
| app_version | 100% | string:2300 | distinct: 3 (0.1% unique) LC — 7.46.0(787); 7.45.2(772); 7.44.0(741) |
| application_id | 100% | string:2300 | distinct: 2300 (100% unique) — (>1000 distinct, omitted) |
| city | 100% | string:2300 | distinct: 7 (0.3% unique) LC — Mumbai(1390); Dubai(239); Singapore(222); New York(154); London(113); Sydney(102); Riyadh(80) |
| client_lib | 100% | string:2300 | distinct: 2 (0.1% unique) LC — mobile-rn(1884); web-js(416) |
| destination | 100% | string:2300 | distinct: 14 (0.6% unique) LC — AU(191); JP(181); SG(175); EG(172); MY(170); TH(169); TR(168); GB(166); ID(166); AE(163); ...(4) |
| device_type | 100% | string:2300 | distinct: 4 (0.2% unique) LC — ios(971); android(745); web-user-b2c(416); Desktop(168) |
| drop_step | 100% | string:2300 | distinct: 4 (0.2% unique) LC — document_uploaded(696); destination_card_clicked(686); application_started(521); pay_now_clicked(397) |
| geoip_country_code | 100% | string:2300 | distinct: 7 (0.3% unique) LC — IN(1390); AE(239); SG(222); US(154); GB(113); AU(102); SA(80) |
| os | 100% (5.1% null) | string:2182 | distinct: 4 (0.2% unique) LC — iOS(971); Android(627); Windows(297); Mac OS X(287) |
| user_id | 100% | string:2300 | distinct: 2300 (100% unique) — (>1000 distinct, omitted) |

## reminder_sent (n=2300, id_duplicates: 0)

| field | present | type | distinct values / range |
|---|---|---|---|
| app_version | 100% | string:2300 | distinct: 3 (0.1% unique) LC — 7.46.0(787); 7.45.2(772); 7.44.0(741) |
| application_id | 100% | string:2300 | distinct: 2300 (100% unique) — (>1000 distinct, omitted) |
| channel | 100% | string:2300 | distinct: 3 (0.1% unique) LC — push(1138); email(678); whatsapp(484) |
| city | 100% | string:2300 | distinct: 7 (0.3% unique) LC — Mumbai(1390); Dubai(239); Singapore(222); New York(154); London(113); Sydney(102); Riyadh(80) |
| client_lib | 100% | string:2300 | distinct: 2 (0.1% unique) LC — mobile-rn(1884); web-js(416) |
| destination | 100% | string:2300 | distinct: 14 (0.6% unique) LC — AU(191); JP(181); SG(175); EG(172); MY(170); TH(169); TR(168); GB(166); ID(166); AE(163); ...(4) |
| device_type | 100% | string:2300 | distinct: 4 (0.2% unique) LC — ios(971); android(745); web-user-b2c(416); Desktop(168) |
| drop_step | 100% | string:2300 | distinct: 4 (0.2% unique) LC — document_uploaded(696); destination_card_clicked(686); application_started(521); pay_now_clicked(397) |
| geoip_country_code | 100% | string:2300 | distinct: 7 (0.3% unique) LC — IN(1390); AE(239); SG(222); US(154); GB(113); AU(102); SA(80) |
| hours_since_drop | 100% | int:2300 | distinct: 5 (0.2% unique) — range: [1, 48] |
| os | 100% (5.1% null) | string:2182 | distinct: 4 (0.2% unique) LC — iOS(971); Android(627); Windows(297); Mac OS X(287) |
| user_id | 100% | string:2300 | distinct: 2300 (100% unique) — (>1000 distinct, omitted) |

## reminder_opened (n=690, id_duplicates: 0)

| field | present | type | distinct values / range |
|---|---|---|---|
| app_version | 100% | string:690 | distinct: 3 (0.4% unique) LC — 7.46.0(243); 7.45.2(228); 7.44.0(219) |
| application_id | 100% | string:690 | distinct: 690 (100% unique) — 00d02b249e5f33b98d9fe85dcb335f95(1); 00e56bc6fd5c0482d0703b0dc4c21a90(1); 012f1e195193a77da0e5d38c445ae607(1); 01309d418942dc35799294996b8ff4b4(1); 01590455081edb166c8042caa447d0fe(1); 018fef685c2dc3cc253d896768680aec(1); 019c4c24b1569122f70854aa22f35855(1); 0312268884a6342f7f87c6272d9785db(1); 0349f15e94d8d781c5e26cbdb3c6d230(1); 034cf47c070a8f76804a4a55403f8e7b(1); ...(680) |
| channel | 100% | string:690 | distinct: 3 (0.4% unique) LC — push(322); whatsapp(224); email(144) |
| city | 100% | string:690 | distinct: 7 (1.0% unique) LC — Mumbai(413); Dubai(68); Singapore(62); Sydney(49); New York(40); London(37); Riyadh(21) |
| client_lib | 100% | string:690 | distinct: 2 (0.3% unique) LC — mobile-rn(571); web-js(119) |
| destination | 100% | string:690 | distinct: 14 (2.0% unique) LC — AU(66); TH(56); TR(55); US(55); MY(54); JP(52); AE(49); GR(48); EG(47); SG(47); ...(4) |
| device_type | 100% | string:690 | distinct: 4 (0.6% unique) LC — ios(313); android(211); web-user-b2c(119); Desktop(47) |
| drop_step | 100% | string:690 | distinct: 4 (0.6% unique) LC — document_uploaded(220); destination_card_clicked(179); application_started(161); pay_now_clicked(130) |
| geoip_country_code | 100% | string:690 | distinct: 7 (1.0% unique) LC — IN(413); AE(68); SG(62); AU(49); US(40); GB(37); SA(21) |
| os | 100% (4.9% null) | string:656 | distinct: 4 (0.6% unique) LC — iOS(313); Android(177); Windows(84); Mac OS X(82) |
| user_id | 100% | string:690 | distinct: 690 (100% unique) — 075J04YW5KDOav620kciCqfEU02s(1); 0JwPYT8jw0hbiAfQUBv35Q34rLnm(1); 0OTnBhzg4hSgdX58f3uxYQchxx95(1); 0QFKdkYs7dW8wv2md4LuH5Qns5D9(1); 0XepBSBJygAf6qrXM7avig5ZRAnS(1); 0f4GrDPOKXaBUEFTEyb5cW4guEr3(1); 0gH6Q8yeiomTqxsJAixASxfFQEli(1); 0iZs4qg13H4rrypjMaFpFaZPvyQu(1); 0lYYPsydAsIb9xbQ7TKduiBjMmDP(1); 11vZ4iPJUwB5jlApTp7DztcFdlVW(1); ...(680) |

## reminder_cta_clicked (n=268, id_duplicates: 0)

| field | present | type | distinct values / range |
|---|---|---|---|
| app_version | 100% | string:268 | distinct: 3 (1.1% unique) LC — 7.45.2(101); 7.46.0(84); 7.44.0(83) |
| application_id | 100% | string:268 | distinct: 268 (100% unique) — 00d02b249e5f33b98d9fe85dcb335f95(1); 00e56bc6fd5c0482d0703b0dc4c21a90(1); 018fef685c2dc3cc253d896768680aec(1); 019c4c24b1569122f70854aa22f35855(1); 06509408b3df4807006ead9226767bcf(1); 087f3b5ca40501dbd68a44f64d5edb9c(1); 090100d4dfb1c4a4468618d5eecd05df(1); 09a6e2f585fde8404c6bbdcb6beb3de1(1); 09d988e9d9ce0d26e24bd1bb221f10ec(1); 0a90f19db081ddc8c6ffb5fcde3a626c(1); ...(258) |
| channel | 100% | string:268 | distinct: 3 (1.1% unique) LC — push(132); whatsapp(78); email(58) |
| city | 100% | string:268 | distinct: 7 (2.6% unique) LC — Mumbai(163); Singapore(29); Dubai(23); Sydney(21); London(13); New York(13); Riyadh(6) |
| client_lib | 100% | string:268 | distinct: 2 (0.7% unique) LC — mobile-rn(227); web-js(41) |
| destination | 100% | string:268 | distinct: 14 (5.2% unique) LC — US(30); AE(23); AU(23); TH(23); JP(22); GB(21); GR(21); FR(17); TR(17); ID(16); ...(4) |
| device_type | 100% | string:268 | distinct: 4 (1.5% unique) LC — ios(128); android(73); web-user-b2c(41); Desktop(26) |
| drop_step | 100% | string:268 | distinct: 4 (1.5% unique) LC — document_uploaded(92); application_started(70); destination_card_clicked(58); pay_now_clicked(48) |
| geoip_country_code | 100% | string:268 | distinct: 7 (2.6% unique) LC — IN(163); SG(29); AE(23); AU(21); GB(13); US(13); SA(6) |
| os | 100% (3.7% null) | string:258 | distinct: 4 (1.5% unique) LC — iOS(128); Android(63); Mac OS X(34); Windows(33) |
| user_id | 100% | string:268 | distinct: 268 (100% unique) — 0OTnBhzg4hSgdX58f3uxYQchxx95(1); 0QFKdkYs7dW8wv2md4LuH5Qns5D9(1); 18cqAqrWW9zEsHkSR4wfZwMH7hwG(1); 19yAEQy5DpgEXvE318HK9PrhHQEd(1); 1OT4HQo7zrfGM8F0K0K28LbRaRmt(1); 2ZRQBUcmjEDgHETOVWFfVLq8u7s3(1); 2hnpbHat401VrGIYgy4DL3zI1zHV(1); 2lcDuOpFWW3FBpGvAqeSxx8KFjl4(1); 34VuVCSljW8xc5xT58ZlmkCM7LbX(1); 3WbjwFM05i7cWh5dXbgSAX80NqJd(1); ...(258) |

## resumed_at_step (n=268, id_duplicates: 0)

| field | present | type | distinct values / range |
|---|---|---|---|
| app_version | 100% | string:268 | distinct: 3 (1.1% unique) LC — 7.45.2(101); 7.46.0(84); 7.44.0(83) |
| application_id | 100% | string:268 | distinct: 268 (100% unique) — 00d02b249e5f33b98d9fe85dcb335f95(1); 00e56bc6fd5c0482d0703b0dc4c21a90(1); 018fef685c2dc3cc253d896768680aec(1); 019c4c24b1569122f70854aa22f35855(1); 06509408b3df4807006ead9226767bcf(1); 087f3b5ca40501dbd68a44f64d5edb9c(1); 090100d4dfb1c4a4468618d5eecd05df(1); 09a6e2f585fde8404c6bbdcb6beb3de1(1); 09d988e9d9ce0d26e24bd1bb221f10ec(1); 0a90f19db081ddc8c6ffb5fcde3a626c(1); ...(258) |
| channel | 100% | string:268 | distinct: 3 (1.1% unique) LC — push(132); whatsapp(78); email(58) |
| city | 100% | string:268 | distinct: 7 (2.6% unique) LC — Mumbai(163); Singapore(29); Dubai(23); Sydney(21); London(13); New York(13); Riyadh(6) |
| client_lib | 100% | string:268 | distinct: 2 (0.7% unique) LC — mobile-rn(227); web-js(41) |
| destination | 100% | string:268 | distinct: 14 (5.2% unique) LC — US(30); AE(23); AU(23); TH(23); JP(22); GB(21); GR(21); FR(17); TR(17); ID(16); ...(4) |
| device_type | 100% | string:268 | distinct: 4 (1.5% unique) LC — ios(128); android(73); web-user-b2c(41); Desktop(26) |
| drop_step | 100% | string:268 | distinct: 4 (1.5% unique) LC — document_uploaded(92); application_started(70); destination_card_clicked(58); pay_now_clicked(48) |
| geoip_country_code | 100% | string:268 | distinct: 7 (2.6% unique) LC — IN(163); SG(29); AE(23); AU(21); GB(13); US(13); SA(6) |
| os | 100% (3.7% null) | string:258 | distinct: 4 (1.5% unique) LC — iOS(128); Android(63); Mac OS X(34); Windows(33) |
| user_id | 100% | string:268 | distinct: 268 (100% unique) — 0OTnBhzg4hSgdX58f3uxYQchxx95(1); 0QFKdkYs7dW8wv2md4LuH5Qns5D9(1); 18cqAqrWW9zEsHkSR4wfZwMH7hwG(1); 19yAEQy5DpgEXvE318HK9PrhHQEd(1); 1OT4HQo7zrfGM8F0K0K28LbRaRmt(1); 2ZRQBUcmjEDgHETOVWFfVLq8u7s3(1); 2hnpbHat401VrGIYgy4DL3zI1zHV(1); 2lcDuOpFWW3FBpGvAqeSxx8KFjl4(1); 34VuVCSljW8xc5xT58ZlmkCM7LbX(1); 3WbjwFM05i7cWh5dXbgSAX80NqJd(1); ...(258) |

## reconverted (n=93, id_duplicates: 0)

| field | present | type | distinct values / range |
|---|---|---|---|
| app_version | 100% | string:93 | distinct: 3 (3.2% unique) LC — 7.45.2(33); 7.46.0(31); 7.44.0(29) |
| application_id | 100% | string:93 | distinct: 93 (100% unique) — 00d02b249e5f33b98d9fe85dcb335f95(1); 018fef685c2dc3cc253d896768680aec(1); 06509408b3df4807006ead9226767bcf(1); 087f3b5ca40501dbd68a44f64d5edb9c(1); 090100d4dfb1c4a4468618d5eecd05df(1); 09d988e9d9ce0d26e24bd1bb221f10ec(1); 0dcf1d7b3214397157f5ac3f8aa21bae(1); 13a35ec5cf7b768af32e9415a9373b06(1); 1748863efc54787e170d6feeba7c007b(1); 17da8bda59c5858000a7a78c17b1d19c(1); ...(83) |
| channel | 100% | string:93 | distinct: 3 (3.2% unique) LC — push(53); whatsapp(21); email(19) |
| city | 100% | string:93 | distinct: 7 (7.5% unique) LC — Mumbai(63); Singapore(10); Dubai(8); Sydney(5); London(3); New York(3); Riyadh(1) |
| client_lib | 100% | string:93 | distinct: 2 (2.2% unique) LC — mobile-rn(80); web-js(13) |
| destination | 100% | string:93 | distinct: 14 (15.1% unique) — TR(10); EG(9); GB(8); AE(7); AU(7); ID(7); TH(7); FR(6); SG(6); US(6); ...(4) |
| device_type | 100% | string:93 | distinct: 4 (4.3% unique) LC — ios(42); android(30); web-user-b2c(13); Desktop(8) |
| drop_step | 100% | string:93 | distinct: 4 (4.3% unique) LC — document_uploaded(31); application_started(25); pay_now_clicked(19); destination_card_clicked(18) |
| geoip_country_code | 100% | string:93 | distinct: 7 (7.5% unique) LC — IN(63); SG(10); AE(8); AU(5); GB(3); US(3); SA(1) |
| os | 100% (4.3% null) | string:89 | distinct: 4 (4.3% unique) LC — iOS(42); Android(26); Mac OS X(11); Windows(10) |
| user_id | 100% | string:93 | distinct: 93 (100% unique) — 0OTnBhzg4hSgdX58f3uxYQchxx95(1); 1OT4HQo7zrfGM8F0K0K28LbRaRmt(1); 2ZRQBUcmjEDgHETOVWFfVLq8u7s3(1); 2hnpbHat401VrGIYgy4DL3zI1zHV(1); 2lcDuOpFWW3FBpGvAqeSxx8KFjl4(1); 34VuVCSljW8xc5xT58ZlmkCM7LbX(1); 642BksCLAjpc6RdUZcAs1sgPYpuU(1); 6A7tmA5J909MQyd4mzuxkdH6eCWK(1); 6BkA4558Fwp7ne7BjexTIqAsWl57(1); 6GnYjFuBo0driEQ3oZn6CryPuB8z(1); ...(83) |

## Field × Event Grid

| field | AD | RS | RO | RCC | RAS | R |
|---|---|---|---|---|---|---|
| app_version | yes | yes | yes | yes | yes | yes |
| application_id | yes | yes | yes | yes | yes | yes |
| city | yes | yes | yes | yes | yes | yes |
| client_lib | yes | yes | yes | yes | yes | yes |
| destination | yes | yes | yes | yes | yes | yes |
| device_type | yes | yes | yes | yes | yes | yes |
| drop_step | yes | yes | yes | yes | yes | yes |
| geoip_country_code | yes | yes | yes | yes | yes | yes |
| os | yes | yes | yes | yes | yes | yes |
| user_id | yes | yes | yes | yes | yes | yes |
| channel | no | yes | yes | yes | yes | yes |
| hours_since_drop | no | yes | no | no | no | no |

**Legend:** AD=abandonment_detected; RS=reminder_sent; RO=reminder_opened; RCC=reminder_cta_clicked; RAS=resumed_at_step; R=reconverted

