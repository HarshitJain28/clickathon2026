# Optimizers

## Track

Atlys

## Project

**C-ATLYST** — like a catalyst, it speeds up how fast a PM gets from question
to answer. (**C**lickHouse + **ATLYS**, and it reads as *catalyst*.)

## Team Members

- Harshit Jain ([@HarshitJain28](https://github.com/HarshitJain28))
- Akshit ([@imakshit04](https://github.com/imakshit04))
- _TBD (handle)_

## What it does

Point C-ATLYST at a feature spec (`spec.md` + `events.ndjson`) and it designs
the ClickHouse schema, loads the data, documents what it did, answers the PM's
questions against the live database, and folds every finding back into a
shared knowledge base.

The problem it removes: a PM's question used to mean pinging the data team,
waiting while someone hunted for the right table, double-checking stale docs
with an engineer, and getting an answer days later — and if the feature wasn't
instrumented yet, waiting on the dev team to design and ship a table before
anyone could even ask. C-ATLYST does both ends of that itself.

## Hosted Demo

_Placeholder — link to be added._

## Demo Video

_Placeholder — link to be added._

## Architecture

Full write-up in **[Architecture.md](Architecture.md)**.

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

`orchestrator.py` runs all of this end to end. The web UI runs the same stages
but **pauses after the Instrumentation Agent** so a human can review the
proposed schema before anything touches the database.

### The three agents

Each agent is a separate process built on the Claude Agent SDK, with its own
system prompt and its own narrow set of tools. They never call each other
directly — they communicate through files on disk and through the context
wiki, which keeps each one independently runnable and debuggable.

**1. Instrumentation Agent — `instrumentation_agent.py`**

Designs the ClickHouse DDL for a new feature spec. Reads the spec, a
deterministic statistical profile of its raw events, the ground-truth DDL of
the existing production tables, and the context wiki. Produces:

- **`ddl.sql`** — `CREATE TABLE` / `ALTER TABLE ADD COLUMN` /
  `CREATE MATERIALIZED VIEW`, whichever actually fits each event. Executable
  as-is: database-qualified and idempotent (`IF NOT EXISTS`).
- **`justification.md`** — the reasoning behind every table, column type, and
  sort key, each citing the specific profiler statistic or wiki fact that
  drove it.

It is constrained to facts: it may not invent a column that isn't in the spec
or the profile, and every type/nullability choice must cite its evidence. It
loads the ClickHouse best-practices skill so schema and query design follow
those rules rather than the model's memory.

**2. Analytics Agent — `analysis_agent.py`**

Answers exactly one PM question per run, against the **live** ClickHouse Cloud
database via its remote MCP server.

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

**3. Context Agent — `context_agent.py`**

Maintains `context/` — the shared wiki both other agents read from. Runs
**twice** per pipeline, on purpose:

- **Pass 1**, after the Loader: publishes the new/altered table pages and any
  known-issue caveats the load surfaced, so the Analytics Agent has them to
  orient from *before* it starts querying.
- **Pass 2**, after all the Analytics Agents finish: as the single writer, it
  folds every `qNN.md` finding (known-issue re-verdicts, table caveats,
  reusable metrics) into the wiki.

It has no database access of its own. It may only cite evidence produced by
something that did have access — `load_report.md` or a `qNN.md` — never
re-derive or extrapolate a number.

### The context layer

Plain markdown under `context/`, structured as an **LLM wiki**: every page
carries frontmatter (`id`, `kind`, `status`, `confidence`, `source`,
`last_verified`) so an agent can judge relevance and trust from the header
alone, and each directory's `index.md` is a small regenerated cache an agent
reads first to pick the 2–3 pages it actually needs.

It isn't seeded from the handed-over `base_context.md` as-is — that document is
warned to be imperfect. A **Stage 0 bootstrap** tested every factual claim in
it against the live database via the ClickHouse MCP server and recorded each as
`verified` or `refuted` with the query that proved it, keeping only its
*business intent* unchanged. Findings are in `data_vs_base_context.md`.

### Supporting (deterministic, non-LLM) components

Data correctness work is deliberately *not* done by a model:

| File | Role |
|---|---|
| `profiler.py` | Stdlib-only NDJSON profiler. Per-field presence, null %, distinct counts, uniqueness ratio, ranges, shape drift, duplicate IDs. Its output is the factual basis the Instrumentation Agent must cite. |
| `loader.py` | Executes `ddl.sql`, buckets `events.ndjson` by event → table, flattens nested objects, applies required id normalizations, and runs the verification queries the justification cites. Writes `load_report.md`. |
| `question_extractor.py` | Pulls the "Questions the PM will ask" list out of `spec.md` and runs one Analytics Agent per question, concurrently. |
| `orchestrator.py` | Chains every stage in order and owns the run's trace. |

### Tracing

Every run produces **one Langfuse trace**, named `onboard-spec:<spec>` with
`sessionId` set to the spec slug.

This is not automatic — each agent is its own OS process building its own
Langfuse client, which by default yields one disconnected trace per process.
`langfuse_trace.py` threads a single trace through all of them: the
orchestrator opens the root span and exports its ids via the environment; each
child process attaches its work underneath.

```
onboard-spec:04_checkout_recovery        [1 root]
├── stage:instrumentation → instrumentation_agent → its tool calls
├── stage:loader
├── stage:context_1       → context_agent
├── stage:analysis        → question_extractor → analysis agents
└── stage:context_2       → context_agent
```

Token usage and cost are recorded per model call, so a run's total spend is
visible on the trace. Standalone runs are unaffected: with no parent ids in the
environment, each script traces on its own.

### Visualization (optional)

**HTML reports.** When a question asks for a chart/report, the Analytics Agent
writes a self-contained `qNN_report.html` — inline CSS/JS, no CDN, no network
calls — so it renders correctly opened straight from disk.

**Web UI** (`webui/`) — a Node/Express front end over the same Python scripts.
Nothing is reimplemented there; it shells out to the identical entrypoints. It
adds a chat interface for ad-hoc questions with live streamed progress, a
spec-onboarding flow that **pauses for human approval** (showing the proposed
`ddl.sql` next to `justification.md`, running nothing against ClickHouse until
you approve), and persistent on-disk history.

## How we built it

| | |
|---|---|
| **Database** | ClickHouse Cloud |
| **Agents** | Claude (`claude-sonnet-5`, pinned) via the Claude Agent SDK |
| **Live data access** | ClickHouse remote MCP server (`mcp.clickhouse.cloud`) |
| **Ingestion** | `clickhouse-connect` (HTTPS, port 8443) |
| **Tracing** | Langfuse |
| **Pipeline** | Python 3.11+, stdlib subprocess chaining |
| **Context store** | Markdown wiki (`context/`) |
| **Web UI** | Node/Express + vanilla JS |

Things worth calling out:

- **Every stage is its own process, handing off through files.** No in-process
  agent-to-agent calls. It costs a subprocess per stage, and buys independent
  resumability, inspectability, and the ability to run any single agent
  standalone while debugging.
- **The wiki has exactly one writer.** Analysis agents run concurrently and are
  read-only against `context/`; the Context Agent's pass 2 is the single writer
  that folds their findings in, so nothing races.
- **Correctness work is deterministic, not modelled.** Profiling, loading,
  normalization, and verification queries are plain Python — the model designs
  and explains, it doesn't compute the numbers it cites.
- **Cross-process trace stitching** (`langfuse_trace.py`) so a ~6-process run
  reads as one tree instead of six disconnected traces, including across the
  web UI's human-approval pause.

## How to run it

Full detail — env vars, both ClickHouse auth paths, per-stage commands,
troubleshooting — in **[RUN.md](RUN.md)**. The short version:

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Create a `.env` in the repo root (see [RUN.md §2](RUN.md) for the full table):

```bash
CLAUDE_OAUTH_TOKEN="..."           # from: claude setup-token
CLICKHOUSE_HOST="<your-service>.clickhouse.cloud"
CLICKHOUSE_PASSWORD="..."
CLICKHOUSE_DATABASE="clickathon"
LANGFUSE_PUBLIC_KEY="..."          # optional; without it, runs are just untraced
LANGFUSE_SECRET_KEY="..."
```

**Option A — one command, end to end:**

```bash
python orchestrator.py ps/Atlys/specs/01_express_checkout
```

Runs Instrumentation Agent → Loader → Context Agent → Analytics Agents (one per
PM question, concurrently) → Context Agent. Output lands in `out/<spec>/`; the
wiki under `context/` is updated in place (review with `git diff context/`).

**Option B — with the web UI:**

```bash
cd webui
npm install
npm start                          # http://localhost:3000
```

Same pipeline, plus a chat interface and a spec-upload flow with a human
approval gate before anything touches ClickHouse.

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
