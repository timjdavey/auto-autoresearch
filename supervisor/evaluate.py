"""
evaluate.py — Analyse Scientist progress after a study completes.
Reads the stable log at scientist/{problem}/results.tsv (written by prepare.py)
for each discovered problem.

Usage:
    python evaluate.py
"""

import csv
import os
import sys
from datetime import datetime
from pathlib import Path

SCIENTIST_DIR = Path(__file__).parent.parent / "scientist"


def discover_problems():
    """Auto-discover problem directories under scientist/."""
    return sorted(
        d.name for d in SCIENTIST_DIR.iterdir()
        if d.is_dir() and (d / "program.md").exists()
    )


def load_results(results_path=None):
    """Load all rows from a results.tsv, returning list of dicts with floats."""
    if results_path is None:
        # Legacy fallback — shouldn't be needed
        results_path = SCIENTIST_DIR / "results.tsv"
    if not os.path.exists(results_path):
        return []
    with open(results_path, newline="") as f:
        rows = []
        for row in csv.DictReader(f, delimiter="\t"):
            rows.append({
                "timestamp": row["timestamp"],
                "avg_improvement": float(row["avg_improvement"]),
                "training_time": float(row["training_time"]),
            })
    return rows


def analyse(rows):
    """Compute study metrics. Returns dict with analysis results."""
    n = len(rows)
    first = rows[0]["avg_improvement"]
    last = rows[-1]["avg_improvement"]
    total_improvement = last - first
    improvement_per_trial = total_improvement / n if n > 0 else 0.0

    # Final 20% velocity
    tail_start = max(1, n - max(1, n // 5))  # at least 1 trial in tail
    tail = rows[tail_start:]
    tail_improvement = tail[-1]["avg_improvement"] - tail[0]["avg_improvement"]
    tail_trials = len(tail)
    tail_velocity = tail_improvement / tail_trials if tail_trials > 0 else 0.0

    # Overall velocity (excluding first trial which has no delta)
    overall_velocity = improvement_per_trial

    return {
        "num_trials": n,
        "first_avg_improvement": first,
        "last_avg_improvement": last,
        "total_improvement": total_improvement,
        "improvement_per_trial": improvement_per_trial,
        "tail_trials": tail_trials,
        "tail_velocity": tail_velocity,
        "overall_velocity": overall_velocity,
        "tailing_off": tail_velocity < overall_velocity * 0.5 if n >= 5 else None,
    }


def print_report(stats, problem=None):
    """Print a human-readable summary."""
    prefix = f"[{problem}] " if problem else ""
    print(f"{prefix}Trials: {stats['num_trials']}")
    print(f"{prefix}First avg_improvement: {stats['first_avg_improvement']:.6f}")
    print(f"{prefix}Last  avg_improvement: {stats['last_avg_improvement']:.6f}")
    print()
    print(f"{prefix}Total improvement:       {stats['total_improvement']:+.6f}")
    print(f"{prefix}Improvement per trial:   {stats['improvement_per_trial']:+.6f}")
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
    "total_improvement", "improvement_per_trial",
    "tail_trials", "tail_velocity", "overall_velocity", "tailing_off",
]

STUDY_RESULTS_PATH = os.path.join(os.path.dirname(__file__), "study_results.csv")


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
        "total_improvement", "improvement_per_trial",
        "tail_trials", "tail_velocity", "overall_velocity",
    ]
    n_problems = len(all_stats)
    aggregate = {}
    for key in agg_keys:
        aggregate[key] = sum(s[key] for s in all_stats.values()) / n_problems
    # Round num_trials and tail_trials for aggregate
    aggregate["num_trials"] = round(aggregate["num_trials"])
    aggregate["tail_trials"] = round(aggregate["tail_trials"])
    # Tailing off: True if any problem is tailing off
    tailing_values = [s["tailing_off"] for s in all_stats.values() if s["tailing_off"] is not None]
    aggregate["tailing_off"] = any(tailing_values) if tailing_values else None
    all_stats["_aggregate"] = aggregate

    # Write to CSV
    write_header = not os.path.exists(output_path)
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


if __name__ == "__main__":
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
