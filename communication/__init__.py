"""Communication package for the MHM application.

Contains messaging channels, orchestration logic, command handlers,
and message processing utilities for multi-channel communication support.
"""

# Main public API - package-level exports for easier refactoring
# Note: Some exports use lazy imports to avoid circular dependencies

# Channel base classes (no circular dependencies)
from .communication_channels.base.base_channel import (
    BaseChannel,
    ChannelStatus,
    ChannelType,
    ChannelConfig,
)

# Message processing (no circular dependencies)
from .message_processing.command_parser import EnhancedCommandParser, ParsingResult, get_enhanced_command_parser, parse_command

# Shared types (high usage)
from .command_handlers.shared_types import InteractionResponse, ParsedCommand

# Message processing - interaction manager (high usage)
from .message_processing.interaction_manager import handle_user_message, get_interaction_manager, InteractionManager, CommandDefinition

# Conversation flow manager (high usage)
from .message_processing.conversation_flow_manager import conversation_manager, ConversationManager

# Core orchestration (high usage)
# Note: CommunicationManager has circular dependencies, using lazy import
# Core factory (medium usage)
# Note: ChannelFactory has circular dependencies, using lazy import
# Core retry manager (low usage)
from .core.retry_manager import RetryManager, QueuedMessage
# Core exceptions (low usage)
from .core.channel_orchestrator import BotInitializationError, MessageSendError
# Core channel monitor (low usage, lazy import due to circular dependencies)
# ERROR_HANDLING_EXCLUDE: Special Python method for dynamic attribute access
def __getattr__(name: str):
    """Lazy import handler for items with circular dependencies.
    
    Note: This function intentionally does not use @handle_errors decorator
    to avoid circular dependencies with error handling infrastructure.
    """
    if name == 'CommunicationManager':
        from .core.channel_orchestrator import CommunicationManager
        return CommunicationManager
    elif name == 'ChannelFactory':
        from .core.factory import ChannelFactory
        return ChannelFactory
    elif name == 'ChannelMonitor':
        from .core.channel_monitor import ChannelMonitor
        return ChannelMonitor
    elif name == 'DiscordBot':
        from .communication_channels.discord.bot import DiscordBot
        return DiscordBot
    elif name == 'EmailBot':
        from .communication_channels.email.bot import EmailBot
        return EmailBot
    elif name == 'DiscordConnectionStatus':
        from .communication_channels.discord.bot import DiscordConnectionStatus
        return DiscordConnectionStatus
    elif name == 'DiscordEventHandler':
        from .communication_channels.discord.event_handler import DiscordEventHandler
        return DiscordEventHandler
    elif name == 'DiscordAPIClient':
        from .communication_channels.discord.api_client import DiscordAPIClient
        return DiscordAPIClient
    elif name == 'EmailBotError':
        from .communication_channels.email.bot import EmailBotError
        return EmailBotError
    elif name == 'MessageRouter':
        from .message_processing.message_router import MessageRouter
        return MessageRouter
    elif name == 'MessageType':
        from .message_processing.message_router import MessageType
        return MessageType
    elif name == 'RoutingResult':
        from .message_processing.message_router import RoutingResult
        return RoutingResult
    elif name == 'get_message_router':
        from .message_processing.message_router import get_message_router
        return get_message_router
    elif name == 'get_discord_event_handler':
        from .communication_channels.discord.event_handler import get_discord_event_handler
        return get_discord_event_handler
    elif name == 'get_rich_formatter':
        from .communication_channels.base.rich_formatter import get_rich_formatter
        return get_rich_formatter
    elif name == 'get_discord_api_client':
        from .communication_channels.discord.api_client import get_discord_api_client
        return get_discord_api_client
    elif name == 'get_command_registry':
        from .communication_channels.base.command_registry import get_command_registry
        return get_command_registry
    elif name == 'get_message_formatter':
        from .communication_channels.base.message_formatter import get_message_formatter
        return get_message_formatter
    elif name == 'RichFormatter':
        from .communication_channels.base.rich_formatter import RichFormatter
        return RichFormatter
    elif name == 'DiscordRichFormatter':
        from .communication_channels.base.rich_formatter import DiscordRichFormatter
        return DiscordRichFormatter
    elif name == 'EmailRichFormatter':
        from .communication_channels.base.rich_formatter import EmailRichFormatter
        return EmailRichFormatter
    elif name == 'MessageFormatter':
        from .communication_channels.base.message_formatter import MessageFormatter
        return MessageFormatter
    elif name == 'TextMessageFormatter':
        from .communication_channels.base.message_formatter import TextMessageFormatter
        return TextMessageFormatter
    elif name == 'EmailMessageFormatter':
        from .communication_channels.base.message_formatter import EmailMessageFormatter
        return EmailMessageFormatter
    elif name == 'CommandRegistry':
        from .communication_channels.base.command_registry import CommandRegistry
        return CommandRegistry
    elif name == 'DiscordCommandRegistry':
        from .communication_channels.base.command_registry import DiscordCommandRegistry
        return DiscordCommandRegistry
    elif name == 'EmailCommandRegistry':
        from .communication_channels.base.command_registry import EmailCommandRegistry
        return EmailCommandRegistry
    elif name == 'EventContext':
        from .communication_channels.discord.event_handler import EventContext
        return EventContext
    elif name == 'EventType':
        from .communication_channels.discord.event_handler import EventType
        return EventType
    elif name == 'MessageData':
        from .communication_channels.discord.api_client import MessageData
        return MessageData
    elif name == 'SendMessageOptions':
        from .communication_channels.discord.api_client import SendMessageOptions
        return SendMessageOptions
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

# Command handlers - base handler (medium usage)
from .command_handlers.base_handler import InteractionHandler

# Command handlers - analytics handler (medium usage)
from .command_handlers.analytics_handler import AnalyticsHandler

# Command handlers - interaction handlers (medium usage)
from .command_handlers.interaction_handlers import (
    TaskManagementHandler,
    get_all_handlers,
    get_interaction_handler,
    CheckinHandler,
    ProfileHandler,
    HelpHandler,
    ScheduleManagementHandler,
)

# Discord channel - lazy import to avoid circular dependencies
# Use: from communication import DiscordBot (imported on-demand)
# Note: DiscordBot has circular dependencies, so it's imported lazily

__all__ = [
    # Channel base classes
    'BaseChannel',
    'ChannelStatus',
    'ChannelType',
    'ChannelConfig',
    # Message processing
    'EnhancedCommandParser',
    'ParsingResult',
    'get_enhanced_command_parser',
    'parse_command',
    # Shared types (high usage)
    'InteractionResponse',
    'ParsedCommand',
    # Message processing - interaction manager (high usage)
    'handle_user_message',
    'get_interaction_manager',
    'InteractionManager',
    'CommandDefinition',
    # Conversation flow manager (high usage)
    'conversation_manager',
    'ConversationManager',
    # Message router (low usage, lazy import)
    'MessageRouter',
    'MessageType',
    'RoutingResult',
    'get_message_router',
    # Core orchestration (high usage, lazy import)
    'CommunicationManager',
    # Core factory (medium usage, lazy import)
    'ChannelFactory',
    # Core retry manager (low usage)
    'RetryManager',
    'QueuedMessage',
    # Core exceptions (low usage)
    'BotInitializationError',
    'MessageSendError',
    # Core channel monitor (low usage, lazy import)
    'ChannelMonitor',
    # Command handlers - base handler (medium usage)
    'InteractionHandler',
    # Command handlers - analytics handler (medium usage)
    'AnalyticsHandler',
    # Command handlers - interaction handlers (medium usage)
    'TaskManagementHandler',
    'get_all_handlers',
    'get_interaction_handler',
    # Command handlers - low usage
    'CheckinHandler',
    'ProfileHandler',
    'HelpHandler',
    'ScheduleManagementHandler',
    # Discord channel (low usage, lazy import)
    'DiscordBot',
    'DiscordConnectionStatus',
    'DiscordEventHandler',
    'DiscordAPIClient',
    'get_discord_event_handler',
    'get_discord_api_client',
    'EventContext',
    'EventType',
    'MessageData',
    'SendMessageOptions',
    # Email channel (low usage, lazy import)
    'EmailBot',
    'EmailBotError',
    # Formatters (low usage, lazy import)
    'RichFormatter',
    'DiscordRichFormatter',
    'EmailRichFormatter',
    'get_rich_formatter',
    # Message formatters (low usage, lazy import)
    'MessageFormatter',
    'TextMessageFormatter',
    'EmailMessageFormatter',
    'get_message_formatter',
    # Command registries (low usage, lazy import)
    'CommandRegistry',
    'DiscordCommandRegistry',
    'EmailCommandRegistry',
    'get_command_registry',
]
