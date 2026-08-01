# Justification — Spec 03: Visa Status Sharing

## Overview

| Object | Kind | Source event(s) | Rows | ORDER BY / key | Notes |
|---|---|---|---:|---|---|
| `share_clicked` | CREATE TABLE | `share_clicked` | 1,600 | `(status_shared, toDate(timestamp), share_id, id)` | full envelope; join key `share_id` for K-factor |
| `channel_selected` | CREATE TABLE | `channel_selected` | 1,144 | `(channel, toDate(timestamp), share_id, id)` | full envelope |
| `link_generated` | CREATE TABLE | `link_generated` | 1,144 | `(channel, toDate(timestamp), share_id, id)` | full envelope; field set/count identical to `channel_selected` — kept separate (see below) |
| `link_opened` | CREATE TABLE | `link_opened` | 2,310 | `(channel, toDate(timestamp), destination, share_id, id)` | recipient event, **no `user_id`** |
| `recipient_cta_clicked` | CREATE TABLE | `recipient_cta_clicked` | 305 | `(destination, toDate(timestamp), share_id, id)` | recipient event, **no `user_id`** |

No `ALTER TABLE` statements and no materialized view were produced. Reasoning below.

---

## CREATE vs ALTER call (all 5 events)

Checked every event in the spec against the 8 existing tables' column lists in `ddl.sql`/`instrumentation_notes.md` and against each existing table's context page for an explicit "instrument alongside X" instruction (per the required-reading step 2). None of the 8 existing tables' pages mention status sharing, and none of the 5 new events describe firing "alongside"/"as part of" a step any existing table already writes (unlike, e.g., an add-on purchase alongside `purchase_completed`). Sharing is a standalone post-funnel feature with its own moment for each event. So every event gets its **own new table**, per `instrumentation_notes.md`'s stated convention: *"one table per event, auto-created by the client event SDK."* Zero ALTERs.

One internal wrinkle worth flagging even though it didn't change the output: `channel_selected` and `link_generated` have **byte-identical field sets and identical row counts** (1,144 = 1,144, per the profile) — every `channel_selected` row has a matching `link_generated` row and vice versa, suggesting the client fires both atomically the instant a channel is tapped (selecting a channel immediately generates the share link for it). This looks like a candidate for merging into one table under the ALTER framework's logic ("same moment, same grain"). I did **not** merge them, because:
- the ALTER-vs-CREATE decision procedure given to me is scoped to *new event joins existing table's grain*, not *two sibling new events collapse into one table* — nothing in spec.md or known_issues.md licenses that merge;
- spec.md names them as two distinct, separately-meaningful UX steps (`channel_selected` = pick a channel; `link_generated` = a link is created for it);
- collapsing them would break the "one table per event" convention without an explicit instruction to do so.
This coincidence is recorded here as a caveat to carry forward (see Risks below), not acted on.

---

## Column choices

### Shared envelope columns (`share_clicked`, `channel_selected`, `link_generated`)

spec.md states *"Sharer events carry the full envelope"* — a direct spec instruction, so all 3 sharer-side tables get the full 30-column envelope from `tables/index.md`, typed exactly as the baseline (`Nullable(String)`/`Nullable(UInt8)`/`Nullable(Float64)`) for every envelope column the profile did **not** specifically exercise for this spec (e.g. `locale`, `language`, `client_ip`, `latitude`/`longitude`, `funnel_type`, `gclid`/`fbclid`/`gad_source`, `is_guest`/`is_referral`/`is_enterprise`, `co_travelers`, `citizenship`, `is_back_filled`, `duplicate_id`, `app_session_id`, `device`, `geoip_subdivision_1_code`). No stat justifies deviating from baseline for these, so none was invented.

For columns the profile **did** exercise, per the String-type decision:

| Column | Stat used | Type chosen | Why not the alternatives |
|---|---|---|---|
| `user_id` | relationship.md: "exactly 28 characters everywhere" | `FixedString(28)` | This is the exact example the instructions cite for a confirmed-fixed-length high-cardinality identifier. Deliberate upgrade from baseline `String`. |
| `destination` | 100% present across all 5 events; 27 known ISO-2 values, no catch-all bucket documented for `destination` (unlike `geoip_country_code`'s `OTHER`) | `FixedString(2)` | Every sampled value (AU, VN, TH, GB, AE, FR, GR, TR, ID, MY, ...) is exactly 2 bytes; relationship.md's full 27-value list is uniformly 2-char. `LowCardinality(String)` was considered but `FixedString` is the tighter, correctly-justified choice for a genuinely fixed-format code. |
| `geoip_country_code` | tables/index.md: value list includes `OTHER` (5 chars) alongside 2-char codes | `LowCardinality(Nullable(String))` | The `OTHER` catch-all disqualifies `FixedString(2)` even though every *real* code is 2 chars — this is the exact ragged-catch-all trap the instructions warn about. Distinct count (7 sampled here) is well under the 10% LC threshold. |
| `device_type`, `os`, `client_lib`, `city` | LC hint fires in profile (distinct 2–7, 0.1–0.6% unique, all «10%) | `LowCardinality(Nullable(String))` | Ragged value lengths (`Desktop` vs `ios`; `Mumbai` vs `New York`) rule out `FixedString`. `os` kept `Nullable` — profile shows 5.1–5.6% null. |
| `app_version` | distinct 3, LC hint fires | `LowCardinality(Nullable(String))` | Same byte length today (`7.44.0` etc.) but this is a semantic version string, not a fixed-format code (future versions may add digits, e.g. `7.100.0`) — `FixedString` would be a latent breakage risk, so `LowCardinality` per rule 2 of the String-type decision. |
| `application_id` | 100% present in all 3 sharer tables | `Nullable(String)` (unchanged from baseline) | High-cardinality identifier; kept `Nullable` per baseline convention since a sharer without an application_id is plausible even though not observed in this sample. **Must be normalized 32→36 char on ingest — see D2 risk below.** |
| `status_shared` | distinct 3 (`submitted`/`processing`/`approved`), 100% present, ragged lengths | `LowCardinality(String)` non-nullable | LC hint fires; ragged length rules out `FixedString`; 100% presence across all three sharer events justifies non-nullable (avoid-nullable rule). |
| `channel` | distinct 4 (`whatsapp`/`copy_link`/`email`/`sms`), 100% present, ragged lengths (3–9 chars) | `LowCardinality(String)` non-nullable | Same reasoning as `status_shared`. |
| `share_id` | 32-char hex string in every sample across all 5 events, no ragged exceptions observed | `FixedString(32)` non-nullable | Confirmed fixed-length identifier (like an md5-style hash) — satisfies the "real fixed-format code" bar from the String-type decision, unlike `application_id` (whose format is under active correction per D2, so left as `String`). |

### Recipient tables (`link_opened`, `recipient_cta_clicked`)

spec.md: *"recipient events... are keyed by `share_id`"*, and relationship.md's "Entities the incoming specs will add" states recipient events **carry no `user_id`** — a join topology nothing else in the dataset supports. The profile confirms this: neither event has `user_id`, `application_id`, or any device/geo envelope field. Per the "never invent a column" rule, these two tables carry **only** `id`, `timestamp`, and the fields the profile actually shows:

- `link_opened`: `channel` (LC, 4 values, 100% present), `destination` (`FixedString(2)`, 100% present), `recipient_is_new_user` — 100% present, exactly 2 boolean values, no nulls in the profile → non-nullable `UInt8` (avoid-nullable rule: no null semantics observed, so no reason to pay the `Nullable` overhead), and `share_id` (`FixedString(32)`, 39.9% unique — recipients can reopen a link, so repeats are expected and not an error).
- `recipient_cta_clicked`: `cta` — distinct **1** value (`start_own_application`) in the whole sample. Considered `Enum8` per the Enum rule, but rejected: the set is *small today*, not *confirmed closed* — a recipient CTA surface is exactly the kind of UI element likely to grow a second CTA (e.g. "learn more") without a coordinated schema change, and an `Enum` would reject that insert outright. Kept `LowCardinality(String)`, matching how the baseline 8 tables never use `Enum` for any categorical. `destination` and `share_id` typed as above (`share_id` here is 86.2% unique — closer to 1:1 with opens, as expected for a rarer, further-down-funnel action).

---

## ORDER BY / PARTITION BY reasoning

All 5 tables use `PARTITION BY toYYYYMM(timestamp)` — identical to the 8 existing tables and compliant with `schema-partition-low-cardinality` (monthly partitions stay in the tens over any realistic data lifetime, far under the 100–1,000 warning threshold).

None of the 5 new tables repeats the `ORDER BY (id, timestamp, user_id)` pattern flagged as D8 — `id` never leads. Per `schema-pk-cardinality-order` (low-to-high cardinality) and `schema-pk-prioritize-filters` (lead with the columns the PM's own questions filter/group by):

- **`share_clicked`**: `(status_shared, toDate(timestamp), share_id, id)`. PM's first question is "does share rate vary by `status_shared`?" — that's the lowest-cardinality (3 values), most-filtered column, so it leads. `toDate(timestamp)` next for coarse time-range pruning per the cardinality-order guideline. `share_id` next as the join key to the recipient tables (K-factor question), `id` last as tiebreaker only (never queried directly).
- **`channel_selected`** / **`link_generated`**: `(channel, toDate(timestamp), share_id, id)`. PM's second question is "channel mix" — `channel` (4 values) leads for the same reason.
- **`link_opened`**: `(channel, toDate(timestamp), destination, share_id, id)`. Two PM questions hit this table directly: channel mix (which channel drives new-user opens) and "which destinations spread most" — both categoricals earn a slot; `channel` (4 values) precedes `destination` (14 values) per cardinality order. `recipient_is_new_user` was deliberately left out of the key — it's a boolean filter typically combined with `channel`, and adding a 3rd/4th key column with only 2 values inside an already-4-column key gives little extra pruning; it remains a cheap `WHERE` predicate on a small table instead.
- **`recipient_cta_clicked`**: `(destination, toDate(timestamp), share_id, id)`. `cta` was excluded from the key entirely — with only 1 distinct value observed it has zero discriminating power and would waste a key position (an index built on a constant can't skip anything). `destination` leads instead, directly serving "which destinations spread most" down to the conversion step.

---

## Materialized view decision: **not built**

Per `query-mv-incremental` (impact: HIGH), the win an incremental MV buys is *"read thousands of rows instead of billions."* This spec's entire event volume across all 5 event types is **6,503 rows total** (max single table 2,310 rows). A full `GROUP BY channel` or `GROUP BY status_shared` scan over 1,144–2,310 rows is already a sub-millisecond operation — there is no billions-of-rows problem for an MV to solve, and the PM's repeated questions (share rate by status, channel mix, K-factor, destination spread) are all cheap `count()`/`countIf()` aggregations at this scale. Building a `-State`/`-Merge` AggregatingMergeTree pipeline here would add ingestion-path complexity (per `insert-mutation-avoid-update`/`query-mv-incremental`'s own point that MVs run at insert time) without a query-latency problem to justify it. Explicitly not proposing one; revisit if/when this feature's volume grows into the millions.

---

## Risks / caveats to carry forward

- **D2 (mandatory before deploy)** — `application_id` on `share_clicked`, `channel_selected`, and `link_generated` arrives as 32-char unhyphenated hex from the spec NDJSON; the live DB's `application_started.application_id` is 36-char hyphenated. Ingestion **must** normalize with:
  ```sql
  concat(substring(raw_id,1,8),'-',substring(raw_id,9,4),'-',substring(raw_id,13,4),
         '-',substring(raw_id,17,4),'-',substring(raw_id,21,12)) AS application_id
  ```
  and the overlap check is **mandatory** before declaring any of these 3 tables ready, e.g. for `share_clicked`:
  ```sql
  SELECT round(100.0 * uniqExactIf(application_id, application_id IN (
           SELECT application_id FROM clickathon.application_started))
         / uniqExact(application_id), 2) AS overlap_pct
  FROM clickathon.share_clicked
  ```
  Repeat for `channel_selected` and `link_generated`. If `overlap_pct` is 0%, stop and report as a finding rather than silently shipping a table that can never join the funnel (per D2's decision table).
- **Entity conflict check (relationship.md)** — relationship.md explicitly calls out that spec 03 introduces `share_id` and that recipient events carry no `user_id`, "a join topology nothing in this dataset currently supports." This is faithfully reflected: `link_opened`/`recipient_cta_clicked` have no `user_id` column and cannot be joined to the funnel except via `share_id → share_clicked.share_id → user_id`. Any K-factor analysis must go through that indirection and should explicitly flag it, not assume a direct user join.
- **`channel_selected` / `link_generated` identical grain** — flagged above under CREATE-vs-ALTER. If a future audit confirms these always co-occur 1:1 with no exceptions, consider collapsing them into one table with an explicit instruction to do so — not done here since it wasn't authorized by this task's decision framework.
- **D9-style casing/vocabulary risk** — `destination` here is upper-case ISO-2, consistent with the existing envelope's `destination` column; no new collision introduced. `status_shared` values (`submitted`/`processing`/`approved`) should be checked against `purchase_completed`/`application_started` status vocabulary (if any exists) for a K2/D9-style mismatch before cross-table comparisons — not verified here as no such column was found in the 8 existing tables' DDL.
- **No repeat-user caveat (D6)** — the 8 baseline tables show exactly one event per user; this spec's `share_clicked` (1,600 rows) will need checking against that pattern before assuming one share per applicant — not verified in this pass since it requires a query against the live table, not just the profile.
