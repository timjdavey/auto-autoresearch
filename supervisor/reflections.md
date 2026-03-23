# Reflections

Meta-process reflections about your own methodology as a Supervisor. How are you approaching study planning? What's working about your process, what isn't? What would you tell your future self?

## Study 1 — Baseline post-study

**What went well:** Having a clean baseline is invaluable. I can now see what Scientists do with minimal guidance — they're strong coders but waste trials on regressions and timeouts.

**What I learned about the analysis process:**
- evaluate.py crashes on TIMEOUT rows — had to do manual analysis. This is an infrastructure issue that needs fixing (but evaluate.py is locked).
- Reading results.tsv directly is fine for 2 problems, but won't scale. Need the evaluate pipeline working.
- Looking at the actual train.py code alongside results.tsv is essential — the numbers alone don't tell you *why* improvement stalled.

**What I'd tell my future self:**
- Focus guidance on *process* not *algorithms*. The Scientists already know how to code. They need help with: reading prior work, managing time, avoiding regressions, and making incremental progress.
- Keep guidance generic. TSP and GC are very different problems but the failure modes (timeouts, crashes, ignoring prior work) are the same.
- Don't over-prescribe. The current guidance is too minimal, but swinging to the other extreme (micro-managing each step) would be equally bad. Find the middle ground: clear process guardrails, freedom on approach.
- 2 trials is very few data points. Be cautious about drawing strong conclusions from small samples.
