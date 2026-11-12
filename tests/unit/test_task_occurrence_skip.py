"""Unit tests for skipping one task occurrence."""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from tasks.task_data_handlers import runtime_task_due_date, runtime_task_is_completed
from tasks.task_occurrence_skip import skip_task_occurrence
from tests.test_helpers.test_utilities import TestUserFactory


@pytest.mark.unit
@pytest.mark.tasks
class TestSkipTaskOccurrence:
    @pytest.mark.parametrize("scheduler_outcome", ["scheduled", "rejected", "unavailable", "error"])
    def test_recurring_skip_advances_due_and_stays_active(self, test_data_dir, scheduler_outcome):
        user_id = "skip_recurring_due"
        assert TestUserFactory.create_basic_user(
            user_id, enable_tasks=True, test_data_dir=test_data_dir
        )
        from tasks import create_task, get_task_by_id, load_active_tasks, load_completed_tasks

        task_id = create_task(
            user_id,
            title="Take meds",
            due_date="2026-09-15",
            due_time="09:00",
            recurrence_pattern="daily",
        )
        scheduler = MagicMock()
        schedule = scheduler.schedule_task_reminder_at_datetime
        schedule.return_value = scheduler_outcome == "scheduled"
        if scheduler_outcome == "error":
            schedule.side_effect = RuntimeError("scheduler failed")
        with patch(
            "scheduler.runtime_access.get_scheduler_manager",
            return_value=None if scheduler_outcome == "unavailable" else scheduler,
        ):
            result = skip_task_occurrence(
                user_id, task_id, now_dt=datetime(2026, 9, 15, 10, 0, 0)
            )
        assert result.success is True
        assert result.recurring is True
        assert result.next_due == "2026-09-16"
        assert "Next one is due 2026-09-16" in result.message
        assert ("I could not schedule the next reminder" in result.message) == (
            scheduler_outcome != "scheduled"
        )
        if scheduler_outcome != "scheduled":
            assert "Set a separate reminder" in result.message
        task = get_task_by_id(user_id, task_id)
        assert runtime_task_due_date(task) == "2026-09-16"
        assert runtime_task_is_completed(task) is False
        assert any(_task_id(item) == task_id for item in load_active_tasks(user_id))
        assert not any(_task_id(item) == task_id for item in load_completed_tasks(user_id))
        assert "Skipped this time" in str(task.get("description") or "")
        assert [entry["action"] for entry in task["reminder_deferrals"]] == ["skip"]

    @pytest.mark.parametrize("reminder_scheduled", [True, False])
    def test_one_off_skip_keeps_due_until_tomorrow_morning(self, test_data_dir, reminder_scheduled):
        user_id = "skip_one_off_due"
        assert TestUserFactory.create_basic_user(
            user_id, enable_tasks=True, test_data_dir=test_data_dir
        )
        from tasks import create_task, get_task_by_id

        task_id = create_task(
            user_id, title="Call dentist", due_date="2026-09-20", due_time="14:00"
        )
        scheduler = MagicMock()
        scheduler.schedule_task_reminder_at_datetime.return_value = reminder_scheduled
        with patch(
            "scheduler.runtime_access.get_scheduler_manager", return_value=scheduler
        ):
            result = skip_task_occurrence(
                user_id, task_id, now_dt=datetime(2026, 9, 15, 10, 0, 0)
            )
        assert result.success is True
        assert result.recurring is False
        if not reminder_scheduled:
            assert "It is still due 2026-09-20." in result.message
            assert "I saved the snooze until 2026-09-16" in result.message
            assert "Set a separate reminder" in result.message
        task = get_task_by_id(user_id, task_id)
        assert runtime_task_due_date(task) == "2026-09-20"
        assert task.get("due", {}).get("time") == "14:00"
        assert runtime_task_is_completed(task) is False
        assert task.get("reminder_snooze_until", "").startswith("2026-09-16")
        assert [entry["action"] for entry in task["reminder_deferrals"]] == ["skip"]


def _task_id(task):
    return str(task.get("id") or "")
