"""
prepare.py — Fixed evaluation harness for facility location autoresearch.
DO NOT MODIFY. The Scientist may only modify train.py.

Provides two evaluation modes:

  evaluate(solve_fn) — training eval over random instances.
    Metric: avg_improvement (higher is better).
    improvement = (baseline_cost - solver_cost) / baseline_cost
    Baseline is greedy nearest (assign each client to cheapest facility,
    ignoring opening costs), computed once and cached.

  benchmark(solve_fn) — benchmark eval over 5 larger instances.
    Metric: avg_loss (lower is better).
    loss = (solver_cost - lp_bound) / lp_bound
"""

import csv
import math
import os
import random
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

def _generate_random_instance(n_facilities: int, n_clients: int, seed: int):
    """Generate a random UFLP instance with fixed seed.

    Facilities and clients are placed at integer coordinates in [0, 1000].
    Assignment costs are integer Euclidean distances (floor via math.isqrt).
    Opening costs are uniform in [500, 3000].

    Returns (opening_costs, assign_costs) where:
      opening_costs: list of n_facilities ints
      assign_costs: n_facilities x n_clients matrix of ints
    """
    rng = random.Random(seed)
    # Facility coordinates and opening costs
    fac_x = [rng.randint(0, 1000) for _ in range(n_facilities)]
    fac_y = [rng.randint(0, 1000) for _ in range(n_facilities)]
    opening_costs = [rng.randint(500, 3000) for _ in range(n_facilities)]
    # Client coordinates
    cli_x = [rng.randint(0, 1000) for _ in range(n_clients)]
    cli_y = [rng.randint(0, 1000) for _ in range(n_clients)]
    # Assignment costs: integer Euclidean distance
    assign_costs = []
    for i in range(n_facilities):
        row = []
        for j in range(n_clients):
            dx = fac_x[i] - cli_x[j]
            dy = fac_y[i] - cli_y[j]
            row.append(math.isqrt(dx * dx + dy * dy))
        assign_costs.append(row)
    return opening_costs, assign_costs


# ---------------------------------------------------------------------------
# Training instances (unknown optimal — no memorisation possible)
# ---------------------------------------------------------------------------

TRAIN_INSTANCES = {
    "rand30_100a": {
        "opening_costs": (d := _generate_random_instance(30, 100, seed=200003))[0],
        "assign_costs": d[1], "optimal": None, "known": False,
    },
    "rand40_120a": {
        "opening_costs": (d := _generate_random_instance(40, 120, seed=200004))[0],
        "assign_costs": d[1], "optimal": None, "known": False,
    },
    "rand50_150a": {
        "opening_costs": (d := _generate_random_instance(50, 150, seed=200005))[0],
        "assign_costs": d[1], "optimal": None, "known": False,
    },
}

QUICK_INSTANCES = TRAIN_INSTANCES  # same set — no separate subset

# ---------------------------------------------------------------------------
# Benchmark instances (larger, with LP relaxation lower bounds)
# ---------------------------------------------------------------------------

BENCHMARK_INSTANCES = {
    "bench60_200a": {
        "opening_costs": (d := _generate_random_instance(60, 200, seed=200011))[0],
        "assign_costs": d[1], "optimal": None, "known": True,
    },
    "bench60_200b": {
        "opening_costs": (d := _generate_random_instance(60, 200, seed=200012))[0],
        "assign_costs": d[1], "optimal": None, "known": True,
    },
    "bench80_250a": {
        "opening_costs": (d := _generate_random_instance(80, 250, seed=200013))[0],
        "assign_costs": d[1], "optimal": None, "known": True,
    },
    "bench100_300a": {
        "opening_costs": (d := _generate_random_instance(100, 300, seed=200014))[0],
        "assign_costs": d[1], "optimal": None, "known": True,
    },
    "bench100_300b": {
        "opening_costs": (d := _generate_random_instance(100, 300, seed=200015))[0],
        "assign_costs": d[1], "optimal": None, "known": True,
    },
}

INSTANCES = {**TRAIN_INSTANCES, **BENCHMARK_INSTANCES}

# ---------------------------------------------------------------------------
# Cost computation
# ---------------------------------------------------------------------------

def total_cost(opening_costs, assign_costs, assignment):
    """Compute UFLP objective: sum of opening costs for used facilities
    plus sum of assignment costs."""
    opened = set(assignment)
    cost = sum(opening_costs[i] for i in opened)
    cost += sum(assign_costs[assignment[j]][j] for j in range(len(assignment)))
    return cost


def validate_assignment(n_facilities, n_clients, assignment):
    """Return an error string if assignment is invalid, None if valid."""
    if not isinstance(assignment, list):
        return "assignment must be a list"
    if len(assignment) != n_clients:
        return f"assignment has {len(assignment)} entries, expected {n_clients}"
    for j, fac in enumerate(assignment):
        if not isinstance(fac, int) or fac < 0 or fac >= n_facilities:
            return f"assignment[{j}] = {fac!r}, must be int in [0, {n_facilities})"
    return None

# ---------------------------------------------------------------------------
# Greedy nearest baseline
# ---------------------------------------------------------------------------

def _baseline_solve(opening_costs, assign_costs):
    """Greedy nearest: assign each client to cheapest facility, ignoring opening costs."""
    n_facilities = len(opening_costs)
    n_clients = len(assign_costs[0]) if assign_costs else 0
    assignment = []
    for j in range(n_clients):
        best_fac = min(range(n_facilities), key=lambda i: assign_costs[i][j])
        assignment.append(best_fac)
    return assignment


def _baseline_cost(opening_costs, assign_costs):
    """Cost of the greedy nearest baseline."""
    assignment = _baseline_solve(opening_costs, assign_costs)
    return total_cost(opening_costs, assign_costs, assignment)


# Precomputed: cost of greedy nearest baseline on each training instance.
BASELINE_COSTS = {
    "rand30_100a": 58857,
    "rand40_120a": 75302,
    "rand50_150a": 92043,
}

# ---------------------------------------------------------------------------
# LP relaxation lower bound (precomputed for benchmark instances)
# ---------------------------------------------------------------------------

# LP relaxation of UFLP:
#   min  sum_i f_i y_i + sum_ij c_ij x_ij
#   s.t. sum_i x_ij = 1   for all j  (each client assigned)
#        x_ij <= y_i       for all i,j (assign only to open facilities)
#        0 <= y_i <= 1,  0 <= x_ij <= 1
#
# Solved via scipy.optimize.linprog and hardcoded here.

LP_BOUNDS = {
    "bench60_200a": 33798,
    "bench60_200b": 34612,
    "bench80_250a": 39985,
    "bench100_300a": 44183,
    "bench100_300b": 45324,
}

# ---------------------------------------------------------------------------
# Evaluation core
# ---------------------------------------------------------------------------

def _run_solver(solve_fn, opening_costs, assign_costs):
    """Run solver with time budget. Returns (assignment, elapsed) or (error_str, elapsed)."""
    start = time.time()
    try:
        assignment = solve_fn(opening_costs, assign_costs)
        elapsed = time.time() - start
    except Exception as e:
        return str(e), time.time() - start

    if elapsed > TIME_BUDGET * 1.1:  # 10% grace
        return f"exceeded time budget: {elapsed:.1f}s > {TIME_BUDGET}s", elapsed

    n_facilities = len(opening_costs)
    n_clients = len(assign_costs[0]) if assign_costs else 0
    err = validate_assignment(n_facilities, n_clients, assignment)
    if err:
        return err, elapsed

    return assignment, elapsed


def _evaluate_instances(instances, solve_fn, metric_fn, penalty, summary_key):
    """
    Shared evaluation loop for both training and benchmark modes.

    metric_fn(cost, inst, name) -> (metric_value, extra_fields_dict)
    """
    results = {}
    total_time = 0.0
    metrics = []

    for name, inst in instances.items():
        opening_costs = inst["opening_costs"]
        assign_costs = inst["assign_costs"]
        result, elapsed = _run_solver(solve_fn, opening_costs, assign_costs)
        total_time += elapsed

        if isinstance(result, str):
            results[name] = {"valid": False, "error": result, "time": elapsed}
            metrics.append(penalty)
            continue

        cost = total_cost(opening_costs, assign_costs, result)
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
    Metric: avg_improvement over greedy nearest baseline (higher is better).

    improvement = (baseline_cost - solver_cost) / baseline_cost
    """
    def metric_fn(cost, inst, name):
        baseline = BASELINE_COSTS[name]
        improvement = (baseline - cost) / baseline
        return improvement, {"baseline": baseline, "improvement": improvement}

    return _evaluate_instances(QUICK_INSTANCES, solve_fn, metric_fn, penalty=-10.0, summary_key="avg_improvement")


def benchmark(solve_fn) -> dict:
    """
    Evaluate against benchmark instances (larger, with LP relaxation bounds).
    Metric: avg_loss from LP lower bound (lower is better).

    loss = (solver_cost - lp_bound) / lp_bound
    """
    def metric_fn(cost, inst, name):
        lp_bound = float(LP_BOUNDS[name])
        loss = (cost - lp_bound) / lp_bound
        return loss, {"lp_bound": LP_BOUNDS[name], "loss": loss}

    return _evaluate_instances(BENCHMARK_INSTANCES, solve_fn, metric_fn, penalty=10.0, summary_key="avg_loss")


# ---------------------------------------------------------------------------
# Stable evaluation log (scientist/results.tsv — not editable by Supervisor)
# ---------------------------------------------------------------------------

RESULTS_LOG_PATH = os.path.join(os.path.dirname(__file__), "results.tsv")

# Per-instance columns for each QUICK_INSTANCE
_INSTANCE_NAMES = list(QUICK_INSTANCES.keys())
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
    from scientist.facloc.train import solve

    train_results = evaluate(solve)

    print("\n=== Evaluation (quick instances) ===\n")
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
