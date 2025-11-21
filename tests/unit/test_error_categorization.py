"""
Tests for error categorization - verifying proper MHMError subclass usage.
"""

import pytest
from core.error_handling import (
    ValidationError, DataError, FileOperationError, 
    ConfigurationError, CommunicationError, AIError, SchedulerError, MHMError
)


class TestErrorCategorization:
    """Test that exceptions are properly categorized."""
    
    @pytest.mark.unit
    def test_validation_error_creation(self):
        """Test ValidationError can be created with details."""
        error = ValidationError(
            "Invalid input",
            details={'field': 'email', 'value': 'invalid'}
        )
        assert isinstance(error, MHMError)
        assert error.message == "Invalid input"
        assert error.details['field'] == 'email'
        assert error.recoverable is True
    
    @pytest.mark.unit
    def test_file_operation_error_creation(self):
        """Test FileOperationError can be created."""
        error = FileOperationError(
            "File not found",
            details={'file_path': '/test/file.json'}
        )
        assert isinstance(error, DataError)
        assert isinstance(error, MHMError)
        assert error.message == "File not found"
        assert error.details['file_path'] == '/test/file.json'
    
    @pytest.mark.unit
    def test_data_error_creation(self):
        """Test DataError can be created."""
        error = DataError("Data validation failed")
        assert isinstance(error, MHMError)
        assert error.message == "Data validation failed"
    
    @pytest.mark.unit
    def test_configuration_error_creation(self):
        """Test ConfigurationError can be created."""
        error = ConfigurationError(
            "Invalid configuration",
            details={'setting': 'api_key'}
        )
        assert isinstance(error, MHMError)
        assert error.message == "Invalid configuration"
        assert error.details['setting'] == 'api_key'
    
    @pytest.mark.unit
    def test_communication_error_creation(self):
        """Test CommunicationError can be created."""
        error = CommunicationError(
            "Network connection failed",
            details={'channel': 'discord'}
        )
        assert isinstance(error, MHMError)
        assert error.message == "Network connection failed"
        assert error.details['channel'] == 'discord'
    
    @pytest.mark.unit
    def test_ai_error_creation(self):
        """Test AIError can be created."""
        error = AIError("AI model call failed")
        assert isinstance(error, MHMError)
        assert error.message == "AI model call failed"
    
    @pytest.mark.unit
    def test_scheduler_error_creation(self):
        """Test SchedulerError can be created."""
        error = SchedulerError("Scheduling operation failed")
        assert isinstance(error, MHMError)
        assert error.message == "Scheduling operation failed"
    
    @pytest.mark.unit
    def test_error_inheritance_hierarchy(self):
        """Test that error inheritance hierarchy is correct."""
        # FileOperationError should inherit from DataError
        file_error = FileOperationError("Test")
        assert isinstance(file_error, DataError)
        assert isinstance(file_error, MHMError)
        
        # DataError should inherit from MHMError
        data_error = DataError("Test")
        assert isinstance(data_error, MHMError)
        assert not isinstance(data_error, FileOperationError)
    
    @pytest.mark.unit
    def test_error_recoverable_flag(self):
        """Test that errors can be marked as non-recoverable."""
        error = ValidationError("Invalid input", recoverable=False)
        assert error.recoverable is False
        
        error2 = ValidationError("Invalid input", recoverable=True)
        assert error2.recoverable is True
        
        # Default should be True
        error3 = ValidationError("Invalid input")
        assert error3.recoverable is True

