# Research Methodology Guidance

Your job is to improve the design of `train.py` through iterative experimentation and reflection.

## Research Loop (4 Stages)

### 1. Profile and Diagnose
Read `results.tsv` from your last trial(s). Look for:
- **Training time trends:** If `training_time` is consistently high (>60s) and errors mention "exceeded time budget", your algorithm is too expensive.
- **Improvement plateau:** If improvements levelled off, you're hitting local maxima — try diversification (more restarts, larger perturbations) or algorithm change.
- **Error patterns:** If errors repeat (same test, same problem), it's not randomness — diagnose the root cause before trying again.
- **Per-trial efficiency:** Calculate `(best_avg_improvement - first_avg_improvement) / num_trials`. Low number means slow exploration.

**Failure diagnosis:**
- **If timeout/scientist_error:** Do NOT retry the same code. The solver is too slow or has an infinite loop. Identify the bottleneck (nested O(n^k) loop? unbounded iteration? floating-point tolerance issue?) and fix complexity before next trial.
- **If solver_error but no timeout:** The change introduced a logic bug. Revert and adjust the hypothesis, not the debugging.
- **If high error rate:** Randomness is normal, but repeated errors in the same trial suggest a consistent issue — use print statements in train.py to debug.

### 2. Hypothesize
Propose ONE specific change:
- If time is the bottleneck: measure first. Add print statements to report execution time per phase (nearest-neighbor init: _s, local search: _s, restarts: _s). Identify which phase consumes the budget, then reduce that phase's iterations or switch to a faster algorithm.
- If exploration is stuck: try multi-start initialization, larger neighborhood sizes, or randomized perturbations.
- If a particular local-search method is expensive (e.g., O(n^4) nested loops): replace with a faster approximation. Avoid nested iteration counts that scale with problem size.

Do NOT try multiple changes at once — you won't know which one worked.

**Time profiling is required:** If you modify solver code, add timing instrumentation to measure per-phase cost. Report these measurements in your reflection notes.

### 3. Experiment
1. Edit `train.py` with your hypothesis.
2. Run `uv run prepare.py`.
3. Check for errors:
   - If `solver_error` or `scientist_timeout`: your change likely made things worse (too slow, infinite loop, etc.). Revert and try a different approach.
   - If `ok` status: proceed to stage 4.

### 4. Reflect
Compare your new results to your baseline:
- Did `best_avg_improvement` increase?
- Did `avg_training_time` decrease? (both matter)
- Did error rate drop?
- Did `improvement_per_trial` increase? (efficiency matters)
- Any surprised by the results?

Record your findings. Plan your next hypothesis based on what you learned. Repeat.

## Key Principles

- **Time budget is real:** If your solver takes >60s on a single test, you will see solver_error. Recognize this pattern and fix it (don't retry the same code). Measure complexity: O(n^k) nested loops are unscalable.
- **Failure is data:** If a trial fails, diagnose why. Timeout = asymptotic complexity problem. Error = logic bug. High error rate = randomness or debug opportunity. Do not retry without understanding the failure.
- **Incremental changes:** Small, focused edits are easier to understand and debug than large rewrites.
- **Profile before you optimize:** Add timing instrumentation to measure per-phase cost. Don't guess which part is slow — measure it.