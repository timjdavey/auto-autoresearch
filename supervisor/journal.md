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