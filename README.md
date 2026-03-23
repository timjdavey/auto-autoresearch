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
* **Inner improvement only**. For the same reasons as above, we allow the Supervisor to only do a minimal amount of self-improvement via self reflection in the `/supervisor/journal.md` file.
* **Filesystem over git**. We've opted for storing previous iterations as files over git as it allows us to slightly easier manage what previous experiments are considered (as this is a multi-layered inception style system of iterations).
* **Invocation**. Scientists are explicitly called in parallel via a CLI as this was more robust than trying to get the Supervisor to spin up multiple parallel sub-agents. Similarly we use claude here because that's our subscription, but could add codex on request.


## Project structure

### `scientist/` — Inner agents

Each problem lives in its own subdirectory (e.g. `tsp/`, `graph_colouring/`):
* `{problem}/train.py` contains a `solve` function which the **Scientist** edits.
* `{problem}/prepare.py` evaluation harness. **Not modified (even by Supervisor to prevent gaming).**
* `{problem}/program.md` problem-specific instructions for the **Scientist**. **Not modified by agents.**
* `{problem}/results.tsv` auto-written trial results.
* `{problem}/archive/` trial snapshots and baseline (`original.py`).
* `{problem}/baselines/` benchmark instances.
* `guidance.md` shared research methodology guidance, edited by the **Supervisor**.

### `supervisor/` — Outer agent

* `studies.py` runs a study: trials across all problems in parallel. **Not modified by agents.**
* `evaluate.py` post-study analysis: reads results, computes stats. **Not modified by agents.**
* `method.md` instructions for the **Supervisor**. **Not modified by agents.**
* `journal.md` the **Supervisor's** persistent self-reflection journal.
* `study_results.csv` aggregated cross-study results (auto-written by `evaluate.py`).

### Root — Orchestration (human-only)

* `experiment.py` runs a full experiment: multiple Supervisor studies in sequence. **Not modified by agents.**


## Commands

Run a full experiment (default 5 studies, opus):
```
uv run experiment
uv run experiment --studies 3 --model sonnet
```

Run a single study (default 100 trials, sonnet):
```
uv run study --trials 5
```

Evaluate the current results:
```
uv run evaluate
```

Run tests:
```
uv run pytest
```


## Problem experiments

Chosen problems:
- Traveling salesman problem (TSP)
- Graph colouring (DIMACS)

We chose these as we want:
- Cheap: to evaluate (CPU-friendly)
- Context contained: Can be run in a single python file
- Hardware independant: so scalar metric ideally not time based
- Indefinite: optimization landscape for high discoverability variance
