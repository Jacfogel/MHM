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


@dataclass(frozen=True)
class PaginationAction:
    """Channel-neutral metadata for requesting the next page of results."""

    domain: str
    action: str
    params: dict[str, Any]
    limit: int
    offset: int
    next_offset: int
    remaining_count: int


@dataclass
class ParsedCommand:
    """Parsed command with intent and entities"""

    intent: str
    entities: dict[str, Any]
    confidence: float
    original_message: str
