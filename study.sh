#!/usr/bin/env bash
# ============================================================
# DO NOT EDIT — this file is managed at the top level.
# Neither the Supervisor nor the Scientist should modify it.
# ============================================================
#
# Runs one full study: a single Scientist invocation that keeps
# context across all trials.

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

claude -p \
    --allowedTools "${ALLOWED_TOOLS[@]}" \
    "Read and follow lab/program.md"
