# Atlys — Click-a-thon 2026 Proposal
## Stage 0: Context Bootstrap (Match & Correct)

### Background

The challenge asks us to build three agents on ClickHouse — **Instrumentation**, **Analytics**, and **Context** — plus tracing (Langfuse) and a visualization layer. We're given a `base_context.md` file describing the business, entities, and metrics, but the problem statement itself flags it directly:

> "Fair warning: the base context layer you receive is not perfect. Treat it with suspicion."

So before the Analytics or Instrumentation agents can trust the context layer, it needs to be checked against what the data actually shows.

### Proposal

**Before any other agent runs, run a one-time Bootstrap Run** that uses the **ClickHouse MCP server** to compare `base_context.md` against the real event tables in ClickHouse, and produce a corrected, verified context layer for the rest of the pipeline to build on.

This becomes **Stage 0** of the overall system — it runs once at startup (and again whenever new tables land), ahead of Instrumentation and Analytics.

There are two flows:

Flow 1 -> User uploads spec.md and json file -> Instrumentation agent (with human in the loop)-> Context agent -> Analysis Agent
The visualization can also cover , how the schmema is created, why the use of view making 100 transparency. (This is the meat)

Flow 2 -> PM visits the app, asks the question, gets the response.


---

## Flow 1 


## Stage 1: Instrumentation Agent

> Take in the spec folder from the user. Run a parsing layer that parses the JSON data file and producing a summary of events in the json(Distinct event, distinct values, null values) allowing our instrumentation agent what type of data types to use.

### Scope

1. **Read the context layer** — Read the context, to understand the business, entities, and existing schema conventions before designing anything new.
2. **Load all ClickHouse-related skills/tooling** Load all the clickhouse related instructions and skills for designing the schema.
3. **Generate and apply the schema** — based on the feature spec and its raw NDJSON sample, design the table schema,(Human in the loop), create it, and insert the mapped data.
4. **Verify** — confirm the table was created correctly and the data was inserted as expected.
5. **Record the change** — write out whatever schema changes were made to a `schema.sql` file, so there's a durable, reviewable record alongside the trace.

## Stage 2: Context Agent (plan on using an LLM wiki?)

### Context wiki structure

The context layer is stored as a wiki — one file per concern, so the Context Agent can update a single file instead of rewriting one large document, and the diff/changelog stays readable:

```
context/
├── index.md          — entry point; links to everything below
├── business.md        — business overview, north-star metric, funnel
├── tables/             — one file per table (schema, columns, ownership)
├── metrics/            — one file per metric (formula, definition, owner)
├── known-issues/       — one file per known issue/quirk
└── relationship.md     — entity relationships / join map
```

### Scope

1. Updates the entities,relationship, metrics, based on Instrumentation Agent changes.
2. Updates the project context based on the schema created and data inserted.

## Stage 3: Analytical Agent

### Scope

1. Reads the context layer, the spec, and the PM questions.
2. Based on the questions and context, creates a report.
3. Update the Context with the new findings 



## planned if time permits

1. We can even have a schedule: based on the most-asked PM questions, the Instrumentation Agent can learn and create more intelligent materialized views for those queries, for faster responses. - Additional thing, not asked, will demonstrate self learning. 
2. Agent to Agent communication - will look good on langfuse
