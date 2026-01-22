"""
Tests for communication/core/retry_manager.py
"""

import pytest
import time
import threading
from datetime import datetime, timedelta
from unittest.mock import patch, Mock

from communication.core.retry_manager import RetryManager, QueuedMessage
from core.time_utilities import now_datetime_full


@pytest.mark.unit
@pytest.mark.communication
class TestQueuedMessage:
    """Test QueuedMessage dataclass."""

    def test_queued_message_creation(self):
        """Test creating a QueuedMessage with default values."""
        message = QueuedMessage(
            user_id="test_user",
            category="motivational",
            message="Test message",
            recipient="test@example.com",
            channel_name="email",
            timestamp=now_datetime_full(),
        )

        assert message.user_id == "test_user"
        assert message.category == "motivational"
        assert message.message == "Test message"
        assert message.recipient == "test@example.com"
        assert message.channel_name == "email"
        assert message.retry_count == 0
        assert message.max_retries == 3
        assert message.retry_delay == 300

    def test_queued_message_custom_values(self):
        """Test creating a QueuedMessage with custom values."""
        message = QueuedMessage(
            user_id="test_user",
            category="motivational",
            message="Test message",
            recipient="test@example.com",
            channel_name="email",
            timestamp=now_datetime_full(),
            retry_count=2,
            max_retries=5,
            retry_delay=600,
        )

        assert message.retry_count == 2
        assert message.max_retries == 5
        assert message.retry_delay == 600


@pytest.mark.unit
@pytest.mark.communication
class TestRetryManager:
    """Test RetryManager functionality."""

    @pytest.fixture
    def retry_manager(self):
        """Create RetryManager instance for testing."""
        return RetryManager()

    def test_retry_manager_initialization(self, retry_manager):
        """Test RetryManager initializes correctly."""
        assert retry_manager._failed_message_queue is not None
        assert retry_manager._retry_thread is None
        assert retry_manager._retry_running is False

    def test_queue_failed_message(self, retry_manager):
        """Test queueing a failed message."""
        with patch("communication.core.retry_manager.logger") as mock_logger:
            retry_manager.queue_failed_message(
                user_id="test_user",
                category="motivational",
                message="Test message",
                recipient="test@example.com",
                channel_name="email",
            )

            # Verify message was queued
            assert retry_manager.get_queue_size() == 1
            mock_logger.info.assert_called_once()

    def test_queue_failed_message_multiple(self, retry_manager):
        """Test queueing multiple failed messages."""
        with patch("communication.core.retry_manager.logger"):
            # Queue multiple messages
            for i in range(3):
                retry_manager.queue_failed_message(
                    user_id=f"test_user_{i}",
                    category="motivational",
                    message=f"Test message {i}",
                    recipient=f"test{i}@example.com",
                    channel_name="email",
                )

            assert retry_manager.get_queue_size() == 3

    def test_get_queue_size_empty(self, retry_manager):
        """Test getting queue size when empty."""
        assert retry_manager.get_queue_size() == 0

    def test_get_queue_size_with_messages(self, retry_manager):
        """Test getting queue size with messages."""
        with patch("communication.core.retry_manager.logger"):
            retry_manager.queue_failed_message(
                user_id="test_user",
                category="motivational",
                message="Test message",
                recipient="test@example.com",
                channel_name="email",
            )

            assert retry_manager.get_queue_size() == 1

    def test_clear_queue_empty(self, retry_manager):
        """Test clearing an empty queue."""
        with patch("communication.core.retry_manager.logger") as mock_logger:
            retry_manager.clear_queue()

            assert retry_manager.get_queue_size() == 0
            mock_logger.info.assert_called_once_with("Retry queue cleared")

    def test_clear_queue_with_messages(self, retry_manager):
        """Test clearing a queue with messages."""
        with patch("communication.core.retry_manager.logger"):
            # Add some messages
            for i in range(3):
                retry_manager.queue_failed_message(
                    user_id=f"test_user_{i}",
                    category="motivational",
                    message=f"Test message {i}",
                    recipient=f"test{i}@example.com",
                    channel_name="email",
                )

            assert retry_manager.get_queue_size() == 3

            # Clear the queue
            retry_manager.clear_queue()
            assert retry_manager.get_queue_size() == 0

    def test_start_retry_thread(self, retry_manager):
        """Test starting the retry thread."""
        with patch("communication.core.retry_manager.logger") as mock_logger:
            with patch("threading.Thread") as mock_thread_class:
                mock_thread = Mock()
                mock_thread_class.return_value = mock_thread

                retry_manager.start_retry_thread()

                assert retry_manager._retry_running is True
                mock_thread_class.assert_called_once()
                mock_thread.start.assert_called_once()
                mock_logger.info.assert_called_once_with("Started message retry thread")

    def test_start_retry_thread_already_running(self, retry_manager):
        """Test starting retry thread when already running."""
        with patch("communication.core.retry_manager.logger"):
            with patch("threading.Thread") as mock_thread_class:
                mock_thread = Mock()
                mock_thread.is_alive.return_value = True
                mock_thread_class.return_value = mock_thread

                # Start thread first time
                retry_manager.start_retry_thread()

                # Try to start again
                retry_manager.start_retry_thread()

                # Should only create one thread
                assert mock_thread_class.call_count == 1

    def test_stop_retry_thread(self, retry_manager):
        """Test stopping the retry thread."""
        with patch("communication.core.retry_manager.logger") as mock_logger:
            with patch("threading.Thread") as mock_thread_class:
                mock_thread = Mock()
                mock_thread.is_alive.return_value = True
                mock_thread_class.return_value = mock_thread

                # Start thread
                retry_manager.start_retry_thread()

                # Stop thread
                retry_manager.stop_retry_thread()

                assert retry_manager._retry_running is False
                mock_thread.join.assert_called_once_with(timeout=5)
                mock_logger.debug.assert_called_once_with("Retry thread stopped")

    def test_stop_retry_thread_not_running(self, retry_manager):
        """Test stopping retry thread when not running."""
        with patch("communication.core.retry_manager.logger"):
            # Try to stop when no thread is running
            retry_manager.stop_retry_thread()

            # Should not raise an error
            assert retry_manager._retry_running is False

    def test_process_retry_queue_empty(self, retry_manager):
        """Test processing an empty retry queue."""
        with patch("communication.core.retry_manager.logger"):
            # Process empty queue
            retry_manager._process_retry_queue()

            # Should not raise an error
            assert retry_manager.get_queue_size() == 0

    def test_process_retry_queue_with_messages(self, retry_manager):
        """Test processing retry queue with messages."""
        with patch("communication.core.retry_manager.logger"):
            # Add a message that's ready for retry
            retry_manager.queue_failed_message(
                user_id="test_user",
                category="motivational",
                message="Test message",
                recipient="test@example.com",
                channel_name="email",
            )

            # Make the message deterministically old enough for retry without patching the system clock.
            # This timestamp is production-behavior-sensitive, so keep it explicit and stable.
            queued_message = retry_manager._failed_message_queue.get()
            queued_message.timestamp = datetime(2000, 1, 1, 0, 0, 0)
            retry_manager._failed_message_queue.put(queued_message)

            retry_manager._process_retry_queue()

            # Message should be processed and requeued
            assert retry_manager.get_queue_size() == 1

    def test_process_retry_queue_message_not_ready(self, retry_manager):
        """Test processing retry queue when message is not ready for retry."""
        with patch("communication.core.retry_manager.logger"):
            # Add a message
            retry_manager.queue_failed_message(
                user_id="test_user",
                category="motivational",
                message="Test message",
                recipient="test@example.com",
                channel_name="email",
            )

            # Process immediately (message not ready for retry)
            retry_manager._process_retry_queue()

            # Message should still be in queue
            assert retry_manager.get_queue_size() == 1

    def test_process_retry_queue_max_retries_exceeded(self, retry_manager):
        """Test processing retry queue when max retries exceeded."""
        with patch("communication.core.retry_manager.logger") as mock_logger:
            # Add a message
            retry_manager.queue_failed_message(
                user_id="test_user",
                category="motivational",
                message="Test message",
                recipient="test@example.com",
                channel_name="email",
            )

            # Get the message and modify it to exceed max retries
            queued_message = retry_manager._failed_message_queue.get()
            queued_message.retry_count = 3  # Max retries
            queued_message.timestamp = datetime(
                2000, 1, 1, 0, 0, 0
            )  # Explicit old timestamp; deterministic for retry eligibility
            retry_manager._failed_message_queue.put(queued_message)

            # Process the queue
            retry_manager._process_retry_queue()

            # Message should be removed from queue
            assert retry_manager.get_queue_size() == 0
            mock_logger.warning.assert_called_once()

    def test_retry_loop_exception_handling(self, retry_manager):
        """Test retry loop handles exceptions gracefully."""
        with patch("communication.core.retry_manager.logger") as mock_logger:
            with patch.object(retry_manager, "_process_retry_queue") as mock_process:
                with patch("communication.core.retry_manager.time.sleep") as mock_sleep:
                    mock_process.side_effect = Exception("Test error")

                    # Set retry running to True
                    retry_manager._retry_running = True

                    # Set up the loop to exit after one iteration
                    def side_effect():
                        retry_manager._retry_running = False
                        raise Exception("Test error")

                    mock_process.side_effect = side_effect

                    # Run the loop
                    retry_manager._retry_loop()

                    # Should log the error and continue
                    mock_logger.error.assert_called_once()
                    mock_sleep.assert_called_once_with(60)

    def test_retry_loop_stops_when_running_false(self, retry_manager):
        """Test retry loop stops when _retry_running is False."""
        with patch("communication.core.retry_manager.logger"):
            with patch.object(retry_manager, "_process_retry_queue") as mock_process:
                # Set retry running to False
                retry_manager._retry_running = False

                # Run the loop
                retry_manager._retry_loop()

                # Should not process the queue
                mock_process.assert_not_called()

    def test_retry_loop_with_sleep(self, retry_manager):
        """Test retry loop includes sleep between iterations."""
        with patch("communication.core.retry_manager.logger"):
            with patch.object(retry_manager, "_process_retry_queue") as mock_process:
                with patch("communication.core.retry_manager.time.sleep") as mock_sleep:
                    # Set up the loop to run once
                    retry_manager._retry_running = True
                    mock_process.side_effect = lambda: setattr(
                        retry_manager, "_retry_running", False
                    )

                    # Run the loop
                    retry_manager._retry_loop()

                    # Should call sleep
                    mock_sleep.assert_called_once_with(60)

    def test_retry_loop_continues_after_error(self, retry_manager):
        """Test retry loop continues after processing error."""
        with patch("communication.core.retry_manager.logger"):
            with patch.object(retry_manager, "_process_retry_queue") as mock_process:
                with patch("communication.core.retry_manager.time.sleep") as mock_sleep:
                    # Set up the loop to run twice
                    call_count = 0

                    def side_effect():
                        nonlocal call_count
                        call_count += 1
                        if call_count == 1:
                            raise Exception("Test error")
                        else:
                            retry_manager._retry_running = False

                    mock_process.side_effect = side_effect
                    retry_manager._retry_running = True

                    # Run the loop
                    retry_manager._retry_loop()

                    # Should have called process twice (once with error, once to stop)
                    assert mock_process.call_count == 2
                    # Should have slept twice
                    assert mock_sleep.call_count == 2
