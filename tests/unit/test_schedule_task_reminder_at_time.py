"""Unit coverage for daily task reminder scheduling at HH:MM."""

from __future__ import annotations

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
import pytz

from scheduler import task_reminders as tr


@pytest.fixture
def mock_scheduler_manager():
    return MagicMock()


@pytest.fixture
def active_task():
    return {"id": "task-1", "title": "Test", "completion": {"completed": False}}


@pytest.mark.unit
@pytest.mark.scheduler
class TestScheduleTaskReminderAtTime:
    def test_returns_false_when_task_missing(self, mock_scheduler_manager, monkeypatch):
        monkeypatch.setattr("tasks.get_task_by_id", lambda uid, tid: None)

        assert (
            tr.schedule_task_reminder_at_time(
                mock_scheduler_manager, "user-1", "missing", "09:00"
            )
            is False
        )

    def test_returns_false_for_completed_task(
        self, mock_scheduler_manager, monkeypatch
    ):
        completed = {"id": "task-1", "completion": {"completed": True}}
        monkeypatch.setattr("tasks.get_task_by_id", lambda uid, tid: completed)

        with patch.object(tr.schedule, "every") as mock_every:
            result = tr.schedule_task_reminder_at_time(
                mock_scheduler_manager, "user-1", "task-1", "09:00"
            )

        assert result is False
        mock_every.assert_not_called()

    def test_returns_false_for_invalid_time_format(
        self, mock_scheduler_manager, active_task, monkeypatch
    ):
        monkeypatch.setattr("tasks.get_task_by_id", lambda uid, tid: active_task)

        with patch.object(tr.schedule, "every") as mock_every:
            result = tr.schedule_task_reminder_at_time(
                mock_scheduler_manager, "user-1", "task-1", "not-a-time"
            )

        assert result is False
        mock_every.assert_not_called()

    def test_schedules_daily_job_and_wake_timer(
        self, mock_scheduler_manager, active_task, monkeypatch
    ):
        fixed_now = datetime(2026, 5, 29, 8, 0, 0)
        regina = pytz.timezone("America/Regina")
        aware_now = regina.localize(fixed_now)

        monkeypatch.setattr("tasks.get_task_by_id", lambda uid, tid: active_task)
        monkeypatch.setattr(tr, "resolve_user_timezone_str", lambda uid: "America/Regina")
        monkeypatch.setattr(tr, "localized_now_for_user", lambda uid: aware_now)

        mock_at = MagicMock()
        mock_day = MagicMock()
        mock_day.at.return_value = mock_at

        with patch.object(tr.schedule, "every") as mock_every:
            mock_every.return_value.day = mock_day

            result = tr.schedule_task_reminder_at_time(
                mock_scheduler_manager, "user-1", "task-1", "9:30"
            )

        assert result is True
        mock_day.at.assert_called_once_with("09:30")
        mock_at.do.assert_called_once()
        mock_scheduler_manager.set_wake_timer.assert_called_once()
