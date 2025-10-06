# channel_monitor.py

import threading
import time
from typing import Dict, Optional, Any
from datetime import datetime, timedelta

from core.logger import get_component_logger
from core.error_handling import handle_errors
from communication.communication_channels.base.base_channel import BaseChannel

# Route monitoring logs to communication component
monitor_logger = get_component_logger('channel_monitor')
logger = monitor_logger

class ChannelMonitor:
    """Monitors channel health and manages automatic restart logic"""
    
    @handle_errors("initializing channel monitor", default_return=None)
    def __init__(self):
        """Initialize the channel monitor"""
        try:
            self._restart_monitor_thread = None
            self._restart_monitor_running = False
            self._channel_failure_counts = {}  # Track consecutive failures per channel
            self._last_restart_attempts = {}   # Track last restart attempt time per channel
            self._max_consecutive_failures = 3  # Restart after 3 consecutive failures
            self._restart_cooldown = 300  # 5 minutes between restart attempts
            self._channels_dict = {}  # Reference to channels for monitoring
        except Exception as e:
            logger.error(f"Error initializing channel monitor: {e}")
            raise
        
    @handle_errors("setting channels for monitoring", default_return=None)
    def set_channels(self, channels_dict: Dict[str, BaseChannel]):
        """Set the channels dictionary for monitoring"""
        try:
            self._channels_dict = channels_dict
        except Exception as e:
            logger.error(f"Error setting channels for monitoring: {e}")
            raise
        
    @handle_errors("starting restart monitor", default_return=None)
    def start_restart_monitor(self):
        """Start the automatic restart monitor thread"""
        try:
            if self._restart_monitor_thread and self._restart_monitor_thread.is_alive():
                logger.debug("Restart monitor already running")
                return
            
            self._restart_monitor_running = True
            self._restart_monitor_thread = threading.Thread(
                target=self._restart_monitor_loop,
                daemon=True,
                name="RestartMonitor"
            )
            self._restart_monitor_thread.start()
            logger.info("Automatic restart monitor started")
        except Exception as e:
            logger.error(f"Error starting restart monitor: {e}")
            raise

    @handle_errors("stopping restart monitor", default_return=None)
    def stop_restart_monitor(self):
        """Stop the automatic restart monitor thread"""
        try:
            if self._restart_monitor_thread and self._restart_monitor_thread.is_alive():
                self._restart_monitor_running = False
                self._restart_monitor_thread.join(timeout=5)
                logger.debug("Restart monitor stopped")
        except Exception as e:
            logger.error(f"Error stopping restart monitor: {e}")
            raise

    def _restart_monitor_loop(self):
        """Main restart monitor loop that checks channel health"""
        while self._restart_monitor_running:
            try:
                self._check_and_restart_stuck_channels()
                time.sleep(60)  # Check every minute
            except Exception as e:
                logger.error(f"Error in restart monitor loop: {e}")
                time.sleep(60)  # Continue after error

    def _check_and_restart_stuck_channels(self):
        """Check for stuck channels and attempt restarts"""
        for channel_name, channel in self._channels_dict.items():
            try:
                # Check if channel is in a failed state
                if hasattr(channel, 'status') and channel.status == 'failed':
                    self._attempt_channel_restart(channel_name)
                elif hasattr(channel, 'is_healthy') and not channel.is_healthy():
                    self._attempt_channel_restart(channel_name)
            except Exception as e:
                logger.error(f"Error checking channel {channel_name}: {e}")

    def _attempt_channel_restart(self, channel_name: str):
        """Attempt to restart a specific channel"""
        try:
            # Check cooldown period
            last_attempt = self._last_restart_attempts.get(channel_name)
            if last_attempt and (datetime.now() - last_attempt).total_seconds() < self._restart_cooldown:
                return
            
            # Increment failure count
            self._channel_failure_counts[channel_name] = self._channel_failure_counts.get(channel_name, 0) + 1
            
            # Check if we should attempt restart
            if self._channel_failure_counts[channel_name] >= self._max_consecutive_failures:
                logger.warning(f"Attempting restart of channel {channel_name} after {self._channel_failure_counts[channel_name]} consecutive failures")
                
                # Attempt restart
                channel = self._channels_dict.get(channel_name)
                if channel and hasattr(channel, 'restart'):
                    try:
                        channel.restart()
                        logger.info(f"Successfully restarted channel {channel_name}")
                        # Reset failure count on successful restart
                        self._channel_failure_counts[channel_name] = 0
                    except Exception as e:
                        logger.error(f"Failed to restart channel {channel_name}: {e}")
                else:
                    logger.warning(f"Channel {channel_name} does not support restart")
                
                # Update last attempt time
                self._last_restart_attempts[channel_name] = datetime.now()
                
        except Exception as e:
            logger.error(f"Error attempting restart of channel {channel_name}: {e}")

    @handle_errors("recording channel failure", default_return=None)
    def record_channel_failure(self, channel_name: str):
        """Record a failure for a specific channel"""
        try:
            self._channel_failure_counts[channel_name] = self._channel_failure_counts.get(channel_name, 0) + 1
            logger.debug(f"Recorded failure for channel {channel_name}, total failures: {self._channel_failure_counts[channel_name]}")
        except Exception as e:
            logger.error(f"Error recording channel failure for {channel_name}: {e}")
            raise

    @handle_errors("recording channel success", default_return=None)
    def record_channel_success(self, channel_name: str):
        """Record a success for a specific channel (resets failure count)"""
        try:
            if channel_name in self._channel_failure_counts:
                self._channel_failure_counts[channel_name] = 0
                logger.debug(f"Reset failure count for channel {channel_name}")
        except Exception as e:
            logger.error(f"Error recording channel success for {channel_name}: {e}")
            raise

    def get_channel_health_status(self) -> Dict[str, Any]:
        """Get health status for all monitored channels"""
        status = {}
        for channel_name, channel in self._channels_dict.items():
            try:
                channel_status = {
                    'name': channel_name,
                    'failure_count': self._channel_failure_counts.get(channel_name, 0),
                    'last_restart_attempt': self._last_restart_attempts.get(channel_name),
                    'is_healthy': True  # Default assumption
                }
                
                # Check actual channel health if available
                if hasattr(channel, 'status'):
                    channel_status['status'] = channel.status
                    channel_status['is_healthy'] = channel.status != 'failed'
                elif hasattr(channel, 'is_healthy'):
                    channel_status['is_healthy'] = channel.is_healthy()
                
                status[channel_name] = channel_status
                
            except Exception as e:
                logger.error(f"Error getting health status for channel {channel_name}: {e}")
                status[channel_name] = {
                    'name': channel_name,
                    'error': str(e),
                    'is_healthy': False
                }
        
        return status

    @handle_errors("resetting channel failures", default_return=None)
    def reset_channel_failures(self, channel_name: str = None):
        """Reset failure counts for a specific channel or all channels"""
        try:
            if channel_name:
                if channel_name in self._channel_failure_counts:
                    self._channel_failure_counts[channel_name] = 0
                    logger.info(f"Reset failure count for channel {channel_name}")
            else:
                self._channel_failure_counts.clear()
                logger.info("Reset failure counts for all channels")
        except Exception as e:
            logger.error(f"Error resetting channel failures for {channel_name or 'all channels'}: {e}")
            raise
