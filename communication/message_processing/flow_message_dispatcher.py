# communication/message_processing/flow_message_dispatcher.py

"""Dispatch messages when the user is in an active conversation flow."""

from dataclasses import dataclass

from core.error_handling import handle_errors
from core.logger import get_component_logger
from communication.command_handlers.shared_types import InteractionResponse
from communication.message_processing.command_parser import ParsingResult
from communication.message_processing.conversation_flow_manager import (
    conversation_manager,
)
from communication.message_processing.flows.flow_constants import (
    FLOW_JOURNAL_BODY,
    FLOW_LIST_ITEMS,
    FLOW_NOTE_BODY,
    FLOW_TASK_DUE_DATE,
    FLOW_TASK_PRIORITY,
    FLOW_TASK_REMINDER,
    JOURNAL_BODY_SUGGESTIONS,
    LIST_ITEMS_SUGGESTIONS,
    NOTEBOOK_BODY_SUGGESTIONS,
    TASK_DUE_DATE_SUGGESTIONS,
    TASK_PRIORITY_SUGGESTIONS,
)

from communication.message_processing.flows.flow_command_helpers import (
    FLOW_DISPATCH_KEYWORDS,
)

logger = get_component_logger("communication_manager")

COMMAND_KEYWORDS = [
    "update task",
    "complete task",
    "delete task",
    "show tasks",
    "list tasks",
    "create task",
    "add task",
    "new task",
    "/n ",
    "!n ",
    "n ",
    "/note ",
    "!note ",
    "note ",
    "/nn ",
    "!nn ",
    "nn ",
    "/newn ",
    "!newn ",
    "newn ",
    "/newnote ",
    "!newnote ",
    "newnote ",
    "/show ",
    "!show ",
    "show ",
    "/recent",
    "!recent",
    "recent",
    "/r ",
    "!r ",
    "r ",
]


@dataclass
class FlowDispatchResult:
    """Result of flow dispatch for an in-flow user."""

    response: InteractionResponse | None = None
    rule_based_override: ParsingResult | None = None
    continue_parsing: bool = True


@handle_errors("attaching flow suggestions", default_return=None)
def _attach_flow_suggestions(
    response: InteractionResponse,
    user_id: str,
    reply_text: str,
    completed: bool,
) -> InteractionResponse:
    """Attach follow-up buttons for active multi-step flows."""
    if completed or response.suggestions:
        return response

    user_state = conversation_manager.user_states.get(
        user_id, {"flow": 0, "state": 0, "data": {}}
    )
    flow = user_state.get("flow")

    if flow == FLOW_TASK_DUE_DATE:
        response.suggestions = list(TASK_DUE_DATE_SUGGESTIONS)
        return response

    if flow == FLOW_TASK_PRIORITY:
        response.suggestions = list(TASK_PRIORITY_SUGGESTIONS)
        return response

    if flow == FLOW_NOTE_BODY:
        response.suggestions = list(NOTEBOOK_BODY_SUGGESTIONS)
        return response

    if flow == FLOW_JOURNAL_BODY:
        response.suggestions = list(JOURNAL_BODY_SUGGESTIONS)
        return response

    if flow == FLOW_LIST_ITEMS:
        response.suggestions = list(LIST_ITEMS_SUGGESTIONS)
        return response

    if flow == FLOW_TASK_REMINDER or (
        not completed and "Would you like to set custom reminder periods" in reply_text
    ):
        state_data = user_state.get("data", {})
        task_id = state_data.get("task_identifier")
        if task_id:
            reminder_suggestions = (
                conversation_manager._generate_context_aware_reminder_suggestions(
                    user_id, task_id
                )
            )
            if reminder_suggestions:
                response.suggestions = reminder_suggestions

    return response


@handle_errors("dispatching flow message", default_return=FlowDispatchResult())
def dispatch_flow_message(
    user_id: str,
    message: str,
    command_parser,
) -> FlowDispatchResult:
    """
    Handle message routing when user is in an active conversation flow.

    Returns early response, rule_based_override for bypassed flow, or continue_parsing.
    """
    user_state = conversation_manager.user_states.get(
        user_id, {"flow": 0, "state": 0, "data": {}}
    )
    logger.info(
        f"FLOW_CHECK: User {user_id} flow state: {user_state.get('flow', 'None')} "
        f"(type: {type(user_state.get('flow'))})"
    )

    if user_state["flow"] == 0:
        return FlowDispatchResult()

    message_lower = message.strip().lower()

    if message_lower in FLOW_DISPATCH_KEYWORDS:
        logger.info(
            f"User {user_id} in flow {user_state['flow']} used flow keyword "
            f"'{message_lower}', delegating to conversation manager"
        )
        reply_text, completed = conversation_manager.handle_inbound_message(
            user_id, message
        )
        response = InteractionResponse(reply_text, completed)
        updated = _attach_flow_suggestions(
            response, user_id, reply_text, completed
        )
        if updated is not None:
            response = updated
        return FlowDispatchResult(
            response=response,
            continue_parsing=False,
        )

    rule_based_override: ParsingResult | None = None
    try:
        rule_based_result = command_parser._rule_based_parse(message)
    except Exception:
        rule_based_result = None

    if (
        rule_based_result is not None
        and rule_based_result.parsed_command.intent != "unknown"
    ):
        logger.info(
            f"User {user_id} in flow {user_state['flow']} issued command intent "
            f"'{rule_based_result.parsed_command.intent}', clearing flow"
        )
        conversation_manager.user_states.pop(user_id, None)
        conversation_manager._save_user_states()
        rule_based_override = rule_based_result

    is_command = any(
        message_lower == keyword or message_lower.startswith(keyword + " ")
        for keyword in COMMAND_KEYWORDS
    )

    if rule_based_override is None and is_command:
        logger.info(
            f"User {user_id} in flow {user_state['flow']} but issued command, "
            "clearing flow and processing command"
        )
        conversation_manager.user_states.pop(user_id, None)
        conversation_manager._save_user_states()
        return FlowDispatchResult(continue_parsing=True)

    if rule_based_override is None:
        logger.info(
            f"User {user_id} in active flow {user_state['flow']}, "
            "delegating to conversation manager"
        )
        reply_text, completed = conversation_manager.handle_inbound_message(
            user_id, message
        )
        response = InteractionResponse(reply_text, completed)
        updated = _attach_flow_suggestions(
            response, user_id, reply_text, completed
        )
        if updated is not None:
            response = updated

        return FlowDispatchResult(
            response=response,
            continue_parsing=False,
        )

    return FlowDispatchResult(
        rule_based_override=rule_based_override,
        continue_parsing=True,
    )
