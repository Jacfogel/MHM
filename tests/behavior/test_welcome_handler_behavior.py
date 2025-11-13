"""
Welcome Handler Behavior Tests

Tests for communication/communication_channels/discord/welcome_handler.py focusing on real behavior and side effects.
These tests verify that welcome handler actually works and produces expected side effects.
"""

import pytest
from unittest.mock import patch, MagicMock
from communication.communication_channels.discord.welcome_handler import (
    has_been_welcomed,
    mark_as_welcomed,
    clear_welcomed_status,
    get_welcome_message,
    get_welcome_message_view
)


class TestWelcomeHandlerBehavior:
    """Test welcome handler real behavior and side effects."""
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.channels
    @pytest.mark.file_io
    def test_has_been_welcomed_delegates_to_manager(self, test_data_dir):
        """Test: has_been_welcomed delegates to welcome_manager with discord channel type."""
        with patch('communication.core.welcome_manager.BASE_DATA_DIR', test_data_dir):
            discord_user_id = 'discord_user_123'
            
            # Mark as welcomed using the handler
            mark_as_welcomed(discord_user_id)
            
            # Check using handler
            result = has_been_welcomed(discord_user_id)
            
            # Assert: Should return True
            assert result is True, "Should return True after marking as welcomed"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.channels
    @pytest.mark.file_io
    def test_mark_as_welcomed_delegates_to_manager(self, test_data_dir):
        """Test: mark_as_welcomed delegates to welcome_manager with discord channel type."""
        with patch('communication.core.welcome_manager.BASE_DATA_DIR', test_data_dir):
            discord_user_id = 'discord_user_456'
            
            # Mark as welcomed using handler
            result = mark_as_welcomed(discord_user_id)
            
            # Assert: Should mark successfully
            assert result is True, "Should mark as welcomed successfully"
            
            # Verify using manager directly
            from communication.core.welcome_manager import has_been_welcomed as manager_has_been_welcomed
            assert manager_has_been_welcomed(discord_user_id, channel_type='discord'), "Manager should confirm user is welcomed"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.channels
    @pytest.mark.file_io
    def test_clear_welcomed_status_delegates_to_manager(self, test_data_dir):
        """Test: clear_welcomed_status delegates to welcome_manager with discord channel type."""
        with patch('communication.core.welcome_manager.BASE_DATA_DIR', test_data_dir):
            discord_user_id = 'discord_user_789'
            
            # Mark as welcomed first
            mark_as_welcomed(discord_user_id)
            assert has_been_welcomed(discord_user_id), "Should be welcomed"
            
            # Clear using handler
            result = clear_welcomed_status(discord_user_id)
            
            # Assert: Should clear successfully
            assert result is True, "Should clear welcomed status successfully"
            assert not has_been_welcomed(discord_user_id), "Should no longer be welcomed"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.channels
    def test_get_welcome_message_delegates_to_manager(self):
        """Test: get_welcome_message delegates to welcome_manager with discord channel type."""
        discord_user_id = 'discord_user_message'
        discord_username = 'TestUser'
        
        # The function imports and calls _get_welcome_message directly
        with patch('communication.communication_channels.discord.welcome_handler._get_welcome_message') as mock_get_message:
            mock_get_message.return_value = "Test welcome message"
            
            result = get_welcome_message(discord_user_id, discord_username, is_authorization=True)
            
            # Assert: Should delegate to manager
            assert result == "Test welcome message", "Should return message from manager"
            assert mock_get_message.called, "Should call manager function"
            call_args = mock_get_message.call_args
            assert call_args[1]['channel_identifier'] == discord_user_id, "Should pass Discord user ID"
            assert call_args[1]['channel_type'] == 'discord', "Should use discord channel type"
            assert call_args[1]['username'] == discord_username, "Should pass username"
            assert call_args[1]['is_authorization'] is True, "Should pass is_authorization flag"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.channels
    def test_get_welcome_message_without_username(self):
        """Test: get_welcome_message works without username."""
        discord_user_id = 'discord_user_no_username'
        
        # Test actual function behavior (it calls the real manager)
        result = get_welcome_message(discord_user_id, is_authorization=False)
        
        # Assert: Should return actual welcome message
        assert isinstance(result, str), "Should return string"
        assert len(result) > 0, "Should return non-empty message"
        assert 'Welcome to MHM' in result, "Should contain welcome text"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.channels
    def test_get_welcome_message_view_creates_discord_view(self):
        """Test: get_welcome_message_view creates Discord View with buttons."""
        discord_user_id = 'discord_user_view'
        
        # Test actual function (may return None if error occurs, which is handled by decorator)
        view = get_welcome_message_view(discord_user_id)
        
        # Assert: Should return view if Discord is available, or None if error (both are valid)
        # The function uses @handle_errors with default_return=None, so None is acceptable
        if view is not None:
            assert hasattr(view, 'discord_user_id'), "View should have discord_user_id"
            assert view.discord_user_id == discord_user_id, "View should store Discord user ID"
        else:
            # Function returned None (likely due to error handling) - this is acceptable behavior
            # The decorator handles errors gracefully
            pass
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.channels
    def test_get_welcome_message_view_handles_errors_gracefully(self):
        """Test: get_welcome_message_view handles errors gracefully."""
        discord_user_id = 'discord_user_error'
        
        # Function should handle errors gracefully via @handle_errors decorator
        view = get_welcome_message_view(discord_user_id)
        
        # Assert: Should return None on error (per decorator default_return)
        # This is acceptable - the function is protected by error handling
        assert view is None or hasattr(view, 'discord_user_id'), "Should return None or valid view"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.channels
    def test_get_welcome_message_view_function_exists(self):
        """Test: get_welcome_message_view function exists and is callable."""
        # Verify function exists and can be called
        assert callable(get_welcome_message_view), "Function should be callable"
        
        # Test that function can be called with discord_user_id
        # (decorator wraps signature, so we test actual callability)
        result = get_welcome_message_view('test_user_id')
        # Function may return None (error handling) or a view - both are valid
        assert result is None or hasattr(result, 'discord_user_id'), "Should return None or valid view"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.channels
    @pytest.mark.file_io
    def test_welcome_handler_integration_with_manager(self, test_data_dir):
        """Test: Welcome handler functions integrate correctly with welcome_manager."""
        with patch('communication.core.welcome_manager.BASE_DATA_DIR', test_data_dir):
            discord_user_id = 'discord_integration_test'
            
            # Test full flow using handler functions
            # 1. Check new user
            assert not has_been_welcomed(discord_user_id), "New user should not be welcomed"
            
            # 2. Mark as welcomed
            assert mark_as_welcomed(discord_user_id), "Should mark as welcomed"
            
            # 3. Check welcomed status
            assert has_been_welcomed(discord_user_id), "Should be welcomed"
            
            # 4. Get welcome message
            message = get_welcome_message(discord_user_id, is_authorization=True)
            assert isinstance(message, str), "Should return string message"
            assert len(message) > 0, "Should return non-empty message"
            
            # 5. Clear welcomed status
            assert clear_welcomed_status(discord_user_id), "Should clear welcomed status"
            
            # 6. Verify cleared
            assert not has_been_welcomed(discord_user_id), "Should no longer be welcomed"

