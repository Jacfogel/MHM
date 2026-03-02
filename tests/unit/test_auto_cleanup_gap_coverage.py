from __future__ import annotations

import os
from pathlib import Path

import pytest

import core.auto_cleanup as auto_cleanup
import core.config as core_config


@pytest.mark.unit
def test_calculate_pyc_files_size_logs_warning_on_getsize_error(monkeypatch, tmp_path):
    pyc_file = tmp_path / "bad.pyc"
    pyc_file.write_text("x", encoding="utf-8")

    warnings = []
    monkeypatch.setattr(auto_cleanup.logger, "warning", lambda msg: warnings.append(msg))
    monkeypatch.setattr(auto_cleanup.os.path, "exists", lambda p: True)
    monkeypatch.setattr(
        auto_cleanup.os.path, "getsize", lambda p: (_ for _ in ()).throw(OSError("boom"))
    )

    size = auto_cleanup._calculate_cache_size__calculate_pyc_files_size([str(pyc_file)])
    assert size == 0
    assert any("Error calculating size" in msg for msg in warnings)


@pytest.mark.unit
def test_remove_cache_directories_and_files_warning_paths(monkeypatch, tmp_path):
    pycache_dir = tmp_path / "__pycache__"
    pycache_dir.mkdir(parents=True, exist_ok=True)
    pyc_file = tmp_path / "a.pyc"
    pyc_file.write_text("x", encoding="utf-8")

    warnings = []
    monkeypatch.setattr(auto_cleanup.logger, "warning", lambda msg: warnings.append(msg))
    monkeypatch.setattr(auto_cleanup.shutil, "rmtree", lambda *_args, **_kwargs: (_ for _ in ()).throw(PermissionError("nope")))
    monkeypatch.setattr(auto_cleanup.os, "remove", lambda *_args, **_kwargs: (_ for _ in ()).throw(PermissionError("nope")))

    removed_dirs = auto_cleanup._perform_cleanup__remove_cache_directories([str(pycache_dir)])
    removed_files = auto_cleanup._perform_cleanup__remove_cache_files_list([str(pyc_file)])
    assert removed_dirs == 0
    assert removed_files == 0
    assert any("Failed to remove directory" in msg for msg in warnings)
    assert any("Failed to remove file" in msg for msg in warnings)


@pytest.mark.unit
def test_cleanup_old_backup_files_missing_dir_returns_true(monkeypatch, tmp_path):
    missing = tmp_path / "not-there"
    monkeypatch.setattr(core_config, "get_backups_dir", lambda: str(missing), raising=False)
    assert auto_cleanup.cleanup_old_backup_files() is True


@pytest.mark.unit
def test_cleanup_old_request_files_old_and_failed_remove(monkeypatch, tmp_path):
    requests_dir = tmp_path / "requests"
    requests_dir.mkdir(parents=True, exist_ok=True)
    old_file = requests_dir / "old.req"
    keep_file = requests_dir / "new.req"
    old_file.write_text("old", encoding="utf-8")
    keep_file.write_text("new", encoding="utf-8")

    now = 2_100_000_000
    old_mtime = now - (8 * 24 * 3600)
    new_mtime = now - (1 * 24 * 3600)
    os.utime(old_file, (old_mtime, old_mtime))
    os.utime(keep_file, (new_mtime, new_mtime))

    monkeypatch.setattr(core_config, "BASE_DATA_DIR", str(tmp_path), raising=False)
    monkeypatch.setattr(auto_cleanup.time, "time", lambda: now)

    warnings = []
    monkeypatch.setattr(auto_cleanup.logger, "warning", lambda msg: warnings.append(msg))

    real_remove = auto_cleanup.os.remove

    def flaky_remove(path):
        if str(path).endswith("old.req"):
            raise PermissionError("locked")
        return real_remove(path)

    monkeypatch.setattr(auto_cleanup.os, "remove", flaky_remove)

    assert auto_cleanup.cleanup_old_request_files() is True
    assert old_file.exists()
    assert keep_file.exists()
    assert any("Failed to remove old request file" in msg for msg in warnings)


@pytest.mark.unit
def test_cleanup_old_message_archives_user_iteration_warnings(monkeypatch, tmp_path):
    base_dir = tmp_path / "data"
    archives = base_dir / "users" / "u1" / "messages" / "archives"
    archives.mkdir(parents=True, exist_ok=True)
    (base_dir / "users" / "u2" / "messages" / "archives").mkdir(
        parents=True, exist_ok=True
    )
    old_archive = archives / "sent_messages_archive_old.json"
    old_archive.write_text("{}", encoding="utf-8")

    now = 2_100_000_000
    old_mtime = now - (100 * 24 * 3600)
    os.utime(old_archive, (old_mtime, old_mtime))

    monkeypatch.setattr(core_config, "BASE_DATA_DIR", str(base_dir), raising=False)
    monkeypatch.setattr(auto_cleanup.time, "time", lambda: now)

    def fake_get_all_user_ids():
        return ["u1", "u2"]

    warnings = []
    monkeypatch.setattr(auto_cleanup.logger, "warning", lambda msg: warnings.append(msg))
    monkeypatch.setattr(
        auto_cleanup.os,
        "remove",
        lambda _p: (_ for _ in ()).throw(PermissionError("locked")),
    )
    monkeypatch.setattr(
        "core.user_data_handlers.get_all_user_ids",
        fake_get_all_user_ids,
    )

    real_iterdir = Path.iterdir

    def patched_iterdir(self):
        if str(self).endswith(str(Path("u2") / "messages" / "archives")):
            raise RuntimeError("bad user dir")
        return real_iterdir(self)

    monkeypatch.setattr(Path, "iterdir", patched_iterdir)

    assert auto_cleanup.cleanup_old_message_archives() is True
    assert any("Failed to remove old archive" in msg for msg in warnings)
    assert any("Failed to clean archives for user u2" in msg for msg in warnings)


@pytest.mark.unit
def test_cleanup_old_backup_files_branches_with_zip_artifacts(monkeypatch, tmp_path):
    backup_dir = tmp_path / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)

    now = 2_100_000_000
    monkeypatch.setattr(auto_cleanup.time, "time", lambda: now)
    monkeypatch.setenv("BACKUP_RETENTION_DAYS", "invalid")
    monkeypatch.setenv("WEEKLY_BACKUP_MAX_KEEP", "invalid")
    monkeypatch.setattr(core_config, "get_backups_dir", lambda: str(backup_dir), raising=False)

    old_file = backup_dir / "old_backup.zip"
    old_file.write_text("x", encoding="utf-8")
    old_mtime = now - (40 * 24 * 3600)
    os.utime(old_file, (old_mtime, old_mtime))

    for i in range(6):
        p = backup_dir / f"weekly_backup_{i}.zip"
        p.write_text("w", encoding="utf-8")
        os.utime(p, (now - i, now - i))
    for i in range(12):
        p = backup_dir / f"auto_backup_{i}.zip"
        p.write_text("a", encoding="utf-8")
        os.utime(p, (now - 100 - i, now - 100 - i))

    warnings = []
    monkeypatch.setattr(auto_cleanup.logger, "warning", lambda msg: warnings.append(msg))

    real_remove = auto_cleanup.os.remove

    def patched_remove(path):
        name = Path(path).name
        if name in {"weekly_backup_5.zip", "auto_backup_11.zip"}:
            raise PermissionError("locked")
        return real_remove(path)

    monkeypatch.setattr(auto_cleanup.os, "remove", patched_remove)

    assert auto_cleanup.cleanup_old_backup_files() is True
    assert any("Failed to remove old weekly backup" in msg for msg in warnings)
    assert any("Failed to remove old backup" in msg for msg in warnings)


@pytest.mark.unit
def test_cleanup_old_backup_files_outer_exception_returns_false(monkeypatch):
    monkeypatch.setattr(
        core_config,
        "get_backups_dir",
        lambda: (_ for _ in ()).throw(RuntimeError("no backup dir")),
        raising=False,
    )
    assert auto_cleanup.cleanup_old_backup_files() is False


@pytest.mark.unit
def test_cleanup_old_request_files_removes_old_and_logs_summary(monkeypatch, tmp_path):
    requests_dir = tmp_path / "requests"
    requests_dir.mkdir(parents=True, exist_ok=True)
    old_file = requests_dir / "old.req"
    old_file.write_text("old", encoding="utf-8")
    now = 2_100_000_000
    os.utime(old_file, (now - (8 * 24 * 3600), now - (8 * 24 * 3600)))

    infos = []
    monkeypatch.setattr(auto_cleanup.logger, "info", lambda msg: infos.append(msg))
    monkeypatch.setattr(core_config, "BASE_DATA_DIR", str(tmp_path), raising=False)
    monkeypatch.setattr(auto_cleanup.time, "time", lambda: now)

    assert auto_cleanup.cleanup_old_request_files() is True
    assert not old_file.exists()
    assert any("Request cleanup: removed" in msg for msg in infos)


@pytest.mark.unit
def test_cleanup_old_request_files_outer_exception_returns_false(monkeypatch, tmp_path):
    requests_dir = tmp_path / "requests"
    requests_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(core_config, "BASE_DATA_DIR", str(tmp_path), raising=False)
    monkeypatch.setattr(Path, "iterdir", lambda self: (_ for _ in ()).throw(RuntimeError("bad iterdir")))
    assert auto_cleanup.cleanup_old_request_files() is False


@pytest.mark.unit
def test_cleanup_old_message_archives_success_and_outer_exception(monkeypatch, tmp_path):
    base_dir = tmp_path / "data"
    archives = base_dir / "users" / "u1" / "messages" / "archives"
    archives.mkdir(parents=True, exist_ok=True)
    old_archive = archives / "sent_messages_archive_1.json"
    old_archive.write_text("{}", encoding="utf-8")
    now = 2_100_000_000
    old_mtime = now - (100 * 24 * 3600)
    os.utime(old_archive, (old_mtime, old_mtime))

    infos = []
    monkeypatch.setattr(auto_cleanup.logger, "info", lambda msg: infos.append(msg))
    monkeypatch.setattr(core_config, "BASE_DATA_DIR", str(base_dir), raising=False)
    monkeypatch.setattr(auto_cleanup.time, "time", lambda: now)
    monkeypatch.setattr("core.user_data_handlers.get_all_user_ids", lambda: ["u1"])

    assert auto_cleanup.cleanup_old_message_archives() is True
    assert any("Archive cleanup: removed" in msg for msg in infos)

    monkeypatch.setattr(
        "core.user_data_handlers.get_all_user_ids",
        lambda: (_ for _ in ()).throw(RuntimeError("ids fail")),
    )
    assert auto_cleanup.cleanup_old_message_archives() is False


@pytest.mark.unit
def test_cleanup_data_directory_exception_paths(monkeypatch):
    warnings = []
    monkeypatch.setattr(auto_cleanup.logger, "warning", lambda msg: warnings.append(msg))
    monkeypatch.setattr(auto_cleanup.logger, "debug", lambda _msg: None)
    monkeypatch.setattr(
        auto_cleanup,
        "cleanup_old_backup_files",
        lambda: (_ for _ in ()).throw(RuntimeError("backup-fail")),
    )
    monkeypatch.setattr(
        auto_cleanup,
        "cleanup_old_request_files",
        lambda: (_ for _ in ()).throw(RuntimeError("request-fail")),
    )
    monkeypatch.setattr(
        auto_cleanup,
        "cleanup_old_message_archives",
        lambda: (_ for _ in ()).throw(RuntimeError("archive-fail")),
    )

    assert auto_cleanup.cleanup_data_directory() is False
    assert any("Backup cleanup failed" in msg for msg in warnings)
    assert any("Request cleanup failed" in msg for msg in warnings)
    assert any("Archive cleanup failed" in msg for msg in warnings)


@pytest.mark.unit
def test_cleanup_data_directory_success_logs_info(monkeypatch):
    infos = []
    monkeypatch.setattr(auto_cleanup.logger, "info", lambda msg: infos.append(msg))
    monkeypatch.setattr(auto_cleanup, "cleanup_old_backup_files", lambda: True)
    monkeypatch.setattr(auto_cleanup, "cleanup_old_request_files", lambda: False)
    monkeypatch.setattr(auto_cleanup, "cleanup_old_message_archives", lambda: False)
    assert auto_cleanup.cleanup_data_directory() is True
    assert any("Data directory cleanup completed" in msg for msg in infos)


@pytest.mark.unit
def test_auto_cleanup_if_needed_noncritical_step_exceptions(monkeypatch):
    warnings = []
    monkeypatch.setattr(auto_cleanup.logger, "warning", lambda msg: warnings.append(msg))
    monkeypatch.setattr(auto_cleanup, "should_run_cleanup", lambda _i: True)
    monkeypatch.setattr(auto_cleanup, "perform_cleanup", lambda _r: True)
    monkeypatch.setattr(
        auto_cleanup,
        "archive_old_messages_for_all_users",
        lambda: (_ for _ in ()).throw(RuntimeError("archive-step-fail")),
    )
    monkeypatch.setattr(
        auto_cleanup,
        "cleanup_old_backup_files",
        lambda: (_ for _ in ()).throw(RuntimeError("backup-step-fail")),
    )
    monkeypatch.setattr(
        auto_cleanup,
        "cleanup_old_request_files",
        lambda: (_ for _ in ()).throw(RuntimeError("request-step-fail")),
    )
    monkeypatch.setattr(
        auto_cleanup,
        "cleanup_old_message_archives",
        lambda: (_ for _ in ()).throw(RuntimeError("message-archive-step-fail")),
    )

    called = {"updated": False}
    monkeypatch.setattr(
        auto_cleanup, "update_cleanup_timestamp", lambda: called.__setitem__("updated", True)
    )

    assert auto_cleanup.auto_cleanup_if_needed(".") is True
    assert called["updated"] is True
    assert any("Message archiving failed during cleanup" in msg for msg in warnings)
    assert any("Backup cleanup failed during auto cleanup" in msg for msg in warnings)
    assert any("Request cleanup failed during auto cleanup" in msg for msg in warnings)
    assert any("Archive cleanup failed during auto cleanup" in msg for msg in warnings)


@pytest.mark.unit
def test_auto_cleanup_if_needed_when_cleanup_fails(monkeypatch):
    errors = []
    monkeypatch.setattr(auto_cleanup.logger, "error", lambda msg: errors.append(msg))
    monkeypatch.setattr(auto_cleanup, "should_run_cleanup", lambda _i: True)
    monkeypatch.setattr(auto_cleanup, "perform_cleanup", lambda _r: False)
    assert auto_cleanup.auto_cleanup_if_needed(".") is False
    assert any("Cleanup failed" in msg for msg in errors)


@pytest.mark.unit
def test_archive_old_messages_for_all_users_no_users(monkeypatch):
    monkeypatch.setattr("core.user_data_handlers.get_all_user_ids", lambda: [])
    assert auto_cleanup.archive_old_messages_for_all_users() is True


@pytest.mark.unit
def test_archive_old_messages_for_all_users_mixed_results(monkeypatch):
    logs = {"debug": [], "warning": []}
    monkeypatch.setattr(auto_cleanup.logger, "debug", lambda msg: logs["debug"].append(msg))
    monkeypatch.setattr(auto_cleanup.logger, "warning", lambda msg: logs["warning"].append(msg))
    monkeypatch.setattr("core.user_data_handlers.get_all_user_ids", lambda: ["u1", "u2", "u3"])

    def fake_archive(user_id, days_to_keep=365):
        if user_id == "u1":
            return True
        if user_id == "u2":
            return False
        raise RuntimeError("fail-u3")

    monkeypatch.setattr("core.message_management.archive_old_messages", fake_archive)

    assert auto_cleanup.archive_old_messages_for_all_users() is True
    assert any("No messages to archive for user u2" in msg for msg in logs["debug"])
    assert any("Failed to archive messages for user u3" in msg for msg in logs["warning"])


@pytest.mark.unit
def test_archive_old_messages_for_all_users_outer_exception(monkeypatch):
    monkeypatch.setattr(
        "core.user_data_handlers.get_all_user_ids",
        lambda: (_ for _ in ()).throw(RuntimeError("id fail")),
    )
    assert auto_cleanup.archive_old_messages_for_all_users() is False


@pytest.mark.unit
def test_cleanup_status_helpers_handle_none_now(monkeypatch):
    monkeypatch.setattr(auto_cleanup, "now_datetime_full", lambda: None)
    days_since, last_date = auto_cleanup._get_cleanup_status__calculate_days_since_cleanup(
        1_700_000_000
    )
    assert days_since == 0
    assert isinstance(last_date, auto_cleanup.datetime)

    rendered = auto_cleanup._get_cleanup_status__format_next_cleanup_date(last_date)
    assert isinstance(rendered, str)
    assert rendered != "Unknown"


@pytest.mark.unit
def test_cleanup_tests_data_directory_fallback_resolution_and_cleanup(monkeypatch, tmp_path):
    fake_project = tmp_path / "fake_project" / "core"
    fake_project.mkdir(parents=True, exist_ok=True)
    fake_auto_cleanup_file = fake_project / "auto_cleanup.py"
    fake_auto_cleanup_file.write_text("# fake", encoding="utf-8")

    tests_data = tmp_path / "tests" / "data"
    tests_data.mkdir(parents=True, exist_ok=True)
    (tests_data / "tmp_coverage_gap").mkdir(parents=True, exist_ok=True)
    (tests_data / "pytest-of-gap").mkdir(parents=True, exist_ok=True)
    (tests_data / "test_gap.json").write_text("{}", encoding="utf-8")
    (tests_data / ".last_cache_cleanup").write_text("{}", encoding="utf-8")

    monkeypatch.setattr(auto_cleanup, "__file__", str(fake_auto_cleanup_file))
    monkeypatch.setattr(core_config, "BASE_DATA_DIR", str(tests_data), raising=False)

    assert auto_cleanup.cleanup_tests_data_directory() is True
    assert not (tests_data / "tmp_coverage_gap").exists()
    assert not (tests_data / "pytest-of-gap").exists()
    assert not (tests_data / "test_gap.json").exists()
    assert not (tests_data / ".last_cache_cleanup").exists()


@pytest.mark.unit
def test_cleanup_tests_data_directory_additional_fallback_paths(monkeypatch, tmp_path):
    fake_project = tmp_path / "project" / "core"
    fake_project.mkdir(parents=True, exist_ok=True)
    fake_auto_cleanup_file = fake_project / "auto_cleanup.py"
    fake_auto_cleanup_file.write_text("# fake", encoding="utf-8")
    monkeypatch.setattr(auto_cleanup, "__file__", str(fake_auto_cleanup_file))

    base_data_dir = tmp_path / "work" / "data"
    base_data_dir.mkdir(parents=True, exist_ok=True)
    fallback_tests_data = tmp_path / "tests" / "data"
    fallback_tests_data.mkdir(parents=True, exist_ok=True)
    (fallback_tests_data / "tmp_cleanup_branch").mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(core_config, "BASE_DATA_DIR", str(base_data_dir), raising=False)
    assert auto_cleanup.cleanup_tests_data_directory() is True
    assert not (fallback_tests_data / "tmp_cleanup_branch").exists()

    # When no tests/data can be resolved, function should return True early.
    monkeypatch.setattr(core_config, "BASE_DATA_DIR", "", raising=False)
    assert auto_cleanup.cleanup_tests_data_directory() is True
