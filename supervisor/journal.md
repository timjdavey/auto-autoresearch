# Journal

A chronological log of studies — one entry per study, recording what changed, what happened, and what you learned. Write each entry during the post-study review (see method.md § "Study reflection").

## Study log

### Study 1 — Baseline

**Changes made:** None. This is an unmodified baseline study to measure how Scientists perform with no Supervisor guidance (guidance.md was just: come up with idea, edit, run, move on if crash).

**Result (manual — evaluate.py crashed on TIMEOUT rows):**
- TSP: 5 results.tsv entries across 2 trials. Started 0.097 → peaked 0.111. Total improvement: +0.014. 1 timeout.
- Graph colouring: 11 entries across 2 trials. Started 0.256 → stayed 0.256. Total improvement: 0.0. 2 crashes (-10.0), 2 timeouts.
- Aggregate: Modest TSP gains, zero graph colouring gains. High instability (timeouts, crashes).

**Analysis:**
- Both Scientists built sophisticated code from a simple baseline (TSP: Held-Karp + ILS + 3-opt w/ numba; GC: DSatur + RLF + TabuCol w/ numba). They're clearly capable coders.
- TSP Scientist used the time budget well (27s deadline) and made real progress. But improvement plateaued after first successful iteration.
- GC Scientist built complex code but couldn't beat the initial approach. Had regressions (-10.0 = crash penalty) suggesting risky edits without validation. Recovered but wasted trials.
- Timeouts (600s kill) happened in both problems — Scientists spending too long thinking/editing without running evaluation.
- Current guidance is too minimal — "if a run crashes move on" doesn't help with: planning, building on prior work, using time wisely, or avoiding regressions.

**Infrastructure bug:** evaluate.py `load_results()` can't parse TIMEOUT rows (non-numeric avg_improvement). This blocks `analyse_and_save()`.

**Learnings for next study:**
1. Scientists need guidance on reading and building upon prior trial results (they start fresh each trial).
2. Need to emphasise: run evaluation early and often — don't spend 10 mins coding without testing.
3. Need guidance on regression prevention: test before committing big changes.
4. Scientists are already good at using numba/numpy — no need to push tools, but should guide the *process*.
