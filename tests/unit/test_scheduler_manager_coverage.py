"""Unit tests targeting uncovered scheduler.manager and task_reminders paths."""

from __future__ import annotations

from datetime import datetime, timedelta
from unittest.mock import Mock, patch

import pytest

from communication.core.message_send_result import MessageSendResult
from scheduler import task_reminders as tr
from scheduler.manager import (
    SchedulerManager,
    clear_all_accumulated_jobs_standalone,
    process_user_schedules,
    set_scheduler_delivery_factory,
)
from core.time_utilities import now_datetime_full


@pytest.fixture
def delivery():
    mock = Mock()
    mock.handle_message_sending = Mock(
        return_value=MessageSendResult.sent("user-1", "motivational")
    )
    mock.handle_task_reminder = Mock(return_value=True)
    return mock


@pytest.fixture
def scheduler_manager(delivery):
    return SchedulerManager(delivery)


@pytest.mark.unit
@pytest.mark.scheduler
class TestResetAndRescheduleDailyMessages:
    def test_returns_early_when_no_active_user(self, scheduler_manager):
        with patch("scheduler.manager.UserContext") as mock_ctx:
            mock_ctx.return_value.get_user_id.return_value = None
            scheduler_manager.reset_and_reschedule_daily_messages("motivational")

    def test_reschedules_task_reminders_when_tasks_enabled(self, scheduler_manager):
        user_id = "user-1"
        with (
            patch("scheduler.manager.schedule") as mock_schedule,
            patch("scheduler.manager.get_user_data") as mock_get_data,
            patch.object(
                scheduler_manager, "schedule_all_task_reminders"
            ) as mock_task_schedule,
        ):
            mock_schedule.jobs = []
            mock_get_data.return_value = {
                "account": {"features": {"task_management": "enabled"}}
            }
            scheduler_manager.reset_and_reschedule_daily_messages("tasks", user_id)
            mock_task_schedule.assert_called_once_with(user_id)

    def test_skips_task_reminders_when_tasks_disabled(self, scheduler_manager):
        user_id = "user-1"
        with (
            patch("scheduler.manager.schedule") as mock_schedule,
            patch("scheduler.manager.get_user_data") as mock_get_data,
            patch.object(
                scheduler_manager, "schedule_all_task_reminders"
            ) as mock_task_schedule,
        ):
            mock_schedule.jobs = []
            mock_get_data.return_value = {
                "account": {"features": {"task_management": "disabled"}}
            }
            scheduler_manager.reset_and_reschedule_daily_messages("tasks", user_id)
            mock_task_schedule.assert_not_called()

    def test_reschedules_checkin_category(self, scheduler_manager):
        user_id = "user-1"
        with (
            patch("scheduler.manager.schedule") as mock_schedule,
            patch.object(
                scheduler_manager, "schedule_daily_message_job"
            ) as mock_daily,
        ):
            mock_schedule.jobs = []
            scheduler_manager.reset_and_reschedule_daily_messages("checkin", user_id)
            mock_daily.assert_called_once_with(user_id=user_id, category="checkin")

    def test_reschedules_message_category(self, scheduler_manager):
        user_id = "user-1"
        with (
            patch("scheduler.manager.schedule") as mock_schedule,
            patch(
                "scheduler.manager._automated_category_allowed", return_value=True
            ),
            patch.object(
                scheduler_manager, "schedule_daily_message_job"
            ) as mock_daily,
        ):
            mock_schedule.jobs = []
            scheduler_manager.reset_and_reschedule_daily_messages(
                "motivational", user_id
            )
            mock_daily.assert_called_once_with(
                user_id=user_id, category="motivational"
            )

    def test_disabled_message_category_is_cleared_without_rescheduling(
        self, scheduler_manager
    ):
        user_id = "user-1"
        with (
            patch("scheduler.manager.schedule") as mock_schedule,
            patch(
                "scheduler.manager._automated_category_allowed", return_value=False
            ),
            patch.object(
                scheduler_manager, "schedule_daily_message_job"
            ) as mock_daily,
        ):
            mock_schedule.jobs = []
            scheduler_manager.reset_and_reschedule_daily_messages(
                "motivational", user_id
            )
            mock_daily.assert_not_called()


@pytest.mark.unit
@pytest.mark.scheduler
class TestSchedulerManagerUncoveredPaths:
    def test_is_job_for_category_scans_schedule_when_job_none(
        self, scheduler_manager
    ):
        matching_job = Mock()
        matching_job.job_func = Mock()
        matching_job.job_func.func = scheduler_manager.schedule_daily_message_job
        matching_job.job_func.keywords = {
            "user_id": "user-1",
            "category": "motivational",
        }

        with patch("scheduler.manager.schedule") as mock_schedule:
            mock_schedule.jobs = [matching_job]
            assert (
                scheduler_manager.is_job_for_category(
                    None, "user-1", "motivational"
                )
                is True
            )

    def test_schedule_message_at_random_time_success(self, scheduler_manager):
        user_id = "user-1"
        category = "motivational"
        future = now_datetime_full() + timedelta(hours=2)

        with (
            patch(
                "scheduler.manager.get_schedule_time_periods",
                return_value={"morning": {"active": True}},
            ),
            patch.object(
                scheduler_manager,
                "get_random_time_within_period",
                return_value="2026-06-20 10:30",
            ),
            patch(
                "scheduler.manager.load_and_localize_datetime",
                return_value=future,
            ),
            patch(
                "scheduler.manager.localized_now_for_user",
                return_value=now_datetime_full(),
            ),
            patch.object(scheduler_manager, "is_time_conflict", return_value=False),
            patch.object(scheduler_manager, "set_wake_timer") as mock_wake,
            patch("scheduler.manager.schedule.every") as mock_every,
        ):
            mock_every.return_value.day.at.return_value.do.return_value = None
            scheduler_manager.schedule_message_at_random_time(user_id, category)
            mock_wake.assert_called_once()

    def test_schedule_message_at_random_time_no_periods(self, scheduler_manager):
        with patch(
            "scheduler.manager.get_schedule_time_periods", return_value=None
        ):
            scheduler_manager.schedule_message_at_random_time("user-1", "motivational")

    def test_schedule_message_for_period_success_path(self, scheduler_manager):
        user_id = "user-1"
        future = now_datetime_full() + timedelta(hours=3)

        with (
            patch.object(
                scheduler_manager,
                "get_random_time_within_period",
                return_value="2026-06-20 10:30",
            ),
            patch(
                "scheduler.manager.resolve_user_timezone_str",
                return_value="America/Regina",
            ),
            patch(
                "scheduler.manager.load_and_localize_datetime",
                return_value=future,
            ),
            patch(
                "scheduler.manager.localized_now_for_user",
                return_value=now_datetime_full(),
            ),
            patch.object(scheduler_manager, "is_time_conflict", return_value=False),
            patch.object(scheduler_manager, "set_wake_timer") as mock_wake,
            patch("scheduler.manager.schedule.every") as mock_every,
        ):
            mock_every.return_value.day.at.return_value.do.return_value = None
            scheduler_manager.schedule_message_for_period(
                user_id, "motivational", "morning"
            )
            mock_wake.assert_called_once()

    def test_handle_sending_scheduled_message_skipped_removes_job(
        self, scheduler_manager
    ):
        scheduler_manager.delivery.handle_message_sending.return_value = (
            MessageSendResult.skipped("user-1", "motivational")
        )
        with (
            patch(
                "scheduler.manager._automated_category_allowed", return_value=True
            ),
            patch.object(
                scheduler_manager, "_remove_user_message_job"
            ) as mock_remove,
        ):
            scheduler_manager.handle_sending_scheduled_message(
                "user-1", "motivational"
            )
            mock_remove.assert_called_once_with("user-1", "motivational")

    def test_remove_user_message_job_matches_keyword_jobs(self, scheduler_manager):
        """Keyword message jobs are removed, and their clock time still counts as a conflict."""
        from scheduler.manager import schedule

        schedule.clear()
        try:
            schedule.every().day.at("10:15").do(
                scheduler_manager.handle_sending_scheduled_message,
                user_id="user-1",
                category="motivational",
            )
            schedule.every().day.at("11:15").do(
                scheduler_manager.handle_sending_scheduled_message,
                user_id="user-1",
                category="checkin",
            )
            schedule.every().day.at("12:15").do(
                scheduler_manager.handle_sending_scheduled_message,
                "user-2",
                "health",
            )
            keyword_job = schedule.jobs[0].job_func
            assert keyword_job is not None
            assert keyword_job.args == ()
            assert keyword_job.keywords["category"] == "motivational"

            scheduler_manager._remove_user_message_job("user-1", "motivational")
            remaining = []
            for job in schedule.jobs:
                job_func = job.job_func
                assert job_func is not None
                keywords = job_func.keywords
                if keywords.get("user_id") is not None:
                    remaining.append((keywords.get("user_id"), keywords.get("category")))
                else:
                    remaining.append((job_func.args[0], job_func.args[1]))
            assert remaining == [("user-1", "checkin"), ("user-2", "health")]

            checkin_run = schedule.jobs[0].next_run
            assert scheduler_manager.is_time_conflict("user-1", checkin_run) is True
            assert scheduler_manager.is_time_conflict("someone-else", checkin_run) is False

            scheduler_manager._remove_user_message_job("user-2", "health")
            assert len(schedule.jobs) == 1
            checkin_job = schedule.jobs[0].job_func
            assert checkin_job is not None
            assert checkin_job.keywords["category"] == "checkin"
        finally:
            schedule.clear()

    def test_handle_sending_scheduled_message_failed_retries_then_removes_job(
        self, scheduler_manager
    ):
        failed = MessageSendResult.failed(
            "user-1", "checkin", message_id="<checkin@example.com>"
        )
        scheduler_manager.delivery.handle_message_sending.side_effect = [
            failed,
            failed,
        ]
        with (
            patch.object(scheduler_manager, "_remove_user_message_job") as mock_remove,
            patch("scheduler.manager.time.sleep") as sleep,
        ):
            scheduler_manager.handle_sending_scheduled_message(
                "user-1",
                "checkin",
                retry_attempts=2,
                retry_delay=5,
            )
        assert scheduler_manager.delivery.handle_message_sending.call_count == 2
        second = scheduler_manager.delivery.handle_message_sending.call_args_list[1]
        assert second.kwargs["message_id"] == "<checkin@example.com>"
        sleep.assert_called_once_with(5)
        mock_remove.assert_called_once_with("user-1", "checkin")

    def test_run_full_daily_scheduler(self, scheduler_manager):
        with (
            patch.object(
                scheduler_manager, "check_and_perform_weekly_backup"
            ) as mock_backup,
            patch.object(
                scheduler_manager, "clear_all_accumulated_jobs"
            ) as mock_clear,
            patch.object(
                scheduler_manager, "schedule_all_users_immediately"
            ) as mock_schedule_users,
            patch(
                "scheduler.manager.scheduler_jobs.register_full_daily_maintenance_jobs"
            ) as mock_register,
            patch("scheduler.manager.schedule") as mock_schedule,
        ):
            mock_schedule.jobs = []
            scheduler_manager.run_full_daily_scheduler()
            mock_backup.assert_called_once()
            mock_clear.assert_called_once()
            mock_schedule_users.assert_called_once()
            mock_register.assert_called_once_with(scheduler_manager)

    def test_stop_scheduler_logs_timeout_when_thread_stays_alive(
        self, scheduler_manager
    ):
        mock_thread = Mock()
        mock_thread.is_alive.return_value = True
        scheduler_manager.scheduler_thread = mock_thread
        scheduler_manager.stop_scheduler()
        assert scheduler_manager.scheduler_thread is None

    def test_schedule_daily_message_job_skips_period_not_for_today(
        self, scheduler_manager
    ):
        today_name = now_datetime_full().strftime("%A")
        other_day = "Sunday" if today_name != "Sunday" else "Monday"
        with (
            patch(
                "scheduler.manager.get_schedule_time_periods",
                return_value={
                    "evening": {
                        "active": True,
                        "days": [other_day],
                        "start_time": "18:00",
                        "end_time": "20:00",
                    }
                },
            ),
            patch(
                "scheduler.manager._automated_category_allowed", return_value=True
            ),
            patch.object(scheduler_manager, "cleanup_old_tasks"),
            patch.object(
                scheduler_manager, "schedule_message_for_period"
            ) as mock_period,
        ):
            scheduler_manager.schedule_daily_message_job("user-1", "motivational")
            mock_period.assert_not_called()

    def test_set_wake_timer_skips_in_test_mode(self, scheduler_manager, monkeypatch):
        monkeypatch.setenv("MHM_TESTING", "1")
        with patch("scheduler.manager.subprocess.run") as mock_run:
            scheduler_manager.set_wake_timer(
                now_datetime_full() + timedelta(hours=1),
                "user-1",
                "motivational",
                "morning",
            )
            mock_run.assert_not_called()

    def test_get_active_job_count_returns_schedule_job_length(self, scheduler_manager):
        with patch("scheduler.manager.schedule") as mock_schedule:
            mock_schedule.jobs = [object(), object(), object()]
            assert scheduler_manager.get_active_job_count() == 3


@pytest.mark.unit
@pytest.mark.scheduler
class TestStandaloneSchedulerHelpers:
    def test_clear_all_accumulated_jobs_standalone_success(self):
        mock_delivery = Mock()
        mock_manager = Mock()
        with (
            patch(
                "scheduler.manager._create_standalone_scheduler_manager",
                return_value=mock_manager,
            ),
            patch(
                "scheduler.manager.set_scheduler_delivery_factory"
            ),
        ):
            set_scheduler_delivery_factory(lambda: mock_delivery)
            try:
                assert clear_all_accumulated_jobs_standalone() is True
                mock_manager.clear_all_accumulated_jobs.assert_called_once()
            finally:
                set_scheduler_delivery_factory(None)

    def test_process_user_schedules_no_categories(self):
        with patch(
            "scheduler.manager.get_user_data",
            return_value={"preferences": {}},
        ):
            process_user_schedules("user-1")


@pytest.mark.unit
@pytest.mark.scheduler
class TestTaskRemindersModuleCoverage:
    def test_schedule_all_task_reminders_skips_inactive_period(
        self, scheduler_manager
    ):
        user_id = "user-1"
        with (
            patch("tasks.are_tasks_enabled", return_value=True),
            patch(
                "core.schedule_runtime.get_schedule_time_periods",
                return_value={
                    "morning": {"active": False, "start_time": "08:00", "end_time": "10:00"}
                },
            ),
            patch("tasks.load_active_tasks", return_value=[{"id": "t1", "title": "Task"}]),
            patch.object(
                scheduler_manager, "schedule_task_reminder_at_time"
            ) as mock_schedule,
        ):
            tr.schedule_all_task_reminders(scheduler_manager, user_id)
            mock_schedule.assert_not_called()

    def test_schedule_all_task_reminders_skips_task_without_id(
        self, scheduler_manager
    ):
        user_id = "user-1"
        with (
            patch("tasks.are_tasks_enabled", return_value=True),
            patch(
                "core.schedule_runtime.get_schedule_time_periods",
                return_value={
                    "morning": {
                        "active": True,
                        "start_time": "08:00",
                        "end_time": "10:00",
                    }
                },
            ),
            patch(
                "tasks.load_active_tasks",
                return_value=[{"title": "No id task"}],
            ),
            patch.object(
                scheduler_manager,
                "select_task_for_reminder",
                return_value={"title": "No id task"},
            ),
            patch.object(
                scheduler_manager,
                "get_random_time_within_task_period",
                return_value="09:00",
            ),
            patch.object(
                scheduler_manager, "schedule_task_reminder_at_time"
            ) as mock_schedule,
        ):
            tr.schedule_all_task_reminders(scheduler_manager, user_id)
            mock_schedule.assert_not_called()

    def test_handle_task_reminder_retries_on_delivery_error(self, scheduler_manager):
        scheduler_manager.delivery.handle_task_reminder.side_effect = [
            RuntimeError("network"),
            MessageSendResult.sent("user-1", "task_reminders"),
        ]
        with (
            patch(
                "tasks.get_task_by_id",
                return_value={"id": "t1", "completion": {"completed": False}},
            ),
            patch("tasks.update_task") as mock_update,
            patch("scheduler.task_reminders.time.sleep"),
        ):
            tr.handle_task_reminder(
                scheduler_manager, "user-1", "t1", retry_attempts=2, retry_delay=0
            )
            assert scheduler_manager.delivery.handle_task_reminder.call_count == 2
            mock_update.assert_called_once()

    def test_select_task_by_weight_prunes_stale_selection_state(
        self, scheduler_manager
    ):
        scheduler_manager._reminder_selection_state = {"stale-key": 1.0}
        tasks = [
            {"id": "t1", "priority": "high"},
            {"id": "t2", "priority": "low"},
        ]
        weights = [(tasks[0], 2.0), (tasks[1], 1.0)]
        with patch("scheduler.task_reminders.random.uniform", return_value=1.0):
            selected = tr.select_task_by_weight(scheduler_manager, weights, tasks)
        assert selected is not None
        assert "stale-key" not in scheduler_manager._reminder_selection_state


def _period(start_time, end_time):
    return {"start_time": start_time, "end_time": end_time, "active": True}


@pytest.mark.unit
@pytest.mark.scheduler
class TestRemainingWindowAndPeriodJobs:
    def _random_time(self, scheduler_manager, now, periods, period_name):
        with (
            patch("scheduler.manager.now_datetime_full", return_value=now),
            patch(
                "scheduler.manager.get_schedule_time_periods",
                return_value=periods,
            ),
            patch("scheduler.manager.random.randint", return_value=0),
        ):
            return scheduler_manager.get_random_time_within_period(
                "user-1",
                "motivational",
                period_name,
                "America/Regina",
            )

    def test_upcoming_period_stays_today(self, scheduler_manager):
        result = self._random_time(
            scheduler_manager,
            datetime(2026, 10, 6, 19, 19, 0),
            {"TestMotivation": _period("19:22", "19:25")},
            "TestMotivation",
        )
        assert result == "2026-10-06 19:22"

    def test_open_period_uses_the_remaining_window(self, scheduler_manager):
        result = self._random_time(
            scheduler_manager,
            datetime(2026, 10, 6, 19, 23, 40),
            {"evening": _period("19:00", "23:00")},
            "evening",
        )
        assert result == "2026-10-06 19:24"

    def test_ended_period_moves_to_tomorrow(self, scheduler_manager):
        result = self._random_time(
            scheduler_manager,
            datetime(2026, 10, 6, 19, 30, 0),
            {"TestMotivation": _period("19:22", "19:25")},
            "TestMotivation",
        )
        assert result == "2026-10-07 19:22"

    def test_sending_one_period_leaves_the_other_period(self, scheduler_manager):
        from scheduler.manager import schedule

        schedule.clear()
        try:
            schedule.every().day.at("10:15").do(
                scheduler_manager.handle_sending_scheduled_message,
                user_id="user-1",
                category="motivational",
                period_name="morning",
            )
            schedule.every().day.at("21:16").do(
                scheduler_manager.handle_sending_scheduled_message,
                user_id="user-1",
                category="motivational",
                period_name="evening",
            )
            with patch(
                "scheduler.manager._automated_category_allowed", return_value=True
            ):
                scheduler_manager.handle_sending_scheduled_message(
                    "user-1", "motivational", period_name="morning"
                )
            remaining = [
                job.job_func.keywords.get("period_name")
                for job in schedule.jobs
                if job.job_func is not None
            ]
            assert remaining == ["evening"]
        finally:
            schedule.clear()

    def test_category_cleanup_removes_every_period_job(self, scheduler_manager):
        from scheduler.manager import schedule

        schedule.clear()
        try:
            schedule.every().day.at("10:15").do(
                scheduler_manager.handle_sending_scheduled_message,
                user_id="user-1",
                category="motivational",
                period_name="morning",
            )
            schedule.every().day.at("21:16").do(
                scheduler_manager.handle_sending_scheduled_message,
                user_id="user-1",
                category="checkin",
                period_name="checkin_time",
            )
            scheduler_manager.cleanup_old_tasks("user-1", "motivational")
            remaining = [
                job.job_func.keywords.get("category")
                for job in schedule.jobs
                if job.job_func is not None
            ]
            assert remaining == ["checkin"]
        finally:
            schedule.clear()
