#!/usr/bin/env python3
# ============================================================
# DO NOT EDIT — this file is managed at the top level.
# Neither the Supervisor nor the Scientist should modify it.
# ============================================================
#
# Runs a study: one or more Scientist invocations across all problems.
#
# Usage:
#   uv run studies                            # haiku (default)
#   uv run studies --trials 5                 # 5 fresh-context trials
#   uv run studies --timeout 300              # 5-minute per-trial timeout
#   uv run studies --opus                     # run with opus (for testing)
#   uv run studies --haiku                    # run with haiku (explicit)
#   uv run studies --pro                      # run with gemini pro
#   uv run studies --flash                    # run with gemini flash

import argparse
import csv
import importlib
import os
import shutil
import signal
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

from cli import build_cmd
from scientist import SCIENTIST_DIR, discover_problems
from reset import soft_reset
from supervisor.evaluate import analyse_and_save, load_results

DEFAULT_MODEL = "haiku"
DEFAULT_TRIALS = 10
DEFAULT_TIMEOUT = 600
ALLOWED_TOOLS = "Read,Edit,Write,Bash(python3:*),Bash(grep:*),Bash(tail:*),Bash(cat:*)"

# Immediate exit on Ctrl-C
signal.signal(signal.SIGINT, lambda *_: sys.exit(130))


def _log_timeout(problem_dir, problem_name, trial_timeout):
    """Append a scientist_timeout row to results.tsv so the Scientist sees what happened."""
    # Import the problem's prepare module to get its RESULT_FIELDS
    mod = importlib.import_module(f"scientist.{problem_name}.prepare")
    fields = mod.RESULT_FIELDS

    row = {f: "" for f in fields}
    row["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    row["status"] = "scientist_timeout"
    row["training_time"] = trial_timeout
    row["notes"] = f"Scientist process killed after {trial_timeout}s"

    results_path = problem_dir / "results.tsv"
    write_header = not results_path.exists()
    with open(results_path, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, delimiter="\t")
        if write_header:
            writer.writeheader()
        writer.writerow(row)


def run_trial(problem, trial_num, timestamp, log_dir, model, trial_timeout):
    """Run a single trial for a single problem. Returns (problem, trial_num, status, elapsed)."""
    problem_dir = SCIENTIST_DIR / problem
    archive_dir = problem_dir / "archive" / timestamp
    archive_dir.mkdir(parents=True, exist_ok=True)

    # Archive train.py before Scientist modifies it
    train_path = problem_dir / "train.py"
    if train_path.exists():
        shutil.copy(train_path, archive_dir / f"trial-{trial_num:03d}.py")

    prompt = f"Read and follow scientist/{problem}/program.md"
    cli_cmd, stdin_input = build_cmd(model, prompt, ALLOWED_TOOLS)
    log_file = log_dir / f"{problem}-trial-{trial_num:03d}.jsonl"
    start = time.monotonic()
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
            proc.communicate(input=stdin_input, timeout=trial_timeout)
        except subprocess.TimeoutExpired:
            elapsed = time.monotonic() - start
            os.killpg(proc.pid, signal.SIGTERM)
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(proc.pid, signal.SIGKILL)
                proc.wait()
            _log_timeout(problem_dir, problem, trial_timeout)
            return problem, trial_num, "TIMEOUT", elapsed
    elapsed = time.monotonic() - start
    if proc.returncode != 0:
        return problem, trial_num, "FAILED", elapsed
    return problem, trial_num, "done", elapsed


def _run_problem_trials(problem, num_trials, timestamp, log_dir, model, trial_timeout):
    """Run all trials for a single problem sequentially."""
    study_start = time.monotonic()
    problem_label = problem[:16].ljust(16)
    for i in range(1, num_trials + 1):
        problem, trial_num, status, elapsed = run_trial(
            problem, i, timestamp, log_dir, model, trial_timeout
        )
        total = time.monotonic() - study_start

        # Read metric from results.tsv for richer output
        metric_str = ""
        if status != "TIMEOUT":
            results_path = SCIENTIST_DIR / problem / "results.tsv"
            try:
                rows = load_results(results_path)
                if rows:
                    current = rows[-1]["avg_improvement"]
                    metric_str = f"  avg={current:+.4f}"
                    if len(rows) >= 2:
                        prev = rows[-2]["avg_improvement"]
                        delta = current - prev
                        metric_str += f" ({delta:+.4f})"
            except Exception:
                pass

        status_label = status.ljust(7)
        print(
            f"  {problem_label} trial {trial_num:>2}/{num_trials}: {status_label}{metric_str}"
            f"  ({elapsed:.1f}s) [total: {total:.1f}s]",
            file=sys.stderr,
        )


def run_study(num_trials=DEFAULT_TRIALS, trial_timeout=DEFAULT_TIMEOUT, model=DEFAULT_MODEL):
    """Run a study across all problems and return the log directory path."""
    problems = discover_problems()
    if not problems:
        raise RuntimeError("No problems found in scientist/. Each problem needs a program.md.")

    print(f"Problems: {', '.join(problems)}", file=sys.stderr)

    # Reset per-problem state for a clean slate
    soft_reset(problems)

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    log_dir = Path("logs") / timestamp
    log_dir.mkdir(parents=True, exist_ok=True)

    # Run each problem's full trial sequence in parallel
    with ThreadPoolExecutor(max_workers=len(problems)) as pool:
        futures = {
            pool.submit(
                _run_problem_trials, problem, num_trials,
                timestamp, log_dir, model, trial_timeout
            ): problem
            for problem in problems
        }
        for future in as_completed(futures):
            future.result()  # propagate exceptions

    try:
        analyse_and_save(timestamp=timestamp)
    except Exception as e:
        print(f"  Warning: analyse_and_save failed: {e}", file=sys.stderr)
    return log_dir


def main():
    parser = argparse.ArgumentParser(description="Run a study: one or more Scientist invocations.")
    parser.add_argument("--trials", type=int, default=DEFAULT_TRIALS, help=f"Number of trials (default: {DEFAULT_TRIALS})")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT, help=f"Per-trial timeout in seconds (default: {DEFAULT_TIMEOUT})")
    parser.add_argument("--model", type=str, default=DEFAULT_MODEL, help=f"Model to use: opus/sonnet/haiku (Claude) or pro/flash (Gemini) (default: {DEFAULT_MODEL})")
    parser.add_argument("--opus", action="store_true", help="Shorthand for --model opus")
    parser.add_argument("--haiku", action="store_true", help="Shorthand for --model haiku")
    parser.add_argument("--pro", action="store_true", help="Shorthand for --model pro (Gemini)")
    parser.add_argument("--flash", action="store_true", help="Shorthand for --model flash (Gemini)")
    args = parser.parse_args()

    model = ("opus" if args.opus else "haiku" if args.haiku
             else "pro" if args.pro else "flash" if args.flash
             else args.model)
    log_dir = run_study(num_trials=args.trials, trial_timeout=args.timeout, model=model)
    print(f"Logs: {log_dir}", file=sys.stderr)


if __name__ == "__main__":
    main()
