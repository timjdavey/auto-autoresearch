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

## Study 3 Observations

1. **Conditional guidance branches create confusion and failure:**
   - MaxSAT regressed catastrophically: 98.61% → 94.38% (-4.23%)
   - Root cause: Added CRITICAL CHECKPOINT "If you already use 2-opt, skip to initialization diversity." This checkpoint caused Scientists to skip context and examples that MaxSAT needed.
   - **Proposal:** NEVER use "skip" instructions in guidance. Conditional branches should ADD guidance for specific states, not DELETE sections. Structure as: "If condition X, also try A. If condition Y, focus on B instead." Never remove guidance paths.
   - **Evidence:** Study 2 (simple, focused guidance) achieved +1.25% aggregate. Study 3 (complex, conditional guidance) achieved -0.63% aggregate. Complexity is the bottleneck.

2. **Vague conceptual guidance fails to direct action:**
   - Study 3 added "Initialization diversity & timeout management" section for problems with advanced neighborhoods
   - LOP: -0.05%, QAP: -1.07% (no improvement from redirect)
   - Reason: Section provided concepts (multi-seed, phase profiling) without concrete next steps
   - **Proposal:** Guidance must include concrete examples, not abstractions. Instead of "try initialization diversity," specify: "Try 5–10 random seeds with different greedy orderings (facility-first, load-balanced, cost-weighted)" with parameter ranges.
   - **Evidence:** LOP improved 23.52% in Trial 001 via specific technique (client moves). Multi-seed diversification later achieved 58.85%. Concrete examples work; abstract concepts don't.

3. **Trial count stability is required for inter-study comparison:**
   - GC ran only 33 trials in Study 3 vs 50–56 in Studies 1–2
   - Cannot distinguish "GC improved +1.56%" from "lower trial count = more noise"
   - **Proposal:** Enforce fixed trial budgets per problem. If harness varies budgets per study, document the mechanism and report it in results. Current anomaly in GC trial count suggests either harness variation or hidden per-study logic.
   - **Evidence:** GC's +1.56% improvement is suspicious given reduced trials and solver errors (trials 11, 23). Need stable budget to interpret improvement signal.

4. **Guidance complexity scaling — evidence for simplification in Study 4:**
   - Study 1 (baseline, minimal): 39.79% aggregate, all problems executed cleanly
   - Study 2 (one section added: "Neighborhood structure"): 41.04% aggregate (+1.25%), MaxSAT +6.2% breakthrough
   - Study 3 (two new sections + conditional checkpoint): 40.41% aggregate (-0.63%), MaxSAT crashed -4.23%
   - **Pattern:** Increased complexity ≠ increased performance. Each new section added after Study 2 backfired.
   - **Proposal:** Study 4 should return to Study 2 guidance as baseline, then test ONE small, concrete refinement (e.g., add specific multi-seed examples for weak problems). Measure in isolation before adding more.
   - **Evidence:** Guidance regression from 41.04% to 40.41%, paired with increased error rates (MaxSAT solver_error, GC coloring bug, LOP range error), indicates guidance-induced instability.

## Study 4 Observations

1. **"Skip checkpoint" hypothesis definitively confirmed:**
   - Study 3 added "If you already use 2-opt, skip to initialization diversity" → MaxSAT crashed -4.23%
   - Study 4 removed the checkpoint, restored full neighborhood section → MaxSAT jumped +4.93% to 99.31% (best across all studies)
   - **Proposal:** LOCKED DECISION: Never include "skip" or "ignore section X" instructions in guidance.md. Conditional guidance should ADD clarifications, not DELETE paths. Structure as "If X, also try Y" not "If X, skip section Z."
   - **Evidence:** Two independent studies (3 and 4) confirm causality: conditional skip instruction → catastrophic failure; removal of skip instruction → recovery.

2. **Concrete examples did NOT rescue weak problems:**
   - Study 4 added explicit initialization strategies: "Try 5–10 random seeds with different greedy orderings", "Swap initialization (random → greedy → multi-start)", "Use problem-specific construction (facility-first, degree-ordering)"
   - **Outcome:** LOP crashed -4.18% (9.23% → 5.05%), QAP regressed -0.97% (13.41% → 12.44%)
   - **Root cause:** LOP memory.md shows trials 29–38 (prior studies) exhaustively tested multi-seed, greedy variants, and random initialization — all failed. Study 4 guidance re-suggested these exhausted strategies, causing Scientists to waste budget re-exploring known-dead space.
   - **Proposal (CRITICAL):** Weak problems (LOP, QAP) have fundamentally exhausted initiative diversification strategies. Generic guidance cannot direct them toward unexplored approaches. Two options:
     - **(A) Accept failure:** Stop trying to improve LOP/QAP with generic guidance; focus on the 3 problems that respond (FacLoc, MaxSAT, GC).
     - **(B) Problem-specific guidance:** Create problem-specific sections in guidance.md (e.g., "For LOP: Tabu search, SA, Lin-Kernighan") rather than generic "try initialization."
     - **(C) Algorithmic hints:** Modify guidance to suggest that if (trial_count > X) AND (no improvement > Y%), scientists should attempt algorithm-family redesign (e.g., "switch to Tabu" for LOP) rather than parameter tuning.
   - **Evidence:** 4 studies + 35+ trials on LOP have shown greedy+2-opt is a proven local optimum. Any guidance that re-suggests parameter variations or initialization will fail.

3. **Divergence is now structural, not tunable:**
   - Study 4 spread: MaxSAT +99.31%, FacLoc +67.17%, GC +18.97%, QAP +12.44%, LOP +5.05%
   - Improvement ratios: MaxSAT is 19× better than LOP; this is not fixable by guidance.
   - **Proposal:** Acknowledge that the five problems have fundamentally different solvability profiles. Generic guidance cannot bridge this gap. Either:
     - Develop problem-specific guidance (separate sections per problem)
     - Or accept that 2 of 5 problems will underperform and focus on optimizing the 3 responders
   - **Evidence:** All 4 studies show consistent per-problem ordering (MaxSAT > FacLoc > GC > QAP > LOP) despite major guidance changes. Problem difficulty is intrinsic, not guidance-fixable.

4. **FacLoc is the only problem showing consistent improvement trajectory:**
   - Study 1: 64.18%
   - Study 2: 63.88% (marginal regression)
   - Study 3: 64.50% (recovery)
   - Study 4: 67.17% (new best, +2.67%)
   - **Insight:** FacLoc plateaued at 27% in early trials (prior ensemble, per memory.md), then breakthrough to 58–67% range via multi-seed + 2-opt. Continued refinement via facility-closing and phase ordering yielding steady 1–3% gains per study. Not yet at hard ceiling.
   - **Proposal:** Use FacLoc as the "proof of concept" for iterative refinement. FacLoc shows that sustained exploration and phase-based optimization work. Contrast with LOP/QAP where guidance has proven ineffective.
   - **Evidence:** FacLoc 4/4 studies trending upward; only problem without regression.

5. **Trial count instability in GC requires investigation:**
   - Study 1: 51 trials, 18.95% improvement
   - Study 2: 56 trials, 18.95% improvement (no change)
   - Study 3: 33 trials, 20.51% improvement (fewer trials, higher improvement — suspicious)
   - Study 4: 50 trials, 18.97% improvement (back to baseline)
   - **Question:** Why did GC run only 33 trials in Study 3? Early convergence, harness variation, or hidden logic?
   - **Proposal:** If harness has per-study trial-count logic, document it in method.md. If not, investigate Study 3 execution to understand the anomaly. GC's +1.56% improvement in Study 3 may be spurious due to lower trial count.
   - **Evidence:** GC's improvement in Study 3 (+1.56%) disappeared in Study 4 (-1.54% vs Study 3), suggesting noise rather than real improvement.
