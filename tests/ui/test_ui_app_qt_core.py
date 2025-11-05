"""
Core functionality tests for ui/ui_app_qt.py - Focus on non-UI functionality.
Tests the core logic without UI components to avoid hanging issues.
"""
from tests.conftest import ensure_qt_runtime

ensure_qt_runtime()


import pytest
from unittest.mock import patch, Mock

# Import the main UI application
from ui.ui_app_qt import ServiceManager


class TestServiceManagerCore:
    """Test ServiceManager core functionality without UI dependencies."""
    
    @pytest.fixture
    def service_manager(self):
        """Create ServiceManager instance for testing."""
        return ServiceManager()
    
    def test_service_manager_initialization(self, service_manager):
        """Test ServiceManager initializes correctly."""
        assert service_manager.service_process is None
        assert hasattr(service_manager, 'validate_configuration_before_start')
        assert hasattr(service_manager, 'is_service_running')
        assert hasattr(service_manager, 'start_service')
        assert hasattr(service_manager, 'stop_service')
        assert hasattr(service_manager, 'restart_service')
    
    def test_validate_configuration_before_start_success(self, service_manager):
        """Test configuration validation when valid."""
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
    
    def test_validate_configuration_before_start_with_errors(self, service_manager):
        """Test configuration validation when errors exist."""
        with patch('ui.ui_app_qt.validate_all_configuration') as mock_validate:
            with patch('ui.ui_app_qt.QMessageBox') as mock_msgbox:
                mock_validate.return_value = {
                    'valid': False,
                    'errors': ['Error 1', 'Error 2'],
                    'warnings': ['Warning 1']
                }
                
                result = service_manager.validate_configuration_before_start()
                
                assert result is False
                mock_validate.assert_called_once()
    
    def test_validate_configuration_before_start_with_critical_warnings(self, service_manager):
        """Test configuration validation with critical warnings."""
        with patch('ui.ui_app_qt.validate_all_configuration') as mock_validate:
            with patch('ui.ui_app_qt.QMessageBox') as mock_msgbox:
                mock_validate.return_value = {
                    'valid': True,
                    'errors': [],
                    'warnings': ['Critical warning that should be shown'],
                    'available_channels': []
                }
                
                result = service_manager.validate_configuration_before_start()
                
                assert result is True
                mock_validate.assert_called_once()
    
    def test_validate_configuration_before_start_no_channels(self, service_manager):
        """Test configuration validation when no channels available."""
        with patch('ui.ui_app_qt.validate_all_configuration') as mock_validate:
            with patch('ui.ui_app_qt.QMessageBox') as mock_msgbox:
                mock_validate.return_value = {
                    'valid': True,
                    'errors': [],
                    'warnings': [],
                    'available_channels': []
                }
                
                result = service_manager.validate_configuration_before_start()
                
                assert result is True
                mock_validate.assert_called_once()
    
    def test_is_service_running_no_process(self, service_manager):
        """Test service running check when no process."""
        with patch('ui.ui_app_qt.psutil.process_iter', return_value=[]):
            result = service_manager.is_service_running()
            assert result == (False, None)
    
    def test_is_service_running_with_process(self, service_manager):
        """Test service running check when process exists."""
        mock_process = Mock()
        mock_process.info = {'pid': 12345, 'name': 'python.exe', 'cmdline': ['python', 'service.py']}
        mock_process.is_running.return_value = True
        
        with patch('ui.ui_app_qt.psutil.process_iter', return_value=[mock_process]):
            result = service_manager.is_service_running()
            assert result == (True, 12345)
    
    def test_is_service_running_process_terminated(self, service_manager):
        """Test service running check when process terminated."""
        mock_process = Mock()
        mock_process.info = {'pid': 12345, 'name': 'python.exe', 'cmdline': ['python', 'service.py']}
        mock_process.is_running.return_value = False  # Process terminated
        
        with patch('ui.ui_app_qt.psutil.process_iter', return_value=[mock_process]):
            result = service_manager.is_service_running()
            assert result == (False, None)
    
    def test_is_service_running_multiple_processes(self, service_manager):
        """Test service running check with multiple processes."""
        mock_process1 = Mock()
        mock_process1.info = {'pid': 12345, 'name': 'python.exe', 'cmdline': ['python', 'service.py']}
        mock_process1.is_running.return_value = True
        
        mock_process2 = Mock()
        mock_process2.info = {'pid': 67890, 'name': 'python.exe', 'cmdline': ['python', 'service.py']}
        mock_process2.is_running.return_value = True
        
        with patch('ui.ui_app_qt.psutil.process_iter', return_value=[mock_process1, mock_process2]):
            result = service_manager.is_service_running()
            # Should return the first running process
            assert result == (True, 12345)
    
    @pytest.mark.slow
    def test_start_service_success(self, service_manager):
        """Test starting service successfully."""
        # Test the core logic by calling the method directly without decorator
        with patch.object(service_manager, 'validate_configuration_before_start', return_value=True):
            with patch.object(service_manager, 'is_service_running', return_value=(False, None)):
                with patch('ui.ui_app_qt.subprocess.Popen') as mock_popen:
                    with patch('ui.ui_app_qt.os.path.exists', return_value=True):
                        with patch('ui.ui_app_qt.os.environ.copy', return_value={}):
                            with patch('ui.ui_app_qt.os.name', 'nt'):  # Windows
                                mock_process = Mock()
                                mock_popen.return_value = mock_process
                                
                                # Call the method directly to test core logic
                                result = service_manager.start_service()
                                
                                # The method should complete without raising exceptions
                                # The actual return value depends on the error handling decorator
                                assert service_manager.service_process == mock_process
                                mock_popen.assert_called_once()
    
    def test_start_service_config_validation_fails(self, service_manager):
        """Test starting service when config validation fails."""
        with patch.object(service_manager, 'validate_configuration_before_start', return_value=False):
            result = service_manager.start_service()
            
            assert result is False
            assert service_manager.service_process is None
    
    def test_start_service_already_running(self, service_manager):
        """Test starting service when already running."""
        with patch.object(service_manager, 'validate_configuration_before_start', return_value=True):
            with patch.object(service_manager, 'is_service_running', return_value=(True, 12345)):
                with patch('ui.ui_app_qt.QMessageBox') as mock_msgbox:
                    result = service_manager.start_service()
                    
                    assert result is True  # Returns True when already running
    
    @pytest.mark.slow
    def test_stop_service_success(self, service_manager):
        """Test stopping service successfully."""
        with patch.object(service_manager, 'is_service_running', return_value=(True, 12345)):
            with patch('ui.ui_app_qt.psutil.process_iter', return_value=[]):
                with patch('ui.ui_app_qt.QMessageBox') as mock_msgbox:
                    result = service_manager.stop_service()
                    
                    assert result is True
    
    def test_stop_service_no_process(self, service_manager):
        """Test stopping service when no process."""
        with patch.object(service_manager, 'is_service_running', return_value=(False, None)):
            with patch('ui.ui_app_qt.QMessageBox') as mock_msgbox:
                result = service_manager.stop_service()
                
                assert result is True  # Returns True when not running
    
    def test_stop_service_process_already_terminated(self, service_manager):
        """Test stopping service when process already terminated."""
        with patch.object(service_manager, 'is_service_running', return_value=(False, None)):
            with patch('ui.ui_app_qt.QMessageBox') as mock_msgbox:
                result = service_manager.stop_service()
                
                assert result is True
    
    def test_restart_service_success(self, service_manager):
        """Test restarting service successfully."""
        with patch.object(service_manager, 'stop_service', return_value=True):
            with patch.object(service_manager, 'start_service', return_value=True):
                result = service_manager.restart_service()
                
                assert result is True
    
    def test_restart_service_stop_fails(self, service_manager):
        """Test restarting service when stop fails."""
        with patch.object(service_manager, 'stop_service', return_value=False):
            result = service_manager.restart_service()
            
            assert result is False
    
    def test_restart_service_start_fails(self, service_manager):
        """Test restarting service when start fails."""
        with patch.object(service_manager, 'stop_service', return_value=True):
            with patch.object(service_manager, 'start_service', return_value=False):
                result = service_manager.restart_service()
                
                assert result is False
