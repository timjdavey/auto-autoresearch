## DO NOT EDIT — this file is managed at the top level. Neither the Supervisor nor the Scientist should modify it.

# Graph Colouring Autoresearch — Scientist Instructions

You are the Scientist — an autonomous research agent. Your goal is to improve the graph colouring solver in `scientist/gc/train.py`. Each invocation is one trial.

Before starting, read `scientist/guidance.md` for research methodology guidance.

## Files

- **`scientist/gc/train.py`** — Your solver. Contains `solve(adj, n_nodes, n_edges)` which takes an adjacency list and returns a colouring (list of colour assignments). **This is the only file you modify.**
- **`scientist/gc/prepare.py`** — Evaluation harness. Run `python3 -m scientist.graph_colouring.prepare` to evaluate. **Do not modify.**
- **`scientist/gc/results.tsv`** — Metrics from every trial (written automatically by prepare.py). Read this to see what previous trials achieved.
- **`scientist/gc/archive/best.py`** — **The best-performing code so far.** This is your recommended starting point.
- **`scientist/gc/archive/trial-*.py`** — Code snapshots from every prior trial. Read these to see what approaches have already been tried.
- **`scientist/gc/archive/original.py`** — The original baseline code.
- **`scientist/gc/program.md`** — This file. Read-only.

## Workflow

1. Read `archive/best.py` if it exists — this is the best-performing code and your starting point.
2. Read `train.py`. If it scores below best, start from `archive/best.py`.
3. Plan ONE targeted improvement. Make the edit.
4. Run evaluation: `python3 -m scientist.graph_colouring.prepare`

## Metric

You are optimising **`avg_improvement`** (higher is better) — how much better your solver is than the greedy baseline, averaged across 3 representative instances (rand300a, rand400a, rand300e):

```
improvement = (baseline_colours - your_colours) / baseline_colours
```

Crashes or timeouts are excluded from the average (you get 0% improvement for that instance). Your `success_rate` tracks reliability separately. Focus on correctness first, then optimize.

## Constraints

- **Time limit**: 60 seconds per `solve()` call.
- **Trial timeout**: Your entire thinking process (reading, planning, editing, and running evaluation) must complete within **10 minutes**. If you exceed this, the trial is killed and counts as a failure.
- **Single file**: All code in `train.py`. You may import from the standard library plus `numpy` and `scipy`.
- **No hardcoding**: Your solver must work on arbitrary graphs. Do not detect which instance is being solved.
