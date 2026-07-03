"""Convert AI-layer action requests into communication-layer command dispatch."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ai.prompts.action_catalog import AIActionRequest
from communication.command_handlers.shared_types import InteractionResponse, ParsedCommand
from communication.message_processing.command_parser import ParsingResult
from core.error_handling import handle_errors


@dataclass(frozen=True)
class AIActionExecutionMetadata:
    """Structured execution metadata for result-aware product-AI responses."""

    action_name: str
    attempted: bool
    completed: bool
    handler_message: str
    confidence: float
    source_message: str
    rich_data: dict[str, Any] | None = None
    suggestions: list[str] | None = None
    error: str | None = None

    @handle_errors("serializing AI action execution metadata", default_return={})
    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable metadata dict for prompt composition."""
        return {
            "action_name": self.action_name,
            "attempted": self.attempted,
            "completed": self.completed,
            "handler_message": self.handler_message,
            "confidence": self.confidence,
            "source_message": self.source_message,
            "rich_data": self.rich_data,
            "suggestions": self.suggestions,
            "error": self.error,
        }


@handle_errors("converting AI action request to parsed command", default_return=None)
def convert_action_request_to_parsed_command(
    request: AIActionRequest,
) -> ParsedCommand | None:
    """Convert an AI-planned action request into a communication-layer ParsedCommand."""
    if not request or not request.action_name:
        return None
    return ParsedCommand(
        intent=request.action_name,
        entities=dict(request.entities or {}),
        confidence=float(request.confidence),
        original_message=request.source_message,
    )


@handle_errors("building parsing result from AI action request", default_return=None)
def build_parsing_result_from_action_request(
    request: AIActionRequest,
) -> ParsingResult | None:
    """Build a ParsingResult suitable for dispatch_structured_command."""
    parsed_command = convert_action_request_to_parsed_command(request)
    if parsed_command is None:
        return None
    return ParsingResult(
        parsed_command=parsed_command,
        confidence=float(request.confidence),
        method="ai_action_request",
    )


@handle_errors("building AI action execution metadata", default_return=None)
def build_action_execution_metadata(
    request: AIActionRequest,
    response: InteractionResponse,
) -> AIActionExecutionMetadata | None:
    """Capture handler execution output for result-aware response generation."""
    if request is None or response is None:
        return None
    return AIActionExecutionMetadata(
        action_name=request.action_name,
        attempted=True,
        completed=bool(response.completed),
        handler_message=str(response.message or ""),
        confidence=float(request.confidence),
        source_message=request.source_message,
        rich_data=response.rich_data,
        suggestions=response.suggestions,
        error=response.error,
    )
