#!/usr/bin/env python3
# ============================================================
# DO NOT EDIT — this file is managed at the top level.
# Neither the Supervisor nor the Scientist should modify it.
# ============================================================
#
# Runs a study: one or more Scientist invocations across all problems.
#
# Usage:
#   uv run studies                            # sonnet (default)
#   uv run studies --trials 5                 # 5 fresh-context trials
#   uv run studies --timeout 300              # 5-minute per-trial timeout
#   uv run studies --opus                     # run with opus (for testing)

import argparse
import os
import shutil
import signal
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

from scientist import SCIENTIST_DIR, discover_problems
from reset import soft_reset
from supervisor.evaluate import analyse_and_save

DEFAULT_MODEL = "sonnet"
DEFAULT_TRIALS = 15
DEFAULT_TIMEOUT = 600
ALLOWED_TOOLS = "Read,Edit,Write,Bash(python3:*),Bash(grep:*),Bash(tail:*),Bash(cat:*)"

# Immediate exit on Ctrl-C
signal.signal(signal.SIGINT, lambda *_: sys.exit(130))


def run_trial(problem, trial_num, timestamp, log_dir, claude_cmd, trial_timeout):
    """Run a single trial for a single problem. Returns (problem, trial_num, success)."""
    problem_dir = SCIENTIST_DIR / problem
    archive_dir = problem_dir / "archive" / timestamp
    archive_dir.mkdir(parents=True, exist_ok=True)

    # Archive train.py before Scientist modifies it
    train_path = problem_dir / "train.py"
    if train_path.exists():
        shutil.copy(train_path, archive_dir / f"trial-{trial_num:03d}.py")

    prompt = f"Read and follow scientist/{problem}/program.md"
    log_file = log_dir / f"{problem}-trial-{trial_num:03d}.jsonl"
    with open(log_file, "w") as f:
        proc = subprocess.Popen(
            claude_cmd,
            stdin=subprocess.PIPE,
            stdout=f,
            stderr=sys.stderr,
            text=True,
            start_new_session=True,
        )
        try:
            proc.communicate(input=prompt, timeout=trial_timeout)
        except subprocess.TimeoutExpired:
            print(f"=== {problem} trial {trial_num} timed out after {trial_timeout}s, killing process group ===", file=sys.stderr)
            os.killpg(proc.pid, signal.SIGTERM)
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(proc.pid, signal.SIGKILL)
                proc.wait()
            return problem, trial_num, False
    if proc.returncode != 0:
        print(f"=== {problem} trial {trial_num} failed (exit code {proc.returncode}) ===", file=sys.stderr)
        return problem, trial_num, False
    return problem, trial_num, True


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

    claude_cmd = [
        "claude", "-p",
        "--verbose",
        "--model", model,
        "--output-format", "stream-json",
        "--allowedTools", ALLOWED_TOOLS,
    ]

    for i in range(1, num_trials + 1):
        print(f"=== Trial {i} / {num_trials} ({', '.join(problems)}) ===", file=sys.stderr)

        # Run all problems in parallel for this trial
        with ThreadPoolExecutor(max_workers=len(problems)) as pool:
            futures = {
                pool.submit(run_trial, problem, i, timestamp, log_dir, claude_cmd, trial_timeout): problem
                for problem in problems
            }
            for future in as_completed(futures):
                problem, trial_num, success = future.result()
                status = "done" if success else "TIMEOUT"
                print(f"  {problem} trial {trial_num}: {status}", file=sys.stderr)

    try:
        analyse_and_save(timestamp=timestamp)
    except Exception as e:
        print(f"  Warning: analyse_and_save failed: {e}", file=sys.stderr)
    return log_dir


def main():
    parser = argparse.ArgumentParser(description="Run a study: one or more Scientist invocations.")
    parser.add_argument("--trials", type=int, default=DEFAULT_TRIALS, help=f"Number of trials (default: {DEFAULT_TRIALS})")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT, help=f"Per-trial timeout in seconds (default: {DEFAULT_TIMEOUT})")
    parser.add_argument("--model", type=str, default=DEFAULT_MODEL, help=f"Claude model to use (default: {DEFAULT_MODEL})")
    parser.add_argument("--opus", action="store_true", help="Shorthand for --model opus")
    args = parser.parse_args()

    model = "opus" if args.opus else args.model
    log_dir = run_study(num_trials=args.trials, trial_timeout=args.timeout, model=model)
    print(f"Logs: {log_dir}", file=sys.stderr)


if __name__ == "__main__":
    main()
