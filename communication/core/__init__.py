"""Core orchestration package for communication channels.

Contains channel orchestration, factory patterns, monitoring,
and retry management for communication infrastructure.
"""

# Main public API - package-level exports for easier refactoring
# Note: CommunicationManager has circular dependencies, so it may need lazy import
from .factory import ChannelFactory
from .retry_manager import RetryManager, QueuedMessage
from .channel_monitor import ChannelMonitor

# Core orchestration - lazy import to avoid circular dependencies
# Use: from communication.core import CommunicationManager (imported on-demand)
# Note: CommunicationManager has circular dependencies, so it's imported lazily

__all__ = [
    # Factory
    'ChannelFactory',
    # Retry management
    'RetryManager',
    'QueuedMessage',
    # Channel monitoring
    'ChannelMonitor',
]
