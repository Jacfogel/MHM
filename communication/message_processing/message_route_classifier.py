# communication/message_processing/message_route_classifier.py

"""Classify inbound messages by prefix and command registry for routing tests and tooling."""

from dataclasses import dataclass
from enum import Enum

from core.error_handling import handle_errors
from core.logger import get_component_logger
from communication.message_processing.command_registry import (
    CommandDefinition,
    build_command_definitions,
    build_slash_command_map,
    command_definitions_as_dicts,
    lookup_command_definition,
)

logger = get_component_logger("message_route_classifier")


class MessageType(Enum):
    """Types of messages for routing classification."""

    SLASH_COMMAND = "slash_command"
    BANG_COMMAND = "bang_command"
    STRUCTURED_COMMAND = "structured_command"
    CONVERSATIONAL = "conversational"
    FLOW_COMMAND = "flow_command"
    UNKNOWN = "unknown"


@dataclass
class RoutingResult:
    """Result of message route classification."""

    message_type: MessageType
    command_name: str | None = None
    mapped_message: str | None = None
    should_continue_parsing: bool = True
    flow_command: bool = False


class MessageRouteClassifier:
    """Classify messages by slash/bang prefix using the canonical command registry."""

    @handle_errors("initializing message route classifier", default_return=None)
    def __init__(self):
        self._command_definitions: list[CommandDefinition] = build_command_definitions()
        defs_as_dicts = command_definitions_as_dicts(self._command_definitions)
        self.slash_command_map = {
            f"/{c['name']}": c["mapped_message"] for c in defs_as_dicts
        }
        self.bang_command_map = {
            f"!{c['name']}": c["mapped_message"] for c in defs_as_dicts
        }

    @handle_errors("routing message", default_return=RoutingResult(MessageType.UNKNOWN))
    def route_message(self, message: str) -> RoutingResult:
        """Classify a message and return routing metadata."""
        if not message or not isinstance(message, str) or not message.strip():
            logger.error(f"Invalid message: {message}")
            return RoutingResult(MessageType.UNKNOWN)

        message_stripped = message.strip()
        if message_stripped.startswith("/"):
            return self._route_prefixed_command(message_stripped, "/")
        if message_stripped.startswith("!"):
            return self._route_prefixed_command(message_stripped, "!")
        return RoutingResult(MessageType.STRUCTURED_COMMAND, should_continue_parsing=True)

    @handle_errors("routing prefixed command", default_return=RoutingResult(MessageType.UNKNOWN))
    def _route_prefixed_command(self, message: str, prefix: str) -> RoutingResult:
        """Classify a slash or bang command with validation."""
        if not message or not isinstance(message, str) or not message.strip():
            logger.error(f"Invalid message: {message}")
            return RoutingResult(MessageType.UNKNOWN)

        lowered = message.lower()
        parts = lowered.split()
        cmd_name = parts[0][1:] if parts and parts[0].startswith(prefix) else ""
        flow_keywords = {"cancel", "skip", "end", "endlist", "endl"}

        if cmd_name in flow_keywords:
            return RoutingResult(
                MessageType.FLOW_COMMAND,
                command_name=cmd_name,
                mapped_message=message if prefix == "/" else f"{prefix}{cmd_name}",
                should_continue_parsing=False,
                flow_command=True,
            )

        cmd_def = lookup_command_definition(self._command_definitions, cmd_name)
        if cmd_def:
            if cmd_def.is_flow:
                return RoutingResult(
                    MessageType.FLOW_COMMAND,
                    command_name=cmd_name,
                    mapped_message=cmd_def.get_mapped_message(),
                    should_continue_parsing=False,
                    flow_command=True,
                )
            msg_type = (
                MessageType.SLASH_COMMAND if prefix == "/" else MessageType.BANG_COMMAND
            )
            return RoutingResult(
                msg_type,
                command_name=cmd_name,
                mapped_message=cmd_def.get_mapped_message(),
                should_continue_parsing=True,
            )

        msg_type = MessageType.SLASH_COMMAND if prefix == "/" else MessageType.BANG_COMMAND
        return RoutingResult(msg_type, should_continue_parsing=True)

    @handle_errors("getting command definitions", default_return=[])
    def get_command_definitions(self) -> list[dict[str, str]]:
        return command_definitions_as_dicts(self._command_definitions)

    @handle_errors("getting slash command map", default_return={})
    def get_slash_command_map(self) -> dict[str, str]:
        return build_slash_command_map(self._command_definitions)

    @handle_errors("getting bang command map", default_return={})
    def get_bang_command_map(self) -> dict[str, str]:
        return build_slash_command_map(self._command_definitions)

    @handle_errors("checking if command is flow command", default_return=False)
    def is_flow_command(self, command_name: str) -> bool:
        if not command_name or not isinstance(command_name, str) or not command_name.strip():
            return False
        cmd_def = lookup_command_definition(self._command_definitions, command_name)
        return bool(cmd_def and cmd_def.is_flow)

    @handle_errors("getting command mapping", default_return=None)
    def get_command_mapping(self, command_name: str) -> str | None:
        if not command_name or not isinstance(command_name, str) or not command_name.strip():
            return None
        cmd_def = lookup_command_definition(self._command_definitions, command_name)
        return cmd_def.get_mapped_message() if cmd_def else None
