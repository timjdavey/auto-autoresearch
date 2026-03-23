#!/usr/bin/env python3
# ============================================================
# DO NOT EDIT — this file is managed at the top level.
# Neither the Supervisor nor the Scientist should modify it.
# ============================================================
#
# Runs an experiment: one or more Supervisor studies.
#
# Usage:
#   uv run experiment                          # 20 studies, opus (default)
#   uv run experiment --studies 3              # 3 studies
#   uv run experiment --timeout 7200           # 2-hour per-study timeout
#   uv run experiment --trials 5                # 5 trials per study
#   uv run experiment --model sonnet           # use sonnet for Supervisor
#   uv run experiment --model pro              # use gemini pro for Supervisor

import argparse
import os
import shutil
import signal
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from cli import build_cmd
from scientist import SCIENTIST_DIR, discover_problems
from reset import soft_reset
from supervisor.evaluate import analyse_and_save
from supervisor.studies import run_study

DEFAULT_MODEL = "opus"
DEFAULT_STUDIES = 20
DEFAULT_STUDY_TIMEOUT = 36000  # 10 hours per study
ALLOWED_TOOLS = "Read,Edit,Write,Bash"
SUPERVISOR_PRE_PROMPT = "Read and follow supervisor/method.md — PRE-STUDY phase only."
SUPERVISOR_POST_PROMPT = "Read and follow supervisor/method.md — POST-STUDY phase only."

# Immediate exit on Ctrl-C
signal.signal(signal.SIGINT, lambda *_: sys.exit(130))


def run_supervisor(model, allowed_tools, prompt, log_file, timeout):
    """Run a Supervisor CLI call (Claude or Gemini), logging to log_file."""
    cli_cmd, stdin_input = build_cmd(model, prompt, allowed_tools)
    with open(log_file, "w") as f:
        proc = subprocess.Popen(
            cli_cmd,
            stdin=subprocess.PIPE,
            stdout=f,
            stderr=sys.stderr,
            text=True,
            start_new_session=True,
        )
        try:
            proc.communicate(input=stdin_input, timeout=timeout)
        except subprocess.TimeoutExpired:
            print(f"  Supervisor call timed out after {timeout}s, killing process group", file=sys.stderr)
            os.killpg(proc.pid, signal.SIGTERM)
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(proc.pid, signal.SIGKILL)
                proc.wait()
            return False
    if proc.returncode != 0:
        print(f"  Supervisor call failed (exit code {proc.returncode})", file=sys.stderr)
        return False
    return True


def run_experiment(num_studies=DEFAULT_STUDIES, study_timeout=DEFAULT_STUDY_TIMEOUT, model=DEFAULT_MODEL, num_trials=None):
    """Run an experiment of sequential studies."""
    problems = discover_problems()
    print(f"Problems: {', '.join(problems)}", file=sys.stderr)

    for i in range(1, num_studies + 1):
        study_timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        print(f"=== Study {i} / {num_studies} ({study_timestamp}) ===", file=sys.stderr)

        try:
            # Archive current scientist/ state
            archive_dir = Path("archive") / study_timestamp
            shutil.copytree("scientist", archive_dir, ignore=shutil.ignore_patterns("__pycache__"))
            print(f"  Archived scientist/ → {archive_dir}", file=sys.stderr)

            # Reset each problem's train.py to baseline and delete ephemeral results
            soft_reset(problems)

            # Git commit current state
            result = subprocess.run(["git", "add", "-A"], capture_output=True, text=True)
            if result.returncode != 0:
                print(f"  Warning: git add failed: {result.stderr.strip()}", file=sys.stderr)
            result = subprocess.run(
                ["git", "commit", "-m", f"archive study {study_timestamp}"],
                capture_output=True, text=True,
            )
            if result.returncode != 0 and "nothing to commit" not in result.stdout:
                print(f"  Warning: git commit failed: {result.stderr.strip()}", file=sys.stderr)

            log_dir = Path("logs") / study_timestamp
            log_dir.mkdir(parents=True, exist_ok=True)

            # Phase 1: Pre-study Supervisor call
            print(f"  Phase 1: Pre-study planning", file=sys.stderr)
            if not run_supervisor(model, ALLOWED_TOOLS, SUPERVISOR_PRE_PROMPT, log_dir / "pre-study.jsonl", study_timeout):
                print(f"  Pre-study supervisor failed, skipping study {i}", file=sys.stderr)
                continue

            # Phase 2: Run the study (directly, no Bash timeout issues)
            print(f"  Phase 2: Running trials", file=sys.stderr)
            study_kwargs = {}
            if num_trials is not None:
                study_kwargs["num_trials"] = num_trials
            run_study(**study_kwargs)

            # Evaluate
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

            # Phase 3: Post-study Supervisor call
            print(f"  Phase 3: Post-study review", file=sys.stderr)
            if not run_supervisor(model, ALLOWED_TOOLS, SUPERVISOR_POST_PROMPT, log_dir / "post-study.jsonl", study_timeout):
                print(f"  Warning: post-study supervisor failed (study results are saved)", file=sys.stderr)

        except Exception as e:
            print(f"  Study {i} failed with unexpected error: {e}", file=sys.stderr)
            continue


def main():
    parser = argparse.ArgumentParser(description="Run an experiment: one or more Supervisor studies.")
    parser.add_argument("--studies", type=int, default=DEFAULT_STUDIES, help=f"Number of studies (default: {DEFAULT_STUDIES})")
    parser.add_argument("--timeout", type=int, default=DEFAULT_STUDY_TIMEOUT, help=f"Per-study timeout in seconds (default: {DEFAULT_STUDY_TIMEOUT})")
    parser.add_argument("--model", type=str, default=DEFAULT_MODEL, help=f"Model to use: opus/sonnet/haiku (Claude) or pro/flash (Gemini) (default: {DEFAULT_MODEL})")
    parser.add_argument("--trials", type=int, default=None, help="Number of trials per study (default: study default)")
    args = parser.parse_args()

    run_experiment(num_studies=args.studies, study_timeout=args.timeout, model=args.model, num_trials=args.trials)


if __name__ == "__main__":
    main()
