"""
prepare.py — Fixed evaluation harness for MAX-SAT autoresearch.
DO NOT MODIFY. The Scientist may only modify train.py.

Provides:

  evaluate(solve_fn) — training eval over 3 random 3-SAT instances.
    Metric: avg_improvement (higher is better).
    improvement = (baseline_unsat - solver_unsat) / baseline_unsat
    Baseline is greedy sequential assignment, computed once and cached.
"""

import csv
import json
import os
import random
import signal
import time
from datetime import datetime

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

TIME_BUDGET = 60  # seconds per solve attempt (wall clock)

# ---------------------------------------------------------------------------
# Random 3-SAT instance generation
# ---------------------------------------------------------------------------

def _generate_random_instance(n_vars: int, n_clauses: int, seed: int):
    """Generate a random 3-SAT instance with fixed seed.

    Returns (n_vars, clauses) where clauses is a list of 3-literal lists.
    Variables are 1-indexed; negative means negated.
    """
    rng = random.Random(seed)
    clauses = []
    for _ in range(n_clauses):
        vars_chosen = rng.sample(range(1, n_vars + 1), 3)
        clause = [v if rng.random() < 0.5 else -v for v in vars_chosen]
        clauses.append(clause)
    return n_vars, clauses


# ---------------------------------------------------------------------------
# Training instances (unknown optimal — no memorisation possible)
# ---------------------------------------------------------------------------

TRAIN_INSTANCES = {
    "rand200a": {"n_vars": (d := _generate_random_instance(200, 853, seed=421003))[0], "clauses": d[1], "optimal": None, "known": False},
    "rand250a": {"n_vars": (d := _generate_random_instance(250, 1067, seed=421004))[0], "clauses": d[1], "optimal": None, "known": False},
    "rand300a": {"n_vars": (d := _generate_random_instance(300, 1280, seed=421005))[0], "clauses": d[1], "optimal": None, "known": False},
}

# ---------------------------------------------------------------------------
# Greedy baseline
# ---------------------------------------------------------------------------

def _greedy_solve(n_vars, clauses):
    """Greedy sequential assignment. Used to compute baseline unsatisfied counts."""
    if n_vars == 0:
        return []
    assignment = [False] * n_vars
    for var_idx in range(n_vars):
        var = var_idx + 1
        count_true = 0
        count_false = 0
        for clause in clauses:
            if var not in clause and -var not in clause:
                continue
            already_sat = False
            for lit in clause:
                v = abs(lit) - 1
                if v < var_idx:
                    if (lit > 0 and assignment[v]) or (lit < 0 and not assignment[v]):
                        already_sat = True
                        break
            if already_sat:
                continue
            if var in clause:
                count_true += 1
            if -var in clause:
                count_false += 1
        assignment[var_idx] = count_true >= count_false
    return assignment


def count_unsatisfied(n_vars, clauses, assignment):
    """Return the number of clauses not satisfied by the assignment."""
    n_unsat = 0
    for clause in clauses:
        satisfied = False
        for lit in clause:
            var_idx = abs(lit) - 1
            val = assignment[var_idx]
            if (lit > 0 and val) or (lit < 0 and not val):
                satisfied = True
                break
        if not satisfied:
            n_unsat += 1
    return n_unsat


# Precomputed: number of unsatisfied clauses by greedy on each training instance.
# To recompute: run _greedy_solve on each instance and call count_unsatisfied.
GREEDY_BASELINES = {
    "rand200a": 29,
    "rand250a": 31,
    "rand300a": 48,
}

# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate_assignment(n_vars, assignment):
    """Return an error string if assignment is invalid, None if valid."""
    if not isinstance(assignment, list):
        return "assignment must be a list"
    if len(assignment) != n_vars:
        return f"assignment has {len(assignment)} entries, expected {n_vars}"
    for i, v in enumerate(assignment):
        if not isinstance(v, bool):
            return f"value at index {i} must be a bool, got {type(v).__name__}"
    return None

# ---------------------------------------------------------------------------
# Evaluation core
# ---------------------------------------------------------------------------

def _run_solver(solve_fn, n_vars, clauses):
    """Run solver with time budget. Returns (assignment, elapsed) or (error_str, elapsed)."""
    def _timeout_handler(signum, frame):
        raise TimeoutError("solver exceeded hard time budget")

    old_handler = signal.signal(signal.SIGALRM, _timeout_handler)
    signal.alarm(TIME_BUDGET + 5)
    start = time.time()
    try:
        assignment = solve_fn(n_vars, clauses)
        elapsed = time.time() - start
    except TimeoutError:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)
        return "exceeded hard time budget", time.time() - start
    except Exception as e:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)
        return str(e), time.time() - start
    signal.alarm(0)
    signal.signal(signal.SIGALRM, old_handler)

    if elapsed > TIME_BUDGET * 1.1:  # 10% grace
        return f"exceeded time budget: {elapsed:.1f}s > {TIME_BUDGET}s", elapsed

    err = validate_assignment(n_vars, assignment)
    if err:
        return err, elapsed

    return assignment, elapsed


def _evaluate_instances(instances, solve_fn, metric_fn, summary_key):
    """
    Shared evaluation loop.

    metric_fn(n_unsat, inst, name) -> (metric_value, extra_fields_dict)
    """
    results = {}
    total_time = 0.0
    metrics = []
    n_total = len(instances)
    n_failed = 0

    for name, inst in instances.items():
        n_vars = inst["n_vars"]
        clauses = inst["clauses"]
        result, elapsed = _run_solver(solve_fn, n_vars, clauses)
        total_time += elapsed

        if isinstance(result, str):
            results[name] = {"valid": False, "error": result, "time": elapsed}
            n_failed += 1
            continue

        n_unsat = count_unsatisfied(n_vars, clauses, result)
        metric, extra = metric_fn(n_unsat, inst, name)
        results[name] = {
            "valid": True,
            "n_unsat": n_unsat,
            **{k: round(v, 6) if isinstance(v, float) else v for k, v in extra.items()},
            "time": round(elapsed, 3),
        }
        metrics.append(metric)

    results[summary_key] = round(
        sum(metrics) / len(metrics) if metrics else 0.0, 6
    )
    results["success_rate"] = round((n_total - n_failed) / n_total, 6) if n_total > 0 else 0.0
    results["total_time"] = round(total_time, 3)
    return results


def evaluate(solve_fn) -> dict:
    """
    Evaluate against training instances (random 3-SAT).
    Metric: avg_improvement over greedy baseline (higher is better).

    improvement = (baseline_unsat - solver_unsat) / baseline_unsat
    """
    def metric_fn(n_unsat, inst, name):
        baseline = GREEDY_BASELINES[name]
        improvement = (baseline - n_unsat) / baseline if baseline > 0 else 0.0
        return improvement, {"baseline": baseline, "improvement": improvement}

    return _evaluate_instances(TRAIN_INSTANCES, solve_fn, metric_fn, summary_key="avg_improvement")


# ---------------------------------------------------------------------------
# Stable evaluation log (scientist/results.tsv — not editable by Supervisor)
# ---------------------------------------------------------------------------

RESULTS_LOG_PATH = os.path.join(os.path.dirname(__file__), "results.tsv")
BEST_KNOWN_PATH = os.path.join(os.path.dirname(__file__), "best_known.json")

_INSTANCE_NAMES = list(TRAIN_INSTANCES.keys())
RESULT_FIELDS = (
    ["timestamp", "status", "avg_improvement", "success_rate", "training_time"]
    + [f"{n}_{s}" for n in _INSTANCE_NAMES for s in ("unsat", "improvement", "time")]
    + ["notes"]
)


def _load_best_known():
    """Load best-known unsatisfied counts per instance from persistent JSON."""
    if os.path.exists(BEST_KNOWN_PATH):
        with open(BEST_KNOWN_PATH) as f:
            return json.load(f)
    return {}


def _update_best_known(instance_results):
    """Update best-known unsatisfied counts if any instance achieved a new record.

    For minimisation: fewer unsatisfied clauses is better.
    """
    best_known = _load_best_known()
    updated = False
    for name in _INSTANCE_NAMES:
        inst = instance_results.get(name)
        if not isinstance(inst, dict) or not inst.get("valid"):
            continue
        n_unsat = inst["n_unsat"]
        prev_best = best_known.get(name)
        if prev_best is None or n_unsat < prev_best:
            best_known[name] = n_unsat
            updated = True
    if updated:
        with open(BEST_KNOWN_PATH, "w") as f:
            json.dump(best_known, f, indent=2)


def log_result(train_results):
    """Append a result record with per-instance detail to results.tsv."""
    write_header = not os.path.exists(RESULTS_LOG_PATH)

    # Update best-known tracking
    _update_best_known(train_results)

    # Determine status and collect error notes
    notes = []
    any_failed = False
    for name in _INSTANCE_NAMES:
        inst = train_results.get(name)
        if isinstance(inst, dict) and not inst.get("valid", True):
            any_failed = True
            notes.append(f"{name}: {inst.get('error', 'unknown')}")
    status = "solver_error" if any_failed else "ok"

    row = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "status": status,
        "avg_improvement": train_results.get("avg_improvement"),
        "success_rate": train_results.get("success_rate"),
        "training_time": train_results.get("total_time"),
        "notes": "; ".join(notes),
    }

    # Per-instance detail
    for name in _INSTANCE_NAMES:
        inst = train_results.get(name)
        if isinstance(inst, dict) and inst.get("valid"):
            row[f"{name}_unsat"] = inst.get("n_unsat")
            row[f"{name}_improvement"] = round(inst["improvement"], 6) if "improvement" in inst else ""
            row[f"{name}_time"] = inst.get("time")
        elif isinstance(inst, dict):
            row[f"{name}_unsat"] = "FAIL"
            row[f"{name}_improvement"] = ""
            row[f"{name}_time"] = round(inst.get("time", 0), 3)
        else:
            row[f"{name}_unsat"] = ""
            row[f"{name}_improvement"] = ""
            row[f"{name}_time"] = ""

    with open(RESULTS_LOG_PATH, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=RESULT_FIELDS, delimiter="\t")
        if write_header:
            writer.writeheader()
        writer.writerow(row)


def _get_prev_best():
    """Read max avg_improvement from results.tsv, or None if no prior results."""
    if not os.path.exists(RESULTS_LOG_PATH):
        return None
    try:
        with open(RESULTS_LOG_PATH) as f:
            reader = csv.DictReader(f, delimiter="\t")
            values = [float(r["avg_improvement"]) for r in reader if r.get("avg_improvement")]
        return max(values) if values else None
    except (ValueError, KeyError):
        return None


if __name__ == "__main__":
    from scientist.maxsat.train import solve

    prev_best = _get_prev_best()
    train_results = evaluate(solve)

    print("\n=== Evaluation ===\n")
    for name, data in train_results.items():
        if not isinstance(data, dict):
            continue
        if data.get("valid"):
            n_clauses = len(TRAIN_INSTANCES[name]["clauses"])
            n_sat = n_clauses - data["n_unsat"]
            print(
                f"  {name:12s}  {n_sat:>5d} / {n_clauses:>5d} satisfied"
                f"  ({data['n_unsat']} unsat, baseline {data['baseline']})"
                f"  {data['improvement']:>+8.2%}  {data['time']:.1f}/{TIME_BUDGET}s"
            )
        else:
            print(f"  {name:12s}  FAILED: {data.get('error', 'unknown')}")
    best_str = f" (prev best: {prev_best:.2%})" if prev_best is not None else ""
    print(f"\n  avg_improvement: {train_results['avg_improvement']:.2%}{best_str}  |  success_rate: {train_results['success_rate']:.0%}  |  total_time: {train_results['total_time']}s")

    log_result(train_results)
