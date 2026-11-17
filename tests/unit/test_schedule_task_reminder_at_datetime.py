"""Unit tests for one-time task reminder scheduling."""

from __future__ import annotations

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
import pytz
import schedule

from communication.core.message_send_result import MessageSendResult
from scheduler import task_reminders as tr
from tasks import task_reminder_delivery


class DeliveryProcessStopped(BaseException):
    """Simulate process exit without running the delivery result handler."""


@pytest.mark.unit
@pytest.mark.scheduler
@pytest.mark.parametrize("first_outcome", ["crash", "sent", "failed"])
def test_recovered_reminder_retries_only_explicit_failure(
    tmp_path, monkeypatch, first_outcome
):
    monkeypatch.setattr(task_reminder_delivery, "get_user_subdir_path", lambda *args: tmp_path)
    monkeypatch.setattr(tr, "has_service_access", lambda account: True)
    monkeypatch.setattr("core.get_user_data", lambda *args: {"account": {}})
    task = {"id": "task-1", "reminder_snooze_until": "2000-01-01 12:00:00"}
    monkeypatch.setattr("tasks.get_task_by_id", lambda *args: task)
    manager = MagicMock()
    settle = MagicMock(side_effect=DeliveryProcessStopped)
    monkeypatch.setattr(tr, "settle_task_reminder", settle)
    deliver = manager.delivery.handle_task_reminder
    failure = MessageSendResult.failed(message_id="<retry@example.com>")
    success = MessageSendResult.sent("user-1", "task_reminders")
    if first_outcome == "crash":
        deliver.side_effect = DeliveryProcessStopped
    else:
        deliver.return_value = failure if first_outcome == "failed" else success

    if first_outcome == "failed":
        tr.handle_task_reminder(manager, "user-1", "task-1", retry_attempts=1)
    else:
        with pytest.raises(DeliveryProcessStopped):
            tr.handle_task_reminder(manager, "user-1", "task-1", retry_attempts=1)

    monkeypatch.setattr(task_reminder_delivery, "_PROCESS_ID", "restarted-process")
    settle.side_effect = None
    settle.reset_mock()
    deliver.side_effect = None
    deliver.return_value = success
    deliver.reset_mock()
    tr.handle_task_reminder(manager, "user-1", "task-1", retry_attempts=1)

    if first_outcome == "failed":
        deliver.assert_called_once_with("user-1", "task-1", message_id="<retry@example.com>")
    else:
        deliver.assert_not_called()
    settle.assert_called_once()
    stored = task_reminder_delivery.record_reminder_attempt(
        "user-1", "task-1", "deferred", task["reminder_snooze_until"]
    )
    assert stored["status"] == ("unconfirmed" if first_outcome == "crash" else "sent")


@pytest.fixture
def mock_scheduler_manager():
    return MagicMock()


@pytest.fixture
def active_task():
    return {"id": "task-1", "title": "Test", "completion": {"completed": False}}


@pytest.mark.unit
@pytest.mark.scheduler
class TestScheduleTaskReminderAtDatetime:
    @pytest.mark.parametrize("delivery_fails", [False, True])
    def test_one_time_job_preserves_seconds_and_removes_itself(
        self, mock_scheduler_manager, active_task, monkeypatch, delivery_fails
    ):
        local_scheduler = schedule.Scheduler()
        now = pytz.timezone("America/Regina").localize(
            datetime(2026, 10, 22, 10, 0, 0, 500000)
        )
        monkeypatch.setattr("tasks.get_task_by_id", lambda *args: active_task)
        monkeypatch.setattr(tr, "resolve_user_timezone_str", lambda uid: "America/Regina")
        monkeypatch.setattr(tr, "localized_now_for_user", lambda uid: now)
        monkeypatch.setattr(tr.schedule, "every", local_scheduler.every)
        if delivery_fails:
            mock_scheduler_manager.handle_task_reminder.side_effect = RuntimeError("delivery failed")

        assert tr.schedule_task_reminder_at_datetime(
            mock_scheduler_manager, "user-1", "task-1", "2026-10-22", "11:00:30"
        )
        assert local_scheduler.jobs[0].interval == 3630
        local_scheduler.jobs[0].next_run = datetime.min
        local_scheduler.run_pending()
        local_scheduler.run_pending()
        assert local_scheduler.jobs == []
        mock_scheduler_manager.handle_task_reminder.assert_called_once_with(
            user_id="user-1", task_identifier="task-1"
        )

    def test_cleanup_removes_one_time_jobs(self, mock_scheduler_manager, active_task, monkeypatch):
        local_scheduler = schedule.Scheduler()
        local_scheduler.every(30).seconds.do(
            tr._run_one_time_task_reminder,
            scheduler_manager=mock_scheduler_manager, user_id="user-1", task_identifier="task-1",
        )
        monkeypatch.setattr(tr.schedule, "jobs", local_scheduler.jobs)
        assert tr.cleanup_task_reminders(mock_scheduler_manager, "user-1", "task-1")
        assert local_scheduler.jobs == []

    def test_orphan_cleanup_removes_one_time_jobs(self, mock_scheduler_manager, monkeypatch):
        local_scheduler = schedule.Scheduler()
        local_scheduler.every(30).seconds.do(
            tr._run_one_time_task_reminder,
            scheduler_manager=mock_scheduler_manager, user_id="user-1", task_identifier="task-1",
        )
        monkeypatch.setattr(tr.schedule, "jobs", local_scheduler.jobs)
        monkeypatch.setattr("core.get_all_user_ids", lambda: ["user-1"])
        monkeypatch.setattr("tasks.get_task_by_id", lambda *args: None)
        tr.cleanup_orphaned_task_reminders(mock_scheduler_manager)
        assert local_scheduler.jobs == []

    def test_restart_preserves_snooze_seconds(self, mock_scheduler_manager, monkeypatch):
        monkeypatch.setattr("tasks.load_active_tasks", lambda uid: [{
            "id": "task-1", "status": "active",
            "reminder_snooze_until": "2026-10-22 11:00:30",
        }])
        tr.reschedule_snoozed_task_reminders(mock_scheduler_manager, "user-1")
        mock_scheduler_manager.schedule_task_reminder_at_datetime.assert_called_once_with(
            "user-1", "task-1", "2026-10-22", "11:00:30"
        )

    @pytest.mark.parametrize("superseded", [False, True])
    def test_recovery_restores_one_overdue_job_without_changing_saved_time(
        self, mock_scheduler_manager, active_task, monkeypatch, superseded
    ):
        local_scheduler = schedule.Scheduler()
        now = pytz.timezone("America/Regina").localize(datetime(2026, 10, 22, 12))
        saved_time = "2026-10-22 11:00:30"
        active_task["reminder_snooze_until"] = saved_time
        monkeypatch.setattr("tasks.load_active_tasks", lambda uid: [active_task])
        monkeypatch.setattr("tasks.get_task_by_id", lambda *args: active_task)
        monkeypatch.setattr("tasks.are_tasks_enabled", lambda uid: True)
        monkeypatch.setattr("core.get_all_user_ids", lambda: ["user-1"])
        monkeypatch.setattr("core.get_user_data", lambda *args: {"account": {}})
        monkeypatch.setattr(tr, "has_service_access", lambda account: True)
        monkeypatch.setattr(tr, "resolve_user_timezone_str", lambda uid: "America/Regina")
        monkeypatch.setattr(tr, "localized_now_for_user", lambda uid: now)
        monkeypatch.setattr(tr.schedule, "every", local_scheduler.every)
        monkeypatch.setattr(tr.schedule, "get_jobs", local_scheduler.get_jobs)
        mock_scheduler_manager.schedule_task_reminder_at_datetime.side_effect = (
            lambda *args: tr.schedule_task_reminder_at_datetime(mock_scheduler_manager, *args)
        )

        tr.recover_deferred_task_reminders(mock_scheduler_manager)
        tr.recover_deferred_task_reminders(mock_scheduler_manager)

        assert active_task["reminder_snooze_until"] == saved_time
        job, = local_scheduler.jobs
        assert job.interval == 1
        if superseded:
            active_task["reminder_snooze_until"] = "2026-10-22 14:00:00"
        job.next_run = datetime.min
        local_scheduler.run_pending()

        assert not local_scheduler.jobs
        if superseded:
            mock_scheduler_manager.handle_task_reminder.assert_not_called()
        else:
            mock_scheduler_manager.handle_task_reminder.assert_called_once_with(
                user_id="user-1", task_identifier="task-1"
            )

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
