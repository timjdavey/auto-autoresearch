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

---

## Study 2 (Plateau-breaking Diversification)
- **Date:** 2026-03-26
- **Hypothesis:** Study 1 showed all problems plateau by trial ~10–20. Guidance mentions diversification and mandatory protocols exist, but Scientists didn't aggressively explore algorithmic variants. Making plateau-breaking more concrete (with specific neighborhood examples, measurement protocols, and parameter ranges) will increase exploration and unlock improvements, especially for weak problems (QAP, LOP).
- **Changes to guidance.md:**
  1. Enhanced "Plateau detection & breaking" section with concrete examples:
     - Restart diversification: specific strategies (seed change, init swap, parameter adjustment)
     - Neighborhood variants: clarified 2-opt vs 1-opt, gave examples of how to measure impact
     - Root cause profiling: emphasized per-phase timing as the decision tool
  2. Added new "Neighborhood structure" section explaining:
     - What 1-opt, 2-opt, 3-opt neighborhoods are
     - When to use each (early vs mid vs late plateau)
     - How to measure impact (time vs quality trade-off)

#### Results Summary
- **Aggregate metrics:** 41.04% best avg_improvement (vs 39.79% Study 1, +1.25% gain)
- **Per-problem breakdown:**
  - facloc: 63.88% improvement (vs 64.18%, -0.30% regression)
  - maxsat: **98.61% improvement (vs 92.39%, +6.22% breakthrough) ✓✓✓**
  - gc: 18.95% improvement (vs 18.95%, 0% flat)
  - lop: **9.28% improvement (vs 9.62%, -0.34% regression) ✗**
  - qap: 14.48% improvement (vs 13.83%, +0.65% marginal)

#### Key Observations
1. **Divergence increased — red flag:** MaxSAT jumped +6% while LOP dropped -0.34%. This suggests guidance is not generic: it helps some problems but hurts others. The "Neighborhood Structure" section appears to help search problems (MaxSAT) but backfire on problems already using neighborhood variants (LOP).

2. **MaxSAT's breakthrough:** The new guidance on local search neighborhoods energized exploration. Scientists tried aggressive 2-opt/1-opt combinations, and WalkSAT-based algorithms gained ~6% improvement to reach 98.6%. This is a genuine insight: MaxSAT benefits from explicit, varied local search strategies.

3. **LOP's regression — root cause:** LOP memory.md shows the scientist attempted 2-opt/3-opt variations during Study 2 but got worse results (~9.3% vs prior best 9.6%+). The guidance encouraged trying neighborhoods already in the code; the scientist spent budget on parameter variations (1-opt iters, 2-opt iters) rather than fundamental redesign. This is a negative feedback loop: "try 2-opt variants" → "we already have 2-opt" → "adjust parameters" → worse.

4. **GC and FacLoc flat:** Both solid performers (19% and 64%) showed no response to the new guidance. They may be already well-optimized or the guidance didn't apply. No regression, but no breakthrough either.

5. **QAP marginal (+0.65%):** Weak improvement, and still has 10+ solver timeouts (rand75a). Time budget pressure remains the bottleneck.

6. **Trial counts reasonable:** All problems completed 49–72 trials with manageable error rates. No unexpected failures in harness execution.

#### Study 2 Conclusion
**Status:** Mixed results. Aggregate is up due to MaxSAT breakthrough, but LOP regression and GC/FacLoc stagnation reveal guidance is now problem-specific. The "Neighborhood Structure" section helps problems without pre-existing advanced neighborhoods (MaxSAT) but creates negative feedback for problems already exploring neighborhoods (LOP). Need to refine guidance to be truly generic or provide problem-specific branches.