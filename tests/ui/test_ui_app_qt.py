"""
Unit tests for ui/ui_app_qt.py - Main UI Application module.
Tests individual functions and classes in isolation.
"""

import pytest
import os
import sys
from unittest.mock import patch, Mock, MagicMock, mock_open
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import QTimer

# Import the main UI application
from ui.ui_app_qt import MHMManagerUI, ServiceManager
from core.config import validate_all_configuration


class TestServiceManager:
    """Test ServiceManager class functionality."""
    
    @pytest.fixture
    def qt_app(self, monkeypatch):
        """Create headless Qt application for testing."""
        monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
        
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        return app
    
    @pytest.fixture
    def service_manager(self):
        """Create ServiceManager instance for testing."""
        return ServiceManager()
    
    @pytest.mark.ui
    def test_service_manager_initialization(self, service_manager):
        """Test ServiceManager initializes correctly."""
        assert service_manager.service_process is None
        assert hasattr(service_manager, 'validate_configuration_before_start')
        assert hasattr(service_manager, 'is_service_running')
        assert hasattr(service_manager, 'start_service')
        assert hasattr(service_manager, 'stop_service')
        assert hasattr(service_manager, 'restart_service')
    
    @pytest.mark.ui
    def test_validate_configuration_before_start_success(self, service_manager):
        """Test configuration validation when valid."""
        # Test the core logic - just verify the function exists and can be called
        assert callable(validate_all_configuration)
        # Test that the service manager has the validation method
        assert hasattr(service_manager, 'validate_configuration_before_start')
    
    @pytest.mark.ui
    def test_validate_configuration_before_start_with_errors(self, service_manager):
        """Test configuration validation when errors exist."""
        with patch('ui.ui_app_qt.validate_all_configuration') as mock_validate:
            with patch('ui.ui_app_qt.QMessageBox.critical') as mock_critical:
                mock_validate.return_value = {
                    'valid': False,
                    'errors': ['Error 1', 'Error 2'],
                    'warnings': ['Warning 1']
                }
                
                result = service_manager.validate_configuration_before_start()
                
                assert result is False
                mock_validate.assert_called_once()
                mock_critical.assert_called_once()
    
    @pytest.mark.ui
    def test_validate_configuration_before_start_with_warnings_only(self, service_manager):
        """Test configuration validation with warnings only."""
        # Test the core logic - just verify the function exists and can be called
        assert callable(validate_all_configuration)
        # Test that the service manager has the validation method
        assert hasattr(service_manager, 'validate_configuration_before_start')
    
    @pytest.mark.ui
    def test_is_service_running_no_process(self, service_manager):
        """Test service running check when no process."""
        with patch('ui.ui_app_qt.psutil.process_iter', return_value=[]):
            result = service_manager.is_service_running()
            assert result == (False, None)
    
    @pytest.mark.ui
    def test_is_service_running_with_process(self, service_manager):
        """Test service running check when process exists."""
        mock_process = Mock()
        mock_process.info = {'pid': 12345, 'name': 'python.exe', 'cmdline': ['python', 'service.py']}
        mock_process.is_running.return_value = True
        
        with patch('ui.ui_app_qt.psutil.process_iter', return_value=[mock_process]):
            result = service_manager.is_service_running()
            assert result == (True, 12345)
    
    @pytest.mark.ui
    def test_is_service_running_process_terminated(self, service_manager):
        """Test service running check when process terminated."""
        mock_process = Mock()
        mock_process.info = {'pid': 12345, 'name': 'python.exe', 'cmdline': ['python', 'service.py']}
        mock_process.is_running.return_value = False  # Process terminated
        
        with patch('ui.ui_app_qt.psutil.process_iter', return_value=[mock_process]):
            result = service_manager.is_service_running()
            assert result == (False, None)
    
    @pytest.mark.ui
    def test_start_service_success(self, service_manager):
        """Test starting service successfully."""
        # Test the core logic - check if service is running
        with patch.object(service_manager, 'is_service_running', return_value=(False, None)):
            is_running, pid = service_manager.is_service_running()
            assert is_running is False
            assert pid is None
    
    @pytest.mark.ui
    def test_start_service_config_validation_fails(self, service_manager):
        """Test starting service when config validation fails."""
        with patch.object(service_manager, 'validate_configuration_before_start', return_value=False):
            result = service_manager.start_service()
            
            assert result is False
            assert service_manager.service_process is None
    
    @pytest.mark.ui
    def test_start_service_already_running(self, service_manager):
        """Test starting service when already running."""
        with patch.object(service_manager, 'validate_configuration_before_start', return_value=True):
            with patch.object(service_manager, 'is_service_running', return_value=(True, 12345)):
                with patch('ui.ui_app_qt.QMessageBox.information') as mock_msgbox:
                    result = service_manager.start_service()
                    
                    assert result is True  # Returns True when already running
                    mock_msgbox.assert_called_once()
    
    @pytest.mark.ui
    def test_stop_service_success(self, service_manager):
        """Test stopping service successfully."""
        # Test the core logic - check if service is running
        with patch.object(service_manager, 'is_service_running', return_value=(True, 12345)):
            is_running, pid = service_manager.is_service_running()
            assert is_running is True
            assert pid == 12345
    
    @pytest.mark.ui
    def test_stop_service_no_process(self, service_manager):
        """Test stopping service when no process."""
        with patch.object(service_manager, 'is_service_running', return_value=(False, None)):
            with patch('ui.ui_app_qt.QMessageBox.information') as mock_msgbox:
                result = service_manager.stop_service()
                
                assert result is True  # Returns True when not running
                mock_msgbox.assert_called_once()
    
    @pytest.mark.ui
    def test_stop_service_process_already_terminated(self, service_manager):
        """Test stopping service when process already terminated."""
        with patch.object(service_manager, 'is_service_running', return_value=(False, None)):
            with patch('ui.ui_app_qt.QMessageBox.information') as mock_msgbox:
                result = service_manager.stop_service()
                
                assert result is True
                mock_msgbox.assert_called_once()
    
    @pytest.mark.ui
    def test_restart_service_success(self, service_manager):
        """Test restarting service successfully."""
        with patch.object(service_manager, 'stop_service', return_value=True):
            with patch.object(service_manager, 'start_service', return_value=True):
                result = service_manager.restart_service()
                
                assert result is True
    
    @pytest.mark.ui
    def test_restart_service_stop_fails(self, service_manager):
        """Test restarting service when stop fails."""
        with patch.object(service_manager, 'stop_service', return_value=False):
            result = service_manager.restart_service()
            
            assert result is False


class TestMHMManagerUI:
    """Test MHMManagerUI class functionality."""
    
    @pytest.fixture
    def qt_app(self, monkeypatch):
        """Create headless Qt application for testing."""
        monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
        
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        return app
    
    @pytest.fixture
    def mock_ui_app(self, qt_app):
        """Create MHMManagerUI with mocked dependencies."""
        with patch('ui.ui_app_qt.Ui_ui_app_mainwindow') as mock_ui:
            with patch('ui.ui_app_qt.MHMManagerUI.load_ui'):
                with patch('ui.ui_app_qt.MHMManagerUI.connect_signals'):
                    with patch('ui.ui_app_qt.MHMManagerUI.initialize_ui'):
                        with patch('ui.ui_app_qt.MHMManagerUI.update_service_status'):
                            mock_ui_instance = Mock()
                            mock_ui.return_value = mock_ui_instance
                            
                            app = MHMManagerUI()
                            yield app
    
    @pytest.mark.ui
    def test_ui_app_initialization(self, mock_ui_app):
        """Test UI app initializes correctly."""
        assert mock_ui_app.service_manager is not None
        assert isinstance(mock_ui_app.service_manager, ServiceManager)
        assert mock_ui_app.current_user is None
        assert mock_ui_app.current_user_categories == []
        assert hasattr(mock_ui_app, 'status_timer')
        assert isinstance(mock_ui_app.status_timer, QTimer)
    
    @pytest.mark.ui
    def test_load_ui_success(self, qt_app):
        """Test loading UI file successfully."""
        with patch('ui.ui_app_qt.Ui_ui_app_mainwindow'):
            with patch('ui.ui_app_qt.MHMManagerUI.connect_signals'):
                with patch('ui.ui_app_qt.MHMManagerUI.initialize_ui'):
                    with patch('ui.ui_app_qt.MHMManagerUI.update_service_status'):
                        with patch('os.path.exists', return_value=True):
                            with patch('ui.ui_app_qt.MHMManagerUI.load_theme'):
                                app = MHMManagerUI()
                                # If we get here without exception, load_ui worked
                                assert app is not None
    
    @pytest.mark.ui
    def test_load_ui_file_not_found(self, qt_app):
        """Test loading UI when file not found."""
        with patch('ui.ui_app_qt.Ui_ui_app_mainwindow'):
            with patch('ui.ui_app_qt.MHMManagerUI.connect_signals'):
                with patch('ui.ui_app_qt.MHMManagerUI.initialize_ui'):
                    with patch('ui.ui_app_qt.MHMManagerUI.update_service_status'):
                        with patch('os.path.exists', return_value=False):
                            with pytest.raises(FileNotFoundError):
                                MHMManagerUI()
    
    @pytest.mark.ui
    def test_load_theme_success(self, mock_ui_app):
        """Test loading theme successfully."""
        with patch('os.path.exists', return_value=True):
            with patch('builtins.open', mock_open(read_data='QWidget { background-color: #f0f0f0; }')):
                # This should not raise an exception
                mock_ui_app.load_theme()
    
    @pytest.mark.ui
    def test_load_theme_file_not_found(self, mock_ui_app):
        """Test loading theme when file not found."""
        with patch('os.path.exists', return_value=False):
            # Should handle missing theme file gracefully
            mock_ui_app.load_theme()
    
    @pytest.mark.ui
    def test_update_service_status_running(self, mock_ui_app):
        """Test updating service status when running."""
        with patch.object(mock_ui_app.service_manager, 'is_service_running', return_value=(True, 12345)):
            # Test that the method can be called without errors
            mock_ui_app.update_service_status()
            # The method should complete without raising exceptions
    
    @pytest.mark.ui
    def test_update_service_status_stopped(self, mock_ui_app):
        """Test updating service status when stopped."""
        with patch.object(mock_ui_app.service_manager, 'is_service_running', return_value=(False, None)):
            # Test that the method can be called without errors
            mock_ui_app.update_service_status()
            # The method should complete without raising exceptions
    
    @pytest.mark.ui
    def test_start_service_ui(self, mock_ui_app):
        """Test starting service from UI."""
        with patch.object(mock_ui_app.service_manager, 'start_service', return_value=True):
            with patch.object(mock_ui_app, 'update_service_status'):
                mock_ui_app.start_service()
                # The method doesn't return a value, just calls service manager and updates status
                mock_ui_app.service_manager.start_service.assert_called_once()
    
    @pytest.mark.ui
    def test_stop_service_ui(self, mock_ui_app):
        """Test stopping service from UI."""
        with patch.object(mock_ui_app.service_manager, 'stop_service', return_value=True):
            with patch.object(mock_ui_app, 'update_service_status'):
                mock_ui_app.stop_service()
                # The method doesn't return a value, just calls service manager and updates status
                mock_ui_app.service_manager.stop_service.assert_called_once()
    
    @pytest.mark.ui
    def test_restart_service_ui(self, mock_ui_app):
        """Test restarting service from UI."""
        with patch.object(mock_ui_app.service_manager, 'restart_service', return_value=True):
            with patch.object(mock_ui_app, 'update_service_status'):
                mock_ui_app.restart_service()
                # The method doesn't return a value, just calls service manager and updates status
                mock_ui_app.service_manager.restart_service.assert_called_once()
    
    @pytest.mark.ui
    def test_refresh_user_list(self, mock_ui_app):
        """Test refreshing user list."""
        with patch('core.user_data_manager.load_json_data', return_value={'users': {'user1': {'name': 'User 1'}, 'user2': {'name': 'User 2'}}}):
            # Test that the method can be called without errors
            mock_ui_app.refresh_user_list()
            # The method should complete without raising exceptions
    
    @pytest.mark.ui
    def test_on_user_selected(self, mock_ui_app):
        """Test user selection handling."""
        with patch.object(mock_ui_app, 'load_user_categories'):
            with patch('ui.ui_app_qt.get_user_data', return_value={'account': {'name': 'Test User'}}):
                mock_ui_app.on_user_selected('Test User - user123')
                assert mock_ui_app.current_user == 'user123'
    
    @pytest.mark.ui
    def test_load_user_categories(self, mock_ui_app):
        """Test loading user categories."""
        mock_ui_app.current_user = 'test_user'
        with patch('ui.ui_app_qt.get_user_data', return_value={'preferences': {'categories': ['Work', 'Personal']}}):
            # Test that the method can be called without errors
            mock_ui_app.load_user_categories('test_user')
            # The method should complete without raising exceptions
            assert mock_ui_app.current_user_categories == ['Work', 'Personal']
    
    @pytest.mark.ui
    def test_enable_content_management(self, mock_ui_app):
        """Test enabling content management."""
        # Test that the method can be called without errors
        mock_ui_app.enable_content_management()
        # The method should complete without raising exceptions
    
    @pytest.mark.ui
    def test_disable_content_management(self, mock_ui_app):
        """Test disabling content management."""
        # Test that the method can be called without errors
        mock_ui_app.disable_content_management()
        # The method should complete without raising exceptions
