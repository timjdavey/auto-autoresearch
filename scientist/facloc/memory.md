---
name: Facloc Trial Progress
description: Track best approaches and improvements for Facility Location problem
type: project
---

## Current Best: 61.76% avg_improvement (Trial 041 - Optimized)

**Trial 041 (LATEST - OPTIMIZED FOR SPEED & QUALITY):**
- Approach: Multi-strategy initialization + optimized local search (no 3-opt)
- Results: rand30_100a 56.18%, rand40_120a 64.20%, rand50_150a 64.92% → avg 61.76%
- Time: 38.7s total (fast & stable, was seeing 100+ in earlier trials)
- Algorithm changes from Trial 038:
  1. **REMOVED 3-opt** — O(n²) neighborhood was expensive with marginal gains. Iteration would hit >100s on larger instances
  2. **Kept 2-opt** — essential for quality, performs swap between open facilities
  3. **Reduced max_iterations** — 28 instead of 30 (minimal quality impact)
  4. **Tuned initialization** — 9 strategies total:
     - Greedy nearest (best-fit)
     - Greedy worst-fit (diversity)
     - Facility-minimizing with budgets: 5%, 10%, 15%, 25%
     - Random initializations with seeds: 42, 123, 456
- Local search neighborhoods (in order):
  - Facility closing (expensive first), reassign clients greedily
  - Individual client reassignment (first-improvement, incremental cost)
  - 2-opt: swap client between two open facilities (first-improvement)

**Key insight from optimization:**
- 3-opt deletion was critical — removed O(n²) cost that was causing timeouts
- Quality plateau (61.76%) is robust across initialization strategies
- 9 strategies provides good diversity without excessive overhead
- 2-opt is essential; greedy 1-opt alone gives 60.47% (lost 1.3pp)

**Trial history for this session:**
- Trial 038: 61.76% (8 long strategies, 30 iter, had 3-opt - slow)
- Trial 040: 60.47% (3 strategies, no 2-opt/3-opt - regression)
- Trial 041: 61.76% (9 strategies, 28 iter, 2-opt only - STABLE & FAST)
