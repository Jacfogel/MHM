# message_router.py

from typing import Optional, Dict, List
from dataclasses import dataclass
from enum import Enum

from core.logger import get_component_logger
from core.error_handling import handle_errors

# Route routing logs to message processing component
router_logger = get_component_logger('message_router')
logger = router_logger

class MessageType(Enum):
    """Types of messages that can be routed"""
    SLASH_COMMAND = "slash_command"
    BANG_COMMAND = "bang_command"
    STRUCTURED_COMMAND = "structured_command"
    CONVERSATIONAL = "conversational"
    FLOW_COMMAND = "flow_command"
    UNKNOWN = "unknown"

@dataclass
class RoutingResult:
    """Result of message routing"""
    message_type: MessageType
    command_name: Optional[str] = None
    mapped_message: Optional[str] = None
    should_continue_parsing: bool = True
    flow_command: bool = False

class MessageRouter:
    """Routes messages to appropriate handlers based on message type and content"""
    
    @handle_errors("initializing message router", default_return=None)
    def __init__(self):
        """Initialize the message router"""
        # Channel-agnostic command definitions for discoverability across channels
        self._command_definitions = [
            {"name": "tasks", "mapped_message": "show my tasks", "description": "Show your tasks", "is_flow": False},
            {"name": "profile", "mapped_message": "show profile", "description": "Show your profile", "is_flow": False},
            {"name": "schedule", "mapped_message": "show schedule", "description": "Show your schedules", "is_flow": False},
            {"name": "messages", "mapped_message": "show messages", "description": "Show your messages", "is_flow": False},
            {"name": "analytics", "mapped_message": "show analytics", "description": "Show wellness analytics and insights", "is_flow": False},
            {"name": "status", "mapped_message": "status", "description": "Show system/user status", "is_flow": False},
            {"name": "help", "mapped_message": "help", "description": "Show help and examples", "is_flow": False},
            {"name": "checkin", "mapped_message": "start checkin", "description": "Start a check-in", "is_flow": True},
            {"name": "cancel", "mapped_message": "/cancel", "description": "Cancel current flow", "is_flow": False},
        ]
        
        # Build the legacy map for quick lookup
        self.slash_command_map = {f"/{c['name']}": c['mapped_message'] for c in self._command_definitions}
        self.bang_command_map = {f"!{c['name']}": c['mapped_message'] for c in self._command_definitions}
    
    @handle_errors("routing message", default_return=RoutingResult(MessageType.UNKNOWN))
    def route_message(self, message: str) -> RoutingResult:
        """
        Route a message to determine its type and appropriate handling.
        
        Args:
            message: The user's message
            
        Returns:
            RoutingResult with message type and routing information
        """
        # Validate message
        if not message or not isinstance(message, str):
            logger.error(f"Invalid message: {message}")
            return RoutingResult(MessageType.UNKNOWN)
            
        if not message.strip():
            logger.error("Empty message provided")
            return RoutingResult(MessageType.UNKNOWN)
        
        message_stripped = message.strip()
        
        # Handle slash commands
        if message_stripped.startswith("/"):
            return self._route_slash_command(message_stripped)
        
        # Handle bang commands
        elif message_stripped.startswith("!"):
            return self._route_bang_command(message_stripped)
        
        # Default to structured command parsing
        return RoutingResult(MessageType.STRUCTURED_COMMAND, should_continue_parsing=True)
    
    @handle_errors("routing slash command", default_return=RoutingResult(MessageType.UNKNOWN))
    def _route_slash_command(self, message: str) -> RoutingResult:
        """
        Route a slash command with validation.
        
        Returns:
            RoutingResult: Routing result, UNKNOWN if failed
        """
        # Validate message
        if not message or not isinstance(message, str):
            logger.error(f"Invalid message: {message}")
            return RoutingResult(MessageType.UNKNOWN)
            
        if not message.strip():
            logger.error("Empty message provided")
            return RoutingResult(MessageType.UNKNOWN)
        """Route a slash command"""
        lowered = message.lower()
        parts = lowered.split()
        cmd_name = parts[0][1:] if parts and parts[0].startswith('/') else ''
        
        # Special handling for /cancel
        if cmd_name == 'cancel':
            return RoutingResult(
                MessageType.FLOW_COMMAND,
                command_name=cmd_name,
                mapped_message="/cancel",
                should_continue_parsing=False,
                flow_command=True
            )
        
        # Look up command definition
        cmd_def = next((c for c in self._command_definitions if c['name'] == cmd_name), None)
        
        if cmd_def:
            # Flow commands
            if cmd_def['is_flow']:
                return RoutingResult(
                    MessageType.FLOW_COMMAND,
                    command_name=cmd_name,
                    mapped_message=cmd_def['mapped_message'],
                    should_continue_parsing=False,
                    flow_command=True
                )
            
            # Regular commands
            return RoutingResult(
                MessageType.SLASH_COMMAND,
                command_name=cmd_name,
                mapped_message=cmd_def['mapped_message'],
                should_continue_parsing=True
            )
        
        # Unknown slash command - drop prefix and continue parsing
        return RoutingResult(
            MessageType.SLASH_COMMAND,
            should_continue_parsing=True
        )
    
    @handle_errors("routing bang command", default_return=RoutingResult(MessageType.UNKNOWN))
    def _route_bang_command(self, message: str) -> RoutingResult:
        """
        Route a bang command with validation.
        
        Returns:
            RoutingResult: Routing result, UNKNOWN if failed
        """
        # Validate message
        if not message or not isinstance(message, str):
            logger.error(f"Invalid message: {message}")
            return RoutingResult(MessageType.UNKNOWN)
            
        if not message.strip():
            logger.error("Empty message provided")
            return RoutingResult(MessageType.UNKNOWN)
        """Route a bang command"""
        lowered = message.lower()
        parts = lowered.split()
        cmd_name = parts[0][1:] if parts and parts[0].startswith('!') else ''
        
        # Look up command definition
        cmd_def = next((c for c in self._command_definitions if c['name'] == cmd_name), None)
        
        if cmd_def:
            # Flow commands
            if cmd_def['is_flow']:
                return RoutingResult(
                    MessageType.FLOW_COMMAND,
                    command_name=cmd_name,
                    mapped_message=cmd_def['mapped_message'],
                    should_continue_parsing=False,
                    flow_command=True
                )
            
            # Regular commands
            return RoutingResult(
                MessageType.BANG_COMMAND,
                command_name=cmd_name,
                mapped_message=cmd_def['mapped_message'],
                should_continue_parsing=True
            )
        
        # Unknown bang command - drop prefix and continue parsing
        return RoutingResult(
            MessageType.BANG_COMMAND,
            should_continue_parsing=True
        )
    
    @handle_errors("getting command definitions", default_return=[])
    def get_command_definitions(self) -> List[Dict[str, str]]:
        """
        Get command definitions with validation.
        
        Returns:
            List[Dict[str, str]]: Command definitions, empty list if failed
        """
        """Return canonical command definitions"""
        return [
            {"name": c['name'], "mapped_message": c['mapped_message'], "description": c['description']}
            for c in self._command_definitions
        ]
    
    @handle_errors("getting slash command map", default_return={})
    def get_slash_command_map(self) -> Dict[str, str]:
        """
        Get slash command map with validation.
        
        Returns:
            Dict[str, str]: Slash command map, empty dict if failed
        """
        """Get slash command mappings"""
        return {c['name']: c['mapped_message'] for c in self._command_definitions}
    
    @handle_errors("getting bang command map", default_return={})
    def get_bang_command_map(self) -> Dict[str, str]:
        """
        Get bang command map with validation.
        
        Returns:
            Dict[str, str]: Bang command map, empty dict if failed
        """
        """Get bang command mappings"""
        return {c['name']: c['mapped_message'] for c in self._command_definitions}
    
    @handle_errors("checking if command is flow command", default_return=False)
    def is_flow_command(self, command_name: str) -> bool:
        """
        Check if command is flow command with validation.
        
        Returns:
            bool: True if flow command, False otherwise
        """
        # Validate command_name
        if not command_name or not isinstance(command_name, str):
            logger.error(f"Invalid command_name: {command_name}")
            return False
            
        if not command_name.strip():
            logger.error("Empty command_name provided")
            return False
        """Check if a command is a flow command"""
        cmd_def = next((c for c in self._command_definitions if c['name'] == command_name), None)
        return cmd_def['is_flow'] if cmd_def else False
    
    @handle_errors("getting command mapping", default_return=None)
    def get_command_mapping(self, command_name: str) -> Optional[str]:
        """
        Get command mapping with validation.
        
        Returns:
            Optional[str]: Command mapping, None if failed
        """
        # Validate command_name
        if not command_name or not isinstance(command_name, str):
            logger.error(f"Invalid command_name: {command_name}")
            return None
            
        if not command_name.strip():
            logger.error("Empty command_name provided")
            return None
        """Get the mapped message for a command"""
        cmd_def = next((c for c in self._command_definitions if c['name'] == command_name), None)
        return cmd_def['mapped_message'] if cmd_def else None

# Global router instance
_message_router = None

@handle_errors("getting message router", default_return=None)
def get_message_router() -> MessageRouter:
    """Get the global message router instance"""
    global _message_router
    if _message_router is None:
        _message_router = MessageRouter()
    return _message_router
