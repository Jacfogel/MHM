"""Saved deferrals and delivery claims survive scheduler process replacement."""

from datetime import datetime, timedelta
from unittest.mock import MagicMock

import pytest
import pytz
import schedule

from communication.core.message_send_result import MessageSendResult
from core.time_utilities import DATE_ONLY, format_timestamp, parse_timestamp_full
from scheduler import task_reminders as reminders
from tasks import create_task, get_task_by_id
from tasks import task_reminder_delivery, task_reminder_snooze
from tasks.task_data_handlers import runtime_task_due_date, runtime_task_is_completed
from tasks.task_occurrence_skip import skip_task_occurrence
from tests.test_helpers.test_utilities import TestUserFactory

pytestmark = [pytest.mark.integration, pytest.mark.tasks, pytest.mark.scheduler, pytest.mark.file_io]


class ProcessExited(BaseException):
    """Stop before normal cleanup, as an abruptly terminated process would."""


@pytest.mark.parametrize("action", ["snooze", "one_off_skip", "recurring_skip"])
@pytest.mark.parametrize("outcome", ["crash", "sent", "unconfirmed", "exception", "failed"])
def test_saved_deferral_recovery_does_not_replay_uncertain_delivery(
    test_data_dir, monkeypatch, action, outcome
):
    """Only an explicit failure permits another send after a process replacement."""
    label = f"restart_{action}_{outcome}"
    assert TestUserFactory.create_basic_user(
        label, enable_tasks=True, test_data_dir=test_data_dir
    )
    user_id = TestUserFactory.get_test_user_id_by_label(label, test_data_dir)
    assert user_id
    anchor = datetime(2026, 11, 20, 10, 0, 30)
    clock = [anchor]
    monkeypatch.setattr(task_reminder_snooze, "now_datetime_full", lambda: clock[0])
    monkeypatch.setattr(reminders, "user_local_now_naive", lambda _uid: clock[0])
    monkeypatch.setattr("scheduler.user_timezone.user_local_now_naive", lambda _uid: clock[0])
    monkeypatch.setattr(
        reminders, "localized_now_for_user",
        lambda _uid: pytz.timezone("America/Regina").localize(clock[0]),
    )
    monkeypatch.setattr(reminders, "resolve_user_timezone_str", lambda _uid: "America/Regina")
    monkeypatch.setattr("core.get_all_user_ids", lambda: [user_id])
    monkeypatch.setattr("scheduler.runtime_access.get_scheduler_manager", lambda: None)
    task_id = create_task(
        user_id, title="Isolated restart reminder", due_date="2026-11-20",
        due_time="09:00", recurrence_pattern="daily" if action == "recurring_skip" else None,
    )
    assert task_id
    if action == "snooze":
        result = task_reminder_snooze.snooze_task_reminder(
            user_id, task_id, "1_hour", now_dt=anchor
        )
    else:
        result = skip_task_occurrence(user_id, task_id, now_dt=anchor)
    if action == "snooze":
        assert result.until  # The snooze was saved while the scheduler was unavailable.
        assert not result.success
    else:
        assert result.success
    saved = get_task_by_id(user_id, task_id)
    assert saved
    saved_until = saved["reminder_snooze_until"]
    due_date = runtime_task_due_date(saved)
    assert due_date == ("2026-11-21" if action == "recurring_skip" else "2026-11-20")
    due = parse_timestamp_full(saved_until)
    assert due

    def manager_for(local_scheduler):
        """Bind production callbacks to a fresh, isolated in-memory scheduler."""
        manager = MagicMock()
        manager.schedule_task_reminder_at_datetime.side_effect = (
            lambda *args: reminders.schedule_task_reminder_at_datetime(manager, *args)
        )
        manager.handle_task_reminder.side_effect = (
            lambda **kwargs: reminders.handle_task_reminder(manager, **kwargs, retry_attempts=1)
        )
        monkeypatch.setattr(reminders.schedule, "every", local_scheduler.every)
        monkeypatch.setattr(reminders.schedule, "get_jobs", local_scheduler.get_jobs)
        return manager

    first_scheduler = schedule.Scheduler()
    first_manager = manager_for(first_scheduler)
    reminders.recover_deferred_task_reminders(first_manager)
    reminders.recover_deferred_task_reminders(first_manager)
    job, = first_scheduler.jobs
    assert job.interval == int((due - anchor).total_seconds())
    assert get_task_by_id(user_id, task_id)["reminder_snooze_until"] == saved_until
    clock[0] = due + timedelta(seconds=1)
    delivery = first_manager.delivery.handle_task_reminder
    settlement = reminders.settle_task_reminder
    if outcome == "crash":
        delivery.side_effect = ProcessExited
    elif outcome == "exception":
        delivery.side_effect = RuntimeError("channel outcome unknown")
    else:
        delivery.return_value = MessageSendResult(
            status=outcome, user_id=user_id, category="task_reminders",
            message_id="<restart-test@example.com>",
        )
    # Preserve the saved deferral even if the channel outcome was already recorded.
    monkeypatch.setattr(reminders, "settle_task_reminder", MagicMock(side_effect=ProcessExited))
    job.next_run = datetime.min
    if outcome == "failed":
        first_scheduler.run_pending()
    else:
        with pytest.raises(ProcessExited):
            first_scheduler.run_pending()
    delivery.assert_called_once()

    # Discard in-memory jobs and use a new process identity; persistence stays real.
    monkeypatch.setattr(task_reminder_delivery, "_PROCESS_ID", "replacement-process")
    monkeypatch.setattr(reminders, "settle_task_reminder", settlement)
    restarted_scheduler = schedule.Scheduler()
    restarted = manager_for(restarted_scheduler)
    restarted.delivery.handle_task_reminder.return_value = MessageSendResult.sent(
        user_id, "task_reminders"
    )
    reminders.recover_deferred_task_reminders(restarted)
    reminders.recover_deferred_task_reminders(restarted)
    recovered_job, = restarted_scheduler.jobs
    assert recovered_job.interval == 1  # Recover a reminder due during downtime.
    recovered_job.next_run = datetime.min
    restarted_scheduler.run_pending()
    if outcome == "failed":
        restarted.delivery.handle_task_reminder.assert_called_once_with(
            user_id, task_id, message_id="<restart-test@example.com>"
        )
    else:
        restarted.delivery.handle_task_reminder.assert_not_called()
    restored = get_task_by_id(user_id, task_id)
    assert restored
    assert not restored.get("reminder_snooze_until")
    assert restored["reminder_sent_on"] == format_timestamp(clock[0], DATE_ONLY)
    assert runtime_task_due_date(restored) == due_date
    assert not runtime_task_is_completed(restored)
    record = task_reminder_delivery.record_reminder_attempt(
        user_id, task_id, "deferred", saved_until
    )
    assert record
    assert record["status"] == (
        "unconfirmed" if outcome in {"crash", "unconfirmed", "exception"} else "sent"
    )
    assert not record.get("claimed")
    reminders.recover_deferred_task_reminders(restarted)
    assert not restarted_scheduler.jobs
