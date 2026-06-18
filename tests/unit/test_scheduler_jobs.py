"""Unit coverage for scheduler/jobs.py daily job registration."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from scheduler.jobs import register_full_daily_maintenance_jobs, register_system_daily_jobs


@pytest.mark.unit
@pytest.mark.scheduler
def test_register_system_daily_jobs_schedules_log_archival_and_full_daily_run():
    manager = MagicMock()
    mock_at = MagicMock()
    mock_day = MagicMock()
    mock_every = MagicMock()
    mock_every.day = mock_day
    mock_day.at.return_value = mock_at

    with patch("scheduler.jobs.schedule") as schedule_module:
        schedule_module.every.return_value = mock_every
        register_system_daily_jobs(manager)

    at_calls = [call.args[0] for call in mock_day.at.call_args_list]
    do_calls = [call.args[0] for call in mock_at.do.call_args_list]

    assert at_calls == ["02:00", "01:00"]
    assert do_calls == [
        manager.perform_daily_log_archival,
        manager.run_full_daily_scheduler,
    ]


@pytest.mark.unit
@pytest.mark.scheduler
def test_register_full_daily_maintenance_jobs_includes_orphan_cleanup_and_data_cleanup():
    manager = MagicMock()
    mock_at = MagicMock()
    mock_day = MagicMock()
    mock_every = MagicMock()
    mock_every.day = mock_day
    mock_day.at.return_value = mock_at

    cleanup_data = MagicMock()
    cleanup_tests = MagicMock()

    with (
        patch("scheduler.jobs.register_system_daily_jobs") as register_system,
        patch("scheduler.jobs.schedule") as schedule_module,
        patch("core.auto_cleanup.cleanup_data_directory", cleanup_data),
        patch("core.auto_cleanup.cleanup_tests_data_directory", cleanup_tests),
    ):
        schedule_module.every.return_value = mock_every
        register_full_daily_maintenance_jobs(manager)

    register_system.assert_called_once_with(manager)

    at_calls = [call.args[0] for call in mock_day.at.call_args_list]
    do_targets = [call.args[0] for call in mock_at.do.call_args_list]

    assert "03:00" in at_calls
    assert manager.cleanup_orphaned_task_reminders in do_targets
    assert "04:00" in at_calls
    assert "04:05" in at_calls
    assert cleanup_data in do_targets
    assert cleanup_tests in do_targets


@pytest.mark.unit
@pytest.mark.scheduler
def test_register_full_daily_maintenance_jobs_handles_cleanup_import_failure(
    monkeypatch: pytest.MonkeyPatch,
):
    manager = MagicMock()
    mock_at = MagicMock()
    mock_day = MagicMock()
    mock_every = MagicMock()
    mock_every.day = mock_day
    mock_day.at.return_value = mock_at

    import builtins

    real_import = builtins.__import__

    def _block_auto_cleanup_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "core.auto_cleanup":
            raise ImportError("simulated missing auto_cleanup")
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", _block_auto_cleanup_import)

    with (
        patch("scheduler.jobs.register_system_daily_jobs"),
        patch("scheduler.jobs.schedule") as schedule_module,
    ):
        schedule_module.every.return_value = mock_every
        register_full_daily_maintenance_jobs(manager)

    do_targets = [call.args[0] for call in mock_at.do.call_args_list]
    assert manager.cleanup_orphaned_task_reminders in do_targets
    assert "04:00" not in [call.args[0] for call in mock_day.at.call_args_list]
