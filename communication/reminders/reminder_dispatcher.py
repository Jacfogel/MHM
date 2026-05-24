# Task reminder dispatch flow (delegates transport to CommunicationManager).

from __future__ import annotations

from typing import Any

from communication.core.message_send_result import MessageSendResult
from core.error_handling import handle_errors
from core.logger import get_component_logger

logger = get_component_logger("channel_orchestrator")

TASK_REMINDER_CATEGORY = "task_reminders"


class TaskReminderDispatcher:
    """Loads task reminder context, formats the reminder, and sends it."""

    @handle_errors(
        "initializing task reminder dispatcher", user_friendly=False, re_raise=True
    )
    def __init__(self, communication_manager: Any) -> None:
        self._cm = communication_manager

    @handle_errors("handling task reminder", default_return=MessageSendResult.failed())
    def handle_task_reminder(
        self, user_id: str, task_identifier: str
    ) -> MessageSendResult:
        """
        Send a reminder for a task and return the standard send contract.

        ``task_identifier`` matches the task record's canonical ``id`` or another
        value ``get_task_by_id`` accepts.
        """
        if not user_id or not isinstance(user_id, str):
            logger.error(f"Invalid user_id: {user_id}")
            return MessageSendResult.failed(category=TASK_REMINDER_CATEGORY)

        if not user_id.strip():
            logger.error("Empty user_id provided")
            return MessageSendResult.failed(user_id, TASK_REMINDER_CATEGORY)

        if not task_identifier or not isinstance(task_identifier, str):
            logger.error(f"Invalid task_identifier: {task_identifier}")
            return MessageSendResult.failed(user_id, TASK_REMINDER_CATEGORY)

        if not task_identifier.strip():
            logger.error("Empty task_identifier provided")
            return MessageSendResult.failed(user_id, TASK_REMINDER_CATEGORY)

        logger.debug(
            f"Handling task reminder for user_id: {user_id}, task_identifier: {task_identifier}"
        )

        from tasks import are_tasks_enabled, get_task_by_id

        if not are_tasks_enabled(user_id):
            logger.debug(f"Tasks not enabled for user {user_id}")
            return MessageSendResult.skipped(user_id, TASK_REMINDER_CATEGORY)

        task = get_task_by_id(user_id, task_identifier)
        if not task:
            logger.error(f"Task {task_identifier} not found for user {user_id}")
            return MessageSendResult.failed(user_id, TASK_REMINDER_CATEGORY)

        from tasks.task_data_handlers import runtime_task_is_completed

        if runtime_task_is_completed(task):
            logger.debug(
                f"Task {task_identifier} is already completed, skipping reminder"
            )
            return MessageSendResult.skipped(user_id, TASK_REMINDER_CATEGORY)

        from communication.core import channel_orchestrator as _orch

        prefs_result = _orch.get_user_data(user_id, "preferences")
        preferences = prefs_result.get("preferences")
        if not preferences:
            logger.error(f"User preferences not found for user {user_id}.")
            return MessageSendResult.failed(user_id, TASK_REMINDER_CATEGORY)

        messaging_service = preferences.get("channel", {}).get("type")
        if not messaging_service:
            logger.error(f"No messaging service configured for user {user_id}")
            return MessageSendResult.failed(user_id, TASK_REMINDER_CATEGORY)

        recipient = self._cm.get_recipient_for_service(
            user_id, messaging_service, preferences
        )
        if not recipient:
            logger.error(
                f"No valid recipient found for user {user_id} with service {messaging_service}"
            )
            return MessageSendResult.failed(user_id, TASK_REMINDER_CATEGORY)

        reminder_message = self.create_task_reminder_message(task)
        custom_view = self.create_task_reminder_view(
            user_id, task_identifier, task, messaging_service
        )

        success = self._cm.send_message_sync(
            messaging_service,
            recipient,
            reminder_message,
            user_id=user_id,
            category=TASK_REMINDER_CATEGORY,
            view=custom_view,
        )

        if success:
            logger.info(
                f"Task reminder sent successfully for user {user_id}, task {task_identifier}"
            )
            self._cm._last_task_reminders[user_id] = task_identifier
            return MessageSendResult.sent(
                user_id, TASK_REMINDER_CATEGORY, sent_text=reminder_message
            )

        logger.error(
            f"Failed to send task reminder for user {user_id}, task {task_identifier}"
        )
        return MessageSendResult.failed(user_id, TASK_REMINDER_CATEGORY)

    @handle_errors("creating task reminder view", default_return=None)
    def create_task_reminder_view(
        self,
        user_id: str,
        task_identifier: str,
        task: dict,
        messaging_service: str,
    ):
        """Create a channel-specific interactive reminder view when supported."""
        from communication.communication_channels.interaction_view_factory import (
            create_interaction_view,
        )

        return create_interaction_view(
            messaging_service,
            "task_reminder",
            user_id,
            task_identifier=task_identifier,
            task_title=task.get("title", "Untitled Task"),
        )

    @handle_errors("creating task reminder message", default_return="Task reminder")
    def create_task_reminder_message(self, task: dict) -> str:
        """Create a formatted task reminder message."""
        if not task or not isinstance(task, dict):
            logger.error(f"Invalid task: {task}")
            return "Task reminder"

        from tasks.task_data_handlers import runtime_task_due_date

        title = task.get("title", "Untitled Task")
        description = task.get("description", "")
        due_date = runtime_task_due_date(task) or ""
        priority = task.get("priority", "medium")

        priority_emoji = {
            "low": "🟢",
            "medium": "🟡",
            "high": "🔴",
            "critical": "🚨",
        }.get(priority, "🟡")

        message = f"💡 **Task Reminder:** {priority_emoji}\n\n"
        message += f"**{title}**\n"

        if description:
            message += f"{description}\n\n"

        if due_date:
            message += f"📅 **Due:** {due_date}\n"

        message += f"⚡ **Priority:** {priority.title()}"

        return message
