#!/usr/bin/env bash
# ============================================================
# DO NOT EDIT — this file is managed at the top level.
# Neither the Supervisor nor the Scientist should modify it.
# ============================================================
#
# Runs a study: one or more Scientist invocations.
#
# Usage:
#   ./study.sh                       # 100 fresh-context trials
#   ./study.sh --trials 5            # 5 fresh-context trials
#   ./study.sh --persistent          # single persistent-context invocation
#   ./study.sh --persistent --trials 10  # persistent, hint "aim for ~10 trials"

set -euo pipefail

# --- Defaults ---
NUM_TRIALS=100
PERSISTENT=false

# --- Parse args ---
while [[ $# -gt 0 ]]; do
    case "$1" in
        --trials)
            NUM_TRIALS="$2"
            shift 2
            ;;
        --persistent)
            PERSISTENT=true
            shift
            ;;
        *)
            echo "Unknown option: $1" >&2
            echo "Usage: $0 [--trials N] [--persistent]" >&2
            exit 1
            ;;
    esac
done

# --- Allowed tools (shared) ---
ALLOWED_TOOLS=(
    "Read"
    "Edit"
    "Write"
    "Bash(python3:*)"
    "Bash(grep:*)"
    "Bash(tail:*)"
    "Bash(cat:*)"
)

# --- Run ---
if [ "$PERSISTENT" = true ]; then
    echo "=== Persistent study (aim for ~${NUM_TRIALS} trials) ==="
    claude -p \
        --allowedTools "${ALLOWED_TOOLS[@]}" \
        "Read and follow lab/program.md. Aim for around ${NUM_TRIALS} trials."
else
    for i in $(seq 1 "$NUM_TRIALS"); do
        echo "=== Trial $i / $NUM_TRIALS ==="
        claude -p \
            --allowedTools "${ALLOWED_TOOLS[@]}" \
            "Read and follow lab/program.md"
    done
fi
