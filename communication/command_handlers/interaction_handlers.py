# communication/command_handlers/interaction_handlers.py

"""
Interaction handlers for channel-neutral user interactions.

This module provides a framework for handling different types of user interactions
(like task management, check-ins, profile management) in a way that works across
all communication channels (Discord, email, etc.).
"""

from typing import Any

from core.logger import get_component_logger
from core.error_handling import handle_errors
from core.user_data_handlers import get_user_data

from communication.command_handlers.shared_types import (
    InteractionResponse,
    ParsedCommand,
)
from communication.command_handlers.base_handler import InteractionHandler

# Pending confirmations (simple in-memory store)
PENDING_DELETIONS: dict[str, str] = {}

logger = get_component_logger("communication_manager")
handlers_logger = logger


class HelpHandler(InteractionHandler):
    """Handler for help and command information"""

    @handle_errors("checking if can handle help intent", default_return=False)
    def can_handle(self, intent: str) -> bool:
        """Check if this handler can handle the given intent."""
        return intent in ["help", "commands", "examples", "status", "messages"]

    @handle_errors(
        "handling help interaction",
        default_return=InteractionResponse(
            "I'm having trouble with help right now. Please try again.", True
        ),
    )
    def handle(
        self, user_id: str, parsed_command: ParsedCommand
    ) -> InteractionResponse:
        """Handle help and command information interactions."""
        intent = parsed_command.intent
        entities = parsed_command.entities

        if intent == "help":
            return self._handle_general_help(user_id, entities)
        elif intent == "commands":
            return self._handle_commands_list(user_id)
        elif intent == "examples":
            return self._handle_examples(user_id, entities)
        elif intent == "status":
            return self._handle_status(user_id)
        elif intent == "messages":
            return self._handle_messages(user_id)
        else:
            return InteractionResponse(
                "I'm here to help! Try 'help' for general help or 'commands' for a list of commands.",
                True,
            )

    @handle_errors(
        "handling general help",
        default_return=InteractionResponse("Error providing help", False),
    )
    def _handle_general_help(
        self, user_id: str, entities: dict[str, Any]
    ) -> InteractionResponse:
        """Handle general help request"""
        topic = entities.get("topic", "general")

        if topic == "tasks":
            return InteractionResponse(
                "**Task Management Help:**\n"
                "• Create tasks: 'create task \"Call mom tomorrow\"'\n"
                "• List tasks: 'list tasks' or 'show my tasks'\n"
                "• Complete tasks: 'complete task 1' or 'complete \"Call mom\"'\n"
                "• Delete tasks: 'delete task 2' or 'delete \"Buy groceries\"'\n"
                "• Update tasks: 'update task 1 priority high'\n"
                "• Task stats: 'task stats' or 'show task statistics'\n"
                "• Weekly progress: 'how am I doing with my tasks this week?'",
                True,
            )
        elif topic == "checkin":
            return InteractionResponse(
                "**Check-in Help:**\n"
                "• Start check-in: 'start checkin' or 'checkin'\n"
                "• Check-in status: 'checkin status' or 'show checkins'\n"
                "• Check-in history: 'show my check-in history'\n"
                "• Cancel check-in: 'cancel' or '/cancel'",
                True,
            )
        elif topic == "profile":
            return InteractionResponse(
                "**Profile Management Help:**\n"
                "• Show profile: 'show profile' or 'my profile'\n"
                "• Update name: 'update name \"Julie\"'\n"
                "• Update gender identity: 'update gender_identity \"Non-binary\"'\n"
                "• Profile stats: 'profile stats' or 'my statistics'",
                True,
            )
        else:
            return InteractionResponse(
                "**MHM Bot Commands** 🌟\n\n"
                "I understand natural language best! Just talk to me naturally.\n\n"
                "**Tasks**:\n"
                '• "create a task to..." - Add new task\n'
                '• "show my tasks" - View all tasks\n'
                '• "complete [task]" - Mark task done\n'
                "• Or use: /tasks (also !tasks)\n\n"
                "**Check-ins** (Conversational):\n"
                '• "start a check-in" - Begin wellness check-in\n'
                "• I'll ask you questions about mood, energy, etc.\n"
                "• Or use: /checkin (also !checkin)\n\n"
                "**Profile**:\n"
                '• "show my profile" - View your information\n'
                '• "update my name to..." - Change details\n'
                "• Or use: /profile (also !profile)\n\n"
                "**Analytics**:\n"
                '• "show my analytics" - View insights\n'
                '• "what are my mood trends?" - See patterns\n'
                '• "how am I doing with habits?" - Get analysis\n'
                "• Or use: /analytics (also !analytics)\n\n"
                "**Schedule**:\n"
                '• "show my schedule" - View time periods\n'
                '• "add schedule period..." - Create new periods\n'
                "• Or use: /schedule (also !schedule)\n\n"
                "**Need More Help?**\n"
                '• Say "examples" for more natural language examples\n'
                '• Say "commands" for a complete command list\n'
                "• Visit DISCORD_GUIDE.md for full documentation\n\n"
                "Just start typing naturally - I'll understand what you want to do!",
                True,
            )

    @handle_errors(
        "handling commands list",
        default_return=InteractionResponse(
            "Error listing commands", completed=False, error="error"
        ),
    )
    def _handle_commands_list(self, user_id: str) -> InteractionResponse:
        """Handle commands list request"""
        response = "**Complete Command List:**\n\n"

        # Task commands
        response += "📋 **Task Management:**\n"
        response += (
            '• Natural: "create a task to...", "show my tasks", "complete [task]"\n'
        )
        response += "• Explicit: create_task, list_tasks, complete_task, delete_task, update_task, task_stats\n"
        response += "• Slash: /tasks (also !tasks)\n\n"

        # Check-in commands
        response += "✅ **Check-ins** (Conversational Flows):\n"
        response += (
            '• Natural: "start a check-in", "how am I feeling?", "I want to check in"\n'
        )
        response += "• Explicit: start_checkin, checkin_status, checkin_history, checkin_analysis\n"
        response += "• Slash: /checkin (also !checkin)\n"
        response += "• Note: Check-ins are conversational - bot asks questions and waits for responses\n\n"

        # Profile commands
        response += "👤 **Profile Management:**\n"
        response += '• Natural: "show my profile", "update my name to...", "add health condition..."\n'
        response += "• Explicit: show_profile, update_profile, profile_stats\n"
        response += "• Slash: /profile (also !profile)\n\n"

        # Schedule commands
        response += "📅 **Schedule Management:**\n"
        response += '• Natural: "show my schedule", "add schedule period...", "what\'s my schedule status?"\n'
        response += "• Explicit: show_schedule, update_schedule, schedule_status, add_schedule_period, edit_schedule_period\n"
        response += "• Slash: /schedule (also !schedule)\n\n"

        # Analytics commands
        response += "📊 **Analytics & Insights:**\n"
        response += '• Natural: "show my analytics", "what are my mood trends?", "how am I doing with habits?"\n'
        response += "• Explicit: show_analytics, mood_trends, habit_analysis, sleep_analysis, wellness_score\n"
        response += (
            "• More: checkin_history, completion_rate, task_analytics, quant_summary\n"
        )
        response += "• Slash: /analytics (also !analytics)\n\n"

        # System commands
        response += "🔧 **System Commands:**\n"
        response += (
            '• Natural: "help", "what commands are available?", "show me examples"\n'
        )
        response += (
            "• Explicit: help, commands, examples, status, clear_flows, cancel\n"
        )
        response += "• Slash: /help, /status, /clear, /cancel\n\n"

        response += "**Command Types Explained:**\n"
        response += "• **Single-Turn**: Most commands - you ask, bot responds once\n"
        response += "• **Conversational Flows**: Check-ins, some task creation - multi-turn conversations\n"
        response += "• **Natural Language**: Primary method - just talk naturally!\n"
        response += "• **Explicit Commands**: For precision when needed\n"
        response += "• **Slash Commands**: Discord-native shortcuts (preferred) - also supports !commands\n\n"
        response += "**Flow Management:**\n"
        response += '• To exit a conversation: say "cancel" or "/cancel"\n'
        response += '• To clear stuck flows: say "clear flows" or use /clear\n\n'
        response += "**Need More Help?**\n"
        response += '• Say "examples" for natural language examples\n'
        response += (
            '• Say "help [topic]" for specific help (tasks, checkin, profile, etc.)\n'
        )
        response += "• Visit DISCORD_GUIDE.md for complete documentation"

        return InteractionResponse(response, True)

    @handle_errors(
        "handling examples",
        default_return=InteractionResponse("Error providing examples", False),
    )
    def _handle_examples(
        self, user_id: str, entities: dict[str, Any]
    ) -> InteractionResponse:
        """Handle examples request"""
        category = entities.get("category", "general")

        if category == "tasks":
            return InteractionResponse(
                "**Task Examples:**\n"
                "• 'I need to call mom tomorrow'\n"
                "• 'Create a task to buy groceries'\n"
                "• 'Show me my tasks'\n"
                "• 'What tasks are due soon?'\n"
                "• 'Complete task 1'\n"
                "• 'Delete the grocery task'\n"
                "• 'Update task 2 to high priority'",
                True,
            )
        elif category == "checkin":
            return InteractionResponse(
                "**Check-in Examples:**\n"
                "• 'I want to check in'\n"
                "• 'Start my check-in'\n"
                "• 'Show me my check-in history'\n"
                "• 'How am I doing this week?'",
                True,
            )
        elif category == "schedule":
            return InteractionResponse(
                "**Schedule Examples:**\n"
                "• 'Show my schedule'\n"
                "• 'Show my task schedule'\n"
                "• 'Schedule status'\n"
                "• 'Enable my check-in schedule'\n"
                "• 'Add a new period called morning to my task schedule from 9am to 11am'",
                True,
            )
        elif category == "analytics":
            return InteractionResponse(
                "**Analytics Examples:**\n"
                "• 'Show my analytics'\n"
                "• 'Mood trends for 7 days'\n"
                "• 'Habit analysis'\n"
                "• 'Sleep analysis'\n"
                "• 'Wellness score'\n"
                "• 'How am I doing overall?'",
                True,
            )
        else:
            return InteractionResponse(
                "**General Examples:**\n"
                "• 'Create a task to call mom tomorrow'\n"
                "• 'Show me my profile'\n"
                "• 'I want to check in'\n"
                "• 'What tasks do I have?'\n"
                "• 'Update my gender identity to Non-binary'\n"
                "• 'How am I doing with tasks?'\n"
                "• 'Show my schedule'\n"
                "• 'Mood trends'\n\n"
                "Try 'examples tasks', 'examples schedule', or 'examples analytics' for specific examples!",
                True,
            )

    @handle_errors(
        "getting status",
        default_return=InteractionResponse(
            "I'm up and running! 🌟\n\nI can help you with:\n"
            "📋 **Tasks**: Create, list, complete, and manage tasks\n"
            "✅ **Check-ins**: Wellness check-ins\n"
            "👤 **Profile**: View and update your information\n"
            "📅 **Schedule**: Manage message schedules\n"
            "📊 **Analytics**: View wellness insights\n\n"
            "Just start typing naturally - I'll understand what you want to do!",
            True,
        ),
    )
    def _handle_status(self, user_id: str) -> InteractionResponse:
        """Handle status request with detailed system information"""
        from tasks import load_active_tasks
        from core.response_tracking import is_user_checkins_enabled

        # Load user data
        account_result = get_user_data(user_id, "account")
        account_data = account_result.get("account", {}) if account_result else {}
        if not account_data:
            return InteractionResponse(
                "I'm up and running! 🌟\n\nPlease register first to see your personal status.",
                True,
            )

        # Get user info
        username = account_data.get("internal_username", "Unknown")
        features = account_data.get("features", {})

        # Get active tasks
        tasks = load_active_tasks(user_id)
        task_count = len(tasks) if tasks else 0

        # Check if check-ins are enabled
        checkins_enabled = is_user_checkins_enabled(user_id)

        # Build status response
        response = f"**System Status for {username}** 🌟\n\n"

        # Account status
        response += "👤 **Account Status:**\n"
        response += f"• Username: {username}\n"
        response += "• Account: Active ✅\n"
        response += f"• Timezone: {account_data.get('timezone', 'Not set')}\n\n"

        # Features status
        response += "🔧 **Features:**\n"
        for feature, status in features.items():
            status_icon = "✅" if status == "enabled" else "❌"
            response += f"• {feature.replace('_', ' ').title()}: {status_icon}\n"
        response += "\n"

        # Current status
        response += "📊 **Current Status:**\n"
        response += f"• Active Tasks: {task_count}\n"
        response += (
            f"• Check-ins: {'Enabled ✅' if checkins_enabled else 'Disabled ❌'}\n"
        )
        response += "• System: Running smoothly ✅\n\n"

        # Quick actions
        response += "🚀 **Quick Actions:**\n"
        response += "• 'show my tasks' - View your tasks\n"
        response += "• 'start checkin' - Begin check-in\n"
        response += "• 'show profile' - View your profile\n"
        response += "• 'show schedule' - View your schedules\n"
        response += "• 'help' - Get help and examples\n\n"

        response += "Just start typing naturally - I'll understand what you want to do!"

        return InteractionResponse(response, True)

    @handle_errors(
        "getting messages",
        default_return=InteractionResponse(
            "**Messages** 📬\n\n"
            "I can help you with:\n"
            "• check-ins\n"
            "• Task reminders\n"
            "• Motivational messages\n"
            "• Schedule management\n\n"
            "Try 'start checkin' to begin a check-in!",
            True,
        ),
    )
    def _handle_messages(self, user_id: str) -> InteractionResponse:
        """Handle messages request with message history and settings"""
        from core.response_tracking import get_recent_checkins

        # Load user data
        account_result = get_user_data(user_id, "account")
        account_data = account_result.get("account", {}) if account_result else {}
        if not account_data:
            return InteractionResponse(
                "Please register first to view your messages.", True
            )

        # Get user info
        username = account_data.get("internal_username", "Unknown")

        # Get recent check-ins (as a proxy for recent messages)
        recent_checkins = get_recent_checkins(user_id, limit=5)

        # Build messages response
        response = f"**Messages for {username}** 📬\n\n"

        # Message settings
        response += "📧 **Message Settings:**\n"
        response += "• Automated Messages: Enabled ✅\n"
        response += "• Check-ins: Available ✅\n"
        response += "• Task Reminders: Available ✅\n"
        response += "• Motivational Messages: Available ✅\n\n"

        # Recent activity
        response += "📅 **Recent Activity:**\n"
        if recent_checkins:
            response += "Recent check-ins:\n"
            for checkin in recent_checkins:
                date = checkin.get("date", "Unknown")
                response += f"• {date}: Check-in completed ✅\n"
        else:
            response += "No recent check-ins found.\n"
        response += "\n"

        # Quick actions
        response += "🚀 **Quick Actions:**\n"
        response += "• 'start checkin' - Begin check-in\n"
        response += "• 'show schedule' - View message schedules\n"
        response += "• 'show analytics' - View message analytics\n"
        response += "• 'help' - Get help with messages\n\n"

        response += "Your messages are automatically scheduled and delivered based on your preferences!"

        return InteractionResponse(response, True)

    @handle_errors(
        "getting help help", default_return="Get help and see available commands"
    )
    def get_help(self) -> str:
        """Get help text for help commands."""
        return "Get help and see available commands"

    @handle_errors("getting help examples", default_return=[])
    def get_examples(self) -> list[str]:
        """Get example commands for help."""
        return [
            "help",
            "help tasks",
            "help checkin",
            "commands",
            "examples",
            "examples tasks",
        ]


# Registry of all interaction handlers (values may be None until lazy-loaded)
INTERACTION_HANDLERS: dict[str, InteractionHandler | None] = {
    "TaskManagementHandler": None,  # Lazy import
    "CheckinHandler": None,  # Lazy import
    "ProfileHandler": None,  # Lazy import
    "HelpHandler": HelpHandler(),  # Stays in this file (no separate file)
    "ScheduleManagementHandler": None,  # Lazy import
    "AnalyticsHandler": None,  # Lazy import
    "NotebookHandler": None,  # Will be imported below to avoid circular imports
    "AccountManagementHandler": None,  # Will be imported below to avoid circular imports
}


@handle_errors("getting interaction handler", default_return=None)
def get_interaction_handler(intent: str) -> InteractionHandler | None:
    """Get the appropriate handler for an intent"""
    # Lazy import handlers to avoid circular imports
    if INTERACTION_HANDLERS["TaskManagementHandler"] is None:
        try:
            from communication.command_handlers.task_handler import (
                TaskManagementHandler,
            )

            INTERACTION_HANDLERS["TaskManagementHandler"] = TaskManagementHandler()
        except Exception as e:
            logger.warning(f"Could not import TaskManagementHandler: {e}")

    if INTERACTION_HANDLERS["CheckinHandler"] is None:
        try:
            from communication.command_handlers.checkin_handler import CheckinHandler

            INTERACTION_HANDLERS["CheckinHandler"] = CheckinHandler()
        except Exception as e:
            logger.warning(f"Could not import CheckinHandler: {e}")

    if INTERACTION_HANDLERS["ProfileHandler"] is None:
        try:
            from communication.command_handlers.profile_handler import ProfileHandler

            INTERACTION_HANDLERS["ProfileHandler"] = ProfileHandler()
        except Exception as e:
            logger.warning(f"Could not import ProfileHandler: {e}")

    if INTERACTION_HANDLERS["ScheduleManagementHandler"] is None:
        try:
            from communication.command_handlers.schedule_handler import (
                ScheduleManagementHandler,
            )

            INTERACTION_HANDLERS["ScheduleManagementHandler"] = (
                ScheduleManagementHandler()
            )
        except Exception as e:
            logger.warning(f"Could not import ScheduleManagementHandler: {e}")

    if INTERACTION_HANDLERS["AnalyticsHandler"] is None:
        try:
            from communication.command_handlers.analytics_handler import (
                AnalyticsHandler,
            )

            INTERACTION_HANDLERS["AnalyticsHandler"] = AnalyticsHandler()
        except Exception as e:
            logger.warning(f"Could not import AnalyticsHandler: {e}")

    if (
        "NotebookHandler" not in INTERACTION_HANDLERS
        or INTERACTION_HANDLERS["NotebookHandler"] is None
    ):
        try:
            from communication.command_handlers.notebook_handler import NotebookHandler

            INTERACTION_HANDLERS["NotebookHandler"] = NotebookHandler()
        except Exception as e:
            logger.warning(f"Could not import NotebookHandler: {e}")

    if (
        "AccountManagementHandler" not in INTERACTION_HANDLERS
        or INTERACTION_HANDLERS["AccountManagementHandler"] is None
    ):
        try:
            from communication.command_handlers.account_handler import (
                AccountManagementHandler,
            )

            INTERACTION_HANDLERS["AccountManagementHandler"] = (
                AccountManagementHandler()
            )
        except Exception as e:
            logger.warning(f"Could not import AccountManagementHandler: {e}")

    for handler in INTERACTION_HANDLERS.values():
        if handler and handler.can_handle(intent):
            return handler
    return None


@handle_errors("getting all handlers", default_return={})
def get_all_handlers() -> dict[str, InteractionHandler]:
    """Get all registered handlers"""
    # Ensure handlers are loaded
    if INTERACTION_HANDLERS["TaskManagementHandler"] is None:
        try:
            from communication.command_handlers.task_handler import (
                TaskManagementHandler,
            )

            INTERACTION_HANDLERS["TaskManagementHandler"] = TaskManagementHandler()
        except Exception as e:
            logger.warning(f"Could not import TaskManagementHandler: {e}")

    if INTERACTION_HANDLERS["CheckinHandler"] is None:
        try:
            from communication.command_handlers.checkin_handler import CheckinHandler

            INTERACTION_HANDLERS["CheckinHandler"] = CheckinHandler()
        except Exception as e:
            logger.warning(f"Could not import CheckinHandler: {e}")

    if INTERACTION_HANDLERS["ProfileHandler"] is None:
        try:
            from communication.command_handlers.profile_handler import ProfileHandler

            INTERACTION_HANDLERS["ProfileHandler"] = ProfileHandler()
        except Exception as e:
            logger.warning(f"Could not import ProfileHandler: {e}")

    if INTERACTION_HANDLERS["ScheduleManagementHandler"] is None:
        try:
            from communication.command_handlers.schedule_handler import (
                ScheduleManagementHandler,
            )

            INTERACTION_HANDLERS["ScheduleManagementHandler"] = (
                ScheduleManagementHandler()
            )
        except Exception as e:
            logger.warning(f"Could not import ScheduleManagementHandler: {e}")

    if INTERACTION_HANDLERS["AnalyticsHandler"] is None:
        try:
            from communication.command_handlers.analytics_handler import (
                AnalyticsHandler,
            )

            INTERACTION_HANDLERS["AnalyticsHandler"] = AnalyticsHandler()
        except Exception as e:
            logger.warning(f"Could not import AnalyticsHandler: {e}")

    if (
        "NotebookHandler" not in INTERACTION_HANDLERS
        or INTERACTION_HANDLERS["NotebookHandler"] is None
    ):
        try:
            from communication.command_handlers.notebook_handler import NotebookHandler

            INTERACTION_HANDLERS["NotebookHandler"] = NotebookHandler()
        except Exception as e:
            logger.warning(f"Could not import NotebookHandler: {e}")

    if (
        "AccountManagementHandler" not in INTERACTION_HANDLERS
        or INTERACTION_HANDLERS["AccountManagementHandler"] is None
    ):
        try:
            from communication.command_handlers.account_handler import (
                AccountManagementHandler,
            )

            INTERACTION_HANDLERS["AccountManagementHandler"] = (
                AccountManagementHandler()
            )
        except Exception as e:
            logger.warning(f"Could not import AccountManagementHandler: {e}")

    return {k: v for k, v in INTERACTION_HANDLERS.items() if v is not None}
