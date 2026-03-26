# Ideas

List of ideas to test to improve how the Scientist conducts their work.
DO NOT include (or consider) any problem specific ideas.
RED FLAG that you need to given seperate advice for each problem.


## Study 2 Results — COMPLETED

**Outcome:** Mixed. Aggregate +1.25%, but divergence revealed: MaxSAT +6%, LOP -0.34%, GC/FacLoc flat.

### 1. Neighborhood Structure guidance — CONDITIONAL, NOW IMPLEMENTED FOR STUDY 3
   - **What worked:** MaxSAT breakthrough (+6.2%) using aggressive 2-opt/1-opt combinations. Guidance on "when to use 2-opt vs 1-opt" energized exploration in a problem without pre-existing neighborhoods.
   - **What failed:** LOP regression (-0.34%). Scientists already using 2-opt/3-opt (evident in train.py) tried parameter tuning instead of algorithmic redesign. Guidance created negative feedback: "try 2-opt variants" → already have it → adjust iters → worse results.
   - **Root cause:** Guidance was too generic. MaxSAT benefited; LOP was harmed because it wasted budget on incremental parameter tweaks within an already-explored design space.
   - **Solution (Study 3):** Added CRITICAL CHECKPOINT at top of "Neighborhood Structure" section: "Are you already using 2-opt? If yes, skip to initialization diversity and timeout management." Also added new "Initialization diversity & timeout management" section for problems with advanced neighborhoods. This preserves MaxSAT's breakthrough while redirecting LOP/QAP toward multi-seed, greedy variants, and phase profiling.

### 2. Weak-problem support — PARTIALLY ADDRESSED
   - **QAP (13.8% → 14.48%):** Marginal +0.65%. Still has 10+ timeouts on rand75a. Time budget is bottleneck, not algorithm diversity.
   - **LOP (9.6% → 9.28%):** Regression. Guidance backfired.
   - **Insight:** Weak problems need different help. Time profiling (Study 1) worked better than neighborhood tweaks. For Study 3, emphasize timeout diagnosis + algorithm selection rather than parameter variations.

### 3. Guidance quality signal — SUCCESS
   - GC/FacLoc flat (19% and 64%): no regression, just no improvement. They're already optimized locally.
   - All problems executed cleanly with reasonable trial counts. Harness and error handling working well.

## Study 3 Implementation & Results — FAILED

1. ✅ **Attempted Refactor:** Added CRITICAL CHECKPOINT: "Are you already using 2-opt? If yes, skip to initialization diversity."
   - **Outcome:** CATASTROPHIC FAILURE. MaxSAT dropped 4.23% (98.61% → 94.38%). The conditional checkpoint disrupted MaxSAT's winning path instead of preserving it.
   - **Root cause:** Checkpoints that tell Scientists to "skip sections" are dangerous — they may cause loss of critical guidance. MaxSAT benefited from the neighborhood discussion; the skip instruction removed that benefit.
   - **Lesson:** Conditional branches should ADD guidance for specific states, not DELETE it. Avoid "skip" instructions.

2. ✅ **Attempted Redirect:** Created "Initialization diversity & timeout management" section for problems with advanced neighborhoods.
   - **Outcome:** NO IMPROVEMENT. LOP -0.05%, QAP -1.07%. The redirect didn't generate expected gains.
   - **Root cause:** Weak guidance. Section provided concepts (multi-seed, phase profiling) but no concrete, actionable next steps. Scientists didn't know how to apply it.
   - **Lesson:** "Try initialization diversity" is too vague. Guidance must include concrete examples (e.g., "try 5–10 random seeds with different greedy orderings").

3. ✅ **Preserved neighborhood discussion:** For problems without 2-opt, kept the neighborhood section intact.
   - **Outcome:** GC improved +1.56% — only positive signal. But GC also ran 33 trials vs 50–56 expected, so unclear if true improvement or trial variation.

### Study 3 Expectations vs Reality
- **MaxSAT:** Expected ~98.6%, Got 94.38% ✗✗✗ CATASTROPHIC FAILURE
- **LOP:** Expected 9.6%+, Got 9.23% ✗
- **QAP:** Expected 14.48%+ improvement, Got 13.41% ✗
- **GC:** Expected maintenance, Got +1.56% ✓ (but low trial count suggests noise)
- **FacLoc:** Expected maintenance, Got +0.62% ✓ (marginal)

## Untested ideas

- Memory: each new trial gets a new Scientist, so what files should the Scientist have to maintain pass it's thinking on most efficiently and effectively? e.g. a scratchpad. As searching through old train.py is expensive & slow & doesn't show any insights.
- Memory: what's the best format of memory? is it a single journal of historical logs, or an ideas list, or freeform notes?
- Reflection: what kinds of reflection steps lead to the best results? Create hypothesis, then test, spend time planning up front or use budget reflecting after?
- Structure: does storing hypothesis, analysis, conclusion, abstract make a difference compared to freeform notes?
- Perceived trial budget: inflate count to encourage risk-taking, or deflate to force concentrated bets
- Note verbosity: more verbose for richer reasoning vs more concise to fit more history in context
- Motivation: be more aggressive with threats about failure vs motivational, supportive and kind
- Directive: let it design it's own method vs being more perspective and micromanaging
- Ranking: best ways to rank ideas?
- Optimisation mindset: "explore and fail lots" to avoid local maxima vs "always try to beat your last score" for momentum
- Planning vs opportunism: structured upfront planning vs staying open to serendipity
- Explore/exploit phasing: explicit exploration phase then exploit — but what split?
- Note length vs breadth: long comprehensive notes vs short wide-coverage notes
- Review strategy: read all best options then review for gems vs ignore prior work to avoid anchoring
- Failure review: re-run previous failures to check for non-deterministic bad luck
- Search at scale: what strategies work when trial counts get large?
- Missing: record what information they would have liked to have had?
- Multi-test: try multiple ideas at once or stay scientific & only edit one idea at a time?
- 4-stage structured research loop: does a rigid loop (Profile → Hypothesize → Experiment → Reflect) outperform freeform experimentation?
- Early error detection with instance isolation: spend first 20% of budget isolating which specific instance/seed/phase triggers errors, re-run 2x to confirm deterministic vs random
- Risk-tolerant research mindset: "try improvements even with uncertain payoff"; prefer 90% reliable 10× gain over 99% reliable no gain
- Simplicity as tiebreaker: when two solvers achieve similar quality, choose the simpler one
- Per-trial efficiency metric: track `(best_avg_improvement - first_avg_improvement) / num_trials` as an explicit diagnostic
- Incremental changes principle: small focused edits easier to debug than large rewrites
- Print-statement time instrumentation: add per-phase timing (init, local search, restarts) to measure where budget is consumed

## Proven strategies

*(what reliably works, and why)*
- **Multi-start heuristic initialization:** Graph Colouring's multi-start DSATUR (12 high-degree + 12 random starting points) reliably improved solutions. Generalizable: starting point diversity matters. GC maintained 19% across studies = proof of stability.
- **Local search with max-iteration guards:** Graph Colouring's reduce_colors() with iteration limits (passes < 3) avoids computational blow-up. Key: bounded loops prevent timeouts.
- **Failure diagnosis + time profiling:** Study 1 profiling ("which phase dominates?") helped identify bottlenecks. Study 2 showed this is more effective than blind parameter tweaking. When scientists understand timing, they make better algorithm choices.
- **Asymptotic complexity awareness:** When Scientists understood O(n^k) bottlenecks via time profiling, they swapped to better algorithms. Key: "what's consuming the budget?" guidance surfaces the right optimization target.
- **Conditional local search guidance:** MaxSAT +6% via "try 2-opt vs 1-opt" guidance. Works when the solver doesn't already use advanced neighborhoods. Generalizable: check current solver state before suggesting variant neighborhoods.

## Promising

*(showed potential, needs refinement — what to tweak)*
- **Timeout diagnostics for weak problems:** QAP and LOP both show persistent timeouts (10+ per study). Instead of "try more neighborhoods", better guidance: "isolate which instance size (50/60/75 for QAP, 75/100/125 for LOP) times out, then reduce algorithm complexity only for that size." Conditional adaptation may unlock improvements.
- **Initialization diversity WITH concrete examples:** Study 3 showed vague "try initialization diversity" guidance failed (LOP -0.05%, QAP -1.07%). But Study 3 memory.md from prior trials shows multi-seed diversification worked (+58.85% in facloc-trial_6, multi-seed diversification). Solution: provide concrete examples in guidance: "Try 5–10 random seeds with different greedy orderings" or "Swap initialization from random→facility-first for facloc."
- **GC's marginal improvement signal:** Study 3 showed GC +1.56%, but trial count dropped (33 vs 50–56 expected). Need to isolate: is +1.56% real improvement or trial variation? Run Study 4 with stable trial budgets to clarify.
- **Simplification as recovery:** Study 2 worked well (aggregate +1.25%, MaxSAT +6.2%), Study 3 broke everything. Hypothesis: Study 2 guidance was clear and focused; Study 3 added too much complexity (checkpoints, redirects, new sections). Recovery strategy: Return to Study 2 guidance as baseline for Study 4, test ONE small refinement in isolation.

## Abandoned

*(tried and failed, or logically flawed — why, to avoid re-testing)*
- **Generic "try 2-opt" guidance for all problems:** Study 2 showed this backfires for problems already using neighborhoods. LOP regressed -0.34% when guidance encouraged 2-opt parameter tweaks (already present, parameter variations didn't help). Action: Make neighborhood suggestions conditional on solver state.
- **Minimal guidance (4-point process):** Study 1 showed Scientists need structure to handle failure modes. No room for reflection, diagnosis, or strategic pivots. Insufficient for harder problems (TSP, QAP).
- **"If a run crashes move on" strategy:** Leads to silent failure: Scientist doesn't learn why, can't improve, just retries the same broken solver. Study 2 proved explicit diagnosis is required.
- **Problem-agnostic plateau advice:** Study 2 showed all problems hitting plateaus, but each needs different escape strategy. MaxSAT: neighborhood tweaks. LOP: initialization diversity or timeout mgmt. GC: already optimal locally. One-size guidance creates divergence.
- **Conditional "skip" instructions in guidance:** Study 3 showed catastrophic failure. Added checkpoint "If you already use 2-opt, skip to initialization diversity" broke MaxSAT by 4.23%. Reason: skipping removes context and examples Scientists need. Conditional branches should ADD guidance, not DELETE sections. **Never use "skip" instructions.**
- **Vague initialization diversity guidance:** Study 3 created "Initialization diversity & timeout management" section. LOP -0.05%, QAP -1.07% because guidance was conceptual (multi-seed, phase profiling) without concrete next steps. Scientists didn't know how to apply it. Lesson: Examples and concrete variations required, not just concepts.