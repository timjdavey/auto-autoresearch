## LOP Autoresearch Progress — Trial 60+ Time-Optimized ILS at 9.02%

### **CURRENT BEST: 9.03% avg_improvement (Trial 63)**
- **Performance**: rand75a: 9.96%, rand100a: 8.74%, rand125a: 8.39%
- **Algorithm**: Iterated Local Search (ILS) with optimized time allocation
- **Exact approach**:
  1. Rowsum initialization → first-improvement 1-opt
  2. Greedy initialization → first-improvement 1-opt (if time < 10% of budget)
  3. ILS: Loop while time < 55s:
     - Perturb best solution: k = max(1, n//20) random swaps
     - Apply first-improvement 1-opt to perturbed solution
     - Accept if better than best found
- **Key insight**: Reducing init budget 20%→10% breaks previous plateau (8.96%→9.03%)
- **Time**: 167.8s total across 3 instances (safe margin)

### Recent Trial Exploration (Trials 57-63)
- **Trial 57**: Epsilon acceptance + adaptive k → 8.93% (REGRESSED - too permissive)
- **Trial 58**: Stronger perturbations (k=n//12) → 8.95% (no improvement)
- **Trial 59**: Limited 2-opt final polish → 8.95% (no improvement)
- **Trial 60**: Reduced init budget 20%→10% → 9.02% (IMPROVED)
- **Trial 61**: Reduced init budget to 5% → 9.00% (TOO AGGRESSIVE)
- **Trial 62**: Added random initialization → 9.01% (diversity, no gain)
- **Trial 63**: Reconfirm trial 60 config → 9.03% (BEST)

### What WORKS (Validated This Trial)
- **Time allocation tuning**: Init budget 20%→10% is sweet spot for rowsum+greedy+ILS balance
- **Iterated Local Search**: Stable core algorithm, k=n//20 perturbations effective
- **First-improvement 1-opt**: Fast and effective local search
- **Rowsum initialization**: Deterministic, high-quality starting point

### What DIDN'T WORK (Tried this round)
- **Aggressive perturbations (k = n//10)**: Regressed to 8.91%
- **Multi-start with colsum**: Regressed to 8.93% (colsum worse than greedy)
- **SA-style acceptance (accept worse solutions)**: Regressed to 8.77%
- **Best-improvement 1-opt in ILS**: Too slow, regressed to 8.90%

### Next Trial Suggestions
- **Try ILS with different perturbation operators**: Instead of random swaps, try position-based swaps or domain-informed moves
- **Variable neighborhood search**: Swap between different neighborhood sizes (k varies)
- **Chained ILS**: Multiple chains with different random seeds
- **Accept marginal improvements**: Accept perm_score > best_score - epsilon for diversity
- **3-opt moves**: If time permits, add 3-opt to local search phase

### Algorithm Details
- **Initialization**: construct_from_rowsums() — Sort nodes by descending row-sum, build permutation
- **1-opt local search**: First-improvement strategy (break on first improving swap)
- **2-opt (light)**: Adjacent/nearby swaps only (max_distance = min(5, n/20)), first-improvement
- **Time per instance**: ~6s (rand75a), ~24s (rand100a), ~58s (rand125a)

### Diversification Actions Tried (Trial 28)
1. **Best-improvement 1-opt alone** — Regressed from 8.77% to 8.55% avg
2. **Best-improvement 1-opt + multi-start (rowsum + greedy)** — 8.58% avg, marginal (only +0.01% at 2x time)
3. **3-start (rowsum + colsum + greedy)** — Timeout on rand125a (106s > 60s limit)
4. **Confirmed**: First-improvement 1-opt + adjacent-swap outperforms best-improvement variants

### Root Cause Analysis
- **1-opt coverage**: First-improvement 1-opt explores ~O(n²) swaps; most improving moves are found
- **Time budget**: rand125a (n≈125) uses ~58s for rowsum + 1-opt. Adding any pass causes timeout.
- **Local optimum strength**: All tested variants converge to same 8.77% solution, suggesting strong local optimum

### Plateau Detection
- 10 trials (17-26) at identical 0.087711 avg_improvement
- Per guidance, diversification is mandatory. Tried 4 approaches; none improved.
- Suggests algorithm has hit strong local optimum resistant to local search variants

### What Works
- Row-sum initialization: +1.3% over greedy construction
- First-improvement 1-opt: Better than best-improvement despite less thorough search
- No time budget for multi-start on large instances

### What Doesn't Work
- Best-improvement 1-opt: Slower, same or worse quality
- Multi-start with multiple methods: Timeouts on n≥100
- Adjacent-swap 2-opt: Redundant (1-opt already finds adjacent improvements)

### Trial 40+ Findings (This Round)
- **Best-improvement 1-opt**: Regressed 8.77% → 8.42%, too slow for large instances
- **Multi-start attempts**: Caused timeouts on rand125a (106-152s vs 60s limit)
- **Time-limit safeguard**: Added explicit TIME_LIMIT=55s to prevent drift, confirmed stable at 88.8s total
- **Random restart**: Same result (8.77%) but slower (118s), row-sum initialization is deterministic

### Key Insight: Algorithm Saturation
- All optimization attempts converge to **8.77% ± 0.01%**
- First-improvement + adjacent-swap is bottleneck-optimal given time constraint
- Deterministic initialization (rowsum) leaves no room for random restarts

### Next Trial Suggestions
**Current ILS at 9.03% is well-optimized for time budget. To break further:**
1. **Try different perturbation operator**: Instead of random swaps, try block moves or position-based swaps
2. **Simulated Annealing**: Accept worse moves with cooling schedule — escape local optima
3. **Better initialization heuristic**: Try construction methods beyond rowsum/greedy (e.g., arc-weighted ordering)
4. **3-opt in local search**: If adding custom delta_3opt is feasible within time (expensive, needs careful timing)
5. **Acceptance criterion variants**: Try accepting moves slightly better than best (e.g., >best_score×0.9995)
