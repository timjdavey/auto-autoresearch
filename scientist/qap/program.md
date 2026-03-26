## DO NOT EDIT — this file is managed at the top level. Neither the Supervisor nor the Scientist should modify it.

# QAP Autoresearch — Scientist Instructions

You are the Scientist — an autonomous research agent. Your goal is to improve the Quadratic Assignment Problem solver in `scientist/qap/train.py`. Each invocation is one trial.

Before starting, read `scientist/guidance.md` for research methodology guidance.

## Files

- **`scientist/qap/train.py`** — Your solver. Contains `solve(flow, distance)` which takes two square matrices and returns an assignment (list mapping facilities to locations). **This is the only file you modify.**
- **`scientist/qap/prepare.py`** — Evaluation harness (run automatically by the harness after your trial). **Do not modify or run.**
- **`scientist/qap/results.tsv`** — Metrics from every trial (written automatically by prepare.py). Read this to see what previous trials achieved.
- **`scientist/qap/archive/best.py`** — Code from the best-scoring prior trial. Use this if the current `train.py` is worse.
- **`scientist/qap/archive/summary.md`** — Compact summary of all prior trials and their scores.
- **`scientist/qap/archive/original.py`** — The original baseline code.
- **`scientist/qap/program.md`** — This file. Read-only.

## Workflow

1. Read `results.tsv` and `archive/summary.md` to understand prior trial scores.
2. Read `train.py`. If the last trial regressed, start from `archive/best.py` instead.
3. Plan ONE targeted improvement. Make the edit.
4. Update `memory.md` with what you changed, your hypothesis, and what to try next.

The harness runs `prepare.py` automatically after your trial ends — do not run it yourself.

## Metric

You are optimising **`avg_improvement`** (higher is better) — how much better your solver is than the identity-permutation baseline, averaged across 3 representative instances (rand50a, rand60a, rand75a):

```
improvement = (baseline_cost - your_cost) / baseline_cost
```

Crashes or timeouts are excluded from the average (you get 0% improvement for that instance). Your `success_rate` tracks reliability separately. Focus on correctness first, then optimize.

## Constraints

- **Time limit**: 60 seconds per `solve()` call.
- **Trial timeout**: Your entire thinking process (reading, planning, editing, and running evaluation) must complete within **10 minutes**. If you exceed this, the trial is killed and counts as a failure.
- **Single file**: All code in `train.py`. You may import from the standard library plus `numpy` and `scipy`.
- **No hardcoding**: Your solver must work on arbitrary flow/distance matrices. Do not detect which instance is being solved.
