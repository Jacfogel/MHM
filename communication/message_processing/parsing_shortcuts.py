# communication/message_processing/parsing_shortcuts.py

"""Rule-based parsing shortcuts and entity coercion before full parser dispatch."""

import re
from collections.abc import Callable

from core.error_handling import handle_errors
from communication.command_handlers.shared_types import InteractionResponse, ParsedCommand
from communication.message_processing.command_parser import ParsingResult


@handle_errors("getting task management handler", user_friendly=False)
def _get_task_management_handler():
    """Lazy import to avoid circular imports with command handlers."""
    from communication.command_handlers.task_handler import TaskManagementHandler

    return TaskManagementHandler()


@handle_errors("trying parsing shortcuts", default_return=None)
def try_parsing_shortcuts(
    user_id: str,
    message: str,
    channel_type: str,
    handle_structured_command: Callable,
    augment_suggestions: Callable,
) -> InteractionResponse | None:
    """Try shortcut paths that bypass the main parser."""
    low = message.strip().lower()

    if low == "confirm delete":
        try:
            handler = _get_task_management_handler()
            resp = handler._handle_delete_task(user_id, {"task_identifier": None})
            return augment_suggestions(
                ParsedCommand("delete_task", {}, 1.0, message), resp
            )
        except Exception:
            pass

    if low == "complete task":
        try:
            handler = _get_task_management_handler()
            resp = handler._handle_complete_task(user_id, {})
            return augment_suggestions(
                ParsedCommand("complete_task", {}, 1.0, message), resp
            )
        except Exception:
            pass

    try:
        m1 = re.search(
            r"^edit\s+schedule\s+period\s+([\w\-]+)\s+(tasks?|check.?ins?|messages?)",
            low,
            re.IGNORECASE,
        )
        m2 = re.search(
            r"^edit\s+(?:the\s+)?([\w\-]+)\s+period\s+in\s+my\s+(tasks?|check.?ins?|messages?)\s+schedule",
            low,
            re.IGNORECASE,
        )
        m = m1 or m2
        if m:
            period_name = m.group(1)
            category = m.group(2)
            parsed_cmd = ParsedCommand(
                "edit_schedule_period",
                {"period_name": period_name, "category": category},
                0.95,
                message,
            )
            parsing_result = ParsingResult(
                parsed_command=parsed_cmd, confidence=0.95, method="rule_based"
            )
            resp = handle_structured_command(user_id, parsing_result, channel_type)
            return augment_suggestions(parsed_cmd, resp)
    except Exception:
        pass

    return None


@handle_errors("coercing unknown update task", default_return=None)
def coerce_unknown_update_task(
    parsing_result: ParsingResult, message: str
) -> ParsingResult:
    """Coerce update_task when parser returned unknown but message clearly asks to update."""
    if (
        parsing_result.parsed_command.intent != "unknown"
        or not message.lower().strip().startswith("update task")
    ):
        return parsing_result

    coerced_entities = _extract_update_task_entities(message)
    if coerced_entities.get("task_identifier") and any(
        k in coerced_entities for k in ["due_date", "priority", "title"]
    ):
        parsing_result.parsed_command = ParsedCommand(
            "update_task", coerced_entities, 0.9, message
        )
        parsing_result.confidence = 0.9
    return parsing_result


@handle_errors("reinforcing update task parsing", default_return=None)
def reinforce_update_task_parsing(
    parsing_result: ParsingResult, message: str
) -> ParsingResult:
    """Guard and augment update_task entities when confidence is high enough."""
    low_msg = message.lower().strip()
    if low_msg.startswith("update task"):
        coerced_entities = parsing_result.parsed_command.entities.copy()
        extracted = _extract_update_task_entities(message)
        for key, value in extracted.items():
            if key not in coerced_entities:
                coerced_entities[key] = value
        parsing_result.parsed_command = ParsedCommand(
            "update_task", coerced_entities, 0.95, message
        )
        parsing_result.confidence = 0.95
        return parsing_result

    if parsing_result.parsed_command.intent == "update_task":
        entities = parsing_result.parsed_command.entities
        original = parsing_result.parsed_command.original_message
        if "due_date" not in entities:
            m = re.search(r"(?:due\s+date|due)\s+(.+)", original, re.IGNORECASE)
            if m:
                entities["due_date"] = m.group(1)
        if "priority" not in entities:
            p = re.search(
                r"priority\s+(?:to\s+)?(high|medium|low|urgent|critical)",
                original,
                re.IGNORECASE,
            )
            if p:
                entities["priority"] = p.group(1).lower()
        if "title" not in entities:
            t = re.search(
                r'(?:title\s+"?([^"\n]+)"?$|rename\s+(?:task\s+)?(?:to\s+)?"?([^"\n]+)"?$)',
                original,
                re.IGNORECASE,
            )
            if t:
                new_title = t.group(1) or t.group(2)
                if new_title:
                    entities["title"] = new_title.strip()

    return parsing_result


@handle_errors("extracting update task entities", default_return={})
def _extract_update_task_entities(message: str) -> dict:
    """Extract task_identifier and field updates from an update-task message."""
    coerced_entities: dict = {}
    m_id = re.search(
        r"^update\s+task\s+(\d+|\w+)(?=\s+(?:title|priority|due|description)|$)",
        message,
        re.IGNORECASE,
    )
    if m_id:
        coerced_entities["task_identifier"] = m_id.group(1).strip().strip('"')
    m_due = re.search(r"(?:due\s+date|due)\s+(.+)", message, re.IGNORECASE)
    if m_due:
        coerced_entities["due_date"] = m_due.group(1).strip()
    m_pri = re.search(
        r"priority\s+(?:to\s+)?(high|medium|low|urgent|critical)",
        message,
        re.IGNORECASE,
    )
    if m_pri:
        coerced_entities["priority"] = m_pri.group(1).lower()
    m_title = re.search(
        r'(?:title\s+"([^"]+)"|title\s+([^\n]+)|rename\s+(?:task\s+)?(?:to\s+)?"?([^"\n]+)"?)',
        message,
        re.IGNORECASE,
    )
    if m_title:
        new_title = m_title.group(1) or m_title.group(2) or m_title.group(3)
        if new_title:
            coerced_entities["title"] = new_title.strip()
    return coerced_entities
