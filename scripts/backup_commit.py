"""Create and verify an exact-commit archive before a Git push."""

from __future__ import annotations

import argparse
import subprocess
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path


class BackupError(RuntimeError):
    """Raised when an exact-commit backup cannot be proven usable."""


def _git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=repo, text=True, capture_output=True, check=False
    )
    if result.returncode:
        raise BackupError(result.stderr.strip() or result.stdout.strip())
    return result.stdout.strip()


def create_backup(repo: Path, *, commit: str = "HEAD", keep: int = 10) -> Path:
    """Archive one Git commit, verify it, then retain the newest ``keep`` files."""
    repo = repo.resolve()
    sha = _git(repo, "rev-parse", "--verify", f"{commit}^{{commit}}")
    expected = tuple(line for line in _git(repo, "ls-tree", "-r", "--name-only", sha).splitlines() if line)
    if not expected:
        raise BackupError(f"commit {sha} contains no files")

    backup_dir = repo / "BACKUP"
    backup_dir.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    destination = backup_dir / f"N-AutoLab_{stamp}_{sha[:7]}.zip"
    with tempfile.NamedTemporaryFile(dir=backup_dir, suffix=".zip", delete=False) as handle:
        temporary = Path(handle.name)
    try:
        result = subprocess.run(
            ["git", "archive", "--format=zip", f"--output={temporary}", sha],
            cwd=repo,
            text=True,
            capture_output=True,
            check=False,
        )
        if result.returncode:
            raise BackupError(result.stderr.strip() or "git archive failed")
        with zipfile.ZipFile(temporary) as archive:
            bad_member = archive.testzip()
            if bad_member is not None:
                raise BackupError(f"ZIP CRC verification failed at {bad_member}")
            actual = {name.rstrip("/") for name in archive.namelist() if not name.endswith("/")}
            missing = sorted(set(expected) - actual)
            if missing:
                raise BackupError(f"ZIP is missing tracked files: {', '.join(missing[:5])}")
        temporary.replace(destination)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise

    archives = sorted(backup_dir.glob("N-AutoLab_*.zip"), key=lambda path: path.stat().st_mtime, reverse=True)
    for old in archives[keep:]:
        old.unlink()
    return destination


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--commit", default="HEAD")
    parser.add_argument("--keep", type=int, default=10)
    args = parser.parse_args()
    try:
        path = create_backup(args.repo, commit=args.commit, keep=args.keep)
    except (BackupError, OSError, zipfile.BadZipFile) as exc:
        print(f"PRE-PUSH BACKUP FAILED: {exc}")
        return 1
    print(f"Verified exact-commit backup: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
