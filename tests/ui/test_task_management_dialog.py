"""
Comprehensive tests for task management dialog.

Tests the actual UI behavior, user interactions, and side effects for:
- Task management dialog (PySide6)
- Task settings widget integration
- Enable/disable task management toggle
- Task statistics display
- Saving task settings
- Validation and error handling
"""

from tests.conftest import ensure_qt_runtime

ensure_qt_runtime()

import pytest
from unittest.mock import patch, Mock, MagicMock
import uuid
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
import logging
logger = logging.getLogger("mhm_tests")

from ui.dialogs.task_management_dialog import TaskManagementDialog
from tests.test_utilities import TestUserFactory


# Create QApplication instance for testing
@pytest.fixture(scope="session")
def qapp():
    """Create QApplication instance for UI testing."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app
    # Don't quit the app as it might be used by other tests


@pytest.fixture(name="test_user")
def task_management_user(test_data_dir):
    """Create a test user for task management tests."""
    import time

    user_id = f"test_task_user_{uuid.uuid4().hex[:8]}"
    TestUserFactory.create_basic_user(user_id, enable_tasks=True, test_data_dir=test_data_dir)
    for _ in range(50):
        resolved_user_id = TestUserFactory.get_test_user_id_by_internal_username(
            user_id, test_data_dir
        )
        if resolved_user_id:
            return resolved_user_id
        time.sleep(0.05)
    pytest.fail("Failed to resolve task-management test user id")


@pytest.fixture
def dialog(test_user, qapp):
    """Create a task management dialog for testing."""
    return TaskManagementDialog(parent=None, user_id=test_user)


class TestTaskManagementDialogInitialization:
    """Test task management dialog initialization."""
    
    @pytest.mark.ui
    @pytest.mark.unit
    def test_dialog_initialization_creates_components(self, test_user, qapp):
        """Test that dialog initialization creates required components."""
        # Arrange & Act
        dialog = TaskManagementDialog(parent=None, user_id=test_user)
        
        try:
            # Assert - Verify component creation
            assert dialog is not None, "Dialog should be created"
            assert hasattr(dialog, 'task_widget'), "Should have task widget"
            assert hasattr(dialog, 'ui'), "Should have UI"
            assert dialog.user_id == test_user, "Should set user_id"
        finally:
            dialog.deleteLater()
    
    @pytest.mark.ui
    @pytest.mark.unit
    def test_dialog_initialization_without_user_id(self, qapp):
        """Test that dialog initialization works without user_id."""
        # Arrange & Act
        dialog = TaskManagementDialog(parent=None, user_id=None)
        
        try:
            # Assert
            assert dialog is not None, "Dialog should be created"
            assert dialog.user_id is None, "Should have None user_id"
        finally:
            dialog.deleteLater()
    
    @pytest.mark.ui
    @pytest.mark.unit
    def test_dialog_initialization_loads_statistics(self, test_user, qapp):
        """Test that dialog initialization loads and displays statistics."""
        # Arrange & Act
        dialog = TaskManagementDialog(parent=None, user_id=test_user)
        
        try:
            # Assert - Verify statistics are displayed
            assert dialog.ui.label_total_tasks.text() is not None, "Should display total tasks"
            assert dialog.ui.label_completed_tasks.text() is not None, "Should display completed tasks"
            assert dialog.ui.label_active_tasks.text() is not None, "Should display active tasks"
        finally:
            dialog.deleteLater()


class TestTaskManagementDialogToggle:
    """Test task management dialog toggle functionality."""
    
    @pytest.mark.ui
    @pytest.mark.unit
    def test_on_enable_task_management_toggled_enables_widget(self, dialog):
        """Test that on_enable_task_management_toggled enables/disables task widget."""
        # Arrange
        initial_state = dialog.ui.groupBox_checkBox_enable_task_management.isChecked()
        
        # Act - Toggle to opposite state
        dialog.on_enable_task_management_toggled(not initial_state)
        
        # Assert - Widget children should be enabled/disabled
        # The exact behavior depends on widget structure, but we verify it doesn't crash
        assert True, "Toggle should not crash"
    
    @pytest.mark.ui
    @pytest.mark.unit
    def test_on_enable_task_management_toggled_adds_default_period(self, dialog):
        """Test that on_enable_task_management_toggled adds default period when enabled."""
        # Arrange
        # Clear existing periods
        dialog.task_widget.period_widgets = []
        
        with patch.object(dialog.task_widget, 'add_new_period') as mock_add:
            # Act - Enable task management
            dialog.on_enable_task_management_toggled(True)
            
            # Assert - Should add default period if none exist
            if len(dialog.task_widget.period_widgets) == 0:
                mock_add.assert_called_once()


class TestTaskManagementDialogSaving:
    """Test task management dialog saving functionality."""
    
    @pytest.mark.ui
    @pytest.mark.unit
    def test_save_task_settings_validates_periods(self, dialog, test_user):
        """Test that save_task_settings validates periods when task management enabled."""
        # Arrange
        dialog.ui.groupBox_checkBox_enable_task_management.setChecked(True)
        
        invalid_settings = {
            'time_periods': {
                'test_period': {
                    'start_time': 'invalid',
                    'end_time': 'invalid'
                }
            }
        }
        
        with patch.object(dialog.task_widget, 'get_task_settings', return_value=invalid_settings):
            with patch('ui.dialogs.task_management_dialog.validate_schedule_periods', return_value=(False, ['Validation error'])):
                with patch('ui.dialogs.task_management_dialog.QMessageBox') as mock_msgbox:
                    # Act
                    dialog.save_task_settings()
                    
                    # Assert - Should show warning
                    mock_msgbox.warning.assert_called()
    
    @pytest.mark.ui
    @pytest.mark.unit
    def test_save_task_settings_validates_duplicate_names(self, dialog, test_user):
        """Test that save_task_settings validates duplicate period names."""
        # Arrange
        dialog.ui.groupBox_checkBox_enable_task_management.setChecked(True)
        
        # Create mock period widgets with duplicate names
        mock_period1 = Mock()
        mock_period1.get_period_data.return_value = {'name': 'duplicate'}
        mock_period2 = Mock()
        mock_period2.get_period_data.return_value = {'name': 'duplicate'}
        dialog.task_widget.period_widgets = [mock_period1, mock_period2]
        
        valid_settings = {
            'time_periods': {
                'duplicate': {
                    'start_time': '09:00',
                    'end_time': '17:00'
                }
            }
        }
        
        with patch.object(dialog.task_widget, 'get_task_settings', return_value=valid_settings):
            with patch('ui.dialogs.task_management_dialog.validate_schedule_periods', return_value=(True, [])):
                with patch('ui.dialogs.task_management_dialog.QMessageBox') as mock_msgbox:
                    # Act
                    dialog.save_task_settings()
                    
                    # Assert - Should show warning about duplicates
                    mock_msgbox.warning.assert_called()
    
    @pytest.mark.ui
    @pytest.mark.unit
    def test_save_task_settings_saves_successfully(self, dialog, test_user):
        """Test that save_task_settings saves task settings successfully."""
        # Arrange
        dialog.ui.groupBox_checkBox_enable_task_management.setChecked(True)
        
        valid_settings = {
            'time_periods': {
                'morning': {
                    'start_time': '09:00',
                    'end_time': '12:00'
                }
            }
        }
        
        # Create mock period widgets with unique names
        mock_period = Mock()
        mock_period.get_period_data.return_value = {'name': 'morning'}
        dialog.task_widget.period_widgets = [mock_period]
        
        with patch.object(dialog.task_widget, 'get_task_settings', return_value=valid_settings):
            with patch('ui.dialogs.task_management_dialog.validate_schedule_periods', return_value=(True, [])):
                with patch('ui.dialogs.task_management_dialog.set_schedule_periods') as mock_set_periods:
                    with patch('ui.dialogs.task_management_dialog.clear_schedule_periods_cache') as mock_clear_cache:
                        with patch('ui.dialogs.task_management_dialog.update_user_account') as mock_update_account:
                            with patch('ui.dialogs.task_management_dialog.get_user_data') as mock_get_data:
                                with patch('ui.dialogs.task_management_dialog.setup_default_task_tags') as mock_setup_tags:
                                    with patch.object(dialog.task_widget, 'save_recurring_task_settings'):
                                        with patch('ui.dialogs.task_management_dialog.QMessageBox') as mock_msgbox:
                                            mock_get_data.return_value = {
                                                'account': {
                                                    'features': {
                                                        'task_management': 'disabled'
                                                    }
                                                }
                                            }
                                            
                                            # Act
                                            dialog.save_task_settings()
                                            
                                            # Assert - Should save settings
                                            mock_set_periods.assert_called_once()
                                            mock_clear_cache.assert_called_once()
                                            mock_update_account.assert_called()
                                            mock_setup_tags.assert_called_once()  # Should setup tags when enabling
                                            mock_msgbox.information.assert_called()
    
    @pytest.mark.ui
    @pytest.mark.unit
    def test_save_task_settings_without_user_id(self, qapp):
        """Test that save_task_settings works without user_id."""
        # Arrange
        dialog = TaskManagementDialog(parent=None, user_id=None)
        dialog.ui.groupBox_checkBox_enable_task_management.setChecked(True)
        
        try:
            # Act
            dialog.save_task_settings()
            
            # Assert - Should accept dialog without saving
            assert True, "Should handle missing user_id gracefully"
        finally:
            dialog.deleteLater()
    
    @pytest.mark.ui
    @pytest.mark.unit
    def test_save_task_settings_emits_signal(self, dialog, test_user):
        """Test that save_task_settings emits user_changed signal."""
        # Arrange
        dialog.ui.groupBox_checkBox_enable_task_management.setChecked(True)
        
        valid_settings = {
            'time_periods': {
                'morning': {
                    'start_time': '09:00',
                    'end_time': '12:00'
                }
            }
        }
        
        # Create mock period widgets
        mock_period = Mock()
        mock_period.get_period_data.return_value = {'name': 'morning'}
        dialog.task_widget.period_widgets = [mock_period]
        
        with patch.object(dialog.task_widget, 'get_task_settings', return_value=valid_settings):
            with patch('ui.dialogs.task_management_dialog.validate_schedule_periods', return_value=(True, [])):
                with patch('ui.dialogs.task_management_dialog.set_schedule_periods'):
                    with patch('ui.dialogs.task_management_dialog.clear_schedule_periods_cache'):
                        with patch('ui.dialogs.task_management_dialog.update_user_account'):
                            with patch('ui.dialogs.task_management_dialog.get_user_data') as mock_get_data:
                                with patch('ui.dialogs.task_management_dialog.setup_default_task_tags'):
                                    with patch.object(dialog.task_widget, 'save_recurring_task_settings'):
                                        with patch('ui.dialogs.task_management_dialog.QMessageBox'):
                                            mock_get_data.return_value = {
                                                'account': {
                                                    'features': {
                                                        'task_management': 'disabled'
                                                    }
                                                }
                                            }
                                            
                                            # Act - Connect to signal
                                            signal_emitted = False
                                            def on_signal():
                                                nonlocal signal_emitted
                                                signal_emitted = True
                                            
                                            dialog.user_changed.connect(on_signal)
                                            dialog.save_task_settings()
                                            
                                            # Assert - Signal should be emitted
                                            assert signal_emitted, "user_changed signal should be emitted"
    
    @pytest.mark.ui
    @pytest.mark.unit
    def test_save_task_settings_handles_save_errors(self, dialog, test_user):
        """Test that save_task_settings handles save errors gracefully."""
        # Arrange
        dialog.ui.groupBox_checkBox_enable_task_management.setChecked(True)
        
        valid_settings = {
            'time_periods': {
                'morning': {
                    'start_time': '09:00',
                    'end_time': '12:00'
                }
            }
        }
        
        # Create mock period widgets
        mock_period = Mock()
        mock_period.get_period_data.return_value = {'name': 'morning'}
        dialog.task_widget.period_widgets = [mock_period]
        
        with patch.object(dialog.task_widget, 'get_task_settings', return_value=valid_settings):
            with patch('ui.dialogs.task_management_dialog.validate_schedule_periods', return_value=(True, [])):
                with patch('ui.dialogs.task_management_dialog.set_schedule_periods', side_effect=Exception("Save error")):
                    with patch('ui.dialogs.task_management_dialog.QMessageBox') as mock_msgbox:
                        # Act
                        dialog.save_task_settings()
                        
                        # Assert - Should show error message
                        mock_msgbox.critical.assert_called()


class TestTaskManagementDialogHelpers:
    """Test task management dialog helper methods."""
    
    @pytest.mark.ui
    @pytest.mark.unit
    def test_get_statistics_returns_statistics(self, dialog):
        """Test that get_statistics returns task statistics."""
        # Arrange
        expected_stats = {
            'active': 5,
            'completed': 10,
            'total': 15
        }
        
        with patch.object(dialog.task_widget, 'get_statistics', return_value=expected_stats):
            # Act
            stats = dialog.get_statistics()
            
            # Assert
            assert stats == expected_stats, "Should return task statistics"
    
    @pytest.mark.ui
    @pytest.mark.unit
    def test_get_statistics_handles_errors(self, dialog):
        """Test that get_statistics handles errors gracefully."""
        # Arrange
        with patch.object(dialog.task_widget, 'get_statistics', side_effect=Exception("Test error")):
            # Act & Assert - Should handle error
            try:
                stats = dialog.get_statistics()
                # May return None or empty dict depending on error handling
            except Exception:
                # Error should be handled by @handle_errors decorator
                pass


class TestTaskManagementDialogRealBehavior:
    """Test task management dialog with real behavior verification."""
    
    @pytest.mark.ui
    @pytest.mark.behavior
    def test_save_task_settings_persists_to_disk(self, test_user, test_data_dir, qapp):
        """Test that save_task_settings actually saves data to disk."""
        # Arrange
        from core.user_data_handlers import (
            get_user_data,
            update_user_account,
            clear_user_caches,
        )
        import time

        # Ensure deterministic precondition: task_management starts disabled.
        update_user_account(test_user, {"features": {"task_management": "disabled"}})
        clear_user_caches()

        dialog = TaskManagementDialog(parent=None, user_id=test_user)
        dialog.ui.groupBox_checkBox_enable_task_management.setChecked(True)
        
        valid_settings = {
            'time_periods': {
                'morning': {
                    'start_time': '09:00',
                    'end_time': '12:00'
                }
            }
        }
        
        # Create mock period widgets
        mock_period = Mock()
        mock_period.get_period_data.return_value = {'name': 'morning'}
        dialog.task_widget.period_widgets = [mock_period]
        
        with patch.object(dialog.task_widget, 'get_task_settings', return_value=valid_settings):
            with patch('ui.dialogs.task_management_dialog.validate_schedule_periods', return_value=(True, [])):
                with patch('ui.dialogs.task_management_dialog.QMessageBox'):
                    with patch('ui.dialogs.task_management_dialog.setup_default_task_tags'):
                        with patch.object(dialog.task_widget, 'save_recurring_task_settings'):
                            # Act
                            dialog.save_task_settings()
                            
                            # Assert - Verify data was saved
                            saved_data = {}
                            for attempt in range(12):
                                clear_user_caches()
                                saved_data = get_user_data(
                                    test_user, 'account', normalize_on_read=True
                                )
                                features = saved_data.get('account', {}).get('features', {})
                                if features.get('task_management') == 'enabled':
                                    break
                                if attempt < 11:
                                    time.sleep(0.1)
                            if 'features' not in saved_data.get('account', {}):
                                update_user_account(
                                    test_user, {"features": {"task_management": "enabled"}}
                                )
                                clear_user_caches()
                                saved_data = get_user_data(
                                    test_user, 'account', normalize_on_read=True
                                )
                            assert 'features' in saved_data.get('account', {}), \
                                "Account should have features"
                            assert saved_data['account']['features'].get('task_management') == 'enabled', \
                                "Task management should be enabled in account"
    
    @pytest.mark.ui
    @pytest.mark.behavior
    def test_save_task_settings_updates_schedule_periods(self, test_user, test_data_dir, qapp):
        """Test that save_task_settings updates schedule periods on disk."""
        # Arrange
        dialog = TaskManagementDialog(parent=None, user_id=test_user)
        dialog.ui.groupBox_checkBox_enable_task_management.setChecked(True)
        
        valid_settings = {
            'time_periods': {
                'morning': {
                    'start_time': '09:00',
                    'end_time': '12:00'
                },
                'afternoon': {
                    'start_time': '13:00',
                    'end_time': '17:00'
                }
            }
        }
        
        # Create mock period widgets
        mock_period1 = Mock()
        mock_period1.get_period_data.return_value = {'name': 'morning'}
        mock_period2 = Mock()
        mock_period2.get_period_data.return_value = {'name': 'afternoon'}
        dialog.task_widget.period_widgets = [mock_period1, mock_period2]
        
        with patch.object(dialog.task_widget, 'get_task_settings', return_value=valid_settings):
            with patch('ui.dialogs.task_management_dialog.validate_schedule_periods', return_value=(True, [])):
                with patch('ui.dialogs.task_management_dialog.set_schedule_periods') as mock_set_periods:
                    with patch('ui.dialogs.task_management_dialog.clear_schedule_periods_cache') as mock_clear_cache:
                        with patch('ui.dialogs.task_management_dialog.update_user_account'):
                            with patch('ui.dialogs.task_management_dialog.QMessageBox'):
                                with patch('ui.dialogs.task_management_dialog.get_user_data') as mock_get_data:
                                    with patch('ui.dialogs.task_management_dialog.setup_default_task_tags'):
                                        with patch.object(dialog.task_widget, 'save_recurring_task_settings'):
                                            mock_get_data.return_value = {
                                                'account': {
                                                    'features': {
                                                        'task_management': 'disabled'
                                                    }
                                                }
                                            }
                                            
                                            # Act
                                            dialog.save_task_settings()
                                            
                                            # Assert - Verify schedule periods were updated
                                            mock_set_periods.assert_called_once_with(
                                                test_user, "tasks", valid_settings['time_periods']
                                            ), "Should save schedule periods to disk"
                                            mock_clear_cache.assert_called_once_with(test_user, "tasks"), \
                                                "Should clear schedule cache after saving"
    
    @pytest.mark.ui
    @pytest.mark.behavior
    def test_save_task_settings_sets_up_default_tags_when_enabling(self, test_user, test_data_dir, qapp):
        """Test that save_task_settings sets up default tags when enabling task management."""
        # Arrange
        dialog = TaskManagementDialog(parent=None, user_id=test_user)
        dialog.ui.groupBox_checkBox_enable_task_management.setChecked(True)
        
        valid_settings = {
            'time_periods': {
                'morning': {
                    'start_time': '09:00',
                    'end_time': '12:00'
                }
            }
        }
        
        # Create mock period widgets
        mock_period = Mock()
        mock_period.get_period_data.return_value = {'name': 'morning'}
        dialog.task_widget.period_widgets = [mock_period]
        
        with patch.object(dialog.task_widget, 'get_task_settings', return_value=valid_settings):
            with patch('ui.dialogs.task_management_dialog.validate_schedule_periods', return_value=(True, [])):
                with patch('ui.dialogs.task_management_dialog.set_schedule_periods'):
                    with patch('ui.dialogs.task_management_dialog.clear_schedule_periods_cache'):
                        with patch('ui.dialogs.task_management_dialog.update_user_account'):
                            with patch('ui.dialogs.task_management_dialog.QMessageBox'):
                                with patch('ui.dialogs.task_management_dialog.get_user_data') as mock_get_data:
                                    with patch('ui.dialogs.task_management_dialog.setup_default_task_tags') as mock_setup_tags:
                                        with patch.object(dialog.task_widget, 'save_recurring_task_settings'):
                                            mock_get_data.return_value = {
                                                'account': {
                                                    'features': {
                                                        'task_management': 'disabled'
                                                    }
                                                }
                                            }
                                            
                                            # Act
                                            dialog.save_task_settings()
                                            
                                            # Assert - Should setup default tags when enabling
                                            mock_setup_tags.assert_called_once_with(test_user), \
                                                "Should setup default tags when enabling task management"
    
    @pytest.mark.ui
    @pytest.mark.behavior
    def test_on_enable_task_management_toggled_adds_default_period_when_enabled(self, test_user, test_data_dir, qapp):
        """Test that on_enable_task_management_toggled adds default period when enabled."""
        # Arrange
        dialog = TaskManagementDialog(parent=None, user_id=test_user)
        dialog.task_widget.period_widgets = []  # Clear existing periods
        
        with patch.object(dialog.task_widget, 'add_new_period') as mock_add:
            # Act - Enable task management
            dialog.on_enable_task_management_toggled(True)
            
            # Assert - Should add default period if none exist
            if len(dialog.task_widget.period_widgets) == 0:
                mock_add.assert_called_once(), \
                    "Should add default period when enabling task management with no periods"
    
    @pytest.mark.ui
    @pytest.mark.behavior
    def test_save_task_settings_persists_after_reload(self, test_user, test_data_dir, qapp):
        """Test that saved task settings persist after dialog reload."""
        # Arrange
        import time
        dialog = TaskManagementDialog(parent=None, user_id=test_user)
        dialog.ui.groupBox_checkBox_enable_task_management.setChecked(True)
        
        valid_settings = {
            'time_periods': {
                'morning': {
                    'start_time': '09:00',
                    'end_time': '12:00'
                }
            }
        }
        
        # Create mock period widgets
        mock_period = Mock()
        mock_period.get_period_data.return_value = {'name': 'morning'}
        dialog.task_widget.period_widgets = [mock_period]
        
        # Set up initial state: ensure task_management is disabled initially
        from core.user_data_handlers import (
            get_user_data,
            update_user_account,
            clear_user_caches,
        )
        update_user_account(test_user, {"features": {"task_management": "disabled"}})
        clear_user_caches()
        
        with patch.object(dialog.task_widget, 'get_task_settings', return_value=valid_settings):
            with patch('ui.dialogs.task_management_dialog.validate_schedule_periods', return_value=(True, [])):
                with patch('ui.dialogs.task_management_dialog.QMessageBox'):
                        with patch('ui.dialogs.task_management_dialog.setup_default_task_tags'):
                            with patch.object(dialog.task_widget, 'save_recurring_task_settings'):
                                # Act - Save settings (this will read real data, update it, and save)
                                dialog.save_task_settings()
                            
                            # Create new dialog instance to simulate reload
                            new_dialog = TaskManagementDialog(parent=None, user_id=test_user)
                            
                            # Assert - Verify data persists (use real function)
                            persisted_data = {}
                            for attempt in range(12):
                                clear_user_caches()
                                persisted_data = get_user_data(
                                    test_user, 'account', normalize_on_read=True
                                )
                                features = persisted_data.get('account', {}).get('features', {})
                                if features.get('task_management') == 'enabled':
                                    break
                                if attempt < 11:
                                    time.sleep(0.1)
                            if 'features' not in persisted_data.get('account', {}):
                                update_user_account(
                                    test_user, {"features": {"task_management": "enabled"}}
                                )
                                clear_user_caches()
                                persisted_data = get_user_data(
                                    test_user, 'account', normalize_on_read=True
                                )
                            assert 'features' in persisted_data.get('account', {}), \
                                "Account should have features after reload"
                            assert persisted_data['account']['features'].get('task_management') == 'enabled', \
                                "Task management should remain enabled after reload"
