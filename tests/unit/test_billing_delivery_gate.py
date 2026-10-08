from unittest.mock import MagicMock

import pytest

from communication.core.message_send_result import MessageSendResult
from scheduler import manager as scheduler_manager
from scheduler import task_reminders

pytestmark = [pytest.mark.unit, pytest.mark.scheduler]


def test_expired_trial_blocks_scheduled_category_send(monkeypatch):
    monkeypatch.setattr(
        scheduler_manager,
        "get_user_data",
        lambda *_args, **_kwargs: {
            "account": {
                "subscription_status": "trialing",
                "trial_ends_at": "2000-01-01 00:00:00",
            }
        },
    )
    assert scheduler_manager._automated_category_allowed("user-1", "checkin") is False


def test_canceled_subscription_blocks_task_reminder_before_delivery(monkeypatch):
    import core

    monkeypatch.setattr(
        core,
        "get_user_data",
        lambda *_args, **_kwargs: {"account": {"subscription_status": "canceled"}},
    )
    owner = MagicMock()
    owner.delivery.handle_task_reminder.return_value = MessageSendResult.sent(
        "user-1", "task_reminders"
    )
    task_reminders.handle_task_reminder(owner, "user-1", "task-1", retry_attempts=1)
    owner.delivery.handle_task_reminder.assert_not_called()
