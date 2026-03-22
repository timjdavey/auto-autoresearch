# TSP Autoresearch — Scientist Instructions

You are the Scientist — an autonomous research agent. Your goal is to improve the TSP solver in `scientist/train.py`. Each invocation is one trial.

## Files

- **`scientist/train.py`** — Your solver. Contains `solve(coords)` which takes `(x, y)` tuples and returns a tour (list of city indices). **This is the only file you modify.**
- **`scientist/prepare.py`** — Evaluation harness. Run `python3 scientist/prepare.py` to evaluate. **Do not modify.**
- **`scientist/results.tsv`** — Metrics from every trial (written automatically by prepare.py). Read this to see what previous trials achieved.
- **`scientist/archive/`** — Snapshots of `train.py` from prior trials. Read these to see exactly what code was tried before.
- **`scientist/program.md`** — This file. Read-only.

## Metric

You are optimising **`avg_improvement`** (higher is better) — how much better your solver is than the nearest-neighbour baseline, averaged across 3 representative instances (rand20a, rand75a, rand150a):

```
improvement = (baseline_length - your_tour_length) / baseline_length
```

A crash or timeout on any instance incurs an improvement of -10.0. Avoid crashes.

## Constraints

- **Time limit**: 30 seconds per `solve()` call.
- **Single file**: All code in `train.py`. You may import from the standard library plus `numpy`, `scipy`, and `numba`.
- **No hardcoding**: Your solver must work on arbitrary coordinates. Do not detect which instance is being solved.

## The experiment loop

Run exactly one trial per invocation, then stop.

1. **Review history**: Read `scientist/results.tsv` and recent files in `scientist/archive/` to understand what has been tried and how well it worked. Build on what worked; avoid repeating what failed.
2. **Edit `scientist/train.py`**: Implement your idea.
3. **Evaluate**: Run `python3 scientist/prepare.py` from the project root. Do NOT use shell redirection (`>`, `2>&1`, `tee`).
4. **Keep or revert**: If avg_improvement is better than the previous best, keep the change. If it's worse or it crashed, revert with `git checkout -- scientist/train.py`.

If a run crashes, try to fix it (2–3 attempts max). If you can't, revert and move on.
