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
from core.user_management import get_user_id_by_identifier


class TestWebhookHandlerBehavior:
    """Test webhook handler real behavior and side effects."""
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.channels
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
    @pytest.mark.channels
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
    @pytest.mark.channels
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
    @pytest.mark.channels
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
    @pytest.mark.channels
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
    @pytest.mark.channels
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
    @pytest.mark.channels
    @pytest.mark.file_io
    def test_handle_application_authorized_with_existing_user(self, test_data_dir):
        """Test: APPLICATION_AUTHORIZED event skips welcome for existing user."""
        from communication.communication_channels.discord.webhook_handler import handle_application_authorized
        
        # Arrange: Create existing user
        discord_user_id = "111222333444555666"
        TestUserFactory.create_discord_user(discord_user_id, test_data_dir=test_data_dir)
        
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
        
        bot_instance = None  # Not needed for existing users
        
        # Act: Handle authorization
        result = handle_application_authorized(event_data, bot_instance)
        
        # Assert: Should return True (user already exists, no welcome needed)
        assert result is True, "Should handle existing user successfully"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.channels
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
    @pytest.mark.channels
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
    @pytest.mark.channels
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
    @pytest.mark.channels
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
    @pytest.mark.channels
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
    @pytest.mark.channels
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
    @pytest.mark.channels
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
    @pytest.mark.channels
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

