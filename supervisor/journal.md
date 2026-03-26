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

---

### Study 3 (Adaptive Neighborhood Guidance & Timeout Focus)
- **Date:** 2026-03-26
- **Hypothesis:** Study 2 showed that generic "try 2-opt" guidance backfires for problems that already use 2-opt. Solution: make neighborhood guidance conditional on solver state. Add a CRITICAL CHECKPOINT: "Check if you already use 2-opt. If yes, skip to initialization diversity and timeout management instead." This preserves MaxSAT's breakthrough path while redirecting LOP/QAP toward initialization diversity (multi-seed, greedy variants) and timeout/phase profiling — strategies that work better for problems with tight time budgets.

- **Changes to guidance.md:**
  1. **Neighborhood structure section — CONDITIONAL:** Added checkpoint at top: "Are you already using 2-opt? If yes, skip to initialization diversity." Prevents negative feedback loops.
  2. **New section: "Initialization diversity & timeout management":** For problems with advanced neighborhoods, redirects toward multi-seed restarts, greedy variants, and phase profiling (which showed +10–15% in prior studies). Emphasizes that tweaking neighborhood iteration parameters is waste if the neighborhood itself isn't the bottleneck.
  3. **Clarified when to suggest what:** "Already using advanced neighborhoods and still stuck? Don't tweak their parameters. Instead, try initialization diversity or timeout/phase restructuring."

#### Results Summary
- **Aggregate metrics:** 40.41% best avg_improvement (vs 41.04% Study 2, -0.63% regression)
- **Per-problem breakdown:**
  - facloc: 64.50% improvement (vs 63.88%, +0.62% marginal improvement)
  - maxsat: **94.38% improvement (vs 98.61%, -4.23% MAJOR REGRESSION) ✗✗✗**
  - gc: **20.51% improvement (vs 18.95%, +1.56% improvement) ✓**
  - lop: 9.23% improvement (vs 9.28%, -0.05% flat)
  - qap: 13.41% improvement (vs 14.48%, -1.07% regression)

#### Key Observations
1. **Conditional checkpoint FAILED — MaxSAT crashed:** The new conditional checkpoint in "Neighborhood Structure" section broke MaxSAT's winning path. MaxSAT dropped 4.23% (98.61% → 94.38%), the largest single-study regression so far. Likely cause: the checkpoint caused Scientists to skip over neighborhood exploration that MaxSAT was successfully using.

2. **Initialization diversity redirect didn't help weak problems:** LOP and QAP both regressed or stayed flat. QAP -1.07%, LOP -0.05%. The redirect toward "multi-seed and phase profiling" didn't generate improvements. Possible reason: Scientists may have misunderstood the conditional guidance or attempted redirected strategies without sufficient depth.

3. **GC improved (+1.56%) — signal from somewhere:** GC is the only problem showing strong improvement. However, GC also ran only 33 trials (vs 50–56 in prior studies), suggesting either earlier convergence or harness variation.

4. **Solver errors across all problems:** Multiple crashes in FacLoc (2 errors), GC (2 errors), LOP (1 error), MaxSAT (1 error), QAP (multiple timeouts). This suggests the guidance changes may have caused Scientists to attempt configurations the solvers couldn't handle.

5. **Trial counts unstable:** GC dropped to 33 trials, suggesting early termination or different exploration patterns. Other problems stayed in expected range (47–64 trials).

#### Study 3 Conclusion
**Status:** FAILED. Aggregate regression -0.63%, MaxSAT catastrophic drop -4.23%. The conditional checkpoint strategy backfired. Making neighborhood guidance conditional didn't preserve MaxSAT's path; instead, it disrupted it. The redirect toward initialization diversity/timeout management didn't help LOP or QAP either. The guidance is now problematic: overly complex with conditional branches that confuse rather than clarify. Revert to simpler, more direct guidance and reconsider the approach.