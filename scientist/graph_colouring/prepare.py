"""
prepare.py — Fixed evaluation harness for graph colouring autoresearch.
DO NOT MODIFY. The Scientist may only modify train.py.

Provides two evaluation modes:

  evaluate(solve_fn) — training eval over 20 random instances.
    Metric: avg_improvement (higher is better).
    improvement = (baseline_colours - solver_colours) / baseline_colours
    Baseline is greedy colouring with natural ordering, computed once and cached.

  benchmark(solve_fn) — benchmark eval over 5 DIMACS instances.
    Metric: avg_loss (lower is better).
    loss = (solver_colours - optimal) / optimal
"""

import csv
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
# DIMACS benchmark instances (loaded from baselines/*.col files)
# ---------------------------------------------------------------------------

def _parse_col_file(filepath):
    """Parse a DIMACS .col file, return (adjacency list, n_nodes, n_edges).

    Source: DIMACS Second Implementation Challenge (1993)
    Format: 'p edge N M' header, then 'e u v' edge lines (1-indexed).
    """
    adj = None
    n_nodes = 0
    n_edges = 0
    with open(filepath) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("c"):
                continue
            if line.startswith("p"):
                parts = line.split()
                n_nodes = int(parts[2])
                n_edges = int(parts[3])
                adj = [[] for _ in range(n_nodes)]
            elif line.startswith("e"):
                parts = line.split()
                u = int(parts[1]) - 1  # convert to 0-indexed
                v = int(parts[2]) - 1
                adj[u].append(v)
                adj[v].append(u)
    # Sort adjacency lists for consistency
    for i in range(n_nodes):
        adj[i].sort()
    return adj, n_nodes, n_edges


# Chromatic numbers from DIMACS challenge results and literature
_OPTIMAL = {
    "myciel4": 5,
    "queen5_5": 5,
    "queen6_6": 7,
    "myciel5": 6,
    "queen8_8": 9,
}

_BASELINES_DIR = Path(__file__).parent / "baselines"

BENCHMARK_INSTANCES = {
    name: {
        "adj": (parsed := _parse_col_file(_BASELINES_DIR / f"{name}.col"))[0],
        "n_nodes": parsed[1],
        "n_edges": parsed[2],
        "optimal": optimal,
        "known": True,
    }
    for name, optimal in _OPTIMAL.items()
    if (_BASELINES_DIR / f"{name}.col").exists()
}

# ---------------------------------------------------------------------------
# Random training instances (unknown optimal — no memorisation possible)
# ---------------------------------------------------------------------------

def _generate_random_instance(n_nodes: int, edge_prob: float, seed: int):
    """Generate a random G(n, p) graph with fixed seed. Returns (adj, n_nodes, n_edges)."""
    rng = random.Random(seed)
    adj = [[] for _ in range(n_nodes)]
    n_edges = 0
    for i in range(n_nodes):
        for j in range(i + 1, n_nodes):
            if rng.random() < edge_prob:
                adj[i].append(j)
                adj[j].append(i)
                n_edges += 1
    return adj, n_nodes, n_edges


TRAIN_INSTANCES = {
    "rand75a":  {"adj": (d := _generate_random_instance(75,  0.3, seed=173205))[0], "n_nodes": d[1], "n_edges": d[2], "optimal": None, "known": False},
    "rand100a": {"adj": (d := _generate_random_instance(100, 0.3, seed=346410))[0], "n_nodes": d[1], "n_edges": d[2], "optimal": None, "known": False},
    "rand150a": {"adj": (d := _generate_random_instance(150, 0.4, seed=538516))[0], "n_nodes": d[1], "n_edges": d[2], "optimal": None, "known": False},
    "rand200a": {"adj": (d := _generate_random_instance(200, 0.3, seed=600001))[0], "n_nodes": d[1], "n_edges": d[2], "optimal": None, "known": False},
    "rand200e": {"adj": (d := _generate_random_instance(200, 0.5, seed=700001))[0], "n_nodes": d[1], "n_edges": d[2], "optimal": None, "known": False},
}

QUICK_INSTANCES = {k: v for k, v in TRAIN_INSTANCES.items()
                   if k in ("rand150a", "rand200a", "rand200e")}

INSTANCES = {**TRAIN_INSTANCES, **BENCHMARK_INSTANCES}

# ---------------------------------------------------------------------------
# Greedy baseline
# ---------------------------------------------------------------------------

def _greedy_solve(adj, n_nodes, n_edges):
    """Greedy colouring with natural ordering. Used to compute baseline colour counts."""
    if n_nodes == 0:
        return []
    colouring = [-1] * n_nodes
    for node in range(n_nodes):
        used = set()
        for neighbour in adj[node]:
            if colouring[neighbour] != -1:
                used.add(colouring[neighbour])
        colour = 0
        while colour in used:
            colour += 1
        colouring[node] = colour
    return colouring


def _count_colours(colouring):
    """Return the number of distinct colours used."""
    if not colouring:
        return 0
    return max(colouring) + 1


# Precomputed: number of colours used by greedy on each training instance.
# To recompute: run _greedy_solve on each instance and call _count_colours.
GREEDY_BASELINES = {
    "rand75a": 12,
    "rand100a": 14,
    "rand150a": 24,
    "rand200a": 24,
    "rand200e": 35,
}

# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate_colouring(adj, n_nodes, colouring):
    """Return an error string if colouring is invalid, None if valid."""
    if not isinstance(colouring, list):
        return "colouring must be a list"
    if len(colouring) != n_nodes:
        return f"colouring has {len(colouring)} entries, expected {n_nodes}"
    for i, c in enumerate(colouring):
        if not isinstance(c, int) or c < 0:
            return f"colour at node {i} must be a non-negative integer, got {c!r}"
    for i in range(n_nodes):
        for j in adj[i]:
            if colouring[i] == colouring[j]:
                return f"adjacent nodes {i} and {j} share colour {colouring[i]}"
    return None

# ---------------------------------------------------------------------------
# Evaluation core
# ---------------------------------------------------------------------------

def _run_solver(solve_fn, adj, n_nodes, n_edges):
    """Run solver with time budget. Returns (colouring, elapsed) or (error_str, elapsed)."""
    start = time.time()
    try:
        colouring = solve_fn(adj, n_nodes, n_edges)
        elapsed = time.time() - start
    except Exception as e:
        return str(e), time.time() - start

    if elapsed > TIME_BUDGET * 1.1:  # 10% grace
        return f"exceeded time budget: {elapsed:.1f}s > {TIME_BUDGET}s", elapsed

    err = validate_colouring(adj, n_nodes, colouring)
    if err:
        return err, elapsed

    return colouring, elapsed


def _evaluate_instances(instances, solve_fn, metric_fn, penalty, summary_key):
    """
    Shared evaluation loop for both training and benchmark modes.

    metric_fn(n_colours, inst, name) -> (metric_value, extra_fields_dict)
    """
    results = {}
    total_time = 0.0
    metrics = []

    for name, inst in instances.items():
        adj = inst["adj"]
        n_nodes = inst["n_nodes"]
        n_edges = inst["n_edges"]
        result, elapsed = _run_solver(solve_fn, adj, n_nodes, n_edges)
        total_time += elapsed

        if isinstance(result, str):
            results[name] = {"valid": False, "error": result, "time": elapsed}
            metrics.append(penalty)
            continue

        n_colours = _count_colours(result)
        metric, extra = metric_fn(n_colours, inst, name)
        results[name] = {
            "valid": True,
            "n_colours": n_colours,
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
    Metric: avg_improvement over greedy baseline (higher is better).

    improvement = (baseline_colours - n_colours) / baseline_colours
    """
    def metric_fn(n_colours, inst, name):
        baseline = GREEDY_BASELINES[name]
        improvement = (baseline - n_colours) / baseline
        return improvement, {"baseline": baseline, "improvement": improvement}

    return _evaluate_instances(QUICK_INSTANCES, solve_fn, metric_fn, penalty=-10.0, summary_key="avg_improvement")


def benchmark(solve_fn) -> dict:
    """
    Evaluate against benchmark instances (DIMACS known chromatic numbers).
    Metric: avg_loss from optimal (lower is better).

    loss = (n_colours - optimal) / optimal
    """
    def metric_fn(n_colours, inst, name):
        optimal = float(inst["optimal"])
        loss = (n_colours - optimal) / optimal
        return loss, {"optimal": int(inst["optimal"]), "loss": loss}

    return _evaluate_instances(BENCHMARK_INSTANCES, solve_fn, metric_fn, penalty=10.0, summary_key="avg_loss")


# ---------------------------------------------------------------------------
# Stable evaluation log (scientist/results.tsv — not editable by Supervisor)
# ---------------------------------------------------------------------------

RESULTS_LOG_PATH = os.path.join(os.path.dirname(__file__), "results.tsv")

# Per-instance columns for each QUICK_INSTANCE (rand150a, rand200a, rand200e)
_INSTANCE_NAMES = list(QUICK_INSTANCES.keys())
RESULT_FIELDS = (
    ["timestamp", "status", "avg_improvement", "training_time"]
    + [f"{n}_{s}" for n in _INSTANCE_NAMES for s in ("colours", "improvement", "time")]
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
            row[f"{name}_colours"] = inst.get("n_colours")
            row[f"{name}_improvement"] = round(inst["improvement"], 6) if "improvement" in inst else ""
            row[f"{name}_time"] = inst.get("time")
        elif isinstance(inst, dict):
            row[f"{name}_colours"] = "FAIL"
            row[f"{name}_improvement"] = ""
            row[f"{name}_time"] = round(inst.get("time", 0), 3)
        else:
            row[f"{name}_colours"] = ""
            row[f"{name}_improvement"] = ""
            row[f"{name}_time"] = ""

    with open(RESULTS_LOG_PATH, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=RESULT_FIELDS, delimiter="\t")
        if write_header:
            writer.writeheader()
        writer.writerow(row)


if __name__ == "__main__":
    from scientist.graph_colouring.train import solve

    train_results = evaluate(solve)

    print("\n=== Evaluation (quick instances) ===\n")
    for name, data in train_results.items():
        if not isinstance(data, dict):
            continue
        if data.get("valid"):
            print(
                f"  {name:12s}  {data['n_colours']:>3d} / {data['baseline']:>3d} colours"
                f"  {data['improvement']:>+8.2%}  {data['time']:.3f}s"
            )
        else:
            print(f"  {name:12s}  FAILED: {data.get('error', 'unknown')}")
    print(f"\n  avg_improvement: {train_results['avg_improvement']:.2%}  |  total_time: {train_results['total_time']}s")

    log_result(train_results)
