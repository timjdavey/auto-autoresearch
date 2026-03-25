"""Runs a study: one or more Scientist invocations across all problems."""

import os
import shutil
import signal
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

from human.cli import build_cmd
from scientist import SCIENTIST_DIR, discover_problems
from human.reset import soft_reset
from supervisor.evaluate import load_results

DEFAULT_MODEL = "haiku"
DEFAULT_TRIALS = 10
DEFAULT_MAX_TURNS = 25
DEFAULT_MAX_BUDGET = 0.25
ALLOWED_TOOLS = "Read,Edit,Write,Bash(python3:*),Bash(grep:*),Bash(tail:*),Bash(cat:*)"

# Track active child process groups so SIGINT can clean them up
_active_pgids = set()
_pgid_lock = threading.Lock()


def _sigint_handler(*_):
    """Kill all active child process groups, then exit."""
    with _pgid_lock:
        for pgid in _active_pgids:
            try:
                os.killpg(pgid, signal.SIGTERM)
            except OSError:
                pass
    sys.exit(130)


signal.signal(signal.SIGINT, _sigint_handler)


def run_trial(problem, trial_num, timestamp, log_dir, model, max_turns, max_budget_usd=None):
    """Run a single trial for a single problem. Returns (problem, trial_num, status, elapsed)."""
    problem_dir = SCIENTIST_DIR / problem
    archive_dir = problem_dir / "archive"

    # Archive train.py before Scientist modifies it
    train_path = problem_dir / "train.py"
    if train_path.exists():
        shutil.copy(train_path, archive_dir / f"trial-{trial_num:03d}.py")

    prompt = f"Read and follow scientist/{problem}/program.md"
    cli_cmd, stdin_input = build_cmd(model, prompt, ALLOWED_TOOLS, max_budget_usd=max_budget_usd, max_turns=max_turns)
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
        with _pgid_lock:
            _active_pgids.add(proc.pid)
        try:
            proc.communicate(input=stdin_input)
        finally:
            with _pgid_lock:
                _active_pgids.discard(proc.pid)
    elapsed = time.monotonic() - start
    if proc.returncode != 0:
        return problem, trial_num, "FAILED", elapsed
    return problem, trial_num, "done", elapsed


def _curate_archive(problem_dir):
    """Maintain archive/best.py after each trial."""
    results_path = problem_dir / "results.tsv"
    rows = load_results(results_path)
    if not rows:
        return

    archive_dir = problem_dir / "archive"

    # Find the best trial and copy its code to archive/best.py
    best_idx = max(range(len(rows)), key=lambda i: rows[i]["avg_improvement"])
    best_trial_num = best_idx + 1  # trials are 1-indexed
    best_file = archive_dir / f"trial-{best_trial_num:03d}.py"
    if best_file.exists():
        shutil.copy(best_file, archive_dir / "best.py")


def _run_problem_trials(problem, num_trials, timestamp, log_dir, model, max_turns, max_budget_usd=None):
    """Run all trials for a single problem sequentially."""
    study_start = time.monotonic()
    problem_label = problem[:16].ljust(16)
    for i in range(1, num_trials + 1):
        problem, trial_num, status, elapsed = run_trial(
            problem, i, timestamp, log_dir, model, max_turns, max_budget_usd=max_budget_usd
        )
        total = time.monotonic() - study_start

        # Read metric from results.tsv for richer output
        metric_str = ""
        if status == "done":
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

        # Curate archive: maintain best.py
        try:
            _curate_archive(SCIENTIST_DIR / problem)
        except Exception:
            pass


def run_study(num_trials=DEFAULT_TRIALS, max_turns=DEFAULT_MAX_TURNS, model=DEFAULT_MODEL, sequential=True, max_budget_usd=DEFAULT_MAX_BUDGET):
    """Run a study across all problems and return the log directory path."""
    problems = discover_problems()
    if not problems:
        raise RuntimeError("No problems found in scientist/. Each problem needs a program.md.")

    print(f"Problems: {', '.join(problems)}", file=sys.stderr)

    # Reset per-problem state for a clean slate
    soft_reset(problems, verbose=False)

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    log_dir = Path("logs") / timestamp
    log_dir.mkdir(parents=True, exist_ok=True)

    # Run each problem's full trial sequence
    max_workers = 1 if sequential else len(problems)
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {
            pool.submit(
                _run_problem_trials, problem, num_trials,
                timestamp, log_dir, model, max_turns, max_budget_usd
            ): problem
            for problem in problems
        }
        for future in as_completed(futures):
            future.result()  # propagate exceptions

    return log_dir
