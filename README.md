# auto-autoresearch
Autoresearching autoresearch. Let's optimise how an LLM does autoresearch! It's autoresearch all the way down.

## How it works

There are two research layers.
* `inner`: edits `train.py` like a standard autoresearch cycle.
* `outer`: this now a meta researcher which `program.md` and related tools in the `lab/` folder.

Key files:

* `prepare.py` this is still the evaluation framework etc. **Not modified (even by outer to prevent gaming)**. Placed outside of lab to avoid confusion.
* `lab/train.py` contains a `solve` function which the **inner agent** edits.
* `lab/record.py` tools to record how the hypotheses, learnings and results are stored. This is edited by the **outer agent**.
* `lab/program.md` instructions for the **inner agent** to follow. This is edited by the **outer agent**.
* `lab` will contain other files and tools e.g. MEMORY.md, dbsqlite, graph databases etc... Which the **outer agent** will optimise.

## Design choices

* **Optimisation over nanochat.** Our goal here isn't to improve deep-learning, it's to improve learning-learning. So we've swapped out `train.py` to an inner experiment which is cheaper and faster to evaluate. This is so each run of the _entire autoresearch loop_ can be kept within a similar small time budget.
* **Dependencies.** Have been kept to a minimum initially to keep things sane. But the more tools (incl coding languages) it has available the better it can optimise ((as we've seen with hardware)[https://blog.skypilot.co/scaling-autoresearch/]).
* **Evaluation.** In the future we'll want to give the outer loop control over `prepare.py`, to tinker with the loss_functions etc, but for now that's too easy to game. So we've locked this off until guardrails can be put in place. For the same reason, `prepare.py` contains the evaluation calls rather than `train.py`.
* **Inner improvement only.** In theory we should allow the outer loop to incorporate the best runs from the inner loop directly. But we want to avoid local optimas, so we'll only merge the best systems in periodically (for now).


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