"""Manual-checklist leftover tests for schedules and reminders."""

from __future__ import annotations

import uuid
from unittest.mock import MagicMock, patch

import pytest

from communication.reminders.reminder_dispatcher import TaskReminderDispatcher
from core.schedule_runtime import (
    clear_schedule_periods_cache,
    get_schedule_time_periods,
    set_schedule_periods,
)
from core.time_utilities import now_datetime_full
from scheduler.manager import SchedulerManager
from scheduler.task_reminders import handle_task_reminder
from storage.user_data_validation import validate_schedule_periods
from tasks import create_task, get_task_by_id, update_task
from tests.test_helpers.test_utilities import TestUserFactory


def _user(prefix: str, test_data_dir: str, **kwargs) -> str:
    internal = f"{prefix}_{uuid.uuid4().hex[:8]}"
    assert TestUserFactory.create_basic_user(
        internal, test_data_dir=test_data_dir, **kwargs
    )
    resolved = TestUserFactory.get_test_user_id_by_internal_username(
        internal, test_data_dir
    )
    assert resolved, f"Could not resolve created user {internal}"
    return resolved


def _morning_afternoon() -> dict:
    return {
        "Morning": {
            "start_time": "08:00",
            "end_time": "12:00",
            "active": True,
            "days": ["ALL"],
        },
        "Afternoon": {
            "start_time": "11:00",
            "end_time": "15:00",
            "active": True,
            "days": ["ALL"],
        },
    }


@pytest.mark.behavior
@pytest.mark.scheduler
def test_validate_schedule_periods_allows_overlapping_ranges():
    is_valid, errors = validate_schedule_periods(_morning_afternoon(), "messages")
    assert is_valid is True
    assert errors == []


@pytest.mark.behavior
@pytest.mark.scheduler
@pytest.mark.file_io
def test_schedule_edits_persist_across_cache_clear_and_reload(test_data_dir):
    user_id = _user("sched_persist", test_data_dir)
    category = "motivational"
    assert set_schedule_periods(user_id, category, _morning_afternoon()) is True

    edited = {
        "Morning": {
            "start_time": "07:30",
            "end_time": "11:30",
            "active": True,
            "days": ["ALL"],
        }
    }
    assert set_schedule_periods(user_id, category, edited) is True
    clear_schedule_periods_cache(user_id, category)

    reloaded = {
        name: data
        for name, data in get_schedule_time_periods(user_id, category).items()
        if name != "ALL"
    }
    assert reloaded["Morning"]["start_time"] == "07:30"
    assert reloaded["Morning"]["end_time"] == "11:30"
    assert "Afternoon" not in reloaded


@pytest.mark.behavior
@pytest.mark.scheduler
@pytest.mark.file_io
def test_delete_schedule_period_with_message_refs_does_not_crash(test_data_dir):
    user_id = _user("sched_delete", test_data_dir, enable_tasks=True)
    category = "motivational"
    assert set_schedule_periods(user_id, category, _morning_afternoon()) is True
    task_id = create_task(user_id, title="Tied to morning")
    assert task_id

    morning_only_removed = {
        "Afternoon": {
            "start_time": "11:00",
            "end_time": "15:00",
            "active": True,
            "days": ["ALL"],
        }
    }
    assert set_schedule_periods(user_id, category, morning_only_removed) is True
    clear_schedule_periods_cache()

    scheduler = MagicMock()
    scheduler.cleanup_old_tasks = MagicMock()
    scheduler.schedule_message_for_period = MagicMock()
    scheduler.delivery = MagicMock()
    scheduler.delivery.handle_message_sending = MagicMock(
        return_value=MagicMock(status="sent")
    )
    scheduler._remove_user_message_job = MagicMock()

    SchedulerManager.schedule_daily_message_job(scheduler, user_id, category)
    SchedulerManager.handle_sending_scheduled_message(
        scheduler, user_id, category, retry_attempts=1, retry_delay=0
    )

    remaining = get_schedule_time_periods(user_id, category)
    assert "Morning" not in remaining or remaining.get("Morning") is None
    assert get_task_by_id(user_id, task_id) is not None


@pytest.mark.behavior
@pytest.mark.scheduler
def test_scheduled_message_not_scheduled_for_wrong_day():
    today_name = now_datetime_full().strftime("%A")
    other_day = "Sunday" if today_name != "Sunday" else "Monday"
    scheduler = MagicMock()
    scheduler.cleanup_old_tasks = MagicMock()
    scheduler.schedule_message_for_period = MagicMock()

    with patch(
        "scheduler.manager.get_schedule_time_periods",
        return_value={
            "Morning": {
                "active": True,
                "days": [other_day],
                "start_time": "08:00",
                "end_time": "12:00",
            }
        },
    ):
        SchedulerManager.schedule_daily_message_job(scheduler, "user-1", "motivational")

    scheduler.schedule_message_for_period.assert_not_called()


@pytest.mark.behavior
@pytest.mark.scheduler
@pytest.mark.file_io
def test_task_reminder_update_text_used_on_next_send(test_data_dir):
    user_id = _user("remind_update", test_data_dir, enable_tasks=True)
    task_id = create_task(user_id, title="Old title")
    assert task_id
    assert update_task(user_id, task_id, {"title": "Updated grocery run"}) is True

    task = get_task_by_id(user_id, task_id)
    assert task is not None
    message = TaskReminderDispatcher(MagicMock()).create_task_reminder_message(task)
    assert "Updated grocery run" in message
    assert "Old title" not in message

    manager = MagicMock()
    handle_task_reminder(manager, user_id, task_id, retry_attempts=1, retry_delay=0)
    manager.delivery.handle_task_reminder.assert_called_once_with(user_id, task_id)


@pytest.mark.behavior
@pytest.mark.scheduler
def test_task_reminder_already_sent_is_not_delivered_again():
    manager = MagicMock()
    task = {"id": "t1", "status": "active", "reminder_sent": True}
    with (
        patch("tasks.get_task_by_id", return_value=task),
        patch("scheduler.task_reminders.runtime_task_is_completed", return_value=False),
        patch("tasks.update_task") as update_task_mock,
    ):
        handle_task_reminder(manager, "u1", "t1", retry_attempts=1, retry_delay=0)

    manager.delivery.handle_task_reminder.assert_not_called()
    update_task_mock.assert_not_called()


@pytest.mark.behavior
@pytest.mark.scheduler
@pytest.mark.file_io
def test_task_reminder_sent_flag_persists_and_blocks_duplicate(test_data_dir):
    user_id = _user("remind_dup", test_data_dir, enable_tasks=True)
    task_id = create_task(user_id, title="One reminder only")
    assert task_id

    manager = MagicMock()
    handle_task_reminder(manager, user_id, task_id, retry_attempts=1, retry_delay=0)
    manager.delivery.handle_task_reminder.assert_called_once_with(user_id, task_id)

    reloaded = get_task_by_id(user_id, task_id)
    assert reloaded is not None
    assert reloaded.get("reminder_sent") is True

    handle_task_reminder(manager, user_id, task_id, retry_attempts=1, retry_delay=0)
    assert manager.delivery.handle_task_reminder.call_count == 1
