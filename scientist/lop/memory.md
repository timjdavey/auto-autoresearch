## LOP Trial Results

### Trial 10 (current): Ultra-conservative restarts
- **avg_improvement**: 8.90% (0.089) — near-best quality with high stability
- **Key change**: Further reduced restart scaling
  - Changed from `max(5, n // 20)` to `max(2, n // 40)`
  - Restart counts: n=75→1, n=100→2, n=125→3
  - Each instance now completes in ~55s with no timeout risk

**Results by instance:**
- rand75a: 10.28% (52.839s)
- rand100a: 8.42% (55.075s)
- rand125a: 7.98% (55.009s)

**Why it works**:
- Even fewer restarts (compared to Trial 7) reduces greedy initialization overhead
- Allows 1-opt local search to run nearly to completion (dominates time budget)
- Trading initialization diversity for local search convergence yields similar final quality
- Total time: 162.922s (faster than 165+s typical)

### Performance plateau confirmed
Quality ranges 8.64%–8.92%. Tried first-improvement 1-opt but it degraded quality (8.76%). Best-improvement with conservative initialization appears optimal. Further gains likely require different algorithms (e.g., 3-opt, variable neighborhood search).
