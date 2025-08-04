# bot/discord_bot.py

import os
import discord
import asyncio
import threading
from discord.ext import commands
from typing import List, Dict, Any, Optional
import queue
import time
import socket
import random
import enum

from core.config import DISCORD_BOT_TOKEN
from core.logger import get_logger
from bot.conversation_manager import conversation_manager
from bot.base_channel import BaseChannel, ChannelType, ChannelStatus, ChannelConfig
from core.user_management import get_user_id_by_discord_user_id
from core.error_handling import (
    error_handler, DataError, FileOperationError, handle_errors
)

logger = get_logger(__name__)

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

class DiscordConnectionStatus(enum.Enum):
    """Detailed Discord connection status for better error reporting"""
    UNINITIALIZED = "uninitialized"
    INITIALIZING = "initializing"
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    DNS_FAILURE = "dns_failure"
    NETWORK_FAILURE = "network_failure"
    AUTH_FAILURE = "authentication_failure"
    RATE_LIMITED = "rate_limited"
    GATEWAY_ERROR = "gateway_error"
    UNKNOWN_ERROR = "unknown_error"

class DiscordBot(BaseChannel):
    def __init__(self, config: ChannelConfig = None):
        # Initialize BaseChannel
        """Initialize the object."""
        if config is None:
            config = ChannelConfig(
                name='discord',
                max_retries=5,  # Increased from 3
                retry_delay=2.0,  # Increased from 1.5
                backoff_multiplier=2.0
            )
        super().__init__(config)
        
        self.bot = None
        self.discord_thread = None
        self._loop = None
        self._starting = False
        self._command_queue = queue.Queue()  # For sending commands to Discord thread
        self._result_queue = queue.Queue()   # For getting results back
        self._reconnect_attempts = 0
        self._max_reconnect_attempts = 10
        self._last_reconnect_time = 0
        self._reconnect_cooldown = 60  # Increased to 60 seconds to reduce rapid reconnection attempts
        self._connection_status = DiscordConnectionStatus.UNINITIALIZED
        self._last_health_check = 0
        self._health_check_interval = 30  # Check health every 30 seconds
        self._detailed_error_info = {}

    @property
    def channel_type(self) -> ChannelType:
        """
        Get the channel type for Discord bot.
        
        Returns:
            ChannelType.ASYNC: Discord bot operates asynchronously
        """
        return ChannelType.ASYNC

    def _check_dns_resolution(self, hostname: str = "discord.com") -> bool:
        """Check DNS resolution for a hostname with fallback to alternative DNS servers"""
        # Alternative DNS servers to try if primary fails
        alternative_dns_servers = [
            "8.8.8.8",      # Google DNS
            "1.1.1.1",      # Cloudflare DNS
            "208.67.222.222", # OpenDNS
            "9.9.9.9"       # Quad9 DNS
        ]
        
        # Try primary DNS first (system default)
        try:
            socket.gethostbyname(hostname)
            return True
        except socket.gaierror as e:
            primary_error = {
                'hostname': hostname,
                'error_code': e.errno,
                'error_message': str(e),
                'timestamp': time.time(),
                'dns_server': 'system_default'
            }
            
            # Try alternative DNS servers
            for dns_server in alternative_dns_servers:
                try:
                    logger.info(f"Primary DNS failed for {hostname}, trying {dns_server}")
                    
                    # Create a custom resolver using the alternative DNS server
                    import dns.resolver
                    resolver = dns.resolver.Resolver()
                    resolver.nameservers = [dns_server]
                    resolver.timeout = 5
                    resolver.lifetime = 10
                    
                    # Try to resolve the hostname
                    answers = resolver.resolve(hostname, 'A')
                    if answers:
                        ip_address = str(answers[0])
                        logger.info(f"Successfully resolved {hostname} to {ip_address} using {dns_server}")
                        
                        # Update error info to show which DNS server worked
                        self._detailed_error_info['dns_error'] = {
                            'hostname': hostname,
                            'primary_error': primary_error,
                            'resolved_with': dns_server,
                            'resolved_ip': ip_address,
                            'timestamp': time.time()
                        }
                        return True
                        
                except Exception as alt_e:
                    logger.debug(f"Alternative DNS {dns_server} also failed: {alt_e}")
                    continue
            
            # All DNS servers failed
            self._detailed_error_info['dns_error'] = {
                'hostname': hostname,
                'primary_error': primary_error,
                'alternative_dns_failed': alternative_dns_servers,
                'timestamp': time.time()
            }
            logger.error(f"All DNS servers failed for {hostname}")
            return False

    def _check_network_connectivity(self, hostname: str = "discord.com", port: int = 443) -> bool:
        """Check if network connectivity is available to Discord servers with fallback endpoints"""
        # Discord endpoints to try in order of preference
        discord_endpoints = [
            ("discord.com", 443),
            ("gateway.discord.gg", 443),
            ("gateway-us-east1-b.discord.gg", 443),
            ("gateway-us-east1-c.discord.gg", 443),
            ("gateway-us-east1-d.discord.gg", 443),
            ("gateway-us-east1-a.discord.gg", 443)  # Try this last since it's been problematic
        ]
        
        # If a specific hostname was requested, try it first
        if hostname != "discord.com":
            discord_endpoints.insert(0, (hostname, port))
        
        for endpoint_hostname, endpoint_port in discord_endpoints:
            try:
                socket.create_connection((endpoint_hostname, endpoint_port), timeout=10)
                logger.info(f"Network connectivity successful to {endpoint_hostname}:{endpoint_port}")
                return True
            except (socket.gaierror, socket.timeout, OSError) as e:
                logger.debug(f"Network connectivity failed to {endpoint_hostname}:{endpoint_port} - {e}")
                continue
        
        # All endpoints failed
        self._detailed_error_info['network_error'] = {
            'hostname': hostname,
            'port': port,
            'endpoints_tried': discord_endpoints,
            'error_type': 'all_endpoints_failed',
            'error_message': f"All Discord endpoints failed connectivity test",
            'timestamp': time.time()
        }
        logger.error(f"All Discord endpoints failed network connectivity test")
        return False

    def _wait_for_network_recovery(self, max_wait: int = 300) -> bool:
        """Wait for network connectivity to recover with enhanced DNS and endpoint fallback."""
        logger.info("Waiting for network connectivity to recover with enhanced fallback...")
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            # Check DNS resolution with fallback servers
            if self._check_dns_resolution():
                logger.info("DNS resolution restored (may be using alternative DNS server)")
                # Then check actual connectivity with multiple endpoints
                if self._check_network_connectivity():
                    logger.info("Network connectivity restored (may be using alternative endpoint)")
                    return True
            
            # Wait before next check (shorter interval for faster recovery)
            time.sleep(5)
        
        logger.error("Network recovery timeout - connectivity not restored after trying all fallbacks")
        return False

    def _get_detailed_connection_status(self) -> Dict[str, Any]:
        """Get detailed connection status information"""
        status_info = {
            'connection_status': self._connection_status.value,
            'bot_initialized': self.bot is not None,
            'bot_ready': self.bot.is_ready() if self.bot else False,
            'bot_closed': self.bot.is_closed() if self.bot else True,
            'reconnect_attempts': self._reconnect_attempts,
            'max_reconnect_attempts': self._max_reconnect_attempts,
            'last_reconnect_time': self._last_reconnect_time,
            'dns_resolution': self._check_dns_resolution(),
            'network_connectivity': self._check_network_connectivity(),
            'detailed_errors': self._detailed_error_info.copy(),
            'timestamp': time.time()
        }
        
        # Add Discord-specific status if available
        if self.bot:
            try:
                status_info['latency'] = self.bot.latency
                status_info['guild_count'] = len(self.bot.guilds)
            except Exception as e:
                status_info['discord_status_error'] = str(e)
        
        return status_info

    def _update_connection_status(self, status: DiscordConnectionStatus, error_info: Dict[str, Any] = None):
        """Update connection status with detailed error information"""
        self._connection_status = status
        if error_info:
            self._detailed_error_info.update(error_info)
        
        # Log status change with details
        logger.info(f"Discord connection status changed to: {status.value}")
        if error_info:
            logger.debug(f"Connection error details: {error_info}")

    @handle_errors("initializing Discord bot", default_return=False)
    async def initialize(self) -> bool:
        """Initialize Discord bot"""
        # Prevent multiple simultaneous initializations
        if self._starting:
            logger.warning("Discord bot initialization already in progress")
            return False
        
        if self.get_status() == ChannelStatus.READY:
            logger.info("Discord bot already initialized")
            return True
        
        self._starting = True
        self._set_status(ChannelStatus.INITIALIZING)
        self._update_connection_status(DiscordConnectionStatus.INITIALIZING)
        
        try:
            if not DISCORD_BOT_TOKEN:
                error_msg = "DISCORD_BOT_TOKEN not configured"
                self._set_status(ChannelStatus.ERROR, error_msg)
                self._update_connection_status(DiscordConnectionStatus.AUTH_FAILURE, {
                    'error': 'Missing bot token',
                    'timestamp': time.time()
                })
                return False

            # Simplified initialization - let Discord.py handle connection issues
            logger.info("Initializing Discord bot...")

            # Create bot instance with enhanced connection settings
            self.bot = commands.Bot(
                command_prefix="!", 
                intents=intents,
                # Enhanced connection settings for better resilience
                max_messages=10000,  # Increase message cache
                heartbeat_timeout=120.0,  # Increased heartbeat timeout (was 60.0)
                guild_ready_timeout=30.0,  # Increased guild ready timeout (was 20.0)
                # Add connection retry settings
                max_retries=5,  # Maximum connection retries
                retry_delay=2.0,  # Base retry delay
            )
            
            # Register event handlers
            self._register_events()
            self._register_commands()
            
            # Start bot in a separate thread
            self.discord_thread = threading.Thread(
                target=self._run_bot_in_thread, 
                daemon=True
            )
            self.discord_thread.start()
            
            # Wait for the bot to be ready with longer timeout and better checking
            max_wait = 60  # Increased to 60 seconds for network issues (was 30)
            wait_interval = 0.5  # Check every 0.5 seconds
            total_waited = 0
            
            while total_waited < max_wait:
                await asyncio.sleep(wait_interval)
                total_waited += wait_interval
                
                if self.bot and self.bot.is_ready():
                    self._set_status(ChannelStatus.READY)
                    self._reconnect_attempts = 0  # Reset reconnect attempts on successful connection
                    self._starting = False  # Reset starting flag
                    self._update_connection_status(DiscordConnectionStatus.CONNECTED)
                    logger.info("Discord bot initialized successfully")
                    return True
                
                # Log progress for longer waits
                if total_waited % 10 == 0:  # Every 10 seconds (was 5)
                    logger.info(f"Waiting for Discord bot to be ready... ({total_waited}s/{max_wait}s)")
            
            # If we get here, the bot didn't become ready in time
            error_msg = f"Discord bot failed to become ready within {max_wait} seconds"
            self._set_status(ChannelStatus.ERROR, error_msg)
            self._update_connection_status(DiscordConnectionStatus.GATEWAY_ERROR, {
                'error': error_msg,
                'timeout_seconds': max_wait,
                'timestamp': time.time()
            })
            logger.error(error_msg)
            return False
            
        except Exception as e:
            logger.error(f"Error during Discord bot initialization: {e}")
            self._set_status(ChannelStatus.ERROR, f"Initialization error: {e}")
            self._update_connection_status(DiscordConnectionStatus.UNKNOWN_ERROR, {
                'error': str(e),
                'error_type': type(e).__name__,
                'timestamp': time.time()
            })
            return False
        finally:
            # Always reset the starting flag, even if initialization fails
            self._starting = False

    @handle_errors("running Discord bot in thread")
    def _run_bot_in_thread(self):
        """Run Discord bot in completely isolated thread with its own event loop"""
        # Create completely new event loop for this thread
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        
        # Start the bot and process commands
        self._loop.run_until_complete(self._bot_main_loop())

    @handle_errors("running Discord bot main loop")
    async def _bot_main_loop(self):
        """Main bot loop that handles both Discord and command queue"""
        # Start the Discord bot
        bot_task = asyncio.create_task(self.bot.start(DISCORD_BOT_TOKEN))
        
        # Process command queue
        while True:
            try:
                # Check for commands from main thread (non-blocking)
                try:
                    command, args = self._command_queue.get_nowait()
                    
                    if command == "send_message":
                        if len(args) == 2:
                            # Backward compatibility: just message
                            recipient, message = args
                            result = await self._send_message_internal(recipient, message)
                        elif len(args) == 4:
                            # New format: message with rich data and suggestions
                            recipient, message, rich_data, suggestions = args
                            result = await self._send_message_internal(recipient, message, rich_data, suggestions)
                        else:
                            logger.error(f"Invalid send_message args: {args}")
                            result = False
                        self._result_queue.put(result)
                    elif command == "stop":
                        logger.info("Discord bot received stop command")
                        break
                        
                except queue.Empty:
                    pass
                
                # Give Discord bot time to process
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Error in Discord command processing: {e}")

    @handle_errors("registering Discord events")
    def _register_events(self):
        """Register Discord event handlers"""
        @self.bot.event
        async def on_ready():
            logger.info(f"Discord Bot logged in as {self.bot.user}")
            print(f"Discord Bot is online as {self.bot.user}")
            # Reset reconnect attempts on successful connection
            self._reconnect_attempts = 0
            self._set_status(ChannelStatus.READY)
            self._update_connection_status(DiscordConnectionStatus.CONNECTED)
            logger.info("Discord bot is ready and connected")

        @self.bot.event
        async def on_disconnect():
            logger.warning("Discord bot disconnected")
            self._set_status(ChannelStatus.INITIALIZING)
            self._update_connection_status(DiscordConnectionStatus.DISCONNECTED)
            
            # Let Discord.py handle reconnection, but log our status
            logger.info("Discord.py will handle automatic reconnection")

        @self.bot.event
        async def on_error(event, *args, **kwargs):
            logger.error(f"Discord bot error in event {event}: {args} {kwargs}")
            
            # Check if this is a connection-related error
            error_str = str(args) + str(kwargs)
            if any(keyword in error_str.lower() for keyword in ['connection', 'dns', 'timeout', 'network']):
                logger.warning("Connection-related error detected - checking network status")
                if not self._check_dns_resolution():
                    logger.error("DNS resolution failed during error recovery")
                    self._update_connection_status(DiscordConnectionStatus.DNS_FAILURE)
                if not self._check_network_connectivity():
                    logger.error("Network connectivity failed during error recovery")
                    self._update_connection_status(DiscordConnectionStatus.NETWORK_FAILURE)
            
            # Let discord.py handle reconnection for most errors

        @self.bot.event
        async def on_message(message):
            # Don't respond to ourselves
            if message.author == self.bot.user:
                return

            # Let commands run if the message starts with "!"
            if message.content.startswith("!"):
                await self.bot.process_commands(message)
                return

            # Map Discord user ID to internal user ID
            discord_user_id = str(message.author.id)
            internal_user_id = get_user_id_by_discord_user_id(discord_user_id)
            
            if not internal_user_id:
                await message.channel.send(
                    f"I don't recognize you yet! Please register first using the MHM application. "
                    f"Your Discord ID is: {discord_user_id}"
                )
                return

            # Use the new interaction manager for enhanced user interactions
            try:
                from bot.interaction_manager import handle_user_message
                response = handle_user_message(internal_user_id, message.content, "discord")
                
                if response.message:
                    # Send the main message
                    await message.channel.send(response.message)
                    
                    # Add suggestions if provided
                    if response.suggestions:
                        suggestions_text = "\n💡 **Suggestions:**\n" + "\n".join([f"• {s}" for s in response.suggestions[:3]])
                        await message.channel.send(suggestions_text)
                        
            except Exception as e:
                logger.error(f"Error in enhanced interaction for user {internal_user_id}: {e}")
                # Fall back to existing conversation manager
                reply_text, completed = conversation_manager.handle_inbound_message(
                    internal_user_id, message.content
                )
                if reply_text:
                    await message.channel.send(reply_text)

    @handle_errors("registering Discord commands")
    def _register_commands(self):
        """Register Discord commands"""
        @self.bot.command(name="status")
        async def status(ctx):
            await ctx.send("I'm up and running! 🌟\n\nI can help you with:\n📋 **Tasks**: Create, list, complete, and manage tasks\n✅ **Check-ins**: Daily wellness check-ins\n👤 **Profile**: View and update your information\n\nJust start typing naturally - I'll understand what you want to do!\n\nTry: 'Create a task to call mom tomorrow' or 'Show my tasks'")

        @self.bot.command(name="dailycheckin")
        async def dailycheckin_cmd(ctx):
            """Manually start the daily check-in flow (normally prompted automatically)."""
            discord_user_id = str(ctx.author.id)
            internal_user_id = get_user_id_by_discord_user_id(discord_user_id)
            
            if not internal_user_id:
                await ctx.send(
                    f"I don't recognize you yet! Please register first using the MHM application. "
                    f"Your Discord ID is: {discord_user_id}"
                )
                return
                
            # Use new interaction system
            try:
                from bot.interaction_manager import handle_user_message
                response = handle_user_message(internal_user_id, "start checkin", "discord")
                await ctx.send(response.message)
            except Exception as e:
                logger.error(f"Error in check-in command: {e}")
                # Fall back to existing system
                reply_text, completed = conversation_manager.handle_inbound_message(
                    internal_user_id, "/dailycheckin"
                )
                await ctx.send(reply_text)

        @self.bot.command(name="cancel")
        async def cancel_cmd(ctx):
            """Cancel the current flow (like daily check-in)."""
            discord_user_id = str(ctx.author.id)
            internal_user_id = get_user_id_by_discord_user_id(discord_user_id)
            
            if not internal_user_id:
                await ctx.send("You don't have an active conversation to cancel.")
                return
                
            reply_text, completed = conversation_manager.handle_inbound_message(
                internal_user_id, "/cancel"
            )
            await ctx.send(reply_text)

        @self.bot.command(name="mhm_help")
        async def help_cmd(ctx):
            """Show help information."""
            discord_user_id = str(ctx.author.id)
            internal_user_id = get_user_id_by_discord_user_id(discord_user_id)
            
            if not internal_user_id:
                await ctx.send("I'm here to help! Try these commands:\n• !help - Show this help\n• !status - Show system status")
                return
            
            try:
                from bot.interaction_manager import handle_user_message
                response = handle_user_message(internal_user_id, "help", "discord")
                await ctx.send(response.message)
            except Exception as e:
                logger.error(f"Error in help command: {e}")
                await ctx.send("I'm here to help! Try typing naturally - I'll understand what you want to do.")

        @self.bot.command(name="tasks")
        async def tasks_cmd(ctx):
            """Show user's tasks."""
            discord_user_id = str(ctx.author.id)
            internal_user_id = get_user_id_by_discord_user_id(discord_user_id)
            
            if not internal_user_id:
                await ctx.send("Please register first to use task management features.")
                return
            
            try:
                from bot.interaction_manager import handle_user_message
                response = handle_user_message(internal_user_id, "show my tasks", "discord")
                await ctx.send(response.message)
            except Exception as e:
                logger.error(f"Error in tasks command: {e}")
                await ctx.send("I'm having trouble accessing your tasks right now. Please try again.")

    @handle_errors("shutting down Discord bot", default_return=False)
    async def shutdown(self) -> bool:
        """Shutdown Discord bot safely"""
        # Send stop command to Discord thread
        self._command_queue.put(("stop", None))
        
        # Wait for thread to finish
        if self.discord_thread and self.discord_thread.is_alive():
            self.discord_thread.join(timeout=10)
        
        self._set_status(ChannelStatus.STOPPED)
        logger.info("Discord bot shutdown successfully")
        return True

    @handle_errors("sending Discord message", default_return=False)
    async def send_message(self, recipient: str, message: str, **kwargs) -> bool:
        """Send message via Discord using thread-safe queue communication with rich response support"""
        if not self.is_ready():
            logger.error("Discord bot is not ready to send messages")
            return False

        # Check for rich response data
        rich_data = kwargs.get('rich_data', {})
        suggestions = kwargs.get('suggestions', [])
        
        # Send command to Discord thread with rich data
        self._command_queue.put(("send_message", (recipient, message, rich_data, suggestions)))
        
        # Wait for result with timeout
        timeout = 10  # 10 seconds
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                result = self._result_queue.get_nowait()
                return result
            except queue.Empty:
                time.sleep(0.1)
        
        logger.error(f"Timeout waiting for Discord message send to {recipient}")
        return False

    @handle_errors("sending Discord message internally", default_return=False)
    async def _send_message_internal(self, recipient: str, message: str, rich_data: Dict[str, Any] = None, suggestions: List[str] = None) -> bool:
        """Send message safely within async context with rich response support"""
        rich_data = rich_data or {}
        suggestions = suggestions or []
        
        # Create Discord embed if rich data is provided
        embed = None
        if rich_data:
            embed = self._create_discord_embed(message, rich_data)
        
        # Create action row with buttons if suggestions are provided
        action_row = None
        if suggestions:
            action_row = self._create_action_row(suggestions)
        
        # Try as a channel first
        try:
            channel_id = int(recipient)
            channel = self.bot.get_channel(channel_id)
            if channel:
                if embed and action_row:
                    await channel.send(embed=embed, components=[action_row])
                elif embed:
                    await channel.send(embed=embed)
                elif action_row:
                    await channel.send(message, components=[action_row])
                else:
                    await channel.send(message)
                logger.info(f"Message sent to Discord channel {recipient}")
                return True
        except (ValueError, TypeError):
            pass  # Not a valid channel ID
        
        # Try as a user DM
        try:
            user_id = int(recipient)
            user = self.bot.get_user(user_id)
            if not user:
                user = await self.bot.fetch_user(user_id)
            
            if user:
                if embed and action_row:
                    await user.send(embed=embed, components=[action_row])
                elif embed:
                    await user.send(embed=embed)
                elif action_row:
                    await user.send(message, components=[action_row])
                else:
                    await user.send(message)
                logger.info(f"DM sent to Discord user {recipient}")
                return True
        except (ValueError, TypeError):
            pass  # Not a valid user ID
        
        logger.error(f"Could not find Discord channel or user with ID {recipient}")
        return False
    
    def _create_discord_embed(self, message: str, rich_data: Dict[str, Any]) -> discord.Embed:
        """Create a Discord embed from rich data"""
        embed = discord.Embed()
        
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
        color_map = {
            'success': 0x00ff00,  # Green
            'error': 0xff0000,    # Red
            'warning': 0xffff00,  # Yellow
            'info': 0x0099ff,     # Blue
            'task': 0x9932cc,     # Purple
            'profile': 0xff6b35,  # Orange
            'schedule': 0x00bfff, # Deep Sky Blue
            'analytics': 0x32cd32 # Lime Green
        }
        
        embed_type = rich_data.get('type', 'info')
        embed.color = color_map.get(embed_type, 0x0099ff)
        
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
    
    def _create_action_row(self, suggestions: List[str]) -> discord.ActionRow:
        """Create a Discord action row with buttons from suggestions"""
        action_row = discord.ActionRow()
        
        # Limit to 5 buttons (Discord limit)
        for i, suggestion in enumerate(suggestions[:5]):
            # Create a button with a unique custom_id
            button = discord.Button(
                style=discord.ButtonStyle.primary,
                label=suggestion[:80],  # Discord button label limit
                custom_id=f"suggestion_{i}_{hash(suggestion) % 10000}"
            )
            action_row.add_item(button)
        
        return action_row

    @handle_errors("receiving Discord messages", default_return=[])
    async def receive_messages(self) -> List[Dict[str, Any]]:
        """Receive messages from Discord"""
        # Discord messages are handled via events, not polling
        # Return empty list as messages are processed via event handlers
        return []

    @handle_errors("performing Discord health check", default_return=False)
    async def health_check(self) -> bool:
        """Perform comprehensive health check on Discord bot with detailed status"""
        current_time = time.time()
        
        # Rate limit health checks to avoid spam
        if current_time - self._last_health_check < self._health_check_interval:
            return self._connection_status == DiscordConnectionStatus.CONNECTED
        
        self._last_health_check = current_time
        
        # Get detailed status information
        status_info = self._get_detailed_connection_status()
        
        # Check basic bot state
        if not self.bot:
            logger.warning("Discord bot not initialized")
            self._update_connection_status(DiscordConnectionStatus.UNINITIALIZED)
            return False
        
        if self.bot.is_closed():
            logger.warning("Discord bot is closed")
            self._update_connection_status(DiscordConnectionStatus.DISCONNECTED)
            return False
        
        if not self.bot.is_ready():
            logger.warning("Discord bot is not ready")
            self._update_connection_status(DiscordConnectionStatus.DISCONNECTED)
            return False
        
        # Enhanced network connectivity checks
        dns_ok = self._check_dns_resolution()
        network_ok = self._check_network_connectivity()
        
        if not dns_ok:
            logger.warning("DNS resolution failed during health check")
            self._update_connection_status(DiscordConnectionStatus.DNS_FAILURE)
            return False
        
        if not network_ok:
            logger.warning("Network connectivity failed during health check")
            self._update_connection_status(DiscordConnectionStatus.NETWORK_FAILURE)
            return False
        
        # Check Discord-specific metrics
        try:
            latency = self.bot.latency
            if latency > 1.0:  # High latency warning
                logger.warning(f"Discord latency is high: {latency:.2f}s")
                status_info['high_latency'] = True
                status_info['latency'] = latency
        except Exception as e:
            logger.warning(f"Could not check Discord latency: {e}")
        
        # Update status to connected if all checks pass
        self._update_connection_status(DiscordConnectionStatus.CONNECTED)
        logger.debug("Discord health check passed")
        return True

    def get_health_status(self) -> Dict[str, Any]:
        """Get comprehensive health status information"""
        return self._get_detailed_connection_status()

    def get_connection_status_summary(self) -> str:
        """Get a human-readable connection status summary"""
        status_info = self._get_detailed_connection_status()
        
        if status_info['connection_status'] == 'connected':
            latency = status_info.get('latency', 'unknown')
            guild_count = status_info.get('guild_count', 'unknown')
            return f"Connected (Latency: {latency}s, Guilds: {guild_count})"
        elif status_info['connection_status'] == 'dns_failure':
            error = status_info.get('detailed_errors', {}).get('dns_error', {})
            return f"DNS Failure: {error.get('error_message', 'Unknown DNS error')}"
        elif status_info['connection_status'] == 'network_failure':
            error = status_info.get('detailed_errors', {}).get('network_error', {})
            return f"Network Failure: {error.get('error_message', 'Unknown network error')}"
        elif status_info['connection_status'] == 'gateway_error':
            return "Gateway Error: Unable to connect to Discord servers"
        elif status_info['connection_status'] == 'disconnected':
            return "Disconnected: Bot is not ready or closed"
        else:
            return f"Status: {status_info['connection_status']}"

    def is_actually_connected(self) -> bool:
        """Check if the Discord bot is actually connected, regardless of initialization status"""
        if not self.bot:
            return False
        
        # Check if the bot is ready and not closed
        if self.bot.is_ready() and not self.bot.is_closed():
            # If we're actually connected but our status is wrong, fix it
            if self.get_status() != ChannelStatus.READY:
                logger.info("Discord bot is actually connected - fixing status")
                self._set_status(ChannelStatus.READY)
                self._starting = False
            return True
        
        return False

    @handle_errors("manually reconnecting Discord bot", default_return=False)
    async def manual_reconnect(self) -> bool:
        """Manually trigger a reconnection attempt"""
        if not self.bot:
            logger.error("Cannot reconnect - bot not initialized")
            return False
        
        logger.info("Manual reconnection requested")
        
        # Check network connectivity first
        if not self._check_dns_resolution():
            logger.error("DNS resolution failed - cannot reconnect")
            return False
        
        try:
            # Close the current connection
            await self.bot.close()
            
            # Wait a moment
            await asyncio.sleep(2)
            
            # Attempt to reconnect
            await self.bot.start(DISCORD_BOT_TOKEN)
            
            logger.info("Manual reconnection successful")
            return True
            
        except Exception as e:
            logger.error(f"Manual reconnection failed: {e}")
            return False

    # Legacy methods for backward compatibility
    @handle_errors("starting Discord bot")
    def start(self):
        """
        Legacy start method.
        
        Initializes the Discord bot if not already running.
        """
        if not self.is_initialized():
            logger.info("Starting Discord bot...")
            asyncio.run(self.initialize())
        else:
            logger.info("Discord bot already running")

    @handle_errors("stopping Discord bot")
    def stop(self):
        """
        Legacy stop method - thread-safe.
        
        Stops the Discord bot and cleans up resources.
        """
        logger.info("Stopping Discord bot...")
        
        # Send stop command to Discord thread
        try:
            self._command_queue.put(("stop", None))
        except Exception as e:
            logger.warning(f"Error sending stop command: {e}")
        
        # Wait for thread to finish
        if self.discord_thread and self.discord_thread.is_alive():
            self.discord_thread.join(timeout=10)
            if self.discord_thread.is_alive():
                logger.warning("Discord thread did not stop gracefully")
        
        # Stop the bot
        if self.bot:
            try:
                asyncio.run(self.shutdown())
            except Exception as e:
                logger.error(f"Error during Discord bot shutdown: {e}")
        
        logger.info("Discord bot stopped")

    def is_initialized(self):
        """
        Legacy method for backward compatibility.
        
        Returns:
            bool: True if the Discord bot is initialized and ready
        """
        return self.get_status() == ChannelStatus.READY

    # Keep the existing send_dm method for specific Discord functionality
    @handle_errors("sending Discord DM", default_return=False)
    async def send_dm(self, user_id: str, message: str) -> bool:
        """Send a direct message to a Discord user"""
        return await self.send_message(user_id, message)
