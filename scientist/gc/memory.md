## Trial 31-35: Perturbation Tuning — Plateau at 18.77%

**Trial 31:** Diverse heuristics (DSATUR-sat/deg + random-greedy + lowest-degree-first)
- Result: 17.24% ❌ (DOWN from 18.77%)
- Insight: Weaker heuristics hurt ensemble; DSATUR-only is best

**Trial 32:** Aggressive perturbation (30 iterations, no time limit)
- Result: 18.97% ✅ (potential improvement)
- Problem: rand300e TIMEOUT ❌ (64.5s, over hard limit)

**Trial 33-34:** Time-aware perturbation (30 iters with 3s/1s safety margin)
- Result: 18.77% (tied, no improvement despite time awareness)
- Insight: Perturbation starts too late; DSATUR dominates time budget

**Trial 35:** Adaptive perturbation based on elapsed time
- 22 iterations if elapsed < 40s
- 10 iterations if elapsed 40-50s
- 3 iterations if elapsed > 50s
- Result: **18.77% stable** ✅ 100% success rate, safe timing
- rand300e: 54.2s (safe), rand300a: 41.4s (has budget), rand400a: 1.7s

**CONCLUSION: 18.77% is PRACTICAL CEILING**
- Theoretical max with 30 iters: 18.97%, but causes rand300e timeout
- Stable achievable: 18.77% with adaptive perturbation
- Bottleneck: rand300e density forces time-aggressive perturbation reduction
- Further improvement requires algorithmic redesign, not parameter tuning

## Trial 37+: Plateau-Breaking Attempts (all failed)

**Trial 37:** Selective 2-opt post-processing (3s time limit on best solution)
- Result: 18.77% (no improvement)
- Insight: 2-opt doesn't find better colorings; strong local optimum

**Trial 38:** Increased multi-start (100→150 runs)
- Result: 18.97% but **TIMEOUT** on rand300e
- Trade-off confirmed: can't safely push beyond 100 runs within 60s budget

**Trial 39:** Targeted perturbation (prioritize high-colored nodes)
- Result: 18.77% (no improvement)
- Insight: Random vs targeted perturbation equally ineffective

**Trial 40:** Hybrid 1-opt+2-opt in main loop (80 runs, 2-opt per iteration)
- Result: 18.77% (no improvement)
- Insight: 2-opt integrated into loop still finds no improvements

**Trial 42:** Degree-first ordering mix increased (25%→50%)
- Result: 17.06% ❌ (regression)
- Insight: Saturation-first is critical; degree-first too weak

**Trial 43:** Reduced num_runs 80→70, increased perturbation_rounds 22→25
- Result: 18.77% (tied) ✅ Faster (81s vs 89s)
- Insight: Budget rebalancing toward refinement doesn't help

**Trial 44:** Added 5 wildcard random-greedy runs + perturbation
- Result: 18.77% (tied) ✅ No regression
- Insight: Different initialization doesn't escape basin

**Trial 45:** Aggressive perturbation (30 rounds, tighter time thresholds)
- Result: 18.77% (tied, 89s execution)
- Insight: All perturbation variants reach same local optimum

**Trial 46:** Larger perturbations (uncolor 20-50% of nodes, was 10-30%)
- Result: 18.77% (tied) ❌ Slower (121s, timing degraded)
- Insight: Larger perturbations ineffective; likely worse recoloring opportunity

**PLATEAU CONFIRMED SOLID at 18.77% (18.772% in results):**
- Trials exhausted: 42 different approaches (45 trials total)
- All local search variants (1-opt, 2-opt, targeted, perturbed) exhausted
- All initialization variants (DSATUR mix, random greedy, degree ordering, node ordering tweaks) exhausted
- All perturbation parameters (size, intensity, timing, targeting) exhausted
- Time budget: optimal at 89s per evaluation
- **Strong local optimum confirmed:** DSATUR + 1-opt + perturbation is algorithmic ceiling under current family

## Next Trial: Major Algorithmic Redesign

**MANDATORY ACTION:** The plateau requires a fundamentally different algorithm, not parameter tuning.

Options to try (in order):
1. **Simulated Annealing (SA)** — probabilistic acceptance of worse solutions to escape local optima
2. **Iterated Local Search (ILS)** — larger perturbations with ILS framework
3. **Tabu Search** — forbidden moves to prevent cycling
4. **Genetic Algorithm (GA)** — population-based search
5. **Hybrid:** DSATUR construction (best current) + SA refinement

**Recommendation:** Try simple SA first:
- Start with current best solution (24 colors on rand300a)
- Use Metropolis acceptance: accept worse with probability e^(-Δcost/T)
- Decay temperature gradually
- Move set: 1-opt (reassign node to different color)
- Target: escape current 40-color barrier on rand300e

Current best: rand300e = 40 colors (18.37% improvement)
If SA can get 39 colors: that's +2.04% improvement → 18.77% + 2% ≈ 20%+ ensemble score
