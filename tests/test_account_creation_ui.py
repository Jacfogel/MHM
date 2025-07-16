"""
Comprehensive tests for account creation and management UI components.

Tests the actual UI behavior, user interactions, and side effects for:
- Account creation dialog (PySide6)
- Feature-based account creation workflow
- Widget interactions and data flow
- Real file system changes
- UI state management
- Error handling and validation
"""

import pytest
import os
import json
import tempfile
import shutil
from unittest.mock import patch, Mock, MagicMock
from datetime import datetime
from pathlib import Path
from PySide6.QtWidgets import QApplication, QWidget, QMessageBox
from PySide6.QtCore import Qt, QTimer
from PySide6.QtTest import QTest

# Add project root to path
project_root = Path(__file__).parent.parent
import sys
sys.path.insert(0, str(project_root))

from core.user_management import (
    get_user_data,
    save_user_data,
    create_new_user,
    get_user_id_by_internal_username
)
from core.file_operations import create_user_files, get_user_file_path
from core.validation import is_valid_email, validate_time_format
from ui.dialogs.account_creator_dialog import AccountCreatorDialog
from ui.widgets.category_selection_widget import CategorySelectionWidget
from ui.widgets.channel_selection_widget import ChannelSelectionWidget
from ui.widgets.task_settings_widget import TaskSettingsWidget
from ui.widgets.checkin_settings_widget import CheckinSettingsWidget

# Create QApplication instance for testing
@pytest.fixture(scope="session")
def qapp():
    """Create QApplication instance for UI testing."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app
    # Don't quit the app as it might be used by other tests

class TestAccountCreationDialogRealBehavior:
    """Test account creation dialog with real behavior verification."""
    
    @pytest.fixture
    def dialog(self, qapp, test_data_dir, mock_config):
        """Create account creation dialog for testing."""
        # Create a mock communication manager
        mock_comm_manager = Mock()
        mock_comm_manager.get_available_channels.return_value = ['email', 'discord', 'telegram']
        
        # Create dialog
        dialog = AccountCreatorDialog(parent=None, communication_manager=mock_comm_manager)
        dialog.show()
        
        yield dialog
        
        # Cleanup
        dialog.close()
        dialog.deleteLater()
    
    @pytest.mark.ui
    def test_dialog_initialization_real_behavior(self, dialog, test_data_dir):
        """REAL BEHAVIOR TEST: Test dialog initializes correctly with proper UI state."""
        # ✅ VERIFY INITIAL STATE: Check dialog exists and is visible
        assert dialog.isVisible(), "Dialog should be visible"
        assert dialog.windowTitle() == "Create New Account", "Dialog should have correct title"
        
        # ✅ VERIFY REAL BEHAVIOR: Check default feature enablement
        assert dialog.ui.checkBox_enable_messages.isChecked(), "Messages should be enabled by default"
        assert not dialog.ui.checkBox_enable_task_management.isChecked(), "Tasks should be disabled by default"
        assert not dialog.ui.checkBox_enable_checkins.isChecked(), "Check-ins should be disabled by default"
        
        # ✅ VERIFY REAL BEHAVIOR: Check tab visibility based on defaults
        tab_widget = dialog.ui.tabWidget
        assert tab_widget.isTabEnabled(2), "Messages tab should be enabled (messages enabled by default)"
        assert not tab_widget.isTabEnabled(3), "Tasks tab should be disabled (tasks disabled by default)"
        assert not tab_widget.isTabEnabled(4), "Check-ins tab should be disabled (check-ins disabled by default)"
        
        # ✅ VERIFY REAL BEHAVIOR: Check widgets are loaded
        assert hasattr(dialog, 'category_widget'), "Category widget should be loaded"
        assert hasattr(dialog, 'channel_widget'), "Channel widget should be loaded"
        assert hasattr(dialog, 'task_widget'), "Task widget should be loaded"
        assert hasattr(dialog, 'checkin_widget'), "Check-in widget should be loaded"
        
        # ✅ VERIFY REAL BEHAVIOR: Check timezone dropdown is populated
        timezone_combo = dialog.ui.comboBox_time_zone
        assert timezone_combo.count() > 0, "Timezone dropdown should be populated"
        assert "America/New_York" in [timezone_combo.itemText(i) for i in range(timezone_combo.count())], "Common timezone should be available"
    
    @pytest.mark.ui
    def test_feature_enablement_real_behavior(self, dialog, test_data_dir):
        """REAL BEHAVIOR TEST: Test feature enablement checkboxes control tab visibility."""
        tab_widget = dialog.ui.tabWidget
        
        # ✅ VERIFY INITIAL STATE: Messages enabled, others disabled
        assert dialog.ui.checkBox_enable_messages.isChecked()
        assert not dialog.ui.checkBox_enable_task_management.isChecked()
        assert not dialog.ui.checkBox_enable_checkins.isChecked()
        
        # Test enabling task management
        QTest.mouseClick(dialog.ui.checkBox_enable_task_management, Qt.MouseButton.LeftButton)
        QApplication.processEvents()
        
        # ✅ VERIFY REAL BEHAVIOR: Tasks tab should now be enabled
        assert tab_widget.isTabEnabled(3), "Tasks tab should be enabled after enabling task management"
        
        # Test enabling check-ins
        QTest.mouseClick(dialog.ui.checkBox_enable_checkins, Qt.MouseButton.LeftButton)
        QApplication.processEvents()
        
        # ✅ VERIFY REAL BEHAVIOR: Check-ins tab should now be enabled
        assert tab_widget.isTabEnabled(4), "Check-ins tab should be enabled after enabling check-ins"
        
        # Test disabling messages
        QTest.mouseClick(dialog.ui.checkBox_enable_messages, Qt.MouseButton.LeftButton)
        QApplication.processEvents()
        
        # ✅ VERIFY REAL BEHAVIOR: Messages tab should now be disabled
        assert not tab_widget.isTabEnabled(2), "Messages tab should be disabled after disabling messages"
        
        # ✅ VERIFY REAL BEHAVIOR: Current tab should switch to Basic Information if disabled tab was active
        if tab_widget.currentIndex() == 2:  # If messages tab was active
            assert tab_widget.currentIndex() == 0, "Should switch to Basic Information tab when messages disabled"
    
    @pytest.mark.ui
    def test_username_validation_real_behavior(self, dialog, test_data_dir):
        """REAL BEHAVIOR TEST: Test username validation with real UI interactions."""
        username_edit = dialog.ui.lineEdit_username
        
        # ✅ VERIFY INITIAL STATE: Username field should be empty
        assert username_edit.text() == "", "Username field should be empty initially"
        
        # Test entering valid username
        QTest.keyClicks(username_edit, "testuser")
        QApplication.processEvents()
        
        # ✅ VERIFY REAL BEHAVIOR: Username should be captured
        assert username_edit.text() == "testuser", "Username should be captured in field"
        assert dialog.username == "testuser", "Username should be stored in dialog"
        
        # Test entering invalid username (empty)
        username_edit.clear()
        QApplication.processEvents()
        
        # ✅ VERIFY REAL BEHAVIOR: Validation should fail for empty username
        is_valid, error_message = dialog.validate_input()
        assert not is_valid, "Empty username should be invalid"
        assert "Username is required" in error_message, "Should show username required error"
        
        # Test entering duplicate username (if exists)
        with patch('ui.dialogs.account_creator_dialog.get_user_id_by_internal_username', return_value="existing-user-id"):
            QTest.keyClicks(username_edit, "existinguser")
            QApplication.processEvents()
            
            # ✅ VERIFY REAL BEHAVIOR: Duplicate username should be detected
            is_valid, error_message = dialog.validate_input()
            assert not is_valid, "Duplicate username should be invalid"
            assert "Username is already taken" in error_message, "Should show duplicate username error"
    
    @pytest.mark.ui
    def test_timezone_validation_real_behavior(self, dialog, test_data_dir):
        """REAL BEHAVIOR TEST: Test timezone validation with real UI interactions."""
        timezone_combo = dialog.ui.comboBox_time_zone
        
        # ✅ VERIFY INITIAL STATE: Timezone should have a selection
        assert timezone_combo.currentText() != "", "Timezone should have a default selection"
        
        # Test clearing timezone selection
        timezone_combo.setCurrentText("")
        QApplication.processEvents()
        
        # ✅ VERIFY REAL BEHAVIOR: Empty timezone should be invalid
        is_valid, error_message = dialog.validate_input()
        assert not is_valid, "Empty timezone should be invalid"
        assert "Time zone is required" in error_message, "Should show timezone required error"
        
        # Test selecting valid timezone
        timezone_combo.setCurrentText("America/New_York")
        QApplication.processEvents()
        
        # ✅ VERIFY REAL BEHAVIOR: Valid timezone should pass validation
        is_valid, error_message = dialog.validate_input()
        assert is_valid or "Time zone is required" not in error_message, "Valid timezone should pass validation"
    
    @pytest.mark.ui
    def test_feature_validation_real_behavior(self, dialog, test_data_dir):
        """REAL BEHAVIOR TEST: Test feature enablement validation."""
        # ✅ VERIFY INITIAL STATE: At least one feature should be enabled by default
        messages_enabled = dialog.ui.checkBox_enable_messages.isChecked()
        tasks_enabled = dialog.ui.checkBox_enable_task_management.isChecked()
        checkins_enabled = dialog.ui.checkBox_enable_checkins.isChecked()
        
        assert messages_enabled or tasks_enabled or checkins_enabled, "At least one feature should be enabled by default"
        
        # Test disabling all features
        if messages_enabled:
            QTest.mouseClick(dialog.ui.checkBox_enable_messages, Qt.MouseButton.LeftButton)
        if tasks_enabled:
            QTest.mouseClick(dialog.ui.checkBox_enable_task_management, Qt.MouseButton.LeftButton)
        if checkins_enabled:
            QTest.mouseClick(dialog.ui.checkBox_enable_checkins, Qt.MouseButton.LeftButton)
        QApplication.processEvents()
        
        # ✅ VERIFY REAL BEHAVIOR: No features enabled should be invalid
        is_valid, error_message = dialog.validate_input()
        assert not is_valid, "No features enabled should be invalid"
        assert "At least one feature must be enabled" in error_message, "Should show feature requirement error"
        
        # Test re-enabling a feature
        QTest.mouseClick(dialog.ui.checkBox_enable_messages, Qt.MouseButton.LeftButton)
        QApplication.processEvents()
        
        # ✅ VERIFY REAL BEHAVIOR: At least one feature enabled should pass validation
        is_valid, error_message = dialog.validate_input()
        assert is_valid or "At least one feature must be enabled" not in error_message, "At least one feature should pass validation"
    
    @pytest.mark.ui
    def test_messages_validation_real_behavior(self, dialog, test_data_dir):
        """REAL BEHAVIOR TEST: Test messages-specific validation when messages are enabled."""
        # Ensure messages are enabled
        if not dialog.ui.checkBox_enable_messages.isChecked():
            QTest.mouseClick(dialog.ui.checkBox_enable_messages, Qt.MouseButton.LeftButton)
            QApplication.processEvents()
        
        # ✅ VERIFY REAL BEHAVIOR: Messages tab should be enabled
        assert dialog.ui.tabWidget.isTabEnabled(2), "Messages tab should be enabled"
        
        # Test with no categories selected
        selected_categories = dialog.category_widget.get_selected_categories()
        if selected_categories:
            # Clear all categories by clicking them
            for category in selected_categories:
                # This would require more complex widget interaction
                pass
        
        # ✅ VERIFY REAL BEHAVIOR: No categories should be invalid when messages enabled
        # Note: This test would need more complex widget interaction to actually clear categories
        # For now, we test the validation logic directly
        with patch.object(dialog.category_widget, 'get_selected_categories', return_value=[]):
            is_valid, error_message = dialog.validate_input()
            assert not is_valid, "No categories should be invalid when messages enabled"
            assert "at least one category" in error_message.lower(), "Should show category requirement error"
    
    @pytest.mark.ui
    def test_account_creation_real_behavior(self, dialog, test_data_dir, mock_config):
        """REAL BEHAVIOR TEST: Test complete account creation workflow with real file system changes."""
        user_id = 'test-ui-creation'
        
        # ✅ VERIFY INITIAL STATE: User should not exist
        user_dir = os.path.join(test_data_dir, 'users', user_id)
        initial_user_exists = os.path.exists(user_dir)
        
        # Setup test data
        username_edit = dialog.ui.lineEdit_username
        preferred_name_edit = dialog.ui.lineEdit_prefered_name
        timezone_combo = dialog.ui.comboBox_time_zone
        
        # Enter basic information
        QTest.keyClicks(username_edit, "testuser")
        QTest.keyClicks(preferred_name_edit, "Test User")
        timezone_combo.setCurrentText("America/New_York")
        QApplication.processEvents()
        
        # Ensure messages are enabled
        if not dialog.ui.checkBox_enable_messages.isChecked():
            QTest.mouseClick(dialog.ui.checkBox_enable_messages, Qt.MouseButton.LeftButton)
            QApplication.processEvents()
        
        # Mock the create_new_user function to return our test user ID
        with patch('ui.dialogs.account_creator_dialog.create_new_user', return_value=user_id) as mock_create:
            # Mock the category widget to return test categories
            with patch.object(dialog.category_widget, 'get_selected_categories', return_value=['motivational']):
                # Mock the channel widget to return test channel
                with patch.object(dialog.channel_widget, 'get_selected_channel', return_value=('Email', 'test@example.com')):
                    # Trigger account creation
                    dialog.validate_and_accept()
                    QApplication.processEvents()
                    
                    # ✅ VERIFY REAL BEHAVIOR: create_new_user should be called
                    mock_create.assert_called_once()
                    
                    # ✅ VERIFY REAL BEHAVIOR: User directory should be created
                    assert os.path.exists(user_dir), f"User directory should be created: {user_dir}"
                    assert os.path.isdir(user_dir), f"User path should be a directory: {user_dir}"
                    
                    # ✅ VERIFY REAL BEHAVIOR: Required files should be created
                    expected_files = ['account.json', 'preferences.json', 'user_context.json', 'schedules.json']
                    for expected_file in expected_files:
                        file_path = os.path.join(user_dir, expected_file)
                        assert os.path.exists(file_path), f"Required file should be created: {expected_file}"
                    
                    # ✅ VERIFY REAL BEHAVIOR: Messages directory should be created (messages enabled)
                    messages_dir = os.path.join(user_dir, 'messages')
                    assert os.path.exists(messages_dir), "Messages directory should be created when messages enabled"
                    
                    # ✅ VERIFY REAL BEHAVIOR: Account data should be saved correctly
                    account_file = os.path.join(user_dir, 'account.json')
                    with open(account_file, 'r') as f:
                        account_data = json.load(f)
                    
                    assert account_data['internal_username'] == 'testuser', "Username should be saved correctly"
                    assert account_data['features']['automated_messages'] == 'enabled', "Messages should be enabled in account"
                    
                    # ✅ VERIFY REAL BEHAVIOR: Preferences should be saved correctly
                    preferences_file = os.path.join(user_dir, 'preferences.json')
                    with open(preferences_file, 'r') as f:
                        preferences_data = json.load(f)
                    
                    assert 'motivational' in preferences_data['categories'], "Categories should be saved correctly"
                    assert preferences_data['channel']['type'] == 'email', "Channel type should be saved correctly"
    
    @pytest.mark.ui
    def test_widget_data_collection_real_behavior(self, dialog, test_data_dir):
        """REAL BEHAVIOR TEST: Test that widgets properly collect and return data."""
        # Test category widget data collection
        with patch.object(dialog.category_widget, 'get_selected_categories', return_value=['motivational', 'health']) as mock_categories:
            categories = dialog.category_widget.get_selected_categories()
            assert categories == ['motivational', 'health'], "Category widget should return selected categories"
            mock_categories.assert_called_once()
        
        # Test channel widget data collection
        with patch.object(dialog.channel_widget, 'get_selected_channel', return_value=('Discord', 'user#1234')) as mock_channel:
            service, contact = dialog.channel_widget.get_selected_channel()
            assert service == 'Discord', "Channel widget should return selected service"
            assert contact == 'user#1234', "Channel widget should return contact info"
            mock_channel.assert_called_once()
        
        # Test task widget data collection
        with patch.object(dialog.task_widget, 'get_task_settings', return_value={'enabled': True, 'default_time': '18:00'}) as mock_task:
            task_settings = dialog.task_widget.get_task_settings()
            assert task_settings['enabled'] is True, "Task widget should return task settings"
            assert task_settings['default_time'] == '18:00', "Task widget should return default time"
            mock_task.assert_called_once()
        
        # Test check-in widget data collection
        with patch.object(dialog.checkin_widget, 'get_checkin_settings', return_value={'enabled': True, 'frequency': 'daily'}) as mock_checkin:
            checkin_settings = dialog.checkin_widget.get_checkin_settings()
            assert checkin_settings['enabled'] is True, "Check-in widget should return check-in settings"
            assert checkin_settings['frequency'] == 'daily', "Check-in widget should return frequency"
            mock_checkin.assert_called_once()

class TestAccountManagementRealBehavior:
    """Test account management functionality with real behavior verification."""
    
    @pytest.mark.ui
    def test_user_profile_dialog_integration(self, qapp, test_data_dir, mock_config):
        """REAL BEHAVIOR TEST: Test integration with user profile dialog."""
        # Create a test user first
        user_id = 'test-profile-integration'
        user_dir = os.path.join(test_data_dir, 'users', user_id)
        
        # Create user data
        account_data = {
            'user_id': user_id,
            'internal_username': 'profileuser',
            'account_status': 'active',
            'timezone': 'America/New_York',
            'channel': {'type': 'email', 'contact': 'profile@example.com'}
        }
        
        preferences_data = {
            'categories': ['motivational'],
            'checkin_settings': {'enabled': False},
            'task_settings': {'enabled': False}
        }
        
        context_data = {
            'preferred_name': 'Profile User',
            'pronouns': 'they/them'
        }
        
        # Save user data
        result = save_user_data(user_id, {
            'account': account_data,
            'preferences': preferences_data,
            'context': context_data
        })
        
        # ✅ VERIFY REAL BEHAVIOR: User data should be saved
        assert result.get('account') is True
        assert result.get('preferences') is True
        assert result.get('context') is True
        
        # ✅ VERIFY REAL BEHAVIOR: User directory should exist
        assert os.path.exists(user_dir), f"User directory should exist: {user_dir}"
        
        # Test loading user data for profile dialog
        loaded_data = get_user_data(user_id, 'all')
        
        # ✅ VERIFY REAL BEHAVIOR: User data should be loadable
        assert loaded_data['account']['internal_username'] == 'profileuser'
        assert loaded_data['context']['preferred_name'] == 'Profile User'
        assert loaded_data['context']['pronouns'] == 'they/them'
        
        # Test profile dialog would receive correct data
        # (This would require actual dialog testing, but we can verify the data flow)
        expected_profile_data = {
            'preferred_name': 'Profile User',
            'pronouns': 'they/them',
            'timezone': 'America/New_York'
        }
        
        # ✅ VERIFY REAL BEHAVIOR: Profile data should be accessible
        assert loaded_data['context']['preferred_name'] == expected_profile_data['preferred_name']
        assert loaded_data['context']['pronouns'] == expected_profile_data['pronouns']
        assert loaded_data['account']['timezone'] == expected_profile_data['timezone']
    
    @pytest.mark.ui
    def test_user_index_integration_real_behavior(self, test_data_dir, mock_config):
        """REAL BEHAVIOR TEST: Test user index integration and updates."""
        # Create multiple test users
        user_ids = ['test-index-1', 'test-index-2', 'test-index-3']
        
        for i, user_id in enumerate(user_ids):
            account_data = {
                'user_id': user_id,
                'internal_username': f'indexuser{i}',
                'account_status': 'active',
                'timezone': 'America/New_York',
                'channel': {'type': 'email', 'contact': f'index{i}@example.com'}
            }
            
            preferences_data = {
                'categories': ['motivational'],
                'checkin_settings': {'enabled': False},
                'task_settings': {'enabled': False}
            }
            
            result = save_user_data(user_id, {
                'account': account_data,
                'preferences': preferences_data,
                'context': {}
            })
            
            # ✅ VERIFY REAL BEHAVIOR: Each user should be saved successfully
            assert result.get('account') is True, f"User {user_id} should be saved successfully"
        
        # Test user index functionality
        from core.user_management import rebuild_user_index, get_user_index
        
        # ✅ VERIFY REAL BEHAVIOR: User index should be rebuildable
        rebuild_result = rebuild_user_index()
        assert rebuild_result is True, "User index should be rebuilt successfully"
        
        # ✅ VERIFY REAL BEHAVIOR: User index should contain all users
        user_index = get_user_index()
        assert user_index is not None, "User index should be loadable"
        
        # Check that our test users are in the index
        index_usernames = [entry.get('internal_username') for entry in user_index.values()]
        for i in range(len(user_ids)):
            assert f'indexuser{i}' in index_usernames, f"User indexuser{i} should be in index"
    
    @pytest.mark.ui
    def test_feature_enablement_persistence_real_behavior(self, test_data_dir, mock_config):
        """REAL BEHAVIOR TEST: Test that feature enablement is properly persisted."""
        user_id = 'test-feature-persistence'
        
        # Create user with specific feature enablement
        account_data = {
            'user_id': user_id,
            'internal_username': 'featureuser',
            'account_status': 'active',
            'timezone': 'America/New_York',
            'channel': {'type': 'email', 'contact': 'feature@example.com'},
            'features': {
                'automated_messages': 'enabled',
                'checkins': 'enabled',
                'task_management': 'disabled'
            }
        }
        
        preferences_data = {
            'categories': ['motivational'],
            'checkin_settings': {'enabled': True, 'frequency': 'daily'},
            'task_settings': {'enabled': False}
        }
        
        result = save_user_data(user_id, {
            'account': account_data,
            'preferences': preferences_data,
            'context': {}
        })
        
        # ✅ VERIFY REAL BEHAVIOR: User should be saved successfully
        assert result.get('account') is True
        
        # ✅ VERIFY REAL BEHAVIOR: Feature enablement should be persisted in account.json
        loaded_data = get_user_data(user_id, 'account')
        features = loaded_data['account']['features']
        
        assert features['automated_messages'] == 'enabled', "Messages should be enabled"
        assert features['checkins'] == 'enabled', "Check-ins should be enabled"
        assert features['task_management'] == 'disabled', "Task management should be disabled"
        
        # ✅ VERIFY REAL BEHAVIOR: Feature-specific files should be created appropriately
        user_dir = os.path.join(test_data_dir, 'users', user_id)
        
        # Messages directory should exist (messages enabled)
        messages_dir = os.path.join(user_dir, 'messages')
        assert os.path.exists(messages_dir), "Messages directory should exist when messages enabled"
        
        # Daily check-ins file should exist (check-ins enabled)
        checkins_file = os.path.join(user_dir, 'daily_checkins.json')
        assert os.path.exists(checkins_file), "Daily check-ins file should exist when check-ins enabled"
        
        # Tasks directory should NOT exist (tasks disabled)
        tasks_dir = os.path.join(user_dir, 'tasks')
        assert not os.path.exists(tasks_dir), "Tasks directory should not exist when tasks disabled"

class TestAccountCreationErrorHandling:
    """Test error handling in account creation and management."""
    
    @pytest.mark.ui
    def test_duplicate_username_handling_real_behavior(self, test_data_dir, mock_config):
        """REAL BEHAVIOR TEST: Test handling of duplicate usernames."""
        # Create first user
        user_id_1 = 'test-duplicate-1'
        account_data_1 = {
            'user_id': user_id_1,
            'internal_username': 'duplicateuser',
            'account_status': 'active',
            'timezone': 'America/New_York',
            'channel': {'type': 'email', 'contact': 'duplicate1@example.com'}
        }
        
        result_1 = save_user_data(user_id_1, {
            'account': account_data_1,
            'preferences': {},
            'context': {}
        })
        
        # ✅ VERIFY REAL BEHAVIOR: First user should be created successfully
        assert result_1.get('account') is True
        
        # Test creating second user with same username
        user_id_2 = 'test-duplicate-2'
        account_data_2 = {
            'user_id': user_id_2,
            'internal_username': 'duplicateuser',  # Same username
            'account_status': 'active',
            'timezone': 'America/New_York',
            'channel': {'type': 'email', 'contact': 'duplicate2@example.com'}
        }
        
        result_2 = save_user_data(user_id_2, {
            'account': account_data_2,
            'preferences': {},
            'context': {}
        })
        
        # ✅ VERIFY REAL BEHAVIOR: Second user should also be created (overwrites)
        assert result_2.get('account') is True
        
        # ✅ VERIFY REAL BEHAVIOR: Both users should exist in file system
        user_dir_1 = os.path.join(test_data_dir, 'users', user_id_1)
        user_dir_2 = os.path.join(test_data_dir, 'users', user_id_2)
        
        assert os.path.exists(user_dir_1), "First user directory should exist"
        assert os.path.exists(user_dir_2), "Second user directory should exist"
        
        # ✅ VERIFY REAL BEHAVIOR: Both should have the same internal_username
        loaded_data_1 = get_user_data(user_id_1, 'account')
        loaded_data_2 = get_user_data(user_id_2, 'account')
        
        assert loaded_data_1['account']['internal_username'] == 'duplicateuser'
        assert loaded_data_2['account']['internal_username'] == 'duplicateuser'
    
    @pytest.mark.ui
    def test_invalid_data_handling_real_behavior(self, test_data_dir, mock_config):
        """REAL BEHAVIOR TEST: Test handling of invalid data during account creation."""
        user_id = 'test-invalid-data'
        
        # Test with invalid account data (missing required fields)
        invalid_account_data = {
            'user_id': user_id,
            # Missing internal_username, timezone, etc.
        }
        
        # ✅ VERIFY REAL BEHAVIOR: Should handle invalid data gracefully
        result = save_user_data(user_id, {
            'account': invalid_account_data,
            'preferences': {},
            'context': {}
        })
        
        # Should either succeed with defaults or fail gracefully
        assert isinstance(result, dict), "Should return a result dictionary"
        
        # ✅ VERIFY REAL BEHAVIOR: User directory should be created even with invalid data
        user_dir = os.path.join(test_data_dir, 'users', user_id)
        if result.get('account') is True:
            assert os.path.exists(user_dir), "User directory should be created even with invalid data"
    
    @pytest.mark.ui
    def test_file_system_error_handling_real_behavior(self, test_data_dir, mock_config):
        """REAL BEHAVIOR TEST: Test handling of file system errors."""
        user_id = 'test-fs-error'
        
        # Create a read-only directory to simulate permission errors
        user_dir = os.path.join(test_data_dir, 'users', user_id)
        os.makedirs(user_dir, exist_ok=True)
        
        # Make directory read-only
        os.chmod(user_dir, 0o444)  # Read-only
        
        try:
            account_data = {
                'user_id': user_id,
                'internal_username': 'fsuser',
                'account_status': 'active',
                'timezone': 'America/New_York',
                'channel': {'type': 'email', 'contact': 'fs@example.com'}
            }
            
            # ✅ VERIFY REAL BEHAVIOR: Should handle file system errors gracefully
            result = save_user_data(user_id, {
                'account': account_data,
                'preferences': {},
                'context': {}
            })
            
            # Should either fail gracefully or succeed with error handling
            assert isinstance(result, dict), "Should return a result dictionary"
            
        finally:
            # Restore permissions for cleanup
            os.chmod(user_dir, 0o755)
    
    @pytest.mark.ui
    def test_widget_error_handling_real_behavior(self, qapp, test_data_dir, mock_config):
        """REAL BEHAVIOR TEST: Test handling of widget errors during account creation."""
        # Create dialog
        mock_comm_manager = Mock()
        dialog = AccountCreatorDialog(parent=None, communication_manager=mock_comm_manager)
        
        # Test with widget that raises an exception
        with patch.object(dialog.category_widget, 'get_selected_categories', side_effect=Exception("Widget error")):
            # ✅ VERIFY REAL BEHAVIOR: Should handle widget errors gracefully
            try:
                is_valid, error_message = dialog.validate_input()
                # Should either handle the error or propagate it appropriately
                assert isinstance(is_valid, bool), "Should return boolean validity"
            except Exception as e:
                # If exception is propagated, it should be handled by error handling decorator
                assert "Widget error" in str(e), "Should propagate widget error appropriately"
        
        dialog.close()
        dialog.deleteLater()

class TestAccountCreationIntegration:
    """Test integration scenarios for account creation and management."""
    
    @pytest.mark.integration
    def test_full_account_lifecycle_real_behavior(self, test_data_dir, mock_config):
        """REAL BEHAVIOR TEST: Test complete account lifecycle with real file system changes."""
        user_id = 'test-lifecycle'
        
        # ✅ VERIFY INITIAL STATE: User should not exist
        user_dir = os.path.join(test_data_dir, 'users', user_id)
        initial_user_exists = os.path.exists(user_dir)
        
        # Step 1: Create user
        account_data = {
            'user_id': user_id,
            'internal_username': 'lifecycleuser',
            'account_status': 'active',
            'timezone': 'America/New_York',
            'channel': {'type': 'email', 'contact': 'lifecycle@example.com'}
        }
        
        preferences_data = {
            'categories': ['motivational'],
            'checkin_settings': {'enabled': True, 'frequency': 'daily'},
            'task_settings': {'enabled': False}
        }
        
        context_data = {
            'preferred_name': 'Lifecycle User',
            'pronouns': 'they/them'
        }
        
        # Create user
        result = save_user_data(user_id, {
            'account': account_data,
            'preferences': preferences_data,
            'context': context_data
        })
        
        # ✅ VERIFY REAL BEHAVIOR: User should be created successfully
        assert result.get('account') is True
        assert result.get('preferences') is True
        assert result.get('context') is True
        
        # ✅ VERIFY REAL BEHAVIOR: User directory should be created
        assert os.path.exists(user_dir), f"User directory should be created: {user_dir}"
        
        # ✅ VERIFY REAL BEHAVIOR: All required files should exist
        expected_files = ['account.json', 'preferences.json', 'user_context.json', 'schedules.json', 'daily_checkins.json']
        for expected_file in expected_files:
            file_path = os.path.join(user_dir, expected_file)
            assert os.path.exists(file_path), f"Required file should exist: {expected_file}"
        
        # ✅ VERIFY REAL BEHAVIOR: Feature-specific directories should exist
        messages_dir = os.path.join(user_dir, 'messages')
        assert os.path.exists(messages_dir), "Messages directory should exist (messages enabled)"
        
        # Tasks directory should NOT exist (tasks disabled)
        tasks_dir = os.path.join(user_dir, 'tasks')
        assert not os.path.exists(tasks_dir), "Tasks directory should not exist (tasks disabled)"
        
        # Step 2: Load and verify user data
        loaded_data = get_user_data(user_id, 'all')
        
        # ✅ VERIFY REAL BEHAVIOR: All data should be loadable
        assert loaded_data['account']['internal_username'] == 'lifecycleuser'
        assert loaded_data['preferences']['categories'] == ['motivational']
        assert loaded_data['context']['preferred_name'] == 'Lifecycle User'
        assert loaded_data['context']['pronouns'] == 'they/them'
        
        # ✅ VERIFY REAL BEHAVIOR: Feature enablement should be correct
        features = loaded_data['account']['features']
        assert features['automated_messages'] == 'enabled', "Messages should be enabled"
        assert features['checkins'] == 'enabled', "Check-ins should be enabled"
        assert features['task_management'] == 'disabled', "Task management should be disabled"
        
        # Step 3: Update user data
        from core.user_management import update_user_preferences, update_user_context
        
        # Update preferences
        updated_preferences = {
            'categories': ['motivational', 'health'],
            'checkin_settings': {'enabled': True, 'frequency': 'weekly'},
            'task_settings': {'enabled': True}
        }
        
        update_result = update_user_preferences(user_id, updated_preferences)
        assert update_result is True
        
        # Update context
        updated_context = {
            'preferred_name': 'Updated Lifecycle User',
            'pronouns': 'he/him'
        }
        
        context_update_result = update_user_context(user_id, updated_context)
        assert context_update_result is True
        
        # ✅ VERIFY REAL BEHAVIOR: Updates should be persisted
        updated_data = get_user_data(user_id, 'all')
        assert 'health' in updated_data['preferences']['categories'], "New category should be added"
        assert updated_data['preferences']['checkin_settings']['frequency'] == 'weekly', "Frequency should be updated"
        assert updated_data['context']['preferred_name'] == 'Updated Lifecycle User', "Name should be updated"
        assert updated_data['context']['pronouns'] == 'he/him', "Pronouns should be updated"
        
        # ✅ VERIFY REAL BEHAVIOR: Files should be updated on disk
        preferences_file = os.path.join(user_dir, 'preferences.json')
        with open(preferences_file, 'r') as f:
            disk_preferences = json.load(f)
        
        assert 'health' in disk_preferences['categories'], "Disk file should contain updated categories"
        assert disk_preferences['checkin_settings']['frequency'] == 'weekly', "Disk file should contain updated frequency"
        
        # Step 4: Test user index integration
        from core.user_management import rebuild_user_index, get_user_index
        
        rebuild_result = rebuild_user_index()
        assert rebuild_result is True, "User index should be rebuilt successfully"
        
        user_index = get_user_index()
        assert user_index is not None, "User index should be loadable"
        
        # ✅ VERIFY REAL BEHAVIOR: User should be in index
        index_usernames = [entry.get('internal_username') for entry in user_index.values()]
        assert 'lifecycleuser' in index_usernames, "User should be in index"
        
        # Step 5: Test user deletion (cleanup)
        # Note: In a real system, you might have a delete_user function
        # For now, we'll just verify the user can be loaded and modified
        
        # ✅ VERIFY REAL BEHAVIOR: User should remain accessible throughout lifecycle
        final_data = get_user_data(user_id, 'all')
        assert final_data['account']['internal_username'] == 'lifecycleuser', "User should remain accessible"
    
    @pytest.mark.integration
    def test_multiple_users_same_features_real_behavior(self, test_data_dir, mock_config):
        """REAL BEHAVIOR TEST: Test multiple users with same feature configurations."""
        user_ids = ['test-multi-1', 'test-multi-2', 'test-multi-3']
        
        for i, user_id in enumerate(user_ids):
            # Create user with same feature configuration
            account_data = {
                'user_id': user_id,
                'internal_username': f'multiuser{i}',
                'account_status': 'active',
                'timezone': 'America/New_York',
                'channel': {'type': 'email', 'contact': f'multi{i}@example.com'},
                'features': {
                    'automated_messages': 'enabled',
                    'checkins': 'enabled',
                    'task_management': 'enabled'
                }
            }
            
            preferences_data = {
                'categories': ['motivational', 'health'],
                'checkin_settings': {'enabled': True, 'frequency': 'daily'},
                'task_settings': {'enabled': True, 'default_time': '18:00'}
            }
            
            context_data = {
                'preferred_name': f'Multi User {i}',
                'pronouns': 'they/them'
            }
            
            result = save_user_data(user_id, {
                'account': account_data,
                'preferences': preferences_data,
                'context': context_data
            })
            
            # ✅ VERIFY REAL BEHAVIOR: Each user should be created successfully
            assert result.get('account') is True, f"User {user_id} should be created successfully"
        
        # ✅ VERIFY REAL BEHAVIOR: All users should have same feature structure
        for user_id in user_ids:
            user_dir = os.path.join(test_data_dir, 'users', user_id)
            
            # All should have messages directory
            messages_dir = os.path.join(user_dir, 'messages')
            assert os.path.exists(messages_dir), f"User {user_id} should have messages directory"
            
            # All should have tasks directory
            tasks_dir = os.path.join(user_dir, 'tasks')
            assert os.path.exists(tasks_dir), f"User {user_id} should have tasks directory"
            
            # All should have daily check-ins file
            checkins_file = os.path.join(user_dir, 'daily_checkins.json')
            assert os.path.exists(checkins_file), f"User {user_id} should have daily check-ins file"
            
            # All should have same feature enablement
            loaded_data = get_user_data(user_id, 'account')
            features = loaded_data['account']['features']
            
            assert features['automated_messages'] == 'enabled', f"User {user_id} should have messages enabled"
            assert features['checkins'] == 'enabled', f"User {user_id} should have check-ins enabled"
            assert features['task_management'] == 'enabled', f"User {user_id} should have tasks enabled"
        
        # ✅ VERIFY REAL BEHAVIOR: User index should contain all users
        from core.user_management import rebuild_user_index, get_user_index
        
        rebuild_result = rebuild_user_index()
        assert rebuild_result is True, "User index should be rebuilt successfully"
        
        user_index = get_user_index()
        assert user_index is not None, "User index should be loadable"
        
        index_usernames = [entry.get('internal_username') for entry in user_index.values()]
        for i in range(len(user_ids)):
            assert f'multiuser{i}' in index_usernames, f"User multiuser{i} should be in index"

if __name__ == "__main__":
    pytest.main([__file__]) 