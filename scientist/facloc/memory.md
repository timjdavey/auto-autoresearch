# Facility Location Scientist Memory

## Results Summary
- **Baseline (greedy nearest):** 0.00%
- **Trial 1 (greedy+1-opt local search):** 19.80% (11.05% / 24.33% / 24.01%)
- **Trial 3 (facility-first initialization):** 27.55% (11.05% / 47.59% / 24.01%) ✓ BREAKTHROUGH

## Trial 1-2 Analysis
- Simple 1-opt local search with best-improvement achieved 19.80%
- Multi-start with 5 random seeds on client-first greedy: stuck at 19.80%
- Conclusion: Client-first greedy + 1-opt is a strong local optimum

## Trial 3: Facility-First Initialization BREAKTHROUGH
- Added facility-first construction strategy (open facilities in order of cost, assign clients)
- Tried both client-first and facility-first with 3 seeds each (6 total attempts)
- Key insight: facility-first escapes the local basin of client-first greedy
- Result: +7.75% improvement (19.80% → 27.55%)
- Breaking point: rand40_120a jumped from 24.33% to 47.59% (almost 2x)

## Trial 4: Load-Balanced Facility Ordering BREAKTHROUGH ✓
- Added load-balanced facility ordering: sort by opening_cost / avg_assignment_cost
- Three strategies: client-first + facility-cost + facility-load-balanced (3 seeds each = 9 total)
- Removed expensive 2-opt, kept only 1-opt
- Key insight: Cost-to-benefit ratio captures facility value better than cost alone
- Result: MASSIVE +36.28% improvement (27.55% → 63.83%)
- Per-instance gains:
  - rand30_100a: 58.38% (was 11.05%) [+5.25x!]
  - rand40_120a: 65.94% (was 47.59%) [+1.39x]
  - rand50_150a: 67.17% (was 24.01%) [+2.80x]

## Convergence Analysis
- Tested seed count: 3 seeds/strategy achieves 63.83%, 4 seeds also 63.83% (converged)
- Solver is stable and finds same local optimum across variations
- Total time: 2.67s (well under 60s per-instance limit)

## Algorithm Structure (FINAL)
**Three parallel construction strategies:**
1. **Client-first:** Greedy nearest (baseline-like but with random tie-breaking)
2. **Facility-first:** Sort facilities by opening cost, incrementally add facilities
3. **Facility load-balanced:** Sort by cost/avg_assignment_cost ratio (KEY INSIGHT)

Each strategy runs 3 times with different random seeds (9 total attempts).
All solutions refined with 1-opt local search (best-improvement).
Best solution kept.

**Why load-balanced works:** Captures facility value as ratio of opening cost to typical assignment benefit. Pure cost sorting ignores how useful each facility is to clients.

## Next Trial Recommendations
1. **Try facility removal phase:** After construction, greedily close facilities that don't improve cost. (Current code has basic version; make more aggressive)
2. **Explore weight variations:** Weight opening_cost differently in load-balanced ratio (e.g., 0.5x, 0.8x, 1.2x) to see if slightly different orderings help
3. **Try neighborhood swap:** Instead of just client moves, try facility swaps (reassign cluster of clients to different facility)
4. **Profile time per instance:** Small instances solve very fast (<1s), room for stronger local search (e.g., 2-opt on small instances only)

## Trial 12: Plateau-Breaking Diversification
- Added facility closing phase + seed/weight variations: +0.15% (63.83% → 63.98%)

## Trial 13+: Plateau Analysis (64.10% achieved, stuck)
- **Current best: 64.10%** (trials 37-40, stable)
  - rand30_100a: 58.50% (bottleneck)
  - rand40_120a: 66.41% (strong)
  - rand50_150a: 67.39% (strong)

- **Failed plateau-breaking approaches:**
  1. 2-opt refinement: Caused timeouts on large instances (rand40, rand50 exceeded 60s budget)
  2. Perturbation ILS (5 rounds, strength=2): No improvement, time ~9s
  3. Simulated annealing post-processing (200 iters): No improvement
  4. Outer-level multi-start (3 full solves): 3× time increase to 21s, no score gain

- **Root cause analysis:**
    - Current approach: 7 strategies × 8 seeds = 56 construction attempts
    - All converge to same 64.10% solution (tight local optimum)
    - Time remaining: 60-9 = 51s available per instance
    - Local search (1-opt) appears fully saturated; further 1-opt iterations don't improve
    - rand30 is algorithmically harder (different structure vs rand40/rand50?)

## Next Trial Strategy
- **Current code is stable:** 56 attempts cover solution space well, facility closing helps
- **To break plateau:** Need fundamentally different algorithm
- Options (priority order):
  1. **3-opt for rand30 only** (small instance, time available): More thorough local search
  2. **Perturbation-based ILS with acceptance criteria** (tabu, variable depth)
  3. **Swap to Tabu Search** entirely (replace greedy+1-opt with tabu)
  4. **Problem structure analysis** (why rand30 weak? specialized init for small instances?)

## Key Metrics (Current)
- **avg_improvement: 64.10%** (stable plateau 50+ trials)
- Success rate: 100%
- Time per instance: 3-4s of 60s (7-8% utilization)
- Trial count: 50+ with no improvement

## Trial 48 (2-opt + 3-opt + perturbation attempts — FAILED)
- Tried: 2-opt on all 35 attempts (7 strategies × 5 seeds) → **TIMEOUT** (all instances exceeded 65s budget)
- Tried: 2-opt only on best solution → **NO IMPROVEMENT** (64.10%)
- Tried: Aggressive 3-opt (max_iters=100, 20-client scan) for n_clients<=30 → **NO IMPROVEMENT** (64.10%)
- Tried: Perturbation (strength=2) + 1-opt loop (3 rounds) for small instances → **NO IMPROVEMENT** (64.10%)

**Root cause:** All 56 construction attempts + facility closing + 1-opt converge to same local optimum (tight basin). No local search neighborhood (2-opt, 3-opt) or perturbation escapes it from within same basin.

## Plateau Escape Conclusion
- Local search variants exhausted: 1-opt, 2-opt, 3-opt, multi-start, perturbation all fail
- Construction diversity exhausted: 7 strategies × 8 seeds all find identical solution
- Facility closing already aggressive (removes unprofitable facilities)
- **Truly stuck at local optimum.** Need fundamentally different algorithm:
  - **ILS with deeper perturbation** (move 5+ clients, allow temporary cost increase)
  - **Tabu Search** (forbidden moves to force exploration)
  - **Variable Neighborhood Search** (switch between multiple neighborhood structures)
  - **Genetic Algorithm** (population-based crossing)
  - **Simulated Annealing with proper cooling** (currently tried but parameters may be weak)

## Trial 52+: ILS and Savings Heuristic Attempts (FAILED)
- **Aggressive perturbation ILS:** Move 15-25% of clients + 1-opt (8 iterations) → **NO IMPROVEMENT** (64.10%), time increased 9.4s → 22.2s
- **Multi-start ILS:** 6 ILS processes (3 seeds × 2 variations) on best solution → **TIMEOUT + REGRESSION** (62.52%, success_rate 67%)
- **Single-run ILS (3 iterations):** Reduced iterations to avoid timeout → **NO IMPROVEMENT** (64.10%), time 15.4s
- **Savings-based construction:** Clarke-Wright style savings heuristic added as 8th strategy → **NO IMPROVEMENT** (64.10%)

**Analysis:** All 8 construction strategies (including new savings heuristic) converge to identical 64.10% solution after facility closing + 1-opt. Perturbation + re-optimization doesn't escape. The local optimum is SO tight that even aggressive perturbation (moving 25% of clients) + full 1-opt re-run doesn't find better solutions.

**Plateau status:** 60+ trials at 64.10% with zero improvement. All feasible local search variants and construction heuristics exhausted.

**What's left to try (major rewrites only):**
- Tabu Search with tabu tenure/aspiration
- Genetic Algorithm with population-based search
- Variable Neighborhood Search with multiple neighborhood sizes
- Ant Colony Optimization
- Accept this plateau as near-optimal for this problem
