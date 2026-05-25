"""Unit tests for one-time task reminder scheduling."""

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
class TestScheduleTaskReminderAtDatetime:
    def test_skips_past_reminder(self, mock_scheduler_manager, active_task, monkeypatch):
        fixed_now = datetime(2026, 1, 20, 12, 0, 0)
        regina = pytz.timezone("America/Regina")
        aware_now = regina.localize(fixed_now)
        past_reminder = regina.localize(datetime(2026, 1, 20, 10, 0, 0))

        monkeypatch.setattr("tasks.get_task_by_id", lambda uid, tid: active_task)
        monkeypatch.setattr(tr, "resolve_user_timezone_str", lambda uid: "America/Regina")
        monkeypatch.setattr(tr, "localized_now_for_user", lambda uid: aware_now)
        monkeypatch.setattr(
            tr,
            "load_and_localize_datetime",
            lambda value, tz: past_reminder if value == "2026-01-20 10:00" else None,
        )

        with patch.object(tr.schedule, "every") as mock_every:
            result = tr.schedule_task_reminder_at_datetime(
                mock_scheduler_manager,
                "user-1",
                "task-1",
                "2026-01-20",
                "10:00",
            )

        assert result is False
        mock_every.assert_not_called()

    def test_schedules_future_reminder(
        self, mock_scheduler_manager, active_task, monkeypatch
    ):
        fixed_now = datetime(2026, 1, 20, 12, 0, 0)
        regina = pytz.timezone("America/Regina")
        aware_now = regina.localize(fixed_now)
        future_reminder = regina.localize(datetime(2026, 1, 20, 14, 0, 0))

        monkeypatch.setattr("tasks.get_task_by_id", lambda uid, tid: active_task)
        monkeypatch.setattr(tr, "resolve_user_timezone_str", lambda uid: "America/Regina")
        monkeypatch.setattr(tr, "localized_now_for_user", lambda uid: aware_now)
        monkeypatch.setattr(
            tr,
            "load_and_localize_datetime",
            lambda value, tz: future_reminder if value == "2026-01-20 14:00" else None,
        )

        mock_job = MagicMock()
        with patch.object(tr.schedule, "every") as mock_every:
            mock_every.return_value.seconds.do.return_value = mock_job

            result = tr.schedule_task_reminder_at_datetime(
                mock_scheduler_manager,
                "user-1",
                "task-1",
                "2026-01-20",
                "14:00",
            )

        assert result is True
        mock_every.assert_called_once()
        # 2 hours = 7200 seconds
        mock_every.assert_called_with(7200)
        mock_scheduler_manager.handle_task_reminder.assert_not_called()

    def test_skips_completed_task(self, mock_scheduler_manager, monkeypatch):
        completed = {"id": "task-1", "completion": {"completed": True}}
        monkeypatch.setattr("tasks.get_task_by_id", lambda uid, tid: completed)

        with patch.object(tr.schedule, "every") as mock_every:
            result = tr.schedule_task_reminder_at_datetime(
                mock_scheduler_manager,
                "user-1",
                "task-1",
                "2026-01-20",
                "14:00",
            )

        assert result is False
        mock_every.assert_not_called()
