## DO NOT EDIT — this file is managed at the top level. Neither the Supervisor nor the Scientist should modify it.

# TSP Autoresearch — Scientist Instructions

You are the Scientist — an autonomous research agent. Your goal is to improve the TSP solver in `scientist/tsp/train.py`. Each invocation is one trial.

Before starting, read `scientist/guidance.md` for research methodology guidance.

## Files

- **`scientist/tsp/train.py`** — Your solver. Contains `solve(coords)` which takes `(x, y)` tuples and returns a tour (list of city indices). **This is the only file you modify.**
- **`scientist/tsp/prepare.py`** — Evaluation harness. Run `python3 -m scientist.tsp.prepare` to evaluate. **Do not modify.**
- **`scientist/tsp/results.tsv`** — Metrics from every trial (written automatically by prepare.py). Read this to see what previous trials achieved.
- **`scientist/tsp/archive/best.py`** — **The best-performing code so far.** This is your recommended starting point.
- **`scientist/tsp/archive/trial-*.py`** — Code snapshots from every prior trial. Read these to see what approaches have already been tried.
- **`scientist/tsp/archive/original.py`** — The original baseline code.
- **`scientist/tsp/program.md`** — This file. Read-only.

## Workflow

1. Read `archive/best.py` if it exists — this is the best-performing code and your starting point.
2. Read `train.py`. If it scores below best, start from `archive/best.py`.
3. Plan ONE targeted improvement. Make the edit.
4. Run evaluation: `python3 -m scientist.tsp.prepare`

## Metric

You are optimising **`avg_improvement`** (higher is better) — how much better your solver is than the nearest-neighbour baseline, averaged across 3 representative instances (rand100a, rand150a, rand200a):

```
improvement = (baseline_length - your_tour_length) / baseline_length
```

A crash or timeout on any instance incurs an improvement of -10.0. Avoid crashes.

## Constraints

- **Time limit**: 60 seconds per `solve()` call.
- **Trial timeout**: Your entire thinking process (reading, planning, editing, and running evaluation) must complete within **10 minutes**. If you exceed this, the trial is killed and counts as a failure.
- **Single file**: All code in `train.py`. You may import from the standard library plus `numpy`, `scipy`, and `numba`.
- **No hardcoding**: Your solver must work on arbitrary coordinates. Do not detect which instance is being solved.
