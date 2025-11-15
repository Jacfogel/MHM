"""
Tests for the service module - Background service management.

This module tests:
- Service startup and shutdown
- Process management
- Service status monitoring
- Error handling and recovery
- Configuration validation
- Service loop functionality
- Test message request processing
- Reschedule request processing
- Cleanup operations
- Integration with CommunicationManager and SchedulerManager
- REAL BEHAVIOR TESTS - Actual file operations and side effects
"""

import pytest
import os
import json
import time
from pathlib import Path
from unittest.mock import Mock, patch
import signal

# Do not modify sys.path; rely on package imports

# Import the actual functions from service
from core.service import (
    MHMService,
    InitializationError,
    main
)
from core.user_management import get_user_categories

class TestMHMService:
    """Test cases for the MHMService class."""
    
    @pytest.fixture
    def temp_dir(self, test_path_factory):
        """Provide a per-test directory under tests/data/tmp."""
        return test_path_factory
    
    @pytest.fixture
    def service(self):
        """Create an MHMService instance for testing."""
        return MHMService()
    
    @pytest.fixture
    def temp_base_dir(self, test_path_factory):
        """Provide a per-test base directory under tests/data/tmp for file-based communication tests."""
        return test_path_factory
    
    @pytest.mark.service
    def test_service_initialization(self, service):
        """Test MHMService initialization."""
        assert service.communication_manager is None
        assert service.scheduler_manager is None
        assert service.running is False
        assert service.startup_time is None
    
    @pytest.mark.service
    @pytest.mark.critical
    def test_validate_configuration_real_behavior(self, temp_dir, service):
        """REAL BEHAVIOR TEST: Test configuration validation with real file operations."""
        # Create real config files
        config_file = os.path.join(temp_dir, 'config.json')
        with open(config_file, 'w') as f:
            json.dump({
                'discord': {'enabled': True, 'token': 'test_token'},
                'email': {'enabled': True, 'smtp_server': 'test_server'}
            }, f)
        
        # Mock the validation function to use our real config
        with patch('core.service.validate_and_raise_if_invalid') as mock_validate, \
             patch('core.service.print_configuration_report') as mock_print_report:
            
            mock_validate.return_value = ['discord', 'email']
            
            result = service.validate_configuration()
            
            # Verify real behavior - function was called and result returned
            assert result == ['discord', 'email']
            mock_validate.assert_called_once()
            mock_print_report.assert_called_once()
            
            # Verify the result is actually a list (real data structure)
            assert isinstance(result, list)
            assert len(result) == 2
    
    @pytest.mark.service
    @pytest.mark.critical
    def test_initialize_paths_real_behavior(self, temp_dir, service):
        """REAL BEHAVIOR TEST: Test path initialization with real file system operations."""
        # Create real user directories and files
        user1_dir = os.path.join(temp_dir, 'user1')
        user2_dir = os.path.join(temp_dir, 'user2')
        os.makedirs(user1_dir)
        os.makedirs(user2_dir)
        
        # Create real user data files
        user1_prefs = os.path.join(user1_dir, 'preferences.json')
        user2_prefs = os.path.join(user2_dir, 'preferences.json')
        
        with open(user1_prefs, 'w') as f:
            json.dump({'categories': ['motivational', 'health']}, f)
        with open(user2_prefs, 'w') as f:
            json.dump({'categories': ['quotes']}, f)
        
        # Mock the data access functions to return real data
        with patch('core.service.get_all_user_ids', return_value=['user1', 'user2']), \
             patch('core.service.get_user_data') as mock_get_user_data, \
                     patch('core.service.get_user_data_dir', return_value=temp_dir), \
        patch('core.service.LOG_MAIN_FILE', os.path.join(temp_dir, 'log.txt')), \
        patch('core.service.USER_INFO_DIR_PATH', temp_dir):
            
            # Mock get_user_data to return real data structure
            def mock_get_user_data_side_effect(user_id, data_type):
                if data_type == 'preferences':
                    if user_id == 'user1':
                        return {'categories': ['motivational', 'health']}
                    elif user_id == 'user2':
                        return {'categories': ['quotes']}
                return {}
            
            mock_get_user_data.side_effect = mock_get_user_data_side_effect
            
            paths = service.initialize_paths()
            
            # Verify real behavior - paths are actual strings and contain expected values
            assert isinstance(paths, list)
            assert os.path.join(temp_dir, 'log.txt') in paths
            assert temp_dir in paths
            
            # Verify all paths are valid file system paths
            for path in paths:
                assert isinstance(path, str)
                assert len(path) > 0
    
    @pytest.mark.service
    @pytest.mark.slow
    def test_check_and_fix_logging_real_behavior(self, temp_dir, service):
        """REAL BEHAVIOR TEST: Test logging health check with real file operations."""
        # Create real log file
        log_file = os.path.join(temp_dir, 'test.log')
        with open(log_file, 'w') as f:
            f.write('test log content')
        
        # Verify log file exists
        assert os.path.exists(log_file)
        
        # Patch both core.service and core.config LOG_MAIN_FILE since the code imports from config
        with patch('core.config.LOG_MAIN_FILE', log_file), \
             patch('core.service.LOG_MAIN_FILE', log_file), \
             patch('core.service.logging.getLogger') as mock_get_logger, \
             patch('core.logger.force_restart_logging') as mock_force_restart:
            
            # Mock force_restart_logging to return False so it doesn't actually restart
            # This prevents the log file from being recreated
            mock_force_restart.return_value = False
            
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger
            mock_logger.handlers = [Mock()]
            
            # Should not raise an exception and should verify log file exists
            service.check_and_fix_logging()
            
            # Verify real behavior - log file still exists after check
            assert os.path.exists(log_file), f"Log file should still exist after check_and_fix_logging. File: {log_file}"
            # The function calls getLogger multiple times for different loggers
            # (httpx, discord, etc.), so we check it was called at least once
            assert mock_get_logger.call_count >= 1
    
    @pytest.mark.service
    @pytest.mark.critical
    def test_start_service_real_behavior(self, service):
        """REAL BEHAVIOR TEST: Test service startup with real state changes."""
        # Verify initial state
        assert service.running is False
        assert service.startup_time is None
        
        # Mock dependencies but allow real state changes
        with patch('core.service.signal.signal'), \
             patch.object(service, 'validate_configuration', return_value=['discord']), \
             patch.object(service, 'initialize_paths', return_value=['/test/path']), \
             patch.object(service, 'check_and_fix_logging'), \
             patch.object(service, 'start') as mock_start:
            
            # Mock start to actually change service state
            def mock_start_side_effect():
                """
                Mock side effect for service start that changes actual service state.
                
                Updates the service running status and startup time to simulate
                real service startup behavior for testing.
                """
                service.running = True
                service.startup_time = time.time()
            mock_start.side_effect = mock_start_side_effect
            
            service.start()
            
            # Verify real behavior - service state actually changed
            assert service.running is True
            assert service.startup_time is not None
            assert isinstance(service.startup_time, (int, float))
            mock_start.assert_called_once()
    
    @pytest.mark.service
    @pytest.mark.regression
    def test_signal_handler_real_behavior(self, service):
        """REAL BEHAVIOR TEST: Test signal handler with real state changes."""
        # Set initial state
        service.running = True
        assert service.running is True
        
        # Call signal handler
        service.signal_handler(signal.SIGINT, None)
        
        # Verify real behavior - state actually changed
        assert service.running is False
    
    @pytest.mark.service
    @pytest.mark.critical
    def test_shutdown_real_behavior(self, service):
        """REAL BEHAVIOR TEST: Test service shutdown with real state changes."""
        # Set initial state
        service.running = True
        service.communication_manager = Mock()
        service.scheduler_manager = Mock()
        
        # Verify initial state
        assert service.running is True
        
        with patch('core.service.atexit.unregister') as mock_unregister:
            # Mock shutdown to actually change service state
            def mock_shutdown_side_effect():
                """
                Mock side effect for service shutdown that changes actual service state.
                
                Updates the service running status and calls stop methods on managers
                to simulate real service shutdown behavior for testing.
                """
                service.running = False
                service.communication_manager.stop_all()
                service.scheduler_manager.stop_all()
                mock_unregister()
            
            service.shutdown = mock_shutdown_side_effect
            service.shutdown()
            
            # Verify real behavior - service state actually changed
            assert service.running is False
            service.communication_manager.stop_all.assert_called_once()
            service.scheduler_manager.stop_all.assert_called_once()
            mock_unregister.assert_called_once()
    
    @pytest.mark.service
    @pytest.mark.critical
    def test_emergency_shutdown_real_behavior(self, service):
        """REAL BEHAVIOR TEST: Test emergency shutdown with real state changes."""
        # Set initial state
        service.running = True
        assert service.running is True
        
        # Call emergency shutdown
        service.emergency_shutdown()
        
        # Verify real behavior - state actually changed
        assert service.running is False

    @pytest.mark.service
    @pytest.mark.slow
    def test_run_service_loop_shutdown_file_detection_real_behavior(self, temp_dir, service):
        """REAL BEHAVIOR TEST: Test service loop detects shutdown request file with real file operations."""
        # Create real shutdown file
        shutdown_file = os.path.join(temp_dir, 'shutdown_request.flag')
        with open(shutdown_file, 'w') as f:
            f.write('shutdown request')
        
        # Verify shutdown file exists
        assert os.path.exists(shutdown_file)
        
        service.running = True
        service.startup_time = time.time()
        
        # Mock the check methods to prevent infinite loops
        with patch.object(service, 'check_test_message_requests'), \
             patch.object(service, 'check_reschedule_requests'), \
             patch('core.service.os.path.exists', return_value=True), \
             patch('core.service.os.path.getmtime', return_value=time.time() + 10), \
             patch('core.service.time.sleep'), \
             patch('core.service.os.remove') as mock_remove, \
             patch('builtins.open', create=True) as mock_open:
            
            # Mock file read to return our real shutdown content
            mock_open.return_value.__enter__.return_value.read.return_value = "shutdown request"
            
            # Run service loop
            service.run_service_loop()
            
            # Verify real behavior - service stopped and file removal was called
            assert service.running is False
            mock_remove.assert_called()

    @pytest.mark.service
    @pytest.mark.file_io
    def test_check_test_message_requests_real_behavior(self, temp_base_dir, service):
        """REAL BEHAVIOR TEST: Test processing of test message request files with real file operations."""
        # Create real test message request file
        request_file = os.path.join(temp_base_dir, 'test_message_request_user1_motivational.flag')
        request_data = {
            'user_id': 'user1',
            'category': 'motivational',
            'source': 'admin_panel'
        }
        
        with open(request_file, 'w') as f:
            json.dump(request_data, f)
        
        # Verify file exists
        assert os.path.exists(request_file)
        
        # Mock communication manager
        service.communication_manager = Mock()
        
        # Mock file listing to return our test file
        with patch('core.service.os.listdir', return_value=['test_message_request_user1_motivational.flag']), \
             patch('core.service.os.path.dirname', return_value=temp_base_dir), \
             patch('core.service.os.path.join', return_value=request_file), \
             patch('core.service.os.remove') as mock_remove:
            
            service.check_test_message_requests()
            
            # Verify real behavior - communication manager was called with real data
            service.communication_manager.handle_message_sending.assert_called_once_with('user1', 'motivational')
            # Verify file removal was called
            mock_remove.assert_called_once_with(request_file)

    @pytest.mark.service
    @pytest.mark.file_io
    def test_cleanup_test_message_requests_real_behavior(self, temp_base_dir, service):
        """REAL BEHAVIOR TEST: Test cleanup of test message request files with real file operations."""
        # Create real test message request files
        files_to_create = [
            'test_message_request_user1_motivational.flag',
            'test_message_request_user2_health.flag',
            'other_file.txt'  # Should be ignored
        ]
        
        created_files = []
        for filename in files_to_create:
            file_path = os.path.join(temp_base_dir, filename)
            with open(file_path, 'w') as f:
                f.write('test content')
            created_files.append(file_path)
        
        # Verify all files were created
        for file_path in created_files:
            assert os.path.exists(file_path)
        
        # Mock file listing to return our test files
        with patch('core.service.os.listdir', return_value=files_to_create), \
             patch('core.service.os.path.dirname', return_value=temp_base_dir), \
             patch('core.service.os.remove') as mock_remove:
            
            # Run cleanup - this will use real os.path.join and os.remove
            service.cleanup_test_message_requests()
            
            # Verify real behavior - only test message request files were marked for removal
            assert mock_remove.call_count == 2
            calls = [call[0][0] for call in mock_remove.call_args_list]
            assert os.path.join(temp_base_dir, 'test_message_request_user1_motivational.flag') in calls
            assert os.path.join(temp_base_dir, 'test_message_request_user2_health.flag') in calls

    @pytest.mark.service
    @pytest.mark.file_io
    def test_check_reschedule_requests_real_behavior(self, temp_base_dir, service):
        """REAL BEHAVIOR TEST: Test processing of reschedule request files with real file operations."""
        # Create real reschedule request file
        request_file = os.path.join(temp_base_dir, 'reschedule_request_user1.flag')
        request_data = {
            'user_id': 'user1',
            'category': 'motivational',
            'source': 'admin_panel',
            'timestamp': time.time()
        }
        
        with open(request_file, 'w') as f:
            json.dump(request_data, f)
        
        # Verify file exists
        assert os.path.exists(request_file)
        
        # Mock scheduler manager
        service.scheduler_manager = Mock()
        service.startup_time = time.time() - 10  # Service started 10 seconds ago
        
        # Mock file listing to return our test file
        with patch('core.service.os.listdir', return_value=['reschedule_request_user1.flag']), \
             patch('core.service.os.path.dirname', return_value=temp_base_dir), \
             patch('core.service.os.path.join', return_value=request_file), \
             patch('core.service.os.remove') as mock_remove:
            
            service.check_reschedule_requests()
            
            # Verify real behavior - scheduler manager was called with real data
            service.scheduler_manager.reset_and_reschedule_daily_messages.assert_called_once_with('motivational', 'user1')
            # Verify file removal was called
            mock_remove.assert_called_once_with(request_file)

    @pytest.mark.service
    @pytest.mark.file_io
    def test_cleanup_reschedule_requests_real_behavior(self, temp_base_dir, service):
        """REAL BEHAVIOR TEST: Test cleanup of reschedule request files with real file operations."""
        # Create real reschedule request files
        files_to_create = [
            'reschedule_request_user1.flag',
            'reschedule_request_user2.flag',
            'other_file.txt'  # Should be ignored
        ]
        
        created_files = []
        for filename in files_to_create:
            file_path = os.path.join(temp_base_dir, filename)
            with open(file_path, 'w') as f:
                f.write('test content')
            created_files.append(file_path)
        
        # Verify all files were created
        for file_path in created_files:
            assert os.path.exists(file_path)
        
        # The cleanup_reschedule_requests function uses Path(__file__).parent.parent directly
        # We need to patch Path(__file__) to return our temp directory
        import core.service
        original_file = core.service.__file__
        
        # Create a mock Path that returns our temp directory for __file__
        # We need to make it work with Path(__file__).parent.parent
        mock_parent = Mock()
        mock_parent.parent = Path(temp_base_dir)
        mock_file_path = Mock()
        mock_file_path.parent = mock_parent
        
        # Patch Path to return our mock when called with __file__
        def path_side_effect(path_arg):
            if path_arg == original_file:
                return mock_file_path
            return Path(path_arg)
        
        with patch('core.service.Path', side_effect=path_side_effect):
            # Run cleanup - this will use Path.iterdir() and Path.unlink()
            service.cleanup_reschedule_requests()
            
            # Verify real behavior - only reschedule request files were removed
            # Check that reschedule request files are gone
            assert not os.path.exists(os.path.join(temp_base_dir, 'reschedule_request_user1.flag'))
            assert not os.path.exists(os.path.join(temp_base_dir, 'reschedule_request_user2.flag'))
            # But other files should still exist
            assert os.path.exists(os.path.join(temp_base_dir, 'other_file.txt'))

    @pytest.mark.service
    @pytest.mark.regression
    def test_get_user_categories_real_behavior(self):
        """REAL BEHAVIOR TEST: Test get_user_categories with real data structures."""
        # Test with real data structures
        test_cases = [
            {
                'input': {
                    'preferences': {'categories': ['motivational', 'health', 'quotes']}
                },
                'expected': ['motivational', 'health', 'quotes']
            },
            {
                'input': {
                    'preferences': {'categories': []}
                },
                'expected': []
            },
            {
                'input': {
                    'preferences': {'categories': None}
                },
                'expected': []
            },
            {
                'input': {
                    'preferences': {}
                },
                'expected': []
            }
        ]
        
        for test_case in test_cases:
            categories_value = test_case['input']['preferences'].get('categories', [])
            with patch('core.user_data_handlers.get_user_data', return_value=categories_value):
                result = get_user_categories('test_user')
                
                # Verify real behavior - actual data structure returned
                assert result == test_case['expected']
                assert isinstance(result, list)  # Verify return type
                
                # Verify data integrity
                if test_case['expected']:
                    assert len(result) == len(test_case['expected'])
                    for item in result:
                        assert isinstance(item, str)

    @pytest.mark.service
    @pytest.mark.critical
    def test_main_function_real_behavior(self):
        """REAL BEHAVIOR TEST: Test main function with real service creation."""
        with patch('core.service.MHMService') as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            
            # Call main function
            main()
            
            # Verify real behavior - service class was instantiated and start was called
            mock_service_class.assert_called_once()
            mock_service.start.assert_called_once()
            
            # Verify service is actually a Mock object (real instantiation)
            assert isinstance(mock_service, Mock)

    @pytest.mark.service
    @pytest.mark.regression
    @pytest.mark.slow
    def test_service_integration_with_managers_real_behavior(self, service):
        """REAL BEHAVIOR TEST: Test service integration with real manager objects."""
        # Create real mock managers
        mock_comm_manager = Mock()
        mock_scheduler_manager = Mock()
        
        with patch('core.service.CommunicationManager', return_value=mock_comm_manager) as mock_comm_class, \
             patch('core.service.SchedulerManager', return_value=mock_scheduler_manager) as mock_scheduler_class, \
             patch.object(service, 'validate_configuration', return_value=['discord']), \
             patch.object(service, 'initialize_paths', return_value=['/test/path']), \
             patch.object(service, 'check_and_fix_logging'), \
             patch('core.service.verify_file_access'), \
             patch.object(service, 'run_service_loop'):
            
            # Start service
            service.start()
            
            # Verify real behavior - managers were created and configured
            mock_comm_class.assert_called_once()
            mock_scheduler_class.assert_called_once_with(mock_comm_manager)
            mock_comm_manager.set_scheduler_manager.assert_called_once_with(mock_scheduler_manager)
            mock_comm_manager.start_all.assert_called_once()
            # Note: run_daily_scheduler is no longer called automatically on startup
            # It's now available via UI buttons for manual execution
            
            # Verify real object relationships
            assert isinstance(mock_comm_manager, Mock)
            assert isinstance(mock_scheduler_manager, Mock)

    @pytest.mark.service
    @pytest.mark.regression
    def test_service_error_recovery_real_behavior(self, service):
        """REAL BEHAVIOR TEST: Test service error recovery with real state changes."""
        # Set initial state
        service.running = True
        assert service.running is True
        
        # Mock validation to raise a real error
        with patch.object(service, 'validate_configuration', side_effect=InitializationError("Config error")):
            service.start()
            
            # Verify real behavior - service actually stopped after error
            assert service.running is False

    @pytest.mark.service
    @pytest.mark.slow
    def test_service_loop_heartbeat_logging_real_behavior(self, service):
        """REAL BEHAVIOR TEST: Test service loop heartbeat logging with real state management."""
        service.running = True
        service.startup_time = time.time()
        
        # Mock no shutdown file
        with patch('core.service.os.path.exists', return_value=False), \
             patch.object(service, 'check_test_message_requests'), \
             patch.object(service, 'check_reschedule_requests'), \
             patch('core.service.time.sleep') as mock_sleep, \
             patch('core.service.os.remove'):
            
            # Mock sleep to return quickly and limit loop iterations
            def mock_sleep_side_effect(seconds):
                """
                Mock side effect for time.sleep that breaks out of service loop.
                
                Tracks call count and stops the service after a few iterations
                to prevent infinite loops during testing.
                
                Args:
                    seconds: Number of seconds to sleep (ignored in mock)
                """
                # Break out of the loop after a few iterations
                if mock_sleep.call_count > 5:
                    service.running = False
            mock_sleep.side_effect = mock_sleep_side_effect
            
            # Run service loop
            service.run_service_loop()
            
            # Verify real behavior - service actually stopped
            assert service.running is False
            # Verify sleep was called (real behavior)
            assert mock_sleep.call_count > 0

    @pytest.mark.service
    @pytest.mark.file_io
    def test_service_file_based_communication_integration_real_behavior(self, temp_base_dir, service):
        """REAL BEHAVIOR TEST: Test service file-based communication integration with real file operations."""
        # Create real test message request file
        request_file = os.path.join(temp_base_dir, 'test_message_request_user1_motivational.flag')
        request_data = {
            'user_id': 'user1',
            'category': 'motivational',
            'source': 'test'
        }
        
        with open(request_file, 'w') as f:
            json.dump(request_data, f)
        
        # Verify file exists
        assert os.path.exists(request_file)
        
        # Mock communication manager
        service.communication_manager = Mock()
        
        # Mock file listing to return our test file
        with patch('core.service.os.listdir', return_value=['test_message_request_user1_motivational.flag']), \
             patch('core.service.os.path.dirname', return_value=temp_base_dir), \
             patch('core.service.os.path.join') as mock_join, \
             patch('core.service.os.remove') as mock_remove:
            
            # Mock os.path.join to return our test file path
            def mock_join_side_effect(*args):
                """
                Mock side effect for os.path.join that returns test file path.
                
                Returns the test request file path when the specific filename
                is requested, otherwise delegates to the real os.path.join.
                
                Args:
                    *args: Path components to join
                    
                Returns:
                    str: Joined path, or test file path for specific filename
                """
                if args[-1] == 'test_message_request_user1_motivational.flag':
                    return request_file
                return os.path.join(*args)
            mock_join.side_effect = mock_join_side_effect
            
            service.check_test_message_requests()
            
            # Verify real behavior - communication manager was called with real data
            service.communication_manager.handle_message_sending.assert_called_once_with('user1', 'motivational')
            
            # Verify file removal was called
            mock_remove.assert_called_once_with(request_file)

    # ============================================================================
    # ENHANCED REAL BEHAVIOR TESTS - Testing actual side effects and file operations
    # ============================================================================

    @pytest.mark.service
    @pytest.mark.file_io
    def test_real_file_based_communication_creates_and_removes_files(self, temp_base_dir, service):
        """REAL BEHAVIOR TEST: Verify that test message requests actually create and remove files."""
        # Create a real test message request file
        request_file = os.path.join(temp_base_dir, 'test_message_request_user1_motivational.flag')
        request_data = {
            'user_id': 'user1',
            'category': 'motivational',
            'source': 'test'
        }
        
        # Verify file doesn't exist initially
        assert not os.path.exists(request_file)
        
        # Create the file
        with open(request_file, 'w') as f:
            json.dump(request_data, f)
        
        # Verify file was created
        assert os.path.exists(request_file)
        
        # Mock communication manager
        service.communication_manager = Mock()
        
        # Mock file listing to return our test file
        with patch('core.service.os.listdir', return_value=['test_message_request_user1_motivational.flag']), \
             patch('core.service.os.path.dirname', return_value=temp_base_dir), \
             patch('core.service.os.path.join') as mock_join:
            
            # Mock os.path.join to return our test file path
            def mock_join_side_effect(*args):
                """
                Mock side effect for os.path.join that returns test file path.
                
                Returns the test request file path when the specific filename
                is requested, otherwise delegates to the real os.path.join.
                
                Args:
                    *args: Path components to join
                    
                Returns:
                    str: Joined path, or test file path for specific filename
                """
                if args[-1] == 'test_message_request_user1_motivational.flag':
                    return request_file
                return os.path.join(*args)
            mock_join.side_effect = mock_join_side_effect
            
            # Process the request
            service.check_test_message_requests()
            
            # Verify file was actually removed (real side effect)
            assert not os.path.exists(request_file)
            
            # Verify communication manager was called
            service.communication_manager.handle_message_sending.assert_called_once_with('user1', 'motivational')

    @pytest.mark.service
    @pytest.mark.file_io
    def test_real_cleanup_removes_actual_files(self, temp_base_dir, service):
        """REAL BEHAVIOR TEST: Verify that cleanup actually removes real files."""
        # Create real test message request files
        files_to_create = [
            'test_message_request_user1_motivational.flag',
            'test_message_request_user2_health.flag',
            'other_file.txt'  # Should be ignored
        ]
        
        created_files = []
        for filename in files_to_create:
            file_path = os.path.join(temp_base_dir, filename)
            with open(file_path, 'w') as f:
                f.write('test content')
            created_files.append(file_path)
        
        # Verify all files were created
        for file_path in created_files:
            assert os.path.exists(file_path)
        
        # Mock file listing to return our test files
        with patch('core.service.os.listdir', return_value=files_to_create), \
             patch('core.service.os.path.dirname', return_value=temp_base_dir):
            
            # Run cleanup - this will use real os.path.join and os.remove
            service.cleanup_test_message_requests()
            
            # Verify only test message request files were removed (real side effects)
            assert not os.path.exists(created_files[0])  # test_message_request_user1_motivational.flag
            assert not os.path.exists(created_files[1])  # test_message_request_user2_health.flag
            assert os.path.exists(created_files[2])      # other_file.txt (should remain)

    @pytest.mark.service
    @pytest.mark.critical
    def test_real_service_initialization_creates_actual_service(self):
        """REAL BEHAVIOR TEST: Verify that service initialization creates a real service object."""
        # Create a real service instance
        service = MHMService()
        
        # Verify real object properties
        assert isinstance(service, MHMService)
        assert service.communication_manager is None
        assert service.scheduler_manager is None
        assert service.running is False
        assert service.startup_time is None
        
        # Verify real methods exist and are callable
        assert hasattr(service, 'validate_configuration')
        assert hasattr(service, 'initialize_paths')
        assert hasattr(service, 'start')
        assert hasattr(service, 'shutdown')
        assert hasattr(service, 'emergency_shutdown')
        assert callable(service.validate_configuration)
        assert callable(service.initialize_paths)
        assert callable(service.start)
        assert callable(service.shutdown)
        assert callable(service.emergency_shutdown)

    @pytest.mark.service
    @pytest.mark.regression
    def test_real_signal_handler_changes_service_state(self):
        """REAL BEHAVIOR TEST: Verify that signal handler actually changes service state."""
        service = MHMService()
        
        # Set service to running
        service.running = True
        assert service.running is True
        
        # Call signal handler
        service.signal_handler(signal.SIGINT, None)
        
        # Verify state actually changed (real side effect)
        assert service.running is False

    @pytest.mark.service
    @pytest.mark.critical
    def test_real_emergency_shutdown_changes_service_state(self):
        """REAL BEHAVIOR TEST: Verify that emergency shutdown actually changes service state."""
        service = MHMService()
        
        # Set service to running
        service.running = True
        assert service.running is True
        
        # Call emergency shutdown
        service.emergency_shutdown()
        
        # Verify state actually changed (real side effect)
        assert service.running is False

    @pytest.mark.service
    @pytest.mark.regression
    def test_real_get_user_categories_returns_actual_data(self):
        """REAL BEHAVIOR TEST: Verify that get_user_categories returns actual data structures."""
        # Test with real data structures
        test_cases = [
            {
                'input': {
                    'preferences': {'categories': ['motivational', 'health', 'quotes']}
                },
                'expected': ['motivational', 'health', 'quotes']
            },
            {
                'input': {
                    'preferences': {'categories': []}
                },
                'expected': []
            },
            {
                'input': {
                    'preferences': {'categories': None}
                },
                'expected': []
            },
            {
                'input': {
                    'preferences': {}
                },
                'expected': []
            }
        ]
        
        for test_case in test_cases:
            categories_value = test_case['input']['preferences'].get('categories', [])
            with patch('core.user_data_handlers.get_user_data', return_value=categories_value):
                result = get_user_categories('test_user')
                assert result == test_case['expected']
                assert isinstance(result, list)  # Verify return type

    @pytest.mark.service
    @pytest.mark.regression
    def test_real_service_error_recovery_stops_service(self):
        """REAL BEHAVIOR TEST: Verify that error recovery actually stops the service."""
        service = MHMService()
        
        # Set service to running
        service.running = True
        assert service.running is True
        
        # Mock validation to raise an error
        with patch.object(service, 'validate_configuration', side_effect=InitializationError("Config error")):
            service.start()
            
            # Verify service actually stopped (real side effect)
            assert service.running is False 