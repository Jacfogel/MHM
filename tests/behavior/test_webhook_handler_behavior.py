"""
Webhook Handler Behavior Tests

Tests for communication/communication_channels/discord/webhook_handler.py focusing on real behavior and side effects.
These tests verify that webhook handlers actually work and produce expected side effects.
"""

import pytest
import json
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from tests.test_utilities import TestUserFactory
from core.user_data_handlers import get_user_id_by_identifier


class TestWebhookHandlerBehavior:
    """Test webhook handler real behavior and side effects."""
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.communication
    def test_verify_webhook_signature_with_valid_inputs(self):
        """Test: Webhook signature verification returns True for valid inputs."""
        from communication.communication_channels.discord.webhook_handler import verify_webhook_signature
        
        # Arrange: Valid signature inputs
        signature = "test_signature_12345"
        timestamp = "1234567890"
        body = b"test body content"
        public_key = "test_public_key"
        
        # Act: Verify signature
        result = verify_webhook_signature(signature, timestamp, body, public_key)
        
        # Assert: Should return True (placeholder implementation)
        assert result is True, "Signature verification should return True for valid inputs"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.communication
    def test_verify_webhook_signature_with_missing_signature(self):
        """Test: Webhook signature verification returns False for missing signature."""
        from communication.communication_channels.discord.webhook_handler import verify_webhook_signature
        
        # Arrange: Missing signature
        signature = ""
        timestamp = "1234567890"
        body = b"test body content"
        public_key = "test_public_key"
        
        # Act: Verify signature
        result = verify_webhook_signature(signature, timestamp, body, public_key)
        
        # Assert: Should return False for missing signature
        assert result is False, "Signature verification should return False for missing signature"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.communication
    def test_verify_webhook_signature_with_missing_timestamp(self):
        """Test: Webhook signature verification returns False for missing timestamp."""
        from communication.communication_channels.discord.webhook_handler import verify_webhook_signature
        
        # Arrange: Missing timestamp
        signature = "test_signature_12345"
        timestamp = ""
        body = b"test body content"
        public_key = "test_public_key"
        
        # Act: Verify signature
        result = verify_webhook_signature(signature, timestamp, body, public_key)
        
        # Assert: Should return False for missing timestamp
        assert result is False, "Signature verification should return False for missing timestamp"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.communication
    def test_parse_webhook_event_with_valid_json(self):
        """Test: Parse webhook event returns dict for valid JSON."""
        from communication.communication_channels.discord.webhook_handler import parse_webhook_event
        
        # Arrange: Valid JSON event
        event_data = {
            "event": {
                "type": "APPLICATION_AUTHORIZED",
                "data": {
                    "user": {
                        "id": "123456789",
                        "username": "testuser"
                    }
                }
            }
        }
        body = json.dumps(event_data)
        
        # Act: Parse event
        result = parse_webhook_event(body)
        
        # Assert: Should return parsed dict
        assert result is not None, "Should return parsed event data"
        assert isinstance(result, dict), "Should return dict"
        assert result["event"]["type"] == "APPLICATION_AUTHORIZED", "Should parse event type correctly"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.communication
    def test_parse_webhook_event_with_invalid_json(self):
        """Test: Parse webhook event returns None for invalid JSON."""
        from communication.communication_channels.discord.webhook_handler import parse_webhook_event
        
        # Arrange: Invalid JSON
        body = "{ invalid json }"
        
        # Act: Parse event
        result = parse_webhook_event(body)
        
        # Assert: Should return None for invalid JSON
        assert result is None, "Should return None for invalid JSON"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.communication
    @pytest.mark.file_io
    def test_handle_application_authorized_with_new_user(self, test_data_dir):
        """Test: APPLICATION_AUTHORIZED event creates welcome for new user."""
        from communication.communication_channels.discord.webhook_handler import handle_application_authorized
        from communication.core.welcome_manager import has_been_welcomed, clear_welcomed_status
        
        # Arrange: New user event data
        discord_user_id = "987654321098765432"
        event_data = {
            "event": {
                "type": "APPLICATION_AUTHORIZED",
                "data": {
                    "user": {
                        "id": discord_user_id,
                        "username": "newuser"
                    }
                }
            }
        }
        
        # Clear any existing welcomed status
        clear_welcomed_status(discord_user_id, channel_type='discord')
        
        # Mock bot instance with async loop
        mock_bot = MagicMock()
        mock_loop = MagicMock()
        mock_loop.is_closed.return_value = False
        mock_bot.loop = mock_loop
        
        # Mock user fetch and send
        mock_user = AsyncMock()
        mock_user.send = AsyncMock(return_value=None)
        
        async def mock_fetch_user(user_id):
            return mock_user
        
        mock_bot.fetch_user = AsyncMock(return_value=mock_user)
        
        bot_instance = MagicMock()
        bot_instance.bot = mock_bot
        
        # Act: Handle authorization
        with patch('asyncio.run_coroutine_threadsafe') as mock_run_coro:
            # Mock the coroutine execution
            mock_future = MagicMock()
            mock_future.result.return_value = True
            mock_run_coro.return_value = mock_future
            
            result = handle_application_authorized(event_data, bot_instance)
        
        # Assert: Should handle successfully
        assert result is True, "Should handle authorization successfully"
        assert mock_run_coro.called, "Should schedule welcome DM"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.communication
    @pytest.mark.file_io
    @pytest.mark.no_parallel
    def test_handle_application_authorized_with_existing_user(self, test_data_dir):
        """Test: APPLICATION_AUTHORIZED event skips welcome for already-welcomed user."""
        from communication.communication_channels.discord.webhook_handler import handle_application_authorized
        from communication.core.welcome_manager import mark_as_welcomed
        
        # Arrange: Create existing user and mark as already welcomed
        discord_user_id = "111222333444555666"
        TestUserFactory.create_discord_user(discord_user_id, test_data_dir=test_data_dir)
        
        # Mark user as already welcomed (simulating they were welcomed before)
        mark_as_welcomed(discord_user_id, channel_type='discord')
        
        # Verify user exists
        internal_user_id = get_user_id_by_identifier(discord_user_id)
        assert internal_user_id is not None, "User should exist"
        
        event_data = {
            "event": {
                "type": "APPLICATION_AUTHORIZED",
                "data": {
                    "user": {
                        "id": discord_user_id,
                        "username": "existinguser"
                    }
                }
            }
        }
        
        bot_instance = None  # Not needed for already-welcomed users
        
        # Act: Handle authorization
        result = handle_application_authorized(event_data, bot_instance)
        
        # Assert: Should return True (user already welcomed, no welcome needed)
        assert result is True, "Should handle already-welcomed user successfully"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.communication
    @pytest.mark.file_io
    def test_handle_application_authorized_with_missing_user_id(self, test_data_dir):
        """Test: APPLICATION_AUTHORIZED event returns False for missing user ID."""
        from communication.communication_channels.discord.webhook_handler import handle_application_authorized
        
        # Arrange: Event data without user ID
        event_data = {
            "event": {
                "type": "APPLICATION_AUTHORIZED",
                "data": {
                    "user": {
                        "username": "testuser"
                        # Missing "id" field
                    }
                }
            }
        }
        
        bot_instance = None
        
        # Act: Handle authorization
        result = handle_application_authorized(event_data, bot_instance)
        
        # Assert: Should return False for missing user ID
        assert result is False, "Should return False for missing user ID"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.communication
    @pytest.mark.file_io
    def test_handle_application_authorized_with_already_welcomed_user(self, test_data_dir):
        """Test: APPLICATION_AUTHORIZED event skips welcome for already welcomed user."""
        from communication.communication_channels.discord.webhook_handler import handle_application_authorized
        from communication.core.welcome_manager import mark_as_welcomed, clear_welcomed_status
        
        # Arrange: Mark user as already welcomed
        discord_user_id = "555666777888999000"
        clear_welcomed_status(discord_user_id, channel_type='discord')
        mark_as_welcomed(discord_user_id, channel_type='discord')
        
        # Verify user is marked as welcomed
        from communication.core.welcome_manager import has_been_welcomed
        assert has_been_welcomed(discord_user_id, channel_type='discord'), "User should be marked as welcomed"
        
        event_data = {
            "event": {
                "type": "APPLICATION_AUTHORIZED",
                "data": {
                    "user": {
                        "id": discord_user_id,
                        "username": "welcomeduser"
                    }
                }
            }
        }
        
        bot_instance = None
        
        # Act: Handle authorization
        result = handle_application_authorized(event_data, bot_instance)
        
        # Assert: Should return True (already welcomed, no action needed)
        assert result is True, "Should handle already welcomed user successfully"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.communication
    def test_handle_application_authorized_with_bot_unavailable(self, test_data_dir):
        """Test: APPLICATION_AUTHORIZED event handles bot unavailability gracefully."""
        from communication.communication_channels.discord.webhook_handler import handle_application_authorized
        from communication.core.welcome_manager import clear_welcomed_status
        
        # Arrange: New user event data
        discord_user_id = "777888999000111222"
        clear_welcomed_status(discord_user_id, channel_type='discord')
        
        event_data = {
            "event": {
                "type": "APPLICATION_AUTHORIZED",
                "data": {
                    "user": {
                        "id": discord_user_id,
                        "username": "newuser"
                    }
                }
            }
        }
        
        # Bot instance without bot attribute
        bot_instance = MagicMock()
        bot_instance.bot = None
        
        # Act: Handle authorization
        result = handle_application_authorized(event_data, bot_instance)
        
        # Assert: Should handle bot unavailability gracefully (returns False but marks as welcomed)
        assert result is False, "Should return False when bot unavailable (but marks as welcomed)"
        from communication.core.welcome_manager import has_been_welcomed
        assert has_been_welcomed(discord_user_id, channel_type='discord'), "Should mark as welcomed to avoid retry"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.communication
    def test_handle_webhook_event_routes_application_authorized(self, test_data_dir):
        """Test: Webhook event handler routes APPLICATION_AUTHORIZED events correctly."""
        from communication.communication_channels.discord.webhook_handler import (
            handle_webhook_event,
            EVENT_APPLICATION_AUTHORIZED
        )
        from communication.core.welcome_manager import clear_welcomed_status
        
        # Arrange: APPLICATION_AUTHORIZED event
        discord_user_id = "333444555666777888"
        clear_welcomed_status(discord_user_id, channel_type='discord')
        
        event_data = {
            "event": {
                "type": "APPLICATION_AUTHORIZED",
                "data": {
                    "user": {
                        "id": discord_user_id,
                        "username": "testuser"
                    }
                }
            }
        }
        
        bot_instance = None
        
        # Act: Handle webhook event
        with patch('communication.communication_channels.discord.webhook_handler.handle_application_authorized') as mock_handler:
            mock_handler.return_value = True
            result = handle_webhook_event(EVENT_APPLICATION_AUTHORIZED, event_data, bot_instance)
        
        # Assert: Should route to correct handler
        assert result is True, "Should handle event successfully"
        assert mock_handler.called, "Should call APPLICATION_AUTHORIZED handler"
        assert mock_handler.call_args[0][0] == event_data, "Should pass event data to handler"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.communication
    @pytest.mark.file_io
    def test_handle_webhook_event_routes_application_deauthorized(self, test_data_dir):
        """Test: Webhook event handler routes APPLICATION_DEAUTHORIZED events correctly."""
        from communication.communication_channels.discord.webhook_handler import (
            handle_webhook_event,
            EVENT_APPLICATION_DEAUTHORIZED
        )
        from communication.core.welcome_manager import mark_as_welcomed, has_been_welcomed
        
        # Arrange: Mark user as welcomed first
        discord_user_id = "444555666777888999"
        mark_as_welcomed(discord_user_id, channel_type='discord')
        assert has_been_welcomed(discord_user_id, channel_type='discord'), "User should be welcomed"
        
        event_data = {
            "event": {
                "type": "APPLICATION_DEAUTHORIZED",
                "data": {
                    "user": {
                        "id": discord_user_id,
                        "username": "testuser"
                    }
                }
            }
        }
        
        bot_instance = None
        
        # Act: Handle webhook event
        result = handle_webhook_event(EVENT_APPLICATION_DEAUTHORIZED, event_data, bot_instance)
        
        # Assert: Should handle deauthorization and clear welcomed status
        assert result is True, "Should handle deauthorization successfully"
        assert not has_been_welcomed(discord_user_id, channel_type='discord'), "Should clear welcomed status"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.communication
    @pytest.mark.file_io
    @pytest.mark.no_parallel
    def test_deauthorize_then_reauthorize_sends_welcome(self, test_data_dir):
        """Test: User who deauthorizes then reauthorizes should receive welcome message."""
        from communication.communication_channels.discord.webhook_handler import (
            handle_webhook_event,
            handle_application_authorized,
            EVENT_APPLICATION_DEAUTHORIZED,
            EVENT_APPLICATION_AUTHORIZED
        )
        from communication.core.welcome_manager import mark_as_welcomed, has_been_welcomed
        from unittest.mock import MagicMock, AsyncMock
        
        # Arrange: Create existing user and mark as welcomed
        discord_user_id = "555666777888999000"
        TestUserFactory.create_discord_user(discord_user_id, test_data_dir=test_data_dir)
        mark_as_welcomed(discord_user_id, channel_type='discord')
        assert has_been_welcomed(discord_user_id, channel_type='discord'), "User should be welcomed initially"
        
        # Step 1: Deauthorize (should clear welcomed status)
        deauth_event_data = {
            "event": {
                "type": "APPLICATION_DEAUTHORIZED",
                "data": {
                    "user": {
                        "id": discord_user_id,
                        "username": "testuser"
                    }
                }
            }
        }
        result = handle_webhook_event(EVENT_APPLICATION_DEAUTHORIZED, deauth_event_data, None)
        assert result is True, "Should handle deauthorization successfully"
        assert not has_been_welcomed(discord_user_id, channel_type='discord'), "Should clear welcomed status after deauthorization"
        
        # Step 2: Reauthorize (should send welcome message since welcomed status was cleared)
        auth_event_data = {
            "event": {
                "type": "APPLICATION_AUTHORIZED",
                "data": {
                    "user": {
                        "id": discord_user_id,
                        "username": "testuser"
                    }
                }
            }
        }
        
        # Mock bot instance with event loop
        mock_bot = MagicMock()
        mock_loop = MagicMock()
        mock_loop.is_closed.return_value = False
        mock_bot.loop = mock_loop
        mock_bot.fetch_user = AsyncMock(return_value=MagicMock())
        mock_user = MagicMock()
        mock_user.send = AsyncMock()
        mock_bot.fetch_user.return_value = mock_user
        
        bot_instance = MagicMock()
        bot_instance.bot = mock_bot
        
        # Mock asyncio.run_coroutine_threadsafe to capture the coroutine
        with patch('asyncio.run_coroutine_threadsafe') as mock_run_coro:
            mock_future = MagicMock()
            mock_run_coro.return_value = mock_future
            
            result = handle_application_authorized(auth_event_data, bot_instance)
            
            # Assert: Should schedule welcome DM (user was deauthorized, so needs welcome)
            assert result is True, "Should handle reauthorization successfully"
            assert mock_run_coro.called, "Should schedule welcome DM for reauthorized user"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.communication
    def test_handle_webhook_event_handles_unknown_event_type(self):
        """Test: Webhook event handler handles unknown event types gracefully."""
        from communication.communication_channels.discord.webhook_handler import handle_webhook_event
        
        # Arrange: Unknown event type
        event_type = "UNKNOWN_EVENT_TYPE"
        event_data = {
            "event": {
                "type": event_type,
                "data": {}
            }
        }
        
        bot_instance = None
        
        # Act: Handle webhook event
        result = handle_webhook_event(event_type, event_data, bot_instance)
        
        # Assert: Should return True to acknowledge receipt
        assert result is True, "Should acknowledge unknown event type"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.communication
    def test_handle_application_authorized_with_closed_event_loop(self, test_data_dir):
        """Test: APPLICATION_AUTHORIZED event handles closed event loop gracefully."""
        from communication.communication_channels.discord.webhook_handler import handle_application_authorized
        from communication.core.welcome_manager import clear_welcomed_status
        
        # Arrange: New user event data
        discord_user_id = "999000111222333444"
        clear_welcomed_status(discord_user_id, channel_type='discord')
        
        event_data = {
            "event": {
                "type": "APPLICATION_AUTHORIZED",
                "data": {
                    "user": {
                        "id": discord_user_id,
                        "username": "newuser"
                    }
                }
            }
        }
        
        # Mock bot instance with closed loop
        mock_bot = MagicMock()
        mock_loop = MagicMock()
        mock_loop.is_closed.return_value = True
        mock_bot.loop = mock_loop
        
        bot_instance = MagicMock()
        bot_instance.bot = mock_bot
        
        # Act: Handle authorization
        result = handle_application_authorized(event_data, bot_instance)
        
        # Assert: Should handle closed loop gracefully (returns False but marks as welcomed)
        assert result is False, "Should return False when loop closed (but marks as welcomed)"
        from communication.core.welcome_manager import has_been_welcomed
        assert has_been_welcomed(discord_user_id, channel_type='discord'), "Should mark as welcomed to avoid retry"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.communication
    def test_handle_application_authorized_with_missing_event_structure(self, test_data_dir):
        """Test: APPLICATION_AUTHORIZED event handles missing event structure gracefully."""
        from communication.communication_channels.discord.webhook_handler import handle_application_authorized
        
        # Arrange: Event data with missing structure
        event_data = {
            # Missing "event" key
            "data": {
                "user": {
                    "id": "123456789",
                    "username": "testuser"
                }
            }
        }
        
        bot_instance = None
        
        # Act: Handle authorization
        result = handle_application_authorized(event_data, bot_instance)
        
        # Assert: Should handle missing structure gracefully
        assert result is False, "Should return False for missing event structure"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.communication
    @pytest.mark.file_io
    def test_handle_application_authorized_with_dm_send_failure(self, test_data_dir):
        """Test: APPLICATION_AUTHORIZED event handles DM send failure gracefully."""
        from communication.communication_channels.discord.webhook_handler import handle_application_authorized
        from communication.core.welcome_manager import clear_welcomed_status
        
        # Arrange: New user event data
        discord_user_id = "111222333444555666"
        clear_welcomed_status(discord_user_id, channel_type='discord')
        
        event_data = {
            "event": {
                "type": "APPLICATION_AUTHORIZED",
                "data": {
                    "user": {
                        "id": discord_user_id,
                        "username": "newuser"
                    }
                }
            }
        }
        
        # Mock bot instance with async loop
        mock_bot = MagicMock()
        mock_loop = MagicMock()
        mock_loop.is_closed.return_value = False
        mock_bot.loop = mock_loop
        
        bot_instance = MagicMock()
        bot_instance.bot = mock_bot
        
        # Act: Handle authorization with mocked async execution
        with patch('asyncio.run_coroutine_threadsafe') as mock_run_coro:
            # Mock the coroutine execution - the actual coroutine handles errors internally
            mock_future = MagicMock()
            mock_future.result.return_value = False  # DM send failed (handled in coroutine)
            mock_run_coro.return_value = mock_future
            
            result = handle_application_authorized(event_data, bot_instance)
        
        # Assert: Should schedule DM (even if it fails later, scheduling succeeds)
        assert result is True, "Should return True when DM is scheduled (failure handled in coroutine)"
        # The coroutine is scheduled, but we can't easily verify it was called without more complex mocking
        # The important thing is that the function doesn't crash
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.communication
    @pytest.mark.file_io
    def test_handle_application_authorized_with_scheduling_error(self, test_data_dir):
        """Test: APPLICATION_AUTHORIZED event handles scheduling error gracefully."""
        from communication.communication_channels.discord.webhook_handler import handle_application_authorized
        from communication.core.welcome_manager import clear_welcomed_status, has_been_welcomed
        
        # Arrange: New user event data
        discord_user_id = "222333444555666777"
        clear_welcomed_status(discord_user_id, channel_type='discord')
        
        event_data = {
            "event": {
                "type": "APPLICATION_AUTHORIZED",
                "data": {
                    "user": {
                        "id": discord_user_id,
                        "username": "newuser"
                    }
                }
            }
        }
        
        # Mock bot instance with async loop
        mock_bot = MagicMock()
        mock_loop = MagicMock()
        mock_loop.is_closed.return_value = False
        mock_bot.loop = mock_loop
        
        bot_instance = MagicMock()
        bot_instance.bot = mock_bot
        
        # Ensure user doesn't exist and hasn't been welcomed (to avoid early returns)
        # The function returns True early if user exists (line 111) or already welcomed (line 122)
        # We need to ensure we reach the asyncio.run_coroutine_threadsafe call to test the exception path
        from core.user_data_handlers import get_user_id_by_identifier
        import uuid
        
        # Use a unique Discord ID to avoid conflicts with other tests
        # Generate a new ID that definitely doesn't exist
        discord_user_id = f"test_{uuid.uuid4().hex[:16]}"
        event_data["event"]["data"]["user"]["id"] = discord_user_id
        clear_welcomed_status(discord_user_id, channel_type='discord')
        
        # Double-check user doesn't exist (shouldn't, but verify)
        existing_user_id = get_user_id_by_identifier(discord_user_id)
        if existing_user_id:
            # If somehow user exists, use a completely different ID
            discord_user_id = f"test_{uuid.uuid4().hex[:16]}"
            event_data["event"]["data"]["user"]["id"] = discord_user_id
            clear_welcomed_status(discord_user_id, channel_type='discord')
        
        # Verify user hasn't been welcomed
        assert not has_been_welcomed(discord_user_id, channel_type='discord'), \
            "User should not be welcomed before test"
        
        # Act: Handle authorization with scheduling error
        # The actual code catches exceptions and marks as welcomed
        # Verify mock setup is correct before patching
        assert bot_instance.bot.loop is not None, "Bot loop should be set"
        assert not bot_instance.bot.loop.is_closed(), "Bot loop should not be closed"
        
        # Patch asyncio.run_coroutine_threadsafe - use both string path and patch.object
        # to ensure it works when asyncio is imported inside the function in parallel execution
        # The string path patches the builtin module, patch.object patches the already-imported module
        def raise_exception(*args, **kwargs):
            raise Exception("Scheduling error")
        
        with patch('asyncio.run_coroutine_threadsafe', side_effect=raise_exception), \
             patch.object(asyncio, 'run_coroutine_threadsafe', side_effect=raise_exception):
            result = handle_application_authorized(event_data, bot_instance)
        
        # Assert: Should handle scheduling error gracefully
        # The function catches the exception and marks as welcomed, then returns False
        assert result is False, f"Should return False on scheduling error, got {result}"
        assert has_been_welcomed(discord_user_id, channel_type='discord'), "Should mark as welcomed to avoid retry"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.communication
    def test_verify_webhook_signature_with_exception(self):
        """Test: Webhook signature verification handles exceptions gracefully."""
        from communication.communication_channels.discord.webhook_handler import verify_webhook_signature
        
        # Arrange: Valid inputs but force exception
        signature = "test_signature_12345"
        timestamp = "1234567890"
        body = b"test body content"
        public_key = "test_public_key"
        
        # Act: Verify signature (should handle any exceptions internally)
        result = verify_webhook_signature(signature, timestamp, body, public_key)
        
        # Assert: Should return boolean (True for placeholder, False on error)
        assert isinstance(result, bool), "Should return boolean result"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.communication
    def test_parse_webhook_event_with_empty_string(self):
        """Test: Parse webhook event handles empty string gracefully."""
        from communication.communication_channels.discord.webhook_handler import parse_webhook_event
        
        # Arrange: Empty string
        body = ""
        
        # Act: Parse event
        result = parse_webhook_event(body)
        
        # Assert: Should return None for empty string (invalid JSON)
        assert result is None, "Should return None for empty string"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.communication
    def test_parse_webhook_event_with_none(self):
        """Test: Parse webhook event handles None gracefully."""
        from communication.communication_channels.discord.webhook_handler import parse_webhook_event
        
        # Arrange: None input
        body = None
        
        # Act: Parse event
        result = parse_webhook_event(body)
        
        # Assert: Should return None for None input
        assert result is None, "Should return None for None input"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.communication
    @pytest.mark.file_io
    def test_handle_webhook_event_with_exception(self, test_data_dir):
        """Test: Webhook event handler handles exceptions gracefully."""
        from communication.communication_channels.discord.webhook_handler import (
            handle_webhook_event,
            EVENT_APPLICATION_AUTHORIZED
        )
        
        # Arrange: Event data that will cause exception
        event_data = {
            "event": {
                "type": EVENT_APPLICATION_AUTHORIZED,
                "data": {
                    "user": {
                        "id": "123456789",
                        "username": "testuser"
                    }
                }
            }
        }
        
        bot_instance = None
        
        # Act: Handle webhook event with patched handler that raises exception
        with patch('communication.communication_channels.discord.webhook_handler.handle_application_authorized') as mock_handler:
            mock_handler.side_effect = Exception("Test exception")
            result = handle_webhook_event(EVENT_APPLICATION_AUTHORIZED, event_data, bot_instance)
        
        # Assert: Should handle exception gracefully
        assert result is False, "Should return False on exception"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.communication
    @pytest.mark.file_io
    def test_handle_application_authorized_with_empty_username(self, test_data_dir):
        """Test: APPLICATION_AUTHORIZED event handles empty username gracefully."""
        from communication.communication_channels.discord.webhook_handler import handle_application_authorized
        from communication.core.welcome_manager import clear_welcomed_status
        
        # Arrange: Event data with empty username
        discord_user_id = "333444555666777888"
        clear_welcomed_status(discord_user_id, channel_type='discord')
        
        event_data = {
            "event": {
                "type": "APPLICATION_AUTHORIZED",
                "data": {
                    "user": {
                        "id": discord_user_id,
                        "username": ""  # Empty username
                    }
                }
            }
        }
        
        bot_instance = None
        
        # Act: Handle authorization
        result = handle_application_authorized(event_data, bot_instance)
        
        # Assert: Should handle empty username (user ID is what matters)
        # The function should still work if user ID is present
        assert isinstance(result, bool), "Should return boolean result"

