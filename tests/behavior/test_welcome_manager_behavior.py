"""
Welcome Manager Behavior Tests

Tests for communication/core/welcome_manager.py focusing on real behavior and side effects.
These tests verify that welcome manager actually works and produces expected side effects.
"""

import pytest
import json
import uuid
import contextlib
from unittest.mock import patch
from communication.core.welcome_manager import (
    has_been_welcomed,
    mark_as_welcomed,
    clear_welcomed_status,
    get_welcome_message,
    welcome_tracking_json_path,
)


class TestWelcomeManagerBehavior:
    """Test welcome manager real behavior and side effects."""
    
    @pytest.fixture(autouse=True)
    def setup_welcome_tracking(self, tmp_path):
        """Isolate welcome tracking under pytest tmp_path so parallel workers cannot share one JSON file."""
        isolated = tmp_path / f"welcome_{uuid.uuid4().hex[:8]}"
        isolated.mkdir()
        with patch(
            "communication.core.welcome_manager.BASE_DATA_DIR",
            str(isolated.resolve()),
        ):
            yield
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.file_io
    def test_has_been_welcomed_returns_false_for_new_user(self):
        """Test: has_been_welcomed returns False for new user."""
        result = has_been_welcomed('new_user_123', channel_type='discord')

        # Assert: Should return False for new user
        assert result is False, "Should return False for new user"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.file_io
    def test_mark_as_welcomed_creates_tracking_file(self):
        """Test: mark_as_welcomed creates tracking file and saves data."""
        channel_identifier = 'test_user_456'
        result = mark_as_welcomed(channel_identifier, channel_type='discord')

        # Assert: Should save successfully
        assert result is True, "Should mark as welcomed successfully"

        tracking_file = welcome_tracking_json_path()
        assert tracking_file.exists(), "Tracking file should be created"

        with open(tracking_file, encoding='utf-8') as f:
            data = json.load(f)

        key = "discord:test_user_456"
        assert key in data, "User should be in tracking data"
        assert data[key]['welcomed'] is True, "Should be marked as welcomed"
        assert 'welcomed_at' in data[key], "Should have timestamp"
        assert data[key]['channel_type'] == 'discord', "Should have channel type"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.file_io
    def test_has_been_welcomed_returns_true_after_marking(self):
        """Test: has_been_welcomed returns True after marking user as welcomed."""
        channel_identifier = 'test_user_789'

        mark_as_welcomed(channel_identifier, channel_type='discord')

        result = has_been_welcomed(channel_identifier, channel_type='discord')

        assert result is True, "Should return True after marking as welcomed"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.file_io
    def test_clear_welcomed_status_removes_user_from_tracking(self):
        """Test: clear_welcomed_status removes user from tracking file."""
        channel_identifier = 'test_user_clear'

        mark_as_welcomed(channel_identifier, channel_type='discord')
        assert has_been_welcomed(channel_identifier, channel_type='discord'), "Should be welcomed"

        result = clear_welcomed_status(channel_identifier, channel_type='discord')

        assert result is True, "Should clear welcomed status successfully"
        assert not has_been_welcomed(channel_identifier, channel_type='discord'), "Should no longer be welcomed"

        tracking_file = welcome_tracking_json_path()
        if tracking_file.exists():
            with open(tracking_file, encoding='utf-8') as f:
                data = json.load(f)
            key = "discord:test_user_clear"
            assert key not in data, "User should be removed from tracking"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.file_io
    def test_clear_welcomed_status_handles_nonexistent_user(self):
        """Test: clear_welcomed_status handles nonexistent user gracefully."""
        channel_identifier = 'nonexistent_user'

        result = clear_welcomed_status(channel_identifier, channel_type='discord')

        assert result is True, "Should return True for nonexistent user"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.file_io
    def test_welcome_tracking_supports_multiple_channels(self):
        """Test: Welcome tracking supports multiple channel types."""
        channel_identifier = f'test_multi_channel_{uuid.uuid4().hex[:8]}'

        mark_as_welcomed(channel_identifier, channel_type='discord')

        mark_as_welcomed(channel_identifier, channel_type='email')

        assert has_been_welcomed(channel_identifier, channel_type='discord'), "Discord should be welcomed"
        assert has_been_welcomed(channel_identifier, channel_type='email'), "Email should be welcomed"

        clear_welcomed_status(channel_identifier, channel_type='discord')

        assert not has_been_welcomed(channel_identifier, channel_type='discord'), "Discord should be cleared"
        assert has_been_welcomed(channel_identifier, channel_type='email'), "Email should still be welcomed"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.file_io
    def test_welcome_tracking_supports_multiple_users(self):
        """Test: Welcome tracking supports multiple users."""
        user1 = f'user_1_{uuid.uuid4().hex[:8]}'
        user2 = f'user_2_{uuid.uuid4().hex[:8]}'

        mark_as_welcomed(user1, channel_type='discord')
        mark_as_welcomed(user2, channel_type='discord')

        assert has_been_welcomed(user1, channel_type='discord'), "User 1 should be welcomed"
        assert has_been_welcomed(user2, channel_type='discord'), "User 2 should be welcomed"

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
    def test_mark_as_welcomed_persists_across_calls(self):
        """Test: mark_as_welcomed persists data across multiple calls."""
        channel_identifier = f'persistent_user_{uuid.uuid4().hex[:8]}'

        mark_as_welcomed(channel_identifier, channel_type='discord')

        assert has_been_welcomed(channel_identifier, channel_type='discord'), "Should be welcomed"

        mark_as_welcomed(channel_identifier, channel_type='discord')

        assert has_been_welcomed(channel_identifier, channel_type='discord'), "Should still be welcomed after second mark"

        tracking_file = welcome_tracking_json_path()
        with open(tracking_file, encoding='utf-8') as f:
            data = json.load(f)
        key = f"discord:{channel_identifier}"
        assert key in data, "User should still be in tracking"
        assert data[key]['welcomed'] is True, "Should still be marked as welcomed"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.file_io
    def test_welcome_tracking_handles_missing_file_gracefully(self):
        """Test: Welcome tracking handles missing file gracefully."""
        tracking_file = welcome_tracking_json_path()

        if tracking_file.exists():
            with contextlib.suppress(PermissionError, OSError):
                tracking_file.unlink()

        result = has_been_welcomed('any_user', channel_type='discord')
        assert result is False, "Should return False when file doesn't exist"

        mark_result = mark_as_welcomed('any_user', channel_type='discord')
        assert mark_result is True, "Should create file and mark as welcomed"
        assert tracking_file.exists(), "File should be created"
    
    @pytest.mark.behavior
    @pytest.mark.communication
    @pytest.mark.file_io
    def test_welcome_tracking_handles_corrupted_file_gracefully(self):
        """Test: Welcome tracking handles corrupted file gracefully."""
        tracking_file = welcome_tracking_json_path()

        tracking_file.parent.mkdir(parents=True, exist_ok=True)
        with open(tracking_file, 'w', encoding='utf-8') as f:
            f.write('{ invalid json }')

        result = has_been_welcomed('test_user', channel_type='discord')
        assert result is False, "Should return False for corrupted file"

        mark_result = mark_as_welcomed('test_user', channel_type='discord')
        assert mark_result is True, "Should recover and save successfully"

        with open(tracking_file, encoding='utf-8') as f:
            data = json.load(f)
        assert isinstance(data, dict), "File should be valid JSON"
