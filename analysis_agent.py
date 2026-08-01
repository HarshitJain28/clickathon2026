"""Analysis Agent.

Answers one PM question at a time against the live ClickHouse Cloud database
(via its remote MCP server). Always writes a short Question/Answer markdown
file (e.g. out/.../q01.md). Additionally writes a self-contained HTML report
— with a visualization if warranted — but ONLY when the question itself asks
for a report/visualization/chart/dashboard; a plain factual question gets a
markdown-only answer. Where its finding genuinely updates something the
context wiki (context/) already claims — a stale figure, a re-testable known
issue, a metric worth documenting — it updates that page in place too,
following context/SCHEMA.md's rules, since (unlike the Context Agent) it has
live query evidence to back the edit.

Usage:
    python analysis_agent.py "<question>" [--out-dir DIR] [--index N]
                             [--context-dir DIR] [--service-id ID]
                             [--database NAME]
"""

import argparse
import asyncio
import os
import re
import sys
from pathlib import Path

# Windows consoles often default stdout/stderr to a non-UTF-8 codepage
# (e.g. cp1252), which can't encode characters like "→" that show up in the
# agent's own generated text — force UTF-8 so printing never crashes on it.
sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

from dotenv import load_dotenv

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ResultMessage,
    TextBlock,
    ToolUseBlock,
    query,
)

REPO_ROOT = Path(__file__).resolve().parent
CONTEXT_DIR = REPO_ROOT / "context"
VENDORED_SKILLS_DIR = REPO_ROOT / ".skills"
PROJECT_SKILLS_DIR = REPO_ROOT / ".claude" / "skills"

# Verified live environment, per context/index.md's "Verified environment"
# table — a starting fact for the agent, not an assumption it's told to skip
# checking (see the system prompt's connection section).
DEFAULT_SERVICE_ID = "78f5870d-894f-4405-bf4f-542014537dcb"
DEFAULT_DATABASE = "clickathon"
CLICKHOUSE_MCP_URL = "https://mcp.clickhouse.cloud/mcp"

load_dotenv(REPO_ROOT / ".env")

# The Claude Agent SDK's CLI subprocess reads CLAUDE_CODE_OAUTH_TOKEN; this
# repo's .env names it CLAUDE_OAUTH_TOKEN. Map it without requiring the .env
# file itself to use the SDK's exact variable name.
if os.environ.get("CLAUDE_OAUTH_TOKEN") and not os.environ.get(
    "CLAUDE_CODE_OAUTH_TOKEN"
):
    os.environ["CLAUDE_CODE_OAUTH_TOKEN"] = os.environ["CLAUDE_OAUTH_TOKEN"]

from langfuse import get_client, observe  # noqa: E402

langfuse_client = get_client()


def slugify(question: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", question.lower()).strip("_")
    return slug[:60] or "question"


@observe(name="discover_skills")
def discover_skills(vendored_dir: Path, project_dir: Path) -> list[str]:
    """Make every skill under .skills/ discoverable by the SDK's native
    `skills` option, and return the discovered skill names.

    Identical to instrumentation_agent.py's version — see there for why the
    symlinking happens (the SDK looks under .claude/skills/, this repo
    vendors skills one level up under .skills/).
    """
    if not vendored_dir.is_dir():
        return []

    project_dir.mkdir(parents=True, exist_ok=True)
    names = []
    for skill_md in sorted(vendored_dir.glob("*/SKILL.md")):
        name = skill_md.parent.name
        link_path = project_dir / name
        if not link_path.exists():
            target = skill_md.parent.resolve()
            if os.name == "nt":
                import _winapi

                _winapi.CreateJunction(str(target), str(link_path))
            else:
                link_path.symlink_to(target, target_is_directory=True)
        names.append(name)
    return names


def build_system_prompt(
    skill_names: list[str], context_dir: Path, service_id: str, database: str
) -> str:
    if skill_names:
        skills_section = f"""## Skills available

You have the following skill(s) available via the Skill tool: {", ".join(skill_names)}.
Invoke one if its trigger applies while you're writing a query (e.g. the
ClickHouse best-practices skill for query-shape/performance guidance) —
don't rely on memorized ClickHouse knowledge for anything it covers."""
    else:
        skills_section = """## Skills available

No skills were discovered under `.skills/` at runtime. Fall back to your own
ClickHouse knowledge."""

    return f"""You are the Analytics Agent for the Atlys agentic-analytics
project — the second of its three agents (Instrumentation, Analytics,
Context), per `{context_dir / 'index.md'}`'s own reading-priority table. You
answer exactly one PM question per run, against the live ClickHouse Cloud
database. Precision and honesty about what the data can and can't show
matter more than a polished-looking but wrong answer.

You always write a short Question/Answer markdown file. You additionally
write a self-contained HTML report — with a visualization inside it if
warranted — ONLY when the question itself is asking for a report or
visualization (see "Output" below for exactly how to tell the difference).
Most questions are plain factual questions and get a markdown-only answer;
don't over-produce.

## Connection

A ClickHouse Cloud MCP server is registered for you (tools prefixed
`mcp__clickhouse-cloud__`). The verified live service, per
`{context_dir / 'index.md'}`:
- serviceId: `{service_id}`
- database: `{database}`

Trust these as a starting point, but if anything behaves unexpectedly, use
the MCP server's own `list_databases`/`list_tables` tools to confirm rather
than assuming they're still correct forever — the wiki is a snapshot, the
live database is the current truth.

## Orient via the wiki first — index-driven, not a full-wiki read

Read the context wiki *before* touching the MCP server, but do it the way
`{context_dir / 'SCHEMA.md'}` itself prescribes: orient through index files
and only open the specific pages this question needs. Scanning the whole
wiki on every question burns tokens for no benefit — the indexes exist
precisely so you don't have to.

1. Always read `{context_dir / 'index.md'}` first, in full — it's short by
   design: verified environment, directory map, and one-sentence pointers to
   everything else. This is the only file you unconditionally read cover to
   cover.
2. From the question's subject (which metric, entity, table, or column it's
   actually about), decide what else you need, and open only that:
   - Question names or implies an existing metric (conversion, funnel,
     revenue, step-through, drop-off, etc.) → read
     `{context_dir / 'metrics' / 'index.md'}` (one-sentence descriptions per
     metric), then open only the specific metric page(s) that match. Reuse
     its formula instead of re-deriving one from scratch; cite the page.
   - Question names or implies specific tables/events → read
     `{context_dir / 'tables' / 'index.md'}` (shared envelope + table list)
     first, then open only the specific `{context_dir / 'tables'}/<name>.md`
     page(s) for tables the question actually touches — not all of them.
   - Question involves a join, an entity, or a relationship between two
     things → read `{context_dir / 'relationship.md'}`.
3. `{context_dir / 'known_issues.md'}` — skim its structure first (the D-trap
   headings and the K-issue verdict table are compact and index-like), then
   read in full only the specific entries whose subject overlaps this
   question's tables/metrics/columns. Never silently skip this file, but
   don't pay to read entries that plainly can't apply to what you're
   answering either. The wiki keeps growing, so nothing about which entries
   exist is hardcoded here — decide relevance from what you actually see,
   not from a remembered list.
4. If a page you opened links to another page that's clearly relevant to
   this specific question, follow that link. Otherwise don't — a link is an
   option to chase only when it matters here, not an obligation to read the
   whole graph.

## Synthesize before you call the MCP server

Before your first `mcp__clickhouse-cloud__*` call (beyond a cheap existence
check — see below), be able to state to yourself: which metric formula (if
any) you're reusing, which known-issue traps apply and how your query avoids
them, and which join keys/casing/ID formats you must match. Let those facts
directly shape the SQL you write — don't query first and rationalize
afterward. If the question turns out to need a page you didn't originally
open, go back and read it before finalizing the query, rather than guessing.

## The data may not exist yet — check before assuming

The question you're given may come from a feature spec whose instrumentation
hasn't been deployed to the live database yet. Before writing your real
query, confirm with `list_tables` (or a query against `system.tables`) that
every table/column the question needs actually exists in `{database}`. If it
doesn't:
- Do not guess, simulate, or fabricate numbers.
- Answer honestly, in the markdown file (see "Output" below), that the
  question can't be answered yet because the required instrumentation isn't
  live, naming specifically which table/column is missing and what the
  question needs once it lands.
This is a complete, legitimate answer — give it the same care as a
fully-answered question, not a stub or apology.

## Answering the question

- Query the live database for a real, current answer. Don't answer from
  memory of what the wiki says a number was on some past verification date —
  re-derive it now. Only fall back to a cited wiki figure if a live query is
  genuinely impossible (see above).
- State the query's scope honestly: sample size, date range, and any
  known-issue caveat that affects how the number should be read (e.g. "do
  not aggregate this across currencies without grouping").

{skills_section}

## Update the wiki, if your finding warrants it

You have something the Context Agent doesn't: a live query result. If what
you found genuinely changes, confirms with fresh evidence, or adds to a
claim the wiki already makes, update the relevant page(s) in
`{context_dir}` in place — don't just leave the finding stranded in your
answer file. Skip this section entirely if nothing you found bears on an
existing page; don't force an edit to satisfy a checklist.

Follow `{context_dir / 'SCHEMA.md'}` exactly — it is the authority, read it
before editing anything if you haven't already:
- Update in place; never create a new page for an existing table/metric,
  never a `_v2` page.
- A `known_issues.md` entry you just re-tested with a live query: this is
  the one agent in this project actually allowed to change its `status` or
  verdict text, because you have real evidence — cite your exact query and
  result as the `source`. Never delete a refuted claim; add the new evidence
  alongside it with today's date if it conflicts with what's there.
- A metric you computed that matches an existing `metrics/*.md` page: update
  its value/`last_verified` if your fresh number differs from what's
  recorded, citing your query.
- A metric you computed that has no existing page and is likely to be asked
  again: consider adding a short new `metrics/*.md` page for it, plus an
  entry in `metrics/index.md` — only if it's a genuinely reusable
  definition, not a one-off cut specific to this single question.
- A table-specific caveat you newly confirmed or disproved (e.g. a data
  quality issue in a column): add a short note to that table's
  `tables/<name>.md` page.
- Whatever you touch: update its `status`, `confidence`, `last_verified`,
  and regenerate the containing `index.md` as the last step, per SCHEMA.md.
  Append one entry to `{context_dir / 'log.md'}` naming the question, what
  you found, and the evidence.
- Do not run `git commit` — leave wiki edits uncommitted for human review.

## Output

You are given two paths: a markdown path and an HTML path.

1. **Always** write the markdown path — a short Question/Answer file, this
   structure exactly:

   ```markdown
   ## Question
   <the question, verbatim>

   ## Answer
   <a short, direct paragraph — the finding, the key number(s), and one line
   of scope/caveat (sample size, date range, a known-issue note if it
   applies). A few sentences, not an essay. If you also wrote a report (see
   below), end with a line linking to it, e.g. "See the full report:
   <html filename>.">
   ```

   This file is the answer for every question, including ones you couldn't
   fully answer (state why, per "The data may not exist yet" above) and ones
   where you also produced a report.

2. **Only** additionally write the HTML path — a complete, self-contained
   report (inline `<style>`/`<script>` only, no external dependencies, no
   CDN, renders correctly opened directly from disk offline) — when the
   question itself is explicitly asking for one. Signals that this is a
   report/visualization request: it uses words like "report", "dashboard",
   "visualize"/"visualise", "chart", "graph", "plot", "show me a
   breakdown/trend" as an explicit deliverable, or otherwise directly asks
   you to produce a visual artifact rather than just tell it a fact. A
   question that's simply asking "what is X" / "does X lift Y" / "how much
   faster is X" — even if your answer happens to involve segments or a
   trend internally — does NOT warrant a report; answer that fully in the
   markdown file's prose and do not create the HTML file at all.
   If (and only if) you do build the report: use inline SVG or `<canvas>` +
   vanilla JS for any visualization, make it genuinely good (considered
   layout, a coherent color scheme that reads correctly in both light and
   dark viewing — don't assume a white background — legible typography, real
   axis labels and units naming the actual metric, and a visible note of the
   time window / row count the figure is based on), and keep the markdown
   file's own answer self-sufficient rather than just "see the report."

Then give a short (under 100 words) plain-text summary as your final
response: the headline finding (or why the question couldn't be answered),
whether you also produced an HTML report and why (or why not), and which
wiki page(s) (if any) you updated and why.
"""


def build_prompt(question: str, md_path: Path, html_path: Path) -> str:
    return f"""Answer this PM question against the live ClickHouse database.

Question: {question}

- Always write your Question/Answer markdown to: {md_path}
- Only if this question explicitly asks for a report/visualization (per your
  system prompt's Output section), also write the HTML report to: {html_path}

Follow the required reading order, the "data may not exist yet" check, the
wiki-update rule (only where genuinely warranted), and the output rules from
your system prompt.
"""


@observe(name="analysis-agent", as_type="agent", capture_output=False)
async def run_agent(
    prompt: str,
    out_dir: Path,
    context_dir: Path,
    service_id: str,
    database: str,
    skill_names: list[str],
) -> str:
    options = ClaudeAgentOptions(
        cwd=str(REPO_ROOT),
        add_dirs=[str(context_dir), str(out_dir)],
        mcp_servers={
            "clickhouse-cloud": {
                "type": "http",
                "url": CLICKHOUSE_MCP_URL,
            }
        },
        allowed_tools=["Read", "Write", "Edit", "mcp__clickhouse-cloud__*"],
        permission_mode="bypassPermissions",
        system_prompt=build_system_prompt(skill_names, context_dir, service_id, database),
        skills=skill_names or None,
        setting_sources=["project"],
        max_turns=20,
    )

    final_text_parts = []
    tool_call_count = 0
    async for message in query(prompt=prompt, options=options):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    final_text_parts.append(block.text)
                elif isinstance(block, ToolUseBlock):
                    tool_call_count += 1
                    print(f"  [tool] {block.name} {block.input}", file=sys.stderr)
                    langfuse_client.create_event(
                        name=f"tool:{block.name}",
                        input=block.input,
                        metadata={"tool_use_id": block.id, "sequence": tool_call_count},
                    )
        elif isinstance(message, ResultMessage):
            if message.is_error:
                print(f"error: {message.result}", file=sys.stderr)

            # Cost/tokens must go on a `generation` observation (usage_details /
            # cost_details / model) to show up in Langfuse's usage & cost
            # dashboards — a plain metadata dict on a span is invisible there.
            for model_name, model_usage in (message.model_usage or {}).items():
                with langfuse_client.start_as_current_observation(
                    as_type="generation",
                    name=f"claude-agent-sdk:{model_name}",
                    model=model_usage.get("canonicalModel") or model_name,
                    usage_details={
                        "input": model_usage.get("inputTokens", 0),
                        "output": model_usage.get("outputTokens", 0),
                        "cache_read_input_tokens": model_usage.get(
                            "cacheReadInputTokens", 0
                        ),
                        "cache_creation_input_tokens": model_usage.get(
                            "cacheCreationInputTokens", 0
                        ),
                    },
                    cost_details={"total": model_usage.get("costUSD", 0.0)},
                ):
                    pass

            langfuse_client.update_current_span(
                metadata={
                    "num_turns": message.num_turns,
                    "tool_calls": tool_call_count,
                    "duration_ms": message.duration_ms,
                    "total_cost_usd": message.total_cost_usd,
                    "is_error": message.is_error,
                    "stop_reason": message.stop_reason,
                },
            )

    result_text = "\n".join(final_text_parts)
    langfuse_client.update_current_span(output=result_text)
    return result_text


@observe(name="analysis-agent-run")
def main():
    parser = argparse.ArgumentParser(
        description="Analysis Agent: answer one PM question against live "
        "ClickHouse data, writing a markdown Q&A file (and, if the question "
        "asks for one, a self-contained HTML report)"
    )
    parser.add_argument("question", help="the PM question to answer")
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=None,
        help="directory to write the markdown/HTML output into (default: "
        "out/adhoc/analysis)",
    )
    parser.add_argument(
        "--index",
        type=int,
        default=None,
        help="optional question number; if given, output files are named "
        "qNN.md / qNN_report.html instead of a slug of the question",
    )
    parser.add_argument(
        "--context-dir",
        type=Path,
        default=None,
        help="context wiki root to read (default: context/)",
    )
    parser.add_argument(
        "--service-id",
        default=DEFAULT_SERVICE_ID,
        help="ClickHouse Cloud serviceId to query (default: the verified "
        "service from context/index.md)",
    )
    parser.add_argument(
        "--database",
        default=DEFAULT_DATABASE,
        help="database to query (default: clickathon)",
    )
    args = parser.parse_args()

    out_dir = (args.out_dir or REPO_ROOT / "out" / "adhoc" / "analysis").resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    context_dir = (args.context_dir or CONTEXT_DIR).resolve()

    if not context_dir.is_dir():
        print(f"error: {context_dir} is not a directory", file=sys.stderr)
        return 1

    base_name = f"q{args.index:02d}" if args.index is not None else slugify(args.question)
    md_path = out_dir / f"{base_name}.md"
    html_path = out_dir / f"{base_name}_report.html"

    langfuse_client.update_current_span(
        input={
            "question": args.question,
            "md_path": str(md_path),
            "html_path": str(html_path),
        }
    )

    skill_names = discover_skills(VENDORED_SKILLS_DIR, PROJECT_SKILLS_DIR)
    if skill_names:
        print(f"skills discovered: {', '.join(skill_names)}", file=sys.stderr)
    else:
        print(f"no skills found under {VENDORED_SKILLS_DIR}", file=sys.stderr)

    prompt = build_prompt(args.question, md_path, html_path)
    summary = asyncio.run(
        run_agent(
            prompt, out_dir, context_dir, args.service_id, args.database, skill_names
        )
    )
    langfuse_client.update_current_span(output=summary)
    print(summary)

    if not md_path.exists():
        print(
            f"error: expected markdown answer was not created: {md_path}",
            file=sys.stderr,
        )
        return 1
    print(
        f"report {'created' if html_path.exists() else 'not created (not requested)'}: "
        f"{html_path}",
        file=sys.stderr,
    )

    trace_url = langfuse_client.get_trace_url()
    if trace_url:
        print(f"\nLangfuse trace: {trace_url}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    try:
        exit_code = main()
    finally:
        langfuse_client.flush()
    sys.exit(exit_code)
