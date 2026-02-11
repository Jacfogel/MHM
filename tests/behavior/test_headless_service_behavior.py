"""
Headless Service Behavior Tests

Tests for core/headless_service.py focusing on real behavior and side effects.
These tests verify that the headless service manager actually works and produces expected
side effects rather than just returning values.
"""

import pytest
import os
import json
import time
from unittest.mock import patch, Mock, MagicMock
from pathlib import Path

# Import the modules we're testing
from core.headless_service import HeadlessServiceManager
from tests.test_utilities import TestUserFactory


@pytest.mark.behavior
class TestHeadlessServiceManagerBehavior:
    """Test headless service manager real behavior and side effects."""
    
    @pytest.fixture
    def manager(self):
        """Create a HeadlessServiceManager instance for testing."""
        return HeadlessServiceManager()
    
    @pytest.fixture
    def test_data_dir(self, test_path_factory):
        """Provide per-test directory under tests/data/tmp."""
        return test_path_factory
    
    @pytest.mark.behavior
    @pytest.mark.behavior
    def test_headless_service_manager_initialization(self, manager):
        """Test that HeadlessServiceManager initializes correctly."""
        assert manager.service_process is None, "service_process should be None initially"
        assert manager.running is False, "running should be False initially"
    
    @pytest.mark.behavior
    @pytest.mark.behavior
    @pytest.mark.file_io
    @patch('core.headless_service.get_service_processes')
    def test_get_headless_service_status_no_processes(self, mock_get_processes, manager):
        """Test getting headless service status when no processes exist."""
        mock_get_processes.return_value = []
        
        is_running, pid = manager.get_headless_service_status()
        
        assert is_running is False, "Should return False when no processes"
        assert pid is None, "Should return None for PID when no processes"
        mock_get_processes.assert_called_once()
    
    @pytest.mark.behavior
    @pytest.mark.behavior
    @pytest.mark.file_io
    @patch('core.headless_service.get_service_processes')
    def test_get_headless_service_status_with_headless_process(self, mock_get_processes, manager):
        """Test getting headless service status when headless process exists."""
        mock_get_processes.return_value = [
            {
                'pid': 12345,
                'is_headless': True,
                'is_ui_managed': False,
                'process_type': 'headless',
                'create_time': time.time(),
                'cmdline': ['python', 'core/service.py']
            }
        ]
        
        is_running, pid = manager.get_headless_service_status()
        
        assert is_running is True, "Should return True when headless process exists"
        assert pid == 12345, "Should return correct PID"
        mock_get_processes.assert_called_once()
    
    @pytest.mark.behavior
    @pytest.mark.behavior
    @pytest.mark.file_io
    @patch('core.headless_service.get_service_processes')
    def test_get_headless_service_status_with_multiple_processes(self, mock_get_processes, manager):
        """Test getting headless service status with multiple processes (returns most recent)."""
        current_time = time.time()
        mock_get_processes.return_value = [
            {
                'pid': 11111,
                'is_headless': True,
                'is_ui_managed': False,
                'process_type': 'headless',
                'create_time': current_time - 10,  # Older
                'cmdline': ['python', 'core/service.py']
            },
            {
                'pid': 22222,
                'is_headless': True,
                'is_ui_managed': False,
                'process_type': 'headless',
                'create_time': current_time,  # Most recent
                'cmdline': ['python', 'core/service.py']
            }
        ]
        
        is_running, pid = manager.get_headless_service_status()
        
        assert is_running is True, "Should return True when headless processes exist"
        assert pid == 22222, "Should return PID of most recent process"
        mock_get_processes.assert_called_once()
    
    @pytest.mark.behavior
    @pytest.mark.behavior
    @pytest.mark.file_io
    @patch('core.headless_service.get_service_processes')
    @patch('core.headless_service.is_ui_service_running')
    def test_can_start_headless_service_no_conflicts(self, mock_is_ui_running, mock_get_processes, manager):
        """Test that can_start_headless_service returns True when no conflicts."""
        mock_get_processes.return_value = []
        mock_is_ui_running.return_value = False
        
        result = manager.can_start_headless_service()
        
        assert result is True, "Should return True when no conflicts"
    
    @pytest.mark.behavior
    @pytest.mark.behavior
    @pytest.mark.file_io
    @patch('core.headless_service.get_service_processes')
    @patch('core.headless_service.is_ui_service_running')
    def test_can_start_headless_service_headless_already_running(self, mock_is_ui_running, mock_get_processes, manager):
        """Test that can_start_headless_service allows restart when headless already running."""
        mock_get_processes.return_value = [
            {
                'pid': 12345,
                'is_headless': True,
                'is_ui_managed': False,
                'process_type': 'headless',
                'create_time': time.time(),
                'cmdline': ['python', 'core/service.py']
            }
        ]
        mock_is_ui_running.return_value = False
        
        result = manager.can_start_headless_service()
        
        assert result is True, "Should return True to allow restart"
    
    @pytest.mark.behavior
    @pytest.mark.behavior
    @pytest.mark.file_io
    @patch('core.headless_service.get_service_processes')
    @patch('core.headless_service.is_ui_service_running')
    def test_can_start_headless_service_ui_running(self, mock_is_ui_running, mock_get_processes, manager):
        """Test that can_start_headless_service handles UI service running."""
        mock_get_processes.return_value = []
        mock_is_ui_running.return_value = True
        
        result = manager.can_start_headless_service()
        
        assert result is True, "Should return True (will stop UI services first)"
    
    @pytest.mark.behavior
    @pytest.mark.behavior
    @pytest.mark.file_io
    def test_start_headless_service_success(self, manager, test_data_dir):
        """Test starting headless service successfully."""
        with patch('core.headless_service.get_service_processes', return_value=[]):
            with patch('core.headless_service.is_ui_service_running', return_value=False):
                with patch('core.headless_service.subprocess.Popen') as mock_popen:
                    with patch('core.headless_service.os.path.exists', return_value=True):
                        with patch('core.headless_service.os.environ.copy', return_value={}):
                            with patch('core.headless_service.os.name', 'nt'):
                                with patch('core.headless_service.time.sleep', return_value=None):
                                    mock_process = Mock()
                                    mock_process.pid = 12345
                                    mock_process.poll.return_value = None  # Process is running
                                    mock_popen.return_value = mock_process
                                    
                                    # Mock get_headless_service_status to return True after start
                                    with patch.object(manager, 'get_headless_service_status', return_value=(True, 12345)):
                                        result = manager.start_headless_service()
                                    
                                    # Verify side effects
                                    assert result is True, "Should return True on success"
                                    assert manager.running is True, "Should set running to True"
                                    assert manager.service_process == mock_process, "Should store service process"
                                    mock_popen.assert_called_once()
    
    @pytest.mark.behavior
    @pytest.mark.behavior
    @pytest.mark.file_io
    def test_start_headless_service_stops_existing_headless(self, manager):
        """Test that starting headless service stops existing headless service."""
        with patch('core.headless_service.get_service_processes') as mock_get_processes:
            mock_get_processes.return_value = [
                {
                    'pid': 12345,
                    'is_headless': True,
                    'is_ui_managed': False,
                    'process_type': 'headless',
                    'create_time': time.time(),
                    'cmdline': ['python', 'core/service.py']
                }
            ]
            with patch('core.headless_service.is_ui_service_running', return_value=False):
                # get_headless_service_status is called in can_start_headless_service() and start_headless_service()
                # First call (in can_start_headless_service): returns (True, 12345)
                # Second call (in start_headless_service): returns (True, 12345) to trigger stop
                # Third call (after stop): returns (False, None) to indicate stopped
                with patch.object(manager, 'get_headless_service_status', side_effect=[(True, 12345), (True, 12345), (False, None)]):
                    with patch.object(manager, 'stop_headless_service', return_value=True) as mock_stop_headless:
                        with patch('core.headless_service.subprocess.Popen') as mock_popen:
                            with patch('core.headless_service.os.path.exists', return_value=True):
                                with patch('core.headless_service.os.environ.copy', return_value={}):
                                    with patch('core.headless_service.os.name', 'nt'):
                                        with patch('core.headless_service.time.sleep'):  # Skip sleep delays
                                            mock_process = Mock()
                                            mock_process.pid = 12346
                                            mock_process.poll.return_value = None
                                            mock_popen.return_value = mock_process
                                            
                                            manager.start_headless_service()
                
                # Verify that stop was called
                mock_stop_headless.assert_called_once()
    
    @pytest.mark.behavior
    @pytest.mark.behavior
    @pytest.mark.file_io
    @patch('core.headless_service.get_service_processes')
    @patch('core.headless_service.is_ui_service_running')
    def test_start_headless_service_stops_ui_services(self, mock_is_ui_running, mock_get_processes, 
                                                      manager):
        """Test that starting headless service stops UI services."""
        mock_get_processes.return_value = []
        mock_is_ui_running.return_value = True
        
        with patch.object(manager, 'get_headless_service_status', return_value=(False, None)):
            with patch.object(manager, 'stop_ui_services', return_value=True) as mock_stop_ui:
                with patch('core.headless_service.subprocess.Popen') as mock_popen:
                    with patch('core.headless_service.os.path.exists', return_value=True):
                        with patch('core.headless_service.os.environ.copy', return_value={}):
                            with patch('core.headless_service.os.name', 'nt'):
                                mock_process = Mock()
                                mock_process.pid = 12345
                                mock_process.poll.return_value = None
                                mock_popen.return_value = mock_process
                                
                                manager.start_headless_service()
        
        # Verify that stop_ui_services was called
        mock_stop_ui.assert_called_once()
    
    @pytest.mark.behavior
    @pytest.mark.behavior
    @pytest.mark.file_io
    @patch('core.headless_service.get_service_processes')
    @patch('core.headless_service.is_ui_service_running')
    def test_stop_headless_service_not_running(self, mock_is_ui_running, mock_get_processes, manager):
        """Test stopping headless service when not running."""
        mock_get_processes.return_value = []
        
        with patch.object(manager, 'get_headless_service_status', return_value=(False, None)):
            result = manager.stop_headless_service()
        
        assert result is True, "Should return True when no service to stop"
        assert manager.running is False, "Should keep running as False"
    
    @pytest.mark.behavior
    @pytest.mark.behavior
    @pytest.mark.file_io
    @patch('core.headless_service.get_service_processes')
    @patch('core.headless_service.is_ui_service_running')
    @patch('core.headless_service.os.path.dirname')
    @patch('builtins.open', create=True)
    def test_stop_headless_service_creates_shutdown_file(self, mock_open, mock_dirname, 
                                                         mock_is_ui_running, mock_get_processes, manager):
        """Test that stopping headless service creates shutdown request file."""
        mock_get_processes.return_value = []
        mock_dirname.return_value = '/test/project'
        
        with patch.object(manager, 'get_headless_service_status', side_effect=[(True, 12345), (False, None)]):
            result = manager.stop_headless_service()
        
        # Verify shutdown file was created
        assert mock_open.called, "Should create shutdown request file"
        assert manager.running is False, "Should set running to False"
    
    @pytest.mark.behavior
    @pytest.mark.behavior
    @pytest.mark.file_io
    @patch('core.headless_service.get_service_processes')
    @patch('core.headless_service.is_ui_service_running')
    @patch('core.headless_service.os.path.dirname')
    @patch('builtins.open', create=True)
    def test_stop_ui_services_creates_shutdown_file(self, mock_open, mock_dirname, 
                                                     mock_is_ui_running, mock_get_processes, manager):
        """Test that stopping UI services creates shutdown request file."""
        mock_get_processes.return_value = []
        mock_dirname.return_value = '/test/project'
        mock_is_ui_running.side_effect = [True, False]  # Running, then stopped
        
        result = manager.stop_ui_services()
        
        # Verify shutdown file was created
        assert mock_open.called, "Should create shutdown request file"
        assert result is True, "Should return True on success"
    
    @pytest.mark.behavior
    @pytest.mark.behavior
    @pytest.mark.file_io
    @patch('core.headless_service.get_service_processes')
    @patch('core.headless_service.is_headless_service_running')
    @patch('core.headless_service.is_ui_service_running')
    def test_get_service_info_comprehensive(self, mock_is_ui_running, mock_is_headless_running, 
                                           mock_get_processes, manager):
        """Test that get_service_info returns comprehensive information."""
        mock_get_processes.return_value = [
            {
                'pid': 12345,
                'is_headless': True,
                'is_ui_managed': False,
                'process_type': 'headless',
                'create_time': time.time(),
                'cmdline': ['python', 'core/service.py']
            },
            {
                'pid': 12346,
                'is_headless': False,
                'is_ui_managed': True,
                'process_type': 'ui',
                'create_time': time.time(),
                'cmdline': ['python', 'ui/ui_app_qt.py']
            }
        ]
        mock_is_headless_running.return_value = True
        mock_is_ui_running.return_value = True
        
        info = manager.get_service_info()
        
        # Verify comprehensive information
        assert 'total_services' in info, "Should include total_services"
        assert 'headless_services' in info, "Should include headless_services"
        assert 'ui_services' in info, "Should include ui_services"
        assert 'unknown_services' in info, "Should include unknown_services"
        assert 'can_start_headless' in info, "Should include can_start_headless"
        assert 'is_headless_running' in info, "Should include is_headless_running"
        assert 'is_ui_running' in info, "Should include is_ui_running"
        assert info['total_services'] == 2, "Should count all services"
        assert len(info['headless_services']) == 1, "Should count headless services"
        assert len(info['ui_services']) == 1, "Should count UI services"
    
    @pytest.mark.behavior
    @pytest.mark.behavior
    @pytest.mark.file_io
    @patch('core.headless_service.os.path.dirname')
    @patch('builtins.open', create=True)
    def test_send_test_message_creates_request_file(self, mock_open, mock_dirname, manager):
        """Test that send_test_message creates test message request file."""
        mock_dirname.return_value = '/test/project'
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file
        
        result = manager.send_test_message('test_user_123', 'motivation')
        
        # Verify request file was created
        assert mock_open.called, "Should create test message request file"
        assert result is True, "Should return True on success"
        # Verify JSON was written
        mock_file.write.assert_called()
    
    @pytest.mark.behavior
    @pytest.mark.behavior
    @pytest.mark.file_io
    @patch('core.headless_service.os.path.dirname')
    @patch('builtins.open', create=True)
    def test_reschedule_messages_creates_request_file(self, mock_open, mock_dirname, manager):
        """Test that reschedule_messages creates reschedule request file."""
        mock_dirname.return_value = '/test/project'
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file
        
        result = manager.reschedule_messages('test_user_123', 'motivation')
        
        # Verify request file was created
        assert mock_open.called, "Should create reschedule request file"
        assert result is True, "Should return True on success"
        # Verify JSON was written
        mock_file.write.assert_called()
    
    @pytest.mark.behavior
    @pytest.mark.behavior
    @pytest.mark.file_io
    def test_main_function_start_action(self, test_data_dir):
        """Test main function with start action."""
        with patch('argparse.ArgumentParser') as mock_parser_class:
            mock_parser = Mock()
            mock_args = Mock()
            mock_args.action = 'start'
            mock_parser.parse_args.return_value = mock_args
            mock_parser_class.return_value = mock_parser
            
            with patch('core.headless_service.HeadlessServiceManager') as mock_manager_class:
                mock_manager = Mock()
                mock_manager.start_headless_service.return_value = True
                mock_manager_class.return_value = mock_manager
                
                with patch('sys.exit') as mock_exit:
                    from core.headless_service import main
                    main()
            
            # Verify manager was created and start was called
            mock_manager_class.assert_called_once()
            mock_manager.start_headless_service.assert_called_once()
            mock_exit.assert_called_once_with(0)
    
    @pytest.mark.behavior
    @pytest.mark.behavior
    @pytest.mark.file_io
    def test_main_function_stop_action(self, test_data_dir):
        """Test main function with stop action."""
        with patch('argparse.ArgumentParser') as mock_parser_class:
            mock_parser = Mock()
            mock_args = Mock()
            mock_args.action = 'stop'
            mock_parser.parse_args.return_value = mock_args
            mock_parser_class.return_value = mock_parser
            
            with patch('core.headless_service.HeadlessServiceManager') as mock_manager_class:
                mock_manager = Mock()
                mock_manager.stop_headless_service.return_value = True
                mock_manager_class.return_value = mock_manager
                
                with patch('sys.exit') as mock_exit:
                    from core.headless_service import main
                    main()
            
            # Verify manager was created and stop was called
            mock_manager_class.assert_called_once()
            mock_manager.stop_headless_service.assert_called_once()
            mock_exit.assert_called_once_with(0)
    
    @pytest.mark.behavior
    @pytest.mark.behavior
    @pytest.mark.file_io
    def test_main_function_status_action(self, test_data_dir):
        """Test main function with status action."""
        with patch('argparse.ArgumentParser') as mock_parser_class:
            mock_parser = Mock()
            mock_args = Mock()
            mock_args.action = 'status'
            mock_parser.parse_args.return_value = mock_args
            mock_parser_class.return_value = mock_parser
            
            with patch('core.headless_service.HeadlessServiceManager') as mock_manager_class:
                mock_manager = Mock()
                mock_manager.get_headless_service_status.return_value = (True, 12345)
                mock_manager_class.return_value = mock_manager
                
                with patch('builtins.print') as mock_print:
                    from core.headless_service import main
                    main()
            
            # Verify manager was created and status was checked
            mock_manager_class.assert_called_once()
            mock_manager.get_headless_service_status.assert_called_once()
            mock_print.assert_called()
    
    @pytest.mark.behavior
    @pytest.mark.behavior
    @pytest.mark.file_io
    def test_main_function_info_action(self, test_data_dir):
        """Test main function with info action."""
        with patch('argparse.ArgumentParser') as mock_parser_class:
            mock_parser = Mock()
            mock_args = Mock()
            mock_args.action = 'info'
            mock_parser.parse_args.return_value = mock_args
            mock_parser_class.return_value = mock_parser
            
            with patch('core.headless_service.HeadlessServiceManager') as mock_manager_class:
                mock_manager = Mock()
                mock_manager.get_service_info.return_value = {
                    'total_services': 1,
                    'headless_services': [],
                    'ui_services': [],
                    'can_start_headless': True,
                    'is_headless_running': False,
                    'is_ui_running': False
                }
                mock_manager_class.return_value = mock_manager
                
                with patch('builtins.print') as mock_print:
                    from core.headless_service import main
                    main()
            
            # Verify manager was created and info was retrieved
            mock_manager_class.assert_called_once()
            mock_manager.get_service_info.assert_called_once()
            assert mock_print.call_count >= 5, "Should print multiple info lines"
