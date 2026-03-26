# Research Methodology Guidance

Your job is to improve the design of `train.py` through systematic experimentation and diagnosis.

## Turn budget — HARD LIMIT

You have a **hard turn limit** enforced by the harness. When you hit it, the process stops immediately — any unsaved work is lost. Each turn = one assistant response. A typical plan/edit/run cycle costs 3–5 turns.

**Rules:**
- **Write to `memory.md` continuously** — after every meaningful result, not just at the end. If the process stops mid-trial, memory.md is the only thing that persists.
- **Reserve your last 2–3 turns** for saving state: update memory.md with your best findings, what worked, what didn't, and what to try next.
- **Don't start a new idea if you're near the limit** — consolidate and document instead.

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
- **Plateau detections:** trial number, current best, diversification action taken, result
- **Error diagnostics:** which instance/seed, suspected phase, isolation steps, resolution

## Plateau detection & breaking — MANDATORY PROTOCOL

**Recognizing a plateau:** After ~10 trials without a new best solution, you've hit a local optimum. This is a CRITICAL signal. Continuing the same approach wastes trials.

**MANDATORY action on plateau detection:**
When plateau ≥ 10 trials, you MUST take a diversification action in the very next trial. This is non-negotiable. Your choices (in order of effort and novelty):

1. **Restart diversification (easiest, 1 trial):**
   - Change random seed + re-initialize solver state from scratch
   - Swap initialization strategy (random vs greedy vs multi-start)
   - Adjust algorithm parameters (e.g., temperature in simulated annealing, mutation rate, neighborhood size)
   - Example: "if using single-seed greedy init, try 5 random restarts with different seeds"

2. **Neighborhood variant (medium effort, 1-2 trials):**
   - If you have 1-opt local search, try 2-opt (explores more configurations)
   - If you have greedy construction, try a different tiebreaker (e.g., "best marginal gain" → "first improvement")
   - If you have one neighborhood, run multiple simultaneously and pick best result
   - Example: "prior solver uses 1-opt only; add 2-opt moves for a few iterations on top, measure impact vs cost"
   - **Key:** measure before/after. If 2-opt costs 40% more time but gains 1%, it's not worth it. If it gains 5%, it is.

3. **Root cause profiling (2-3 trials):**
   - Use `memory.md` to record per-phase timing: initialization, construction, local search, restart
   - Which phase takes 60%+ of budget? That's your optimization target.
   - Swap that phase with a faster algorithm or reduce its iterations
   - Example: "local search dominates (80% of time); replace with faster 1-opt variant or limit to fewer iterations"

4. **Major redesign (only after 1-3 fail):**
   - Consider fundamentally different algorithm (e.g., switch from greedy+1-opt to simulated annealing, or add 3-opt if stuck in tight local optima)
   - Only pursue if profiling reveals the current approach is algorithmically limited, not just parametrically weak

**Do NOT ignore plateaus** — they don't break by accident. **Do NOT repeat the same change** hoping it improves next time — it won't.

## Neighborhood structure — local search variants

Local search is a powerful way to escape plateaus. Understanding what "neighborhoods" mean helps you vary your solver intelligently.

**Before suggesting variants:** Check your current `train.py` carefully. If you already have 2-opt, 3-opt, or multi-start, focus on the strengths and weaknesses of your current approach. Don't waste time on parameter tweaking if the neighborhood itself isn't the bottleneck.

**Red flag:** If you've already tried varying a neighborhood's parameters (iterations, acceptance criteria) without improvement, the issue is NOT more parameter tuning — it's that the neighborhood itself is not the bottleneck. Switch to initialization diversity (see below) or timeout/phase restructuring instead.

**Common neighborhoods (in increasing complexity):**
- **1-opt (swap):** Change one element at a time. Fast, finds nearby improvements, weak on hard problems.
- **2-opt (swap pairs):** Change two elements together, often reordering or reconnecting. Stronger than 1-opt, ~4-8× slower.
- **3-opt (swap triples):** Even stronger but expensive (20–40× slower). Only use on small instances or if 2-opt plateaus.
- **Greedy variants:** Different tie-breaking rules in construction phase (best marginal gain vs first-fit vs most-constrained).
- **Multi-start:** Run construction multiple times from different random seeds, keep the best result.

**How to measure neighborhood impact (for new neighborhoods only):**
1. Time the baseline solver end-to-end.
2. Add a neighborhood variant (e.g., add 2-opt on top of 1-opt).
3. Measure new end-to-end time and solution quality.
4. If quality improves by >5% for ≤20% extra time, it's worth keeping.
5. Record the trial result and time breakdown in `memory.md`.

**When to use which:**
- **Stuck early (trial <10)?** Time budget may be insufficient. Reduce iterations of heavy phases, or profile to find bottlenecks.
- **Stuck mid-plateau (trial 10-30) and no advanced neighborhoods?** Try 2-opt or multi-start restarts to escape the local basin.
- **Already using advanced neighborhoods and still stuck?** Don't tweak their parameters. Instead, try initialization diversity (different seeds, greedy variants, or problem-specific construction heuristics) or timeout/phase restructuring (see Timeout and Phase Profiling below).
- **Stuck late (trial 40+)?** If profiling shows time available, try 3-opt on small instances only; otherwise accept local optimum or redesign.

## Initialization diversity — when local search alone doesn't break plateaus

If you're stuck on a plateau and have tried local search variants, initialization diversity is your next lever. Different starting solutions can escape the same local basin your current initialization gets trapped in.

**Concrete strategies to try (in order of effort):**

1. **Multi-seed restarts (easiest, 1 trial):**
   - Run your solver 5–10 times with **different random seeds**, keep best result.
   - Example: `for seed in [1, 42, 123, 456, 789]: best_result = max(best_result, solve(instance, seed))`
   - Cost: ~2–5 times slower; benefit: avoids seed-specific local optima.

2. **Greedy construction variants (easy, 1-2 trials):**
   - Use different tie-breaking or ordering rules in your greedy construction phase.
   - Examples:
     - **Facility Location:** Try "random facility-first init" vs "demand-first init" vs "cost-weighted init"
     - **Graph Colouring:** Try "high-degree-first ordering" vs "saturation-based ordering" vs "random ordering"
     - **QAP/LOP:** Try "best marginal cost" vs "first-fit" vs "random tie-breaking"
   - Cost: minimal (just reorder construction loop); benefit: different solution landscape, can escape plateaus.

3. **Problem-specific construction (medium, 1-2 trials):**
   - If you understand problem structure, seed your initial solution based on that insight.
   - Examples:
     - **Facility Location:** Start with a few "obvious" facilities (low cost or high demand) and build from there.
     - **Graph Colouring:** Assign colors to high-degree nodes first, fill in easier nodes later.
     - **LOP:** Order rows by some heuristic (sum of distances, correlation with target) instead of random.
   - Cost: 1 trial to design + 1 to measure; benefit: leverages domain knowledge, often large gains.

**When to try which:** If you're already stuck on a plateau (trial 10+) and local search variants didn't help, try multi-seed first (easiest, quick win). If that stalls too, try greedy variants or problem-specific construction.

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