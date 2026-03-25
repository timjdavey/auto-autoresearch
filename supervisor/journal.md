# Journal

A chronological log of studies — one entry per study, recording what changed, what happened, and what you learned. Write each entry during the post-study review (see method.md § "Study reflection").

## Study log

### Study 1 — Baseline

**Status:** Baseline study with unmodified `guidance.md`.

**Guidance:** Minimal 4-point methodology (come up with idea → edit file → run evaluation → move on if crash).

**Purpose:** Establish baseline performance across all problems with no structured guidance beyond the basic process loop.

**Expected outcome:** Quantify how each problem performs with minimal researcher scaffolding. Sets performance ceiling for what unguided trial-and-error can achieve.

---

### Study 4 — Restore exploration-focused guidance

**Status:** Plan for next study.

**Guidance:** Expanded methodology emphasizing failure diagnosis, time profiling, early exploration, and persistence through complex changes. Removes premature simplification bias that Study 3 introduced.

**Key changes from baseline:**
- Explicit failure diagnosis: when crashes occur, Scientists spend 10% of budget isolating root cause (instance size? seed? algorithm phase?), not just moving on.
- Time profiling as first-class optimization: measure where budget is consumed; target high-cost phases.
- Trade velocity for exploration early: use first half of trials to explore multiple directions, second half to focus. Avoid premature "stability over improvement" mindset.
- Measurement discipline: before/after metrics for each idea; reject only ideas with <2% improvement after proper measurement.
- Memory.md for persistence: record bottlenecks, parameter ranges, failed approaches to guide future trials.

**Hypothesis:** Study 3 collapsed efficiency by being too conservative with the "5% simplification threshold". Restoration of aggressive exploration (combined with better failure diagnosis) will recover the ~80× QAP efficiency gain seen in Study 2.

**Expected trajectory:** all problems show sustained improvement with no forced plateau; lower error rate via proactive diagnosis.

---