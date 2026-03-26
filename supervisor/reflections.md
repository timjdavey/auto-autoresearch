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

## Study 2 Observations

1. **Per-solve timeout is the hard bottleneck for weak problems:**
   - QAP: 13 solver errors out of 66 trials (20% error rate), all on rand75a timeouts
   - LOP: 24 solver errors out of 72 trials (33% error rate), all on rand100a/rand125a timeouts
   - FacLoc: 2 errors out of 51 trials (4%), manageable
   - **Proposal:** Increase per-solve hard timeout from 65s to 75–80s. Current limit prevents meaningful algorithm exploration on large instances.
   - **Evidence:** Even simple greedy + 1-opt + 2-opt algorithms timeout on n=100+. Scientists cannot explore better approaches within this ceiling.

2. **Guidance divergence reveals problem-specific needs:**
   - MaxSAT: +6.2% breakthrough from "try 2-opt" guidance (was using only 1-opt before)
   - LOP: -0.34% regression from same guidance (already uses 2-opt, guidance wasted budget on parameter tweaking)
   - GC, FacLoc: 0% (no response to guidance)
   - **Proposal:** Refactor guidance.md to include conditional advice based on observable solver state (does it already use 2-opt? already multi-start?). One-size-fits-all guidance creates negative feedback in already-optimized solvers.
   - **Evidence:** MaxSAT improved with "explore neighborhoods", LOP regressed because it spent trials on "neighborhood variants" that don't help when neighborhoods are already present.

3. **Trial count adequacy is masked by timeout ceiling:**
   - QAP/LOP show persistent timeouts even with 66–72 trials
   - Cannot distinguish "problem needs more trials" from "problem needs bigger timeout"
   - **Proposal:** Fix timeout first (proposal 1), then revisit trial counts. Current 50–72 trial range may be sufficient once timeout is not a bottleneck.
   - **Evidence:** MaxSAT finished well in 61 trials with 0 errors. FacLoc was stable. Only timeout-limited problems needed more trials.
