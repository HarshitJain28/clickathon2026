# C-ATLYST

An agentic analytics pipeline for ClickHouse. Point it at a feature spec
(`spec.md` + `events.ndjson`) and it designs the schema, loads the data,
documents what it did, answers the PM's questions against the live database,
and folds every finding back into a shared knowledge base.

**→ To actually run it, see [RUN.md](RUN.md).**

---

## The three agents

Each agent is a separate process built on the Claude Agent SDK, with its own
system prompt and its own narrow set of tools. They never call each other
directly — they communicate through files on disk and through the context
wiki, which keeps each one independently runnable and debuggable.

### 1. Instrumentation Agent — `instrumentation_agent.py`

Designs the ClickHouse DDL for a new feature spec.

Reads the spec, a deterministic statistical profile of its raw events, the
ground-truth DDL of the existing production tables, and the context wiki.
Produces:

- **`ddl.sql`** — `CREATE TABLE` / `ALTER TABLE ADD COLUMN` /
  `CREATE MATERIALIZED VIEW`, whichever actually fits each event. Executable
  as-is: database-qualified and idempotent (`IF NOT EXISTS`).
- **`justification.md`** — the reasoning behind every table, column type, and
  sort key, each citing the specific profiler statistic or wiki fact that
  drove it.

It is constrained to facts: it may not invent a column that isn't in the spec
or the profile, and every type/nullability choice must cite its evidence.

### 2. Analytics Agent — `analysis_agent.py`

Answers exactly one PM question per run, against the **live** ClickHouse
Cloud database via its remote MCP server.

- Always writes `qNN.md` — a short Question/Answer file.
- Additionally writes `qNN_report.html` — a self-contained HTML report with a
  visualization — **only** when the question actually asks for a
  report/chart/dashboard. Plain factual questions get a prose answer.
- Orients from the context wiki index-first, opening only the pages a given
  question needs, rather than reading the whole wiki every time.
- **Read-only against `context/`.** Several of these run concurrently (one per
  question), and concurrent writes to the same wiki files would corrupt them.
  Its `qNN.md` — cited with the exact query and result — *is* the evidence the
  Context Agent later consolidates.

If the data needed to answer a question isn't live yet, it says so and names
the missing table/column instead of fabricating a number.

### 3. Context Agent — `context_agent.py`

Maintains `context/` — the shared wiki both other agents read from.

Runs **twice** per pipeline, on purpose:

- **Pass 1**, after the Loader: publishes the new/altered table pages and any
  known-issue caveats the load surfaced, so the Analytics Agent has them to
  orient from *before* it starts querying.
- **Pass 2**, after all the Analytics Agents finish: as the single writer, it
  folds every `qNN.md` finding (known-issue re-verdicts, table caveats,
  reusable metrics) into the wiki.

It has no database access of its own. It may only cite evidence produced by
something that did have access — `load_report.md` or a `qNN.md` — never
re-derive or extrapolate a number.

---

## Supporting (deterministic, non-LLM) components

Data correctness work is deliberately *not* done by a model:

| File | Role |
|---|---|
| `profiler.py` | Stdlib-only NDJSON profiler. Per-field presence, null %, distinct counts, uniqueness ratio, ranges. Its output is the factual basis the Instrumentation Agent must cite. |
| `loader.py` | Executes `ddl.sql`, buckets `events.ndjson` by event → table, flattens nested objects, applies required id normalizations, and runs the verification queries the justification cites. Writes `load_report.md`. |
| `question_extractor.py` | Pulls the "Questions the PM will ask" list out of `spec.md` and runs one Analytics Agent per question, concurrently. |
| `orchestrator.py` | Chains every stage in order and owns the run's trace. |

---

## Pipeline

```
spec.md + events.ndjson
        │
        ├─ profiler.py ─────────────► profile.md
        │
        ▼
  Instrumentation Agent ────────────► ddl.sql, justification.md
        │
        ▼
      loader.py ─────────────────────► live ClickHouse tables + load_report.md
        │
        ▼
  Context Agent (pass 1) ───────────► context/ table pages, known issues
        │
        ▼
  question_extractor.py
        └─ Analytics Agent ×N ───────► analysis/qNN.md (+ qNN_report.html)
        │
        ▼
  Context Agent (pass 2) ───────────► findings consolidated into context/
```

`orchestrator.py` runs all of this end to end. The web UI runs the same
stages but **pauses after the Instrumentation Agent** so a human can review
the proposed schema before anything touches the database (see below).

---

## Tracing

Every run produces **one Langfuse trace**, named `onboard-spec:<spec>` with
`sessionId` set to the spec slug.

This is not automatic — each agent is its own OS process building its own
Langfuse client, which by default yields one disconnected trace per process.
`langfuse_trace.py` threads a single trace through all of them: the
orchestrator opens the root span and exports its ids via the environment;
each child process attaches its work underneath.

```
onboard-spec:04_checkout_recovery        [1 root]
├── stage:instrumentation → instrumentation_agent → its tool calls
├── stage:loader
├── stage:context_1       → context_agent
├── stage:analysis        → question_extractor → analysis agents
└── stage:context_2       → context_agent
```

Token usage and cost are recorded per model call, so a run's total spend is
visible on the trace.

Standalone runs are unaffected: with no parent ids in the environment, each
script traces on its own exactly as before.

---

## Visualization (optional)

Two layers, both optional:

**HTML reports.** When a question asks for a chart/report, the Analytics
Agent writes a self-contained `qNN_report.html` — inline CSS/JS, no CDN, no
network calls — so it renders correctly opened straight from disk.

**Web UI** (`webui/`) — a Node/Express front end over the same Python
scripts. Nothing is reimplemented there; it shells out to the identical
entrypoints. It adds:

- A chat interface for ad-hoc questions, with the agent's live progress
  streamed as it works.
- A spec-onboarding flow that **pauses for human approval**: it shows the
  proposed `ddl.sql` side by side with `justification.md`, and nothing runs
  against ClickHouse until you approve. Rejecting ends the run there.
- Persistent history — chats and onboarding runs are stored on disk (not
  browser storage), so they survive refreshes and server restarts.

---

## Layout

```
├── orchestrator.py            end-to-end pipeline
├── instrumentation_agent.py   agent 1 — schema design
├── analysis_agent.py          agent 2 — answers one PM question
├── context_agent.py           agent 3 — maintains the wiki
├── loader.py                  deterministic DDL execution + ingestion
├── profiler.py                deterministic event profiler
├── question_extractor.py      spec questions → concurrent analysis agents
├── langfuse_trace.py          one trace per run, across processes
├── context/                   the wiki the agents read and maintain
├── ps/Atlys/                  problem statement, base context, sample specs
├── out/<spec>/                per-spec output (ddl, justification, analysis)
└── webui/                     optional Node front end
```
