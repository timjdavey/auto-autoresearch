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
* **Minimal**. It's already a complex conceptual setup, so we've tried to not overengineer anything. We've only included two problems to solve for generalisation & replication, but trying to keep it at only two.
* **Agency**. Similarly starting with just one memory file for the Supervisor and no memory files (similar to autoresearch) aims to give the Supervisor the highest agency it can explore the space on it's own. Likewise for `train.py` in the inner cycles.

## Project structure

Key files:

```
experiment.py       - Starts the supervisor loop (human-only edit)
supervisor/
    studies.py      - runs a round of scientist studies (human-only edit)
    evaluate.py     - evaluates a study (human-only edit)
    method.md       - the program.md for the supervisor (human-only edit)
    journal.md      - a scratchpad of ideas and memories (supervisor views & edits)
scientist/
    guidance.md     - on how to run the scientific process (viewed by all scientists, edited by supervisor)
    {problem}/      - subdirectories with autoresearch train.py, prepare.py, program.md, etc.
```

The most interesting one to review is `supervisor/journal.md`.


## Problem experiments

Chosen problems:
- Traveling salesman problem (TSP)
- Graph colouring (DIMACS)

We chose these as we want:
- Cheap: to evaluate (CPU-friendly)
- Context contained: Can be run in a single python file
- Hardware independant: so scalar metric ideally not time based
- Indefinite: optimization landscape for high discoverability variance


## Commands

Run a full experiment (default 5 studies, opus):
```
uv run experiment
uv run experiment --studies 3 --model sonnet
```

## Quick start

Run tests:
```
uv run pytest
```

