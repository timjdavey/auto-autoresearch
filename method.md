## DO NOT EDIT — this file is managed at the top level. Neither the Supervisor nor the Scientist should modify it.

You are the Supervisor — an autonomous meta-research agent. Your goal is to iteratively improve how a sub-agent called Scientist goes about iteratively improving a Travelling Salesman Problem solver by modifying `train.py`. They run trials, evaluate results, and reflect on what you've learned. A full series of trials is called a study. The series of studies you run is called a campaign.

## Running a study

A single script `study.py` invokes the Scientist with the following prompt `Read and follow lab/program.md`

### `study.py`
```
python study.py                              # 100 fresh-context trials (default)
python study.py --trials 5                   # 5 fresh-context trials
python study.py --persistent                 # single persistent-context invocation
python study.py --persistent --trials 10     # persistent, with ~10 trial hint
```

**Fresh context (default):** Loops N times, each a fresh `claude -p` call. The Scientist starts from scratch every trial. Best when you want independent runs without context drift.

**Persistent context (`--persistent`):** Single `claude -p` call. The Scientist keeps its context window across all trials in the study. The `--trials` value is passed as a hint in the prompt. Best when continuity and accumulated learning matter.

### What you can change
- `lab/program.md` — the Scientist's instructions
- `lab/record.py` — trial recording tools
- Anything else inside `lab/` (except for `train.py` as this is the Scientists code)

### What you must NOT change
- `study.py`, `method.md` — top-level orchestration (locked)
- `prepare.py`, `test_prepare.py` — evaluation framework (locked)
