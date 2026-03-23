# Ideas

Strategies, hypotheses, and observations about how the scientist approaches discovery. Organise these however helps you think clearly — by status (untested, proven, promising, abandoned), by theme, or freeform. Periodically review and prune.

## Proven from baseline

- Scientists are strong coders — both built numba-accelerated, algorithmically sophisticated solvers from trivial baselines in just 2 trials.
- They naturally use numpy/numba without prompting.
- TSP Scientist used the 30s time budget well (27s deadline). GC Scientist also set 27s.

## High-priority ideas for Study 2

- **Run evaluation early**: Scientists should run prepare.py as their FIRST action after any edit, before making more changes. The GC Scientist made big changes and crashed (-10.0) — likely could have caught issues sooner.
- **Read prior work carefully**: Each trial is a fresh Scientist. They need to read results.tsv AND archive/ code to understand what's been tried. The guidance should emphasise: start by understanding the current best, then make targeted improvements.
- **Incremental changes**: Make one change at a time, test, then build further. Avoid rewriting everything at once (which risks regressions and timeouts).
- **Time management**: Don't spend too long planning/coding. Get to a working evaluation within the first few minutes. The 10-min trial timeout killed 3 runs.
- **Regression guard**: Before submitting a big change, compare your score against the previous best. If worse, revert.

## Untested ideas (lower priority)

- Perceived trial budget: inflate count to encourage risk-taking, or deflate to force concentrated bets
- Motivation: aggressive vs supportive tone
- Explore/exploit phasing: explicit exploration phase then exploit
- Multi-test: try multiple ideas at once vs one at a time
- Note verbosity: how much to write in results
- Planning vs opportunism: structured upfront planning vs staying open to serendipity
- Ranking: best ways to rank and communicate ideas across trials

## Open questions

- Model transfer: does optimising for Sonnet then transplanting to Opus give the same boost?
- Verification: results are highly non-deterministic — how to confirm the system actually works better?
- The -10.0 crash penalty in GC: was it a compilation error, runtime error, or timeout within solve()? Need to check logs if it recurs.
