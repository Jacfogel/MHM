# Scheduled check-in prompt flow (delegates send to CommunicationManager).

from __future__ import annotations

from typing import Any

from communication.core.message_send_result import MessageSendResult
from core.error_handling import handle_errors
from core.logger import get_component_logger

logger = get_component_logger("communication_manager")


class CheckinPromptDispatcher:
    """Handles scheduled check-in prompt eligibility and delivery."""

    @handle_errors(
        "initializing check-in prompt dispatcher", user_friendly=False, re_raise=True
    )
    def __init__(self, communication_manager: Any) -> None:
        self._cm = communication_manager

    @handle_errors("determining if check-in prompt should be sent", default_return=True)
    def should_send_checkin_prompt(self, user_id: str, checkin_prefs: dict) -> bool:
        """Return True when the user's check-in settings allow an automatic prompt."""
        try:
            frequency = checkin_prefs.get("frequency", "daily")

            if frequency in ["none", "manual"]:
                logger.debug(
                    f"User {user_id} has check-in frequency set to '{frequency}', skipping auto-prompt"
                )
                return False

            logger.debug(
                f"Check-in scheduled for user {user_id} during scheduled time period"
            )
            return True

        except Exception as e:
            logger.error(
                f"Error determining if check-in prompt should be sent for user {user_id}: {e}"
            )
            return True

    @handle_errors(
        "handling scheduled check-in",
        user_friendly=False,
        default_return=MessageSendResult.failed("", "checkin"),
    )
    def handle_scheduled_checkin(
        self,
        user_id: str,
        messaging_service: str,
        recipient: str,
        message_id: str | None = None,
    ) -> MessageSendResult:
        """Validate check-in feature settings and send the scheduled prompt when due."""
        from communication.communication_channels.email.bot import message_id_for_retry
        from communication.core import channel_orchestrator as _orch
        from communication.message_processing.conversation_flow_manager import (
            conversation_manager,
        )

        prefs_result = _orch.get_user_data(
            user_id, "preferences", normalize_on_read=True
        )
        preferences = prefs_result.get("preferences")
        if not preferences:
            logger.error(f"User preferences not found for user {user_id}")
            return MessageSendResult.failed(user_id, "checkin")

        user_data_result = _orch.get_user_data(user_id, "account", normalize_on_read=True)
        account_data = user_data_result.get("account")
        if (
            not account_data
            or account_data.get("features", {}).get("checkins") != "enabled"
        ):
            logger.debug(f"Check-ins disabled for user {user_id}")
            return MessageSendResult.skipped(user_id, "checkin")

        checkin_prefs = preferences.get("checkin_settings", {})
        frequency = checkin_prefs.get("frequency", "daily")

        if frequency == "none":
            logger.debug(
                f"Check-in frequency set to 'none' for user {user_id}, skipping scheduled check-in"
            )
            return MessageSendResult.skipped(user_id, "checkin")

        if not self.should_send_checkin_prompt(user_id, checkin_prefs):
            logger.debug(f"Check-in not due yet for user {user_id}")
            return MessageSendResult.skipped(user_id, "checkin")

        existing = conversation_manager.current_checkin_prompt(user_id)
        if existing and existing.get("message"):
            logger.info(
                f"Check-in already open for user {user_id}; not starting another"
            )
            return MessageSendResult.skipped(user_id, "checkin")

        success = self.send_checkin_prompt(
            user_id, messaging_service, recipient, message_id=message_id
        )
        if success:
            logger.info(f"Sent scheduled check-in prompt to user {user_id}")
            return MessageSendResult.sent(user_id, "checkin")
        logger.error(f"Failed to send scheduled check-in prompt to user {user_id}")
        return MessageSendResult.failed(
            user_id,
            "checkin",
            message_id=message_id_for_retry(self._cm, message_id),
        )

    # not_duplicate: checkin_prompt_delivery_boundary
    @handle_errors("sending check-in prompt", default_return=False)
    def send_checkin_prompt(
        self,
        user_id: str,
        messaging_service: str,
        recipient: str,
        message_id: str | None = None,
    ) -> bool:
        """Start the dynamic check-in flow and send its prompt through the channel.

        The flow is kept only after the channel accepts the message. A failed
        send clears it so a later attempt can send the same prompt.
        """
        from communication.message_processing.conversation_flow_manager import (
            conversation_manager,
        )

        existing = conversation_manager.current_checkin_prompt(user_id)
        if existing and existing.get("message"):
            logger.info(
                f"Check-in already open for user {user_id}; not starting another"
            )
            return False

        accepted = False
        try:
            reply_text, _completed = conversation_manager._start_dynamic_checkin(user_id)

            from communication.communication_channels.interaction_view_factory import (
                create_interaction_view,
            )

            custom_view = create_interaction_view(
                messaging_service, "checkin", user_id
            )
            send_kwargs: dict[str, str] = {}
            if messaging_service == "email":
                send_kwargs["subject"] = "Check-in"
                send_kwargs["reply_kind"] = "checkin"
            if isinstance(message_id, str) and message_id.strip():
                send_kwargs["message_id"] = message_id.strip()

            accepted = (
                self._cm.send_message_sync(
                    messaging_service,
                    recipient,
                    reply_text,
                    user_id=user_id,
                    category="checkin",
                    view=custom_view,
                    **send_kwargs,
                )
                is True
            )

            if not accepted:
                logger.error(f"Failed to send check-in prompt to user {user_id}")
                return False

            from communication.communication_channels.website.inbox import (
                deliver_to_website,
            )

            deliver_to_website(user_id, reply_text, "checkin")
            logger.info(
                f"Successfully sent check-in prompt to user {user_id} and initialized flow"
            )
            try:
                from communication.core import channel_orchestrator as _orch

                user_logger = _orch.get_component_logger("user_activity")
                user_logger.info(
                    "User check-in started", user_id=user_id, checkin_type="daily"
                )
            except Exception:
                pass
            return True

        except Exception as e:
            logger.error(f"Error sending check-in prompt to user {user_id}: {e}")
            return False
        finally:
            if not accepted:
                conversation_manager._clear_flow_state(user_id, mark_completion=False)
