"""
Comprehensive tests for ui/ui_app_qt.py - Main UI functionality.
Tests the MHMManagerUI class with proper mocking to avoid UI dependencies.
"""

import pytest
import os
import sys
from unittest.mock import patch, Mock, mock_open

# Import the main UI application
from ui.ui_app_qt import ServiceManager


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
                            assert mock_running.call_count == 3
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

