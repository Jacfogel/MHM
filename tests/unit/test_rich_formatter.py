"""
Rich Formatter Tests

Tests for communication/communication_channels/base/rich_formatter.py:
- DiscordRichFormatter functionality
- EmailRichFormatter functionality
- Factory function behavior
- Error handling and edge cases
"""

import pytest
from unittest.mock import patch, MagicMock

from communication.communication_channels.base.rich_formatter import (
    RichFormatter,
    DiscordRichFormatter,
    EmailRichFormatter,
    get_rich_formatter
)


class TestDiscordRichFormatter:
    """Test DiscordRichFormatter functionality"""
    
    @pytest.fixture
    def mock_discord(self):
        """Create a mock Discord library"""
        mock_discord = MagicMock()
        # Make Embed a callable class that returns a mock embed
        mock_embed_class = MagicMock()
        mock_embed_instance = MagicMock()
        mock_embed_class.return_value = mock_embed_instance
        mock_discord.Embed = mock_embed_class
        
        mock_discord.ui = MagicMock()
        mock_view_class = MagicMock()
        mock_view_instance = MagicMock()
        mock_view_class.return_value = mock_view_instance
        mock_discord.ui.View = mock_view_class
        
        mock_button_class = MagicMock()
        mock_button_instance = MagicMock()
        mock_button_class.return_value = mock_button_instance
        mock_discord.ui.Button = mock_button_class
        
        mock_discord.ButtonStyle = MagicMock()
        mock_discord.ButtonStyle.primary = "primary"
        mock_discord.Color = MagicMock()
        mock_discord.Color.green = MagicMock(return_value=0x00ff00)
        mock_discord.Color.red = MagicMock(return_value=0xff0000)
        mock_discord.Color.yellow = MagicMock(return_value=0xffff00)
        mock_discord.Color.blue = MagicMock(return_value=0x0000ff)
        mock_discord.Color.purple = MagicMock(return_value=0x800080)
        mock_discord.Color.orange = MagicMock(return_value=0xffa500)
        mock_discord.Color.teal = MagicMock(return_value=0x008080)
        mock_discord.Color.light_grey = MagicMock(return_value=0xcccccc)
        
        # Store the mock embed instance for tests to access
        mock_discord._mock_embed = mock_embed_instance
        mock_discord._mock_view = mock_view_instance
        return mock_discord
    
    @pytest.fixture
    def formatter_with_discord(self, mock_discord):
        """Create a DiscordRichFormatter with mocked Discord library"""
        import builtins
        original_import = builtins.__import__
        
        def mock_import(name, *args, **kwargs):
            if name == 'discord':
                return mock_discord
            return original_import(name, *args, **kwargs)
        
        with patch('builtins.__import__', side_effect=mock_import):
            formatter = DiscordRichFormatter()
            formatter.discord = mock_discord
            return formatter
    
    @pytest.fixture
    def formatter_without_discord(self):
        """Create a DiscordRichFormatter without Discord library"""
        import builtins
        original_import = builtins.__import__
        
        def mock_import(name, *args, **kwargs):
            if name == 'discord':
                raise ImportError("No module named 'discord'")
            return original_import(name, *args, **kwargs)
        
        with patch('builtins.__import__', side_effect=mock_import):
            formatter = DiscordRichFormatter()
            return formatter
    
    @pytest.mark.communication
    @pytest.mark.unit
    def test_initialization_with_discord(self, mock_discord):
        """Test: DiscordRichFormatter initializes correctly with Discord library"""
        # Arrange
        import builtins
        original_import = builtins.__import__
        
        def mock_import(name, *args, **kwargs):
            if name == 'discord':
                return mock_discord
            return original_import(name, *args, **kwargs)
        
        # Act
        with patch('builtins.__import__', side_effect=mock_import):
            formatter = DiscordRichFormatter()
        
        # Assert
        assert formatter.discord is not None, "Should have Discord library available"
    
    @pytest.mark.communication
    @pytest.mark.unit
    def test_initialization_without_discord(self):
        """Test: DiscordRichFormatter handles missing Discord library gracefully"""
        # Arrange & Act
        with patch('builtins.__import__', side_effect=ImportError("No module named 'discord'")):
            formatter = DiscordRichFormatter()
        
        # Assert
        assert formatter.discord is None, "Should handle missing Discord library"
    
    @pytest.mark.communication
    @pytest.mark.unit
    def test_create_embed_with_title(self, formatter_with_discord, mock_discord):
        """Test: create_embed creates embed with title from rich data"""
        # Arrange
        message = "Test message"
        rich_data = {"title": "Test Title"}
        mock_embed = mock_discord._mock_embed
        
        # Act
        result = formatter_with_discord.create_embed(message, rich_data)
        
        # Assert
        assert result is not None, "Should return embed"
        assert mock_embed.title == "Test Title", "Should set title on embed"
    
    @pytest.mark.communication
    @pytest.mark.unit
    def test_create_embed_with_description(self, formatter_with_discord, mock_discord):
        """Test: create_embed creates embed with description from rich data"""
        # Arrange
        message = "Test message"
        rich_data = {"description": "Test Description"}
        mock_embed = mock_discord._mock_embed
        
        # Act
        result = formatter_with_discord.create_embed(message, rich_data)
        
        # Assert
        assert result is not None, "Should return embed"
        assert mock_embed.description == "Test Description", "Should set description on embed"
    
    @pytest.mark.communication
    @pytest.mark.unit
    def test_create_embed_with_message_as_description(self, formatter_with_discord, mock_discord):
        """Test: create_embed uses message as description when not in rich data"""
        # Arrange
        message = "Test message"
        rich_data = {}
        mock_embed = mock_discord._mock_embed
        
        # Act
        result = formatter_with_discord.create_embed(message, rich_data)
        
        # Assert
        assert result is not None, "Should return embed"
        assert mock_embed.description == message, "Should use message as description"
    
    @pytest.mark.communication
    @pytest.mark.unit
    def test_create_embed_extracts_title_from_message(self, formatter_with_discord, mock_discord):
        """Test: create_embed extracts title from message when starts with **"""
        # Arrange
        message = "**Test Title**\nMessage body"
        rich_data = {}
        mock_embed = mock_discord._mock_embed
        
        # Act
        result = formatter_with_discord.create_embed(message, rich_data)
        
        # Assert
        assert result is not None, "Should return embed"
        assert mock_embed.title == "Test Title", "Should extract title from message"
    
    @pytest.mark.communication
    @pytest.mark.unit
    def test_create_embed_with_fields(self, formatter_with_discord, mock_discord):
        """Test: create_embed adds fields to embed"""
        # Arrange
        message = "Test message"
        rich_data = {
            "fields": [
                {"name": "Field1", "value": "Value1", "inline": False},
                {"name": "Field2", "value": "Value2", "inline": True}
            ]
        }
        mock_embed = mock_discord._mock_embed
        
        # Act
        result = formatter_with_discord.create_embed(message, rich_data)
        
        # Assert
        assert result is not None, "Should return embed"
        assert mock_embed.add_field.call_count == 2, "Should add both fields"
    
    @pytest.mark.communication
    @pytest.mark.unit
    def test_create_embed_with_footer(self, formatter_with_discord, mock_discord):
        """Test: create_embed sets footer on embed"""
        # Arrange
        message = "Test message"
        rich_data = {"footer": "Test Footer"}
        mock_embed = mock_discord._mock_embed
        
        # Act
        result = formatter_with_discord.create_embed(message, rich_data)
        
        # Assert
        assert result is not None, "Should return embed"
        mock_embed.set_footer.assert_called_once_with(text="Test Footer")
    
    @pytest.mark.communication
    @pytest.mark.unit
    def test_create_embed_with_timestamp(self, formatter_with_discord, mock_discord):
        """Test: create_embed sets timestamp on embed"""
        # Arrange
        message = "Test message"
        from datetime import datetime
        timestamp = datetime.now()
        rich_data = {"timestamp": timestamp}
        mock_embed = mock_discord._mock_embed
        
        # Act
        result = formatter_with_discord.create_embed(message, rich_data)
        
        # Assert
        assert result is not None, "Should return embed"
        assert mock_embed.timestamp == timestamp, "Should set timestamp on embed"
    
    @pytest.mark.communication
    @pytest.mark.unit
    def test_create_embed_without_discord(self, formatter_without_discord):
        """Test: create_embed returns None when Discord library not available"""
        # Arrange
        message = "Test message"
        rich_data = {"title": "Test Title"}
        
        # Act
        result = formatter_without_discord.create_embed(message, rich_data)
        
        # Assert
        assert result is None, "Should return None when Discord library not available"
    
    @pytest.mark.communication
    @pytest.mark.unit
    def test_create_interactive_view_with_suggestions(self, formatter_with_discord, mock_discord):
        """Test: create_interactive_view creates view with buttons from suggestions"""
        # Arrange
        suggestions = ["Option 1", "Option 2", "Option 3"]
        mock_view = mock_discord._mock_view
        
        # Act
        result = formatter_with_discord.create_interactive_view(suggestions)
        
        # Assert
        assert result is not None, "Should return view"
        assert mock_view.add_item.call_count == 3, "Should add buttons for all suggestions"
    
    @pytest.mark.communication
    @pytest.mark.unit
    def test_create_interactive_view_limits_to_five(self, formatter_with_discord, mock_discord):
        """Test: create_interactive_view limits buttons to 5"""
        # Arrange
        suggestions = [f"Option {i}" for i in range(10)]
        mock_view = mock_discord._mock_view
        
        # Act
        result = formatter_with_discord.create_interactive_view(suggestions)
        
        # Assert
        assert result is not None, "Should return view"
        assert mock_view.add_item.call_count == 5, "Should limit to 5 buttons"
    
    @pytest.mark.communication
    @pytest.mark.unit
    def test_create_interactive_view_without_discord(self, formatter_without_discord):
        """Test: create_interactive_view returns None when Discord library not available"""
        # Arrange
        suggestions = ["Option 1", "Option 2"]
        
        # Act
        result = formatter_without_discord.create_interactive_view(suggestions)
        
        # Assert
        assert result is None, "Should return None when Discord library not available"
    
    @pytest.mark.communication
    @pytest.mark.unit
    def test_get_color_for_type_success(self, formatter_with_discord, mock_discord):
        """Test: get_color_for_type returns correct color for content type"""
        # Arrange
        content_type = "success"
        
        # Act
        result = formatter_with_discord.get_color_for_type(content_type)
        
        # Assert
        assert result is not None, "Should return color"
    
    @pytest.mark.communication
    @pytest.mark.unit
    def test_get_color_for_type_default(self, formatter_with_discord, mock_discord):
        """Test: get_color_for_type returns default color for unknown type"""
        # Arrange
        content_type = "unknown_type"
        
        # Act
        result = formatter_with_discord.get_color_for_type(content_type)
        
        # Assert
        assert result is not None, "Should return default color"
    
    @pytest.mark.communication
    @pytest.mark.unit
    def test_get_color_for_type_without_discord(self, formatter_without_discord):
        """Test: get_color_for_type returns None when Discord library not available"""
        # Arrange
        content_type = "success"
        
        # Act
        result = formatter_without_discord.get_color_for_type(content_type)
        
        # Assert
        assert result is None, "Should return None when Discord library not available"


class TestEmailRichFormatter:
    """Test EmailRichFormatter functionality"""
    
    @pytest.fixture
    def formatter(self):
        """Create an EmailRichFormatter instance"""
        return EmailRichFormatter()
    
    @pytest.mark.communication
    @pytest.mark.unit
    def test_create_embed_with_title(self, formatter):
        """Test: create_embed creates HTML with title"""
        # Arrange
        message = "Test message"
        rich_data = {"title": "Test Title"}
        
        # Act
        result = formatter.create_embed(message, rich_data)
        
        # Assert
        assert "<h2" in result, "Should include HTML title tag"
        assert "Test Title" in result, "Should include title text"
    
    @pytest.mark.communication
    @pytest.mark.unit
    def test_create_embed_with_description(self, formatter):
        """Test: create_embed creates HTML with description"""
        # Arrange
        message = "Test message"
        rich_data = {"description": "Test Description"}
        
        # Act
        result = formatter.create_embed(message, rich_data)
        
        # Assert
        assert "<p>Test Description</p>" in result, "Should include description paragraph"
    
    @pytest.mark.communication
    @pytest.mark.unit
    def test_create_embed_with_message_as_description(self, formatter):
        """Test: create_embed uses message as description when not in rich data"""
        # Arrange
        message = "Test message"
        rich_data = {}
        
        # Act
        result = formatter.create_embed(message, rich_data)
        
        # Assert
        assert f"<p>{message}</p>" in result, "Should use message as description"
    
    @pytest.mark.communication
    @pytest.mark.unit
    def test_create_embed_with_fields(self, formatter):
        """Test: create_embed creates HTML table with fields"""
        # Arrange
        message = "Test message"
        rich_data = {
            "fields": [
                {"name": "Field1", "value": "Value1"},
                {"name": "Field2", "value": "Value2"}
            ]
        }
        
        # Act
        result = formatter.create_embed(message, rich_data)
        
        # Assert
        assert "<table" in result, "Should include HTML table"
        assert "Field1" in result, "Should include first field name"
        assert "Value1" in result, "Should include first field value"
        assert "Field2" in result, "Should include second field name"
        assert "Value2" in result, "Should include second field value"
    
    @pytest.mark.communication
    @pytest.mark.unit
    def test_create_embed_with_footer(self, formatter):
        """Test: create_embed creates HTML with footer"""
        # Arrange
        message = "Test message"
        rich_data = {"footer": "Test Footer"}
        
        # Act
        result = formatter.create_embed(message, rich_data)
        
        # Assert
        assert "<hr" in result, "Should include horizontal rule"
        assert "Test Footer" in result, "Should include footer text"
    
    @pytest.mark.communication
    @pytest.mark.unit
    def test_create_interactive_view_with_suggestions(self, formatter):
        """Test: create_interactive_view creates HTML buttons from suggestions"""
        # Arrange
        suggestions = ["Option 1", "Option 2", "Option 3"]
        
        # Act
        result = formatter.create_interactive_view(suggestions)
        
        # Assert
        assert "<div" in result, "Should include div container"
        assert "<a href='#'" in result, "Should include anchor tags"
        assert "Option 1" in result, "Should include first suggestion"
        assert "Option 2" in result, "Should include second suggestion"
        assert "Option 3" in result, "Should include third suggestion"
    
    @pytest.mark.communication
    @pytest.mark.unit
    def test_create_interactive_view_with_empty_list(self, formatter):
        """Test: create_interactive_view handles empty suggestions"""
        # Arrange
        suggestions = []
        
        # Act
        result = formatter.create_interactive_view(suggestions)
        
        # Assert
        assert result == "", "Should return empty string for empty suggestions"
    
    @pytest.mark.communication
    @pytest.mark.unit
    def test_create_interactive_view_limits_to_five(self, formatter):
        """Test: create_interactive_view limits suggestions to 5"""
        # Arrange
        suggestions = [f"Option {i}" for i in range(10)]
        
        # Act
        result = formatter.create_interactive_view(suggestions)
        
        # Assert
        assert "Option 4" in result, "Should include fifth suggestion"
        assert "Option 5" not in result, "Should not include sixth suggestion"
    
    @pytest.mark.communication
    @pytest.mark.unit
    def test_get_color_for_type_success(self, formatter):
        """Test: get_color_for_type returns correct color for content type"""
        # Arrange
        content_type = "success"
        
        # Act
        result = formatter.get_color_for_type(content_type)
        
        # Assert
        assert result == "#27ae60", "Should return success color"
    
    @pytest.mark.communication
    @pytest.mark.unit
    def test_get_color_for_type_error(self, formatter):
        """Test: get_color_for_type returns correct color for error type"""
        # Arrange
        content_type = "error"
        
        # Act
        result = formatter.get_color_for_type(content_type)
        
        # Assert
        assert result == "#e74c3c", "Should return error color"
    
    @pytest.mark.communication
    @pytest.mark.unit
    def test_get_color_for_type_default(self, formatter):
        """Test: get_color_for_type returns default color for unknown type"""
        # Arrange
        content_type = "unknown_type"
        
        # Act
        result = formatter.get_color_for_type(content_type)
        
        # Assert
        assert result == "#3498db", "Should return default color"


class TestRichFormatterFactory:
    """Test get_rich_formatter factory function"""
    
    @pytest.mark.communication
    @pytest.mark.unit
    def test_get_rich_formatter_for_discord(self):
        """Test: get_rich_formatter returns DiscordRichFormatter for discord"""
        # Arrange
        import builtins
        original_import = builtins.__import__
        mock_discord = MagicMock()
        
        def mock_import(name, *args, **kwargs):
            if name == 'discord':
                return mock_discord
            return original_import(name, *args, **kwargs)
        
        # Act
        with patch('builtins.__import__', side_effect=mock_import):
            formatter = get_rich_formatter("discord")
        
        # Assert
        assert isinstance(formatter, DiscordRichFormatter), "Should return DiscordRichFormatter for discord"
    
    @pytest.mark.communication
    @pytest.mark.unit
    def test_get_rich_formatter_for_email(self):
        """Test: get_rich_formatter returns EmailRichFormatter for email"""
        # Arrange & Act
        formatter = get_rich_formatter("email")
        
        # Assert
        assert isinstance(formatter, EmailRichFormatter), "Should return EmailRichFormatter for email"
    
    @pytest.mark.communication
    @pytest.mark.unit
    def test_get_rich_formatter_for_unknown_type(self):
        """Test: get_rich_formatter returns EmailRichFormatter for unknown type"""
        # Arrange & Act
        formatter = get_rich_formatter("unknown")
        
        # Assert
        assert isinstance(formatter, EmailRichFormatter), "Should return EmailRichFormatter as default"
    
    @pytest.mark.communication
    @pytest.mark.unit
    def test_get_rich_formatter_handles_exception(self):
        """Test: get_rich_formatter handles exceptions and returns default"""
        # Arrange
        with patch('communication.communication_channels.base.rich_formatter.DiscordRichFormatter', side_effect=Exception("Test error")):
            # Act
            formatter = get_rich_formatter("discord")
            
            # Assert
            assert isinstance(formatter, EmailRichFormatter), "Should return default formatter on error"

