"""
prepare.py — Fixed evaluation harness for LOP autoresearch.
DO NOT MODIFY. The Scientist may only modify train.py.

Provides two evaluation modes:

  evaluate(solve_fn) — training eval over random instances.
    Metric: avg_improvement (higher is better).
    improvement = (solver_score - baseline_score) / baseline_score
    Baseline is identity permutation, computed once and cached.

  benchmark(solve_fn) — benchmark eval over 5 larger instances.
    Metric: avg_loss (lower is better).
    loss = (best_known - solver_score) / best_known
"""

import csv
import json
import os
import random
import signal
import time
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

TIME_BUDGET = 60  # seconds per solve attempt (wall clock)

# ---------------------------------------------------------------------------
# Instance generation
# ---------------------------------------------------------------------------

def _generate_random_instance(n: int, seed: int):
    """Generate a random LOP instance with fixed seed.

    Returns an n x n matrix with integer entries in [1, 100] and zero diagonal.
    The matrix is generally non-symmetric.
    """
    rng = random.Random(seed)
    matrix = [[0] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            if i != j:
                matrix[i][j] = rng.randint(1, 100)
    return matrix


# ---------------------------------------------------------------------------
# Training instances (unknown optimal — no memorisation possible)
# ---------------------------------------------------------------------------

TRAIN_INSTANCES = {
    "rand75a":  {"matrix": _generate_random_instance(75,  seed=271828), "optimal": None, "known": False},
    "rand100a": {"matrix": _generate_random_instance(100, seed=314159), "optimal": None, "known": False},
    "rand125a": {"matrix": _generate_random_instance(125, seed=577215), "optimal": None, "known": False},
}

# ---------------------------------------------------------------------------
# Benchmark instances (larger, with best-known scores from extended SA)
# ---------------------------------------------------------------------------

BENCHMARK_INSTANCES = {
    "bench150a": {"matrix": _generate_random_instance(150, seed=800001), "optimal": 611127, "known": True},
    "bench150b": {"matrix": _generate_random_instance(150, seed=800002), "optimal": 615411, "known": True},
    "bench175a": {"matrix": _generate_random_instance(175, seed=800003), "optimal": 825573, "known": True},
    "bench200a": {"matrix": _generate_random_instance(200, seed=800004), "optimal": 1073152, "known": True},
    "bench200b": {"matrix": _generate_random_instance(200, seed=800005), "optimal": 1077593, "known": True},
}

INSTANCES = {**TRAIN_INSTANCES, **BENCHMARK_INSTANCES}

# ---------------------------------------------------------------------------
# Score computation
# ---------------------------------------------------------------------------

def upper_triangle_sum(matrix, perm):
    """Compute LOP objective: sum of matrix[perm[i]][perm[j]] for all i < j."""
    n = len(perm)
    score = 0
    for i in range(n):
        pi = perm[i]
        for j in range(i + 1, n):
            score += matrix[pi][perm[j]]
    return score


def validate_permutation(n, perm):
    """Return an error string if perm is invalid, None if valid."""
    if not isinstance(perm, list):
        return "permutation must be a list"
    if len(perm) != n:
        return f"permutation has {len(perm)} entries, expected {n}"
    if set(perm) != set(range(n)):
        return f"permutation must be a permutation of 0..{n - 1}"
    return None

# ---------------------------------------------------------------------------
# Identity permutation baseline
# ---------------------------------------------------------------------------

def _identity_score(matrix):
    """Score of the identity permutation."""
    return upper_triangle_sum(matrix, list(range(len(matrix))))


# Precomputed: score of identity permutation on each training instance.
IDENTITY_BASELINES = {
    "rand75a":  139044,
    "rand100a": 249907,
    "rand125a": 387846,
}

# ---------------------------------------------------------------------------
# Evaluation core
# ---------------------------------------------------------------------------

def _run_solver(solve_fn, matrix):
    """Run solver with time budget. Returns (perm, elapsed) or (error_str, elapsed)."""
    def _timeout_handler(signum, frame):
        raise TimeoutError("solver exceeded hard time budget")

    old_handler = signal.signal(signal.SIGALRM, _timeout_handler)
    signal.alarm(TIME_BUDGET + 5)
    start = time.time()
    try:
        perm = solve_fn(matrix)
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

    n = len(matrix)
    err = validate_permutation(n, perm)
    if err:
        return err, elapsed

    return perm, elapsed


def _evaluate_instances(instances, solve_fn, metric_fn, summary_key):
    """
    Shared evaluation loop for both training and benchmark modes.

    metric_fn(score, inst, name) -> (metric_value, extra_fields_dict)
    """
    results = {}
    total_time = 0.0
    metrics = []
    n_total = len(instances)
    n_failed = 0

    for name, inst in instances.items():
        matrix = inst["matrix"]
        result, elapsed = _run_solver(solve_fn, matrix)
        total_time += elapsed

        if isinstance(result, str):
            results[name] = {"valid": False, "error": result, "time": elapsed}
            n_failed += 1
            continue

        score = upper_triangle_sum(matrix, result)
        metric, extra = metric_fn(score, inst, name)
        results[name] = {
            "valid": True,
            "score": score,
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
    Evaluate against training instances (random).
    Metric: avg_improvement over identity baseline (higher is better).

    improvement = (solver_score - baseline_score) / baseline_score
    """
    def metric_fn(score, inst, name):
        baseline = IDENTITY_BASELINES[name]
        improvement = (score - baseline) / baseline
        return improvement, {"baseline": baseline, "improvement": improvement}

    return _evaluate_instances(TRAIN_INSTANCES, solve_fn, metric_fn, summary_key="avg_improvement")


def benchmark(solve_fn) -> dict:
    """
    Evaluate against benchmark instances (larger, with best-known scores).
    Metric: avg_loss from best known (lower is better).

    loss = (best_known - solver_score) / best_known
    """
    def metric_fn(score, inst, name):
        best_known = float(inst["optimal"])
        loss = (best_known - score) / best_known
        return loss, {"optimal": int(inst["optimal"]), "loss": loss}

    return _evaluate_instances(BENCHMARK_INSTANCES, solve_fn, metric_fn, summary_key="avg_loss")


# ---------------------------------------------------------------------------
# Stable evaluation log (scientist/results.tsv — not editable by Supervisor)
# ---------------------------------------------------------------------------

RESULTS_LOG_PATH = os.path.join(os.path.dirname(__file__), "results.tsv")
BEST_KNOWN_PATH = os.path.join(os.path.dirname(__file__), "best_known.json")

# Per-instance columns for each training instance
_INSTANCE_NAMES = list(TRAIN_INSTANCES.keys())
RESULT_FIELDS = (
    ["timestamp", "status", "avg_improvement", "success_rate", "training_time"]
    + [f"{n}_{s}" for n in _INSTANCE_NAMES for s in ("score", "improvement", "time")]
    + ["notes"]
)


def _load_best_known():
    """Load best-known scores per instance from persistent JSON."""
    if os.path.exists(BEST_KNOWN_PATH):
        with open(BEST_KNOWN_PATH) as f:
            return json.load(f)
    return {}


def _update_best_known(instance_results):
    """Update best-known scores if any instance achieved a new record.

    For maximisation: higher score is better.
    """
    best_known = _load_best_known()
    updated = False
    for name in _INSTANCE_NAMES:
        inst = instance_results.get(name)
        if not isinstance(inst, dict) or not inst.get("valid"):
            continue
        score = inst["score"]
        prev_best = best_known.get(name)
        if prev_best is None or score > prev_best:
            best_known[name] = score
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
            row[f"{name}_score"] = inst.get("score")
            row[f"{name}_improvement"] = round(inst["improvement"], 6) if "improvement" in inst else ""
            row[f"{name}_time"] = inst.get("time")
        elif isinstance(inst, dict):
            row[f"{name}_score"] = "FAIL"
            row[f"{name}_improvement"] = ""
            row[f"{name}_time"] = round(inst.get("time", 0), 3)
        else:
            row[f"{name}_score"] = ""
            row[f"{name}_improvement"] = ""
            row[f"{name}_time"] = ""

    with open(RESULTS_LOG_PATH, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=RESULT_FIELDS, delimiter="\t")
        if write_header:
            writer.writeheader()
        writer.writerow(row)


if __name__ == "__main__":
    from scientist.lop.train import solve

    train_results = evaluate(solve)

    print("\n=== Evaluation (training instances) ===\n")
    for name, data in train_results.items():
        if not isinstance(data, dict):
            continue
        if data.get("valid"):
            print(
                f"  {name:12s}  {data['score']:>12d} / {data['baseline']:>12d}"
                f"  {data['improvement']:>+8.2%}  {data['time']:.3f}s"
            )
        else:
            print(f"  {name:12s}  FAILED: {data.get('error', 'unknown')}")
    print(f"\n  avg_improvement: {train_results['avg_improvement']:.2%}  |  success_rate: {train_results['success_rate']:.0%}  |  total_time: {train_results['total_time']}s")

    log_result(train_results)
