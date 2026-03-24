## DO NOT EDIT — this file is managed at the top level. Neither the Supervisor nor the Scientist should modify it.

# Graph Colouring Autoresearch — Scientist Instructions

You are the Scientist — an autonomous research agent. Your goal is to improve the graph colouring solver in `scientist/graph_colouring/train.py`. Each invocation is one trial.

Before starting, read `scientist/guidance.md` for research methodology guidance.

## Files

- **`scientist/graph_colouring/train.py`** — Your solver. Contains `solve(adj, n_nodes, n_edges)` which takes an adjacency list and returns a colouring (list of colour assignments). **This is the only file you modify.**
- **`scientist/graph_colouring/prepare.py`** — Evaluation harness. Run `python3 -m scientist.graph_colouring.prepare` to evaluate. **Do not modify.**
- **`scientist/graph_colouring/results.tsv`** — Metrics from every trial (written automatically by prepare.py). Read this to see what previous trials achieved.
- **`scientist/graph_colouring/archive/best.py`** — Code from the best-scoring prior trial. Use this if the current `train.py` is worse.
- **`scientist/graph_colouring/archive/summary.md`** — Compact summary of all prior trials and their scores.
- **`scientist/graph_colouring/archive/original.py`** — The original baseline code.
- **`scientist/graph_colouring/program.md`** — This file. Read-only.

## Workflow

1. Read `results.tsv` and `archive/summary.md` to understand prior trial scores.
2. Read `train.py`. If the last trial regressed, start from `archive/best.py` instead.
3. Plan ONE targeted improvement. Make the edit.
4. Run evaluation immediately: `python3 -m scientist.graph_colouring.prepare`
5. If it crashes or regresses badly, revert and try a different approach. Do not spend time debugging.

## Metric

You are optimising **`avg_improvement`** (higher is better) — how much better your solver is than the greedy baseline, averaged across 3 representative instances (rand100e, rand100f, rand150a):

```
improvement = (baseline_colours - your_colours) / baseline_colours
```

A crash or timeout on any instance incurs an improvement of -10.0. Avoid crashes.

## Constraints

- **Time limit**: 60 seconds per `solve()` call.
- **Trial timeout**: Your entire thinking process (reading, planning, editing, and running evaluation) must complete within **10 minutes**. If you exceed this, the trial is killed and counts as a failure.
- **Single file**: All code in `train.py`. You may import from the standard library plus `numpy`, `scipy`, and `numba`.
- **No hardcoding**: Your solver must work on arbitrary graphs. Do not detect which instance is being solved.
