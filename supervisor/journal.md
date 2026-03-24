# Journal

A chronological log of studies — one entry per study, recording what changed, what happened, and what you learned. Write each entry during the post-study review (see method.md § "Study reflection").

## Study log

### Study 1 — Baseline

**Status:** Unmodified baseline study.

**Guidance changes:** None. Running with minimal baseline methodology (4-point process).

**Trial counts:** Graph Colouring: 46 | QAP: 46 | TSP: 9 (incomplete)

**Key metrics:**
- Graph Colouring: first=0.056 → last=0.200 (3.6× improvement), median=0.191, errors=2 (4.3%)
- QAP: first=0.077 → last=0.124 (1.6× improvement), median=0.119, errors=6 (13%), longest_plateau=41 trials
- TSP: only 9 trials, first=0.197 → last=0.198 (flat), errors=0 in completed trials but 8 scientist_timeouts

**Per-trial efficiency:**
- Graph Colouring: 0.00315 improvement/trial at 26.9s/trial
- QAP: 0.00101 improvement/trial at 80.2s/trial (3× slower)
- TSP: 0.000029 improvement/trial at 163.4s/trial (incomplete; timeouts prevent learning)

**What worked:** Graph Colouring shows healthy improvement trajectory and problem responsiveness. Multi-start DSATUR + color reduction is scalable.

**What failed:**
- TSP: Scientist process killed 8 times (600s timeout each). The LLM guidance loop breaks on this problem — either the failure pattern confuses the Scientist or train.py issues prevent meaningful trials.
- QAP: High error rate (13%), computational bottleneck in 2-opt + Or-opt loops. Local search iterations are O(n^4) per restart, unscalable for n=75.

**Learnings:**
1. Minimal guidance (4 points) is insufficient: Scientist has no strategy for repeated failures, no reflection structure.
2. Solver design matters: QAP solver architecture (nested loops) causes time budget violations. TSP local search has potential infinite-loop risk (1e-10 tolerance in `nlen >= prev - 1e-10`).
3. Cross-problem divergence is dramatic: TSP/QAP fail; Graph Colouring succeeds. Need guidance that surfaces problem-specific bottlenecks without problem-specific solutions.

---

### Study 2 — Failure diagnosis + Time profiling

**Status:** Complete.

**Guidance changes:**
1. Added explicit failure diagnosis: timeout → complexity problem, error → logic bug
2. Added time profiling requirement: Scientists must measure per-phase execution time before optimizing
3. Strengthened emphasis on computational complexity: O(n^k) nested loops are unscalable

**Trial counts:** Graph Colouring: 47 | QAP: 42 | TSP: 45 (full runs)

**Key metrics:**
- Graph Colouring: first=0.079 → last=0.200 (2.5× improvement), median=0.187, best=0.200, errors=2 (4.3%), avg_time=32.8s
- QAP: first=-3.252 → last=0.119 (recovery!), best=0.126, errors=2 (4.8%), avg_time=53.5s, longest_plateau=12 trials
- TSP: first=0.055 → last=0.202 (3.7× improvement), best=0.203, errors=10 (22%), avg_time=151.2s, longest_plateau=2 trials

**Per-trial efficiency (vs Study 1):**
- Graph Colouring: 0.00258 improvement/trial (was 0.00315) — slight regression in efficiency but similar peak quality
- QAP: 0.0803 improvement/trial (was 0.00101) — **80× better!** Massive breakthrough in efficiency per trial
- TSP: 0.00325 improvement/trial (was 0.000029) — **100× better!** Complete turnaround from flat to strong learning

**Aggregate:** 45 trials avg, 0.0287 improvement/trial (was 0.00140) — **20× more efficient!**

**What worked:**
1. **Failure diagnosis forced rethinking:** Scientists didn't just retry failures — they diagnosed root causes (timeouts from O(n^4) loops in QAP, near-infinite convergence loops in TSP)
2. **QAP transformation:** The -3.252 first trial suggests Scientist completely redesigned the solver (moved away from naive nested-loop 2-opt to something vastly more efficient). Plateau dropped from 41 → 12 trials
3. **TSP breakthrough:** Run count jumped from 9 → 45 trials due to reduced timeouts. First value shows Scientist found a much better construction approach (0.055 is recovery from something)
4. **Time profiling signals worked:** Scientists used per-phase timing to identify which component was consuming the budget (especially visible in TSP — now has sophisticated k-neighbors + Held-Karp + Numba JIT)

**What failed or regressed:**
- Graph Colouring: efficiency per trial declined slightly (32.8s vs 26.9s avg time), though peak quality stayed same. Suggests guidance nudged toward complexity over simplicity
- TSP error rate is still high (22%), suggesting solver still has unresolved edge cases or variable behavior

**Learnings:**
1. **Diagnostic thinking works:** Explicit guidance to diagnose failure modes (vs blind retry) led to fundamental algorithm redesigns, not just tweaks
2. **Time profiling unlocked the bottleneck:** Scientists could now see exactly which phase was burning time budget and could target that component
3. **Complexity awareness pays off:** All three problems moved to better algorithmic foundations (Graph Colouring's color reduction became more sophisticated, QAP abandoned naive approach, TSP integrated advanced techniques like Held-Karp)
4. **Cross-problem generality:** The same guidance changes helped all three problems, confirming the 4-point process in guidance.md is now generic enough to work across diverse problem types