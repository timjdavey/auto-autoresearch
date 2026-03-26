## DO NOT EDIT — this file is managed at the top level. Neither the Supervisor nor the Scientist should modify it.

# Facility Location Autoresearch — Scientist Instructions

You are the Scientist — an autonomous research agent. Your goal is to improve the Uncapacitated Facility Location solver in `scientist/facloc/train.py`. Each invocation is one trial.

Before starting, read `scientist/guidance.md` for research methodology guidance.

## Files

- **`scientist/facloc/train.py`** — Your solver. Contains `solve(opening_costs, assign_costs)` which takes facility opening costs and an assignment cost matrix, and returns an assignment of clients to facilities. **This is the only file you modify.**
- **`scientist/facloc/prepare.py`** — Evaluation harness. Run `python3 -m scientist.facloc.prepare` to evaluate. **Do not modify.**
- **`scientist/facloc/results.tsv`** — Metrics from every trial (written automatically by prepare.py). Read this to see what previous trials achieved.
- **`scientist/facloc/archive/best.py`** — Code from the best-scoring prior trial. Use this if the current `train.py` is worse.
- **`scientist/facloc/archive/summary.md`** — Compact summary of all prior trials and their scores.
- **`scientist/facloc/archive/original.py`** — The original baseline code.
- **`scientist/facloc/program.md`** — This file. Read-only.

## Workflow

1. Read `results.tsv` and `archive/summary.md` to understand prior trial scores.
2. Read `train.py`. If the last trial regressed, start from `archive/best.py` instead.
3. Plan ONE targeted improvement. Make the edit.
4. Run evaluation immediately: `python3 -m scientist.facloc.prepare`
5. If it crashes or regresses badly, revert and try a different approach. Do not spend time debugging.

## Metric

You are optimising **`avg_improvement`** (higher is better) — how much better your solver is than the greedy-nearest baseline, averaged across 3 instances (rand30_100a, rand40_120a, rand50_150a):

```
improvement = (baseline_cost - your_cost) / baseline_cost
```

The greedy-nearest baseline assigns each client to the facility with the lowest assignment cost, ignoring opening costs. Your solver should balance opening costs against assignment costs.

Crashes or timeouts are excluded from the average (you get 0% improvement for that instance). Your `success_rate` tracks reliability separately. Focus on correctness first, then optimize.

## Constraints

- **Time limit**: 60 seconds per `solve()` call.
- **Trial timeout**: Your entire thinking process (reading, planning, editing, and running evaluation) must complete within **10 minutes**. If you exceed this, the trial is killed and counts as a failure.
- **Single file**: All code in `train.py`. You may import from the standard library plus `numpy` and `scipy`.
- **No hardcoding**: Your solver must work on arbitrary opening costs and assignment cost matrices. Do not detect which instance is being solved.
