# MAX-SAT Scientist Memory

## Trial 61: BREAKTHROUGH — 94.38% (NEW BEST)

**Configuration change from Trial 60:**
- Changed max_flips decay from linear (`20000 // (restart + 1)`) to more gradual (`int(22000 / (1 + 0.8 * (restart / 25)))`)
- This gives later restarts more search depth instead of starving them

**New flip budget distribution:**
- restart=0: 22000 flips
- restart=5: ~18966 flips
- restart=12: ~15895 flips
- restart=24: ~12442 flips
- (vs old: 20k, 10k, 6.6k, 5k, 4k, ... rapid decay)

**Results (Trial 61):**
- rand200a: 0 unsat (100.00%) ✓ PERFECT
- rand250a: 2 unsat (93.55%)
- rand300a: 5 unsat (89.58%)
- **avg_improvement: 94.38%** ✓ NEW BEST (+0.46pp vs 93.92%)
- Total eval time: 112.1s (faster than trial 60's 140.1s)

**Key insight:**
The aggressive decay in flip budget was hurting later restarts. By reducing decay rate from 1/(restart+1) to ~1/(1+0.8*progress), we give later restarts enough budget to escape local minima while keeping early restarts deep. Combined with 25 restarts, this creates better balance between breadth and depth.

**Previous best comparison:**
- Trial 60: 93.92% (20000/(restart+1), 25 restarts)
- Trial 61: 94.38% (22000/(1+0.8*(restart/25)), 25 restarts)
- Improvement: +0.46 percentage points

## Trial 55: BREAKTHROUGH — 93.92% (PREVIOUS BEST)

**Best configuration (relaxed 3-opt from Trial 51, confirmed in Trial 55):**

Core algorithm: Smart WalkSAT + 1-opt + 2-opt + selective 3-opt
- 25 multi-start restarts
- 20k flips per restart (decreasing by factor of (restart+1))
- Random walk probability: 0.2-0.4 (cycles through values)
- 1-opt: 3 passes of first-improvement local search
- 2-opt: 100 random pair flips
- 3-opt: **RELAXED CONDITIONS** — n_vars ≤ 270 (was 250), best_unsat ≤ 6 (was 3), 50-150 iterations (was 30-100)

**Results (Trial 55):**
- rand200a: 1 unsat (96.55%)
- rand250a: 2 unsat (93.55%)
- rand300a: 4 unsat (91.67%)
- **avg_improvement: 93.92%** ✓ PREVIOUS BEST
- Total eval time: 140.1s

## Key insight — Why 3-opt relaxation worked

The selective 3-opt was too conservative. By expanding conditions:
- More instances benefit from 3-opt refinement (even those with 4-6 unsat clauses)
- Small-medium instances (rand200a, rand250a) get proper final refinement
- No time budget issues (still within 55s per instance)
- 3-opt's exponential moves help escape plateaus that 1-opt/2-opt can't break

## What didn't work

1. **Clause weighting** (Trial 61) → disrupted search, dropped to 89.69% (weighted cost mixed with unweighted final phases)
2. **More restarts** (35 instead of 25) → hurt by reducing depth per restart
3. **Higher flip budget per restart** (24k instead of 20k) → time limit violations
4. **Fewer 1-opt passes** (2 instead of 3) → quality loss (91.08%)
5. **More 2-opt pairs** (150 instead of 100) → instance-specific variance, no net gain
6. **More breadth, less depth** (30 restarts, 18k flips) → dropped to 89.23%

## Current plateau status

At 94.38%, we've broken through the previous plateau. The key was balancing restart breadth with search depth per restart. The slower decay function allows later restarts to contribute meaningfully.

Further improvements could try:
- Even slower decay (if time permits)
- Different random walk probabilities
- Adaptive multi-start (increase restarts for harder instances)
- Problem-specific tuning
