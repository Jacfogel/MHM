from typing import Dict, Type, Optional
from bot.base_channel import BaseChannel, ChannelConfig
from core.logger import get_logger
from core.error_handling import (
    error_handler, DataError, FileOperationError, handle_errors
)

logger = get_logger(__name__)

class ChannelFactory:
    """Factory for creating communication channels"""
    
    _channel_registry: Dict[str, Type[BaseChannel]] = {}
    
    @classmethod
    @handle_errors("registering channel")
    def register_channel(cls, name: str, channel_class: Type[BaseChannel]):
        """Register a new channel type"""
        cls._channel_registry[name] = channel_class
        logger.debug(f"Registered channel type: {name}")
    
    @classmethod
    @handle_errors("creating channel", default_return=None)
    def create_channel(cls, name: str, config: ChannelConfig) -> Optional[BaseChannel]:
        """Create a channel instance"""
        if name not in cls._channel_registry:
            logger.error(f"Unknown channel type: {name}")
            return None
        
        channel_class = cls._channel_registry[name]
        return channel_class(config)
    
    @classmethod
    @handle_errors("getting available channels", default_return=[])
    def get_available_channels(cls) -> list:
        """Get list of available channel types"""
        return list(cls._channel_registry.keys()) 