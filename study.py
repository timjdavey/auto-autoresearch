#!/usr/bin/env python3
# ============================================================
# DO NOT EDIT — this file is managed at the top level.
# Neither the Supervisor nor the Scientist should modify it.
# ============================================================
#
# Runs a study: one or more Scientist invocations.
#
# Usage:
#   python study.py                       # 100 fresh-context trials
#   python study.py --trials 5            # 5 fresh-context trials
#   python study.py --persistent          # single persistent-context invocation
#   python study.py --persistent --trials 10  # persistent, hint "aim for ~10 trials"

import argparse
import signal
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ALLOWED_TOOLS = "Read,Edit,Write,Bash(python3:*),Bash(grep:*),Bash(tail:*),Bash(cat:*)"

# Immediate exit on Ctrl-C
signal.signal(signal.SIGINT, lambda *_: sys.exit(130))


def run_study(num_trials=100, persistent=False):
    """Run a study and return the log directory path."""
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    log_dir = Path("logs") / timestamp
    log_dir.mkdir(parents=True, exist_ok=True)

    claude_cmd = [
        "claude", "-p",
        "--verbose",
        "--output-format", "stream-json",
        "--allowedTools", ALLOWED_TOOLS,
    ]

    if persistent:
        print(f"=== Persistent study (aim for ~{num_trials} trials) ===", file=sys.stderr)
        log_file = log_dir / "study.jsonl"
        prompt = f"Read and follow lab/program.md. Aim for around {num_trials} trials."
        with open(log_file, "w") as f:
            subprocess.run(claude_cmd, input=prompt, text=True, stdout=f, stderr=sys.stderr)
    else:
        for i in range(1, num_trials + 1):
            print(f"=== Trial {i} / {num_trials} ===", file=sys.stderr)
            log_file = log_dir / f"trial-{i:03d}.jsonl"
            with open(log_file, "w") as f:
                subprocess.run(
                    claude_cmd,
                    input="Read and follow lab/program.md",
                    text=True,
                    stdout=f,
                    stderr=sys.stderr,
                )

    return log_dir


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run a study: one or more Scientist invocations.")
    parser.add_argument("--trials", type=int, default=100, help="Number of trials (default: 100)")
    parser.add_argument("--persistent", action="store_true", help="Single persistent-context invocation")
    args = parser.parse_args()

    log_dir = run_study(num_trials=args.trials, persistent=args.persistent)
    print(f"Logs: {log_dir}", file=sys.stderr)
