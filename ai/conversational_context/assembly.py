# ai/conversational_context/assembly.py

"""Orchestrate natural-language context sections into LM Studio message arrays."""

from typing import Any

from ai.context_builder import ContextData, get_context_builder
from ai.context_service import AIContextEnvelope, build_ai_context_envelope
from ai.conversational_context.instructions import CONVERSATIONAL_CONTEXT_INSTRUCTIONS
from ai.conversational_context.context_phraser import (
    append_profile_sections,
    phrase_checkin_summary,
    _checkin_completed_today,
)
from ai.prompt_flows import get_product_ai_prompt_flow
from core.error_handling import handle_errors
from tasks.task_data_handlers import runtime_task_due_date


@handle_errors("building conversational context parts", default_return=[])
def build_context_parts(
    user_id: str, envelope: AIContextEnvelope | None = None
) -> list[str]:
    """Assemble natural-language context lines for the system prompt."""
    envelope = envelope or build_ai_context_envelope(
        user_id,
        requested_intent="chat_response",
        include_conversation_history=True,
    )
    if envelope is None:
        return []

    context = _profile_context_from_envelope(envelope)
    structured = envelope.structured
    parts: list[str] = []

    append_profile_sections(parts, context)
    _append_feature_enablement_from_envelope(parts, structured)
    _append_checkin_summary_from_envelope(parts, structured)
    _append_health_guidance_from_envelope(parts, structured)
    _append_activity_and_mood_trends_from_envelope(parts, structured)
    _append_conversation_history_from_envelope(parts, structured)
    _append_today_checkin_status_from_envelope(parts, structured)

    recent_sent_all = _append_recent_sent_messages_from_envelope(parts, structured)
    _append_task_reminder_from_messages(parts, recent_sent_all)
    _append_task_data_from_envelope(parts, structured)
    _append_schedule_details_from_envelope(parts, structured)

    return parts


@handle_errors(
    "assembling comprehensive conversational messages",
    default_return=[
        {
            "role": "system",
            "content": "You are a supportive wellness assistant. Keep responses helpful, encouraging, and conversational.",
        },
        {"role": "user", "content": "Hello"},
    ],
)
def assemble_comprehensive_messages(
    user_id: str, user_prompt: str, wellness_base_prompt: str
) -> list[dict[str, Any]]:
    """Build system + user messages for comprehensive conversational generation."""
    flow = get_product_ai_prompt_flow("chat_response")
    envelope = build_ai_context_envelope(
        user_id,
        requested_intent=flow.name,
        prompt_request=user_prompt,
        include_conversation_history=True,
    )
    context_parts = build_context_parts(user_id, envelope=envelope)
    context_str = (
        "\n".join(context_parts) if context_parts else "New user with no data"
    )

    instructions = CONVERSATIONAL_CONTEXT_INSTRUCTIONS.format(context_str=context_str)
    system_message = {
        "role": "system",
        "content": f"{wellness_base_prompt}\n{instructions}",
    }
    user_message = {"role": "user", "content": user_prompt}
    return [system_message, user_message]


@handle_errors("building profile context from AI envelope", default_return={})
def _profile_context_from_envelope(
    envelope: AIContextEnvelope,
) -> dict[str, Any]:
    """Build the profile/context dict expected by existing phrasing helpers."""
    structured = envelope.structured
    account = structured.get("account") or {}
    preferences = structured.get("preferences") or {}
    personal_context = structured.get("personal_context") or {}
    schedules = structured.get("schedules") or {}
    return {
        "user_profile": {
            "preferred_name": (
                account.get("preferred_name")
                or personal_context.get("preferred_name")
                or ""
            ),
            "active_categories": preferences.get("categories") or [],
            "messaging_service": (preferences.get("channel") or {}).get("type", ""),
            "active_schedules": schedules.get("active_schedules") or [],
        },
        "user_context": personal_context,
    }


@handle_errors("appending feature enablement from AI envelope", default_return=None)
def _append_feature_enablement_from_envelope(
    parts: list[str], structured: dict[str, Any]
) -> None:
    """Append feature availability lines from envelope sections."""
    checkins = structured.get("checkins") or {}
    tasks = structured.get("tasks") or {}
    messages = structured.get("messages") or {}
    feature_status = []
    if checkins.get("enabled"):
        feature_status.append("check-ins are enabled")
    else:
        feature_status.append(
            "check-ins are disabled - do NOT mention check-ins, check-in data, "
            "or suggest starting check-ins"
        )
    if tasks.get("enabled"):
        feature_status.append("task management is enabled")
    else:
        feature_status.append(
            "task management is disabled - do NOT mention tasks, task creation, "
            "or task reminders"
        )
    if messages.get("enabled"):
        feature_status.append("automated messages are enabled")
    else:
        feature_status.append(
            "automated messages are disabled - do NOT mention scheduled message "
            "categories, suggest enabling automated messages, or reference recent "
            "automated sends"
        )
    parts.append(f"IMPORTANT - Feature availability: {'; '.join(feature_status)}")


# not_duplicate: checkin_prompt_sections_share_guard_shape
@handle_errors("appending check-in summary from AI envelope", default_return=None)
def _append_checkin_summary_from_envelope(
    parts: list[str], structured: dict[str, Any]
) -> None:
    """Append check-in summary text from envelope check-in data."""
    checkins = structured.get("checkins") or {}
    if not checkins.get("enabled"):
        return
    recent = list(checkins.get("recent") or [])
    if not recent:
        parts.append("They have not completed any check-ins yet.")
        return
    analysis = get_context_builder().analyze_context(
        ContextData(recent_checkins=recent)
    )
    parts.append(phrase_checkin_summary(analysis, recent))


@handle_errors("appending health guidance from AI envelope", default_return=None)
def _append_health_guidance_from_envelope(
    parts: list[str], structured: dict[str, Any]
) -> None:
    """Append safe health guidance from envelope health data."""
    summary = (structured.get("health") or {}).get("guidance_summary")
    if summary:
        parts.append(summary)


@handle_errors("appending activity and mood trends from AI envelope", default_return=None)
def _append_activity_and_mood_trends_from_envelope(
    parts: list[str], structured: dict[str, Any]
) -> None:
    """Append activity counts and mood trend summaries from envelope data."""
    checkins = structured.get("checkins") or {}
    if not checkins.get("enabled"):
        return
    recent = list(checkins.get("recent") or [])
    if recent:
        count = len(recent)
        parts.append(
            f"They have completed {count} check-in{'s' if count != 1 else ''} recently"
        )
    analysis = get_context_builder().analyze_context(
        ContextData(recent_checkins=recent)
    )
    if analysis.avg_mood is not None:
        trend_desc = {
            "improving": "improving",
            "declining": "declining",
            "stable": "staying stable",
        }.get(analysis.mood_trend, analysis.mood_trend)
        parts.append(
            f"Their mood has been averaging {analysis.avg_mood:.1f} out of 5 and is {trend_desc}"
        )


@handle_errors("appending conversation history from AI envelope", default_return=None)
def _append_conversation_history_from_envelope(
    parts: list[str], structured: dict[str, Any]
) -> None:
    """Append recent conversation history from envelope data."""
    history = (structured.get("conversation") or {}).get("recent_chat_interactions") or []
    if not history:
        return
    parts.append("In recent conversations, they've talked about:")
    for exchange in history[-3:]:
        user_msg = str(exchange.get("user_message") or "")[:80]
        if user_msg:
            full_msg = str(exchange.get("user_message") or "")
            suffix = "..." if len(full_msg) > 80 else ""
            parts.append(f"  - {user_msg}{suffix}")


# not_duplicate: checkin_prompt_sections_share_guard_shape
@handle_errors("appending today's check-in status from AI envelope", default_return=None)
def _append_today_checkin_status_from_envelope(
    parts: list[str], structured: dict[str, Any]
) -> None:
    """Append today's check-in completion status from envelope data."""
    checkins = structured.get("checkins") or {}
    if not checkins.get("enabled"):
        return
    latest = checkins.get("latest") or {}
    ts = (checkins.get("daily_status") or {}).get("last_checkin_timestamp") or ""
    completed_today = False
    completed_at = ""
    if ts:
        completed_today, completed_at = _checkin_completed_today(ts)
    if completed_today:
        details = []
        if latest.get("mood") is not None:
            details.append(f"mood was {latest['mood']} out of 5")
        if latest.get("energy") is not None:
            details.append(f"energy was {latest['energy']} out of 5")
        if details:
            parts.append(
                f"They completed their check-in today at {completed_at}, "
                f"reporting that their {' and '.join(details)}"
            )
        else:
            parts.append(f"They completed their check-in today at {completed_at}")
    else:
        parts.append("They have not completed their check-in for today yet")


@handle_errors("appending recent sent messages from AI envelope", default_return=None)
def _append_recent_sent_messages_from_envelope(
    parts: list[str], structured: dict[str, Any]
) -> list[dict[str, Any]] | None:
    """Append recent automated message context from envelope message data."""
    messages = structured.get("messages") or {}
    if not messages.get("enabled"):
        return None
    recent_sent_all = list(messages.get("recent_sent") or [])
    recent_sent = [m for m in recent_sent_all if m.get("category") != "checkin"][:3]
    if not recent_sent:
        return recent_sent_all
    parts.append("Recent automated messages sent to them:")
    for idx, msg in enumerate(recent_sent[:3]):
        category = msg.get("category", "general")
        text = str(msg.get("sent_text") or "").strip()
        timestamp = str(msg.get("sent_at") or "").strip()
        if idx == 0:
            parts.append(
                f'  - Most recently ({timestamp}): A {category} message: "{text}"'
            )
        else:
            words = text.split()
            snippet = " ".join(words[:10]) + ("..." if len(words) > 10 else "")
            parts.append(
                f'  - Previously ({timestamp}): A {category} message: "{snippet}"'
            )
    return recent_sent_all


@handle_errors("appending task reminder from recent messages", default_return=None)
def _append_task_reminder_from_messages(
    parts: list[str], recent_sent_all: list[dict[str, Any]] | None
) -> None:
    """Append task-reminder context from recent sent messages."""
    if not recent_sent_all:
        return
    task_msgs = [m for m in recent_sent_all if m.get("category") == "task_reminders"]
    if not task_msgs:
        return
    latest_task = task_msgs[0]
    text = str(latest_task.get("sent_text") or "").strip()
    timestamp = str(latest_task.get("sent_at") or "").strip()
    parts.append(f'They received a task reminder at {timestamp}: "{text}"')


@handle_errors("appending task data from AI envelope", default_return=None)
def _append_task_data_from_envelope(
    parts: list[str], structured: dict[str, Any]
) -> None:
    """Append task summary context from envelope task data."""
    tasks = structured.get("tasks") or {}
    if not tasks.get("enabled"):
        return
    stats = tasks.get("stats") or {}
    if stats.get("total_count", 0) <= 0:
        return
    active_tasks = list(tasks.get("active") or [])
    due_soon = list(tasks.get("due_soon") or [])
    parts.append("Their task information:")
    active_count = stats.get("active_count", 0)
    completed_count = stats.get("completed_count", 0)
    parts.append(
        f"  - They have {active_count} active task{'s' if active_count != 1 else ''}"
    )
    parts.append(
        f"  - They have completed {completed_count} task{'s' if completed_count != 1 else ''} total"
    )
    if due_soon:
        parts.append(
            f"  - They have {len(due_soon)} task{'s' if len(due_soon) != 1 else ''} "
            "due within the next 7 days"
        )
        for task in due_soon[:3]:
            title = task.get("title", "Untitled task")
            due_date = runtime_task_due_date(task) or ""
            priority = task.get("priority", "normal")
            due_desc = f", due on {due_date}" if due_date else ""
            priority_desc = f" ({priority} priority)" if priority != "normal" else ""
            parts.append(f'    * "{title}"{due_desc}{priority_desc}')
    if len(active_tasks) > len(due_soon[:3]):
        other_active = [t for t in active_tasks if t not in due_soon[:3]][:3]
        if other_active:
            parts.append("  - Other active tasks:")
            for task in other_active:
                parts.append(f'    * "{task.get("title", "Untitled task")}"')


@handle_errors("appending schedule details from AI envelope", default_return=None)
def _append_schedule_details_from_envelope(
    parts: list[str], structured: dict[str, Any]
) -> None:
    """Append active schedule details from envelope schedule data."""
    messages = structured.get("messages") or {}
    if not messages.get("enabled"):
        return
    schedules = structured.get("schedules") or {}
    active_schedules = schedules.get("active_schedules") or []
    schedules_data = schedules.get("raw") or {}
    if not active_schedules or not schedules_data:
        return
    parts.append("Their active schedules:")
    for schedule_name in active_schedules[:5]:
        schedule_info = None
        for category, category_data in schedules_data.items():
            if not isinstance(category_data, dict) or "periods" not in category_data:
                continue
            for period_name, period_data in category_data["periods"].items():
                if period_name == schedule_name:
                    schedule_info = {
                        "category": category,
                        "period": period_name,
                        "data": period_data,
                    }
                    break
            if schedule_info:
                break
        if schedule_info:
            period_data = schedule_info["data"]
            days = period_data.get("days", ["ALL"])
            start_time = period_data.get("start_time", "00:00")
            end_time = period_data.get("end_time", "23:59")
            days_str = ", ".join(days) if days != ["ALL"] else "every day"
            parts.append(
                f"  - {schedule_name} ({schedule_info['category']}): "
                f"{days_str} from {start_time} to {end_time}"
            )
