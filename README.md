# auto-autoresearch
Autoresearching autoresearch. Let's optimise how an LLM does autoresearch! It's autoresearch all the way down.

## How it works

There are two layers.
* inner loop: a **Scientist** agent edits `train.py` like the standard autoresearch cycle. Runs trials.
* outer loop: a **Supervisor** meta-researcher optimises `program.md` and related tools in the `lab/` folder to improve how the Scientist runs its studies.


## Taxonomy

| Term | Definition |
|------|-----------|
| **Supervisor** | The outer agent. Meta-optimizer that tunes `lab/` and `program.md` |
| **Scientist** | The inner agent. Modifies `train.py` to improve the TSP solver |
| **Trial** | One experiment cycle: edit the solver, evaluate, keep or revert |
| **Study** | A full series of trials in one invocation of the Scientist |
| **Campaign** | A series of iteratively improving studies, executed by the Supervisor |


## Project structure

* `lab/train.py` contains a `solve` function which the **Scientist** edits.
* `lab/program.md` instructions for the **Scientist** to follow. This is edited by the **Supervisor**.
* `lab` will contain other files and tools e.g. MEMORY.md, dbsqlite, graph databases etc... Which the **Supervisor** will optimise.
* `prepare.py` evaluation framework. **Not modified (even by Supervisor to prevent gaming)**. Placed outside of lab to avoid confusion.
* `method.md` instructions for the **Supervisor** to follow. **Not modified by Supervisor or Scientist.**
* `study.py` runs a study. Supports `--trials N` (default 100) and `--timeout S` (default 600s per trial). **Not modified by Supervisor or Scientist.**


## Quick test

To verify everything is working, run a short study (1 trial, sonnet by default):
```
python study.py --trials 1
```

To test with opus:
```
python study.py --trials 1 --opus
```


## Design choices

* **Optimisation over nanochat.** Our goal here isn't to improve deep-learning, it's to improve learning-learning. So we've swapped out `train.py` to an inner experiment which is cheaper and faster to evaluate. This is so each study can be kept within a similar small time budget.
* **Dependencies.** Have been kept to a minimum initially to keep things sane. But the more tools (incl coding languages) it has available the better it can optimise ((as we've seen with hardware)[https://blog.skypilot.co/scaling-autoresearch/]).
* **Evaluation.** In the future we'll want to give the Supervisor control over `prepare.py`, to tinker with the loss_functions etc, but for now that's too easy to game. So we've locked this off until guardrails can be put in place. For the same reason, `prepare.py` contains the evaluation calls rather than `train.py`.
* **Invocation.** `study.py` is locked to prevent the Supervisor from dangerously-skipping-permissions.
* **Inner improvement only.** In theory we should allow the Supervisor to incorporate the best studies into it's own learning process directly. But we want to avoid local optimas, so we'll only merge the best systems in periodically (for now).
* **git.** We avoid git as the archive system because we're possibly dealing with filetypes which aren't easily diff'd (e.g. sqlite) & there's no point running experiments parallel from a learning perspective.


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
