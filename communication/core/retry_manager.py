# retry_manager.py

import threading
import time
import queue
from typing import Optional
from dataclasses import dataclass
from datetime import datetime

from core.logger import get_component_logger
from core.error_handling import handle_errors

# Route retry logs to communication component
retry_logger = get_component_logger('retry_manager')
logger = retry_logger

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

class RetryManager:
    """Manages message retry logic and failed message queuing"""
    
    @handle_errors("initializing retry manager", default_return=None)
    def __init__(self):
        """Initialize the retry manager"""
        self._failed_message_queue = queue.Queue()
        self._retry_thread = None
        self._retry_running = False
        
    @handle_errors("queueing failed message", default_return=None)
    def queue_failed_message(self, user_id: str, category: str, message: str, recipient: str, channel_name: str):
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

    @handle_errors("starting retry thread", default_return=None)
    def start_retry_thread(self):
        """Start the retry thread for failed messages"""
        if self._retry_thread and self._retry_thread.is_alive():
            return
        
        self._retry_running = True
        self._retry_thread = threading.Thread(target=self._retry_loop, daemon=True)
        self._retry_thread.start()
        logger.info("Started message retry thread")

    @handle_errors("stopping retry thread", default_return=None)
    def stop_retry_thread(self):
        """Stop the retry thread"""
        if self._retry_thread and self._retry_thread.is_alive():
            self._retry_running = False
            self._retry_thread.join(timeout=5)
            logger.debug("Retry thread stopped")

    @handle_errors("running retry loop", default_return=None)
    def _retry_loop(self):
        """Main retry loop that processes failed messages"""
        while self._retry_running:
            try:
                self._process_retry_queue()
                time.sleep(60)  # Check every minute
            except Exception as e:
                logger.error(f"Error in retry loop: {e}")
                time.sleep(60)  # Continue after error

    @handle_errors("processing retry queue", default_return=None)
    def _process_retry_queue(self):
        """Process the retry queue and attempt to resend failed messages"""
        try:
            # Process up to 10 messages per cycle to avoid blocking
            for _ in range(10):
                if self._failed_message_queue.empty():
                    break
                
                try:
                    queued_message = self._failed_message_queue.get_nowait()
                except queue.Empty:
                    break
                
                # Check if enough time has passed for retry
                time_since_failure = datetime.now() - queued_message.timestamp
                if time_since_failure.total_seconds() < queued_message.retry_delay:
                    # Put back in queue for later retry
                    self._failed_message_queue.put(queued_message)
                    continue
                
                # Attempt retry
                if queued_message.retry_count < queued_message.max_retries:
                    queued_message.retry_count += 1
                    logger.info(f"Retrying message for user {queued_message.user_id}, attempt {queued_message.retry_count}")
                    
                    # Here we would call the actual send method
                    # For now, we'll just log the retry attempt
                    # In the full implementation, this would call back to the communication manager
                    
                    # If retry fails, put back in queue with updated timestamp
                    queued_message.timestamp = datetime.now()
                    self._failed_message_queue.put(queued_message)
                else:
                    logger.warning(f"Max retries exceeded for message to user {queued_message.user_id}")
                    
        except Exception as e:
            logger.error(f"Error processing retry queue: {e}")

    @handle_errors("getting queue size", default_return=0)
    def get_queue_size(self) -> int:
        """Get the current size of the retry queue"""
        return self._failed_message_queue.qsize()

    @handle_errors("clearing retry queue", default_return=None)
    def clear_queue(self):
        """Clear all queued messages (use with caution)"""
        while not self._failed_message_queue.empty():
            try:
                self._failed_message_queue.get_nowait()
            except queue.Empty:
                break
        logger.info("Retry queue cleared")
