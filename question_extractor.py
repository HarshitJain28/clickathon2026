"""Question Extractor.

Extracts the "## Questions the PM will ask" bullet list from a feature
spec's spec.md and calls analysis_agent.py with each question, concurrently
— the questions are independent (different qNN.md output files, no shared
write target: analysis_agent.py is read-only against context/, see its own
docstring). Does nothing else — no logic beyond parsing and passing
questions along.

Usage:
    python question_extractor.py <spec_dir> [--out-dir DIR] [--context-dir DIR]
                                  [--max-workers N]

<spec_dir> must contain spec.md (e.g. ps/Atlys/specs/01_express_checkout).
--out-dir defaults to out/<spec_dir name>/analysis, where analysis_agent.py
writes one HTML file per question. Run context_agent.py on the spec's
top-level out_dir AFTER this script finishes — it's the single writer that
consolidates every qNN.md's findings into context/.
"""

import argparse
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
ANALYSIS_AGENT = REPO_ROOT / "analysis_agent.py"

QUESTIONS_HEADING = "## questions the pm will ask"


def extract_questions(spec_md: Path) -> list[str]:
    """Return the bullet-list questions under "## Questions the PM will ask",
    joining any indented continuation lines back into the bullet they
    belong to."""
    lines = spec_md.read_text().splitlines()

    start = None
    for i, line in enumerate(lines):
        if line.strip().lower() == QUESTIONS_HEADING:
            start = i + 1
            break
    if start is None:
        return []

    questions = []
    current = None
    for line in lines[start:]:
        stripped = line.strip()
        if stripped.startswith("## "):
            break
        if stripped.startswith("- "):
            if current is not None:
                questions.append(current)
            current = stripped[2:].strip()
        elif stripped and current is not None:
            current += " " + stripped
    if current is not None:
        questions.append(current)
    return questions


def run_one(i: int, question: str, out_dir: Path, context_dir: Path | None) -> tuple[int, str, subprocess.CompletedProcess]:
    """Run analysis_agent.py for one question, capturing its output rather
    than letting it interleave with sibling runs on the shared console."""
    cmd = [
        sys.executable,
        str(ANALYSIS_AGENT),
        question,
        "--out-dir",
        str(out_dir),
        "--index",
        str(i),
    ]
    if context_dir:
        cmd += ["--context-dir", str(context_dir)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return i, question, result


def main():
    parser = argparse.ArgumentParser(
        description="Question Extractor: spec.md's PM questions -> "
        "analysis_agent.py, run concurrently"
    )
    parser.add_argument(
        "spec_dir", type=Path, help="folder containing spec.md"
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=None,
        help="directory analysis_agent.py writes HTML files into (default: "
        "out/<spec_dir name>/analysis)",
    )
    parser.add_argument(
        "--context-dir",
        type=Path,
        default=None,
        help="context wiki root passed through to analysis_agent.py "
        "(default: context/)",
    )
    parser.add_argument(
        "--max-workers",
        type=int,
        default=None,
        help="max concurrent analysis_agent.py runs (default: one per "
        "question, i.e. fully concurrent)",
    )
    args = parser.parse_args()

    spec_dir = args.spec_dir.resolve()
    spec_md = spec_dir / "spec.md"
    if not spec_md.exists():
        print(f"error: spec.md not found in {spec_dir}", file=sys.stderr)
        return 1

    questions = extract_questions(spec_md)
    if not questions:
        print(
            f"error: no '## Questions the PM will ask' section found in {spec_md}",
            file=sys.stderr,
        )
        return 1

    out_dir = (args.out_dir or REPO_ROOT / "out" / spec_dir.name / "analysis").resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"found {len(questions)} question(s) in {spec_md} -- running concurrently", file=sys.stderr)

    max_workers = args.max_workers or len(questions)
    failures = 0
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {
            pool.submit(run_one, i, question, out_dir, args.context_dir): i
            for i, question in enumerate(questions, start=1)
        }
        for future in as_completed(futures):
            i, question, result = future.result()
            print(f"\n[{i}/{len(questions)}] {question}", file=sys.stderr)
            if result.stdout:
                print(result.stdout, file=sys.stderr)
            if result.stderr:
                print(result.stderr, file=sys.stderr)
            if result.returncode != 0:
                failures += 1
                print(f"error: analysis_agent.py failed on question {i}", file=sys.stderr)

    if failures:
        print(f"\n{failures}/{len(questions)} question(s) failed", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
