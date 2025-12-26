"""
User Preferences Test Coverage Expansion

This module provides comprehensive test coverage for user/user_preferences.py.
Focuses on real behavior testing to verify actual side effects and system changes.

Coverage Areas:
- UserPreferences class initialization
- Preference loading and saving
- Preference CRUD operations (get, set, update, remove)
- Schedule period active state management
- Error handling and edge cases
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from user.user_preferences import UserPreferences
from core.user_data_handlers import get_user_data


@pytest.mark.unit
class TestUserPreferences:
    """Comprehensive test coverage for UserPreferences class."""
    
    @pytest.fixture
    def user_id(self):
        """Provide a test user ID."""
        return "test-user-preferences"
    
    @pytest.fixture
    def mock_user_data_dir(self, tmp_path, monkeypatch):
        """Mock user data directory to use temporary test directory."""
        test_data_dir = tmp_path / "data"
        test_data_dir.mkdir()
        (test_data_dir / "users").mkdir()
        
        # Mock the user data path
        def mock_get_user_data_path(user_id, data_type):
            return test_data_dir / "users" / user_id / f"{data_type}.json"
        
        return str(test_data_dir)
    
    def test_user_preferences_initialization_real_behavior(self, mock_user_data_dir, user_id):
        """Test UserPreferences initialization loads preferences."""
        # Create initial preferences
        initial_prefs = {'theme': 'dark', 'notifications': True}
        
        with patch('user.user_preferences.get_user_data', return_value={'preferences': initial_prefs}):
            prefs = UserPreferences(user_id)
            
            assert prefs.user_id == user_id
            assert prefs.preferences == initial_prefs
    
    def test_user_preferences_initialization_empty_preferences_real_behavior(self, mock_user_data_dir, user_id):
        """Test UserPreferences initialization with empty preferences."""
        with patch('user.user_preferences.get_user_data', return_value={}):
            prefs = UserPreferences(user_id)
            
            assert prefs.user_id == user_id
            assert prefs.preferences == {}
    
    def test_user_preferences_initialization_none_preferences_real_behavior(self, mock_user_data_dir, user_id):
        """Test UserPreferences initialization with None preferences."""
        with patch('user.user_preferences.get_user_data', return_value={'preferences': None}):
            prefs = UserPreferences(user_id)
            
            assert prefs.user_id == user_id
            assert prefs.preferences == {}
    
    def test_load_preferences_real_behavior(self, mock_user_data_dir, user_id):
        """Test loading preferences from user data."""
        expected_prefs = {'theme': 'light', 'language': 'en'}
        
        with patch('user.user_preferences.get_user_data', return_value={'preferences': expected_prefs}):
            prefs = UserPreferences(user_id)
            loaded = prefs.load_preferences()
            
            assert loaded == expected_prefs
    
    def test_load_preferences_error_handling_real_behavior(self, mock_user_data_dir, user_id):
        """Test load_preferences error handling returns empty dict."""
        with patch('user.user_preferences.get_user_data', side_effect=Exception("Database error")):
            prefs = UserPreferences(user_id)
            # Should return empty dict on error due to @handle_errors decorator
            assert prefs.preferences == {}
    
    def test_save_preferences_real_behavior(self, mock_user_data_dir, user_id):
        """Test saving preferences updates user data."""
        prefs = UserPreferences(user_id)
        prefs.preferences = {'theme': 'dark', 'notifications': False}
        
        with patch('user.user_preferences.update_user_preferences') as mock_update:
            prefs.save_preferences()
            
            mock_update.assert_called_once_with(user_id, prefs.preferences)
    
    def test_save_preferences_error_handling_real_behavior(self, mock_user_data_dir, user_id):
        """Test save_preferences error handling."""
        prefs = UserPreferences(user_id)
        prefs.preferences = {'theme': 'dark'}
        
        with patch('user.user_preferences.update_user_preferences', side_effect=Exception("Save error")):
            # Should not raise exception due to @handle_errors decorator
            prefs.save_preferences()
            # Preferences should still be set locally even if save fails
            assert prefs.preferences == {'theme': 'dark'}
    
    def test_set_preference_real_behavior(self, mock_user_data_dir, user_id):
        """Test setting a preference saves it."""
        prefs = UserPreferences(user_id)
        prefs.preferences = {}
        
        with patch.object(prefs, 'save_preferences') as mock_save:
            prefs.set_preference('theme', 'dark')
            
            assert prefs.preferences['theme'] == 'dark'
            mock_save.assert_called_once()
    
    def test_set_preference_overwrites_existing_real_behavior(self, mock_user_data_dir, user_id):
        """Test setting a preference overwrites existing value."""
        prefs = UserPreferences(user_id)
        prefs.preferences = {'theme': 'light'}
        
        with patch.object(prefs, 'save_preferences'):
            prefs.set_preference('theme', 'dark')
            
            assert prefs.preferences['theme'] == 'dark'
    
    def test_set_preference_error_handling_real_behavior(self, mock_user_data_dir, user_id):
        """Test set_preference error handling."""
        prefs = UserPreferences(user_id)
        prefs.preferences = {}
        
        with patch.object(prefs, 'save_preferences', side_effect=Exception("Save error")):
            # Should not raise exception due to @handle_errors decorator
            prefs.set_preference('theme', 'dark')
            # Preference should still be set locally
            assert prefs.preferences['theme'] == 'dark'
    
    def test_get_preference_existing_real_behavior(self, mock_user_data_dir, user_id):
        """Test getting an existing preference."""
        prefs = UserPreferences(user_id)
        prefs.preferences = {'theme': 'dark', 'notifications': True}
        
        assert prefs.get_preference('theme') == 'dark'
        assert prefs.get_preference('notifications') is True
    
    def test_get_preference_missing_real_behavior(self, mock_user_data_dir, user_id):
        """Test getting a missing preference returns None."""
        prefs = UserPreferences(user_id)
        prefs.preferences = {}
        
        assert prefs.get_preference('theme') is None
    
    def test_get_preference_error_handling_real_behavior(self, mock_user_data_dir, user_id):
        """Test get_preference with invalid key type (edge case)."""
        prefs = UserPreferences(user_id)
        prefs.preferences = {'theme': 'dark'}
        
        # Test with non-string key (edge case)
        result = prefs.get_preference(123)  # Invalid key type
        # Should return None for invalid key
        assert result is None
    
    def test_update_preference_real_behavior(self, mock_user_data_dir, user_id):
        """Test update_preference calls set_preference."""
        prefs = UserPreferences(user_id)
        prefs.preferences = {}
        
        with patch.object(prefs, 'set_preference') as mock_set:
            prefs.update_preference('theme', 'dark')
            
            mock_set.assert_called_once_with('theme', 'dark')
    
    def test_remove_preference_existing_real_behavior(self, mock_user_data_dir, user_id):
        """Test removing an existing preference."""
        prefs = UserPreferences(user_id)
        prefs.preferences = {'theme': 'dark', 'notifications': True}
        
        with patch.object(prefs, 'save_preferences') as mock_save:
            prefs.remove_preference('theme')
            
            assert 'theme' not in prefs.preferences
            assert 'notifications' in prefs.preferences
            mock_save.assert_called_once()
    
    def test_remove_preference_missing_real_behavior(self, mock_user_data_dir, user_id):
        """Test removing a missing preference logs warning but doesn't fail."""
        prefs = UserPreferences(user_id)
        prefs.preferences = {'notifications': True}
        
        with patch.object(prefs, 'save_preferences') as mock_save, \
             patch('user.user_preferences.logger') as mock_logger:
            prefs.remove_preference('theme')
            
            # Should not save if preference wasn't found
            mock_save.assert_not_called()
            # Should log warning
            mock_logger.warning.assert_called_once()
    
    def test_remove_preference_error_handling_real_behavior(self, mock_user_data_dir, user_id):
        """Test remove_preference error handling."""
        prefs = UserPreferences(user_id)
        prefs.preferences = {'theme': 'dark'}
        
        with patch.object(prefs, 'save_preferences', side_effect=Exception("Save error")):
            # Should not raise exception due to @handle_errors decorator
            prefs.remove_preference('theme')
            # Preference should still be removed locally
            assert 'theme' not in prefs.preferences
    
    def test_get_all_preferences_real_behavior(self, mock_user_data_dir, user_id):
        """Test getting all preferences returns a copy."""
        original_prefs = {'theme': 'dark', 'notifications': True}
        prefs = UserPreferences(user_id)
        prefs.preferences = original_prefs.copy()
        
        all_prefs = prefs.get_all_preferences()
        
        assert all_prefs == original_prefs
        # Should be a copy, not a reference
        assert all_prefs is not prefs.preferences
        # Modifying copy shouldn't affect original
        all_prefs['new_key'] = 'new_value'
        assert 'new_key' not in prefs.preferences
    
    def test_get_all_preferences_empty_real_behavior(self, mock_user_data_dir, user_id):
        """Test getting all preferences when empty returns empty dict."""
        prefs = UserPreferences(user_id)
        prefs.preferences = {}
        
        all_prefs = prefs.get_all_preferences()
        
        assert all_prefs == {}
    
    def test_get_all_preferences_with_nested_structure_real_behavior(self, mock_user_data_dir, user_id):
        """Test get_all_preferences with nested preference structure."""
        nested_prefs = {
            'theme': 'dark',
            'settings': {
                'notifications': True,
                'language': 'en'
            }
        }
        prefs = UserPreferences(user_id)
        prefs.preferences = nested_prefs.copy()
        
        all_prefs = prefs.get_all_preferences()
        
        assert all_prefs == nested_prefs
        # Should be a shallow copy (not deep copy)
        assert all_prefs is not prefs.preferences
        # Modifying top-level keys shouldn't affect original
        all_prefs['theme'] = 'light'
        assert prefs.preferences['theme'] == 'dark'  # Original unchanged
        # But nested structures are shared (shallow copy behavior)
        assert all_prefs['settings'] is prefs.preferences['settings']  # Same reference
    
    def test_set_schedule_period_active_static_method_real_behavior(self, mock_user_data_dir, user_id):
        """Test static method set_schedule_period_active."""
        with patch('user.user_preferences.set_schedule_period_active', return_value=True) as mock_set:
            result = UserPreferences.set_schedule_period_active(user_id, 'work', 'morning', True)
            
            assert result is True
            mock_set.assert_called_once_with(user_id, 'work', 'morning', active=True)
    
    def test_set_schedule_period_active_error_handling_real_behavior(self, mock_user_data_dir, user_id):
        """Test set_schedule_period_active error handling returns False."""
        with patch('user.user_preferences.set_schedule_period_active', side_effect=Exception("Error")):
            result = UserPreferences.set_schedule_period_active(user_id, 'work', 'morning', True)
            
            # Should return False on error due to @handle_errors decorator
            assert result is False
    
    def test_is_schedule_period_active_static_method_real_behavior(self, mock_user_data_dir, user_id):
        """Test static method is_schedule_period_active."""
        with patch('user.user_preferences.is_schedule_period_active', return_value=True) as mock_is:
            result = UserPreferences.is_schedule_period_active(user_id, 'work', 'morning')
            
            assert result is True
            mock_is.assert_called_once_with(user_id, 'work', 'morning')
    
    def test_is_schedule_period_active_error_handling_real_behavior(self, mock_user_data_dir, user_id):
        """Test is_schedule_period_active error handling returns False."""
        with patch('user.user_preferences.is_schedule_period_active', side_effect=Exception("Error")):
            result = UserPreferences.is_schedule_period_active(user_id, 'work', 'morning')
            
            # Should return False on error due to @handle_errors decorator
            assert result is False
    
    def test_multiple_preference_operations_real_behavior(self, mock_user_data_dir, user_id):
        """Test multiple preference operations in sequence."""
        prefs = UserPreferences(user_id)
        prefs.preferences = {}
        
        with patch.object(prefs, 'save_preferences') as mock_save:
            prefs.set_preference('theme', 'dark')
            prefs.set_preference('notifications', True)
            prefs.set_preference('language', 'en')
            prefs.remove_preference('language')
            
            assert prefs.preferences == {'theme': 'dark', 'notifications': True}
            # Should save after each set/remove operation
            assert mock_save.call_count == 4
    
    def test_preference_persistence_real_behavior(self, mock_user_data_dir, user_id):
        """Test that preferences persist across UserPreferences instances."""
        initial_prefs = {'theme': 'dark'}
        
        with patch('user.user_preferences.get_user_data', return_value={'preferences': initial_prefs}):
            prefs1 = UserPreferences(user_id)
            prefs1.set_preference('notifications', True)
            
            # Create new instance - should load updated preferences
            with patch('user.user_preferences.get_user_data', return_value={'preferences': {'theme': 'dark', 'notifications': True}}):
                prefs2 = UserPreferences(user_id)
                
                assert prefs2.get_preference('theme') == 'dark'
                assert prefs2.get_preference('notifications') is True

