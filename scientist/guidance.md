# Research Methodology Guidance

Your job is to improve the design of `train.py` through systematic experimentation and diagnosis.

## Core loop

1. **Come up with an idea** — what algorithmic change, parameter tweak, or initialization strategy might help?
2. **Edit the file** — implement it in `train.py`.
3. **Run the evaluation** — `uv run prepare.py` to measure impact.
4. **Reflect and diagnose** — if it crashes or fails, diagnose WHY (which instance size? which solver phase? deterministic or random?). Don't just move on.

## Key principles

**Failure diagnosis matters:** When solver crashes or timeouts occur, use first ~10% of budget to isolate the failure in detail (which specific instance, seed, or algorithm phase). This is not wasted time — it points to the actual problem. Study 2 showed 80–100× efficiency gains came from diagnosing timeouts and root-causing algorithmic bottlenecks.

**Measure before and after:** For each idea, record the metric BEFORE (from prior `results.tsv` if available) and AFTER. If a complex change gives <2% improvement, consider if simpler alternatives exist. But don't prematurely reject ideas — measure properly first.

**Trade velocity for exploration early:** You have a full trial budget. Use the first half to explore: try multiple directions, measure their impact, understand which bottlenecks matter. Use the second half to focus on what works. Switching too early to "stability over improvement" wastes the exploration phase.

**Time profiling wins:** Add timing instruments (e.g., `print(f"phase_X: {elapsed}s")`) to understand where your budget is consumed. Problems where one phase takes 60%+ of time often have straightforward optimizations (better algorithm, JIT, early termination).

**Simplicity as a final tiebreaker:** If two solvers achieve similar final quality, prefer the simpler one for the next round. Avoid code bloat. But during exploration, complexity is acceptable if it unlocks improvement.

**Memory.md for persistence:** Use `memory.md` to record:
- Best ideas so far and why they work
- Bottlenecks and root causes
- Parameter ranges that work well
- Failed approaches and why (so you don't re-test them)

## Plateau detection & breaking — MANDATORY PROTOCOL

**Recognizing a plateau:** After ~10 trials without a new best solution, you've hit a local optimum. This is a CRITICAL signal. Continuing the same approach wastes trials.

**MANDATORY action on plateau detection:**
When plateau ≥ 10 trials, you MUST take a diversification action in the very next trial. This is non-negotiable. Your choices (in order of effort):
1. **Restart diversification (easiest):** Change random seed, re-initialize solver state, or swap algorithm parameters. This costs 1 trial, forces a different path.
2. **Algorithm variant:** If current solver has components (e.g., multiple local search neighborhoods), swap to one you haven't tested. Different heuristic = different starting basin.
3. **Root cause profiling:** Where is time spent in your current best solver? Can you replace the bottleneck phase with a faster algorithm?
4. **Major redesign:** Only if 1-3 fail multiple times. Consider fundamentally different approach (different heuristic class, search paradigm).

Do NOT ignore plateaus and hope for breakthrough — they don't happen by accident. Do NOT repeat the same code change hoping it improves next time — it won't.

**Error-first exploration — MANDATORY PROTOCOL**

**If any crash occurs in the first ~30% of budget**, you MUST pause new feature exploration and diagnose immediately. This is not optional:

1. **Isolate the failure** (~3-5 trials):
   - Does it crash on ALL instances or only some? Test small, medium, and large separately.
   - Is it a specific seed? Re-run the failing instance 2-3 times to confirm deterministic vs random bad luck.
   - Which algorithm phase? Add timing/debug output to pinpoint: initialization? solver loop? cleanup?

2. **Once isolated, fix or document** (~2-3 trials):
   - If the crash has a fix (bounds check, timeout, algorithm swap), implement and re-test.
   - If it's non-deterministic bad luck, document and continue exploration.
   - If deterministic but unfixable, either redesign that phase or accept the constraint.

3. **Resume exploration** only after crashes are fixed or fully understood. Continuing to develop new features while crashes persist is pure waste.

**Rationale:** Study data shows that unsolved crashes lead to cascading failures — the Scientist develops around a broken solver, wastes trials on features that might help but don't fix the root problem. 16% error rates in early studies came from skipping this step. Investing 5-10% of budget to isolate crashes saves 30-50% on wasted feature exploration.