"""
Check-in Management Dialog Tests

Tests for ui/dialogs/checkin_management_dialog.py:
- CheckinManagementDialog initialization
- UI setup
- Enable/disable checkins toggle
- Loading user checkin data
- Saving checkin settings
- Validation
- Error handling
"""

from tests.conftest import ensure_qt_runtime

ensure_qt_runtime()

import pytest
import uuid
from unittest.mock import patch, Mock, MagicMock
from PySide6.QtWidgets import QApplication, QWidget, QMessageBox
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
import logging
logger = logging.getLogger("mhm_tests")

from ui.dialogs.checkin_management_dialog import CheckinManagementDialog
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


class TestCheckinManagementDialogInitialization:
    """Test CheckinManagementDialog initialization"""
    
    @pytest.mark.ui
    @pytest.mark.unit
    def test_initialization_without_user_id(self, qapp, test_data_dir, mock_config):
        """Test: CheckinManagementDialog initializes correctly without user_id"""
        # Act
        dialog = CheckinManagementDialog()
        
        try:
            # Assert
            assert dialog is not None, "Dialog should be created"
            assert dialog.user_id is None, "Should have None user_id"
            assert dialog.ui is not None, "Should have UI"
            assert dialog.checkin_widget is not None, "Should have checkin widget"
        finally:
            dialog.deleteLater()
    
    @pytest.mark.ui
    @pytest.mark.unit
    def test_initialization_with_user_id(self, qapp, test_data_dir, mock_config):
        """Test: CheckinManagementDialog initializes correctly with user_id"""
        # Arrange
        user_id = "test_checkin_dialog_user"
        TestUserFactory.create_basic_user(user_id, enable_checkins=True, test_data_dir=test_data_dir)
        
        from core.user_data_handlers import (
            get_user_id_by_identifier,
            get_user_data,
            update_user_account,
            clear_user_caches,
        )
        actual_user_id = get_user_id_by_identifier(user_id)
        if actual_user_id is None:
            actual_user_id = user_id
        
        # Act
        dialog = CheckinManagementDialog(user_id=actual_user_id)
        
        try:
            # Assert
            assert dialog is not None, "Dialog should be created"
            assert dialog.user_id == actual_user_id, "Should set user_id"
            assert dialog.checkin_widget is not None, "Should have checkin widget"
        finally:
            dialog.deleteLater()
    
    @pytest.mark.ui
    @pytest.mark.unit
    def test_initialization_with_parent(self, qapp, test_data_dir, mock_config):
        """Test: CheckinManagementDialog initializes correctly with parent"""
        # Arrange
        parent = QWidget()
        
        # Act
        dialog = CheckinManagementDialog(parent=parent)
        
        try:
            # Assert
            assert dialog is not None, "Dialog should be created"
            assert dialog.parent() == parent, "Should set parent"
        finally:
            dialog.deleteLater()
            parent.deleteLater()
    
    @pytest.mark.ui
    @pytest.mark.unit
    def test_initialization_loads_user_data(self, qapp, test_data_dir, mock_config):
        """Test: CheckinManagementDialog loads user data on initialization"""
        # Arrange
        from tests.conftest import wait_until

        user_id = f"test_checkin_dialog_load_user_{uuid.uuid4().hex[:8]}"
        TestUserFactory.create_basic_user(user_id, enable_checkins=True, test_data_dir=test_data_dir)
        
        from core.user_data_handlers import (
            get_user_id_by_identifier,
            get_user_data,
            update_user_account,
            clear_user_caches,
        )
        actual_user_id = None
        for _ in range(40):
            actual_user_id = get_user_id_by_identifier(user_id)
            if actual_user_id is None:
                actual_user_id = TestUserFactory.get_test_user_id_by_internal_username(
                    user_id, test_data_dir
                )
            if actual_user_id:
                break
            import time
            time.sleep(0.05)
        assert actual_user_id, "Expected test user id resolution before dialog init"
        update_user_account(
            actual_user_id, {"features": {"checkins": "enabled"}}, auto_create=True
        )
        assert wait_until(
            lambda: (
                get_user_data(actual_user_id, "account", normalize_on_read=True)
                .get("account", {})
                .get("features", {})
                .get("checkins")
                == "enabled"
            ),
            timeout_seconds=6.0,
            poll_seconds=0.02,
        ), "Expected checkins feature to be enabled for created user"
        clear_user_caches()
        
        # Act
        dialog = CheckinManagementDialog(user_id=actual_user_id)
        
        try:
            # Assert
            # Should load user data and set groupbox checked state
            assert dialog.ui.groupBox_checkBox_enable_checkins.isChecked() == True, "Should enable checkins if user has them enabled"
        finally:
            dialog.deleteLater()
    
    @pytest.mark.ui
    @pytest.mark.unit
    def test_initialization_sets_up_widget(self, qapp, test_data_dir, mock_config):
        """Test: CheckinManagementDialog sets up checkin widget"""
        # Act
        dialog = CheckinManagementDialog()
        
        try:
            # Assert
            assert dialog.checkin_widget is not None, "Should create checkin widget"
            # Widget is added to placeholder widget's layout
            layout = dialog.ui.widget_placeholder_checkin_settings.layout()
            assert layout is not None, "Should have layout"
            assert layout.count() > 0, "Should add widget to layout"
        finally:
            dialog.deleteLater()


class TestCheckinManagementDialogToggle:
    """Test CheckinManagementDialog enable/disable toggle"""
    
    @pytest.fixture
    def dialog(self, qapp, test_data_dir, mock_config):
        """Create CheckinManagementDialog instance for testing"""
        dialog = CheckinManagementDialog()
        yield dialog
        dialog.deleteLater()
    
    @pytest.mark.ui
    @pytest.mark.unit
    def test_on_enable_checkins_toggled_enables_widgets(self, dialog):
        """Test: on_enable_checkins_toggled enables child widgets when checked"""
        # Arrange
        dialog.ui.groupBox_checkBox_enable_checkins.setChecked(False)
        
        # Act
        dialog.on_enable_checkins_toggled(True)
        
        # Assert
        # Child widgets should be enabled
        for child in dialog.ui.groupBox_checkBox_enable_checkins.findChildren(QWidget):
            if child is not dialog.ui.groupBox_checkBox_enable_checkins:
                assert child.isEnabled(), "Should enable child widgets"
    
    @pytest.mark.ui
    @pytest.mark.unit
    def test_on_enable_checkins_toggled_disables_widgets(self, dialog):
        """Test: on_enable_checkins_toggled disables child widgets when unchecked"""
        # Arrange
        dialog.ui.groupBox_checkBox_enable_checkins.setChecked(True)
        
        # Act
        dialog.on_enable_checkins_toggled(False)
        
        # Assert
        # Child widgets should be disabled
        for child in dialog.ui.groupBox_checkBox_enable_checkins.findChildren(QWidget):
            if child is not dialog.ui.groupBox_checkBox_enable_checkins:
                assert not child.isEnabled(), "Should disable child widgets"
    
    @pytest.mark.ui
    @pytest.mark.unit
    def test_on_enable_checkins_toggled_creates_default_period(self, dialog):
        """Test: on_enable_checkins_toggled creates default period when enabled with no periods"""
        # Arrange
        dialog.ui.groupBox_checkBox_enable_checkins.setChecked(False)
        dialog.checkin_widget.period_widgets = []  # No periods
        
        # Act
        dialog.on_enable_checkins_toggled(True)
        
        # Assert
        # Should create default period
        assert len(dialog.checkin_widget.period_widgets) > 0, "Should create default period"
    
    @pytest.mark.ui
    @pytest.mark.unit
    def test_on_enable_checkins_toggled_does_not_create_period_if_exists(self, dialog):
        """Test: on_enable_checkins_toggled does not create period if periods already exist"""
        # Arrange
        dialog.ui.groupBox_checkBox_enable_checkins.setChecked(False)
        # Add a period widget
        from ui.widgets.period_row_widget import PeriodRowWidget
        period_widget = PeriodRowWidget(dialog.checkin_widget)
        dialog.checkin_widget.period_widgets = [period_widget]
        initial_count = len(dialog.checkin_widget.period_widgets)
        
        # Act
        dialog.on_enable_checkins_toggled(True)
        
        # Assert
        # Should not create additional period
        assert len(dialog.checkin_widget.period_widgets) == initial_count, "Should not create additional period"


class TestCheckinManagementDialogData:
    """Test CheckinManagementDialog data methods"""
    
    @pytest.fixture
    def dialog(self, qapp, test_data_dir, mock_config):
        """Create CheckinManagementDialog instance for testing"""
        user_id = "test_checkin_dialog_data"
        TestUserFactory.create_basic_user(user_id, enable_checkins=True, test_data_dir=test_data_dir)
        
        from core.user_data_handlers import get_user_id_by_identifier
        actual_user_id = get_user_id_by_identifier(user_id)
        if actual_user_id is None:
            actual_user_id = user_id
        
        dialog = CheckinManagementDialog(user_id=actual_user_id)
        yield dialog
        dialog.deleteLater()
    
    @pytest.mark.ui
    @pytest.mark.unit
    def test_load_user_checkin_data_without_user_id(self, qapp, test_data_dir, mock_config):
        """Test: load_user_checkin_data returns early without user_id"""
        # Arrange
        dialog = CheckinManagementDialog()
        
        try:
            # Act
            dialog.load_user_checkin_data()
            
            # Assert
            # Should return early without error
            assert True, "Should return early without error"
        finally:
            dialog.deleteLater()
    
    @pytest.mark.ui
    @pytest.mark.unit
    def test_load_user_checkin_data_loads_settings(self, dialog):
        """Test: load_user_checkin_data loads user checkin settings"""
        # Arrange
        test_settings = {
            'time_periods': {
                'morning': {'name': 'Morning', 'time': '09:00'}
            },
            'questions': {'mood': 'How are you feeling?'}
        }
        
        with patch('ui.dialogs.checkin_management_dialog.get_user_data') as mock_get:
            mock_get.return_value = {
                'preferences': {
                    'checkin_settings': test_settings
                }
            }
            
            with patch.object(dialog.checkin_widget, 'set_checkin_settings') as mock_set:
                # Act
                dialog.load_user_checkin_data()
                
                # Assert
                mock_set.assert_called_once_with(test_settings)
    
    @pytest.mark.ui
    @pytest.mark.unit
    def test_get_checkin_settings(self, dialog):
        """Test: get_checkin_settings returns widget settings"""
        # Arrange
        test_settings = {'time_periods': {}, 'questions': {}}
        
        with patch.object(dialog.checkin_widget, 'get_checkin_settings', return_value=test_settings):
            # Act
            result = dialog.get_checkin_settings()
            
            # Assert
            assert result == test_settings, "Should return widget settings"
    
    @pytest.mark.ui
    @pytest.mark.unit
    def test_set_checkin_settings(self, dialog):
        """Test: set_checkin_settings sets widget settings"""
        # Arrange
        test_settings = {'time_periods': {}, 'questions': {}}
        
        with patch.object(dialog.checkin_widget, 'set_checkin_settings') as mock_set:
            # Act
            dialog.set_checkin_settings(test_settings)
            
            # Assert
            mock_set.assert_called_once_with(test_settings)


class TestCheckinManagementDialogSave:
    """Test CheckinManagementDialog save functionality"""
    
    @pytest.fixture
    def dialog(self, qapp, test_data_dir, mock_config):
        """Create CheckinManagementDialog instance for testing"""
        user_id = "test_checkin_dialog_save"
        TestUserFactory.create_basic_user(user_id, enable_checkins=True, test_data_dir=test_data_dir)
        
        from core.user_data_handlers import get_user_id_by_identifier
        actual_user_id = get_user_id_by_identifier(user_id)
        if actual_user_id is None:
            actual_user_id = user_id
        
        dialog = CheckinManagementDialog(user_id=actual_user_id)
        yield dialog
        dialog.deleteLater()
    
    @pytest.mark.ui
    @pytest.mark.unit
    def test_save_checkin_settings_without_user_id(self, qapp, test_data_dir, mock_config):
        """Test: save_checkin_settings accepts dialog without user_id"""
        # Arrange
        dialog = CheckinManagementDialog()
        
        try:
            # Act
            dialog.save_checkin_settings()
            
            # Assert
            # Should accept and close dialog
            assert True, "Should accept dialog without user_id"
        finally:
            dialog.deleteLater()
    
    @pytest.mark.ui
    @pytest.mark.unit
    def test_save_checkin_settings_validates_periods_when_enabled(self, dialog):
        """Test: save_checkin_settings validates periods when checkins enabled"""
        # Arrange
        dialog.ui.groupBox_checkBox_enable_checkins.setChecked(True)
        invalid_periods = {'period1': {'name': 'Test', 'time': 'invalid'}}
        
        with patch.object(dialog.checkin_widget, 'get_checkin_settings') as mock_get:
            mock_get.return_value = {'time_periods': invalid_periods, 'questions': {}}
            
            with patch('ui.dialogs.checkin_management_dialog.validate_schedule_periods') as mock_validate:
                mock_validate.return_value = (False, ["Invalid time format"])
                
                with patch('PySide6.QtWidgets.QMessageBox.warning') as mock_warning:
                    # Act
                    dialog.save_checkin_settings()
                    
                    # Assert
                    mock_validate.assert_called_once()
                    mock_warning.assert_called_once()
    
    @pytest.mark.ui
    @pytest.mark.unit
    def test_save_checkin_settings_skips_validation_when_disabled(self, dialog):
        """Test: save_checkin_settings skips validation when checkins disabled"""
        # Arrange
        dialog.ui.groupBox_checkBox_enable_checkins.setChecked(False)
        
        # Suppress the expected RuntimeWarning about unawaited coroutine
        import warnings
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=RuntimeWarning, message=".*coroutine.*was never awaited")
            
            with patch.object(dialog.checkin_widget, 'get_checkin_settings') as mock_get:
                mock_get.return_value = {'time_periods': {}, 'questions': {}}
                
                with patch('ui.dialogs.checkin_management_dialog.validate_schedule_periods') as mock_validate:
                    with patch('ui.dialogs.checkin_management_dialog.set_schedule_periods') as mock_set:
                        with patch('ui.dialogs.checkin_management_dialog.update_user_preferences') as mock_update_prefs:
                            with patch('ui.dialogs.checkin_management_dialog.update_user_account') as mock_update_account:
                                with patch('ui.dialogs.checkin_management_dialog.get_user_data') as mock_get_data:
                                    mock_get_data.return_value = {'preferences': {}, 'account': {}}
                                    
                                    with patch('PySide6.QtWidgets.QMessageBox.information') as mock_info:
                                        # Act
                                        dialog.save_checkin_settings()
                                        
                                        # Assert
                                        # Should not validate when disabled
                                        mock_validate.assert_not_called()
                                        # But should still save
                                        mock_set.assert_called_once()
    
    @pytest.mark.ui
    @pytest.mark.unit
    def test_save_checkin_settings_validates_duplicate_names(self, dialog):
        """Test: save_checkin_settings validates duplicate period names"""
        # Arrange
        dialog.ui.groupBox_checkBox_enable_checkins.setChecked(True)
        
        # Create period widgets with duplicate names
        from ui.widgets.period_row_widget import PeriodRowWidget
        period1 = PeriodRowWidget(dialog.checkin_widget)
        period1.get_period_data = Mock(return_value={'name': 'Morning'})
        period2 = PeriodRowWidget(dialog.checkin_widget)
        period2.get_period_data = Mock(return_value={'name': 'Morning'})
        dialog.checkin_widget.period_widgets = [period1, period2]
        
        with patch.object(dialog.checkin_widget, 'get_checkin_settings') as mock_get:
            mock_get.return_value = {'time_periods': {}, 'questions': {}}
            
            with patch('ui.dialogs.checkin_management_dialog.validate_schedule_periods', return_value=(True, [])):
                with patch('PySide6.QtWidgets.QMessageBox.warning') as mock_warning:
                    # Act
                    dialog.save_checkin_settings()
                    
                    # Assert
                    mock_warning.assert_called_once()
                    # Should not save
                    assert not dialog.isVisible() or dialog.result() != 1, "Should not accept dialog"
    
    @pytest.mark.ui
    @pytest.mark.unit
    def test_save_checkin_settings_saves_successfully(self, dialog):
        """Test: save_checkin_settings saves successfully with valid data"""
        # Arrange
        dialog.ui.groupBox_checkBox_enable_checkins.setChecked(True)
        test_settings = {
            'time_periods': {'morning': {'name': 'Morning', 'time': '09:00'}},
            'questions': {'mood': {'always_include': True, 'sometimes_include': False}},
            'min_questions': 1,
            'max_questions': 1
        }
        
        with patch.object(dialog.checkin_widget, 'get_checkin_settings', return_value=test_settings):
            with patch.object(dialog.checkin_widget, 'period_widgets', []):
                with patch('ui.dialogs.checkin_management_dialog.validate_schedule_periods', return_value=(True, [])):
                    with patch('ui.dialogs.checkin_management_dialog.set_schedule_periods') as mock_set:
                        with patch('ui.dialogs.checkin_management_dialog.clear_schedule_periods_cache') as mock_clear:
                            with patch('ui.dialogs.checkin_management_dialog.update_user_preferences') as mock_update_prefs:
                                with patch('ui.dialogs.checkin_management_dialog.update_user_account') as mock_update_account:
                                    with patch('ui.dialogs.checkin_management_dialog.get_user_data') as mock_get_data:
                                        mock_get_data.return_value = {'preferences': {}, 'account': {}}
                                        
                                        with patch('PySide6.QtWidgets.QMessageBox.information') as mock_info:
                                            with patch.object(dialog, 'user_changed') as mock_signal:
                                                # Act
                                                dialog.save_checkin_settings()
                                                
                                                # Assert
                                                mock_set.assert_called_once()
                                                mock_clear.assert_called_once()
                                                mock_update_prefs.assert_called_once()
                                                mock_update_account.assert_called_once()
                                                mock_info.assert_called_once()
                                                mock_signal.emit.assert_called_once()
    
    @pytest.mark.ui
    @pytest.mark.unit
    def test_save_checkin_settings_updates_account_features(self, dialog):
        """Test: save_checkin_settings updates account features"""
        # Arrange
        dialog.ui.groupBox_checkBox_enable_checkins.setChecked(True)
        
        with patch.object(dialog.checkin_widget, 'get_checkin_settings', return_value={
            'time_periods': {}, 
            'questions': {'mood': {'always_include': True, 'sometimes_include': False}},
            'min_questions': 1,
            'max_questions': 1
        }):
            with patch.object(dialog.checkin_widget, 'period_widgets', []):
                with patch('ui.dialogs.checkin_management_dialog.validate_schedule_periods', return_value=(True, [])):
                    with patch('ui.dialogs.checkin_management_dialog.set_schedule_periods'):
                        with patch('ui.dialogs.checkin_management_dialog.clear_schedule_periods_cache'):
                            with patch('ui.dialogs.checkin_management_dialog.update_user_preferences'):
                                with patch('ui.dialogs.checkin_management_dialog.get_user_data') as mock_get_data:
                                    mock_get_data.return_value = {'preferences': {}, 'account': {}}
                                    
                                    with patch('ui.dialogs.checkin_management_dialog.update_user_account') as mock_update_account:
                                        with patch('PySide6.QtWidgets.QMessageBox.information'):
                                            # Act
                                            dialog.save_checkin_settings()
                                            
                                            # Assert
                                            mock_update_account.assert_called_once()
                                            call_args = mock_update_account.call_args[0]
                                            account = call_args[1]
                                            assert account['features']['checkins'] == 'enabled', "Should set checkins to enabled"
    
    @pytest.mark.ui
    @pytest.mark.unit
    def test_save_checkin_settings_handles_errors(self, dialog):
        """Test: save_checkin_settings handles errors gracefully"""
        # Arrange
        dialog.ui.groupBox_checkBox_enable_checkins.setChecked(True)
        
        with patch.object(dialog.checkin_widget, 'get_checkin_settings', side_effect=Exception("Test error")):
            with patch('PySide6.QtWidgets.QMessageBox.critical') as mock_critical:
                # Act
                dialog.save_checkin_settings()
                
                # Assert
                mock_critical.assert_called_once()


class TestCheckinManagementDialogSignals:
    """Test CheckinManagementDialog signals"""
    
    @pytest.fixture
    def dialog(self, qapp, test_data_dir, mock_config):
        """Create CheckinManagementDialog instance for testing"""
        dialog = CheckinManagementDialog()
        yield dialog
        dialog.deleteLater()
    
    @pytest.mark.ui
    @pytest.mark.unit
    def test_user_changed_signal_exists(self, dialog):
        """Test: CheckinManagementDialog has user_changed signal"""
        # Assert
        assert hasattr(dialog, 'user_changed'), "Should have user_changed signal"
        assert dialog.user_changed is not None, "Should have user_changed signal instance"
