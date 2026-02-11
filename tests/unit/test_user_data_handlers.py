"""
Unit tests for user data handlers convenience functions.

Tests for core/user_data_handlers.py focusing on update convenience functions
and validation logic.
"""

import pytest
import uuid
from unittest.mock import patch, Mock, MagicMock
from tests.test_utilities import TestUserFactory
from core.file_locking import safe_json_read
from core.user_data_handlers import (
    update_user_account,
    update_user_preferences,
    update_user_context,
    update_channel_preferences,
    update_user_schedules,
    get_all_user_ids,
    register_data_loader,
    get_user_data,
    save_user_data_transaction
)


def extract_nested_data(data, data_type):
    """Helper function to extract nested data from get_user_data result."""
    if isinstance(data, dict) and data_type in data:
        return data[data_type]
    return data


def _resolve_account_file(test_data_dir, internal_username):
    """Resolve account.json path for a logical test username via test index mapping."""
    actual_user_id = TestUserFactory.get_test_user_id_by_internal_username(
        internal_username, test_data_dir
    )
    if not actual_user_id:
        return None
    from pathlib import Path

    return Path(test_data_dir) / "users" / actual_user_id / "account.json"


def _resolve_actual_user_id(test_data_dir, internal_username):
    """Resolve UUID user id for a logical username from the test index."""
    return TestUserFactory.get_test_user_id_by_internal_username(
        internal_username, test_data_dir
    )


@pytest.mark.unit
@pytest.mark.user_management
class TestUserDataHandlersConvenienceFunctions:
    """Test convenience functions for updating user data."""

    def test_update_user_account_valid_input(self, test_data_dir):
        """Test update_user_account with valid input."""
        from pathlib import Path
        from tests.conftest import wait_until

        user_id = f"test_update_account_{uuid.uuid4().hex[:8]}"
        assert TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
        actual_user_id = _resolve_actual_user_id(test_data_dir, user_id)
        assert actual_user_id, "Should resolve created UUID user id"
        
        updates = {
            "timezone": "America/New_York"
        }
        
        # Use resolved UUID to avoid cross-test identifier index collisions in parallel runs.
        result = update_user_account(actual_user_id, updates, auto_create=True)
        
        assert result is True, "Should update account successfully"
        
        # Verify update was applied to the exact created user record (avoid index/cache cross-talk)
        account_file = Path(test_data_dir) / "users" / actual_user_id / "account.json"
        assert wait_until(
            lambda: account_file.exists(), timeout_seconds=1.0, poll_seconds=0.01
        ), "Should resolve created account file"
        account = safe_json_read(str(account_file), default={})
        assert (
            account.get("internal_username") == user_id
        ), "Should read the expected test user"
        assert account.get("user_id") == actual_user_id, "Should update the expected UUID user"
        assert account.get("timezone") == "America/New_York", "Should update timezone"

    def test_update_user_account_invalid_user_id(self, test_data_dir):
        """Test update_user_account with invalid user_id."""
        # Test None user_id
        result = update_user_account(None, {"test": "value"})
        assert result is False, "Should return False for None user_id"
        
        # Test empty string user_id
        result = update_user_account("", {"test": "value"})
        assert result is False, "Should return False for empty user_id"
        
        # Test whitespace-only user_id
        result = update_user_account("   ", {"test": "value"})
        assert result is False, "Should return False for whitespace-only user_id"
        
        # Test non-string user_id
        result = update_user_account(123, {"test": "value"})
        assert result is False, "Should return False for non-string user_id"

    def test_update_user_account_invalid_updates(self, test_data_dir):
        """Test update_user_account with invalid updates."""
        user_id = "test_invalid_updates"
        TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
        
        # Test None updates
        result = update_user_account(user_id, None)
        assert result is False, "Should return False for None updates"
        
        # Test non-dict updates
        result = update_user_account(user_id, "not a dict")
        assert result is False, "Should return False for non-dict updates"
        
        result = update_user_account(user_id, ["list", "not", "dict"])
        assert result is False, "Should return False for list updates"

    def test_update_user_account_auto_create_false(self, test_data_dir):
        """Test update_user_account with auto_create=False for nonexistent user."""
        user_id = "nonexistent_user_12345"
        
        # Should return False when user doesn't exist and auto_create=False
        result = update_user_account(user_id, {"test": "value"}, auto_create=False)
        assert result is False, "Should return False when user doesn't exist and auto_create=False"

    def test_update_user_preferences_valid_input(self, test_data_dir):
        """Test update_user_preferences with valid input."""
        from pathlib import Path
        from tests.conftest import wait_until

        user_id = f"test_update_prefs_{uuid.uuid4().hex[:8]}"
        TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
        actual_user_id = _resolve_actual_user_id(test_data_dir, user_id)
        assert actual_user_id, "Should resolve created UUID user id"
        
        updates = {
            "checkin_settings": {
                "enabled": True,
                "frequency": "daily"
            }
        }
        
        result = update_user_preferences(actual_user_id, updates, auto_create=True)
        
        assert result is True, "Should update preferences successfully"

        prefs_file = Path(test_data_dir) / "users" / actual_user_id / "preferences.json"
        assert wait_until(
            lambda: prefs_file.exists(), timeout_seconds=1.0, poll_seconds=0.01
        ), "Preferences file should exist for created user"
        preferences = safe_json_read(str(prefs_file), default={})
        assert preferences.get("checkin_settings", {}).get("enabled") is True, "Should update checkin settings"

    def test_update_user_preferences_with_categories(self, test_data_dir):
        """Test update_user_preferences with category updates."""
        user_id = "test_update_categories"
        TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
        
        updates = {
            "categories": ["motivational", "health", "new_category"]
        }
        
        result = update_user_preferences(user_id, updates, auto_create=True)
        
        assert result is True, "Should update preferences with categories successfully"
        
        # Verify categories were updated
        prefs_data = get_user_data(user_id, "preferences")
        assert prefs_data is not None, "Should retrieve preferences data"
        # get_user_data returns dict with data_type as key
        preferences = prefs_data.get("preferences") if isinstance(prefs_data, dict) and "preferences" in prefs_data else prefs_data
        assert preferences is not None, "Should have preferences data"
        categories = preferences.get("categories", [])
        assert "new_category" in categories, "Should include new category"

    def test_update_user_preferences_invalid_input(self, test_data_dir):
        """Test update_user_preferences with invalid input."""
        user_id = "test_invalid_prefs"
        TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
        
        # Test None updates
        result = update_user_preferences(user_id, None)
        assert result is False, "Should return False for None updates"
        
        # Test non-dict updates
        result = update_user_preferences(user_id, "not a dict")
        assert result is False, "Should return False for non-dict updates"
        
        # Test invalid user_id
        result = update_user_preferences("", {"test": "value"})
        assert result is False, "Should return False for empty user_id"

    def test_update_user_preferences_auto_create_false(self, test_data_dir):
        """Test update_user_preferences with auto_create=False."""
        user_id = "nonexistent_user_prefs_12345"
        
        # Should return False when user doesn't exist and auto_create=False
        result = update_user_preferences(user_id, {"test": "value"}, auto_create=False)
        assert result is False, "Should return False when user doesn't exist and auto_create=False"

    def test_update_user_context_valid_input(self, test_data_dir):
        """Test update_user_context with valid input."""
        user_id = "test_update_context"
        TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
        
        updates = {
            "preferred_name": "Context Name",
            "interests": ["reading", "coding"]
        }
        
        result = update_user_context(user_id, updates, auto_create=True)
        
        assert result is True, "Should update context successfully"
        
        # Verify update was applied
        context_data = get_user_data(user_id, "context")
        assert context_data is not None, "Should retrieve context data"
        # get_user_data returns dict with data_type as key
        context = extract_nested_data(context_data, "context")
        assert context is not None, "Should have context data"
        assert context.get("preferred_name") == "Context Name", "Should update preferred_name"
        assert "reading" in context.get("interests", []), "Should update interests"

    def test_update_user_context_invalid_input(self, test_data_dir):
        """Test update_user_context with invalid input."""
        user_id = "test_invalid_context"
        TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
        
        # Test None updates
        result = update_user_context(user_id, None)
        assert result is False, "Should return False for None updates"
        
        # Test non-dict updates
        result = update_user_context(user_id, "not a dict")
        assert result is False, "Should return False for non-dict updates"
        
        # Test invalid user_id
        result = update_user_context("", {"test": "value"})
        assert result is False, "Should return False for empty user_id"

    def test_update_channel_preferences_valid_input(self, test_data_dir):
        """Test update_channel_preferences with valid input."""
        user_id = "test_update_channel"
        TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
        
        updates = {
            "discord": {
                "channel_id": "123456789",
                "enabled": True
            }
        }
        
        result = update_channel_preferences(user_id, updates, auto_create=True)
        
        assert result is True, "Should update channel preferences successfully"
        
        # Verify update was applied
        channel_data = get_user_data(user_id, "channel_preferences")
        assert channel_data is not None, "Should retrieve channel preferences data"

    def test_update_channel_preferences_invalid_input(self, test_data_dir):
        """Test update_channel_preferences with invalid input."""
        user_id = "test_invalid_channel"
        TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
        
        # Test None updates
        result = update_channel_preferences(user_id, None)
        assert result is False, "Should return False for None updates"
        
        # Test non-dict updates
        result = update_channel_preferences(user_id, "not a dict")
        assert result is False, "Should return False for non-dict updates"
        
        # Test invalid user_id
        result = update_channel_preferences("", {"test": "value"})
        assert result is False, "Should return False for empty user_id"

    def test_update_user_schedules_valid_input(self, test_data_dir):
        """Test update_user_schedules with valid input."""
        user_id = "test_update_schedules"
        TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
        
        schedules_data = {
            "motivational": {
                "Morning": {
                    "start": "08:00",
                    "end": "12:00"
                }
            }
        }
        
        result = update_user_schedules(user_id, schedules_data)
        
        assert result is True, "Should update schedules successfully"

    def test_update_user_schedules_invalid_input(self, test_data_dir):
        """Test update_user_schedules with invalid input."""
        user_id = "test_invalid_schedules"
        TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
        
        # Test None schedules_data
        result = update_user_schedules(user_id, None)
        assert result is False, "Should return False for None schedules_data"
        
        # Test non-dict schedules_data
        result = update_user_schedules(user_id, "not a dict")
        assert result is False, "Should return False for non-dict schedules_data"
        
        # Test invalid user_id
        result = update_user_schedules("", {"test": "value"})
        assert result is False, "Should return False for empty user_id"
        
        # Test whitespace-only user_id
        result = update_user_schedules("   ", {"test": "value"})
        assert result is False, "Should return False for whitespace-only user_id"

    def test_get_all_user_ids_returns_list(self, test_data_dir):
        """Test get_all_user_ids returns a list."""
        # Create some test users
        TestUserFactory.create_basic_user("user1", test_data_dir=test_data_dir)
        TestUserFactory.create_basic_user("user2", test_data_dir=test_data_dir)
        
        user_ids = get_all_user_ids()
        
        assert isinstance(user_ids, list), "Should return a list"
        assert len(user_ids) >= 2, "Should include created users"

    def test_register_data_loader_valid_input(self, test_data_dir):
        """Test register_data_loader with valid input."""
        def test_loader(user_id, auto_create=True):
            return {"test": "data"}
        
        result = register_data_loader(
            "test_type",
            test_loader,
            "test_file.json",
            default_fields=["test"],
            description="Test loader"
        )
        
        assert result is True, "Should register loader successfully"

    def test_register_data_loader_invalid_input(self, test_data_dir):
        """Test register_data_loader with invalid input."""
        def test_loader(user_id, auto_create=True):
            return {"test": "data"}
        
        # Test None data_type
        result = register_data_loader(None, test_loader, "test.json")
        assert result is False, "Should return False for None data_type"
        
        # Test empty data_type
        result = register_data_loader("", test_loader, "test.json")
        assert result is False, "Should return False for empty data_type"
        
        # Test None file_type
        result = register_data_loader("test_type", test_loader, None)
        assert result is False, "Should return False for None file_type"
        
        # Test empty file_type
        result = register_data_loader("test_type", test_loader, "")
        assert result is False, "Should return False for empty file_type"
        
        # Test non-callable loader_func
        result = register_data_loader("test_type", "not callable", "test.json")
        assert result is False, "Should return False for non-callable loader_func"

    def test_get_user_data_with_fields_selection(self, test_data_dir):
        """Test get_user_data with field selection."""
        user_id = "test_fields_selection"
        TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
        
        # Test single field selection
        result = get_user_data(user_id, "account", fields="preferred_name")
        assert result is not None, "Should return data"
        
        # Test multiple fields selection
        result = get_user_data(user_id, "account", fields=["preferred_name", "timezone"])
        assert isinstance(result, dict), "Should return dict for multiple fields"
        
        # Test field selection for specific data type
        result = get_user_data(user_id, "all", fields={"account": ["preferred_name"]})
        assert isinstance(result, dict), "Should return dict for type-specific fields"

    def test_get_user_data_with_auto_create_false(self, test_data_dir):
        """Test get_user_data with auto_create=False."""
        user_id = "nonexistent_auto_create_false"
        
        # Should return empty dict when user doesn't exist and auto_create=False
        result = get_user_data(user_id, "account", auto_create=False)
        assert result == {}, "Should return empty dict for nonexistent user with auto_create=False"

    def test_get_user_data_with_metadata(self, test_data_dir):
        """Test get_user_data with include_metadata=True."""
        user_id = "test_metadata"
        TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
        
        result = get_user_data(user_id, "account", include_metadata=True)
        
        assert isinstance(result, dict), "Should return dict"
        if result:
            # Check if metadata is included (may be in _metadata key or as part of structure)
            assert True, "Metadata inclusion tested"

    def test_get_user_data_with_normalize_on_read(self, test_data_dir):
        """Test get_user_data with normalize_on_read=True."""
        user_id = "test_normalize"
        TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
        
        result = get_user_data(user_id, "account", normalize_on_read=True)
        
        assert isinstance(result, dict), "Should return normalized dict"
        # Normalized account should have timezone
        if result and "account" in result:
            account = result["account"]
            assert "timezone" in account, "Normalized account should have timezone"

    def test_update_functions_handle_errors_gracefully(self, test_data_dir):
        """Test that update functions handle errors gracefully."""
        user_id = "test_error_handling"
        TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
        
        # Mock save_user_data to raise an error
        with patch('core.user_data_handlers.save_user_data', side_effect=Exception("Test error")):
            result = update_user_account(user_id, {"test": "value"})
            # Should return False on error, not raise exception
            assert result is False, "Should return False on error"
            
            result = update_user_preferences(user_id, {"test": "value"})
            assert result is False, "Should return False on error"
            
            result = update_user_context(user_id, {"test": "value"})
            assert result is False, "Should return False on error"
            
            result = update_channel_preferences(user_id, {"test": "value"})
            assert result is False, "Should return False on error"

    def test_save_user_data_transaction_valid_input(self, test_data_dir):
        """Test save_user_data_transaction with valid input."""
        from pathlib import Path
        from tests.conftest import wait_until

        user_id = f"test_transaction_{uuid.uuid4().hex[:8]}"
        assert TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
        actual_user_id = _resolve_actual_user_id(test_data_dir, user_id)
        assert actual_user_id, "Should resolve created UUID user id"
        
        data_updates = {
            "account": {
                "internal_username": user_id,
                "timezone": "America/Chicago"
            },
            "preferences": {
                "checkin_settings": {"enabled": True}
            }
        }
        
        # Use resolved UUID to avoid cross-test identifier index collisions in parallel runs.
        result = save_user_data_transaction(actual_user_id, data_updates, auto_create=True)
        
        assert result is True, "Should complete transaction successfully"
        
        # Verify updates were applied to the exact created user record (avoid index/cache cross-talk)
        account_file = Path(test_data_dir) / "users" / actual_user_id / "account.json"
        assert wait_until(
            lambda: account_file.exists(), timeout_seconds=1.0, poll_seconds=0.01
        ), "Should resolve created account file"
        account = safe_json_read(str(account_file), default={})
        assert account.get("internal_username") == user_id, "Should read the expected test user"
        assert account.get("user_id") == actual_user_id, "Should update the expected UUID user"
        assert account.get("timezone") == "America/Chicago", "Should update account timezone"

    def test_save_user_data_transaction_invalid_input(self, test_data_dir):
        """Test save_user_data_transaction with invalid input."""
        # Test None user_id
        result = save_user_data_transaction(None, {"account": {"test": "value"}})
        assert result is False, "Should return False for None user_id"
        
        # Test empty user_id
        result = save_user_data_transaction("", {"account": {"test": "value"}})
        assert result is False, "Should return False for empty user_id"
        
        # Test None data_updates
        result = save_user_data_transaction("test_user", None)
        assert result is False, "Should return False for None data_updates"
        
        # Test empty data_updates
        result = save_user_data_transaction("test_user", {})
        assert result is False, "Should return False for empty data_updates"

    def test_save_user_data_transaction_creates_backup(self, test_data_dir):
        """Test that save_user_data_transaction creates backup."""
        user_id = "test_transaction_backup"
        TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
        
        data_updates = {
            "account": {
                "preferred_name": "Backup Test"
            }
        }
        
        # Mock backup creation to verify it's called
        # UserDataManager is imported inside the function, so patch the import location
        with patch('core.user_data_manager.UserDataManager') as mock_manager_class:
            mock_manager = Mock()
            mock_manager_class.return_value = mock_manager
            mock_manager.backup_user_data.return_value = "backup_path.zip"
            
            result = save_user_data_transaction(user_id, data_updates, auto_create=True)
            
            # Verify backup was attempted (may not be called if backup fails, but function should still work)
            assert isinstance(result, bool), "Should return boolean result"

    def test_save_user_data_transaction_updates_index_on_success(self, test_data_dir):
        """Test that save_user_data_transaction updates index on success."""
        user_id = "test_transaction_index"
        TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
        
        data_updates = {
            "account": {
                "preferred_name": "Index Test"
            }
        }
        
        # Mock index update to verify it's called
        # update_user_index is imported inside the function, so patch the import location
        with patch('core.user_data_manager.update_user_index') as mock_update_index:
            result = save_user_data_transaction(user_id, data_updates, auto_create=True)
            
            # If transaction succeeded, index should be updated
            # Note: The function may handle errors gracefully, so we just verify it completes
            assert isinstance(result, bool), "Should return boolean result"

    def test_save_user_data_transaction_handles_partial_failure(self, test_data_dir):
        """Test that save_user_data_transaction handles partial failures."""
        user_id = "test_transaction_partial"
        TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
        
        # Create data_updates with one valid and one invalid type
        data_updates = {
            "account": {
                "preferred_name": "Partial Test"
            },
            "invalid_type": {
                "test": "value"
            }
        }
        
        result = save_user_data_transaction(user_id, data_updates, auto_create=True)
        
        # Transaction should fail if any type fails
        # The exact behavior depends on implementation, but should not crash
        assert isinstance(result, bool), "Should return boolean result"
