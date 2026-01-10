"""
Unit tests for notebook validation error handling.

Tests verify that validation functions properly handle errors according to
MHM error handling guidelines, using @handle_errors decorator and proper
error categorization.
"""

import pytest
from unittest.mock import patch

from notebook.notebook_validation import (
    is_valid_entry_reference,
    parse_short_id,
    format_short_id,
    is_valid_entry_title,
    is_valid_entry_body,
    is_valid_entry_group,
    is_valid_entry_kind,
    is_valid_list_item_index,
    normalize_list_item_index,
    validate_entry_content,
    MAX_TITLE_LENGTH,
    MAX_BODY_LENGTH
)


@pytest.mark.unit
@pytest.mark.notebook
@pytest.mark.critical
class TestValidationErrorHandling:
    """Test that validation functions handle errors correctly."""
    
    @pytest.mark.critical
    def test_validation_functions_use_error_handling_decorator(self):
        """Test that validation functions are decorated with @handle_errors."""
        # All validation functions should have the decorator
        # This is verified by checking they return safe defaults on errors
        # rather than raising exceptions
        
        # Test with invalid input types - should return False/None, not raise
        assert is_valid_entry_reference(None) is False
        assert is_valid_entry_reference(123) is False
        assert parse_short_id(None) is None
        assert parse_short_id(123) is None
        assert format_short_id("not-a-uuid", "note") is None
        assert is_valid_entry_title(123) is False
        assert is_valid_entry_body(123) is False
        assert is_valid_entry_group(123) is False
        assert is_valid_entry_kind(123) is False
        assert is_valid_list_item_index("not-int", 5) is False
        assert normalize_list_item_index("not-int", 5) is None
    
    @pytest.mark.critical
    def test_validation_errors_logged_appropriately(self):
        """Test that validation errors are logged at appropriate levels."""
        # Patch the logger at the module level where it's used
        with patch('notebook.notebook_validation.logger') as mock_logger:
            # Invalid entry reference
            is_valid_entry_reference(None)
            assert mock_logger.warning.called, "Should log warning for invalid entry reference"
            
            mock_logger.warning.reset_mock()
            
            # Invalid entry kind
            is_valid_entry_kind(123)
            assert mock_logger.warning.called, "Should log warning for invalid entry kind"
            
            mock_logger.warning.reset_mock()
            
            # Invalid list item index
            is_valid_list_item_index(-1, 5)
            assert mock_logger.warning.called, "Should log warning for invalid list item index"
    
    @pytest.mark.regression
    def test_validation_functions_return_safe_defaults(self):
        """Test that validation functions return safe defaults on errors."""
        # All functions should return False/None on errors, never raise exceptions
        # This allows callers to handle errors gracefully
        
        # Test various error conditions
        invalid_inputs = [
            (is_valid_entry_reference, [None, 123, ""]),
            (is_valid_entry_title, [123, []]),
            (is_valid_entry_body, [123, []]),
            (is_valid_entry_group, [123, []]),
            (is_valid_entry_kind, [None, 123, []]),
            (is_valid_list_item_index, [None, "not-int", -1]),
        ]
        
        for func, inputs in invalid_inputs:
            for invalid_input in inputs:
                try:
                    if func == is_valid_list_item_index:
                        result = func(invalid_input, 5)
                    else:
                        result = func(invalid_input)
                    # Should return False/None, not raise
                    assert result is False or result is None, \
                        f"{func.__name__} should return False/None for invalid input {invalid_input}, got {result}"
                except Exception as e:
                    pytest.fail(f"{func.__name__} raised {type(e).__name__} for input {invalid_input}: {e}")


@pytest.mark.unit
@pytest.mark.notebook
@pytest.mark.critical
class TestValidationErrorMessages:
    """Test that validation error messages are user-friendly."""
    
    @pytest.mark.critical
    def test_validate_entry_content_error_messages(self):
        """Test that validate_entry_content returns user-friendly error messages."""
        # Test various validation failures
        test_cases = [
            {
                'title': None,
                'body': None,
                'kind': 'note',
                'expected_keywords': ['title', 'body', 'must have']
            },
            {
                'title': 'a' * (MAX_TITLE_LENGTH + 1),
                'body': 'Body',
                'kind': 'note',
                'expected_keywords': ['title', 'max', str(MAX_TITLE_LENGTH)]
            },
            {
                'title': 'Title',
                'body': 'a' * (MAX_BODY_LENGTH + 1),
                'kind': 'note',
                'expected_keywords': ['body', 'max', str(MAX_BODY_LENGTH)]
            },
            {
                'title': 'Title',
                'body': 'Body',
                'kind': 'invalid',
                'expected_keywords': ['kind', 'invalid']
            },
        ]
        
        for case in test_cases:
            is_valid, error_msg = validate_entry_content(
                title=case.get('title'),
                body=case.get('body'),
                kind=case['kind']
            )
            
            assert is_valid is False, f"Should fail validation for {case}"
            assert error_msg is not None, "Should provide error message"
            
            # Check that error message contains expected keywords
            error_lower = error_msg.lower()
            for keyword in case['expected_keywords']:
                assert keyword.lower() in error_lower, \
                    f"Error message should mention '{keyword}': {error_msg}"
            
            # Error message should not contain technical details like stack traces
            assert 'traceback' not in error_lower, "Error message should not contain traceback"
            assert 'file' not in error_lower or 'line' not in error_lower, \
                "Error message should not contain file/line numbers"
    
    @pytest.mark.regression
    def test_error_messages_are_concise(self):
        """Test that error messages are concise and actionable."""
        # Error messages should be short enough for user-facing display
        max_message_length = 200  # Reasonable limit for user messages
        
        test_cases = [
            (None, None, 'note'),
            ('a' * (MAX_TITLE_LENGTH + 1), 'Body', 'note'),
            ('Title', 'a' * (MAX_BODY_LENGTH + 1), 'note'),
            ('Title', 'Body', 'invalid'),
        ]
        
        for title, body, kind in test_cases:
            is_valid, error_msg = validate_entry_content(title=title, body=body, kind=kind)
            if not is_valid and error_msg:
                assert len(error_msg) <= max_message_length, \
                    f"Error message too long ({len(error_msg)} chars): {error_msg}"


@pytest.mark.unit
@pytest.mark.notebook
@pytest.mark.regression
class TestValidationErrorRecovery:
    """Test error recovery scenarios in validation."""
    
    @pytest.mark.critical
    def test_validation_handles_edge_cases_gracefully(self):
        """Test that validation handles edge cases without crashing."""
        edge_cases = [
            # Empty strings
            ('', ''),
            # Very long strings
            ('a' * 10000, 'b' * 100000),
            # Unicode strings
            ('测试', '🎉'),
            # Whitespace-only
            ('   ', '\n\t'),
            # Special characters
            ('!@#$%^&*()', '<script>alert("xss")</script>'),
        ]
        
        for title, body in edge_cases:
            # Should not raise exceptions
            try:
                result = validate_entry_content(title=title, body=body, kind='note')
                assert isinstance(result, tuple), "Should return tuple"
                assert len(result) == 2, "Should return (is_valid, error_msg)"
            except Exception as e:
                pytest.fail(f"Validation should handle edge case gracefully, but raised {type(e).__name__}: {e}")
    
    @pytest.mark.regression
    def test_validation_handles_none_values(self):
        """Test that validation handles None values correctly."""
        # None values should be handled gracefully (not raise exceptions)
        test_cases = [
            (None, None, 'note'),
            (None, None, 'list'),
            (None, None, 'journal'),
            ('Title', None, 'note'),
            (None, 'Body', 'note'),
        ]
        
        for title, body, kind in test_cases:
            try:
                result = validate_entry_content(title=title, body=body, kind=kind)
                assert isinstance(result, tuple), "Should return tuple"
            except Exception as e:
                pytest.fail(f"Validation should handle None values, but raised {type(e).__name__}: {e}")


@pytest.mark.unit
@pytest.mark.notebook
@pytest.mark.critical
class TestValidationIntegrationWithErrorHandling:
    """Test integration of validation with error handling system."""
    
    @pytest.mark.critical
    def test_validation_works_with_error_handler(self):
        """Test that validation functions work correctly with error handler."""
        from core.error_handling import ErrorHandler
        
        handler = ErrorHandler()
        
        # Validation functions should work even if error handler is involved
        # (they use @handle_errors decorator which integrates with ErrorHandler)
        
        # Test that validation still works correctly
        assert is_valid_entry_reference("n-123abc") is True
        assert is_valid_entry_reference(None) is False
        
        # Test that error handler doesn't interfere with normal operation
        assert is_valid_entry_title("Valid Title") is True
        assert is_valid_entry_title("a" * (MAX_TITLE_LENGTH + 1)) is False
    
    @pytest.mark.regression
    def test_validation_error_propagation(self):
        """Test that validation errors propagate correctly through call chain."""
        # When validation fails, the error should be detectable by callers
        is_valid, error_msg = validate_entry_content(
            title=None,
            body=None,
            kind='note'
        )
        
        assert is_valid is False, "Should indicate validation failure"
        assert error_msg is not None, "Should provide error message"
        assert isinstance(error_msg, str), "Error message should be string"
        
        # Caller should be able to check is_valid and handle accordingly
        if not is_valid:
            # This is the expected pattern - caller checks is_valid
            assert error_msg is not None, "Error message should be available"


@pytest.mark.unit
@pytest.mark.notebook
@pytest.mark.regression
class TestValidationTypeSafety:
    """Test that validation functions handle type errors correctly."""
    
    @pytest.mark.critical
    def test_type_validation_prevents_errors(self):
        """Test that type validation prevents downstream errors."""
        # Invalid types should be caught early and return False/None
        # rather than causing downstream errors
        
        type_errors = [
            # Wrong types for entry reference
            (is_valid_entry_reference, [123, [], {}, None]),
            # Wrong types for title
            (is_valid_entry_title, [[], {}, 123]),
            # Wrong types for body
            (is_valid_entry_body, [[], {}, 123]),
            # Wrong types for group
            (is_valid_entry_group, [[], {}, 123]),
            # Wrong types for kind
            (is_valid_entry_kind, [None, 123, [], {}]),
            # Wrong types for index
            (is_valid_list_item_index, [None, "string", [], {}]),
        ]
        
        for func, invalid_types in type_errors:
            for invalid_type in invalid_types:
                try:
                    if func == is_valid_list_item_index:
                        result = func(invalid_type, 5)
                    else:
                        result = func(invalid_type)
                    
                    # Should return False/None, not raise
                    assert result is False or result is None, \
                        f"{func.__name__} should handle type {type(invalid_type).__name__} gracefully"
                except (TypeError, AttributeError, ValueError) as e:
                    pytest.fail(f"{func.__name__} should handle type errors, but raised {type(e).__name__}: {e}")
