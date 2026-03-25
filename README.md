# auto-autoresearch
Autoresearching how to do autoresearch.

As we've seen it isn't just a great tool for optimising [NLM models](https://github.com/karpathy/autoresearch/), but also an [excellent pattern](https://x.com/tobi/status/2032212531846971413) for many optimisation problems.

Here we treat autoresearch itself as one of those problems. How to store and analyse experiments, what kind of reflection is most effective, to plan or random walk... these are all questions we aim to let an LLM test.


## How it works

There are two layers to the system:
* an inner **Scientist** agent runs the standard autoresearch cycle (editing `train.py`).
* an outer **Supervisor** that tweaks the Scientists environment (effectively `guidance.md`).


## Design choices

* **Supervisor over self-reflection**. Getting the scientist to edit it's own environment can too easily lead it to game the output; or worse, poor process choices could ruin it's entire future tradjectory. So you need an outer loop to verify the modifications work.
* **Multi-problem**. We found early on that the Supervisor wants to micro-manage and work as a Scientist, so we introduced a set of parallel Scientists working on different problems (not nanochat). This forces the Supervisor to work at a higher level. It also helps introduce a bit of replication robustness.
* **CPU over GPU**. Since we're not directly optimising nanochat here and instead are looking for universal principals we've opted for CPU friendly problems. See below.
* **Inner improvement only**. For the same reasons as above, we allow the Supervisor to only do a minimal amount of self-improvement via self reflection in the `/supervisor/` files (journal, ideas, and reflections).
* **Filesystem over git**. We've opted for storing previous iterations as files over git as it allows us to slightly easier manage what previous experiments are considered (as this is a multi-layered inception style system of iterations).
* **Invocation**. Scientists are explicitly called in parallel via a CLI as this was more robust than trying to get the Supervisor to spin up multiple parallel sub-agents. Similarly we use claude here because that's our subscription, but could add codex on request.
* **Minimal**. It's already a complex conceptual setup, so we've tried to not overengineer anything. We've only included two problems for generalisation & replication.
* **Human readability**. The only exception to this is breaking the learnings into three easier to consume files for the humans `ideas.md` and `reflections.md`, seperate from the `journal.md`.



## Project structure

Key files:

```
scientist/
    guidance.md     - on how to run the scientific process (viewed by all scientists, edited by supervisor)
    {problem}/
        train.py    - standard autoresearch, code written by Scientist
        prepare.py  - standard autoresearch, does evaluation etc.
        program.md  - now contains only very specific details about problem, guidance.md instructs flow
        memory.md   - Scientists are invoked per trial, so need a persistent store outside of their context
supervisor/
    studies.py      - runs a round of scientist studies (human-only edit)
    evaluate.py     - evaluates a study (human-only edit)
    method.md       - the program.md for the supervisor (human-only edit)
    journal.md      - chronological study log (supervisor views & edits)
    ideas.md        - ideas for improving scientists processes (supervisor views & edits)
    reflections.md  - ideas for improving supervisor processes (supervisor views & edits)
human/
    experiment.py   - starts the supervisor loop
    cli.py          - CLI command builder (abstracts Claude vs Codex)
    reset.py        - reset utilities for clearing experiment/study state
    shutdown.py     - kills all running scientist/experiment processes
```

The most interesting ones to review are `supervisor/journal.md`, `supervisor/ideas.md`, and `supervisor/reflections.md`.


## Problem experiments

Chosen problems:
- Graph colouring (gc)
- Quadratic assignment problem (qap)
- Maximum satisfiability (maxsat)
- Linear ordering problem (lop)
- Facility location, uncapacitated (facloc)

We chose these as we want:
- Cheap: to evaluate (CPU-friendly)
- Context contained: can be run in a single python file
- Hardware independant: scalar metric, not time based
- Continuous metric, not discrete jumps
- No LLM memorised dominant algorithm or well-known heuristic 
- Algorithmic diversity within time budget (this is the most important, is there huge room for creativity or just a single obvious path)
- Awkard tool use e.g. numpy to help but not much. Stops reliance on easy vectorization and instead invest in metaheuristics, smart neighborhood structures, or novel ways to evaluate "deltas".

## Quick start

Requires claude:

```bash
# 1. Install uv project manager (if you don't already have it)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. Install dependencies
uv sync

# 3. Make sure system is setup correctly
uv run pytest

# 4. Run the Supervisor to build on that
uv run experiment

# 5. Kill all running scientist/experiment processes
uv run shutdown
```


## Experimental setup learnings

- The Supervisor (& Scientists) really struggle with self-reflection. They tend to focus too much on the facts about what they did, rather than thinking about how they can change their own processes. This feels similar to how humans are poor at expressing their needs as JTBD. However, humans tend to be good at making concrete feature requests so we've enabled that pattern in `reflections.md`. _Maybe we should introduce a third product interviewer layer?_
- Scientists (like all agents) can often go off the rails. We found that ~70% of the token cost was from <5% of the runs. The smoking gun with all those runs was when they used the `TodoWrite` tool when the others didn't. So this is now off limits and we've added a max-budget.
- Similarly context rot / going off the rails is still a problem for Sonnet (which the Scientist uses), so we've bounded the Supervisor & Scientist to small invocations. This also forces the models to be deliberate about writing their learnings down.
- Surprisingly Haiku gives enough of a signal about what works. So has become the default Scientist, as we can run more studies in the same time, plus more parallel agents without destroying the token budget.
- Identical replications don't add enough value for their cost at this stage. We're not looking for statistical significance, we're playing at the boundary of simplicity & optimisation.
- Supervisor was reluctant to suggest anything radical like introducing a "MEMORY.md" even when heavily prompted. At first it was frustrating as limits the experimental evolution. But in retrospect it's great, as means we can pick up the requests from `reflections.md` and conciously add infrastructure complexity.
- Problem depth if everything. There needs to be a huge number of paths & gains to be had by the Scientists to get any sort of signal. But at the same time, not _too_ many otherwise you can't see any plateau and difference with the `guidance.md`.
- More tools (particularly numba) decreased creativity and optionality of paths of Scientists, so removed and kept dependancies small (like original autoresearch).
- TSP (Travelling Salesman Problem) was ditched as a problem as produced the worst signal. Despite having a vast theoretical optimisation landscape, it has a tiny *effective* landscape: LLMs converge to the same memorised dominant heuristic (nearest-neighbor + 2-opt) regardless of guidance, hitting a ceiling at ~0.20 improvement that doesn't vary. Large instances (needed to prevent trivial solving) consumed 90% of the time budget, leaving no room for algorithmic diversity. A "solved" problem with well-known optimal heuristics produces worse signal than a less famous problem where the LLM must genuinely explore. QAP, being less prominent in training data and having no single dominant algorithm has been far better.
- Gemini CLI just can't operate in this mode.


## Evaluation metrics

Each problem's `prepare.py` reports `avg_improvement` — the percentage gain over a weak baseline (greedy or identity permutation). This is the primary signal the Scientist optimises and the Supervisor compares across studies.

### Known limitations

- **Cross-problem scale mismatch.** Baselines vary in weakness (identity permutation for QAP/LOP vs crippled greedy for facloc/gc/maxsat), so raw values are incomparable across problems. A 62% on facloc and 17% on gc don't mean facloc is "more solved." Within a single problem across studies, the baseline is a constant so deltas are meaningful.
- **No optimality ceiling.** The metric shows distance from baseline, not proximity to optimal. A Scientist stuck at 62% can't tell whether the algorithm is near-optimal or the guidance is bad.
- **Nonlinear compression near ceiling.** Going from 60%→70% improvement is harder than 10%→20% because the remaining absolute gap shrinks. This compresses progress signals as the Scientist improves.

### Metric suite

Rather than replacing `avg_improvement`, we augment it with complementary signals:

**Per-trial** (in `results.tsv`):
- `avg_improvement` — quality signal, computed only over successful instances (failures excluded, not penalised)
- `success_rate` — fraction of instances producing valid results (reliability signal, separate from quality)
- `best_known.json` — persisted per-instance best-ever-seen, updated on each run when records are broken

**Per-study** (in `evaluate.py`):
- `improvement_velocity` — `(best - first) / num_trials`, how fast the Scientist learns
- `plateau_trial` — first trial where running best doesn't improve for 3+ consecutive trials
- `success_rate` trend — first vs last success rate shows whether Scientist learns to avoid crashes

**Ensemble-level** (for Supervisor, in `_aggregate` rows):
- `mean_headroom_captured` — `mean((new_best - old_best) / (1 - old_best))` per problem. Normalises cross-problem progress to a common scale: "what fraction of remaining potential did this guidance capture?"
- `problems_improved` — count of problems where guidance helped (breadth signal)
- `worst_problem_delta` — guard against guidance that helps some problems but hurts others
