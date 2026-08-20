"""Install the repository-owned Git hooks path."""

from __future__ import annotations

import subprocess
from pathlib import Path


def main() -> int:
    repo = Path(__file__).resolve().parents[1]
    subprocess.run(
        ["git", "config", "core.hooksPath", ".githooks"], cwd=repo, check=True
    )
    print("Installed Git hooks: core.hooksPath=.githooks")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
