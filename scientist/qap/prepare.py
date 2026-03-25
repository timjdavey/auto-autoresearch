"""
prepare.py — Fixed evaluation harness for QAP autoresearch.
DO NOT MODIFY. The Scientist may only modify train.py.

Provides:

  evaluate(solve_fn) — training eval over 3 random instances.
    Metric: avg_improvement (higher is better).
    improvement = (baseline_cost - solver_cost) / baseline_cost
    Baseline is identity permutation, computed once and cached.
"""

import csv
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
# Instance generation
# ---------------------------------------------------------------------------

def _generate_random_instance(n: int, seed: int):
    """Generate a random QAP instance with fixed seed.

    Returns (flow, distance) as symmetric n x n integer matrices with zero diagonal.
    """
    rng = random.Random(seed)
    flow = [[0] * n for _ in range(n)]
    distance = [[0] * n for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            f = rng.randint(1, 100)
            flow[i][j] = f
            flow[j][i] = f
            d = rng.randint(1, 100)
            distance[i][j] = d
            distance[j][i] = d
    return flow, distance


# ---------------------------------------------------------------------------
# Training instances (unknown optimal — no memorisation possible)
# ---------------------------------------------------------------------------

TRAIN_INSTANCES = {
    "rand50a": {"flow": (d := _generate_random_instance(50, seed=314159))[0], "distance": d[1], "optimal": None, "known": False},
    "rand60a": {"flow": (d := _generate_random_instance(60, seed=577215))[0], "distance": d[1], "optimal": None, "known": False},
    "rand75a": {"flow": (d := _generate_random_instance(75, seed=161803))[0], "distance": d[1], "optimal": None, "known": False},
}

# ---------------------------------------------------------------------------
# Cost computation
# ---------------------------------------------------------------------------

def assignment_cost(flow, distance, assignment):
    """Compute QAP objective: sum of flow[i][j] * distance[perm[i]][perm[j]]."""
    n = len(flow)
    cost = 0
    for i in range(n):
        pi = assignment[i]
        for j in range(n):
            cost += flow[i][j] * distance[pi][assignment[j]]
    return cost


def validate_assignment(n, assignment):
    """Return an error string if assignment is invalid, None if valid."""
    if not isinstance(assignment, list):
        return "assignment must be a list"
    if len(assignment) != n:
        return f"assignment has {len(assignment)} entries, expected {n}"
    if set(assignment) != set(range(n)):
        return f"assignment must be a permutation of 0..{n - 1}"
    return None

# ---------------------------------------------------------------------------
# Identity permutation baseline
# ---------------------------------------------------------------------------

def _identity_cost(flow, distance):
    """Cost of the identity permutation (facility i -> location i)."""
    return assignment_cost(flow, distance, list(range(len(flow))))


# Precomputed: cost of identity permutation on each training instance.
IDENTITY_BASELINES = {
    "rand50a": 6191454,
    "rand60a": 8955822,
    "rand75a": 14134126,
}

# ---------------------------------------------------------------------------
# Evaluation core
# ---------------------------------------------------------------------------

def _run_solver(solve_fn, flow, distance):
    """Run solver with time budget. Returns (assignment, elapsed) or (error_str, elapsed)."""
    def _timeout_handler(signum, frame):
        raise TimeoutError("solver exceeded hard time budget")

    old_handler = signal.signal(signal.SIGALRM, _timeout_handler)
    signal.alarm(TIME_BUDGET + 5)
    start = time.time()
    try:
        assignment = solve_fn(flow, distance)
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

    n = len(flow)
    err = validate_assignment(n, assignment)
    if err:
        return err, elapsed

    return assignment, elapsed


def _evaluate_instances(instances, solve_fn, metric_fn, penalty, summary_key):
    """
    Shared evaluation loop.

    metric_fn(cost, inst, name) -> (metric_value, extra_fields_dict)
    """
    results = {}
    total_time = 0.0
    metrics = []

    for name, inst in instances.items():
        flow = inst["flow"]
        distance = inst["distance"]
        result, elapsed = _run_solver(solve_fn, flow, distance)
        total_time += elapsed

        if isinstance(result, str):
            results[name] = {"valid": False, "error": result, "time": elapsed}
            metrics.append(penalty)
            continue

        cost = assignment_cost(flow, distance, result)
        metric, extra = metric_fn(cost, inst, name)
        results[name] = {
            "valid": True,
            "cost": cost,
            **{k: round(v, 6) if isinstance(v, float) else v for k, v in extra.items()},
            "time": round(elapsed, 3),
        }
        metrics.append(metric)

    results[summary_key] = round(
        sum(metrics) / len(metrics) if metrics else penalty, 6
    )
    results["total_time"] = round(total_time, 3)
    return results


def evaluate(solve_fn) -> dict:
    """
    Evaluate against training instances (random).
    Metric: avg_improvement over identity baseline (higher is better).

    improvement = (baseline_cost - solver_cost) / baseline_cost
    """
    def metric_fn(cost, inst, name):
        baseline = IDENTITY_BASELINES[name]
        improvement = (baseline - cost) / baseline
        return improvement, {"baseline": baseline, "improvement": improvement}

    return _evaluate_instances(TRAIN_INSTANCES, solve_fn, metric_fn, penalty=-10.0, summary_key="avg_improvement")


# ---------------------------------------------------------------------------
# Stable evaluation log (scientist/results.tsv — not editable by Supervisor)
# ---------------------------------------------------------------------------

RESULTS_LOG_PATH = os.path.join(os.path.dirname(__file__), "results.tsv")

_INSTANCE_NAMES = list(TRAIN_INSTANCES.keys())
RESULT_FIELDS = (
    ["timestamp", "status", "avg_improvement", "training_time"]
    + [f"{n}_{s}" for n in _INSTANCE_NAMES for s in ("cost", "improvement", "time")]
    + ["notes"]
)


def log_result(train_results):
    """Append a result record with per-instance detail to results.tsv."""
    write_header = not os.path.exists(RESULTS_LOG_PATH)

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
        "training_time": train_results.get("total_time"),
        "notes": "; ".join(notes),
    }

    # Per-instance detail
    for name in _INSTANCE_NAMES:
        inst = train_results.get(name)
        if isinstance(inst, dict) and inst.get("valid"):
            row[f"{name}_cost"] = inst.get("cost")
            row[f"{name}_improvement"] = round(inst["improvement"], 6) if "improvement" in inst else ""
            row[f"{name}_time"] = inst.get("time")
        elif isinstance(inst, dict):
            row[f"{name}_cost"] = "FAIL"
            row[f"{name}_improvement"] = ""
            row[f"{name}_time"] = round(inst.get("time", 0), 3)
        else:
            row[f"{name}_cost"] = ""
            row[f"{name}_improvement"] = ""
            row[f"{name}_time"] = ""

    with open(RESULTS_LOG_PATH, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=RESULT_FIELDS, delimiter="\t")
        if write_header:
            writer.writeheader()
        writer.writerow(row)


if __name__ == "__main__":
    from scientist.qap.train import solve

    train_results = evaluate(solve)

    print("\n=== Evaluation ===\n")
    for name, data in train_results.items():
        if not isinstance(data, dict):
            continue
        if data.get("valid"):
            print(
                f"  {name:12s}  {data['cost']:>12d} / {data['baseline']:>12d}"
                f"  {data['improvement']:>+8.2%}  {data['time']:.3f}s"
            )
        else:
            print(f"  {name:12s}  FAILED: {data.get('error', 'unknown')}")
    print(f"\n  avg_improvement: {train_results['avg_improvement']:.2%}  |  total_time: {train_results['total_time']}s")

    log_result(train_results)
