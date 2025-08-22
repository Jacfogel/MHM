from typing import Dict, Type, Optional
from bot.base_channel import BaseChannel, ChannelConfig
from core.logger import get_logger, get_component_logger
from core.error_handling import (
    error_handler, DataError, FileOperationError, handle_errors
)
from core.config import get_available_channels, get_channel_class_mapping

factory_logger = get_component_logger('communication_manager')
logger = factory_logger

class ChannelFactory:
    """Factory for creating communication channels using config-based discovery"""
    
    _channel_registry: Dict[str, Type[BaseChannel]] = {}
    _initialized = False
    
    @classmethod
    @handle_errors("initializing channel factory")
    def _initialize_registry(cls):
        """Initialize the channel registry from configuration"""
        if cls._initialized:
            return
            
        from core.config import get_available_channels, get_channel_class_mapping
        
        available_channels = get_available_channels()
        channel_mapping = get_channel_class_mapping()
        
        for channel_name in available_channels:
            if channel_name in channel_mapping:
                try:
                    # Dynamic import of channel class
                    class_path = channel_mapping[channel_name]
                    module_name, class_name = class_path.rsplit('.', 1)
                    
                    import importlib
                    module = importlib.import_module(module_name)
                    channel_class = getattr(module, class_name)
                    
                    cls._channel_registry[channel_name] = channel_class
                    logger.debug(f"Auto-registered channel type: {channel_name}")
                    
                except (ImportError, AttributeError) as e:
                    logger.error(f"Failed to import channel class for {channel_name}: {e}")
        
        cls._initialized = True
        logger.info(f"Channel factory initialized with {len(cls._channel_registry)} channels: {list(cls._channel_registry.keys())}")
    
    @classmethod
    @handle_errors("registering channel")
    def register_channel(cls, name: str, channel_class: Type[BaseChannel]):
        """Register a new channel type (legacy compatibility)"""
        cls._channel_registry[name] = channel_class
        logger.debug(f"Manually registered channel type: {name}")
    
    @classmethod
    @handle_errors("creating channel", default_return=None)
    def create_channel(cls, name: str, config: ChannelConfig) -> Optional[BaseChannel]:
        """Create a channel instance"""
        # Ensure registry is initialized
        cls._initialize_registry()
        
        if name not in cls._channel_registry:
            logger.error(f"Unknown channel type: {name}. Available: {list(cls._channel_registry.keys())}")
            return None
        
        channel_class = cls._channel_registry[name]
        return channel_class(config)
    
    @classmethod
    @handle_errors("getting available channels", default_return=[])
    def get_available_channels(cls) -> list:
        """Get list of available channel types"""
        # Ensure registry is initialized
        cls._initialize_registry()
        return list(cls._channel_registry.keys()) 