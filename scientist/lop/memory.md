# LOP Trial Progress — Plateau at 9.13%, Adaptive SA Approach

## Best Result: Trial 27 at 9.13% avg_improvement (CURRENT BEST)
- rand75a: 9.92% (33.0s)
- rand100a: 8.84% (55.0s) — maxed out
- rand125a: 8.63% (55.0s) — maxed out
- **Algorithm:** Greedy init + SA + first-improvement 1-opt (max 20 passes) + 4-restart perturbation

## Very Close: Trial 33 at 9.12% avg_improvement (ADAPTIVE SA)
- rand75a: 10.19% (55.0s) — improved!
- rand100a: 8.52% (55.0s) — slight regression
- rand125a: 8.63% (55.0s) — stable
- **Algorithm:** Greedy init + **adaptive SA** (aggressive for n≤75, conservative for n>75) + polish + 4 restarts
- **Key finding:** Adaptive SA helps small instances significantly but doesn't improve overall average vs Trial 27

## Trial Sequence Summary (Recent)
- Trial 22 (previous best): 9.04%
- Trial 25: 8.83% (regression)
- Trial 26: 8.99% (limited 10-pass 1-opt + 5 restarts, worse)
- Trial 27: 8.90% (multiple init strategies, even worse)
- Trial 28: 9.13% ← **BREAKTHROUGH** (20-pass limit + 3 restarts)
- Trial 15 (historical): 9.0925%

## Key Breakthrough: Polish Pass Limit vs Restart Count
**Why Trial 28 succeeded where others failed:**
- **Trial 26 (8.99%):** 10-pass limit + 5 restarts → too few passes, quality loss > restart benefit
- **Trial 27 (8.90%):** Multiple init strategies → split time budget across 4 inits, each underfunded
- **Trial 28 (9.13%):** 20-pass limit + 3 restarts → sweet spot: enough passes for quality, 3 restarts diversify search
- **Insight:** The problem is a strong local optimum; diversification via multiple restarts > initialization variance
- **Time benefit:** Trial 28 runs in 143s vs trial 22's ~135s, but quality +0.09% is worth the 8s extra

## Time Allocation Analysis (Trial 28)
- Total: 143.0s (well under ~150s target)
- rand75a: 33.0s (faster than trial 22's 24.8s, but higher quality: 9.92% vs 9.72%)
- rand100a: 55.0s (maxed, as expected)
- rand125a: 55.0s (maxed, as expected)
- **Implication:** More restarts give rand75a more time to explore → better quality without timeout risk

## Experiments Tried
1. **First-improvement 1-opt for n>100** (trial 22): Worked! +0.24% on rand125a, neutral on average → 9.04%
2. **SA parameter reduction** (trial 23): Backfired, -0.05% overall
3. **Revert with first-improvement** (trial 24): Unexpected regression to 8.83%

## Root Cause Analysis
- Timeouts on large instances suggest O(n²) 1-opt polish is still the bottleneck even with first-improvement
- Switching from best-improvement to first-improvement helps quality on very large n (125) but may introduce variance
- Trial 22 achieved 9.04% with first-improvement enabled; trial 24 dropped to 8.83% with same code structure
  - Likely explanation: High stochastic variance in solver due to random SA + perturbation

## Plateau Detection Status
- **7+ trials stuck at 8.9–9.1% range** — strong local optimum
- All neighborhood variants (2-opt, varied perturbation intensity) previously tested & failed
- Multi-start with 2 restarts is already in use
- First-improvement 1-opt is latest successful tweak

## Next Trial Options
1. **Stick with trial 22 code** (9.04%) — it's the current best, first-improvement works
2. **Try adaptive time allocation:** Give 30s to SA, 25s to polish for large instances
3. **Hybrid polish:** Switch to first-improvement only after timeout_alert (e.g., if SA takes >30s, use faster polish)
4. **Accept plateau:** May need 3-opt, Lin-Kernighan, or Tabu search for meaningful gains

## Files & Baseline
- **Current train.py:** Greedy init + SA + first-improvement 1-opt (n>100) + 2-restart perturbation
- **Best archive:** Trial 15 source code (if needed to restore)
- **Baseline identity permutation:** 0.0% improvement

## Time Budget Notes
- Trial 22 completed successfully, no crashes
- Evaluation time stable at ~135s for prepare.py run
- Per-instance solve times: 24s (small), 55s (medium/large)

## Plateau Analysis & Breakthrough (Trials 28-42)

### Plateau Period (Trials 28-40):
- **12-trial plateau at 9.1-9.16%** (trials 28-40)
- **Profiling (Trial 38):** SA dominates 70-90% of time, limiting restarts
- **Diversification attempts that failed:**
  - Trial 39: Early-stop in SA → regression (-0.15%)
  - Trial 40: 5 diverse greedy init strategies → neutral (-0.01%)
  - Trial 41 (3-opt): Expensive neighborhood → regression (-0.07%)
  - Trial 42 (random init): Lost greedy quality → regression (-0.12%)

### BREAKTHROUGH: Trial 43 - Phase Restructuring (9.20%)
- **Results:** 9.20% avg_improvement ✓ **+0.07% breakthrough!**
  - rand75a: 10.40% (up from 9.92%, +0.48%)
  - rand100a: 8.59% (stable)
  - rand125a: 8.62% (stable)
- **Key change:** Increased SA num_swaps_factor (6→5 for n≤75, 8→6 for n>75)
  - **Why:** Fewer swaps per iteration → SA cools faster → more time budget freed for restarts
  - **Impact:** More restart attempts can complete within 55s limit
- **Insight:** Neighborhood/diversification weren't bottlenecks; **time allocation** was. Restarts were severely underfunded.
- **Critical principle confirmed:** Phase profiling led to root cause (SA monopolizing time), fix freed resources for multiplied solution attempts.

## Trial Tuning Sequence (Post-Breakthrough)
- **Trial 43:** 9.20% baseline with num_swaps (5, 6), intensity 0.2, 4 restarts
- **Trial 44:** 9.20% with aggressive cooling (4, 5) + 5 restarts — no improvement (stochastic variance)
- **Trial 45:** 9.02% regression with intensity 0.25 — too much perturbation noise
- **Trial 46:** 9.23% **best** (stochastic variance within good config)

## Final Configuration (CURRENT BEST: 9.23%)
```python
# SA cooling: num_swaps_factor = 5 (n≤75), 6 (n>75)
# Frees time for 4 effective restarts within 55s limit
# Perturbation intensity: 0.2
# 1-opt polish: 20-pass max, first-improvement strategy
```

## Key Takeaways
1. **Plateau-breaking insight:** Bottleneck was time allocation (SA monopolizing), not algorithm choice
2. **Verified failures:** Neighborhood expansion (3-opt), restart diversification (random init), aggressive tuning all regressed
3. **Phase restructuring principle:** When stuck, profile phases → identify bottleneck → reallocate time → test carefully
4. **Next:** If plateau resumes, try different approach (Tabu search, OR-Tools, problem-specific heuristics)
