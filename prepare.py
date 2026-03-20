"""
prepare.py — Fixed evaluation harness for TSP autoresearch.
DO NOT MODIFY. The agent may only modify train.py.

Provides two evaluation modes:

  evaluate(solve_fn) — training eval over 3 random instances.
    Metric: avg_improvement (higher is better).
    improvement = (baseline_length - tour_length) / baseline_length
    Baseline is nearest-neighbour, computed once and cached.

  benchmark(solve_fn) — benchmark eval over 3 TSPLIB instances.
    Metric: avg_loss (lower is better).
    loss = (tour_length - optimal) / optimal
"""

import json
import math
import random
import time
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

TIME_BUDGET = 30  # seconds per solve attempt (wall clock)

# ---------------------------------------------------------------------------
# TSPLIB benchmark instances (loaded from baselines.json)
# ---------------------------------------------------------------------------

_BASELINES = json.loads((Path(__file__).parent / "baselines.json").read_text())

BENCHMARK_INSTANCES = {
    name: {
        "coords": [tuple(c) for c in data["coords"]],
        "optimal": data["optimal"],
        "known": True,
    }
    for name, data in _BASELINES.items()
}

# ---------------------------------------------------------------------------
# Random training instances (unknown optimal — no memorisation possible)
# ---------------------------------------------------------------------------

def _generate_random_instance(n_cities: int, seed: int, max_coord: int = 10000) -> list[tuple[int, int]]:
    """Generate a random TSP instance with fixed seed."""
    rng = random.Random(seed)
    return [(rng.randint(0, max_coord), rng.randint(0, max_coord)) for _ in range(n_cities)]

TRAIN_INSTANCES = {
    "rand50":  {"coords": _generate_random_instance(50,  seed=770299), "optimal": None, "known": False},
    "rand75":  {"coords": _generate_random_instance(75,  seed=831401), "optimal": None, "known": False},
    "rand100": {"coords": _generate_random_instance(100, seed=952867), "optimal": None, "known": False},
}

INSTANCES = {**TRAIN_INSTANCES, **BENCHMARK_INSTANCES}

# ---------------------------------------------------------------------------
# Distance computation
# ---------------------------------------------------------------------------

def euclidean_distance(a: tuple[int, int], b: tuple[int, int]) -> float:
    return math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2)

def tour_length(coords: list[tuple[int, int]], tour: list[int]) -> float:
    """Compute total tour length. tour is a list of indices into coords."""
    total = 0.0
    n = len(tour)
    for i in range(n):
        total += euclidean_distance(coords[tour[i]], coords[tour[(i + 1) % n]])
    return total

def validate_tour(coords: list[tuple[int, int]], tour: list[int]) -> str | None:
    """Return an error string if tour is invalid, None if valid."""
    n = len(coords)
    if not isinstance(tour, list):
        return "tour must be a list"
    if len(tour) != n:
        return f"tour has {len(tour)} cities, expected {n}"
    if set(tour) != set(range(n)):
        return f"tour must be a permutation of 0..{n-1}"
    return None

# ---------------------------------------------------------------------------
# Nearest-neighbour baseline
# ---------------------------------------------------------------------------

def _nn_solve(coords: list[tuple[int, int]]) -> list[int]:
    """Nearest-neighbour heuristic. Used to compute baseline tour lengths."""
    n = len(coords)
    if n <= 1:
        return list(range(n))
    visited = [False] * n
    tour = [0]
    visited[0] = True
    for _ in range(n - 1):
        current = tour[-1]
        best_dist = float("inf")
        best_city = -1
        for j in range(n):
            if not visited[j]:
                dx = coords[current][0] - coords[j][0]
                dy = coords[current][1] - coords[j][1]
                d = math.sqrt(dx * dx + dy * dy)
                if d < best_dist:
                    best_dist = d
                    best_city = j
        tour.append(best_city)
        visited[best_city] = True
    return tour

NN_BASELINES = {
    "rand50": 67578.16163993768,
    "rand75": 80762.1187601478,
    "rand100": 92928.91055244379,
}

# ---------------------------------------------------------------------------
# Evaluation core
# ---------------------------------------------------------------------------

def _run_solver(solve_fn, coords):
    """Run solver with time budget. Returns (tour, elapsed) or (error_str, elapsed)."""
    start = time.time()
    try:
        tour = solve_fn(coords)
        elapsed = time.time() - start
    except Exception as e:
        return str(e), time.time() - start

    if elapsed > TIME_BUDGET * 1.1:  # 10% grace
        return f"exceeded time budget: {elapsed:.1f}s > {TIME_BUDGET}s", elapsed

    err = validate_tour(coords, tour)
    if err:
        return err, elapsed

    return tour, elapsed


def _evaluate_instances(instances, solve_fn, metric_fn, penalty, summary_key):
    """
    Shared evaluation loop for both training and benchmark modes.

    metric_fn(length, inst, name) -> (metric_value, extra_fields_dict)
    """
    results = {}
    total_time = 0.0
    metrics = []

    for name, inst in instances.items():
        coords = inst["coords"]
        result, elapsed = _run_solver(solve_fn, coords)
        total_time += elapsed

        if isinstance(result, str):
            results[name] = {"valid": False, "error": result, "time": elapsed}
            metrics.append(penalty)
            continue

        length = tour_length(coords, result)
        metric, extra = metric_fn(length, inst, name)
        results[name] = {
            "valid": True,
            "tour_length": round(length, 2),
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
    Metric: avg_improvement over NN baseline (higher is better).

    improvement = (baseline - tour_length) / baseline
    """
    def metric_fn(length, inst, name):
        baseline = NN_BASELINES[name]
        improvement = (baseline - length) / baseline
        return improvement, {"baseline": round(baseline, 2), "improvement": improvement}

    return _evaluate_instances(TRAIN_INSTANCES, solve_fn, metric_fn, penalty=-10.0, summary_key="avg_improvement")


def benchmark(solve_fn) -> dict:
    """
    Evaluate against benchmark instances (TSPLIB known optima).
    Metric: avg_loss from optimal (lower is better).

    loss = (tour_length - optimal) / optimal
    """
    def metric_fn(length, inst, name):
        optimal = float(inst["optimal"])
        loss = (length - optimal) / optimal
        return loss, {"optimal": round(optimal, 2), "loss": loss}

    return _evaluate_instances(BENCHMARK_INSTANCES, solve_fn, metric_fn, penalty=10.0, summary_key="avg_loss")


if __name__ == "__main__":
    from lab.train import solve
    from lab.record import training_results, benchmark_results

    train_results = evaluate(solve)
    training_results(train_results)

    bench_results = benchmark(solve)
    benchmark_results(bench_results)
