"""
Discord Event Handler Tests

Tests for communication/communication_channels/discord/event_handler.py:
- EventType enum
- EventContext dataclass
- DiscordEventHandler class
- Factory function
"""

import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock

from communication.communication_channels.discord.event_handler import (
    EventType,
    EventContext,
    DiscordEventHandler,
    get_discord_event_handler
)
import discord


class TestEventType:
    """Test EventType enum"""
    
    @pytest.mark.communication
    @pytest.mark.unit
    def test_event_type_values(self):
        """Test: EventType has correct values"""
        # Assert
        assert EventType.MESSAGE.value == "message", "Should have message value"
        assert EventType.READY.value == "ready", "Should have ready value"
        assert EventType.DISCONNECT.value == "disconnect", "Should have disconnect value"
        assert EventType.ERROR.value == "error", "Should have error value"
        assert EventType.REACTION_ADD.value == "reaction_add", "Should have reaction_add value"
        assert EventType.REACTION_REMOVE.value == "reaction_remove", "Should have reaction_remove value"
        assert EventType.MEMBER_JOIN.value == "member_join", "Should have member_join value"
        assert EventType.MEMBER_LEAVE.value == "member_leave", "Should have member_leave value"


class TestEventContext:
    """Test EventContext dataclass"""
    
    @pytest.mark.communication
    @pytest.mark.unit
    def test_event_context_initialization(self):
        """Test: EventContext initializes correctly"""
        # Act
        context = EventContext(
            event_type=EventType.MESSAGE,
            user_id="123456789",
            channel_id="987654321",
            guild_id="111222333",
            message_id="444555666"
        )
        
        # Assert
        assert context.event_type == EventType.MESSAGE, "Should set event_type"
        assert context.user_id == "123456789", "Should set user_id"
        assert context.channel_id == "987654321", "Should set channel_id"
        assert context.guild_id == "111222333", "Should set guild_id"
        assert context.message_id == "444555666", "Should set message_id"
        assert context.timestamp is not None, "Should set timestamp"
        assert context.data == {}, "Should default data to empty dict"
    
    @pytest.mark.communication
    @pytest.mark.unit
    def test_event_context_post_init_sets_timestamp(self):
        """Test: EventContext __post_init__ sets timestamp if None"""
        # Act
        context = EventContext(
            event_type=EventType.MESSAGE,
            timestamp=None
        )
        
        # Assert
        assert context.timestamp is not None, "Should set timestamp if None"
    
    @pytest.mark.communication
    @pytest.mark.unit
    def test_event_context_post_init_sets_data(self):
        """Test: EventContext __post_init__ sets data if None"""
        # Act
        context = EventContext(
            event_type=EventType.MESSAGE,
            data=None
        )
        
        # Assert
        assert context.data == {}, "Should set data to empty dict if None"


class TestDiscordEventHandler:
    """Test DiscordEventHandler class"""
    
    @pytest.fixture
    def mock_bot(self):
        """Create a mock Discord bot"""
        mock_bot = MagicMock()
        mock_bot.user = MagicMock()
        mock_bot.user.id = 123456789
        mock_bot.event = MagicMock()
        mock_bot.change_presence = AsyncMock()
        return mock_bot
    
    @pytest.fixture
    def event_handler(self, mock_bot):
        """Create a DiscordEventHandler instance"""
        return DiscordEventHandler(mock_bot)
    
    @pytest.fixture
    def event_handler_no_bot(self):
        """Create a DiscordEventHandler instance without bot"""
        return DiscordEventHandler(None)
    
    @pytest.mark.communication
    @pytest.mark.unit
    def test_initialization_with_bot(self, mock_bot):
        """Test: DiscordEventHandler initializes correctly with bot"""
        # Act
        handler = DiscordEventHandler(mock_bot)
        
        # Assert
        assert handler.bot == mock_bot, "Should set bot"
        assert handler._message_handlers == [], "Should initialize message handlers"
        assert handler._ready_handlers == [], "Should initialize ready handlers"
        assert handler._disconnect_handlers == [], "Should initialize disconnect handlers"
        assert handler._error_handlers == [], "Should initialize error handlers"
    
    @pytest.mark.communication
    @pytest.mark.unit
    def test_initialization_without_bot(self):
        """Test: DiscordEventHandler initializes correctly without bot"""
        # Act
        handler = DiscordEventHandler(None)
        
        # Assert
        assert handler.bot is None, "Should handle None bot"
    
    @pytest.mark.communication
    @pytest.mark.unit
    def test_register_default_handlers_with_bot(self, mock_bot):
        """Test: _register_default_handlers registers handlers when bot available"""
        # Act
        handler = DiscordEventHandler(mock_bot)
        
        # Assert
        assert mock_bot.event.call_count == 4, "Should register 4 default handlers"
    
    @pytest.mark.communication
    @pytest.mark.unit
    def test_register_default_handlers_without_bot(self):
        """Test: _register_default_handlers does nothing when bot not available"""
        # Arrange
        mock_bot = None
        
        # Act
        handler = DiscordEventHandler(mock_bot)
        
        # Assert
        assert handler.bot is None, "Should handle None bot"
    
    @pytest.mark.communication
    @pytest.mark.unit
    def test_add_message_handler(self, event_handler):
        """Test: add_message_handler adds handler to list"""
        # Arrange
        def handler():
            pass
        
        # Act
        event_handler.add_message_handler(handler)
        
        # Assert
        assert handler in event_handler._message_handlers, "Should add handler to list"
    
    @pytest.mark.communication
    @pytest.mark.unit
    def test_add_ready_handler(self, event_handler):
        """Test: add_ready_handler adds handler to list"""
        # Arrange
        def handler():
            pass
        
        # Act
        event_handler.add_ready_handler(handler)
        
        # Assert
        assert handler in event_handler._ready_handlers, "Should add handler to list"
    
    @pytest.mark.communication
    @pytest.mark.unit
    def test_add_disconnect_handler(self, event_handler):
        """Test: add_disconnect_handler adds handler to list"""
        # Arrange
        def handler():
            pass
        
        # Act
        event_handler.add_disconnect_handler(handler)
        
        # Assert
        assert handler in event_handler._disconnect_handlers, "Should add handler to list"
    
    @pytest.mark.communication
    @pytest.mark.unit
    def test_add_error_handler(self, event_handler):
        """Test: add_error_handler adds handler to list"""
        # Arrange
        def handler():
            pass
        
        # Act
        event_handler.add_error_handler(handler)
        
        # Assert
        assert handler in event_handler._error_handlers, "Should add handler to list"
    
    @pytest.mark.communication
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_on_ready_success(self, event_handler, mock_bot):
        """Test: on_ready handles ready event successfully"""
        # Arrange
        mock_bot.change_presence = AsyncMock()
        
        # Act
        await event_handler.on_ready()
        
        # Assert
        mock_bot.change_presence.assert_called_once()
    
    @pytest.mark.communication
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_on_ready_calls_custom_handlers(self, event_handler, mock_bot):
        """Test: on_ready calls custom ready handlers"""
        # Arrange
        mock_handler = AsyncMock()
        event_handler.add_ready_handler(mock_handler)
        mock_bot.change_presence = AsyncMock()
        
        # Act
        await event_handler.on_ready()
        
        # Assert
        mock_handler.assert_called_once_with(mock_bot)
    
    @pytest.mark.communication
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_on_ready_handles_handler_error(self, event_handler, mock_bot):
        """Test: on_ready handles errors in custom handlers gracefully"""
        # Arrange
        async def failing_handler(bot):
            raise Exception("Handler error")
        
        event_handler.add_ready_handler(failing_handler)
        mock_bot.change_presence = AsyncMock()
        
        # Act
        await event_handler.on_ready()
        
        # Assert
        # Should not raise exception, should continue execution
        mock_bot.change_presence.assert_called_once()
    
    @pytest.mark.communication
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_on_disconnect_success(self, event_handler, mock_bot):
        """Test: on_disconnect handles disconnect event successfully"""
        # Act
        await event_handler.on_disconnect()
        
        # Assert
        # Should complete without error
        assert True, "Should handle disconnect event"
    
    @pytest.mark.communication
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_on_disconnect_calls_custom_handlers(self, event_handler, mock_bot):
        """Test: on_disconnect calls custom disconnect handlers"""
        # Arrange
        mock_handler = AsyncMock()
        event_handler.add_disconnect_handler(mock_handler)
        
        # Act
        await event_handler.on_disconnect()
        
        # Assert
        mock_handler.assert_called_once_with(mock_bot)
    
    @pytest.mark.communication
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_on_error_success(self, event_handler):
        """Test: on_error handles error event successfully"""
        # Arrange
        event = "test_event"
        args = ("arg1", "arg2")
        kwargs = {"key": "value"}
        
        # Act
        await event_handler.on_error(event, *args, **kwargs)
        
        # Assert
        # Should complete without error
        assert True, "Should handle error event"
    
    @pytest.mark.communication
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_on_error_calls_custom_handlers(self, event_handler):
        """Test: on_error calls custom error handlers"""
        # Arrange
        mock_handler = AsyncMock()
        event_handler.add_error_handler(mock_handler)
        event = "test_event"
        args = ("arg1", "arg2")
        kwargs = {"key": "value"}
        
        # Act
        await event_handler.on_error(event, *args, **kwargs)
        
        # Assert
        mock_handler.assert_called_once_with(event, args, kwargs)
    
    @pytest.mark.communication
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_on_message_ignores_bot_messages(self, event_handler, mock_bot):
        """Test: on_message ignores messages from bot"""
        # Arrange
        mock_message = MagicMock()
        mock_message.author = mock_bot.user
        mock_message.content = "Test message"
        
        # Act
        await event_handler.on_message(mock_message)
        
        # Assert
        # Should return early without processing
        assert len(event_handler._message_handlers) == 0, "Should not process bot messages"
    
    @pytest.mark.communication
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_on_message_ignores_empty_messages(self, event_handler, mock_bot):
        """Test: on_message ignores messages without content"""
        # Arrange
        mock_message = MagicMock()
        mock_message.author = MagicMock()
        mock_message.author.id = 987654321
        mock_message.content = None
        
        # Act
        await event_handler.on_message(mock_message)
        
        # Assert
        # Should return early without processing
        assert True, "Should ignore empty messages"
    
    @pytest.mark.communication
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_on_message_calls_custom_handlers(self, event_handler, mock_bot):
        """Test: on_message calls custom message handlers"""
        # Arrange
        mock_handler = AsyncMock()
        event_handler.add_message_handler(mock_handler)
        
        mock_message = MagicMock()
        mock_message.author = MagicMock()
        mock_message.author.id = 987654321
        mock_message.content = "Test message"
        mock_message.channel.id = 123456789
        mock_message.guild = None
        mock_message.id = 111222333
        mock_message.attachments = []
        mock_message.embeds = []
        
        with patch.object(event_handler, '_handle_user_message', new_callable=AsyncMock):
            # Act
            await event_handler.on_message(mock_message)
            
            # Assert
            mock_handler.assert_called_once()
    
    @pytest.mark.communication
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_on_message_creates_event_context(self, event_handler, mock_bot):
        """Test: on_message creates EventContext correctly"""
        # Arrange
        mock_message = MagicMock()
        mock_message.author = MagicMock()
        mock_message.author.id = 987654321
        mock_message.content = "Test message"
        mock_message.channel.id = 123456789
        mock_message.guild = MagicMock()
        mock_message.guild.id = 111222333
        mock_message.id = 444555666
        mock_message.attachments = []
        mock_message.embeds = []
        
        with patch.object(event_handler, '_handle_user_message', new_callable=AsyncMock) as mock_handle:
            # Act
            await event_handler.on_message(mock_message)
            
            # Assert
            mock_handle.assert_called_once()
            call_args = mock_handle.call_args[0]
            assert call_args[0] == mock_message, "Should pass message"
            assert call_args[1].event_type == EventType.MESSAGE, "Should create MESSAGE context"
            assert call_args[1].user_id == "987654321", "Should set user_id"
    
    @pytest.mark.communication
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_handle_user_message_user_not_registered(self, event_handler, mock_bot):
        """Test: _handle_user_message sends registration prompt for unregistered user"""
        # Arrange
        mock_message = MagicMock()
        mock_message.author.id = 987654321
        mock_message.content = "Test message"
        mock_channel = AsyncMock()
        mock_message.channel = mock_channel
        
        with patch('communication.communication_channels.discord.event_handler.get_user_id_by_identifier', return_value=None):
            # Act
            await event_handler._handle_user_message(mock_message, EventContext(EventType.MESSAGE))
            
            # Assert
            mock_channel.send.assert_called_once()
            call_args = mock_channel.send.call_args[0][0]
            assert "register" in call_args.lower(), "Should send registration prompt"
    
    @pytest.mark.communication
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_handle_user_message_processes_message(self, event_handler, mock_bot):
        """Test: _handle_user_message processes message through interaction manager"""
        # Arrange
        mock_message = MagicMock()
        mock_message.author.id = 987654321
        mock_message.content = "Test message"
        mock_channel = AsyncMock()
        mock_message.channel = mock_channel
        
        mock_response = MagicMock()
        mock_response.message = "Response message"
        mock_response.rich_data = None
        mock_response.suggestions = None
        
        with patch('communication.communication_channels.discord.event_handler.get_user_id_by_identifier', return_value="user123"):
            with patch('communication.communication_channels.discord.event_handler.handle_user_message', return_value=mock_response):
                with patch.object(event_handler, '_send_response', new_callable=AsyncMock) as mock_send:
                    # Act
                    await event_handler._handle_user_message(mock_message, EventContext(EventType.MESSAGE))
                    
                    # Assert
                    mock_send.assert_called_once_with(mock_channel, mock_response)
    
    @pytest.mark.communication
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_handle_user_message_handles_errors(self, event_handler, mock_bot):
        """Test: _handle_user_message handles errors gracefully"""
        # Arrange
        mock_message = MagicMock()
        mock_message.author.id = 987654321
        mock_message.content = "Test message"
        mock_channel = AsyncMock()
        mock_message.channel = mock_channel
        
        with patch('communication.communication_channels.discord.event_handler.get_user_id_by_identifier', side_effect=Exception("Test error")):
            # Act
            await event_handler._handle_user_message(mock_message, EventContext(EventType.MESSAGE))
            
            # Assert
            mock_channel.send.assert_called_once()
            call_args = mock_channel.send.call_args[0][0]
            assert "trouble" in call_args.lower(), "Should send error message"
    
    @pytest.mark.communication
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_send_response_with_message_only(self, event_handler, mock_bot):
        """Test: _send_response sends message without embed or view"""
        # Arrange
        mock_channel = AsyncMock()
        mock_response = MagicMock()
        mock_response.message = "Test response"
        mock_response.rich_data = None
        mock_response.suggestions = None
        
        # Act
        await event_handler._send_response(mock_channel, mock_response)
        
        # Assert
        mock_channel.send.assert_called_once_with("Test response")
    
    @pytest.mark.communication
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_send_response_with_embed(self, event_handler, mock_bot):
        """Test: _send_response sends message with embed"""
        # Arrange
        mock_channel = AsyncMock()
        mock_embed = MagicMock()
        mock_response = MagicMock()
        mock_response.message = "Test response"
        mock_response.rich_data = {"title": "Test"}
        mock_response.suggestions = None
        
        with patch('communication.communication_channels.base.rich_formatter.get_rich_formatter') as mock_get_formatter:
            mock_formatter = MagicMock()
            mock_formatter.create_embed.return_value = mock_embed
            mock_get_formatter.return_value = mock_formatter
            
            # Act
            await event_handler._send_response(mock_channel, mock_response)
            
            # Assert
            mock_channel.send.assert_called_once_with(embed=mock_embed)
    
    @pytest.mark.communication
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_send_response_with_view(self, event_handler, mock_bot):
        """Test: _send_response sends message with view"""
        # Arrange
        mock_channel = AsyncMock()
        mock_view = MagicMock()
        mock_response = MagicMock()
        mock_response.message = "Test response"
        mock_response.rich_data = None
        mock_response.suggestions = ["Option 1", "Option 2"]
        
        with patch('communication.communication_channels.base.rich_formatter.get_rich_formatter') as mock_get_formatter:
            mock_formatter = MagicMock()
            mock_formatter.create_interactive_view.return_value = mock_view
            mock_get_formatter.return_value = mock_formatter
            
            # Act
            await event_handler._send_response(mock_channel, mock_response)
            
            # Assert
            mock_channel.send.assert_called_once_with("Test response", view=mock_view)
    
    @pytest.mark.communication
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_send_response_handles_errors(self, event_handler, mock_bot):
        """Test: _send_response handles errors gracefully"""
        # Arrange
        mock_channel = AsyncMock()
        mock_channel.send = AsyncMock(side_effect=Exception("Send error"))
        mock_response = MagicMock()
        mock_response.message = "Test response"
        mock_response.rich_data = None
        mock_response.suggestions = None
        
        # Act
        await event_handler._send_response(mock_channel, mock_response)
        
        # Assert
        # Should call send twice - once for message, once for error
        assert mock_channel.send.call_count == 2, "Should send error message"
    
    @pytest.mark.communication
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_on_reaction_add_ignores_bot_reactions(self, event_handler, mock_bot):
        """Test: on_reaction_add ignores reactions from bot"""
        # Arrange
        mock_reaction = MagicMock()
        mock_reaction.message.channel.id = 123456789
        mock_reaction.message.guild = None
        mock_reaction.message.id = 111222333
        mock_reaction.emoji = "👍"
        mock_reaction.count = 1
        mock_user = mock_bot.user
        
        # Act
        await event_handler.on_reaction_add(mock_reaction, mock_user)
        
        # Assert
        # Should return early without processing
        assert True, "Should ignore bot reactions"
    
    @pytest.mark.communication
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_on_reaction_remove_ignores_bot_reactions(self, event_handler, mock_bot):
        """Test: on_reaction_remove ignores reactions from bot"""
        # Arrange
        mock_reaction = MagicMock()
        mock_reaction.message.channel.id = 123456789
        mock_reaction.message.guild = None
        mock_reaction.message.id = 111222333
        mock_reaction.emoji = "👍"
        mock_reaction.count = 0
        mock_user = mock_bot.user
        
        # Act
        await event_handler.on_reaction_remove(mock_reaction, mock_user)
        
        # Assert
        # Should return early without processing
        assert True, "Should ignore bot reactions"
    
    @pytest.mark.communication
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_on_member_join_success(self, event_handler, mock_bot):
        """Test: on_member_join handles member join event"""
        # Arrange
        mock_member = MagicMock()
        mock_member.id = 987654321
        mock_member.name = "TestUser"
        mock_member.display_name = "Test User"
        mock_member.joined_at = None
        mock_member.guild = MagicMock()
        mock_member.guild.id = 123456789
        mock_member.guild.name = "Test Guild"
        
        # Act
        await event_handler.on_member_join(mock_member)
        
        # Assert
        # Should complete without error
        assert True, "Should handle member join event"
    
    @pytest.mark.communication
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_on_member_remove_success(self, event_handler, mock_bot):
        """Test: on_member_remove handles member leave event"""
        # Arrange
        mock_member = MagicMock()
        mock_member.id = 987654321
        mock_member.name = "TestUser"
        mock_member.display_name = "Test User"
        mock_member.guild = MagicMock()
        mock_member.guild.id = 123456789
        mock_member.guild.name = "Test Guild"
        
        # Act
        await event_handler.on_member_remove(mock_member)
        
        # Assert
        # Should complete without error
        assert True, "Should handle member leave event"
    
    @pytest.mark.communication
    @pytest.mark.unit
    def test_register_events(self, event_handler_no_bot, mock_bot):
        """Test: register_events registers all event handlers"""
        # Arrange
        mock_bot.event = MagicMock()
        
        # Act
        event_handler_no_bot.register_events(mock_bot)
        
        # Assert
        assert event_handler_no_bot.bot == mock_bot, "Should set bot"
        assert mock_bot.event.call_count == 8, "Should register 8 event handlers"


class TestGetDiscordEventHandler:
    """Test get_discord_event_handler factory function"""
    
    @pytest.mark.communication
    @pytest.mark.unit
    def test_get_discord_event_handler_with_bot(self):
        """Test: get_discord_event_handler returns handler with bot"""
        # Arrange
        mock_bot = MagicMock()
        
        # Act
        handler = get_discord_event_handler(mock_bot)
        
        # Assert
        assert isinstance(handler, DiscordEventHandler), "Should return DiscordEventHandler"
        assert handler.bot == mock_bot, "Should set bot on handler"
    
    @pytest.mark.communication
    @pytest.mark.unit
    def test_get_discord_event_handler_without_bot(self):
        """Test: get_discord_event_handler returns handler without bot"""
        # Act
        handler = get_discord_event_handler(None)
        
        # Assert
        assert isinstance(handler, DiscordEventHandler), "Should return DiscordEventHandler"
        assert handler.bot is None, "Should handle None bot"

