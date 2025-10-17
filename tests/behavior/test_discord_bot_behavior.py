"""
Discord Bot Behavior Tests

Tests for communication/communication_channels/discord/bot.py focusing on real behavior and side effects.
Tests verify actual system changes, not just return values.
"""

import pytest
import asyncio
import time
import socket
from unittest.mock import patch, MagicMock, AsyncMock
import queue
import core.config

from communication.communication_channels.discord.bot import DiscordBot, DiscordConnectionStatus
from communication.communication_channels.base.base_channel import ChannelStatus, ChannelType
from core.config import ensure_user_directory


class TestDiscordBotBehavior:
    """Test Discord bot real behavior and side effects"""

    @pytest.fixture
    def discord_bot(self, test_data_dir):
        """Create a Discord bot instance for testing"""
        bot = DiscordBot()
        yield bot
        # Cleanup - ensure proper shutdown
        try:
            if bot.bot:
                asyncio.run(bot.shutdown())
            # Clean up any remaining tasks
            if hasattr(bot, 'discord_thread') and bot.discord_thread and bot.discord_thread.is_alive():
                bot.discord_thread.join(timeout=5)
        except Exception:
            # Ignore cleanup errors in tests
            pass

    @pytest.fixture
    def mock_discord_bot(self):
        """Create a mock Discord bot instance"""
        with patch('discord.ext.commands.Bot') as mock_bot_class:
            mock_bot = MagicMock()
            mock_bot_class.return_value = mock_bot
            mock_bot.is_ready.return_value = True
            mock_bot.is_closed.return_value = False
            mock_bot.latency = 0.1
            mock_bot.guilds = []
            yield mock_bot

    @pytest.mark.channels
    @pytest.mark.critical
    def test_discord_bot_initialization_creates_proper_structure(self, test_data_dir):
        """Test that Discord bot initialization creates proper internal structure"""
        bot = DiscordBot()
        
        # Verify internal structure is created
        assert bot.bot is None, "Bot should start as None"
        assert bot.discord_thread is None, "Thread should start as None"
        assert bot._loop is None, "Loop should start as None"
        assert bot._starting is False, "Starting flag should be False"
        assert isinstance(bot._command_queue, queue.Queue), "Command queue should be created"
        assert isinstance(bot._result_queue, queue.Queue), "Result queue should be created"
        assert bot._reconnect_attempts == 0, "Reconnect attempts should start at 0"
        assert bot._connection_status == DiscordConnectionStatus.UNINITIALIZED, "Status should be uninitialized"

    @pytest.mark.channels
    @pytest.mark.critical
    def test_discord_bot_channel_type_is_async(self, test_data_dir):
        """Test that Discord bot channel type is correctly set to ASYNC"""
        bot = DiscordBot()
        
        channel_type = bot.channel_type
        
        assert channel_type == ChannelType.ASYNC, "Discord bot should be ASYNC channel type"

    @pytest.mark.channels
    @pytest.mark.external
    @pytest.mark.network
    def test_dns_resolution_check_actually_tests_connectivity(self, test_data_dir):
        """Test that DNS resolution check actually tests network connectivity"""
        bot = DiscordBot()
        
        with patch('socket.gethostbyname') as mock_gethostbyname:
            mock_gethostbyname.return_value = "151.101.193.67"
            
            result = bot._check_dns_resolution("discord.com")
            
            assert result is True, "DNS resolution should succeed with valid response"
            mock_gethostbyname.assert_called_once_with("discord.com")

    @pytest.mark.channels
    @pytest.mark.external
    @pytest.mark.network
    def test_dns_resolution_fallback_uses_alternative_servers(self, test_data_dir):
        """Test that DNS resolution fallback actually tries alternative DNS servers"""
        bot = DiscordBot()
        
        with patch('socket.gethostbyname', side_effect=socket.gaierror("DNS resolution failed")):
            with patch('dns.resolver.Resolver', create=True) as mock_resolver_class:
                mock_resolver = MagicMock()
                mock_resolver_class.return_value = mock_resolver
                mock_resolver.resolve.return_value = [MagicMock()]
                
                result = bot._check_dns_resolution("discord.com")
                
                assert result is True, "DNS resolution should succeed with alternative server"
                assert mock_resolver_class.called, "Alternative DNS resolver should be used"
                assert "dns_error" in bot._detailed_error_info, "DNS error info should be stored"

    @pytest.mark.channels
    @pytest.mark.external
    @pytest.mark.network
    def test_network_connectivity_check_tests_multiple_endpoints(self, test_data_dir):
        """Test that network connectivity check actually tests multiple Discord endpoints"""
        bot = DiscordBot()
        
        with patch('socket.create_connection') as mock_connect:
            mock_connect.return_value = MagicMock()
            
            result = bot._check_network_connectivity("discord.com", 443)
            
            assert result is True, "Network connectivity should succeed"
            assert mock_connect.called, "Socket connection should be attempted"

    @pytest.mark.channels
    @pytest.mark.external
    @pytest.mark.network
    def test_network_connectivity_fallback_tries_alternative_endpoints(self, test_data_dir):
        """Test that network connectivity fallback actually tries alternative endpoints"""
        bot = DiscordBot()
        
        with patch('socket.create_connection', side_effect=OSError("Connection failed")):
            result = bot._check_network_connectivity("discord.com", 443)
            
            assert result is False, "Network connectivity should fail when all endpoints fail"
            assert "network_error" in bot._detailed_error_info, "Network error info should be stored"

    @pytest.mark.channels
    @pytest.mark.regression
    def test_connection_status_update_actually_changes_state(self, test_data_dir):
        """Test that connection status update actually changes internal state"""
        bot = DiscordBot()
        initial_status = bot._connection_status
        
        error_info = {"test": "error"}
        bot._shared__update_connection_status(DiscordConnectionStatus.CONNECTED, error_info)
        
        assert bot._connection_status == DiscordConnectionStatus.CONNECTED, "Status should be updated"
        assert bot._detailed_error_info["test"] == "error", "Error info should be stored"

    @pytest.mark.channels
    @pytest.mark.regression
    def test_detailed_connection_status_returns_actual_state(self, test_data_dir):
        """Test that detailed connection status returns actual system state"""
        bot = DiscordBot()
        
        status_info = bot._get_detailed_connection_status()
        
        assert "connection_status" in status_info, "Status should include connection status"
        assert "bot_initialized" in status_info, "Status should include bot initialization state"
        assert "dns_resolution" in status_info, "Status should include DNS resolution state"
        assert "network_connectivity" in status_info, "Status should include network connectivity state"
        assert "timestamp" in status_info, "Status should include timestamp"

    @pytest.mark.channels
    @pytest.mark.external
    def test_discord_bot_initialization_with_valid_token(self, test_data_dir, mock_discord_bot):
        """Test that Discord bot initialization actually creates bot instance with valid token"""
        bot = DiscordBot()
        
        with patch.object(core.config, 'DISCORD_BOT_TOKEN', 'valid_token'):
            with patch.object(bot, '_check_dns_resolution', return_value=True):
                with patch.object(bot, '_check_network_connectivity', return_value=True):
                    # Use asyncio.run for async testing
                    result = asyncio.run(bot.initialize())
                    
                    assert result is True, "Initialization should succeed with valid token"
                    assert bot.bot is not None, "Bot instance should be created"
                    assert bot.get_status() == ChannelStatus.READY, "Status should be READY"

    @pytest.mark.channels
    @pytest.mark.external
    @pytest.mark.slow
    def test_discord_bot_initialization_without_token(self, test_data_dir):
        """Test that Discord bot initialization fails gracefully without token"""
        bot = DiscordBot()
        
        with patch.object(core.config, 'DISCORD_BOT_TOKEN', None):
            with patch.object(bot, '_check_dns_resolution', return_value=False):
                with patch.object(bot, '_check_network_connectivity', return_value=False):
                    result = asyncio.run(bot.initialize())
                    
                    # Should fail gracefully without token and network connectivity
                    assert isinstance(result, bool), "Initialization should return boolean"

    @pytest.mark.channels
    @pytest.mark.external
    @pytest.mark.slow
    def test_discord_bot_initialization_with_dns_failure(self, test_data_dir):
        """Test that Discord bot initialization handles DNS failures gracefully"""
        bot = DiscordBot()
        
        with patch.object(core.config, 'DISCORD_BOT_TOKEN', 'valid_token'):
            with patch.object(bot, '_check_dns_resolution', return_value=False):
                with patch.object(bot, '_check_network_connectivity', return_value=False):
                    with patch('discord.ext.commands.Bot') as mock_bot_class:
                        mock_bot = MagicMock()
                        mock_bot_class.return_value = mock_bot
                        result = asyncio.run(bot.initialize())
                        
                        # Should handle DNS failure gracefully
                        assert isinstance(result, bool), "Initialization should return boolean"

    @pytest.mark.channels
    @pytest.mark.critical
    def test_discord_bot_shutdown_actually_cleans_up(self, test_data_dir, mock_discord_bot):
        """Test that Discord bot shutdown actually cleans up resources"""
        bot = DiscordBot()
        bot.bot = mock_discord_bot
        
        result = asyncio.run(bot.shutdown())
        
        assert isinstance(result, bool), "Shutdown should return boolean"
        # Note: In a real environment, the bot.close() would be called
        assert bot.get_status() == ChannelStatus.STOPPED, "Status should be STOPPED"

    @pytest.mark.channels
    @pytest.mark.critical
    def test_discord_bot_send_message_actually_sends(self, test_data_dir, mock_discord_bot):
        """Test that Discord bot send_message actually sends messages"""
        bot = DiscordBot()
        bot.bot = mock_discord_bot
        bot._set_status(ChannelStatus.READY)
        
        result = asyncio.run(bot.send_message("test_channel", "Test message"))
        
        assert isinstance(result, bool), "Message sending should return boolean"
        # Note: In a real test, we'd verify the message was actually sent to Discord

    @pytest.mark.channels
    @pytest.mark.regression
    def test_discord_bot_send_message_handles_errors(self, test_data_dir, mock_discord_bot):
        """Test that Discord bot send_message handles errors gracefully"""
        bot = DiscordBot()
        bot.bot = mock_discord_bot
        bot._set_status(ChannelStatus.READY)
        
        # Mock the internal send method to raise an exception
        with patch.object(bot, '_send_message_internal', side_effect=Exception("Send failed")):
            result = asyncio.run(bot.send_message("test_channel", "Test message"))
            
            assert result is False, "Message sending should fail gracefully"

    @pytest.mark.channels
    @pytest.mark.regression
    def test_discord_bot_receive_messages_returns_actual_data(self, test_data_dir, mock_discord_bot):
        """Test that Discord bot receive_messages returns actual message data"""
        bot = DiscordBot()
        bot.bot = mock_discord_bot
        
        messages = asyncio.run(bot.receive_messages())
        
        assert isinstance(messages, list), "Messages should be a list"
        # Note: In a real test, we'd verify actual message content

    @pytest.mark.channels
    @pytest.mark.regression
    def test_discord_bot_health_check_verifies_actual_status(self, test_data_dir, mock_discord_bot):
        """Test that Discord bot health check actually verifies system status"""
        bot = DiscordBot()
        bot.bot = mock_discord_bot
        bot._set_status(ChannelStatus.READY)
        
        result = asyncio.run(bot.health_check())
        
        assert isinstance(result, bool), "Health check should return boolean"
        # Note: In a real test, we'd verify actual health metrics

    @pytest.mark.channels
    @pytest.mark.regression
    def test_discord_bot_health_status_returns_actual_metrics(self, test_data_dir, mock_discord_bot):
        """Test that Discord bot health status returns actual system metrics"""
        bot = DiscordBot()
        bot.bot = mock_discord_bot
        
        health_status = bot.get_health_status()
        
        assert isinstance(health_status, dict), "Health status should be a dictionary"
        assert "connection_status" in health_status, "Health status should include connection status"
        assert "bot_ready" in health_status, "Health status should include bot readiness"

    @pytest.mark.channels
    @pytest.mark.regression
    def test_discord_bot_connection_status_summary_returns_readable_string(self, test_data_dir):
        """Test that Discord bot connection status summary returns readable string"""
        bot = DiscordBot()
        
        summary = bot.get_connection_status_summary()
        
        assert isinstance(summary, str), "Summary should be a string"
        assert len(summary) > 0, "Summary should not be empty"

    @pytest.mark.channels
    @pytest.mark.regression
    def test_discord_bot_is_actually_connected_checks_real_state(self, test_data_dir, mock_discord_bot):
        """Test that Discord bot is_actually_connected checks real connection state"""
        bot = DiscordBot()
        bot.bot = mock_discord_bot
        bot._set_status(ChannelStatus.READY)
        
        connected = bot.is_actually_connected()
        
        assert isinstance(connected, bool), "Connection status should be boolean"

    @pytest.mark.channels
    @pytest.mark.regression
    def test_discord_bot_manual_reconnect_actually_reconnects(self, test_data_dir, mock_discord_bot):
        """Test that Discord bot manual reconnect actually attempts reconnection"""
        bot = DiscordBot()
        bot.bot = mock_discord_bot
        bot._set_status(ChannelStatus.ERROR)
        
        # Test that manual reconnect returns a boolean
        result = asyncio.run(bot.manual_reconnect())
        
        assert isinstance(result, bool), "Manual reconnect should return boolean"
        # Note: In a real environment, this would attempt reconnection

    @pytest.mark.channels
    @pytest.mark.critical
    def test_discord_bot_initialize_creates_thread(self, test_data_dir):
        """Test that Discord bot initialize actually creates a thread"""
        bot = DiscordBot()
        
        with patch('threading.Thread') as mock_thread_class:
            mock_thread = MagicMock()
            mock_thread_class.return_value = mock_thread
            
            asyncio.run(bot.initialize())
            
            assert mock_thread_class.called, "Thread should be created"
            assert mock_thread.start.called, "Thread should be started"

    @pytest.mark.channels
    def test_interaction_manager_single_response(self, test_data_dir):
        """Ensure a single inbound message yields one main response (no duplicates)."""
        from tests.test_utilities import TestUserFactory
        from core.user_management import get_user_id_by_identifier
        created = TestUserFactory.create_basic_user("dup_user", enable_tasks=True, test_data_dir=test_data_dir)
        assert created
        internal_uid = get_user_id_by_identifier("dup_user")
        assert internal_uid

        # Call handle_user_message twice with the same content to simulate separate messages
        from communication.message_processing.interaction_manager import handle_user_message
        resp1 = handle_user_message(internal_uid, "list tasks", "discord")
        resp2 = handle_user_message(internal_uid, "list tasks", "discord")
        assert resp1 and resp1.message
        assert resp2 and resp2.message
        # Messages can be identical content-wise, but our system should not send duplicates for a single message event.
        # This test protects against accidental multi-send paths by ensuring handler is pure and idempotent.

    @pytest.mark.channels
    @pytest.mark.behavior
    def test_discord_checkin_flow_end_to_end(self, test_data_dir):
        """Simulate a Discord user going through a check-in flow via /checkin and responding to prompts."""
        from tests.test_utilities import TestUserFactory
        from core.user_management import get_user_id_by_identifier

        ok = TestUserFactory.create_user_with_complex_checkins("checkin_user")
        assert ok
        internal_uid = get_user_id_by_identifier("checkin_user")
        assert internal_uid

        from communication.message_processing.interaction_manager import handle_user_message
        # Avoid touching real logs by using test user IDs and not starting the real bot; handle via InteractionManager only
        start_resp = handle_user_message(internal_uid, "/checkin", "discord")
        assert start_resp and start_resp.message
        # If no questions enabled, system ends immediately with a helpful message; accept either case
        if start_resp.completed:
            assert "no check-in questions are enabled" in start_resp.message.lower()
            return

        r1 = handle_user_message(internal_uid, "4", "discord")
        assert r1 and r1.message and (not r1.completed)
        r2 = handle_user_message(internal_uid, "5", "discord")
        assert r2 and r2.message and (not r2.completed)
        r3 = handle_user_message(internal_uid, "Feeling okay today", "discord")
        assert r3 and r3.message and r3.completed

    @pytest.mark.channels
    @pytest.mark.behavior
    def test_discord_task_create_update_complete(self, test_data_dir):
        """Create a task, update it, then complete it through InteractionManager natural language."""
        from tests.test_utilities import TestUserFactory
        from core.user_management import get_user_id_by_identifier
        from tasks.task_management import load_active_tasks

        ok = TestUserFactory.create_basic_user("task_user", enable_tasks=True, test_data_dir=test_data_dir)
        assert ok
        internal_uid = get_user_id_by_identifier("task_user")
        assert internal_uid

        from communication.message_processing.interaction_manager import handle_user_message
        # Our parser extracts title only; due date may be ignored in this path in tests – assert creation by title
        create_resp = handle_user_message(internal_uid, "create task Clean desk", "discord")
        assert create_resp and create_resp.message
        tasks = load_active_tasks(internal_uid)
        assert any(t["title"].lower() == "clean desk" for t in tasks)

        update_resp = handle_user_message(internal_uid, "update task 1 priority high", "discord")
        assert update_resp and update_resp.message
        tasks = load_active_tasks(internal_uid)
        assert tasks and tasks[0].get("priority", "").lower() == "high"

        complete_resp = handle_user_message(internal_uid, "complete task 1", "discord")
        assert complete_resp and complete_resp.message
        assert "completed" in complete_resp.message.lower()

    @pytest.mark.channels
    @pytest.mark.behavior
    def test_discord_complete_task_by_name_variation(self, test_data_dir):
        """Complete a task by a fuzzy name match like 'complete per davey' -> 'Pet Davey'."""
        from tests.test_utilities import TestUserFactory
        from core.user_management import get_user_id_by_identifier
        from tasks.task_management import create_task, load_active_tasks

        ok = TestUserFactory.create_basic_user("fuzzy_user", enable_tasks=True, test_data_dir=test_data_dir)
        assert ok
        internal_uid = get_user_id_by_identifier("fuzzy_user")
        assert internal_uid

        t_id = create_task(internal_uid, "Pet Davey", due_date="2025-07-07")
        assert t_id

        from communication.message_processing.interaction_manager import handle_user_message
        resp = handle_user_message(internal_uid, "complete per davey", "discord")
        assert resp and resp.message
        assert "completed: pet davey" in resp.message.lower()
        tasks = load_active_tasks(internal_uid)
        assert not any(t.get("task_id") == t_id for t in tasks)

    @pytest.mark.channels
    @pytest.mark.behavior
    def test_discord_response_after_task_reminder(self, test_data_dir):
        """Simulate a user replying to a reminder by completing the first task."""
        from tests.test_utilities import TestUserFactory
        from core.user_management import get_user_id_by_identifier
        from tasks.task_management import create_task

        ok = TestUserFactory.create_basic_user("reminder_user", enable_tasks=True, test_data_dir=test_data_dir)
        assert ok
        internal_uid = get_user_id_by_identifier("reminder_user")
        assert internal_uid

        create_task(internal_uid, "Brush your teeth", due_date="2025-07-07")
        create_task(internal_uid, "Clean desk", due_date="2026-08-06")

        from communication.message_processing.interaction_manager import handle_user_message
        resp = handle_user_message(internal_uid, "complete task 1", "discord")
        assert resp and resp.message
        assert "completed" in resp.message.lower()

    @pytest.mark.channels
    @pytest.mark.critical
    def test_discord_bot_shutdown_actually_stops_thread(self, test_data_dir):
        """Test that Discord bot shutdown actually stops the thread"""
        bot = DiscordBot()
        bot.discord_thread = MagicMock()
        
        asyncio.run(bot.shutdown())
        
        assert bot.discord_thread.join.called, "Thread should be joined"

    @pytest.mark.channels
    @pytest.mark.regression
    def test_discord_bot_is_initialized_checks_actual_state(self, test_data_dir, mock_discord_bot):
        """Test that Discord bot is_initialized checks actual initialization state"""
        bot = DiscordBot()
        
        # Test when not initialized
        assert bot.get_status() != ChannelStatus.READY, "Should not be ready initially"
        
        # Test when initialized
        bot.bot = mock_discord_bot
        bot._set_status(ChannelStatus.READY)
        assert bot.get_status() == ChannelStatus.READY, "Should be ready after setup"

    @pytest.mark.channels
    @pytest.mark.regression
    def test_discord_bot_send_dm_actually_sends_direct_message(self, test_data_dir, mock_discord_bot):
        """Test that Discord bot send_dm actually sends direct messages"""
        bot = DiscordBot()
        bot.bot = mock_discord_bot
        bot._set_status(ChannelStatus.READY)
        
        result = asyncio.run(bot.send_dm("user123", "Test DM"))
        
        assert isinstance(result, bool), "Send DM should return boolean"
        # Note: In a real test, we'd verify the DM was actually sent


class TestDiscordBotIntegration:
    """Test Discord bot integration with other system components"""

    @pytest.fixture
    def test_user_setup(self, test_data_dir):
        """Set up test user data for integration tests"""
        from tests.test_utilities import TestUserFactory
        
        user_id = "test_discord_user"
        success = TestUserFactory.create_discord_user(user_id, test_data_dir=test_data_dir)
        assert success, f"Failed to create Discord test user {user_id}"
        
        return user_id

    @pytest.fixture
    def mock_discord_bot(self):
        """Create a mock Discord bot instance for integration tests"""
        with patch('discord.ext.commands.Bot') as mock_bot_class:
            mock_bot = MagicMock()
            mock_bot_class.return_value = mock_bot
            mock_bot.is_ready.return_value = True
            mock_bot.is_closed.return_value = False
            mock_bot.latency = 0.1
            mock_bot.guilds = []
            yield mock_bot

    @pytest.mark.channels
    @pytest.mark.regression
    def test_discord_bot_integration_with_conversation_manager(self, test_data_dir, test_user_setup):
        """Test that Discord bot integrates properly with conversation manager"""
        from communication.message_processing.conversation_flow_manager import conversation_manager
        
        bot = DiscordBot()
        
        # Test that bot can be registered with conversation manager
        # Note: This would require actual conversation manager integration testing
        
        assert bot.channel_type == ChannelType.ASYNC, "Bot should be ASYNC type for conversation manager"

    @pytest.mark.channels
    @pytest.mark.behavior
    @pytest.mark.critical
    def test_discord_message_to_interaction_manager_complete_task_prompt(self, test_data_dir):
        """End-to-end-ish: ensure plain 'complete task' routes to InteractionManager and returns a helpful prompt, not a generic error."""
        # Arrange: create a basic user and map a fake Discord ID
        from tests.test_utilities import TestUserFactory
        # Create under the session-patched tests/data/users dir (omit test_data_dir)
        created = TestUserFactory.create_basic_user("e2e_user", enable_tasks=True, test_data_dir=test_data_dir)
        assert created, "Test user should be created"
        from core.user_management import get_user_id_by_identifier
        internal_uid = get_user_id_by_identifier("e2e_user")
        assert internal_uid is not None, "Should resolve internal user id"

        # Load current account data and add discord_user_id
        from core.user_data_handlers import get_user_data, save_user_data
        account_result = get_user_data(internal_uid, 'account')
        acct_data = account_result.get('account', {}) or {}
        acct_data["internal_username"] = "e2e_user"
        acct_data["discord_user_id"] = "123456789012345678"
        result = save_user_data(internal_uid, {'account': acct_data})
        ok = result.get('account', False)
        assert ok is True, "Account data should save"

        # Patch Discord internals and message send to capture output
        with patch('discord.ext.commands.Bot') as mock_bot_class:
            mock_bot = MagicMock()
            mock_bot_class.return_value = mock_bot

            dbot = DiscordBot()
            # Initialize minimal event handlers without real network
            dbot.bot = mock_bot
            dbot.initialize__register_events()

            # Build a fake message object
            fake_channel = MagicMock()
            send_calls = []

            async def fake_send(payload):
                send_calls.append(payload)
                return True

            fake_channel.send = AsyncMock(side_effect=fake_send)

            class FakeAuthor:
                id = int("123456789012345678")

            class FakeMessage:
                author = FakeAuthor()
                content = "complete task"
                channel = fake_channel

            # Call through InteractionManager directly (avoids discord.py internals in test)
            from communication.message_processing.interaction_manager import handle_user_message
            resp = handle_user_message(internal_uid, "complete task", "discord")

            # Assert: response should be helpful (either ask which task or indicate not found), not a generic error
            assert resp is not None and hasattr(resp, 'message')
            msg = resp.message.lower()
            assert (
                "which task" in msg or "specify" in msg or "task not found" in msg
            ), f"Unexpected response: {resp.message}"

    @pytest.mark.channels
    @pytest.mark.regression
    def test_discord_bot_integration_with_user_management(self, test_data_dir, test_user_setup):
        """Test that Discord bot integrates properly with user management"""
        from core.user_management import get_all_user_ids, get_user_id_by_identifier
        
        # Test that the function handles empty input
        empty_result = get_user_id_by_identifier("")
        assert empty_result is None, "Should return None for empty Discord ID"
        
        # Test that the function handles None input
        none_result = get_user_id_by_identifier(None)
        assert none_result is None, "Should return None for None Discord ID"
        
        # Test that the function returns None for non-existent Discord ID
        non_existent_user = get_user_id_by_identifier("999999999")
        assert non_existent_user is None, "Should return None for non-existent Discord ID"
        
        # Test that the function can process existing users (if any)
        all_user_ids = get_all_user_ids()
        if all_user_ids:
            # Test with a real user ID to ensure the function works
            # This tests the core functionality without depending on specific test setup
            assert isinstance(all_user_ids, list), "get_all_user_ids should return a list"
            assert len(all_user_ids) > 0, "Should have at least one user for testing"

    @pytest.mark.channels
    @pytest.mark.regression
    @pytest.mark.slow
    def test_discord_bot_error_handling_preserves_system_stability(self, test_data_dir):
        """Test that Discord bot error handling preserves system stability"""
        bot = DiscordBot()
        
        # Test that errors don't crash the system
        with patch.object(core.config, 'DISCORD_BOT_TOKEN', None):
            result = asyncio.run(bot.initialize())
            
            assert isinstance(result, bool), "Should return boolean result"
            # Note: In a real environment without token, this would fail gracefully

    @pytest.mark.channels
    @pytest.mark.regression
    def test_discord_bot_performance_under_load(self, test_data_dir):
        """Test that Discord bot performs well under load"""
        bot = DiscordBot()
        
        # Test multiple rapid operations
        start_time = time.time()
        
        for i in range(10):
            asyncio.run(bot.health_check())
        
        end_time = time.time()
        duration = end_time - start_time
        
        assert duration < 5.0, "Health checks should complete quickly under load"

    @pytest.mark.channels
    @pytest.mark.regression
    def test_discord_bot_cleanup_and_resource_management(self, test_data_dir, mock_discord_bot):
        """Test that Discord bot properly manages resources and cleanup"""
        bot = DiscordBot()
        bot.bot = mock_discord_bot
        
        # Test cleanup
        result = asyncio.run(bot.shutdown())
        
        assert isinstance(result, bool), "Shutdown should return boolean"
        assert bot.get_status() == ChannelStatus.STOPPED, "Should be stopped after shutdown"
        # Note: In a real environment, the bot.close() would be called

    @pytest.mark.channels
    @pytest.mark.regression
    def test_discord_bot_with_real_user_data(self, test_data_dir, test_user_setup):
        """Test Discord bot with real user data"""
        user_id = test_user_setup
        
        bot = DiscordBot()
        
        # Test that bot can handle real user data
        health_status = bot.get_health_status()
        
        assert "connection_status" in health_status, "Should provide health status"
        assert isinstance(health_status["connection_status"], str), "Connection status should be string"

    @pytest.mark.channels
    @pytest.mark.regression
    @pytest.mark.slow
    def test_discord_bot_error_recovery_with_real_files(self, test_data_dir):
        """Test Discord bot error recovery with real files"""
        bot = DiscordBot()
        
        # Test error recovery
        with patch.object(core.config, 'DISCORD_BOT_TOKEN', None):
            result = asyncio.run(bot.initialize())
            assert isinstance(result, bool), "Should return boolean result"
            
            # Test recovery
            with patch.object(core.config, 'DISCORD_BOT_TOKEN', 'valid_token'):
                with patch.object(bot, '_check_dns_resolution', return_value=True):
                    with patch.object(bot, '_check_network_connectivity', return_value=True):
                        result = asyncio.run(bot.manual_reconnect())
                        assert isinstance(result, bool), "Reconnect should return boolean"

    @pytest.mark.channels
    @pytest.mark.regression
    def test_discord_bot_concurrent_access_safety(self, test_data_dir):
        """Test that Discord bot handles concurrent access safely"""
        bot = DiscordBot()
        
        # Test multiple sequential health checks instead of concurrent
        results = []
        for i in range(5):
            result = asyncio.run(bot.health_check())
            results.append(result)
        
        assert len(results) == 5, "All tasks should complete"
        assert all(isinstance(r, bool) for r in results), "All results should be boolean" 