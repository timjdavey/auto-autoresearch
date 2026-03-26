#!/usr/bin/env python3
# ============================================================
# DO NOT EDIT — this file is managed at the top level.
# Neither the Supervisor nor the Scientist should modify it.
# ============================================================
#
# Runs an experiment: one or more Supervisor studies, each consisting
# of Scientist trials across all problems.
#
# Usage:
#   uv run experiment                          # 20 studies, opus (default)
#   uv run experiment --studies 3              # 3 studies
#   uv run experiment --timeout 7200           # 2-hour per-study timeout
#   uv run experiment --trials 5               # 5 trials per study
#   uv run experiment --model sonnet           # use sonnet for Supervisor

import argparse
import dataclasses
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

from human.reset import soft_reset
from scientist import SCIENTIST_DIR, discover_problems
from supervisor.evaluate import analyse_and_save, load_results

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Experiment defaults
DEFAULT_MODEL = "opus"
DEFAULT_STUDIES = 20
DEFAULT_STUDY_TIMEOUT = 36_000  # 10 hours per study

# Scientist
SCIENTIST_MODEL = "haiku"
SCIENTIST_TRIALS = 10
SCIENTIST_MAX_TURNS = 15
SCIENTIST_MAX_BUDGET = 0.25
SCIENTIST_TOOLS = "Read,Edit,Write"

# Supervisor
SUPERVISOR_MAX_BUDGET = 2.0
SUPERVISOR_TOOLS = "Read,Edit,Write"
SUPERVISOR_PRE_PROMPT = "Read and follow supervisor/method.md — PRE-STUDY phase only."
SUPERVISOR_POST_PROMPT = "Read and follow supervisor/method.md — POST-STUDY phase only."

# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------


@dataclasses.dataclass
class TrialResult:
    problem: str
    trial: int
    status: str  # "done" | "failed"
    elapsed: float


# ---------------------------------------------------------------------------
# Process-group tracking (shared by supervisor & scientist calls)
# ---------------------------------------------------------------------------

_child_pgids: set[int] = set()
_child_pgids_lock = threading.Lock()


def _sigint_handler(*_):
    """Kill all active child process groups, then exit."""
    with _child_pgids_lock:
        for pgid in _child_pgids:
            try:
                os.killpg(pgid, signal.SIGTERM)
            except OSError:
                pass
    sys.exit(130)


signal.signal(signal.SIGINT, _sigint_handler)

# ---------------------------------------------------------------------------
# CLI helpers
# ---------------------------------------------------------------------------


def build_cmd(model, *, allowed_tools=None, max_budget_usd=None, max_turns=None):
    """Build a Claude CLI command list."""
    cmd = [
        "claude", "-p", "--verbose",
        "--model", model,
        "--output-format", "stream-json",
        "--disallowedTools", "TodoWrite",
    ]
    if allowed_tools:
        cmd += ["--allowedTools", allowed_tools]
    if max_budget_usd is not None:
        cmd += ["--max-budget-usd", str(max_budget_usd)]
    if max_turns is not None:
        cmd += ["--max-turns", str(max_turns)]
    return cmd


def _run_cli(cmd, *, prompt, log_path, timeout=None):
    """Run a CLI subprocess with pgid tracking.

    Returns (returncode, timed_out).
    """
    with open(log_path, "w") as f:
        proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=f,
            stderr=sys.stderr,
            text=True,
            start_new_session=True,
        )
    with _child_pgids_lock:
        _child_pgids.add(proc.pid)
    timed_out = False
    try:
        proc.communicate(input=prompt, timeout=timeout)
    except subprocess.TimeoutExpired:
        timed_out = True
        os.killpg(proc.pid, signal.SIGTERM)
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid, signal.SIGKILL)
            proc.wait()
    finally:
        with _child_pgids_lock:
            _child_pgids.discard(proc.pid)
    return proc.returncode, timed_out


# ---------------------------------------------------------------------------
# Study: scientist trials across all problems
# ---------------------------------------------------------------------------


def run_trial(problem, trial_num, *, log_dir, model=SCIENTIST_MODEL,
              max_turns=SCIENTIST_MAX_TURNS, max_budget_usd=SCIENTIST_MAX_BUDGET):
    """Run a single Scientist trial for a problem. Returns a TrialResult."""
    problem_dir = SCIENTIST_DIR / problem
    archive_dir = problem_dir / "archive"

    # Archive train.py before Scientist modifies it
    train_path = problem_dir / "train.py"
    if train_path.exists():
        shutil.copy(train_path, archive_dir / f"trial-{trial_num:03d}.py")

    prompt = f"Read and follow scientist/{problem}/program.md"
    cmd = build_cmd(model, allowed_tools=SCIENTIST_TOOLS,
                    max_budget_usd=max_budget_usd, max_turns=max_turns)
    log_file = log_dir / f"{problem}-trial-{trial_num:03d}.jsonl"

    start = time.monotonic()
    returncode, _ = _run_cli(cmd, prompt=prompt, log_path=log_file)

    # Post phase: harness evaluates train.py (Scientists cannot call prepare.py)
    eval_result = subprocess.run(
        ["uv", "run", "python3", "-m", f"scientist.{problem}.prepare"],
        capture_output=True, text=True, timeout=120,
    )
    if eval_result.stdout:
        print(eval_result.stdout, end="", file=sys.stderr)

    elapsed = time.monotonic() - start
    status = "done" if returncode == 0 and eval_result.returncode == 0 else "failed"
    return TrialResult(problem, trial_num, status, elapsed)


def _curate_archive(problem_dir):
    """Maintain archive/best.py — copy the best trial's code."""
    rows = load_results(problem_dir / "results.tsv")
    if not rows:
        return
    best_idx = max(range(len(rows)), key=lambda i: rows[i]["avg_improvement"])
    best_file = problem_dir / "archive" / f"trial-{best_idx + 1:03d}.py"
    if best_file.exists():
        shutil.copy(best_file, problem_dir / "archive" / "best.py")


def _run_problem_trials(problem, num_trials, *, log_dir, model, max_turns, max_budget_usd):
    """Run all trials for a single problem sequentially."""
    study_start = time.monotonic()
    label = problem[:16].ljust(16)

    for i in range(1, num_trials + 1):
        result = run_trial(problem, i, log_dir=log_dir, model=model,
                           max_turns=max_turns, max_budget_usd=max_budget_usd)
        total = time.monotonic() - study_start

        # Read metric from results.tsv for richer output
        metric_str = ""
        if result.status == "done":
            try:
                rows = load_results(SCIENTIST_DIR / problem / "results.tsv")
                if rows:
                    current = rows[-1]["avg_improvement"]
                    running_best = max(r["avg_improvement"] for r in rows)
                    is_new_best = current >= running_best
                    best_marker = " ★" if is_new_best else ""
                    metric_str = f"  avg={current:+.4f}{best_marker}"
                    if len(rows) >= 2:
                        delta = current - rows[-2]["avg_improvement"]
                        metric_str += f" ({delta:+.4f})"
            except Exception:
                pass

        print(
            f"  {label} trial {result.trial:>2}/{num_trials}: {result.status:<7}{metric_str}"
            f"  ({result.elapsed:.1f}s) [total: {total:.1f}s]",
            file=sys.stderr,
        )

        try:
            _curate_archive(SCIENTIST_DIR / problem)
        except Exception:
            pass


def run_study(*, num_trials=SCIENTIST_TRIALS, max_turns=SCIENTIST_MAX_TURNS,
              model=SCIENTIST_MODEL, sequential=True, max_budget_usd=SCIENTIST_MAX_BUDGET):
    """Run a study: all trials across all problems. Returns the log directory."""
    problems = discover_problems()
    if not problems:
        raise RuntimeError("No problems found in scientist/. Each problem needs a program.md.")

    print(f"Problems: {', '.join(problems)}", file=sys.stderr)
    soft_reset(problems, verbose=False)

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    log_dir = Path("logs") / timestamp
    log_dir.mkdir(parents=True, exist_ok=True)

    max_workers = 1 if sequential else len(problems)
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {
            pool.submit(
                _run_problem_trials, problem, num_trials,
                log_dir=log_dir, model=model, max_turns=max_turns,
                max_budget_usd=max_budget_usd,
            ): problem
            for problem in problems
        }
        for future in as_completed(futures):
            future.result()  # propagate exceptions

    return log_dir


# ---------------------------------------------------------------------------
# Experiment: one or more supervisor studies
# ---------------------------------------------------------------------------


def run_supervisor(prompt, *, model, log_file, timeout, max_budget_usd=SUPERVISOR_MAX_BUDGET):
    """Run a Supervisor CLI call. Returns True on success."""
    cmd = build_cmd(model, allowed_tools=SUPERVISOR_TOOLS, max_budget_usd=max_budget_usd)
    returncode, timed_out = _run_cli(cmd, prompt=prompt, log_path=log_file, timeout=timeout)

    if timed_out:
        print(f"  Supervisor call timed out after {timeout}s", file=sys.stderr)
        return False
    if returncode != 0:
        print(f"  Supervisor call failed (exit code {returncode})", file=sys.stderr)
        return False
    return True


def run_experiment(*, num_studies=DEFAULT_STUDIES, study_timeout=DEFAULT_STUDY_TIMEOUT,
                   model=DEFAULT_MODEL, num_trials=None, sequential=True):
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
            print("  Phase 1: Pre-study planning", file=sys.stderr)
            if not run_supervisor(SUPERVISOR_PRE_PROMPT, model=model,
                                  log_file=log_dir / "pre-study.jsonl", timeout=study_timeout):
                print(f"  Pre-study supervisor failed, skipping study {i}", file=sys.stderr)
                continue

            # Phase 2: Run the study
            print("  Phase 2: Running trials", file=sys.stderr)
            study_kwargs = {"sequential": sequential, "max_budget_usd": SCIENTIST_MAX_BUDGET}
            if num_trials is not None:
                study_kwargs["num_trials"] = num_trials
            run_study(**study_kwargs)

            # Evaluate
            try:
                all_stats = analyse_and_save(timestamp=study_timestamp)
                if all_stats and "_aggregate" in all_stats:
                    agg = all_stats["_aggregate"]
                    print(f"  Aggregate: velocity={agg['improvement_velocity']:+.6f}/trial, "
                          f"best={agg['best_avg_improvement']:.4f} (trial {agg['best_trial']}), "
                          f"new_bests={agg['num_new_bests']}, "
                          f"tailing_off={agg['tailing_off']}", file=sys.stderr)
                    for problem in problems:
                        if problem in all_stats:
                            s = all_stats[problem]
                            print(f"    {problem}: velocity={s['improvement_velocity']:+.6f}, "
                                  f"best={s['best_avg_improvement']:.4f} (trial {s['best_trial']}), "
                                  f"new_bests={s['num_new_bests']}, "
                                  f"plateau={s['plateau_trial']}", file=sys.stderr)
                else:
                    print("  Study result: too few trials to analyse", file=sys.stderr)
            except Exception as e:
                print(f"  Warning: study evaluation failed: {e}", file=sys.stderr)

            # Phase 3: Post-study Supervisor call
            print("  Phase 3: Post-study review", file=sys.stderr)
            if not run_supervisor(SUPERVISOR_POST_PROMPT, model=model,
                                  log_file=log_dir / "post-study.jsonl", timeout=study_timeout):
                print("  Warning: post-study supervisor failed (study results are saved)", file=sys.stderr)

        except Exception as e:
            print(f"  Study {i} failed with unexpected error: {e}", file=sys.stderr)
            continue


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(description="Run an experiment: one or more Supervisor studies.")
    parser.add_argument("--studies", type=int, default=DEFAULT_STUDIES,
                        help=f"Number of studies (default: {DEFAULT_STUDIES})")
    parser.add_argument("--timeout", type=int, default=DEFAULT_STUDY_TIMEOUT,
                        help=f"Per-study timeout in seconds (default: {DEFAULT_STUDY_TIMEOUT})")
    parser.add_argument("--model", type=str, default=DEFAULT_MODEL,
                        help=f"Model for Supervisor (default: {DEFAULT_MODEL})")
    parser.add_argument("--trials", type=int, default=None,
                        help="Number of trials per study (default: study default)")
    parser.add_argument("--sequential", action="store_true", default=True,
                        help="Run problems sequentially (default, avoids rate limits)")
    parser.add_argument("--parallel", action="store_true",
                        help="Run problems in parallel")
    args = parser.parse_args()

    run_experiment(
        num_studies=args.studies,
        study_timeout=args.timeout,
        model=args.model,
        num_trials=args.trials,
        sequential=not args.parallel,
    )


if __name__ == "__main__":
    main()
