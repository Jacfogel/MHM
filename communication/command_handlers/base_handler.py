# communication/command_handlers/base_handler.py

"""
Base handler class and common data structures for command handlers.

This module provides the abstract base class and common data structures
that all command handlers inherit from and use.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from communication.command_handlers.shared_types import InteractionResponse, ParsedCommand
from core.logger import get_component_logger
from core.error_handling import handle_errors, DataError, CommunicationError

# Route handler logs to communication component
handler_logger = get_component_logger('command_handlers')
logger = handler_logger

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
    
    # Helper methods with error handling for common operations
    @handle_errors("validating user ID", default_return=False)
    def _validate_user_id(self, user_id: str) -> bool:
        """Validate that user ID is properly formatted"""
        if not user_id:
            logger.warning("Empty user ID provided")
            return False
        
        if not isinstance(user_id, str):
            logger.warning(f"User ID must be string, got {type(user_id)}")
            return False
        
        if not user_id.strip():
            logger.warning("User ID is whitespace only")
            return False
        
        return True
    
    @handle_errors("validating parsed command", default_return=False)
    def _validate_parsed_command(self, parsed_command: ParsedCommand) -> bool:
        """Validate that parsed command is properly formatted"""
        if not parsed_command:
            logger.warning("Empty parsed command provided")
            return False
        
        if not hasattr(parsed_command, 'intent'):
            logger.warning("Parsed command missing intent attribute")
            return False
        
        if not parsed_command.intent:
            logger.warning("Parsed command has empty intent")
            return False
        
        return True
    
    @handle_errors("creating error response", default_return=None)
    def _create_error_response(self, error_message: str, user_id: str = None) -> InteractionResponse:
        """Create a standardized error response"""
        try:
            from communication.command_handlers.shared_types import InteractionResponse
            
            return InteractionResponse(
                message=f"I'm sorry, I encountered an error: {error_message}",
                success=False,
                error=error_message,
                user_id=user_id
            )
        except Exception as e:
            logger.error(f"Error creating error response: {e}")
            # Return minimal response as fallback
            return InteractionResponse(
                message="I'm sorry, I encountered an error processing your request.",
                success=False,
                error="Response creation failed"
            )
