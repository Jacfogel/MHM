# communication/message_processing/help_responses.py

"""Help and command-list responses for interaction manager."""

from core.error_handling import handle_errors
from communication.command_handlers.shared_types import InteractionResponse
from communication.message_processing.command_registry import (
    CommandDefinition,
    command_definitions_as_dicts,
)


@handle_errors(
    "getting help response",
    default_return=InteractionResponse(
        "I'm here to help! Try asking about tasks, check-ins, or your profile.",
        True,
    ),
)
def get_help_response(
    user_id: str,
    message: str,
    *,
    command_parser,
    command_definitions: list[CommandDefinition],
) -> InteractionResponse:
    """Get a help response when command parsing fails."""
    suggestions = command_parser.get_suggestions(message)

    help_text = (
        "I'm not sure what you'd like to do. Here are some things you can try:\n\n"
        "📋 **Task Management:**\n"
        "• Create a task: 'I need to call mom tomorrow'\n"
        "• List tasks: 'Show me my tasks'\n"
        "• Complete tasks: 'Complete task 1'\n\n"
        "✅ **Check-ins:**\n"
        "• Start check-in: 'I want to check in'\n"
        "• View history: 'Show my check-ins'\n\n"
        "👤 **Profile:**\n"
        "• View profile: 'Show my profile'\n"
        "• Update info: 'Update my name to Julie'\n\n"
        "📅 **Schedule Management:**\n"
        "• View schedule: 'Show my schedule'\n"
        "• Check status: 'Schedule status'\n"
        "• Enable/disable: 'Enable my task schedule'\n\n"
        "📊 **Analytics & Insights:**\n"
        "• View analytics: 'Show my analytics'\n"
        "• Mood trends: 'Mood trends for 7 days'\n"
        "• Habit analysis: 'Habit analysis'\n\n"
        "Try one of these or ask for 'help' to learn more!"
    )

    try:
        defs = command_definitions_as_dicts(command_definitions)
        names = [f"/{d['name']}" for d in defs]
        if names:
            help_text += "\n\nQuick commands: " + ", ".join(names)
    except Exception:
        pass

    return InteractionResponse(help_text, True, suggestions=suggestions)


@handle_errors(
    "getting commands response",
    default_return=InteractionResponse("Error getting commands", False),
)
def get_commands_response(
    command_definitions: list[CommandDefinition],
) -> InteractionResponse:
    """Return a concise, channel-agnostic commands list for quick discovery."""
    defs = command_definitions_as_dicts(command_definitions)
    preferred = [
        "checkin",
        "tasks",
        "profile",
        "schedule",
        "messages",
        "analytics",
        "status",
        "help",
        "cancel",
    ]
    sorted_defs = sorted(
        defs,
        key=lambda d: preferred.index(d["name"]) if d["name"] in preferred else 999,
    )

    lines: list[str] = ["**Available Commands**"]
    lines.append("Slash commands (where supported):")
    for d in sorted_defs:
        slash = f"/{d['name']}"
        lines.append(f"- {slash} — {d['description']}")
    lines.append("")
    lines.append(
        "Classic commands (if enabled): !tasks, !profile, !schedule, !messages, !analytics, !status"
    )

    text = "\n".join(lines)
    return InteractionResponse(text, True)
