# communication/message_processing/prefix_command_processor.py

"""Unified slash and bang prefix command processing."""

from dataclasses import dataclass
from typing import Literal

from core.error_handling import handle_errors
from core.logger import get_component_logger
from communication.command_handlers.shared_types import InteractionResponse
from communication.message_processing.command_registry import CommandDefinition
from communication.message_processing.conversation_flow_manager import conversation_manager

logger = get_component_logger("communication_manager")

FLOW_KEYWORDS = frozenset(["cancel", "skip", "end", "endlist", "endl"])


@dataclass
class PrefixCommandResult:
    """Result of prefix command processing."""

    response: InteractionResponse | None = None
    message: str | None = None


@handle_errors("processing prefix command", default_return=PrefixCommandResult())
def process_prefix_command(
    user_id: str,
    message_stripped: str,
    user_state: dict,
    command_definitions: list[CommandDefinition],
) -> PrefixCommandResult:
    """
    Process slash or bang prefixed commands.

    Returns an early InteractionResponse or a converted message for continued parsing.
    """
    if message_stripped.startswith("/"):
        return _process_prefixed_command(
            user_id, message_stripped, user_state, command_definitions, "/"
        )
    if message_stripped.startswith("!"):
        return _process_prefixed_command(
            user_id, message_stripped, user_state, command_definitions, "!"
        )
    return PrefixCommandResult(message=message_stripped)


@handle_errors("processing prefixed command", default_return=PrefixCommandResult())
def _process_prefixed_command(
    user_id: str,
    message_stripped: str,
    user_state: dict,
    command_definitions: list[CommandDefinition],
    prefix: Literal["/", "!"],
) -> PrefixCommandResult:
    label = "SLASH_COMMAND" if prefix == "/" else "BANG_COMMAND"
    logger.info(
        f"{label}: Detected {prefix} command '{message_stripped}' for user {user_id}"
    )

    lowered = message_stripped.lower()
    parts = lowered.split()
    cmd_name = parts[0][1:] if parts and parts[0].startswith(prefix) else ""

    if cmd_name in FLOW_KEYWORDS:
        reply_text, completed = conversation_manager.handle_inbound_message(
            user_id, message_stripped
        )
        return PrefixCommandResult(
            response=InteractionResponse(reply_text, completed)
        )

    if user_state["flow"] != 0 and cmd_name not in FLOW_KEYWORDS:
        logger.info(
            f"User {user_id} in flow {user_state['flow']} but sent command "
            f"'{message_stripped}', clearing flow"
        )
        conversation_manager.user_states.pop(user_id, None)
        conversation_manager._save_user_states()

    cmd_def = next(
        (c for c in command_definitions if c.name == cmd_name), None
    )

    if cmd_def and cmd_def.is_flow:
        flow_response = _start_flow_command(user_id, cmd_name)
        if flow_response is not None:
            return PrefixCommandResult(response=flow_response)

    if cmd_def:
        converted = _convert_mapped_command(
            message_stripped, cmd_name, cmd_def, prefix
        )
        return PrefixCommandResult(message=converted)

    return PrefixCommandResult(message=message_stripped[1:])


@handle_errors("starting flow command", default_return=None)
def _start_flow_command(user_id: str, cmd_name: str) -> InteractionResponse | None:
    if cmd_name == "checkin":
        reply_text, completed = conversation_manager.start_checkin(user_id)
        return InteractionResponse(reply_text, completed)
    if cmd_name == "restart":
        reply_text, completed = conversation_manager.restart_checkin(user_id)
        return InteractionResponse(reply_text, completed)
    if cmd_name == "clear":
        reply_text, completed = conversation_manager.clear_stuck_flows(user_id)
        return InteractionResponse(reply_text, completed)

    starter_name = f"start_{cmd_name}_flow"
    starter_fn = getattr(conversation_manager, starter_name, None)
    if callable(starter_fn):
        result = starter_fn(user_id)
        if isinstance(result, (list, tuple)) and len(result) >= 2:
            reply_text, completed = result[0], result[1]
        else:
            reply_text, completed = "", True
        return InteractionResponse(reply_text, completed)

    return InteractionResponse(f"Flow '{cmd_name}' is not available yet.", True)


@handle_errors("converting mapped command", default_return="")
def _convert_mapped_command(
    message_stripped: str,
    cmd_name: str,
    cmd_def: CommandDefinition,
    prefix: Literal["/", "!"],
) -> str:
    if cmd_def.mapped_message is None:
        return message_stripped[1:]

    if len(message_stripped) > len(cmd_name) + 1:
        args = message_stripped[len(cmd_name) + 1 :].strip()
        converted_message = cmd_def.get_mapped_message()
        if converted_message.startswith("!"):
            converted_message = converted_message[1:]
        if args:
            converted_message += " " + args
    else:
        converted_message = cmd_def.get_mapped_message()
        if converted_message.startswith("!"):
            converted_message = converted_message[1:]

    return converted_message
