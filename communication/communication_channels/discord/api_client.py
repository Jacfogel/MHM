# api_client.py

import discord
import asyncio
import time
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass

from core.logger import get_component_logger
from core.error_handling import handle_errors

# Route API client logs to Discord component
api_logger = get_component_logger('discord_api')
logger = api_logger

@dataclass
class MessageData:
    """Data structure for Discord messages"""
    content: str
    channel_id: str
    user_id: str
    message_id: str
    timestamp: float
    attachments: Optional[List[str]] = None
    embeds: Optional[List[Dict[str, Any]]] = None

@dataclass
class SendMessageOptions:
    """Options for sending messages"""
    rich_data: Optional[Dict[str, Any]] = None
    suggestions: Optional[List[str]] = None
    embed: Optional[discord.Embed] = None
    view: Optional[discord.ui.View] = None
    tts: bool = False
    delete_after: Optional[float] = None

class DiscordAPIClient:
    """Discord API client for handling Discord-specific operations"""
    
    @handle_errors("initializing Discord API client", default_return=None)
    def __init__(self, bot: discord.Client = None):
        """Initialize the Discord API client"""
        self.bot = bot
        self._rate_limit_info = {}
        self._last_request_time = 0
        self._min_request_interval = 0.1  # 100ms between requests
    
    @handle_errors("sending Discord message", default_return=False)
    async def send_message(self, recipient: str, message: str, options: SendMessageOptions = None) -> bool:
        """
        Send a message to a Discord channel or user
        
        Args:
            recipient: Channel ID or user ID
            message: Message content
            options: Additional send options
            
        Returns:
            True if message was sent successfully
        """
        if not self.bot:
            logger.error("Discord bot not available")
            return False
        
        if not options:
            options = SendMessageOptions()
        
        try:
            # Rate limiting
            await self._rate_limit_check()
            
            channel = await self._get_channel_or_user(recipient)
            if not channel:
                logger.error(f"Could not find Discord channel or user with ID {recipient}")
                return False
            
            # Prepare send kwargs
            send_kwargs: Dict[str, Any] = {"content": message}
            
            if options.embed:
                send_kwargs["embed"] = options.embed
            if options.view:
                send_kwargs["view"] = options.view
            if options.tts:
                send_kwargs["tts"] = options.tts
            if options.delete_after:
                send_kwargs["delete_after"] = options.delete_after
            
            # Send the message
            await channel.send(**send_kwargs)
            logger.debug(f"Message sent to {recipient}")
            return True
            
        except discord.Forbidden:
            logger.error(f"Bot lacks permissions to send messages to {recipient}")
            return False
        except discord.HTTPException as e:
            logger.error(f"HTTP error sending message to {recipient}: {e}")
            return False
        except Exception as e:
            logger.error(f"Error sending message to {recipient}: {e}")
            return False
    
    @handle_errors("sending Discord DM", default_return=False)
    async def send_dm(self, user_id: str, message: str, options: SendMessageOptions = None) -> bool:
        """
        Send a direct message to a Discord user
        
        Args:
            user_id: Discord user ID
            message: Message content
            options: Additional send options
            
        Returns:
            True if DM was sent successfully
        """
        if not self.bot:
            logger.error("Discord bot not available")
            return False
        
        try:
            # Rate limiting
            await self._rate_limit_check()
            
            user = self.bot.get_user(int(user_id))
            if not user:
                logger.error(f"Could not find Discord user with ID {user_id}")
                return False
            
            # Create DM channel
            dm_channel = user.dm_channel
            if not dm_channel:
                dm_channel = await user.create_dm()
            
            # Send the message
            send_kwargs: Dict[str, Any] = {"content": message}
            if options and options.embed:
                send_kwargs["embed"] = options.embed
            if options and options.view:
                send_kwargs["view"] = options.view
            
            await dm_channel.send(**send_kwargs)
            logger.debug(f"DM sent to user {user_id}")
            return True
            
        except discord.Forbidden:
            logger.error(f"Cannot send DM to user {user_id} - user has DMs disabled")
            return False
        except Exception as e:
            logger.error(f"Error sending DM to user {user_id}: {e}")
            return False
    
    @handle_errors("getting Discord channel or user", default_return=None)
    async def _get_channel_or_user(self, recipient: str) -> Optional[Union[discord.TextChannel, discord.User]]:
        """Get a Discord channel or user by ID"""
        if not self.bot:
            return None
        
        try:
            # Try to get as channel first
            channel = self.bot.get_channel(int(recipient))
            if channel and isinstance(channel, discord.TextChannel):
                return channel
            
            user = self.bot.get_user(int(recipient))
            if user:
                return user
            
            return None
            
        except (ValueError, TypeError):
            logger.error(f"Invalid recipient ID format: {recipient}")
            return None
        except Exception as e:
            logger.error(f"Error getting channel or user {recipient}: {e}")
            return None
    
    @handle_errors("checking rate limits", default_return=None)
    async def _rate_limit_check(self):
        """Check and enforce rate limits"""
        current_time = time.time()
        time_since_last = current_time - self._last_request_time
        
        if time_since_last < self._min_request_interval:
            sleep_time = self._min_request_interval - time_since_last
            await asyncio.sleep(sleep_time)
        
        self._last_request_time = time.time()
    
    @handle_errors("getting Discord guilds", default_return=[])
    async def get_guilds(self) -> List[discord.Guild]:
        """Get all guilds the bot is in"""
        if not self.bot:
            return []
        
        return list(self.bot.guilds)
    
    @handle_errors("getting Discord channels", default_return=[])
    async def get_channels(self, guild_id: Optional[str] = None) -> List[discord.TextChannel]:
        """Get text channels from a guild or all guilds"""
        if not self.bot:
            return []
        
        channels = []
        
        if guild_id:
            guild = self.bot.get_guild(int(guild_id))
            if guild:
                channels.extend([c for c in guild.text_channels])
        else:
            for guild in self.bot.guilds:
                channels.extend([c for c in guild.text_channels])
        
        return channels
    
    @handle_errors("getting Discord users", default_return=[])
    async def get_users(self, guild_id: Optional[str] = None) -> List[discord.Member]:
        """Get users from a guild or all guilds"""
        if not self.bot:
            return []
        
        users = []
        
        if guild_id:
            guild = self.bot.get_guild(int(guild_id))
            if guild:
                users.extend(list(guild.members))
        else:
            for guild in self.bot.guilds:
                users.extend(list(guild.members))
        
        return users
    
    @handle_errors("checking bot permissions", default_return=False)
    async def check_permissions(self, channel_id: str, permissions: List[str]) -> Dict[str, bool]:
        """Check bot permissions in a channel"""
        if not self.bot:
            return {perm: False for perm in permissions}
        
        try:
            channel = self.bot.get_channel(int(channel_id))
            if not channel:
                return {perm: False for perm in permissions}
            
            bot_member = channel.guild.get_member(self.bot.user.id)
            if not bot_member:
                return {perm: False for perm in permissions}
            
            permissions_dict = {}
            for perm in permissions:
                permissions_dict[perm] = getattr(bot_member.guild_permissions, perm, False)
            
            return permissions_dict
            
        except Exception as e:
            logger.error(f"Error checking permissions in channel {channel_id}: {e}")
            return {perm: False for perm in permissions}
    
    @handle_errors("checking Discord connection status", default_return=False)
    def is_connected(self) -> bool:
        """Check if the bot is connected to Discord"""
        return self.bot and not self.bot.is_closed()
    
    @handle_errors("getting Discord connection latency", default_return=0.0)
    def get_connection_latency(self) -> float:
        """Get the bot's connection latency"""
        if not self.bot:
            return float('inf')
        
        return self.bot.latency

# Factory function to get Discord API client
@handle_errors("getting Discord API client", default_return=None)
def get_discord_api_client(bot: discord.Client = None) -> DiscordAPIClient:
    """Get a Discord API client instance"""
    return DiscordAPIClient(bot)
