"""Shared per-user scheduling used by all-users and new-user paths."""

from unittest.mock import Mock, patch

import pytest

from communication.core.message_send_result import MessageSendResult
from scheduler.manager import SchedulerManager


@pytest.fixture
def scheduler_manager():
    delivery = Mock()
    delivery.handle_message_sending = Mock(
        return_value=MessageSendResult.sent("user-1", "motivational")
    )
    return SchedulerManager(delivery)


@pytest.mark.unit
@pytest.mark.scheduler
class TestScheduleUserJobs:
    def test_schedules_categories_checkins_and_reminders(self, scheduler_manager):
        with (
            patch("scheduler.manager.get_user_data") as mock_get_data,
            patch("scheduler.manager.get_schedule_time_periods") as mock_periods,
            patch.object(scheduler_manager, "schedule_daily_message_job") as mock_daily,
            patch.object(
                scheduler_manager, "schedule_all_task_reminders"
            ) as mock_reminders,
        ):
            mock_get_data.side_effect = [
                {"preferences": {"categories": ["motivational", "health"]}},
                {"account": {"features": {"checkins": "enabled"}}},
            ]
            mock_periods.return_value = {"morning": {"active": True}}

            scheduled = scheduler_manager._schedule_user_jobs("user-1")

            assert scheduled == 3
            assert mock_daily.call_args_list == [
                (("user-1", "motivational"),),
                (("user-1", "health"),),
                (("user-1", "checkin"),),
            ]
            mock_reminders.assert_called_once_with("user-1")

    def test_warns_when_categories_is_not_a_list(self, scheduler_manager):
        with (
            patch("scheduler.manager.get_user_data") as mock_get_data,
            patch("scheduler.manager.get_schedule_time_periods") as mock_periods,
            patch.object(scheduler_manager, "schedule_daily_message_job") as mock_daily,
            patch.object(scheduler_manager, "schedule_all_task_reminders"),
            patch("scheduler.manager.logger") as mock_logger,
        ):
            mock_get_data.side_effect = [
                {"preferences": {"categories": "motivational"}},
                {"account": {"features": {"checkins": "disabled"}}},
            ]
            mock_periods.return_value = {}

            scheduled = scheduler_manager._schedule_user_jobs("user-1")

            assert scheduled == 0
            mock_daily.assert_not_called()
            mock_logger.warning.assert_called()
            assert "Expected list for categories" in mock_logger.warning.call_args[0][0]

    def test_all_users_and_new_user_share_schedule_user_jobs(self, scheduler_manager):
        with (
            patch("scheduler.manager.get_all_user_ids", return_value=["user-a", "user-b"]),
            patch.object(
                scheduler_manager, "_schedule_user_jobs", return_value=2
            ) as mock_jobs,
            patch("scheduler.manager.schedule") as mock_schedule,
        ):
            mock_schedule.jobs = []
            scheduler_manager.schedule_all_users_immediately()
            assert mock_jobs.call_count == 2
            mock_jobs.assert_any_call("user-a")
            mock_jobs.assert_any_call("user-b")

            mock_jobs.reset_mock()
            scheduler_manager.schedule_new_user("user-new")
            mock_jobs.assert_called_once_with("user-new", verbose=True)
