# communication/command_handlers/base_handler.py

"""
Base handler class and common data structures for command handlers.

This module provides the abstract base class and common data structures
that all command handlers inherit from and use.
"""

from abc import ABC, abstractmethod
from communication.command_handlers.shared_types import (
    InteractionResponse,
    ParsedCommand,
)
from core.logger import get_component_logger
from core.error_handling import handle_errors

# Route handler logs to communication component
handler_logger = get_component_logger("command_handlers")
logger = handler_logger


class InteractionHandler(ABC):
    """Abstract base class for interaction handlers"""

    @abstractmethod
    @handle_errors("checking if can handle intent", default_return=False)
    def can_handle(self, intent: str) -> bool:
        """
        Check if this handler can handle the given intent.

        Args:
            intent: The intent string to check (e.g., 'create_task', 'show_profile')

        Returns:
            bool: True if can handle, False otherwise
        """
        pass

    @abstractmethod
    @handle_errors(
        "handling interaction",
        default_return=InteractionResponse(
            "I'm having trouble processing your request. Please try again.", True
        ),
    )
    def handle(
        self, user_id: str, parsed_command: ParsedCommand
    ) -> InteractionResponse:
        """
        Handle the interaction and return a response with validation.

        Returns:
            InteractionResponse: Response to the interaction
        """
        # Validate user_id
        if not user_id or not isinstance(user_id, str):
            logger.error(f"Invalid user_id: {user_id}")
            return InteractionResponse("Invalid user ID provided", False)

        if not user_id.strip():
            logger.error("Empty user_id provided")
            return InteractionResponse("Empty user ID provided", False)

        # Validate parsed_command
        if not parsed_command:
            logger.error("Invalid parsed_command: None")
            return InteractionResponse("Invalid command provided", False)

    @abstractmethod
    @handle_errors("getting help", default_return="Help information not available")
    def get_help(self) -> str:
        """
        Get help text for this handler with validation.

        Returns:
            str: Help text, default if failed
        """

    @abstractmethod
    @handle_errors("getting examples", default_return=[])
    def get_examples(self) -> list[str]:
        """
        Get example commands for this handler with validation.

        Returns:
            List[str]: Example commands, empty list if failed
        """

    # Helper methods with error handling for common operations
    @handle_errors("validating user ID", default_return=False)
    def _validate_user_id(self, user_id: str) -> bool:
        """
        Validate that user ID is properly formatted with enhanced validation.

        Returns:
            bool: True if valid, False otherwise
        """
        # Validate user_id type
        if not user_id or not isinstance(user_id, str):
            logger.error(f"Invalid user_id type: {type(user_id)}")
            return False

        if not user_id.strip():
            logger.error("Empty user_id provided")
            return False

        # Additional validation for user_id format
        if len(user_id) < 1 or len(user_id) > 100:
            logger.error(f"Invalid user_id length: {len(user_id)}")
            return False

        # Check for valid characters (alphanumeric, underscore, hyphen)
        if not user_id.replace("_", "").replace("-", "").isalnum():
            logger.error(f"Invalid user_id format: {user_id}")
            return False

        return True

    @handle_errors("validating parsed command", default_return=False)
    def _validate_parsed_command(self, parsed_command: ParsedCommand) -> bool:
        """
        Validate that parsed command is properly formatted with enhanced validation.

        Returns:
            bool: True if valid, False otherwise
        """
        if not parsed_command:
            logger.error("Empty parsed command provided")
            return False

        if not hasattr(parsed_command, "intent"):
            logger.error("Parsed command missing intent attribute")
            return False

        if not parsed_command.intent:
            logger.error("Parsed command has empty intent")
            return False

        # Validate intent format
        if not isinstance(parsed_command.intent, str):
            logger.error(f"Invalid intent type: {type(parsed_command.intent)}")
            return False

        if not parsed_command.intent.strip():
            logger.error("Intent is whitespace only")
            return False

        return True

    @handle_errors("creating error response", default_return=None)
    def _create_error_response(
        self, error_message: str, user_id: str | None = None
    ) -> InteractionResponse | None:
        """
        Create a standardized error response with validation.

        Args:
            error_message: The error message to include
            user_id: Optional user ID for logging

        Returns:
            InteractionResponse: Error response, or None if inputs are invalid
        """
        # Validate error_message
        if not error_message or not isinstance(error_message, str):
            logger.error(f"Invalid error_message: {error_message}")
            return None

        if not error_message.strip():
            logger.error("Empty error_message provided")
            return None

        # Validate user_id if provided
        if user_id is not None and not isinstance(user_id, str):
            logger.error(f"Invalid user_id: {user_id}")
            return None

        try:
            return InteractionResponse(
                message=f"I'm sorry, I encountered an error: {error_message}",
                completed=False,
                error=error_message,
            )
        except Exception as e:
            logger.error(f"Error creating error response: {e}")
            return None
