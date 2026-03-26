# Ideas

- This is a list of ideas to test to improve how the Scientist conducts their work.
- DO NOT include (or consider) any problem specific ideas.
- DO NOT include any specific outcomes or per stage information (that is what `journal.md` is for).
- RED FLAG that you need to given seperate advice for each problem.
- STRICTLY keep to this format.

## Results analysis

`improvement_velocity`
- is particularly useful when ...


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
- **Meta-guidance approach (Study 6 candidate):** Instead of "try neighborhoods", teach Scientists diagnostic skills: "How do you know if the bottleneck is algorithmic (needs different approach) vs parametric (needs tuning)? Profile time, measure marginal gains, make conscious trade-offs." This works across all problems without diverging.
- **Problem-specific guidance branches (alternative for Study 6):** Create separate guidance sections per problem type (strong vs weak), with conditional entry: "For problems where neighborhood/phase methods work (FacLoc, MaxSAT), use X. For problems requiring algorithmic redesign (LOP, QAP), use Y." Explicit acknowledgment of divergence.

## Proven strategies

*(what reliably works, and why)*
...

## Promising

*(showed potential, needs refinement — what to tweak)*
...

## Abandoned

*(tried and failed, or logically flawed — why, to avoid re-testing)*
...