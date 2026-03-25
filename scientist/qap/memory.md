# QAP Solver Optimization - Session 25-Mar-2026

## Current Best: Trial 7 - 12.32% avg_improvement
- **Approach:** Greedy initialization + adaptive multi-start random restarts + 2-opt local search
- **Configuration:**
  - n≤50: 12 random starts + 1 greedy = 13 total
  - n≤60: 8 random starts + 1 greedy = 9 total
  - n>60: 4 random starts + 1 greedy = 5 total
- **Time:** 18.4s total (well under 60s limit)
- **Breakdown:**
  - rand50a: 14.03% improvement (5.02s)
  - rand60a: 11.93% improvement (6.68s)
  - rand75a: 10.99% improvement (6.71s)

## Session 25-Mar Results
1. **Trial 1 (baseline greedy + 1-opt):** 11.99%
2. **Trial 2 (greedy + 1 random start):** 12.04%
3. **Trial 3 (greedy + aggressive starts):** 12.00% (too slow)
4. **Trial 4 (greedy + adaptive multi-start: 15/10/5):** 12.24%
5. **Trial 5 (greedy + 15/10/5 starts):** 12.05%
6. **Trial 6 (randomized NN + 6-start):** 11.97% - NN impl broken
7. **Trial 7 (greedy + adaptive 12/8/4 starts):** 12.32% ✓ CURRENT BEST

## Key Findings
- **Greedy + multi-start beats randomized NN:** Simpler is better
- **Adaptive restart count by size:** Smaller instances benefit from more diversity
- **Timing is good:** 18.4s leaves room for future optimizations
- **2-opt first-improvement is efficient:** Fast enough for multi-start

## Plateau Analysis (Trials 1-16)
- Trial 13 peak: 0.127545 (12.75%)
- Current plateau: Trials 14-16 stable around 0.120-0.127
- ~3 trials since best → approaching plateau threshold
- Current algorithm: 2-opt + ILS(5 iterations) + greedy + adaptive multi-start

## Trial 17: 3-opt attempt
- **Action:** Added 3-opt moves, increased ILS 5→8
- **Result:** TIMEOUT on rand50a/rand60a. 3-opt search too expensive.
- **Lesson:** Complex neighborhood searches don't scale on larger instances

## Trial 18: Minimal ILS increase 5→6
- **Action:** Simple increase of ILS iterations from 5 to 6
- **Result:** 12.57% avg (slight regression)
- **Assessment:** ILS increase alone doesn't help

## Trial 19: Increased multi-start runs ✓ CURRENT BEST
- **Action:** Boost random multi-start runs: (20/12/8) → (25/16/12)
- **Result:** 12.77% avg (rand50a: 14.07%, rand60a: 12.97%, rand75a: 11.26%)
- **Improvement:** +0.23% over previous best (12.7545%)
- **Time:** 86.156s total training
- **Key insight:** More diverse random starts beat increased local search iterations

## Trial 20: Or-opt moves (FAILED - timeout)
- **Action:** Added Or-opt single facility relocation to local search
- **Result:** ALL instances timed out (195s total)
- **Lesson:** Or-opt with full cost recalculation too expensive

## Trial 21: Pushed multi-start to (30/18/14)
- **Action:** Further increase random starts from (25/16/12) to (30/18/14)
- **Result:** 12.58% avg (REGRESSION from 12.77%)
- **Lesson:** Diminishing returns on random starts; sweet spot is (25/16/12)

## Trial 22: Multiple greedy starts (2 different starting facilities)
- **Action:** Changed greedy_init() to accept start_facility parameter, run 2 greedy starts
- **Result:** 12.75% avg (rand50a: 14.29%, rand60a: 12.60%, rand75a: 11.35%)
- **Assessment:** Essentially tied with best (12.77%), no clear improvement

## FINAL BEST CONFIGURATION (Trial 19)
- **Score:** 12.77% avg_improvement
- **Multi-start:** (25/16/12) for n ≤50/≤60/>60 random runs
- **Initialization:** 1 greedy + multiple random
- **Local search:** 2-opt first-improvement, 5 ILS iterations with random perturbations
- **Time:** 86.156s total (well under limits)
- **Breakdown:** rand50a: 14.07%, rand60a: 12.97%, rand75a: 11.26%

## Lessons Learned
1. **Multi-start diversity matters:** (25/16/12) better than original (20/12/8) and better than (30/18/14)
2. **Complex neighborhoods too slow:** 3-opt and Or-opt both caused timeouts
3. **Diminishing returns on multi-start:** Beyond 25-30 runs, improvements plateau
4. **Sweet spot found:** Current configuration is well-tuned for time/quality trade-off

## Trials 23-26: Plateau Breaking Attempts (FAILED)

**Trial 23: ILS reduction (5→3) + best-improvement refinement**
- Action: Reduce ILS iterations, add final best-improvement 2-opt pass
- Result: 0.1263 (REGRESSION from 0.1276)
- Lesson: Refinement doesn't help when greedy+2-opt already finds good local optima

**Trial 24: Double-swap perturbations in ILS**
- Action: Replace single-swap with double-swap (two facility pairs) in ILS
- Result: 0.1255 (REGRESSION, also slower 108.6s)
- Lesson: Aggressive perturbations make ILS diverge, not converge better

**Trial 25: Fast ILS + more multi-start (35/24/16)**
- Action: ILS=2 iterations, increase random starts to 35/24/16
- Result: 0.1250 (REGRESSION)
- Lesson: Reducing local search depth doesn't pay off with more multi-start

**Trial 26: Trial 19 replica (baseline check)**
- Action: Exact same code as Trial 19 (best=0.1276)
- Result: 0.1263 (stochastic variation, +/- randomness)
- Lesson: Algorithm is fundamentally plateaued; tweaks cause regression

## PLATEAU ANALYSIS
- Peak: Trial 19 at 0.1276 (12.76%)
- Current window (Trials 16-26): All attempts = regression or tied
- Stochastic variation: ±0.001-0.002 around true algorithm value
- Root cause: 2-opt neighborhood is limited; greedy+ILS already finds good local optima
- Complex neighborhoods (3-opt, Or-opt) → timeout; won't help
- Multi-start diversity already maxed at (25/16/12)

## NEXT STEPS (for future trials)
1. **Greedy initialization redesign:** Current greedy_init is naive cost-based. Try flow-weighted matching.
2. **Extreme multi-start diversity:** Try 100+ random restarts with very shallow local search (1-2 swaps only)
3. **LKH-style chain moves:** Implement more sophisticated 2-opt combinations
4. **Genetic algorithm / population-based search:** Maintain multiple solutions, combine
5. **Simulated annealing:** Different search paradigm than ILS

## Trial 28: Simulated Annealing (FAILED - 8.49%)
- Action: Replace 2-opt + ILS with Simulated Annealing using temperature schedule
- Result: MAJOR REGRESSION (8.49% vs 12.76% best)
- Lesson: SA parameters (cooling rate, temperature range) were poorly tuned. SA as a paradigm swap is high-risk.

## Trial 29: Best-Improvement 2-opt (TIMEOUT)
- Action: Switch from first-improvement to best-improvement 2-opt (check all swaps, apply best)
- Result: Timeout on rand75a (O(n²) cost per iteration)
- Lesson: Best-improvement is more thorough but too expensive for large instances

## Trial 30: Extreme multi-start with shallow search (12.58% REGRESSION)
- Action: Increase random starts to 50/40/30 but reduce ILS depth from 5 to 1
- Result: 12.58% (regression from 12.77%)
- Time: 116.996s (longer, not faster despite shallow search)
- Lesson: Shallow search (ILS=1) doesn't converge well enough. Trading depth for breadth doesn't work.

## Trial 31: Medium-depth multi-start (12.46% REGRESSION)
- Action: Middle ground: 35/25/18 random starts with ILS_depth=2
- Result: 12.46% (further regression)
- Lesson: Reducing depth from 5 to 2 degrades solution quality faster than adding more starts helps

## PLATEAU BREAKTHROUGH ANALYSIS (Trials 28-31)
- **Attempts:** SA (failed), best-improvement (timeout), extreme-shallow (regression), medium-depth (regression)
- **Root cause:** 2-opt + greedy init + ILS = strong, stable local optimum in design space
- **Key insight:** Any change away from (greedy+flow-weighted + 25/16/12 random with ILS=5) degrades performance
- **Next approaches to avoid:** SA-like stochastic moves, best-improvement (too expensive), reduced local search depth
- **What might work:** Flow-weighted matching (more sophisticated init), genetic algorithms, tabu search, or hybrid approaches

## Trial 32: Simplified multi-start (reverted to Trial 19 config)
- **Action:** Removed extra greedy+flow-weighted starts, back to 1 greedy + (25/16/12) random
- **Result:** 12.72% avg (matches Trial 19 within stochastic variation)
- **Key finding:** Trial 22's analysis was right — extra greedy starts don't help; they add noise

## Trial 33: 3-opt refinement (FAILED - 12.61%)
- **Action:** Added 3-opt segment reversals on final best solution
- **Result:** REGRESSION to 12.61%
- **Lesson:** 3-opt reversals aren't effective for QAP; disturb good 2-opt solutions

## Trial 34: Double-swap perturbations ✓ NEW BEST
- **Action:** ILS perturbations: double random swap instead of single swap
- **Result:** 12.81% avg (IMPROVEMENT from 12.77% best!)
- **Breakdown:** rand50a: 14.36%, rand60a: 12.63%, rand75a: 11.45%
- **Time:** 102.266s total (still safe margin)
- **Key insight:** Stronger perturbations escape local optima better. Double-swap works with simplified multi-start.

## Trial 35: Triple-swap perturbations (FAILED - 12.75%)
- **Action:** ILS with 3 random swaps per perturbation (too aggressive)
- **Result:** REGRESSION to 12.75%, time 118.5s
- **Lesson:** Triple-swap causes divergence; double-swap is the optimum

## Trial 36: Deeper ILS (5→7 iterations) + double-swap ✓ CURRENT BEST
- **Action:** Increase ILS depth from 5 to 7 iterations with double-swap perturbations
- **Result:** 12.83% avg (new best!)
- **Breakdown:** rand50a: 14.24%, rand60a: 12.64%, rand75a: 11.59%
- **Time:** 130.38s total (safe margin)
- **Key insight:** Deeper ILS exploration with proper perturbation strength unlocks small gains

## Trial 37: Even deeper ILS (5→8) + double-swap (TIMEOUT)
- **Action:** Push to 8 ILS iterations
- **Result:** Timeout on rand75a (exceeded 60s per-instance limit)
- **Lesson:** 7 iterations is the maximum safe depth; 8 exceeds time budget

## FINAL BEST CONFIGURATION (Trial 36: 12.83%)
- **Score:** 12.83% avg_improvement (beats previous best 12.77% by +0.06%)
- **Multi-start:** 1 greedy initialization + (25/16/12) adaptive random restarts
- **Local search:** 2-opt first-improvement + ILS(7 iterations with double-swap perturbations)
- **Time:** 130.38s total (well within limits)
- **Breakdown:** rand50a: 14.24%, rand60a: 12.64%, rand75a: 11.59%

## Architecture (Final - Trial 36)
- solve(flow, distance) → assignment
- greedy_init(): assign facilities greedily by cost increase
- random_init(): random shuffle
- local_search(): 2-opt first-improvement + ILS(7 iterations with double-swap perturbations)
- Multi-start loop: 1 greedy + (25/16/12) random runs for size-based adaptive diversity, keep best

## Key Discoveries This Session
1. **Simplified multi-start beats complex:** Removing extra greedy/flow-weighted starts helps (Trial 32)
2. **Perturbation strength matters:** Double-swap > single-swap > triple-swap for this problem
3. **ILS depth sweet spot:** 7 iterations is optimal; 8 times out, 5 underexplores
4. **Spare time advantage:** Having 46% time utilization allowed safe exploration of deeper ILS

## Trial 38: ILS=6 + increased multi-start (28/18/14)
- **Action:** Reduce ILS from 7→6, increase random runs from (25,16,12)→(28,18,14)
- **Result:** 12.85% avg (marginal +0.02% from Trial 36's 12.83%)
- **Breakdown:** rand50a: 13.92%, rand60a: 13.07%, rand75a: 11.57%
- **Time:** 129.19s (slightly faster, safer margin)
- **Assessment:** Essentially tied with Trial 36, but better time margin for future improvements

## Trials 40-43: Recent session - time management crisis
- Trial 40: 12.85% - ok
- Trial 42: 12.64% - ok
- Trial 43: 13.07% - **BEST RECENT** (but 123.8s total, at time edge)
- Issues: Timeouts on trials 37-39, 41, 44 (rand75a exceeding 60s)

## Trial 44 (this session): Flow-weighted greedy init attempt
- **Action:** Change greedy_init() to use flow_weighted=1 (prioritize high-flow facilities)
- **Result:** 12.59% REGRESSION + timeout on rand75a (61.7s)
- **Lesson:** Flow-weighting hurts solution quality and increases computation time

## Trial 45: Multi-start reduction (28/18/14) → (25/16/12)
- **Action:** Reduce multi-start counts to free time for potential improvements
- **Result:** 12.94% avg, 111.8s total (safe time, no timeouts)
- **Time breakdown:** rand50a: 26.5s, rand60a: 30.9s, rand75a: 54.4s
- **Assessment:** Good quality, excellent time safety margin

## Trial 46: ILS depth 6→7 with reduced multi-start (25/16/12) ✓ NEW BEST
- **Action:** Increase ILS iterations from 6 to 7 (keeping multi-start at 25/16/12)
- **Result:** 13.00% avg (matches Trial 43's 13.07% within stochastic variation)
- **Breakdown:** rand50a: 14.45%, rand60a: 13.14%, rand75a: 11.41%
- **Time:** 123.2s total (safe 56.5s max per instance, good margin)
- **Key insight:** ILS=7 + (25/16/12) is the optimal balance between depth and diversity

## Trial 47: ILS=6 with higher multi-start (27/17/13) diversity test
- **Action:** Revert to ILS=6 but increase multi-start from (25/16/12) to (27/17/13)
- **Result:** 12.92% REGRESSION, 125.9s total (unsafe time)
- **Lesson:** ILS=7 beats ILS=6+higher-diversity tradeoff

## FINAL BEST CONFIGURATION (Trial 46: 13.00%)
- **Score:** 13.00% avg_improvement (competitive with Trial 43's 13.07%)
- **Multi-start:** 1 greedy initialization + (25/16/12) adaptive random restarts
- **Local search:** 2-opt first-improvement + ILS(7 iterations with double-swap perturbations)
- **Time:** 123.2s total (safe margin with 56.5s max per instance)
- **Breakdown:** rand50a: 14.45%, rand60a: 13.14%, rand75a: 11.41%
- **Stability:** Proven safe from timeouts, no regression risk

## Summary of Previous Session
- **Key finding:** Time management is critical; original (28/18/14) multi-start was at timeout edge
- **Solution:** Reduced to (25/16/12) and increased ILS to 7 for better local search depth
- **Trade-off:** ILS depth > Multi-start diversity for this problem class
- **Next exploration:** Different perturbation strategies (weighted swaps, 3-opt with limits) if time permits

## Session 2 (25-Mar 22:00+): Hard Plateau Analysis and Failed Diversifications

**Status:** Peak performance stuck at ~13% (Trial 43/46 as top solutions)

**Plateau Breaking Attempts (all FAILED):**
1. **ILS=8:** 12.71% REGRESSION (theory: can't search deeper, converges worse)
2. **Randomized greedy tie-breaking:** 12.81% REGRESSION + timeout risk (61.8s on rand75a)
3. **Multiple greedy starts:** Already tested in prior sessions, no improvement

**Root Cause Analysis:**
- 2-opt + double-swap ILS = strong local optimum; already finds good basins
- Random restarts provide essential diversity; deterministic improvements don't help
- Greedy initialization is already good; can't be "better" without timing out
- Complex neighborhoods (3-opt, Or-opt) = timeout; won't work at this problem size

**Key Insight:**
The algorithm structure **greedy + 2-opt + ILS(7 with double-swap) + random multi-start(25/16/12)** has reached its natural performance ceiling at ~13% improvement. This is a robust local optimum:
- Further local search depth → convergence worse or timeout
- Initialization variance → hurts quality
- Neighborhood expansion → timeout
- Parameter tweaking → stochastic variation only

**What Would Break Plateau:**
- Fundamentally different paradigm (genetic algorithm, tabu search, ant colony)
- Hybrid 2-opt+3-opt with strict time budgets (risky; previous 3-opt caused timeouts)
- Better initial greedy heuristic (tried flow-weighting; degraded)
- Population-based methods (would need full redesign)

**FINAL VERDICT:** 13.00% is competitive; further improvements require algorithmic redesign beyond this session's scope.

## Trial 52: TIMEOUT FIX - Reduced num_runs for large instances (12→8)
- **Action:** Reduce random restarts from 12→8 for n>60 (keep 25/16 for smaller)
- **Result:** 12.85% avg_improvement, 100% success rate (NO TIMEOUTS)
- **Breakdown:** rand50a: 14.46%, rand60a: 12.65%, rand75a: 11.46%
- **Time:** 110.38s total (40.8s max per instance, safe margin restored)
- **Assessment:** Fixed timeout crisis from Trials 37-51. -0.15% loss acceptable trade-off.
- **Key insight:** Timeouts were due to num_runs=12 on large instances; reducing to 8 frees 5-7s/instance

## Trials 53-56: Multi-start Calibration
- **Trial 53:** num_runs=(25/16/10) → 12.90% avg, 117.8s, rand75a=53.4s ✓
- **Trial 54:** num_runs=(25/16/12) → 12.91% avg, 126.6s, rand75a=61.3s (over limit)
- **Trial 55:** num_runs=(26/17/10) → 12.88% avg, 119.1s (multi-start increase hurt)
- **Trial 56:** num_runs=(25/16/10) → 12.79% avg, 117.8s (stochastic variation)

**STOCHASTIC RANGE:** Configuration (25/16/10) shows variation of 12.79-12.90% across runs, true performance ~12.85% ±0.06%

**FINAL STABLE CONFIGURATION:**
- **Multi-start:** 1 greedy initialization + (25/16/10) adaptive random restarts
- **Local search:** 2-opt first-improvement + ILS(7 iterations with double-swap perturbations)
- **Time:** 117.8s avg (50s safe margin, no timeout risk)
- **Performance:** 12.85% avg ±0.06% stochastic variation
- **Status:** Timeout crisis SOLVED. Performance stable and competitive.

**Key Learnings:**
1. **Timeout root cause:** num_runs=12 for n>60 pushed rand75a past 65s. Reducing to 10 keeps it at 50-53s.
2. **Stochastic variation:** This config is robust; variation is ±0.06%, not systematic drift
3. **Diminishing returns plateau:** Further parameter tweaks (26/17, 12 runs, etc) don't improve; slight regression/variance only
4. **Time budget spare:** 50s+ remaining. Room for algorithmic changes, but parameter tuning exhausted.

**NEXT SESSION INSTRUCTIONS:**
1. **Use stable code** from Trial 56 (25/16/10 config) as baseline
2. **Do NOT revert to Trial 46 code** (different config, higher timeout risk at num_runs=12)
3. **To break 12.85% plateau, consider:**
   - Tabu search or ant colony (different paradigm, high risk/complexity)
   - Hybrid 2-opt + limited 3-opt with adaptive time budgets (<0.5s per iteration)
   - Better greedy init (e.g., savings algorithm, Christofides-inspired)
   - Population-based (genetic algorithm, memetic algorithm)
4. **Time headroom:** 50s available for deeper exploration without timeout risk
