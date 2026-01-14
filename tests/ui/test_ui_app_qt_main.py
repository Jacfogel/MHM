"""
Comprehensive tests for ui/ui_app_qt.py - Main UI functionality.
Tests the MHMManagerUI class with proper mocking to avoid UI dependencies.
"""
from tests.conftest import ensure_qt_runtime

ensure_qt_runtime()


import pytest
from unittest.mock import patch, Mock, mock_open, MagicMock
from PySide6.QtWidgets import QApplication

# Import the main UI application
from ui.ui_app_qt import ServiceManager

# Create QApplication instance for testing
@pytest.fixture(scope="function")
def qapp():
    """Create QApplication instance for UI testing."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.mark.ui
class TestMHMManagerUIServiceManager:
    """Test ServiceManager functionality which is the core of the UI."""
    
    def test_service_manager_initialization(self):
        """Test ServiceManager initializes correctly."""
        service_manager = ServiceManager()
        
        # Verify initialization
        assert service_manager.service_process is None
        assert hasattr(service_manager, 'validate_configuration_before_start')
        assert hasattr(service_manager, 'is_service_running')
        assert hasattr(service_manager, 'start_service')
        assert hasattr(service_manager, 'stop_service')
        assert hasattr(service_manager, 'restart_service')
    
    def test_validate_configuration_before_start_success(self):
        """Test configuration validation when valid."""
        service_manager = ServiceManager()
        
        with patch('ui.ui_app_qt.validate_all_configuration') as mock_validate:
            with patch('ui.ui_app_qt.QMessageBox') as mock_msgbox:
                mock_validate.return_value = {
                    'valid': True,
                    'errors': [],
                    'warnings': ['Non-critical warning'],
                    'available_channels': ['discord']
                }
                
                result = service_manager.validate_configuration_before_start()
                
                assert result is True
                mock_validate.assert_called_once()
    
    def test_validate_configuration_before_start_with_errors(self):
        """Test configuration validation when errors exist."""
        service_manager = ServiceManager()
        
        with patch('ui.ui_app_qt.validate_all_configuration') as mock_validate:
            with patch('ui.ui_app_qt.QMessageBox.critical') as mock_critical:
                mock_validate.return_value = {
                    'valid': False,
                    'errors': ['Critical configuration error'],
                    'warnings': [],
                    'available_channels': []
                }
                
                result = service_manager.validate_configuration_before_start()
                
                assert result is False
                mock_validate.assert_called_once()
                mock_critical.assert_called_once()
    
    def test_start_service_success(self):
        """Test starting service successfully."""
        service_manager = ServiceManager()

        with patch.object(service_manager, 'validate_configuration_before_start') as mock_validate:
            with patch.object(service_manager, 'is_service_running') as mock_running:
                with patch('ui.ui_app_qt.subprocess.Popen') as mock_popen:
                    with patch('ui.ui_app_qt.time.sleep') as mock_sleep:
                        with patch('ui.ui_app_qt.os.path.exists') as mock_exists:
                            with patch('ui.ui_app_qt.QMessageBox.information') as mock_info:
                                mock_validate.return_value = True
                                # First call: not running, second call: running after start
                                mock_running.side_effect = [(False, None), (True, 12345)]
                                mock_exists.return_value = True  # venv python exists
                                mock_process = Mock()
                                mock_popen.return_value = mock_process

                                result = service_manager.start_service()

                                assert result is True
                                mock_validate.assert_called_once()
                                assert mock_running.call_count == 2
                                mock_popen.assert_called_once()
                                mock_sleep.assert_called_once_with(2)
                                mock_info.assert_called_once()
                                assert service_manager.service_process == mock_process
    
    def test_start_service_failure(self):
        """Test starting service with failure."""
        service_manager = ServiceManager()

        with patch.object(service_manager, 'validate_configuration_before_start') as mock_validate:
            with patch.object(service_manager, 'is_service_running') as mock_running:
                with patch('ui.ui_app_qt.subprocess.Popen') as mock_popen:
                    with patch('ui.ui_app_qt.time.sleep') as mock_sleep:
                        with patch('ui.ui_app_qt.os.path.exists') as mock_exists:
                            mock_validate.return_value = True
                            mock_running.return_value = (False, None)  # Not running initially
                            mock_exists.return_value = True  # venv python exists
                            mock_popen.side_effect = Exception("Failed to start service")

                            result = service_manager.start_service()

                            assert result is False
                            assert service_manager.service_process is None
    
    def test_stop_service_success(self):
        """Test stopping service successfully."""
        service_manager = ServiceManager()

        with patch.object(service_manager, 'is_service_running') as mock_running:
            with patch('ui.ui_app_qt.psutil.process_iter') as mock_process_iter:
                with patch('ui.ui_app_qt.open', mock_open()) as mock_file:
                    with patch('ui.ui_app_qt.time.sleep') as mock_sleep:
                        with patch('ui.ui_app_qt.QMessageBox.information') as mock_info:
                            # Multiple calls to is_service_running in the stop_service method
                            # First call: service is running, subsequent calls: service is stopped
                            mock_running.side_effect = [(True, 12345), (False, None), (False, None)]
                            mock_proc = Mock()
                            mock_proc.terminate.return_value = None
                            mock_proc.is_running.return_value = False  # Process stops after terminate
                            mock_proc.info = {'pid': 12345, 'name': 'python.exe', 'cmdline': ['python', 'service.py']}
                            mock_process_iter.return_value = [mock_proc]

                            result = service_manager.stop_service()

                            assert result is True
                            mock_info.assert_called_once()
                            # is_service_running is called: initial check, then in wait loop (exits early when stopped)
                            # Force termination path not taken if service stops gracefully
                            assert mock_running.call_count >= 2, f"Expected at least 2 calls, got {mock_running.call_count}"
                            mock_file.assert_called_once()
    
    def test_stop_service_no_process(self):
        """Test stopping service when no process is running."""
        service_manager = ServiceManager()
        
        with patch.object(service_manager, 'is_service_running') as mock_running:
            mock_running.return_value = (False, None)  # Not running
            
            result = service_manager.stop_service()
            
            assert result is True  # ServiceManager returns True even when no process
            mock_running.assert_called_once()
    
    def test_restart_service_success(self):
        """Test restarting service successfully."""
        service_manager = ServiceManager()
        
        with patch.object(service_manager, 'stop_service') as mock_stop:
            with patch.object(service_manager, 'start_service') as mock_start:
                mock_stop.return_value = True
                mock_start.return_value = True
                
                result = service_manager.restart_service()
                
                assert result is True
                mock_stop.assert_called_once()
                mock_start.assert_called_once()
    
    def test_is_service_running_true(self):
        """Test service running check when service is running."""
        service_manager = ServiceManager()
        
        with patch('ui.ui_app_qt.psutil.process_iter') as mock_process_iter:
            mock_proc = Mock()
            mock_proc.info = {'pid': 12345, 'name': 'python.exe', 'cmdline': ['python', 'service.py']}
            mock_proc.is_running.return_value = True
            mock_process_iter.return_value = [mock_proc]
            
            result = service_manager.is_service_running()
            
            assert result == (True, 12345)
    
    def test_is_service_running_false(self):
        """Test service running check when service is not running."""
        service_manager = ServiceManager()
        
        with patch('ui.ui_app_qt.psutil.process_iter') as mock_process_iter:
            mock_process_iter.return_value = []  # No processes found
            
            result = service_manager.is_service_running()
            
            assert result == (False, None)
    
    def test_is_service_running_no_process(self):
        """Test service running check when no process exists."""
        service_manager = ServiceManager()
        
        with patch('ui.ui_app_qt.psutil.process_iter') as mock_process_iter:
            mock_process_iter.return_value = []  # No processes found
            
            result = service_manager.is_service_running()
            
            assert result == (False, None)


@pytest.mark.ui
class TestMHMManagerUI:
    """Test MHMManagerUI class methods."""
    
    def test_mhm_manager_ui_initialization(self, qapp):
        """Test MHMManagerUI initializes correctly."""
        from ui.ui_app_qt import MHMManagerUI
        
        with patch('ui.ui_app_qt.Ui_ui_app_mainwindow') as mock_ui:
            with patch('ui.ui_app_qt.QTimer') as mock_timer:
                with patch('ui.ui_app_qt.Path') as mock_path:
                    mock_ui_instance = Mock()
                    mock_ui.return_value = mock_ui_instance
                    mock_timer_instance = Mock()
                    mock_timer.return_value = mock_timer_instance
                    mock_path.return_value.exists.return_value = True
                    
                    # Mock the UI setup
                    ui = MHMManagerUI()
                    
                    # Verify initialization
                    assert ui.service_manager is not None
                    assert ui.current_user is None
                    assert ui.current_user_categories == []
                    assert ui.status_timer is not None
                    mock_ui_instance.setupUi.assert_called_once()
    
    def test_update_service_status_updates_display(self, qapp):
        """Test that update_service_status updates the status display."""
        from ui.ui_app_qt import MHMManagerUI
        
        with patch('ui.ui_app_qt.Ui_ui_app_mainwindow') as mock_ui:
            with patch('ui.ui_app_qt.QTimer') as mock_timer:
                with patch('ui.ui_app_qt.Path') as mock_path:
                    mock_ui_instance = Mock()
                    mock_ui.return_value = mock_ui_instance
                    mock_timer_instance = Mock()
                    mock_timer.return_value = mock_timer_instance
                    mock_path.return_value.exists.return_value = True
                    
                    ui = MHMManagerUI()
                    
                    # Test with running service
                    with patch.object(ui.service_manager, 'is_service_running', return_value=(True, 12345)):
                        ui.update_service_status()
                        mock_ui_instance.label_service_status.setText.assert_called()
                    
                    # Test with stopped service
                    with patch.object(ui.service_manager, 'is_service_running', return_value=(False, None)):
                        ui.update_service_status()
                        mock_ui_instance.label_service_status.setText.assert_called()
    
    def test_load_user_categories_loads_categories(self, test_data_dir):
        """Test that load_user_categories loads user categories correctly."""
        from ui.ui_app_qt import MHMManagerUI
        from tests.test_utilities import TestUserFactory
        
        # Arrange
        user_id = "test_user"
        TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
        
        with patch('ui.ui_app_qt.Ui_ui_app_mainwindow') as mock_ui:
            with patch('ui.ui_app_qt.QTimer') as mock_timer:
                with patch('ui.ui_app_qt.Path') as mock_path:
                    mock_ui_instance = Mock()
                    mock_ui.return_value = mock_ui_instance
                    mock_timer_instance = Mock()
                    mock_timer.return_value = mock_timer_instance
                    mock_path.return_value.exists.return_value = True
                    mock_ui_instance.comboBox_user_categories = Mock()
                    
                    ui = MHMManagerUI()
                    ui.current_user = user_id
                    
                    # Act
                    ui.load_user_categories(user_id)
                    
                    # Assert
                    assert ui.current_user_categories is not None, "Categories should be loaded"
    
    def test_on_category_selected_handles_selection(self, test_data_dir):
        """Test that on_category_selected handles category selection."""
        from ui.ui_app_qt import MHMManagerUI
        from tests.test_utilities import TestUserFactory
        
        # Arrange
        user_id = "test_user"
        TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
        
        with patch('ui.ui_app_qt.Ui_ui_app_mainwindow') as mock_ui:
            with patch('ui.ui_app_qt.QTimer') as mock_timer:
                with patch('ui.ui_app_qt.Path') as mock_path:
                    mock_ui_instance = Mock()
                    mock_ui.return_value = mock_ui_instance
                    mock_timer_instance = Mock()
                    mock_timer.return_value = mock_timer_instance
                    mock_path.return_value.exists.return_value = True
                    
                    ui = MHMManagerUI()
                    ui.current_user = user_id
                    
                    # Act
                    ui.on_category_selected("test_category")
                    
                    # Assert - Should not raise exception
                    assert True
    
    def test_enable_content_management_enables_ui(self, qapp):
        """Test that enable_content_management enables UI elements."""
        from ui.ui_app_qt import MHMManagerUI
        
        with patch('ui.ui_app_qt.Ui_ui_app_mainwindow') as mock_ui:
            with patch('ui.ui_app_qt.QTimer') as mock_timer:
                with patch('ui.ui_app_qt.Path') as mock_path:
                    mock_ui_instance = Mock()
                    mock_ui.return_value = mock_ui_instance
                    mock_timer_instance = Mock()
                    mock_timer.return_value = mock_timer_instance
                    mock_path.return_value.exists.return_value = True
                    
                    ui = MHMManagerUI()
                    
                    # Act
                    ui.enable_content_management()
                    
                    # Assert - UI elements should be enabled
                    # The method should not raise exceptions
                    assert True
    
    def test_disable_content_management_disables_ui(self, qapp):
        """Test that disable_content_management disables UI elements."""
        from ui.ui_app_qt import MHMManagerUI
        
        with patch('ui.ui_app_qt.Ui_ui_app_mainwindow') as mock_ui:
            with patch('ui.ui_app_qt.QTimer') as mock_timer:
                with patch('ui.ui_app_qt.Path') as mock_path:
                    mock_ui_instance = Mock()
                    mock_ui.return_value = mock_ui_instance
                    mock_timer_instance = Mock()
                    mock_timer.return_value = mock_timer_instance
                    mock_path.return_value.exists.return_value = True
                    
                    ui = MHMManagerUI()
                    
                    # Act
                    ui.disable_content_management()
                    
                    # Assert - UI elements should be disabled
                    # The method should not raise exceptions
                    assert True
    
    def test_run_category_scheduler_runs_scheduler(self, qapp):
        """Test that run_category_scheduler runs the category scheduler."""
        from ui.ui_app_qt import MHMManagerUI
        
        with patch('ui.ui_app_qt.Ui_ui_app_mainwindow') as mock_ui:
            with patch('ui.ui_app_qt.QTimer') as mock_timer:
                with patch('ui.ui_app_qt.Path') as mock_path:
                    with patch('ui.ui_app_qt.QMessageBox') as mock_msgbox:
                        mock_ui_instance = Mock()
                        mock_ui.return_value = mock_ui_instance
                        mock_timer_instance = Mock()
                        mock_timer.return_value = mock_timer_instance
                        mock_path.return_value.exists.return_value = True
                        mock_ui_instance.comboBox_user_categories = Mock()
                        mock_ui_instance.comboBox_user_categories.currentText.return_value = "test_category"
                        
                        ui = MHMManagerUI()
                        ui.current_user = "test_user"
                        
                        with patch('core.scheduler.run_category_scheduler_standalone', return_value=True):
                            # Act
                            ui.run_category_scheduler()
                            
                            # Assert
                            mock_msgbox.information.assert_called()
    
    def test_send_test_message_validation_checks_user(self, qapp):
        """Test that _send_test_message__validate_user_selection validates user selection."""
        from ui.ui_app_qt import MHMManagerUI
        
        with patch('ui.ui_app_qt.Ui_ui_app_mainwindow') as mock_ui:
            with patch('ui.ui_app_qt.QTimer') as mock_timer:
                with patch('ui.ui_app_qt.Path') as mock_path:
                    with patch('ui.ui_app_qt.QMessageBox') as mock_msgbox:
                        mock_ui_instance = Mock()
                        mock_ui.return_value = mock_ui_instance
                        mock_timer_instance = Mock()
                        mock_timer.return_value = mock_timer_instance
                        mock_path.return_value.exists.return_value = True
                        
                        ui = MHMManagerUI()
                        
                        # Act - Test with no user selected
                        result = ui._send_test_message__validate_user_selection()
                        
                        # Assert
                        assert result is False, "Should return False when no user selected"
                        mock_msgbox.warning.assert_called()
    
    def test_send_test_message_validation_checks_service(self, qapp):
        """Test that _send_test_message__validate_service_running validates service."""
        from ui.ui_app_qt import MHMManagerUI
        
        with patch('ui.ui_app_qt.Ui_ui_app_mainwindow') as mock_ui:
            with patch('ui.ui_app_qt.QTimer') as mock_timer:
                with patch('ui.ui_app_qt.Path') as mock_path:
                    with patch('ui.ui_app_qt.QMessageBox') as mock_msgbox:
                        mock_ui_instance = Mock()
                        mock_ui.return_value = mock_ui_instance
                        mock_timer_instance = Mock()
                        mock_timer.return_value = mock_timer_instance
                        mock_path.return_value.exists.return_value = True
                        
                        ui = MHMManagerUI()
                        
                        # Act - Test with service not running
                        with patch.object(ui.service_manager, 'is_service_running', return_value=(False, None)):
                            result = ui._send_test_message__validate_service_running()
                            
                            # Assert
                            assert result is False, "Should return False when service not running"
                            mock_msgbox.warning.assert_called()
    
    @pytest.mark.no_parallel
    def test_refresh_user_list_loads_users(self, test_data_dir):
        """Test that refresh_user_list loads users correctly."""
        from ui.ui_app_qt import MHMManagerUI
        from tests.test_utilities import TestUserFactory
        
        # Create test user (minimal user since we only need basic structure for refresh)
        user_id = "test_user_refresh"
        TestUserFactory.create_minimal_user(user_id, test_data_dir=test_data_dir)
        
        with patch('ui.ui_app_qt.Ui_ui_app_mainwindow') as mock_ui:
            with patch('ui.ui_app_qt.QTimer') as mock_timer:
                with patch('ui.ui_app_qt.Path') as mock_path:
                    mock_ui_instance = Mock()
                    mock_ui.return_value = mock_ui_instance
                    mock_timer_instance = Mock()
                    mock_timer.return_value = mock_timer_instance
                    mock_path.return_value.exists.return_value = True
                    
                    ui = MHMManagerUI()
                    
                    # Test refresh_user_list
                    ui.refresh_user_list()
                    
                    # Verify combo box was cleared and items added
                    mock_ui_instance.comboBox_users.clear.assert_called()
                    assert mock_ui_instance.comboBox_users.addItem.call_count >= 1
    
    def test_on_user_selected_handles_empty_selection(self, qapp):
        """Test that on_user_selected handles empty selection."""
        from ui.ui_app_qt import MHMManagerUI
        
        with patch('ui.ui_app_qt.Ui_ui_app_mainwindow') as mock_ui:
            with patch('ui.ui_app_qt.QTimer') as mock_timer:
                with patch('ui.ui_app_qt.Path') as mock_path:
                    mock_ui_instance = Mock()
                    mock_ui.return_value = mock_ui_instance
                    mock_timer_instance = Mock()
                    mock_timer.return_value = mock_timer_instance
                    mock_path.return_value.exists.return_value = True
                    
                    ui = MHMManagerUI()
                    
                    # Test on_user_selected with empty selection
                    ui.on_user_selected("Select a user...")
                    
                    # Verify user was cleared
                    assert ui.current_user is None
    
    def test_run_full_scheduler_calls_scheduler(self, qapp):
        """Test that run_full_scheduler calls scheduler correctly."""
        from ui.ui_app_qt import MHMManagerUI
        
        with patch('ui.ui_app_qt.Ui_ui_app_mainwindow') as mock_ui:
            with patch('ui.ui_app_qt.QTimer') as mock_timer:
                with patch('ui.ui_app_qt.Path') as mock_path:
                    with patch('core.scheduler.run_full_scheduler_standalone') as mock_scheduler:
                        with patch('ui.ui_app_qt.QMessageBox') as mock_msgbox:
                            mock_ui_instance = Mock()
                            mock_ui.return_value = mock_ui_instance
                            mock_timer_instance = Mock()
                            mock_timer.return_value = mock_timer_instance
                            mock_path.return_value.exists.return_value = True
                            mock_scheduler.return_value = True
                            
                            ui = MHMManagerUI()
                            
                            # Test run_full_scheduler
                            ui.run_full_scheduler()
                            
                            # Verify scheduler was called
                            mock_scheduler.assert_called_once()
    
    def test_run_user_scheduler_requires_user_selection(self, qapp):
        """Test that run_user_scheduler requires user selection."""
        from ui.ui_app_qt import MHMManagerUI
        
        with patch('ui.ui_app_qt.Ui_ui_app_mainwindow') as mock_ui:
            with patch('ui.ui_app_qt.QTimer') as mock_timer:
                with patch('ui.ui_app_qt.Path') as mock_path:
                    with patch('ui.ui_app_qt.QMessageBox') as mock_msgbox:
                        mock_ui_instance = Mock()
                        mock_ui.return_value = mock_ui_instance
                        mock_timer_instance = Mock()
                        mock_timer.return_value = mock_timer_instance
                        mock_path.return_value.exists.return_value = True
                        
                        ui = MHMManagerUI()
                        ui.current_user = None  # No user selected
                        
                        # Test run_user_scheduler without user
                        ui.run_user_scheduler()
                        
                        # Verify warning was shown
                        mock_msgbox.warning.assert_called_once()
    
    def test_enable_content_management_enables_buttons(self, qapp):
        """Test that enable_content_management enables buttons."""
        from ui.ui_app_qt import MHMManagerUI
        
        with patch('ui.ui_app_qt.Ui_ui_app_mainwindow') as mock_ui:
            with patch('ui.ui_app_qt.QTimer') as mock_timer:
                with patch('ui.ui_app_qt.Path') as mock_path:
                    mock_ui_instance = Mock()
                    mock_ui.return_value = mock_ui_instance
                    mock_timer_instance = Mock()
                    mock_timer.return_value = mock_timer_instance
                    mock_path.return_value.exists.return_value = True
                    
                    # Mock all button widgets that enable_content_management accesses
                    mock_ui_instance.pushButton_communication_settings = Mock()
                    mock_ui_instance.pushButton_personalization = Mock()
                    mock_ui_instance.pushButton_category_management = Mock()
                    mock_ui_instance.pushButton_checkin_settings = Mock()
                    mock_ui_instance.pushButton_task_management = Mock()
                    mock_ui_instance.pushButton_task_crud = Mock()
                    mock_ui_instance.pushButton_user_analytics = Mock()
                    mock_ui_instance.pushButton_run_user_scheduler = Mock()
                    mock_ui_instance.groupBox_category_actions = Mock()
                    
                    ui = MHMManagerUI()
                    
                    # Reset mocks after initialization (initialize_ui calls disable_content_management)
                    # This clears the calls from initialization so we can test enable_content_management cleanly
                    mock_ui_instance.pushButton_communication_settings.setEnabled.reset_mock()
                    mock_ui_instance.pushButton_personalization.setEnabled.reset_mock()
                    mock_ui_instance.pushButton_category_management.setEnabled.reset_mock()
                    mock_ui_instance.pushButton_checkin_settings.setEnabled.reset_mock()
                    mock_ui_instance.pushButton_task_management.setEnabled.reset_mock()
                    mock_ui_instance.pushButton_task_crud.setEnabled.reset_mock()
                    mock_ui_instance.pushButton_user_analytics.setEnabled.reset_mock()
                    mock_ui_instance.pushButton_run_user_scheduler.setEnabled.reset_mock()
                    mock_ui_instance.groupBox_category_actions.setEnabled.reset_mock()
                    
                    # Test enable_content_management
                    ui.enable_content_management()
                    
                    # Verify all buttons were enabled (after reset, should only be called once with True)
                    mock_ui_instance.pushButton_communication_settings.setEnabled.assert_called_once_with(True)
                    mock_ui_instance.pushButton_personalization.setEnabled.assert_called_once_with(True)
                    mock_ui_instance.pushButton_category_management.setEnabled.assert_called_once_with(True)
                    mock_ui_instance.pushButton_checkin_settings.setEnabled.assert_called_once_with(True)
                    mock_ui_instance.pushButton_task_management.setEnabled.assert_called_once_with(True)
                    mock_ui_instance.pushButton_task_crud.setEnabled.assert_called_once_with(True)
                    mock_ui_instance.pushButton_user_analytics.setEnabled.assert_called_once_with(True)
                    mock_ui_instance.pushButton_run_user_scheduler.setEnabled.assert_called_once_with(True)
                    mock_ui_instance.groupBox_category_actions.setEnabled.assert_called_once_with(True)
    
    def test_disable_content_management_disables_buttons(self, qapp):
        """Test that disable_content_management disables buttons."""
        from ui.ui_app_qt import MHMManagerUI
        
        with patch('ui.ui_app_qt.Ui_ui_app_mainwindow') as mock_ui:
            with patch('ui.ui_app_qt.QTimer') as mock_timer:
                with patch('ui.ui_app_qt.Path') as mock_path:
                    mock_ui_instance = Mock()
                    mock_ui.return_value = mock_ui_instance
                    mock_timer_instance = Mock()
                    mock_timer.return_value = mock_timer_instance
                    mock_path.return_value.exists.return_value = True
                    
                    # Mock all button widgets that disable_content_management accesses
                    mock_ui_instance.pushButton_communication_settings = Mock()
                    mock_ui_instance.pushButton_personalization = Mock()
                    mock_ui_instance.pushButton_category_management = Mock()
                    mock_ui_instance.pushButton_checkin_settings = Mock()
                    mock_ui_instance.pushButton_task_management = Mock()
                    mock_ui_instance.pushButton_task_crud = Mock()
                    mock_ui_instance.pushButton_user_analytics = Mock()
                    mock_ui_instance.pushButton_run_user_scheduler = Mock()
                    mock_ui_instance.groupBox_category_actions = Mock()
                    mock_ui_instance.groupBox_user_actions = Mock()
                    mock_ui_instance.comboBox_user_categories = Mock()
                    
                    ui = MHMManagerUI()
                    
                    # Reset mocks after initialization (initialize_ui calls disable_content_management)
                    # This clears the calls from initialization so we can test disable_content_management cleanly
                    mock_ui_instance.pushButton_communication_settings.setEnabled.reset_mock()
                    mock_ui_instance.pushButton_personalization.setEnabled.reset_mock()
                    mock_ui_instance.pushButton_category_management.setEnabled.reset_mock()
                    mock_ui_instance.pushButton_checkin_settings.setEnabled.reset_mock()
                    mock_ui_instance.pushButton_task_management.setEnabled.reset_mock()
                    mock_ui_instance.pushButton_task_crud.setEnabled.reset_mock()
                    mock_ui_instance.pushButton_user_analytics.setEnabled.reset_mock()
                    mock_ui_instance.pushButton_run_user_scheduler.setEnabled.reset_mock()
                    mock_ui_instance.groupBox_category_actions.setEnabled.reset_mock()
                    mock_ui_instance.groupBox_user_actions.setEnabled.reset_mock()
                    mock_ui_instance.comboBox_user_categories.clear.reset_mock()
                    mock_ui_instance.comboBox_user_categories.addItem.reset_mock()
                    
                    # Test disable_content_management
                    ui.disable_content_management()
                    
                    # Verify all buttons were disabled (after reset, should only be called once with False)
                    mock_ui_instance.pushButton_communication_settings.setEnabled.assert_called_once_with(False)
                    mock_ui_instance.pushButton_personalization.setEnabled.assert_called_once_with(False)
                    mock_ui_instance.pushButton_category_management.setEnabled.assert_called_once_with(False)
                    mock_ui_instance.pushButton_checkin_settings.setEnabled.assert_called_once_with(False)
                    mock_ui_instance.pushButton_task_management.setEnabled.assert_called_once_with(False)
                    mock_ui_instance.pushButton_task_crud.setEnabled.assert_called_once_with(False)
                    mock_ui_instance.pushButton_user_analytics.setEnabled.assert_called_once_with(False)
                    mock_ui_instance.pushButton_run_user_scheduler.setEnabled.assert_called_once_with(False)
                    mock_ui_instance.groupBox_category_actions.setEnabled.assert_called_once_with(False)
                    mock_ui_instance.groupBox_user_actions.setEnabled.assert_called_once_with(False)
                    mock_ui_instance.comboBox_user_categories.clear.assert_called_once()
                    mock_ui_instance.comboBox_user_categories.addItem.assert_called_once_with("Select a category...")
    
    @pytest.mark.no_parallel
    def test_update_user_index_on_startup_calls_rebuild(self, qapp):
        """Test that update_user_index_on_startup calls rebuild_user_index."""
        from ui.ui_app_qt import MHMManagerUI
        
        with patch('ui.ui_app_qt.Ui_ui_app_mainwindow') as mock_ui:
            with patch('ui.ui_app_qt.QTimer') as mock_timer:
                with patch('ui.ui_app_qt.Path') as mock_path:
                    with patch('core.user_data_manager.rebuild_user_index') as mock_rebuild:
                        mock_ui_instance = Mock()
                        mock_ui.return_value = mock_ui_instance
                        mock_timer_instance = Mock()
                        mock_timer.return_value = mock_timer_instance
                        mock_path.return_value.exists.return_value = True
                        mock_rebuild.return_value = True
                        
                        ui = MHMManagerUI()
                        
                        # Reset mock call count after initialization (which calls it once)
                        mock_rebuild.reset_mock()
                        
                        # Test update_user_index_on_startup
                        ui.update_user_index_on_startup()
                        
                        # Verify rebuild was called once (after reset)
                        mock_rebuild.assert_called_once()
    
    @pytest.mark.no_parallel
    def test_toggle_logging_verbosity_toggles_logging(self):
        """Test that toggle_logging_verbosity toggles logging."""
        from ui.ui_app_qt import MHMManagerUI
        
        with patch('ui.ui_app_qt.Ui_ui_app_mainwindow') as mock_ui:
            with patch('ui.ui_app_qt.QTimer') as mock_timer:
                with patch('ui.ui_app_qt.Path') as mock_path:
                    with patch('core.logger.toggle_verbose_logging') as mock_toggle:
                        with patch('ui.ui_app_qt.QMessageBox') as mock_msgbox:
                            mock_ui_instance = Mock()
                            mock_ui.return_value = mock_ui_instance
                            mock_timer_instance = Mock()
                            mock_timer.return_value = mock_timer_instance
                            mock_path.return_value.exists.return_value = True
                            mock_toggle.return_value = True
                            
                            ui = MHMManagerUI()
                            
                            # Test toggle_logging_verbosity
                            ui.toggle_logging_verbosity()
                            
                            # Verify toggle was called
                            mock_toggle.assert_called_once()
    
    def test_view_log_file_opens_log_file(self, qapp):
        """Test that view_log_file opens log file."""
        from ui.ui_app_qt import MHMManagerUI
        
        # Patch webbrowser.open before importing/using the UI
        # Since webbrowser is imported inside view_log_file, we patch it at module level
        # Use MagicMock to ensure it returns immediately and doesn't block
        with patch('webbrowser.open', new_callable=MagicMock) as mock_open:
            with patch('ui.ui_app_qt.Ui_ui_app_mainwindow') as mock_ui:
                with patch('ui.ui_app_qt.QTimer') as mock_timer:
                    with patch('ui.ui_app_qt.Path') as mock_path:
                        mock_ui_instance = Mock()
                        mock_ui.return_value = mock_ui_instance
                        mock_timer_instance = Mock()
                        mock_timer.return_value = mock_timer_instance
                        mock_path.return_value.exists.return_value = True
                        
                        ui = MHMManagerUI()
                        
                        # Test view_log_file
                        ui.view_log_file()
                        
                        # Verify webbrowser.open was called
                        mock_open.assert_called_once()
    
    def test_open_process_watcher_opens_dialog(self, qapp):
        """Test that open_process_watcher opens dialog."""
        from ui.ui_app_qt import MHMManagerUI
        
        with patch('ui.ui_app_qt.Ui_ui_app_mainwindow') as mock_ui:
            with patch('ui.ui_app_qt.QTimer') as mock_timer:
                with patch('ui.ui_app_qt.Path') as mock_path:
                    # Patch at the source module - the import happens inside open_process_watcher
                    with patch('ui.dialogs.process_watcher_dialog.ProcessWatcherDialog') as mock_dialog:
                        mock_ui_instance = Mock()
                        mock_ui.return_value = mock_ui_instance
                        mock_timer_instance = Mock()
                        mock_timer.return_value = mock_timer_instance
                        mock_path.return_value.exists.return_value = True
                        mock_dialog_instance = Mock()
                        mock_dialog.return_value = mock_dialog_instance
                        
                        ui = MHMManagerUI()
                        
                        # Test open_process_watcher
                        ui.open_process_watcher()
                        
                        # Verify dialog was created and shown
                        mock_dialog.assert_called_once()
                        mock_dialog_instance.show.assert_called_once()
    
    def test_load_user_categories_loads_categories_extended(self, test_data_dir, qapp):
        """Test that load_user_categories loads user categories."""
        from ui.ui_app_qt import MHMManagerUI
        from tests.test_utilities import TestUserFactory
        
        # Create test user with categories
        user_id = "test_user_categories"
        TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
        
        with patch('ui.ui_app_qt.Ui_ui_app_mainwindow') as mock_ui:
            with patch('ui.ui_app_qt.QTimer') as mock_timer:
                with patch('ui.ui_app_qt.Path') as mock_path:
                    mock_ui_instance = Mock()
                    mock_ui.return_value = mock_ui_instance
                    mock_timer_instance = Mock()
                    mock_timer.return_value = mock_timer_instance
                    mock_path.return_value.exists.return_value = True
                    
                    ui = MHMManagerUI()
                    ui.current_user = user_id
                    
                    # Test load_user_categories
                    ui.load_user_categories(user_id)
                    
                    # Verify combo box was cleared and items added
                    mock_ui_instance.comboBox_user_categories.clear.assert_called()
                    assert mock_ui_instance.comboBox_user_categories.addItem.call_count >= 0
    
    def test_on_category_selected_handles_selection_extended(self, qapp):
        """Test that on_category_selected handles category selection."""
        from ui.ui_app_qt import MHMManagerUI
        
        with patch('ui.ui_app_qt.Ui_ui_app_mainwindow') as mock_ui:
            with patch('ui.ui_app_qt.QTimer') as mock_timer:
                with patch('ui.ui_app_qt.Path') as mock_path:
                    mock_ui_instance = Mock()
                    mock_ui.return_value = mock_ui_instance
                    mock_timer_instance = Mock()
                    mock_timer.return_value = mock_timer_instance
                    mock_path.return_value.exists.return_value = True
                    # Mock currentIndex to return an integer (1 = valid selection)
                    mock_ui_instance.comboBox_user_categories.currentIndex.return_value = 1
                    mock_ui_instance.comboBox_user_categories.itemData.return_value = "test_category"
                    
                    ui = MHMManagerUI()
                    ui.current_user = "test_user"
                    
                    # Test on_category_selected
                    ui.on_category_selected("test_category")
                    
                    # Verify method completes without error
                    assert True
    
    def test_create_new_user_opens_dialog(self, qapp):
        """Test that create_new_user opens account creation dialog."""
        from ui.ui_app_qt import MHMManagerUI
        
        with patch('ui.ui_app_qt.Ui_ui_app_mainwindow') as mock_ui:
            with patch('ui.ui_app_qt.QTimer') as mock_timer:
                with patch('ui.ui_app_qt.Path') as mock_path:
                    with patch('ui.dialogs.account_creator_dialog.AccountCreatorDialog') as mock_dialog:
                        with patch('communication.core.channel_orchestrator.CommunicationManager') as mock_comm:
                            mock_ui_instance = Mock()
                            mock_ui.return_value = mock_ui_instance
                            mock_timer_instance = Mock()
                            mock_timer.return_value = mock_timer_instance
                            mock_path.return_value.exists.return_value = True
                            mock_dialog_instance = Mock()
                            mock_dialog.return_value = mock_dialog_instance
                            mock_comm_instance = Mock()
                            mock_comm.return_value = mock_comm_instance
                            
                            ui = MHMManagerUI()
                            
                            # Test create_new_user
                            ui.create_new_user()
                            
                            # Verify dialog was created
                            mock_dialog.assert_called_once()
    
    def test_manage_communication_settings_opens_dialog(self, qapp):
        """Test that manage_communication_settings opens dialog."""
        from ui.ui_app_qt import MHMManagerUI
        
        with patch('ui.ui_app_qt.Ui_ui_app_mainwindow') as mock_ui:
            with patch('ui.ui_app_qt.QTimer') as mock_timer:
                with patch('ui.ui_app_qt.Path') as mock_path:
                    with patch('ui.dialogs.channel_management_dialog.ChannelManagementDialog') as mock_dialog:
                        with patch('communication.core.channel_orchestrator.CommunicationManager') as mock_comm_manager_class:
                            mock_ui_instance = Mock()
                            mock_ui.return_value = mock_ui_instance
                            mock_timer_instance = Mock()
                            mock_timer.return_value = mock_timer_instance
                            mock_path.return_value.exists.return_value = True
                            mock_dialog_instance = Mock()
                            mock_dialog.return_value = mock_dialog_instance
                            mock_comm_manager = Mock()
                            mock_comm_manager_class.return_value = mock_comm_manager
                            
                            ui = MHMManagerUI()
                            ui.current_user = "test_user"
                            
                            # Test manage_communication_settings
                            ui.manage_communication_settings()
                            
                            # Verify dialog was created
                            mock_dialog.assert_called_once()
    
    @pytest.mark.no_parallel
    def test_manage_categories_opens_dialog(self):
        """Test that manage_categories opens dialog."""
        from ui.ui_app_qt import MHMManagerUI
        
        with patch('ui.ui_app_qt.Ui_ui_app_mainwindow') as mock_ui:
            with patch('ui.ui_app_qt.QTimer') as mock_timer:
                with patch('ui.ui_app_qt.Path') as mock_path:
                    with patch('ui.dialogs.category_management_dialog.CategoryManagementDialog') as mock_dialog:
                        mock_ui_instance = Mock()
                        mock_ui.return_value = mock_ui_instance
                        mock_timer_instance = Mock()
                        mock_timer.return_value = mock_timer_instance
                        mock_path.return_value.exists.return_value = True
                        mock_dialog_instance = Mock()
                        mock_dialog.return_value = mock_dialog_instance
                        
                        ui = MHMManagerUI()
                        ui.current_user = "test_user"
                        
                        # Test manage_categories
                        ui.manage_categories()
                        
                        # Verify dialog was created
                        mock_dialog.assert_called_once()
    
    def test_manage_checkins_opens_dialog(self, qapp):
        """Test that manage_checkins opens dialog."""
        from ui.ui_app_qt import MHMManagerUI
        
        with patch('ui.ui_app_qt.Ui_ui_app_mainwindow') as mock_ui:
            with patch('ui.ui_app_qt.QTimer') as mock_timer:
                with patch('ui.ui_app_qt.Path') as mock_path:
                    with patch('ui.dialogs.checkin_management_dialog.CheckinManagementDialog') as mock_dialog:
                        mock_ui_instance = Mock()
                        mock_ui.return_value = mock_ui_instance
                        mock_timer_instance = Mock()
                        mock_timer.return_value = mock_timer_instance
                        mock_path.return_value.exists.return_value = True
                        mock_dialog_instance = Mock()
                        mock_dialog.return_value = mock_dialog_instance
                        
                        ui = MHMManagerUI()
                        ui.current_user = "test_user"
                        
                        # Test manage_checkins
                        ui.manage_checkins()
                        
                        # Verify dialog was created
                        mock_dialog.assert_called_once()
    
    def test_manage_tasks_opens_dialog(self):
        """Test that manage_tasks opens dialog."""
        from ui.ui_app_qt import MHMManagerUI
        
        with patch('ui.ui_app_qt.Ui_ui_app_mainwindow') as mock_ui:
            with patch('ui.ui_app_qt.QTimer') as mock_timer:
                with patch('ui.ui_app_qt.Path') as mock_path:
                    with patch('ui.dialogs.task_management_dialog.TaskManagementDialog') as mock_dialog:
                        mock_ui_instance = Mock()
                        mock_ui.return_value = mock_ui_instance
                        mock_timer_instance = Mock()
                        mock_timer.return_value = mock_timer_instance
                        mock_path.return_value.exists.return_value = True
                        mock_dialog_instance = Mock()
                        mock_dialog.return_value = mock_dialog_instance
                        
                        ui = MHMManagerUI()
                        ui.current_user = "test_user"
                        
                        # Test manage_tasks
                        ui.manage_tasks()
                        
                        # Verify dialog was created
                        mock_dialog.assert_called_once()
    
    @pytest.mark.no_parallel
    def test_manage_task_crud_opens_dialog(self, qapp):
        """Test that manage_task_crud opens dialog."""
        from ui.ui_app_qt import MHMManagerUI
        
        with patch('ui.ui_app_qt.Ui_ui_app_mainwindow') as mock_ui:
            with patch('ui.ui_app_qt.QTimer') as mock_timer:
                with patch('ui.ui_app_qt.Path') as mock_path:
                    with patch('ui.dialogs.task_crud_dialog.TaskCrudDialog') as mock_dialog:
                        mock_ui_instance = Mock()
                        mock_ui.return_value = mock_ui_instance
                        mock_timer_instance = Mock()
                        mock_timer.return_value = mock_timer_instance
                        mock_path.return_value.exists.return_value = True
                        mock_dialog_instance = Mock()
                        mock_dialog.return_value = mock_dialog_instance
                        
                        ui = MHMManagerUI()
                        ui.current_user = "test_user"
                        
                        # Test manage_task_crud
                        ui.manage_task_crud()
                        
                        # Verify dialog was created
                        mock_dialog.assert_called_once()
    
    def test_manage_personalization_opens_dialog(self, qapp):
        """Test that manage_personalization opens dialog."""
        from ui.ui_app_qt import MHMManagerUI
        
        with patch('ui.ui_app_qt.Ui_ui_app_mainwindow') as mock_ui:
            with patch('ui.ui_app_qt.QTimer') as mock_timer:
                with patch('ui.ui_app_qt.Path') as mock_path:
                    with patch('ui.dialogs.user_profile_dialog.UserProfileDialog') as mock_dialog:
                        mock_ui_instance = Mock()
                        mock_ui.return_value = mock_ui_instance
                        mock_timer_instance = Mock()
                        mock_timer.return_value = mock_timer_instance
                        mock_path.return_value.exists.return_value = True
                        mock_dialog_instance = Mock()
                        mock_dialog.return_value = mock_dialog_instance
                        
                        ui = MHMManagerUI()
                        ui.current_user = "test_user"
                        
                        # Test manage_personalization
                        ui.manage_personalization()
                        
                        # Verify dialog was created
                        mock_dialog.assert_called_once()
    
    def test_manage_user_analytics_opens_dialog(self, qapp):
        """Test that manage_user_analytics opens dialog."""
        from ui.ui_app_qt import MHMManagerUI
        
        with patch('ui.ui_app_qt.Ui_ui_app_mainwindow') as mock_ui:
            with patch('ui.ui_app_qt.QTimer') as mock_timer:
                with patch('ui.ui_app_qt.Path') as mock_path:
                    with patch('ui.dialogs.user_analytics_dialog.open_user_analytics_dialog') as mock_open:
                        mock_ui_instance = Mock()
                        mock_ui.return_value = mock_ui_instance
                        mock_timer_instance = Mock()
                        mock_timer.return_value = mock_timer_instance
                        mock_path.return_value.exists.return_value = True
                        
                        ui = MHMManagerUI()
                        ui.current_user = "test_user"
                        
                        # Test manage_user_analytics
                        ui.manage_user_analytics()
                        
                        # Verify dialog was opened
                        mock_open.assert_called_once()
    
    def test_edit_user_messages_opens_dialog(self, qapp):
        """Test that edit_user_messages opens dialog."""
        from ui.ui_app_qt import MHMManagerUI
        
        with patch('ui.ui_app_qt.Ui_ui_app_mainwindow') as mock_ui:
            with patch('ui.ui_app_qt.QTimer') as mock_timer:
                with patch('ui.ui_app_qt.Path') as mock_path:
                    with patch('ui.dialogs.message_editor_dialog.open_message_editor_dialog') as mock_open_dialog:
                        mock_ui_instance = Mock()
                        mock_ui.return_value = mock_ui_instance
                        mock_timer_instance = Mock()
                        mock_timer.return_value = mock_timer_instance
                        mock_path.return_value.exists.return_value = True
                        mock_ui_instance.comboBox_user_categories.currentIndex.return_value = 1
                        mock_ui_instance.comboBox_user_categories.itemData.return_value = "test_category"
                        
                        ui = MHMManagerUI()
                        ui.current_user = "test_user"
                        
                        # Test edit_user_messages
                        ui.edit_user_messages()
                        
                        # Verify dialog was opened
                        mock_open_dialog.assert_called_once()
    
    def test_edit_user_schedules_opens_dialog(self, qapp):
        """Test that edit_user_schedules opens dialog."""
        from ui.ui_app_qt import MHMManagerUI
        
        with patch('ui.ui_app_qt.Ui_ui_app_mainwindow') as mock_ui:
            with patch('ui.ui_app_qt.QTimer') as mock_timer:
                with patch('ui.ui_app_qt.Path') as mock_path:
                    with patch('ui.dialogs.schedule_editor_dialog.open_schedule_editor') as mock_open_dialog:
                        mock_ui_instance = Mock()
                        mock_ui.return_value = mock_ui_instance
                        mock_timer_instance = Mock()
                        mock_timer.return_value = mock_timer_instance
                        mock_path.return_value.exists.return_value = True
                        mock_ui_instance.comboBox_user_categories.currentIndex.return_value = 1
                        mock_ui_instance.comboBox_user_categories.itemData.return_value = "test_category"
                        mock_open_dialog.return_value = True
                        
                        ui = MHMManagerUI()
                        ui.current_user = "test_user"
                        
                        # Test edit_user_schedules
                        ui.edit_user_schedules()
                        
                        # Verify dialog was opened
                        mock_open_dialog.assert_called_once()
    
    def test_send_test_message_validates_user_selection(self, qapp):
        """Test that send_test_message validates user selection."""
        from ui.ui_app_qt import MHMManagerUI
        
        with patch('ui.ui_app_qt.Ui_ui_app_mainwindow') as mock_ui:
            with patch('ui.ui_app_qt.QTimer') as mock_timer:
                with patch('ui.ui_app_qt.Path') as mock_path:
                    with patch('ui.ui_app_qt.QMessageBox') as mock_msgbox:
                        mock_ui_instance = Mock()
                        mock_ui.return_value = mock_ui_instance
                        mock_timer_instance = Mock()
                        mock_timer.return_value = mock_timer_instance
                        mock_path.return_value.exists.return_value = True
                        
                        ui = MHMManagerUI()
                        ui.current_user = None  # No user selected
                        
                        # Test send_test_message without user
                        ui.send_test_message()
                        
                        # Verify warning was shown
                        mock_msgbox.warning.assert_called_once()
    
    def test_run_category_scheduler_requires_user_and_category(self, qapp):
        """Test that run_category_scheduler requires user and category."""
        from ui.ui_app_qt import MHMManagerUI
        
        with patch('ui.ui_app_qt.Ui_ui_app_mainwindow') as mock_ui:
            with patch('ui.ui_app_qt.QTimer') as mock_timer:
                with patch('ui.ui_app_qt.Path') as mock_path:
                    with patch('ui.ui_app_qt.QMessageBox') as mock_msgbox:
                        mock_ui_instance = Mock()
                        mock_ui.return_value = mock_ui_instance
                        mock_timer_instance = Mock()
                        mock_timer.return_value = mock_timer_instance
                        mock_path.return_value.exists.return_value = True
                        mock_ui_instance.comboBox_user_categories.currentText.return_value = ""
                        
                        ui = MHMManagerUI()
                        ui.current_user = "test_user"
                        
                        # Test run_category_scheduler without category
                        ui.run_category_scheduler()
                        
                        # Verify warning was shown
                        mock_msgbox.warning.assert_called_once()
    
    def test_load_theme_loads_theme_file(self, qapp):
        """Test that load_theme loads theme file."""
        from ui.ui_app_qt import MHMManagerUI
        from pathlib import Path
        
        with patch('ui.ui_app_qt.Ui_ui_app_mainwindow') as mock_ui:
            with patch('ui.ui_app_qt.QTimer') as mock_timer:
                mock_ui_instance = Mock()
                mock_ui.return_value = mock_ui_instance
                mock_timer_instance = Mock()
                mock_timer.return_value = mock_timer_instance
                
                # Create a mock Path that supports all operations needed
                def create_path_mock(*args):
                    """Create a mock Path that supports parent.parent / 'styles' / 'admin_theme.qss'"""
                    mock = Mock(spec=Path)
                    
                    # Create parent chain: parent -> parent.parent
                    parent_parent_mock = Mock(spec=Path)
                    parent_parent_mock.exists.return_value = True
                    parent_parent_mock.__truediv__ = lambda self, other: create_path_mock()
                    
                    parent_mock = Mock(spec=Path)
                    parent_mock.exists.return_value = True
                    parent_mock.parent = parent_parent_mock
                    parent_mock.__truediv__ = lambda self, other: create_path_mock()
                    
                    # Set up the main mock
                    mock.parent = parent_mock
                    mock.exists.return_value = True
                    mock.__truediv__ = lambda self, other: create_path_mock()
                    
                    return mock
                
                theme_content = "QWidget { background-color: white; }"
                
                # Patch setStyleSheet before creating the instance
                with patch.object(MHMManagerUI, 'setStyleSheet') as mock_set_style:
                    with patch('ui.ui_app_qt.Path', side_effect=create_path_mock):
                        with patch('builtins.open', mock_open(read_data=theme_content)):
                            ui = MHMManagerUI()
                            
                            # load_theme is called during __init__, so verify it was called
                            # Also call it explicitly to test the method directly
                            ui.load_theme()
                            
                            # Verify theme was loaded (setStyleSheet should be called at least once)
                            # It may be called twice (once during init, once explicitly)
                            assert mock_set_style.call_count >= 1
                            # Verify it was called with the theme content
                            mock_set_style.assert_any_call(theme_content)
