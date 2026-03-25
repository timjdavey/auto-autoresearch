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