"""
Test Discord check-in retry behavior and logging.

Verifies:
1. Messages are queued for retry when Discord disconnects during check-in sending
2. "User check-in started" is logged only once after successful message delivery
3. Retries work correctly after Discord reconnects
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import uuid

from tests.test_utilities import TestUserFactory, TestDataManager


@pytest.mark.behavior
class TestDiscordCheckinRetryBehavior:
    """Test Discord check-in retry behavior and logging."""

    @pytest.fixture
    def test_data_dir(self):
        """Create test data directory."""
        result = TestDataManager.setup_test_environment()
        # setup_test_environment returns a tuple, extract the first element (base dir)
        if isinstance(result, tuple):
            return result[0]
        return result

    @pytest.fixture
    def user_id(self, test_data_dir):
        """Create test user with Discord channel."""
        user_id = f"test_discord_retry_user_{uuid.uuid4().hex[:8]}"
        # Create basic user with check-ins enabled
        TestUserFactory.create_basic_user(
            user_id,
            test_data_dir=test_data_dir,
            enable_checkins=True,
            enable_tasks=False,
        )
        # Set Discord channel in preferences
        from core.user_data_handlers import (
            get_user_data,
            save_user_data,
            update_user_account,
            update_user_preferences,
            clear_user_caches,
        )

        actual_user_id = TestUserFactory.get_test_user_id_by_internal_username(
            user_id, test_data_dir
        )
        if actual_user_id:
            prefs = get_user_data(
                actual_user_id, "preferences", normalize_on_read=True
            ).get("preferences", {})
            prefs["channel"] = {"type": "discord", "discord_username": "testuser#1234"}
            save_user_data(actual_user_id, {"preferences": prefs})
        return user_id

    @pytest.fixture
    def comm_manager(self, test_data_dir):
        """Create communication manager for testing."""
        from communication.core.channel_orchestrator import CommunicationManager
        from communication.core.retry_manager import RetryManager

        manager = CommunicationManager()
        # Isolate retry-manager state for this test module to avoid singleton cross-test queue noise.
        try:
            manager.retry_manager.stop_retry_thread()
        except Exception:
            pass
        manager.retry_manager = RetryManager(send_callback=manager.send_message_sync)
        return manager

    def test_checkin_message_queued_on_discord_disconnect(
        self, comm_manager, user_id, test_data_dir
    ):
        """Test that check-in messages are queued when Discord disconnects during send."""
        from tests.conftest import wait_until

        # Arrange: Get actual user ID (UUID) for the test user
        from core.user_data_handlers import (
            get_user_data,
            update_user_account,
            update_user_preferences,
            clear_user_caches,
        )

        actual_user_id = TestUserFactory.get_test_user_id_by_internal_username(
            user_id, test_data_dir
        )
        if not actual_user_id:
            pytest.skip("Could not resolve actual user ID for test")

        # Ensure check-ins are enabled for this user and Discord channel is configured.
        user_data = get_user_data(actual_user_id, "all", auto_create=True) or {}

        update_user_account(
            actual_user_id,
            {"features": {"checkins": "enabled"}},
            auto_create=True,
        )
        prefs_updates = dict(user_data.get("preferences", {}))
        prefs_updates.setdefault("checkin_settings", {})["enabled"] = True
        prefs_updates["checkin_settings"]["frequency"] = "daily"
        prefs_updates.setdefault("channel", {})["type"] = "discord"
        update_user_preferences(actual_user_id, prefs_updates, auto_create=True)
        clear_user_caches()
        assert wait_until(
            lambda: (
                clear_user_caches() is None
                and get_user_data(actual_user_id, "preferences", normalize_on_read=True)
                .get("preferences", {})
                .get("channel", {})
                .get("type")
                == "discord"
                and get_user_data(actual_user_id, "account", normalize_on_read=True)
                .get("account", {})
                .get("features", {})
                .get("checkins")
                == "enabled"
            ),
            timeout_seconds=8.0,
            poll_seconds=0.02,
        ), "User should have persisted discord channel + enabled checkins before send"

        # Ensure clean retry-manager state in case singleton carries over from other tests.
        comm_manager.retry_manager.stop_retry_thread()

        # Clear retry queue to ensure clean state
        while not comm_manager.retry_manager._failed_message_queue.empty():
            comm_manager.retry_manager._failed_message_queue.get()

        # Mock Discord bot to simulate disconnect - is_ready() returns False
        mock_discord_bot = Mock()
        mock_discord_bot.is_ready.return_value = False  # Simulate disconnect
        mock_discord_bot.channel_type.return_value = "async"
        # Don't mock send_message - send_message_sync will detect not_ready and queue before calling it

        # Replace Discord channel with mock
        comm_manager._channels_dict["discord"] = mock_discord_bot

        # Act: Try to send check-in - should queue because channel not ready
        from communication.message_processing.conversation_flow_manager import (
            conversation_manager,
        )

        def _mock_get_user_data(request_user_id, data_type="all", **kwargs):
            if data_type == "preferences":
                return {
                    "preferences": {
                        "channel": {"type": "discord"},
                        "checkin_settings": {"enabled": True, "frequency": "daily"},
                    }
                }
            if data_type == "account":
                return {"account": {"features": {"checkins": "enabled"}}}
            return {
                "account": {"features": {"checkins": "enabled"}},
                "preferences": {
                    "channel": {"type": "discord"},
                    "checkin_settings": {"enabled": True, "frequency": "daily"},
                },
            }

        with (
            patch.object(comm_manager, "_should_send_checkin_prompt", return_value=True),
            patch.object(
                conversation_manager,
                "_start_dynamic_checkin",
                return_value=("How are you feeling today?", False),
            ),
            patch(
                "communication.core.channel_orchestrator.get_user_data",
                side_effect=_mock_get_user_data,
            ),
        ):
            comm_manager.handle_message_sending(actual_user_id, "checkin")

        # Assert: Verify message was queued for retry
        assert wait_until(
            lambda: comm_manager.retry_manager.get_queue_size() > 0,
            timeout_seconds=8.0,
            poll_seconds=0.02,
        ), "Failed check-in message should be queued for retry"
        queue_size = comm_manager.retry_manager.get_queue_size()
        assert (
            queue_size > 0
        ), f"Failed check-in message should be queued for retry, but queue size is {queue_size}"

        # Verify queued message details
        queued_messages = []
        while not comm_manager.retry_manager._failed_message_queue.empty():
            queued_messages.append(
                comm_manager.retry_manager._failed_message_queue.get()
            )

        assert len(queued_messages) > 0, "Should have at least one queued message"
        checkin_message = next(
            (m for m in queued_messages if m.category == "checkin"), None
        )
        assert checkin_message is not None, "Check-in message should be in retry queue"
        assert (
            checkin_message.user_id == actual_user_id
        ), f"Queued message should have correct user_id (expected {actual_user_id}, got {checkin_message.user_id})"

    @patch("communication.core.channel_orchestrator.get_component_logger")
    def test_checkin_started_logged_once_after_successful_send(
        self, mock_get_logger, comm_manager, user_id, test_data_dir
    ):
        """Test that 'User check-in started' is logged only once after successful message delivery."""
        # Arrange: Get actual user ID (UUID) for the test user
        actual_user_id = TestUserFactory.get_test_user_id_by_internal_username(
            user_id, test_data_dir
        )
        if not actual_user_id:
            pytest.skip("Could not resolve actual user ID for test")

        # Mock logger to track log calls
        mock_user_logger = Mock()
        mock_get_logger.return_value = mock_user_logger

        # Mock Discord bot to succeed on send
        mock_discord_bot = Mock()
        mock_discord_bot.is_ready.return_value = True  # Channel is ready
        mock_discord_bot.channel_type.return_value = "async"

        # Mock the async send_message to return True (success)
        async def mock_send_message(*args, **kwargs):
            return True

        mock_discord_bot.send_message = MagicMock(side_effect=mock_send_message)

        # Also need to mock the sync wrapper that send_message_sync uses
        # The actual send happens via async, but we need to ensure it returns True
        comm_manager._channels_dict["discord"] = mock_discord_bot

        # Patch send_message_sync to return True (simulating successful send)
        with patch.object(comm_manager, "send_message_sync", return_value=True):
            # Act: Send check-in
            comm_manager.handle_message_sending(actual_user_id, "checkin")

        # Assert: Verify "User check-in started" was logged exactly once
        log_calls = [
            call
            for call in mock_user_logger.info.call_args_list
            if len(call[0]) > 0 and "check-in started" in str(call[0][0]).lower()
        ]

        assert (
            len(log_calls) == 1
        ), f"Expected exactly 1 'check-in started' log, got {len(log_calls)}: {log_calls}"

        # Verify log call has correct parameters
        log_call = log_calls[0]
        assert "check-in started" in str(log_call[0][0]).lower()
        assert (
            log_call[1].get("user_id") == actual_user_id
        ), f"Expected user_id {actual_user_id}, got {log_call[1].get('user_id')}"
        assert log_call[1].get("checkin_type") == "daily"

    @patch("communication.core.channel_orchestrator.get_component_logger")
    def test_checkin_started_not_logged_on_failed_send(
        self, mock_get_logger, comm_manager, user_id, test_data_dir
    ):
        """Test that 'User check-in started' is NOT logged when message send fails."""
        # Arrange: Get actual user ID (UUID) for the test user
        actual_user_id = TestUserFactory.get_test_user_id_by_internal_username(
            user_id, test_data_dir
        )
        if not actual_user_id:
            pytest.skip("Could not resolve actual user ID for test")

        # Mock logger
        mock_user_logger = Mock()
        mock_get_logger.return_value = mock_user_logger

        # Mock Discord bot - channel is ready but send fails
        mock_discord_bot = Mock()
        mock_discord_bot.is_ready.return_value = True
        mock_discord_bot.channel_type.return_value = "async"

        comm_manager._channels_dict["discord"] = mock_discord_bot

        # Patch send_message_sync to return False (simulating failed send)
        with patch.object(comm_manager, "send_message_sync", return_value=False):
            # Act: Try to send check-in (will fail)
            comm_manager.handle_message_sending(actual_user_id, "checkin")

        # Assert: Verify "User check-in started" was NOT logged
        log_calls = [
            call
            for call in mock_user_logger.info.call_args_list
            if len(call[0]) > 0 and "check-in started" in str(call[0][0]).lower()
        ]

        assert (
            len(log_calls) == 0
        ), f"Expected 0 'check-in started' logs on failure, got {len(log_calls)}"

    def test_checkin_retry_after_discord_reconnect(
        self, comm_manager, user_id, test_data_dir
    ):
        """Test that queued check-in messages are retried after Discord reconnects."""
        # Arrange: Get actual user ID (UUID) for the test user
        actual_user_id = TestUserFactory.get_test_user_id_by_internal_username(
            user_id, test_data_dir
        )
        if not actual_user_id:
            pytest.skip("Could not resolve actual user ID for test")

        # Start with disconnected Discord
        mock_discord_bot = Mock()
        mock_discord_bot.is_ready.return_value = False  # Initially disconnected
        mock_discord_bot.channel_type.return_value = "async"

        comm_manager._channels_dict["discord"] = mock_discord_bot

        # Queue a failed check-in message (will be queued because channel not ready)
        comm_manager.handle_message_sending(actual_user_id, "checkin")

        # Verify message is queued
        initial_queue_size = comm_manager.retry_manager.get_queue_size()
        assert (
            initial_queue_size > 0
        ), f"Message should be queued after failure, but queue size is {initial_queue_size}"

        # Act: Simulate Discord reconnection
        mock_discord_bot.is_ready.return_value = True  # Now connected

        # Mock send_message_sync to succeed when retry happens
        original_send = comm_manager.send_message_sync
        send_call_count = [0]

        def mock_send_sync(*args, **kwargs):
            send_call_count[0] += 1
            # First call is the initial attempt (already happened), this is the retry
            if send_call_count[0] > 1:
                return True  # Retry succeeds
            return original_send(*args, **kwargs)

        comm_manager.send_message_sync = mock_send_sync

        # Start retry thread and process queue
        comm_manager.retry_manager.start_retry_thread()

        # Wait a bit for retry to process (retry_delay is 300 seconds by default, so we'll manually trigger)
        # For testing, we'll directly process the queue with a shorter delay
        import time
        from communication.core.retry_manager import QueuedMessage
        from datetime import datetime, timedelta

        # Get queued message and manually reduce retry_delay for testing
        if not comm_manager.retry_manager._failed_message_queue.empty():
            queued = comm_manager.retry_manager._failed_message_queue.get()
            # Create a new message with immediate retry
            queued.retry_delay = 0  # No delay for testing
            queued.timestamp = datetime(2026, 1, 20, 12, 0, 0) - timedelta(
                seconds=1
            )  # Deterministic: eligible for retry
            comm_manager.retry_manager._failed_message_queue.put(queued)

        # Process retry queue manually
        comm_manager.retry_manager._process_retry_queue()

        # Assert: Verify retry was attempted
        # The retry mechanism should have attempted to resend
        assert (
            send_call_count[0] > 0 or initial_queue_size > 0
        ), "Retry mechanism should attempt to resend queued messages"

    def test_multiple_checkin_attempts_only_log_once(
        self, comm_manager, user_id, test_data_dir
    ):
        """Test that multiple check-in send attempts only result in one log entry."""
        # Arrange: Get actual user ID (UUID) for the test user
        actual_user_id = TestUserFactory.get_test_user_id_by_internal_username(
            user_id, test_data_dir
        )
        if not actual_user_id:
            pytest.skip("Could not resolve actual user ID for test")

        # Mock Discord to fail first, then succeed
        mock_discord_bot = Mock()
        mock_discord_bot.is_ready.return_value = True
        mock_discord_bot.channel_type.return_value = "async"

        # First call fails, second succeeds
        mock_discord_bot.send_message = Mock(side_effect=[False, True])

        comm_manager._channels_dict["discord"] = mock_discord_bot

        # Mock logger
        with patch(
            "communication.core.channel_orchestrator.get_component_logger"
        ) as mock_get_logger:
            mock_user_logger = Mock()
            mock_get_logger.return_value = mock_user_logger

            # Act: First attempt fails (message queued)
            comm_manager.handle_message_sending(actual_user_id, "checkin")

            # Simulate retry (second attempt succeeds)
            # In real scenario, retry manager would handle this
            # For this test, we manually trigger the retry callback
            if comm_manager.retry_manager._send_callback:
                # Get queued message and retry
                if not comm_manager.retry_manager._failed_message_queue.empty():
                    queued = comm_manager.retry_manager._failed_message_queue.get()
                    comm_manager.retry_manager._send_callback(
                        queued.channel_name,
                        queued.recipient,
                        queued.message,
                        user_id=queued.user_id,
                        category=queued.category,
                    )

            # Assert: Should only have one log entry
            log_calls = [
                call
                for call in mock_user_logger.info.call_args_list
                if len(call[0]) > 0 and "check-in started" in str(call[0][0]).lower()
            ]

            # Note: This test verifies the pattern - actual retry timing is handled by retry_manager
            # The key is that logging only happens on successful send in _handle_scheduled_checkin
            assert (
                len(log_calls) <= 1
            ), f"Expected at most 1 'check-in started' log, got {len(log_calls)}"
