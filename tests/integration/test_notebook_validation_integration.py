"""
Integration tests for notebook validation.

Tests verify that validation works correctly when integrated with data manager
and handler operations, following MHM testing and error handling guidelines.
"""

import pytest
from unittest.mock import patch

from notebook.notebook_data_manager import (
    create_entry,
    create_note,
    create_list,
    append_to_entry_body,
    set_entry_body,
    add_list_item,
    set_group
)
from notebook.notebook_validation import (
    MAX_TITLE_LENGTH,
    MAX_BODY_LENGTH,
    MAX_GROUP_LENGTH,
    validate_entry_content
)
from tests.test_utilities import TestUserFactory


@pytest.mark.integration
@pytest.mark.notebook
@pytest.mark.critical
class TestNotebookValidationIntegration:
    """Test validation integration with data manager operations."""
    
    def _create_test_user(self, user_id: str, test_data_dir: str | None = None) -> bool:
        """Create a test user with proper account setup."""
        return TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
    
    @pytest.mark.file_io
    def test_create_entry_validates_content(self, test_data_dir):
        """Test that create_entry validates content before creating."""
        user_id = "test_user_validation_integration"
        assert self._create_test_user(user_id, test_data_dir=test_data_dir), "Failed to create test user"
        
        # Valid entry should succeed
        entry = create_entry(
            user_id=user_id,
            kind='note',
            title='Valid Title',
            body='Valid body'
        )
        assert entry is not None, "Valid entry should be created"
        
        # Invalid entry (too long title) should fail
        long_title = 'a' * (MAX_TITLE_LENGTH + 1)
        entry = create_entry(
            user_id=user_id,
            kind='note',
            title=long_title,
            body='Valid body'
        )
        assert entry is None, "Entry with too long title should not be created"
        
        # Invalid entry (neither title nor body) should fail
        entry = create_entry(
            user_id=user_id,
            kind='note',
            title=None,
            body=None
        )
        assert entry is None, "Entry without title or body should not be created"
    
    @pytest.mark.file_io
    def test_append_validates_length(self, test_data_dir):
        """Test that append_to_entry_body validates length."""
        user_id = "test_user_append_validation"
        assert self._create_test_user(user_id, test_data_dir=test_data_dir), "Failed to create test user"
        
        # Create a note first
        entry = create_note(user_id, title='Test Note', body='Initial body')
        assert entry is not None, "Note should be created"
        # Short ID format is now n123abc (no dash) for easier mobile typing
        short_id = f"n{str(entry.id).replace('-', '')[:6]}"
        
        # Valid append should succeed
        updated = append_to_entry_body(user_id, short_id, 'More text')
        assert updated is not None, "Valid append should succeed"
        
        # Append that would exceed limit should fail
        long_text = 'a' * (MAX_BODY_LENGTH + 1)
        updated = append_to_entry_body(user_id, short_id, long_text)
        assert updated is None, "Append that exceeds limit should fail"
    
    @pytest.mark.file_io
    def test_set_body_validates_length(self, test_data_dir):
        """Test that set_entry_body validates length."""
        user_id = "test_user_set_body_validation"
        assert self._create_test_user(user_id, test_data_dir=test_data_dir), "Failed to create test user"
        
        # Create a note first
        entry = create_note(user_id, title='Test Note', body='Initial body')
        assert entry is not None, "Note should be created"
        # Short ID format is now n123abc (no dash) for easier mobile typing
        short_id = f"n{str(entry.id).replace('-', '')[:6]}"
        
        # Valid body should succeed
        updated = set_entry_body(user_id, short_id, 'New body text')
        assert updated is not None, "Valid body should succeed"
        
        # Body that exceeds limit should fail
        long_body = 'a' * (MAX_BODY_LENGTH + 1)
        updated = set_entry_body(user_id, short_id, long_body)
        assert updated is None, "Body that exceeds limit should fail"
    
    @pytest.mark.file_io
    def test_add_list_item_validates_text(self, test_data_dir):
        """Test that add_list_item validates item text."""
        user_id = "test_user_list_item_validation"
        assert self._create_test_user(user_id, test_data_dir=test_data_dir), "Failed to create test user"
        
        # Create a list first
        entry = create_list(user_id, title='Test List', items=['Item 1'])
        assert entry is not None, "List should be created"
        # Short ID format is now l123abc (no dash) for easier mobile typing
        short_id = f"l{str(entry.id).replace('-', '')[:6]}"
        
        # Valid item should succeed
        updated = add_list_item(user_id, short_id, 'Item 2')
        assert updated is not None, "Valid item should succeed"
        
        # Empty item should fail
        updated = add_list_item(user_id, short_id, '')
        assert updated is None, "Empty item should fail"
        
        # Whitespace-only item should fail
        updated = add_list_item(user_id, short_id, '   ')
        assert updated is None, "Whitespace-only item should fail"
    
    @pytest.mark.file_io
    def test_set_group_validates_group_name(self, test_data_dir):
        """Test that set_group validates group name."""
        user_id = "test_user_group_validation"
        assert self._create_test_user(user_id, test_data_dir=test_data_dir), "Failed to create test user"
        
        # Create a note first
        entry = create_note(user_id, title='Test Note')
        assert entry is not None, "Note should be created"
        # Short ID format is now n123abc (no dash) for easier mobile typing
        short_id = f"n{str(entry.id).replace('-', '')[:6]}"
        
        # Valid group should succeed
        updated = set_group(user_id, short_id, 'work')
        assert updated is not None, "Valid group should succeed"
        
        # Group that exceeds limit should fail
        long_group = 'a' * (MAX_GROUP_LENGTH + 1)
        updated = set_group(user_id, short_id, long_group)
        assert updated is None, "Group that exceeds limit should fail"
        
        # Group with invalid characters should fail
        updated = set_group(user_id, short_id, 'invalid@group')
        assert updated is None, "Group with invalid characters should fail"
    
    @pytest.mark.file_io
    def test_validation_errors_logged(self, test_data_dir):
        """Test that validation errors are properly logged."""
        user_id = "test_user_validation_logging"
        assert self._create_test_user(user_id, test_data_dir=test_data_dir), "Failed to create test user"
        
        # Patch logger at module level
        with patch('notebook.notebook_data_manager.logger') as mock_logger:
            # Try to create entry with invalid content
            entry = create_entry(
                user_id=user_id,
                kind='note',
                title='a' * (MAX_TITLE_LENGTH + 1),
                body='Valid body'
            )
            
            # Entry should not be created
            assert entry is None, "Invalid entry should not be created"
            
            # Should log error
            assert mock_logger.error.called, "Should log error for invalid entry content"
            
            # Check that error message mentions validation
            error_calls = [str(call) for call in mock_logger.error.call_args_list]
            assert any('invalid' in str(call).lower() or 'title' in str(call).lower() 
                      for call in error_calls), \
                "Error message should mention validation issue"
    
    @pytest.mark.file_io
    def test_validation_prevents_invalid_data_persistence(self, test_data_dir):
        """Test that validation prevents invalid data from being persisted."""
        user_id = "test_user_validation_persistence"
        assert self._create_test_user(user_id, test_data_dir=test_data_dir), "Failed to create test user"
        
        # Try to create invalid entry
        entry = create_entry(
            user_id=user_id,
            kind='note',
            title=None,
            body=None
        )
        assert entry is None, "Invalid entry should not be created"
        
        # Verify no entry was persisted
        from notebook.notebook_data_manager import list_recent
        recent = list_recent(user_id, n=10)
        # Should have no entries (or only valid ones from previous tests)
        invalid_entries = [e for e in recent if not e.title and not e.body and e.kind == 'note']
        assert len(invalid_entries) == 0, "No invalid entries should be persisted"
    
    @pytest.mark.file_io
    def test_validation_works_with_entry_reference(self, test_data_dir):
        """Test that validation works correctly with entry references."""
        user_id = "test_user_ref_validation"
        assert self._create_test_user(user_id, test_data_dir=test_data_dir), "Failed to create test user"
        
        # Create a note
        entry = create_note(user_id, title='Test Note', body='Body')
        assert entry is not None, "Note should be created"
        
        # Try to append with invalid reference
        updated = append_to_entry_body(user_id, 'invalid-ref-12345', 'Text')
        assert updated is None, "Invalid reference should fail"
        
        # Try with valid reference
        # Short ID format is now n123abc (no dash) for easier mobile typing
        short_id = f"n{str(entry.id).replace('-', '')[:6]}"
        updated = append_to_entry_body(user_id, short_id, 'More text')
        assert updated is not None, "Valid reference should succeed"
    
    @pytest.mark.file_io
    def test_validation_error_messages_are_user_friendly(self, test_data_dir):
        """Test that validation error messages are user-friendly."""
        user_id = "test_user_error_messages"
        assert self._create_test_user(user_id, test_data_dir=test_data_dir), "Failed to create test user"
        
        # Test validate_entry_content error messages
        is_valid, error_msg = validate_entry_content(
            title=None,
            body=None,
            kind='note'
        )
        
        assert is_valid is False, "Should fail validation"
        assert error_msg is not None, "Should provide error message"
        assert len(error_msg) <= 200, "Error message should be concise"
        assert 'traceback' not in error_msg.lower(), "Error message should not contain traceback"
        assert 'file' not in error_msg.lower() or 'line' not in error_msg.lower(), \
            "Error message should not contain file/line numbers"
        
        # Error message should be actionable
        assert 'title' in error_msg.lower() or 'body' in error_msg.lower(), \
            "Error message should mention what's missing"


@pytest.mark.integration
@pytest.mark.notebook
@pytest.mark.regression
class TestNotebookValidationEdgeCases:
    """Test validation edge cases in integration scenarios."""
    
    def _create_test_user(self, user_id: str, test_data_dir: str | None = None) -> bool:
        """Create a test user with proper account setup."""
        return TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
    
    @pytest.mark.file_io
    def test_validation_handles_unicode_content(self, test_data_dir):
        """Test that validation handles Unicode content correctly."""
        user_id = "test_user_unicode_validation"
        assert self._create_test_user(user_id, test_data_dir=test_data_dir), "Failed to create test user"
        
        # Unicode title and body should work
        entry = create_note(
            user_id=user_id,
            title='测试标题',
            body='测试内容 🎉'
        )
        assert entry is not None, "Unicode content should be accepted"
        assert entry.title == '测试标题', "Unicode title should be preserved"
        assert entry.body == '测试内容 🎉', "Unicode body should be preserved"
    
    @pytest.mark.file_io
    def test_validation_handles_boundary_lengths(self, test_data_dir):
        """Test validation at boundary lengths."""
        user_id = "test_user_boundary_validation"
        assert self._create_test_user(user_id, test_data_dir=test_data_dir), "Failed to create test user"
        
        # Title at max length should succeed
        max_title = 'a' * MAX_TITLE_LENGTH
        entry = create_note(user_id=user_id, title=max_title, body='Body')
        assert entry is not None, "Title at max length should succeed"
        
        # Title one over max should fail
        over_max_title = 'a' * (MAX_TITLE_LENGTH + 1)
        entry = create_note(user_id=user_id, title=over_max_title, body='Body')
        assert entry is None, "Title over max length should fail"
        
        # Body at max length should succeed
        max_body = 'a' * MAX_BODY_LENGTH
        entry = create_note(user_id=user_id, title='Title', body=max_body)
        assert entry is not None, "Body at max length should succeed"
        
        # Body one over max should fail
        over_max_body = 'a' * (MAX_BODY_LENGTH + 1)
        entry = create_note(user_id=user_id, title='Title', body=over_max_body)
        assert entry is None, "Body over max length should fail"
    
    @pytest.mark.file_io
    def test_validation_handles_empty_strings_vs_none(self, test_data_dir):
        """Test that validation correctly handles empty strings vs None."""
        user_id = "test_user_empty_vs_none"
        assert self._create_test_user(user_id, test_data_dir=test_data_dir), "Failed to create test user"
        
        # Empty string title should be treated as None (stripped)
        entry = create_note(user_id=user_id, title='   ', body='Body')
        # Should succeed (empty title is allowed if body exists)
        assert entry is not None, "Empty string title should be handled"
        
        # None title with body should succeed
        entry = create_note(user_id=user_id, title=None, body='Body')
        assert entry is not None, "None title with body should succeed"
        
        # Empty string body with title should succeed (stripped to None)
        entry = create_note(user_id=user_id, title='Title', body='   ')
        assert entry is not None, "Empty string body should be handled"
    
    @pytest.mark.file_io
    def test_validation_preserves_valid_data(self, test_data_dir):
        """Test that validation doesn't modify valid data."""
        user_id = "test_user_data_preservation"
        assert self._create_test_user(user_id, test_data_dir=test_data_dir), "Failed to create test user"
        
        # Create entry with specific content
        original_title = '  Test Title  '  # Has whitespace
        original_body = '  Test Body  '  # Has whitespace
        original_tags = ['#work', '#urgent']
        original_group = '  work  '  # Has whitespace
        
        entry = create_entry(
            user_id=user_id,
            kind='note',
            title=original_title,
            body=original_body,
            tags=original_tags,
            group=original_group
        )
        
        assert entry is not None, "Entry should be created"
        # Validation should strip whitespace but preserve content
        assert entry.title == 'Test Title', "Title should be stripped but preserved"
        assert entry.body == 'Test Body', "Body should be stripped but preserved"
        assert len(entry.tags) == 2, "Tags should be preserved"
        assert entry.group == 'work', "Group should be stripped but preserved"
