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

import subprocess
import sys


PATTERNS = [
    r"scientist\..*\.prepare",
    r"claude.*scientist",
]


def shutdown():
    """Kill processes matching scientist patterns."""
    killed_any = False
    for pattern in PATTERNS:
        # pgrep first to report what will be killed
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
        print("  No scientist processes found.", file=sys.stderr)


def main():
    print("Shutdown: killing all scientist processes", file=sys.stderr)
    shutdown()
    print("Done.", file=sys.stderr)


if __name__ == "__main__":
    main()
