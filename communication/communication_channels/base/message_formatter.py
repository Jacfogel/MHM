# message_formatter.py

from typing import Dict, Any, List, Optional
from abc import ABC, abstractmethod

from core.logger import get_component_logger
from core.error_handling import handle_errors, DataError

# Route formatting logs to communication component
formatter_logger = get_component_logger("message_formatter")
logger = formatter_logger


class MessageFormatter(ABC):
    """Abstract base class for message formatting utilities"""

    @abstractmethod
    @handle_errors("formatting message", default_return="")
    def format_message(
        self, message: str, rich_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """Format a message with optional rich data"""
        pass

    @abstractmethod
    @handle_errors("creating rich content", default_return=None)
    def create_rich_content(self, message: str, rich_data: Dict[str, Any]) -> Any:
        """Create rich content (embed, card, etc.) from rich data"""
        pass

    @abstractmethod
    @handle_errors("creating interactive elements", default_return=None)
    def create_interactive_elements(self, suggestions: List[str]) -> Any:
        """Create interactive elements (buttons, menus, etc.) from suggestions"""
        pass


class TextMessageFormatter(MessageFormatter):
    """Simple text-based message formatter for plain text channels"""

    @handle_errors("formatting text message", default_return="")
    def format_message(
        self, message: str, rich_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """Format a message as plain text"""
        if not message:
            logger.warning("Empty message provided to formatter")
            return ""

        if not rich_data:
            return message

        try:
            # Extract title if present
            if "title" in rich_data:
                title = str(rich_data["title"])
                message = f"**{title}**\n\n{message}"

            # Add fields if present
            if "fields" in rich_data and isinstance(rich_data["fields"], list):
                message += "\n\n"
                for field in rich_data["fields"]:
                    if isinstance(field, dict):
                        name = str(field.get("name", ""))
                        value = str(field.get("value", ""))
                        message += f"**{name}:** {value}\n"

            # Add footer if present
            if "footer" in rich_data:
                footer = str(rich_data["footer"])
                message += f"\n\n---\n{footer}"

            return message

        except (TypeError, KeyError, AttributeError) as e:
            logger.error(f"Error formatting message with rich data: {e}")
            raise DataError(f"Invalid rich data format: {e}") from e

    @handle_errors("creating rich text content", default_return="")
    def create_rich_content(self, message: str, rich_data: Dict[str, Any]) -> str:
        """Create rich text content"""
        if not message:
            logger.warning("Empty message provided for rich content creation")
            return ""

        if not rich_data:
            logger.warning("No rich data provided for rich content creation")
            return message

        return self.format_message(message, rich_data)

    @handle_errors("creating interactive elements", default_return="")
    def create_interactive_elements(self, suggestions: List[str]) -> str:
        """Create text-based interactive elements"""
        if not suggestions:
            return ""

        try:
            result = "\n\n**Suggestions:**\n"
            for i, suggestion in enumerate(suggestions[:5], 1):
                if suggestion:  # Skip empty suggestions
                    result += f"{i}. {str(suggestion)}\n"

            return result

        except (TypeError, AttributeError) as e:
            logger.error(f"Error creating interactive elements: {e}")
            raise DataError(f"Invalid suggestions format: {e}") from e


class EmailMessageFormatter(MessageFormatter):
    """Email-specific message formatter"""

    @handle_errors("formatting email message", default_return="")
    def format_message(
        self, message: str, rich_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """Format a message for email"""
        if not message:
            logger.warning("Empty message provided to email formatter")
            return ""

        if not rich_data:
            return message

        try:
            # Create HTML-like structure for email
            formatted = message

            if "title" in rich_data:
                title = str(rich_data["title"])
                formatted = f"<h2>{title}</h2>\n\n{formatted}"

            if "fields" in rich_data and isinstance(rich_data["fields"], list):
                formatted += "\n\n"
                for field in rich_data["fields"]:
                    if isinstance(field, dict):
                        name = str(field.get("name", ""))
                        value = str(field.get("value", ""))
                        formatted += f"<strong>{name}:</strong> {value}<br>\n"

            if "footer" in rich_data:
                footer = str(rich_data["footer"])
                formatted += f"\n\n<hr>\n{footer}"

            return formatted

        except (TypeError, KeyError, AttributeError) as e:
            logger.error(f"Error formatting email message with rich data: {e}")
            raise DataError(f"Invalid rich data format for email: {e}") from e

    @handle_errors("creating rich email content", default_return="")
    def create_rich_content(self, message: str, rich_data: Dict[str, Any]) -> str:
        """Create rich email content"""
        if not message:
            logger.warning("Empty message provided for email rich content creation")
            return ""

        if not rich_data:
            logger.warning("No rich data provided for email rich content creation")
            return message

        return self.format_message(message, rich_data)

    @handle_errors("creating email interactive elements", default_return="")
    def create_interactive_elements(self, suggestions: List[str]) -> str:
        """Create email-friendly interactive elements"""
        if not suggestions:
            return ""

        try:
            result = "\n\n<strong>Quick Actions:</strong><br>\n"
            for suggestion in suggestions[:5]:
                if suggestion:  # Skip empty suggestions
                    result += f"• {str(suggestion)}<br>\n"

            return result

        except (TypeError, AttributeError) as e:
            logger.error(f"Error creating email interactive elements: {e}")
            raise DataError(f"Invalid suggestions format for email: {e}") from e


# Factory function to get appropriate formatter
@handle_errors("getting message formatter", default_return=TextMessageFormatter())
def get_message_formatter(channel_type: str) -> MessageFormatter:
    """Get the appropriate message formatter for a channel type"""
    if not channel_type:
        logger.warning("No channel type provided, using default text formatter")
        return TextMessageFormatter()

    try:
        if channel_type.lower() == "email":
            return EmailMessageFormatter()
        else:
            return TextMessageFormatter()
    except Exception as e:
        logger.error(
            f"Error creating message formatter for channel type '{channel_type}': {e}"
        )
        # Return default formatter as fallback
        return TextMessageFormatter()
