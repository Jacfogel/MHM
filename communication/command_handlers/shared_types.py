# shared_types.py

from typing import Any
from dataclasses import dataclass


@dataclass
class InteractionResponse:
    """Response from an interaction handler"""

    message: str
    completed: bool = True
    rich_data: dict[str, Any] | None = None
    suggestions: list[str] | None = None
    error: str | None = None


@dataclass
class ParsedCommand:
    """Parsed command with intent and entities"""

    intent: str
    entities: dict[str, Any]
    confidence: float
    original_message: str
