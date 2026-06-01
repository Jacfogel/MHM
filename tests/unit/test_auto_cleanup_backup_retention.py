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


@pytest.mark.unit
@pytest.mark.core
def test_cleanup_manifest_less_directories_respects_grace_period(backup_root):
    import time

    from core.backup_manager import cleanup_manifest_less_backup_directories

    stale_mtime = 1_700_000_000
    stale_orphan = backup_root / "user1_backup_user_data_v2_2026-01-01_02-00-00"
    stale_orphan.mkdir(parents=True)
    os.utime(stale_orphan, (stale_mtime, stale_mtime))

    recent_orphan = backup_root / "mhm_backup_in_progress"
    recent_orphan.mkdir(parents=True)
    recent_mtime = time.time() - 120
    os.utime(recent_orphan, (recent_mtime, recent_mtime))

    _make_backup_dir(backup_root, "weekly_backup_keep", stale_mtime + 10)

    removed = cleanup_manifest_less_backup_directories(
        backup_root, grace_seconds=3600
    )
    assert removed == 1

    remaining = {p.name for p in backup_root.iterdir() if p.is_dir()}
    assert "weekly_backup_keep" in remaining
    assert "mhm_backup_in_progress" in remaining
    assert "user1_backup_user_data_v2_2026-01-01_02-00-00" not in remaining


@pytest.mark.unit
@pytest.mark.core
def test_cleanup_old_backup_files_runs_manifest_less_cleanup_when_no_managed_backups(
    backup_root, monkeypatch
):
    orphan = backup_root / "legacy_orphan_dir"
    orphan.mkdir(parents=True)
    (orphan / "data.txt").write_text("x", encoding="utf-8")
    old_mtime = 1_700_000_000
    os.utime(orphan, (old_mtime, old_mtime))

    assert auto_cleanup.cleanup_old_backup_files() is True
    assert not orphan.exists()
