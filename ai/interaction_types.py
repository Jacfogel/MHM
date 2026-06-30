# ai/interaction_types.py

"""Named AI-service interaction types for logging and refactor boundaries."""

from enum import StrEnum

from core.error_handling import handle_errors


class AIInteractionType(StrEnum):
    """Why the system is calling AI and what shape of output is expected."""

    CONVERSATIONAL = "conversational"
    COMMAND_INTERPRETATION = "command_interpretation"
    CLARIFICATION = "clarification"
    PERSONALIZED_MESSAGE = "personalized_message"
    FALLBACK = "fallback"


@handle_errors(
    "mapping response mode to interaction type",
    default_return=AIInteractionType.CONVERSATIONAL,
)
def interaction_type_for_mode(mode: str | None) -> AIInteractionType:
    """Map generate_response mode strings to interaction types."""
    if not mode:
        return AIInteractionType.CONVERSATIONAL
    normalized = mode.lower()
    if normalized == "command":
        return AIInteractionType.COMMAND_INTERPRETATION
    if normalized == "command_with_clarification":
        return AIInteractionType.CLARIFICATION
    if normalized == "chat":
        return AIInteractionType.CONVERSATIONAL
    if normalized == "personalized":
        return AIInteractionType.PERSONALIZED_MESSAGE
    if normalized.startswith("command"):
        return AIInteractionType.COMMAND_INTERPRETATION
    return AIInteractionType.CONVERSATIONAL
