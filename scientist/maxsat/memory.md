# MAX-SAT Solver Progress

## Trial 1: GSAT Local Search + Random Restarts
- **avg_improvement: 15.82%** (baseline was 0%)
  - rand200a: +24.14% (22 unsat vs 29 baseline)
  - rand250a: +12.90% (27 unsat vs 31 baseline)
  - rand300a: +10.42% (43 unsat vs 48 baseline)

**Approach:** GSAT-style local search where each iteration flips the variable that most reduces unsatisfied clauses. Greedy initialization + random restarts.

**Performance:** Hitting 60s time limit per instance. Room to optimize.

**Next ideas:**
1. WalkSAT: Add probabilistic moves to escape local optima
2. Better initialization: Use literal frequency analysis
3. Adaptive time allocation: Spend less time on smaller instances
4. Clause weighting: Track which clauses are hard and bias search toward them
