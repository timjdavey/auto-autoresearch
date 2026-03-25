# Reflections

A list of changes you'd make to the experimental setup if you were allowed.
DO NOT structure this by Stage.
Be specific and justify with evidence.

## Study 1 Observations

1. **Trial count adequacy confirmed:** QAP and LOP needed 55–62 trials to exhaust their search space. Facloc, GC, and MaxSAT plateaued with 49–51 trials. Current limit is sufficient, but consider raising to 70+ for future weak-performer focused studies to allow more recovery from early errors.
   - Evidence: LOP had 2 timeouts (trials 2, 7), still completed 62 trials and reached 9.62% improvement. With lower budget, might have failed to recover.

2. **Time budget clarity needed for all solvers:** Only LOP and MaxSAT explicitly set time limits (55s). Facloc, GC, and QAP lack explicit hard limits, relying on harness timeout. This creates variance.
   - Proposal: Standardize guidance to require explicit `time_limit = 55` in all solvers with margin buffer, and add per-phase timing instrumentation to diagnose bottlenecks.
   - Rationale: TimeProfiler wins per ideas.md; explicit limits prevent silent failures.

3. **Error mode distribution suggests tuning priorities:** GC and LOP hit timeouts, facloc/maxsat/qap ran cleanly. This suggests GC and LOP have higher complexity solvers that are hitting time budget limits on large instances.
   - Proposal: Adaptive complexity scaling for GC/LOP (e.g., reduce num_runs or local search depth for n>350 or n>125).
   - Rationale: Avoids timeout noise, allows Scientists to focus on algorithmic improvements rather than debugging time issues.
