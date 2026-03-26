## LOP Solver Progress

**Trial 1-3:** Baseline + simple greedy
- Trial 1: Identity → 0% (baseline)
- Trial 2: Greedy construction + 1-opt → 0.69%
- Trial 3: Optimized greedy gain calc + best-improvement 1-opt → 0.74%

**Trial 4:** Greedy + 1-opt + 2-opt + 10/7/3 multi-starts
- Result: 4.28% improvement
- Time: 134s (too aggressive on restarts)

**Trial 5:** First-improvement 2-opt (regressed to 1.19%)
- Lesson: Need best-improvement for solution quality

**Trial 6:** Balanced approach - fewer starts (5/3/2) + more time for 2-opt per start
- Result: 7.31% improvement
- Time: 167s (good, using full budget)

**Trial 7:** Randomized greedy + 2-opt max_iterations=100
- Result: **7.59% improvement** (new best!)
- Added randomized greedy variant (picks from top 30% candidates)
- Increased 2-opt max_iterations: 50→100
- Increased num_starts: 5/3/2 → 6/4/3
- Alternating deterministic and randomized construction

**Current algorithm:**
1. Greedy construction (deterministic or randomized): build permutation by selecting element maximizing contribution
2. Best-improvement 1-opt: adjacent swaps
3. Best-improvement 2-opt: all pair swaps (max 100 iterations)
4. Multi-start: 6/4/3 runs (75/100/125 instances) alternating strategies
5. Time budget: 55s per instance (5s margin)

**Key insights:**
- Best-improvement better than first-improvement for solution quality
- Deeper search (fewer multi-starts, more 2-opt iterations) beats breadth
- Randomized greedy adds diversity to multi-start restarts
- 2-opt is expensive but essential for good solutions

**Trial 8:** Breadth vs depth trade-off failed
- Increased num_starts (6/4/3 → 8/6/4), reduced 2-opt (100 → 50 iterations)
- Result: **7.46% (regressed)** — more diverse starts didn't compensate for shallower search

**Trial 9:** Randomized greedy variance
- Changed top-30% to top-50% in randomized greedy
- Result: **7.46% (regressed)** — same as trial 8

**Trial 10:** Insertion-based construction ✓ breakthrough
- Added insertion_construct() that inserts each element at best position
- Alternating: deterministic greedy, randomized greedy, insertion (cycle 3)
- Result: **7.71% (new best!)** +0.12% improvement
- Key: Different construction heuristic explores different solution landscape

**Trial 11:** 3-opt on small instances
- Added 3-opt (O(n³) moves) for n≤75 instances
- Result: **7.31% (regressed)** — 3-opt too expensive, not worth time cost

**Trial 12:** Aggressive insertion construction ✓ major breakthrough
- Increased insertion usage: every 3rd start → every other start (50%)
- Alternation: insertion (50%) + greedy deterministic/randomized (50%)
- Result: **8.66% (major breakthrough!)** +0.95% from trial 10
- Key: Insertion construction explores fundamentally different solution landscape
- Per-instance improvements: rand75a +9.28%, rand100a +8.16%, rand125a +8.54%

**Key insight:** Different construction heuristics are critical to breaking local optima.
- Greedy (best gain) captures one landscape
- Randomized greedy (top-30%) adds diversity
- Insertion (position-based) finds better overall orderings

**Trial 13:** Insertion expansion 60/40
- Changed insertion usage: 50% → 60% of multi-start trials
- Ratio: 60% insertion (position-based) / 40% greedy (deterministic/randomized mix)
- Result: **8.72% (new best!)** +0.06% from trial 12
- Per-instance improvements: rand75a +9.33%, rand100a +8.30%, rand125a +8.54%
- Key: Insertion construction continues to outperform greedy construction

**Trial 14-17:** Plateau at 8.72% — extensive testing
- Trial 14: 70/30 insertion/greedy split → 8.72% (no improvement)
- Trial 15: 40/40/20 with row-sum construction → 8.72% (row-sum doesn't help)
- Trial 16: Increased num_starts (6→8, 4→5, 3→4) → 8.72% (more starts don't help)
- Trial 17: Reduced 2-opt iterations (100→50) → 8.72% (trading depth for breadth doesn't help)
- **Key finding:** We've hit a true local optimum with current algorithm (greedy/insertion construction + 1-opt + 2-opt best-improvement)

**Plateau Analysis:**
- All parameter variations of construction/greedy split converge to 8.72%
- Adding new construction variants (row-sum) doesn't escape plateau
- More multi-starts with same search don't help
- Reducing 2-opt depth to allow more restarts doesn't help
- Current solver achieves: 9.33% (rand75a), 8.30% (rand100a), 8.54% (rand125a)

**Trial 18:** Perturbation-based refinement
- Added post-processing: perturb best solution (random swaps) and re-optimize (1-opt + 2-opt)
- Tried 2 perturbation cycles to escape local basin
- Result: **8.72% (no improvement)** — perturbation doesn't escape plateau
- Key: Current local optimum is very strong; perturbations from same basin converge to same score

**PLATEAU DIAGNOSIS (8.72% hard ceiling):**
The solver has reached a tight local optimum that resists:
- Different construction ratios (60/40, 70/30, 40/40/20)
- New construction variants (row-sum heuristic)
- More multi-starts (num_starts 6→8)
- Reduced 2-opt (100→50 iterations)
- Perturbation-based refinement
- Multiple restarts from perturbed solutions

**Next breakthrough attempts (requires major redesign):**
1. **Simulated Annealing:** Replace greedy 2-opt with probabilistic SA (accept some bad moves)
2. **Tabu Search:** Add tabu list to prevent cycling, escape local optima
3. **3-opt on small instances:** More expensive but explores larger neighborhoods
4. **Lin-Kernighan heuristic:** Advanced local search beyond 2-opt
5. **Genetic algorithm:** Population-based search with crossover/mutation

**Trial 19:** First-improvement 2-opt diversification ✓ marginal breakthrough
- Alternated between best-improvement and first-improvement 2-opt (by start index)
- First-improvement is faster, sometimes finds escape paths that best-improvement misses
- Result: **8.73% (new best!)** +0.01% from trial 13-18 plateau
- Key: Diversity in local search method (different neighborhoods for different restarts)
- Timing: 135s vs 167s before — efficiency gain from first-improvement variant

**Trials 20-27:** Plateau at 8.72-8.73% — extensive testing of variations
- All parameter tweaks (construction ratios, num_starts, 2-opt iterations) converged to 8.73%
- Perturbation-based refinement didn't escape local optimum

**Trial 25-28:** BREAKTHROUGH — local search ordering critical ✓ major improvement
- **Key insight:** 2-opt BEFORE 1-opt instead of after
  - Before (Trial 24): 1-opt → 2-opt → Score: 8.73%
  - After (Trial 25): 2-opt → 1-opt → Score: 8.74% (+0.01%)
  - Reason: 2-opt explores larger neighborhoods first, 1-opt fine-tunes the result
- Trial 26: More aggressive perturbation (25% element swaps, 5 attempts for small instances) → 8.77%
- Trial 27: Consistent 2-opt→1-opt in perturbation phase (80 iterations) → **8.88% (new best!)** +0.15%

**Current best:** 8.88% avg_improvement (Trial 27)
- Per-instance: rand75a 9.62%, rand100a 8.44%, rand125a 8.57%
- Multi-start: 6/4/3 for 75/100/125 instances
- Construction: 60% insertion, 40% greedy (deterministic/randomized)
- **Local search sequence (critical):**
  1. Main loop: 2-opt (best or first-improvement) → 1-opt
  2. Perturbation: 2-opt (80 iterations) → 1-opt → repeat 5/3 times for small/large instances
- Perturbation: 25% element swaps per attempt (was 10%)
- Time: 163s total, using full 55s per instance with 5s margin

**Trial 30-31: Plateau-breaking attempts (regressed to 8.78-8.79%)**
- Trial 30: 3-opt with max_iterations=10 on small instances (n≤75) → 8.78% (-0.10%)
  - 3-opt is too expensive despite iteration limits; costs time without finding better solutions
- Trial 31: Increased perturbations (8/5/3 vs 5/3) + varying strengths (10%-50% swaps) → 8.79% (-0.09%)
  - More diverse perturbation attempts don't escape tight local optimum
- Random construction variant (10% of starts) → 8.79% (same regression)
  - Random starts from distant basins not helping

**PLATEAU DIAGNOSIS (8.88% hard ceiling - 20+ trials stuck):**
The solver has exhausted all variations within current algorithm family:
- ✓ Construction heuristics: greedy (deterministic/randomized), insertion, row-sum tried
- ✓ Local search neighborhoods: 1-opt, 2-opt (best/first-improvement) combined
- ✓ Multi-start counts: tested 3-10 starts per instance size
- ✓ 2-opt iterations: tested 50-100 per multi-start
- ✓ Perturbation-based refinement: tested 3-8 attempts, different swap rates (10%-50%)
- ✓ Higher-order neighborhoods: 3-opt too expensive without gains
- ✓ Initialization diversity: random starts don't escape basin

**Next breakthrough requires major algorithm redesign:**
1. **Simulated Annealing:** Probabilistic moves to escape local optima (accept worse solutions temporarily)
2. **Tabu Search:** Memory-based search to prevent cycling through same solutions
3. **Lin-Kernighan heuristic:** Chained 2-opt moves with variable depth, more sophisticated than simple 2-opt
4. **Genetic Algorithm:** Population-based crossover/mutation to maintain diversity
5. **Iterated Local Search:** Deeper perturbations + controlled escape (change 30-50% of solution)

Current local optimum appears very strong - parameter tuning alone won't break it.
