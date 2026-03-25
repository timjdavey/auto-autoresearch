# Facility Location Solver Evolution

## Final Solution: Multi-start Facility Insertion + 1-opt Local Search
**Result: 64.26% improvement** ✓

### Algorithm:
1. **Multi-start Facility Insertion** (Initialization phase ~15s)
   - Evaluate all facilities by "cost per client" metric
   - Try top 3 candidates as starting facilities
   - For each: iteratively insert facilities that reduce total cost
   - Keep best result

2. **1-opt Local Search Refinement** (~2s)
   - Iteratively reassign individual clients to better facilities
   - Use best-improvement strategy
   - Stop when no improvements found or time limit approached

### Performance:
- rand30_100a: 59.17% improvement
- rand40_120a: 66.21% improvement
- rand50_150a: 67.39% improvement
- **Average: 64.26%**
- Total time: 16.8s (well under 60s/instance limit)

### Exploration Summary:
1. **Baseline greedy**: 0% (assigns each client to cheapest facility)
2. **Local search only**: 34-36% (facility closing + 1-opt on greedy baseline)
3. **Single-start insertion**: 63.5% (major breakthrough - 2x improvement)
4. **Optimized start selection**: 63.6% (slight gain)
5. **Multi-start insertion**: **64.3%** (best - explores multiple paths)

### Key Insights:
- **Initialization matters most**: Switching from greedy to Facility Insertion gave 63.5% → massive leap
- **Multi-start provides robustness**: Different starting facilities explore different facility sets
- **Local search refinement is minimal**: Insertion already near-optimal, 1-opt adds <1%
- **Time profile**: Initialization dominates (15s), leaves 30s safety margin for future improvements
