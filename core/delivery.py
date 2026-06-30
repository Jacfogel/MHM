"""Small delivery interfaces used by scheduler and service request orchestration."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class MessageSendOutcome(Protocol):
    """Result shape returned by delivery sends."""

    status: str
    user_id: str
    category: str
    sent_text: str | None

    # ERROR_HANDLING_EXCLUDE: Protocol method declaration; concrete send result implements handling.
    def matches_request(self, user_id: str, category: str) -> bool:
        """Return True when this result belongs to a request identity."""
        ...


@runtime_checkable
class SchedulerDeliveryPort(Protocol):
    """Delivery operations the scheduler needs."""

    # ERROR_HANDLING_EXCLUDE: Protocol method declaration; concrete delivery implementations handle errors.
    def handle_message_sending(
        self,
        user_id: str,
        category: str,
        is_scheduled_trigger: bool = False,
        allow_deferral: bool = True,
        skip_ai_cache: bool = False,
    ) -> MessageSendOutcome:
        """Send a scheduled or manual category message."""
        ...

    # ERROR_HANDLING_EXCLUDE: Protocol method declaration; concrete delivery implementations handle errors.
    def handle_task_reminder(
        self, user_id: str, task_identifier: str
    ) -> MessageSendOutcome:
        """Send a task reminder."""
        ...


@runtime_checkable
class ServiceRequestDeliveryPort(SchedulerDeliveryPort, Protocol):
    """Delivery operations needed by file-flag service requests."""

    # ERROR_HANDLING_EXCLUDE: Protocol method declaration; concrete delivery implementations handle errors.
    def get_recipient_for_service(
        self, user_id: str, messaging_service: str, preferences: dict
    ) -> str | None:
        """Resolve the channel recipient for a user."""
        ...

    # not_duplicate: checkin_prompt_delivery_boundary
    # ERROR_HANDLING_EXCLUDE: Protocol method declaration; concrete delivery implementations handle errors.
    def send_checkin_prompt(
        self, user_id: str, messaging_service: str, recipient: str
    ) -> Any:
        """Send a check-in prompt for a user."""
        ...
