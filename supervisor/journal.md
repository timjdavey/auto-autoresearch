# Journal

A chronological log of studies — one entry per study, recording what changed, what happened, and what you learned. Write each entry during the post-study review (see method.md § "Study reflection").

## Study log

### Study 1 (Baseline)
- **Date:** 2026-03-25
- **Changes:** None. Unmodified baseline to establish baseline performance and validate experimental harness.
- **Rationale:** First study runs with stock guidance to measure: (1) harness correctness, (2) baseline solver performance, (3) trial count adequacy.

#### Results Summary
- **Aggregate metrics:** 39.79% best avg_improvement, 53 trials average, 0% error rate
- **Per-problem breakdown:**
  - facloc: 64.18% improvement (49 trials, excellent trajectory)
  - maxsat: 92.39% improvement (49 trials, outstanding progress)
  - gc: 18.95% improvement (51 trials, 1 timeout early, recovered)
  - lop: 9.62% improvement (62 trials, 2 timeouts, struggled to escape)
  - qap: 13.83% improvement (55 trials, flat improvement, weak signal)

#### Key Observations
1. **Harness correctness:** Errors handled cleanly (solver_error logged, studies continued), timeouts caught properly.
2. **Trial adequacy:** 49–62 trials sufficient for baseline, though lop needed extra budget to recover from crashes.
3. **Divergence signal:** 64% (facloc) → 9% (lop) spans 7× range, suggesting:
   - Either problems have fundamentally different solvability profiles
   - Or generic guidance is insufficient for some problems
   - Baseline study cannot distinguish yet; more data needed after guidance refinement.
4. **All problems plateau:** Every problem shows tailing off (plateau_trial 3–13, longest_plateau 15–30 trials), indicating local optima were reached in first ~60% of budget.
5. **Solver coverage:** All five problems have reasonable solvers (greedy/heuristic + local search). No obvious omissions detected.

#### Guidance Assessment
- Memory.md protocol worked: Scientists recorded decisions and bottlenecks.
- Time profiling guidance followed: Most solvers have explicit time budgets (lop, maxsat set 55s).
- Plateau detection language was read but **not aggressively acted on** — scientists continued same algorithms rather than forcing diversification. This is expected in a baseline with unrefined guidance.

#### Study Conclusion
**Status:** Baseline valid and useful. Harness works, trial counts adequate, guidance understood. All five problems executed cleanly with expected variance. Ready for Study 2 refinement.