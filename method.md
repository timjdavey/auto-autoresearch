# Method

## DO NOT EDIT — this file is managed at the top level. Neither the Supervisor nor the Scientist should modify it.

Two shell scripts invoke the Scientist. Both use the same allowed tools and prompt (`Read and follow lab/program.md`).

### `study.sh` — persistent context
Single `claude -p` call. The Scientist keeps its context window across all trials in the study. Best when continuity and accumulated learning matter.

### `trials.sh` — clean context
Loops 100 times, each a fresh `claude -p` call. The Scientist starts from scratch every trial. Best when you want independent runs without context drift.

### What you can change
- `lab/program.md` — the Scientist's instructions
- `lab/record.py` — trial recording tools
- Anything else inside `lab/`

### What you must NOT change
- `study.sh`, `trials.sh`, `method.md` — top-level orchestration (locked)
- `prepare.py` — evaluation framework (locked)
