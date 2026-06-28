# channel_orchestrator.py

import asyncio
import threading
import time
from typing import Any

from core.logger import get_component_logger
from core.error_handling import handle_errors
from communication.communication_channels.base.base_channel import (
    BaseChannel,
    ChannelConfig,
    ChannelStatus,
)
from communication.core.factory import ChannelFactory
from communication.core.retry_manager import RetryManager
from communication.core.channel_monitor import ChannelMonitor
from communication.core.message_send_result import MessageSendResult
from communication.communication_channels.email.inbound_processor import (
    EmailInboundProcessor,
)
from communication.delivery.message_dispatcher import PredefinedMessageDispatcher
from communication.delivery.recipient_resolver import RecipientResolver
from communication.reminders.checkin_prompt_dispatcher import CheckinPromptDispatcher
from communication.reminders.reminder_dispatcher import TaskReminderDispatcher
from core import get_user_data
from messages.message_data_manager import store_sent_message
from core.schedule_runtime import get_current_time_periods_with_validation
from core.config import EMAIL_SMTP_SERVER, DISCORD_BOT_TOKEN
from core.network_probe import wait_for_network
import contextlib

# Route orchestration logs to channels component; keep module logger for local debug if needed
comm_logger = get_component_logger("channel_orchestrator")
logger = comm_logger


@handle_errors("getting conversation manager", user_friendly=False)
def _get_conversation_manager():
    """Lazy import to avoid import cycles with message processing."""
    from communication.message_processing.conversation_flow_manager import (
        conversation_manager,
    )

    return conversation_manager


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

    # not_duplicate: singleton_new_methods
    @handle_errors("creating channel orchestrator instance", default_return=None)
    def __new__(cls, *args, **kwargs):
        """Ensure that only one instance of the CommunicationManager exists (Singleton pattern)."""
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    @handle_errors("initializing channel orchestrator", default_return=None)
    def __init__(self):
        """Initialize the CommunicationManager singleton"""
        # Check if already initialized
        if hasattr(self, "_initialized") and self._initialized:
            return

        # Initialize basic attributes
        self._channels_dict = {}
        self.channel_configs = {}
        self._running = False
        self._main_loop = None
        self._loop_thread = None
        self.scheduler_manager = None
        self._last_task_reminders = (
            {}
        )  # Track last task reminder per user: {user_id: task_id}
        # Initialize extracted modules
        # Pass send_message_sync as callback for retry manager
        self.retry_manager = RetryManager(send_callback=self.send_message_sync)
        self.channel_monitor = ChannelMonitor()
        self.email_inbound_processor = EmailInboundProcessor(
            get_email_channel=lambda: self._channels_dict.get("email"),
            run_async_sync=self.send_message_sync__run_async_sync,
            is_runtime_running=lambda: self._running,
        )
        self.recipient_resolver = RecipientResolver()
        self.predefined_dispatcher = PredefinedMessageDispatcher(self)
        self.checkin_dispatcher = CheckinPromptDispatcher(self)
        self.task_reminder_dispatcher = TaskReminderDispatcher(self)

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
        except Exception:
            # Fallback: create new loop
            self._main_loop = asyncio.new_event_loop()
            self._event_loop = self._main_loop
            asyncio.set_event_loop(self._main_loop)

    @handle_errors("running async sync", default_return=None)
    def send_message_sync__run_async_sync(self, coro):
        """Run async function synchronously using our managed loop"""
        if not self._main_loop:
            self.__init____setup_event_loop()
        if not self._main_loop:
            raise RuntimeError("Event loop not initialized for sync execution")
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
    def send_message_sync__queue_failed_message(
        self,
        user_id: str,
        category: str,
        message: str,
        recipient: str,
        channel_name: str,
    ):
        """Queue a failed message for retry"""
        self.retry_manager.queue_failed_message(
            user_id, category, message, recipient, channel_name
        )

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

    @handle_errors("initializing channels from config", default_return=False)
    def initialize_channels_from_config(
        self, channel_configs: dict[str, ChannelConfig] | None = None
    ):
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
        return loop.run_until_complete(
            self.initialize_channels_from_config__initialize_channels_async()
        )

    @handle_errors("initializing channels from config async", default_return=None)
    async def initialize_channels_from_config__initialize_channels_async(self):
        """Async method to initialize all configured channels"""
        logger.debug("Starting async channel initialization.")
        if not self.channel_configs:
            logger.error("Channel configs not initialized for async initialization")
            return False

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

    @handle_errors(
        "initializing channel with retry", user_friendly=False, default_return=False
    )
    async def _initialize_channel_with_retry(
        self, channel: BaseChannel, config: ChannelConfig
    ) -> bool:
        """Initialize a channel with retry logic"""
        retry_delay = config.retry_delay

        for attempt in range(config.max_retries):
            try:
                logger.debug(
                    f"Initializing {channel.config.name}, attempt {attempt + 1}/{config.max_retries}"
                )

                # Add timeout to prevent hanging
                try:
                    success = await asyncio.wait_for(
                        channel.initialize(),
                        timeout=30.0,  # 30 second timeout per attempt
                    )
                    if success:
                        logger.info(
                            f"Channel {channel.config.name} initialized on attempt {attempt + 1}"
                        )
                        return True
                    else:
                        logger.warning(
                            f"Channel {channel.config.name} initialization returned False on attempt {attempt + 1}"
                        )

                        is_connected_fn = getattr(
                            channel, "is_actually_connected", None
                        )
                        if callable(is_connected_fn) and is_connected_fn():
                            logger.info(
                                f"Channel {channel.config.name} is connected despite initialization returning False"
                            )
                            return True

                except asyncio.TimeoutError:
                    logger.warning(
                        f"Channel {channel.config.name} initialization timed out on attempt {attempt + 1}"
                    )

                    is_connected_fn = getattr(channel, "is_actually_connected", None)
                    if callable(is_connected_fn) and is_connected_fn():
                        logger.info(
                            f"Channel {channel.config.name} is connected despite initialization timeout"
                        )
                        return True

            except Exception as e:
                logger.warning(
                    f"Channel {channel.config.name} initialization attempt {attempt + 1} failed: {e}"
                )

            if attempt < config.max_retries - 1:
                logger.debug(
                    f"Waiting {retry_delay} seconds before next attempt for {channel.config.name}"
                )
                await asyncio.sleep(retry_delay)
                retry_delay *= config.backoff_multiplier

        logger.error(
            f"Failed to initialize {channel.config.name} after {config.max_retries} attempts"
        )
        return False

    @handle_errors("getting default channel configs", default_return={})
    def _get_default_channel_configs(self) -> dict[str, ChannelConfig]:
        """Get default channel configurations"""
        configs = {}

        # Only create configs for channels that have tokens/configs available

        #         enabled=True,
        #         max_retries=5,
        #         retry_delay=2.0,
        #         backoff_multiplier=2.0
        #     )

        if EMAIL_SMTP_SERVER:
            configs["email"] = ChannelConfig(
                name="email",
                enabled=True,
                max_retries=3,
                retry_delay=1.0,
                backoff_multiplier=2.0,
            )

        if DISCORD_BOT_TOKEN:
            configs["discord"] = ChannelConfig(
                name="discord",
                enabled=True,
                max_retries=3,
                retry_delay=1.5,
                backoff_multiplier=2.0,
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
            if (
                "email" in self.channel_configs
                and self.channel_configs["email"].enabled
            ):
                self.email_inbound_processor.start_polling()

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
        if not self.channel_configs:
            logger.error("Channel configs not initialized for async startup")
            return False

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
        if not self.channel_configs:
            logger.error("Channel configs not initialized for sync startup")
            return False

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

    @handle_errors(
        "initializing channel with retry (sync)",
        user_friendly=False,
        default_return=False,
    )
    def _initialize_channel_with_retry_sync(
        self, channel: BaseChannel, config: ChannelConfig
    ) -> bool:
        """Synchronous version of channel initialization with retry logic"""
        retry_delay = config.retry_delay

        for attempt in range(config.max_retries):
            try:
                logger.debug(
                    f"Initializing {channel.config.name}, attempt {attempt + 1}/{config.max_retries}"
                )

                # Try to initialize the channel
                if hasattr(channel, "initialize"):
                    # If it's an async method, run it in a new event loop
                    try:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        success = loop.run_until_complete(
                            asyncio.wait_for(
                                channel.initialize(),
                                timeout=30.0,  # 30 second timeout per attempt
                            )
                        )
                        loop.close()
                    except asyncio.TimeoutError:
                        logger.warning(
                            f"Channel {channel.config.name} initialization timed out on attempt {attempt + 1}"
                        )
                        success = False
                    except Exception as e:
                        logger.warning(
                            f"Channel {channel.config.name} initialization attempt {attempt + 1} failed: {e}"
                        )
                        success = False
                else:
                    # If no initialize method, assume it's ready
                    success = True

                if success:
                    logger.info(
                        f"Channel {channel.config.name} initialized on attempt {attempt + 1}"
                    )
                    return True
                else:
                    logger.warning(
                        f"Channel {channel.config.name} initialization returned False on attempt {attempt + 1}"
                    )

                    is_connected_fn = getattr(channel, "is_actually_connected", None)
                    if callable(is_connected_fn) and is_connected_fn():
                        logger.info(
                            f"Channel {channel.config.name} is connected despite initialization returning False"
                        )
                        return True

            except Exception as e:
                logger.warning(
                    f"Channel {channel.config.name} initialization attempt {attempt + 1} failed: {e}"
                )

            if attempt < config.max_retries - 1:
                logger.debug(
                    f"Waiting {retry_delay} seconds before next attempt for {channel.config.name}"
                )
                time.sleep(retry_delay)
                retry_delay *= config.backoff_multiplier

        logger.error(
            f"Failed to initialize {channel.config.name} after {config.max_retries} attempts"
        )
        return False

    # not_duplicate: send_message_sync_pair
    @handle_errors("sending message", default_return=False)
    async def send_message(
        self, channel_name: str, recipient: str, message: str, **kwargs
    ) -> bool:
        """Send message via specified channel using unified interface"""
        logger.debug(f"Preparing to send message to {recipient} via {channel_name}")

        channel = self._channels_dict.get(channel_name)
        if not channel:
            logger.error(f"Channel {channel_name} not found")
            return False

        if not self._channel_can_send(channel):
            logger.error(f"Channel {channel_name} not ready")
            with contextlib.suppress(Exception):
                self.send_message_sync__queue_failed_message(
                    kwargs.get("user_id", ""),
                    kwargs.get("category", "unknown"),
                    message,
                    recipient,
                    channel_name,
                )
            return False

        # Check network connectivity with proper error handling
        try:
            if not wait_for_network():
                from core.error_handling import handle_network_error

                handle_network_error(
                    ConnectionError("Network not available"),
                    "message send",
                    kwargs.get("user_id"),
                )
                return False
        except Exception as network_error:
            from core.error_handling import handle_network_error

            handle_network_error(network_error, "network check", kwargs.get("user_id"))
            return False

        try:
            # FIXED: Ensure we're actually awaiting a coroutine
            success = await channel.send_message(recipient, message, **kwargs)

            # FIXED: Better return value validation
            # Use == instead of is to handle mock return values correctly
            if success is True or success:
                # Enhanced logging with message content and time period
                message[:50] + "..." if len(message) > 50 else message
                kwargs.get("time_period", "unknown")
                kwargs.get("user_id", "unknown")
                kwargs.get("category", "unknown")
                # Log will be handled by the deduplication logic below
                return True
            elif success is False or not success:
                failure_detail = self._channel_send_failure_detail(channel)
                detail_suffix = f": {failure_detail}" if failure_detail else ""
                logger.warning(
                    f"Channel {channel_name} returned False for message send to {recipient}{detail_suffix}"
                )
                return False
            else:
                # Handle unexpected return values
                logger.warning(
                    f"Channel {channel_name} returned unexpected value: {success} (type: {type(success)})"
                )
                # If it's not explicitly False, assume success if no exception was raised
                return True

        except ConnectionError as e:
            from core.error_handling import handle_network_error

            logger.error(
                f"Message send via {channel_name} raised {type(e).__name__}: {e}"
            )
            handle_network_error(
                e, f"message send via {channel_name}", kwargs.get("user_id")
            )
            return False
        except TimeoutError as e:
            from core.error_handling import handle_network_error

            logger.error(
                f"Message send via {channel_name} raised {type(e).__name__}: {e}"
            )
            handle_network_error(
                e, f"message send via {channel_name}", kwargs.get("user_id")
            )
            return False
        except Exception as e:
            from core.error_handling import handle_communication_error

            logger.error(
                f"Message send via {channel_name} raised {type(e).__name__}: {e}"
            )
            handle_communication_error(
                e, channel_name, f"message send to {recipient}", kwargs.get("user_id")
            )
            return False

    @handle_errors("checking logging health", user_friendly=False, default_return=False)
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
            for handler in logger.logger.handlers if hasattr(logger, "logger") else []:
                if hasattr(handler, "flush"):
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

    @handle_errors("checking channel send readiness", default_return=False)
    def _channel_can_send(self, channel: BaseChannel | None) -> bool:
        """Return whether a channel is ready to send using its capability if present."""
        if not channel:
            return False

        can_send = getattr(type(channel), "can_send_messages", None)
        if callable(can_send):
            return bool(can_send(channel))
        return channel.is_ready()

    @handle_errors("getting channel send failure detail", default_return="")
    def _channel_send_failure_detail(self, channel: BaseChannel | None) -> str:
        """Return a concise channel-provided failure reason, when available."""
        if not channel:
            return ""

        get_error = getattr(channel, "get_error", None)
        if callable(get_error):
            error = get_error()
            if isinstance(error, str) and error.strip():
                return error.strip()

        error_message = getattr(channel, "error_message", None)
        if isinstance(error_message, str) and error_message.strip():
            return error_message.strip()

        return ""

    # not_duplicate: send_message_sync_pair
    @handle_errors("sending message (sync)", default_return=False)
    def send_message_sync(
        self, channel_name: str, recipient: str, message: str, **kwargs
    ) -> bool:
        """Synchronous wrapper with logging health check"""
        # Check logging health periodically
        self._check_logging_health()

        # Queue immediately if channel is not ready
        channel = self._channels_dict.get(channel_name)
        if not self._channel_can_send(channel):
            logger.error(
                f"Channel {channel_name} not ready - queuing message for retry"
            )
            try:
                self.send_message_sync__queue_failed_message(
                    kwargs.get("user_id", ""),
                    kwargs.get("category", "unknown"),
                    message,
                    recipient,
                    channel_name,
                )
            except Exception as e:
                logger.warning(f"Failed to queue message for retry: {e}")
            return False

        try:
            # Double-check channel exists before attempting to send
            # This is a defensive check in case we somehow got past the earlier check
            if channel_name not in self._channels_dict:
                logger.error(
                    f"Channel {channel_name} not found in channels_dict - cannot send"
                )
                return False

            # Fallback to async send
            # Note: This should only be reached if channel exists and is ready
            # If we get here with a non-existent channel, something went wrong
            try:
                result = self.send_message_sync__run_async_sync(
                    self.send_message(channel_name, recipient, message, **kwargs)
                )
                # Ensure we return False if result is None or unexpected
                if result is None:
                    logger.warning(
                        f"Async send_message returned None for channel {channel_name}"
                    )
                    return False
                return result
            except Exception as e:
                logger.error(f"Fallback async send failed: {e}")
                return False

        except Exception as e:
            logger.error(f"Error in simplified send_message_sync: {e}")
            # Queue for retry if this is a scheduled message
            if "user_id" in kwargs and "category" in kwargs:
                self.send_message_sync__queue_failed_message(
                    kwargs["user_id"],
                    kwargs["category"],
                    message,
                    recipient,
                    channel_name,
                )
            return False

    @handle_errors("broadcasting message", default_return={})
    async def broadcast_message(
        self, recipients: dict[str, str], message: str
    ) -> dict[str, bool]:
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
        logger.info(
            f"Broadcast completed: {successful}/{len(recipients)} channels successful"
        )
        return results

    # not_duplicate: channel_status_vs_connectivity_details
    @handle_errors("getting channel status", user_friendly=False, default_return=None)
    async def get_channel_status(self, channel_name: str) -> ChannelStatus | None:
        """Get status of a specific channel"""
        channel = self._channels_dict.get(channel_name)
        if channel:
            return await channel.get_status()
        return None

    @handle_errors("getting all channel statuses", default_return={})
    async def get_all_statuses(self) -> dict[str, ChannelStatus]:
        """Get status of all channels"""
        statuses = {}
        for name, channel in self._channels_dict.items():
            if channel:
                statuses[name] = await channel.get_status()
        return statuses

    @handle_errors(
        "performing health check on all channels",
        user_friendly=False,
        default_return={},
    )
    async def health_check_all(self) -> dict[str, Any]:
        """Perform health check on all channels"""
        health_results = {}

        for name, channel in self._channels_dict.items():
            if channel:
                # Per-item error handling: continue processing other channels even if one fails
                try:
                    health_results[name] = await channel.get_health_status()
                except Exception as e:
                    health_results[name] = {"status": "error", "error": str(e)}

        return health_results

    # not_duplicate: channel_status_vs_connectivity_details
    @handle_errors("getting channel connectivity status", default_return=None)
    def get_channel_connectivity_status(
        self, channel_name: str
    ) -> dict[str, Any] | None:
        """Get detailed connectivity status for a channel if it exposes one."""
        channel = self._channels_dict.get(channel_name)
        if channel and hasattr(channel, "get_health_status"):
            return channel.get_health_status()
        return None

    @handle_errors(
        "shutting down all channels (async)", user_friendly=False, default_return=None
    )
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
                        loop.run_until_complete(
                            asyncio.wait_for(self._shutdown_all_async(), timeout=15.0)
                        )
                    except asyncio.TimeoutError:
                        logger.warning(
                            "Channel shutdown timed out after 15 seconds - forcing sync shutdown"
                        )
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

    @handle_errors(
        "shutting down all channels (sync)", user_friendly=False, default_return=None
    )
    def _shutdown_sync(self):
        """
        Synchronous shutdown method for all channels.

        Stops all communication channels and cleans up resources.
        """
        logger.info("Shutting down CommunicationManager...")
        self._running = False

        # Stop email polling
        self.email_inbound_processor.stop_polling()

        # Stop all channels
        for name, channel in self._channels_dict.items():
            try:
                if hasattr(channel, "shutdown"):
                    # Add timeout to prevent hanging
                    try:
                        asyncio.run(asyncio.wait_for(channel.shutdown(), timeout=10.0))
                    except asyncio.TimeoutError:
                        logger.warning(
                            f"Channel {name} shutdown timed out after 10 seconds"
                        )
                    except RuntimeError:
                        # Event loop already running - try sync approach
                        logger.warning(
                            f"Could not run async shutdown for {name} - event loop conflict"
                        )
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

    @handle_errors("receiving messages", default_return=[])
    async def receive_messages(self) -> list[dict[str, Any]]:
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
                    msg["channel"] = channel_name
                all_messages.extend(messages)
            except Exception as e:
                logger.error(f"Failed to receive messages from {channel_name}: {e}")

        logger.info(f"Total messages received: {len(all_messages)}")
        return all_messages

    @handle_errors(
        "handling message sending",
        default_return=MessageSendResult.failed(),
    )
    def handle_message_sending(
        self,
        user_id: str,
        category: str,
        is_scheduled_trigger: bool = False,
        allow_deferral: bool = True,
    ) -> MessageSendResult:
        """
        Handle sending messages for a user and category with improved recipient resolution.
        Now uses scheduled check-ins instead of random replacement.
        """
        logger.debug(
            "Handling message sending for user_id: "
            f"{user_id}, category: {category}, "
            f"is_scheduled_trigger={is_scheduled_trigger}, allow_deferral={allow_deferral}"
        )

        if not user_id:
            logger.error("User ID is not provided.")
            return MessageSendResult.failed(category=category)

        # Scheduled sends should defer if user is mid-flow or just completed one.
        if is_scheduled_trigger and allow_deferral:
            block_reason = _get_conversation_manager().get_flow_block_reason(user_id)
            if block_reason:
                logger.info(
                    f"Deferring scheduled message for user {user_id}, category {category}, reason={block_reason}"
                )
                return MessageSendResult.deferred(user_id, category)

        # Get user preferences
        prefs_result = get_user_data(user_id, "preferences", normalize_on_read=True)
        preferences = prefs_result.get("preferences")
        if not preferences:
            logger.error(f"User preferences not found for user {user_id}.")
            return MessageSendResult.failed(user_id, category)

        messaging_service = preferences.get("channel", {}).get("type")
        if not messaging_service:
            logger.error(f"No messaging service configured for user {user_id}")
            return MessageSendResult.failed(user_id, category)

        # Get the appropriate recipient ID for the messaging service
        recipient = self.get_recipient_for_service(
            user_id, messaging_service, preferences
        )
        if not recipient:
            logger.error(
                f"No valid recipient found for user {user_id} with service {messaging_service}"
            )
            return MessageSendResult.failed(user_id, category)

        # Handle check-in category specially
        if category == "checkin":
            self.checkin_dispatcher.handle_scheduled_checkin(
                user_id, messaging_service, recipient
            )
            return MessageSendResult.sent(user_id, category)

        # Handle AI-generated messages and track if message was actually sent
        message_sent = False
        sent_message_content = None
        if category in ["personalized", "ai_personalized"]:
            message_sent, sent_message_content = self._send_ai_generated_message(
                user_id, category, messaging_service, recipient
            )
        else:
            message_sent, sent_message_content = (
                self.predefined_dispatcher.send_predefined_message(
                    user_id, category, messaging_service, recipient
                )
            )

        # CRITICAL: Only expire check-in flows if a message was actually sent and delivered
        # Don't expire flows for failed sends or when no message was available to send
        if message_sent:
            # Only cancel check-in flows when responding to user input with unrelated content.
            if not is_scheduled_trigger:
                self._expire_checkin_flow_if_needed(user_id, category)

            # Message sending completion already logged above with full details
            return MessageSendResult.sent(
                user_id, category, sent_text=sent_message_content
            )
        logger.debug(
            f"No message sent for user {user_id}, category {category} - preserving any active check-in flow"
        )
        return MessageSendResult.skipped(user_id, category)

    @handle_errors(
        "expiring check-in flow if needed", user_friendly=False, default_return=None
    )
    def _expire_checkin_flow_if_needed(self, user_id: str, category: str):
        """Expire check-in flow if this is a non-scheduled message."""
        # Determine if this is a scheduled message or a response to user input
        is_scheduled_message = category in [
            "motivational",
            "health",
            "checkin",
            "task_reminders",
        ]

        if not is_scheduled_message:
            # This is a response to user input - expire any active check-in flow
            _get_conversation_manager().expire_checkin_flow_due_to_unrelated_outbound(
                user_id
            )
            logger.debug(
                f"Expired check-in flow for user {user_id} due to unrelated response message"
            )
        else:
            logger.debug(
                f"Skipping check-in flow expiration for scheduled {category} message to user {user_id}"
            )

    @handle_errors("getting recipient for service", default_return=None)
    def get_recipient_for_service(
        self, user_id: str, messaging_service: str, preferences: dict
    ) -> str | None:
        """
        Resolve channel recipient for a user (ServiceRequestDeliveryPort).

        Returns:
            Optional[str]: Recipient ID, None if failed
        """
        return self.recipient_resolver.get_recipient_for_service(
            user_id, messaging_service, preferences
        )

    # not_duplicate: checkin_prompt_delivery_boundary
    @handle_errors("sending check-in prompt", default_return=None)
    def send_checkin_prompt(
        self, user_id: str, messaging_service: str, recipient: str
    ):
        """Public delivery-port wrapper for scheduled check-in prompts."""
        self.checkin_dispatcher.send_checkin_prompt(
            user_id, messaging_service, recipient
        )

    @handle_errors("sending AI-generated message", default_return=(False, None))
    def _send_ai_generated_message(
        self, user_id: str, category: str, messaging_service: str, recipient: str
    ) -> tuple[bool, str | None]:
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
                from core.health_signals import get_message_guidance
                from integrations.google_health.personalization_rules import (
                    build_scheduled_message_context_prefix,
                )

                guidance = get_message_guidance(user_id)
                prefix = build_scheduled_message_context_prefix(guidance)
                context_prompt = "Generate a supportive, personalized message based on my recent activity and mood."
                if prefix:
                    context_prompt = f"{prefix} {context_prompt}"
                message_to_send = ai_bot.generate_contextual_response(
                    user_id, context_prompt, timeout=15
                )
            else:
                # Fallback to standard personalized message
                message_to_send = ai_bot.generate_personalized_message(user_id)

            import uuid

            message_id = str(uuid.uuid4())

            success = self.send_message_sync(
                messaging_service,
                recipient,
                message_to_send,
                user_id=user_id,
                category=category,
            )
            if success:
                # Get current time period for storage
                matching_periods, valid_periods = (
                    get_current_time_periods_with_validation(user_id, category)
                )
                current_time_period = matching_periods[0] if matching_periods else None
                store_sent_message(
                    user_id,
                    category,
                    message_id,
                    message_to_send,
                    time_period=current_time_period,
                )
                # Enhanced logging with message content
                message_preview = (
                    message_to_send[:50] + "..."
                    if len(message_to_send) > 50
                    else message_to_send
                )
                logger.info(
                    f"Sent contextual AI-generated message for user {user_id}, category {category} | Content: '{message_preview}'"
                )
                return True, message_to_send
            else:
                logger.error(f"Failed to send AI-generated message for user {user_id}")
                return False, None

        except Exception as e:
            logger.error(f"Error sending AI-generated message for user {user_id}: {e}")
            return False, None

    # NEW METHODS: More specific channel management methods
    @handle_errors("getting active channels", default_return=[])
    def get_active_channels(self) -> list[str]:
        """
        Get active channels with validation.

        Returns:
            List[str]: List of active channels, empty list if failed
        """
        """Get list of currently active/running channels"""
        return list(self._channels_dict.keys())

    @handle_errors("getting configured channels", default_return=[])
    def get_configured_channels(self) -> list[str]:
        """
        Get configured channels with validation.

        Returns:
            List[str]: List of configured channels, empty list if failed
        """
        """Get list of channels that are configured (from config)"""
        from core.config import get_available_channels

        return get_available_channels()

    @handle_errors("getting registered channels", default_return=[])
    def get_registered_channels(self) -> list[str]:
        """
        Get registered channels with validation.

        Returns:
            List[str]: List of registered channels, empty list if failed
        """
        """Get list of channels that are registered in the factory"""
        from communication.core.factory import ChannelFactory

        return ChannelFactory.get_registered_channels()

    # devtools: ignore[facade-shims]: required SchedulerDeliveryPort implementation delegates to owned dispatcher
    @handle_errors("handling task reminder", default_return=MessageSendResult.failed())
    def handle_task_reminder(
        self, user_id: str, task_identifier: str
    ) -> MessageSendResult:
        """
        Handle sending task reminders for a user.

        ``task_identifier`` matches the task record's canonical ``id`` (or another
        value ``get_task_by_id`` accepts), not the legacy JSON key ``task_id``.

        Returns:
            MessageSendResult: Standard send outcome for reminder dispatch.
        """
        return self.task_reminder_dispatcher.handle_task_reminder(
            user_id, task_identifier
        )

    @handle_errors("getting last task reminder", default_return=None)
    def get_last_task_reminder(self, user_id: str) -> str | None:
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
