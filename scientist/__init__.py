from pathlib import Path

SCIENTIST_DIR = Path(__file__).parent


def discover_problems():
    """Auto-discover problem directories under scientist/."""
    return sorted(
        d.name for d in SCIENTIST_DIR.iterdir()
        if d.is_dir() and (d / "program.md").exists()
    )
