# event_handler.py

import discord
from discord import app_commands
import asyncio
import time
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum

from core.logger import get_component_logger
from core.error_handling import handle_errors
from core.user_management import get_user_id_by_identifier
from communication.message_processing.interaction_manager import handle_user_message

# Route event handler logs to Discord component
event_logger = get_component_logger('discord_events')
logger = event_logger

class EventType(Enum):
    """Types of Discord events"""
    MESSAGE = "message"
    READY = "ready"
    DISCONNECT = "disconnect"
    ERROR = "error"
    REACTION_ADD = "reaction_add"
    REACTION_REMOVE = "reaction_remove"
    MEMBER_JOIN = "member_join"
    MEMBER_LEAVE = "member_leave"

@dataclass
class EventContext:
    """Context for Discord events"""
    event_type: EventType
    user_id: Optional[str] = None
    channel_id: Optional[str] = None
    guild_id: Optional[str] = None
    message_id: Optional[str] = None
    timestamp: float = None
    data: Dict[str, Any] = None
    
    @handle_errors("post-initializing Discord event handler", default_return=None)
    def __post_init__(self):
        """Post-initialization setup"""
        if self.timestamp is None:
            self.timestamp = time.time()
        if self.data is None:
            self.data = {}

class DiscordEventHandler:
    """Handles Discord events and routes them to appropriate handlers"""
    
    @handle_errors("initializing Discord event handler", default_return=None)
    def __init__(self, bot: discord.Client = None):
        """Initialize the Discord event handler"""
        self.bot = bot
        self._event_handlers: Dict[EventType, List[Callable]] = {}
        self._message_handlers: List[Callable] = []
        self._ready_handlers: List[Callable] = []
        self._disconnect_handlers: List[Callable] = []
        self._error_handlers: List[Callable] = []
        
        # Register default handlers
        self._register_default_handlers()
    
    @handle_errors("registering default Discord handlers", default_return=None)
    def _register_default_handlers(self):
        """Register default event handlers"""
        if self.bot:
            self.bot.event(self.on_ready)
            self.bot.event(self.on_disconnect)
            self.bot.event(self.on_error)
            self.bot.event(self.on_message)
    
    @handle_errors("adding message handler")
    def add_message_handler(self, handler: Callable):
        """Add a custom message handler"""
        self._message_handlers.append(handler)
    
    @handle_errors("adding ready handler")
    def add_ready_handler(self, handler: Callable):
        """Add a custom ready handler"""
        self._ready_handlers.append(handler)
    
    @handle_errors("adding disconnect handler")
    def add_disconnect_handler(self, handler: Callable):
        """Add a custom disconnect handler"""
        self._disconnect_handlers.append(handler)
    
    @handle_errors("adding error handler")
    def add_error_handler(self, handler: Callable):
        """Add a custom error handler"""
        self._error_handlers.append(handler)
    
    @handle_errors("handling Discord ready event")
    async def on_ready(self):
        """Handle Discord ready event"""
        logger.info(f"Discord bot is ready! Logged in as {self.bot.user}")
        
        # Call custom ready handlers
        for handler in self._ready_handlers:
            try:
                await handler(self.bot)
            except Exception as e:
                logger.error(f"Error in custom ready handler: {e}")
        
        # Set bot status
        try:
            await self.bot.change_presence(
                activity=discord.Activity(
                    type=discord.ActivityType.watching,
                    name="your wellness"
                )
            )
        except Exception as e:
            logger.warning(f"Could not set bot status: {e}")
    
    @handle_errors("handling Discord disconnect event")
    async def on_disconnect(self):
        """Handle Discord disconnect event"""
        logger.warning("Discord bot disconnected")
        
        # Call custom disconnect handlers
        for handler in self._disconnect_handlers:
            try:
                await handler(self.bot)
            except Exception as e:
                logger.error(f"Error in custom disconnect handler: {e}")
    
    @handle_errors("handling Discord error event")
    async def on_error(self, event, *args, **kwargs):
        """Handle Discord error event"""
        logger.error(f"Discord error in event {event}: {args} {kwargs}")
        
        # Call custom error handlers
        for handler in self._error_handlers:
            try:
                await handler(event, args, kwargs)
            except Exception as e:
                logger.error(f"Error in custom error handler: {e}")
    
    @handle_errors("handling Discord message event")
    async def on_message(self, message: discord.Message):
        """Handle Discord message event"""
        # Ignore bot messages
        if message.author == self.bot.user:
            return
        
        # Ignore messages without content
        if not message.content:
            return
        
        # Create event context
        context = EventContext(
            event_type=EventType.MESSAGE,
            user_id=str(message.author.id),
            channel_id=str(message.channel.id),
            guild_id=str(message.guild.id) if message.guild else None,
            message_id=str(message.id),
            data={
                "content": message.content,
                "attachments": [att.url for att in message.attachments],
                "embeds": [embed.to_dict() for embed in message.embeds]
            }
        )
        
        # Call custom message handlers
        for handler in self._message_handlers:
            try:
                await handler(message, context)
            except Exception as e:
                logger.error(f"Error in custom message handler: {e}")
        
        # Handle the message through the interaction manager
        await self._handle_user_message(message, context)
    
    @handle_errors("handling user message through interaction manager")
    async def _handle_user_message(self, message: discord.Message, context: EventContext):
        """Handle user message through the interaction manager"""
        try:
            # Get internal user ID
            discord_user_id = str(message.author.id)
            internal_user_id = get_user_id_by_identifier(discord_user_id)
            
            if not internal_user_id:
                # User not registered, send registration prompt
                await message.channel.send(
                    "Welcome! Please register first to use this bot. "
                    "Contact an administrator to get started."
                )
                return
            
            # Process message through interaction manager
            response = handle_user_message(internal_user_id, message.content, "discord")
            
            # Send response
            await self._send_response(message.channel, response)
            
        except Exception as e:
            logger.error(f"Error handling user message: {e}")
            await message.channel.send(
                "I'm having trouble processing your message right now. Please try again in a moment."
            )
    
    @handle_errors("sending Discord response")
    async def _send_response(self, channel: discord.TextChannel, response):
        """Send a response to a Discord channel"""
        try:
            # Create embed if rich_data is provided
            embed = None
            if hasattr(response, 'rich_data') and response.rich_data:
                from communication.communication_channels.base.rich_formatter import get_rich_formatter
                rich_formatter = get_rich_formatter('discord')
                embed = rich_formatter.create_embed(response.message, response.rich_data)
            
            # Create view with buttons if suggestions are provided
            view = None
            if hasattr(response, 'suggestions') and response.suggestions:
                from communication.communication_channels.base.rich_formatter import get_rich_formatter
                rich_formatter = get_rich_formatter('discord')
                view = rich_formatter.create_interactive_view(response.suggestions)
            
            # Send response with embed and/or view
            if embed and view:
                await channel.send(embed=embed, view=view)
            elif embed:
                await channel.send(embed=embed)
            elif view:
                await channel.send(response.message, view=view)
            else:
                await channel.send(response.message)
                
        except Exception as e:
            logger.error(f"Error sending response: {e}")
            await channel.send("I'm having trouble responding right now. Please try again.")
    
    @handle_errors("handling Discord reaction add event")
    async def on_reaction_add(self, reaction: discord.Reaction, user: discord.User):
        """Handle Discord reaction add event"""
        # Ignore bot reactions
        if user == self.bot.user:
            return
        
        context = EventContext(
            event_type=EventType.REACTION_ADD,
            user_id=str(user.id),
            channel_id=str(reaction.message.channel.id),
            guild_id=str(reaction.message.guild.id) if reaction.message.guild else None,
            message_id=str(reaction.message.id),
            data={
                "emoji": str(reaction.emoji),
                "count": reaction.count
            }
        )
        
        # Handle reaction (could be used for button interactions, etc.)
        logger.debug(f"Reaction added: {reaction.emoji} by {user.name}")
    
    @handle_errors("handling Discord reaction remove event")
    async def on_reaction_remove(self, reaction: discord.Reaction, user: discord.User):
        """Handle Discord reaction remove event"""
        # Ignore bot reactions
        if user == self.bot.user:
            return
        
        context = EventContext(
            event_type=EventType.REACTION_REMOVE,
            user_id=str(user.id),
            channel_id=str(reaction.message.channel.id),
            guild_id=str(reaction.message.guild.id) if reaction.message.guild else None,
            message_id=str(reaction.message.id),
            data={
                "emoji": str(reaction.emoji),
                "count": reaction.count
            }
        )
        
        logger.debug(f"Reaction removed: {reaction.emoji} by {user.name}")
    
    @handle_errors("handling Discord member join event")
    async def on_member_join(self, member: discord.Member):
        """Handle Discord member join event"""
        context = EventContext(
            event_type=EventType.MEMBER_JOIN,
            user_id=str(member.id),
            guild_id=str(member.guild.id),
            data={
                "member_name": member.name,
                "member_display_name": member.display_name,
                "joined_at": member.joined_at.isoformat() if member.joined_at else None
            }
        )
        
        logger.info(f"Member joined: {member.name} in {member.guild.name}")
    
    @handle_errors("handling Discord member leave event")
    async def on_member_remove(self, member: discord.Member):
        """Handle Discord member leave event"""
        context = EventContext(
            event_type=EventType.MEMBER_LEAVE,
            user_id=str(member.id),
            guild_id=str(member.guild.id),
            data={
                "member_name": member.name,
                "member_display_name": member.display_name
            }
        )
        
        logger.info(f"Member left: {member.name} from {member.guild.name}")
    
    @handle_errors("registering Discord events")
    def register_events(self, bot: discord.Client):
        """Register all event handlers with a Discord bot"""
        self.bot = bot
        
        # Register core events
        bot.event(self.on_ready)
        bot.event(self.on_disconnect)
        bot.event(self.on_error)
        bot.event(self.on_message)
        bot.event(self.on_reaction_add)
        bot.event(self.on_reaction_remove)
        bot.event(self.on_member_join)
        bot.event(self.on_member_remove)
        
        logger.info("Discord event handlers registered")

# Factory function to get Discord event handler
@handle_errors("getting Discord event handler")
def get_discord_event_handler(bot: discord.Client = None) -> DiscordEventHandler:
    """Get a Discord event handler instance"""
    return DiscordEventHandler(bot)
