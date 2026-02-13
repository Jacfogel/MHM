from communication.communication_channels.base.base_channel import BaseChannel, ChannelConfig
from core.logger import get_component_logger
from core.error_handling import handle_errors
import core.config

factory_logger = get_component_logger('communication_manager')
logger = factory_logger


@handle_errors("getting available channels", default_return=[])
def get_available_channels() -> list[str]:
    """Compatibility wrapper so tests can patch either module or core.config path."""
    return core.config.get_available_channels()


@handle_errors("getting channel class mapping", default_return={})
def get_channel_class_mapping() -> dict[str, str]:
    """Compatibility wrapper so tests can patch either module or core.config path."""
    return core.config.get_channel_class_mapping()


class ChannelFactory:
    """Factory for creating communication channels using config-based discovery"""
    
    _channel_registry: dict[str, type[BaseChannel]] = {}
    _initialized = False
    
    @classmethod
    @handle_errors("initializing channel factory")
    def _initialize_registry(cls):
        """Initialize the channel registry from configuration"""
        if cls._initialized:
            return

        try:
            # Use configured channels for auto-registration
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
                        if channel_class is None:
                            raise AttributeError(
                                f"{class_name} is None in module {module_name}"
                            )

                        cls._channel_registry[channel_name] = channel_class
                        logger.debug(f"Auto-registered channel type: {channel_name}")

                    except (ImportError, AttributeError) as e:
                        logger.error(
                            f"Failed to import channel class for {channel_name}: {e}"
                        )
        except Exception as e:
            logger.error(f"Failed to initialize channel registry: {e}")
        finally:
            cls._initialized = True
            logger.info(
                f"Channel factory initialized with {len(cls._channel_registry)} channels: {list(cls._channel_registry.keys())}"
            )
    
    @classmethod
    @handle_errors("creating channel", default_return=None)
    def create_channel(cls, name: str, config: ChannelConfig) -> BaseChannel | None:
        """Create a channel instance"""
        # Ensure registry is initialized
        cls._initialize_registry()
        
        if name not in cls._channel_registry:
            logger.error(f"Unknown channel type: {name}. Available: {list(cls._channel_registry.keys())}")
            return None
        
        channel_class = cls._channel_registry[name]
        return channel_class(config)
    
    @classmethod
    @handle_errors("getting registered channels", default_return=[])
    def get_registered_channels(cls) -> list:
        """Get list of registered channel types"""
        # Ensure registry is initialized
        cls._initialize_registry()
        return list(cls._channel_registry.keys())
    
 
