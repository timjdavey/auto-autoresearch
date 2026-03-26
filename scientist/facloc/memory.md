# Facility Location Trial Progress

## Trial 62 (Latest): Plateau 64.50% — metric variants & initialization reordering (all failed)

**Status:** 25+ trial plateau at 64.50% (trials 36-62). Attempted 4 new approaches:
1. **Linear penalty metric** `delta - 0.15*opening_cost`: Regressed to 64.37% (-0.13%)
2. **Logarithmic scaling** `delta/(1.0 + 0.1*opening_cost)`: Same 64.50%, no change
3. **2-opt refinement** (50 iters): Same 64.50%, but 2.5× slower (23.2s vs 9.2s)
4. **Cost-ordered facility starts**: Same 64.50%, no improvement

**Key finding:** All parameter and initialization tweaks keep returning to 64.50%. The plateau is extremely robust.

**Exhaustion status:** Previous trials (36-61) tried:
- Randomized facility selection (70/30 best/random)
- Best-improvement vs first-improvement 1-opt
- Phase reordering
- Simulated annealing with random moves
- Multi-start increases
- Various opening phase metrics

**Next strategy (when resuming):**
The plateau appears to be a STRONG local optimum that resists parameter tweaking. Options:
1. **Simulated annealing with facility swaps** (not random moves) — move whole facilities instead of clients
2. **Tabu search** — forbid re-opening facilities just closed to prevent cycling
3. **Genetic algorithm** — population-based diversification (higher overhead but might escape)
4. **Accept plateau** — current algorithm is a 64.50% local optimum; further gains may require fundamental redesign

**Time profiling remains:**
- 1-opt: 85-87% of time
- Opening: 12-14% of time
- Closing: 1-2% of time
- Total per-solve: ~5.7-6.2s out of 60s limit (plenty of time available)

---

## Trial 55: Plateau 64.50% — profiling & failed diversification attempts

**Current status:** Extended plateau at 64.50% improvement (trials 36-54 = 19 trials stuck).

### Attempted diversification actions (all failed):
1. **Random multi-start initialization** (50% deterministic + 50% random facilities): No improvement, still 64.50%
2. **Best-improvement 1-opt for 50% of starts** (vs first-improvement): **Regressed to 63.09%** (-1.41%)
3. **Reduce max_iterations from 1000→500**: No quality improvement, search actually slower

### Key profiling findings (timing analysis):
- **1-opt local search dominates 85-87% of total time** (guidance bottleneck)
  - rand30_100a: 0.86s/1.01s (85%)
  - rand40_120a: 2.05s/2.42s (85%)
  - rand50_150a: 4.91s/5.65s (87%)
- Opening phase: ~12-14% of time
- Facility closing: ~1-2% of time

### Why current plateau is strong:
- Previous simple diversification strategies failed (2-opt, perturbation, randomization in memory.md)
- Profiling shows 1-opt is critical but also very expensive
- Reducing 1-opt iterations counterintuitively made solver slower (quality diffs forced more multi-start evaluations)
- Best-improvement 1-opt made things worse (likely getting stuck in worse local optima)

### Next trial strategy (when resuming):
Since neighborhood and initialization variations failed, try:
1. **Problem-specific construction heuristic** — analyze opening facility patterns (e.g., open few high-value facilities early)
2. **Different opening phase metric** — current uses `delta / opening_cost`, try alternatives:
   - `delta - 0.2 * opening_cost` (linear penalty vs division)
   - `delta / (1 + log(opening_cost))` (softer scaling)
3. **Tabu search concepts** — forbid closing facilities that were just opened (prevent cycling)
4. **Accept simulated annealing with better moves** — restrict moves to facility swaps (not random reassignment)

---

## Trial 34: Cost-per-opening tie-breaking breakthrough — 64.50%
- **Result:** 64.50% (+0.11% from 64.39% plateau)
- Changed facility opening heuristic: instead of picking facility with best absolute delta, pick by `delta / opening_cost`
- Favors high-impact, low-cost facilities over expensive ones
- Improvement came from rand30_100a (59.38%→59.71%)
- Time: 4.7s (fast, well under 60s limit)
- **Key insight:** Previous approach (absolute delta) was opening expensive facilities; cost-normalization improves solution diversity

## Trial 33 (Previous attempt): Phase reordering (closing→1-opt) — FAILED
- Tried moving facility closing BEFORE 1-opt instead of after
- Result: identical 64.39%, no change at all
- Conclusion: Phase order not the bottleneck

## Trial 32 (Previous attempt): Simulated Annealing — FAILED
- Replaced 1-opt with SA using random facility swaps
- Result: 64.39%, but 67s (11× slower)
- Conclusion: Random moves ineffective for facility location; algorithm needs structure

## Plateau Analysis (Trials 19-33): 64.39% plateau — broken by greedy construction variant
- **12 trials stuck without improvement** — strong local optimum
- Tried many diversification approaches, all failed:
  1. 2-opt local search (100 iters) - no gain, 2.5× slower
  2. Perturbation-restart (3 restarts) - no gain, 11× slower
  3. Randomized facility selection (70/30 best/random) - worse
  4. Increased multi-start (25→50) - no gain
  5. Cost-normalized opening (delta - opening_cost) - worse
  6. Best-improvement vs first-improvement 1-opt - no difference
  7. Phase reordering (closing before 1-opt) - no change
  8. SA with random moves - too slow, no gain
  9. **Cost-per-opening tie-breaking (delta/opening_cost)** - SUCCESS! +0.11%

**Next strategy (Trial 35+):** Continue refining tie-breaking metrics
- Current best: `score = delta / opening_cost` — 64.50%
- Tested: `delta / (affected_clients + opening_cost/1000)` — same result
- To try: adjust scaling factors, combine metrics, or try **tabu search** to forbid recent moves and escape local optimum
- Alternative: increase num_starts from 50 to 100+ if facilities < 100, or try deterministic + random initialization mix

## Trial 10: Best-facility greedy selection (63.61%)
- **MAJOR IMPROVEMENT: +3.98% from 59.63%**
- Key change: Evaluate ALL closed facilities, pick best cost reduction
- Algorithm: Multi-start (5) → best-facility greedy opening → 1-opt → facility closing

## Previous plateau (Trials 1-8): 36.66% (greedy client init)
- Hit local optimum; 2-opt and multi-start didn't help
- Issue: Client-centric initialization ignored facility opening cost structure

## Architecture analysis:
- Facility-opening heuristic is powerful — core to all improvements
- Multi-start with different opening facilities adds diversity
- 1-opt + facility closing still effective
- Cost-normalization in heuristics matters significantly
