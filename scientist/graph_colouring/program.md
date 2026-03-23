## DO NOT EDIT — this file is managed at the top level. Neither the Supervisor nor the Scientist should modify it.

# Graph Colouring Autoresearch — Scientist Instructions

You are the Scientist — an autonomous research agent. Your goal is to improve the graph colouring solver in `scientist/graph_colouring/train.py`. Each invocation is one trial.

Before starting, read `scientist/guidance.md` for research methodology guidance.

## Files

- **`scientist/graph_colouring/train.py`** — Your solver. Contains `solve(adj, n_nodes, n_edges)` which takes an adjacency list and returns a colouring (list of colour assignments). **This is the only file you modify.**
- **`scientist/graph_colouring/prepare.py`** — Evaluation harness. Run `python3 -m scientist.graph_colouring.prepare` to evaluate. **Do not modify.**
- **`scientist/graph_colouring/results.tsv`** — Metrics from every trial (written automatically by prepare.py). Read this to see what previous trials achieved.
- **`scientist/graph_colouring/archive/`** — Snapshots of `train.py` from prior trials. Read these to see exactly what code was tried before.
- **`scientist/graph_colouring/program.md`** — This file. Read-only.

## Metric

You are optimising **`avg_improvement`** (higher is better) — how much better your solver is than the greedy baseline, averaged across 3 representative instances (rand30a, rand75a, rand150a):

```
improvement = (baseline_colours - your_colours) / baseline_colours
```

A crash or timeout on any instance incurs an improvement of -10.0. Avoid crashes.

## Constraints

- **Time limit**: 30 seconds per `solve()` call.
- **Trial timeout**: Your entire trial (reading, planning, editing, and running evaluation) must complete within **10 minutes**. If you exceed this, the trial is killed and counts as a failure.
- **Single file**: All code in `train.py`. You may import from the standard library plus `numpy`, `scipy`, and `numba`.
- **No hardcoding**: Your solver must work on arbitrary graphs. Do not detect which instance is being solved.
