"""
Tests for core error handling module.

Tests error handling decorators, custom exceptions, and recovery strategies.
"""

import pytest
from unittest.mock import patch, Mock
from datetime import datetime

from core.error_handling import (
    handle_errors,
    MHMError,
    DataError,
    FileOperationError,
    ConfigurationError,
    ValidationError,
    handle_file_error,
    handle_configuration_error
)

class TestCustomExceptions:
    """Test custom exception classes."""
    
    @pytest.mark.unit
    @pytest.mark.critical
    def test_mhm_error_basic(self):
        """Test basic MHMError creation."""
        error = MHMError("Test error message")
        
        assert str(error) == "Test error message"
        assert error.message == "Test error message"
        assert error.details == {}
        assert error.recoverable is True
        assert isinstance(error.timestamp, datetime)
        assert error.traceback is not None
    
    @pytest.mark.unit
    @pytest.mark.regression
    def test_mhm_error_with_details(self):
        """Test MHMError with custom details."""
        details = {'file': 'test.json', 'operation': 'read'}
        error = MHMError("Test error", details=details, recoverable=False)
        
        assert error.details == details
        assert error.recoverable is False
    
    @pytest.mark.unit
    @pytest.mark.smoke
    def test_data_error(self):
        """Test DataError exception."""
        error = DataError("Data operation failed", {'user_id': 'test'})
        
        assert isinstance(error, MHMError)
        assert error.message == "Data operation failed"
        assert error.details['user_id'] == 'test'
    
    @pytest.mark.unit
    @pytest.mark.smoke
    def test_file_operation_error(self):
        """Test FileOperationError exception."""
        error = FileOperationError("File not found", {'path': '/test/file.json'})
        
        assert isinstance(error, MHMError)
        assert error.message == "File not found"
        assert error.details['path'] == '/test/file.json'
    
    @pytest.mark.unit
    @pytest.mark.smoke
    def test_config_error(self):
        """Test ConfigError exception."""
        error = ConfigurationError("Invalid configuration", {'setting': 'BASE_DATA_DIR'})
        
        assert isinstance(error, MHMError)
        assert error.message == "Invalid configuration"
        assert error.details['setting'] == 'BASE_DATA_DIR'
    
    @pytest.mark.unit
    @pytest.mark.smoke
    def test_validation_error(self):
        """Test ValidationError exception."""
        error = ValidationError("Validation failed", {'field': 'email', 'value': 'invalid'})
        
        assert isinstance(error, MHMError)
        assert error.message == "Validation failed"
        assert error.details['field'] == 'email'

class TestErrorHandlerDecorator:
    """Test the handle_errors decorator."""
    
    @pytest.mark.unit
    @pytest.mark.critical
    def test_error_handler_success(self):
        """Test error_handler with successful function."""
        @handle_errors("test operation")
        def test_function():
            """Test Function."""
            return "success"
        
        result = test_function()
        assert result == "success"
    
    @pytest.mark.unit
    @pytest.mark.regression
    def test_error_handler_exception(self):
        """Test error_handler with exception."""
        @handle_errors("test operation")
        def test_function():
            raise ValueError("Test error")
        
        result = test_function()
        assert result is None
    
    @pytest.mark.unit
    @pytest.mark.regression
    def test_error_handler_custom_return(self):
        """Test error_handler with custom return value."""
        @handle_errors("test operation", default_return="fallback")
        def test_function():
            raise ValueError("Test error")
        
        result = test_function()
        assert result == "fallback"
    
    @pytest.mark.unit
    @pytest.mark.regression
    def test_error_handler_logs_error(self):
        """Test error_handler logs errors."""
        with patch('core.logger.get_component_logger') as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger
            @handle_errors("test operation")
            def test_function():
                raise ValueError("Test error")
            
            test_function()
            
            # Verify error was logged (should be called multiple times: error + user message + retry messages)
            assert mock_logger.error.call_count >= 2
            
            # Check that we have the main error call
            error_calls = [call for call in mock_logger.error.call_args_list if "test operation" in call[0][0] and "Test error" in call[0][0]]
            assert len(error_calls) >= 1
            
            # Check that we have the user-friendly message
            user_calls = [call for call in mock_logger.error.call_args_list if "User Error:" in call[0][0]]
            assert len(user_calls) >= 1

class TestHandleErrorsDecorator:
    """Test the handle_errors decorator."""
    
    @pytest.mark.unit
    @pytest.mark.critical
    def test_handle_errors_success(self):
        """Test handle_errors with successful function."""
        @handle_errors("test operation")
        def test_function():
            return "success"
        
        result = test_function()
        assert result == "success"
    
    @pytest.mark.unit
    @pytest.mark.regression
    def test_handle_errors_exception(self):
        """Test handle_errors with exception."""
        @handle_errors("test operation")
        def test_function():
            raise ValueError("Test error")
        
        result = test_function()
        assert result is None
    
    @pytest.mark.unit
    @pytest.mark.regression
    def test_handle_errors_custom_return(self):
        """Test handle_errors with custom return value."""
        @handle_errors("test operation", default_return="fallback")
        def test_function():
            raise ValueError("Test error")
        
        result = test_function()
        assert result == "fallback"
    
    @pytest.mark.unit
    @pytest.mark.regression
    def test_handle_errors_specific_exception(self):
        """Test handle_errors with specific exception handling."""
        @handle_errors("test operation")
        def test_function():
            raise FileNotFoundError("File not found")
        
        result = test_function()
        assert result is None
    
    @pytest.mark.unit
    @pytest.mark.regression
    def test_handle_errors_logs_error(self):
        """Test handle_errors logs errors."""
        with patch('core.logger.get_component_logger') as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger
            @handle_errors("test operation")
            def test_function():
                raise ValueError("Test error")
            
            test_function()
            
            # Verify error was logged (should be called multiple times: error + user message + retry messages)
            assert mock_logger.error.call_count >= 2
            
            # Check that we have the main error call
            error_calls = [call for call in mock_logger.error.call_args_list if "test operation" in call[0][0] and "Test error" in call[0][0]]
            assert len(error_calls) >= 1
            
            # Check that we have the user-friendly message
            user_calls = [call for call in mock_logger.error.call_args_list if "User Error:" in call[0][0]]
            assert len(user_calls) >= 1

class TestErrorHandlingFunctions:
    """Test specific error handling functions."""
    
    @pytest.mark.unit
    @pytest.mark.smoke
    def test_handle_file_error(self):
        """Test handle_file_error function."""
        with patch('core.logger.get_component_logger') as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger
            error = FileNotFoundError("File not found")
            
            result = handle_file_error(error, "tests/data/test_file.json", "reading file")
            
            assert result is True  # Should succeed with file_path context
            # Should be called for error logging and recovery success
            assert mock_logger.error.call_count >= 1
            assert mock_logger.info.call_count >= 1  # Recovery success message
            
            # Check that we have the main error call
            error_calls = [call for call in mock_logger.error.call_args_list if "tests/data/test_file.json" in call[0][0] and "reading file" in call[0][0]]
            assert len(error_calls) >= 1
            
            # Check that we have recovery success message
            success_calls = [call for call in mock_logger.info.call_args_list if "Successfully recovered" in call[0][0]]
            assert len(success_calls) >= 1
    
    @pytest.mark.unit
    @pytest.mark.smoke
    def test_handle_configuration_error(self):
        """Test handle_configuration_error function."""
        with patch('core.logger.get_component_logger') as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger
            error = ValueError("Invalid setting")
            
            result = handle_configuration_error(error, "BASE_DATA_DIR", "validating path")
            
            assert result is False
            # Should be called multiple times: error + user message + retry messages
            assert mock_logger.error.call_count >= 2
            
            # Check that we have the main error call
            error_calls = [call for call in mock_logger.error.call_args_list if "validating path" in call[0][0] and "Invalid setting" in call[0][0]]
            assert len(error_calls) >= 1
            
            # Check that we have the user-friendly message
            user_calls = [call for call in mock_logger.error.call_args_list if "User Error:" in call[0][0]]
            assert len(user_calls) >= 1

class TestErrorHandlingIntegration:
    """Test error handling integration scenarios."""
    
    @pytest.mark.integration
    def test_error_handling_in_function_chain(self):
        """Test error handling in a chain of functions."""
        with patch('core.logger.get_component_logger') as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger
            @handle_errors("outer operation")
            def outer_function():
                return inner_function()
            
            @handle_errors("inner operation")
            def inner_function():
                raise ValueError("Inner error")
            
            result = outer_function()
            assert result is None
            
            # Verify both errors were logged (each error logs twice: error + user message)
            assert mock_logger.error.call_count >= 2
    
    @pytest.mark.integration
    def test_error_handling_with_recovery(self, test_path_factory):
        """Test error handling with recovery mechanisms and real side effects."""
        import os
        import json
        
        #[OK] VERIFY INITIAL STATE: Create a test environment under tests/data
        temp_dir = test_path_factory
        test_file = os.path.join(temp_dir, 'test_data.json')
        # Create initial valid data
        initial_data = {'status': 'healthy', 'data': [1, 2, 3]}
        with open(test_file, 'w') as f:
            json.dump(initial_data, f)
        
        #[OK] VERIFY INITIAL STATE: Check file exists and is valid
        assert os.path.exists(test_file), f"Test file should exist: {test_file}"
        with open(test_file, 'r') as f:
            loaded_data = json.load(f)
            assert loaded_data == initial_data
            
            # Test 1: Function that fails but has recovery mechanism
            @handle_errors("test operation", default_return="recovered")
            def test_function():
                # Simulate a file operation that fails
                raise FileNotFoundError("File not found")
            
            #[OK] VERIFY REAL BEHAVIOR: Check error handling works
            result = test_function()
            assert result == "recovered"
            
            #[OK] VERIFY REAL BEHAVIOR: Check original file is unaffected
            assert os.path.exists(test_file), f"Original file should be unaffected: {test_file}"
            with open(test_file, 'r') as f:
                current_data = json.load(f)
            assert current_data == initial_data
            
            # Test 2: Function that corrupts data but recovers
            @handle_errors("data corruption test", default_return="corrupted")
            def corrupt_data_function():
                # Corrupt the file
                with open(test_file, 'w') as f:
                    f.write('{invalid json}')
                raise ValueError("Data corruption occurred")
            
            #[OK] VERIFY REAL BEHAVIOR: Check corruption and recovery
            result = corrupt_data_function()
            assert result == "corrupted"
            
            #[OK] VERIFY REAL BEHAVIOR: Check file was actually corrupted
            with open(test_file, 'r') as f:
                corrupted_content = f.read()
            assert corrupted_content == '{invalid json}'
            
            #[OK] VERIFY REAL BEHAVIOR: Check file is no longer valid JSON
            try:
                with open(test_file, 'r') as f:
                    json.load(f)
                assert False, "File should be corrupted and not valid JSON"
            except json.JSONDecodeError:
                pass  # Expected behavior
            
            # Test 3: Function that recovers from corruption
            @handle_errors("data recovery test", default_return="recovery_failed")
            def recover_data_function():
                # Attempt to recover by rewriting valid data
                recovered_data = {'status': 'recovered', 'data': [4, 5, 6]}
                with open(test_file, 'w') as f:
                    json.dump(recovered_data, f)
                return "recovery_successful"
            
            #[OK] VERIFY REAL BEHAVIOR: Check recovery mechanism
            result = recover_data_function()
            assert result == "recovery_successful"
            
            #[OK] VERIFY REAL BEHAVIOR: Check file was actually recovered
            assert os.path.exists(test_file), f"File should still exist after recovery: {test_file}"
            with open(test_file, 'r') as f:
                recovered_data = json.load(f)
            assert recovered_data == {'status': 'recovered', 'data': [4, 5, 6]}
            
            #[OK] VERIFY REAL BEHAVIOR: Check file is valid JSON again
            try:
                with open(test_file, 'r') as f:
                    json.load(f)  # Should not raise exception
            except json.JSONDecodeError as e:
                assert False, f"Recovered file should be valid JSON: {e}"
            
            # Test 4: Function that creates backup during error
            backup_file = os.path.join(temp_dir, 'backup_data.json')
            
            @handle_errors("backup creation test", default_return="backup_created")
            def backup_function():
                # Create backup before potential error
                with open(test_file, 'r') as f:
                    current_data = json.load(f)
                with open(backup_file, 'w') as f:
                    json.dump(current_data, f)
                
                # Simulate an error after backup
                raise RuntimeError("Operation failed after backup")
            
            #[OK] VERIFY REAL BEHAVIOR: Check backup creation
            result = backup_function()
            assert result == "backup_created"
            
            #[OK] VERIFY REAL BEHAVIOR: Check backup file was created
            assert os.path.exists(backup_file), f"Backup file should be created: {backup_file}"
            with open(backup_file, 'r') as f:
                backup_data = json.load(f)
            assert backup_data == {'status': 'recovered', 'data': [4, 5, 6]}
            
            #[OK] VERIFY REAL BEHAVIOR: Check original file is unchanged
            with open(test_file, 'r') as f:
                original_data = json.load(f)
            assert original_data == {'status': 'recovered', 'data': [4, 5, 6]}
            
            # Test 5: Function that performs cleanup on error
            temp_files = []
            
            @handle_errors("cleanup test", default_return="cleanup_completed")
            def cleanup_function():
                # Create some temporary files
                for i in range(3):
                    temp_file = os.path.join(temp_dir, f'temp_{i}.json')
                    with open(temp_file, 'w') as f:
                        json.dump({'temp': i}, f)
                    temp_files.append(temp_file)
                
                # Simulate an error
                raise Exception("Cleanup needed")
            
            #[OK] VERIFY REAL BEHAVIOR: Check cleanup mechanism
            result = cleanup_function()
            assert result == "cleanup_completed"
            
            #[OK] VERIFY REAL BEHAVIOR: Check temporary files were created
            for temp_file in temp_files:
                assert os.path.exists(temp_file), f"Temp file should exist: {temp_file}"
            
            # Test 6: Function that validates system state after errors
            @handle_errors("state validation test", default_return="state_valid")
            def state_validation_function():
                # Check that all expected files still exist
                expected_files = [test_file, backup_file] + temp_files
                for file_path in expected_files:
                    if not os.path.exists(file_path):
                        raise FileNotFoundError(f"Expected file missing: {file_path}")
                
                # Check that files are still valid JSON
                for file_path in expected_files:
                    try:
                        with open(file_path, 'r') as f:
                            json.load(f)
                    except json.JSONDecodeError as e:
                        raise ValueError(f"Invalid JSON in {file_path}: {e}")
                
                return "all_files_valid"
            
            #[OK] VERIFY REAL BEHAVIOR: Check state validation
            result = state_validation_function()
            assert result == "all_files_valid"
            
            #[OK] VERIFY REAL BEHAVIOR: Check final system state
            # All files should exist and be valid
            all_files = [test_file, backup_file] + temp_files
            for file_path in all_files:
                assert os.path.exists(file_path), f"File should exist in final state: {file_path}"
                assert os.path.isfile(file_path), f"Path should be a file: {file_path}"
                assert os.access(file_path, os.R_OK), f"File should be readable: {file_path}"
                
                # Check JSON validity
                try:
                    with open(file_path, 'r') as f:
                        json.load(f)
                except json.JSONDecodeError as e:
                    assert False, f"File should be valid JSON in final state: {file_path} - {e}"
            
            #[OK] VERIFY REAL BEHAVIOR: Check no unexpected files were created
            all_files_in_dir = os.listdir(temp_dir)
            expected_file_names = [os.path.basename(f) for f in all_files]
            unexpected_files = [f for f in all_files_in_dir if f not in expected_file_names and not f.startswith('.')]
            assert len(unexpected_files) == 0, f"No unexpected files should be created: {unexpected_files}"
    
    @pytest.mark.integration
    def test_error_handling_different_exception_types(self):
        """Test error handling with different exception types and side effects."""
        # Track function calls to verify side effects
        call_log = []
        
        @handle_errors("test operation")
        def test_function(exception_type):
            call_log.append(f"function_called_with_{exception_type}")
            
            if exception_type == "value":
                raise ValueError("Value error")
            elif exception_type == "file":
                raise FileNotFoundError("File error")
            elif exception_type == "key":
                raise KeyError("Key error")
            else:
                return "success"
        
        #[OK] VERIFY INITIAL STATE: Check call log is empty
        assert len(call_log) == 0, "Call log should be empty initially"
        
        # Test different exception types
        result1 = test_function("value")
        result2 = test_function("file")
        result3 = test_function("key")
        result4 = test_function("success")
        
        #[OK] VERIFY REAL BEHAVIOR: Check return values
        assert result1 is None, "ValueError should return None"
        assert result2 is None, "FileNotFoundError should return None"
        assert result3 is None, "KeyError should return None"
        assert result4 == "success", "Success case should return 'success'"
        
        #[OK] VERIFY REAL BEHAVIOR: Check side effects (function calls were made)
        assert len(call_log) == 4, f"Function should have been called 4 times: {call_log}"
        assert "function_called_with_value" in call_log
        assert "function_called_with_file" in call_log
        assert "function_called_with_key" in call_log
        assert "function_called_with_success" in call_log
        
        #[OK] VERIFY REAL BEHAVIOR: Check call order
        assert call_log[0] == "function_called_with_value"
        assert call_log[1] == "function_called_with_file"
        assert call_log[2] == "function_called_with_key"
        assert call_log[3] == "function_called_with_success"

class TestErrorHandlingEdgeCases:
    """Test error handling edge cases."""
    
    @pytest.mark.unit
    @pytest.mark.regression
    def test_error_handler_with_args_kwargs(self):
        """Test error_handler with function arguments."""
        @handle_errors("test operation")
        def test_function(arg1, arg2, kwarg1=None):
            if arg1 == "error":
                raise ValueError("Error triggered")
            return f"{arg1}-{arg2}-{kwarg1}"
        
        # Test successful call
        result = test_function("a", "b", kwarg1="c")
        assert result == "a-b-c"
        
        # Test error call
        result = test_function("error", "b", kwarg1="c")
        assert result is None
    
    @pytest.mark.unit
    @pytest.mark.regression
    def test_handle_errors_with_args_kwargs(self):
        """Test handle_errors with function arguments."""
        @handle_errors("test operation")
        def test_function(arg1, arg2, kwarg1=None):
            if arg1 == "error":
                raise ValueError("Error triggered")
            return f"{arg1}-{arg2}-{kwarg1}"
        
        # Test successful call
        result = test_function("a", "b", kwarg1="c")
        assert result == "a-b-c"
        
        # Test error call
        result = test_function("error", "b", kwarg1="c")
        assert result is None
    
    @pytest.mark.unit
    @pytest.mark.regression
    def test_error_handler_nested_exceptions(self):
        """Test error_handler with nested exceptions."""
        @handle_errors("outer operation")
        def outer_function():
            try:
                inner_function()
            except ValueError:
                raise RuntimeError("Wrapped error")
        
        @handle_errors("inner operation")
        def inner_function():
            raise ValueError("Original error")
        
        result = outer_function()
        assert result is None
    
    @pytest.mark.unit
    @pytest.mark.regression
    def test_handle_errors_with_logging_disabled(self):
        """Test handle_errors when logging is disabled."""
        with patch('core.logger.get_component_logger') as mock_get_logger:
            mock_logger = Mock()
            mock_logger.error.side_effect = Exception("Logger error")
            mock_get_logger.return_value = mock_logger
            
            @handle_errors("test operation")
            def test_function():
                raise ValueError("Test error")
            
            # Should not raise exception even if logger fails
            result = test_function()
            assert result is None

class TestAsyncErrorHandling:
    """Test async function error handling."""
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_handle_errors_async_success(self):
        """Test handle_errors decorator with successful async function."""
        @handle_errors("async test operation")
        async def async_function():
            return "success"
        
        result = await async_function()
        assert result == "success"
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_handle_errors_async_exception(self):
        """Test handle_errors decorator with async function that raises exception."""
        @handle_errors("async test operation", default_return="default")
        async def async_function():
            raise ValueError("Test error")
        
        result = await async_function()
        assert result == "default"
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_handle_errors_async_custom_return(self):
        """Test handle_errors decorator with custom return value for async functions."""
        @handle_errors("async test operation", default_return=42)
        async def async_function():
            raise ValueError("Test error")
        
        result = await async_function()
        assert result == 42
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_handle_errors_async_is_coroutine(self):
        """Test that decorated async functions remain coroutine functions."""
        import asyncio
        
        @handle_errors("async test operation")
        async def async_function():
            return "success"
        
        # Verify it's still a coroutine function
        assert asyncio.iscoroutinefunction(async_function)
        
        # And it can be awaited
        result = await async_function()
        assert result == "success" 
