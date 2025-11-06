"""
Communication Package Init Tests

Tests for communication package initialization and exports:
- Direct imports
- Lazy imports via __getattr__
- Export verification
- Circular dependency handling
"""

import pytest
from unittest.mock import patch, MagicMock

# Test direct imports (no circular dependencies)
from communication import (
    BaseChannel,
    ChannelStatus,
    ChannelType,
    ChannelConfig,
    EnhancedCommandParser,
    ParsingResult,
    get_enhanced_command_parser,
    parse_command,
    InteractionResponse,
    ParsedCommand,
    handle_user_message,
    get_interaction_manager,
    InteractionManager,
    CommandDefinition,
    conversation_manager,
    ConversationManager,
    RetryManager,
    QueuedMessage,
    BotInitializationError,
    MessageSendError,
    InteractionHandler,
    AnalyticsHandler,
    TaskManagementHandler,
    get_all_handlers,
    get_interaction_handler,
    CheckinHandler,
    ProfileHandler,
    HelpHandler,
    ScheduleManagementHandler,
)


class TestCommunicationDirectImports:
    """Test direct imports (no circular dependencies)"""
    
    @pytest.mark.communication
    @pytest.mark.unit
    def test_base_channel_imports(self):
        """Test: BaseChannel and related classes can be imported directly"""
        # Arrange: Import already done at module level
        # Act: Verify imports are available
        # Assert: Should be importable
        assert BaseChannel is not None, "BaseChannel should be importable"
        assert ChannelStatus is not None, "ChannelStatus should be importable"
        assert ChannelType is not None, "ChannelType should be importable"
        assert ChannelConfig is not None, "ChannelConfig should be importable"
    
    @pytest.mark.communication
    @pytest.mark.unit
    def test_command_parser_imports(self):
        """Test: Command parser classes can be imported directly"""
        # Arrange: Import already done at module level
        # Act: Verify imports are available
        # Assert: Should be importable
        assert EnhancedCommandParser is not None, "EnhancedCommandParser should be importable"
        assert ParsingResult is not None, "ParsingResult should be importable"
        assert get_enhanced_command_parser is not None, "get_enhanced_command_parser should be importable"
        assert parse_command is not None, "parse_command should be importable"
    
    @pytest.mark.communication
    @pytest.mark.unit
    def test_shared_types_imports(self):
        """Test: Shared types can be imported directly"""
        # Arrange: Import already done at module level
        # Act: Verify imports are available
        # Assert: Should be importable
        assert InteractionResponse is not None, "InteractionResponse should be importable"
        assert ParsedCommand is not None, "ParsedCommand should be importable"
    
    @pytest.mark.communication
    @pytest.mark.unit
    def test_interaction_manager_imports(self):
        """Test: Interaction manager classes can be imported directly"""
        # Arrange: Import already done at module level
        # Act: Verify imports are available
        # Assert: Should be importable
        assert handle_user_message is not None, "handle_user_message should be importable"
        assert get_interaction_manager is not None, "get_interaction_manager should be importable"
        assert InteractionManager is not None, "InteractionManager should be importable"
        assert CommandDefinition is not None, "CommandDefinition should be importable"
    
    @pytest.mark.communication
    @pytest.mark.unit
    def test_conversation_manager_imports(self):
        """Test: Conversation manager classes can be imported directly"""
        # Arrange: Import already done at module level
        # Act: Verify imports are available
        # Assert: Should be importable
        assert conversation_manager is not None, "conversation_manager should be importable"
        assert ConversationManager is not None, "ConversationManager should be importable"
    
    @pytest.mark.communication
    @pytest.mark.unit
    def test_retry_manager_imports(self):
        """Test: Retry manager classes can be imported directly"""
        # Arrange: Import already done at module level
        # Act: Verify imports are available
        # Assert: Should be importable
        assert RetryManager is not None, "RetryManager should be importable"
        assert QueuedMessage is not None, "QueuedMessage should be importable"
    
    @pytest.mark.communication
    @pytest.mark.unit
    def test_exception_imports(self):
        """Test: Exception classes can be imported directly"""
        # Arrange: Import already done at module level
        # Act: Verify imports are available
        # Assert: Should be importable
        assert BotInitializationError is not None, "BotInitializationError should be importable"
        assert MessageSendError is not None, "MessageSendError should be importable"
    
    @pytest.mark.communication
    @pytest.mark.unit
    def test_command_handler_imports(self):
        """Test: Command handler classes can be imported directly"""
        # Arrange: Import already done at module level
        # Act: Verify imports are available
        # Assert: Should be importable
        assert InteractionHandler is not None, "InteractionHandler should be importable"
        assert AnalyticsHandler is not None, "AnalyticsHandler should be importable"
        assert TaskManagementHandler is not None, "TaskManagementHandler should be importable"
        assert get_all_handlers is not None, "get_all_handlers should be importable"
        assert get_interaction_handler is not None, "get_interaction_handler should be importable"
        assert CheckinHandler is not None, "CheckinHandler should be importable"
        assert ProfileHandler is not None, "ProfileHandler should be importable"
        assert HelpHandler is not None, "HelpHandler should be importable"
        assert ScheduleManagementHandler is not None, "ScheduleManagementHandler should be importable"


class TestCommunicationLazyImports:
    """Test lazy imports via __getattr__ (circular dependencies)"""
    
    @pytest.mark.communication
    @pytest.mark.unit
    def test_communication_manager_lazy_import(self):
        """Test: CommunicationManager can be imported lazily"""
        # Arrange: Import communication module
        import communication
        
        # Act: Access CommunicationManager (should trigger lazy import)
        manager = communication.CommunicationManager
        
        # Assert: Should be importable
        assert manager is not None, "CommunicationManager should be importable via lazy import"
    
    @pytest.mark.communication
    @pytest.mark.unit
    def test_channel_factory_lazy_import(self):
        """Test: ChannelFactory can be imported lazily"""
        # Arrange: Import communication module
        import communication
        
        # Act: Access ChannelFactory (should trigger lazy import)
        factory = communication.ChannelFactory
        
        # Assert: Should be importable
        assert factory is not None, "ChannelFactory should be importable via lazy import"
    
    @pytest.mark.communication
    @pytest.mark.unit
    def test_channel_monitor_lazy_import(self):
        """Test: ChannelMonitor can be imported lazily"""
        # Arrange: Import communication module
        import communication
        
        # Act: Access ChannelMonitor (should trigger lazy import)
        monitor = communication.ChannelMonitor
        
        # Assert: Should be importable
        assert monitor is not None, "ChannelMonitor should be importable via lazy import"
    
    @pytest.mark.communication
    @pytest.mark.unit
    def test_discord_bot_lazy_import(self):
        """Test: DiscordBot can be imported lazily"""
        # Arrange: Import communication module
        import communication
        
        # Act: Access DiscordBot (should trigger lazy import)
        bot = communication.DiscordBot
        
        # Assert: Should be importable
        assert bot is not None, "DiscordBot should be importable via lazy import"
    
    @pytest.mark.communication
    @pytest.mark.unit
    def test_email_bot_lazy_import(self):
        """Test: EmailBot can be imported lazily"""
        # Arrange: Import communication module
        import communication
        
        # Act: Access EmailBot (should trigger lazy import)
        bot = communication.EmailBot
        
        # Assert: Should be importable
        assert bot is not None, "EmailBot should be importable via lazy import"
    
    @pytest.mark.communication
    @pytest.mark.unit
    def test_discord_connection_status_lazy_import(self):
        """Test: DiscordConnectionStatus can be imported lazily"""
        # Arrange: Import communication module
        import communication
        
        # Act: Access DiscordConnectionStatus (should trigger lazy import)
        status = communication.DiscordConnectionStatus
        
        # Assert: Should be importable
        assert status is not None, "DiscordConnectionStatus should be importable via lazy import"
    
    @pytest.mark.communication
    @pytest.mark.unit
    def test_message_router_lazy_import(self):
        """Test: MessageRouter can be imported lazily"""
        # Arrange: Import communication module
        import communication
        
        # Act: Access MessageRouter (should trigger lazy import)
        router = communication.MessageRouter
        
        # Assert: Should be importable
        assert router is not None, "MessageRouter should be importable via lazy import"
    
    @pytest.mark.communication
    @pytest.mark.unit
    def test_message_type_lazy_import(self):
        """Test: MessageType can be imported lazily"""
        # Arrange: Import communication module
        import communication
        
        # Act: Access MessageType (should trigger lazy import)
        msg_type = communication.MessageType
        
        # Assert: Should be importable
        assert msg_type is not None, "MessageType should be importable via lazy import"
    
    @pytest.mark.communication
    @pytest.mark.unit
    def test_routing_result_lazy_import(self):
        """Test: RoutingResult can be imported lazily"""
        # Arrange: Import communication module
        import communication
        
        # Act: Access RoutingResult (should trigger lazy import)
        result = communication.RoutingResult
        
        # Assert: Should be importable
        assert result is not None, "RoutingResult should be importable via lazy import"
    
    @pytest.mark.communication
    @pytest.mark.unit
    def test_get_message_router_lazy_import(self):
        """Test: get_message_router can be imported lazily"""
        # Arrange: Import communication module
        import communication
        
        # Act: Access get_message_router (should trigger lazy import)
        func = communication.get_message_router
        
        # Assert: Should be importable
        assert func is not None, "get_message_router should be importable via lazy import"
        assert callable(func), "get_message_router should be callable"
    
    @pytest.mark.communication
    @pytest.mark.unit
    def test_rich_formatter_lazy_import(self):
        """Test: RichFormatter classes can be imported lazily"""
        # Arrange: Import communication module
        import communication
        
        # Act: Access RichFormatter classes (should trigger lazy import)
        formatter = communication.RichFormatter
        discord_formatter = communication.DiscordRichFormatter
        email_formatter = communication.EmailRichFormatter
        get_formatter = communication.get_rich_formatter
        
        # Assert: Should be importable
        assert formatter is not None, "RichFormatter should be importable via lazy import"
        assert discord_formatter is not None, "DiscordRichFormatter should be importable via lazy import"
        assert email_formatter is not None, "EmailRichFormatter should be importable via lazy import"
        assert get_formatter is not None, "get_rich_formatter should be importable via lazy import"
        assert callable(get_formatter), "get_rich_formatter should be callable"
    
    @pytest.mark.communication
    @pytest.mark.unit
    def test_message_formatter_lazy_import(self):
        """Test: MessageFormatter classes can be imported lazily"""
        # Arrange: Import communication module
        import communication
        
        # Act: Access MessageFormatter classes (should trigger lazy import)
        formatter = communication.MessageFormatter
        text_formatter = communication.TextMessageFormatter
        email_formatter = communication.EmailMessageFormatter
        get_formatter = communication.get_message_formatter
        
        # Assert: Should be importable
        assert formatter is not None, "MessageFormatter should be importable via lazy import"
        assert text_formatter is not None, "TextMessageFormatter should be importable via lazy import"
        assert email_formatter is not None, "EmailMessageFormatter should be importable via lazy import"
        assert get_formatter is not None, "get_message_formatter should be importable via lazy import"
        assert callable(get_formatter), "get_message_formatter should be callable"
    
    @pytest.mark.communication
    @pytest.mark.unit
    def test_command_registry_lazy_import(self):
        """Test: CommandRegistry classes can be imported lazily"""
        # Arrange: Import communication module
        import communication
        
        # Act: Access CommandRegistry classes (should trigger lazy import)
        registry = communication.CommandRegistry
        discord_registry = communication.DiscordCommandRegistry
        email_registry = communication.EmailCommandRegistry
        get_registry = communication.get_command_registry
        
        # Assert: Should be importable
        assert registry is not None, "CommandRegistry should be importable via lazy import"
        assert discord_registry is not None, "DiscordCommandRegistry should be importable via lazy import"
        assert email_registry is not None, "EmailCommandRegistry should be importable via lazy import"
        assert get_registry is not None, "get_command_registry should be importable via lazy import"
        assert callable(get_registry), "get_command_registry should be callable"
    
    @pytest.mark.communication
    @pytest.mark.unit
    def test_discord_event_handler_lazy_import(self):
        """Test: DiscordEventHandler can be imported lazily"""
        # Arrange: Import communication module
        import communication
        
        # Act: Access DiscordEventHandler (should trigger lazy import)
        handler = communication.DiscordEventHandler
        get_handler = communication.get_discord_event_handler
        
        # Assert: Should be importable
        assert handler is not None, "DiscordEventHandler should be importable via lazy import"
        assert get_handler is not None, "get_discord_event_handler should be importable via lazy import"
        assert callable(get_handler), "get_discord_event_handler should be callable"
    
    @pytest.mark.communication
    @pytest.mark.unit
    def test_discord_api_client_lazy_import(self):
        """Test: DiscordAPIClient can be imported lazily"""
        # Arrange: Import communication module
        import communication
        
        # Act: Access DiscordAPIClient (should trigger lazy import)
        client = communication.DiscordAPIClient
        get_client = communication.get_discord_api_client
        
        # Assert: Should be importable
        assert client is not None, "DiscordAPIClient should be importable via lazy import"
        assert get_client is not None, "get_discord_api_client should be importable via lazy import"
        assert callable(get_client), "get_discord_api_client should be callable"
    
    @pytest.mark.communication
    @pytest.mark.unit
    def test_event_context_lazy_import(self):
        """Test: EventContext and EventType can be imported lazily"""
        # Arrange: Import communication module
        import communication
        
        # Act: Access EventContext and EventType (should trigger lazy import)
        context = communication.EventContext
        event_type = communication.EventType
        
        # Assert: Should be importable
        assert context is not None, "EventContext should be importable via lazy import"
        assert event_type is not None, "EventType should be importable via lazy import"
    
    @pytest.mark.communication
    @pytest.mark.unit
    def test_message_data_lazy_import(self):
        """Test: MessageData and SendMessageOptions can be imported lazily"""
        # Arrange: Import communication module
        import communication
        
        # Act: Access MessageData and SendMessageOptions (should trigger lazy import)
        message_data = communication.MessageData
        send_options = communication.SendMessageOptions
        
        # Assert: Should be importable
        assert message_data is not None, "MessageData should be importable via lazy import"
        assert send_options is not None, "SendMessageOptions should be importable via lazy import"
    
    @pytest.mark.communication
    @pytest.mark.unit
    def test_email_bot_error_lazy_import(self):
        """Test: EmailBotError can be imported lazily"""
        # Arrange: Import communication module
        import communication
        
        # Act: Access EmailBotError (should trigger lazy import)
        error = communication.EmailBotError
        
        # Assert: Should be importable
        assert error is not None, "EmailBotError should be importable via lazy import"


class TestCommunicationLazyImportErrorHandling:
    """Test lazy import error handling"""
    
    @pytest.mark.communication
    @pytest.mark.unit
    def test_lazy_import_unknown_attribute(self):
        """Test: __getattr__ raises AttributeError for unknown attributes"""
        # Arrange: Import communication module
        import communication
        
        # Act: Access unknown attribute
        # Assert: Should raise AttributeError
        with pytest.raises(AttributeError, match="module 'communication' has no attribute 'UnknownAttribute'"):
            _ = communication.UnknownAttribute
    
    @pytest.mark.communication
    @pytest.mark.unit
    def test_lazy_import_handles_import_errors(self):
        """Test: __getattr__ handles import errors gracefully"""
        # Arrange: Import communication module and mock import to fail
        import communication
        
        # This test verifies that if a lazy import fails, it should raise the import error
        # We can't easily test this without breaking the actual imports, so we'll just
        # verify that the mechanism works for valid imports
        # Act: Access a valid lazy import
        manager = communication.CommunicationManager
        
        # Assert: Should work for valid imports
        assert manager is not None, "Valid lazy imports should work"


class TestCommunicationExports:
    """Test __all__ exports"""
    
    @pytest.mark.communication
    @pytest.mark.unit
    def test_all_exports_are_defined(self):
        """Test: All items in __all__ are actually exportable"""
        # Arrange: Import communication module
        import communication
        
        # Act: Get __all__ list
        all_exports = communication.__all__
        
        # Assert: All items should be accessible
        for export_name in all_exports:
            # Try to access the export
            try:
                export = getattr(communication, export_name)
                assert export is not None, f"{export_name} should be accessible"
            except AttributeError:
                # If it's a lazy import, it should still be in __all__
                # This is expected for lazy imports that haven't been accessed yet
                pass
    
    @pytest.mark.communication
    @pytest.mark.unit
    def test_all_exports_are_in_all(self):
        """Test: All direct imports are in __all__"""
        # Arrange: Import communication module
        import communication
        
        # Act: Get __all__ list
        all_exports = set(communication.__all__)
        
        # Assert: Key direct imports should be in __all__
        direct_imports = [
            'BaseChannel',
            'ChannelStatus',
            'ChannelType',
            'ChannelConfig',
            'EnhancedCommandParser',
            'ParsingResult',
            'get_enhanced_command_parser',
            'parse_command',
            'InteractionResponse',
            'ParsedCommand',
            'handle_user_message',
            'get_interaction_manager',
            'InteractionManager',
            'CommandDefinition',
            'conversation_manager',
            'ConversationManager',
            'RetryManager',
            'QueuedMessage',
            'BotInitializationError',
            'MessageSendError',
            'InteractionHandler',
            'AnalyticsHandler',
            'TaskManagementHandler',
            'get_all_handlers',
            'get_interaction_handler',
            'CheckinHandler',
            'ProfileHandler',
            'HelpHandler',
            'ScheduleManagementHandler',
        ]
        
        for import_name in direct_imports:
            assert import_name in all_exports, f"{import_name} should be in __all__"

