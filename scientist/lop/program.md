## DO NOT EDIT — this file is managed at the top level. Neither the Supervisor nor the Scientist should modify it.

# LOP Autoresearch — Scientist Instructions

You are the Scientist — an autonomous research agent. Your goal is to improve the Linear Ordering Problem solver in `scientist/lop/train.py`. Each invocation is one trial.

Before starting, read `scientist/guidance.md` for research methodology guidance.

## Files

- **`scientist/lop/train.py`** — Your solver. Contains `solve(matrix)` which takes a square weight matrix and returns a permutation of indices. **This is the only file you modify.**
- **`scientist/lop/prepare.py`** — Evaluation harness. Run `python3 -m scientist.lop.prepare` to evaluate. **Do not modify.**
- **`scientist/lop/results.tsv`** — Metrics from every trial (written automatically by prepare.py). Read this to see what previous trials achieved.
- **`scientist/lop/archive/best.py`** — Code from the best-scoring prior trial. Use this if the current `train.py` is worse.
- **`scientist/lop/archive/summary.md`** — Compact summary of all prior trials and their scores.
- **`scientist/lop/archive/original.py`** — The original baseline code.
- **`scientist/lop/program.md`** — This file. Read-only.

## Workflow

1. Read `results.tsv` and `archive/summary.md` to understand prior trial scores.
2. Read `train.py`. If the last trial regressed, start from `archive/best.py` instead.
3. Plan ONE targeted improvement. Make the edit.
4. Run evaluation immediately: `python3 -m scientist.lop.prepare`
5. If it crashes or regresses badly, revert and try a different approach. Do not spend time debugging.

## Metric

You are optimising **`avg_improvement`** (higher is better) — how much better your solver is than the identity-permutation baseline, averaged across 3 representative instances (rand75a, rand100a, rand125a):

```
improvement = (your_score - baseline_score) / baseline_score
```

The score is the sum of matrix elements strictly above the main diagonal after reordering rows and columns by your permutation. Higher score = better ordering.

Crashes or timeouts are excluded from the average (you get 0% improvement for that instance). Your `success_rate` tracks reliability separately. Focus on correctness first, then optimize.

## Constraints

- **Time limit**: 60 seconds per `solve()` call.
- **Trial timeout**: Your entire thinking process (reading, planning, editing, and running evaluation) must complete within **10 minutes**. If you exceed this, the trial is killed and counts as a failure.
- **Single file**: All code in `train.py`. You may import from the standard library plus `numpy` and `scipy`.
- **No hardcoding**: Your solver must work on arbitrary weight matrices. Do not detect which instance is being solved.
