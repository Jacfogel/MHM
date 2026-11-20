# checkin_handler.py

from typing import Any

from core.logger import get_component_logger
from core.error_handling import handle_errors
from checkins.checkin_service import (
    checkin_display_date,
    get_checkin_start_status,
    get_recent_checkin_summary,
)
from checkins.checkin_data_manager import (
    checkin_runtime_timestamp,
    get_recent_checkins,
    is_user_checkins_enabled,
)
from communication.command_handlers.base_handler import InteractionHandler
from communication.command_handlers.shared_types import (
    InteractionResponse,
    ParsedCommand,
)


# Route checkin logs to command handlers component
checkin_logger = get_component_logger("communication_manager")
logger = checkin_logger


class CheckinHandler(InteractionHandler):
    """Handler for check-in interactions"""

    @handle_errors("checking if can handle check-in", default_return=False)
    def can_handle(self, intent: str) -> bool:
        """Check if this handler can handle the given intent."""
        return intent in ["start_checkin", "continue_checkin", "checkin_status"]

    @handle_errors(
        "handling check-in interaction",
        default_return=InteractionResponse(
            "I could not confirm that your check-in request finished. Your latest answer may already be saved. Send 'checkin status' to check completed check-ins, then use 'start checkin' to resume or start a check-in.",
            True,
        ),
    )
    def handle(
        self, user_id: str, parsed_command: ParsedCommand
    ) -> InteractionResponse:
        """Handle check-in interactions."""
        intent = parsed_command.intent
        entities = parsed_command.entities

        if intent == "start_checkin":
            return self._handle_start_checkin(user_id)
        elif intent == "continue_checkin":
            return self._handle_continue_checkin(user_id, entities)
        elif intent == "checkin_status":
            return self._handle_checkin_status(user_id)
        else:
            return InteractionResponse(
                f"I don't understand that check-in command. Try: {', '.join(self.get_examples())}",
                True,
            )

    @handle_errors(
        "starting check-in",
        default_return=InteractionResponse(
            "I could not finish opening your check-in. A check-in may already be in progress. Send 'start checkin' again to check for an open check-in; send 'checkin status' to check completed check-ins.",
            True,
        ),
    )
    def _handle_start_checkin(self, user_id: str) -> InteractionResponse:
        """Handle starting a check-in by delegating to conversation manager"""
        status = get_checkin_start_status(
            user_id,
            is_enabled=is_user_checkins_enabled,
            load_recent=get_recent_checkins,
            runtime_timestamp=checkin_runtime_timestamp,
        )
        if not status.enabled:
            return InteractionResponse(
                "Check-ins are not enabled for your account. Please contact an administrator to enable check-ins.",
                True,
            )

        if status.already_completed_today:
            return InteractionResponse(
                f"You've already completed a check-in today at {status.last_checkin_timestamp}. "
                "You can start a new check-in tomorrow!",
                True,
            )

        # Delegate to conversation manager for proper check-in flow (modern API)
        from communication.message_processing.conversation_flow_manager import (
            conversation_manager,
        )

        try:
            message, completed = conversation_manager.start_checkin(user_id)
            return InteractionResponse(message, completed)
        except Exception as e:
            logger.error(f"Error starting check-in for user {user_id}: {e}")
            return InteractionResponse(
                "I could not finish opening your check-in. A check-in may already be in progress. Send 'start checkin' again to check for an open check-in; send 'checkin status' to check completed check-ins.",
                True,
            )

    @handle_errors(
        "continuing check-in",
        default_return=InteractionResponse(
            "I could not show how to continue your check-in. This help request did not save an answer. Reply to the latest question, or send 'start checkin' to check for an open check-in.",
            True,
        ),
    )
    def _handle_continue_checkin(
        self, user_id: str, entities: dict[str, Any]
    ) -> InteractionResponse:
        """Handle continuing a check-in"""
        return InteractionResponse(
            "To continue a check-in, reply to the latest question in this chat. "
            "If no question is open, use `/checkin` to start. Type `/cancel` to leave an open check-in.",
            True,
        )

    @handle_errors(
        "checking check-in status",
        default_return=InteractionResponse(
            "I could not load check-in status. This status request did not change your recorded check-ins. Try 'checkin status' again later; if this continues, ask your MHM administrator for help.",
            True,
        ),
    )
    def _handle_checkin_status(self, user_id: str) -> InteractionResponse:
        """Handle check-in status request"""
        summary = get_recent_checkin_summary(
            user_id,
            limit=7,
            is_enabled=is_user_checkins_enabled,
            load_recent=get_recent_checkins,
        )
        if not summary.enabled:
            return InteractionResponse(
                "Check-ins are not enabled for your account.", True
            )

        recent_checkins = summary.entries

        if not recent_checkins:
            return InteractionResponse(
                "No check-ins recorded in the last 7 days.", True
            )

        # Format status
        response = "**Recent Check-ins:**\n"
        for checkin in recent_checkins[:5]:  # Show last 5
            date = checkin_display_date(checkin)
            responses = checkin.get("responses") if isinstance(checkin.get("responses"), dict) else {}
            mood = responses.get("mood", checkin.get("mood", "No mood recorded"))
            energy = responses.get("energy", checkin.get("energy", "No energy recorded"))

            # Display mood and energy together if both are available
            if energy != "No energy recorded":
                response += f"📅 {date}: 😊 Mood {mood}/5 | ⚡ Energy {energy}/5\n"
            else:
                response += f"📅 {date}: 😊 Mood {mood}/5\n"

        if len(recent_checkins) > 5:
            response += f"... and {len(recent_checkins) - 5} more"

        return InteractionResponse(response, True)

    @handle_errors(
        "getting check-in help",
        default_return="Help with check-ins - start, continue, or check status of check-ins",
    )
    def get_help(self) -> str:
        """Get help text for check-in commands."""
        return "Help with check-ins - start check-ins and view your status"

    @handle_errors("getting check-in examples", default_return=[])
    def get_examples(self) -> list[str]:
        """Get example commands for check-ins."""
        return ["start checkin", "checkin status", "checkin"]
