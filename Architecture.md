# Architecture

## Overview

C·ATLYST is a pipeline of three Claude-based agents, chained by a thin
Python orchestrator, that turns two inputs — a feature spec (`spec.md`) and
a sample of raw events (`events.ndjson`) — into (a) a ClickHouse table for
the new data, (b) an updated markdown context wiki describing that table
and any quirks found in it, and (c) grounded answers to the PM questions
listed in the spec.

`orchestrator.py` has no logic of its own beyond invoking each step as a
subprocess, in order, and stopping on the first non-zero exit code:

```
spec.md + events.ndjson
        │
        ▼
┌────────────────────┐
│ Instrumentation     │  reads context/ + prod ddl.sql, designs a new
│ Agent               │  ClickHouse schema, writes ddl.sql + justification.md
└─────────┬──────────┘
          ▼
┌────────────────────┐
│ Loader              │  deterministic Python — applies the DDL, loads
│ (not an LLM agent)  │  events.ndjson, writes load_report.md
└─────────┬──────────┘
          ▼
┌────────────────────┐
│ Context Agent       │  PASS 1 — publishes the new table page + any
│ (pass 1)            │  known-issue caveats to context/ BEFORE analysis runs
└─────────┬──────────┘
          ▼
┌────────────────────┐
│ Question Extractor  │  parses "## Questions the PM will ask" out of
│                      │  spec.md, fans out one Analysis Agent per question,
│                      │  all concurrent (ThreadPoolExecutor)
└─────────┬──────────┘
          ▼
┌────────────────────┐
│ Analysis Agent × N   │  read-only against context/, queries ClickHouse
│ (concurrent)         │  live via MCP, writes qNN.md (+ qNN_report.html)
└─────────┬──────────┘
          ▼
┌────────────────────┐
│ Context Agent       │  PASS 2 — single writer, consolidates every
│ (pass 2)            │  qNN.md's findings into context/
└─────────┬──────────┘
          ▼
  Answer(s) back to the PM
```

Every step hands off through **files on disk**, not in-process calls or
direct agent-to-agent messages — `orchestrator.py` invokes each stage as a
separate `subprocess.run(...)`, passing the same `out_dir` (and
`--context-dir`) along the chain. This keeps every stage independently
resumable, inspectable, and traceable, at the cost of an extra process
per step.

## The three agents and how they hand off

All three are Claude agents built on the `claude-agent-sdk` (`query()`
over `ClaudeAgentOptions`), each invoked as its own subprocess, pinned to
`claude-sonnet-5` so every run uses a known, consistently-priced model.

- **Instrumentation Agent** — reads the spec, the sample events' profile
  (`profile.md`, generated on demand), the current wiki, and the
  production `ddl.sql` for schema conventions. `profile.md` itself comes
  from `profiler.py`, a small deterministic (non-LLM) parser that reads
  `events.ndjson` and reports per-field presence/null %, type, cardinality,
  shape drift, and duplicate IDs per event type — so schema decisions are
  grounded in what the sample data actually looks like, not guesses.
  Designs and writes `ddl.sql` + `justification.md`. Tools: `Read, Glob,
  Grep, Write`. No database access of its own — the schema isn't applied
  until the Loader runs.
- **Loader** — not an LLM agent, plain Python. Applies the DDL and loads
  `events.ndjson` into ClickHouse via `clickhouse_connect`, writes
  `load_report.md`. A data-quality finding here (e.g. a 0% join-key
  overlap) does not stop the pipeline — it's recorded for the Context
  Agent to document, not treated as a failure.
- **Context Agent** — the only agent allowed to write to `context/`. Runs
  twice per spec: pass 1 reads the Instrumentation Agent's output
  (`ddl.sql`, `justification.md`, `profile.md`, `load_report.md`) and
  publishes the new table page and any known-issue caveats *before*
  Analysis runs, so Analysis has real facts to orient from instead of
  re-deriving them; pass 2, after every Analysis Agent has finished,
  consolidates all `qNN.md` findings into the wiki as the single writer,
  so nothing races. It has no live database access of its own — it only
  cites what the Loader and Analysis Agent already found.
- **Analysis Agent** — read-only against `context/` by design, so
  nothing writes to the wiki mid-flight while several of these run
  concurrently. It's the only agent with ClickHouse access, via the
  ClickHouse Cloud MCP server, so it can check its answer against live
  data rather than trusting the wiki's numbers blindly. One run per PM
  question, all concurrent; writes `qNN.md` and, when the question calls
  for it, a `qNN_report.html`.

## Where the context layer is stored, and why

The context layer is **plain markdown files under `context/`** — an
`index.md` entry point, `business.md`, `known_issues.md`,
`relationship.md`, `log.md`, plus one file per table under `tables/` and
one per metric under `metrics/`. No ClickHouse table or vector store
backs it.

Its structure follows an **"LLM wiki" pattern** (`context/SCHEMA.md`
cites Karpathy's Apr 2026 write-up on this, adapted here): every page
carries frontmatter (`id`, `kind`, `status`, `confidence`, `source`,
`last_verified`) so an agent can judge relevance and trust from the
header alone, and each directory's `index.md` is a small regenerated
cache an agent reads first to decide which 2–3 pages to open — file
selection by cheap index, not by scanning the whole wiki.

This was a deliberate choice for the shape of this problem, not an
oversight:
- The wiki's job is to hold a small number of durable, structured facts
  (schema, known join issues, metric definitions) that get read in full
  or by section, not searched by similarity — a flat file per concern is
  enough, and keeps diffs human-reviewable in a PR.
- One file per table/metric means an agent updates a single page instead
  of rewriting one giant document, and a human can read exactly what
  changed.
- It avoids a second stateful system to run and keep in sync. The
  Analysis Agent already has live ClickHouse access via MCP for anything
  that genuinely needs current data — the wiki only needs to hold the
  facts *about* the schema, not the schema's data.

**Bootstrap (Stage 0), before any of this is trusted.** The wiki isn't
seeded from the handed-over `base_context.md` as-is — that document is
warned to be imperfect. Every factual claim in it was tested against the
live database via the ClickHouse MCP server (schemas, distributions,
whether a claimed effect actually shows up) and recorded as `verified` or
`refuted` with the query that proved it; only the document's *business
intent* (why a metric matters) was kept as-is, since data can't verify
intent. This is a one-time pass, repeated whenever new tables land, and
its findings/method are recorded in `data_vs_base_context.md`.

The tradeoff: this doesn't scale to a very large number of tables/metrics
without some kind of retrieval on top of the flat files. **Graph-based
RAG over the context wiki is on our future-ideas list** for exactly that
reason — richer retrieval for relationships, joins, and metric lineage —
but is not implemented in this submission.

## Observability: Langfuse tracing, and ClickStack/LibreChat

**Langfuse is wired into every stage**, at two layers:

1. **One unified trace per run, across processes.** Each pipeline stage
   is its own OS process, which would normally scatter a single spec
   onboarding across ~6 disconnected Langfuse traces. `orchestrator.py`
   opens one root span (`onboard-spec:<spec_name>`) and, for each stage
   (Instrumentation, Loader, Context pass 1, Analysis, Context pass 2),
   a child span whose trace/span ids it exports into that subprocess's
   environment (`langfuse_trace.py`). Each agent picks those ids up via
   `attach_to_parent(...)` and nests its own spans underneath instead of
   starting a new trace — so the whole run reads as one tree. This falls
   back to a no-op when a script is invoked standalone (e.g. directly
   from the CLI), so it still gets its own trace as before. The web UI's
   human-approval gate (which must launch Instrumentation separately from
   the rest of the pipeline) mints the trace id itself and the
   orchestrator joins it rather than starting a second one.
2. **Per-agent detail inside each span**, via `langfuse.get_client()`
   and `@observe`: a run-level span (input paths, final summary), an
   agent-level span around the `query()` call to the Claude Agent SDK,
   a per-tool-call event for every Read/Write/Grep/MCP call, and a
   `generation` observation per LLM call with token usage and cost — so
   it shows up in Langfuse's usage/cost dashboards. Span metadata also
   captures turn count, tool-call count, duration, total cost, and
   error/stop-reason.

Each run prints its Langfuse trace URL and flushes on exit.

**ClickStack and LibreChat are not integrated in this submission.**
ClickStack appears only as a stretch idea in the pitch deck (a
system-level companion to Langfuse's agent/LLM-level tracing, if we had
more time); LibreChat isn't referenced anywhere in the codebase. Langfuse
covers what we actually needed for this scope — per-agent and per-LLM-call
tracing across a multi-process pipeline — so we didn't build the extra
system-level view or a chat-UI integration on top of it.

## LLM provider(s), and why

**Anthropic Claude**, exclusively, via the `claude-agent-sdk` package —
no other provider SDK (OpenAI, Google, etc.) is imported anywhere in the
repo, including the web UI, which only shells out to these same Python
scripts and never calls an LLM directly itself.

All three agents pin `AGENT_MODEL = "claude-sonnet-5"` rather than
letting the SDK/CLI resolve a default, so every run uses a known,
consistently-priced model instead of drifting onto whatever the default
happens to be at run time. Authentication goes through
`CLAUDE_CODE_OAUTH_TOKEN`, the env var the Claude Agent SDK's CLI
subprocess reads.

We chose the Claude Agent SDK specifically because this problem is a
multi-step, tool-using agent pipeline (read files, design schema, call
MCP, write files) rather than a single completion call — the SDK's
built-in tool-use loop, `ClaudeAgentOptions` (allowed tools, MCP server
registration), and native Langfuse-friendly usage/cost reporting per turn
fit that shape directly, without us having to hand-roll a tool-calling
loop against a lower-level chat completions API.
