# Justification — Spec 02: Group / Family Applications

## Overview table

| Object | Kind | Source event(s) | Rows | ORDER BY / key | Notes |
|---|---|---|---:|---|---|
| `group_started` | CREATE TABLE | `group_started` | 1,200 | `(group_size, destination, toDate(timestamp), group_id, id)` | Origin of `group_id`; one row per group. |
| `traveller_added` | CREATE TABLE | `traveller_added` | 3,495 | `(group_size, destination, toDate(timestamp), group_id, id)` | Highest-volume table; ~2.9 adds per started group. |
| `traveller_removed` | CREATE TABLE | `traveller_removed` | 70 | `(group_size, destination, toDate(timestamp), group_id, id)` | Rare (2% of started groups touch removal). |
| `group_submitted` | CREATE TABLE | `group_submitted` | 688 | `(group_size, destination, toDate(timestamp), group_id, id)` | Conversion event for this flow; 688/1,200 = 57.3% step-through from `group_started`. |
| — | no ALTER | — | n/a | — | No spec event shares an existing table's grain; see below. |
| — | no MATERIALIZED VIEW | — | n/a | — | Raw volume (5,453 rows total) too small to justify pre-aggregation. |

---

## CREATE vs ALTER call

All four events were evaluated against the 8 existing tables in `ddl.sql` / `instrumentation_notes.md`:

- **`group_started`** — fires when "the group flow begins," after `application_id` already exists (100% present, distinct-count matches row-count in the profile, i.e. it never precedes `application_started`). It is not the same moment as `application_started` (that event fires once per application at the very start of the funnel, well before a user opts into a group flow) — it's a **later, distinct occurrence** with its own identity (`group_id`). → **CREATE TABLE**.
- **`traveller_added`** / **`traveller_removed`** — each co-traveller add/remove is its own discrete UI action, potentially firing many times per group (3,495 adds across 1,200 groups = 2.9/group on average). No existing table captures a per-traveller sub-event at this grain. → **CREATE TABLE** each.
- **`group_submitted`** — the group's submission moment. It is a candidate to consider against `application_started`/`purchase_completed`, but neither shares its grain: `application_started` already happened earlier (creates `application_id`, not `group_id`), and `purchase_completed` is the *payment* moment, not group submission — the spec doesn't describe these as co-occurring ("alongside"/"as part of" language, the signal used elsewhere in this project to justify an ALTER, is absent here). It is its own moment with its own row identity. → **CREATE TABLE**.

No event in this spec is a same-moment attribute addition to an existing table's row, so **no `ALTER TABLE` statements were issued.**

### Entity reconciliation — `group_size` vs `co_travelers` (relationship.md)

`relationship.md` §"Entities the incoming specs will add" flags that spec 02's `group_id`/`group_size` **conflicts with the existing `co_travelers` column** (present in the shared 30-column envelope on all 8 existing tables, recording a co-traveller count on the *application*) and instructs: *"Reconcile before instrumenting; don't create a parallel model."*

Resolution applied: `co_travelers` is **not present in any of spec 02's sampled events** (absent from the profile's field×event grid for all four events), so there is no field-level duplication to remove — the new tables do not re-emit a `co_travelers`-shaped column. The reconciliation instead is **analytical, not schematic**: `group_size` (this spec, keyed by `group_id`) and `co_travelers` (existing envelope, keyed by `application_id`) both describe "how many people are on this trip" for the *same* `application_id` and can diverge (e.g. `co_travelers` set at `application_started` before the group flow finalizes who's actually included). Any analysis that reports "group size" or "co-traveller count" **must state which column it used** and, ideally, join `group_started.application_id = application_started.application_id` to compare the two rather than treating them as interchangeable. This is carried forward as a caveat below — no schema change was made to `application_started`.

---

## Column choices

Columns included are exactly those present in `spec.md`'s event descriptions and `profile.md`'s field list for each event — no envelope column absent from both (e.g. `client_ip`, `latitude`/`longitude`, `gclid`/`fbclid`, `citizenship`, `is_guest`, `funnel_type`, `duplicate_id`, `is_back_filled`) was invented, since the profiler shows zero presence for them across all 5,453 sampled rows.

| Column | Type chosen | Reasoning |
|---|---|---|
| `id` | `UUID` | Structural row id, matches envelope; not nullable. Not used in `ORDER BY` leading position — see D8 discussion below. |
| `timestamp` | `DateTime` | Matches envelope; second precision; partition source. |
| `user_id` | `FixedString(28)` | `relationship.md` states as a live-DB fact that `user_id` "is exactly 28 characters everywhere" across all existing tables. Sample values in every one of the four events (`08XPyMerzcBikSv3RkbZ8L7HyJzJ`, `FtE340IwZiAQ8Zn70o8LBS0q1oUQ`, etc.) are 28 characters, confirming the same convention holds for this spec. **Deliberate upgrade** from production's plain `String` — justified because the length is a confirmed, universal fixed format, not a guess (skill rule `schema-types-native-types`: prefer native/fixed types when the format is truly fixed). |
| `application_id` | `FixedString(36)`, **not nullable** | Profile shows 100% presence (0 nulls) across all four events — unlike `destination_card_clicked`/`search_typed` in the existing schema (where `application_id` is legitimately absent pre-application), the group flow only fires *after* `application_started`, so absence is not a valid state here. Stored **post-normalization** (see D2 below) to the live DB's 36-char hyphenated form, which is a confirmed fixed length once normalized — hence `FixedString(36)` rather than `Nullable(String)`. **Mandatory D2 normalization + overlap check** (see Risks). |
| `group_id` | `String`, not nullable | New entity, no live-DB precedent to normalize against. Profile shows 100% presence, high uniqueness (100% unique in `group_started`/`group_submitted`; 34.3% unique in `traveller_added` because each group has ~2.9 adds). Sampled values look like a consistent 32-char hex token, but the profiler emits no explicit length-uniformity statistic (only top-values), so per the "never guess a type" rule this was **not** upgraded to `FixedString(32)` — kept as plain `String`. High-cardinality identifier → never `LowCardinality`/`Enum` (rule `schema-types-lowcardinality`: >10K-style unbounded identifiers stay `String`). |
| `group_size` | `UInt8`, not nullable | Profiler: 100% present, 0 nulls, integer range `[2, 6]` in every event. Fits easily in `UInt8` (rule `schema-types-minimize-bitwidth`). Not nullable — no null observed and no null semantic (`schema-types-avoid-nullable`: this is a **deliberate upgrade** over the production baseline's blanket `Nullable`, justified by the profiler's explicit 100%-presence stat, not assumed). |
| `app_version` | `LowCardinality(String)`, not nullable | 3 distinct values (`7.44.0`/`7.45.2`/`7.46.0`), profiler-flagged `LC`, 100% present. Variable-length-in-principle version strings with tiny cardinality → `LowCardinality(String)` per `schema-types-lowcardinality` (not `FixedString`: `7.44.0` (6 chars) vs `7.46.0` (6) happen to match today but the format isn't a guaranteed fixed-width contract, and K7 already shows `app_version` is an unreliable, randomly-assigned field — no reason to over-constrain it). |
| `city` | `LowCardinality(String)`, not nullable | 7 distinct values, ragged lengths (`Mumbai` 6, `New York` 8, `Singapore` 9) → disqualified from `FixedString`; genuinely variable-length low-cardinality categorical → `LowCardinality(String)`. |
| `client_lib` | `LowCardinality(String)`, not nullable | 2 distinct values (`mobile-rn`, `web-js`), ragged lengths → `LowCardinality(String)`. |
| `destination` | `FixedString(2)`, not nullable | 14 distinct values sampled, all 2-char uppercase ISO-2 codes (`MY`, `TH`, `US`, ...). `relationship.md` documents the **full** 27-value destination vocabulary for this envelope column as clean 2-char uppercase codes with **no catch-all/"OTHER" bucket** (unlike `geoip_country_code`, which explicitly has one) — this is the disqualifying check the string-type decision calls for, and it passes. → `FixedString(2)`, a deliberate upgrade over production's `Nullable(String)`. |
| `device_type` | `LowCardinality(String)`, not nullable | 4 distinct values (`ios`, `android`, `web-user-b2c`, `Desktop`) — ragged lengths (3–12 chars) and known casing inconsistency (D9: `Desktop` vs `ios`) → `LowCardinality(String)`, not `FixedString`/`Enum` (D9 notes this field already mixes conventions; forcing an `Enum` risks insert-time rejection if a 5th value with different casing appears). |
| `geoip_country_code` | `LowCardinality(String)`, not nullable | 7 distinct values sampled, subset of the envelope's known 10-value set which **includes the `OTHER` catch-all** (5 chars) per `tables/index.md` — this directly disqualifies `FixedString(2)` even though every code sampled here happens to be 2 chars (the exact trap the string-type decision guide calls out). → `LowCardinality(String)`. |
| `os` | `LowCardinality(Nullable(String))` | 4 distinct values, but **6.3%/6.5%/6.3%/4.3% null** across the four events — matches the existing envelope's documented `os` null texture (5.95% NULL system-wide, "some Android rows have `os = NULL`"). This is the **one** column in the spec's field list with a real null rate, so it's the one column kept `Nullable` (rule `schema-types-avoid-nullable`: nullable only when semantically/empirically required — here it is). |
| `traveller_index` (`traveller_added`, `traveller_removed`) | `UInt8`, not nullable | Integer range `[0, 5]`, 100% present in both events it appears in. |
| `docs_complete` (`traveller_added`) | `Bool` | Profiler type `bool`, 2 distinct values (`true`/`false`), 100% present, no null. `Bool` is ClickHouse's native alias for `UInt8` with 0/1 semantics — direct fit (rule `schema-types-native-types`). |
| `relation` (`traveller_added`) | `LowCardinality(String)`, not nullable | 5 distinct values (`friend`/`spouse`/`child`/`sibling`/`parent`), all present, profiler-flagged `LC`. Considered `Enum8` (rule `schema-types-enum`) but **rejected**: family-relation taxonomies are exactly the kind of set a product team extends (e.g. adding `partner`, `guardian`) without a coordinated schema migration, and the existing 8 tables never use `Enum` for any comparable categorical (`device_type`, `citizenship`) specifically to avoid ingestion breaking on an unseen value — same risk applies here, so `LowCardinality(String)` was kept instead. |
| `travellers_submitted` (`group_submitted`) | `UInt8`, not nullable | Integer range `[1, 6]`, 100% present. |

---

## ORDER BY / PARTITION BY reasoning

All four tables use:

```sql
PARTITION BY toYYYYMM(timestamp)
ORDER BY (group_size, destination, toDate(timestamp), group_id, id)
```

- **`PARTITION BY toYYYYMM(timestamp)`** — matches the existing 8 tables' convention and stays well inside the 100–1,000 bound in `schema-partition-low-cardinality` (≤12 partitions/year, and the sampled window is only 3 weeks of June 2026).
- **`ORDER BY` avoids the D8 trap.** The existing 8 tables lead with the random `id` UUID, which `known_issues.md` D8 flags as defeating the primary index (no query filters by `id`, so only partition pruning helps). This spec's tables instead lead with real filter columns, per `schema-pk-prioritize-filters` and `schema-pk-plan-before-creation`.
- **Column order follows `schema-pk-cardinality-order`** (low-to-high cardinality, coarse-to-fine): `group_size` (5 distinct values) leads because it is the PM's headline segment ("completion rate by group size — where do large groups fall off?"); `destination` (14 distinct, `FixedString(2)`) is next as the second-most-asked segment cut ("which destinations drive group applications?"); `toDate(timestamp)` follows for date-range filtering at 16-bit granularity instead of full `DateTime` (per the `schema-pk-cardinality-order` tip); `group_id` (medium-high cardinality, ~1,200–1,268 distinct per table) supports the per-group joins all four PM questions require (funnel step-through, add/remove churn, `docs_complete` bottleneck); `id` trails as a final uniqueness tie-breaker, mirroring the `(tenant_id, event_date, event_id)` pattern in `schema-pk-plan-before-creation`.
- The same key was applied to **all four tables** deliberately, even though `traveller_added`/`traveller_removed`/`group_submitted` will most often be joined to `group_started` via `group_id` — a shared physical layout keeps cross-table funnel and churn queries (e.g. `group_started` join `group_submitted` on `group_id`, or counting adds/removes per `group_id`) predictable and index-friendly on both sides.

---

## Materialized view decision

**Not built.** `query-mv-incremental` (skill, impact HIGH) frames MVs as a fix for queries that would otherwise "scan billions of rows" — pre-aggregating so a dashboard "reads thousands of rows instead of billions." This spec's total volume is **5,453 rows across all four tables** (688 in the smallest funnel-relevant table, 3,495 in the largest). A full scan of any of these tables, or a join across all four, costs nothing meaningful at this scale — the incremental-MV mechanism exists to avoid a cost that doesn't exist here.

More importantly, every PM question in `spec.md` needs **row-level, not pre-aggregated, detail**:
- "Completion rate by group size" only needs `GROUP BY group_size` over `group_started`/`group_submitted` — cheap ad hoc, and it's a ratio the analyst will want to slice differently each time (by destination, by month) rather than a single fixed rollup.
- "Add/remove churn" and "is `docs_complete` the bottleneck for big groups" both require per-traveller, per-event inspection (individual `traveller_index`/`relation`/`docs_complete` values) — a `-State`/`-Merge` aggregate table would discard exactly the detail these questions need.

If group volume grows by orders of magnitude in production, a monthly `AggregatingMergeTree` rollup of `group_started`→`group_submitted` step-through by `(group_size, destination, month)` (per `query-mv-incremental`'s pattern) would become worth revisiting — but that is not justified by today's profile.

---

## Risks / caveats to carry forward

- **D2 (mandatory before deploy).** `application_id` must be normalized from the spec's 32-char unhyphenated hex to the live DB's 36-char hyphenated UUID on ingest (see the comment block at the top of `ddl.sql`). Before declaring any of these four tables ready, run the mandatory overlap check from `known_issues.md` D2, adapted per table, e.g. for `group_started`:
  ```sql
  SELECT round(100.0 * uniqExactIf(application_id, application_id IN (
           SELECT application_id FROM clickathon.application_started))
         / uniqExact(application_id), 2) AS overlap_pct
  FROM clickathon.group_started
  ```
  (repeat for `traveller_added`, `traveller_removed`, `group_submitted`). >90% → proceed; 1–90% → proceed but state coverage in every insight; 0% → stop and report as a finding, analyze standalone only.
- **`co_travelers` vs `group_size` divergence** (relationship.md). These are two different columns, on two different grains (`application_id` vs `group_id`), that both claim to describe party size for the same trip. Any report on group/family size must name which column it used; do not average or compare them without an explicit `application_id` join, and expect them to disagree since `co_travelers` is set once at `application_started` while `group_size` can change as travellers are added/removed afterward.
- **D9 casing/vocabulary collisions.** `destination` here is upper-case ISO-2 (consistent with the existing envelope), and this spec introduces no new colliding vocabulary (`relation`'s values — friend/spouse/child/sibling/parent — don't overlap `purpose`'s tourist/tourism collision). No new D9 instance found, but flag if a future spec adds a `purpose`-like field to the group flow.
- **Funnel time-ordering (D1/§4 of relationship.md).** Do not assume `group_started.timestamp < traveller_added.timestamp < group_submitted.timestamp` holds without checking monotonicity first (`countIf(t_later >= t_earlier) / count()`), per D1's guidance for new feature tables — the existing funnel tables show up to 47.8% non-monotonicity between adjacent stages, and this has not yet been verified for the group flow.
- **Small-n caution.** `traveller_removed` has only 70 rows; any churn-rate or removal-driver analysis on it should state the small sample size rather than presenting rates with false precision.
