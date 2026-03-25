# MAX-SAT Solver Optimization

## Trial 011+ (2026-03-25): Reverted to stable restart schedule — +7.23% recovery

**Result:** 89.93% average improvement (was 82.70%)

**Approach:** Reverted from unstable 12×28k configuration back to trial-008's proven 10×30k:
- Reduced restarts: 12 → 10
- Increased iterations per restart: 28k → 30k (total: 336k → 300k)
- Reduced perturbation phases: 10 → 6

**Metrics by instance:**
- rand200a: 93.10% (2 unsat, was 4)
- rand250a: 87.10% (4 unsat, was 6)
- rand300a: 89.58% (5 unsat, was 9)

**Key insight:** Recent config (12 restarts) showed high variance (0.82–0.91). Trial-008's conservative restart schedule (10 restarts, fewer perturb phases) provides stability. Fewer restarts but deeper iterations (30k) allows each trajectory more exploration without thrashing between local optima.

**Next directions:**
- Clause weighting: track hard clauses (frequently unsat), bias WalkSAT selection toward them
- Adaptive restart: detect plateaus, trigger restart more aggressively
- Multi-start diversification: better initialization strategies (not just sequential greedy)

## Trial 010+ (2026-03-25): Increased search intensity — +1.16% improvement

**Result:** 87.70% average improvement (was 86.55%)

**Approach:** Exploit the eval_flip_cost speedup by increasing search aggressiveness:
- Increased restart count from 7 → 10
- Increased iterations per restart from 25k → 30k
- Total iterations: 175k → 300k (+71% search intensity)

**Metrics by instance:**
- rand200a: 89.66% (3 unsat, was 4)
- rand250a: 83.87% (5 unsat, was 6)
- rand300a: 89.58% (5 unsat, was 6)

**Key insight:** The eval_flip_cost optimization freed enough CPU budget to allow much deeper local search without hitting time limits. WalkSAT benefits from exploring more trajectory space per trial.

**Next directions:**
- Further increase restarts (12-15) if time budget allows
- Clause weighting: track unsatisfied clause frequency, bias search toward harder clauses
- Adaptive restart: detect plateaus and restart more aggressively when stuck

## Trial 009 (2026-03-25): eval_flip_cost optimization — +8.1% breakthrough

**Result:** 84.78% average improvement (was 78.39%)

**Approach:** Optimized the critical `eval_flip_cost()` function:
- **Problem:** Original code scanned ALL ~1275 clauses for each variable flip (60k flips/trial × 1275 clauses = 76.5M clause scans)
- **Solution:** Precompute `var_to_clauses[var_idx]` at setup, only check relevant clauses (~3 per variable on average)
- Reduced computation from 76.5M to ~180k clause scans per trial
- No algorithmic change; same 5 restarts × 20k iterations, same greedy init

**Metrics by instance:**
- rand200a: 86.21% (4 unsat, was 3) — still excellent, more variance
- rand250a: 80.65% (6 unsat, was 8) — improved +2 unsat
- rand300a: 87.50% (6 unsat, was 14) — improved +8 unsat (largest gain!)

**Key insight:** WalkSAT needs aggressive local search to escape plateaus. By cutting eval time 400×, the search can explore more thoroughly without hitting time limits. Speedup applied uniformly; hardest instance (rand300a) benefited most.

**Next directions:**
- Further parameter tuning: increase restart count (maybe 7-10?) to exploit speedup
- Smarter restart: perturb best rather than full random
- Clause weighting: harder clauses (always unsat) could guide search better
