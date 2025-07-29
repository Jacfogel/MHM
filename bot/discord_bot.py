# bot/discord_bot.py

import os
import discord
import asyncio
import threading
from discord.ext import commands
from typing import List, Dict, Any
import queue
import time
import socket
import random

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

    @property
    def channel_type(self) -> ChannelType:
        """
        Get the channel type for Discord bot.
        
        Returns:
            ChannelType.ASYNC: Discord bot operates asynchronously
        """
        return ChannelType.ASYNC

    def _check_dns_resolution(self, hostname: str = "discord.com") -> bool:
        """Check if DNS resolution is working for a given hostname."""
        try:
            socket.gethostbyname(hostname)
            return True
        except socket.gaierror:
            return False

    def _check_network_connectivity(self, hostname: str = "discord.com", port: int = 443) -> bool:
        """Check if network connectivity is available to a specific host and port."""
        try:
            socket.create_connection((hostname, port), timeout=10)
            return True
        except (socket.gaierror, socket.timeout, OSError):
            return False

    def _wait_for_network_recovery(self, max_wait: int = 300) -> bool:
        """Wait for network connectivity to recover."""
        logger.info("Waiting for network connectivity to recover...")
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            # Check DNS resolution first
            if self._check_dns_resolution():
                logger.info("DNS resolution restored")
                # Then check actual connectivity
                if self._check_network_connectivity():
                    logger.info("Network connectivity restored")
                    return True
            
            # Wait before next check
            time.sleep(10)
        
        logger.error("Network connectivity did not recover within timeout")
        return False

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
        
        try:
            if not DISCORD_BOT_TOKEN:
                error_msg = "DISCORD_BOT_TOKEN not configured"
                self._set_status(ChannelStatus.ERROR, error_msg)
                return False

            # Enhanced network connectivity check
            logger.info("Performing enhanced network connectivity check...")
            
            # Check DNS resolution first
            if not self._check_dns_resolution():
                logger.warning("DNS resolution failed - checking alternative DNS servers")
                # Try alternative DNS servers
                alternative_hosts = ["8.8.8.8", "1.1.1.1", "208.67.222.222"]
                dns_working = False
                
                for dns_server in alternative_hosts:
                    try:
                        socket.create_connection((dns_server, 53), timeout=5)
                        dns_working = True
                        logger.info(f"Alternative DNS server {dns_server} is reachable")
                        break
                    except (socket.gaierror, socket.timeout, OSError):
                        continue
                
                if not dns_working:
                    logger.error("All DNS servers unreachable - network may be down")
                    error_msg = "Network connectivity issues detected"
                    self._set_status(ChannelStatus.ERROR, error_msg)
                    return False
            
            # Check Discord connectivity
            if not self._check_network_connectivity():
                logger.warning("Direct Discord connectivity failed - will attempt connection anyway")
                # Continue anyway as the check might be overly strict

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
                    logger.info("Discord bot initialized successfully")
                    return True
                
                # Log progress for longer waits
                if total_waited % 10 == 0:  # Every 10 seconds (was 5)
                    logger.info(f"Waiting for Discord bot to be ready... ({total_waited}s/{max_wait}s)")
            
            # If we get here, the bot didn't become ready in time
            error_msg = f"Discord bot failed to become ready within {max_wait} seconds"
            self._set_status(ChannelStatus.ERROR, error_msg)
            logger.error(error_msg)
            return False
            
        except Exception as e:
            logger.error(f"Error during Discord bot initialization: {e}")
            self._set_status(ChannelStatus.ERROR, f"Initialization error: {e}")
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
                        recipient, message = args
                        result = await self._send_message_internal(recipient, message)
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

        @self.bot.event
        async def on_disconnect():
            current_time = time.time()
            self._reconnect_attempts += 1
            
            logger.warning(f"Discord bot disconnected (attempt {self._reconnect_attempts}/{self._max_reconnect_attempts})")
            
            # Check if we should attempt custom reconnection
            if (self._reconnect_attempts <= self._max_reconnect_attempts and 
                current_time - self._last_reconnect_time > self._reconnect_cooldown):
                
                self._last_reconnect_time = current_time
                self._set_status(ChannelStatus.INITIALIZING)
                
                # Wait a bit before attempting reconnection
                await asyncio.sleep(random.uniform(1, 3))
                
                # Check network connectivity before attempting reconnection
                if not self._check_dns_resolution():
                    logger.error("DNS resolution failed during reconnection attempt")
                    if not self._wait_for_network_recovery(max_wait=60):
                        logger.error("Network recovery failed - will rely on discord.py auto-reconnection")
                        return
                
                logger.info("Network connectivity confirmed - discord.py will handle reconnection")
            else:
                if self._reconnect_attempts > self._max_reconnect_attempts:
                    logger.error(f"Maximum reconnection attempts ({self._max_reconnect_attempts}) exceeded")
                    self._set_status(ChannelStatus.ERROR, "Maximum reconnection attempts exceeded")
                elif current_time - self._last_reconnect_time <= self._reconnect_cooldown:
                    logger.debug("Reconnection attempt skipped due to cooldown period")

        @self.bot.event
        async def on_error(event, *args, **kwargs):
            logger.error(f"Discord bot error in event {event}: {args} {kwargs}")
            
            # Check if this is a connection-related error
            error_str = str(args) + str(kwargs)
            if any(keyword in error_str.lower() for keyword in ['connection', 'dns', 'timeout', 'network']):
                logger.warning("Connection-related error detected - checking network status")
                if not self._check_dns_resolution():
                    logger.error("DNS resolution failed during error recovery")
                    self._set_status(ChannelStatus.ERROR, "Network connectivity issues detected")
            
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

            # All messages now default to contextual chat unless in a specific flow
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
            await ctx.send("I'm up and running! Just send me any message and I'll respond with personalized, contextual chat.\n\nAvailable commands:\n• !dailycheckin - Start a check-in anytime\n• !cancel - Cancel current check-in\n• !status - Show this status")

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
        """Send message via Discord using thread-safe queue communication"""
        if not self.is_ready():
            logger.error("Discord bot is not ready to send messages")
            return False

        # Send command to Discord thread
        self._command_queue.put(("send_message", (recipient, message)))
        
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
    async def _send_message_internal(self, recipient: str, message: str) -> bool:
        """Send message safely within async context"""
        # Try as a channel first
        try:
            channel_id = int(recipient)
            channel = self.bot.get_channel(channel_id)
            if channel:
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
                await user.send(message)
                logger.info(f"DM sent to Discord user {recipient}")
                return True
        except (ValueError, TypeError):
            pass  # Not a valid user ID
        
        logger.error(f"Could not find Discord channel or user with ID {recipient}")
        return False

    @handle_errors("receiving Discord messages", default_return=[])
    async def receive_messages(self) -> List[Dict[str, Any]]:
        """Receive messages from Discord"""
        # Discord messages are handled via events, not polling
        # Return empty list as messages are processed via event handlers
        return []

    @handle_errors("performing Discord health check", default_return=False)
    async def health_check(self) -> bool:
        """Perform health check on Discord bot"""
        if not self.bot:
            logger.warning("Discord bot not initialized")
            return False
        
        if self.bot.is_closed():
            logger.warning("Discord bot is closed")
            return False
        
        if not self.bot.is_ready():
            logger.warning("Discord bot is not ready")
            return False
        
        # Enhanced network connectivity check
        if not self._check_dns_resolution():
            logger.warning("DNS resolution failed during health check")
            return False
        
        # Check actual network connectivity
        if not self._check_network_connectivity():
            logger.warning("Network connectivity failed during health check")
            return False
        
        return True

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
