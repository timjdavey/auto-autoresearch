#!/usr/bin/env python3
# ============================================================
# DO NOT EDIT — this file is managed at the top level.
# Neither the Supervisor nor the Scientist should modify it.
# ============================================================
#
# Reset utilities for clearing experiment / study state.
#
# Usage:
#   uv run reset                              # hard reset (everything)
#   uv run reset --soft                       # soft reset (all problems)
#   uv run reset --soft --problems qap        # soft reset (specific problems)

import argparse
import shutil
import sys
from pathlib import Path

from scientist import SCIENTIST_DIR, discover_problems


def soft_reset(problems=None):
    """Reset per-problem state: archive timestamps, results.tsv, and train.py.

    Args:
        problems: list of problem names, or None for all discovered problems.
    """
    if problems is None:
        problems = discover_problems()

    for problem in problems:
        problem_dir = SCIENTIST_DIR / problem
        if not problem_dir.is_dir():
            print(f"  Warning: problem directory {problem_dir} not found, skipping", file=sys.stderr)
            continue

        # Remove trial snapshots, best.py, and legacy timestamp dirs (preserve original.py)
        archive_dir = problem_dir / "archive"
        if archive_dir.is_dir():
            for child in archive_dir.iterdir():
                if child.is_dir():
                    shutil.rmtree(child)
                    print(f"  Deleted {child}", file=sys.stderr)
            for trial_file in sorted(archive_dir.glob("trial-*.py")):
                trial_file.unlink()
                print(f"  Deleted {trial_file}", file=sys.stderr)
            best_path = archive_dir / "best.py"
            if best_path.exists():
                best_path.unlink()
                print(f"  Deleted {best_path}", file=sys.stderr)

        # Delete results
        results = problem_dir / "results.tsv"
        if results.exists():
            results.unlink()
            print(f"  Deleted {results}", file=sys.stderr)

        # Reset train.py from original.py
        original = archive_dir / "original.py" if archive_dir.is_dir() else None
        train = problem_dir / "train.py"
        if original and original.exists():
            shutil.copy(original, train)
            print(f"  Reset {train} from {original}", file=sys.stderr)


def hard_reset():
    """Full reset: soft reset all problems + delete top-level archive, logs, study_results."""
    soft_reset()

    # Top-level experiment archive
    archive = Path("archive")
    if archive.is_dir():
        shutil.rmtree(archive)
        print(f"  Deleted {archive}/", file=sys.stderr)

    # Logs
    logs = Path("logs")
    if logs.is_dir():
        shutil.rmtree(logs)
        print(f"  Deleted {logs}/", file=sys.stderr)

    # Supervisor study results
    study_results = Path("supervisor") / "study_results.csv"
    if study_results.exists():
        study_results.unlink()
        print(f"  Deleted {study_results}", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(description="Reset experiment / study state.")
    parser.add_argument("--soft", action="store_true", help="Soft reset (per-problem only, keeps top-level archive/logs/study_results)")
    parser.add_argument("--problems", type=str, default=None, help="Comma-separated list of problems to reset (implies --soft)")
    args = parser.parse_args()

    if args.problems:
        problems = [p.strip() for p in args.problems.split(",")]
        print(f"Soft reset: {', '.join(problems)}", file=sys.stderr)
        soft_reset(problems)
    elif args.soft:
        print("Soft reset: all problems", file=sys.stderr)
        soft_reset()
    else:
        print("Hard reset: clearing everything", file=sys.stderr)
        hard_reset()

    print("Done.", file=sys.stderr)


if __name__ == "__main__":
    main()
