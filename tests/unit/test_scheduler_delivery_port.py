import pytest

from communication.core.message_send_result import MessageSendResult
from scheduler.manager import (
    SchedulerManager,
    clear_all_accumulated_jobs_standalone,
    run_category_scheduler_standalone,
    run_user_scheduler_standalone,
    set_scheduler_delivery_factory,
)


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
@pytest.mark.scheduler
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


@pytest.mark.unit
@pytest.mark.scheduler
def test_scheduler_exposes_delivery_without_communication_manager_alias():
    scheduler = SchedulerManager(SlimDelivery())

    assert isinstance(scheduler.delivery, SlimDelivery)
    assert not hasattr(scheduler, "communication_manager")


@pytest.mark.unit
@pytest.mark.scheduler
def test_standalone_scheduler_helpers_use_configured_delivery_factory(monkeypatch):
    delivery = SlimDelivery()
    created_schedulers = []

    def fake_factory():
        return delivery

    def track_schedule_new_user(self, user_id):
        created_schedulers.append(("user", self.delivery, user_id))

    def track_schedule_category(self, user_id, category):
        created_schedulers.append(("category", self.delivery, user_id, category))

    monkeypatch.setattr(SchedulerManager, "schedule_new_user", track_schedule_new_user)
    monkeypatch.setattr(
        SchedulerManager, "schedule_daily_message_job", track_schedule_category
    )
    set_scheduler_delivery_factory(fake_factory)
    try:
        assert run_user_scheduler_standalone("user-1") is True
        assert run_category_scheduler_standalone("user-1", "motivational") is True
    finally:
        set_scheduler_delivery_factory(None)

    assert created_schedulers == [
        ("user", delivery, "user-1"),
        ("category", delivery, "user-1", "motivational"),
    ]


@pytest.mark.unit
@pytest.mark.scheduler
def test_standalone_scheduler_helper_fails_without_delivery_factory():
    set_scheduler_delivery_factory(None)

    assert clear_all_accumulated_jobs_standalone() is False
