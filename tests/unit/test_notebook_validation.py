"""
Unit tests for notebook validation functions.
Tests focus on real behavior and side effects of validation operations.
"""

import pytest
from uuid import uuid4

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
    MAX_BODY_LENGTH,
    MAX_GROUP_LENGTH,
    MIN_SHORT_ID_LENGTH,
    MAX_SHORT_ID_LENGTH,
    ENTRY_KIND_PREFIXES,
    PREFIX_TO_KIND
)


class TestEntryReferenceValidation:
    """Test entry reference validation."""
    
    @pytest.mark.unit
    @pytest.mark.critical
    @pytest.mark.smoke
    def test_is_valid_entry_reference_with_valid_uuid(self):
        """Test UUID format validation."""
        valid_uuid = str(uuid4())
        result = is_valid_entry_reference(valid_uuid)
        assert result is True, f"Valid UUID {valid_uuid} should be accepted"
    
    @pytest.mark.unit
    @pytest.mark.critical
    def test_is_valid_entry_reference_with_short_id_prefix(self):
        """Test short ID with prefix format (e.g., 'n-3f2a9c')."""
        valid_refs = [
            'n-3f2a9c',
            'l-91ab20',
            'j-0c77e2',
            'N-ABCDEF',  # Case insensitive
            'n-12345678'  # Max length
        ]
        
        for ref in valid_refs:
            result = is_valid_entry_reference(ref)
            assert result is True, f"Short ID with prefix {ref} should be valid"
    
    @pytest.mark.unit
    @pytest.mark.critical
    def test_is_valid_entry_reference_with_short_id_fragment(self):
        """Test short ID fragment format (e.g., '3f2a9c')."""
        valid_refs = [
            '3f2a9c',
            '91ab20',
            'ABCDEF',  # Case insensitive
            '12345678'  # Max length
        ]
        
        for ref in valid_refs:
            result = is_valid_entry_reference(ref)
            assert result is True, f"Short ID fragment {ref} should be valid"
    
    @pytest.mark.unit
    @pytest.mark.critical
    def test_is_valid_entry_reference_with_title(self):
        """Test title string as reference."""
        valid_refs = [
            'My Note',
            'Shopping List',
            'A',
            'a' * 100  # Long title
        ]
        
        for ref in valid_refs:
            result = is_valid_entry_reference(ref)
            assert result is True, f"Title reference {ref} should be valid"
    
    @pytest.mark.unit
    @pytest.mark.regression
    def test_is_valid_entry_reference_with_invalid_formats(self):
        """Test invalid reference formats."""
        invalid_refs = [
            '',  # Empty
            '   ',  # Whitespace only
            'n-12345',  # Too short fragment
            'x-3f2a9c',  # Invalid prefix
            None,  # None value
            123,  # Non-string
        ]
        
        for ref in invalid_refs:
            result = is_valid_entry_reference(ref)
            assert result is False, f"Invalid reference {ref} should be rejected"


class TestShortIDParsing:
    """Test short ID parsing and formatting."""
    
    @pytest.mark.unit
    @pytest.mark.critical
    @pytest.mark.smoke
    def test_parse_short_id_with_prefix(self):
        """Test parsing short ID with prefix."""
        test_cases = [
            ('n-3f2a9c', ('n', '3f2a9c')),
            ('l-91ab20', ('l', '91ab20')),
            ('j-0c77e2', ('j', '0c77e2')),
            ('N-ABCDEF', ('n', 'abcdef')),  # Case normalization
        ]
        
        for ref, expected in test_cases:
            result = parse_short_id(ref)
            assert result == expected, f"Failed to parse {ref}: got {result}, expected {expected}"
    
    @pytest.mark.unit
    @pytest.mark.critical
    def test_parse_short_id_without_prefix(self):
        """Test parsing short ID fragment without prefix."""
        test_cases = [
            ('3f2a9c', (None, '3f2a9c')),
            ('91ab20', (None, '91ab20')),
            ('ABCDEF', (None, 'abcdef')),  # Case normalization
        ]
        
        for ref, expected in test_cases:
            result = parse_short_id(ref)
            assert result == expected, f"Failed to parse {ref}: got {result}, expected {expected}"
    
    @pytest.mark.unit
    @pytest.mark.regression
    def test_parse_short_id_with_invalid_formats(self):
        """Test parsing invalid short ID formats."""
        invalid_refs = [
            '',  # Empty
            'n-12345',  # Too short
            'x-3f2a9c',  # Invalid prefix
            'not-a-short-id',  # Not a short ID
            None,  # None value
            123,  # Non-string
        ]
        
        for ref in invalid_refs:
            result = parse_short_id(ref)
            assert result is None, f"Invalid reference {ref} should return None, got {result}"
    
    @pytest.mark.unit
    @pytest.mark.critical
    def test_format_short_id(self):
        """Test formatting UUID to short ID."""
        test_uuid = uuid4()
        
        for kind, prefix in ENTRY_KIND_PREFIXES.items():
            result = format_short_id(test_uuid, kind)
            assert result is not None, f"Should format short ID for {kind}"
            assert result.startswith(f"{prefix}-"), f"Short ID should start with {prefix}-"
            assert len(result.split('-')[1]) >= MIN_SHORT_ID_LENGTH, "Fragment should meet minimum length"
    
    @pytest.mark.unit
    @pytest.mark.regression
    def test_format_short_id_with_invalid_inputs(self):
        """Test formatting with invalid inputs."""
        test_uuid = uuid4()
        
        # Invalid kind
        result = format_short_id(test_uuid, 'invalid')
        assert result is None, "Invalid kind should return None"
        
        # Invalid UUID type
        result = format_short_id('not-a-uuid', 'note')
        assert result is None, "Non-UUID should return None"


class TestEntryTitleValidation:
    """Test entry title validation."""
    
    @pytest.mark.unit
    @pytest.mark.critical
    @pytest.mark.smoke
    def test_is_valid_entry_title_with_valid_titles(self):
        """Test valid entry titles."""
        valid_titles = [
            None,  # Optional
            'My Note',
            'A',  # Single character
            'a' * MAX_TITLE_LENGTH,  # Max length
            '  Padded Title  ',  # Will be stripped
        ]
        
        for title in valid_titles:
            result = is_valid_entry_title(title)
            assert result is True, f"Valid title {title} should be accepted"
    
    @pytest.mark.unit
    @pytest.mark.critical
    @pytest.mark.regression
    def test_is_valid_entry_title_with_invalid_titles(self):
        """Test invalid entry titles."""
        invalid_titles = [
            'a' * (MAX_TITLE_LENGTH + 1),  # Too long
            123,  # Non-string
            [],  # Non-string
        ]
        
        for title in invalid_titles:
            result = is_valid_entry_title(title)
            assert result is False, f"Invalid title {title} should be rejected"


class TestEntryBodyValidation:
    """Test entry body validation."""
    
    @pytest.mark.unit
    @pytest.mark.critical
    @pytest.mark.smoke
    def test_is_valid_entry_body_with_valid_bodies(self):
        """Test valid entry bodies."""
        valid_bodies = [
            None,  # Optional
            'My note body',
            'A',  # Single character
            'a' * MAX_BODY_LENGTH,  # Max length
            '  Padded Body  ',  # Will be stripped
        ]
        
        for body in valid_bodies:
            result = is_valid_entry_body(body)
            assert result is True, f"Valid body {body} should be accepted"
    
    @pytest.mark.unit
    @pytest.mark.critical
    def test_is_valid_entry_body_for_lists(self):
        """Test body validation for list entries (body is optional)."""
        valid_bodies = [
            None,
            '',
            'Optional description',
        ]
        
        for body in valid_bodies:
            result = is_valid_entry_body(body, kind='list')
            assert result is True, f"Body {body} should be valid for lists"
    
    @pytest.mark.unit
    @pytest.mark.regression
    def test_is_valid_entry_body_with_invalid_bodies(self):
        """Test invalid entry bodies."""
        invalid_bodies = [
            'a' * (MAX_BODY_LENGTH + 1),  # Too long
            123,  # Non-string
            [],  # Non-string
        ]
        
        for body in invalid_bodies:
            result = is_valid_entry_body(body)
            assert result is False, f"Invalid body {body} should be rejected"


class TestEntryGroupValidation:
    """Test entry group validation."""
    
    @pytest.mark.unit
    @pytest.mark.critical
    @pytest.mark.smoke
    def test_is_valid_entry_group_with_valid_groups(self):
        """Test valid entry groups."""
        valid_groups = [
            None,  # Optional
            'work',
            'home',
            'health',
            'Work Group',  # With spaces
            'work-group',  # With hyphens
            'work_group',  # With underscores
            'a' * MAX_GROUP_LENGTH,  # Max length
        ]
        
        for group in valid_groups:
            result = is_valid_entry_group(group)
            assert result is True, f"Valid group {group} should be accepted"
    
    @pytest.mark.unit
    @pytest.mark.critical
    @pytest.mark.regression
    def test_is_valid_entry_group_with_invalid_groups(self):
        """Test invalid entry groups."""
        invalid_groups = [
            '',  # Empty string
            '   ',  # Whitespace only
            'a' * (MAX_GROUP_LENGTH + 1),  # Too long
            'group@invalid',  # Invalid characters
            'group#invalid',  # Invalid characters
            123,  # Non-string
        ]
        
        for group in invalid_groups:
            result = is_valid_entry_group(group)
            assert result is False, f"Invalid group {group} should be rejected"


class TestEntryKindValidation:
    """Test entry kind validation."""
    
    @pytest.mark.unit
    @pytest.mark.critical
    @pytest.mark.smoke
    def test_is_valid_entry_kind_with_valid_kinds(self):
        """Test valid entry kinds."""
        valid_kinds = ['note', 'list', 'journal', 'NOTE', 'List', 'JOURNAL']
        
        for kind in valid_kinds:
            result = is_valid_entry_kind(kind)
            assert result is True, f"Valid kind {kind} should be accepted"
    
    @pytest.mark.unit
    @pytest.mark.critical
    @pytest.mark.regression
    def test_is_valid_entry_kind_with_invalid_kinds(self):
        """Test invalid entry kinds."""
        invalid_kinds = [
            'invalid',
            'task',
            '',
            None,
            123,
        ]
        
        for kind in invalid_kinds:
            result = is_valid_entry_kind(kind)
            assert result is False, f"Invalid kind {kind} should be rejected"


class TestListItemIndexValidation:
    """Test list item index validation."""
    
    @pytest.mark.unit
    @pytest.mark.critical
    @pytest.mark.smoke
    def test_is_valid_list_item_index_with_valid_indices(self):
        """Test valid list item indices (both 0-based and 1-based)."""
        list_length = 5
        
        # 0-based indices
        valid_0_based = [0, 1, 2, 3, 4]
        for idx in valid_0_based:
            result = is_valid_list_item_index(idx, list_length)
            assert result is True, f"0-based index {idx} should be valid for list of length {list_length}"
        
        # 1-based indices
        valid_1_based = [1, 2, 3, 4, 5]
        for idx in valid_1_based:
            result = is_valid_list_item_index(idx, list_length)
            assert result is True, f"1-based index {idx} should be valid for list of length {list_length}"
    
    @pytest.mark.unit
    @pytest.mark.critical
    @pytest.mark.regression
    def test_is_valid_list_item_index_with_invalid_indices(self):
        """Test invalid list item indices."""
        list_length = 5
        
        invalid_indices = [
            -1,  # Negative
            6,  # Out of range (both 0-based and 1-based)
            100,  # Way out of range
            None,  # None value
            '1',  # String
        ]
        
        for idx in invalid_indices:
            result = is_valid_list_item_index(idx, list_length)
            assert result is False, f"Invalid index {idx} should be rejected for list of length {list_length}"
        
        # Index 5 is valid as 1-based (last item) for list of length 5
        result = is_valid_list_item_index(5, list_length)
        assert result is True, f"Index 5 should be valid as 1-based for list of length {list_length}"
    
    @pytest.mark.unit
    @pytest.mark.critical
    def test_normalize_list_item_index(self):
        """Test normalizing list item index to 0-based."""
        list_length = 5
        
        test_cases = [
            (0, 0),  # Already 0-based (only valid as 0-based)
            (1, 1),  # Ambiguous: valid as both 0-based (2nd item) and 1-based (1st item)
                     # Prioritizes 0-based (programming convention) -> returns 1
            (5, 4),  # Only valid as 1-based (last item) -> converts to 0-based (4)
            (4, 4),  # Ambiguous: valid as both 0-based (5th item) and 1-based (4th item)
                     # Prioritizes 0-based (programming convention) -> returns 4
        ]
        
        for input_idx, expected_output in test_cases:
            result = normalize_list_item_index(input_idx, list_length)
            assert result == expected_output, f"Index {input_idx} should normalize to {expected_output}, got {result}"
    
    @pytest.mark.unit
    @pytest.mark.regression
    def test_normalize_list_item_index_with_invalid_indices(self):
        """Test normalizing invalid indices."""
        list_length = 5
        
        invalid_indices = [-1, 6, 100, None, '1']
        
        for idx in invalid_indices:
            result = normalize_list_item_index(idx, list_length)
            assert result is None, f"Invalid index {idx} should return None, got {result}"


class TestEntryContentValidation:
    """Test comprehensive entry content validation."""
    
    @pytest.mark.unit
    @pytest.mark.critical
    @pytest.mark.smoke
    def test_validate_entry_content_with_valid_content(self):
        """Test validation of valid entry content."""
        test_cases = [
            # Note with title and body
            {'title': 'My Note', 'body': 'Note body', 'kind': 'note'},
            # Note with title only
            {'title': 'Title Only', 'body': None, 'kind': 'note'},
            # Note with body only
            {'title': None, 'body': 'Body Only', 'kind': 'note'},
            # List (body optional)
            {'title': 'Shopping List', 'body': None, 'kind': 'list'},
            # Journal
            {'title': 'Journal Entry', 'body': 'Journal body', 'kind': 'journal'},
        ]
        
        for content in test_cases:
            is_valid, error = validate_entry_content(
                title=content.get('title'),
                body=content.get('body'),
                kind=content['kind']
            )
            assert is_valid is True, f"Valid content {content} should pass validation, got error: {error}"
            assert error is None, f"Valid content should have no error message"
    
    @pytest.mark.unit
    @pytest.mark.critical
    @pytest.mark.regression
    def test_validate_entry_content_with_invalid_content(self):
        """Test validation of invalid entry content."""
        test_cases = [
            # Note with neither title nor body
            {'title': None, 'body': None, 'kind': 'note', 'expected_error': 'must have at least'},
            # Invalid kind
            {'title': 'Test', 'body': 'Body', 'kind': 'invalid', 'expected_error': 'Invalid entry kind'},
            # Title too long
            {'title': 'a' * (MAX_TITLE_LENGTH + 1), 'body': 'Body', 'kind': 'note', 'expected_error': 'title'},
            # Body too long
            {'title': 'Title', 'body': 'a' * (MAX_BODY_LENGTH + 1), 'kind': 'note', 'expected_error': 'body'},
        ]
        
        for content in test_cases:
            is_valid, error = validate_entry_content(
                title=content.get('title'),
                body=content.get('body'),
                kind=content['kind']
            )
            assert is_valid is False, f"Invalid content {content} should fail validation"
            assert error is not None, f"Invalid content should have error message"
            if 'expected_error' in content:
                assert content['expected_error'].lower() in error.lower(), f"Error message should mention {content['expected_error']}"


class TestValidationConstants:
    """Test validation constants are properly defined."""
    
    @pytest.mark.unit
    def test_validation_constants_defined(self):
        """Test that all validation constants are defined."""
        assert MAX_TITLE_LENGTH > 0
        assert MAX_BODY_LENGTH > 0
        assert MAX_GROUP_LENGTH > 0
        assert MIN_SHORT_ID_LENGTH > 0
        assert MAX_SHORT_ID_LENGTH >= MIN_SHORT_ID_LENGTH
    
    @pytest.mark.unit
    def test_entry_kind_prefixes_defined(self):
        """Test that entry kind prefixes are properly defined."""
        assert 'note' in ENTRY_KIND_PREFIXES
        assert 'list' in ENTRY_KIND_PREFIXES
        assert 'journal' in ENTRY_KIND_PREFIXES
        assert ENTRY_KIND_PREFIXES['note'] == 'n'
        assert ENTRY_KIND_PREFIXES['list'] == 'l'
        assert ENTRY_KIND_PREFIXES['journal'] == 'j'
    
    @pytest.mark.unit
    def test_prefix_to_kind_mapping(self):
        """Test that prefix to kind mapping is correct."""
        assert PREFIX_TO_KIND['n'] == 'note'
        assert PREFIX_TO_KIND['l'] == 'list'
        assert PREFIX_TO_KIND['j'] == 'journal'
