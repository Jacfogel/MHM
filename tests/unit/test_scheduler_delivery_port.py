import pytest

from communication.core.message_send_result import MessageSendResult
from core.scheduler import SchedulerManager


class SlimDelivery:
    """Minimal fake implementing only the scheduler delivery port."""

    def __init__(self):
        self.message_calls = []
        self.task_calls = []

    def handle_message_sending(
        self,
        user_id,
        category,
        is_scheduled_trigger=False,
        allow_deferral=True,
    ):
        self.message_calls.append(
            {
                "user_id": user_id,
                "category": category,
                "is_scheduled_trigger": is_scheduled_trigger,
                "allow_deferral": allow_deferral,
            }
        )
        return MessageSendResult.sent(user_id, category, sent_text="sent")

    def handle_task_reminder(self, user_id, task_identifier):
        self.task_calls.append((user_id, task_identifier))
        return MessageSendResult.sent(user_id, "task_reminders")


@pytest.mark.unit
@pytest.mark.core
def test_scheduler_handles_scheduled_message_with_slim_delivery(monkeypatch):
    delivery = SlimDelivery()
    scheduler = SchedulerManager(delivery)
    removed_jobs = []

    monkeypatch.setattr(
        scheduler,
        "_remove_user_message_job",
        lambda user_id, category: removed_jobs.append((user_id, category)),
    )

    scheduler.handle_sending_scheduled_message(
        "user-1",
        "motivational",
        retry_attempts=1,
    )

    assert delivery.message_calls == [
        {
            "user_id": "user-1",
            "category": "motivational",
            "is_scheduled_trigger": True,
            "allow_deferral": True,
        }
    ]
    assert removed_jobs == [("user-1", "motivational")]
