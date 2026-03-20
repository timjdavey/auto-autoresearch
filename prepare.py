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

import math
import time
import random

# ---------------------------------------------------------------------------
# Constants (fixed, do not modify)
# ---------------------------------------------------------------------------

TIME_BUDGET = 30  # seconds per solve attempt (wall clock)

# ---------------------------------------------------------------------------
# TSPLIB instances (known optimal solutions)
# Coordinates sourced from TSPLIB. Optimal tour lengths are published.
# ---------------------------------------------------------------------------

# berlin52: 52 locations in Berlin. Optimal = 7542
BERLIN52_COORDS = [
    (565,575),(25,185),(345,750),(945,685),(845,655),
    (880,660),(25,230),(525,1000),(580,1175),(650,1130),
    (1605,620),(1220,580),(1465,200),(1530,5),(845,680),
    (725,370),(145,665),(415,635),(510,875),(560,365),
    (300,465),(520,585),(480,415),(835,625),(975,580),
    (1215,245),(1320,315),(1250,400),(660,180),(410,250),
    (420,555),(575,665),(1150,1160),(700,580),(685,595),
    (685,610),(770,610),(795,645),(720,635),(760,650),
    (475,960),(95,260),(875,920),(700,500),(555,815),
    (830,485),(1170,65),(830,610),(605,625),(595,360),
    (1340,725),(1740,245),
]
BERLIN52_OPTIMAL = 7542

# eil51: 51 cities. Optimal = 426
EIL51_COORDS = [
    (37,52),(49,49),(52,64),(20,26),(40,30),
    (21,47),(17,63),(31,62),(52,33),(51,21),
    (42,41),(31,32),(5,25),(12,42),(36,16),
    (52,41),(27,23),(17,33),(13,13),(57,58),
    (62,42),(42,57),(16,57),(8,52),(7,38),
    (27,68),(30,48),(43,67),(58,48),(58,27),
    (37,69),(38,46),(46,10),(61,33),(62,63),
    (63,69),(32,22),(45,35),(59,15),(5,6),
    (10,17),(21,10),(5,64),(30,15),(39,10),
    (32,39),(25,32),(25,55),(48,28),(56,37),
    (30,40),
]
EIL51_OPTIMAL = 426

# kroA100: 100 cities. Optimal = 21282
KROA100_COORDS = [
    (1380,939),(2848,96),(3510,1671),(457,334),(3888,666),
    (984,965),(2721,1482),(1286,525),(2716,1432),(738,1325),
    (1251,1832),(2728,1698),(3815,169),(3683,1533),(1247,1945),
    (123,862),(1234,1946),(252,1240),(611,673),(2576,1676),
    (928,1700),(53,857),(2301,1718),(2631,302),(1100,2153),
    (3918,1012),(3780,1044),(1944,1622),(2510,832),(3455,1782),
    (1150,1041),(2688,1305),(3010,1969),(2895,1675),(3329,841),
    (3500,1214),(1605,1417),(1255,1462),(555,2174),(1151,2076),
    (2941,749),(2611,1222),(2163,2049),(2710,1780),(3272,1924),
    (1632,2060),(3022,2037),(2483,1455),(1,1857),(1764,37),
    (2848,1230),(2967,1868),(2665,2130),(3249,920),(3266,1561),
    (2693,1862),(1015,1929),(2009,1881),(2366,1040),(2234,1672),
    (3312,790),(2578,1490),(2989,1500),(2914,1869),(3195,1825),
    (2244,1781),(3074,379),(2828,1857),(3371,1488),(3258,1861),
    (2298,1553),(3426,1048),(2438,1318),(3585,1235),(2417,76),
    (2535,1015),(1327,1893),(1801,672),(2810,1681),(2014,1686),
    (2732,1285),(1555,1428),(2052,1778),(1344,1694),(1910,541),
    (3159,1700),(1290,1914),(2569,1564),(2278,1198),(1191,1366),
    (1167,1695),(2529,1655),(2738,1365),(3326,1001),(652,1577),
    (1222,1615),(2834,1268),(1490,1543),(2013,1841),(2012,1868),
]
KROA100_OPTIMAL = 21282

# ---------------------------------------------------------------------------
# Random instances (unknown optimal — no memorisation possible)
# ---------------------------------------------------------------------------

def _generate_random_instance(n_cities: int, seed: int, max_coord: int = 10000) -> list[tuple[int, int]]:
    """Generate a random TSP instance with fixed seed."""
    rng = random.Random(seed)
    return [(rng.randint(0, max_coord), rng.randint(0, max_coord)) for _ in range(n_cities)]

RANDOM_50  = _generate_random_instance(50,  seed=770299)
RANDOM_75  = _generate_random_instance(75,  seed=831401)
RANDOM_100 = _generate_random_instance(100, seed=952867)

# ---------------------------------------------------------------------------
# Instance sets
# ---------------------------------------------------------------------------

# Training instances — random, no known optimal. The agent optimises against these.
TRAIN_INSTANCES = {
    "rand50":   {"coords": RANDOM_50,  "optimal": None, "known": False},
    "rand75":   {"coords": RANDOM_75,  "optimal": None, "known": False},
    "rand100":  {"coords": RANDOM_100, "optimal": None, "known": False},
}

# Benchmark instances — TSPLIB with published optima. For independent progress checking.
BENCHMARK_INSTANCES = {
    "berlin52": {"coords": BERLIN52_COORDS, "optimal": BERLIN52_OPTIMAL, "known": True},
    "eil51":    {"coords": EIL51_COORDS,    "optimal": EIL51_OPTIMAL,    "known": True},
    "kroA100":  {"coords": KROA100_COORDS,  "optimal": KROA100_OPTIMAL,  "known": True},
}

# All instances (union)
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
# Nearest-neighbour baseline (reference for training improvement metric)
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
# Evaluation
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


def evaluate(solve_fn) -> dict:
    """
    Evaluate against training instances (random).
    Metric: avg_improvement over NN baseline (higher is better).

    improvement = (baseline - tour_length) / baseline
    """
    baselines = NN_BASELINES
    results = {}
    total_time = 0.0
    improvements = []

    for name, inst in TRAIN_INSTANCES.items():
        coords = inst["coords"]
        result, elapsed = _run_solver(solve_fn, coords)
        total_time += elapsed

        if isinstance(result, str):
            results[name] = {"valid": False, "error": result, "time": elapsed}
            improvements.append(-10.0)  # heavy penalty for crash
            continue

        length = tour_length(coords, result)
        baseline = baselines[name]
        improvement = (baseline - length) / baseline

        results[name] = {
            "valid": True,
            "tour_length": round(length, 2),
            "baseline": round(baseline, 2),
            "improvement": round(improvement, 6),
            "time": round(elapsed, 3),
        }
        improvements.append(improvement)

    results["avg_improvement"] = round(
        sum(improvements) / len(improvements) if improvements else -10.0, 6
    )
    results["total_time"] = round(total_time, 3)
    return results


def benchmark(solve_fn) -> dict:
    """
    Evaluate against benchmark instances (TSPLIB known optima).
    Metric: avg_loss from optimal (lower is better).

    loss = (tour_length - optimal) / optimal
    """
    results = {}
    total_time = 0.0
    losses = []

    for name, inst in BENCHMARK_INSTANCES.items():
        coords = inst["coords"]
        result, elapsed = _run_solver(solve_fn, coords)
        total_time += elapsed

        if isinstance(result, str):
            results[name] = {"valid": False, "error": result, "time": elapsed}
            losses.append(10.0)  # heavy penalty for crash
            continue

        length = tour_length(coords, result)
        optimal = float(inst["optimal"])
        loss = (length - optimal) / optimal

        results[name] = {
            "valid": True,
            "tour_length": round(length, 2),
            "optimal": round(optimal, 2),
            "loss": round(loss, 6),
            "time": round(elapsed, 3),
        }
        losses.append(loss)

    results["avg_loss"] = round(
        sum(losses) / len(losses) if losses else 10.0, 6
    )
    results["total_time"] = round(total_time, 3)
    return results

if __name__ == "__main__":
    from lab.train import solve
    from lab.record import training_results, benchmark_results

    train_results = evaluate(solve)
    training_results(train_results)

    bench_results = benchmark(solve)
    benchmark_results(bench_results)