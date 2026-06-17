# communication/message_processing/structured_command_dispatcher.py

"""Dispatch structured commands to interaction handlers."""

from core.error_handling import handle_errors
from core.logger import get_component_logger
from communication.command_handlers.interaction_handlers import get_interaction_handler
from communication.command_handlers.shared_types import InteractionResponse
from communication.message_processing.command_parser import ParsingResult
from communication.message_processing.help_responses import (
    get_commands_response,
    get_help_response,
)
from communication.message_processing.response_enhancer import enhance_response_with_ai

logger = get_component_logger("communication_manager")


@handle_errors(
    "handling structured command",
    default_return=InteractionResponse(
        "I encountered an error while processing your request. Please try again or ask for help.",
        True,
    ),
)
def dispatch_structured_command(
    user_id: str,
    parsing_result: ParsingResult,
    channel_type: str,
    *,
    command_parser,
    ai_chatbot,
    enable_ai_enhancement: bool,
    command_definitions,
) -> InteractionResponse:
    """Handle a structured command using interaction handlers."""
    parsed_command = parsing_result.parsed_command
    intent = parsed_command.intent

    if intent in ["help"]:
        return get_help_response(
            user_id,
            parsed_command.original_message,
            command_parser=command_parser,
            command_definitions=command_definitions,
        )
    if intent in ["commands"]:
        return get_commands_response(command_definitions)

    handler = get_interaction_handler(intent)
    if not handler:
        logger.warning(f"No handler found for intent: {intent}")
        return InteractionResponse(
            f"I understand you want to {intent}, but I'm not sure how to help with that yet. "
            "Try 'help' to see what I can do!",
            True,
        )

    response = handler.handle(user_id, parsed_command)

    if enable_ai_enhancement and ai_chatbot.is_ai_available():
        response = enhance_response_with_ai(
            user_id,
            response,
            parsed_command,
            ai_chatbot=ai_chatbot,
            enable_ai_enhancement=enable_ai_enhancement,
        )

    if (
        not response.completed
        and intent not in ["start_checkin", "update_task"]
        and (response.suggestions is None)
    ):
        response.suggestions = command_parser.get_suggestions(
            parsed_command.original_message
        )

    return response
