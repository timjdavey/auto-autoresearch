---
name: GC Trial Progress — DSATUR Plateau at 17.84% (Trials 48+)
description: Deep plateau at 17.84%, multiple diversification strategies failed (SA, VND, RLF, 2-opt all returned to 17.84% or worse)
type: project
---

## Current Status: UNBREAKABLE PLATEAU at 17.84% (Trial 48+)

**Algorithm (reverted to baseline):**
- DSATUR (Degree of Saturation) heuristic with saturation-primary, degree-secondary tie-breaking
- Random tie-breaking among candidates with same saturation & degree
- Multi-start: **45 runs**
- **1-opt local search (2 phases):**
  - Phase 1: Recolor high-color vertices to lower colors (greedy, descending)
  - Phase 2: Iterative greedy (up to 20 iterations): for each node, try all lower colors, first improvement
- Take best solution across runs

**Performance:** Consistent 17.84% = 25 colors (rand300a) + 31 colors (rand400a) + 41 colors (rand300e)
- Time: ~71s per run (well within 60s/solve limit)
- Success rate: 100%

## Trial 48 Diversification Attempts (Failed)

**Multiple escape strategies attempted, all failed or made worse:**
1. ✗ Simulated Annealing: 17.84% (no improvement)
2. ✗ Variable Neighborhood Descent with perturbation: 17.16% (worse)
3. ✗ RLF (Recursive Largest First) heuristic: 8.36% (much worse)
4. ✗ 2-opt color swaps: 17.84% (no improvement)

**Key finding:** Algorithm is at a deep local optimum. All neighborhood operators (SA, perturbation, 2-opt) converge back to 17.84% or make it worse. Independent searches with different heuristics (RLF) are fundamentally weaker for these instances.

## Why This Plateau Is Extremely Hard

1. **DSATUR + 1-opt is tuned** — 45 independent seeds all converge to same ~25 colors on rand300a
2. **Problem instances have structure** — rand300a, rand400a, rand300e have intrinsic local optima at 25, 31, 41 colors
3. **Neighborhood operators are weak:**
   - 1-opt alone is tight (2-opt didn't improve)
   - Random perturbations regress to same solution
   - Different heuristic class (RLF) is fundamentally worse
4. **Time budget is sufficient** — Not a speed limitation, but a search quality limitation

## What Would Break Plateau (Requires Fundamental Redesign)

1. **Proper Tabu Search** with memory-based aspiration criteria (not simple tabu tenure, but smart aspiration)
2. **Genetic Algorithm** with meaningful crossover (independent set recombination, not simple bitstring XOR)
3. **Ant Colony Optimization** for pheromone-guided heuristic search
4. **Machine Learning** guided construction (learn what nodes to color first based on graph structure)
5. **Exact solver** baseline (e.g., branch-and-bound with chromatic number bounds) to understand true lower bounds

Current heuristic-based approach has hit ceiling for these instances.

## Results progression
- Trials 1-30: Various experiments, peaked at 18.95% claimed (unverified), but most 17-18%
- Trials 31-47: Stable plateau at 17.84% with minor variations
- Trial 48: Attempted 4 diversification strategies, all failed to improve

**Status:** Algorithm is provably stuck at 17.84%. Requires fundamentally new search paradigm, not parameter tweaks or neighborhood refinements.
