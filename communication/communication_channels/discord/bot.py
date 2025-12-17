# communication/communication_channels/discord/bot.py

import discord
from discord import app_commands
import asyncio
import threading
from discord.ext import commands
from typing import List, Dict, Any
import queue
import time
import socket
import enum
import contextlib
import subprocess
import shutil
import os
import psutil

from core.config import DISCORD_BOT_TOKEN, DISCORD_APPLICATION_ID
from core.logger import get_component_logger
from communication.communication_channels.base.base_channel import BaseChannel, ChannelType, ChannelStatus, ChannelConfig
from core.user_management import get_user_id_by_identifier
from core.error_handling import handle_errors

# Route all Discord module logs to the Discord component logger so they appear in logs/discord.log
discord_logger = get_component_logger('discord')
logger = discord_logger

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
    @handle_errors("initializing Discord bot", default_return=None)
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
        # Idempotency flags
        self._events_registered = False
        self._commands_registered = False
        # Session management
        self._sessions_to_cleanup = []
        # Task management for proper cleanup
        self._sync_task = None
        # Webhook server for receiving installation events
        self._webhook_server = None
        # Ngrok process for webhook tunneling (auto-launched if enabled)
        self._ngrok_process = None
        self._ngrok_pid = None  # Store PID separately in case process reference is lost
        self._on_ready_fired = False  # Track if on_ready() event has fired
        # Ensure BaseChannel logs for this instance also go to the Discord component log
        self.logger = discord_logger

    @property
    @handle_errors("getting Discord channel type", default_return=ChannelType.ASYNC)
    def channel_type(self) -> ChannelType:
        """
        Get the channel type for Discord bot.
        
        Returns:
            ChannelType.ASYNC: Discord bot operates asynchronously
        """
        return ChannelType.ASYNC

    @handle_errors("checking DNS resolution", default_return=False)
    def _check_dns_resolution(self, hostname: str = "discord.com") -> bool:
        """
        Check DNS resolution with validation.
        
        Returns:
            bool: True if successful, False if failed
        """
        # Validate hostname
        if not hostname or not isinstance(hostname, str):
            logger.error(f"Invalid hostname: {hostname}")
            return False
            
        if not hostname.strip():
            logger.error("Empty hostname provided")
            return False
        """Check DNS resolution for a hostname with enhanced fallback and error reporting"""
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
            # Only log DNS success occasionally to reduce log noise
            if hasattr(self, '_dns_success_count'):
                self._dns_success_count += 1
            else:
                self._dns_success_count = 1
            
            # Log DNS success every 60th check to reduce noise
            if self._dns_success_count % 60 == 0:
                logger.debug(f"Primary DNS resolution successful for {hostname} (check #{self._dns_success_count})")
            return True
        except socket.gaierror as e:
            primary_error = {
                'hostname': hostname,
                'error_code': e.errno,
                'error_message': str(e),
                'timestamp': time.time(),
                'dns_server': 'system_default'
            }
            
            logger.warning(f"Primary DNS failed for {hostname}: {e}")
            
            # Try alternative DNS servers
            for dns_server in alternative_dns_servers:
                try:
                    logger.info(f"Trying alternative DNS server {dns_server} for {hostname}")
                    
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
            self._connection_status = DiscordConnectionStatus.DNS_FAILURE
            return False

    @handle_errors("checking network connectivity", default_return=False)
    def _check_network_connectivity(self, hostname: str = "discord.com", port: int = 443) -> bool:
        """
        Check network connectivity with validation.
        
        Returns:
            bool: True if successful, False if failed
        """
        # Validate hostname
        if not hostname or not isinstance(hostname, str):
            logger.error(f"Invalid hostname: {hostname}")
            return False
            
        if not hostname.strip():
            logger.error("Empty hostname provided")
            return False
            
        # Validate port
        if not isinstance(port, int) or port < 1 or port > 65535:
            logger.error(f"Invalid port: {port}")
            return False
        """Check if network connectivity is available to Discord servers with enhanced fallback and timeout handling"""
        # Discord endpoints to try in order of preference
        discord_endpoints = [
            ("discord.com", 443),
            ("gateway.discord.gg", 443),
            ("gateway-us-east1-b.discord.gg", 443),
            ("gateway-us-east1-c.discord.gg", 443),
            ("gateway-us-east1-d.discord.gg", 443),
            ("gateway-us-east1-a.discord.gg", 443)
        ]
        
        # If a specific hostname was requested, try it first
        if hostname != "discord.com":
            discord_endpoints.insert(0, (hostname, port))
        
        for endpoint_hostname, endpoint_port in discord_endpoints:
            try:
                # Use a shorter timeout for faster failure detection
                socket.create_connection((endpoint_hostname, endpoint_port), timeout=5)
                # Only log network success occasionally to reduce log noise
                if hasattr(self, '_network_success_count'):
                    self._network_success_count += 1
                else:
                    self._network_success_count = 1
                
                # Log network success every 60th check to reduce noise
                if self._network_success_count % 60 == 0:
                    logger.debug(f"Network connectivity successful to {endpoint_hostname}:{endpoint_port} (check #{self._network_success_count})")
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
        self._connection_status = DiscordConnectionStatus.NETWORK_FAILURE
        return False

    @handle_errors("waiting for network recovery", default_return=False)
    def _wait_for_network_recovery(self, max_wait: int = 300) -> bool:
        """
        Wait for network recovery with validation.
        
        Returns:
            bool: True if successful, False if failed
        """
        # Validate max_wait
        if not isinstance(max_wait, int) or max_wait < 0:
            logger.error(f"Invalid max_wait: {max_wait}")
            return False
        """Wait for network connectivity to recover with enhanced monitoring and early exit"""
        logger.info(f"Waiting for network connectivity to recover (max {max_wait}s)...")
        start_time = time.time()
        check_interval = 10  # Check every 10 seconds
        
        while time.time() - start_time < max_wait:
            # Check DNS resolution first
            if self._check_dns_resolution():
                # Then check network connectivity
                if self._check_network_connectivity():
                    logger.info("Network connectivity recovered successfully")
                    self._connection_status = DiscordConnectionStatus.INITIALIZING
                    return True
            
            # Wait before next check
            time.sleep(check_interval)
        
        logger.error(f"Network connectivity did not recover within {max_wait} seconds")
        return False

    @contextlib.asynccontextmanager
    @handle_errors("cleaning up session context", default_return=None)
    async def shutdown__session_cleanup_context(self):
        """Context manager for proper session cleanup with timeout handling"""
        sessions_to_cleanup = []
        try:
            yield sessions_to_cleanup
        finally:
            # Clean up all sessions with timeout
            cleanup_tasks = []
            for session in sessions_to_cleanup:
                if hasattr(session, 'close') and not session.closed:
                    cleanup_tasks.append(self._cleanup_session_with_timeout(session))
            
            if cleanup_tasks:
                try:
                    await asyncio.wait_for(
                        asyncio.gather(*cleanup_tasks, return_exceptions=True),
                        timeout=10.0
                    )
                    logger.info(f"Successfully cleaned up {len(cleanup_tasks)} sessions")
                except asyncio.TimeoutError:
                    logger.warning("Session cleanup timed out, some sessions may not be properly closed")
                except Exception as e:
                    logger.error(f"Error during session cleanup: {e}")

    @handle_errors("cleaning up session with timeout", user_friendly=False, default_return=False)
    async def _cleanup_session_with_timeout(self, session) -> bool:
        """Clean up a single session with timeout handling"""
        try:
            await asyncio.wait_for(session.close(), timeout=5.0)
            return True
        except asyncio.TimeoutError:
            logger.warning(f"Session cleanup timed out for {type(session).__name__}")
            return False
        except Exception as e:
            logger.debug(f"Error closing session {type(session).__name__}: {e}")
            return False

    @handle_errors("cleaning up event loop safely", user_friendly=False, default_return=False)
    async def _cleanup_event_loop_safely(self, loop: asyncio.AbstractEventLoop) -> bool:
        """Safely clean up event loop with proper task cancellation and error handling"""
        if not loop or loop.is_closed():
            return True
        
        # Get all tasks in this specific loop
        tasks = [task for task in asyncio.all_tasks(loop) if not task.done()]
        
        if not tasks:
            logger.debug("No pending tasks to cancel")
            return True
        
        logger.info(f"Cancelling {len(tasks)} pending tasks")
        
        # Cancel all tasks
        for task in tasks:
            if not task.done():
                task.cancel()
        
        # Wait for tasks to be cancelled with timeout
        try:
            await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=5.0
            )
            logger.info("All tasks cancelled successfully")
        except asyncio.TimeoutError:
            logger.warning("Task cancellation timed out, some tasks may still be running")
        
        # Close the loop if it's not already closed
        if not loop.is_closed():
            loop.close()
            logger.info("Event loop closed successfully")
        
        return True

    @handle_errors("cleaning up aiohttp sessions", user_friendly=False, default_return=False)
    async def _cleanup_aiohttp_sessions(self) -> bool:
        """Clean up any remaining aiohttp sessions to prevent warnings"""
        # Get current event loop
        loop = asyncio.get_running_loop()
        
        # Find and close any aiohttp sessions
        import gc
        import aiohttp
        
        # Force garbage collection to find any orphaned sessions
        gc.collect()
        
        # Look for aiohttp ClientSession objects in memory
        for obj in gc.get_objects():
            if isinstance(obj, aiohttp.ClientSession) and not obj.closed:
                try:
                    await obj.close()
                    logger.debug("Closed orphaned aiohttp session")
                except Exception as e:
                    logger.debug(f"Error closing aiohttp session: {e}")
        
        return True

    @handle_errors("getting detailed connection status", default_return={})
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

    @handle_errors("updating connection status", default_return=None)
    def _shared__update_connection_status(self, status: DiscordConnectionStatus, error_info: Dict[str, Any] = None):
        """Update connection status with detailed error information"""
        # Only log if status actually changed
        if self._connection_status != status:
            self._connection_status = status
            if error_info:
                self._detailed_error_info.update(error_info)
            
            # Log status change with details (single log message)
            logger.info(f"Discord connection status changed to: {status.value}")
            if error_info:
                logger.debug(f"Connection error details: {error_info}")
        else:
            # Status didn't change, just update error info if provided
            if error_info:
                self._detailed_error_info.update(error_info)

    @handle_errors("checking network health", default_return=False)
    def _check_network_health(self) -> bool:
        """Comprehensive network health check with detailed reporting"""
        logger.debug("Performing network health check...")
        
        # Check DNS resolution first
        if not self._check_dns_resolution():
            logger.warning("DNS resolution failed during health check")
            return False
        
        # Check network connectivity
        if not self._check_network_connectivity():
            logger.warning("Network connectivity failed during health check")
            return False
        
        # If we have a bot instance, check its health
        if self.bot and hasattr(self.bot, 'latency'):
            try:
                latency = self.bot.latency
                if latency > 1.0:  # More than 1 second latency
                    logger.warning(f"High Discord latency detected: {latency:.3f}s")
                    return False
                logger.debug(f"Discord latency: {latency:.3f}s")
            except Exception as e:
                logger.debug(f"Could not check Discord latency: {e}")
        
        logger.debug("Network health check passed")
        return True

    @handle_errors("checking if should attempt reconnection", default_return=False)
    def _should_attempt_reconnection(self) -> bool:
        """Determine if reconnection should be attempted based on various factors"""
        current_time = time.time()
        
        # Check if we've exceeded max attempts
        if self._reconnect_attempts >= self._max_reconnect_attempts:
            logger.warning(f"Maximum reconnection attempts ({self._max_reconnect_attempts}) exceeded")
            return False
        
        # Check cooldown period
        if current_time - self._last_reconnect_time < self._reconnect_cooldown:
            remaining_cooldown = self._reconnect_cooldown - (current_time - self._last_reconnect_time)
            logger.debug(f"Reconnection cooldown active, {remaining_cooldown:.1f}s remaining")
            return False
        
        # Check network health before attempting reconnection
        if not self._check_network_health():
            logger.info("Network health check failed, skipping reconnection attempt")
            return False
        
        return True

    @handle_errors("initializing Discord bot", default_return=False)
    async def initialize(self) -> bool:
        """
        Initialize Discord bot with validation.
        
        Returns:
            bool: True if successful, False if failed
        """
        """Initialize Discord bot with enhanced network resilience"""
        if self._starting:
            logger.info("Discord bot already initializing")
            return False
        
        if self.is_ready():
            logger.info("Discord bot already initialized")
            return True
        
        self._starting = True
        self._set_status(ChannelStatus.INITIALIZING)
        self._shared__update_connection_status(DiscordConnectionStatus.INITIALIZING)
        
        try:
            # Pre-flight network check
            logger.info("Performing pre-flight network check...")
            if not self._check_network_health():
                logger.warning("Pre-flight network check failed, but continuing with initialization")
                # Don't fail immediately, let Discord.py handle the connection
            
            # Create bot instance with automatic command processing disabled
            self.bot = commands.Bot(
                command_prefix='!',
                intents=intents,
                application_id=DISCORD_APPLICATION_ID,
                help_command=None  # Disable default help command
            )
            
            # Register events and commands
            if not self._events_registered:
                self.initialize__register_events()
            
            if not self._commands_registered:
                self.initialize__register_commands()
            
            # Start bot in a separate thread
            self.discord_thread = threading.Thread(
                target=self.initialize__run_bot_in_thread, 
                daemon=True
            )
            self.discord_thread.start()
            
            # Wait for the bot to be ready with enhanced monitoring
            max_wait = 60  # 60 seconds for network issues
            wait_interval = 0.5  # Check every 0.5 seconds
            total_waited = 0
            
            while total_waited < max_wait:
                await asyncio.sleep(wait_interval)
                total_waited += wait_interval
                
                if self.bot and self.bot.is_ready():
                    self._set_status(ChannelStatus.READY)
                    self._reconnect_attempts = 0  # Reset reconnect attempts on successful connection
                    self._starting = False  # Reset starting flag
                    self._shared__update_connection_status(DiscordConnectionStatus.CONNECTED)
                    logger.info("Discord bot initialized successfully")
                    
                    # If on_ready() hasn't fired yet (or won't fire), manually trigger webhook server startup
                    # This can happen if the bot becomes ready before on_ready() fires, or if on_ready() fails silently
                    # Wait a moment to see if on_ready() fires naturally
                    await asyncio.sleep(0.5)  # Give on_ready() a chance to fire
                    
                    if hasattr(self, '_on_ready_handler') and self._on_ready_handler:
                        if not self._on_ready_fired:
                            discord_logger.warning("Bot is ready but on_ready() hasn't fired - manually triggering webhook server startup")
                            try:
                                # Only create task if loop is running and not closed
                                if hasattr(self.bot, 'loop') and self.bot.loop and not self.bot.loop.is_closed():
                                    self.bot.loop.create_task(self._on_ready_handler())
                                else:
                                    discord_logger.debug("Bot loop not available for manual on_ready trigger")
                            except Exception as e:
                                discord_logger.warning(f"Failed to manually trigger webhook server startup: {e}", exc_info=True)
                    
                    return True
                
                # Log progress for longer waits
                if total_waited % 10 == 0:  # Every 10 seconds
                    logger.info(f"Waiting for Discord bot to be ready... ({total_waited}s/{max_wait}s)")
                    
                    # Perform periodic network health check
                    if total_waited % 20 == 0:  # Every 20 seconds
                        if not self._check_network_health():
                            logger.warning("Network health check failed during initialization")
            
            # If we get here, the bot didn't become ready in time
            error_msg = f"Discord bot failed to become ready within {max_wait} seconds"
            self._set_status(ChannelStatus.ERROR, error_msg)
            self._shared__update_connection_status(DiscordConnectionStatus.GATEWAY_ERROR, {
                'error': error_msg,
                'timeout_seconds': max_wait,
                'timestamp': time.time()
            })
            logger.error(error_msg)
            return False
        finally:
            # Always reset the starting flag, even if initialization fails
            self._starting = False

    @handle_errors("running Discord bot in thread")
    def initialize__run_bot_in_thread(self):
        """Run Discord bot in completely isolated thread with its own event loop"""
        # Create completely new event loop for this thread
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        
        # Start the bot and process commands
        self._loop.run_until_complete(self.initialize__bot_main_loop())

    @handle_errors("running Discord bot main loop")
    async def initialize__bot_main_loop(self):
        """Main bot loop that handles both Discord and command queue"""
        # Start the Discord bot
        bot_task = asyncio.create_task(self.bot.start(DISCORD_BOT_TOKEN))
        
        # Process command queue concurrently with bot
        command_task = asyncio.create_task(self.initialize__process_command_queue())
        
        try:
            # Wait for either the bot to finish or a stop command
            done, pending = await asyncio.wait(
                [bot_task, command_task],
                return_when=asyncio.FIRST_COMPLETED
            )
            
            # Cancel any remaining tasks
            for task in pending:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        finally:
            # Ensure bot is properly closed
            if not self.bot.is_closed():
                await self.bot.close()
            
            # Clean up HTTP session to prevent "Unclosed client session" errors
            try:
                if hasattr(self.bot, '_HTTP') and self.bot._HTTP:
                    if hasattr(self.bot._HTTP, '_HTTPClient') and self.bot._HTTP._HTTPClient:
                        if hasattr(self.bot._HTTP._HTTPClient, '_session') and self.bot._HTTP._HTTPClient._session:
                            await self.bot._HTTP._HTTPClient._session.close()
                            logger.info("Discord bot HTTP session closed in main loop")
            except Exception as e:
                logger.debug(f"Error closing HTTP session in main loop (may already be closed): {e}")

    @handle_errors("processing Discord command queue")
    async def initialize__process_command_queue(self):
        """Process command queue without blocking Discord bot heartbeat"""
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
                        elif len(args) == 5:
                            # New format: message with rich data, suggestions, and custom view
                            recipient, message, rich_data, suggestions, custom_view = args
                            result = await self._send_message_internal(recipient, message, rich_data, suggestions, custom_view)
                        else:
                            logger.error(f"Invalid send_message args: {args}")
                            result = False
                        self._result_queue.put(result)
                    elif command == "stop":
                        logger.info("Discord bot received stop command")
                        return  # Exit the command processing loop
                        
                except queue.Empty:
                    pass
                
                # Give Discord bot time to process heartbeat and other events
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Error in Discord command processing: {e}")
                # Continue processing even if one command fails
                await asyncio.sleep(0.1)

    @handle_errors("registering Discord events")
    def initialize__register_events(self):
        """Register Discord event handlers"""
        if self._events_registered or not self.bot:
            return
        
        # Create the on_ready handler function
        async def _on_ready_internal():
            # Prevent duplicate execution if already called
            if self._on_ready_fired:
                return
            
            self._on_ready_fired = True
            try:
                # Single consolidated log message
                logger.info(f"Discord Bot logged in as {self.bot.user}")
                print(f"Discord Bot is online as {self.bot.user}")
                
                # Reset reconnect attempts on successful connection
                self._reconnect_attempts = 0
                self._set_status(ChannelStatus.READY)
                self._shared__update_connection_status(DiscordConnectionStatus.CONNECTED)

                # Sync application (slash) commands
                @handle_errors("syncing Discord application commands", user_friendly=False, default_return=None)
                async def _sync_app_cmds():
                    await self.bot.tree.sync()
                    logger.info("Discord application commands synced")
                # Schedule on the bot's loop to ensure proper task context
                # Store task reference for proper cleanup during shutdown
                self._sync_task = self.bot.loop.create_task(_sync_app_cmds())
                
                # Check for new users who have authorized the app (can now DM us)
                # This runs periodically to catch users who authorized while bot was offline
                @handle_errors("checking for new authorized Discord users", user_friendly=False, default_return=None)
                async def _check_new_authorized_users():
                    from communication.communication_channels.discord.welcome_handler import (
                        has_been_welcomed,
                        mark_as_welcomed,
                        get_welcome_message
                    )
                    
                    # Get all users who can DM us (have authorized the app)
                    # Note: We can't directly query this, but we can check when they first DM us
                    # This is handled in on_message for DMs
                    discord_logger.debug("Bot ready - will welcome users on Discord app authorization (via webhook) or first interaction")
                
                # Schedule the check (non-blocking)
                self.bot.loop.create_task(_check_new_authorized_users())
                
                # Start webhook server for receiving installation events
                try:
                    from communication.communication_channels.discord.webhook_server import WebhookServer
                    from core.config import DISCORD_WEBHOOK_PORT, DISCORD_AUTO_NGROK
                    
                    # Auto-launch ngrok if enabled
                    if DISCORD_AUTO_NGROK:
                        self._start_ngrok_tunnel(DISCORD_WEBHOOK_PORT)
                    
                    self._webhook_server = WebhookServer(port=DISCORD_WEBHOOK_PORT, bot_instance=self)
                    if self._webhook_server.start():
                        # Log message is handled by WebhookServer.start() - don't duplicate
                        if self._ngrok_process:
                            discord_logger.info(f"ngrok tunnel active - check ngrok web interface at http://127.0.0.1:4040 for public URL")
                        else:
                            # Check if ngrok is running externally
                            ngrok_running = False
                            try:
                                for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                                    try:
                                        if not proc.info['name']:
                                            continue
                                        proc_name = proc.info['name'].lower()
                                        if 'ngrok' in proc_name:
                                            cmdline = proc.info.get('cmdline', [])
                                            if cmdline and 'http' in ' '.join(cmdline).lower():
                                                if proc.is_running():
                                                    ngrok_running = True
                                                    discord_logger.info(f"ngrok tunnel detected (external) - check http://127.0.0.1:4040 for public URL")
                                                    break
                                    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                                        continue
                            except Exception:
                                pass
                            
                            if not ngrok_running:
                                discord_logger.info(f"Webhook server ready on port {DISCORD_WEBHOOK_PORT} - configure webhook URL in Discord Developer Portal")
                    else:
                        discord_logger.warning("Failed to start Discord webhook server")
                except Exception as e:
                    discord_logger.warning(f"Could not start webhook server: {e}")
                    # Non-critical - bot will still work, just won't receive installation events
            except Exception as e:
                discord_logger.error(f"Exception in on_ready(): {type(e).__name__}: {e}", exc_info=True)
                raise  # Re-raise to let @handle_errors decorator handle it
        
        # Wrap with error handling decorator
        @self.bot.event
        @handle_errors("Discord bot ready event", user_friendly=False, default_return=None)
        async def on_ready():
            await _on_ready_internal()

        @self.bot.event
        @handle_errors("handling Discord disconnect event", default_return=None)
        async def on_disconnect():
            logger.warning("Discord bot disconnected")
            # Use component logger for Discord disconnection events
            discord_logger.warning("Discord bot disconnected", 
                                 bot_name=str(self.bot.user) if self.bot.user else "unknown",
                                 reconnect_attempts=self._reconnect_attempts)
            # Don't change status to INITIALIZING - keep it as READY or ERROR
            # This prevents the bot from getting stuck in INITIALIZING state
            current_status = self.get_status()
            if current_status == ChannelStatus.READY:
                # Only change to ERROR if we were previously ready
                self._set_status(ChannelStatus.ERROR, "Disconnected")
            self._shared__update_connection_status(DiscordConnectionStatus.DISCONNECTED)
            
            # Let Discord.py handle reconnection, but log our status
            logger.info("Discord.py will handle automatic reconnection")

        @self.bot.event
        @handle_errors("handling Discord error event", default_return=None)
        async def on_error(event, *args, **kwargs):
            logger.error(f"Discord bot error in event {event}: {args} {kwargs}")
            
            # Use component logger for Discord error events
            error_str = str(args) + str(kwargs)
            discord_logger.error("Discord bot error", 
                               event=event, 
                               error_details=error_str[:200],  # Truncate long errors
                               bot_name=str(self.bot.user) if self.bot.user else "unknown")
            
            # Check if this is a connection-related error
            if any(keyword in error_str.lower() for keyword in ['connection', 'dns', 'timeout', 'network']):
                logger.warning("Connection-related error detected - checking network status")
                discord_logger.warning("Connection-related error detected", event=event)
                if not self._check_dns_resolution():
                    logger.error("DNS resolution failed during error recovery")
                    discord_logger.error("DNS resolution failed during error recovery")
                    self._shared__update_connection_status(DiscordConnectionStatus.DNS_FAILURE)
                if not self._check_network_connectivity():
                    logger.error("Network connectivity failed during error recovery")
                    discord_logger.error("Network connectivity failed during error recovery")
                    self._shared__update_connection_status(DiscordConnectionStatus.NETWORK_FAILURE)
            
            # Let discord.py handle reconnection for most errors

        @self.bot.event
        @handle_errors("handling Discord interaction event", default_return=None)
        async def on_interaction(interaction: discord.Interaction):
            """Handle Discord interactions (slash commands, buttons, etc.)"""
            # Handle button clicks (component interactions)
            if interaction.type == discord.InteractionType.component:
                # Check if this is a welcome message button
                if interaction.data and 'custom_id' in interaction.data:
                    custom_id = interaction.data['custom_id']
                    if custom_id.startswith('welcome_create_') or custom_id.startswith('welcome_link_'):
                        # Extract Discord user ID from custom_id
                        # Format: welcome_create_<discord_user_id> or welcome_link_<discord_user_id>
                        parts = custom_id.split('_', 2)
                        if len(parts) >= 3:
                            discord_user_id = parts[2]
                            
                            from communication.communication_channels.discord.account_flow_handler import (
                                start_account_creation_flow,
                                start_account_linking_flow
                            )
                            
                            # Get Discord username if available
                            discord_username = interaction.user.name if interaction.user else None
                            
                            # Validate interaction type before proceeding
                            if not isinstance(interaction, discord.Interaction):
                                discord_logger.error(f"Invalid interaction type for welcome button: {type(interaction)}")
                                await interaction.response.send_message(
                                    "❌ An error occurred. Please try again.",
                                    ephemeral=True
                                )
                                return
                            
                            if custom_id.startswith('welcome_create_'):
                                await start_account_creation_flow(interaction, discord_user_id, discord_username)
                            elif custom_id.startswith('welcome_link_'):
                                await start_account_linking_flow(interaction, discord_user_id)
                            return
                    
                    # Handle check-in buttons
                    elif custom_id.startswith('checkin_'):
                        # Check-in buttons are handled by the view's callback methods
                        # The view is attached to the message, so discord.py will handle it automatically
                        # We just need to let it pass through
                        return
                    
                    # Handle task reminder buttons
                    elif custom_id.startswith('task_'):
                        # Task reminder buttons are handled by the view's callback methods
                        # The view is attached to the message, so discord.py will handle it automatically
                        # We just need to let it pass through
                        return
                
                # Let other component interactions fall through to default handling
                # (buttons from other parts of the system)
                return
            
            # Handle application commands (slash commands)
            if interaction.type == discord.InteractionType.application_command:
                discord_user_id = str(interaction.user.id)
                command_name = interaction.command.name if hasattr(interaction, 'command') and interaction.command else 'unknown'
                discord_logger.debug(f"DISCORD_INTERACTION: user_id={discord_user_id}, command={command_name}")
                
                # Check if this is a new user who hasn't been welcomed
                from communication.communication_channels.discord.welcome_handler import (
                    has_been_welcomed,
                    mark_as_welcomed,
                    get_welcome_message
                )
                from core.user_management import get_user_id_by_identifier
                
                internal_user_id = get_user_id_by_identifier(discord_user_id)
                
                # Special handling for /start command (explicit welcome trigger)
                if command_name == 'start' and not internal_user_id:
                    welcome_msg = get_welcome_message(discord_user_id, is_authorization=True)
                    try:
                        # Send welcome DM
                        await interaction.user.send(welcome_msg)
                        mark_as_welcomed(discord_user_id)
                        if not interaction.response.is_done():
                            await interaction.response.send_message(
                                "👋 Welcome! I've sent you setup instructions via DM. Check your direct messages!",
                                ephemeral=True
                            )
                        discord_logger.info(f"Sent welcome DM to newly authorized Discord user via /start: {discord_user_id}")
                        return  # Don't process the command further
                    except discord.Forbidden:
                        # User has DMs disabled - respond in interaction instead
                        mark_as_welcomed(discord_user_id)
                        if not interaction.response.is_done():
                            await interaction.response.send_message(
                                f"👋 Welcome! I see you've authorized MHM. However, I can't send you a direct message.\n\n"
                                f"**Your Discord ID:** `{discord_user_id}`\n\n"
                                f"**To get started:**\n"
                                f"- Create a new account via the MHM application UI with your Discord ID, or\n"
                                f"- Ask an administrator to link your Discord ID to an existing account",
                                ephemeral=True
                            )
                        discord_logger.info(f"Welcomed user {discord_user_id} via /start (DM blocked)")
                        return
                    except Exception as e:
                        discord_logger.warning(f"Error sending welcome DM to {discord_user_id}: {e}")
                
                # For any other command, check if user needs welcome
                if not internal_user_id and not has_been_welcomed(discord_user_id):
                    # User has authorized the app (they can use slash commands) but hasn't been welcomed
                    welcome_msg = get_welcome_message(discord_user_id, is_authorization=True)
                    
                    try:
                        # Send welcome DM (non-blocking - don't interfere with command processing)
                        await interaction.user.send(welcome_msg)
                        mark_as_welcomed(discord_user_id)
                        discord_logger.info(f"Sent welcome DM to newly authorized Discord user via interaction: {discord_user_id}")
                    except discord.Forbidden:
                        # User has DMs disabled - mark as welcomed but don't interrupt command flow
                        mark_as_welcomed(discord_user_id)
                        discord_logger.info(f"User {discord_user_id} has DMs disabled, marked as welcomed")
                    except Exception as e:
                        discord_logger.warning(f"Error sending welcome DM to {discord_user_id}: {e}")

        @self.bot.event
        @handle_errors("handling Discord guild join event", default_return=None)
        async def on_guild_join(guild):
            """Handle when the bot is added to a new Discord server"""
            discord_logger.info(f"Bot added to server: {guild.name} (ID: {guild.id})")
            
            # Try to find a suitable channel to send welcome message
            # Prefer system channel, then first text channel the bot can send to
            welcome_channel = None
            
            # Try system channel first (where Discord sends system messages)
            if guild.system_channel and guild.system_channel.permissions_for(guild.me).send_messages:
                welcome_channel = guild.system_channel
                discord_logger.debug(f"Using system channel: {guild.system_channel.name}")
            else:
                # Find first text channel the bot can send to
                for channel in guild.text_channels:
                    if channel.permissions_for(guild.me).send_messages:
                        welcome_channel = channel
                        discord_logger.debug(f"Using text channel: {channel.name}")
                        break
            
            if welcome_channel:
                welcome_msg = (
                    f"👋 **Hello {guild.name}!**\n\n"
                    f"I'm **MHM (Mental Health Manager)**, your mental health assistant bot. "
                    f"I'm here to help you manage tasks, check-ins, reminders, and provide personalized support.\n\n"
                    f"**To get started:**\n"
                    f"1. Send me a message to get your Discord ID\n"
                    f"2. Create or link a MHM account with that Discord ID\n"
                    f"3. Start using commands like `/help` to see what I can do!\n\n"
                    f"**Quick Commands:**\n"
                    f"- `/help` - See all available commands\n"
                    f"- `create task [description]` - Create a new task\n"
                    f"- `show my tasks` - View your tasks\n"
                    f"- `show my profile` - View your profile (once linked)\n\n"
                    f"Feel free to ask me anything! I'm here to help. 🚀"
                )
                
                try:
                    await welcome_channel.send(welcome_msg)
                    discord_logger.info(f"Sent welcome message to {guild.name} in channel {welcome_channel.name}")
                except Exception as e:
                    discord_logger.warning(f"Could not send welcome message to {guild.name}: {e}")
            else:
                discord_logger.warning(f"Could not find a suitable channel to send welcome message in {guild.name}")

        @self.bot.event
        @handle_errors("handling Discord message", default_return=None)
        async def on_message(message):
            # COMPREHENSIVE LOGGING: Log ALL messages received
            discord_logger.debug(f"DISCORD_MESSAGE_RECEIVED: author_id={message.author.id}, content='{message.content[:100]}', channel={message.channel.id}, guild={message.guild.id if message.guild else 'DM'}")
            
            # Don't respond to ourselves
            if message.author == self.bot.user:
                discord_logger.debug(f"DISCORD_MESSAGE_IGNORED: Message from bot itself, ignoring")
                return

            # Process explicit commands (starting with "!" or "/") through our interaction manager
            # Note: We don't call bot.process_commands() because we handle commands through our own system

            # Process regular messages (not commands) through the interaction manager
            # This prevents Discord from automatically trying to match commands to regular messages
            # Map Discord user ID to internal user ID
            discord_user_id = str(message.author.id)
            discord_logger.debug(f"DISCORD_MESSAGE_PROCESS: Looking up user for Discord ID {discord_user_id}")
            internal_user_id = get_user_id_by_identifier(discord_user_id)
            
            if not internal_user_id:
                discord_logger.warning(f"DISCORD_MESSAGE_UNRECOGNIZED: No internal user found for Discord ID {discord_user_id}")
                
                # Send welcome message if this is the first time
                from communication.communication_channels.discord.welcome_handler import (
                    has_been_welcomed,
                    mark_as_welcomed,
                    get_welcome_message
                )
                
                # Check if this is a DM (user-installable app authorization)
                is_dm = isinstance(message.channel, discord.DMChannel)
                
                if not has_been_welcomed(discord_user_id):
                    # Determine if this is an app authorization (DM) or server message
                    welcome_msg = get_welcome_message(discord_user_id, is_authorization=is_dm)
                    
                    if is_dm:
                        # User-installable app: user has authorized and sent first DM
                        # Send welcome message as DM proactively
                        try:
                            await message.author.send(welcome_msg)
                            mark_as_welcomed(discord_user_id)
                            discord_logger.info(f"Sent welcome DM to newly authorized Discord user: {discord_user_id}")
                        except discord.Forbidden:
                            # User has DMs disabled or blocked bot - send in the channel instead
                            await message.channel.send(
                                f"I see you've authorized MHM! However, I can't send you a direct message. "
                                f"Here's your Discord ID to get started: `{discord_user_id}`\n\n"
                                f"**To get started:**\n"
                                f"- Create a new account via the MHM application UI with your Discord ID, or\n"
                                f"- Ask an administrator to link your Discord ID to an existing account"
                            )
                            mark_as_welcomed(discord_user_id)
                            discord_logger.info(f"Welcomed user {discord_user_id} via channel (DM blocked)")
                    else:
                        # Server message - but user might have authorized the app
                        # Try to send welcome DM first, fallback to channel
                        try:
                            await message.author.send(welcome_msg)
                            mark_as_welcomed(discord_user_id)
                            discord_logger.info(f"Sent welcome DM to new Discord user (from server message): {discord_user_id}")
                        except discord.Forbidden:
                            # Can't DM - send in channel instead
                            await message.channel.send(welcome_msg)
                            mark_as_welcomed(discord_user_id)
                            discord_logger.info(f"Sent welcome message to new Discord user in channel: {discord_user_id}")
                else:
                    # User has been welcomed before
                    if is_dm:
                        # DM reminder - send as DM
                        try:
                            await message.author.send(
                                f"I don't recognize you yet! To use MHM, you need to create or link a MHM account.\n\n"
                                f"**Your Discord ID:** `{discord_user_id}`\n\n"
                                f"**To get started:**\n"
                                f"- Create a new account via the MHM application UI, or\n"
                                f"- Ask an administrator to link your Discord ID to an existing account\n\n"
                                f"Once your account is linked, I'll be able to help you with tasks, reminders, and more!"
                            )
                        except discord.Forbidden:
                            # Fallback to channel if DM blocked
                            await message.channel.send(
                                f"Your Discord ID: `{discord_user_id}` - Please create or link a MHM account to get started!"
                            )
                    else:
                        # Server reminder - send in channel
                        await message.channel.send(
                            f"I don't recognize you yet! To use MHM, you need to create or link a MHM account.\n\n"
                            f"**Your Discord ID:** `{discord_user_id}`\n\n"
                            f"**To get started:**\n"
                            f"- Create a new account via the MHM application UI, or\n"
                            f"- Ask an administrator to link your Discord ID to an existing account\n\n"
                            f"Once your account is linked, I'll be able to help you with tasks, reminders, and more!"
                        )
                
                return
            
            discord_logger.info(f"DISCORD_MESSAGE_USER_IDENTIFIED: Discord ID {discord_user_id} → Internal user {internal_user_id}")

            # Validate that the stored Discord user ID is still accessible
            # This helps catch cases where the user's Discord account was deleted or they blocked the bot
            stored_discord_id = None
            try:
                from core.user_data_handlers import get_user_data
                user_data_result = get_user_data(internal_user_id, 'account')
                account_data = user_data_result.get('account', {})
                stored_discord_id = account_data.get('discord_user_id')
                
                if stored_discord_id and str(stored_discord_id) != discord_user_id:
                    # The user's Discord ID has changed - update it
                    logger.info(f"Updating Discord user ID for user {internal_user_id} from {stored_discord_id} to {discord_user_id}")
                    account_data['discord_user_id'] = discord_user_id
                    from core.user_data_handlers import save_user_data
                    save_user_data(internal_user_id, 'account', account_data)
                    
            except Exception as e:
                logger.warning(f"Error validating Discord user ID for {internal_user_id}: {e}")

            # Use the new interaction manager for enhanced user interactions
            try:
                from communication.message_processing.interaction_manager import handle_user_message
                discord_logger.info(f"DISCORD_BOT: Calling handle_user_message for user {internal_user_id} with message: '{message.content[:50]}...'")
                response = handle_user_message(internal_user_id, message.content, "discord")
                
                if response.message:
                    # Send response directly to the channel (bypass _send_message_internal to avoid DM attempts)
                    send_success = await self._send_to_channel(message.channel, response.message, response.rich_data, response.suggestions)
                    
                    if send_success:
                        # Log successful message handling
                        discord_logger.info("Discord message handled successfully", 
                                          user_id=internal_user_id, 
                                          message_length=len(message.content),
                                          response_length=len(response.message),
                                          suggestions_count=len(response.suggestions) if response.suggestions else 0,
                                          has_rich_data=bool(response.rich_data))
                    else:
                        # Message send failed - could be due to user not being accessible
                        discord_logger.warning("Discord message send failed for user", 
                                             user_id=internal_user_id,
                                             discord_user_id=discord_user_id)
                        
            except Exception as e:
                logger.error(f"Error in enhanced interaction for user {internal_user_id}: {e}")
                discord_logger.error("Discord message handling failed", 
                                   user_id=internal_user_id, 
                                   error=str(e),
                                   fallback_used=True)
                # Don't fall back to conversation manager - interaction manager handles this internally
                # Just send a generic error message
                await message.channel.send("I'm having trouble processing your message right now. Please try again in a moment.")

        # Store reference to the handler so we can call it manually if on_ready() doesn't fire
        # Store as a callable that creates the coroutine, not the coroutine itself
        # This prevents unawaited coroutine warnings in test environments
        self._on_ready_handler = _on_ready_internal
        
        self._events_registered = True
        
        # If bot is already ready when we register events, on_ready won't fire
        # So we need to manually trigger the webhook server startup
        if self.bot and self.bot.is_ready():
            try:
                # Only create task if loop is running and not closed
                if hasattr(self.bot, 'loop') and self.bot.loop and not self.bot.loop.is_closed():
                    self.bot.loop.create_task(_on_ready_internal())
                else:
                    discord_logger.debug("Bot loop not available for manual on_ready trigger")
            except Exception as e:
                discord_logger.warning(f"Failed to manually trigger webhook server startup: {e}", exc_info=True)

    @handle_errors("registering Discord commands")
    def initialize__register_commands(self):
        """Register Discord commands"""
        if self._commands_registered or not self.bot:
            return

        # Register dynamic application (slash) commands from the channel-agnostic map
        from communication.message_processing.interaction_manager import get_interaction_manager, handle_user_message
        im = get_interaction_manager()
        cmd_defs = im.get_command_definitions()

        for cmd in cmd_defs:
            name = cmd["name"]
            mapped = cmd["mapped_message"]
            description = cmd["description"]

            @handle_errors("handling Discord app command", context={"command": name}, default_return=None)
            async def _app_cb(interaction: discord.Interaction, _mapped=mapped, _name=name):
                discord_user_id = str(interaction.user.id)
                internal_user_id = get_user_id_by_identifier(discord_user_id)
                if not internal_user_id:
                    # Welcome message should have been sent by on_interaction handler
                    # But provide helpful response if they try to use a command
                    await interaction.response.send_message(
                        f"Please create or link a MHM account to use this feature. Your Discord ID: `{discord_user_id}`",
                        ephemeral=True
                    )
                    return
                response = handle_user_message(internal_user_id, _mapped, "discord")
                
                # Create embed if rich_data is provided
                embed = None
                if response.rich_data:
                    embed = self._create_discord_embed(response.message, response.rich_data)
                
                # Create view with buttons if suggestions are provided
                view = None
                if response.suggestions:
                    view = self._create_action_row(response.suggestions)
                
                # Send response with embed and/or view
                if embed and view:
                    await interaction.response.send_message(embed=embed, view=view)
                elif embed:
                    await interaction.response.send_message(embed=embed)
                elif view:
                    await interaction.response.send_message(response.message, view=view)
                else:
                    await interaction.response.send_message(response.message)

            try:
                app_cmd = app_commands.Command(name=name, description=(description or f"{name} command"), callback=_app_cb)
                self.bot.tree.add_command(app_cmd)
            except Exception:
                # If already exists, skip silently
                pass

        # Dynamically expose a set of native-style classic commands based on the central slash map.
        from communication.message_processing.interaction_manager import get_interaction_manager
        im = get_interaction_manager()
        cmd_defs = im.get_command_definitions()

        for cmd in cmd_defs:
            name = cmd["name"]
            mapped = cmd["mapped_message"]
            # Skip Discord's native classic commands to avoid duplication
            if name in ["help"]:
                continue

            @handle_errors("handling Discord dynamic command", context={"command": name}, default_return=None)
            async def _dynamic(ctx, _mapped=mapped, _name=name):
                discord_user_id = str(ctx.author.id)
                internal_user_id = get_user_id_by_identifier(discord_user_id)
                if not internal_user_id:
                    await ctx.send("Please register first to use this feature.")
                    return
                from communication.message_processing.interaction_manager import handle_user_message
                response = handle_user_message(internal_user_id, _mapped, "discord")
                await ctx.send(response.message)

            # Register as a classic command: users can type !tasks, !profile, etc.
            try:
                self.bot.command(name=name)(_dynamic)
            except Exception:
                # Ignore duplicates if any
                pass

        self._commands_registered = True

    @handle_errors("shutting down Discord bot", default_return=False)
    async def shutdown(self) -> bool:
        """Shutdown Discord bot safely with improved session and event loop management"""
        logger.info("Starting Discord bot shutdown...")
        
        try:
            # Stop ngrok FIRST - don't wait for full bot shutdown
            # This ensures ngrok stops even if shutdown hangs
            self._stop_ngrok_tunnel()
            
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
            
            # Properly close the bot and event loop with enhanced cleanup
            if self.bot:
                async with self.shutdown__session_cleanup_context() as sessions_to_cleanup:
                    # Cancel any pending sync task first
                    if hasattr(self, '_sync_task') and self._sync_task and not self._sync_task.done():
                        self._sync_task.cancel()
                        try:
                            await asyncio.wait_for(self._sync_task, timeout=2.0)
                        except (asyncio.CancelledError, asyncio.TimeoutError):
                            logger.debug("Sync task cancelled or timed out during shutdown")
                        except Exception as e:
                            logger.debug(f"Error waiting for sync task cancellation: {e}")
                    
                    # Close the bot first
                    if not self.bot.is_closed():
                        await self.bot.close()
                        logger.info("Discord bot closed successfully")
                    
                    # Collect all sessions that need cleanup
                    if hasattr(self.bot, '_HTTP') and self.bot._HTTP:
                        if hasattr(self.bot._HTTP, '_HTTPClient') and self.bot._HTTP._HTTPClient:
                            if hasattr(self.bot._HTTP._HTTPClient, '_session') and self.bot._HTTP._HTTPClient._session:
                                sessions_to_cleanup.append(self.bot._HTTP._HTTPClient._session)
                    
                    # Clean up the event loop if it exists
                    if hasattr(self, '_loop') and self._loop:
                        await self._cleanup_event_loop_safely(self._loop)
                    
                    # Additional cleanup for aiohttp sessions
                    await self._cleanup_aiohttp_sessions()
                    
                    # Stop webhook server
                    if self._webhook_server:
                        try:
                            self._webhook_server.stop()
                        except Exception as e:
                            logger.debug(f"Error stopping webhook server: {e}")
                    
                    # Stop ngrok tunnel if running
                    self._stop_ngrok_tunnel()
            
            # Ensure ngrok is stopped even if shutdown had errors
            self._stop_ngrok_tunnel()
            
            return True
        finally:
            # Always set status to STOPPED, even if shutdown encountered errors
            # This ensures tests can verify shutdown was attempted
            self._set_status(ChannelStatus.STOPPED)
            logger.info("Discord bot shutdown completed")

    @handle_errors("sending Discord message", default_return=False)
    async def send_message(self, recipient: str, message: str, **kwargs) -> bool:
        """
        Send Discord message with validation.
        
        Returns:
            bool: True if successful, False if failed
        """
        # Validate recipient
        if not recipient or not isinstance(recipient, str):
            logger.error(f"Invalid recipient: {recipient}")
            return False
            
        if not recipient.strip():
            logger.error("Empty recipient provided")
            return False
            
        # Validate message
        if not message or not isinstance(message, str):
            logger.error(f"Invalid message: {message}")
            return False
            
        if not message.strip():
            logger.error("Empty message provided")
            return False
        """Send message via Discord using thread-safe queue communication with rich response support"""
        if not self.is_ready():
            logger.error("Discord bot is not ready to send messages")
            return False

        # Check for rich response data
        rich_data = kwargs.get('rich_data', {})
        suggestions = kwargs.get('suggestions', [])
        custom_view = kwargs.get('view', None)
        
        # Send command to Discord thread with rich data and optional custom view
        if custom_view:
            self._command_queue.put(("send_message", (recipient, message, rich_data, suggestions, custom_view)))
        else:
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

    @handle_errors("validating Discord user accessibility", user_friendly=False, default_return=False)
    async def _validate_discord_user_accessibility(self, user_id: str) -> bool:
        """Validate if a Discord user ID is still accessible"""
        user_id_int = int(user_id)
        user = self.bot.get_user(user_id_int)
        if not user:
            try:
                user = await self.bot.fetch_user(user_id_int)
                return True
            except discord.NotFound:
                logger.warning(f"Discord user {user_id} not found (404)")
                return False
            except discord.Forbidden:
                logger.warning(f"Bot forbidden from accessing Discord user {user_id} (403)")
                return False
        return True

    @handle_errors("sending message to Discord channel", user_friendly=False, default_return=False)
    async def _send_to_channel(self, channel, message: str, rich_data: Dict[str, Any] = None, suggestions: List[str] = None) -> bool:
        """Send message directly to a Discord channel (for regular message responses)"""
        rich_data = rich_data or {}
        suggestions = suggestions or []
        
        # Create Discord embed if rich data is provided
        embed = None
        if rich_data:
            embed = self._create_discord_embed(message, rich_data)
        
        # Create view with buttons if suggestions are provided
        view = None
        if suggestions:
            view = self._create_action_row(suggestions)
        
        # Send to the channel
        if embed and view:
            await channel.send(embed=embed, view=view)
        elif embed:
            await channel.send(embed=embed)
        elif view:
            await channel.send(message, view=view)
        else:
            await channel.send(message)
        
        logger.info(f"Message sent to Discord channel {channel.id}")
        discord_logger.info("Discord channel message sent", 
                          channel_id=str(channel.id), 
                          message_length=len(message),
                          has_embed=bool(embed),
                          has_components=bool(view))
        return True

    @handle_errors("sending Discord message internally", default_return=False)
    async def _send_message_internal(self, recipient: str, message: str, rich_data: Dict[str, Any] = None, suggestions: List[str] = None, custom_view = None) -> bool:
        """
        Send Discord message internally with validation.
        
        Returns:
            bool: True if successful, False if failed
        """
        # Validate recipient
        if not recipient or not isinstance(recipient, str):
            logger.error(f"Invalid recipient: {recipient}")
            return False
            
        if not recipient.strip():
            logger.error("Empty recipient provided")
            return False
            
        # Validate message
        if not message or not isinstance(message, str):
            logger.error(f"Invalid message: {message}")
            return False
            
        if not message.strip():
            logger.error("Empty message provided")
            return False
            
        # Validate rich_data
        if rich_data is not None and not isinstance(rich_data, dict):
            logger.error(f"Invalid rich_data: {type(rich_data)}")
            return False
            
        # Validate suggestions
        if suggestions is not None and not isinstance(suggestions, list):
            logger.error(f"Invalid suggestions: {type(suggestions)}")
            return False
        """Send message safely within async context with rich response support"""
        rich_data = rich_data or {}
        suggestions = suggestions or []
        
        # Create Discord embed if rich data is provided
        embed = None
        if rich_data:
            embed = self._create_discord_embed(message, rich_data)
        
        # Create view with buttons - prefer custom_view, then suggestions
        view = None
        if custom_view:
            # Handle factory functions (callables) - create view within async context
            if callable(custom_view) and not isinstance(custom_view, type):
                try:
                    view = custom_view()
                except Exception as e:
                    logger.error(f"Error creating view from factory function: {e}")
                    view = None
            else:
                view = custom_view
        elif suggestions:
            view = self._create_action_row(suggestions)
        
        # Handle special Discord user marker first
        if recipient.startswith("discord_user:"):
            internal_user_id = recipient.split(":", 1)[1]
            # Get the user's Discord user ID and send a DM
            try:
                from core.user_data_handlers import get_user_data
                user_data_result = get_user_data(internal_user_id, 'account')
                account_data = user_data_result.get('account', {})
                discord_user_id = account_data.get('discord_user_id')
                
                if discord_user_id:
                    user_id_int = int(discord_user_id)
                    user = self.bot.get_user(user_id_int)
                    if not user:
                        user = await self.bot.fetch_user(user_id_int)
                    
                    if user:
                        if embed and view:
                            await user.send(embed=embed, view=view)
                        elif embed:
                            await user.send(embed=embed)
                        elif view:
                            await user.send(message, view=view)
                        else:
                            await user.send(message)
                        # Log detailed message information (consolidated from two separate logs)
                        logger.info(f"Discord DM sent | {{\"user_id\": \"{discord_user_id}\", \"message_length\": {len(message)}, \"has_embed\": {bool(embed)}, \"has_components\": {bool(view)}, \"message_preview\": \"{message[:50]}...\"}}")
                        return True
                    else:
                        logger.warning(f"Could not find Discord user {discord_user_id} for internal user {internal_user_id}")
                        return False
                else:
                    logger.warning(f"No Discord user ID found for internal user {internal_user_id}")
                    return False
            except Exception as e:
                logger.error(f"Error sending DM to Discord user {internal_user_id}: {e}")
                return False
        
        # Handle direct Discord user ID (for account linking when user doesn't have internal ID yet)
        if recipient.startswith("discord_direct:"):
            discord_user_id = recipient.split(":", 1)[1]
            # Send DM directly to Discord user ID (no internal user lookup needed)
            try:
                user_id_int = int(discord_user_id)
                user = self.bot.get_user(user_id_int)
                if not user:
                    user = await self.bot.fetch_user(user_id_int)
                
                if user:
                    if embed and view:
                        await user.send(embed=embed, view=view)
                    elif embed:
                        await user.send(embed=embed)
                    elif view:
                        await user.send(message, view=view)
                    else:
                        await user.send(message)
                    logger.info(f"Discord DM sent directly | {{\"discord_user_id\": \"{discord_user_id}\", \"message_length\": {len(message)}, \"has_embed\": {bool(embed)}, \"has_components\": {bool(view)}, \"message_preview\": \"{message[:50]}...\"}}")
                    return True
                else:
                    logger.warning(f"Could not find Discord user {discord_user_id}")
                    return False
            except Exception as e:
                logger.error(f"Error sending DM directly to Discord user {discord_user_id}: {e}")
                return False
        
        # Try as a channel first (preferred method)
        try:
            channel_id = int(recipient)
            channel = self.bot.get_channel(channel_id)
            if channel:
                if embed and view:
                    await channel.send(embed=embed, view=view)
                elif embed:
                    await channel.send(embed=embed)
                elif view:
                    await channel.send(message, view=view)
                else:
                    await channel.send(message)
                logger.info(f"Message sent to Discord channel {recipient}")
                discord_logger.info("Discord channel message sent", 
                                  channel_id=recipient, 
                                  message_length=len(message),
                                  has_embed=bool(embed),
                                  has_components=bool(view))
                return True
            else:
                logger.warning(f"Could not find Discord channel with ID {recipient}")
        except (ValueError, TypeError):
            logger.warning(f"Invalid channel ID format: {recipient}")
            pass  # Not a valid channel ID
        
        
        # If we get here, we couldn't send the message
        logger.error(f"Could not find Discord channel or user with ID {recipient}")
        discord_logger.error("Discord message send failed - recipient not found", 
                           recipient=recipient)
        return False
        
        logger.error(f"Could not find Discord channel or user with ID {recipient}")
        discord_logger.error("Discord message send failed - recipient not found", 
                           recipient=recipient)
        return False
    
    @handle_errors("creating Discord embed", default_return=None)
    def _create_discord_embed(self, message: str, rich_data: Dict[str, Any]) -> discord.Embed:
        """
        Create Discord embed with validation.
        
        Returns:
            discord.Embed: Created embed, None if failed
        """
        # Validate message
        if not message or not isinstance(message, str):
            logger.error(f"Invalid message: {message}")
            return None
            
        if not message.strip():
            logger.error("Empty message provided")
            return None
            
        # Validate rich_data
        if not rich_data or not isinstance(rich_data, dict):
            logger.error(f"Invalid rich_data: {rich_data}")
            return None
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
            'success': discord.Color.green(),
            'error': discord.Color.red(),
            'warning': discord.Color.yellow(),
            'info': discord.Color.blue(),
            'task': discord.Color.purple(),
            'profile': discord.Color.orange(),
            'schedule': discord.Color.blue(),
            'analytics': discord.Color.green()
        }
        
        embed_type = rich_data.get('type', 'info')
        embed.color = color_map.get(embed_type, discord.Color.blue())
        
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
    
    @handle_errors("creating Discord action row", default_return=None)
    def _create_action_row(self, suggestions: List[str]) -> discord.ui.View:
        """
        Create Discord action row with validation.
        
        Returns:
            discord.ui.View: Created view, None if failed
        """
        # Validate suggestions
        if not suggestions or not isinstance(suggestions, list):
            logger.error(f"Invalid suggestions: {suggestions}")
            return None
            
        if not suggestions:
            logger.error("Empty suggestions provided")
            return None
        """Create a Discord view with buttons from suggestions"""
        # Use discord.ui.View instead of ActionRow for discord.py v2.x compatibility
        view = discord.ui.View()
        
        # Limit to 5 buttons (Discord limit)
        for i, suggestion in enumerate(suggestions[:5]):
            # Create a button with a unique custom_id
            button = discord.ui.Button(
                style=discord.ButtonStyle.primary,
                label=suggestion[:80],  # Discord button label limit
                custom_id=f"suggestion_{i}_{hash(suggestion) % 10000}"
            )
            view.add_item(button)
        
        return view

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
            self._shared__update_connection_status(DiscordConnectionStatus.UNINITIALIZED)
            return False
        
        if self.bot.is_closed():
            logger.warning("Discord bot is closed")
            self._shared__update_connection_status(DiscordConnectionStatus.DISCONNECTED)
            return False
        
        if not self.bot.is_ready():
            logger.warning("Discord bot is not ready")
            self._shared__update_connection_status(DiscordConnectionStatus.DISCONNECTED)
            return False
        
        # Enhanced network connectivity checks
        dns_ok = self._check_dns_resolution()
        network_ok = self._check_network_connectivity()
        
        if not dns_ok:
            logger.warning("DNS resolution failed during health check")
            self._shared__update_connection_status(DiscordConnectionStatus.DNS_FAILURE)
            return False
        
        if not network_ok:
            logger.warning("Network connectivity failed during health check")
            self._shared__update_connection_status(DiscordConnectionStatus.NETWORK_FAILURE)
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
        self._shared__update_connection_status(DiscordConnectionStatus.CONNECTED)
        logger.debug("Discord health check passed")
        return True

    @handle_errors("getting Discord health status", default_return={})
    def get_health_status(self) -> Dict[str, Any]:
        """Get comprehensive health status information"""
        return self._get_detailed_connection_status()

    @handle_errors("getting connection status summary", default_return="Unknown")
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

    @handle_errors("checking if actually connected", default_return=False)
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
        
        # If bot exists but not ready, check if it's in a recoverable state
        if self.bot and not self.bot.is_closed():
            # Bot exists and not closed, but not ready - might be reconnecting
            return False
        
        return False

    @handle_errors("checking if can send messages", default_return=False)
    def can_send_messages(self) -> bool:
        """Check if the Discord bot can actually send messages"""
        if not self.is_actually_connected():
            return False
        
        # Additional checks for message sending capability
        try:
            # Check if we have the bot user (means we're logged in)
            if not self.bot.user:
                return False
            
            # Check if we have any guilds (servers) we're connected to
            if not self.bot.guilds:
                return False
            
            return True
        except Exception as e:
            logger.warning(f"Error checking message sending capability: {e}")
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


    @handle_errors("starting ngrok tunnel", default_return=None)
    def _start_ngrok_tunnel(self, port: int):
        """
        Start ngrok tunnel for webhook server (development only).
        
        Args:
            port: Local port to tunnel (e.g., 8080)
        """
        try:
            # Check if ngrok is available
            ngrok_path = shutil.which('ngrok')
            if not ngrok_path:
                discord_logger.warning("ngrok not found in PATH - auto-launch disabled. Install ngrok or set DISCORD_AUTO_NGROK=false")
                return
            
            # Check if ngrok is already running (avoid duplicates)
            if self._ngrok_process and self._ngrok_process.poll() is None:
                discord_logger.info("ngrok tunnel already running (managed by this bot)")
                return
            
            # Check if ngrok is already running from another process
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if not proc.info['name']:
                        continue
                    proc_name = proc.info['name'].lower()
                    if 'ngrok' in proc_name:
                        cmdline = proc.info.get('cmdline', [])
                        if cmdline and 'http' in ' '.join(cmdline).lower():
                            if proc.is_running():
                                discord_logger.info(f"ngrok tunnel already running externally (PID: {proc.info['pid']}) - skipping auto-launch")
                                return
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
            
            # Start ngrok process
            discord_logger.info(f"Starting ngrok tunnel for port {port}...")
            try:
                # Windows: use CREATE_NO_WINDOW to hide console
                # Unix: redirect output to avoid cluttering logs
                if os.name == 'nt':  # Windows
                    self._ngrok_process = subprocess.Popen(
                        ['ngrok', 'http', str(port)],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        creationflags=subprocess.CREATE_NO_WINDOW
                    )
                else:  # Unix/Linux/Mac
                    self._ngrok_process = subprocess.Popen(
                        ['ngrok', 'http', str(port)],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL
                    )
                
                # Give ngrok a moment to start
                time.sleep(2)
                
                # Check if process started successfully
                if self._ngrok_process.poll() is None:
                    self._ngrok_pid = self._ngrok_process.pid  # Store PID for fallback cleanup
                    discord_logger.info(f"ngrok tunnel started successfully (PID: {self._ngrok_process.pid})")
                    discord_logger.info(f"ngrok web interface: http://127.0.0.1:4040")
                    discord_logger.info(f"Check ngrok web interface for public URL to configure in Discord Developer Portal")
                else:
                    discord_logger.warning(f"ngrok process exited immediately (exit code: {self._ngrok_process.poll()})")
                    self._ngrok_process = None
                    self._ngrok_pid = None
                    
            except FileNotFoundError:
                discord_logger.warning("ngrok executable not found - auto-launch disabled")
                self._ngrok_process = None
                self._ngrok_pid = None
            except Exception as e:
                discord_logger.warning(f"Failed to start ngrok: {e}")
                self._ngrok_process = None
                self._ngrok_pid = None
                
        except Exception as e:
            discord_logger.warning(f"Error starting ngrok tunnel: {e}")
            self._ngrok_process = None
            self._ngrok_pid = None
    
    @handle_errors("stopping ngrok tunnel", default_return=None)
    def _stop_ngrok_tunnel(self):
        """Stop ngrok tunnel if running."""
        # Check if we've already stopped ngrok (avoid duplicate stop attempts)
        if not self._ngrok_process and not self._ngrok_pid:
            # Already stopped or never started - skip silently
            return
        
        stopped = False
        
        # Try to stop using process reference first
        if self._ngrok_process:
            try:
                if self._ngrok_process.poll() is None:
                    # Process is still running - terminate it
                    pid = self._ngrok_process.pid
                    discord_logger.info(f"Stopping ngrok tunnel (PID: {pid})...")
                    self._ngrok_process.terminate()
                    
                    # Wait up to 5 seconds for graceful shutdown
                    try:
                        self._ngrok_process.wait(timeout=5)
                        discord_logger.info("ngrok tunnel stopped")
                        stopped = True
                    except subprocess.TimeoutExpired:
                        # Force kill if it doesn't stop gracefully
                        discord_logger.warning("ngrok did not stop gracefully - forcing termination")
                        self._ngrok_process.kill()
                        self._ngrok_process.wait()
                        discord_logger.info("ngrok tunnel force-stopped")
                        stopped = True
                else:
                    # Process already exited
                    exit_code = self._ngrok_process.poll()
                    discord_logger.debug(f"ngrok tunnel already exited (exit code: {exit_code})")
                    stopped = True
                        
                self._ngrok_process = None
            except Exception as e:
                discord_logger.warning(f"Error stopping ngrok tunnel via process reference: {e}")
                self._ngrok_process = None
        
        # Fallback: Try to stop by PID if process reference was lost
        if not stopped and self._ngrok_pid:
            try:
                discord_logger.info(f"Attempting to stop ngrok tunnel by PID (PID: {self._ngrok_pid})...")
                proc = psutil.Process(self._ngrok_pid)
                if proc.is_running():
                    proc.terminate()
                    try:
                        proc.wait(timeout=5)
                        discord_logger.info("ngrok tunnel stopped (via PID)")
                        stopped = True
                    except psutil.TimeoutExpired:
                        proc.kill()
                        proc.wait()
                        discord_logger.info("ngrok tunnel force-stopped (via PID)")
                        stopped = True
                else:
                    discord_logger.debug(f"ngrok process {self._ngrok_pid} already exited")
                    stopped = True
            except psutil.NoSuchProcess:
                discord_logger.debug(f"ngrok process {self._ngrok_pid} not found (already stopped)")
                stopped = True
            except Exception as e:
                discord_logger.warning(f"Error stopping ngrok tunnel by PID: {e}")
        
        # Clear references only after successful stop
        if stopped:
            self._ngrok_process = None
            self._ngrok_pid = None

    # Keep the existing send_dm method for specific Discord functionality
    @handle_errors("sending Discord DM", default_return=False)
    async def send_dm(self, user_id: str, message: str) -> bool:
        """
        Send Discord DM with validation.
        
        Returns:
            bool: True if successful, False if failed
        """
        # Validate user_id
        if not user_id or not isinstance(user_id, str):
            logger.error(f"Invalid user_id: {user_id}")
            return False
            
        if not user_id.strip():
            logger.error("Empty user_id provided")
            return False
            
        # Validate message
        if not message or not isinstance(message, str):
            logger.error(f"Invalid message: {message}")
            return False
            
        if not message.strip():
            logger.error("Empty message provided")
            return False
        """Send a direct message to a Discord user"""
        return await self.send_message(user_id, message)
