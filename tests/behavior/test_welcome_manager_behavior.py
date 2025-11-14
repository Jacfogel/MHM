"""
Welcome Manager Behavior Tests

Tests for communication/core/welcome_manager.py focusing on real behavior and side effects.
These tests verify that welcome manager actually works and produces expected side effects.
"""

import pytest
import json
import os
from pathlib import Path
from unittest.mock import patch
from communication.core.welcome_manager import (
    has_been_welcomed,
    mark_as_welcomed,
    clear_welcomed_status,
    get_welcome_message,
    WELCOME_TRACKING_FILE
)


class TestWelcomeManagerBehavior:
    """Test welcome manager real behavior and side effects."""
    
    @pytest.fixture(autouse=True)
    def setup_welcome_tracking(self, test_data_dir):
        """Set up welcome tracking file for tests."""
        # Patch BASE_DATA_DIR to use test directory
        with patch('communication.core.welcome_manager.BASE_DATA_DIR', test_data_dir):
            # Ensure tracking file doesn't exist at start
            tracking_file = Path(test_data_dir) / "welcome_tracking.json"
            if tracking_file.exists():
                try:
                    tracking_file.unlink()
                except (PermissionError, OSError):
                    # File might be locked by another test in parallel execution
                    # This is OK - the test will work with existing file
                    pass
            
            yield
            
            # Cleanup: remove tracking file after test
            if tracking_file.exists():
                try:
                    tracking_file.unlink()
                except (PermissionError, OSError):
                    # File might be locked by another test in parallel execution
                    # This is OK - cleanup will happen later
                    pass
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.file_io
    def test_has_been_welcomed_returns_false_for_new_user(self, test_data_dir):
        """Test: has_been_welcomed returns False for new user."""
        with patch('communication.core.welcome_manager.BASE_DATA_DIR', test_data_dir):
            result = has_been_welcomed('new_user_123', channel_type='discord')
            
            # Assert: Should return False for new user
            assert result is False, "Should return False for new user"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.file_io
    def test_mark_as_welcomed_creates_tracking_file(self, test_data_dir):
        """Test: mark_as_welcomed creates tracking file and saves data."""
        with patch('communication.core.welcome_manager.BASE_DATA_DIR', test_data_dir):
            channel_identifier = 'test_user_456'
            result = mark_as_welcomed(channel_identifier, channel_type='discord')
            
            # Assert: Should save successfully
            assert result is True, "Should mark as welcomed successfully"
            
            # Verify file was created
            tracking_file = Path(test_data_dir) / "welcome_tracking.json"
            assert tracking_file.exists(), "Tracking file should be created"
            
            # Verify data was saved
            with open(tracking_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            key = "discord:test_user_456"
            assert key in data, "User should be in tracking data"
            assert data[key]['welcomed'] is True, "Should be marked as welcomed"
            assert 'welcomed_at' in data[key], "Should have timestamp"
            assert data[key]['channel_type'] == 'discord', "Should have channel type"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.file_io
    def test_has_been_welcomed_returns_true_after_marking(self, test_data_dir):
        """Test: has_been_welcomed returns True after marking user as welcomed."""
        with patch('communication.core.welcome_manager.BASE_DATA_DIR', test_data_dir):
            channel_identifier = 'test_user_789'
            
            # Mark as welcomed
            mark_as_welcomed(channel_identifier, channel_type='discord')
            
            # Check if welcomed
            result = has_been_welcomed(channel_identifier, channel_type='discord')
            
            # Assert: Should return True
            assert result is True, "Should return True after marking as welcomed"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.file_io
    def test_clear_welcomed_status_removes_user_from_tracking(self, test_data_dir):
        """Test: clear_welcomed_status removes user from tracking file."""
        with patch('communication.core.welcome_manager.BASE_DATA_DIR', test_data_dir):
            channel_identifier = 'test_user_clear'
            
            # Mark as welcomed first
            mark_as_welcomed(channel_identifier, channel_type='discord')
            assert has_been_welcomed(channel_identifier, channel_type='discord'), "Should be welcomed"
            
            # Clear welcomed status
            result = clear_welcomed_status(channel_identifier, channel_type='discord')
            
            # Assert: Should clear successfully
            assert result is True, "Should clear welcomed status successfully"
            assert not has_been_welcomed(channel_identifier, channel_type='discord'), "Should no longer be welcomed"
            
            # Verify file still exists but user is removed
            tracking_file = Path(test_data_dir) / "welcome_tracking.json"
            if tracking_file.exists():
                with open(tracking_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                key = "discord:test_user_clear"
                assert key not in data, "User should be removed from tracking"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.file_io
    def test_clear_welcomed_status_handles_nonexistent_user(self, test_data_dir):
        """Test: clear_welcomed_status handles nonexistent user gracefully."""
        with patch('communication.core.welcome_manager.BASE_DATA_DIR', test_data_dir):
            channel_identifier = 'nonexistent_user'
            
            # Clear welcomed status for user that doesn't exist
            result = clear_welcomed_status(channel_identifier, channel_type='discord')
            
            # Assert: Should return True (success, user already not in list)
            assert result is True, "Should return True for nonexistent user"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.file_io
    def test_welcome_tracking_supports_multiple_channels(self, test_data_dir):
        """Test: Welcome tracking supports multiple channel types."""
        with patch('communication.core.welcome_manager.BASE_DATA_DIR', test_data_dir):
            # Use unique channel identifier to avoid conflicts with other tests
            import uuid
            channel_identifier = f'test_multi_channel_{uuid.uuid4().hex[:8]}'
            
            # Mark as welcomed for Discord
            mark_as_welcomed(channel_identifier, channel_type='discord')
            
            # Mark as welcomed for Email
            mark_as_welcomed(channel_identifier, channel_type='email')
            
            # Assert: Both should be tracked separately (with retry for race conditions)
            import time
            from tests.test_utilities import retry_with_backoff
            
            def _check_discord_welcomed():
                return has_been_welcomed(channel_identifier, channel_type='discord')
            
            def _check_email_welcomed():
                return has_been_welcomed(channel_identifier, channel_type='email')
            
            assert retry_with_backoff(_check_discord_welcomed, max_retries=3, initial_delay=0.1), "Discord should be welcomed"
            assert retry_with_backoff(_check_email_welcomed, max_retries=3, initial_delay=0.1), "Email should be welcomed"
            
            # Clear one, other should remain
            clear_welcomed_status(channel_identifier, channel_type='discord')
            
            # Verify Discord is cleared
            def _check_discord_cleared():
                return not has_been_welcomed(channel_identifier, channel_type='discord')
            
            assert retry_with_backoff(_check_discord_cleared, max_retries=3, initial_delay=0.1), "Discord should be cleared"
            
            # Verify Email is still welcomed
            assert retry_with_backoff(_check_email_welcomed, max_retries=3, initial_delay=0.1), "Email should still be welcomed"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.file_io
    def test_welcome_tracking_supports_multiple_users(self, test_data_dir):
        """Test: Welcome tracking supports multiple users."""
        with patch('communication.core.welcome_manager.BASE_DATA_DIR', test_data_dir):
            user1 = 'user_1'
            user2 = 'user_2'
            
            # Mark both as welcomed
            mark_as_welcomed(user1, channel_type='discord')
            mark_as_welcomed(user2, channel_type='discord')
            
            # Assert: Both should be tracked
            assert has_been_welcomed(user1, channel_type='discord'), "User 1 should be welcomed"
            assert has_been_welcomed(user2, channel_type='discord'), "User 2 should be welcomed"
            
            # Clear one, other should remain
            clear_welcomed_status(user1, channel_type='discord')
            assert not has_been_welcomed(user1, channel_type='discord'), "User 1 should be cleared"
            assert has_been_welcomed(user2, channel_type='discord'), "User 2 should still be welcomed"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    def test_get_welcome_message_returns_authorization_message(self):
        """Test: get_welcome_message returns authorization message when is_authorization=True."""
        message = get_welcome_message(
            'test_user',
            channel_type='discord',
            username='TestUser',
            is_authorization=True
        )
        
        # Assert: Should return authorization message
        assert isinstance(message, str), "Should return string"
        assert len(message) > 0, "Should return non-empty message"
        assert 'Welcome to MHM' in message, "Should contain welcome text"
        assert 'connecting MHM' in message or 'connected MHM' in message, "Should mention connection"
        assert '/help' in message, "Should mention help command"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    def test_get_welcome_message_returns_general_message(self):
        """Test: get_welcome_message returns general message when is_authorization=False."""
        message = get_welcome_message(
            'test_user',
            channel_type='discord',
            username='TestUser',
            is_authorization=False
        )
        
        # Assert: Should return general message
        assert isinstance(message, str), "Should return string"
        assert len(message) > 0, "Should return non-empty message"
        assert 'Welcome to MHM' in message, "Should contain welcome text"
        assert '/help' in message, "Should mention help command"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    def test_get_welcome_message_different_for_authorization(self):
        """Test: get_welcome_message returns different messages for authorization vs general."""
        auth_message = get_welcome_message(
            'test_user',
            channel_type='discord',
            is_authorization=True
        )
        
        general_message = get_welcome_message(
            'test_user',
            channel_type='discord',
            is_authorization=False
        )
        
        # Assert: Messages should be different
        assert auth_message != general_message, "Messages should be different"
        assert 'connecting' in auth_message.lower() or 'connected' in auth_message.lower(), "Auth message should mention connection"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.file_io
    def test_mark_as_welcomed_persists_across_calls(self, test_data_dir):
        """Test: mark_as_welcomed persists data across multiple calls."""
        with patch('communication.core.welcome_manager.BASE_DATA_DIR', test_data_dir):
            channel_identifier = 'persistent_user'
            
            # Mark as welcomed
            mark_as_welcomed(channel_identifier, channel_type='discord')
            
            # Verify persisted
            assert has_been_welcomed(channel_identifier, channel_type='discord'), "Should be welcomed"
            
            # Mark again (should update timestamp)
            mark_as_welcomed(channel_identifier, channel_type='discord')
            
            # Should still be welcomed
            assert has_been_welcomed(channel_identifier, channel_type='discord'), "Should still be welcomed after second mark"
            
            # Verify file has updated data
            tracking_file = Path(test_data_dir) / "welcome_tracking.json"
            with open(tracking_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            key = "discord:persistent_user"
            assert key in data, "User should still be in tracking"
            assert data[key]['welcomed'] is True, "Should still be marked as welcomed"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.file_io
    def test_welcome_tracking_handles_missing_file_gracefully(self, test_data_dir):
        """Test: Welcome tracking handles missing file gracefully."""
        with patch('communication.core.welcome_manager.BASE_DATA_DIR', test_data_dir):
            tracking_file = Path(test_data_dir) / "welcome_tracking.json"
            
            # Ensure file doesn't exist (handle file locking in parallel execution)
            if tracking_file.exists():
                try:
                    tracking_file.unlink()
                except (PermissionError, OSError):
                    # File might be locked by another test - that's OK for this test
                    pass
            
            # Should return False for nonexistent file
            result = has_been_welcomed('any_user', channel_type='discord')
            assert result is False, "Should return False when file doesn't exist"
            
            # Should be able to mark as welcomed (creates file)
            mark_result = mark_as_welcomed('any_user', channel_type='discord')
            assert mark_result is True, "Should create file and mark as welcomed"
            assert tracking_file.exists(), "File should be created"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.file_io
    def test_welcome_tracking_handles_corrupted_file_gracefully(self, test_data_dir):
        """Test: Welcome tracking handles corrupted file gracefully."""
        with patch('communication.core.welcome_manager.BASE_DATA_DIR', test_data_dir):
            tracking_file = Path(test_data_dir) / "welcome_tracking.json"
            
            # Create corrupted file
            tracking_file.parent.mkdir(parents=True, exist_ok=True)
            with open(tracking_file, 'w', encoding='utf-8') as f:
                f.write('{ invalid json }')
            
            # Should handle gracefully
            result = has_been_welcomed('test_user', channel_type='discord')
            # Should return False (default for corrupted file)
            assert result is False, "Should return False for corrupted file"
            
            # Should be able to recover by marking as welcomed
            mark_result = mark_as_welcomed('test_user', channel_type='discord')
            assert mark_result is True, "Should recover and save successfully"
            
            # Verify file is now valid
            with open(tracking_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            assert isinstance(data, dict), "File should be valid JSON"

