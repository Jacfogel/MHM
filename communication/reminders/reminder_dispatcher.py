# Task reminder dispatch flow (delegates transport to CommunicationManager).

from __future__ import annotations

from typing import Any

from communication.core.message_send_result import (
    CHANNEL_SEND_UNCONFIRMED,
    MessageSendResult,
)
from core.error_handling import handle_errors
from core.logger import get_component_logger

logger = get_component_logger("communication_manager")

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
        self,
        user_id: str,
        task_identifier: str,
        message_id: str | None = None,
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

        from tasks.task_breakdown import next_open_step

        focus_step = next_open_step(user_id, task)
        reminder_message = self.create_task_reminder_message(task, focus_step=focus_step)
        display_title = str(
            (focus_step or task).get("title") or task.get("title") or "Untitled Task"
        )
        custom_view = self.create_task_reminder_view(
            user_id,
            task_identifier,
            task,
            messaging_service,
            task_title=display_title,
        )
        send_kwargs: dict[str, str] = {}
        if messaging_service == "email":
            reminder_message = (
                f"{reminder_message}\n\n"
                "Reply with done, later, skip, or simplify to <smaller step>. "
                "Example: simplify to wipe the kitchen counter."
            )
            send_kwargs["subject"] = f"Task reminder: {display_title}"
            send_kwargs["reply_kind"] = "task_reminder"
            send_kwargs["task_id"] = task_identifier
        if isinstance(message_id, str) and message_id.strip():
            send_kwargs["message_id"] = message_id.strip()

        success = self._cm.send_message_sync(
            messaging_service,
            recipient,
            reminder_message,
            user_id=user_id,
            category=TASK_REMINDER_CATEGORY,
            view=custom_view,
            **send_kwargs,
        )

        if success is True or success == CHANNEL_SEND_UNCONFIRMED:
            from communication.communication_channels.website.inbox import (
                deliver_to_website,
            )

            deliver_to_website(user_id, reminder_message, TASK_REMINDER_CATEGORY)
            self._cm._last_task_reminders[user_id] = task_identifier
            if success == CHANNEL_SEND_UNCONFIRMED:
                logger.warning(
                    f"Task reminder for user {user_id}, task {task_identifier} was handed off but not confirmed"
                )
                return MessageSendResult.unconfirmed(
                    user_id, TASK_REMINDER_CATEGORY, sent_text=reminder_message
                )
            logger.info(
                f"Task reminder sent successfully for user {user_id}, task {task_identifier}"
            )
            return MessageSendResult.sent(
                user_id, TASK_REMINDER_CATEGORY, sent_text=reminder_message
            )

        from communication.communication_channels.email.bot import message_id_for_retry

        logger.error(
            f"Failed to send task reminder for user {user_id}, task {task_identifier}"
        )
        return MessageSendResult.failed(
            user_id,
            TASK_REMINDER_CATEGORY,
            message_id=message_id_for_retry(self._cm, message_id),
        )

    @handle_errors("creating task reminder view", default_return=None)
    def create_task_reminder_view(
        self,
        user_id: str,
        task_identifier: str,
        task: dict,
        messaging_service: str,
        task_title: str | None = None,
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
            task_title=task_title or task.get("title", "Untitled Task"),
        )

    @handle_errors("creating task reminder message", default_return="Task reminder")
    def create_task_reminder_message(
        self, task: dict, focus_step: dict | None = None
    ) -> str:
        """Create a formatted task reminder message."""
        if not task or not isinstance(task, dict):
            logger.error(f"Invalid task: {task}")
            return "Task reminder"

        from tasks.task_data_handlers import runtime_task_due_date

        shown = focus_step if isinstance(focus_step, dict) else task
        title = shown.get("title", "Untitled Task")
        description = shown.get("description", "")
        due_date = runtime_task_due_date(shown) or runtime_task_due_date(task) or ""
        priority = shown.get("priority") or task.get("priority", "medium")

        priority_emoji = {
            "low": "🟢",
            "medium": "🟡",
            "high": "🔴",
            "critical": "🚨",
        }.get(priority, "🟡")

        message = f"💡 **Task Reminder:** {priority_emoji}\n\n"
        message += f"**{title}**\n"
        if isinstance(focus_step, dict):
            parent_title = str(task.get("title") or "").strip()
            if parent_title:
                message += f"Part of {parent_title}\n"

        if description:
            message += f"{description}\n\n"

        if due_date:
            message += f"📅 **Due:** {due_date}\n"

        message += f"⚡ **Priority:** {priority.title()}"

        return message
