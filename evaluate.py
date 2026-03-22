"""
evaluate.py — Analyse Scientist progress after a study completes.
Reads the stable log at lab/results.tsv (written by prepare.py).

Usage:
    python evaluate.py
"""

import csv
import os
import sys
from datetime import datetime

RESULTS_LOG_PATH = os.path.join(os.path.dirname(__file__), "lab", "results.tsv")


def load_results():
    """Load all rows from results.tsv, returning list of dicts with floats."""
    if not os.path.exists(RESULTS_LOG_PATH):
        return []
    with open(RESULTS_LOG_PATH, newline="") as f:
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


def print_report(stats):
    """Print a human-readable summary."""
    print(f"Trials: {stats['num_trials']}")
    print(f"First avg_improvement: {stats['first_avg_improvement']:.6f}")
    print(f"Last  avg_improvement: {stats['last_avg_improvement']:.6f}")
    print()
    print(f"Total improvement:       {stats['total_improvement']:+.6f}")
    print(f"Improvement per trial:   {stats['improvement_per_trial']:+.6f}")
    print()
    print(f"Final 20% ({stats['tail_trials']} trials):")
    print(f"  Velocity: {stats['tail_velocity']:+.6f} per trial")
    print(f"  Overall:  {stats['overall_velocity']:+.6f} per trial")
    if stats["tailing_off"] is None:
        print(f"  Tailing off: too few trials to judge")
    elif stats["tailing_off"]:
        print(f"  Tailing off: YES (final velocity < 50% of overall)")
    else:
        print(f"  Tailing off: no")


STUDY_FIELDS = [
    "timestamp", "num_trials",
    "first_avg_improvement", "last_avg_improvement",
    "total_improvement", "improvement_per_trial",
    "tail_trials", "tail_velocity", "overall_velocity", "tailing_off",
]

STUDY_RESULTS_PATH = os.path.join(os.path.dirname(__file__), "study_results.csv")


def analyse_and_save(timestamp=None, output_path=None):
    """Analyse current study results and append summary to persistent CSV."""
    if timestamp is None:
        timestamp = datetime.now().isoformat(timespec="seconds")
    if output_path is None:
        output_path = STUDY_RESULTS_PATH
    rows = load_results()
    if len(rows) < 2:
        return None
    stats = analyse(rows)
    write_header = not os.path.exists(output_path)
    with open(output_path, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=STUDY_FIELDS)
        if write_header:
            writer.writeheader()
        writer.writerow({
            "timestamp": timestamp,
            **{k: stats[k] for k in STUDY_FIELDS[1:]},
        })
    return stats


if __name__ == "__main__":
    rows = load_results()
    if not rows:
        print("No results found. Run a study first.")
        sys.exit(1)
    if len(rows) < 2:
        print("Only 1 trial recorded. Need at least 2 for analysis.")
        print(f"  avg_improvement: {rows[0]['avg_improvement']:.6f}")
        sys.exit(0)
    stats = analyse(rows)
    print_report(stats)
