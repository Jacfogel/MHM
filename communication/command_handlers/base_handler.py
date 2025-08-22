# communication/command_handlers/base_handler.py

"""
Base handler class and common data structures for command handlers.

This module provides the abstract base class and common data structures
that all command handlers inherit from and use.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
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

class InteractionHandler(ABC):
    """Abstract base class for interaction handlers"""
    
    @abstractmethod
    def can_handle(self, intent: str) -> bool:
        """Check if this handler can handle the given intent"""
        pass
    
    @abstractmethod
    def handle(self, user_id: str, parsed_command: ParsedCommand) -> InteractionResponse:
        """Handle the interaction and return a response"""
        pass
    
    @abstractmethod
    def get_help(self) -> str:
        """Get help text for this handler"""
        pass
    
    @abstractmethod
    def get_examples(self) -> List[str]:
        """Get example commands for this handler"""
        pass
