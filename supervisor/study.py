#!/usr/bin/env python3
# ============================================================
# DO NOT EDIT — this file is managed at the top level.
# Neither the Supervisor nor the Scientist should modify it.
# ============================================================
#
# Runs a study: one or more Scientist invocations.
#
# Usage:
#   python study.py                       # 100 trials, sonnet (default)
#   python study.py --trials 5            # 5 fresh-context trials
#   python study.py --timeout 300         # 5-minute per-trial timeout
#   python study.py --opus                # run with opus (for testing)

import argparse
import shutil
import signal
import subprocess
import sys
from datetime import datetime
from pathlib import Path

DEFAULT_MODEL = "sonnet"
DEFAULT_TRIALS = 100
DEFAULT_TIMEOUT = 300
ALLOWED_TOOLS = "Read,Edit,Write,Bash(python3:*),Bash(grep:*),Bash(tail:*),Bash(cat:*)"
SCIENTIST_PROMPT = "Read and follow scientist/program.md"

# Immediate exit on Ctrl-C
signal.signal(signal.SIGINT, lambda *_: sys.exit(130))


def run_study(num_trials=DEFAULT_TRIALS, trial_timeout=DEFAULT_TIMEOUT, model=DEFAULT_MODEL):
    """Run a study and return the log directory path."""
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    log_dir = Path("logs") / timestamp
    log_dir.mkdir(parents=True, exist_ok=True)

    claude_cmd = [
        "claude", "-p",
        "--verbose",
        "--model", model,
        "--output-format", "stream-json",
        "--allowedTools", ALLOWED_TOOLS,
    ]

    archive_dir = Path("scientist/archive") / timestamp
    archive_dir.mkdir(parents=True, exist_ok=True)

    for i in range(1, num_trials + 1):
        print(f"=== Trial {i} / {num_trials} ===", file=sys.stderr)

        # Archive train.py before Scientist modifies it
        shutil.copy("scientist/train.py", archive_dir / f"trial-{i:03d}.py")

        log_file = log_dir / f"trial-{i:03d}.jsonl"
        try:
            with open(log_file, "w") as f:
                subprocess.run(
                    claude_cmd,
                    input=SCIENTIST_PROMPT,
                    text=True,
                    stdout=f,
                    stderr=sys.stderr,
                    timeout=trial_timeout,
                )
        except subprocess.TimeoutExpired:
            print(f"=== Trial {i} timed out after {trial_timeout}s, skipping ===", file=sys.stderr)

    return log_dir


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run a study: one or more Scientist invocations.")
    parser.add_argument("--trials", type=int, default=DEFAULT_TRIALS, help=f"Number of trials (default: {DEFAULT_TRIALS})")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT, help=f"Per-trial timeout in seconds (default: {DEFAULT_TIMEOUT})")
    parser.add_argument("--model", type=str, default=DEFAULT_MODEL, help=f"Claude model to use (default: {DEFAULT_MODEL})")
    parser.add_argument("--opus", action="store_true", help="Shorthand for --model opus")
    args = parser.parse_args()

    model = "opus" if args.opus else args.model
    log_dir = run_study(num_trials=args.trials, trial_timeout=args.timeout, model=model)
    print(f"Logs: {log_dir}", file=sys.stderr)
