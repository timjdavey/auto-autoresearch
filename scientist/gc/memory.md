## GC Trial 35: Time Budget Safety with Full Quality Preserved

**Result:** 16.30% avg_improvement (matches best 0.163004)

**Key Achievement:**
- Fixed timeout issue (row 27 had 76.9s on rand300e, exceeding 60s limit)
- Maintained quality (25 colours on rand300a)
- Added time budget tracking with 55s limit + 5s margin

**Implementation:**
1. Added `import time` and track `start_time` in solve()
2. Set `time_limit = 55.0` (55s per solve, 5s safety margin)
3. Changed `_one_opt` to check time budget **every 10% of nodes** (not every iteration)
4. Kept full iteration limits (max_iterations = n_nodes * 2)
5. Skip restart if time budget >70% exhausted

**Why It Works:**
- Continuous time checks add significant overhead; periodic checks (every 10% nodes) maintain speed
- Full iteration limits preserve quality (we still get 25 colours on rand300a)
- Periodic time checks still catch overruns early enough to exit safely
- Individual solves now complete in 22-25s (safely under 55s limit)

**Result Comparison:**
- Row 31 (previous best): 74.415s total, 0.163004
- Row 35 (this trial): 69.786s total, 0.163004 (same quality, better time safety)
- Rows 32-34 (bad iteration limits): 52-60s, 0.151893 (worse quality)

**Key Lesson:** Iteration limits hurt quality more than they help. Time-based early exit with periodic checks is the right approach.
