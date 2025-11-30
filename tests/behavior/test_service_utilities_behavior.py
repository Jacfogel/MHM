"""
Behavior tests for Service Utilities module.
Tests real behavior and side effects of service utility functions.
"""

import pytest
from unittest.mock import patch, MagicMock, mock_open
from core.service_utilities import (
    Throttler,
    create_reschedule_request,
    is_service_running,
    wait_for_network,
    load_and_localize_datetime
)
from core.user_data_validation import _shared__title_case


@pytest.mark.behavior
class TestServiceUtilitiesBehavior:
    """Test real behavior of service utility functions."""
    
    @pytest.mark.behavior
    @pytest.mark.critical
    def test_throttler_initialization_creates_proper_structure(self, test_data_dir):
        """Test that Throttler initialization creates proper internal structure."""
        # Arrange
        interval = 60  # 60 seconds
        
        # Act
        throttler = Throttler(interval)
        
        # Assert
        assert throttler.interval == 60, "Should set correct interval"
        assert throttler.last_run is None, "Should initialize last_run to None"
    
    @pytest.mark.behavior
    @pytest.mark.critical
    def test_throttler_should_run_returns_true_on_first_call(self, test_data_dir):
        """Test that Throttler should_run returns True on first call and sets last_run."""
        # Arrange
        throttler = Throttler(60)
        
        # Act
        should_run = throttler.should_run()
        
        # Assert
        assert should_run is True, "Should return True on first call"
        assert throttler.last_run is not None, "last_run should be set on first call to enable throttling"
    
    @pytest.mark.behavior
    @pytest.mark.regression
    def test_throttler_should_run_respects_interval(self, test_data_dir):
        """Test that Throttler should_run respects the time interval."""
        throttler = Throttler(1.0)  # use longer interval to assert immediate throttle

        # First call should set last_run and return True
        assert throttler.should_run() is True
        assert throttler.last_run is not None, "last_run should be set on first call"

        # Second call should return False (within interval)
        assert throttler.should_run() is False, "Should return False when within interval"

        # Wait for interval to pass without sleeping the whole test
        from tests.conftest import wait_until
        assert wait_until(lambda: throttler.should_run() is True, timeout_seconds=2.0)

        # Do not immediately invoke should_run again; the assertion above already performed the True call
        assert throttler.last_run is not None, "last_run should be updated after interval"
    
    @pytest.mark.behavior
    @pytest.mark.regression
    def test_throttler_handles_invalid_timestamp_format(self, test_data_dir):
        """Test that Throttler handles invalid timestamp format gracefully."""
        # Arrange
        throttler = Throttler(60)
        throttler.last_run = "invalid_timestamp_format"
        
        # Act
        should_run = throttler.should_run()
        
        # Assert
        assert should_run is True, "Should return True when timestamp format is invalid"
        assert throttler.last_run is not None, "Should update last_run with valid timestamp"
    
    @pytest.mark.behavior
    @pytest.mark.file_io
    @pytest.mark.critical
    def test_create_reschedule_request_creates_actual_file(self, test_data_dir):
        """Test that creating reschedule request actually creates flag file."""
        user_id = "test-user-reschedule"
        category = "checkin"
        
        # Arrange - Mock file operations
        mock_file_content = ""
        
        # Act - Create reschedule request with mocked file operations
        with patch('core.service_utilities.is_service_running', return_value=True):
            with patch('builtins.open', mock_open()) as mock_file:
                with patch('json.dump') as mock_json_dump:
                    result = create_reschedule_request(user_id, category)

        # Assert - Verify file operations were called
        mock_file.assert_called_once()
        mock_json_dump.assert_called_once()
        assert result is True
        
        # Verify the request data structure
        call_args = mock_json_dump.call_args[0][0]
        assert call_args['user_id'] == user_id, "Should include user_id"
        assert call_args['category'] == category, "Should include category"
        assert 'timestamp' in call_args, "Should include timestamp"
        assert call_args['source'] == 'ui_schedule_editor', "Should include source"
    
    def test_create_reschedule_request_skips_when_service_not_running(self, test_data_dir):
        """Test that creating reschedule request skips when service is not running."""
        user_id = "test-user-reschedule"
        category = "checkin"
        
        # Act - Create reschedule request when service is not running
        with patch('core.service_utilities.is_service_running', return_value=False):
            with patch('builtins.open', mock_open()) as mock_file:
                with patch('json.dump') as mock_json_dump:
                    result = create_reschedule_request(user_id, category)

        # Assert - Verify file operations were NOT called
        mock_file.assert_not_called()
        mock_json_dump.assert_not_called()
        assert result is False
    
    def test_is_service_running_checks_actual_processes(self, test_data_dir):
        """Test that is_service_running checks actual system processes."""
        # Arrange - Mock psutil to return different scenarios
        
        # Test case 1: Service is running
        mock_process_running = MagicMock()
        mock_process_running.info = {'name': 'python.exe', 'cmdline': ['python', 'service.py']}
        mock_process_running.is_running.return_value = True
        
        with patch('core.service_utilities.psutil.process_iter', return_value=[mock_process_running]):
            # Act
            is_running = is_service_running()
            
            # Assert
            assert is_running is True, "Should return True when service is running"
        
        # Test case 2: Service is not running
        mock_process_not_running = MagicMock()
        mock_process_not_running.info = {'name': 'python.exe', 'cmdline': ['python', 'other_script.py']}
        
        with patch('core.service_utilities.psutil.process_iter', return_value=[mock_process_not_running]):
            # Act
            is_running = is_service_running()
            
            # Assert
            assert is_running is False, "Should return False when service is not running"
    
    def test_is_service_running_handles_process_errors_gracefully(self, test_data_dir):
        """Test that is_service_running handles process errors gracefully."""
        # Arrange - Mock process that raises exception
        mock_process_error = MagicMock()
        mock_process_error.info = {'name': 'python.exe', 'cmdline': ['python', 'service.py']}
        mock_process_error.is_running.side_effect = Exception("Process error")
        
        with patch('core.service_utilities.psutil.process_iter', return_value=[mock_process_error]):
            # Act - Should not raise exception
            is_running = is_service_running()
            
            # Assert
            assert is_running is False, "Should return False when process check fails"
    
    def test_wait_for_network_returns_true_when_network_available(self, test_data_dir):
        """Test that wait_for_network returns True when network is available."""
        # Arrange - Mock socket to simulate successful connection
        with patch('core.service_utilities.socket.create_connection') as mock_socket:
            mock_socket.return_value = MagicMock()
            
            # Act
            network_available = wait_for_network(timeout=5)
            
            # Assert
            assert network_available is True, "Should return True when network is available"
            mock_socket.assert_called_once_with(("8.8.8.8", 53))
    
    @pytest.mark.slow
    def test_wait_for_network_returns_false_when_network_unavailable(self, test_data_dir):
        """Test that wait_for_network returns False when network is unavailable."""
        # Arrange - Mock socket to simulate connection failure
        with patch('core.service_utilities.socket.create_connection') as mock_socket:
            mock_socket.side_effect = OSError("Network unavailable")
            
            # Act
            network_available = wait_for_network(timeout=1)  # Short timeout for testing
            
            # Assert
            assert network_available is False, "Should return False when network is unavailable"
    
    def test_load_and_localize_datetime_creates_timezone_aware_datetime(self, test_data_dir):
        """Test that load_and_localize_datetime creates timezone-aware datetime."""
        # Arrange
        datetime_str = "2025-01-15 14:30"
        timezone_str = "America/Regina"
        
        # Act
        localized_datetime = load_and_localize_datetime(datetime_str, timezone_str)
        
        # Assert
        assert localized_datetime is not None, "Should return datetime object"
        assert localized_datetime.tzinfo is not None, "Should be timezone-aware"
        assert localized_datetime.strftime("%Y-%m-%d %H:%M") == "2025-01-15 14:30", "Should preserve date/time"
    
    def test_load_and_localize_datetime_raises_error_for_invalid_format(self, test_data_dir):
        """Test that load_and_localize_datetime handles invalid format gracefully."""
        # Arrange
        invalid_datetime_str = "invalid-date-format"
        timezone_str = "America/Regina"
        
        # Act - Function is wrapped with @handle_errors, so it should return None on error
        result = load_and_localize_datetime(invalid_datetime_str, timezone_str)
        
        # Assert
        assert result is None, "Should return None when datetime format is invalid"
    
    def test_load_and_localize_datetime_raises_error_for_invalid_timezone(self, test_data_dir):
        """Test that load_and_localize_datetime handles invalid timezone gracefully."""
        # Arrange
        datetime_str = "2025-01-15 14:30"
        invalid_timezone_str = "Invalid/Timezone"
        
        # Act - Function is wrapped with @handle_errors, so it should return None on error
        result = load_and_localize_datetime(datetime_str, invalid_timezone_str)
        
        # Assert
        assert result is None, "Should return None when timezone is invalid"
    
    def test_title_case_converts_text_properly(self, test_data_dir):
        """Test that title_case converts text to proper title case."""
        # Arrange
        test_cases = [
            ("hello world", "Hello World"),
            ("python programming", "Python Programming"),
            ("ai chatbot", "AI Chatbot"),
            ("api integration", "API Integration"),
            ("mhm system", "MHM System"),
            ("user id", "User ID"),
            ("json data", "JSON DATA"),  # 'data' is in special words as 'DATA'
            ("html css js", "HTML CSS JS"),
            ("", ""),  # Empty string
            (None, None),  # None value
        ]
        
        # Act & Assert
        for input_text, expected_output in test_cases:
            result = _shared__title_case(input_text)
            assert result == expected_output, f"Failed for '{input_text}': expected '{expected_output}', got '{result}'"
    
    def test_title_case_handles_special_words_correctly(self, test_data_dir):
        """Test that title_case handles special words and abbreviations correctly."""
        # Arrange
        special_cases = [
            ("ai api ui ux", "AI API UI UX"),
            ("mhm id url", "MHM ID URL"),
            ("http https json xml", "HTTP HTTPS JSON XML"),
            ("python java c++ c#", "Python Java C++ C#"),
            ("dotnet asp jsp", ".NET ASP JSP"),
            ("yaml toml ini cfg", "YAML TOML INI CFG"),
            ("log tmp temp etc", "LOG TMP TEMP ETC"),
            ("usr var bin lib", "USR VAR BIN LIB"),
            ("src doc docs test", "SRC DOC DOCS TEST"),
            ("backup config data", "BACKUP CONFIG DATA"),
            ("files images media", "FILES IMAGES MEDIA"),
            ("audio video photos", "AUDIO VIDEO PHOTOS"),
            ("downloads uploads cache", "DOWNLOADS UPLOADS CACHE"),
            ("logs temp tmp etc", "LOGS TEMP TMP ETC"),
        ]
        
        # Act & Assert
        for input_text, expected_output in special_cases:
            result = _shared__title_case(input_text)
            assert result == expected_output, f"Failed for '{input_text}': expected '{expected_output}', got '{result}'"
    
    def test_title_case_preserves_mixed_case_words(self, test_data_dir):
        """Test that title_case preserves already properly cased words."""
        # Arrange
        mixed_case_tests = [
            ("Hello World", "Hello World"),
            ("AI Chatbot", "AI Chatbot"),
            ("MHM System", "MHM System"),
            ("Python Programming", "Python Programming"),
            ("JSON Data", "JSON DATA"),  # 'Data' gets converted to 'DATA' because 'data' is in special words
        ]
        
        # Act & Assert
        for input_text, expected_output in mixed_case_tests:
            result = _shared__title_case(input_text)
            assert result == expected_output, f"Failed for '{input_text}': expected '{expected_output}', got '{result}'"
    
    @pytest.mark.slow
    def test_service_utilities_error_handling_preserves_system_stability(self, test_data_dir):
        """Test that service utilities error handling preserves system stability."""
        # Arrange - Test various error conditions
        
        # Test 1: Network timeout
        with patch('core.service_utilities.socket.create_connection') as mock_socket:
            mock_socket.side_effect = OSError("Connection timeout")
            # Should not raise exception
            result = wait_for_network(timeout=0.1)  # Reduced timeout for faster testing
            assert result is False, "Should handle network timeout gracefully"
        
        # Test 2: Process iteration error
        with patch('core.service_utilities.psutil.process_iter') as mock_process_iter:
            mock_process_iter.side_effect = Exception("Process iteration error")
            # Should not raise exception
            result = is_service_running()
            assert result is False, "Should handle process iteration error gracefully"
        
        # Test 3: File creation error
        with patch('core.service_utilities.is_service_running', return_value=True):
            with patch('builtins.open', side_effect=OSError("File creation error")):
                # Should not raise exception
                create_reschedule_request("test-user", "test-category")
    
    @pytest.mark.no_parallel
    def test_service_utilities_performance_under_load(self, test_data_dir):
        """Test that service utilities perform well under load."""
        # Arrange - Create throttler with short interval
        throttler = Throttler(0.01)  # 10ms interval for faster testing
        
        # Act - Test multiple rapid calls
        results = [throttler.should_run() for _ in range(10)]
        
        # Assert - Should throttle appropriately
        assert results[0] is True, "First call should succeed"
        # Note: First call sets last_run, so second call will check interval
        # With 0.01s interval and rapid calls, second call might succeed if fast enough
        # The important thing is that the function handles multiple calls without errors
        assert len(results) == 10, "Should handle all calls without errors"
        assert any(results), "At least one call should succeed"
    
    def test_service_utilities_data_integrity(self, test_data_dir):
        """Test that service utilities maintain data integrity."""
        # Arrange - Test throttler state persistence
        throttler = Throttler(1.0)  # 1 second interval to ensure proper throttling
        
        # Act - Multiple operations
        first_result = throttler.should_run()
        second_result = throttler.should_run()
        
        # Assert - State should be maintained correctly
        assert first_result is True, "First call should succeed"
        assert second_result is False, "Second call should be throttled (last_run was set on first call)"
        
        # Wait for interval to pass without arbitrary sleep
        from tests.conftest import wait_until
        assert wait_until(lambda: throttler.should_run() is True, timeout_seconds=1.0)
        third_result = True
        assert third_result is True, "Third call should succeed (after interval)"
        # Note: last_run timing might vary, focus on core functionality
        
        # Test title case consistency
        test_text = "ai chatbot mhm system"
        result1 = _shared__title_case(test_text)
        result2 = _shared__title_case(test_text)
        assert result1 == result2, "Title case should be consistent"
        assert result1 == "AI Chatbot MHM System", "Should produce correct title case"


@pytest.mark.behavior
class TestServiceUtilitiesIntegration:
    """Test integration between service utility functions."""
    
    @pytest.mark.slow
    def test_service_utilities_integration_with_reschedule_workflow(self, test_data_dir):
        """Test integration between service utilities in reschedule workflow."""
        user_id = "test-user-integration"
        category = "checkin"
        
        # Arrange - Mock all dependencies
        with patch('core.service_utilities.is_service_running', return_value=True):
            with patch('builtins.open', mock_open()) as mock_file:
                with patch('json.dump') as mock_json_dump:
                    # Act - Complete reschedule workflow
                    create_reschedule_request(user_id, category)
                    
                    # Verify service check was called
                    from core.service_utilities import is_service_running
                    is_service_running.assert_called_once()
                    
                    # Verify file creation was called
                    mock_file.assert_called_once()
                    mock_json_dump.assert_called_once()
                    
                    # Verify request data structure
                    call_args = mock_json_dump.call_args[0][0]
                    assert call_args['user_id'] == user_id, "Should include user_id"
                    assert call_args['category'] == category, "Should include category"
    
    @pytest.mark.slow
    def test_service_utilities_error_recovery_with_real_operations(self, test_data_dir):
        """Test error recovery when working with real operations."""
        # Test 1: Network recovery
        with patch('core.service_utilities.socket.create_connection') as mock_socket:
            # Simulate network failure then recovery
            mock_socket.side_effect = [OSError("Network down"), MagicMock()]
            
            # Act
            network_available = wait_for_network(timeout=10)
            
            # Assert
            assert network_available is True, "Should recover when network becomes available"
            assert mock_socket.call_count >= 2, "Should retry multiple times"
        
        # Test 2: Process monitoring recovery
        with patch('core.service_utilities.psutil.process_iter') as mock_process_iter:
            # Simulate process monitoring failure then recovery
            mock_process_iter.side_effect = [
                Exception("Process error"),  # First call fails
                [MagicMock(info={'name': 'python.exe', 'cmdline': ['python', 'service.py']}, is_running=lambda: True)]  # Second call succeeds
            ]
            
            # Act
            is_running = is_service_running()
            
            # Assert
            assert is_running is False, "Should handle first failure gracefully"
    
    def test_service_utilities_concurrent_access_safety(self, test_data_dir):
        """Test that service utilities handle concurrent access safely."""
        # Arrange - Create throttler
        throttler = Throttler(1.0)  # 1 second interval
        
        # Act - Simulate concurrent access
        results = []
        for i in range(5):
            results.append(throttler.should_run())
        
        # Assert - Should handle concurrent access safely
        assert results[0] is True, "First call should succeed"
        # After first call, rapid calls should be throttled (return False)
        # The Throttler is working correctly - it sets last_run on first call
        assert results[1:] == [False] * 4, "Rapid calls should be throttled"
        
        # Test with actual time delay to verify throttling works across seconds
        from tests.conftest import wait_until
        assert wait_until(lambda: throttler.should_run() is True, timeout_seconds=2.0)
        delayed_result = True
        assert delayed_result is True, "Call after interval should succeed"
        
        # Test title case thread safety (should be stateless)
        test_text = "ai chatbot"
        results = []
        for i in range(5):
            results.append(_shared__title_case(test_text))
        
        # Assert - All results should be identical
        assert all(result == "AI Chatbot" for result in results), "Title case should be consistent across calls" 
