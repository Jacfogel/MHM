"""Shared Discord helpers for invoking command handlers from UI callbacks."""

from __future__ import annotations

from typing import Any

from communication.command_handlers.shared_types import InteractionResponse, ParsedCommand
from core.error_handling import handle_errors


@handle_errors("running Discord command handler", default_return=None)
def run_discord_handler_intent(
    user_id: str,
    intent: str,
    entities: dict[str, Any],
    original_message: str,
    *,
    missing_handler_message: str,
) -> InteractionResponse:
    """Run a command handler for a Discord UI action."""
    from communication.command_handlers.interaction_handlers import get_interaction_handler

    handler = get_interaction_handler(intent)
    if not handler:
        return InteractionResponse(missing_handler_message, True)
    return handler.handle(
        user_id,
        ParsedCommand(
            intent=intent,
            entities=entities,
            confidence=1.0,
            original_message=original_message,
        ),
    )
