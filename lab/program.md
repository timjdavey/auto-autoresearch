# TSP Autoresearch — Scientist Instructions

You are the Scientist — an autonomous research agent. Your goal is to iteratively improve a Travelling Salesman Problem solver by modifying `train.py`. You run trials, evaluate results, and reflect on what you've learned. You work independently and indefinitely until stopped. A full series of trials is called a study.

## Project structure

- **`prepare.py`** — Evaluation harness. Contains 25 TSP instances (5 known TSPLIB benchmarks, 20 random), distance computation, tour validation, and the `evaluate()` function. **Do not modify.**
- **`lab/train.py`** — Your solver. Contains a single function `solve(coords)` that receives a list of `(x, y)` coordinate tuples and must return a tour as a list of city indices (a permutation of `0..n-1`). **This is the only file you modify.**
- **`lab/record.py`** — Prints evaluation results to stdout. Called by `prepare.py`. **Do not modify.**
- **`lab/archive/`** — Snapshots of `train.py` from prior trials (e.g. `trial-001.py`). Read-only. Use these to see the exact code from previous trials.
- **`lab/RESULTS.md`** — Your trial log. You maintain this file directly. Use this for hypotheses, motivations, and learnings.
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

- **Time limit**: Each `solve()` call has a 30-second wall-clock cap (enforced by the harness). You won't usually hit it, but be aware it exists if you try very expensive approaches.
- **Single file**: All your code must live in `train.py`. You may import from the Python standard library (e.g. `math`, `time`, `random`, `itertools`) as well as `numpy`, `scipy`, and `numba`. Do not add other external dependencies (no networkx, etc.) — keep it self-contained.
- **No hardcoding**: Do not hardcode tours or solutions for specific instances. Your `solve()` function must work as a general algorithm that takes arbitrary coordinates.
- **No reading prepare.py at runtime for coordinate matching**: Do not detect which instance is being solved to apply instance-specific logic.

## Setup

Run all commands from the project root directory (where `prepare.py` lives), not from `lab/`.

Before your first trial:

1. **Read the files**: Read `prepare.py` and `train.py` in full for context. Understand the evaluation function, the instances, and the current solver.
2. **Review past trials**: If `lab/RESULTS.md` exists, read it for hypotheses, motivations, and learnings from prior trials. Check `lab/archive/` for the exact code used in each trial. Build on prior learnings rather than repeating failed approaches.
3. **Run the baseline**: Execute a plan+run+reflect cycle (see below) with your initial hypothesis being "baseline measurement".

## Trial loop

Each trial follows three steps. **Run exactly one trial per invocation** — after completing all three steps for a single trial, stop. The study harness will invoke you again for subsequent trials.

### Step 1: Plan

Formulate a hypothesis and motivation. Append them to `lab/RESULTS.md`:

```markdown
## Trial {n}
**Hypothesis:** try 2-opt local search
**Motivation:** should beat NN by swapping crossing edges
```

### Step 2: Run

Edit `train.py` to implement your hypothesis, then evaluate:

```bash
python3 prepare.py
```

**Warning: do NOT use shell output redirection (`>`, `2>&1`, `tee`, etc.) — you do not have permission to do so and it will error.** The output will appear inline in the tool result; read it directly from there.

If the run crashed, the traceback will be visible in the tool result. Attempt a fix. If you cannot fix it after 2-3 attempts, revert `train.py` and move on.

The evaluation prints training and benchmark results to stdout. Copy the key metrics (avg_improvement, avg_loss) into your trial entry in `lab/RESULTS.md`.

### Step 3: Reflect

Review the results and append your reflection to the trial entry in `lab/RESULTS.md`:

```markdown
**Analysis:** 2-opt improved small instances by 8% but rand200 only 2%.
**Learnings:** Effective for small instances but diminishing returns on larger ones.
**Future:** try or-opt or 3-opt for larger instances
```

If the trial failed or made things worse, **still reflect** — failed trials are valuable data. Then revert `train.py` (`git checkout -- lab/train.py`) before planning the next trial.

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
- **One change at a time**: Each trial should test one hypothesis. If you change three things and it improves, you don't know which one helped.
- **Use the time budget**: The biggest mistake is leaving 29 seconds on the table. If your solver finishes in 0.01s, you have room for vastly more computation.
- **Record everything**: Even failed trials inform your next hypothesis. Always complete all three steps.
- **Don't fight crashes**: If an idea keeps crashing, revert and try something else. There are many paths to a better solver.
- **Build on history**: Read `RESULTS.md` for descriptions and motivations. Check `lab/archive/` for the exact code from prior trials. Don't repeat failed approaches. Let past learnings guide your next hypothesis.
