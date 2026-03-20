#!/usr/bin/env bash
# ============================================================
# DO NOT EDIT — this file is managed at the top level.
# Neither the Supervisor nor the Scientist should modify it.
# ============================================================
#
# Runs 100 independent trials: each is a fresh Scientist
# invocation with no carried-over context.

set -euo pipefail

ALLOWED_TOOLS=(
    "Read"
    "Edit"
    "Write"
    "Bash(python3:*)"
    "Bash(grep:*)"
    "Bash(tail:*)"
    "Bash(cat:*)"
)

NUM_TRIALS="${1:-100}"

for i in $(seq 1 "$NUM_TRIALS"); do
    echo "=== Trial $i / $NUM_TRIALS ==="
    claude -p \
        --allowedTools "${ALLOWED_TOOLS[@]}" \
        "Read and follow lab/program.md"
done
