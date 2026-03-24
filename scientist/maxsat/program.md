## DO NOT EDIT — this file is managed at the top level. Neither the Supervisor nor the Scientist should modify it.

# MAX-SAT Autoresearch — Scientist Instructions

You are the Scientist — an autonomous research agent. Your goal is to improve the Maximum Satisfiability solver in `scientist/maxsat/train.py`. Each invocation is one trial.

Before starting, read `scientist/guidance.md` for research methodology guidance.

## Files

- **`scientist/maxsat/train.py`** — Your solver. Contains `solve(n_vars, clauses)` which takes a CNF formula and returns a truth assignment (list of bools). **This is the only file you modify.**
- **`scientist/maxsat/prepare.py`** — Evaluation harness. Run `python3 -m scientist.maxsat.prepare` to evaluate. **Do not modify.**
- **`scientist/maxsat/results.tsv`** — Metrics from every trial (written automatically by prepare.py). Read this to see what previous trials achieved.
- **`scientist/maxsat/archive/best.py`** — **The best-performing code so far.** This is your recommended starting point.
- **`scientist/maxsat/archive/trial-*.py`** — Code snapshots from every prior trial. Read these to see what approaches have already been tried.
- **`scientist/maxsat/archive/original.py`** — The original baseline code.
- **`scientist/maxsat/program.md`** — This file. Read-only.

## Workflow

1. Read `archive/best.py` if it exists — this is the best-performing code and your starting point.
2. Read `train.py`. If it scores below best, start from `archive/best.py`.
3. Plan ONE targeted improvement. Make the edit.
4. Run evaluation: `python3 -m scientist.maxsat.prepare`

## Metric

You are optimising **`avg_improvement`** (higher is better) — how much better your solver is than the greedy baseline, averaged across 3 representative instances (rand200a, rand250a, rand300a):

```
improvement = (baseline_unsatisfied - your_unsatisfied) / baseline_unsatisfied
```

A crash or timeout on any instance incurs an improvement of -10.0. Avoid crashes.

## Problem

MAX-SAT: given a Boolean formula in conjunctive normal form (CNF) with 3 literals per clause (3-SAT), find a truth assignment that satisfies as many clauses as possible.

Variables are 1-indexed in clauses. Positive literal `k` means variable k is true; negative literal `-k` means variable k is false. Your assignment is 0-indexed: `assignment[i]` is the truth value for variable `i+1`.

Instances are random 3-SAT near the satisfiability phase transition (clause-to-variable ratio ~4.267), where a significant fraction of clauses cannot be simultaneously satisfied. Approaches to consider: GSAT, WalkSAT, breakout strategies, clause weighting, simulated annealing, genetic algorithms, hybrid methods.

## Constraints

- **Time limit**: 60 seconds per `solve()` call.
- **Trial timeout**: Your entire thinking process (reading, planning, editing, and running evaluation) must complete within **10 minutes**. If you exceed this, the trial is killed and counts as a failure.
- **Single file**: All code in `train.py`. You may import from the standard library plus `numpy` and `scipy`.
- **No hardcoding**: Your solver must work on arbitrary CNF formulas. Do not detect which instance is being solved.
