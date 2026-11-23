"""Shared task and check-in routing for text-only phone channels."""

import re
from core.error_handling import handle_errors


@handle_errors("routing phone channel reply", re_raise=True, user_friendly=False, retry_after_recovery=False)
def route_phone_reply(state, text, user_id, number, channel):
    """Resolve a single prompt or require an explicit target before a mutation."""
    from communication.message_processing.email_reply_routing import (
        build_task_reply_command, route_checkin_reply, route_task_reply,
    )
    from communication.message_processing.interaction_manager import handle_user_message

    if text.lower() == f"{channel} status":
        return f"MHM {channel.upper()} is connected. Reply STOP to stop messages; START to resume."
    if text.lower().startswith("checkin "):
        response = route_checkin_reply(user_id, text[8:].strip())
        if response is None or response.completed:
            state.clear_context(number, "checkin", "")
        return response.message if response else "No check-in is open. Send start checkin to begin."
    contexts = state.contexts(number)
    qualified = re.match(r"^(?:complete|snooze|skip|simplify|update|delete)\s+task\b", text, re.IGNORECASE)
    short = not qualified and (text.isdigit() or build_task_reply_command(text, "probe") is not None)
    if short and not contexts:
        return f"No {channel.upper()} prompt is linked to that reply. Use complete task <task name or ID>, or checkin <answer>. No action was taken."
    if short and len(contexts) > 1:
        return "More than one prompt may need a reply. Use complete task <task name or ID> for a task, or checkin <answer> for your check-in. No action was taken."
    if short and len(contexts) == 1:
        kind, task_id = contexts[0]
        response = (route_task_reply(user_id, text, task_id) if kind == "task_reminder"
                    else route_checkin_reply(user_id, text))
        if kind == "task_reminder":
            from tasks.task_data_manager import get_task_by_id

            task = get_task_by_id(user_id, task_id)
            if task and task.get("status") == "completed":
                state.clear_context(number, kind, task_id)
        elif response is None or response.completed:
            state.clear_context(number, kind, task_id)
        if response:
            return response.message
    response = handle_user_message(user_id, text, channel)
    if not response.completed and text.lower() in {"start checkin", "start check-in", "checkin", "check-in"}:
        state.add_context(number, "checkin")
    return response.message or "I couldn't confirm that action. Check its current state before retrying."
