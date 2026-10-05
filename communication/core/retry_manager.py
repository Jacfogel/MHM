# retry_manager.py

import queue
import threading
import time
from dataclasses import dataclass
from datetime import datetime

from core.time_utilities import now_datetime_full

from core.logger import get_component_logger
from core.error_handling import handle_errors

# Route retry logs to communication component
retry_logger = get_component_logger("communication_manager")
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
    def __init__(self, send_callback=None):
        """
        Initialize the retry manager

        Args:
            send_callback: Optional callable that takes (channel_name, recipient, message, **kwargs)
                          and returns bool indicating success. If None, retries will only be logged.
        """
        self._failed_message_queue = queue.Queue()
        self._retry_thread = None
        self._retry_running = False
        self._send_callback = send_callback
        self._pending_keys: set[tuple[str, str, str, str, str]] = set()
        self._queue_lock = threading.Lock()

    @staticmethod
    @handle_errors(
        "building retry delivery key", default_return=("", "", "", "", "")
    )
    def _delivery_key(
        user_id: str,
        category: str,
        message: str,
        recipient: str,
        channel_name: str,
    ) -> tuple[str, str, str, str, str]:
        """Return the stable identity used to deduplicate one pending delivery."""
        return user_id, category, message, recipient, channel_name

    @handle_errors("releasing retry delivery key", default_return=None)
    def _release_pending_key(self, queued_message: QueuedMessage) -> None:
        """Allow a completed or exhausted delivery to be queued again later."""
        key = self._delivery_key(
            queued_message.user_id,
            queued_message.category,
            queued_message.message,
            queued_message.recipient,
            queued_message.channel_name,
        )
        with self._queue_lock:
            self._pending_keys.discard(key)

    @handle_errors("queueing failed message", default_return=False)
    def queue_failed_message(
        self,
        user_id: str,
        category: str,
        message: str,
        recipient: str,
        channel_name: str,
    ) -> bool:
        """Queue a failed delivery once while an equivalent retry is pending."""
        key = self._delivery_key(
            user_id, category, message, recipient, channel_name
        )
        with self._queue_lock:
            if key in self._pending_keys:
                logger.debug(
                    f"Retry already pending for user {user_id}, category {category}"
                )
                return False
            self._pending_keys.add(key)

        queued_message = QueuedMessage(
            user_id=user_id,
            category=category,
            message=message,
            recipient=recipient,
            channel_name=channel_name,
            timestamp=now_datetime_full(),
        )
        self._failed_message_queue.put(queued_message)
        logger.info(
            f"Queued failed message for user {user_id}, category {category} for retry"
        )
        return True

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
                now_dt = now_datetime_full()
                time_since_failure = now_dt - queued_message.timestamp
                if time_since_failure.total_seconds() < queued_message.retry_delay:
                    # Put back in queue for later retry
                    self._failed_message_queue.put(queued_message)
                    continue

                # Attempt retry
                if queued_message.retry_count < queued_message.max_retries:
                    queued_message.retry_count += 1
                    logger.info(
                        f"Retrying message for user {queued_message.user_id}, attempt {queued_message.retry_count}"
                    )

                    # Attempt to send the message using the callback if available
                    retry_success = False
                    if self._send_callback:
                        try:
                            # Call the send callback with message details
                            retry_success = self._send_callback(
                                queued_message.channel_name,
                                queued_message.recipient,
                                queued_message.message,
                                user_id=queued_message.user_id,
                                category=queued_message.category,
                            )
                            if retry_success:
                                logger.info(
                                    f"Successfully retried message for user {queued_message.user_id} on attempt {queued_message.retry_count}"
                                )
                            else:
                                logger.warning(
                                    f"Retry attempt {queued_message.retry_count} failed for user {queued_message.user_id}"
                                )
                        except Exception as e:
                            logger.error(
                                f"Error during retry attempt {queued_message.retry_count} for user {queued_message.user_id}: {e}"
                            )
                            retry_success = False
                    else:
                        # No callback available - just log the retry attempt
                        logger.warning(
                            f"Retry attempted but no send callback available for user {queued_message.user_id}"
                        )

                    # If retry failed, put back in queue with updated timestamp for next retry
                    if not retry_success:
                        queued_message.timestamp = now_datetime_full()
                        self._failed_message_queue.put(queued_message)
                    else:
                        self._release_pending_key(queued_message)
                else:
                    logger.warning(
                        f"Max retries exceeded for message to user {queued_message.user_id}"
                    )
                    self._release_pending_key(queued_message)

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
        with self._queue_lock:
            self._pending_keys.clear()
        logger.info("Retry queue cleared")
