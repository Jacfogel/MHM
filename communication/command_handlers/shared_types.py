# shared_types.py

from typing import Dict, Any, List, Optional
from dataclasses import dataclass

@dataclass
class InteractionResponse:
    """Response from an interaction handler"""
    message: str
    completed: bool = True
    rich_data: Optional[Dict[str, Any]] = None
    suggestions: Optional[List[str]] = None
    error: Optional[str] = None

@dataclass
class ParsedCommand:
    """Parsed command with intent and entities"""
    intent: str
    entities: Dict[str, Any]
    confidence: float
    original_message: str
