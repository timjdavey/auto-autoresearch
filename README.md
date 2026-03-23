# auto-autoresearch
Autoresearching how to do autoresearch.

As we've seen it isn't just a great tool for optimising (NLM models)[https://github.com/karpathy/autoresearch/], but also an (excellent pattern)[https://x.com/tobi/status/2032212531846971413] for many optimisation problems.

Here we treat autoresearch itself as one of those problems. How to store and analyse experiments, what kind of reflection is most effective, to plan or random walk... these are all questions we aim to let an LLM test.


## How it works

Here we break this system into two:
* First we have multiple **Scientist** agents who run the standard autoresearch cycle (editing `train.py`).
* Then we layer a **Supervisor** on top to tweak the environment (i.e. `program.md`)

The process is:
* The Supervisor set up the "lab" for the scientist. Giving it `guidance.md` on _how_ to run the experiment (e.g. plan, do self-reflection, where to store memories etc).
* Very early we found the Supervisor to be a horendous micro-manager, so to combat this (and make sure the guidance was reasonably adaptable), we've set up three Scientists all working in parallel on different problems. The Supervisor then has to give exactly the same guidance to all, making sure it is generic and problem agnostic.
* Each scientist has a set number of **trials** to complete it's **study** and get the best possible results. The Supervisor reflects, learns and adapts the guidance.
* Then a new **campaign** of each study run in a loop.


## Project structure

We've grouped the files each agent uses by name

* `scientist/train.py` contains a `solve` function which the **Scientist** edits.
* `scientist/program.md` instructions for the **Scientist** to follow. This is edited by the **Supervisor**.
* `scientist/` will contain other files and tools e.g. MEMORY.md, dbsqlite, graph databases etc... Which the **Supervisor** will optimise.
* `scientist/prepare.py` evaluation framework. **Not modified (even by Supervisor to prevent gaming)**.
* `supervisor/method.md` instructions for the **Supervisor** to follow. **Not modified by Supervisor or Scientist.**
* `supervisor/study.py` runs a study. Supports `--trials N` (default 100) and `--timeout S` (default 600s per trial). **Not modified by Supervisor or Scientist.**


## Commands

To kick off the main Supervisor loop:
```
uv run human/campaign.py
```

To verify everything is working, run a short study (1 trial, sonnet by default):
```
uv run supervisor/study.py --trials 1
```


## Design choices

* **Optimisation rather than nanochat.** Our goal here isn't to improve deep-learning, it's to improve learning-learning. So we've had to introduce multiple optimisation problems. These were chosen to be CPU friendly over GPUs for hardware convience.
* **Inner improvement only.** In theory we should allow the Supervisor to incorporate the best studies into it's own learning process directly. But we want to avoid local optimas, so we'll only merge the best systems in periodically (for now). But it will do some self-improvement via self-reflection which gets stored in `/supervisor/journal.md`.
* **Filesystem over git.** We've opted for storing previous iterations as files over git because some of the files / tools are poor at coping with diffs and allows us to be able to slightly easier manage what previous campaigns we merge into the master learning branch (given this is a multi-layered inception type study).
* **Dependencies.** We introduced more tools than the original autoresearch, as we wanted the largest variance in discoverability & nuance in tooling to be tested, ((as we've seen with hardware)[https://blog.skypilot.co/scaling-autoresearch/]).
* **Evaluation.** In the future we'll want to give the Supervisor control over `prepare.py`, to tinker with the loss_functions etc, but for now that's too easy to game.
* **Invocation.** we've moved to calls to CLI as this was more reliable of a call then coaxing sub-agents.
* **Claude.** we've used claude because that's our subscription of choice, but codex versions of the cli could be built if interest.



## Inner experiment
Criteria:
- Cheap to evaluate
- Can be run in a single python file (for now)
- Hardware independant scalar metric
- Indefinite optimization landscape
- Existing benchmarks for comparison

Candidates:
- **TSP (traveling salesman)** (chosen)
- SAT solvers
- Sorting algorithms
- Compression enwik8
- Graph colouring (DIMACS)

Evaluation (two-tier):
- **Training** (`avg_improvement`, higher is better): Evaluated against 3 random instances (fixed seeds, no known optima). Measures percentage improvement over a nearest-neighbour baseline. Random instances prevent the LLM from memorising solutions.
- **Benchmark** (`avg_loss`, lower is better): Separately evaluated against 3 TSPLIB instances (berlin52, eil51, kroA100) with published optimal tour lengths. Measures percentage above optimal. Not part of the optimisation loop — provides an independent measure of progress against the TSP literature.
