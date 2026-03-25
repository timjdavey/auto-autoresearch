# LOP Trial — Current Session Summary

## Trial 40 Plateau-Breaking Attempts (Failed)

**Results Summary:**
1. **Edge-based initialization** (prioritize highest-weight edges) → 9.14% (worse: new init unhelpful)
2. **Perturbation magnitude n//17** (smaller perturbations) → 9.35% (back to plateau, confirms smaller is better)
3. **Increased 2-opt time allocation** (50% instead of 20%) → 9.23% (worse: 1-opt more effective)

**Key Findings:**
- Edge-based initialization: **DOESN'T WORK** (9.14%)
- Smaller perturbations (n//17) > larger (n//12): **CONFIRMED**
- 1-opt is more effective than 2-opt: Allocating more time to 2-opt made things worse
- Current best config: 3 greedy init + n//17 perturbation = 9.35%

## PLATEAU DIAGNOSIS

After 40+ trials at 9.25%-9.37%, all incremental improvements have failed:
- ✗ Edge-based initialization
- ✗ 3-opt moves (previous: timeout)
- ✗ Increasing 2-opt time
- ✗ Different perturbation magnitudes
- ✗ Different time allocations

**Fundamental Bottleneck:** Local search (1-opt + 2-opt) + ILS appears to be hitting a hard local optimum. The solver consistently finds permutations worth ~9.35% improvement, and no neighborhood structure helps escape further.

## Current Best Configuration

**Trial 40 (restored):** 9.35% avg_improvement
- **Init strategies:** 3 greedy (outgoing, incoming, net)
- **Perturbation:** n // 17 (smaller magnitude = more iterations)
- **Local search:** First-improvement 1-opt (70% time) + 2-opt (20% time)
- **ILS:** Iterated with perturbation for diversity
- **Time limit:** 55s per solve

## Recommendations for Next Session

**Do NOT continue incremental tuning.** The plateau is hard-locked. Options:

1. **Variable Neighborhood Search (VNS):**
   - Systematically switch between 1-opt, 2-opt, 3-opt neighborhoods
   - Current solver only uses 1-opt + 2-opt in limited fashion
   - Requires careful time management but could find new basins

2. **Problem Structure Analysis:**
   - Profile which nodes/edges prevent good orderings
   - Identify bottleneck constraints
   - Design init/search around structural constraints

3. **Accept 9.35% as current best and move on**

4. **Try fundamentally different paradigm:**
   - Genetic algorithms
   - Ant colony optimization
   - Tabu search with memory
   - Simulated annealing (with better acceptance criteria than Trial 35)

**Current best remains:** 9.35%-9.37% range (Trial 27-40 range)
