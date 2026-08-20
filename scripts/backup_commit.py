"""Create and verify an exact-commit archive before a Git push."""

from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
import zipfile
from collections.abc import Callable, Iterable
from datetime import datetime
from pathlib import Path


class BackupError(RuntimeError):
    """Raised when an exact-commit backup cannot be proven usable."""


ZERO_SHA = "0" * 40


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


def pushed_commit_shas(lines: Iterable[str]) -> tuple[str, ...]:
    """Parse and deduplicate non-deletion local SHAs from pre-push stdin."""
    unique: list[str] = []
    for line_number, raw_line in enumerate(lines, 1):
        line = raw_line.strip()
        if not line:
            continue
        fields = line.split()
        if len(fields) != 4:
            raise BackupError(f"malformed pre-push input at line {line_number}")
        _local_ref, local_sha, _remote_ref, _remote_sha = fields
        if len(local_sha) != 40 or any(character not in "0123456789abcdefABCDEF" for character in local_sha):
            raise BackupError(f"invalid local SHA at pre-push line {line_number}: {local_sha!r}")
        local_sha = local_sha.lower()
        if local_sha != ZERO_SHA and local_sha not in unique:
            unique.append(local_sha)
    return tuple(unique)


def backup_pushed_refs(
    repo: Path,
    lines: Iterable[str],
    *,
    keep: int = 10,
    creator: Callable[..., Path] = create_backup,
) -> tuple[Path, ...]:
    """Back up every unique commit Git says it will push; never assume HEAD."""
    return tuple(creator(repo, commit=sha, keep=keep) for sha in pushed_commit_shas(lines))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--commit", default=None, help="manual exact-commit backup (defaults to HEAD)")
    parser.add_argument("--pre-push", action="store_true", help="read pushed refs from stdin")
    parser.add_argument("--keep", type=int, default=10)
    args = parser.parse_args()
    try:
        if args.pre_push:
            paths = backup_pushed_refs(args.repo, sys.stdin, keep=args.keep)
        else:
            paths = (create_backup(args.repo, commit=args.commit or "HEAD", keep=args.keep),)
    except (BackupError, OSError, zipfile.BadZipFile) as exc:
        print(f"PRE-PUSH BACKUP FAILED: {exc}")
        return 1
    if not paths:
        print("Pre-push contains only deletions; no source backup required")
    for path in paths:
        print(f"Verified exact-commit backup: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
