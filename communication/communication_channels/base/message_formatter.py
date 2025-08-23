# message_formatter.py

from typing import Dict, Any, List, Optional
from abc import ABC, abstractmethod

from core.logger import get_component_logger

# Route formatting logs to communication component
formatter_logger = get_component_logger('message_formatter')
logger = formatter_logger

class MessageFormatter(ABC):
    """Abstract base class for message formatting utilities"""
    
    @abstractmethod
    def format_message(self, message: str, rich_data: Optional[Dict[str, Any]] = None) -> str:
        """Format a message with optional rich data"""
        pass
    
    @abstractmethod
    def create_rich_content(self, message: str, rich_data: Dict[str, Any]) -> Any:
        """Create rich content (embed, card, etc.) from rich data"""
        pass
    
    @abstractmethod
    def create_interactive_elements(self, suggestions: List[str]) -> Any:
        """Create interactive elements (buttons, menus, etc.) from suggestions"""
        pass

class TextMessageFormatter(MessageFormatter):
    """Simple text-based message formatter for plain text channels"""
    
    def format_message(self, message: str, rich_data: Optional[Dict[str, Any]] = None) -> str:
        """Format a message as plain text"""
        if not rich_data:
            return message
        
        # Extract title if present
        if 'title' in rich_data:
            message = f"**{rich_data['title']}**\n\n{message}"
        
        # Add fields if present
        if 'fields' in rich_data:
            message += "\n\n"
            for field in rich_data['fields']:
                name = field.get('name', '')
                value = field.get('value', '')
                message += f"**{name}:** {value}\n"
        
        # Add footer if present
        if 'footer' in rich_data:
            message += f"\n\n---\n{rich_data['footer']}"
        
        return message
    
    def create_rich_content(self, message: str, rich_data: Dict[str, Any]) -> str:
        """Create rich text content"""
        return self.format_message(message, rich_data)
    
    def create_interactive_elements(self, suggestions: List[str]) -> str:
        """Create text-based interactive elements"""
        if not suggestions:
            return ""
        
        result = "\n\n**Suggestions:**\n"
        for i, suggestion in enumerate(suggestions[:5], 1):
            result += f"{i}. {suggestion}\n"
        
        return result

class EmailMessageFormatter(MessageFormatter):
    """Email-specific message formatter"""
    
    def format_message(self, message: str, rich_data: Optional[Dict[str, Any]] = None) -> str:
        """Format a message for email"""
        if not rich_data:
            return message
        
        # Create HTML-like structure for email
        formatted = message
        
        if 'title' in rich_data:
            formatted = f"<h2>{rich_data['title']}</h2>\n\n{formatted}"
        
        if 'fields' in rich_data:
            formatted += "\n\n"
            for field in rich_data['fields']:
                name = field.get('name', '')
                value = field.get('value', '')
                formatted += f"<strong>{name}:</strong> {value}<br>\n"
        
        if 'footer' in rich_data:
            formatted += f"\n\n<hr>\n{rich_data['footer']}"
        
        return formatted
    
    def create_rich_content(self, message: str, rich_data: Dict[str, Any]) -> str:
        """Create rich email content"""
        return self.format_message(message, rich_data)
    
    def create_interactive_elements(self, suggestions: List[str]) -> str:
        """Create email-friendly interactive elements"""
        if not suggestions:
            return ""
        
        result = "\n\n<strong>Quick Actions:</strong><br>\n"
        for suggestion in suggestions[:5]:
            result += f"• {suggestion}<br>\n"
        
        return result

# Factory function to get appropriate formatter
def get_message_formatter(channel_type: str) -> MessageFormatter:
    """Get the appropriate message formatter for a channel type"""
    if channel_type == 'email':
        return EmailMessageFormatter()
    else:
        return TextMessageFormatter()
