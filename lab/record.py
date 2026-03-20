"""
record.py — Experiment recording and display for TSP autoresearch.
Edited by the outer agent.

Usage as CLI:
    python -m lab.record plan --hypothesis "..." --motivation "..."
    python -m lab.record reflect --analysis "..." --learnings "..." --future "..." --abstract "..."
"""

import json
import os
from datetime import datetime

RESULTS_PATH = os.path.join(os.path.dirname(__file__), "results.json")


def _load_results():
    """Load the results array from results.json, or return empty list."""
    if os.path.exists(RESULTS_PATH):
        with open(RESULTS_PATH, "r") as f:
            return json.load(f)
    return []


def _save_results(results):
    """Write the results array to results.json."""
    with open(RESULTS_PATH, "w") as f:
        json.dump(results, f, indent=2)


def plan_experiment(hypothesis, motivation):
    """Step 1: Create a new experiment entry with hypothesis and motivation."""
    now = datetime.now()
    experiment = {
        "id": now.strftime("%Y%m%d-%H%M%S"),
        "timestamp": now.isoformat(timespec="seconds"),
        "hypothesis": hypothesis,
        "motivation": motivation,
    }
    results = _load_results()
    results.append(experiment)
    _save_results(results)
    print(f"Experiment {experiment['id']} created.")
    return experiment


def training_results(results: dict):
    """Step 2a: Print and record training evaluation results."""
    print("\n=== Training (random instances) ===\n")
    for name, data in results.items():
        if not isinstance(data, dict):
            continue
        if data.get("valid"):
            print(
                f"  {name:12s}  length={data['tour_length']:>12.2f}  "
                f"baseline={data['baseline']:>12.2f}  "
                f"improvement={data['improvement']:>8.4%}  "
                f"time={data['time']:.3f}s"
            )
        else:
            print(f"  {name:12s}  FAILED: {data.get('error', 'unknown')}")
    print()
    print(f"  avg_improvement: {results['avg_improvement']}")
    print(f"  total_time: {results['total_time']}s")

    # Append to current experiment
    experiments = _load_results()
    if experiments:
        experiments[-1]["training_results"] = results
        _save_results(experiments)


def benchmark_results(results: dict):
    """Step 2b: Print and record benchmark evaluation results."""
    print("\n=== Benchmark (TSPLIB known optima) ===\n")
    for name, data in results.items():
        if not isinstance(data, dict):
            continue
        if data.get("valid"):
            print(
                f"  {name:12s}  length={data['tour_length']:>12.2f}  "
                f"optimal={data['optimal']:>12.2f}  "
                f"loss={data['loss']:>8.4%}  "
                f"time={data['time']:.3f}s"
            )
        else:
            print(f"  {name:12s}  FAILED: {data.get('error', 'unknown')}")
    print()
    print(f"  avg_loss: {results['avg_loss']}")
    print(f"  total_time: {results['total_time']}s")

    # Append to current experiment
    experiments = _load_results()
    if experiments:
        experiments[-1]["benchmark_results"] = results
        _save_results(experiments)


def reflect_experiment(analysis, learnings, future, abstract):
    """Step 3: Add retrospective to the latest experiment."""
    experiments = _load_results()
    if not experiments:
        print("Error: no experiment to reflect on. Run 'plan' first.")
        return
    experiments[-1].update({
        "analysis": analysis,
        "learnings": learnings,
        "future": future,
        "abstract": abstract,
    })
    _save_results(experiments)
    print(f"Experiment {experiments[-1]['id']} reflection recorded.")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(prog="lab.record", description="Experiment tracking CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    plan_p = sub.add_parser("plan", help="Create a new experiment")
    plan_p.add_argument("--hypothesis", required=True)
    plan_p.add_argument("--motivation", required=True)

    reflect_p = sub.add_parser("reflect", help="Add retrospective to latest experiment")
    reflect_p.add_argument("--analysis", required=True)
    reflect_p.add_argument("--learnings", required=True)
    reflect_p.add_argument("--future", required=True)
    reflect_p.add_argument("--abstract", required=True)

    args = parser.parse_args()

    if args.command == "plan":
        plan_experiment(args.hypothesis, args.motivation)
    elif args.command == "reflect":
        reflect_experiment(args.analysis, args.learnings, args.future, args.abstract)
