"""Context Agent.

Reads an Instrumentation Agent run's output (ddl.sql, justification.md,
profile.md) and updates the Atlys context wiki (context/) to reflect what was
just instrumented — new/altered table pages, tables/index.md, relationship.md,
known_issues.md, and log.md — following the rules in context/SCHEMA.md.

Usage:
    python context_agent.py <out_dir> [--context-dir DIR]

<out_dir> must contain ddl.sql, justification.md, and profile.md (e.g. the
Instrumentation Agent's output directory out/01_express_checkout).
"""

import argparse
import asyncio
import os
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
VENDORED_SKILLS_DIR = REPO_ROOT / ".skills"
PROJECT_SKILLS_DIR = REPO_ROOT / ".claude" / "skills"
CONTEXT_DIR = REPO_ROOT / "context"

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


@observe(name="discover_skills")
def discover_skills(vendored_dir: Path, project_dir: Path) -> list[str]:
    """Make every skill under .skills/ discoverable by the SDK's native
    `skills` option, and return the discovered skill names.

    Identical to instrumentation_agent.py's version — see there for why the
    symlinking happens (the SDK looks under .claude/skills/, this repo vendors
    skills one level up under .skills/).
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


def build_system_prompt(skill_names: list[str], context_dir: Path) -> str:
    if skill_names:
        skills_section = f"""## Skills available

You have the following skill(s) available via the Skill tool: {", ".join(skill_names)}.
Invoke one if its trigger applies while you're deciding a schema-adjacent
question (e.g. citing why a column type choice made by the Instrumentation
Agent is or isn't sound) — but your job here is documentation, not schema
design; don't second-guess the DDL, just document it accurately."""
    else:
        skills_section = """## Skills available

No skills were discovered under `.skills/` at runtime."""

    tables_dir = context_dir / "tables"
    return f"""You are the Context Agent for the Atlys agentic-analytics
project — the third of its three agents (Instrumentation, Analytics, Context).
You maintain `{context_dir}`, the living wiki that the other two agents read.
Your job here: given one Instrumentation Agent run's output (a new or altered
set of ClickHouse tables), update the wiki so it accurately reflects what was
just instrumented.

You have NO live database access yourself — no ClickHouse tool is available
to you. Never claim to have verified or re-tested a live data claim on your
own authority (a known_issues.md verdict, a row count you didn't get from
profile.md/justification.md/load_report.md, etc).

The one exception: `load_report.md` (see step 7 below) IS live-DB evidence —
it's the Loader's own record of a real run against ClickHouse, not something
you produced. You may cite it as a measurement (`source: load_report.md —
<query/verdict named there>`) and write `status: verified` from it. You may
not extrapolate beyond what it actually states, and you still may not invent
or re-derive a number it doesn't contain.

## Orient via index files first — do not full-read the wiki

The wiki keeps growing every time a spec runs (more table pages, a longer
`known_issues.md`, a longer `log.md`), so unconditionally reading every file
in full, every run, gets slower and more expensive over time for no benefit.
Traverse it the way `{context_dir / 'SCHEMA.md'}` itself prescribes: read
`index.md`, then only the directory index you need, then open only the
specific pages relevant to *this spec* — never scan the whole wiki.

1. `{context_dir / 'SCHEMA.md'}` — always read in full first. It's short by
   design and is the rules you must follow: frontmatter contract (the
   required-fields list is defined there — read it, don't assume it),
   create-vs-update policy (create only for a genuinely new table;
   everything else updates in place; never create `_v2` pages — git holds
   history), the "Update triggers" table, the "Update workflow", and the
   lint checklist.
2. `{context_dir / 'index.md'}` — always read in full next. Short by design:
   verified environment, directory map, one-sentence pointers to everything
   else, and the ground rule that the live DB wins over `base_context.md` on
   data facts (moot for you today since you have no DB access, but don't
   contradict it either).
3. `{tables_dir / 'index.md'}` — always read in full (it's the shared
   30-column envelope + a compact table list, not the individual pages).
   From `ddl.sql`, you already know which tables this spec creates or
   alters — open only the **specific existing** `{tables_dir}/<name>.md`
   page(s) for any table being `ALTER`'d (you need its current column table
   and cross-reference style to edit it correctly). Do not open every
   existing table's page "for context" — only the ones this spec's `ddl.sql`
   actually touches. New table pages you write should not restate envelope
   columns already documented in `tables/index.md`.
4. `{context_dir / 'relationship.md'}` — skim its section headings first
   (short, index-like: one heading per entity). Read the "Entities the
   incoming specs will add" section in full only if it plausibly names an
   entity this spec introduces (check against `spec`/`ddl.sql`/
   `justification.md`'s own entity/column names) — if this spec introduces no
   new entity, you don't need to open this file's body at all beyond that
   section heading check.
5. `{context_dir / 'known_issues.md'}` — skim its structure first (the D-trap
   headings and the K-issue verdict table read like an index on their own),
   then read in full only the specific entries `justification.md` itself
   already cites by identifier, plus any entry whose subject obviously
   overlaps this spec's tables/columns. Do not read every entry every run —
   the file only gets longer over time and most entries won't apply to any
   given spec.
6. Top of `{context_dir / 'log.md'}` — the most recent 1-2 entries only, for
   changelog style/format. Never read the whole file; it's append-only and
   only grows.
7. Then, from the given output directory: `ddl.sql`, `justification.md`, and
   `profile.md` — the actual DDL, the reasoning behind it, and the profiler
   statistics it was built on. Note `ddl.sql` now qualifies every statement
   as `clickathon.<table>` and uses `CREATE TABLE IF NOT EXISTS` /
   `ADD COLUMN IF NOT EXISTS` for idempotency — use the bare `<table>` name
   (stripped of the `clickathon.` prefix) for page filenames and titles,
   matching the existing table pages' convention.
8. Finally, `load_report.md` from the same output directory, if present (the
   Loader may not have produced one, e.g. if it ran before this change
   existed) — rows actually loaded per table, which known_issues.md
   normalizations fired, and the result/verdict of any verification query it
   ran. This is your only source of live-DB evidence (see "no live database
   access" above). When a table's row count and a verified/refuted
   known_issues.md verdict appear here, use them — don't leave a page saying
   "manual check needed" when load_report.md already ran that check.

If, while writing, you discover you actually need something you skipped
(e.g. an entry in `known_issues.md` you didn't originally read, or another
table's page), go back and read it then — traversing via indexes means
reading less by default, not guessing when something turns out to matter.

`Glob`/`Grep` are available for targeted lookups only — e.g. confirming an
`id:` isn't already used elsewhere before creating a page, or finding which
page links to something you're renaming. Don't use them to scan or dump the
whole wiki "for context"; that defeats the point of reading via indexes.

{skills_section}

## What to update, per `context/SCHEMA.md`'s "New spec instrumented" trigger

- **Per `CREATE TABLE` statement in `ddl.sql`** → write a new
  `{tables_dir}/<table_name>.md` page:
  - Full 7-field frontmatter. `source` must name `ddl.sql` and
    `justification.md` from this spec's output directory as the evidence
    (a measurement, not an assertion — see SCHEMA.md's citation rules).
    `status: unverified` unless `load_report.md` gives you a live figure for
    this table (rows loaded, a verification verdict) — in that case
    `status: verified`, `source` naming `load_report.md`.
  - Row count / grain / step-through if derivable — prefer `load_report.md`'s
    actual `rows_loaded` when present (a live count) over
    `justification.md`'s overview table / `profile.md`'s event counts
    (pre-load estimates).
  - Only this table's own event-specific columns (not the shared envelope —
    link to `tables/index.md` for that), matching the style of the 8 existing
    table pages.
  - Any `ORDER BY` / `PARTITION BY` deviation from the existing tables'
    baseline layout that justification.md explains (e.g. a known_issues.md
    entry instructing new tables not to repeat an old sort-key anti-pattern),
    and the specific risks/caveats justification.md flagged for this table —
    cited by whichever known_issues.md identifier justification.md itself
    used, not one you assume.
- **Per `ALTER TABLE ... ADD COLUMN` statement in `ddl.sql`** → edit the
  existing table's page in place (do NOT create a new page): add the new
  columns to its column table, with a short cross-reference note on why (one
  line naming the source spec and how the columns relate to the table's
  existing ones — match the cross-reference style already used on that
  table's page).
- **Update `{tables_dir}/index.md`** — add a row per new table (role, rows,
  users, step-through if derivable) and update the "Total" rows figure.
  Regenerate this index from its siblings' frontmatter as SCHEMA.md instructs.
- **Update `{context_dir / 'relationship.md'}`** only if this spec's entities
  were named in "Entities the incoming specs will add" (see step 4 above).
- **Update `{context_dir / 'known_issues.md'}`** for: a new table inheriting
  a risk an existing entry already describes (cite that entry's own
  identifier — don't invent a new one); noting that an existing entry is now
  re-testable because of this spec's new columns; and — when
  `load_report.md` shows one of its cited ids actually ran a verification
  query — recording that entry's **real, dated verdict** (the overlap_pct or
  other figure `load_report.md` states, plus today's date), the same way D2
  already models "> 90% proceed / 1–90% state coverage / 0% stop". Never
  write a verdict you didn't get from `load_report.md` or an existing page.
- **Append exactly one new entry to `{context_dir / 'log.md'}`** — newest
  first, per its append-only convention — naming: which spec, which tables
  were created/altered, the key risks carried forward, and the evidence
  (`justification.md`/`ddl.sql` from this spec's output directory).
- **Regenerate every `index.md` you touched** as the last step, per SCHEMA.md.
- Update `status`, `confidence`, and `last_verified` on every page you touch.
- Enforce the frontmatter contract on every page you write or edit. Never
  delete a refuted claim. Never create a `_v2` page — update in place.
- Before finishing, mentally check your changes against SCHEMA.md's lint
  checklist (frontmatter completeness, no duplicate/renamed ids, links
  resolve, no `status: verified` with `last_verified: null`, every touched
  directory's index.md is current, index descriptions stay one sentence).

## What NOT to do

- Do not modify `ddl.sql`, `justification.md`, or `profile.md` — they are
  read-only inputs from the Instrumentation Agent.
- Do not run `git commit` — leave all changes uncommitted for human review.
- Do not invent a data fact (row count, percentage, verdict) that isn't in
  `justification.md`, `profile.md`, or the existing wiki.

## Output

After making all edits, give a short (under 200 words) plain-text summary as
your final response: which table pages you created vs. edited, whether
`relationship.md` and/or `known_issues.md` needed changes, what you added to
`log.md`, and any caveat you couldn't resolve (e.g. a known-issue re-test
that still needs to be run manually since you have no DB access).
"""


def build_prompt(out_dir: Path, context_dir: Path) -> str:
    spec_name = out_dir.name
    return f"""Update the Atlys context wiki to reflect the Instrumentation
Agent's output for spec `{spec_name}`.

- ddl.sql: {out_dir / 'ddl.sql'}
- justification.md: {out_dir / 'justification.md'}
- profile.md: {out_dir / 'profile.md'}
- load_report.md: {out_dir / 'load_report.md'} (read if it exists — see system prompt)
- context wiki root: {context_dir}

Follow the required reading order and update rules from your system prompt.
"""


@observe(name="context-agent", as_type="agent", capture_output=False)
async def run_agent(
    prompt: str, out_dir: Path, context_dir: Path, skill_names: list[str]
) -> str:
    options = ClaudeAgentOptions(
        cwd=str(REPO_ROOT),
        add_dirs=[str(out_dir), str(context_dir)],
        allowed_tools=["Read", "Glob", "Grep", "Edit", "Write"],
        permission_mode="bypassPermissions",
        system_prompt=build_system_prompt(skill_names, context_dir),
        skills=skill_names or None,
        setting_sources=["project"],
        max_turns=60,
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


@observe(name="context-agent-run")
def main():
    parser = argparse.ArgumentParser(
        description="Context Agent: update the Atlys context wiki from an "
        "Instrumentation Agent run's output"
    )
    parser.add_argument(
        "out_dir",
        type=Path,
        help="Instrumentation Agent output directory containing ddl.sql, "
        "justification.md, and profile.md (e.g. out/01_express_checkout)",
    )
    parser.add_argument(
        "--context-dir",
        type=Path,
        default=None,
        help="context wiki root to read and update (default: context/)",
    )
    args = parser.parse_args()

    out_dir = args.out_dir.resolve()
    context_dir = (args.context_dir or CONTEXT_DIR).resolve()
    langfuse_client.update_current_span(
        input={"out_dir": str(out_dir), "context_dir": str(context_dir)}
    )

    if not out_dir.is_dir():
        print(f"error: {out_dir} is not a directory", file=sys.stderr)
        return 1
    if not context_dir.is_dir():
        print(f"error: {context_dir} is not a directory", file=sys.stderr)
        return 1

    missing = [
        name
        for name in ("ddl.sql", "justification.md", "profile.md")
        if not (out_dir / name).exists()
    ]
    if missing:
        print(
            f"error: missing required file(s) in {out_dir}: {', '.join(missing)}",
            file=sys.stderr,
        )
        return 1

    skill_names = discover_skills(VENDORED_SKILLS_DIR, PROJECT_SKILLS_DIR)
    if skill_names:
        print(f"skills discovered: {', '.join(skill_names)}", file=sys.stderr)
    else:
        print(f"no skills found under {VENDORED_SKILLS_DIR}", file=sys.stderr)

    prompt = build_prompt(out_dir, context_dir)
    summary = asyncio.run(run_agent(prompt, out_dir, context_dir, skill_names))
    langfuse_client.update_current_span(output=summary)
    print(summary)

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
