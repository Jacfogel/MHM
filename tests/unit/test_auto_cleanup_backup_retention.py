"""Unit tests for backup retention behavior in core.auto_cleanup."""

import os
import shutil
from pathlib import Path
from uuid import uuid4

import pytest

import core.auto_cleanup as auto_cleanup
import core.config as core_config


pytestmark = [pytest.mark.core]

def _make_backup_dir(root: Path, name: str, mtime: int) -> Path:
    path = root / name
    path.mkdir(parents=True, exist_ok=True)
    (path / "manifest.json").write_text(
        '{"backup_name":"x","created_at":"2026-01-01 00:00:00"}',
        encoding="utf-8",
    )
    os.utime(path, (mtime, mtime))
    os.utime(path / "manifest.json", (mtime, mtime))
    return path


@pytest.fixture
def backup_root(monkeypatch):
    tmp = Path.cwd() / f".autocleanup_backups_{uuid4().hex}"
    tmp.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(core_config, "get_backups_dir", lambda: str(tmp), raising=False)
    monkeypatch.setenv("BACKUP_RETENTION_DAYS", "365")
    yield tmp
    shutil.rmtree(tmp, ignore_errors=True)


@pytest.mark.unit
@pytest.mark.core
def test_cleanup_old_backup_files_caps_total_backups_at_ten(backup_root):
    base = 2_000_000_000
    for i in range(12):
        _make_backup_dir(backup_root, f"auto_backup_{i}", base + i)

    assert auto_cleanup.cleanup_old_backup_files() is True
    remaining = [p for p in backup_root.iterdir() if p.is_dir()]
    assert len(remaining) == 10


@pytest.mark.unit
@pytest.mark.core
def test_cleanup_old_backup_files_preserves_weekly_backups_in_separate_bucket(
    backup_root,
):
    base = 2_100_000_000
    for i in range(9):
        _make_backup_dir(backup_root, f"weekly_backup_{i}", base + i)
    for i in range(12):
        _make_backup_dir(backup_root, f"auto_backup_{i}", base + 100 + i)

    assert auto_cleanup.cleanup_old_backup_files() is True

    # Weekly and non-weekly retention are applied independently.
    remaining = sorted([p.name for p in backup_root.iterdir() if p.is_dir()])
    assert len(remaining) == 14
    weekly_remaining = [name for name in remaining if name.startswith("weekly_backup_")]
    auto_remaining = [name for name in remaining if name.startswith("auto_backup_")]
    assert len(weekly_remaining) == 4
    assert len(auto_remaining) == 10
    assert "weekly_backup_0" not in remaining
    assert "auto_backup_0" not in remaining
    assert "auto_backup_1" not in remaining
