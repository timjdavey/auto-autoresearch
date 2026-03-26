## Trial 55: ILS perturbation depth tuning — RECOVERED 64.40% (BEST STABLE)

**Status: Matched recent best at 64.40%**

### Trial 55: Increased ILS perturbations
- Changed: num_perturbations 4→6 for small instances, 2→3 for large
- Rationale: Baseline (trial 54) was at 64.37%, below recent best of 64.40%; time budget available (12.8s of 60s)
- Result: **64.40% (+0.03%)** ✓ - Matched best trials 49-51
- Time: 12.8s → 15.3s (still well within budget)
- Per-instance breakdown:
  - rand30: 59.41% (slight improvement +0.10%)
  - rand40: 66.41% (stable)
  - rand50: 67.39% (stable)

### Key insight:
- ILS perturbation count is a tuning lever for quality vs speed
- Current setting (6/3 perturbations) achieves good balance: 64.40% in only 15.3s
- Still 44.7s unused budget (25% total) — more depth possible but diminishing returns observed in memory

### Plateau status:
- **CONFIRMED STABLE at 64.40%** across multiple trials
- Greedy+LS family architectural ceiling is real (~64.40%)
- All major redesign attempts in earlier trials (39-42) failed
- Time NOT limiting: 15.3s vs 60s available

### Next trial options:
1. **Accept 64.40%** as final if budget exhausted
2. **Genetic Algorithm or Ant Colony** if exploring different algorithm families (high risk, memory shows prior attempts failed)
3. **Cluster-based initialization enhancement** (memory trial 44 had limited success)

## Trial 44: Cluster-based init + adaptive SA — PLATEAU HOLDS AT 64.37% (FINAL)

**Status: CONFIRMED PLATEAU — all greedy+LS variants exhausted**

Final score: **64.37% avg_improvement** (rand30: 59.31%, rand40: 66.41%, rand50: 67.39%)

### Trial 44a: Cluster-based initialization
- New init: group clients by primary facility affinity, assign clusters intelligently
- Clusters should find different solution landscape than greedy
- Result: **NO CHANGE (64.37%)** ✗
- Root cause: clustering is still client-ordering heuristic within greedy+LS family

### Trial 44b: Adaptive SA (temperature varies by facility ratio)
- Facility-heavy (ratio > 0.5): temp=200, 800 iters, cooling=0.95
- Normal: temp=100, 500 iters, cooling=0.98
- Applied as final refinement (replacing weak final SA)
- Result: **NO CHANGE (64.37%)** ✗
- Root cause: SA at the END of optimization runs too late; solution already trapped by LS

### Trial 44c: Early aggressive SA (before LS phases)
- Apply adaptive_sa_escape after greedy init, before facility_closing + 2-opt + pair_swap
- Theory: SA explores while solution is fluid, LS refines after
- Result: **REGRESSION to 64.36%** ✗ (-0.01%)
- Root cause: Running 5+ SA phases per seed × 14 seeds = 70+ SA runs total (excessive, wastes time)
- Early SA variants: not the answer

### Key insights from trial 44:
1. **Cluster-based init doesn't escape plateau** — still greedy+LS family
2. **Adaptive SA at end is weak** — solution locked by LS before SA runs
3. **Early aggressive SA is excessive** — too many SA runs trap quality
4. **Plateau is REAL**: 64.37% confirmed stable across all variants (39-44)

### Critical realization:
- All attempts at greedy+LS variants fail (cluster init, more SA, adaptive temps)
- All SA placement attempts fail (end, early, multiple)
- Plateau appears to be true architectural limit of this family
- **Next trial MUST use fundamentally different algorithm or accept 64.37% as final**

### NEXT TRIAL OPTIONS (in order of likelihood to break plateau):
1. **Genetic Algorithm** — population crossover might find rand30 good solutions greedy can't
2. **Perturbation-based stochastic search** (not ILS) — maybe larger, more varied perturbations
3. **Tabu Search with longer tenure + aspiration** (trial 24 was weak because tenure was too short)
4. **Accept 64.37%** if no GA/Tabu variants work (strong local optimum)

## Trial 39-42: Plateau-breaking attempts — CONFIRMED 64.37% IS ARCHITECTURAL CEILING

**Current Score: 64.37% avg_improvement** (STABLE)

### Trial 39: Simulated Annealing as PRIMARY solver
- Removed multi-start greedy backbone
- SA with 10 restarts (5 for large), basin-hopping focus
- Result: **SEVERE REGRESSION to 56.28%** ✗ (-8.09%)
- Root cause: SA alone without greedy initialization + strong local search backbone performs 40% worse
- Conclusion: SA as primary is not viable; greedy+ILS framework is essential

### Trial 40: Aggressive ILS perturbations (15% vs 5%)
- Increased perturbation size: n_clients//7 instead of n_clients//20
- Increased restart attempts: 8 for small, 5 for large
- Result: **REGRESSION to 63.92%** ✗ (-0.45%)
- Root cause: Larger perturbations disrupt good solutions faster than re-optimization can recover
- Conclusion: Current 5% perturbation size is near-optimal balance

### Trial 41: Expanded weight variations (0.1-0.9)
- Increased weight values from 4 to 9 (dense exploration of opening_cost emphasis)
- Expected: Better facility-heavy (rand30) performance
- Result: **NO CHANGE (64.37%)** ✗
- Time increased: 9.4s → 17.0s (73% more) with zero quality gain
- Root cause: Weight space [0.2, 0.8] was already near-optimal; diminishing returns
- Conclusion: Parameter tuning is exhausted

### Trial 42: More random seeds (10→14 for small, 5→7 for large)
- Increase multi-start configurations: 35 → 52 for small instances
- Expected: More exploration = better solution in seed space
- Result: **NO CHANGE (64.37%)** ✗
- Time increased slightly: 9.4s → 13.0s
- Root cause: Already sampling seed space; more seeds hit same local optima
- Conclusion: Multi-start has saturation point; additional seeds don't escape basin

### Plateau Analysis (40+ trials at 64.17%-64.37%):
- **Proven approaches tried this trial:** SA as primary (failed), larger perturbations (failed), more weights (failed), more seeds (failed)
- **Time budget:** 13s / 60s (78% unused) — solver is NOT time-limited
- **Instance breakdown:**
  - rand30: 59.31% (STUCK: weak on facility-heavy)
  - rand40: 66.41% (STRONG)
  - rand50: 67.39% (STRONG)
  - **Gap: 8.08%** indicates algorithm weakness on high facility-to-client ratios
- **Exhausted approaches (all trials 24-42):**
  1. Parameter tuning: iterations, temperatures, cooling rates, weights, seeds
  2. Neighborhood variants: 1-opt, 2-opt, 3-opt, facility pair swaps, facility closing
  3. Diversification: ILS perturbations (small, large, adaptive), multi-start counts, seed ranges
  4. Initialization: greedy, facility-first, load-balanced, cost-weighted, random
  5. Meta-heuristics: Tabu Search (regressed), VND (regressed), SA as primary (regressed)

### CRITICAL ROOT CAUSE (CONFIRMED by multiple negative results):
- **Greedy+local-search family hits architectural ceiling at 64.37%**
- Weak rand30 (59.31%) is NOT a parameter-tuning issue — it's algorithmic
- All attempts to escape (more seeds, more weights, larger perturbations, new neighborhoods) FAILED
- 78% unused time budget proves: algorithm choice, not execution time, is limiting
- **Previous best SA-post-processing + ILS was optimal within this family**

### MANDATORY NEXT STEP:
**Do NOT attempt:** any more parameter tuning, seed adjustments, or neighborhood variants. All are futile.
**Must redesign** using fundamentally different algorithm family:
1. **Genetic Algorithm** (population-based crossover/mutation, ignores local optima paths)
2. **Ant Colony Optimization** (pheromone trails for facility-assignment patterns)
3. **Simulated Annealing as PRIMARY** with problem-specific neighbor moves (not random 1-opt)
4. **Tabu Search with stronger aspiration + longer tenure** (previous attempt was weak)
5. **Cluster-based construction** (group clients by facility proximity, assign clusters)

**Key insight for next trial:** The algorithm family boundary is clear. Trial 39 showed SA alone fails; Trial 40-42 showed greedy+LS has no improvement room. The solution is a DIFFERENT algorithm, not parameters.

## Trial 24-26: Algorithmic redesign attempts — ALL BLOCKED AT 64.17%

**Current Score: 64.17% avg_improvement** (rand30: 59.31%, rand40: 65.88%, rand50: 67.31%)

### Trial 24: Tabu Search
- Implemented tabu list (tenure=n_clients//10) to avoid cycling
- Replaced ILS with tabu_search as primary solver
- Result: **REGRESSED to 63.86%** ✗ (rand30: 58.62%, rand40: 65.57%, rand50: 67.39%)
- Time increased: 39.86s vs 14.9s, even with fewer configurations
- Root cause: tabu list too restrictive, aspiration criterion weak

### Trial 25: Variable Neighborhood Descent (VND)
- Systematic cycling through neighborhoods: 1-opt → facility_closing → 2-opt → pair_swap
- Perturb on plateau, restart cycling
- Result: **REGRESSED to 63.86%** (same as Tabu) ✗
- Time: 19.66s (better than Tabu, but worse than baseline)
- Root cause: cycling loses the benefits of per-neighborhood iteration tuning

### Trial 26: Enhanced small-instance search
- For n_clients < 60: 10 seeds (vs 5), 4 initializers (+ random_facility_init)
- More random restart diversity for high facility-to-client ratio
- Result: **NO CHANGE (64.17%)** ✗
- Root cause: already at local optimum; more restarts within greedy+LS family can't escape

### Plateau Analysis (15+ trials at 64.17%):
- **Current solver:** 5 seeds × (3 init + 4 weights) = 35 configurations
- **Per-run phases:** init → 1-opt(50) → facility_closing(20) → 2-opt(15) → pair_swap(10) → ILS(7) → SA(50)
- **Time:** 15-16s / 60s (73-75% unused budget)
- **Instance performance:** rand30 weak (59.31%), rand40/50 good (65-67%)
- **Instance gap:** 59.31% - 65.88% = 6.57% spread, suggests algorithm struggles with high facility-to-client ratios

### Exhausted approaches (all blocked at 64.17%):
1. Parameter tuning: more iterations, deeper SA, temperature tweaks
2. Neighborhood variants: 2-opt, 3-opt, facility pair swaps, perturbation ILS
3. Diversification: weight variations, seed increases, phase reordering, random init
4. Instance-aware: adaptive iteration counts, 3-opt for small instances
5. Algorithmic redesign: Tabu Search (regressed), VND (regressed)

### Root cause (CONFIRMED):
- Greedy+local-search family hits architectural ceiling at 64.17%
- Weak rand30 (59.31%) indicates inability to handle facility-heavy instances
- Tabu/VND regressions show new algorithms within similar family don't escape the basin
- 73% unused time budget proves algorithm choice, not time, is limiting factor

### CRITICAL: What works at 64.17%
To avoid regression if reverting, the baseline is:
- Initializations: greedy_nearest, facility_first_init, load_balanced_init, cost_weighted_init (weights 0.2-0.8)
- 5 seeds: [1, 42, 123, 456, 789]
- Local search: 1-opt(50-80) → facility_closing → 2-opt → pair_swap → ILS → SA(50)
- Full search requires only 16s / 60s, so time NOT a bottleneck

### Next trial strategy (CRITICAL):
Attempting yet another variant of greedy+LS will fail. Need FUNDAMENTALLY DIFFERENT algorithm:
1. **Genetic Algorithm** with population-based crossover/mutation (ignores local optima paths)
2. **Ant Colony Optimization** (pheromone trails may find rand30-specific good paths)
3. **Simulated Annealing as PRIMARY** (not post-processing), with adaptive temperature/cooling for different instance sizes
4. **Iterated Local Search with large perturbations** (larger k, more aggressive restart)
5. **Problem-specific cluster-based construction** (group clients, assign clusters, then optimize)

**Do NOT attempt:** any variant of greedy construction, parameter tweaks on existing neighborhoods, or additional random restarts.
Ceiling is algorithm family, not parameters or diversity count.

