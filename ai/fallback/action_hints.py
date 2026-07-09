"""Action-shaped fallback hints when AI chat/planning is unavailable."""

from __future__ import annotations

from ai.fallback.categories import FallbackCategory
from ai.fallback.context import FallbackContext
from ai.prompts.action_catalog import get_action_catalog
from core.error_handling import handle_errors

_ACTION_VERB_MARKERS = (
    "create task",
    "add task",
    "new task",
    "complete task",
    "delete task",
    "update task",
    "start check",
    "check in",
    "check-in",
    "create note",
    "new note",
    "quick note",
    "show profile",
    "update profile",
    "show schedule",
    "sync google",
    "connect google",
)

_COMMAND_EXAMPLES: dict[str, str] = {
    "create_task": "add task buy milk",
    "list_tasks": "list tasks",
    "complete_task": "complete task 1",
    "start_checkin": "check in",
    "create_note": "note Groceries | eggs and bread",
    "show_profile": "show my profile",
    "help": "help tasks",
}


@handle_errors("building action-unavailable fallback", default_return=None)
def try_action_unavailable_response(
    prompt_lower: str,
    context: FallbackContext | None,
) -> tuple[str, FallbackCategory] | None:
    """Suggest command-style retries without claiming an action succeeded."""
    if not any(marker in prompt_lower for marker in _ACTION_VERB_MARKERS):
        return None

    catalog = get_action_catalog()
    matched_action = _match_catalog_action(prompt_lower, catalog.actions)
    example = _COMMAND_EXAMPLES.get(matched_action or "", "help")

    if matched_action:
        action = catalog.get(matched_action)
        if action and action.feature_requirements:
            disabled = _feature_disabled(action.feature_requirements[0], context)
            if disabled:
                return (
                    f"{context.name_prefix if context else ''}{disabled} "
                    f"I can't run `{matched_action}` until that feature is enabled.",
                    FallbackCategory.ACTION_UNAVAILABLE,
                )

    prefix = context.name_prefix if context else ""
    return (
        f"{prefix}I'm offline for AI chat, so I can't run that automatically right now. "
        f"Try the command form instead (for example: `{example}`), or ask `help` for more.",
        FallbackCategory.ACTION_UNAVAILABLE,
    )


@handle_errors("matching catalog action from prompt", default_return=None)
def _match_catalog_action(prompt_lower: str, actions: dict) -> str | None:
    for action_name in sorted(actions, key=len, reverse=True):
        readable = action_name.replace("_", " ")
        if readable in prompt_lower or action_name in prompt_lower:
            return action_name
    if "task" in prompt_lower:
        return "create_task"
    if "check" in prompt_lower:
        return "start_checkin"
    if "note" in prompt_lower:
        return "create_note"
    if "profile" in prompt_lower:
        return "show_profile"
    return None


@handle_errors("checking disabled feature for action hint", default_return=None)
def _feature_disabled(feature: str, context: FallbackContext | None) -> str | None:
    if context is None:
        return None
    if feature == "task_management":
        tasks = context.structured.get("tasks") or {}
        if tasks.get("enabled") is False:
            return "Task management is not enabled on your account."
    if feature == "checkins":
        checkins = context.structured.get("checkins") or {}
        if checkins.get("enabled") is False:
            return "Check-ins are not enabled on your account."
    if feature == "notebook":
        return None
    if feature == "automated_messages":
        messages = context.structured.get("messages") or {}
        if messages.get("enabled") is False:
            return "Automated messages are not enabled on your account."
    if feature == "google_health":
        health = context.structured.get("health") or {}
        if not health.get("available"):
            return "Google Health integration is not available on this account."
    return None
