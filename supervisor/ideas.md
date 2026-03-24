# Ideas

List of ideas to test to improve how the Scientist conducts their work.
DO NOT include (or consider) any problem specific ideas.
RED FLAG that you need to given seperate advice for each problem.

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

## Proven strategies

*(what reliably works, and why)*
- **Multi-start heuristic initialization:** Graph Colouring's multi-start DSATUR (12 high-degree + 12 random starting points) reliably improved solutions. Generalizable: starting point diversity matters.
- **Local search with max-iteration guards:** Graph Colouring's reduce_colors() with iteration limits (passes < 3) avoids computational blow-up. Key: bounded loops prevent timeouts.
- **Failure diagnosis + time profiling:** Study 2 showed this transforms problem-solving: explicit diagnosis of timeouts and errors led to 80-100× improvements in QAP/TSP per-trial efficiency. Scientists didn't just retry — they fundamentally redesigned solvers based on understanding root causes.
- **Asymptotic complexity awareness:** When Scientists understood O(n^k) bottlenecks via time profiling, they swapped to better algorithms (TSP: added Held-Karp for small n, adaptive k-neighbors, Numba JIT). Key: "what's consuming the budget?" guidance surfaces the right optimization target.

## Promising

*(showed potential, needs refinement — what to tweak)*
- **Edge case detection for error modes:** TSP still has 22% error rate (solver_error + timeouts). Investigate what specific situations trigger these: is it a particular instance size, solver phase, or random seed issue? Scientists may need guidance on detecting and isolating non-deterministic failures.
- **Solver stability across instance scales:** TSP training time is 151s (vs 53s for QAP, 33s for Graph Colouring). The solver works but is expensive. Future guidance could nudge toward per-instance scaling (e.g., "what algorithm choices differ for n=300 vs n=750?")
- **Multi-algorithm portfolios:** TSP's final solver uses Held-Karp + ILS + 2-opt + or-opt + SA. This works but is complex. Could guidance help Scientists systematically measure which components contribute value vs complexity?

## Study 2 Plan (completed)

**Focus:** Explicit failure diagnosis + time-aware solver profiling.

**Changes made to guidance.md:**
1. ✅ Add failure diagnosis section: when to revert vs pivot (timeouts = complexity problem, errors = logic problem)
2. ✅ Add time profiling requirement: Scientists must measure and report per-phase execution time
3. ✅ Strengthen emphasis on computational complexity: O(n^k) nested loops are unscalable

**Results:** Massive success. 20× improvement in per-trial efficiency, 80-100× gains in QAP/TSP. Scientists went from silent failure to active diagnosis and algorithmic redesign.

---

## Study 3 Plan (completed — FAILED)

**Focus:** Edge case isolation + solver component measurement.

**Results:** Catastrophic regression. Error rate dropped to zero, but per-trial efficiency collapsed 36× (0.0287 → 0.000791). QAP/TSP went nearly flat. The 5% simplification threshold was too conservative; Scientists spent time measuring rather than optimizing.

**Root cause:** Guidance prioritized "stability and simplicity" over "exploration and improvement." The time-budget trade-off was inverted: measuring edge cases consumed resources that should have gone to optimization.

**Why it failed:** Research mode and production mode have opposite goals. In research, a 90% reliable solver that improves 10× is better than a 99% reliable solver that doesn't improve. The "5% threshold" principle prevented Scientists from trying ideas with uncertain payoff — exactly the wrong incentive for exploration.

---

## Study 4 Plan (planned)

**Focus:** Restore exploration velocity while keeping error detection.

**Rationale:**
- Study 2 showed aggressive algorithmic redesign works (80× QAP gain). Study 3's defensive posture killed momentum.
- TSP/QAP errors are now rare; we can afford to prioritize improvement over stability.
- Cross-problem divergence (Graph Colouring thrives with multi-start; QAP needs 2-opt; TSP needs advanced LS) suggests guidance should be less prescriptive on algorithm choice, more prescriptive on measurement discipline.

**Changes to guidance.md:**
1. **Remove the 5% simplification threshold.** Replace with: "Measure contribution of each component, but try improvements even with uncertain payoff. You learn from failures."
2. **Split time budget explicitly:** "Use the first 20% of your trials for edge case detection and profile measurements. Use the remaining 80% for aggressive exploration and optimization."
3. **Reframe "simplicity":** Change from "prefer 80% reliable" to "if two solvers achieve similar quality, choose the simpler one. But don't sacrifice quality for simplicity."
4. **Restore exploration language:** "Diversity matters. Try multi-start initialization, larger neighborhoods, new algorithm combinations. Cross-problem learning from archive/ may suggest approaches."

**Expected outcome:** Per-trial efficiency back to Study 2 levels (0.01+), errors stay low (<5%), TSP/QAP resume learning curves.

## Abandoned

*(tried and failed, or logically flawed — why, to avoid re-testing)*
- **Minimal guidance (4-point process):** Study 1 showed Scientists need structure to handle failure modes. No room for reflection, diagnosis, or strategic pivots. Insufficient for harder problems (TSP, QAP).
- **"If a run crashes move on" strategy:** Leads to silent failure: Scientist doesn't learn why, can't improve, just retries the same broken solver. Study 2 proved explicit diagnosis is required.
- **Graph Colouring expansion to 2/3-color reduction:** Study 2 shows Graph Colouring efficiency per trial regressed slightly (0.00258 vs 0.00315), suggesting the Scientist may have overfit on complexity. Keep guidance focused on simplicity for this problem.
- **Unfocused solver expansion (TSP):** TSP is now very complex (Held-Karp + ILS + 2-opt + or-opt + SA + Numba JIT). It works but at high training cost (151s). Future guidance should avoid "add more algorithms" and instead focus on "measure contribution of each component."