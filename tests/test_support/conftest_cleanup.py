"""
Pytest plugin: session cleanup fixtures (prune test artifacts, clear test user factory cache).

Implementation lives in tests.test_support.conftest_cleanup_impl; this module provides
the fixtures that call into it. Root conftest loads this via pytest_plugins.
"""

import os
import glob
import shutil
import pytest
from pathlib import Path

from tests.conftest import project_root
from tests.test_support.conftest_cleanup_impl import (
    _cleanup_test_log_files,
    _prune_old_files,
    _is_transient_test_data_dir_name,
    _apply_versioned_retention_protocol,
    _cleanup_pytest_cache_temp_dirs,
    _cleanup_session_test_data_artifacts,
    _apply_flaky_run_group_retention,
    _snapshot_worker_logs_with_retention,
)
import contextlib


@pytest.fixture(scope="session", autouse=True)
def clear_test_user_factory_cache():
    """Clear test user factory cache at the end of the test session."""
    yield
    try:
        from tests.test_utilities import TestUserFactory

        TestUserFactory.clear_cache()
    except Exception:
        pass


@pytest.fixture(scope="session", autouse=True)
def prune_test_artifacts_before_and_after_session():
    """Prune old logs (tests/logs) and backups (tests/data/backups) before and after the session.

    Defaults: logs older than 14 days, test backups older than 7 days.
    Override via TEST_LOG_RETENTION_DAYS and TEST_BACKUP_RETENTION_DAYS env vars.
    """
    if os.environ.get("PYTEST_XDIST_WORKER"):
        yield
        return

    project_root_path = Path(project_root)
    logs_dir = project_root_path / "tests" / "logs"
    logs_archive_dir = logs_dir / "archive"
    logs_backups_dir = logs_dir / "backups"
    flaky_runs_dir = logs_dir / "flaky_detector_runs"
    flaky_runs_backups_dir = logs_backups_dir / "flaky_detector_runs"
    flaky_runs_archive_dir = logs_archive_dir / "flaky_detector_runs"
    worker_logs_dir = logs_dir / "worker_logs_backup"
    worker_logs_backups_dir = logs_backups_dir / "worker_logs_backup"
    worker_logs_archive_dir = logs_archive_dir / "worker_logs_backup"
    test_backups_dir = project_root_path / "tests" / "data" / "backups"
    data_dir = project_root_path / "tests" / "data"

    log_retention_days = int(os.getenv("TEST_LOG_RETENTION_DAYS", "14"))
    backup_retention_days = int(os.getenv("TEST_BACKUP_RETENTION_DAYS", "7"))
    profile_keep_versions = int(os.getenv("TEST_PROFILE_KEEP_VERSIONS", "7"))
    test_archive_retention_days = int(os.getenv("TEST_LOG_ARCHIVE_RETENTION_DAYS", "30"))

    _cleanup_session_test_data_artifacts(data_dir)

    if logs_dir.exists():
        _prune_old_files(
            logs_dir,
            patterns=["*.log", "*.log.*", "*.gz"],
            older_than_days=log_retention_days,
        )
        _apply_versioned_retention_protocol(
            logs_dir,
            logs_backups_dir,
            logs_archive_dir,
            pattern="parallel_profile_*.log",
            keep_backups=profile_keep_versions,
            archive_retention_days=test_archive_retention_days,
        )
        _apply_versioned_retention_protocol(
            logs_dir,
            logs_backups_dir,
            logs_archive_dir,
            pattern="parallel_profile_*.xml",
            keep_backups=profile_keep_versions,
            archive_retention_days=test_archive_retention_days,
        )
        _apply_versioned_retention_protocol(
            logs_dir,
            logs_backups_dir,
            logs_archive_dir,
            pattern="pytest_console_output_*.txt",
            keep_backups=7,
            archive_retention_days=test_archive_retention_days,
            current_file_name="pytest_console_output.txt",
        )
        _apply_versioned_retention_protocol(
            logs_dir,
            logs_backups_dir,
            logs_archive_dir,
            pattern="flaky_test_report_*.md",
            keep_backups=7,
            archive_retention_days=test_archive_retention_days,
            current_file_name="flaky_test_report.md",
        )
        _apply_versioned_retention_protocol(
            logs_dir,
            logs_backups_dir,
            logs_archive_dir,
            pattern="flaky_test_report_timeout_smoke_*.md",
            keep_backups=7,
            archive_retention_days=test_archive_retention_days,
            current_file_name="flaky_test_report_timeout_smoke.md",
        )
        _apply_flaky_run_group_retention(
            flaky_runs_dir,
            flaky_runs_backups_dir,
            flaky_runs_archive_dir,
            keep_backups=7,
            archive_retention_days=test_archive_retention_days,
        )

    if test_backups_dir.exists():
        _prune_old_files(
            test_backups_dir,
            patterns=["*.zip"],
            older_than_days=backup_retention_days,
        )

    _cleanup_test_log_files(project_root)
    _cleanup_pytest_cache_temp_dirs(project_root_path, data_dir)

    try:
        conversation_states_file = data_dir / "conversation_states.json"
        if conversation_states_file.exists():
            with contextlib.suppress(Exception):
                conversation_states_file.unlink(missing_ok=True)

        pytest_pattern = str(data_dir / "pytest-of-*")
        pytest_dirs = glob.glob(pytest_pattern)
        for stray in pytest_dirs:
            stray_path = Path(stray)
            if stray_path.exists():
                shutil.rmtree(stray_path, ignore_errors=True)

        for item in data_dir.iterdir():
            try:
                if item.is_dir():
                    if _is_transient_test_data_dir_name(item.name):
                        shutil.rmtree(item, ignore_errors=True)
                elif item.is_file() and item.name == ".last_cache_cleanup":
                    item.unlink(missing_ok=True)
            except Exception:
                pass

        test_json_patterns = [
            "test_",
            ".tmp_",
            "welcome_tracking",
            "conversation_states",
        ]
        for item in data_dir.iterdir():
            try:
                if item.is_file() and item.suffix == ".json" and any(
                    item.name.startswith(pattern) for pattern in test_json_patterns
                ):
                    item.unlink(missing_ok=True)
            except Exception:
                pass

        tmp_dir = data_dir / "tmp"
        if tmp_dir.exists():
            for child in tmp_dir.iterdir():
                if child.name == "pytest_runner":
                    continue
                if child.is_dir() or child.is_file():
                    try:
                        if child.is_dir():
                            shutil.rmtree(child, ignore_errors=True)
                        else:
                            child.unlink(missing_ok=True)
                    except Exception:
                        pass
    except Exception:
        pass

    yield

    _cleanup_session_test_data_artifacts(data_dir)

    if logs_dir.exists():
        _prune_old_files(
            logs_dir,
            patterns=["*.log", "*.log.*", "*.gz"],
            older_than_days=log_retention_days,
        )
        _apply_versioned_retention_protocol(
            logs_dir,
            logs_backups_dir,
            logs_archive_dir,
            pattern="parallel_profile_*.log",
            keep_backups=profile_keep_versions,
            archive_retention_days=test_archive_retention_days,
        )
        _apply_versioned_retention_protocol(
            logs_dir,
            logs_backups_dir,
            logs_archive_dir,
            pattern="parallel_profile_*.xml",
            keep_backups=profile_keep_versions,
            archive_retention_days=test_archive_retention_days,
        )
        _apply_versioned_retention_protocol(
            logs_dir,
            logs_backups_dir,
            logs_archive_dir,
            pattern="pytest_console_output_*.txt",
            keep_backups=7,
            archive_retention_days=test_archive_retention_days,
            current_file_name="pytest_console_output.txt",
        )
        _apply_versioned_retention_protocol(
            logs_dir,
            logs_backups_dir,
            logs_archive_dir,
            pattern="flaky_test_report_*.md",
            keep_backups=7,
            archive_retention_days=test_archive_retention_days,
            current_file_name="flaky_test_report.md",
        )
        _apply_versioned_retention_protocol(
            logs_dir,
            logs_backups_dir,
            logs_archive_dir,
            pattern="flaky_test_report_timeout_smoke_*.md",
            keep_backups=7,
            archive_retention_days=test_archive_retention_days,
            current_file_name="flaky_test_report_timeout_smoke.md",
        )
        _apply_flaky_run_group_retention(
            flaky_runs_dir,
            flaky_runs_backups_dir,
            flaky_runs_archive_dir,
            keep_backups=7,
            archive_retention_days=test_archive_retention_days,
        )
        _snapshot_worker_logs_with_retention(
            worker_logs_dir,
            worker_logs_backups_dir,
            worker_logs_archive_dir,
            keep_backups=7,
            archive_retention_days=test_archive_retention_days,
        )

    if test_backups_dir.exists():
        _prune_old_files(
            test_backups_dir,
            patterns=["*.zip"],
            older_than_days=backup_retention_days,
        )

    _cleanup_pytest_cache_temp_dirs(project_root_path, data_dir)

    try:
        data_dir = project_root_path / "tests" / "data"
        if data_dir.exists():
            for item in data_dir.iterdir():
                try:
                    if item.is_dir():
                        if _is_transient_test_data_dir_name(item.name):
                            shutil.rmtree(item, ignore_errors=True)
                    elif item.is_file():
                        if item.suffix == ".json":
                            test_json_patterns = [
                                "test_",
                                ".tmp_",
                                "welcome_tracking",
                                "conversation_states",
                            ]
                            if any(
                                item.name.startswith(pattern)
                                for pattern in test_json_patterns
                            ):
                                item.unlink(missing_ok=True)
                        elif item.name == ".last_cache_cleanup":
                            item.unlink(missing_ok=True)
                except Exception:
                    pass

        flags_dir = data_dir / "flags"
        if flags_dir.exists():
            for child in flags_dir.iterdir():
                try:
                    if child.is_dir():
                        shutil.rmtree(child, ignore_errors=True)
                    else:
                        child.unlink(missing_ok=True)
                except Exception:
                    pass

        tmp_dir = data_dir / "tmp"
        if tmp_dir.exists():
            for child in tmp_dir.iterdir():
                if child.name == "pytest_runner":
                    continue
                try:
                    if child.is_dir():
                        shutil.rmtree(child, ignore_errors=True)
                    else:
                        child.unlink(missing_ok=True)
                except Exception:
                    pass

        requests_dir = data_dir / "requests"
        if requests_dir.exists():
            for child in requests_dir.iterdir():
                try:
                    if child.is_dir():
                        shutil.rmtree(child, ignore_errors=True)
                    else:
                        child.unlink(missing_ok=True)
                except Exception:
                    pass

        conversation_states_file = data_dir / "conversation_states.json"
        if conversation_states_file.exists():
            with contextlib.suppress(Exception):
                conversation_states_file.unlink(missing_ok=True)
    except Exception:
        pass
