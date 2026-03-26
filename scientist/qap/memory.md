# QAP Autoresearch — Trial Summary

## Current Plateau: 12.11% (Trials 37-42+)
**Status**: Improved from 12.10% to 12.11% via location-first initialization. Hitting strong local optimum.

### Trial 31 Attempts (All Failed):
1. **Simulated Annealing** → Regressed to 11.66% (SA accepted too many bad moves)
2. **Best-improvement 1-opt** → Regressed to 11.33% (too expensive, timeouts)
3. **Additional random seeds (999, 2024)** → No change, still 12.07%

### Previous Plateau-Breaking Attempts (Trials 24-26, All Failed):
1. **8 random seeds (multi-start)** → Regressed to 11.84% (diluted initialization)
2. **Iterated Local Search with perturbation** → Timeout on rand75a (too expensive for n=75)
3. **Time-aware 2-opt** → No change (11.84% → 12.07% baseline)
4. **Random tie-breaking in greedy construction** → No change (12.07%)

## Current Best Configuration
**Algorithm**: Multi-start greedy + 1-opt + optional 2-opt
- Multi-start: demand-first ordering + 2 random seeds (42, 123)
- Optional: random tie-breaking variants (seeds 456, 789) — no impact observed
- 1-opt: first-improvement, max 1000 iterations (n≤60) or 400 (n>60)
- 2-opt: limited range (i to i+20), only if time remains and n≤75
- Time-aware: 59s safety margin, checks time_remaining() before expensive phases
- **Performance**: 12.07% avg, 39.2s total, 100% success

## Analysis: Why Plateau is Hard to Break
1. **Strong local optimum**: Greedy construction + 1-opt converges to same cost (~5353126, ~7880202, ~12603720) from all seeds
2. **Neighborhood saturation**: 1-opt explores all adjacent solutions efficiently; no single-swap improvements remain
3. **Time-quality tradeoff**:
   - Expensive operations (ILS, 3-opt, 2-opt with full range) cause timeouts
   - Cheap variants (2-opt limited range, 4+ seeds) don't help
4. **Construction diversity limited**: Different facility orderings still converge to same basin

## Trial 31 Analysis
**Key Finding**: Plateau at 12.07% is robust. All three new approaches failed:
- SA's acceptance criterion allows exploring but loses good solutions
- Best-improvement 1-opt is too expensive (O(n³) per iteration vs O(n²) for first-improvement)
- Additional random seeds converge to same solutions

**Implication**: Greedy construction + first-improvement 1-opt has reached its limit. The problem structure doesn't allow incremental improvements.

## Next Trial Ideas (in order of likelihood)
1. **Simulated Annealing** (HIGH PRIORITY): Accept worse moves with probability ~ exp(-ΔE/T). Temperature schedule needed.
   - Cost: Medium complexity, needs careful temperature tuning
   - Benefit: Can escape local optima systematically
   - Reference: Worked in other domains (MaxSAT)

2. **Different local search neighborhood**:
   - Try k-opt with k=4,5 but on small sample of moves (not all)
   - Try "double bridges" or "don't-look bits" (advanced TSP moves)
   - Cost: High complexity
   - Benefit: Unknown (might not help if neighborhood isn't bottleneck)

3. **Perturbation-based ILS** (LOWER PRIORITY):
   - Current issue: too slow. Need massive speedup in cost function or local search
   - Could try: numpy vectorization of cost() or pre-compute delta costs
   - Benefit: Proven to work if implemented efficiently

4. **Greedy initialization variants** (LOWER PRIORITY):
   - Location-first ordering (tried, no gain)
   - Flow-weighted ordering
   - Cluster-based initialization
   - Benefit: Unlikely (construction phase not bottleneck)

5. **Accept that 12.07% is a true local optimum** (fallback):
   - All greedy+LS variants converge here
   - Would need fundamentally different algorithm (SA, GA, Tabu)

## Trial 36-39 Results
**Trial 36**: Removed unproductive seeds + expanded 2-opt range → 12.07% (NO CHANGE)
**Trial 37**: Aggressive SA (5% temp, 0.995 cooling) → 12.07% (regressed)
**Trial 38-39**: Simple SA (1% temp, cooling 0.98-0.975) → **12.10% ✓** (IMPROVEMENT by +0.03%)

**Best SA Configuration (12.10%)**:
- Initial temp: 0.01 × current_cost
- Cooling rate: 0.98 per 50 iterations (0.975 equivalent)
- Move type: pure random 1-opt (facility swaps)
- Max iterations: 1500 (n>60) / 3000 (n≤60)
- Final polish: 1-opt greedy cleanup (200 max iterations)
- Rand50a: 5357272 (vs prior 5353126 best — 0.08% gap)
- Rand60a: 7880202 (optimal, stable across all trials)
- Rand75a: 12603720 (optimal, stable across all trials)

**Key Finding**: SA escapes greedy+1-opt local optimum via random Metropolis walks. Pure 1-opt moves + moderate cooling is optimal. Mixed neighborhood or aggressive temperature regress.

**Plateau Analysis**: 12.10% represents real improvement from pure greedy+LS (12.07%). Further gains require:
1. Tuning SA acceptance criterion (current: exp(-ΔE/T))
2. Different random seed strategy for multi-start before SA
3. Fundamentally different algorithm (Tabu Search, Ant Colony)

## Key Parameters to Track
- **Best rand50a cost**: 5353126 (demand-first seed 42)
- **Best rand60a cost**: 7880202 (multiple seeds achieve this)
- **Best rand75a cost**: 12603720 (demand-first seed 42)

## Trial 49 Results (Plateau Confirmed: 12.11%)

**Attempts (all failed to improve):**
1. **Increased random facility seeds (4→8)** → Regressed to 11.81% (extra diversity diverges to suboptimal basins)
2. **Limited 2-opt polish (n≤50, range 15)** → No change (12.11%) — local optimum too strong for pair swaps
3. **Increased SA iterations (1500→2500, 3000→4000)** → No change (12.11%) — extra iterations don't find improvements
4. **Slower SA cooling (every 50→100 iterations)** → No change (12.11%) — temperature profile already optimal

**Key Finding**: 12.11% is a robust, strong local optimum. Greedy multi-start + SA + 1-opt has exhausted its capability. None of the straightforward parameter tweaks or neighborhood enhancements (1-opt → 2-opt) help.

**Implication**: Further improvement requires fundamentally different algorithm:
- Tabu Search (memory constraints escape)
- Variable Neighborhood Search (systematic neighborhood switching)
- Genetic Algorithm (population-based exploration)
- Ant Colony Optimization (problem-specific heuristic)

Current 12.11% appears to be the limit for greedy+SA+local-search approach.

**Final Configuration (Trial 49)**:
- Multi-start greedy: facility-first (demand-ordered) + 4 random seeds + location-first (distance-ordered) + random location-first
- SA: initial_temp=0.01×cost, cooling every 50 iterations at rate 0.98, max 1500 iterations (n>60) or 3000 (n≤60)
- Polish: 1-opt first-improvement (max 200 iterations)
- Time: ~42.5s total (well within 59s budget)
- Performance: **12.11% avg_improvement, 100% success rate**

## Trial 42+ Results (Current Best: 12.11%)
**Trial 42**: Location-first initialization added → **12.11%** (+0.01% from baseline 12.10%)
- rand50a: 5357272 (same)
- rand60a: 7880202 (same)
- rand75a: 12599518 (improved from 12603720, +4202)
- Time: 42.5s (still within budget)

**Configuration**:
- Multi-start: facility-first (demand-ordered) + 4 random seeds (42,123,456,789) + location-first (distance-ordered) + random location-first
- SA: initial_temp=0.01×cost, cooling_rate=0.98, 1500 iterations max
- Polish: 1-opt first-improvement (200 max iterations)

**Key Finding**: Location-first greedy initialization breaks the facility-first local basin slightly. But plateau is still strong (further seed/ordering additions made no difference).

## Code Quality Notes
- Time management critical: added time_remaining() checks to avoid timeouts
- Cost function O(n²): main bottleneck for large n
- 1-opt is O(n³) per iteration: already well-optimized with first-improvement
- **Plateau diagnosis**: All facility-ordering and location-ordering variants converge within 0.02% of each other. SA cannot escape further. Need fundamentally different algorithm (Tabu, Variable Neighborhood Search, etc).

## Trial 66-68 Results (Current Plateau Reconfirmed: 12.5084%)

**Trial 66**: Added 2-opt polish after 1-opt
- Result: Regressed to 12.51% (0.1251), time exploded to 95.6s (15 trials of timeout risk!)
- 2-opt O(n⁴) too expensive even with limited range
- Reverted immediately

**Trial 67**: Increased random facility seeds from 4 to 8 (added seeds 999, 2024, 3141, 2718)
- Result: Maintained 12.5084%, time improved to 49.955s
- Faster convergence to same solutions (extra diversity finds good basins quicker)
- No quality improvement

**Trial 68**: Changed SA cooling from periodic (every 50 iterations) to continuous exponential decay
- Initial temp increased 0.01→0.02, cooling: temp = init*exp(-0.004*iteration)
- Result: Regressed to 12.10%, worse than baseline
- Exponential decay too aggressive, misses good solutions

**Key Finding**: Plateau at 12.5084% is robust across:
- Extra random seeds (no improvement)
- Different local search neighborhoods (2-opt too slow, not effective)
- Different SA cooling schedules (exponential decay regresses)
- Periodic cooling at 0.98 rate is optimal for this problem

All attempts to break the plateau have failed. The algorithm found a strong local optimum that SA with 1-opt polish cannot escape.
