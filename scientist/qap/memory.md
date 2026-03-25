## Trial 001: Greedy Construction + 2-Opt Local Search

**Result:** 10.45% avg_improvement (12.68% rand50a, 11.62% rand60a, 7.05% rand75a)

**Algorithm:**
- Greedy nearest-neighbor construction: incrementally place facilities at locations with minimal cost delta
- 2-opt local search with delta-cost computation (not full cost recomputation)
- Limited to 5 iterations on n>60 to avoid timeouts

**Key insight:** Improvement degrades on larger instances (7.05% on n=75 vs 12.68% on n=50). Likely due to:
1. Greedy construction not finding good starting solutions for larger problems
2. Limited local search (5 iterations) is too restrictive for n=75

**Next steps:** Try random multi-start + better construction, or random restarts to improve solution quality
