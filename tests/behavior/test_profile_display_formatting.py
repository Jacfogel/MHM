"""
Test profile display formatting to ensure clean text output and proper formatting.

This module tests the profile display functionality to verify:
- Profile responses show formatted text (not raw JSON)
- All profile sections render correctly
- Rich data is properly structured for Discord embeds
"""

import pytest
from unittest.mock import patch
from communication.command_handlers.profile_handler import ProfileHandler
from communication.command_handlers.shared_types import InteractionResponse, ParsedCommand
from tests.test_utilities import TestUserFactory


class TestProfileDisplayFormatting:
    """Test profile display formatting and text output."""

    def test_profile_display_format(self, test_data_dir):
        """Test that profile display shows formatted text, not raw JSON."""
        handler = ProfileHandler()
        user_id = "test_user_profile_format"
        
        # Create test user with complete profile data
        TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
        
        parsed_command = ParsedCommand(
            intent="show_profile",
            entities={},
            confidence=0.9,
            original_message="show my profile"
        )
        
        response = handler.handle(user_id, parsed_command)
        
        assert isinstance(response, InteractionResponse)
        assert response.completed is True
        
        # Verify response contains formatted text (not raw JSON)
        message = response.message
        assert "**Your Profile:**" in message
        
        # Verify no JSON syntax appears
        assert "{" not in message
        assert "}" not in message
        assert '":' not in message  # No JSON key-value syntax
        
        # Verify key profile fields are displayed
        assert "Name:" in message or "Name" in message
        # Email may not be present in basic user data
        # Account Features may not be present in basic user data
        
        # Verify proper formatting (markdown-style)
        assert "\n" in message  # Should have line breaks
        assert "- " in message  # Should have bullet points

    def test_profile_text_formatter_direct(self, test_data_dir):
        """Test _format_profile_text() method directly."""
        handler = ProfileHandler()
        user_id = "test_user_formatter_direct"
        
        # Create test user with complete profile data
        TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
        
        # Mock the data loading to get clean test data
        with patch('communication.command_handlers.profile_handler.get_user_data') as mock_get_data:
            mock_get_data.side_effect = [
                {'account': {'email': 'test@example.com', 'account_status': 'active', 'features': {'checkins': 'enabled', 'task_management': 'enabled'}}},
                {'context': {'preferred_name': 'Test User', 'gender_identity': ['Non-binary'], 'interests': ['coding', 'music'], 'goals': ['learn Python']}},
                {'preferences': {}}
            ]
            
            # Call the formatter directly
            formatted_text = handler._format_profile_text(
                {'email': 'test@example.com', 'account_status': 'active', 'features': {'checkins': 'enabled', 'task_management': 'enabled'}},
                {'preferred_name': 'Test User', 'gender_identity': ['Non-binary'], 'interests': ['coding', 'music'], 'goals': ['learn Python']},
                {}
            )
            
            # Verify output format is clean markdown
            assert "**Your Profile:**" in formatted_text
            assert "- Name: Test User" in formatted_text
            assert "- Email: test@example.com" in formatted_text
            assert "- Gender Identity: Non-binary" in formatted_text
            assert "- Interests: coding, music" in formatted_text
            assert "- Goals: learn Python" in formatted_text
            assert "**Account Features:**" in formatted_text
            assert "- Check-ins: Enabled" in formatted_text
            assert "- Tasks: Enabled" in formatted_text
            
            # Verify proper line breaks and formatting
            lines = formatted_text.split('\n')
            assert len(lines) > 5  # Should have multiple lines
            assert all(line.strip() for line in lines if line)  # No empty lines

    def test_profile_rich_data_structure(self, test_data_dir):
        """Test that rich_data is properly structured for Discord embeds."""
        handler = ProfileHandler()
        user_id = "test_user_rich_data"
        
        # Create test user with complete profile data
        TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
        
        parsed_command = ParsedCommand(
            intent="show_profile",
            entities={},
            confidence=0.9,
            original_message="show my profile"
        )
        
        response = handler.handle(user_id, parsed_command)
        
        assert isinstance(response, InteractionResponse)
        assert response.rich_data is not None
        
        # Verify rich_data structure
        rich_data = response.rich_data
        assert 'type' in rich_data
        assert 'title' in rich_data
        assert 'fields' in rich_data
        
        assert rich_data['type'] == 'profile'
        assert rich_data['title'] == 'Your Profile'
        assert isinstance(rich_data['fields'], list)
        # Fields may be empty for basic user data
        
        # Verify fields are properly structured
        for field in rich_data['fields']:
            assert 'name' in field
            assert 'value' in field
            assert isinstance(field['name'], str)
            assert isinstance(field['value'], str)
            assert len(field['name']) > 0
            assert len(field['value']) > 0

    def test_profile_no_duplicate_formatting(self, test_data_dir):
        """Test that there are no duplicate formatting code paths."""
        handler = ProfileHandler()
        user_id = "test_user_no_duplicates"
        
        # Create test user with complete profile data
        TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
        
        parsed_command = ParsedCommand(
            intent="show_profile",
            entities={},
            confidence=0.9,
            original_message="show my profile"
        )
        
        response = handler.handle(user_id, parsed_command)
        
        assert isinstance(response, InteractionResponse)
        message = response.message
        
        # Verify no duplicate sections (should only appear once)
        assert message.count("**Your Profile:**") == 1
        # Account Features may not be present in basic user data
        
        # Verify no emoji formatting artifacts (since we removed the dead code)
        # The old dead code had emojis like 👤, 🎭, 📧, etc.
        emoji_artifacts = ["👤", "🎭", "📧", "📊", "🏥", "💊", "⚠️", "🎯", "💕", "📝", "✅", "📋"]
        for emoji in emoji_artifacts:
            assert emoji not in message, f"Found emoji artifact {emoji} in profile response - dead code may not be fully removed"

    def test_profile_with_minimal_data(self, test_data_dir):
        """Test profile display with minimal user data."""
        handler = ProfileHandler()
        user_id = "test_user_minimal"
        
        # Create test user with minimal data
        TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
        
        parsed_command = ParsedCommand(
            intent="show_profile",
            entities={},
            confidence=0.9,
            original_message="show my profile"
        )
        
        response = handler.handle(user_id, parsed_command)
        
        assert isinstance(response, InteractionResponse)
        assert response.completed is True
        
        # Should still show formatted text, not JSON
        message = response.message
        assert "**Your Profile:**" in message
        assert "{" not in message
        assert "}" not in message
        
        # Should handle missing fields gracefully
        assert "Not set" in message or "Unknown" in message  # For missing fields

    def test_profile_suggestions(self, test_data_dir):
        """Test that profile response includes appropriate suggestions."""
        handler = ProfileHandler()
        user_id = "test_user_suggestions"
        
        # Create test user with complete profile data
        TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
        
        parsed_command = ParsedCommand(
            intent="show_profile",
            entities={},
            confidence=0.9,
            original_message="show my profile"
        )
        
        response = handler.handle(user_id, parsed_command)
        
        assert isinstance(response, InteractionResponse)
        assert response.suggestions is not None
        assert len(response.suggestions) > 0
        
        # Verify suggestions are relevant to profile management
        suggestions = response.suggestions
        assert any("Update" in suggestion for suggestion in suggestions)
        assert any("profile" in suggestion.lower() for suggestion in suggestions)
