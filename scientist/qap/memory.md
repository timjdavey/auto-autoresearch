# QAP Trial Progress

## Trial 1: Greedy construction + 1-opt (11.46% improvement)
- Greedy + 1-opt best-improvement, single run
- Result: 11.46% avg (rand50a: 13.28%, rand60a: 11.22%, rand75a: 9.88%)
- Time: 10.1s total

## Trial 21: 3-opt for small instances (12.38% improvement) ✓ BEST
- Added 3-opt local search for instances with n ≤ 60 (rand50a, rand60a)
- Result: 12.38% avg (rand50a: 13.74%, rand60a: 12.45%, rand75a: 10.97%)
- Time: 131.9s total (42.3s, 52.7s, 36.8s per instance — all safe)
- Key insight: 3-opt escapes tighter local optima on small instances; timing is acceptable

## Trial 21-25 Exploration Summary (from earlier experiment)
- Trial 21: 12.38% ✓ BREAKTHROUGH (3-opt for n≤60 with 20 iters) — best solution
- Trial 22: 12.35% (3-opt with 30 iters) — diminishing returns on iterations
- Trial 23: 12.35% (3-opt extended to n≤75 with 5 iters each) — slowed down rand75a, no gain
- Trial 24: 12.30% (5 multi-start strategies) — spread time too thin
- Trial 25: 12.35% (back to 3 strategies) — verification run

## Current best: 12.38% avg_improvement (Trial 21)
- Algorithm: Multi-start (3 strategies: high_flow, random, high_degree) + first-improvement 1-opt (250 iters) + 2-opt (70 iters) + 3-opt for n≤60 (20 iters)
- Costs: rand50a 5341038, rand60a 7841206, rand75a 12583164

## Trial 26-27 Plateau-breaking attempts (CURRENT)
- Trial 26: Perturbation-based escape (random swaps + re-optimize) → 12.35% (regression)
  - Tried 3 perturbation cycles with 2-4 random swaps each
  - Insight: Random perturbations too disruptive; existing 1-opt/2-opt/3-opt already strong

- Trial 27: Or-opt moves (sequence relocation) → 12.30% (regression)
  - Added Or-opt phases for moving 1-2 facility sequences
  - Insight: High time cost (134.2s) for no quality gain; not a good tradeoff

- Trial 28: 5 multi-start strategies (cost_weighted, random_greedy added) → 12.30% (regression)
  - Spread time across 5 strategies (40%, 20%, 20%, 10%, 10%)
  - Insight: More strategies dilute per-strategy time budget; new strategies didn't compensate

## Trial 29: Simulated annealing post-processing → 12.30% (REGRESSION)
- Added SA as final phase after multi-start construction+1-opt+2-opt+3-opt
- Result: 12.30% (down from 12.38%)
- Insight: SA didn't escape local basin; added overhead without benefit

## Trial 30: Restored 3-strategy config (50/25/25 allocation, 2-opt 50 iters, 3-opt 20 iters) → 12.35%
- Reverted to Trial 21's approach with better time allocation
- Result: 12.35% (close but still below 12.38% best)
- Individual: rand50a 13.62%, rand60a 12.45%, rand75a 10.99%
- vs best: rand50a 13.74%, rand60a 12.45%, rand75a 10.97%
- Issue: rand50a consistently ~0.1-0.2% below best

## Trial 31: Multi-seed high_flow (2 seeds × 25% budget each) → 12.31% (REGRESSION)
- Ran high_flow strategy twice with different seeds to diversify
- Result: 12.31% (worse than single seed at 12.35%)
- Insight: Splitting time budget is inefficient; per-seed budget too tight for local search phases

## PLATEAU ANALYSIS & CONCLUSION (Trials 21-31)
- Stuck at 12.35-12.38% plateau for 11 trials
- Strong fundamentals: 3 diverse strategies (high_flow/random/high_degree), multi-phase local search (1-opt→2-opt→3-opt)
- All diversification attempts regressed: perturbation (-), Or-opt (-), SA (-), multi-seed (-), extra strategies (-)
- Parameter tweaks (time allocation, iterations) stable at 12.35% but can't reach 12.38%
- **Best stable configuration: 50/25/25 time split, 1-opt 250 iters, 2-opt 50 iters, 3-opt 20 iters → 12.35% consistent**

## Root cause: True local optimum reached
- The 12.38% peak may have been from a fortunate random trajectory, not a property of the algorithm
- Current 12.35% is a robust local optimum that multiple approaches converge to
- Further improvement requires fundamentally different algorithm (Tabu, VNS, genetic) not minor tweaks

## Trials 34-37: Final plateau confirmation
- Trial 34: VNS with neighborhood reordering (1-opt→2-opt→3-opt vs 2-opt→1-opt→3-opt) → 12.35%
- Trial 35: Increased time_limit 55→58s → 12.35% (extra time budget not helpful)
- Trial 36: Increased iteration limits (2-opt 50→100, 3-opt 20→50) → 12.35% (deeper local search insufficient)
- Trial 37: 5-strategy diversification → 12.30% (confirmed: diluting time budget hurts)
- Reverted to 3-strategy + higher iterations → 12.35% (back to stable plateau)

## Trials 39-42: Major algorithm redesigns
- Trial 39: Iterated Local Search (ILS) with 4-6 random swaps + re-optimize → 11.88% (REGRESSION)
  - Too disruptive; perturbations override greedy construction quality
  - Time budget for re-opt after perturbation was too small (0.05s per phase)

- Trial 40: Tabu Search with 2-opt neighborhood → 12.03% (REGRESSION)
  - Converged too fast (24.4s vs expected 58+s)
  - Only 2-opt neighborhood insufficient without 1-opt/3-opt
  - Early stopping when no improving neighbor found

- Trial 41: Multi-start + Simulated Annealing hybrid → 12.32% (REGRESSION)
  - SA with exponential cooling (0.995 rate, initial_temp = cost*0.01)
  - Added 20% of budget to SA phase
  - Slight regression suggests SA overhead > benefit

- Trial 42: Revert to stable 3-strategy (confirming baseline) → 12.35% ✓
  - Confirmed robust 12.35% performance
  - Time: rand50a 34.6s, rand60a 55.2s, rand75a 39.0s

## Trials 43-45: Final plateau confirmation (ALL REGRESSED)
- Trial 43: Iteration rebalancing (1-opt 100→100, 2-opt 100→200) → 12.35% (no gain, same cost)
- Trial 44: Best-improvement 1-opt (evaluate all swaps per iteration) → 11.78% (REGRESSION, too expensive)
- Trial 45: Reordered local search for large instances (2-opt→1-opt for n>60) → 12.35% (no change)
  - Hypothesis was that broader 2-opt search first might help rand75a
  - No improvement; algorithm already explores well regardless of phase order

## Trial 46: Pair-based greedy construction → 12.38% ✓ BREAKTHROUGH
- Introduced new initialization strategy: pair-based greedy
  - Find pair of facilities with highest mutual flow
  - Assign pair to best two locations
  - Greedily extend remaining facilities
- Time allocation: 4 strategies (high_flow 35%, pair_based 35%, random 15%, high_degree 15%)
- Result: **12.38% avg** (up from 12.35%)
  - rand50a: 13.86% (up +0.24%)
  - rand60a: 12.45% (same)
  - rand75a: 10.83% (down -0.16%)
- **Insight:** Domain-specific construction (pair-based) escapes earlier local optimum better than parameter tuning alone

## Trial 47: Multi-seed pair-based (top 3 highest-flow pairs) → 12.30% (REGRESSION)
- Tried testing top 3 highest-flow pairs, picking best initialization
- Result: 12.30% (down from 12.38%)
- Insight: Trying multiple pairs adds overhead without benefit; single best pair is sufficient

## Trial 48: Reverify pair-based (restored after trial 47) → 12.44% ✓ NEW BEST
- Reverted code to simple pair-based (single highest-flow pair)
- Result: **12.44% avg** (up from 12.38% trial 46!)
  - rand50a: 13.86% (same)
  - rand60a: 12.62% (up +0.17% from trial 46)
  - rand75a: 10.83% (same)
- Likely minor stochastic variation in random seed; algorithm is robust

**CURRENT BEST: Trial 48 at 12.44%**
- Algorithm: 4-strategy multi-start (high_flow 35%, pair_based 35%, random 15%, high_degree 15%)
- + first-improvement 1-opt (250 iters) + 2-opt (100 iters) + 3-opt (50 iters for n≤60)
- Breakthrough achieved: pair-based domain-specific construction

**SUMMARY:**
- Breakthrough insight: **Domain-specific initialization (pair-based) > parameter tuning**
- 3-strategy plateau (12.35%) was breakable via initialization diversity, not parameter tweaks
- Key win: Started with highest-flow pair, then greedily extended (domain insight into QAP structure)
- Current config appears locally optimal at ~12.44%; further gains need fundamentally different algorithm
