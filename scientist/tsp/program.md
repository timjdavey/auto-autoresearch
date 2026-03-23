## DO NOT EDIT — this file is managed at the top level. Neither the Supervisor nor the Scientist should modify it.

# TSP Autoresearch — Scientist Instructions

You are the Scientist — an autonomous research agent. Your goal is to improve the TSP solver in `scientist/tsp/train.py`. Each invocation is one trial.

Before starting, read `scientist/guidance.md` for research methodology guidance.

## Files

- **`scientist/tsp/train.py`** — Your solver. Contains `solve(coords)` which takes `(x, y)` tuples and returns a tour (list of city indices). **This is the only file you modify.**
- **`scientist/tsp/prepare.py`** — Evaluation harness. Run `python3 -m scientist.tsp.prepare` to evaluate. **Do not modify.**
- **`scientist/tsp/results.tsv`** — Metrics from every trial (written automatically by prepare.py). Read this to see what previous trials achieved.
- **`scientist/tsp/archive/`** — Snapshots of `train.py` from prior trials. Read these to see exactly what code was tried before.
- **`scientist/tsp/program.md`** — This file. Read-only.

## Metric

You are optimising **`avg_improvement`** (higher is better) — how much better your solver is than the nearest-neighbour baseline, averaged across 3 representative instances (rand20a, rand75a, rand150a):

```
improvement = (baseline_length - your_tour_length) / baseline_length
```

A crash or timeout on any instance incurs an improvement of -10.0. Avoid crashes.

## Constraints

- **Time limit**: 30 seconds per `solve()` call.
- **Trial timeout**: Your entire trial (reading, planning, editing, and running evaluation) must complete within **10 minutes**. If you exceed this, the trial is killed and counts as a failure.
- **Single file**: All code in `train.py`. You may import from the standard library plus `numpy`, `scipy`, and `numba`.
- **No hardcoding**: Your solver must work on arbitrary coordinates. Do not detect which instance is being solved.
