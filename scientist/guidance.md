# Research Methodology Guidance

## The experiment loop

Run exactly one trial per invocation, then stop.

1. **Review history**: Read `results.tsv` and recent files in `archive/` to understand what has been tried and how well it worked. Build on what worked; avoid repeating what failed.
2. **Edit `train.py`**: Implement your idea.
3. **Evaluate**: Run the evaluation harness from the project root. Do NOT use shell redirection (`>`, `2>&1`, `tee`).
4. **Keep or revert**: If the metric is better than the previous best, keep the change. If it's worse or it crashed, revert with `git checkout -- <path to train.py>`.

If a run crashes, try to fix it (2–3 attempts max). If you can't, revert and move on.
