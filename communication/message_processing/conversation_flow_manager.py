# communication/message_processing/conversation_flow_manager.py

"""
conversation_flow_manager.py

Provides a single place to handle 'conversation flows' that can be used
by any platform: Discord, Email, etc.

We keep track of each user's 'state' in a dictionary, so if a user is in the middle
of check-in or an AI chat flow, we know what question to ask next.

Usage:
  1) The platform bot receives a message or command from user_id.
  2) That bot calls: conversation_manager.handle_inbound_message(user_id, message_text).
  3) This returns (reply_text, completed). The bot sends reply_text to the user.
  4) If completed == True, the flow is done, so we remove them from user_states.
"""

import importlib

from ai.chatbot import get_ai_chatbot
from checkins.checkin_data_manager import is_user_checkins_enabled
from core.error_handling import handle_errors
from core.logger import get_component_logger

from communication.message_processing.flows.checkin_flow import CheckinFlowMixin
from communication.message_processing.flows.flow_constants import (
    FLOW_CHECKIN,
    FLOW_JOURNAL_BODY,
    FLOW_LIST_ITEMS,
    FLOW_NONE,
    FLOW_NOTE_BODY,
    FLOW_TASK_DUE_DATE,
    FLOW_TASK_PRIORITY,
    FLOW_TASK_REMINDER,
)
from communication.message_processing.flows.note_flow import NoteFlowMixin
from communication.message_processing.flows.task_flow import TaskFlowMixin

logger = get_component_logger("communication_manager")


class ConversationManager(CheckinFlowMixin, TaskFlowMixin, NoteFlowMixin):
    @handle_errors("initializing conversation flow manager", default_return=None)
    def __init__(self):
        self.init_flow_state()

    @handle_errors(
        "handling inbound message",
        default_return=(
            "I'm having trouble processing your message right now. Please try again in a moment.",
            True,
        ),
    )
    def handle_inbound_message(
        self, user_id: str, message_text: str
    ) -> tuple[str, bool]:
        """
        Primary entry point. Takes user's message and returns a (reply_text, completed).

        Now defaults to contextual chat for all messages unless user is in a specific flow
        or uses a special command.
        """
        user_state = self.user_states.get(
            user_id, {"flow": FLOW_NONE, "state": 0, "data": {}}
        )

        # Check if user wants to start a specific flow or use special commands
        if user_state["flow"] == FLOW_NONE:
            # Handle special commands that start specific flows
            if message_text.lower().startswith("/checkin"):
                # Check if check-ins are enabled for this user
                if not is_user_checkins_enabled(user_id):
                    # Clear any existing state for this user
                    self._clear_flow_state(user_id, mark_completion=True)
                    return (
                        "Check-ins are not enabled for your account. Please contact an administrator to enable check-ins.",
                        True,
                    )

                # Initialize dynamic check-in flow based on user preferences
                return self._start_dynamic_checkin(user_id)

            elif message_text.lower().strip() in [
                "skip",
                "!skip",
                "/skip",
                "cancel",
                "!cancel",
                "/cancel",
            ]:
                return (
                    "Nothing to skip/cancel. You're not in a conversation flow.",
                    True,
                )

            else:
                # Default to contextual chat for all other messages
                # This provides rich, personalized responses using the user's context
                ai_bot = get_ai_chatbot()
                reply = ai_bot.generate_contextual_response(
                    user_id, message_text, timeout=10
                )
                return (reply, True)  # Single response, no ongoing flow

        # If user is mid-flow, continue the appropriate flow
        flow = user_state["flow"]
        if flow == FLOW_CHECKIN:
            return self._handle_checkin(user_id, user_state, message_text)
        elif flow == FLOW_TASK_REMINDER:
            # Check if user is trying to issue a command instead of responding to reminder question
            # Commands like "update task", "complete task", "delete task" should clear the flow
            message_lower = message_text.lower().strip()
            command_keywords = [
                "update task",
                "complete task",
                "delete task",
                "show tasks",
                "list tasks",
                "/cancel",
                "cancel",
            ]
            if any(message_lower.startswith(keyword) for keyword in command_keywords):
                # User is issuing a command, clear the flow and let the command be processed
                logger.debug(
                    f"User in FLOW_TASK_REMINDER but issued command '{message_text}', clearing flow"
                )
                self._clear_flow_state(user_id, mark_completion=True)
                return ("", True)  # Return empty to let command be processed
            # Not a command, handle as reminder followup response
            return self._handle_task_reminder_followup(
                user_id, user_state, message_text
            )
        elif flow == FLOW_NOTE_BODY:
            return self._handle_note_body_flow(user_id, user_state, message_text)
        elif flow == FLOW_JOURNAL_BODY:
            return self._handle_journal_body_flow(user_id, user_state, message_text)
        elif flow == FLOW_LIST_ITEMS:
            return self._handle_list_items_flow(user_id, user_state, message_text)
        elif flow == FLOW_TASK_DUE_DATE:
            return self._handle_task_due_date_flow(user_id, user_state, message_text)
        elif flow == FLOW_TASK_PRIORITY:
            return self._handle_task_priority_flow(user_id, user_state, message_text)
        else:
            # Unknown flow - reset to default contextual chat
            self._clear_flow_state(user_id, mark_completion=True)
            ai_bot = get_ai_chatbot()
            reply = ai_bot.generate_contextual_response(
                user_id, message_text, timeout=10
            )
            return (reply, True)
    @handle_errors(
        "starting checkin",
        default_return=(
            "I'm having trouble starting your check-in. Please try again.",
            True,
        ),
    )
    def start_checkin(self, user_id: str) -> tuple[str, bool]:
        """
        Public method to start a check-in flow for a user.
        This is the proper way to initiate check-ins from external modules.
        """
        # Check if check-ins are enabled for this user
        if not is_user_checkins_enabled(user_id):
            # Clear any existing state for this user
            self._clear_flow_state(user_id, mark_completion=True)
            return (
                "Check-ins are not enabled for your account. Please contact an administrator to enable check-ins.",
                True,
            )

        # Clear stale check-ins before checking for active flows
        self._expire_inactive_checkins(user_id)

        # Check if user already has an active checkin flow
        existing_state = self.user_states.get(user_id)
        if existing_state and existing_state.get("flow") == FLOW_CHECKIN:
            # User already has an active checkin - ask if they want to restart
            return (
                "You already have a check-in in progress. Type /cancel to cancel the current check-in, or continue answering the questions.",
                False,
            )

        # Initialize dynamic check-in flow based on user preferences
        result = self._start_dynamic_checkin(user_id)

        # Log user activity for check-in start
        from core.logger import get_component_logger

        user_logger = get_component_logger("user_activity")
        user_logger.info("User check-in started", user_id=user_id, checkin_type="daily")

        return result
    @handle_errors("clearing all conversation states", default_return=None)
    def clear_all_states(self):
        """Clear all user states - primarily for testing."""
        self.user_states.clear()
        self._save_user_states()
        logger.info("Cleared all user states")
    @handle_errors(
        "restarting checkin",
        default_return=(
            "I'm having trouble restarting your check-in. Please try again.",
            True,
        ),
    )
    def restart_checkin(self, user_id: str) -> tuple[str, bool]:
        """
        Force restart a check-in flow, clearing any existing checkin state.
        This should be used when user explicitly wants to start over.
        """
        # Clear any existing checkin state
        existing_state = self.user_states.get(user_id)
        if existing_state and existing_state.get("flow") == FLOW_CHECKIN:
            self._clear_flow_state(user_id, mark_completion=True)
            logger.info(
                f"Cleared existing checkin flow for user {user_id} before restart"
            )

        # Start a new checkin
        return self.start_checkin(user_id)
    @handle_errors(
        "starting tasks flow",
        default_return=("I'm having trouble starting the tasks flow.", True),
    )
    def start_tasks_flow(self, user_id: str) -> tuple[str, bool]:
        """Starter for a future tasks multi-step flow (placeholder)."""
        # For now, delegate to single-turn handler semantics until flow is implemented
        _im = importlib.import_module(
            "communication.message_processing.interaction_manager"
        )
        resp = _im.handle_user_message(user_id, "show my tasks", "discord")
        return (resp.message, True)
    @handle_errors(
        "starting profile flow",
        default_return=("I'm having trouble starting the profile flow.", True),
    )
    def start_profile_flow(self, user_id: str) -> tuple[str, bool]:
        _im = importlib.import_module(
            "communication.message_processing.interaction_manager"
        )
        resp = _im.handle_user_message(user_id, "show profile", "discord")
        return (resp.message, True)
    @handle_errors(
        "starting schedule flow",
        default_return=("I'm having trouble starting the schedule flow.", True),
    )
    def start_schedule_flow(self, user_id: str) -> tuple[str, bool]:
        _im = importlib.import_module(
            "communication.message_processing.interaction_manager"
        )
        resp = _im.handle_user_message(user_id, "show schedule", "discord")
        return (resp.message, True)
    @handle_errors(
        "starting messages flow",
        default_return=("I'm having trouble starting the messages flow.", True),
    )
    def start_messages_flow(self, user_id: str) -> tuple[str, bool]:
        """
        Start the messages flow for a user.

        Initiates the messages management flow by routing the "show messages" command
        through the interaction manager. Returns the response message and completion status.

        Args:
            user_id: The internal user ID to start the messages flow for

        Returns:
            tuple[str, bool]: Response message and completion status (always True for this flow)
        """
        _im = importlib.import_module(
            "communication.message_processing.interaction_manager"
        )
        resp = _im.handle_user_message(user_id, "show messages", "discord")
        return (resp.message, True)
    @handle_errors(
        "starting analytics flow",
        default_return=("I'm having trouble starting the analytics flow.", True),
    )
    def start_analytics_flow(self, user_id: str) -> tuple[str, bool]:
        """
        Start the analytics flow for a user.

        Initiates the analytics display flow by routing the "show analytics" command
        through the interaction manager. Returns the response message and completion status.

        Args:
            user_id: The internal user ID to start the analytics flow for

        Returns:
            tuple[str, bool]: Response message and completion status (always True for this flow)
        """
        _im = importlib.import_module(
            "communication.message_processing.interaction_manager"
        )
        resp = _im.handle_user_message(user_id, "show analytics", "discord")
        return (resp.message, True)
    @handle_errors(
        "handling contextual question",
        default_return="I'm having trouble accessing your context right now. Please try again later.",
    )
    def handle_contextual_question(self, user_id: str, message_text: str) -> str:
        """
        Handle a single contextual question without entering a conversation flow.
        Perfect for one-off questions that benefit from user context.
        """
        ai_bot = get_ai_chatbot()
        return ai_bot.generate_contextual_response(user_id, message_text, timeout=8)


# Create a global instance for convenience:
conversation_manager = ConversationManager()
