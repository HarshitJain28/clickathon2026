---
id: doc.schema
kind: schema
status: verified
confidence: high
source: LLM-wiki pattern (Karpathy, Apr 2026) + Google Open Knowledge Format v0.2, adapted to this project
last_verified: 2026-08-01
links: [doc.index, doc.log]
---

# Wiki schema — rules for agents

**Every agent reads this before writing to the wiki.**

## Orientation — mandatory before any write

1. Read this file.
2. Read [index.md](index.md), then the relevant directory `index.md`.
3. Read the top of [log.md](log.md).
4. **Search for an existing page before creating one.**

Skipping step 4 is the main cause of duplicate pages.

## Structure

```
context/
├── index.md          entry point + verified environment
├── SCHEMA.md         these rules
├── log.md            changelog
├── business.md       business model, funnel, scale, trend
├── relationship.md   entities + join map + key formats
├── known_issues.md   data traps (D1–D9) + known-issue verdicts (K1–K7)
├── tables/           one page per table + index.md (holds the shared envelope)
└── metrics/          one page per metric + index.md
```

Deliberately flat. Add a directory **only** when a category exceeds ~6 pages.

| `kind` | Where |
|---|---|
| `index` | every directory + root |
| `schema` | `SCHEMA.md` |
| `changelog` | `log.md` |
| `business` | `business.md` |
| `relationship` | `relationship.md` — entities *and* how they join |
| `known_issues` | `known_issues.md` — anything wrong, suspicious, or trap-like |
| `table` | `tables/` |
| `metric` | `metrics/` |

## Frontmatter contract

Required on **every** page:

| Field | Rule |
|---|---|
| `id` | Stable, unique, `<kind>.<slug>`. **Never reused or renamed** — links resolve by it. |
| `kind` | From the table above. |
| `status` | `verified` · `refuted` · `unverifiable` · `unverified` |
| `confidence` | `high` · `medium` · `low` |
| `source` | Origin **and evidence**. Name the query or table, not just the doc. |
| `last_verified` | ISO date of last check against live data, or `null`. |
| `links` | `id`s of related pages. |

Unknown extra fields must be tolerated and preserved, never stripped.

### `status` is about evidence, not opinion

- **`verified`** — checked against the DB, holds.
- **`refuted`** — checked, and the data **disproves** it. Keep the page and record
  both claim and disproof. **Never delete a refuted claim** — its absence lets the
  claim creep back in from `base_context.md`.
- **`unverifiable`** — no data could test it. Distinct from refuted. Say "not
  instrumented", never "no effect".
- **`unverified`** — not yet checked. Default for anything new.

## Create vs update

- **Create** only for a genuinely new table or metric. Everything else updates in
  place.
- **Never** create `_v2` pages — git holds history.
- **Split** a page past ~350 lines.
- **Never silently overwrite a claim.** If new evidence contradicts an existing
  page, record both with dates and add an entry to `known_issues.md`.

## Citation and provenance

- Every non-obvious claim carries its evidence inline: the number, and the query
  or table that produced it.
- `source` must distinguish **assertion** (`base_context.md`) from **measurement**
  (`clickathon DB — <what was run>`). Business intent may only ever be an
  assertion; anything about data must be a measurement.
- Links are relative markdown paths. A link to a not-yet-written page is
  acceptable — it marks future work, not an error.

## Loader-actionable fix blocks (`known_issues.md`)

A `known_issues.md` entry's fenced ` ```sql ` fix block is read by `loader.py`
(deterministic, not LLM-parsed) whenever a spec's `justification.md` cites that
entry's id. To stay machine-actionable, a fix block must use exactly these
line markers:

- `-- normalize: raw_id -> <expr> AS <column>` — a single ClickHouse scalar
  expression, its input variable always named `raw_id`, ending `AS <column>`
  to name its target column. The loader batch-evaluates it via ClickHouse
  itself (`arrayMap(raw_id -> <expr>, {raw_ids:Array(String)})`) — never
  reimplemented in Python — and applies it to any table in the spec's
  `ddl.sql` that has a column of that exact name.
- `-- verify: <query>` — a runnable query containing the literal placeholder
  `<new_table>`, substituted with the bare table name at load time (write
  `clickathon.<new_table>` in the query yourself, as D2 does — the loader
  substitutes only the placeholder, not a `clickathon.`-prefixed one).

Not every entry needs a fix block — most of D1–D9/K1–K7 are narrative only.
Add one only when the check is meant to run automatically on every future
spec that hits the same trap.

## Index files are derived caches

Each `index.md` is regenerated from its siblings' frontmatter: id, title,
`status`, `confidence`, and a **one-sentence** description.

Keep descriptions to one sentence. An index is only cheap if it stays small — its
job is to let an agent orient over the whole wiki, then open 2–3 pages. Bloat
destroys that ratio.

**Regenerate the affected index as the last step of every write.**

## Update triggers

| When this happens | Update these |
|---|---|
| New table created | `tables/<name>.md`, `tables/index.md`, `relationship.md` (joins + key format), `log.md` |
| New spec instrumented | above, **plus** re-test any linked K-issue and update its verdict |
| New month of data loaded | `business.md` (trend), `metrics/*` (values), `tables/index.md` (row counts) |
| A claim is disproved | the page's `status` → `refuted`, add entry to `known_issues.md`, `log.md` |
| Any verification run | `last_verified` on every page touched |

## Update workflow

1. Orient (4 steps above).
2. Make the change, with evidence.
3. Update `status`, `confidence`, `last_verified` on every page touched.
4. Regenerate affected `index.md`.
5. Append to [log.md](log.md).
6. **Commit** — one logical change per commit, message stating what changed and
   what evidence drove it. Git history is the trace.

## Lint checklist

- [ ] All 7 required frontmatter fields on every page
- [ ] No duplicate or renamed `id`
- [ ] Every relative link resolves
- [ ] No `status: verified` with `last_verified: null`
- [ ] Every directory has a current `index.md`
- [ ] Index descriptions are one sentence
- [ ] No `verified` claim without a query or table named in `source`
- [ ] Refuted claims retained, not deleted

## Known weaknesses (accepted, watch them)

- **Volatile figures are restated across pages.** Row counts and rates appear in
  `business.md`, `relationship.md`, `known_issues.md`, `tables/`, `metrics/`.
  When data changes, **grep the old number** and update all occurrences — don't
  update one page and assume.
- **No staleness gradient.** Every page shares one `last_verified` date. K2 (an
  accelerating regression) needs re-checking far more often than the destination
  count. Consider adding `stale_after` if this wiki outlives the hackathon.
