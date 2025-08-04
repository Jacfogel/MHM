# communication_manager.py

import asyncio
import threading
import time
import queue
import random
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta

from core.logger import get_logger
from core.error_handling import handle_errors
from bot.base_channel import BaseChannel, ChannelConfig, ChannelStatus, ChannelType
from bot.channel_factory import ChannelFactory
from core.user_data_handlers import get_user_data, get_all_user_ids
from core.response_tracking import get_recent_daily_checkins
from core.message_management import store_sent_message
from core.schedule_management import get_current_time_periods_with_validation, get_current_day_names
from core.file_operations import determine_file_path, load_json_data
import os
from core.config import EMAIL_SMTP_SERVER, DISCORD_BOT_TOKEN, get_user_data_dir
from core.service_utilities import wait_for_network

logger = get_logger(__name__)

@dataclass
class QueuedMessage:
    """Represents a message that failed to send and is queued for retry"""
    user_id: str
    category: str
    message: str
    recipient: str
    channel_name: str
    timestamp: datetime
    retry_count: int = 0
    max_retries: int = 3
    retry_delay: int = 300  # 5 minutes

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
    
    def __new__(cls, *args, **kwargs):
        """Ensure that only one instance of the CommunicationManager exists (Singleton pattern)."""
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(CommunicationManager, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        """Initialize the object."""
        if self._initialized:
            return
            
        try:
            logger.debug("CommunicationManager initializing...")
            self.channels: Dict[str, BaseChannel] = {}
            self.channel_configs: Dict[str, ChannelConfig] = {}
            self.scheduler_manager = None
            self._running = False
            
            # Centralized event loop management
            self._main_loop = None
            self._loop_thread = None
            self._setup_event_loop()
            
            # Message retry queue
            self._failed_message_queue = queue.Queue()
            self._retry_thread = None
            self._retry_running = False
            
            # For backward compatibility
            self._legacy_channels = {}
            
            self._initialized = True
            logger.info("CommunicationManager ready")
        except Exception as e:
            logger.error(f"Error during CommunicationManager initialization: {e}", exc_info=True)
            raise

    def _setup_event_loop(self):
        """Set up a dedicated event loop for async operations"""
        try:
            # Try to get existing loop
            self._main_loop = asyncio.get_event_loop()
            if self._main_loop.is_running():
                # Create new loop for our operations
                import threading
                def run_event_loop():
                    """
                    Run the event loop in a separate thread for async operations.
                    
                    This nested function is used to manage the event loop for async channel operations.
                    """
                    self._main_loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(self._main_loop)
                    self._main_loop.run_forever()
                
                self._loop_thread = threading.Thread(target=run_event_loop, daemon=True)
                self._loop_thread.start()
                
                # Wait a moment for loop to start
                import time
                time.sleep(0.1)
        except RuntimeError:
            # No event loop exists
            self._main_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._main_loop)
    
    def _run_async_sync(self, coro):
        """Run async function synchronously using our managed loop"""
        if self._loop_thread:
            # Submit to running loop
            future = asyncio.run_coroutine_threadsafe(coro, self._main_loop)
            return future.result(timeout=30)  # 30 second timeout
        else:
            # Use current loop
            return self._main_loop.run_until_complete(coro)

    def set_scheduler_manager(self, scheduler_manager):
        """Set the scheduler manager for the communication manager."""
        self.scheduler_manager = scheduler_manager
        logger.debug("Scheduler manager set in CommunicationManager.")

    def _queue_failed_message(self, user_id: str, category: str, message: str, recipient: str, channel_name: str):
        """Queue a failed message for retry"""
        queued_message = QueuedMessage(
            user_id=user_id,
            category=category,
            message=message,
            recipient=recipient,
            channel_name=channel_name,
            timestamp=datetime.now()
        )
        self._failed_message_queue.put(queued_message)
        logger.info(f"Queued failed message for user {user_id}, category {category} for retry")

    def _start_retry_thread(self):
        """Start the retry thread for failed messages"""
        if self._retry_thread and self._retry_thread.is_alive():
            return
        
        self._retry_running = True
        self._retry_thread = threading.Thread(target=self._retry_loop, daemon=True)
        self._retry_thread.start()
        logger.info("Started message retry thread")

    def _stop_retry_thread(self):
        """Stop the retry thread"""
        self._retry_running = False
        if self._retry_thread and self._retry_thread.is_alive():
            self._retry_thread.join(timeout=5)
        logger.info("Stopped message retry thread")

    def _retry_loop(self):
        """Main retry loop for failed messages"""
        while self._retry_running:
            try:
                # Check for messages to retry
                self._process_retry_queue()
                time.sleep(60)  # Check every minute
            except Exception as e:
                logger.error(f"Error in retry loop: {e}")
                time.sleep(60)

    def _process_retry_queue(self):
        """Process the retry queue and attempt to send failed messages"""
        while not self._failed_message_queue.empty():
            try:
                queued_message = self._failed_message_queue.get_nowait()
                
                # Check if it's time to retry
                time_since_queued = datetime.now() - queued_message.timestamp
                if time_since_queued.total_seconds() < queued_message.retry_delay:
                    # Put it back in the queue
                    self._failed_message_queue.put(queued_message)
                    break
                
                # Check if channel is ready
                channel = self.channels.get(queued_message.channel_name)
                if not channel or not channel.is_ready():
                    # Put it back in the queue for later
                    queued_message.retry_count += 1
                    if queued_message.retry_count < queued_message.max_retries:
                        self._failed_message_queue.put(queued_message)
                    else:
                        logger.warning(f"Message for user {queued_message.user_id} failed after {queued_message.max_retries} retries")
                    continue
                
                # Attempt to send the message
                success = self.send_message_sync(
                    queued_message.channel_name,
                    queued_message.recipient,
                    queued_message.message
                )
                
                if success:
                    logger.info(f"Successfully retried message for user {queued_message.user_id}, category {queued_message.category}")
                else:
                    # Increment retry count and put back in queue
                    queued_message.retry_count += 1
                    if queued_message.retry_count < queued_message.max_retries:
                        self._failed_message_queue.put(queued_message)
                    else:
                        logger.warning(f"Message for user {queued_message.user_id} failed after {queued_message.max_retries} retries")
                        
            except queue.Empty:
                break
            except Exception as e:
                logger.error(f"Error processing retry queue: {e}")
                break

    def initialize_channels_from_config(self, channel_configs: Dict[str, ChannelConfig] = None):
        """Initialize channels from configuration"""
        if channel_configs is None:
            # Use default configurations
            channel_configs = self._get_default_channel_configs()
        
        self.channel_configs = channel_configs
        
        # Create event loop for async operations if we're not in one
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        # Run the async initialization
        return loop.run_until_complete(self._initialize_channels_async())

    async def _initialize_channels_async(self):
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
                self.channels[name] = channel
                logger.debug(f"Channel {name} ready")
            else:
                logger.error(f"Failed to initialize channel {name} after retries")
        
        return len(self.channels) > 0

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

    def _get_default_channel_configs(self) -> Dict[str, ChannelConfig]:
        """Get default channel configurations"""
        configs = {}
        
        # Only create configs for channels that have tokens/configs available
        # if TELEGRAM_BOT_TOKEN:  # Deactivated
        #     configs['telegram'] = ChannelConfig(
        #         name='telegram',
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

    def start_all(self):
        """Legacy method - maintains synchronous interface"""
        try:
            # Create or get event loop
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # We're in an async context, can't use run_until_complete
                    logger.warning("start_all() called from async context - channels may not initialize properly")
                    return False
            except RuntimeError:
                # No event loop, create one
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            # Run the async initialization synchronously
            success = loop.run_until_complete(self._start_all_async())
            
            if not success:
                raise BotInitializationError("Failed to initialize any communication channels")
            
            # Create legacy channel access for backward compatibility
            self._create_legacy_channel_access()
            
            # Start the retry thread for failed messages
            self._start_retry_thread()
            
            self._running = True
            logger.info(f"Communication channels ready ({len(self.channels)} active)")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start communication channels: {e}")
            raise

    async def _start_all_async(self):
        """Internal async method for initialization"""
        channel_configs = self._get_default_channel_configs()
        self.channel_configs = channel_configs
        
        success = await self._initialize_channels_async()
        return success

    def _create_legacy_channel_access(self):
        """
        Create legacy channel access for backward compatibility.
        
        LEGACY COMPATIBILITY FUNCTION - REMOVE AFTER VERIFYING NO USAGE
        Creates wrapper objects that provide the old interface for existing code.
        
        TODO: Remove after confirming no code uses legacy interface
        REMOVAL PLAN:
        1. Add usage logging to track legacy interface access
        2. Monitor app.log for legacy usage warnings for 1 week
        3. If no usage detected, remove LegacyChannelWrapper class
        4. Remove _create_legacy_channel_access method
        5. Update channels property to return _channels_dict directly
        """
        self._legacy_channels = {}
        for name, channel in self.channels.items():
            self._legacy_channels[name] = LegacyChannelWrapper(channel)
        logger.debug("Legacy channel access created")

    @property
    def channels(self):
        """
        Backward compatibility property
        
        LEGACY COMPATIBILITY PROPERTY - REMOVE AFTER VERIFYING NO USAGE
        """
        if hasattr(self, '_legacy_channels') and self._legacy_channels:
            logger.warning("LEGACY channels property accessed - switch to direct channel access")
            return self._legacy_channels
        return self._channels_dict

    @channels.setter
    def channels(self, value):
        """Backward compatibility setter"""
        self._channels_dict = value

    async def send_message(self, channel_name: str, recipient: str, message: str, **kwargs) -> bool:
        """Send message via specified channel using unified interface"""
        logger.debug(f"Preparing to send message to {recipient} via {channel_name}")
        
        channel = self.channels.get(channel_name)
        if not channel:
            logger.error(f"Channel {channel_name} not found")
            return False
        
        if not channel.is_ready():
            logger.error(f"Channel {channel_name} not ready (status: {channel.get_status()})")
            return False

        # Check network connectivity
        if not wait_for_network():
            logger.error("Network not available. Aborting message send.")
            raise MessageSendError("Network not available.")
        
        try:
            # FIXED: Ensure we're actually awaiting a coroutine
            success = await channel.send_message(recipient, message, **kwargs)
            
            # FIXED: Better return value validation
            if success is True:
                logger.info(f"Message sent successfully via {channel_name} to {recipient}")
                return True
            elif success is False:
                logger.warning(f"Channel {channel_name} returned False for message send to {recipient}")
                return False
            else:
                # Handle unexpected return values
                logger.warning(f"Channel {channel_name} returned unexpected value: {success} (type: {type(success)})")
                # If it's not explicitly False, assume success if no exception was raised
                return True
            
        except Exception as e:
            logger.error(f"Error sending message via {channel_name}: {e}")
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
            
            # Force flush
            import logging
            root_logger = logging.getLogger()
            for handler in root_logger.handlers:
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
        
        try:
            # Get the underlying bot directly
            if channel_name == 'discord':
                discord_channel = self.channels.get('discord')
                if discord_channel and hasattr(discord_channel, 'bot'):
                    # Use the discord.py sync methods if available
                    bot = discord_channel.bot
                    
                    # Try to send via the bot's sync methods
                    try:
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
                        
            # Fallback to legacy wrapper
            if hasattr(self, '_legacy_channels') and channel_name in self._legacy_channels:
                return self._legacy_channels[channel_name].send_message(recipient, message, **kwargs)
            
            return False
            
        except Exception as e:
            logger.error(f"Error in simplified send_message_sync: {e}")
            # Queue for retry if this is a scheduled message
            if 'user_id' in kwargs and 'category' in kwargs:
                self._queue_failed_message(
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
            if channel_name in self.channels:
                task = asyncio.create_task(
                    self.send_message(channel_name, recipient, message),
                    name=f"send_{channel_name}"
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
        channel = self.channels.get(channel_name)
        return channel.get_status() if channel else None

    async def get_all_statuses(self) -> Dict[str, ChannelStatus]:
        """Get status of all channels"""
        return {name: channel.get_status() for name, channel in self.channels.items()}

    async def health_check_all(self) -> Dict[str, Any]:
        """Perform comprehensive health check on all channels with detailed status"""
        logger.debug("Performing comprehensive health check on all channels")
        results = {}
        
        for name, channel in self.channels.items():
            try:
                # Basic health check
                basic_health = await channel.health_check()
                
                # Get detailed status for Discord
                detailed_status = {}
                if name == 'discord' and hasattr(channel, 'get_health_status'):
                    detailed_status = channel.get_health_status()
                    status_summary = channel.get_connection_status_summary()
                    detailed_status['status_summary'] = status_summary
                
                results[name] = {
                    'healthy': basic_health,
                    'status': channel.get_status().value if hasattr(channel, 'get_status') else 'unknown',
                    'detailed_status': detailed_status
                }
                
                logger.debug(f"Health check for {name}: {'PASS' if basic_health else 'FAIL'}")
                if detailed_status:
                    logger.debug(f"Detailed status for {name}: {detailed_status.get('status_summary', 'No summary')}")
                    
            except Exception as e:
                logger.error(f"Health check failed for {name}: {e}")
                results[name] = {
                    'healthy': False,
                    'status': 'error',
                    'error': str(e)
                }
        
        return results

    def get_discord_connectivity_status(self) -> Optional[Dict[str, Any]]:
        """Get detailed Discord connectivity status if available"""
        if 'discord' in self.channels:
            discord_channel = self.channels['discord']
            if hasattr(discord_channel, 'get_health_status'):
                return discord_channel.get_health_status()
        return None

    async def _shutdown_all_async(self):
        """Async method to shutdown all channels"""
        for name, channel in list(self.channels.items()):
            if channel is not None:
                try:
                    await channel.shutdown()
                    logger.info(f"Channel {name} shutdown successfully")
                except Exception as e:
                    logger.error(f"Error shutting down {name}: {e}")
        
        self.channels.clear()
        if hasattr(self, '_legacy_channels'):
            self._legacy_channels.clear()

    def stop_all(self):
        """Stop all communication channels"""
        logger.debug("Stopping all communication channels.")
        
        try:
            # Stop the retry thread first
            self._stop_retry_thread()
            
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
                    loop.run_until_complete(self._shutdown_all_async())
                    loop.close()
                except Exception:
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
        
        # Stop all channels
        for name, channel in self.channels.items():
            try:
                if hasattr(channel, 'stop'):
                    channel.stop()
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
        
        for channel_name, channel in self.channels.items():
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

        # Handle check-in category specially
        if category == "checkin":
            self._handle_scheduled_checkin(user_id, messaging_service, recipient)
            return

        # Handle AI-generated messages
        if category in ["personalized", "ai_personalized"]:
            self._send_ai_generated_message(user_id, category, messaging_service, recipient)
        else:
            self._send_predefined_message(user_id, category, messaging_service, recipient)
        
        logger.info(f"Completed message sending for user {user_id}, category {category}")

    def _get_recipient_for_service(self, user_id: str, messaging_service: str, preferences: dict) -> Optional[str]:
        """Get the appropriate recipient ID for the messaging service"""
        if messaging_service == "discord":
            # Get discord_user_id from account.json, not preferences
            # Get user account data
            user_data_result = get_user_data(user_id, 'account')
            account_data = user_data_result.get('account')
            if not account_data:
                logger.error(f"User account not found for {user_id}")
                return False
            return account_data.get('discord_user_id', '') if account_data else None
        elif messaging_service == "telegram":
            logger.error("Telegram channel has been deactivated")
            return None
        elif messaging_service == "email":
            # Get email from account.json, not preferences
            # Get user account data
            user_data_result = get_user_data(user_id, 'account')
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

    def _handle_scheduled_checkin(self, user_id: str, messaging_service: str, recipient: str):
        """
        Handle scheduled check-in messages based on user preferences and frequency.
        """
        try:
            prefs_result = get_user_data(user_id, 'preferences')
            preferences = prefs_result.get('preferences')
            if not preferences:
                logger.error(f"User preferences not found for user {user_id}")
                return
            
            # Check if check-ins are enabled in account features
            # Get user account data
            user_data_result = get_user_data(user_id, 'account')
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
                
        except Exception as e:
            logger.error(f"Error handling scheduled check-in for user {user_id}: {e}")

    def _send_checkin_prompt(self, user_id: str, messaging_service: str, recipient: str):
        """
        Send a check-in prompt message to start the daily check-in flow.
        """
        try:
            # Initialize the dynamic check-in flow properly
            from bot.conversation_manager import conversation_manager
            
            # Use the dynamic check-in initialization instead of hardcoded values
            reply_text, completed = conversation_manager.start_daily_checkin(user_id)
            
            # Send the initial message to the user with retry support
            success = self.send_message_sync(messaging_service, recipient, reply_text, 
                                           user_id=user_id, category="checkin")
            
            if success:
                logger.info(f"Successfully sent check-in prompt to user {user_id} and initialized flow")
            else:
                logger.warning(f"Failed to send check-in prompt to user {user_id}")
                # Clean up the conversation state if message failed
                conversation_manager.user_states.pop(user_id, None)
                
        except Exception as e:
            logger.error(f"Error sending check-in prompt to user {user_id}: {e}")
            # Clean up the conversation state if there was an error
            from bot.conversation_manager import conversation_manager
            conversation_manager.user_states.pop(user_id, None)

    def _send_ai_generated_message(self, user_id: str, category: str, messaging_service: str, recipient: str):
        """Send an AI-generated personalized message using contextual AI"""
        try:
            from bot.ai_chatbot import get_ai_chatbot
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
                store_sent_message(user_id, category, message_id, message_to_send)
                logger.info(f"Sent contextual AI-generated message for user {user_id}, category {category}")
            else:
                logger.error(f"Failed to send AI-generated message for user {user_id}")
                
        except Exception as e:
            logger.error(f"Error sending AI-generated message for user {user_id}: {e}")

    def _send_predefined_message(self, user_id: str, category: str, messaging_service: str, recipient: str):
        """Send a pre-defined message from the user's message library"""
        try:
            matching_periods, valid_periods = get_current_time_periods_with_validation(user_id, category)
            # Remove 'ALL' from matching_periods if there are other periods
            if 'ALL' in matching_periods and len(matching_periods) > 1:
                matching_periods = [p for p in matching_periods if p != 'ALL']
            # If no periods match (other than ALL), use ALL as fallback
            if not matching_periods and 'ALL' in valid_periods:
                matching_periods = ['ALL']

            # Use new user-specific message file structure
            user_messages_dir = os.path.join(get_user_data_dir(user_id), 'messages')
            file_path = os.path.join(user_messages_dir, f"{category}.json")
            data = load_json_data(file_path)

            if not data or 'messages' not in data:
                logger.error(f"No messages found for category {category} and user {user_id}.")
                return

            messages_to_send = [
                msg for msg in data['messages']
                if any(day in msg['days'] for day in get_current_day_names())
                and any(period in msg['time_periods'] for period in matching_periods)
            ]
            
            if not messages_to_send:
                logger.info(f"No messages to send for category {category} and user {user_id} at this time.")
                return

            message_to_send = random.choice(messages_to_send)
            
            # IMPROVED: Better success/failure tracking
            try:
                success = self.send_message_sync(messaging_service, recipient, message_to_send['message'], 
                                               user_id=user_id, category=category)
                
                if success:
                    store_sent_message(user_id, category, message_to_send['message_id'], message_to_send['message'])
                else:
                    logger.warning(f"Message send returned False but may have still been delivered for user {user_id}, category {category}")
                    # Still store it since the message might have gone through
                    store_sent_message(user_id, category, message_to_send['message_id'], message_to_send['message'])
                    
            except Exception as send_error:
                logger.error(f"Exception during message send for user {user_id}, category {category}: {send_error}")
                # Don't store the message if there was an exception

        except Exception as e:
            logger.error(f"Error in predefined message handling for user {user_id}, category {category}: {e}")

    # Legacy compatibility methods
    def get_available_channels(self) -> List[str]:
        """Get list of available/initialized channels"""
        return list(self.channels.keys())

    def is_channel_ready(self, channel_name: str) -> bool:
        """Check if a specific channel is ready"""
        channel = self.channels.get(channel_name)
        return channel.is_ready() if channel else False

    def handle_task_reminder(self, user_id: str, task_id: str):
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
        
        # Send the reminder
        success = self.send_message_sync(messaging_service, recipient, reminder_message)
        
        if success:
            logger.info(f"Task reminder sent successfully for user {user_id}, task {task_id}")
        else:
            logger.error(f"Failed to send task reminder for user {user_id}, task {task_id}")

    def _create_task_reminder_message(self, task: dict) -> str:
        """
        Create a formatted task reminder message.
        """
        title = task.get('title', 'Untitled Task')
        description = task.get('description', '')
        due_date = task.get('due_date', '')
        priority = task.get('priority', 'medium')
        # Tasks now use tags instead of categories
        
        # Create priority emoji
        priority_emoji = {
            'low': '🟢',
            'medium': '🟡', 
            'high': '🔴'
        }.get(priority, '🟡')
        
        # Build the message
        message = f"📋 **Task Reminder** {priority_emoji}\n\n"
        message += f"**{title}**\n"
        
        if description:
            message += f"{description}\n\n"
        
        if due_date:
            message += f"📅 **Due:** {due_date}\n"
        
        message += f"⚡ **Priority:** {priority.title()}\n\n"
        message += "Use 'complete task' or 'list tasks' to manage your tasks."
        
        return message

class LegacyChannelWrapper:
    """
    Provides complete backward compatibility for channel access
    
    LEGACY COMPATIBILITY CLASS - REMOVE AFTER VERIFYING NO USAGE
    TODO: Remove after confirming no code uses legacy interface
    REMOVAL PLAN:
    1. Add usage logging to track legacy method calls
    2. Monitor app.log for legacy usage warnings for 1 week
    3. If no usage detected, remove entire class
    4. Update any remaining call sites to use modern async interface
    """
    
    def __init__(self, base_channel: BaseChannel):
        """
        Initialize the legacy channel wrapper.
        
        Args:
            base_channel: The base channel to wrap
        """
        self._channel = base_channel

    def _run_async_safely(self, coro):
        """
        Run async function safely, handling existing event loops.
        
        Args:
            coro: The coroutine to run
            
        Returns:
            The result of the coroutine
        """
        try:
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = None

            # If we are already inside a running loop (e.g., UI thread), off-load to a helper thread
            if loop and loop.is_running():
                import threading

                result_container = {}

                def run_in_thread():
                    """
                    Run the coroutine in a separate thread with its own event loop.
                    
                    This nested function ensures async operations can run safely in a threaded environment.
                    """
                    _loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(_loop)
                    try:
                        result_container['result'] = _loop.run_until_complete(coro)
                    except Exception as exc:
                        result_container['error'] = exc
                    finally:
                        _loop.close()

                t = threading.Thread(target=run_in_thread, daemon=True)
                t.start()
                t.join(timeout=30)

                if 'error' in result_container:
                    raise result_container['error']
                return result_container.get('result')

            # Otherwise create a new loop in this thread
            loop = loop or asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(coro)
            finally:
                if not loop.is_closed():
                    loop.close()
        except Exception as e:
            logger.error(f"Error running async operation: {e}")
            raise

    def is_initialized(self) -> bool:
        """
        Legacy method - synchronous.
        
        LEGACY COMPATIBILITY METHOD - REMOVE AFTER VERIFYING NO USAGE
        Returns:
            bool: True if the channel is initialized
        """
        logger.warning("LEGACY is_initialized() called - switch to is_ready()")
        return self._channel.is_ready()

    def start(self) -> bool:
        """
        Legacy method - synchronous.
        
        LEGACY COMPATIBILITY METHOD - REMOVE AFTER VERIFYING NO USAGE
        Returns:
            bool: True if the channel started successfully
        """
        logger.warning("LEGACY start() called - switch to initialize()")
        try:
            if hasattr(self._channel, 'start'):
                return self._run_async_safely(self._channel.start())
            return True
        except Exception as e:
            logger.error(f"Error starting channel: {e}")
            return False

    def stop(self) -> bool:
        """
        Legacy method - synchronous.
        
        LEGACY COMPATIBILITY METHOD - REMOVE AFTER VERIFYING NO USAGE
        Returns:
            bool: True if the channel stopped successfully
        """
        logger.warning("LEGACY stop() called - switch to shutdown()")
        try:
            if hasattr(self._channel, 'stop'):
                return self._run_async_safely(self._channel.stop())
            return True
        except Exception as e:
            logger.error(f"Error stopping channel: {e}")
            return False

    def send_message(self, *args, **kwargs):
        """
        Legacy method - synchronous.
        
        LEGACY COMPATIBILITY METHOD - REMOVE AFTER VERIFYING NO USAGE
        Returns:
            The result of sending the message
        """
        logger.warning("LEGACY send_message() called - switch to async send_message()")
        return self._run_async_safely(self._channel.send_message(*args, **kwargs))

    def receive_messages(self):
        """
        Legacy method - synchronous.
        
        LEGACY COMPATIBILITY METHOD - REMOVE AFTER VERIFYING NO USAGE
        Returns:
            List of received messages
        """
        logger.warning("LEGACY receive_messages() called - switch to async receive_messages()")
        return self._run_async_safely(self._channel.receive_messages())

    def __getattr__(self, name):
        """
        Forward attribute access to the base channel for backward compatibility.
        
        Args:
            name: The attribute name to access
            
        Returns:
            The attribute value from the base channel
        """
        return getattr(self._channel, name)