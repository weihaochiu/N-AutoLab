from __future__ import annotations

import subprocess
import sys
import zipfile
from pathlib import Path

from scripts.backup_commit import backup_pushed_refs, create_backup, pushed_commit_shas
from scripts.backup_commit import BackupError
import pytest


def _init_repo(path: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=path, check=True)
    (path / ".gitignore").write_text("ignored.txt\nBACKUP/\n", encoding="utf-8")
    (path / "tracked.txt").write_text("committed\n", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=path, check=True)
    subprocess.run(["git", "commit", "-qm", "fixture"], cwd=path, check=True)


def test_backup_is_exact_commit_not_dirty_tree(tmp_path: Path) -> None:
    _init_repo(tmp_path)
    (tmp_path / "tracked.txt").write_text("dirty\n", encoding="utf-8")
    (tmp_path / "ignored.txt").write_text("local\n", encoding="utf-8")
    archive_path = create_backup(tmp_path)
    with zipfile.ZipFile(archive_path) as archive:
        assert archive.read("tracked.txt").decode().splitlines() == ["committed"]
        assert "ignored.txt" not in archive.namelist()
        restore = tmp_path / "restore"
        archive.extractall(restore)
    assert (restore / "tracked.txt").read_text().splitlines() == ["committed"]


def test_backup_retains_latest_ten(tmp_path: Path) -> None:
    _init_repo(tmp_path)
    for _ in range(11):
        create_backup(tmp_path)
    assert len(list((tmp_path / "BACKUP").glob("N-AutoLab_*.zip"))) == 10


def test_backup_failure_does_not_delete_verified_archives(tmp_path: Path) -> None:
    _init_repo(tmp_path)
    for _ in range(10): create_backup(tmp_path)
    before = {path.name for path in (tmp_path / "BACKUP").glob("*.zip")}
    with pytest.raises(BackupError): create_backup(tmp_path, commit="missing-commit")
    assert {path.name for path in (tmp_path / "BACKUP").glob("*.zip")} == before


def _update(local_ref: str, local_sha: str, remote_ref: str = "refs/heads/main") -> str:
    return f"{local_ref} {local_sha} {remote_ref} {'0' * 40}\n"


def test_pre_push_parses_multiple_refs_deduplicates_and_skips_deletion() -> None:
    sha_one = "1" * 40; sha_two = "2" * 40
    lines = [
        _update("refs/heads/main", sha_one),
        _update("refs/tags/v1", sha_one, "refs/tags/v1"),
        _update("refs/heads/feature", sha_two, "refs/heads/feature"),
        _update("(delete)", "0" * 40, "refs/heads/old"),
    ]
    assert pushed_commit_shas(lines) == (sha_one, sha_two)
    calls = []
    def creator(repo, *, commit, keep):
        calls.append((repo, commit, keep)); return repo / f"{commit}.zip"
    paths = backup_pushed_refs(Path("repo"), lines, creator=creator)
    assert [call[1] for call in calls] == [sha_one, sha_two]
    assert len(paths) == 2


def test_pre_push_non_head_sha_creates_that_archive_not_head(tmp_path: Path) -> None:
    _init_repo(tmp_path)
    pushed_sha = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=tmp_path, text=True, capture_output=True, check=True
    ).stdout.strip()
    (tmp_path / "tracked.txt").write_text("second\n", encoding="utf-8")
    subprocess.run(["git", "add", "tracked.txt"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-qm", "second"], cwd=tmp_path, check=True)
    head_sha = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=tmp_path, text=True, capture_output=True, check=True
    ).stdout.strip()
    assert pushed_sha != head_sha
    script = Path(__file__).resolve().parents[2] / "scripts" / "backup_commit.py"
    result = subprocess.run(
        [sys.executable, str(script), "--pre-push", "--repo", str(tmp_path)],
        input=_update("refs/heads/old", pushed_sha), text=True, capture_output=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    archives = list((tmp_path / "BACKUP").glob("*.zip"))
    assert len(archives) == 1
    assert pushed_sha[:7] in archives[0].name
    assert head_sha[:7] not in archives[0].name


def test_pre_push_deletion_needs_no_archive_and_failure_blocks(tmp_path: Path) -> None:
    _init_repo(tmp_path)
    script = Path(__file__).resolve().parents[2] / "scripts" / "backup_commit.py"
    deletion = subprocess.run(
        [sys.executable, str(script), "--pre-push", "--repo", str(tmp_path)],
        input=_update("(delete)", "0" * 40), text=True, capture_output=True,
    )
    assert deletion.returncode == 0
    assert not (tmp_path / "BACKUP").exists()
    failure = subprocess.run(
        [sys.executable, str(script), "--pre-push", "--repo", str(tmp_path)],
        input=_update("refs/heads/missing", "f" * 40), text=True, capture_output=True,
    )
    assert failure.returncode != 0
    assert "PRE-PUSH BACKUP FAILED" in failure.stdout


def test_tracked_hook_uses_pre_push_stdin_not_head() -> None:
    hook = (Path(__file__).resolve().parents[2] / ".githooks" / "pre-push").read_text()
    assert "--pre-push" in hook
    assert "--commit HEAD" not in hook
