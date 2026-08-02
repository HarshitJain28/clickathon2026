"""Orchestrator.

Chains a spec through: Instrumentation Agent (produces ddl.sql/
justification.md/profile.md) -> Loader (creates/loads the tables in
ClickHouse) -> Context Agent, PASS 1 (publishes new/altered table pages and
any known_issues.md caveats load_report.md surfaced, e.g. a D2-style broken
join key) -> Question Extractor (runs the Analysis Agent once per PM
question in spec.md, all CONCURRENTLY -- see question_extractor.py) ->
Context Agent, PASS 2 (consolidates every analysis/qNN.md the concurrent
Analysis Agent runs just produced into known_issues.md/table pages/metrics/
log.md). Does nothing else -- no logic of its own beyond passing paths along.

Context Agent runs twice, not once, on purpose:
- PASS 1 has to happen BEFORE the Analysis Agent runs, not after: it's how
  the Analysis Agent learns about this spec's new tables and any
  known-issue caveat (e.g. "application_id doesn't join, use user_id
  instead") in the first place, since the Analysis Agent orients from the
  wiki, not from re-deriving schema/join-safety facts itself.
- The Analysis Agent runs are concurrent and read-only against context/ (see
  analysis_agent.py) precisely so nothing writes to the wiki mid-flight;
  PASS 2, after they've all finished, is the single writer that folds their
  findings in. Skipped automatically if no PM questions were found.

Usage:
    python orchestrator.py <spec_dir> [--out-dir DIR] [--context-dir DIR]
                           [--skip-instrumentation]

<spec_dir> must contain spec.md and events.ndjson (e.g.
ps/Atlys/specs/01_express_checkout). --out-dir defaults to
out/<spec_dir name> (e.g. out/01_express_checkout), matching this repo's
existing out/ layout. The Question Extractor/Analysis Agent step writes into
<out-dir>/analysis, one qNN.md (plus qNN_report.html when warranted) per PM
question.

--skip-instrumentation assumes ddl.sql/justification.md/profile.md already
exist in --out-dir from a prior Instrumentation Agent run, and starts from
the Loader instead. This is what lets a caller (e.g. the web UI) run the
Instrumentation Agent alone first, hold for a human to review/approve the
proposed schema, and only then continue the rest of the pipeline against
the same output directory — the schema design is never re-run.

The Loader step is generic across specs: it derives table/column names from
ddl.sql and any required normalization/verification from justification.md's
cited known_issues.md ids (see context/SCHEMA.md's "Loader-actionable fix
blocks" rule). A load-time data finding (e.g. a 0% join-key overlap) does not
stop the pipeline — it's recorded in load_report.md for the Context Agent to
document, not a technical failure.
"""

import argparse
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
INSTRUMENTATION_AGENT = REPO_ROOT / "instrumentation_agent.py"
LOADER = REPO_ROOT / "loader.py"
CONTEXT_AGENT = REPO_ROOT / "context_agent.py"
QUESTION_EXTRACTOR = REPO_ROOT / "question_extractor.py"


def main():
    parser = argparse.ArgumentParser(
        description="Orchestrator: Instrumentation Agent -> Loader -> "
        "Context Agent (pass 1) -> Question Extractor (concurrent Analysis "
        "Agent runs) -> Context Agent (pass 2, consolidates findings)"
    )
    parser.add_argument(
        "spec_dir", type=Path, help="folder containing spec.md and events.ndjson"
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=None,
        help="where the Instrumentation Agent writes its output (default: "
        "out/<spec_dir name>)",
    )
    parser.add_argument(
        "--context-dir",
        type=Path,
        default=None,
        help="context wiki root passed through to the Context Agent "
        "(default: context/)",
    )
    parser.add_argument(
        "--skip-instrumentation",
        action="store_true",
        help="skip the Instrumentation Agent stage (ddl.sql/justification.md/"
        "profile.md must already exist in --out-dir) and start from the Loader",
    )
    args = parser.parse_args()

    spec_dir = args.spec_dir.resolve()
    out_dir = (args.out_dir or REPO_ROOT / "out" / spec_dir.name).resolve()

    if not args.skip_instrumentation:
        instrumentation_cmd = [
            sys.executable,
            str(INSTRUMENTATION_AGENT),
            str(spec_dir),
            "--out-dir",
            str(out_dir),
        ]
        result = subprocess.run(instrumentation_cmd)
        if result.returncode != 0:
            print("error: instrumentation_agent.py failed", file=sys.stderr)
            return result.returncode

    loader_cmd = [
        sys.executable,
        str(LOADER),
        str(spec_dir),
        "--out-dir",
        str(out_dir),
    ]
    if args.context_dir:
        loader_cmd += ["--context-dir", str(args.context_dir)]
    result = subprocess.run(loader_cmd)
    if result.returncode != 0:
        print("error: loader.py failed", file=sys.stderr)
        return result.returncode

    # Pass 1: publish this spec's schema/known-issue caveats into the wiki
    # BEFORE the Analysis Agent runs, so it has them to orient from.
    context_cmd = [sys.executable, str(CONTEXT_AGENT), str(out_dir)]
    if args.context_dir:
        context_cmd += ["--context-dir", str(args.context_dir)]
    result = subprocess.run(context_cmd)
    if result.returncode != 0:
        print("error: context_agent.py (pass 1) failed", file=sys.stderr)
        return result.returncode

    question_extractor_cmd = [
        sys.executable,
        str(QUESTION_EXTRACTOR),
        str(spec_dir),
        "--out-dir",
        str(out_dir / "analysis"),
    ]
    if args.context_dir:
        question_extractor_cmd += ["--context-dir", str(args.context_dir)]
    result = subprocess.run(question_extractor_cmd)
    if result.returncode != 0:
        print("error: question_extractor.py failed", file=sys.stderr)
        return result.returncode

    # Pass 2: single-writer consolidation of every analysis/qNN.md the
    # concurrent Analysis Agent runs just produced.
    result = subprocess.run(context_cmd)
    if result.returncode != 0:
        print("error: context_agent.py (pass 2) failed", file=sys.stderr)
        return result.returncode

    return 0


if __name__ == "__main__":
    sys.exit(main())
