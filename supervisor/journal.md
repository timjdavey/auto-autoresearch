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

### Study 5 — Mandatory protocols for plateaus and errors

**Status:** ✓ Planning phase complete. Guidance updated 2026-03-25.

**Diagnosis of Study 4 divergence:**
- GC hit a 40-trial plateau despite having plateau-breaking guidance. This suggests the guidance was too permissive: "try diversification" was treated as optional.
- LOP hit 16% error rate. Current error-first guidance exists but is insufficiently aggressive — errors were not prioritized for isolation.
- **Root cause:** Existing guidance uses suggestive language ("try", "consider"). Scientists need mandatory protocols, not options.

**Changes made to `guidance.md`:**
1. **Plateau protocol:** Changed threshold from 15 to 10 trials. Made action MANDATORY: "When plateau ≥ 10 trials, you MUST take a diversification action in the very next trial. This is non-negotiable."
2. **Error protocol:** Made error-first exploration MANDATORY: "If any crash in first ~30% of budget, you MUST pause new features and diagnose immediately. This is not optional."
3. **Added rationale:** Explained why unsolved crashes cascade (16% error rate study evidence) and why mandatory protocols matter.
4. **Added specifics:** Concrete isolation steps (test instance sizes, check deterministic vs random, add timing).

**Expected outcome:**
- GC: forced diversification every 10 trials should break the 40-trial plateau.
- LOP: error-first protocol should catch crashes before they cascade, reducing error rate from 16% to <5%.
- facloc/qap: should maintain good performance (guidance not regressive for them).

**Success metrics:**
- All problems improve or maintain performance.
- GC's longest plateau drops from 40 to <20 trials.
- LOP's error rate drops from 16% to <5%.
- Divergence (spread in per-problem improvements) reduces.

---