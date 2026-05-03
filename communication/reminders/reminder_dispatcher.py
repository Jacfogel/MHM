# Scheduled check-in prompt flow (delegates send to CommunicationManager).

from __future__ import annotations

from typing import Any

from core import get_user_data
from core.error_handling import handle_errors
from core.logger import get_component_logger

logger = get_component_logger("channel_orchestrator")


class CheckinReminderDispatcher:
    @handle_errors("initializing check-in reminder dispatcher", user_friendly=False, re_raise=True)
    def __init__(self, communication_manager: Any) -> None:
        self._cm = communication_manager

    @handle_errors("determining if check-in prompt should be sent", default_return=True)
    def should_send_checkin_prompt(self, user_id: str, checkin_prefs: dict) -> bool:
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
        "handling scheduled check-in", user_friendly=False, default_return=None
    )
    def handle_scheduled_checkin(
        self, user_id: str, messaging_service: str, recipient: str
    ):
        prefs_result = get_user_data(user_id, "preferences", normalize_on_read=True)
        preferences = prefs_result.get("preferences")
        if not preferences:
            logger.error(f"User preferences not found for user {user_id}")
            return

        user_data_result = get_user_data(user_id, "account", normalize_on_read=True)
        account_data = user_data_result.get("account")
        if (
            not account_data
            or account_data.get("features", {}).get("checkins") != "enabled"
        ):
            logger.debug(f"Check-ins disabled for user {user_id}")
            return

        checkin_prefs = preferences.get("checkin_settings", {})
        frequency = checkin_prefs.get("frequency", "daily")

        if frequency == "none":
            logger.debug(
                f"Check-in frequency set to 'none' for user {user_id}, skipping scheduled check-in"
            )
            return

        if self.should_send_checkin_prompt(user_id, checkin_prefs):
            self._cm._send_checkin_prompt(user_id, messaging_service, recipient)
            logger.info(f"Sent scheduled check-in prompt to user {user_id}")
        else:
            logger.debug(f"Check-in not due yet for user {user_id}")

    @handle_errors("sending check-in prompt", default_return=None)
    def send_checkin_prompt(
        self, user_id: str, messaging_service: str, recipient: str
    ):
        try:
            from communication.message_processing.conversation_flow_manager import (
                conversation_manager,
            )

            reply_text, completed = conversation_manager._start_dynamic_checkin(user_id)

            custom_view = None
            if messaging_service == "discord":
                try:
                    from communication.communication_channels.discord.checkin_view import (
                        get_checkin_view,
                    )

                    import asyncio

                    try:
                        asyncio.get_running_loop()
                        custom_view = get_checkin_view(user_id)
                    except RuntimeError:

                        @handle_errors("creating check-in view", default_return=None)
                        def create_view():
                            return get_checkin_view(user_id)

                        custom_view = create_view
                except Exception as e:
                    logger.warning(f"Could not create check-in view for Discord: {e}")

            success = self._cm.send_message_sync(
                messaging_service,
                recipient,
                reply_text,
                user_id=user_id,
                category="checkin",
                view=custom_view,
            )

            if success:
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
            else:
                logger.warning(f"Failed to send check-in prompt to user {user_id}")

        except Exception as e:
            logger.error(f"Error sending check-in prompt to user {user_id}: {e}")
