"""
evaluate.py — Analyse Scientist progress after a study completes.

Source of truth: results.tsv files in archive/{timestamp}/{problem}/ and
current scientist/{problem}/ directories.

Writes supervisor/study_summary.md (overwritten each call) with all
historical + current study metrics for the Supervisor to read.

Usage:
    uv run evaluate
"""

import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

from scientist import SCIENTIST_DIR, discover_problems

# Legacy: crash penalties were -10.0 (now removed from prepare.py).
# Anything at or below this threshold is treated as a crash in legacy data.
CRASH_THRESHOLD = -1

ARCHIVE_DIR = Path("archive")
SUMMARY_PATH = Path(__file__).parent / "study_summary.md"


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------

def load_results(results_path):
    """Load rows from a single results.tsv into a DataFrame.

    Rows with status='scientist_timeout' or unparseable avg_improvement are dropped.
    Returns DataFrame with columns: timestamp, avg_improvement, success_rate, training_time.
    """
    results_path = Path(results_path)
    if not results_path.exists():
        return pd.DataFrame(columns=["timestamp", "avg_improvement", "success_rate", "training_time"])

    df = pd.read_csv(results_path, sep="\t", on_bad_lines="skip")

    # Drop scientist timeout rows
    if "status" in df.columns:
        df = df[df["status"] != "scientist_timeout"]

    # Parse avg_improvement, drop unparseable
    df["avg_improvement"] = pd.to_numeric(df["avg_improvement"], errors="coerce")
    df = df.dropna(subset=["avg_improvement"])

    # Parse success_rate with fallback
    if "success_rate" in df.columns:
        df["success_rate"] = pd.to_numeric(df["success_rate"], errors="coerce").fillna(1.0)
    else:
        df["success_rate"] = 1.0

    # Parse training_time with fallback
    if "training_time" in df.columns:
        df["training_time"] = pd.to_numeric(df["training_time"], errors="coerce").fillna(0.0)
    else:
        df["training_time"] = 0.0

    return df[["timestamp", "avg_improvement", "success_rate", "training_time"]].reset_index(drop=True)


def load_archive(archive_dir=None):
    """Load all results.tsv from archive/{timestamp}/{problem}/.

    Returns DataFrame with extra columns: study (timestamp str), problem.
    Sorted by study then problem.
    """
    if archive_dir is None:
        archive_dir = ARCHIVE_DIR
    archive_dir = Path(archive_dir)

    if not archive_dir.exists():
        return pd.DataFrame()

    frames = []
    for study_dir in sorted(archive_dir.iterdir()):
        if not study_dir.is_dir():
            continue
        study_name = study_dir.name
        for problem_dir in sorted(study_dir.iterdir()):
            if not problem_dir.is_dir():
                continue
            results_path = problem_dir / "results.tsv"
            if not results_path.exists():
                continue
            df = load_results(results_path)
            if df.empty:
                continue
            df["study"] = study_name
            df["problem"] = problem_dir.name
            frames.append(df)

    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


def load_current():
    """Load results.tsv from current scientist/{problem}/ directories.

    Returns DataFrame with columns: problem, timestamp, avg_improvement, success_rate, training_time.
    """
    problems = discover_problems()
    frames = []
    for problem in problems:
        results_path = SCIENTIST_DIR / problem / "results.tsv"
        df = load_results(results_path)
        if df.empty:
            continue
        df["problem"] = problem
        frames.append(df)
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


# ---------------------------------------------------------------------------
# Analysis
# ---------------------------------------------------------------------------

def analyse(rows):
    """Compute study metrics from a list of row dicts (or DataFrame rows).

    Returns dict with analysis results, or None if < 2 rows.
    Accepts list of dicts with keys: avg_improvement, success_rate, training_time.
    """
    if isinstance(rows, pd.DataFrame):
        rows = rows.to_dict("records")

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
        s = pd.Series(valid_improvements)
        stdev_avg_improvement = float(s.std(ddof=1))
    else:
        stdev_avg_improvement = 0.0

    # Median (robust to crash outliers)
    median_avg_improvement = float(pd.Series(valid_improvements or improvements).median())

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

    # Success rate stats
    success_rates = [r["success_rate"] for r in rows]
    avg_success_rate = sum(success_rates) / n
    first_success_rate = success_rates[0]
    last_success_rate = success_rates[-1]

    # Plateau detection: first trial where running best doesn't improve for 3+ consecutive
    plateau_trial = None
    running_best_for_plateau = improvements[0]
    stale_count = 0
    for i, v in enumerate(improvements[1:], start=2):  # 1-indexed trial number
        if v > CRASH_THRESHOLD and v > running_best_for_plateau:
            running_best_for_plateau = v
            stale_count = 0
        else:
            stale_count += 1
            if stale_count >= 3 and plateau_trial is None:
                plateau_trial = i - 2  # trial where plateau started

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

    # Improvement velocity (best - first) / num_trials
    improvement_velocity = (best_avg_improvement - first) / n if n > 0 else 0.0

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
        "avg_success_rate": avg_success_rate,
        "first_success_rate": first_success_rate,
        "last_success_rate": last_success_rate,
        "num_new_bests": num_new_bests,
        "longest_plateau": longest_plateau,
        "plateau_trial": plateau_trial,
        "num_regressions": num_regressions,
        "total_improvement": total_improvement,
        "improvement_per_trial": improvement_per_trial,
        "improvement_velocity": improvement_velocity,
        "avg_training_time": avg_training_time,
        "tail_trials": tail_trials,
        "tail_velocity": tail_velocity,
        "overall_velocity": overall_velocity,
        "tailing_off": tail_velocity < overall_velocity * 0.5 if n >= 5 else None,
    }


def _compute_aggregate(all_stats):
    """Compute aggregate stats (mean across problems) + ensemble metrics."""
    import statistics as stats_mod

    agg_keys = [
        "num_trials", "first_avg_improvement", "last_avg_improvement",
        "best_avg_improvement", "worst_avg_improvement",
        "stdev_avg_improvement", "median_avg_improvement",
        "best_trial", "num_errors", "error_rate",
        "avg_success_rate", "first_success_rate", "last_success_rate",
        "num_new_bests", "longest_plateau", "num_regressions",
        "total_improvement", "improvement_per_trial", "improvement_velocity",
        "avg_training_time",
        "tail_trials", "tail_velocity", "overall_velocity",
    ]
    n_problems = len(all_stats)
    aggregate = {}
    for key in agg_keys:
        aggregate[key] = sum(s[key] for s in all_stats.values()) / n_problems
    # Round integer fields
    for key in ("num_trials", "tail_trials", "best_trial", "num_errors",
                "num_new_bests", "longest_plateau", "num_regressions"):
        aggregate[key] = round(aggregate[key])
    # Tailing off: True if any problem is tailing off
    tailing_values = [s["tailing_off"] for s in all_stats.values() if s["tailing_off"] is not None]
    aggregate["tailing_off"] = any(tailing_values) if tailing_values else None
    # Plateau trial: median across problems
    plateau_values = [s["plateau_trial"] for s in all_stats.values() if s["plateau_trial"] is not None]
    aggregate["plateau_trial"] = round(stats_mod.median(plateau_values)) if plateau_values else None

    # Headroom-based ensemble metrics
    headroom_captured = []
    problems_improved = 0
    worst_delta = float("inf")
    for stats in all_stats.values():
        old_best = stats["first_avg_improvement"]
        new_best = stats["best_avg_improvement"]
        delta = new_best - old_best
        if delta > 0:
            problems_improved += 1
        worst_delta = min(worst_delta, delta)
        headroom = 1.0 - old_best
        if headroom > 0.001:
            headroom_captured.append(delta / headroom)
    aggregate["mean_headroom_captured"] = (
        sum(headroom_captured) / len(headroom_captured) if headroom_captured else 0.0
    )
    aggregate["problems_improved"] = problems_improved
    aggregate["worst_problem_delta"] = worst_delta if worst_delta != float("inf") else 0.0

    return aggregate


# ---------------------------------------------------------------------------
# Summary writing
# ---------------------------------------------------------------------------

def _fmt(val, fmt=".4f"):
    """Format a numeric value, handling None."""
    if val is None:
        return "—"
    if isinstance(val, bool):
        return "yes" if val else "no"
    if isinstance(val, int):
        return str(val)
    try:
        return f"{val:{fmt}}"
    except (ValueError, TypeError):
        return str(val)


def write_summary(output_path=None, archive_dir=None):
    """Build study_summary.md from archive + current results. Overwrites each call.

    Returns dict mapping study_timestamp -> {problem -> stats, '_aggregate' -> stats}.
    """
    if output_path is None:
        output_path = SUMMARY_PATH

    # Load archive data
    archive_df = load_archive(archive_dir)

    # Load current scientist/ data (may be empty between studies)
    current_df = load_current()

    # Build per-study, per-problem stats
    # Each archive study is identified by its timestamp directory name
    all_studies = {}  # study_name -> {problem -> stats}

    if not archive_df.empty:
        for study_name, study_group in archive_df.groupby("study", sort=True):
            study_stats = {}
            for problem, problem_group in study_group.groupby("problem", sort=True):
                stats = analyse(problem_group)
                if stats is not None:
                    study_stats[problem] = stats
            if study_stats:
                study_stats["_aggregate"] = _compute_aggregate(study_stats)
                all_studies[study_name] = study_stats

    # Add current study if there's data
    if not current_df.empty:
        current_stats = {}
        for problem, problem_group in current_df.groupby("problem", sort=True):
            stats = analyse(problem_group)
            if stats is not None:
                current_stats[problem] = stats
        if current_stats:
            current_stats["_aggregate"] = _compute_aggregate(current_stats)
            all_studies["_current"] = current_stats

    # Write markdown summary
    lines = ["# Study Summary\n"]
    lines.append("Auto-generated from archive results.tsv files. Do not edit.\n\n")

    if not all_studies:
        lines.append("No study data found.\n")
        Path(output_path).write_text("".join(lines))
        return all_studies

    # Collect all problems across all studies
    all_problems = sorted({
        p for study_stats in all_studies.values()
        for p in study_stats if p != "_aggregate"
    })

    # Key metrics table — one row per study, columns per problem
    key_metrics = ["best_avg_improvement", "improvement_velocity", "best_trial",
                   "num_new_bests", "plateau_trial", "tailing_off", "avg_success_rate"]

    for metric in key_metrics:
        lines.append(f"## {metric}\n\n")
        # Header
        header = "| study | " + " | ".join(all_problems) + " | _aggregate |"
        sep = "|---|" + "|".join("---" for _ in all_problems) + "|---|"
        lines.append(header + "\n")
        lines.append(sep + "\n")
        # Rows
        for study_name, study_stats in all_studies.items():
            label = study_name if study_name != "_current" else "**current**"
            cells = []
            for p in all_problems:
                val = study_stats.get(p, {}).get(metric, "—") if isinstance(study_stats.get(p), dict) else "—"
                cells.append(_fmt(val))
            agg_val = study_stats.get("_aggregate", {}).get(metric, "—")
            cells.append(_fmt(agg_val))
            lines.append(f"| {label} | " + " | ".join(cells) + " |\n")
        lines.append("\n")

    # Detailed per-study sections
    lines.append("## Detailed per-study breakdown\n\n")
    for study_name, study_stats in all_studies.items():
        label = study_name if study_name != "_current" else "**current**"
        lines.append(f"### {label}\n\n")

        # Metrics table for this study
        detail_metrics = [
            "num_trials", "best_avg_improvement", "last_avg_improvement", "first_avg_improvement",
            "improvement_velocity", "best_trial", "num_new_bests",
            "plateau_trial", "longest_plateau", "tail_velocity", "tailing_off",
            "avg_success_rate", "num_errors", "num_regressions",
            "avg_training_time",
        ]

        header = "| metric | " + " | ".join(
            p for p in list(all_problems) + ["_aggregate"]
        ) + " |"
        sep = "|---|" + "|".join("---" for _ in all_problems) + "|---|"
        lines.append(header + "\n")
        lines.append(sep + "\n")
        for metric in detail_metrics:
            cells = []
            for p in list(all_problems) + ["_aggregate"]:
                val = study_stats.get(p, {}).get(metric, "—") if isinstance(study_stats.get(p), dict) else "—"
                cells.append(_fmt(val))
            lines.append(f"| {metric} | " + " | ".join(cells) + " |\n")
        lines.append("\n")

    Path(output_path).write_text("".join(lines))
    return all_studies


# ---------------------------------------------------------------------------
# analyse_and_save — called by experiment.py after each study
# ---------------------------------------------------------------------------

def analyse_and_save(timestamp=None, output_path=None, archive_dir=None):
    """Analyse current study results, write study_summary.md, return stats.

    Returns dict mapping problem name -> stats (plus '_aggregate' key),
    or None if too few results.
    """
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

    all_stats["_aggregate"] = _compute_aggregate(all_stats)

    # Write full summary (archive + current)
    write_summary(output_path=output_path, archive_dir=archive_dir)

    return all_stats


# ---------------------------------------------------------------------------
# Printing
# ---------------------------------------------------------------------------

def print_report(stats, problem=None):
    """Print a human-readable summary."""
    prefix = f"[{problem}] " if problem else ""

    # VELOCITY (primary signal — how fast did the Scientist learn?)
    print(f"{prefix}=== Learning Speed ===")
    print(f"{prefix}Improvement velocity:    {stats['improvement_velocity']:+.6f}  (best - first) / trials")
    print(f"{prefix}Best found at trial:     {stats['best_trial']} / {stats['num_trials']}")
    print(f"{prefix}New bests discovered:    {stats['num_new_bests']}")
    plateau_str = str(stats['plateau_trial']) if stats['plateau_trial'] is not None else "none"
    print(f"{prefix}Plateau starts at trial: {plateau_str}  (longest: {stats['longest_plateau']})")
    print(f"{prefix}Tail velocity (last 20%): {stats['tail_velocity']:+.6f} per trial")
    if stats["tailing_off"] is None:
        print(f"{prefix}Tailing off:             too few trials to judge")
    elif stats["tailing_off"]:
        print(f"{prefix}Tailing off:             YES — Scientists ran out of ideas")
    else:
        print(f"{prefix}Tailing off:             no — still learning")
    print()

    # QUALITY (secondary — what ceiling was reached?)
    print(f"{prefix}=== Outcome Quality ===")
    print(f"{prefix}Best  avg_improvement:  {stats['best_avg_improvement']:.6f}")
    print(f"{prefix}Last  avg_improvement:  {stats['last_avg_improvement']:.6f}")
    print(f"{prefix}First avg_improvement:  {stats['first_avg_improvement']:.6f}")
    print(f"{prefix}Success rate: avg={stats['avg_success_rate']:.0%}  first={stats['first_success_rate']:.0%}  last={stats['last_success_rate']:.0%}")
    print()

    # DETAILS
    print(f"{prefix}Trials: {stats['num_trials']}  (errors: {stats['num_errors']}, regressions: {stats['num_regressions']})")
    print(f"{prefix}Median avg_improvement: {stats['median_avg_improvement']:.6f}")
    print(f"{prefix}Stdev avg_improvement:  {stats['stdev_avg_improvement']:.6f}")
    print(f"{prefix}Avg training time:       {stats['avg_training_time']:.1f}s")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    problems = discover_problems()
    if not problems:
        print("No problems found in scientist/.")
        sys.exit(1)

    any_results = False
    for problem in problems:
        results_path = SCIENTIST_DIR / problem / "results.tsv"
        rows = load_results(results_path)
        if rows.empty:
            print(f"[{problem}] No results found.")
            continue
        if len(rows) < 2:
            print(f"[{problem}] Only 1 trial recorded. Need at least 2 for analysis.")
            print(f"  avg_improvement: {rows.iloc[0]['avg_improvement']:.6f}")
            continue
        any_results = True
        stats = analyse(rows)
        print_report(stats, problem=problem)
        print()

    # Write summary file
    write_summary()

    if not any_results:
        print("No problems had enough results for analysis.")
        sys.exit(1)


if __name__ == "__main__":
    main()
