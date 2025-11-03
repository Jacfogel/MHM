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
from .message_processing.command_parser import EnhancedCommandParser, ParsingResult

# Shared types (high usage)
from .command_handlers.shared_types import InteractionResponse, ParsedCommand

# Message processing - interaction manager (high usage)
from .message_processing.interaction_manager import handle_user_message

# Conversation flow manager (high usage)
from .message_processing.conversation_flow_manager import conversation_manager

# Core orchestration (high usage)
# Note: CommunicationManager has circular dependencies, attempting direct import
# If this causes circular import errors, use lazy import pattern
from .core.channel_orchestrator import CommunicationManager

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
    # Shared types (high usage)
    'InteractionResponse',
    'ParsedCommand',
    # Message processing - interaction manager (high usage)
    'handle_user_message',
    # Conversation flow manager (high usage)
    'conversation_manager',
    # Core orchestration (high usage)
    'CommunicationManager',
]
