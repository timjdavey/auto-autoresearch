# QAP Solver Memory

## Current Status (Trial 22)
- **Best: 12.15%** (Trial 16, single deterministic NN + 2-opt)
- Current: **12.01%** (Trial 22, multi-start 10x randomized NN)
- Plateau visible: trials 16-21 stuck at 0.1170-0.1215 range

## Trial 22: Multi-start (10x randomized NN)
- **Score:** 0.1201 avg_improvement (102.8s total)
- **Issue:** Near time limit (target is 55s + 5s margin)
  - rand50a: 16s, rand60a: 31s, rand75a: 55s
- **Analysis:** 10 starts too aggressive; need to balance construction diversity vs local search depth

## Key Findings (Cumulative)
1. **First-improvement 2-opt is reliable** - fast, decent quality
2. **Single start + greedy NN baseline** achieves ~12.15%
3. **Multi-start promising but time-bound** - 10 starts saturates time budget
4. **Randomized NN doesn't consistently beat deterministic greedy**

## Next Action
- **Trial 23:** Reduce to 5-7 multi-starts (free time for deeper 2-opt)
- Or: Try best-improvement 2-opt with fewer starts
- Goal: Beat 12.15% by improving local search depth
