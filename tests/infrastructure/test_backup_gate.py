from __future__ import annotations

import subprocess
import zipfile
from pathlib import Path

from scripts.backup_commit import create_backup
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
