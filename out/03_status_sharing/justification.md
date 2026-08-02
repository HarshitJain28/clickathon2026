# Justification — Spec 03: Visa Status Sharing

## Overview

| Object | Kind | Source event(s) | Rows | ORDER BY / key | Notes |
|---|---|---|---:|---|---|
| `share_clicked` | CREATE TABLE | `share_clicked` | 1,600 | `(toDate(timestamp), status_shared, user_id, id)` | Sharer taps share; status is the PM's #1 cut. |
| `channel_selected` | CREATE TABLE | `channel_selected` | 1,144 | `(toDate(timestamp), channel, user_id, id)` | Sharer picks a channel. |
| `link_generated` | CREATE TABLE | `link_generated` | 1,144 | `(toDate(timestamp), channel, user_id, id)` | Share link created; identical column set to `channel_selected` — see caveats. |
| `link_opened` | CREATE TABLE | `link_opened` | 2,310 | `(toDate(timestamp), channel, share_id, id)` | Recipient-side; no `user_id`, no envelope. |
| `recipient_cta_clicked` | CREATE TABLE | `recipient_cta_clicked` | 305 | `(toDate(timestamp), destination, share_id, id)` | Recipient-side; K-factor numerator. |

No `ALTER TABLE` and no `MATERIALIZED VIEW` were produced for this spec — reasoning below.

---

## CREATE vs ALTER call

Per event, checked against every existing table's own grain (the 8 baseline + 5 Express Checkout + 4 Group/Family tables, per `ddl.sql`/`instrumentation_notes.md`/`tables/index.md`):

- **`share_clicked`** — fires when a sharer taps "share" on their own application status. This moment does not coincide with any existing table's event (`purchase_completed`, `application_started`, etc. all fire earlier in the journey, at a different moment, and none of them carry `status_shared`/`share_id`). It is also the origin of a brand-new entity (`Share`), which `relationship.md` explicitly anticipates: *"Share (spec 03) — `share_id`. Recipient events carry no `user_id`, a join topology nothing in this dataset currently supports."* New occurrence, own grain → **CREATE TABLE**.
- **`channel_selected`** — fires when the sharer picks a channel, a later and *optional* moment (1,144 of 1,600 `share_clicked` rows, 71.5%, have a corresponding `channel_selected` — not 1:1, so it is not the same instant as `share_clicked`). New occurrence, own grain → **CREATE TABLE**.
- **`link_generated`** — fires when the link is actually created. Its column set is byte-for-byte identical to `channel_selected`'s (see Field × Event Grid in `profile.md`: both carry exactly `app_version, application_id, channel, city, client_lib, destination, device_type, geoip_country_code, os, share_id, status_shared, user_id`) and both have exactly 1,144 rows. This is the strongest CREATE-vs-ALTER signal in the spec, but note it is **not** a case the "ALTER an existing table" rule covers — that rule applies to grafting new attributes onto an *already-deployed* table, and `link_generated` and `channel_selected` are both *new* to this spec; there is no pre-existing table to alter here. `spec.md` and `instrumentation_notes.md`'s "one table per event, auto-created by the client event SDK" convention both treat these as two distinct named raw events (analogous to how the baseline's `pay_now_clicked` and `purchase_completed` are also near-adjacent, similarly-shaped events kept as separate tables). New occurrence, own grain → **CREATE TABLE**. The identical schema is flagged as a caveat below, not resolved by merging the tables.
- **`link_opened`** — fires when a *recipient* (not the sharer) opens the link. Different actor, different grain, no `user_id` at all — cannot be an attribute of any sharer-side table. New occurrence, own grain → **CREATE TABLE**.
- **`recipient_cta_clicked`** — fires when the recipient taps the CTA, a later and optional moment than `link_opened` (305 of 2,310 opens, 13.2%, convert). New occurrence, own grain → **CREATE TABLE**.

No event in this spec shares a moment/grain with any of the 17 already-deployed tables, so there are zero ALTER candidates.

---

## Column choices

### Shared reasoning across all 5 tables

- **`id` / `timestamp`** — structural envelope columns (every event in `profile.md` reports `id_duplicates` and a `time_span`, confirming both exist on every row); non-nullable, matching the platform-wide convention.
- **`share_id`** — the spec's own new entity key. 100% present on **all 5** tables with zero observed nulls, and every sampled value in `profile.md` (e.g. `001a9ac88db527d278975b558d82eb08`, `c06c3e570e4eaaaa93d293904ee0c941`) is exactly 32 lowercase-hex characters — a uniform fixed width. Per the String-type decision rule #5, `FixedString` is permitted for "a new `share_id` joining new table to new table" — exactly this case (`share_clicked`/`channel_selected`/`link_generated` → `link_opened`/`recipient_cta_clicked`, never joined to `application_id`/`user_id`/`group_id`). This mirrors the precedent already set for `group_id` (`FixedString(32)`, spec 02, per `relationship.md`). Made **non-nullable**: per `schema-types-avoid-nullable`, Nullable should be reserved for semantically-meaningful absence, and every table shows 100% presence for this column — it is the row's defining identifier, the same class of column as `id`/`user_id`, not an optional attribute.
- **`application_id`** (sharer tables only) — kept `Nullable(String)`, matching `application_started.application_id`'s exact type, per the join-key-type-match rule (never `FixedString`, since a `FixedString`-vs-`String` join silently mismatches on padding). **D2 risk carried forward** — see Risks section; type match does not guarantee the join will return anything.
- **`user_id`** (sharer tables only) — plain `String`, non-nullable, matching every other table's `user_id` column exactly (100% present, universal join key per `relationship.md` §3).

### Per-column string-type reasoning

| Column | Chosen type | Reasoning |
|---|---|---|
| `status_shared` | `LowCardinality(String)` | 3 values (`submitted`/`processing`/`approved`), ragged lengths (9/10/8 chars) — not fixed-width, rules out `FixedString`. Considered `Enum8` (closed-looking set, natural fit for a status field) but rejected: this is a visa-application-status vocabulary that plausibly gains values (`rejected`, `expired`, etc.) without a coordinated schema change, and none of the 8 baseline tables use `Enum` anywhere — mismatch risk (new value breaks ingestion) outweighs the validation benefit. 100% present, 0% null observed → non-nullable. |
| `channel` | `LowCardinality(String)` | 4 values (`whatsapp`/`copy_link`/`email`/`sms`), ragged lengths (9/10/5/3 chars) — variable-length, rules out `FixedString`. Low-cardinality hint qualifies (4 ≪ 1000 absolute, ≪10% of rows). 100% present, 0% null → non-nullable. |
| `destination` | `FixedString(2)` | Every sampled value across all events is a 2-char ISO-2 code. Checked `relationship.md`'s full 27-value enumeration (`AE AU CA CH EG ES FR GB GR HK ID IT JP KR LK MA MV MY OM QA SA SG TH TR US VN ZA`) for a catch-all exception the way the system prompt warns — **none exists for `destination`** (unlike `geoip_country_code`, see below). Per `schema-types-lowcardinality`'s own carve-out ("Reserve `FixedString` for strictly fixed-length data, e.g. 2-char country codes"), `FixedString(2)` is the precise choice here, a deliberate divergence from spec 01/02's blanket `LowCardinality(String)` for this column. 100% present, 0% null → non-nullable. Not used as a join key, so the join-key type-match constraint does not apply. |
| `geoip_country_code` | `LowCardinality(String)` | This event's own sample is also uniformly 2-char, **but** `tables/index.md`'s envelope description documents this exact column's platform-wide domain as `AE AU GB IN OM OTHER QA SA SG US` — an `OTHER` catch-all bucket that breaks fixed width elsewhere on the platform even though it didn't appear in this spec's 6,503-row sample. This is precisely the ragged-exception case the system prompt calls out; `LowCardinality(String)` (not `FixedString`) avoids a future silent truncation/mismatch. 100% present, 0% null → non-nullable. |
| `device_type` | `LowCardinality(String)` | 4 values (`ios`/`android`/`web-user-b2c`/`Desktop`), ragged lengths (3/7/12/7) and mixed casing (D9) — rules out `FixedString`. 100% present, 0% null → non-nullable. |
| `os` | `LowCardinality(Nullable(String))` | 4 values, ragged lengths (`iOS`/`Android`/`Windows`/`Mac OS X`). **Kept nullable** — 5.6% null in `share_clicked`, 5.1% in `channel_selected`/`link_generated`, matching the baseline envelope's own `os` column (`Nullable(String)`, 5.95% null platform-wide) — this is the one column in the spec with a real, semantically-meaningful absence (`os` not detected), unlike the other 100%-present fields. |
| `city` | `LowCardinality(String)` | 7 values (`Mumbai`/`Singapore`/`Dubai`/`New York`/`London`/`Sydney`/`Riyadh`), ragged lengths — free-form-ish place names, textbook `LowCardinality` case (rule #2 of the String-type decision). 100% present, 0% null → non-nullable. |
| `client_lib` | `LowCardinality(String)` | 2 values (`mobile-rn`/`web-js`), ragged lengths (9/6). 100% present, 0% null → non-nullable. |
| `app_version` | `LowCardinality(String)` | 3 values, all coincidentally 6 characters in this sample (`7.44.0` etc.) — but unlike ISO country codes this is not an externally fixed-width standard; a future `7.100.0`/`8.0.0` would break a `FixedString` silently. `LowCardinality(String)` is the safer, still-cheap choice. 100% present, 0% null → non-nullable. Per K7, carries no temporal signal — usable only as a synthetic segment, never a release timeline. |
| `cta` (`recipient_cta_clicked` only) | `LowCardinality(String)` | Single observed value today (`start_own_application`), same shape as `document_uploaded.doc_type` (`relationship.md`: "single-valued and therefore useless as a cut"). Kept as a real column (it is observed) but not used as an ORDER BY key for the same reason `doc_type` isn't — no discriminating power yet. `LowCardinality` over plain `String` because it is a categorical field expected to gain values later (other CTAs), not free text. |
| `recipient_is_new_user` (`link_opened` only) | `Bool` | 100% present, exactly 2 values (`true`/`false`), 0% null. Chose native `Bool` over the baseline's `Nullable(UInt8)` flag convention, following the precedent already set by spec 02's `traveller_added.docs_complete` (`Bool`, per `relationship.md`) and `schema-types-native-types` ("native types... enable... correct semantics"); no null observed so no `Nullable` wrapper needed. |

---

## ORDER BY / PARTITION BY reasoning

All 5 tables: `PARTITION BY toYYYYMM(timestamp)`, matching the platform-wide convention and `schema-partition-lifecycle` (time-aligned partitions are for lifecycle/retention, bounded to ~months — satisfies `schema-partition-low-cardinality`'s 100–1,000-partition guidance over any realistic retention horizon).

Per **D8** ("new tables must not inherit the `(id, timestamp, user_id)` id-first sort key... lead with real filter columns"), every ORDER BY leads with `toDate(timestamp)` and a low-cardinality dimension, never a random `id`/`share_id` first. This follows the exact substitution pattern already used for spec 01 (`device_type` in the #2 slot) and spec 02 (`group_size` in the #2 slot): the PM's most-cited dimension for each table's own analysis goes in the #2 slot, per `schema-pk-cardinality-order` (low-cardinality columns first enable granule skipping) and `schema-pk-prioritize-filters` (frequently-filtered columns belong in the key):

- **`share_clicked`** → `(toDate(timestamp), status_shared, user_id, id)`. PM Q1 is "does `status_shared` correlate with share rate" — `status_shared` (3 values) is this table's own leading discriminator.
- **`channel_selected` / `link_generated`** → `(toDate(timestamp), channel, user_id, id)`. PM Q2 is channel mix — `channel` (4 values) leads.
- **`link_opened`** → `(toDate(timestamp), channel, share_id, id)`. Same channel-mix question, but `user_id` doesn't exist on this table (recipient-side) so `share_id` (the only entity key present) takes its slot, ahead of the trailing `id`.
- **`recipient_cta_clicked`** → `(toDate(timestamp), destination, share_id, id)`. PM Q4 is "which destinations spread most" — `destination` leads; `cta` is excluded from the key because it is single-valued today (no pruning value, same reasoning as excluding `document_uploaded.doc_type` from any ORDER BY).

`id` trails every key as a final uniqueness tiebreaker, never leading it — satisfying D8 directly.

---

## Materialized view decision

**Not built.** Total spec volume is 6,503 rows across all 5 tables (largest table `link_opened` at 2,310 rows). Per `query-mv-incremental`, incremental MVs earn their keep by turning a "scan billions of rows on every query" problem into "read thousands of rows" — this data is already at the thousands-of-rows scale on the raw tables themselves; a pre-aggregation would save reading a few thousand rows instead of a few hundred thousand, not a meaningful win. `query-mv-refreshable` (complex joins/denormalization) also doesn't apply — the PM's questions (share rate by status, channel mix, K-factor, destination spread) are all single-table `GROUP BY`s or a two-table join on `share_id` between tiny tables, cheap to run live. Revisit if this spec's ingest volume grows by orders of magnitude.

---

## Risks / caveats to carry forward

- **D2** — `application_id` is present on 100% of rows across `share_clicked`/`channel_selected`/`link_generated`, but every prior spec (01: 5 tables, 02: 4 tables) that carried a spec-sourced `application_id` normalized it (32-char unhyphenated hex → 36-char hyphenated) and then found **0% overlap** against `application_started`. This spec's `application_id` values were not directly inspected in `profile.md` (>1,000 distinct, sample omitted), so the same normalize-then-verify overlap check is **mandatory before declaring these 3 tables joinable** to the main funnel — expect the same 0%/STOP outcome as specs 01 and 02 based on the established pattern, but this must be re-run, not assumed.
- **D8** — applied directly: none of the 5 new tables' sort keys lead with a random `id`/`FixedString` key; all lead with `toDate(timestamp)` plus a real filter dimension (see ORDER BY reasoning above).
- **D9** — `device_type` mixes casing conventions (`ios`, `android`, `Desktop`) exactly as documented platform-wide; any cross-table `device_type` comparison must normalize case first, same as the baseline tables.
- **D1** — the PM's step-through question (share → channel select → link generate → open → recipient CTA) must be answered by **set-membership joins on `share_id`**, never `windowFunnel`/`sequenceMatch` — D1 established that this platform's timestamps are not reliably monotonic across funnel steps (52% loss measured on the main funnel), and no monotonicity check has been run yet for this spec's own event sequence. Per D1's guidance for new tables, test `countIf(t_later >= t_earlier) / count()` on this data before trusting any time-ordered function; below ~0.99, use set membership instead.
- **D6** — this spec's sharer-side events (`share_clicked`, `channel_selected`, `link_generated`) each show exactly one row per `user_id` (1,600/1,600, 1,144/1,144, 1,144/1,144 — all 100% unique), consistent with the platform's "no repeat users" pattern holding for this flow too. The recipient-side tables do **not** carry `user_id` at all (no such check is possible), and `share_id` legitimately repeats there (multiple opens/CTAs per share) — this is expected fan-out on the *recipient* side, not a D6 violation, since `user_id` uniqueness is what D6 actually constrains and no `user_id` column exists on those two tables.
- `spec.md` states sharer events "carry the full envelope," but `profile.md` observed only a 9–13 column subset of the 30-column envelope (missing `app_session_id`, `device`, `geoip_subdivision_1_code`, `client_ip`, `latitude`/`longitude`, `locale`/`language`, `funnel_type`, `co_travelers`, `is_guest`/`is_referral`/`is_enterprise`, `gclid`/`fbclid`/`gad_source`, `citizenship`, `is_back_filled`, `duplicate_id`) — per the column policy, these were not added. If the client SDK is later confirmed to emit the remaining envelope fields, that is a follow-up `ALTER TABLE ADD COLUMN` once observed in a fresh profile, not something to add speculatively now.
- The near-identical schemas of `channel_selected` and `link_generated` (byte-for-byte the same column set, same row count, 1,144 each) are worth flagging to the Analytics Agent as a possible 1:1 pairing (every channel selection appears to produce exactly one link) — this was kept as two tables per the CREATE-vs-ALTER reasoning above, but an Analytics-layer check of whether `share_id` values in the two tables are pairwise identical would confirm or refute that assumption before treating them as a single funnel step.
- **Entity check against `relationship.md`** — the new `Share` entity (`share_id`) does not conflict with or duplicate any existing entity (`User`, `Application`, `Destination`, `Document`, `Group`); `relationship.md`'s own "Entities the incoming specs will add" section anticipated this spec by name and confirmed the no-`user_id`-on-recipient-events topology, which this schema implements as designed (recipient tables carry no `user_id` column at all, rather than a nullable one).
