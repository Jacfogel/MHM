"""Core orchestration package for communication channels.

Contains channel orchestration, factory patterns, monitoring,
and retry management for communication infrastructure.
"""

# Main public API - package-level exports for easier refactoring
# Note: CommunicationManager has circular dependencies, so it may need lazy import
# Note: ChannelFactory and ChannelMonitor have circular dependencies, using lazy import
from .retry_manager import RetryManager, QueuedMessage

# Core orchestration - lazy import to avoid circular dependencies
# Use: from communication.core import CommunicationManager (imported on-demand)
# Note: CommunicationManager has circular dependencies, so it's imported lazily

# Lazy import for ChannelFactory and ChannelMonitor to avoid circular dependencies
def __getattr__(name: str):
    """Lazy import handler for items with circular dependencies"""
    if name == 'ChannelFactory':
        from .factory import ChannelFactory
        return ChannelFactory
    elif name == 'ChannelMonitor':
        from .channel_monitor import ChannelMonitor
        return ChannelMonitor
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = [
    # Factory (lazy import)
    'ChannelFactory',
    # Retry management
    'RetryManager',
    'QueuedMessage',
    # Channel monitoring (lazy import)
    'ChannelMonitor',
]
