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

## Promising

*(showed potential, needs refinement — what to tweak)*
- **Failure recovery strategy:** TSP/QAP timeouts suggest Scientists need explicit guidance on how to respond when trials fail. Instead of blind retries, structure reflection: "What caused the timeout? Is the solver inefficient or the guidance wrong?"
- **Time-aware solver design:** QAP's 80s+ training times and TSP's risk of infinite loops suggest Scientist should track solver execution time, profile bottlenecks, and prioritize reducing asymptotic complexity over trying more iterations.
- **Floating-point safeguards:** TSP uses `nlen >= prev - 1e-10` in convergence checks. At that tolerance, rounding error can cause false "no improvement" signals. Scientist should look for tolerance-related infinite loops.
- **Computational budget visibility:** Scientist should profile per-instance time breakdown (e.g., nearest-neighbor vs local search vs restarts) and identify which phase consumes the budget.

## Abandoned

*(tried and failed, or logically flawed — why, to avoid re-testing)*
- **Minimal guidance (4-point process):** Study 1 showed Scientists need structure to handle failure modes. No room for reflection, diagnosis, or strategic pivots. Insufficient for harder problems (TSP, QAP).
- **"If a run crashes move on" strategy:** Leads to silent failure: Scientist doesn't learn why, can't improve, just retries the same broken solver.