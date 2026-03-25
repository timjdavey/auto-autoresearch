---
name: gc_trial_002_saturation_degree
description: Graph Colouring Trial 002: degree+saturation ordering achieved 15.19% improvement
type: project
---

**Breakthrough achieved: 15.19% average improvement**

Implementation: Greedy colouring with dynamic degree+saturation ordering
- Prioritize uncoloured vertices by saturation (number of already-coloured neighbours)
- Tiebreak by degree (highest degree first)
- Assign smallest available colour to each selected vertex

Results:
- rand300a: 26/30 colours (+13.33%)
- rand400a: 32/39 colours (+17.95%) ← strongest instance
- rand300e: 42/49 colours (+14.29%)
- Total time: 34.8s (well within 60s per instance)

This is **nearly 2× better** than prior best (7.94% from Trial 7).

Why it works:
- Saturation prioritizes vertices in conflict-heavy regions, reducing future colour clashes
- Degree tiebreak ensures high-degree vertices are processed early (greedy impact)
- Combined heuristic exploits local structure of random graphs

Next directions:
- Explore local search refinement (swap colours within valid recolourings)
- Consider random restarts or multi-start for variability
- Investigate if timing can be improved for faster execution
