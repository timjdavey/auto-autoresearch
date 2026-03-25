# MAX-SAT Solver Trials

## Trial 056: Rebalanced WalkSAT—Reduced runs + Ultra-cheap 3-opt
**Result: 98.61% avg_improvement** (rand200a: 100%, rand250a: 100%, rand300a: 95.83%)
**Status: Recovered to plateau level after time management adjustment**

**Key changes:**
1. **Reduced WalkSAT restarts** for large instances (n_vars > 250): 57 → 45 runs
   - Frees ~10% time budget from init diversity for refinement
   - Still maintains good exploration via multiple starting points
2. **Increased max_iterations per run** for large instances: 160k → 450k
   - Redirects freed time into more WalkSAT iterations (more effective than expensive refinement)
3. **Ultra-cheap 3-opt for medium instances** (n_vars ≤ 250):
   - Only top 3 critical variables (vs 15 before)
   - Only examines 1 triplet max: C(3,3) = 1
   - Unlocked rand250a 100% (was stuck at 96.77%)
4. **Skipped 2-opt and 3-opt for large instances** (n_vars > 250)
   - rand300a still hits 55s limit; no time for refinement
   - Better to spend time in WalkSAT main loop

**Time profile:**
- rand200a: ~11.7s (10.3MB main loop + 1.4s refinement)
- rand250a: ~20.8s (perfectly solved with cheap 3-opt)
- rand300a: ~55.0s (timeout-bound at 2 unsat)

**Algorithm summary (WalkSAT + selective refinement):**
1. Multi-start WalkSAT (45 runs for large, 50-80 for small/medium)
   - Weighted clause selection with dynamic weights
   - Adaptive walk probability
   - Escape perturbations when stuck
   - Increased iterations for large instances
2. 1-opt hill climbing (2 passes, all variables)
3. 2-opt for small/medium (n_vars ≤ 250): variable pairs in unsatisfied clauses
4. Ultra-cheap 3-opt for small/medium: top 3 critical variables only

**Plateau analysis:** Trial 055 achieved 98.61% with heavier 3-opt (top 15 vars). This trial maintains 98.61% with lighter approach: time management (fewer runs + more main loop iterations) + cheap 3-opt still sufficient for medium instances.

**Current bottleneck:** rand300a. Time-limited at 55s, achieving 95.83%. To break this plateau would require:
- Faster WalkSAT implementation (JIT, vectorization)
- Different heuristic (e.g., Tabu Search instead of WalkSAT + local search)
- Or accept this as the ceiling for current algorithm under 60s constraint

## Previous Trial 055:
98.61% with heavier 3-opt (top 15 critical vars)
