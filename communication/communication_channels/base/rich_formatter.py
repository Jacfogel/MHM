# rich_formatter.py

from typing import Dict, Any, List, Optional
from abc import ABC, abstractmethod

from core.logger import get_component_logger
from core.error_handling import handle_errors

# Route rich formatting logs to communication component
rich_formatter_logger = get_component_logger('rich_formatter')
logger = rich_formatter_logger

class RichFormatter(ABC):
    """Abstract base class for rich formatting utilities"""
    
    @abstractmethod
    def create_embed(self, message: str, rich_data: Dict[str, Any]) -> Any:
        """Create a rich embed/card from rich data"""
        pass
    
    @abstractmethod
    def create_interactive_view(self, suggestions: List[str]) -> Any:
        """Create interactive view with buttons/menus from suggestions"""
        pass
    
    @abstractmethod
    def get_color_for_type(self, content_type: str) -> Any:
        """Get appropriate color for content type"""
        pass

class DiscordRichFormatter(RichFormatter):
    """Discord-specific rich formatting utilities"""
    
    @handle_errors("initializing Discord formatter", default_return=None)
    def __init__(self):
        """Initialize Discord formatter"""
        try:
            import discord
            self.discord = discord
        except ImportError:
            logger.warning("Discord library not available - DiscordRichFormatter will not work")
            self.discord = None
        except Exception as e:
            logger.error(f"Error initializing Discord formatter: {e}")
            self.discord = None
    
    @handle_errors("creating Discord embed")
    def create_embed(self, message: str, rich_data: Dict[str, Any]):
        """Create a Discord embed from rich data"""
        if not self.discord:
            return None
        
        embed = self.discord.Embed()
        
        # Set title
        if 'title' in rich_data:
            embed.title = rich_data['title']
        else:
            # Extract title from message if it starts with **
            if message.startswith('**') and '**' in message[2:]:
                title_end = message.find('**', 2)
                embed.title = message[2:title_end]
                message = message[title_end + 2:].strip()
        
        # Set description
        if 'description' in rich_data:
            embed.description = rich_data['description']
        else:
            embed.description = message
        
        # Set color based on type or use default
        embed_type = rich_data.get('type', 'info')
        embed.color = self.get_color_for_type(embed_type)
        
        # Add fields
        if 'fields' in rich_data:
            for field in rich_data['fields']:
                name = field.get('name', '')
                value = field.get('value', '')
                inline = field.get('inline', False)
                embed.add_field(name=name, value=value, inline=inline)
        
        # Add footer
        if 'footer' in rich_data:
            embed.set_footer(text=rich_data['footer'])
        
        # Add timestamp
        if 'timestamp' in rich_data:
            embed.timestamp = rich_data['timestamp']
        
        return embed
    
    @handle_errors("creating Discord interactive view")
    def create_interactive_view(self, suggestions: List[str]):
        """Create a Discord view with buttons from suggestions"""
        if not self.discord:
            return None
        
        # Use discord.ui.View for discord.py v2.x compatibility
        view = self.discord.ui.View()
        
        # Limit to 5 buttons (Discord limit)
        for i, suggestion in enumerate(suggestions[:5]):
            # Create a button with a unique custom_id
            button = self.discord.ui.Button(
                style=self.discord.ButtonStyle.primary,
                label=suggestion[:80],  # Discord button label limit
                custom_id=f"suggestion_{i}_{hash(suggestion) % 10000}"
            )
            view.add_item(button)
        
        return view
    
    @handle_errors("getting Discord color for type", default_return=None)
    def get_color_for_type(self, content_type: str):
        """Get Discord color for content type"""
        try:
            if not self.discord:
                return None
            
            color_map = {
                'success': self.discord.Color.green(),
                'error': self.discord.Color.red(),
                'warning': self.discord.Color.yellow(),
                'info': self.discord.Color.blue(),
                'task': self.discord.Color.purple(),
                'profile': self.discord.Color.orange(),
                'schedule': self.discord.Color.blue(),
                'analytics': self.discord.Color.green(),
                'checkin': self.discord.Color.teal(),
                'help': self.discord.Color.light_grey()
            }
            
            return color_map.get(content_type, self.discord.Color.blue())
        except Exception as e:
            logger.error(f"Error getting Discord color for type {content_type}: {e}")
            return None

class EmailRichFormatter(RichFormatter):
    """Email-specific rich formatting utilities"""
    
    @handle_errors("creating email embed")
    def create_embed(self, message: str, rich_data: Dict[str, Any]) -> str:
        """Create rich HTML content for email"""
        html = ""
        
        if 'title' in rich_data:
            html += f"<h2 style='color: #2c3e50;'>{rich_data['title']}</h2>\n"
        
        if 'description' in rich_data:
            html += f"<p>{rich_data['description']}</p>\n"
        else:
            html += f"<p>{message}</p>\n"
        
        if 'fields' in rich_data:
            html += "<table style='width: 100%; border-collapse: collapse; margin: 10px 0;'>\n"
            for field in rich_data['fields']:
                name = field.get('name', '')
                value = field.get('value', '')
                html += f"<tr><td style='font-weight: bold; padding: 5px;'>{name}</td><td style='padding: 5px;'>{value}</td></tr>\n"
            html += "</table>\n"
        
        if 'footer' in rich_data:
            html += f"<hr style='margin:20px 0;'><p style='font-size: 0.9em; color: #7f8c8d;'>{rich_data['footer']}</p>\n"
        
        return html
    
    @handle_errors("creating email interactive view", default_return="")
    def create_interactive_view(self, suggestions: List[str]) -> str:
        """Create HTML buttons for email"""
        try:
            if not suggestions:
                return ""
            
            html = "<div style='margin: 15px 0;'>\n"
            for suggestion in suggestions[:5]:
                html += f"<a href='#' style='display: inline-block; margin: 5px; padding: 8px 16px; background-color: #3498db; color: white; text-decoration: none; border-radius: 4px;'>{suggestion}</a>\n"
            html += "</div>\n"
            
            return html
        except Exception as e:
            logger.error(f"Error creating email interactive view: {e}")
            return ""
    
    @handle_errors("getting email color for type", default_return="#3498db")
    def get_color_for_type(self, content_type: str) -> str:
        """Get HTML color for content type"""
        try:
            color_map = {
                'success': '#27ae60',
                'error': '#e74c3c',
                'warning': '#f39c12',
                'info': '#3498db',
                'task': '#9b59b6',
                'profile': '#e67e22',
                'schedule': '#3498db',
                'analytics': '#27ae60'
            }
            
            return color_map.get(content_type, '#3498db')
        except Exception as e:
            logger.error(f"Error getting email color for type {content_type}: {e}")
            return "#3498db"

# Factory function to get appropriate rich formatter
@handle_errors("getting rich formatter", default_return=None)
def get_rich_formatter(channel_type: str) -> RichFormatter:
    """Get the appropriate rich formatter for a channel type"""
    try:
        if channel_type == 'discord':
            return DiscordRichFormatter()
        elif channel_type == 'email':
            return EmailRichFormatter()
        else:
            # Return a basic formatter for other channels
            return EmailRichFormatter()  # Use email formatter as fallback
    except Exception as e:
        logger.error(f"Error getting rich formatter for channel type {channel_type}: {e}")
        return EmailRichFormatter()  # Fallback to email formatter
