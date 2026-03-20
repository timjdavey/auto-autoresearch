# TSP Autoresearch — Agent Instructions

You are an autonomous research agent. Your goal is to iteratively improve a Travelling Salesman Problem solver by modifying `train.py`. You run experiments, evaluate results, and reflect on what you've learned. You work independently and indefinitely until stopped.

## Project structure

- **`prepare.py`** — Evaluation harness. Contains 25 TSP instances (5 known TSPLIB benchmarks, 20 random), distance computation, tour validation, and the `evaluate()` function. **Do not modify.**
- **`lab/train.py`** — Your solver. Contains a single function `solve(coords)` that receives a list of `(x, y)` coordinate tuples and must return a tour as a list of city indices (a permutation of `0..n-1`). **This is the only file you modify.**
- **`lab/record.py`** — Experiment tracking CLI and library. Records experiments to `lab/results.json`. **Do not modify.**
- **`lab/results.json`** — Auto-generated experiment log. Created on first use. **Do not modify directly.**
- **`lab/program.md`** — This file. Read-only.

## The metric

The single number you are optimising is **`avg_improvement`** (higher is better).

It measures how much better your solver is than the nearest-neighbour baseline, averaged across **20 random training instances** (sizes 20–200 cities):

```
improvement = (baseline_length - your_tour_length) / baseline_length
avg_improvement = mean(improvement for all 20 training instances)
```

The baseline is computed once from the nearest-neighbour heuristic and cached. At 0% you match the baseline; at 20% your tours are 20% shorter.

There are also **5 benchmark instances** (berlin52, ch150, eil51, kroA100, st70) — well-known TSPLIB problems with published optimal tour lengths. These are evaluated separately using **`avg_loss`** (lower is better):

```
loss = (your_tour_length - optimal) / optimal
```

Benchmark results are **not** part of the optimisation loop. They exist for independent progress checking against the TSP literature. You do not need to read or act on benchmark results.

A crash or timeout on any training instance incurs an improvement penalty of -10.0 (catastrophic). Avoid crashes.

## Constraints

- **Time budget**: Each instance has a 30-second wall-clock limit. Your `solve()` function is called 25 times per evaluation (once per instance). Design algorithms that use the time budget wisely — a smarter 25-second algorithm beats a naive 0.1-second one.
- **Single file**: All your code must live in `train.py`. You may import from the standard library and `math`. Do not add external dependencies (no numpy, scipy, networkx, etc.) — keep it self-contained.
- **No hardcoding**: Do not hardcode tours or solutions for specific instances. Your `solve()` function must work as a general algorithm that takes arbitrary coordinates.
- **No reading prepare.py at runtime for coordinate matching**: Do not detect which instance is being solved to apply instance-specific logic.

## Setup

Before your first experiment:

1. **Read the files**: Read `prepare.py` and `train.py` in full for context. Understand the evaluation function, the instances, and the current solver.
2. **Review past experiments**: If `lab/results.json` exists, read it to understand what has already been tried, what worked, and what didn't. Build on prior learnings rather than repeating failed approaches.
3. **Run the baseline**: Execute a plan+run+reflect cycle (see below) with your initial hypothesis being "baseline measurement".

## Experiment loop

Each experiment follows three steps. Repeat indefinitely:

### Step 1: Plan

Formulate a hypothesis and motivation, then register the experiment:

```bash
python -m lab.record plan --hypothesis "try 2-opt local search" --motivation "should beat NN by swapping crossing edges"
```

- **hypothesis**: What specific technique or change you will try.
- **motivation**: Why you think it will improve results. This can be rational ("2-opt is proven to reduce tour length") or exploratory ("curious whether random restarts help on larger instances").

### Step 2: Run

Edit `train.py` to implement your hypothesis, then evaluate:

```bash
python prepare.py > run.log 2>&1
```

Do NOT use `tee` or let output flood your context.

Read the results:

```bash
grep "avg_improvement:\|avg_loss:" run.log
```

If grep returns nothing, the run crashed. Run `tail -n 30 run.log` to see the traceback and attempt a fix. If you cannot fix it after 2-3 attempts, revert `train.py` and move on.

The evaluation automatically records training and benchmark results into `lab/results.json` against the current experiment.

### Step 3: Reflect

Review the results and record your retrospective:

```bash
python -m lab.record reflect \
  --analysis "2-opt improved small instances (rand20-50) by 8% but rand200 only 2%. Total time well within budget." \
  --learnings "2-opt is effective for small instances but diminishing returns on larger ones. Edge density matters." \
  --future "try or-opt or 3-opt for larger instances; consider time-aware iteration" \
  --abstract "Implemented 2-opt local search. Modest improvement on small instances, limited gains on rand200. Need more sophisticated moves for larger problems."
```

- **analysis**: Breakdown of the results — what improved, what didn't, by how much.
- **learnings**: What you learned from this experiment relative to your hypothesis and motivation.
- **future**: Ideas for next experiments, informed by what you just learned.
- **abstract**: A concise summary of the entire experiment (1-3 sentences).

If the experiment failed or made things worse, **still reflect** — failed experiments are valuable data. Then revert `train.py` (`git checkout -- lab/train.py`) before planning the next experiment.

### Then repeat from Step 1.

## Research strategy guidance

The baseline is a nearest-neighbour heuristic (`avg_improvement = 0%`). Here is a rough roadmap of TSP techniques ordered by typical impact, but you should explore freely:

### Low-hanging fruit
- **Multiple starting cities**: Run nearest-neighbour from every city, keep the best tour. Cheap and often gives 5-10% improvement.
- **2-opt local search**: The classic TSP improvement. Repeatedly check if swapping two edges shortens the tour. This alone can cut the gap roughly in half.

### Medium improvements
- **Or-opt moves**: Relocate a segment of 1, 2, or 3 cities to a better position in the tour.
- **3-opt**: Like 2-opt but considers three edge swaps. More expensive per move but finds improvements 2-opt misses.
- **Combine construction + improvement**: Use nearest-neighbour (or greedy, or savings) to build an initial tour, then refine with local search.

### Advanced techniques
- **Lin-Kernighan style moves**: Variable-depth search that chains edge swaps.
- **Perturbation + restart**: When local search stalls, perturb the tour (e.g. double-bridge move) and re-optimise. This is the core of iterated local search.
- **Simulated annealing**: Accept worse moves with decreasing probability to escape local optima.
- **Time-aware strategies**: Use most of the 30-second budget. Run local search repeatedly with random restarts or perturbations, keeping the global best.

### Things to think about
- The time budget is generous (30s per instance). A nearest-neighbour + 2-opt takes milliseconds. You have time for much more.
- The larger instances (100–200 cities) benefit most from sophisticated algorithms. The smaller instances (20–50 cities) are easier — don't over-optimise for them at the expense of larger ones.
- Algorithm simplicity matters when improvement is equal. A clean 2-opt that gets 3% gap is better than a messy heuristic soup that also gets 3%.
- Track which instances your changes help most. If you're stuck on one instance, focus effort there.

## What good looks like

| avg_improvement | Rough level |
|-----------------|-------------|
| 0%              | Nearest-neighbour baseline |
| 5–10%           | 2-opt from best-of-N starts |
| 10–15%          | 3-opt or Or-opt refinement |
| 15–20%          | Iterated local search / LK-style |
| > 20%           | Excellent result |

## Principles

- **Keep it simple**: Complexity is a cost. A clean, understandable algorithm that performs well is better than a tangled one that performs slightly better.
- **One change at a time**: Each experiment should test one hypothesis. If you change three things and it improves, you don't know which one helped.
- **Use the time budget**: The biggest mistake is leaving 29 seconds on the table. If your solver finishes in 0.01s, you have room for vastly more computation.
- **Record everything**: Even failed experiments inform your next hypothesis. Always complete all three steps.
- **Don't fight crashes**: If an idea keeps crashing, revert and try something else. There are many paths to a better solver.
- **Build on history**: Read `results.json` before planning. Don't repeat failed approaches. Let past learnings guide your next hypothesis.
