# communication_manager.py

import asyncio
import threading
from typing import Dict, Optional, List, Any
from bot.base_channel import BaseChannel, ChannelConfig, ChannelStatus, ChannelType
from bot.channel_factory import ChannelFactory
from core.logger import get_logger
from user.user_context import UserContext
import random
import time
from core.config import EMAIL_SMTP_SERVER, DISCORD_BOT_TOKEN
from core.service_utilities import wait_for_network
from core.user_management import get_user_preferences
from core.response_tracking import get_recent_daily_checkins
from core.message_management import store_sent_message
from core.schedule_management import get_current_time_periods_with_validation, get_current_day_names
from core.file_operations import determine_file_path, load_json_data
import os
from core.config import get_user_data_dir

logger = get_logger(__name__)

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
                except asyncio.TimeoutError:
                    logger.warning(f"Channel {channel.config.name} initialization timed out on attempt {attempt + 1}")
                
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
        """Create legacy channel access preserving all functionality"""
        self._legacy_channels = {}
        for name, channel in self.channels.items():
            # Create wrapper that preserves the original channel's full interface
            wrapper = LegacyChannelWrapper(channel)
            
            # For Telegram, preserve conversation state access (Deactivated)
            # if name == 'telegram' and hasattr(channel, 'selected_days'):
            #     wrapper.selected_days = channel.selected_days
            #     wrapper.selected_time_periods = channel.selected_time_periods
            #     wrapper.screaming = channel.screaming
            
            self._legacy_channels[name] = wrapper

    @property
    def channels(self):
        """Backward compatibility property"""
        if hasattr(self, '_legacy_channels') and self._legacy_channels:
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
        """Check if logging is still working and recover if needed"""
        try:
            logger.info("Logging health check")
            return True
        except Exception as e:
            print(f"Logging system appears broken: {e}")
            try:
                # Try to restart logging
                from core.logger import setup_logging
                setup_logging()
                return True
            except Exception as restart_error:
                print(f"Failed to restart logging: {restart_error}")
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

    async def health_check_all(self) -> Dict[str, bool]:
        """Perform health check on all channels"""
        logger.debug("Performing health check on all channels")
        results = {}
        
        for name, channel in self.channels.items():
            try:
                results[name] = await channel.health_check()
                logger.debug(f"Health check for {name}: {'PASS' if results[name] else 'FAIL'}")
            except Exception as e:
                logger.error(f"Health check failed for {name}: {e}")
                results[name] = False
        
        return results

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
        """Synchronous shutdown method"""
        logger.debug("Performing synchronous shutdown")
        
        for name, channel in list(self.channels.items()):
            if channel is not None:
                try:
                    # Try the legacy stop method
                    if hasattr(channel, 'stop') and callable(getattr(channel, 'stop')):
                        channel.stop()
                        logger.info(f"Channel {name} stopped successfully")
                except Exception as e:
                    logger.error(f"Error stopping {name}: {e}")
        
        self.channels.clear()
        if hasattr(self, '_legacy_channels'):
            self._legacy_channels.clear()

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

        preferences = get_user_preferences(user_id)
        if not preferences:
            logger.error(f"User preferences not found for user {user_id}.")
            return

        messaging_service = preferences.get('channel', {}).get('type', preferences.get('messaging_service'))
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
            from core.user_management import get_user_account
            account_data = get_user_account(user_id)
            return account_data.get('discord_user_id', '') if account_data else None
        elif messaging_service == "telegram":
            logger.error("Telegram channel has been deactivated")
            return None
        elif messaging_service == "email":
            # Get email from account.json, not preferences
            from core.user_management import get_user_account
            account_data = get_user_account(user_id)
            return account_data.get('email', '') if account_data else None
        else:
            logger.error(f"Unknown messaging service: {messaging_service}")
            return None

    def _should_send_checkin_prompt(self, user_id: str, checkin_prefs: dict) -> bool:
        """
        Determine if it's time to send a check-in prompt based on user preferences.
        This checks if enough time has passed since the last check-in.
        """
        try:
            frequency = checkin_prefs.get('frequency', 'daily')
            
            # If frequency is set to "none" or "manual", never auto-prompt
            if frequency in ['none', 'manual']:
                logger.debug(f"User {user_id} has check-in frequency set to '{frequency}', skipping auto-prompt")
                return False
            
            # Get the most recent check-in
            recent_checkins = get_recent_daily_checkins(user_id, limit=1)
            
            if not recent_checkins:
                # No previous check-ins, so it's time for one
                logger.debug(f"No previous check-ins found for user {user_id}, prompting check-in")
                return True
            
            from datetime import datetime, timedelta
            last_checkin = recent_checkins[0]
            
            # Parse human-readable timestamp format
            timestamp_value = last_checkin.get('timestamp', '1970-01-01 00:00:00')
            last_checkin_date = datetime.strptime(timestamp_value, '%Y-%m-%d %H:%M:%S')
            
            now = datetime.now()
            
            if frequency == 'daily':
                # Check if it's been at least 18 hours since last check-in (allows for some flexibility)
                time_since_last = now - last_checkin_date
                should_prompt = time_since_last.total_seconds() > (18 * 3600)  # 18 hours
                logger.debug(f"Daily check-in: {time_since_last.total_seconds()/3600:.1f} hours since last, should_prompt={should_prompt}")
                return should_prompt
            elif frequency == 'weekly':
                # Check if it's been at least 6 days since last check-in
                time_since_last = now - last_checkin_date
                should_prompt = time_since_last.days >= 6
                logger.debug(f"Weekly check-in: {time_since_last.days} days since last, should_prompt={should_prompt}")
                return should_prompt
            else:
                # For custom or unknown frequencies, default to daily behavior
                time_since_last = now - last_checkin_date
                should_prompt = time_since_last.total_seconds() > (18 * 3600)
                logger.debug(f"Custom frequency check-in: should_prompt={should_prompt}")
                return should_prompt
                
        except Exception as e:
            logger.error(f"Error determining if check-in prompt should be sent for user {user_id}: {e}")
            # Default to sending check-in if there's an error
            return True

    def _handle_scheduled_checkin(self, user_id: str, messaging_service: str, recipient: str):
        """
        Handle scheduled check-in messages based on user preferences and frequency.
        """
        try:
            preferences = get_user_preferences(user_id)
            if not preferences:
                logger.error(f"User preferences not found for user {user_id}")
                return
            
            # Check if check-ins are enabled in account features
            from core.user_management import get_user_account
            account_data = get_user_account(user_id)
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
            
            # Send the initial message to the user
            success = self.send_message_sync(messaging_service, recipient, reply_text)
            
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

            success = self.send_message_sync(messaging_service, recipient, message_to_send)
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
                success = self.send_message_sync(messaging_service, recipient, message_to_send['message'])
                
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
        preferences = get_user_preferences(user_id)
        if not preferences:
            logger.error(f"User preferences not found for user {user_id}.")
            return

        messaging_service = preferences.get('channel', {}).get('type', preferences.get('messaging_service'))
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
        category = task.get('category', '')
        
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
        
        if category:
            message += f"📂 **Category:** {category}\n"
        
        message += f"⚡ **Priority:** {priority.title()}\n\n"
        message += "Use 'complete task' or 'list tasks' to manage your tasks."
        
        return message

class LegacyChannelWrapper:
    """Provides complete backward compatibility for channel access"""
    
    def __init__(self, base_channel: BaseChannel):
        self.base_channel = base_channel
        self._thread_pool = None
    
    def _run_async_safely(self, coro):
        """Run async function safely, handling existing event loops"""
        try:
            # Check if we're already in an async context
            loop = asyncio.get_running_loop()
            # If we reach here, there's already a running loop
            
            # Use run_coroutine_threadsafe for running loop
            import concurrent.futures
            import threading
            
            # Create a future to hold the result
            future = concurrent.futures.Future()
            
            def run_in_thread():
                try:
                    # Create new event loop for this thread
                    new_loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(new_loop)
                    result = new_loop.run_until_complete(coro)
                    future.set_result(result)
                    new_loop.close()
                except Exception as e:
                    future.set_exception(e)
            
            thread = threading.Thread(target=run_in_thread)
            thread.start()
            thread.join(timeout=30)  # 30 second timeout
            
            if thread.is_alive():
                logger.error("Async operation timed out")
                return False
                
            return future.result()
            
        except RuntimeError:
            # No running loop, we can use run_until_complete
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                result = loop.run_until_complete(coro)
                loop.close()
                return result
            except Exception as e:
                logger.error(f"Error running async operation: {e}")
                return False
    
    def is_initialized(self) -> bool:
        """Legacy method - synchronous"""
        return self.base_channel.is_ready()
    
    def start(self) -> bool:
        """Legacy method - synchronous"""
        return self._run_async_safely(self.base_channel.initialize())
    
    def stop(self) -> bool:
        """Legacy method - synchronous"""
        return self._run_async_safely(self.base_channel.shutdown())
    
    def send_message(self, *args, **kwargs):
        """Legacy method - synchronous"""
        return self._run_async_safely(self.base_channel.send_message(*args, **kwargs))
    
    def receive_messages(self):
        """Legacy method - synchronous"""
        return self._run_async_safely(self.base_channel.receive_messages())
    
    # Forward all other attribute access to the base channel
    def __getattr__(self, name):
        return getattr(self.base_channel, name)