#!/usr/bin/env python3
# ============================================================
# DO NOT EDIT — this file is managed at the top level.
# Neither the Supervisor nor the Scientist should modify it.
# ============================================================
#
# Runs a campaign: one or more Supervisor studies.
#
# Usage:
#   python campaign.py                       # 5 studies, opus (default)
#   python campaign.py --studies 3           # 3 studies
#   python campaign.py --timeout 7200        # 2-hour per-study timeout
#   python campaign.py --model sonnet        # use sonnet for Supervisor

import argparse
import shutil
import signal
import subprocess
import sys
from datetime import datetime
from pathlib import Path

DEFAULT_MODEL = "opus"
DEFAULT_STUDIES = 5
DEFAULT_STUDY_TIMEOUT = 36000  # 10 hours per study
ALLOWED_TOOLS = "Read,Edit,Write,Bash"
SUPERVISOR_PROMPT = "Read and follow method.md"

# Immediate exit on Ctrl-C
signal.signal(signal.SIGINT, lambda *_: sys.exit(130))


def run_campaign(num_studies=DEFAULT_STUDIES, study_timeout=DEFAULT_STUDY_TIMEOUT, model=DEFAULT_MODEL):
    """Run a campaign and return the campaign ID."""
    campaign_id = datetime.now().strftime("%Y%m%d-%H%M%S")
    log_dir = Path("logs") / campaign_id
    log_dir.mkdir(parents=True, exist_ok=True)

    claude_cmd = [
        "claude", "-p",
        "--verbose",
        "--model", model,
        "--output-format", "stream-json",
        "--allowedTools", ALLOWED_TOOLS,
    ]

    for i in range(1, num_studies + 1):
        print(f"=== Study {i} / {num_studies} ===", file=sys.stderr)

        # Archive current lab state
        archive_dir = Path("archive") / campaign_id / f"study-{i:03d}"
        shutil.copytree("lab", archive_dir, ignore=shutil.ignore_patterns("__pycache__"))
        print(f"  Archived lab/ → {archive_dir}", file=sys.stderr)

        # Reset train.py to baseline
        shutil.copy("baselines/train.py", "lab/train.py")

        # Git commit current state
        subprocess.run(["git", "add", "-A"], check=False)
        subprocess.run(
            ["git", "commit", "-m", f"campaign {campaign_id}: archive study {i} results"],
            check=False,
        )

        # Delete ephemeral files
        Path("lab/evaluations.csv").unlink(missing_ok=True)
        Path("lab/RESULTS.md").unlink(missing_ok=True)

        # Run the Supervisor
        log_file = log_dir / f"study-{i:03d}.jsonl"
        try:
            with open(log_file, "w") as f:
                subprocess.run(
                    claude_cmd,
                    input=SUPERVISOR_PROMPT,
                    text=True,
                    stdout=f,
                    stderr=sys.stderr,
                    timeout=study_timeout,
                )
        except subprocess.TimeoutExpired:
            print(f"=== Study {i} timed out after {study_timeout}s, skipping ===", file=sys.stderr)

    return campaign_id


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run a campaign: one or more Supervisor studies.")
    parser.add_argument("--studies", type=int, default=DEFAULT_STUDIES, help=f"Number of studies (default: {DEFAULT_STUDIES})")
    parser.add_argument("--timeout", type=int, default=DEFAULT_STUDY_TIMEOUT, help=f"Per-study timeout in seconds (default: {DEFAULT_STUDY_TIMEOUT})")
    parser.add_argument("--model", type=str, default=DEFAULT_MODEL, help=f"Claude model to use (default: {DEFAULT_MODEL})")
    args = parser.parse_args()

    campaign_id = run_campaign(num_studies=args.studies, study_timeout=args.timeout, model=args.model)
    print(f"Campaign: {campaign_id}", file=sys.stderr)
