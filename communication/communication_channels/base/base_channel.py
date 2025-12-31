from abc import ABC, abstractmethod
from enum import Enum
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from core.logger import get_component_logger, get_logger
from core.error_handling import handle_errors

channel_logger = get_component_logger('communication_manager')

class ChannelStatus(Enum):
    UNINITIALIZED = "uninitialized"
    INITIALIZING = "initializing"
    READY = "ready"
    ERROR = "error"
    STOPPED = "stopped"

class ChannelType(Enum):
    SYNC = "synchronous"
    ASYNC = "asynchronous"

@dataclass
class ChannelConfig:
    """Configuration for communication channels"""
    name: str
    enabled: bool = True
    max_retries: int = 3
    retry_delay: float = 1.0
    backoff_multiplier: float = 2.0
    timeout: float = 30.0
    custom_settings: Optional[Dict[str, Any]] = None

    @handle_errors("post-initializing channel config")
    def __post_init__(self):
        """Post-initialization setup."""
        try:
            if self.custom_settings is None:
                self.custom_settings = {}
        except Exception as e:
            # Use a basic logger for dataclass errors
            logger = get_logger(__name__)
            logger.error(f"Error in channel config post-init: {e}")
            # Set a default value to prevent further errors
            self.custom_settings = {}

class BaseChannel(ABC):
    """Abstract base class for all communication channels"""
    
    @handle_errors("initializing base channel")
    def __init__(self, config: ChannelConfig):
        """Initialize the object."""
        try:
            self.config = config
            self.status = ChannelStatus.UNINITIALIZED
            self.error_message: Optional[str] = None
            # Standardize: route channel instance logs to the component logger named by config.name
            try:
                self.logger = get_component_logger(self.config.name)
            except Exception:
                # Fallback to module logger if component logger unavailable
                self.logger = get_logger(f"{__name__}.{self.__class__.__name__}")
        except Exception as e:
            # Use a basic logger if all else fails
            self.logger = get_logger(__name__)
            self.logger.error(f"Error initializing base channel: {e}")
            raise
        
    @property
    @abstractmethod
    @handle_errors("getting channel type", default_return=ChannelType.SYNC)
    def channel_type(self) -> ChannelType:
        """Return whether this channel is sync or async"""
        pass
    
    @abstractmethod
    @handle_errors("initializing channel", default_return=False)
    async def initialize(self) -> bool:
        """Initialize the channel. Returns True if successful."""
        pass
    
    @abstractmethod
    @handle_errors("shutting down channel", default_return=False)
    async def shutdown(self) -> bool:
        """Shutdown the channel. Returns True if successful."""
        pass
    
    @abstractmethod
    @handle_errors("sending message", default_return=False)
    async def send_message(self, recipient: str, message: str, **kwargs) -> bool:
        """Send a message. Returns True if successful."""
        pass
    
    @abstractmethod
    @handle_errors("receiving messages", default_return=[])
    async def receive_messages(self) -> List[Dict[str, Any]]:
        """Receive messages. Returns list of message dictionaries."""
        pass
    
    @abstractmethod
    @handle_errors("performing health check", default_return=False)
    async def health_check(self) -> bool:
        """Perform a health check. Returns True if healthy."""
        pass
    
    @handle_errors("checking if channel is ready", default_return=False)
    def is_ready(self) -> bool:
        """Check if channel is ready to send/receive messages"""
        return self.status == ChannelStatus.READY
    
    @handle_errors("getting channel status", default_return=ChannelStatus.ERROR)
    def get_status(self) -> ChannelStatus:
        """Get current channel status"""
        return self.status
    
    @handle_errors("getting channel error", default_return=None)
    def get_error(self) -> Optional[str]:
        """Get last error message"""
        return self.error_message
    
    @handle_errors("setting channel status")
    def _set_status(self, status: ChannelStatus, error_message: Optional[str] = None):
        """Internal method to update status"""
        self.status = status
        self.error_message = error_message
        # Only log status changes that are important (errors or startup completion)
        if status == ChannelStatus.ERROR:
            self.logger.warning(f"Channel status: {status.value}" + 
                               (f" - {error_message}" if error_message else ""))
        elif status == ChannelStatus.READY:
            self.logger.debug(f"Channel ready")
        # Suppress other status changes to reduce log spam 