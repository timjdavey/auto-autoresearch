# Reflections

A list of changes you'd make to the experimental setup if you were allowed.
DO NOT structure this by Stage.
Be specific and justify with evidence.

## Immediate Action Required

### 1. Increase trial budget for TSP
**Change:** Raise trial limit for TSP from 9 to 46+ (match Graph Colouring/QAP).
**Evidence:** TSP completed only 9 trials before 8 scientist_timeouts. Current guidance too minimal — Scientists have no strategy for repeated failures. With improved guidance (Study 2+), TSP needs 46+ trials to show trajectory.

### 2. Add solver execution-time metrics
**Change:** Track per-problem wall-clock time. Add columns to study_results.csv: `solver_max_time`, `solver_avg_time`.
**Evidence:** QAP averages 80+ seconds per trial (60s budget is tight); multiple solver_error entries cite "exceeded time budget". TSP convergence checks risk infinite loops. No current visibility into whether errors are solver-slow or guidance-wrong.

### 3. Flag TSP solver convergence risk
**Change:** Add diagnostic note to method.md: "TSP train.py line 205-206 uses `nlen >= prev - 1e-10` convergence. At this tolerance, floating-point rounding can cause false 'no improvement' signals. If TSP timeouts persist, investigate _local_search_nn/fast infinite loops."
**Evidence:** TSP's while-loop convergence checks can stall if nlen ≈ prev within floating-point precision.

## For Study 2+

### 4. Restructure guidance.md: add failure-handling strategy
**Change:** Expand guidance from 4 points to structured reflection loop:
1. **Profile:** Measure current bottleneck (time breakdown: init vs local search vs restarts).
2. **Hypothesize:** Target specific bottleneck (reduce iterations, swap algorithm, etc.).
3. **Experiment:** Test on one problem first. If timeout: backtrack immediately.
4. **Reflect:** Did improvement-per-second increase? Did error rate drop?

**Rationale:** Minimal guidance fails on hard problems. Scientists need structure to diagnose and respond to timeouts without getting stuck.

### 5. Add time-awareness to guidance
**Change:** Add section to guidance.md: "When status=solver_error with 'exceeded time budget': 1) reduce restarts/iterations, 2) switch to faster algorithm. Monitor training_time in results.tsv for trends."
**Rationale:** QAP/TSP are hitting time budgets while Graph Colouring succeeds; Scientists must learn to recognize and fix time bottlenecks.