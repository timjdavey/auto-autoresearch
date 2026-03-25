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

**Status:** ✓ Completed 2026-03-24.

**Guidance:** Expanded methodology emphasizing failure diagnosis, time profiling, early exploration, and persistence through complex changes.

**Results:**
- **facloc:** 27.6% improvement over 61 trials. Tailing off (plateau 19). 11 new bests, 0 errors. ✓
- **gc:** 10.2% improvement over 42 trials. SEVERE tailing off (plateau 40!). Only 2 new bests. 1 error. ⚠️
- **lop:** 3.1% improvement over 25 trials. NOT tailing off. 6 new bests, 4 errors (16% rate). ⚠️
- **qap:** 674% improvement over 41 trials. Tailing off (plateau 11). 8 new bests, 4 errors. ✓✓✓
- **Aggregate:** 178.8% improvement. Significant divergence between problems.

**What worked:**
- Failure diagnosis + time profiling led to QAP's exceptional recovery (80-100× efficiency restored).
- facloc and qap both achieved strong sustained improvement.
- Aggressive exploration mindset validated: not premature stability bias.

**What failed:**
- **gc severely underperforming:** 40-trial plateau indicates guidance is NOT helping escape local optima. Only 2 new bests per 42 trials = 4.7% success rate.
- **lop error rate too high:** 16% crashes suggests error diagnosis guidance insufficient. Scientists hitting bugs faster than they're solving them.
- **Divergence signal:** Same guidance producing 674% for qap but only 3.1% for lop. This is "too specific" or "unevenly applicable" problem.

**Hypothesis for Study 5:** gc and lop need targeted help:
- gc: needs stronger restart/diversification to break 40-trial plateau
- lop: needs better error isolation before exploration continues
- Refine guidance to be more universally applicable (reduce divergence).

---

### Study 5 — Improve guidance for diverging problems

**Status:** Planning next study.

**Plan:**
- Add explicit restart/diversification strategy for problems stuck in long plateaus.
- Enhance error diagnosis guidance: lop should prioritize crash root-causing in first trials.
- Generic principle: "If plateau > 15 trials, diversify or change strategy."
- Monitor divergence: all problems should show improvement, not just some.

---