"""
prepare.py — Fixed evaluation harness for TSP autoresearch.
DO NOT MODIFY. The Scientist may only modify train.py.

Provides two evaluation modes:

  evaluate(solve_fn) — training eval over 20 random instances.
    Metric: avg_improvement (higher is better).
    improvement = (baseline_length - tour_length) / baseline_length
    Baseline is nearest-neighbour, computed once and cached.

  benchmark(solve_fn) — benchmark eval over 5 TSPLIB instances.
    Metric: avg_loss (lower is better).
    loss = (tour_length - optimal) / optimal
"""

import csv
import json
import math
import os
import random
import time
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

TIME_BUDGET = 30  # seconds per solve attempt (wall clock)

# ---------------------------------------------------------------------------
# TSPLIB benchmark instances (loaded from baselines/*.tsp files)
# ---------------------------------------------------------------------------

def _parse_tsp_file(filepath):
    """Parse a TSPLIB .tsp file, return list of (x, y) coordinate tuples.

    Source: TSPLIB95 archive (comopt.ifi.uni-heidelberg.de/software/TSPLIB95/tsp/)
    Optimal solutions: TSPLIB95 STSP page (comopt.ifi.uni-heidelberg.de/software/TSPLIB95/STSP.html)
    """
    coords = []
    in_coords = False
    with open(filepath) as f:
        for line in f:
            line = line.strip()
            if line == "NODE_COORD_SECTION":
                in_coords = True
            elif in_coords:
                if line in ("EOF", "") or ":" in line:
                    break
                parts = line.split()
                coords.append((float(parts[1]), float(parts[2])))
    return coords

# Optimal tour lengths from TSPLIB95 published solutions
# Source: comopt.ifi.uni-heidelberg.de/software/TSPLIB95/STSP.html
_OPTIMAL = {
    "eil51": 426,
    "berlin52": 7542,
    "st70": 675,
    "kroA100": 21282,
    "ch150": 6528,
}

_BASELINES_DIR = Path(__file__).parent / "baselines"

BENCHMARK_INSTANCES = {
    name: {
        "coords": _parse_tsp_file(_BASELINES_DIR / f"{name}.tsp"),
        "optimal": optimal,
        "known": True,
    }
    for name, optimal in _OPTIMAL.items()
}

# ---------------------------------------------------------------------------
# Random training instances (unknown optimal — no memorisation possible)
# ---------------------------------------------------------------------------

def _generate_random_instance(n_cities: int, seed: int, max_coord: int = 10000) -> list[tuple[int, int]]:
    """Generate a random TSP instance with fixed seed."""
    rng = random.Random(seed)
    return [(rng.randint(0, max_coord), rng.randint(0, max_coord)) for _ in range(n_cities)]

TRAIN_INSTANCES = {
    "rand20a":  {"coords": _generate_random_instance(20,  seed=142857), "optimal": None, "known": False},
    "rand20b":  {"coords": _generate_random_instance(20,  seed=285714), "optimal": None, "known": False},
    "rand30a":  {"coords": _generate_random_instance(30,  seed=314159), "optimal": None, "known": False},
    "rand30b":  {"coords": _generate_random_instance(30,  seed=271828), "optimal": None, "known": False},
    "rand50a":  {"coords": _generate_random_instance(50,  seed=577215), "optimal": None, "known": False},
    "rand50b":  {"coords": _generate_random_instance(50,  seed=161803), "optimal": None, "known": False},
    "rand50c":  {"coords": _generate_random_instance(50,  seed=236067), "optimal": None, "known": False},
    "rand50d":  {"coords": _generate_random_instance(50,  seed=141421), "optimal": None, "known": False},
    "rand75a":  {"coords": _generate_random_instance(75,  seed=173205), "optimal": None, "known": False},
    "rand75b":  {"coords": _generate_random_instance(75,  seed=223606), "optimal": None, "known": False},
    "rand75c":  {"coords": _generate_random_instance(75,  seed=264575), "optimal": None, "known": False},
    "rand75d":  {"coords": _generate_random_instance(75,  seed=316227), "optimal": None, "known": False},
    "rand100a": {"coords": _generate_random_instance(100, seed=346410), "optimal": None, "known": False},
    "rand100b": {"coords": _generate_random_instance(100, seed=374165), "optimal": None, "known": False},
    "rand100c": {"coords": _generate_random_instance(100, seed=412310), "optimal": None, "known": False},
    "rand100d": {"coords": _generate_random_instance(100, seed=447213), "optimal": None, "known": False},
    "rand150a": {"coords": _generate_random_instance(150, seed=483568), "optimal": None, "known": False},
    "rand150b": {"coords": _generate_random_instance(150, seed=509901), "optimal": None, "known": False},
    "rand200a": {"coords": _generate_random_instance(200, seed=538516), "optimal": None, "known": False},
    "rand200b": {"coords": _generate_random_instance(200, seed=567128), "optimal": None, "known": False},
}

QUICK_INSTANCES = {k: v for k, v in TRAIN_INSTANCES.items()
                   if k in ("rand20a", "rand75a", "rand150a")}

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
    "rand20a": 39587.044174362425,
    "rand20b": 40842.76058618296,
    "rand30a": 57485.3313339793,
    "rand30b": 59994.76856526547,
    "rand50a": 71140.87654979469,
    "rand50b": 81396.97894233433,
    "rand50c": 66471.09699727633,
    "rand50d": 70741.68175324058,
    "rand75a": 78169.84343551836,
    "rand75b": 85407.94029874004,
    "rand75c": 87305.14519900268,
    "rand75d": 85693.18727546492,
    "rand100a": 96800.24669345064,
    "rand100b": 106996.82632505952,
    "rand100c": 89833.000561935,
    "rand100d": 94778.6431453671,
    "rand150a": 108224.7699586495,
    "rand150b": 112584.70702871727,
    "rand200a": 137823.6598990963,
    "rand200b": 138506.1234535633,
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

    return _evaluate_instances(QUICK_INSTANCES, solve_fn, metric_fn, penalty=-10.0, summary_key="avg_improvement")


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


# ---------------------------------------------------------------------------
# Stable evaluation log (scientist/results.tsv — not editable by Supervisor)
# ---------------------------------------------------------------------------

RESULTS_LOG_PATH = os.path.join(os.path.dirname(__file__), "results.tsv")
RESULT_FIELDS = ["timestamp", "avg_improvement", "training_time"]


def log_result(train_results):
    """Append a stable result record to scientist/results.tsv."""
    write_header = not os.path.exists(RESULTS_LOG_PATH)
    with open(RESULTS_LOG_PATH, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=RESULT_FIELDS, delimiter="\t")
        if write_header:
            writer.writeheader()
        writer.writerow({
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "avg_improvement": train_results.get("avg_improvement"),
            "training_time": train_results.get("total_time"),
        })


if __name__ == "__main__":
    from scientist.tsp.train import solve

    train_results = evaluate(solve)

    print("\n=== Evaluation (quick instances) ===\n")
    for name, data in train_results.items():
        if not isinstance(data, dict):
            continue
        if data.get("valid"):
            print(
                f"  {name:12s}  {data['tour_length']:>10.2f} / {data['baseline']:>10.2f}"
                f"  {data['improvement']:>+8.2%}  {data['time']:.3f}s"
            )
        else:
            print(f"  {name:12s}  FAILED: {data.get('error', 'unknown')}")
    print(f"\n  avg_improvement: {train_results['avg_improvement']:.2%}  |  total_time: {train_results['total_time']}s")

    log_result(train_results)
