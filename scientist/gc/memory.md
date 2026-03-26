---
name: GC Trial 53 - Plateau Diversification Attempts
description: Trial 53 investigation of plateau at 18.95%, testing diversification strategies
type: project
---

## Trial Status
- **avg_improvement: 17.84%** (stochastic variance from best 18.95%)
- **success_rate: 100%**
- **total_time: 61.6s**

## What We Tested (Trial 53)

Tried **3 diversification actions** to break 18.95% plateau:

### 1. Hybrid Initialization (FAILED)
- Idea: Use 3 different DSATUR tiebreakers (saturation_first, degree_first, degree_break) across 88 runs
- Result: **17.84%** (worse than 18.95%)
- Diagnosis: degree_first/degree_break strategies suboptimal for this problem; saturation_first remains superior
- Learning: Different tiebreaker doesn't reliably improve — current strategy is already good

### 2. Perturbation + Reoptimization (FAILED)
- Idea: Apply perturbation (random node reassignment) on every 3rd run, then re-run local search
- Result: **17.84%** (same quality, but time increased to 63.1s — over budget)
- Diagnosis: Perturbation adds computational cost without improving solution quality
- Learning: Escape mechanism needs different form, not simple perturbation

### 3. Increased Multi-Start (FAILED)
- Idea: Increase num_runs from 88→120 for small graphs, 52→80 for large
- Result: **17.84%** (no improvement, time exploded to 87s — way over budget)
- Diagnosis: More runs don't help if randomness already well-explored by 88 runs
- Learning: Computational ceiling; plateau is algorithmic, not sampling-limited

### 4. Variable Local Search Intensity (FAILED)
- Idea: 25% of runs use light local search (fewer 2-opt/greedy passes) to maintain diversity
- Result: **16.98%** (worse; rand400a regressed from 31→32 colours)
- Diagnosis: Underoptimizing hurts more than diversity helps
- Learning: All runs need full optimization; diversification must come elsewhere

## Plateau Diagnosis
- **Plateau level:** 18.95% (achieved trials 42, 47, 51, occasionally)
- **Stochastic variance:** ±1-2% depending on random seed luck
- **Root cause:** Algorithm well-tuned at local optimum; all 88 runs converge to similar quality
  - rand300a: usually 25 colours (16.67%), occasionally 24 (20%)
  - rand400a: stable at 31 colours (20.51%)
  - rand300e: stable at 41 colours (16.33%)

## Time Budget Analysis
- Current best config uses **~42s** (with headroom to 60s)
- All diversification attempts either:
  - Added computational cost without quality gain (perturbation, increased runs)
  - Degraded quality (hybrid init, light search)

## Confirmed Strong Local Optimum
The current DSATUR+1opt+2opt+greedy algorithm appears to be at a **strong local optimum**:
- Standard tiebreakers don't help
- Escape mechanisms (perturbation) don't help
- More exploration (increased runs) doesn't help
- Underoptimizing (light search) hurts

## Next Actions (for future trials)

### Option 1: Major Algorithm Change (High Risk, High Reward)
- Replace DSATUR with fundamentally different algorithm:
  - Simulated Annealing with temperature schedule
  - Genetic Algorithm / population-based search
  - Tabu Search with memory-based moves
- Risk: May not improve; time budget is tight for new algo
- Potential: Could escape strong local optimum

### Option 2: 3-opt Local Search (Medium Risk, Medium Reward)
- Add 3-opt moves (swap 3 nodes at once) on small graphs only (n≤300)
- Only on top N solutions from multi-start to fit budget
- Risk: Time budget may exceed 60s
- Potential: Stronger neighborhood might break plateau

### Option 3: Hybrid Local Search (Low Risk, Low-Medium Reward)
- Combine 2-opt + greedy + 3-opt selectively:
  - Full 2-opt on all runs
  - 3-opt only on rand300a (has most headroom, got 24 colours once)
  - Skip on large graphs where time is tight
- Risk: Low; can be tuned to fit budget
- Potential: Targeted optimization where we have time

### Option 4: Accept Plateau, Document
- If further trials fail to beat 18.95%, accept this as local optimum
- Current solver is robust and reliable at 18.95%
- Strong signal that fundamentally different approach needed

## Notes
- Stochastic variance is real (17.84% vs 18.95% from same code)
- Time constraint is binding (any new feature costs time)
- DSATUR + 2-opt + greedy_highest_color_removal is a **strong local optimum**
- Need algorithmic innovation, not parameter tuning, to break further
