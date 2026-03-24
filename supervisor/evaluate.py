"""
evaluate.py — Analyse Scientist progress after a study completes.
Reads the stable log at scientist/{problem}/results.tsv (written by prepare.py)
for each discovered problem.

Usage:
    uv run evaluate
"""

import csv
import math
import statistics
import sys
from datetime import datetime
from pathlib import Path

from scientist import SCIENTIST_DIR, discover_problems

# Crash penalties are -10.0 (set in each problem's prepare.py).
# Anything at or below this threshold is treated as a crash, not a real result.
CRASH_THRESHOLD = -1


def load_results(results_path=None):
    """Load rows from a results.tsv, returning list of dicts with floats.

    Rows with status='scientist_timeout' are skipped (no valid metric).
    Rows where avg_improvement cannot be parsed as float are also skipped.
    """
    if results_path is None:
        # Legacy fallback — shouldn't be needed
        results_path = SCIENTIST_DIR / "results.tsv"
    if not Path(results_path).exists():
        return []
    with open(results_path, newline="") as f:
        rows = []
        for row in csv.DictReader(f, delimiter="\t"):
            # Skip scientist timeout rows — no valid metric
            if row.get("status") == "scientist_timeout":
                continue
            try:
                avg_improvement = float(row["avg_improvement"])
            except (ValueError, TypeError):
                continue  # skip unparseable rows (e.g. legacy "TIMEOUT after 600s")
            rows.append({
                "timestamp": row["timestamp"],
                "avg_improvement": avg_improvement,
                "training_time": float(row.get("training_time", 0)),
            })
    return rows


def analyse(rows):
    """Compute study metrics. Returns dict with analysis results, or None if < 2 rows."""
    n = len(rows)
    if n < 2:
        return None

    improvements = [r["avg_improvement"] for r in rows]
    first = improvements[0]
    last = improvements[-1]
    total_improvement = last - first
    improvement_per_trial = total_improvement / n

    # Best / worst (exclude crash penalties)
    valid_improvements = [v for v in improvements if v > CRASH_THRESHOLD]
    best_avg_improvement = max(valid_improvements) if valid_improvements else max(improvements)
    worst_avg_improvement = min(valid_improvements) if valid_improvements else min(improvements)
    best_trial = improvements.index(best_avg_improvement) + 1  # 1-indexed

    # Standard deviation
    if n >= 2 and valid_improvements:
        mean_val = sum(valid_improvements) / len(valid_improvements)
        variance = sum((v - mean_val) ** 2 for v in valid_improvements) / (len(valid_improvements) - 1)
        stdev_avg_improvement = math.sqrt(variance)
    else:
        stdev_avg_improvement = 0.0

    # Median (robust to crash outliers)
    median_avg_improvement = statistics.median(valid_improvements) if valid_improvements else statistics.median(improvements)

    # Error count and rate
    num_errors = sum(1 for v in improvements if v <= CRASH_THRESHOLD)
    error_rate = num_errors / n

    # Progress consistency: new bests, plateaus, regressions
    running_best = improvements[0]
    num_new_bests = 1  # first trial is trivially a new best
    current_plateau = 0
    longest_plateau = 0
    num_regressions = 0
    for v in improvements[1:]:
        if v > CRASH_THRESHOLD and v > running_best:
            running_best = v
            num_new_bests += 1
            current_plateau = 0
        else:
            current_plateau += 1
            longest_plateau = max(longest_plateau, current_plateau)
        # Regression: non-crash trial drops >10% below running best
        if v > CRASH_THRESHOLD and v < running_best * 0.9:
            num_regressions += 1

    # Training time
    training_times = [r["training_time"] for r in rows]
    avg_training_time = sum(training_times) / n

    # Final 20% velocity
    tail_start = max(1, n - max(1, n // 5))  # at least 1 trial in tail
    tail = rows[tail_start:]
    tail_improvement = tail[-1]["avg_improvement"] - tail[0]["avg_improvement"]
    tail_trials = len(tail)
    tail_velocity = tail_improvement / tail_trials if tail_trials > 0 else 0.0

    # Overall velocity
    overall_velocity = improvement_per_trial

    return {
        "num_trials": n,
        "first_avg_improvement": first,
        "last_avg_improvement": last,
        "best_avg_improvement": best_avg_improvement,
        "worst_avg_improvement": worst_avg_improvement,
        "stdev_avg_improvement": stdev_avg_improvement,
        "median_avg_improvement": median_avg_improvement,
        "best_trial": best_trial,
        "num_errors": num_errors,
        "error_rate": error_rate,
        "num_new_bests": num_new_bests,
        "longest_plateau": longest_plateau,
        "num_regressions": num_regressions,
        "total_improvement": total_improvement,
        "improvement_per_trial": improvement_per_trial,
        "avg_training_time": avg_training_time,
        "tail_trials": tail_trials,
        "tail_velocity": tail_velocity,
        "overall_velocity": overall_velocity,
        "tailing_off": tail_velocity < overall_velocity * 0.5 if n >= 5 else None,
    }


def print_report(stats, problem=None):
    """Print a human-readable summary."""
    prefix = f"[{problem}] " if problem else ""
    print(f"{prefix}Trials: {stats['num_trials']}  (errors: {stats['num_errors']}, rate: {stats['error_rate']:.0%})")
    print(f"{prefix}First avg_improvement:  {stats['first_avg_improvement']:.6f}")
    print(f"{prefix}Last  avg_improvement:  {stats['last_avg_improvement']:.6f}")
    print(f"{prefix}Best  avg_improvement:  {stats['best_avg_improvement']:.6f}  (trial {stats['best_trial']})")
    print(f"{prefix}Worst avg_improvement:  {stats['worst_avg_improvement']:.6f}")
    print(f"{prefix}Median avg_improvement: {stats['median_avg_improvement']:.6f}")
    print(f"{prefix}Stdev avg_improvement:  {stats['stdev_avg_improvement']:.6f}")
    print()
    print(f"{prefix}Total improvement:       {stats['total_improvement']:+.6f}")
    print(f"{prefix}Improvement per trial:   {stats['improvement_per_trial']:+.6f}")
    print(f"{prefix}Avg training time:       {stats['avg_training_time']:.1f}s")
    print()
    print(f"{prefix}Progress: {stats['num_new_bests']} new bests, "
          f"longest plateau: {stats['longest_plateau']}, "
          f"regressions: {stats['num_regressions']}")
    print()
    print(f"{prefix}Final 20% ({stats['tail_trials']} trials):")
    print(f"{prefix}  Velocity: {stats['tail_velocity']:+.6f} per trial")
    print(f"{prefix}  Overall:  {stats['overall_velocity']:+.6f} per trial")
    if stats["tailing_off"] is None:
        print(f"{prefix}  Tailing off: too few trials to judge")
    elif stats["tailing_off"]:
        print(f"{prefix}  Tailing off: YES (final velocity < 50% of overall)")
    else:
        print(f"{prefix}  Tailing off: no")


STUDY_FIELDS = [
    "timestamp", "problem", "num_trials",
    "first_avg_improvement", "last_avg_improvement",
    "best_avg_improvement", "worst_avg_improvement",
    "stdev_avg_improvement", "median_avg_improvement",
    "best_trial", "num_errors", "error_rate",
    "num_new_bests", "longest_plateau", "num_regressions",
    "total_improvement", "improvement_per_trial",
    "avg_training_time",
    "tail_trials", "tail_velocity", "overall_velocity", "tailing_off",
]

STUDY_RESULTS_PATH = Path(__file__).parent / "study_results.csv"


def analyse_and_save(timestamp=None, output_path=None):
    """Analyse current study results for all problems and append summary to persistent CSV.

    Writes one row per problem plus an _aggregate row.
    Returns dict mapping problem name -> stats (plus '_aggregate' key).
    """
    if timestamp is None:
        timestamp = datetime.now().isoformat(timespec="seconds")
    if output_path is None:
        output_path = STUDY_RESULTS_PATH

    problems = discover_problems()
    all_stats = {}

    for problem in problems:
        results_path = SCIENTIST_DIR / problem / "results.tsv"
        rows = load_results(results_path)
        if len(rows) < 2:
            continue
        all_stats[problem] = analyse(rows)

    if not all_stats:
        return None

    # Compute aggregate (mean across problems)
    agg_keys = [
        "num_trials", "first_avg_improvement", "last_avg_improvement",
        "best_avg_improvement", "worst_avg_improvement",
        "stdev_avg_improvement", "median_avg_improvement",
        "best_trial", "num_errors", "error_rate",
        "num_new_bests", "longest_plateau", "num_regressions",
        "total_improvement", "improvement_per_trial",
        "avg_training_time",
        "tail_trials", "tail_velocity", "overall_velocity",
    ]
    n_problems = len(all_stats)
    aggregate = {}
    for key in agg_keys:
        aggregate[key] = sum(s[key] for s in all_stats.values()) / n_problems
    # Round integer fields for aggregate
    for key in ("num_trials", "tail_trials", "best_trial", "num_errors",
                "num_new_bests", "longest_plateau", "num_regressions"):
        aggregate[key] = round(aggregate[key])
    # Tailing off: True if any problem is tailing off
    tailing_values = [s["tailing_off"] for s in all_stats.values() if s["tailing_off"] is not None]
    aggregate["tailing_off"] = any(tailing_values) if tailing_values else None
    all_stats["_aggregate"] = aggregate

    # Write to CSV
    write_header = not Path(output_path).exists()
    with open(output_path, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=STUDY_FIELDS)
        if write_header:
            writer.writeheader()
        for problem_name, stats in all_stats.items():
            writer.writerow({
                "timestamp": timestamp,
                "problem": problem_name,
                **{k: stats[k] for k in STUDY_FIELDS[2:]},
            })

    return all_stats


def main():
    problems = discover_problems()
    if not problems:
        print("No problems found in scientist/.")
        sys.exit(1)

    any_results = False
    for problem in problems:
        results_path = SCIENTIST_DIR / problem / "results.tsv"
        rows = load_results(results_path)
        if not rows:
            print(f"[{problem}] No results found.")
            continue
        if len(rows) < 2:
            print(f"[{problem}] Only 1 trial recorded. Need at least 2 for analysis.")
            print(f"  avg_improvement: {rows[0]['avg_improvement']:.6f}")
            continue
        any_results = True
        stats = analyse(rows)
        print_report(stats, problem=problem)
        print()

    if not any_results:
        print("No problems had enough results for analysis.")
        sys.exit(1)


if __name__ == "__main__":
    main()
