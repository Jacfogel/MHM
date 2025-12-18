# channel_orchestrator.py

import asyncio
import threading
import time
import random
import re
from typing import Dict, List, Optional, Any

from core.logger import get_component_logger
from core.error_handling import handle_errors
from communication.communication_channels.base.base_channel import BaseChannel, ChannelConfig, ChannelStatus
from communication.core.factory import ChannelFactory
from communication.core.retry_manager import RetryManager
from communication.core.channel_monitor import ChannelMonitor
from core.user_data_handlers import get_user_data
from core.message_management import store_sent_message
from core.schedule_management import get_current_time_periods_with_validation, get_current_day_names
from core.file_operations import determine_file_path, load_json_data  # determine_file_path needed for test mocking
from core.config import EMAIL_SMTP_SERVER, DISCORD_BOT_TOKEN, get_user_data_dir
from core.service_utilities import wait_for_network

# Route orchestration logs to channels component; keep module logger for local debug if needed
comm_logger = get_component_logger('channel_orchestrator')
logger = comm_logger

class BotInitializationError(Exception):
    """Custom exception for bot initialization failures."""
    pass

class MessageSendError(Exception):
    """Custom exception for message sending failures."""
    pass

class CommunicationManager:
    """Manages all communication channels with improved modularity"""
    
    _instance = None
    _lock = threading.Lock()
    
    @handle_errors("creating channel orchestrator instance", default_return=None)
    def __new__(cls, *args, **kwargs):
        """Ensure that only one instance of the CommunicationManager exists (Singleton pattern)."""
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(CommunicationManager, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    @handle_errors("initializing channel orchestrator", default_return=None)
    def __init__(self):
        """Initialize the CommunicationManager singleton"""
        # Check if already initialized
        if hasattr(self, '_initialized') and self._initialized:
            return
        
        # Initialize basic attributes
        self._channels_dict = {}
        self.channel_configs = {}
        self._running = False
        self._main_loop = None
        self._loop_thread = None
        self.scheduler_manager = None
        self._last_task_reminders = {}  # Track last task reminder per user: {user_id: task_id}
        self._email_polling_thread = None
        self._email_polling_stop_event = threading.Event()
        self._processed_email_ids = set()  # Track processed emails to avoid duplicates
        
        # Initialize extracted modules
        # Pass send_message_sync as callback for retry manager
        self.retry_manager = RetryManager(send_callback=self.send_message_sync)
        self.channel_monitor = ChannelMonitor()
        
        # Set up event loop for async operations
        self.__init____setup_event_loop()
        
        # Mark as initialized
        self._initialized = True
            
    @handle_errors("setting up event loop", default_return=None)
    def __init____setup_event_loop(self):
        """Set up a dedicated event loop for async operations"""
        try:
            # Try to get existing loop - use get_running_loop() to avoid deprecation warning
            try:
                self._main_loop = asyncio.get_running_loop()
                self._event_loop = self._main_loop
                # If we get here, there's a running loop, so create a new one for our operations
                import threading
                @handle_errors("running event loop", default_return=None)
                def run_event_loop():
                    """
                    Run the event loop in a separate thread for async operations.
                    
                    This nested function is used to manage the event loop for async channel operations.
                    """
                    self._main_loop = asyncio.new_event_loop()
                    self._event_loop = self._main_loop
                    asyncio.set_event_loop(self._main_loop)
                    self._main_loop.run_forever()
                
                self._loop_thread = threading.Thread(target=run_event_loop, daemon=True)
                self._loop_thread.start()
                
                # Wait a moment for loop to start
                import time
                time.sleep(0.1)
            except RuntimeError:
                # No running loop, try to get current loop
                try:
                    # Use get_running_loop() first, fallback to new_event_loop()
                    try:
                        self._main_loop = asyncio.get_running_loop()
                    except RuntimeError:
                        self._main_loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(self._main_loop)
                    self._event_loop = self._main_loop
                except RuntimeError:
                    # No event loop exists, create new one
                    self._main_loop = asyncio.new_event_loop()
                    self._event_loop = self._main_loop
                    asyncio.set_event_loop(self._main_loop)
        except Exception as e:
            # Fallback: create new loop
            self._main_loop = asyncio.new_event_loop()
            self._event_loop = self._main_loop
            asyncio.set_event_loop(self._main_loop)
    
    @handle_errors("running async sync", default_return=None)
    def send_message_sync__run_async_sync(self, coro):
        """Run async function synchronously using our managed loop"""
        if self._loop_thread:
            # Submit to running loop
            future = asyncio.run_coroutine_threadsafe(coro, self._main_loop)
            return future.result(timeout=30)  # 30 second timeout
        else:
            # Use current loop
            return self._main_loop.run_until_complete(coro)

    @handle_errors("setting scheduler manager", default_return=None)
    def set_scheduler_manager(self, scheduler_manager):
        """Set the scheduler manager for the communication manager."""
        self.scheduler_manager = scheduler_manager
        logger.debug("Scheduler manager set in CommunicationManager.")

    @handle_errors("queueing failed message", default_return=None)
    def send_message_sync__queue_failed_message(self, user_id: str, category: str, message: str, recipient: str, channel_name: str):
        """Queue a failed message for retry"""
        self.retry_manager.queue_failed_message(user_id, category, message, recipient, channel_name)

    @handle_errors("starting retry thread", default_return=None)
    def start_all__start_retry_thread(self):
        """Start the retry thread for failed messages"""
        self.retry_manager.start_retry_thread()

    @handle_errors("stopping retry thread", default_return=None)
    def stop_all__stop_retry_thread(self):
        """Stop the retry thread"""
        self.retry_manager.stop_retry_thread()

    @handle_errors("starting restart monitor", default_return=None)
    def start_all__start_restart_monitor(self):
        """Start the automatic restart monitor thread"""
        self.channel_monitor.set_channels(self._channels_dict)
        self.channel_monitor.start_restart_monitor()

    @handle_errors("stopping restart monitor", default_return=None)
    def stop_all__stop_restart_monitor(self):
        """Stop the automatic restart monitor thread"""
        self.channel_monitor.stop_restart_monitor()

    @handle_errors("starting email polling thread", default_return=None)
    def start_all__start_email_polling(self):
        """Start the email polling thread to process incoming emails"""
        if self._email_polling_thread is not None and self._email_polling_thread.is_alive():
            logger.debug("Email polling thread already running")
            return
        
        self._email_polling_stop_event.clear()
        self._email_polling_thread = threading.Thread(target=self._email_polling_loop, daemon=True)
        self._email_polling_thread.start()
        logger.info("Email polling thread started")

    @handle_errors("stopping email polling thread", default_return=None)
    def stop_all__stop_email_polling(self):
        """Stop the email polling thread"""
        if self._email_polling_thread is not None:
            logger.info("Stopping email polling thread...")
            self._email_polling_stop_event.set()
            self._email_polling_thread.join(timeout=5)
            if self._email_polling_thread.is_alive():
                logger.warning("Email polling thread didn't stop within timeout")
            else:
                logger.info("Email polling thread stopped")
            self._email_polling_thread = None

    @handle_errors("email polling loop", default_return=None)
    def _email_polling_loop(self):
        """Background thread that periodically polls for incoming emails and processes them"""
        logger.info("Email polling loop started")
        poll_interval = 30  # Check for emails every 30 seconds
        
        while not self._email_polling_stop_event.is_set():
            try:
                # Only poll if email channel is available and ready
                email_channel = self._channels_dict.get('email')
                if email_channel and email_channel.is_ready() and self._running:
                    # Poll for new emails
                    try:
                        # Use the event loop to run async receive_messages
                        # Check if we have a running loop thread - if not, use temporary loop
                        if self._loop_thread and self._loop_thread.is_alive() and self._main_loop and not self._main_loop.is_closed():
                            try:
                                logger.debug("Using main loop thread for email polling")
                                future = asyncio.run_coroutine_threadsafe(
                                    email_channel.receive_messages(),
                                    self._main_loop
                                )
                                emails = future.result(timeout=10)
                            except RuntimeError as loop_error:
                                # Event loop may have been closed between check and use
                                logger.warning(f"Event loop became invalid during email polling, using fallback: {loop_error}")
                                # Fallback: create temporary loop
                                loop = asyncio.new_event_loop()
                                asyncio.set_event_loop(loop)
                                try:
                                    emails = loop.run_until_complete(email_channel.receive_messages())
                                finally:
                                    loop.close()
                        else:
                            # Fallback: create temporary loop (main loop not running or not available)
                            logger.debug("Using temporary event loop for email polling (main loop not running)")
                            loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(loop)
                            try:
                                emails = loop.run_until_complete(email_channel.receive_messages())
                            finally:
                                loop.close()
                        
                        # Process each email
                        for email_msg in emails:
                            email_id = email_msg.get('message_id')
                            if email_id and email_id not in self._processed_email_ids:
                                self._process_incoming_email(email_msg)
                                self._processed_email_ids.add(email_id)
                                # Limit processed IDs set size to prevent memory growth
                                if len(self._processed_email_ids) > 1000:
                                    # Keep only the most recent 500
                                    self._processed_email_ids = set(list(self._processed_email_ids)[-500:])
                    except asyncio.TimeoutError:
                        logger.error("Error polling for emails: Timeout waiting for receive_messages() to complete (10s timeout exceeded)", exc_info=True)
                    except RuntimeError as e:
                        logger.error(f"Error polling for emails: RuntimeError - {e} (event loop may be closed or invalid)", exc_info=True)
                    except Exception as e:
                        # Enhanced error logging with full exception details
                        error_type = type(e).__name__
                        error_msg = str(e) if str(e) else f"Exception of type {error_type} with no message"
                        logger.error(f"Error polling for emails: {error_type} - {error_msg}", exc_info=True)
                else:
                    logger.debug("Email channel not available or not ready, skipping poll")
                
            except Exception as e:
                # Enhanced error logging for outer exception handler
                error_type = type(e).__name__
                error_msg = str(e) if str(e) else f"Exception of type {error_type} with no message"
                logger.error(f"Error in email polling loop: {error_type} - {error_msg}", exc_info=True)
            
            # Wait for poll interval or stop event
            if self._email_polling_stop_event.wait(timeout=poll_interval):
                break
        
        logger.info("Email polling loop stopped")

    @handle_errors("processing incoming email", default_return=None)
    def _process_incoming_email(self, email_msg: Dict[str, Any]):
        """Process an incoming email message and send response"""
        try:
            email_from = email_msg.get('from', '')
            email_body = email_msg.get('body', '')
            email_subject = email_msg.get('subject', '')
            
            if not email_from or not email_body:
                logger.debug(f"Skipping email with missing from or body: {email_msg}")
                return
            
            # Extract email address from "from" field (may be "Name <email@example.com>" or just "email@example.com")
            email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', email_from)
            if not email_match:
                logger.warning(f"Could not extract email address from 'from' field: {email_from}")
                return
            
            sender_email = email_match.group(0)
            
            # Map email to user ID
            from core.user_management import get_user_id_by_identifier
            user_id = get_user_id_by_identifier(sender_email)
            
            if not user_id:
                logger.info(f"Email from unregistered user: {sender_email}")
                # Send registration prompt
                response_text = (
                    f"I don't recognize you yet! Please register first using the MHM application. "
                    f"Your email is: {sender_email}"
                )
                self._send_email_response(sender_email, response_text, email_subject)
                return
            
            logger.info(f"Processing email from registered user: {sender_email} (user_id: {user_id})")
            
            # Route message to InteractionManager
            from communication.message_processing.interaction_manager import handle_user_message
            response = handle_user_message(user_id, email_body, "email")
            
            if response and response.message:
                # Send response back via email
                self._send_email_response(sender_email, response.message, f"Re: {email_subject}")
            else:
                logger.warning(f"No response generated for email from user {user_id}")
                
        except Exception as e:
            logger.error(f"Error processing incoming email: {e}", exc_info=True)

    @handle_errors("sending email response", default_return=None)
    def _send_email_response(self, recipient_email: str, response_text: str, subject: str = "Re: Your Message"):
        """Send an email response to a user"""
        try:
            email_channel = self._channels_dict.get('email')
            if not email_channel or not email_channel.is_ready():
                logger.error("Email channel not available for sending response")
                return
            
            # Use the event loop to send email
            if self._main_loop and not self._main_loop.is_closed():
                future = asyncio.run_coroutine_threadsafe(
                    email_channel.send_message(recipient_email, response_text, subject=subject),
                    self._main_loop
                )
                future.result(timeout=10)
            else:
                # Fallback: create temporary loop
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(email_channel.send_message(recipient_email, response_text, subject=subject))
                loop.close()
            
            logger.info(f"Email response sent to {recipient_email}")
        except Exception as e:
            logger.error(f"Error sending email response to {recipient_email}: {e}")

    @handle_errors("initializing channels from config", default_return=False)
    def initialize_channels_from_config(self, channel_configs: Dict[str, ChannelConfig] = None):
        """
        Initialize channels from configuration with validation.
        
        Returns:
            bool: True if successful, False if failed
        """
        # Validate channel_configs
        if channel_configs is not None and not isinstance(channel_configs, dict):
            logger.error(f"Invalid channel_configs: {type(channel_configs)}")
            return False
        """Initialize channels from configuration"""
        if channel_configs is None:
            # Use default configurations
            channel_configs = self._get_default_channel_configs()
        
        self.channel_configs = channel_configs
        
        # Create event loop for async operations if we're not in one
        try:
            # Use get_running_loop() first, fallback to new_event_loop()
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        # Run the async initialization
        return loop.run_until_complete(self.initialize_channels_from_config__initialize_channels_async())

    @handle_errors("initializing channels from config async", default_return=None)
    async def initialize_channels_from_config__initialize_channels_async(self):
        """Async method to initialize all configured channels"""
        logger.debug("Starting async channel initialization.")
        
        for name, config in self.channel_configs.items():
            if not config.enabled:
                logger.info(f"Channel {name} is disabled, skipping")
                continue
                
            channel = ChannelFactory.create_channel(name, config)
            if not channel:
                logger.error(f"Failed to create channel: {name}")
                continue
                
            # Initialize with retry logic
            success = await self._initialize_channel_with_retry(channel, config)
            if success:
                # Store the channel
                self._channels_dict[name] = channel
                logger.debug(f"Channel {name} ready")
            else:
                logger.error(f"Failed to initialize channel {name} after retries")
        
        return len(self._channels_dict) > 0

    async def _initialize_channel_with_retry(self, channel: BaseChannel, config: ChannelConfig) -> bool:
        """Initialize a channel with retry logic"""
        retry_delay = config.retry_delay
        
        for attempt in range(config.max_retries):
            try:
                logger.debug(f"Initializing {channel.config.name}, attempt {attempt + 1}/{config.max_retries}")
                
                # Add timeout to prevent hanging
                try:
                    success = await asyncio.wait_for(
                        channel.initialize(), 
                        timeout=30.0  # 30 second timeout per attempt
                    )
                    if success:
                        logger.info(f"Channel {channel.config.name} initialized on attempt {attempt + 1}")
                        return True
                    else:
                        logger.warning(f"Channel {channel.config.name} initialization returned False on attempt {attempt + 1}")
                        
                        # Special handling for Discord bot - check if it's actually connected
                        if channel.config.name == 'discord' and hasattr(channel, 'is_actually_connected'):
                            if channel.is_actually_connected():
                                logger.info(f"Discord bot is actually connected despite initialization returning False")
                                return True
                        
                except asyncio.TimeoutError:
                    logger.warning(f"Channel {channel.config.name} initialization timed out on attempt {attempt + 1}")
                    
                    # Special handling for Discord bot - check if it's actually connected after timeout
                    if channel.config.name == 'discord' and hasattr(channel, 'is_actually_connected'):
                        if channel.is_actually_connected():
                            logger.info(f"Discord bot is actually connected despite initialization timeout")
                            return True
                
            except Exception as e:
                logger.warning(f"Channel {channel.config.name} initialization attempt {attempt + 1} failed: {e}")
            
            if attempt < config.max_retries - 1:
                logger.debug(f"Waiting {retry_delay} seconds before next attempt for {channel.config.name}")
                await asyncio.sleep(retry_delay)
                retry_delay *= config.backoff_multiplier
        
        logger.error(f"Failed to initialize {channel.config.name} after {config.max_retries} attempts")
        return False

    @handle_errors("getting default channel configs", default_return={})
    def _get_default_channel_configs(self) -> Dict[str, ChannelConfig]:
        """Get default channel configurations"""
        configs = {}
        
        # Only create configs for channels that have tokens/configs available
        
        #         enabled=True,
        #         max_retries=5,
        #         retry_delay=2.0,
        #         backoff_multiplier=2.0
        #     )
        
        if EMAIL_SMTP_SERVER:
            configs['email'] = ChannelConfig(
                name='email',
                enabled=True,
                max_retries=3,
                retry_delay=1.0,
                backoff_multiplier=2.0
            )
        
        if DISCORD_BOT_TOKEN:
            configs['discord'] = ChannelConfig(
                name='discord',
                enabled=True,
                max_retries=3,
                retry_delay=1.5,
                backoff_multiplier=2.0
            )
        
        return configs

    @handle_errors("starting all channels", default_return=False)
    def start_all(self):
        """
        Start all communication channels with validation.
        
        Returns:
            bool: True if successful, False if failed
        """
        """Start all communication channels"""
        logger.debug("Starting all communication channels.")
        
        try:
            # If no channel configs set, load defaults now
            if not self.channel_configs:
                self.channel_configs = self._get_default_channel_configs()
                logger.debug("Loaded default channel configurations for startup")
            # Start the retry thread for failed messages
            self.start_all__start_retry_thread()
            
            # Start the restart monitor
            self.start_all__start_restart_monitor()
            
            # Start email polling if email channel is configured
            if 'email' in self.channel_configs and self.channel_configs['email'].enabled:
                self.start_all__start_email_polling()
            
            # Try async startup first
            try:
                loop = asyncio.get_running_loop()
                # If there's a running loop, just do sync startup
                self._start_sync()
            except RuntimeError:
                # No running loop, safe to create one
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(self._start_all_async())
                    loop.close()
                except Exception:
                    # Fallback to sync startup
                    self._start_sync()
            
            self._running = True
            logger.info("All channels started successfully")
            
        except Exception as e:
            logger.error(f"Error during startup: {e}")
            # Final fallback
            self._start_sync()

    @handle_errors("starting all async channels", default_return=None)
    async def _start_all_async(self):
        """Async method to start all configured channels"""
        logger.debug("Starting async channel startup.")
        
        for name, config in self.channel_configs.items():
            if not config.enabled:
                logger.info(f"Channel {name} is disabled, skipping")
                continue
            # Skip if channel already exists to avoid duplicate instances
            if name in self._channels_dict and self._channels_dict[name] is not None:
                logger.debug(f"Channel {name} already exists, skipping re-creation")
                continue
                
            channel = ChannelFactory.create_channel(name, config)
            if not channel:
                logger.error(f"Failed to create channel: {name}")
                continue
                
            # Initialize with retry logic
            success = await self._initialize_channel_with_retry(channel, config)
            if success:
                # Store the channel
                self._channels_dict[name] = channel
                logger.debug(f"Channel {name} ready")
            else:
                logger.error(f"Failed to initialize channel {name} after retries")
        
        return len(self._channels_dict) > 0

    @handle_errors("starting sync channels", default_return=None)
    def _start_sync(self):
        """Synchronous method to start all configured channels"""
        logger.debug("Starting sync channel startup.")
        
        for name, config in self.channel_configs.items():
            if not config.enabled:
                logger.info(f"Channel {name} is disabled, skipping")
                continue
            # Skip if channel already exists to avoid duplicate instances
            if name in self._channels_dict and self._channels_dict[name] is not None:
                logger.debug(f"Channel {name} already exists, skipping re-creation")
                continue
                
            channel = ChannelFactory.create_channel(name, config)
            if not channel:
                logger.error(f"Failed to create channel: {name}")
                continue
                
            # Initialize with retry logic (sync version)
            success = self._initialize_channel_with_retry_sync(channel, config)
            if success:
                # Store the channel
                self._channels_dict[name] = channel
                logger.debug(f"Channel {name} ready")
            else:
                logger.error(f"Failed to initialize channel {name} after retries")
        
        return len(self._channels_dict) > 0

    def _initialize_channel_with_retry_sync(self, channel: BaseChannel, config: ChannelConfig) -> bool:
        """Synchronous version of channel initialization with retry logic"""
        retry_delay = config.retry_delay
        
        for attempt in range(config.max_retries):
            try:
                logger.debug(f"Initializing {channel.config.name}, attempt {attempt + 1}/{config.max_retries}")
                
                # Try to initialize the channel
                if hasattr(channel, 'initialize'):
                    # If it's an async method, run it in a new event loop
                    try:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        success = loop.run_until_complete(asyncio.wait_for(
                            channel.initialize(), 
                            timeout=30.0  # 30 second timeout per attempt
                        ))
                        loop.close()
                    except asyncio.TimeoutError:
                        logger.warning(f"Channel {channel.config.name} initialization timed out on attempt {attempt + 1}")
                        success = False
                    except Exception as e:
                        logger.warning(f"Channel {channel.config.name} initialization attempt {attempt + 1} failed: {e}")
                        success = False
                else:
                    # If no initialize method, assume it's ready
                    success = True
                
                if success:
                    logger.info(f"Channel {channel.config.name} initialized on attempt {attempt + 1}")
                    return True
                else:
                    logger.warning(f"Channel {channel.config.name} initialization returned False on attempt {attempt + 1}")
                    
                    # Special handling for Discord bot - check if it's actually connected
                    if channel.config.name == 'discord' and hasattr(channel, 'is_actually_connected'):
                        if channel.is_actually_connected():
                            logger.info(f"Discord bot is actually connected despite initialization returning False")
                            return True
                
            except Exception as e:
                logger.warning(f"Channel {channel.config.name} initialization attempt {attempt + 1} failed: {e}")
            
            if attempt < config.max_retries - 1:
                logger.debug(f"Waiting {retry_delay} seconds before next attempt for {channel.config.name}")
                time.sleep(retry_delay)
                retry_delay *= config.backoff_multiplier
        
        logger.error(f"Failed to initialize {channel.config.name} after {config.max_retries} attempts")
        return False

    async def send_message(self, channel_name: str, recipient: str, message: str, **kwargs) -> bool:
        """Send message via specified channel using unified interface"""
        logger.debug(f"Preparing to send message to {recipient} via {channel_name}")
        
        channel = self._channels_dict.get(channel_name)
        if not channel:
            logger.error(f"Channel {channel_name} not found")
            return False
        
        # Special handling for Discord bot - check if it can actually send messages
        if channel_name == 'discord' and hasattr(channel, 'can_send_messages'):
            if not channel.can_send_messages():
                logger.error(f"Channel {channel_name} not ready - cannot send messages")
                # Queue for retry after reconnection
                try:
                    self.send_message_sync__queue_failed_message(
                        kwargs.get('user_id', ''),
                        kwargs.get('category', 'unknown'),
                        message,
                        recipient,
                        channel_name
                    )
                except Exception:
                    pass
                return False
        elif not channel.is_ready():
            # Don't call async get_status() in sync context - just log the issue
            logger.error(f"Channel {channel_name} not ready")
            # Queue for retry after reconnection
            try:
                self.send_message_sync__queue_failed_message(
                    kwargs.get('user_id', ''),
                    kwargs.get('category', 'unknown'),
                    message,
                    recipient,
                    channel_name
                )
            except Exception:
                pass
            return False

        # Check network connectivity with proper error handling
        try:
            if not wait_for_network():
                from core.error_handling import handle_network_error
                handle_network_error(
                    ConnectionError("Network not available"), 
                    "message send", 
                    kwargs.get('user_id')
                )
                return False
        except Exception as network_error:
            from core.error_handling import handle_network_error
            handle_network_error(network_error, "network check", kwargs.get('user_id'))
            return False
        
        try:
            # FIXED: Ensure we're actually awaiting a coroutine
            success = await channel.send_message(recipient, message, **kwargs)
            
            # FIXED: Better return value validation
            # Use == instead of is to handle mock return values correctly
            if success is True or success == True:
                # Enhanced logging with message content and time period
                message_preview = message[:50] + "..." if len(message) > 50 else message
                time_period = kwargs.get('time_period', 'unknown')
                user_id = kwargs.get('user_id', 'unknown')
                category = kwargs.get('category', 'unknown')
                # Log will be handled by the deduplication logic below
                return True
            elif success is False or success == False:
                logger.warning(f"Channel {channel_name} returned False for message send to {recipient}")
                return False
            else:
                # Handle unexpected return values
                logger.warning(f"Channel {channel_name} returned unexpected value: {success} (type: {type(success)})")
                # If it's not explicitly False, assume success if no exception was raised
                return True
            
        except ConnectionError as e:
            from core.error_handling import handle_network_error
            handle_network_error(e, f"message send via {channel_name}", kwargs.get('user_id'))
            return False
        except TimeoutError as e:
            from core.error_handling import handle_network_error
            handle_network_error(e, f"message send via {channel_name}", kwargs.get('user_id'))
            return False
        except Exception as e:
            from core.error_handling import handle_communication_error
            handle_communication_error(e, channel_name, f"message send to {recipient}", kwargs.get('user_id'))
            return False

    def _check_logging_health(self):
        """
        Check if logging is still working and recover if needed.
        
        Verifies that the logging system is functional and attempts to restart it if issues are detected.
        """
        try:
            # Test logging
            test_message = f"Logging health check - {time.time()}"
            logger.debug(test_message)
            
            # Force flush via component logger handlers only (avoid direct logging import in app code)
            for handler in logger.logger.handlers if hasattr(logger, 'logger') else []:
                if hasattr(handler, 'flush'):
                    handler.flush()
            
            logger.debug("Logging health check passed")
            return True
        except Exception as e:
            logger.error(f"Logging health check failed: {e}")
            # Try to restart logging
            from core.logger import force_restart_logging
            if force_restart_logging():
                logger.info("Logging system restarted successfully")
                return True
            return False

    def send_message_sync(self, channel_name: str, recipient: str, message: str, **kwargs) -> bool:
        """Synchronous wrapper with logging health check"""
        # Check logging health periodically
        self._check_logging_health()
        
        # Queue immediately if channel is not ready
        channel = self._channels_dict.get(channel_name)
        not_ready = False
        if not channel:
            not_ready = True
        elif channel_name == 'discord' and hasattr(channel, 'can_send_messages') and not channel.can_send_messages():
            not_ready = True
        elif channel and not channel.is_ready():
            not_ready = True
        if not_ready:
            logger.error(f"Channel {channel_name} not ready - queuing message for retry")
            try:
                self.send_message_sync__queue_failed_message(
                    kwargs.get('user_id', ''),
                    kwargs.get('category', 'unknown'),
                    message,
                    recipient,
                    channel_name
                )
            except Exception as e:
                logger.warning(f"Failed to queue message for retry: {e}")
            return False
        
        try:
            # Double-check channel exists before attempting to send
            # This is a defensive check in case we somehow got past the earlier check
            if channel_name not in self._channels_dict:
                logger.error(f"Channel {channel_name} not found in channels_dict - cannot send")
                return False
            
            # Get the underlying bot directly
            if channel_name == 'discord':
                discord_channel = self._channels_dict.get('discord')
                if discord_channel and hasattr(discord_channel, 'bot'):
                    # Use the discord.py sync methods if available
                    bot = discord_channel.bot
                    
                    # Try to send via the bot's sync methods
                    try:
                        # Handle special Discord user format - skip sync method for discord_user: format
                        if recipient.startswith("discord_user:"):
                            # This format is handled by the async send_message method
                            # Skip the sync channel lookup for discord_user: format
                            pass
                        else:
                            # Try to convert to integer for channel ID
                            channel = bot.get_channel(int(recipient))
                            if channel:
                                # This is hacky but might work
                                import asyncio
                                loop = asyncio.new_event_loop()
                                asyncio.set_event_loop(loop)
                                loop.run_until_complete(channel.send(message))
                                loop.close()
                                logger.info(f"Direct Discord message sent to channel {recipient}")
                                return True
                    except Exception as e:
                        logger.error(f"Direct Discord send failed: {e}")
                        
            # Fallback to async send
            # Note: This should only be reached if channel exists and is ready
            # If we get here with a non-existent channel, something went wrong
            try:
                result = self.send_message_sync__run_async_sync(
                    self.send_message(channel_name, recipient, message, **kwargs)
                )
                # Ensure we return False if result is None or unexpected
                if result is None:
                    logger.warning(f"Async send_message returned None for channel {channel_name}")
                    return False
                return result
            except Exception as e:
                logger.error(f"Fallback async send failed: {e}")
                return False
            
        except Exception as e:
            logger.error(f"Error in simplified send_message_sync: {e}")
            # Queue for retry if this is a scheduled message
            if 'user_id' in kwargs and 'category' in kwargs:
                self.send_message_sync__queue_failed_message(
                    kwargs['user_id'],
                    kwargs['category'],
                    message,
                    recipient,
                    channel_name
                )
            return False

    async def broadcast_message(self, recipients: Dict[str, str], message: str) -> Dict[str, bool]:
        """Send message to multiple channels"""
        logger.debug(f"Broadcasting message to {len(recipients)} channels")
        results = {}
        
        # Create tasks for all sends
        tasks = []
        for channel_name, recipient in recipients.items():
            if channel_name in self._channels_dict:
                task = asyncio.create_task(
                    self.send_message(channel_name, recipient, message),
                )
                tasks.append((channel_name, task))
            else:
                logger.warning(f"Channel {channel_name} not available for broadcast")
                results[channel_name] = False
        
        # Wait for all tasks to complete
        for channel_name, task in tasks:
            try:
                results[channel_name] = await task
            except Exception as e:
                logger.error(f"Error in broadcast to {channel_name}: {e}")
                results[channel_name] = False
        
        successful = sum(results.values())
        logger.info(f"Broadcast completed: {successful}/{len(recipients)} channels successful")
        return results

    async def get_channel_status(self, channel_name: str) -> Optional[ChannelStatus]:
        """Get status of a specific channel"""
        channel = self._channels_dict.get(channel_name)
        if channel:
            try:
                return await channel.get_status()
            except Exception as e:
                logger.error(f"Error getting status for channel {channel_name}: {e}")
                return None
        return None

    @handle_errors("getting all channel statuses", default_return={})
    async def get_all_statuses(self) -> Dict[str, ChannelStatus]:
        """Get status of all channels"""
        statuses = {}
        for name, channel in self._channels_dict.items():
            if channel:
                statuses[name] = await channel.get_status()
        return statuses

    async def health_check_all(self) -> Dict[str, Any]:
        """Perform health check on all channels"""
        health_results = {}
        
        for name, channel in self._channels_dict.items():
            if channel:
                try:
                    health_results[name] = await channel.get_health_status()
                except Exception as e:
                    health_results[name] = {
                        'status': 'error',
                        'error': str(e)
                    }
        
        return health_results

    @handle_errors("getting Discord connectivity status", default_return=None)
    def get_discord_connectivity_status(self) -> Optional[Dict[str, Any]]:
        """Get detailed Discord connectivity status if available"""
        if 'discord' in self._channels_dict:
            discord_channel = self._channels_dict['discord']
            if hasattr(discord_channel, 'get_health_status'):
                return discord_channel.get_health_status()
        return None

    async def _shutdown_all_async(self):
        """Async method to shutdown all channels"""
        for name, channel in list(self._channels_dict.items()):
            if channel is not None:
                try:
                    await channel.shutdown()
                    logger.info(f"Channel {name} shutdown successfully")
                except Exception as e:
                    logger.error(f"Error shutting down {name}: {e}")
        
        self._channels_dict.clear()

    @handle_errors("stopping all channels", default_return=False)
    def stop_all(self):
        """
        Stop all communication channels with validation.
        
        Returns:
            bool: True if successful, False if failed
        """
        """Stop all communication channels"""
        logger.debug("Stopping all communication channels.")
        
        try:
            # Stop the retry thread first
            self.stop_all__stop_retry_thread()
            
            # Stop the restart monitor
            self.stop_all__stop_restart_monitor()
            
            # Try async shutdown first
            try:
                loop = asyncio.get_running_loop()
                # If there's a running loop, just do sync shutdown
                self._shutdown_sync()
            except RuntimeError:
                # No running loop, safe to create one
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    # Add timeout to prevent hanging
                    try:
                        loop.run_until_complete(asyncio.wait_for(self._shutdown_all_async(), timeout=15.0))
                    except asyncio.TimeoutError:
                        logger.warning("Channel shutdown timed out after 15 seconds - forcing sync shutdown")
                        self._shutdown_sync()
                    loop.close()
                except Exception as e:
                    logger.error(f"Error in async shutdown: {e}")
                    # Fallback to sync shutdown
                    self._shutdown_sync()
            
            self._running = False
            logger.info("All channels stopped successfully")
            
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
            # Final fallback
            self._shutdown_sync()

    def _shutdown_sync(self):
        """
        Synchronous shutdown method for all channels.
        
        Stops all communication channels and cleans up resources.
        """
        logger.info("Shutting down CommunicationManager...")
        self._running = False
        
        # Stop email polling
        self.stop_all__stop_email_polling()
        
        # Stop all channels
        for name, channel in self._channels_dict.items():
            try:
                if hasattr(channel, 'shutdown'):
                    # Add timeout to prevent hanging
                    try:
                        asyncio.run(asyncio.wait_for(channel.shutdown(), timeout=10.0))
                    except asyncio.TimeoutError:
                        logger.warning(f"Channel {name} shutdown timed out after 10 seconds")
                    except RuntimeError:
                        # Event loop already running - try sync approach
                        logger.warning(f"Could not run async shutdown for {name} - event loop conflict")
                elif hasattr(channel, 'stop'):
                    channel.stop()  # Fallback for any remaining legacy channels
                logger.debug(f"Channel {name} stopped")
            except Exception as e:
                logger.error(f"Error stopping channel {name}: {e}")
        
        # Stop event loop
        if self._main_loop and not self._main_loop.is_closed():
            try:
                self._main_loop.call_soon_threadsafe(self._main_loop.stop)
                if self._loop_thread and self._loop_thread.is_alive():
                    self._loop_thread.join(timeout=5)
            except Exception as e:
                logger.error(f"Error stopping event loop: {e}")
        
        logger.info("CommunicationManager shutdown complete")

    async def receive_messages(self) -> List[Dict[str, Any]]:
        """Receive messages from all communication channels"""
        logger.debug("Receiving messages from all communication channels.")
        all_messages = []
        
        for channel_name, channel in self._channels_dict.items():
            if not channel.is_ready():
                continue
                
            try:
                messages = await channel.receive_messages()
                # Add channel info to each message
                for msg in messages:
                    msg['channel'] = channel_name
                all_messages.extend(messages)
            except Exception as e:
                logger.error(f"Failed to receive messages from {channel_name}: {e}")

        logger.info(f"Total messages received: {len(all_messages)}")
        return all_messages

    @handle_errors("handling message sending", default_return=None)
    def handle_message_sending(self, user_id: str, category: str):
        """
        Handle sending messages for a user and category with improved recipient resolution.
        Now uses scheduled check-ins instead of random replacement.
        """
        logger.debug(f"Handling message sending for user_id: {user_id}, category: {category}")
        
        if not user_id:
            logger.error("User ID is not provided.")
            return

        # Get user preferences
        prefs_result = get_user_data(user_id, 'preferences', normalize_on_read=True)
        preferences = prefs_result.get('preferences')
        if not preferences:
            logger.error(f"User preferences not found for user {user_id}.")
            return

        messaging_service = preferences.get('channel', {}).get('type')
        if not messaging_service:
            logger.error(f"No messaging service configured for user {user_id}")
            return

        # Get the appropriate recipient ID for the messaging service
        recipient = self._get_recipient_for_service(user_id, messaging_service, preferences)
        if not recipient:
            logger.error(f"No valid recipient found for user {user_id} with service {messaging_service}")
            return

        # Handle check-in category specially
        if category == "checkin":
            self._handle_scheduled_checkin(user_id, messaging_service, recipient)
            return

        # Handle AI-generated messages and track if message was actually sent
        message_sent = False
        sent_message_content = None
        if category in ["personalized", "ai_personalized"]:
            message_sent, sent_message_content = self._send_ai_generated_message(user_id, category, messaging_service, recipient)
        else:
            message_sent, sent_message_content = self._send_predefined_message(user_id, category, messaging_service, recipient)
        
        # Store sent message content for response file (if this is a test message request)
        if sent_message_content:
            self._last_sent_message = {
                'user_id': user_id,
                'category': category,
                'message': sent_message_content
            }
        
        # CRITICAL: Only expire check-in flows if a message was actually sent and delivered
        # Don't expire flows for failed sends or when no message was available to send
        if message_sent:
            # Expire active check-in flows ONLY for non-scheduled messages to avoid user confusion
            # Scheduled messages (motivational, health, etc.) are expected and shouldn't cancel active check-ins
            # Only cancel check-in flows when we're responding to user input with unrelated content
            self._expire_checkin_flow_if_needed(user_id, category)
            
            # Message sending completion already logged above with full details
        else:
            logger.debug(f"No message sent for user {user_id}, category {category} - preserving any active check-in flow")

    @handle_errors("expiring check-in flow if needed", user_friendly=False, default_return=None)
    def _expire_checkin_flow_if_needed(self, user_id: str, category: str):
        """Expire check-in flow if this is a non-scheduled message."""
        # Determine if this is a scheduled message or a response to user input
        is_scheduled_message = category in ['motivational', 'health', 'checkin', 'task_reminders']
        
        if not is_scheduled_message:
            # This is a response to user input - expire any active check-in flow
            from communication.message_processing.conversation_flow_manager import conversation_manager
            conversation_manager.expire_checkin_flow_due_to_unrelated_outbound(user_id)
            logger.debug(f"Expired check-in flow for user {user_id} due to unrelated response message")
        else:
            logger.debug(f"Skipping check-in flow expiration for scheduled {category} message to user {user_id}")

    @handle_errors("getting recipient for service", default_return=None)
    def _get_recipient_for_service(self, user_id: str, messaging_service: str, preferences: dict) -> Optional[str]:
        """
        Get recipient for service with validation.
        
        Returns:
            Optional[str]: Recipient ID, None if failed
        """
        # Validate user_id
        if not user_id or not isinstance(user_id, str):
            logger.error(f"Invalid user_id: {user_id}")
            return None
            
        if not user_id.strip():
            logger.error("Empty user_id provided")
            return None
            
        # Validate messaging_service
        if not messaging_service or not isinstance(messaging_service, str):
            logger.error(f"Invalid messaging_service: {messaging_service}")
            return None
            
        if not messaging_service.strip():
            logger.error("Empty messaging_service provided")
            return None
            
        # Validate preferences
        if not preferences or not isinstance(preferences, dict):
            logger.error(f"Invalid preferences: {preferences}")
            return None
        """Get the appropriate recipient ID for the messaging service"""
        if messaging_service == "discord":
            # For Discord, we need to get the channel ID, not the user ID
            # The Discord bot handles user ID mapping internally
            # We'll use a special marker that the Discord bot can recognize
            return f"discord_user:{user_id}"

            return None
        elif messaging_service == "email":
            # Get email from account.json, not preferences
            # Get user account data
            user_data_result = get_user_data(user_id, 'account', normalize_on_read=True)
            account_data = user_data_result.get('account')
            if not account_data:
                logger.error(f"User account not found for {user_id}")
                return False
            return account_data.get('email', '') if account_data else None
        else:
            logger.error(f"Unknown messaging service: {messaging_service}")
            return None

    def _should_send_checkin_prompt(self, user_id: str, checkin_prefs: dict) -> bool:
        """
        Determine if it's time to send a check-in prompt based on user preferences.
        For check-ins, we respect the schedule-based approach - if the scheduler
        triggered this function, it means it's time for a check-in during the
        scheduled period.
        """
        try:
            frequency = checkin_prefs.get('frequency', 'daily')
            
            # If frequency is set to "none" or "manual", never auto-prompt
            if frequency in ['none', 'manual']:
                logger.debug(f"User {user_id} has check-in frequency set to '{frequency}', skipping auto-prompt")
                return False
            
            # For check-ins, we trust the scheduler to determine timing
            # The scheduler only calls this during the scheduled time period
            # So if we get here, it's time for a check-in
            logger.debug(f"Check-in scheduled for user {user_id} during scheduled time period")
            return True
                
        except Exception as e:
            logger.error(f"Error determining if check-in prompt should be sent for user {user_id}: {e}")
            # Default to sending check-in if there's an error
            return True

    @handle_errors("handling scheduled check-in", user_friendly=False, default_return=None)
    def _handle_scheduled_checkin(self, user_id: str, messaging_service: str, recipient: str):
        """
        Handle scheduled check-in messages based on user preferences and frequency.
        """
        prefs_result = get_user_data(user_id, 'preferences', normalize_on_read=True)
        preferences = prefs_result.get('preferences')
        if not preferences:
            logger.error(f"User preferences not found for user {user_id}")
            return
        
        # Check if check-ins are enabled in account features
        # Get user account data
        user_data_result = get_user_data(user_id, 'account', normalize_on_read=True)
        account_data = user_data_result.get('account')
        if not account_data or account_data.get('features', {}).get('checkins') != 'enabled':
            logger.debug(f"Check-ins disabled for user {user_id}")
            return
        
        checkin_prefs = preferences.get('checkin_settings', {})
        
        # Check frequency and last check-in time
        frequency = checkin_prefs.get('frequency', 'daily')
        
        # If frequency is "none", don't send scheduled check-ins
        if frequency == 'none':
            logger.debug(f"Check-in frequency set to 'none' for user {user_id}, skipping scheduled check-in")
            return
        
        # Check if it's time for a check-in based on frequency
        if self._should_send_checkin_prompt(user_id, checkin_prefs):
            self._send_checkin_prompt(user_id, messaging_service, recipient)
            logger.info(f"Sent scheduled check-in prompt to user {user_id}")
        else:
            logger.debug(f"Check-in not due yet for user {user_id}")

    def _send_checkin_prompt(self, user_id: str, messaging_service: str, recipient: str):
        """
        Send a check-in prompt message to start the check-in flow.
        """
        try:
            # Initialize the dynamic check-in flow properly
            from communication.message_processing.conversation_flow_manager import conversation_manager
            
            # Initialize flow without logging start yet; log only after successful send
            reply_text, completed = conversation_manager._start_dynamic_checkin(user_id)
            
            # Create custom view for check-in buttons (Discord only)
            # Note: Views are created lazily within the Discord async context to avoid event loop errors
            custom_view = None
            if messaging_service == 'discord':
                try:
                    # Import here to avoid circular dependencies
                    from communication.communication_channels.discord.checkin_view import get_checkin_view
                    # Try to create view, but handle event loop errors gracefully
                    import asyncio
                    try:
                        # Check if we're in an async context
                        asyncio.get_running_loop()
                        # We're in async context, safe to create view
                        custom_view = get_checkin_view(user_id)
                    except RuntimeError:
                        # No running event loop - view will be created lazily in Discord thread
                        # Pass a factory function instead
                        @handle_errors("creating check-in view", default_return=None)
                        def create_view():
                            return get_checkin_view(user_id)
                        custom_view = create_view
                except Exception as e:
                    logger.warning(f"Could not create check-in view for Discord: {e}")
            
            # Send the initial message to the user with retry support
            success = self.send_message_sync(messaging_service, recipient, reply_text, 
                                           user_id=user_id, category="checkin", view=custom_view)
            
            if success:
                logger.info(f"Successfully sent check-in prompt to user {user_id} and initialized flow")
                # Now record the check-in start in user activity
                try:
                    user_logger = get_component_logger('user_activity')
                    user_logger.info("User check-in started", user_id=user_id, checkin_type="daily")
                except Exception:
                    pass
            else:
                logger.warning(f"Failed to send check-in prompt to user {user_id}")
                # Preserve conversation state so we can retry sending when channel recovers
                
        except Exception as e:
            logger.error(f"Error sending check-in prompt to user {user_id}: {e}")
            # Preserve conversation state to allow retry after recovery

    def _send_ai_generated_message(self, user_id: str, category: str, messaging_service: str, recipient: str) -> tuple[bool, str | None]:
        """
        Send an AI-generated personalized message using contextual AI.
        
        Returns:
            tuple[bool, str | None]: (success, message_content) - True if sent successfully, and the message content that was sent
        """
        try:
            from ai.chatbot import get_ai_chatbot
            ai_bot = get_ai_chatbot()
            
            # Use contextual AI for richer, more personalized messages
            if category in ["personalized", "ai_personalized"]:
                # Create a contextual prompt for personalized message generation
                context_prompt = "Generate a supportive, personalized message based on my recent activity and mood."
                message_to_send = ai_bot.generate_contextual_response(user_id, context_prompt, timeout=15)
            else:
                # Fallback to standard personalized message
                message_to_send = ai_bot.generate_personalized_message(user_id)
            
            import uuid
            message_id = str(uuid.uuid4())

            success = self.send_message_sync(messaging_service, recipient, message_to_send, 
                                           user_id=user_id, category=category)
            if success:
                # Get current time period for storage
                matching_periods, valid_periods = get_current_time_periods_with_validation(user_id, category)
                current_time_period = matching_periods[0] if matching_periods else None
                store_sent_message(user_id, category, message_id, message_to_send, time_period=current_time_period)
                # Enhanced logging with message content
                message_preview = message_to_send[:50] + "..." if len(message_to_send) > 50 else message_to_send
                logger.info(f"Sent contextual AI-generated message for user {user_id}, category {category} | Content: '{message_preview}'")
                return True, message_to_send
            else:
                logger.error(f"Failed to send AI-generated message for user {user_id}")
                return False, None
                
        except Exception as e:
            logger.error(f"Error sending AI-generated message for user {user_id}: {e}")
            return False, None

    def _send_predefined_message(self, user_id: str, category: str, messaging_service: str, recipient: str) -> tuple[bool, str | None]:
        """
        Send a pre-defined message from the user's message library with deduplication.
        
        Returns:
            tuple[bool, str | None]: (success, message_content) - True if sent successfully, and the message content that was sent
        """
        try:
            matching_periods, valid_periods = get_current_time_periods_with_validation(user_id, category)
            logger.debug(f"MESSAGE_SELECTION: User {user_id}, category {category} | Matching periods: {matching_periods}, Valid periods: {valid_periods}")
            
            # Remove 'ALL' from matching_periods if there are other periods
            if 'ALL' in matching_periods and len(matching_periods) > 1:
                matching_periods = [p for p in matching_periods if p != 'ALL']
                logger.debug(f"MESSAGE_SELECTION: Removed 'ALL' from matching_periods, now: {matching_periods}")
            # If no periods match (other than ALL), use ALL as fallback
            if not matching_periods and 'ALL' in valid_periods:
                matching_periods = ['ALL']
                logger.debug(f"MESSAGE_SELECTION: Using 'ALL' as fallback period")

            # Use new user-specific message file structure
            from pathlib import Path
            user_messages_dir = Path(get_user_data_dir(user_id)) / 'messages'
            file_path = user_messages_dir / f"{category}.json"
            data = load_json_data(str(file_path))  # Convert Path to string
            # Normalize messages file shape for robust selection
            try:
                from core.schemas import validate_messages_file_dict
                if isinstance(data, dict):
                    data, _ = validate_messages_file_dict(data)
            except Exception:
                pass

            if not data or 'messages' not in data:
                logger.error(f"MESSAGE_SELECTION_ERROR: No messages found for category {category} and user {user_id}.")
                return False, None

            # Get current day for filtering
            current_days = get_current_day_names()
            logger.debug(f"MESSAGE_SELECTION: Current days: {current_days}")
            logger.debug(f"MESSAGE_SELECTION: Total messages in library: {len(data['messages'])}")

            # Get all available messages for the current time period
            all_messages = [
                msg for msg in data['messages']
                if any(day in msg['days'] for day in current_days)
                and any(period in msg['time_periods'] for period in matching_periods)
            ]
            
            if not all_messages:
                logger.warning(f"MESSAGE_SELECTION_NO_MATCH: No messages found for user {user_id}, category {category} | Current days: {current_days}, Matching periods: {matching_periods}, Total messages: {len(data['messages'])}")
                # Sample first 3 messages to show what we're looking for
                sample_messages = data['messages'][:3]
                for i, msg in enumerate(sample_messages):
                    logger.debug(f"MESSAGE_SELECTION_SAMPLE_{i}: days={msg.get('days')}, time_periods={msg.get('time_periods')}, message_preview='{msg.get('message', '')[:50]}'")
                return False, None

            # ENHANCED: Apply deduplication logic to time-period-filtered messages
            from core.message_management import get_recent_messages
            
            # Get recent messages to check for duplicates
            recent_messages = get_recent_messages(user_id, category=category, limit=50, days_back=60)
            recent_content = {msg.get('message', '').strip().lower() for msg in recent_messages if msg.get('message')}
            
            # Filter out recent duplicates from time-period-filtered messages
            available_messages = []
            for msg in all_messages:
                message_content = msg.get('message', '').strip()
                if message_content and message_content.lower() not in recent_content:
                    available_messages.append(msg)
            
            if not available_messages:
                logger.info(f"No messages available after deduplication for user {user_id}, category {category}. All time-period messages were sent recently.")
                # Fallback: if all time-period messages are recent, select from all time-period messages
                available_messages = all_messages
                logger.info(f"Using fallback: selecting from all {len(available_messages)} time-period messages")
            
            # Select a message using weighted selection (prioritizes specific time periods over 'ALL')
            message_to_send = self._select_weighted_message(available_messages, matching_periods)
            logger.debug(f"Selected message for user {user_id}, category {category} from {len(available_messages)} available messages")
            
            # IMPROVED: Better success/failure tracking
            try:
                success = self.send_message_sync(messaging_service, recipient, message_to_send['message'], 
                                               user_id=user_id, category=category)
                
                if success:
                    from core.message_management import store_sent_message
                    # Get the current time period for storage
                    current_time_period = matching_periods[0] if matching_periods else None
                    store_sent_message(user_id, category, message_to_send['message_id'], message_to_send['message'], time_period=current_time_period)
                    # Enhanced logging with message content and time period
                    message_preview = message_to_send['message'][:50] + "..." if len(message_to_send['message']) > 50 else message_to_send['message']
                    logger.info(f"Message sent successfully via {messaging_service} to {recipient} | User: {user_id}, Category: {category}, Period: {current_time_period} | Content: '{message_preview}'")
                    return True, message_to_send['message']
                else:
                    # Enhanced logging with message content and time period
                    current_time_period = matching_periods[0] if matching_periods else None
                    message_preview = message_to_send['message'][:50] + "..." if len(message_to_send['message']) > 50 else message_to_send['message']
                    logger.warning(f"Message send returned False but may have still been delivered for user {user_id}, category {category} | Period: {current_time_period} | Content: '{message_preview}'")
                    # Still store it since the message might have gone through
                    from core.message_management import store_sent_message
                    store_sent_message(user_id, category, message_to_send['message_id'], message_to_send['message'], time_period=current_time_period)
                    return True, message_to_send['message']  # Message was attempted and likely delivered
                    
            except Exception as send_error:
                logger.error(f"Exception during message send for user {user_id}, category {category}: {send_error}")
                # Don't store the message if there was an exception
                return False, None

        except Exception as e:
            logger.error(f"Error in predefined message handling for user {user_id}, category {category}: {e}")
            return False, None


    # NEW METHODS: More specific channel management methods
    @handle_errors("getting active channels", default_return=[])
    def get_active_channels(self) -> List[str]:
        """
        Get active channels with validation.
        
        Returns:
            List[str]: List of active channels, empty list if failed
        """
        """Get list of currently active/running channels"""
        return list(self._channels_dict.keys())
    
    @handle_errors("getting configured channels", default_return=[])
    def get_configured_channels(self) -> List[str]:
        """
        Get configured channels with validation.
        
        Returns:
            List[str]: List of configured channels, empty list if failed
        """
        """Get list of channels that are configured (from config)"""
        from core.config import get_available_channels
        return get_available_channels()
    
    @handle_errors("getting registered channels", default_return=[])
    def get_registered_channels(self) -> List[str]:
        """
        Get registered channels with validation.
        
        Returns:
            List[str]: List of registered channels, empty list if failed
        """
        """Get list of channels that are registered in the factory"""
        from communication.core.factory import ChannelFactory
        return ChannelFactory.get_registered_channels()

    @handle_errors("handling task reminder", default_return=None)
    def handle_task_reminder(self, user_id: str, task_id: str):
        """
        Handle task reminder with validation.
        
        Returns:
            None: Always returns None
        """
        # Validate user_id
        if not user_id or not isinstance(user_id, str):
            logger.error(f"Invalid user_id: {user_id}")
            return None
            
        if not user_id.strip():
            logger.error("Empty user_id provided")
            return None
            
        # Validate task_id
        if not task_id or not isinstance(task_id, str):
            logger.error(f"Invalid task_id: {task_id}")
            return None
            
        if not task_id.strip():
            logger.error("Empty task_id provided")
            return None
        """
        Handle sending task reminders for a user.
        """
        logger.debug(f"Handling task reminder for user_id: {user_id}, task_id: {task_id}")
        
        if not user_id or not task_id:
            logger.error("User ID and task ID are required for task reminder.")
            return

        # Import task management functions
        from tasks.task_management import get_task_by_id, are_tasks_enabled
        
        # Check if tasks are enabled for this user
        if not are_tasks_enabled(user_id):
            logger.debug(f"Tasks not enabled for user {user_id}")
            return

        # Get the task details
        task = get_task_by_id(user_id, task_id)
        if not task:
            logger.error(f"Task {task_id} not found for user {user_id}")
            return

        # Check if task is still active
        if task.get('completed', False):
            logger.debug(f"Task {task_id} is already completed, skipping reminder")
            return

        # Get user preferences
        prefs_result = get_user_data(user_id, 'preferences')
        preferences = prefs_result.get('preferences')
        if not preferences:
            logger.error(f"User preferences not found for user {user_id}.")
            return

        messaging_service = preferences.get('channel', {}).get('type')
        if not messaging_service:
            logger.error(f"No messaging service configured for user {user_id}")
            return

        # Get the appropriate recipient ID for the messaging service
        recipient = self._get_recipient_for_service(user_id, messaging_service, preferences)
        if not recipient:
            logger.error(f"No valid recipient found for user {user_id} with service {messaging_service}")
            return

        # Create the task reminder message
        reminder_message = self._create_task_reminder_message(task)
        
        # Create custom view for task reminder buttons (Discord only)
        # Note: Views are created lazily within the Discord async context to avoid event loop errors
        custom_view = None
        if messaging_service == 'discord':
            try:
                from communication.communication_channels.discord.task_reminder_view import get_task_reminder_view
                task_title = task.get('title', 'Untitled Task')
                # Try to create view, but handle event loop errors gracefully
                import asyncio
                try:
                    # Check if we're in an async context
                    asyncio.get_running_loop()
                    # We're in async context, safe to create view
                    custom_view = get_task_reminder_view(user_id, task_id, task_title)
                except RuntimeError:
                    # No running event loop - view will be created lazily in Discord thread
                    # Pass a factory function instead
                    @handle_errors("creating task reminder view", default_return=None)
                    def create_view():
                        return get_task_reminder_view(user_id, task_id, task_title)
                    custom_view = create_view
            except Exception as e:
                logger.warning(f"Could not create task reminder view for Discord: {e}")
        
        # Send the reminder
        success = self.send_message_sync(messaging_service, recipient, reminder_message, view=custom_view)
        
        if success:
            logger.info(f"Task reminder sent successfully for user {user_id}, task {task_id}")
            # Track the last task reminder for this user
            self._last_task_reminders[user_id] = task_id
        else:
            logger.error(f"Failed to send task reminder for user {user_id}, task {task_id}")

    @handle_errors("getting last task reminder", default_return=None)
    def get_last_task_reminder(self, user_id: str) -> Optional[str]:
        """
        Get last task reminder with validation.
        
        Returns:
            Optional[str]: Last task reminder, None if failed
        """
        # Validate user_id
        if not user_id or not isinstance(user_id, str):
            logger.error(f"Invalid user_id: {user_id}")
            return None
            
        if not user_id.strip():
            logger.error("Empty user_id provided")
            return None
        """
        Get the task ID of the last task reminder sent to a user.
        
        Args:
            user_id: The user's ID
            
        Returns:
            The task ID of the last reminder, or None if no reminder was sent
        """
        return self._last_task_reminders.get(user_id)

    @handle_errors("creating task reminder message", default_return="Task reminder")
    def _create_task_reminder_message(self, task: dict) -> str:
        """
        Create task reminder message with validation.
        
        Returns:
            str: Task reminder message, default if failed
        """
        # Validate task
        if not task or not isinstance(task, dict):
            logger.error(f"Invalid task: {task}")
            return "Task reminder"
        """
        Create a formatted task reminder message.
        """
        title = task.get('title', 'Untitled Task')
        description = task.get('description', '')
        due_date = task.get('due_date', '')
        priority = task.get('priority', 'medium')
        task_id = task.get('task_id', '')
        # Tasks now use tags instead of categories
        
        # Create priority emoji
        priority_emoji = {
            'low': '🟢',
            'medium': '🟡', 
            'high': '🔴',
            'critical': '🚨'
        }.get(priority, '🟡')
        
        # Build the message
        message = f"💡 **Task Reminder:** {priority_emoji}\n\n"
        message += f"**{title}**\n"
        
        if description:
            message += f"{description}\n\n"
        
        if due_date:
            message += f"📅 **Due:** {due_date}\n"
        
        message += f"⚡ **Priority:** {priority.title()}"
        
        return message

    @handle_errors("selecting weighted message", default_return="")
    def _select_weighted_message(self, available_messages, matching_periods):
        """
        Select weighted message with validation.
        
        Returns:
            str: Selected message, empty string if failed
        """
        # Validate available_messages
        if not available_messages or not isinstance(available_messages, list):
            logger.error(f"Invalid available_messages: {available_messages}")
            return ""
            
        # Validate matching_periods
        if not matching_periods or not isinstance(matching_periods, list):
            logger.error(f"Invalid matching_periods: {matching_periods}")
            return ""
        """
        Select a message using a weighting system that prioritizes
        messages with specific time periods over 'ALL' time periods.
        
        Args:
            available_messages: List of available messages
            matching_periods: List of current matching time periods
            
        Returns:
            Selected message
        """
        import random
        
        if not available_messages:
            return None
        
        # Separate messages into two groups:
        # 1. Messages with specific time periods (higher priority)
        # 2. Messages with only 'ALL' time periods (lower priority)
        
        specific_period_messages = []
        all_period_messages = []
        
        for msg in available_messages:
            time_periods = msg.get('time_periods', [])
            # Check if message has any specific time periods (not just 'ALL')
            has_specific_periods = any(period != 'ALL' for period in time_periods)
            
            if has_specific_periods:
                specific_period_messages.append(msg)
            else:
                all_period_messages.append(msg)
        
        # Weighted selection: 70% chance for specific periods, 30% chance for 'ALL' periods
        if specific_period_messages and random.random() < 0.7:
            # Select from specific period messages
            selected_message = random.choice(specific_period_messages)
            logger.debug(f"Selected message with specific time periods (weighted selection)")
        elif all_period_messages:
            # Select from 'ALL' period messages
            selected_message = random.choice(all_period_messages)
            logger.debug(f"Selected message with 'ALL' time periods (weighted selection)")
        else:
            # Fallback to any available message
            selected_message = random.choice(available_messages)
            logger.debug(f"Selected message (fallback selection)")
        
        return selected_message