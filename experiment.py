#!/usr/bin/env python3
# ============================================================
# DO NOT EDIT — this file is managed at the top level.
# Neither the Supervisor nor the Scientist should modify it.
# ============================================================
#
# Runs an experiment: one or more Supervisor studies.
#
# Usage:
#   uv run experiment                          # 5 studies, opus (default)
#   uv run experiment --studies 3              # 3 studies
#   uv run experiment --timeout 7200           # 2-hour per-study timeout
#   uv run experiment --model sonnet           # use sonnet for Supervisor

import argparse
import shutil
import signal
import subprocess
import sys
from datetime import datetime
from pathlib import Path

DEFAULT_MODEL = "opus"
DEFAULT_STUDIES = 5
DEFAULT_STUDY_TIMEOUT = 36000  # 10 hours per study
ALLOWED_TOOLS = "Read,Edit,Write,Bash"
SUPERVISOR_PROMPT = "Read and follow supervisor/method.md"
SCIENTIST_DIR = Path("scientist")

# Immediate exit on Ctrl-C
signal.signal(signal.SIGINT, lambda *_: sys.exit(130))


def discover_problems():
    """Auto-discover problem directories under scientist/."""
    return sorted(
        d.name for d in SCIENTIST_DIR.iterdir()
        if d.is_dir() and (d / "program.md").exists()
    )


def run_experiment(num_studies=DEFAULT_STUDIES, study_timeout=DEFAULT_STUDY_TIMEOUT, model=DEFAULT_MODEL):
    """Run an experiment of sequential studies."""
    from supervisor.evaluate import analyse_and_save

    claude_cmd = [
        "claude", "-p",
        "--verbose",
        "--model", model,
        "--output-format", "stream-json",
        "--allowedTools", ALLOWED_TOOLS,
    ]

    problems = discover_problems()
    print(f"Problems: {', '.join(problems)}", file=sys.stderr)

    for i in range(1, num_studies + 1):
        study_timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        print(f"=== Study {i} / {num_studies} ({study_timestamp}) ===", file=sys.stderr)

        # Archive current scientist/ state
        archive_dir = Path("archive") / study_timestamp
        shutil.copytree("scientist", archive_dir, ignore=shutil.ignore_patterns("__pycache__"))
        print(f"  Archived scientist/ → {archive_dir}", file=sys.stderr)

        # Reset each problem's train.py to baseline and delete ephemeral results
        for problem in problems:
            problem_dir = SCIENTIST_DIR / problem
            original = problem_dir / "archive" / "original.py"
            train = problem_dir / "train.py"
            if original.exists():
                shutil.copy(original, train)
            results = problem_dir / "results.tsv"
            results.unlink(missing_ok=True)

        # Git commit current state
        subprocess.run(["git", "add", "-A"], check=False)
        subprocess.run(
            ["git", "commit", "-m", f"archive study {study_timestamp}"],
            check=False,
        )

        # Run the Supervisor
        log_dir = Path("logs") / study_timestamp
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / f"study.jsonl"
        try:
            with open(log_file, "w") as f:
                subprocess.run(
                    claude_cmd,
                    input=SUPERVISOR_PROMPT,
                    text=True,
                    stdout=f,
                    stderr=sys.stderr,
                    timeout=study_timeout,
                )
        except subprocess.TimeoutExpired:
            print(f"=== Study {i} timed out after {study_timeout}s, skipping ===", file=sys.stderr)

        # Evaluate study and persist results
        try:
            all_stats = analyse_and_save(timestamp=study_timestamp)
            if all_stats and "_aggregate" in all_stats:
                agg = all_stats["_aggregate"]
                print(f"  Aggregate: improvement={agg['total_improvement']:+.6f}, "
                      f"velocity={agg['overall_velocity']:+.6f}/trial", file=sys.stderr)
                for problem in problems:
                    if problem in all_stats:
                        s = all_stats[problem]
                        print(f"  {problem}: improvement={s['total_improvement']:+.6f}, "
                              f"velocity={s['overall_velocity']:+.6f}/trial", file=sys.stderr)
            else:
                print(f"  Study result: too few trials to analyse", file=sys.stderr)
        except Exception as e:
            print(f"  Warning: study evaluation failed: {e}", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(description="Run an experiment: one or more Supervisor studies.")
    parser.add_argument("--studies", type=int, default=DEFAULT_STUDIES, help=f"Number of studies (default: {DEFAULT_STUDIES})")
    parser.add_argument("--timeout", type=int, default=DEFAULT_STUDY_TIMEOUT, help=f"Per-study timeout in seconds (default: {DEFAULT_STUDY_TIMEOUT})")
    parser.add_argument("--model", type=str, default=DEFAULT_MODEL, help=f"Claude model to use (default: {DEFAULT_MODEL})")
    args = parser.parse_args()

    run_experiment(num_studies=args.studies, study_timeout=args.timeout, model=args.model)


if __name__ == "__main__":
    main()
