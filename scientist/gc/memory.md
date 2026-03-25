# Graph Colouring Scientist Memory

## Trial 37+: Plateau Diagnosis → Still 16.30% (plateau confirmed)

**Best stable score: 16.30% improvement**
- Breakdown: rand300a +16.67%, rand400a +17.95%, rand300e +14.29%
- Weak bottleneck confirmed: rand300e (dense graph, ~49 baseline colours, only 14.29% improvement)

### Tested and FAILED in this trial:
1. **2-opt final refinement** (all variants): No improvement, sometimes worse (15.19%)
   - Targeted 2-opt on dense graphs: triggered wrong instances, degraded performance
   - Full 2-opt as final phase: not helpful for this problem structure

2. **Increased ILS iterations** (10→15) + **stronger perturbation** (n_nodes//12 → n_nodes//10):
   - No improvement, slightly slower
   - Perturbation already strong enough at n_nodes//12

3. **Multi-start vs ILS balance shift** (20 runs→30 runs, 10 ILS→5 ILS):
   - No improvement, significantly slower (8.28s vs 5.9s)
   - Confirms memory finding: "Multi-start beats ILS iterations" doesn't apply here (already optimized)

4. **Density-aware heuristic selection** (bias RLF for dense graphs):
   - RLF supposed to excel at dense instances, but didn't help
   - Suggests RLF implementation may be suboptimal or instance characteristics are different

### Root cause analysis:
- **rand300e bottleneck is structural**: 14.29% improvement is consistent across all variants
- **Not an exploration problem**: We've tried major algorithm variants (DSATUR/RLF/Smallest-Last), multi-start, ILS, perturbation strength tuning
- **Likely need fundamental algorithmic change**, not parameter tuning:
  - Current: Greedy construction + 1-opt + ILS perturbation
  - Possible next: Tabu search, VND (Variable Neighborhood Descent), or hybrid metaheuristic
  - Or: Fix RLF implementation (lines 49-53 look buggy)

### Recommendations for next trial:
1. **Fix RLF bug** (lines 49-53: colour assignment logic seems incorrect)
2. **Implement Tabu search** variant to replace ILS perturbation (keeps tabu list of recently-flipped nodes)
3. **Try Variable Neighborhood Descent** (systematically vary neighborhood size)
4. **Accept plateau**: If 1-3 don't work, 16.30% may be ceiling for this approach class

## Trial 6-9: Plateau Escape & Stabilization → 16.30%

**Final best: 16.30% improvement** (stable across multiple runs)
- Breakdown: rand300a +16.67% (25), rand400a +17.95% (32), rand300e +14.29% (42)
- Total time: ~5.9s (within budget)
- **Escaped plateau at 15.19%** using mandatory diversification

### Successful changes:
1. **Increased multi-start:** num_runs 12 → 20 (more chances for good constructions)
2. **Added RLF heuristic:** Now rotate DSATUR/Smallest-Last/RLF every 5 runs (3 diverse algorithms)
3. **Aggressive perturbation:** First ILS iteration uses n_nodes//12 (~25 nodes for n=300), then gradually reduces (vs static 3)
4. **Final refinement:** After selecting best solution, apply 1-opt exhaustively (max_iterations=1000)

### Tested but ineffective:
- Perturbation strength n_nodes//12 vs n_nodes//15 (no difference)
- num_runs 20 vs 25 (diminishing returns, slower)
- Fixed seed (n_nodes+n_edges) (no improvement, slower)
- 16.98% spike was transient (not reliably reproducible)

### Key insights:
- **Perturbation diversity >> static strength tuning** — aggressive initial kick (n_nodes//12) + frequency cycling escapes local optima better than parameter tweaks
- **Multi-start beats ILS iterations** — 20 runs with 10 ILS better than 16 runs with 12 ILS
- **rand300e is structurally harder** — weak at 14.29% despite overall 16.30%, suggests instance-specific challenges
- **Final 1-opt refinement helps** — polishes best solution but doesn't enable breakthrough beyond 16.30%

### Next trial options if continuing:
- Specialized handling for rand300e (different heuristic mix for high-density graphs)
- Tabu search or Variable Neighborhood Descent (replace ILS perturbation)
- Adaptive allocation (more runs on weaker instances)
