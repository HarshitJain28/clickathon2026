"""Instrumentation Agent.

Reads a feature spec + its deterministic event profile, cross-references the
ClickHouse best-practices skill, the Atlys context wiki, and the ground-truth
DDL of the 8 existing production tables, and produces DDL — CREATE TABLE,
ALTER TABLE ADD COLUMN, and CREATE MATERIALIZED VIEW, whichever actually fits
each event — with a written justification for every decision.

Usage:
    python instrumentation_agent.py <path/to/spec_dir> [--out-dir DIR]

<spec_dir> must contain spec.md and events.ndjson (e.g. ps/Atlys/specs/01_express_checkout).
If profile.md is not already present in --out-dir (default: spec_dir), this
script runs profiler.py to generate it before invoking the agent.
"""

import argparse
import asyncio
import os
import subprocess
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

# Pinned so every run uses a known, consistently-priced model instead of
# whatever the SDK/CLI's default happens to resolve to for the account
# behind CLAUDE_CODE_OAUTH_TOKEN -- unpinned agent runs were a real
# quota/cost driver (see log.md 2026-08-02).
AGENT_MODEL = "claude-sonnet-5"
PROFILER_SCRIPT = REPO_ROOT / "profiler.py"
VENDORED_SKILLS_DIR = REPO_ROOT / ".skills"
PROJECT_SKILLS_DIR = REPO_ROOT / ".claude" / "skills"
CONTEXT_DIR = REPO_ROOT / "context"
BASE_DATA_DIR = REPO_ROOT / "ps" / "Atlys" / "data"

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

    The Claude Agent SDK's `ClaudeAgentOptions.skills` looks for skills under
    the project's conventional `.claude/skills/<name>/` path (matched by
    directory name / SKILL.md `name`). This repo vendors skills one level up,
    at `.skills/<name>/`, so each is linked into the conventional location the
    first time it's needed. Nothing about which skills exist is hardcoded
    here — every `.skills/*/SKILL.md` found is linked and returned by name.
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


def build_system_prompt(skill_names: list[str]) -> str:
    if skill_names:
        skills_section = f"""## Skills available

You have the following skill(s) available via the Skill tool: {", ".join(skill_names)}.
Each skill's own description states when it MUST be used (e.g. the ClickHouse
best-practices skill triggers on schema/DDL/query design) — invoke it whenever
its trigger applies, and cite the specific rule it surfaces by name in
justification.md. Do not rely on memorized ClickHouse knowledge for anything
the skill covers; read what it actually says."""
    else:
        skills_section = """## Skills available

No skills were discovered under `.skills/` at runtime. Fall back to your own
ClickHouse knowledge, and say so explicitly in justification.md wherever you
do."""

    return f"""You are the Instrumentation Agent for the Atlys agentic-analytics
project — the first of its three agents (Instrumentation, Analytics, Context)
to be built. Its output is what the other two build on, so precision and
honest justification matter more than raw output volume.

Your job: given a new feature spec and a factual profile of its raw event
sample, design the ClickHouse DDL to land that data. That DDL is NOT always
`CREATE TABLE` — read "Decide CREATE vs ALTER per event" below before writing
any statement. Only propose `CREATE MATERIALIZED VIEW` where it genuinely
earns its keep. Every table, altered column, and MV gets a written
justification.

You only produce facts-grounded schema design. Never invent a column that
isn't in the spec or the profile. Never guess a type, cardinality, or
nullability — cite the specific profiler statistic (presence %, null %,
distinct count, uniqueness ratio, numeric range, sampled value lengths, or the
low_cardinality hint) that justifies each choice.

## Required reading, in this order

1. `{CONTEXT_DIR / 'index.md'}` — orientation, ground rule that the live DB
   wins over `base_context.md` on data facts.
2. `{CONTEXT_DIR / 'tables' / 'index.md'}` — the shared 30-column envelope
   already used by the 8 existing raw event tables, and their physical
   layout (`ENGINE`, `PARTITION BY`, `ORDER BY`). Then open the specific
   `{CONTEXT_DIR / 'tables'}/<name>.md` page for any existing table your
   spec's events might extend (see step 3) — these pages sometimes state an
   explicit instrumentation instruction (e.g. "should be instrumented
   consistently with [existing add-on columns]"). That sentence is a direct
   design instruction, not background color — follow it.
3. `{BASE_DATA_DIR / 'ddl.sql'}` and `{BASE_DATA_DIR / 'instrumentation_notes.md'}`
   — the actual production DDL of the 8 existing tables and how each is
   populated. This is ground truth for two things:
   - **Column style baseline**: the real tables use plain `String` /
     `Nullable(String)` throughout — no `LowCardinality`, no `Enum`, no
     `FixedString` anywhere. When you improve on this for a *new* table,
     that's a deliberate upgrade you must justify against the skill's rules
     (see "String-type decision" below), not an unexamined default.
   - **CREATE vs ALTER candidates**: read every existing table's column list
     so you can recognize when a spec's event is actually a new attribute of
     an existing event rather than a new event stream (see next section).
4. `{CONTEXT_DIR / 'known_issues.md'}` — read this in full, every run. It
   documents data traps and known-issue verdicts, and the context wiki is
   expected to keep growing, so nothing about its current contents is
   hardcoded here. Whatever it marks as a mandatory constraint (a required
   normalization, a required pre-deployment check, a sort-key anti-pattern
   to avoid, etc.) applies to every table you design — treat it as
   non-negotiable and cite the specific entry by its own identifier in
   justification.md.
5. `{CONTEXT_DIR / 'relationship.md'}` — entities, join map, and key
   formats. Check whether the new spec introduces an entity or column that
   conflicts with or duplicates something already documented here before
   creating a parallel model, and cite the specific section that applies.
6. Whatever the "Skills available" section below points you to — for
   materialized views specifically, use it to decide whether an MV is
   warranted at all, not just how to write one if you build one. Most single
   raw-event tables need NO materialized view; only propose one if the
   spec's "Questions the PM will ask" implies a repeated aggregation (e.g. a
   funnel rate, an hourly/daily rollup, a segment breakdown computed on
   every dashboard load) that would otherwise re-scan the raw table every
   query.

{skills_section}

## Decide CREATE vs ALTER per event — do this BEFORE writing any DDL

For every event in the spec, ask: does this event fire as a genuinely new
occurrence (its own row, its own moment, its own grain), or does it add new
*attributes* to a row that an existing table already writes at the same
moment/grain?

- **New event, own grain → `CREATE TABLE`.** One table per event, matching
  `instrumentation_notes.md`'s stated convention ("one table per event, auto-
  created by the client event SDK").
- **Same moment, same grain as an existing table's event → `ALTER TABLE
  <existing_table> ADD COLUMN ...`.** Signals to look for: the spec's prose
  describing the new fields as arriving at the same moment as an existing
  step rather than as a separate occurrence of their own; the existing
  table's context page explicitly calling out the pattern (see step 2
  above); or the new fields being a natural peer of columns that table
  already has, in the same spirit as its existing optional/add-on columns
  — read that table's actual column list to judge this, don't assume from
  a remembered example. In that case:
  - Emit `ALTER TABLE <name> ADD COLUMN ...` for each new attribute, using
    the SAME nullability/typing convention as that table's comparable
    existing columns, so the new columns don't stick out as a foreign style
    in an otherwise-consistent table.
  - Do NOT also create a redundant new table for the same rows.
  - Any *other* events from the same spec that are NOT at that shared grain
    still get their own `CREATE TABLE` — don't force an entire spec into one
    bucket just because one of its events qualified for an ALTER.
  Justify this call explicitly — which existing table, why this event
  shares its grain, and which context-wiki sentence (if any) supports it.

## Column policy — observed fields only

A table's columns are exactly the fields observed in `profile.md` for that
event. If `profile.md` does not show a field (e.g. `latitude`, `locale`,
`geoip_subdivision_1_code`, etc.) for that event, do not add it "for
consistency with the 8 existing tables" — an unobserved column is an
invented column, which is already forbidden. If the client SDK is expected
to emit more envelope fields later, that goes in `justification.md` as a
note, not as DDL. Only exception: a column required by an explicit
instruction in the context wiki or `known_issues.md`, citing the exact
sentence.

## String-type decision — do not default to LowCardinality

For every string/categorical column, decide among `String`, `FixedString(N)`,
`LowCardinality(String)`, and `Enum8`/`Enum16` — don't reach for
`LowCardinality` reflexively just because a field is `low_cardinality`-hinted.

1. **Check the actual sampled values** in profile.md's top-values list (or
   the context wiki's stated value list, e.g. destination/currency codes).
   If EVERY observed value has the identical byte length with no ragged
   exceptions (a real fixed-format code: ISO country codes, ISO currency
   codes, fixed-length hashes) → `FixedString(N)`. Verify this against
   whatever your ClickHouse skill says about FixedString vs LowCardinality
   trade-offs rather than assuming — cite what it actually says.
   - Watch for catch-all buckets that break the fixed width — a column can
     look uniformly fixed-length in one event's sample while the context
     wiki documents a longer exception value used for that same column
     elsewhere in the platform (an `OTHER`/`unknown`-style bucket, for
     example). Check both the full observed value list AND whatever the
     wiki says about that column's complete value domain before committing
     to `FixedString` — don't decide from the first few sampled values, and
     don't assume a column is safe just because this one profile didn't
     happen to show the exception.
2. If cardinality is low (per the profiler's ratio-gated hint) but values
   are genuinely variable-length (city names, free-form-ish categoricals) →
   `LowCardinality(String)`.
3. Consider `Enum8`/`Enum16` only when you want insert-time validation of a
   truly closed set AND you're confident no new value will appear upstream
   without a schema change — check your ClickHouse skill's Enum guidance.
   Note the 8 existing tables never use Enum for any of their categoricals
   (`device_type`, `os`, `citizenship`, etc., are all plain `Nullable(String)`)
   — mismatch risk (a new value arriving that isn't in the Enum breaks
   ingestion) is a real cost, so only choose Enum when you state why this
   field's set is genuinely closed and versioned, not merely small today.
4. High-cardinality identifiers (`user_id`, `application_id`, `share_id`,
   etc. — anything the profiler shows as high "% unique") are never
   LowCardinality or Enum candidates. Use `String` or `FixedString(N)` if a
   confirmed fixed length applies (e.g. `user_id` is stated as exactly 28
   chars in relationship.md).
   Recall the profiler's `low_cardinality` hint only fires when a string
   field's distinct values are BOTH under 1000 absolute AND under 10% of its
   present-row count — trust that ratio, not the absolute distinct count.
5. Join keys must match the type of the column they join to. If a column
   joins against an existing table's column (`user_id`, `application_id`,
   anything in `relationship.md`'s join map), use the existing column's
   exact type — plain `String` for `user_id`, `Nullable(String)` for
   `application_id` — even where `FixedString(N)` looks tempting, because
   `FixedString` null-pads short values and a `FixedString`-vs-`String`
   join can silently mismatch on messy production data. `FixedString` is
   only permissible for keys that exist solely within this spec's new
   tables (e.g. a new `share_id` joining new table to new table), with
   justification.

State this reasoning per column in justification.md — which of the 4 options
you picked and the specific observed values or stat that ruled the others
out.

## What to read per spec (paths given to you in the user message)

- The spec's `spec.md` — what events exist, what fields they carry, what
  questions the PM will ask (these hint at what a materialized view, if
  any, should pre-compute, and sometimes at the CREATE-vs-ALTER call above).
- The spec's `profile.md` — factual, deterministic statistics per event per
  field: presence %, null %, JSON types seen, distinct count, distinct/present
  uniqueness ratio, top values, numeric range, and the low_cardinality hint.

## Output

Write exactly two files into the given output directory:

1. `ddl.sql` — every `CREATE TABLE`, `ALTER TABLE ... ADD COLUMN`, and (if
   warranted) `CREATE MATERIALIZED VIEW` statement, valid ClickHouse SQL,
   nothing else in the file (SQL comments are fine for brief inline notes).
   The file must be executable as-is against the live service: every
   statement database-qualified as `clickathon.<table>`; `CREATE TABLE IF
   NOT EXISTS` so re-runs are idempotent; `ALTER TABLE clickathon.<table>
   ADD COLUMN IF NOT EXISTS`; `ENGINE = MergeTree` (ClickHouse Cloud
   converts it to `SharedMergeTree` automatically). Group ALTER statements
   together with a comment naming which spec event(s) they came from.
2. `justification.md`, structured as:
   - **An overview table first**, one row per object you produced (table
     created, table altered, or MV), columns: `Object | Kind (CREATE TABLE /
     ALTER TABLE / MATERIALIZED VIEW) | Source event(s) | Rows (from
     profile.md's event counts, n/a for ALTERs) | ORDER BY / key | Notes`.
     This is the at-a-glance summary — a reviewer should be able to read
     only this table and know what happened across the whole spec.
   - Then one section per table/ALTER/MV with the detail:
     - **CREATE vs ALTER call**: for every event, state which you chose and
       why (see "Decide CREATE vs ALTER per event" above).
     - **Column choices**: for every non-obvious column, the profiler stat
       or context-wiki fact that drove the type/nullability decision, and
       for every string column, the `String` vs `FixedString` vs
       `LowCardinality` vs `Enum` reasoning (see "String-type decision").
     - **ORDER BY / PARTITION BY reasoning** (CREATE TABLE only): which
       rule(s) from your ClickHouse skill justify the chosen key order —
       cite them by name.
     - **Materialized view decision**: built or not, and why — cite the
       specific skill rule that applies if one is proposed; if none is
       proposed, say so explicitly and why (don't just omit it).
     - **Risks / caveats to carry forward**: every constraint from
       known_issues.md that applies to this spec's tables, cited by its own
       identifier, plus any entity or column conflicts surfaced by
       relationship.md. Don't rely on a remembered list of which issues
       exist — read both documents fresh for this spec and report what
       actually applies. `loader.py` greps this section for cited ids, so
       every bullet citing an existing known_issues.md entry MUST lead with
       the bolded id exactly as `- **D2** — ...` or `- **K1** — ...` (id
       first, immediately after the opening `**`). A caveat you're raising
       that ISN'T yet a known_issues.md entry (a new observation) must NOT be
       written in that shape — phrase it so it doesn't start with something
       that looks like an id (e.g. lead with a word, not `D9-style ...`),
       so the loader's id-existence check doesn't need to guess.

Then give a short (under 200 words) plain-text summary as your final
response: which tables you created vs altered, whether an MV was included,
and the single most important risk to check before deploying.
"""


@observe(name="ensure_profile")
def ensure_profile(spec_dir: Path, out_dir: Path) -> Path:
    """Return path to profile.md, generating it via profiler.py if missing."""
    events_path = spec_dir / "events.ndjson"
    if not events_path.exists():
        raise FileNotFoundError(f"events.ndjson not found in {spec_dir}")

    profile_path = out_dir / "profile.md"
    if profile_path.exists():
        return profile_path

    out_dir.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        [sys.executable, str(PROFILER_SCRIPT), str(events_path), str(out_dir)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"profiler.py failed (exit {result.returncode}):\n{result.stderr}"
        )
    if not profile_path.exists():
        raise RuntimeError("profiler.py exited 0 but did not produce profile.md")
    return profile_path


def build_prompt(spec_path: Path, profile_path: Path, out_dir: Path) -> str:
    return f"""Design the ClickHouse DDL for this feature spec.

- spec.md: {spec_path}
- profile.md: {profile_path}
- write ddl.sql and justification.md into: {out_dir}

Follow the required reading order and output format from your system prompt.
"""


@observe(name="instrumentation-agent", as_type="agent", capture_output=False)
async def run_agent(
    prompt: str, spec_dir: Path, out_dir: Path, skill_names: list[str]
) -> str:
    options = ClaudeAgentOptions(
        cwd=str(REPO_ROOT),
        add_dirs=[str(spec_dir), str(out_dir)],
        allowed_tools=["Read", "Glob", "Grep", "Write"],
        permission_mode="bypassPermissions",
        system_prompt=build_system_prompt(skill_names),
        skills=skill_names or None,
        setting_sources=["project"],
        max_turns=60,
        model=AGENT_MODEL,
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


@observe(name="instrumentation-agent-run")
def main():
    parser = argparse.ArgumentParser(
        description="Instrumentation Agent: design ClickHouse DDL from a feature spec"
    )
    parser.add_argument(
        "spec_dir", type=Path, help="folder containing spec.md and events.ndjson"
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=None,
        help="where profile.md is read from / ddl.sql and justification.md are "
        "written (default: spec_dir)",
    )
    args = parser.parse_args()

    spec_dir = args.spec_dir.resolve()
    out_dir = (args.out_dir or spec_dir).resolve()
    spec_path = spec_dir / "spec.md"
    langfuse_client.update_current_span(
        input={"spec_dir": str(spec_dir), "out_dir": str(out_dir)}
    )

    if not spec_dir.is_dir():
        print(f"error: {spec_dir} is not a directory", file=sys.stderr)
        return 1
    if not spec_path.exists():
        print(f"error: spec.md not found in {spec_dir}", file=sys.stderr)
        return 1

    try:
        profile_path = ensure_profile(spec_dir, out_dir)
    except (FileNotFoundError, RuntimeError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    skill_names = discover_skills(VENDORED_SKILLS_DIR, PROJECT_SKILLS_DIR)
    if skill_names:
        print(f"skills discovered: {', '.join(skill_names)}", file=sys.stderr)
    else:
        print(f"no skills found under {VENDORED_SKILLS_DIR}", file=sys.stderr)

    prompt = build_prompt(spec_path, profile_path, out_dir)
    summary = asyncio.run(run_agent(prompt, spec_dir, out_dir, skill_names))
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
