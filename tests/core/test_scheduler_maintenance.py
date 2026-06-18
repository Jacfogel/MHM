"""Coverage for scheduler maintenance jobs without real OS or backup side effects."""

from __future__ import annotations

from datetime import timedelta
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from scheduler import maintenance as scheduler_maintenance
from core.time_format_constants import TIMESTAMP_FULL
from core.time_utilities import format_timestamp, now_datetime_full


@pytest.mark.unit
@pytest.mark.core
@pytest.mark.scheduler
def test_cleanup_scheduler_wake_tasks_deletes_matching_user_tasks(monkeypatch: pytest.MonkeyPatch):
    calls: list[list[str]] = []

    def _fake_run(args, **_kwargs):
        calls.append(list(args))
        if args[:2] == ["schtasks", "/query"]:
            return MagicMock(
                returncode=0,
                stdout=(
                    "TaskName: \\Microsoft\\Windows\\Wake_user-a_morning\n"
                    "TaskName: \\Microsoft\\Windows\\Other_Task\n"
                    "TaskName: \\Microsoft\\Windows\\Wake_other-user\n"
                ),
                stderr="",
            )
        return MagicMock(returncode=0, stdout="", stderr="")

    monkeypatch.setattr("core.get_all_user_ids", lambda: ["user-a"])
    monkeypatch.setattr("subprocess.run", _fake_run)

    scheduler_maintenance.cleanup_scheduler_wake_tasks()

    delete_calls = [args for args in calls if "/delete" in args]
    assert len(delete_calls) == 1
    assert "Wake_user-a_morning" in delete_calls[0][3]


@pytest.mark.unit
@pytest.mark.core
@pytest.mark.scheduler
def test_cleanup_scheduler_wake_tasks_logs_nonzero_delete_stderr(
    monkeypatch: pytest.MonkeyPatch,
):
    def _fake_run(args, **_kwargs):
        if args[:2] == ["schtasks", "/query"]:
            return MagicMock(
                returncode=0,
                stdout="TaskName: \\Wake_user-a\n",
                stderr="",
            )
        return MagicMock(returncode=1, stdout="", stderr="already gone")

    monkeypatch.setattr("core.get_all_user_ids", lambda: ["user-a"])
    monkeypatch.setattr("subprocess.run", _fake_run)
    scheduler_maintenance.cleanup_scheduler_wake_tasks()


@pytest.mark.unit
@pytest.mark.core
@pytest.mark.scheduler
def test_cleanup_scheduler_wake_tasks_handles_query_and_delete_failures(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr("core.get_all_user_ids", lambda: ["user-a"])
    monkeypatch.setattr(
        "subprocess.run",
        lambda *_a, **_k: MagicMock(returncode=1, stdout="", stderr="query failed"),
    )
    scheduler_maintenance.cleanup_scheduler_wake_tasks()

    def _delete_raises(args, **_kwargs):
        if args[:2] == ["schtasks", "/query"]:
            return MagicMock(
                returncode=0,
                stdout="TaskName: \\Wake_user-a\n",
                stderr="",
            )
        raise RuntimeError("delete failed")

    monkeypatch.setattr("subprocess.run", _delete_raises)
    scheduler_maintenance.cleanup_scheduler_wake_tasks()


@pytest.mark.unit
@pytest.mark.core
@pytest.mark.scheduler
def test_perform_daily_log_archival_success_and_failure(monkeypatch: pytest.MonkeyPatch):
    compressed = MagicMock(return_value=2)
    cleaned = MagicMock(return_value=3)
    monkeypatch.setattr("core.logger.compress_old_logs", compressed)
    monkeypatch.setattr("core.logger.cleanup_old_archives", cleaned)

    scheduler_maintenance.perform_daily_log_archival()

    compressed.assert_called_once()
    cleaned.assert_called_once()

    monkeypatch.setattr(
        "core.logger.compress_old_logs",
        MagicMock(side_effect=RuntimeError("compress failed")),
    )
    scheduler_maintenance.perform_daily_log_archival()


@pytest.mark.unit
@pytest.mark.core
@pytest.mark.scheduler
def test_check_weekly_backup_creates_when_none_and_reports_health(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    now = now_datetime_full()
    created_at = format_timestamp(now, TIMESTAMP_FULL)
    backup_path = tmp_path / "weekly.zip"
    manager = MagicMock()
    manager.list_backups.side_effect = [
        [],
        [
            {
                "backup_name": "weekly_backup_latest",
                "created_at": created_at,
                "file_size": 2 * 1024 * 1024,
            }
        ],
    ]
    manager.create_backup.return_value = backup_path
    monkeypatch.setattr(scheduler_maintenance, "backup_manager", manager)
    monkeypatch.setattr(scheduler_maintenance, "now_datetime_full", lambda: now)
    monkeypatch.setattr(scheduler_maintenance, "now_timestamp_filename", lambda: "2026")

    scheduler_maintenance.check_and_perform_weekly_backup()

    manager.create_backup.assert_called_once_with(
        backup_name="weekly_backup_2026",
        include_users=True,
        include_config=True,
        include_logs=False,
    )


@pytest.mark.unit
@pytest.mark.core
@pytest.mark.scheduler
@pytest.mark.parametrize(
    ("created_delta_days", "should_create"),
    [(3, False), (8, True)],
)
def test_check_weekly_backup_due_logic(
    monkeypatch: pytest.MonkeyPatch,
    created_delta_days: int,
    should_create: bool,
):
    now = now_datetime_full()
    manager = MagicMock()
    manager.list_backups.return_value = [
        {
            "file_name": "weekly_backup_old.zip",
            "created_at": format_timestamp(
                now - timedelta(days=created_delta_days), TIMESTAMP_FULL
            ),
            "file_size": 1,
        }
    ]
    manager.create_backup.return_value = "backup.zip"
    monkeypatch.setattr(scheduler_maintenance, "backup_manager", manager)
    monkeypatch.setattr(scheduler_maintenance, "now_datetime_full", lambda: now)
    monkeypatch.setattr(scheduler_maintenance, "now_timestamp_filename", lambda: "stamp")

    scheduler_maintenance.check_and_perform_weekly_backup()

    assert manager.create_backup.called is should_create


@pytest.mark.unit
@pytest.mark.core
@pytest.mark.scheduler
def test_check_weekly_backup_handles_invalid_timestamp_failed_create_and_list_error(
    monkeypatch: pytest.MonkeyPatch,
):
    manager = MagicMock()
    manager.list_backups.return_value = [
        {"backup_name": "weekly_backup_bad", "created_at": "not-a-time"}
    ]
    manager.create_backup.return_value = None
    monkeypatch.setattr(scheduler_maintenance, "backup_manager", manager)
    monkeypatch.setattr(scheduler_maintenance, "now_timestamp_filename", lambda: "stamp")

    scheduler_maintenance.check_and_perform_weekly_backup()
    manager.create_backup.assert_called_once()

    manager.list_backups.side_effect = RuntimeError("list failed")
    scheduler_maintenance.check_and_perform_weekly_backup()
