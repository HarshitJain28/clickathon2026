"""Orchestrator.

Chains the two agents: given a feature spec directory, run the Instrumentation
Agent to produce ddl.sql/justification.md/profile.md into an output
directory, then run the Context Agent on that same output directory to update
the wiki. Does nothing else — no logic of its own beyond passing paths along.

Usage:
    python orchestrator.py <spec_dir> [--out-dir DIR] [--context-dir DIR]

<spec_dir> must contain spec.md and events.ndjson (e.g.
ps/Atlys/specs/01_express_checkout). --out-dir defaults to
out/<spec_dir name> (e.g. out/01_express_checkout), matching this repo's
existing out/ layout.
"""

import argparse
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
INSTRUMENTATION_AGENT = REPO_ROOT / "instrumentation_agent.py"
CONTEXT_AGENT = REPO_ROOT / "context_agent.py"


def main():
    parser = argparse.ArgumentParser(
        description="Orchestrator: Instrumentation Agent -> Context Agent"
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
    args = parser.parse_args()

    spec_dir = args.spec_dir.resolve()
    out_dir = (args.out_dir or REPO_ROOT / "out" / spec_dir.name).resolve()

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

    context_cmd = [sys.executable, str(CONTEXT_AGENT), str(out_dir)]
    if args.context_dir:
        context_cmd += ["--context-dir", str(args.context_dir)]
    result = subprocess.run(context_cmd)
    if result.returncode != 0:
        print("error: context_agent.py failed", file=sys.stderr)
        return result.returncode

    return 0


if __name__ == "__main__":
    sys.exit(main())
