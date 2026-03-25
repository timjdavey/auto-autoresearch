---
name: LOP Trial Progression
description: LOP solver improvement trials and techniques
type: project
---

## Trial 001 — Greedy Row-Sum Heuristic
**Result:** 3.15% avg_improvement
- Approach: Sort elements by sum of outgoing weights (row sum), descending
- Rationale: Elements with high outgoing weight placed early maximize upper-triangle contribution
- Performance: rand75a +3.00%, rand100a +2.84%, rand125a +3.61%
- Time: Fast (0.247s total)

## Next Ideas (Priority Order)
1. Local search (1-opt) on top of greedy to refine ordering
2. Try incoming weight (column sum) instead of outgoing
3. Hybrid: combine row and column scores with weights
4. Incremental construction: build permutation by selecting best next element

## Notes
- Current baseline beats identity permutation modestly
- Room for significant improvement through local search refinement
