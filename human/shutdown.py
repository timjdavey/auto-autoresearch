#!/usr/bin/env python3
# ============================================================
# DO NOT EDIT — this file is managed at the top level.
# Neither the Supervisor nor the Scientist should modify it.
# ============================================================
#
# Kill all running scientist / experiment processes.
#
# Usage:
#   uv run shutdown

import argparse
import subprocess
import sys


SCIENTIST_PATTERNS = [
    r"scientist\..*\.prepare",
    r"claude.*scientist",
]

CLAUDE_PATTERNS = [
    r"claude",
]


def kill_patterns(patterns, label):
    """Kill processes matching the given patterns."""
    killed_any = False
    for pattern in patterns:
        result = subprocess.run(
            ["pgrep", "-fl", pattern],
            capture_output=True, text=True,
        )
        if result.stdout.strip():
            for line in result.stdout.strip().splitlines():
                print(f"  Killing: {line}", file=sys.stderr)
            killed_any = True
            subprocess.run(["pkill", "-f", pattern])

    if not killed_any:
        print(f"  No {label} processes found.", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(description="Kill scientist or Claude processes.")
    parser.add_argument(
        "--all", action="store_true",
        help="Kill all Claude processes, not just scientist ones.",
    )
    args = parser.parse_args()

    if args.all:
        print("Shutdown: killing ALL Claude processes", file=sys.stderr)
        kill_patterns(CLAUDE_PATTERNS, "Claude")
    else:
        print("Shutdown: killing all scientist processes", file=sys.stderr)
        kill_patterns(SCIENTIST_PATTERNS, "scientist")
    print("Done.", file=sys.stderr)


if __name__ == "__main__":
    main()
