# Reflections

A list of changes you'd make to the experimental setup if you were allowed.
DO NOT structure this by Stage.
Be specific and justify with evidence.

## Completed (Study 2)

✅ **Increase trial budget for TSP** — TSP now runs 45 trials (was 9), showing full trajectory.
✅ **Restructure guidance.md with failure-handling strategy** — Added explicit failure diagnosis and time profiling sections.
✅ **Add time-awareness to guidance** — Scientists now actively profile and optimize based on budget constraints.

## For Study 3+

### 1. TSP error-mode investigation
**Change:** Add diagnostic requirement to guidance.md: when solver_error occurs, Scientists should attempt to reproduce the error in isolation (same instance, same seed) to determine if it's non-deterministic or systematic.
**Evidence:** TSP has 22% error rate (10/45 trials) vs <5% for other problems. Errors include "cannot access local variable 'no_best_improve'" and continued timeouts despite algorithm improvements. Non-deterministic failures suggest edge cases in stochastic restarts or parallel phases.
**Impact:** Guidance currently assumes errors are deterministic (restart the code). If errors are non-deterministic, Scientists need strategies like "reduce randomization" or "add state guards".

### 2. Per-instance solver scaling metrics
**Change:** Add to guidance.md a section on measuring solver behavior across instance sizes. Request Scientists profile time breakdown separately for small (n=300), medium (n=500), large (n=750) instances.
**Evidence:** TSP avg_training_time is 151s (vs QAP 53s, Graph Colouring 33s). Scientists improved average performance but haven't reported per-size breakdown. Understanding which instance sizes are expensive can guide algorithmic choices.
**Impact:** Enables targeting specific bottlenecks (e.g., "Held-Karp works for n<15, switches to ILS for larger n" — but is this adaptive in current solver?).

### 3. Complexity audit for solvers
**Change:** Add to guidance.md: "Review final solver for Big-O complexity per phase (construction, local search, restart loop). Identify phases that are O(n^3) or worse; propose reduction strategies."
**Evidence:** TSP's final solver includes Held-Karp (exponential for n>20), yet paper setup has n=300+. Either Held-Karp has restricted domain or it's dead code. Current guidance doesn't ask "is this algorithm actually running?".
**Impact:** Prevents waste of code complexity that doesn't contribute to performance.

### 4. Replicate Study 2 with more restricted trial counts
**Change:** Run Study 3 with Trial limit=30 (vs 46+) to test whether improved guidance is robust under tighter constraints.
**Evidence:** Study 2 shows 45 trials for TSP; Graph Colouring uses 47; QAP uses 42. These are resource-heavy. If tighter budgets still produce good results, guidance is more efficient.
**Impact:** Reduces wall-clock time for future studies while validating approach robustness.

## Study 3 Findings — Defensive Guidance Backfired

### Critical insight: Edge case isolation + simplification guidance was too conservative

**Evidence:**
- Per-trial efficiency collapsed 36× (0.0287 → 0.000791 aggregate improvement/trial).
- QAP efficiency: 0.0803 → 0.00041 (95× worse).
- TSP: completely flat (negative improvement, -0.000055).
- All timeouts in Study 2 (TSP errors) are now gone, but Scientists stopped learning.

**Root cause:** The "5% simplification threshold" and "prefer 80% reliability over 85% with variance" reframe caused Scientists to prematurely halt exploration. Time spent on edge case detection and diagnostic measurement consumed the trial budget without improving solvers.

**Why this matters:** Study 2's 80× QAP breakthrough came from aggressive algorithmic redesign. Study 3 prioritized stability over improvement, inverted the incentives.

### No locked-file changes needed for Study 4.

Study 4 will test whether removing the 5% threshold and restoring exploration focus (while keeping error detection) restores efficiency. All changes are in guidance.md.

### For future studies: Monitor efficiency/stability trade-off

If Study 4 restores efficiency but error rates rise, we have a principled trade-off. If Study 4 restores both efficiency AND low error rates, the Study 3 guidance was simply wrong. Track this metric explicitly going forward.