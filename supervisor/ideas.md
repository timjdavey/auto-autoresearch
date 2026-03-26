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

- Memory format: journal of historical logs vs ideas list vs freeform notes — which helps Scientists most?
- Reflection structure: hypothesis-then-test vs freeform experimentation
- Perceived trial budget: inflate count to encourage risk-taking, or deflate to force concentrated bets
- Optimisation mindset: "explore and fail lots" vs "always beat your last score"
- Explore/exploit phasing: explicit exploration phase then exploit — what split?
- Note length vs breadth: long comprehensive notes vs short wide-coverage notes
- Review strategy: read all prior work vs ignore to avoid anchoring
- Failure review: re-run previous failures to check for non-deterministic bad luck
- Multi-test: try multiple ideas at once vs only edit one at a time
- Meta-guidance approach: teach diagnostic skills ("is the bottleneck algorithmic vs parametric?") instead of prescribing specific algorithms — works generically across problems
- Search at scale: what strategies work when trial counts get large?

## Proven strategies (from prior cycle)

- **Concrete neighborhood examples help:** Study 2 showed +6.22% MaxSAT breakthrough from explicit 1-opt/2-opt guidance
- **Never use "skip" instructions:** Study 3 proved conditional skips cause catastrophic regressions (-4.23% MaxSAT)
- **Simplicity over complexity:** Study 2 (simple additions) beat Study 3 (complex conditionals)
- **Time profiling guidance works:** Scientists who profiled phases found bottlenecks faster
- **Memory.md continuous writing:** Prevents lost work on early termination

## Promising

- Meta-guidance (diagnostic skills over prescriptive algorithms) — untested but addresses prior cycle's divergence problem
- Explore/exploit phase split — plateau data suggests first half should be exploration

## Abandoned (from prior cycle)

- **Conditional "skip" checkpoints:** Caused MaxSAT -4.23% regression (Study 3). Never skip guidance sections.
- **Problem-specific construction examples:** LOP -4.18% regression (Study 4). Concrete examples for specific problems cause re-exploration of exhausted space.
- **Parameter tweaking as diversification:** Multiple studies showed adjusting parameters of same algorithm wastes trials