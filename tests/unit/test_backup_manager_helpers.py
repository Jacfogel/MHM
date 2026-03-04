import json
import os
import zipfile
from pathlib import Path
from unittest.mock import Mock

import pytest

import core.config
import core.backup_manager as backup_module
from core.backup_manager import (
    BackupManager,
    _validate_system_state__ensure_user_data_directory,
    _validate_system_state__validate_user_index,
    create_automatic_backup,
    perform_safe_operation,
    validate_system_state,
)


@pytest.fixture
def manager(tmp_path, monkeypatch):
    backup_dir = tmp_path / "backups"
    monkeypatch.setenv("MHM_TESTING", "1")
    monkeypatch.setenv("BACKUP_FORMAT", "zip")
    monkeypatch.setattr(core.config, "get_backups_dir", lambda: str(backup_dir))
    return BackupManager()


@pytest.mark.unit
class TestBackupManagerHelpers:
    def test_validate_user_index_missing_file_returns_true(self, tmp_path, monkeypatch):
        monkeypatch.setattr(core.config, "BASE_DATA_DIR", str(tmp_path))
        monkeypatch.setattr(core.config, "USER_INFO_DIR_PATH", str(tmp_path / "users"))
        assert _validate_system_state__validate_user_index() is True

    def test_validate_user_index_non_dict_returns_false(self, tmp_path, monkeypatch):
        (tmp_path / "users").mkdir(parents=True, exist_ok=True)
        (tmp_path / "user_index.json").write_text(json.dumps(["bad"]), encoding="utf-8")
        monkeypatch.setattr(core.config, "BASE_DATA_DIR", str(tmp_path))
        monkeypatch.setattr(core.config, "USER_INFO_DIR_PATH", str(tmp_path / "users"))

        assert _validate_system_state__validate_user_index() is False

    def test_validate_user_index_missing_user_directory_only_warns(self, tmp_path, monkeypatch):
        user_id = "12345678-1234-1234-1234-1234567890ab"
        (tmp_path / "users").mkdir(parents=True, exist_ok=True)
        (tmp_path / "user_index.json").write_text(
            json.dumps({"last_updated": "now", "alice": user_id}), encoding="utf-8"
        )
        monkeypatch.setattr(core.config, "BASE_DATA_DIR", str(tmp_path))
        monkeypatch.setattr(core.config, "USER_INFO_DIR_PATH", str(tmp_path / "users"))

        assert _validate_system_state__validate_user_index() is True

    def test_ensure_user_data_directory_creates_path(self, tmp_path, monkeypatch):
        user_dir = tmp_path / "users"
        monkeypatch.setattr(core.config, "USER_INFO_DIR_PATH", str(user_dir))

        assert _validate_system_state__ensure_user_data_directory() is True
        assert user_dir.exists()

    def test_validate_system_state_short_circuits_on_failures(self, monkeypatch):
        monkeypatch.setattr(backup_module, "_validate_system_state__validate_user_index", lambda: False)
        assert validate_system_state() is False

        monkeypatch.setattr(backup_module, "_validate_system_state__validate_user_index", lambda: True)
        monkeypatch.setattr(backup_module, "_validate_system_state__ensure_user_data_directory", lambda: False)
        assert validate_system_state() is False

    def test_create_automatic_backup_uses_global_manager(self, monkeypatch):
        fake_manager = Mock()
        fake_manager.create_backup.return_value = "path/to/backup"
        monkeypatch.setattr(backup_module, "backup_manager", fake_manager)
        monkeypatch.setattr(backup_module, "now_timestamp_filename", lambda: "STAMP")

        result = create_automatic_backup("cleanup")

        assert result == "path/to/backup"
        fake_manager.create_backup.assert_called_once_with("auto_cleanup_STAMP")

    def test_perform_safe_operation_failures_and_rollback(self, monkeypatch):
        monkeypatch.setattr(backup_module, "create_automatic_backup", lambda _name: None)
        assert perform_safe_operation(lambda: True) is False

        restore_mock = Mock()
        monkeypatch.setattr(backup_module.backup_manager, "restore_backup", restore_mock)
        monkeypatch.setattr(backup_module, "create_automatic_backup", lambda _name: "b.zip")
        monkeypatch.setattr(backup_module, "validate_system_state", lambda: False)
        assert perform_safe_operation(lambda: True) is False
        restore_mock.assert_called_with("b.zip")

    def test_perform_safe_operation_exception_rolls_back(self, monkeypatch):
        restore_mock = Mock()
        monkeypatch.setattr(backup_module.backup_manager, "restore_backup", restore_mock)
        monkeypatch.setattr(backup_module, "create_automatic_backup", lambda _name: "b.zip")

        def _boom():
            raise RuntimeError("fail")

        assert perform_safe_operation(_boom) is False
        restore_mock.assert_called_once_with("b.zip")

    def test_perform_safe_operation_success_returns_operation_result(self, monkeypatch):
        monkeypatch.setattr(backup_module, "create_automatic_backup", lambda _name: "b.zip")
        monkeypatch.setattr(backup_module, "validate_system_state", lambda: True)

        assert perform_safe_operation(lambda: "OK") == "OK"

    def test_extract_zip_prefix_to_destination_skips_unsafe_paths(self, manager, tmp_path):
        archive = tmp_path / "data.zip"
        with zipfile.ZipFile(archive, "w") as zf:
            zf.writestr("users/good.txt", "ok")
            zf.writestr("users/../../evil.txt", "bad")
            zf.writestr("config/skip.txt", "cfg")

        destination = tmp_path / "restore"
        with zipfile.ZipFile(archive, "r") as zf:
            count = manager._extract_zip_prefix_to_destination(zf, "users/", destination)

        assert count == 1
        assert (destination / "users" / "good.txt").exists()
        assert not (destination / "evil.txt").exists()

    def test_validate_directory_backup_branches(self, manager, tmp_path):
        missing = manager._validate_backup__validate_directory_backup(str(tmp_path / "none"))
        assert any("Backup directory not found" in err for err in missing)

        root_no_manifest = tmp_path / "no_manifest"
        root_no_manifest.mkdir()
        missing_manifest = manager._validate_backup__validate_directory_backup(str(root_no_manifest))
        assert "Backup missing manifest.json" in missing_manifest

        root_bad_json = tmp_path / "bad_manifest"
        root_bad_json.mkdir()
        (root_bad_json / "manifest.json").write_text("{invalid", encoding="utf-8")
        bad_json = manager._validate_backup__validate_directory_backup(str(root_bad_json))
        assert "Manifest.json is not valid JSON" in bad_json

        root_users_required = tmp_path / "users_required"
        root_users_required.mkdir()
        (root_users_required / "manifest.json").write_text(
            json.dumps(
                {
                    "created_at": "2026-01-01 00:00:00",
                    "backup_name": "b1",
                    "includes": {"users": True},
                }
            ),
            encoding="utf-8",
        )
        users_required = manager._validate_backup__validate_directory_backup(str(root_users_required))
        assert any("no user data found" in err for err in users_required)

    def test_get_backup_info_for_directory_without_manifest(self, manager, tmp_path):
        backup_dir = tmp_path / "backup_no_manifest"
        backup_dir.mkdir()
        (backup_dir / "payload.txt").write_text("x", encoding="utf-8")

        info = manager._get_backup_info(str(backup_dir))

        assert info["file_name"] == "backup_no_manifest"
        assert info["backup_name"] == "backup_no_manifest"
        assert info["file_size"] >= 1

    def test_get_backup_info_for_zip_without_manifest(self, manager, tmp_path):
        backup_zip = tmp_path / "legacy.zip"
        with zipfile.ZipFile(backup_zip, "w") as zf:
            zf.writestr("users/a.json", "{}")

        info = manager._get_backup_info(str(backup_zip))

        assert info["file_name"] == "legacy.zip"
        assert info["backup_name"] == "Unknown"
        assert info["file_size"] > 0

    def test_restore_backup_to_path_validates_inputs(self, manager, tmp_path):
        assert manager.restore_backup_to_path("", str(tmp_path)) is False
        assert manager.restore_backup_to_path("fake", "") is False
        assert manager.restore_backup_to_path("fake", str(tmp_path), restore_users="yes") is False
        assert manager.restore_backup_to_path("fake", str(tmp_path), restore_config="yes") is False
        assert manager.restore_backup_to_path(str(tmp_path / "missing.zip"), str(tmp_path)) is False

    def test_restore_backup_to_path_directory_extracts_selected_prefixes(self, manager, tmp_path, monkeypatch):
        backup_root = tmp_path / "dir_backup"
        (backup_root / "users" / "u1").mkdir(parents=True)
        (backup_root / "users" / "u1" / "account.json").write_text("{}", encoding="utf-8")
        (backup_root / "config").mkdir(parents=True)
        (backup_root / "config" / "app.env").write_text("X=1", encoding="utf-8")
        (backup_root / "manifest.json").write_text(
            json.dumps(
                {
                    "created_at": "2026-01-01 00:00:00",
                    "backup_name": "dir_backup",
                    "includes": {"users": True, "config": True},
                }
            ),
            encoding="utf-8",
        )

        destination = tmp_path / "restore_here"
        monkeypatch.setattr(manager, "validate_backup", lambda _path: (True, []))

        ok = manager.restore_backup_to_path(str(backup_root), str(destination), True, False)
        assert ok is True
        assert (destination / "users" / "u1" / "account.json").exists()
        assert not (destination / "config" / "app.env").exists()

        ok2 = manager.restore_backup_to_path(str(backup_root), str(destination), False, True)
        assert ok2 is True
        assert (destination / "config" / "app.env").exists()

    def test_get_backup_artifact_size_bytes_for_file_dir_and_missing(self, manager, tmp_path):
        file_artifact = tmp_path / "artifact.zip"
        file_artifact.write_bytes(b"abcde")
        assert manager._get_backup_artifact_size_bytes(str(file_artifact)) == 5

        dir_artifact = tmp_path / "artifact_dir"
        dir_artifact.mkdir()
        (dir_artifact / "a.txt").write_text("hello", encoding="utf-8")
        (dir_artifact / "b.txt").write_text("world", encoding="utf-8")
        assert manager._get_backup_artifact_size_bytes(str(dir_artifact)) == 10

        assert manager._get_backup_artifact_size_bytes(str(tmp_path / "missing")) == 0

    def test_is_directory_backup_path(self, manager, tmp_path):
        backup_dir = tmp_path / "backupA"
        backup_dir.mkdir()
        (backup_dir / "manifest.json").write_text("{}", encoding="utf-8")
        assert manager._is_directory_backup_path(backup_dir) is True
        assert manager._is_directory_backup_path(tmp_path / "missing") is False

    def test_list_backups_missing_directory_returns_empty(self, manager, tmp_path):
        manager.backup_dir = str(tmp_path / "does_not_exist")
        assert manager.list_backups() == []

    def test_cleanup_old_backups_applies_age_and_count_limits(self, manager, tmp_path, monkeypatch):
        backup_dir = tmp_path / "retention_backups"
        backup_dir.mkdir()
        manager.backup_dir = str(backup_dir)
        manager.backup_retention_days = 1
        manager.weekly_max_backups = 2
        manager.max_backups = 2

        now_ts = 1_800_000_000.0
        monkeypatch.setattr("core.backup_manager.time.time", lambda: now_ts)

        # Old by age (should be removed regardless of count buckets).
        old_weekly = backup_dir / "weekly_backup_old.zip"
        old_weekly.write_bytes(b"x")
        os.utime(old_weekly, (now_ts - 10 * 24 * 3600, now_ts - 10 * 24 * 3600))

        # Weekly bucket (3 files, keep 2 newest).
        weekly_files = []
        for idx, age_seconds in enumerate([100, 200, 300], start=1):
            path = backup_dir / f"weekly_backup_{idx}.zip"
            path.write_bytes(b"w")
            os.utime(path, (now_ts - age_seconds, now_ts - age_seconds))
            weekly_files.append(path)

        # Non-weekly bucket (4 files, keep 2 newest).
        auto_files = []
        for idx, age_seconds in enumerate([100, 200, 300, 400], start=1):
            path = backup_dir / f"auto_backup_{idx}.zip"
            path.write_bytes(b"a")
            os.utime(path, (now_ts - age_seconds, now_ts - age_seconds))
            auto_files.append(path)

        manager._cleanup_old_backups()

        remaining = {p.name for p in backup_dir.glob("*.zip")}
        assert "weekly_backup_old.zip" not in remaining
        assert "weekly_backup_3.zip" not in remaining  # oldest weekly evicted by count
        assert "auto_backup_3.zip" not in remaining  # oldest non-weekly evicted
        assert "auto_backup_4.zip" not in remaining  # oldest non-weekly evicted
        assert {"weekly_backup_1.zip", "weekly_backup_2.zip"}.issubset(remaining)
        assert {"auto_backup_1.zip", "auto_backup_2.zip"}.issubset(remaining)
