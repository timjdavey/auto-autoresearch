"""
prepare.py — Fixed evaluation harness for graph colouring autoresearch.
DO NOT MODIFY. The Scientist may only modify train.py.

Provides:

  evaluate(solve_fn) — training eval over 3 random instances.
    Metric: avg_improvement (higher is better).
    improvement = (baseline_colours - solver_colours) / baseline_colours
    Baseline is greedy colouring with natural ordering, computed once and cached.
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
    "rand300a": {"adj": (d := _generate_random_instance(300, 0.3, seed=800001))[0], "n_nodes": d[1], "n_edges": d[2], "optimal": None, "known": False},
    "rand400a": {"adj": (d := _generate_random_instance(400, 0.3, seed=900001))[0], "n_nodes": d[1], "n_edges": d[2], "optimal": None, "known": False},
    "rand300e": {"adj": (d := _generate_random_instance(300, 0.5, seed=1000001))[0], "n_nodes": d[1], "n_edges": d[2], "optimal": None, "known": False},
}

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
    "rand300a": 30,
    "rand400a": 39,
    "rand300e": 49,
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
    def _timeout_handler(signum, frame):
        raise TimeoutError("solver exceeded hard time budget")

    old_handler = signal.signal(signal.SIGALRM, _timeout_handler)
    signal.alarm(TIME_BUDGET + 5)  # hard kill after budget + 5s grace
    start = time.time()
    try:
        colouring = solve_fn(adj, n_nodes, n_edges)
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

    err = validate_colouring(adj, n_nodes, colouring)
    if err:
        return err, elapsed

    return colouring, elapsed


def _evaluate_instances(instances, solve_fn, metric_fn, summary_key):
    """
    Shared evaluation loop.

    metric_fn(n_colours, inst, name) -> (metric_value, extra_fields_dict)
    """
    results = {}
    total_time = 0.0
    metrics = []
    n_total = len(instances)
    n_failed = 0

    for name, inst in instances.items():
        adj = inst["adj"]
        n_nodes = inst["n_nodes"]
        n_edges = inst["n_edges"]
        result, elapsed = _run_solver(solve_fn, adj, n_nodes, n_edges)
        total_time += elapsed

        if isinstance(result, str):
            results[name] = {"valid": False, "error": result, "time": elapsed}
            n_failed += 1
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
        sum(metrics) / len(metrics) if metrics else 0.0, 6
    )
    results["success_rate"] = round((n_total - n_failed) / n_total, 6) if n_total > 0 else 0.0
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

    return _evaluate_instances(TRAIN_INSTANCES, solve_fn, metric_fn, summary_key="avg_improvement")


# ---------------------------------------------------------------------------
# Stable evaluation log (scientist/results.tsv — not editable by Supervisor)
# ---------------------------------------------------------------------------

RESULTS_LOG_PATH = os.path.join(os.path.dirname(__file__), "results.tsv")
BEST_KNOWN_PATH = os.path.join(os.path.dirname(__file__), "best_known.json")

_INSTANCE_NAMES = list(TRAIN_INSTANCES.keys())
RESULT_FIELDS = (
    ["timestamp", "status", "avg_improvement", "success_rate", "training_time"]
    + [f"{n}_{s}" for n in _INSTANCE_NAMES for s in ("colours", "improvement", "time")]
    + ["notes"]
)


def _load_best_known():
    """Load best-known colour counts per instance from persistent JSON."""
    if os.path.exists(BEST_KNOWN_PATH):
        with open(BEST_KNOWN_PATH) as f:
            return json.load(f)
    return {}


def _update_best_known(instance_results):
    """Update best-known colour counts if any instance achieved a new record.

    For minimisation: fewer colours is better.
    Returns dict of best_known_gap per instance.
    """
    best_known = _load_best_known()
    gaps = {}
    updated = False
    for name in _INSTANCE_NAMES:
        inst = instance_results.get(name)
        if not isinstance(inst, dict) or not inst.get("valid"):
            continue
        n_colours = inst["n_colours"]
        prev_best = best_known.get(name)
        if prev_best is None or n_colours < prev_best:
            best_known[name] = n_colours
            updated = True
            gaps[name] = 0.0
        else:
            gaps[name] = round((n_colours - prev_best) / prev_best, 6) if prev_best > 0 else 0.0
    if updated:
        with open(BEST_KNOWN_PATH, "w") as f:
            json.dump(best_known, f, indent=2)
    return gaps


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
    from scientist.gc.train import solve

    train_results = evaluate(solve)

    print("\n=== Evaluation ===\n")
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
    print(f"\n  avg_improvement: {train_results['avg_improvement']:.2%}  |  success_rate: {train_results['success_rate']:.0%}  |  total_time: {train_results['total_time']}s")

    log_result(train_results)
