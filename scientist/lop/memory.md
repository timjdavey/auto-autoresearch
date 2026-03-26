# LOP Trial Log

## Trial 68: Plateau diagnostics — diversification attempts
- **Current baseline:** 7.06% avg (9.08% r75a, 6.48% r100a, 5.63% r125a)
- **Attempts to break plateau:**
  1. Multi-start SA (3 starts × 3000 iters): **TIMEOUT** on rand125a
  2. Multi-start 2-opt/3-opt (2-3 restarts): **TIMEOUT** on rand125a
  3. Reduced iterations 1-opt(20)+2-opt(15)+3-opt(3): **REGRESSED** to 6.16%
  4. Iterated local search with perturbation: **TIMEOUT** on rand125a

- **Root cause:** Time budget is tight. Any multi-start or extra restarts × expensive neighborhoods (1-opt O(n²), 2-opt O(n⁴) per iter) exceeds 60s limit for n=125
- **Bottleneck:** rand125a (5.63%) drags average down. The other instances (9.08%, 6.48%) are doing well
- **Key insight:** Current greedy + 1-opt(50) + 2-opt(20) + 3-opt(10) is well-tuned for time/quality tradeoff. Hard to improve without algorithmic redesign or better initialization.
- **Next strategy:** Need to profile where 60s is spent on rand125a, then target that specific bottleneck

## Trial 52: Plateau breakthrough — 6.30% via iteration tuning
- **Breakthrough strategy:** Reduced 1-opt from 30→20, increased 2-opt from 20→25
- **Results:** 6.30% avg (9.08% rand75a, 4.23% rand100a, 5.59% rand125a)
- **Success rate:** 100% (all instances pass, no timeouts)
- **Total time:** 99.6s (well within 180s ensemble budget)
- **Improvement:** +15.3% relative gain from 5.47% plateau

### Why it worked:
- Previous plateau at 5.47% was due to aggressive time-safeguards in trial-008 that cut iterations short
- Trial-007 (claimed 6.77%) used 2-opt(20)/3-opt(5) without time checks, but timing overhead from constant checks degraded it
- Key insight: 1-opt dominates time budget on large instances; reducing it frees time for 2-opt which is more effective
- Iteration balance: 1-opt(20) + 2-opt(25) + 3-opt(5) explores more of the 2-opt neighborhood per trial

## Prior plateau: 5.47-5.55% (Trials 44-51)
- Stuck with time-safeguard approach from trial-008
- Root cause: time checks cut 2-opt short on rand125a

## Best Prior: 6.77% (avg_improvement) — Trial 28
- Baseline to beat: 6.77% (may be unconfirmed due to archive issues)
- Current: 6.30% — close but not yet there
- Next step: try 2-opt(26-27) or 3-opt(6) to push toward 6.77%

## Trial Evolution (summary)
1. Initial: greedy + 1-opt/2-opt → 3.28%
2. Multi-start/ILS attempts → 4.38-4.46%
3. Iteration scaling (15/8 → 25/12 → 30/14) → 5.17-6.08%
4. Time-safeguards (trial-008) → regressed to 5.47%
5. Multi-start randomization → 4.81% (failed)
6. Iteration rebalance (1-opt 20 + 2-opt 25) → **6.30%** ✓
