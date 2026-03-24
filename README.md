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
experiment.py       - Starts the supervisor loop (human-only edit)
supervisor/
    studies.py      - runs a round of scientist studies (human-only edit)
    evaluate.py     - evaluates a study (human-only edit)
    method.md       - the program.md for the supervisor (human-only edit)
    journal.md      - chronological study log (supervisor views & edits)
    ideas.md        - ideas for improving scientists processes (supervisor views & edits)
    reflections.md  - ideas for improving supervisor processes (supervisor views & edits)
scientist/
    guidance.md     - on how to run the scientific process (viewed by all scientists, edited by supervisor)
    {problem}/      - subdirectories with autoresearch train.py, prepare.py, program.md, etc.
```

The most interesting ones to review are `supervisor/journal.md`, `supervisor/ideas.md`, and `supervisor/reflections.md`.


## Problem experiments

Chosen problems:
- Graph colouring
- Quadratic assignment problem (QAP)

We chose these as we want:
- Cheap: to evaluate (CPU-friendly)
- Context contained: can be run in a single python file
- Hardware independant: scalar metric, not time based
- Effective depth: large *effective* optimisation landscape under LLM + time constraints (not just theoretical landscape size)
- Continuous metric: fine-grained improvement signal with many achievable levels, not discrete jumps
- No memorised dominant algorithm: the LLM shouldn't be able to recall a single well-known heuristic that immediately solves the problem — it should need to genuinely explore
- Algorithmic diversity within time budget: multiple fundamentally different approaches must be viable within the solve time limit


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
```


## Experimental setup learnings

- The Supervisor (& Scientists) really struggle with self-reflection. They tend to focus too much on the facts about what they did, rather than thinking about how they can change their own processes. This feels similar to how humans are poor at expressing their needs as JTBD. However, humans tend to be good at making concrete feature requests so we've enabled that pattern in `reflections.md`. _Maybe we should introduce a third product interviewer layer?_
- Scientists (like all agents) can often go off the rails. We found that ~70% of the token cost was from <5% of the runs. The smoking gun with all those runs was when they used the `TodoWrite` tool when the others didn't. So this is now off limits and we've added a max-budget.
- Similarly context rot / going off the rails is still a problem for Sonnet (which the Scientist uses), so we've bounded the Supervisor & Scientist to small invocations. This also forces the models to be deliberate about writing their learnings down.
- Surprisingly Haiku gives enough of a signal about what works. So has become the default Scientist, as we can run more studies in the same time, plus more parallel agents without destroying the token budget.
- Identical replications don't add enough value for their cost at this stage. We're not looking for statistical significance, we're playing at the boundary of simplicity & optimisation.
- Problem depth if everything. There needs to be a huge number of paths & gains to be had by the Scientists to get any sort of signal. But at the same time, not _too_ many otherwise you can't see any plateau and difference with the `guidance.md`.
- More tools (particularly numba) decreased creativity and optionality of paths of Scientists, so removed and kept dependancies small (like original autoresearch).
- TSP was removed after 3 studies showed it produced the worst signal. Despite having a vast theoretical optimisation landscape, it has a tiny *effective* landscape: LLMs converge to the same memorised dominant heuristic (nearest-neighbor + 2-opt) regardless of guidance, hitting a ceiling at ~0.20 improvement that doesn't vary across guidance versions. Large instances (needed to prevent trivial solving) consumed 90% of the time budget, leaving no room for algorithmic diversity. A "solved" problem with well-known optimal heuristics produces worse signal than a less famous problem where the LLM must genuinely explore. QAP, being less prominent in training data and having no single dominant algorithm, produces far better guidance signal.
- Gemini CLI just can't operate in this mode.
