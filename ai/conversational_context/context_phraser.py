# ai/conversational_context/context_phraser.py

"""
Format computed context facts into natural-language prompt sections.

Analytics and aggregation live in ``ai.context_builder`` (``analyze_context``).
This module only phrases those facts for comprehensive conversational prompts.
"""

from datetime import date
from typing import Any

from ai.context_builder import ContextAnalysis, ContextData, get_context_builder
from core import get_user_data
from core.error_handling import handle_errors
from core.logger import get_component_logger
from messages.message_data_manager import get_recent_messages
from checkins.checkin_data_manager import (
    checkin_runtime_timestamp,
    get_recent_checkins,
    is_user_checkins_enabled,
)
from messages.message_data_manager import (
    is_automated_messages_enabled,
)
from core.time_utilities import TIME_ONLY_MINUTE, format_timestamp, parse_timestamp_full
from tasks import are_tasks_enabled, get_tasks_due_soon, get_user_task_stats, load_active_tasks
from tasks.task_data_handlers import runtime_task_due_date

logger = get_component_logger("ai")

_FEATURE_STATUS_UNKNOWN = (
    "IMPORTANT - Feature availability: check-ins status unknown, "
    "task management status unknown, automated messages status unknown"
)


@handle_errors("phrasing check-in summary", default_return="")
def phrase_checkin_summary(
    analysis: ContextAnalysis,
    recent_checkins: list[dict[str, Any]],
) -> str:
    """Turn ``ContextAnalysis`` check-in metrics into natural-language summary text."""
    total_entries = analysis.total_entries or len(recent_checkins)
    if total_entries <= 0:
        return "They have not completed any check-ins yet."

    summary_lines = [f"Over the last {total_entries} check-ins:"]
    if analysis.avg_mood is not None:
        summary_lines.append(
            f"Their average mood has been {analysis.avg_mood:.1f} out of 5"
        )
    if analysis.avg_energy is not None:
        summary_lines.append(
            f"Their average energy level has been {analysis.avg_energy:.1f} out of 5"
        )
    summary_lines.append(
        f"They ate breakfast {analysis.breakfast_count} out of {total_entries} times "
        f"({analysis.breakfast_rate:.0f}% of the time)"
    )
    summary_lines.append(
        f"They brushed their teeth {analysis.teeth_brushed_count} out of {total_entries} times "
        f"({analysis.teeth_brushing_rate:.0f}% of the time)"
    )

    if recent_checkins[:3]:
        summary_lines.append("Most recent check-ins:")
        for i, entry in enumerate(recent_checkins[:3]):
            entry_desc = []
            if entry.get("mood") is not None:
                entry_desc.append(f"mood was {entry['mood']} out of 5")
            if entry.get("energy") is not None:
                entry_desc.append(f"energy was {entry['energy']} out of 5")
            if entry.get("ate_breakfast") is not None:
                entry_desc.append(
                    f"{'ate' if entry['ate_breakfast'] else 'did not eat'} breakfast"
                )
            if entry.get("brushed_teeth") is not None:
                entry_desc.append(
                    f"{'brushed' if entry['brushed_teeth'] else 'did not brush'} teeth"
                )
            if entry_desc:
                summary_lines.append(f"  - Check-in {i + 1}: {', '.join(entry_desc)}")

    return "\n".join(summary_lines)


@handle_errors("appending profile context sections", default_return=None)
def append_profile_sections(parts: list[str], context: dict[str, Any]) -> None:
    """Profile, neurodivergent context, and goals from get_ai_context."""
    profile = context.get("user_profile", {})
    if profile.get("preferred_name"):
        parts.append(f"The user's preferred name is {profile['preferred_name']}")
    if profile.get("active_categories"):
        parts.append(f"Their interests include: {', '.join(profile['active_categories'])}")

    user_context_data = context.get("user_context", {})
    if not user_context_data:
        return

    health_conditions = user_context_data.get("custom_fields", {}).get(
        "health_conditions", []
    )
    if health_conditions:
        parts.append(
            f"They have been diagnosed with or are managing: {', '.join(health_conditions)}"
        )

    notes_for_ai = user_context_data.get("notes_for_ai", [])
    if notes_for_ai:
        parts.append(f"Important notes about them: {'; '.join(notes_for_ai)}")

    encouraging_activities = user_context_data.get("activities_for_encouragement", [])
    if encouraging_activities:
        parts.append(
            f"Activities that encourage them include: {', '.join(encouraging_activities)}"
        )

    goals = user_context_data.get("goals", [])
    if goals:
        parts.append(f"Their goals include: {', '.join(goals)}")


@handle_errors("reading feature enablement flags", default_return=None)
def _feature_status_lines(user_id: str) -> list[str] | None:
    checkins_enabled = is_user_checkins_enabled(user_id)
    tasks_enabled = are_tasks_enabled(user_id) if user_id else False
    messages_enabled = is_automated_messages_enabled(user_id) if user_id else False

    feature_status: list[str] = []
    if checkins_enabled:
        feature_status.append("check-ins are enabled")
    else:
        feature_status.append(
            "check-ins are disabled - do NOT mention check-ins, check-in data, "
            "or suggest starting check-ins"
        )

    if tasks_enabled:
        feature_status.append("task management is enabled")
    else:
        feature_status.append(
            "task management is disabled - do NOT mention tasks, task creation, "
            "or task reminders"
        )

    if messages_enabled:
        feature_status.append("automated messages are enabled")
    else:
        feature_status.append(
            "automated messages are disabled - do NOT mention scheduled message "
            "categories, suggest enabling automated messages, or reference recent "
            "automated sends"
        )
    return feature_status


@handle_errors("appending feature enablement context", default_return=None)
def append_feature_enablement(parts: list[str], user_id: str) -> None:
    """Tell the model which product features are enabled for this user."""
    feature_status = _feature_status_lines(user_id)
    if feature_status is None:
        parts.append(_FEATURE_STATUS_UNKNOWN)
        return
    if feature_status:
        parts.append(f"IMPORTANT - Feature availability: {'; '.join(feature_status)}")


@handle_errors("appending check-in summary context", default_return=None)
def append_checkin_summary(parts: list[str], user_id: str) -> None:
    """Recent check-in analytics phrased from ``ContextBuilder.analyze_context``."""
    if not is_user_checkins_enabled(user_id):
        return

    recent_checkins = get_recent_checkins(user_id, limit=10)
    if not recent_checkins:
        parts.append("They have not completed any check-ins yet.")
        return

    analysis = get_context_builder().analyze_context(
        ContextData(recent_checkins=recent_checkins)
    )
    parts.append(phrase_checkin_summary(analysis, recent_checkins))


@handle_errors("appending activity and mood trend context", default_return=None)
def append_activity_and_mood_trends(
    parts: list[str], user_id: str, context: dict[str, Any]
) -> None:
    """Recent activity counts and mood trend summary from get_ai_context."""
    if not is_user_checkins_enabled(user_id):
        return

    recent_activity = context.get("recent_activity", {})
    if recent_activity.get("recent_responses_count", 0) > 0:
        count = recent_activity["recent_responses_count"]
        parts.append(
            f"They have completed {count} check-in{'s' if count != 1 else ''} recently"
        )

    mood_trends = context.get("mood_trends", {})
    if mood_trends.get("average_mood") is not None:
        avg_mood = mood_trends["average_mood"]
        trend = mood_trends.get("trend", "stable")
        trend_desc = {
            "improving": "improving",
            "declining": "declining",
            "stable": "staying stable",
        }.get(trend, trend)
        parts.append(
            f"Their mood has been averaging {avg_mood:.1f} out of 5 and is {trend_desc}"
        )


@handle_errors("appending conversation history context", default_return=None)
def append_conversation_history(parts: list[str], context: dict[str, Any]) -> None:
    conversation_history = context.get("conversation_history", [])
    if not conversation_history:
        return

    parts.append("In recent conversations, they've talked about:")
    for exchange in conversation_history[-3:]:
        user_msg = exchange.get("user_message", "")[:80]
        if user_msg:
            full_msg = exchange.get("user_message", "")
            suffix = "..." if len(full_msg) > 80 else ""
            parts.append(f"  - {user_msg}{suffix}")


@handle_errors("parsing today's check-in timestamp", default_return=(False, ""))
def _checkin_completed_today(ts: str) -> tuple[bool, str]:
    dt = parse_timestamp_full(ts)
    if dt is not None and dt.date() == date.today():
        return True, format_timestamp(dt, TIME_ONLY_MINUTE)
    return False, ""


@handle_errors("appending today check-in status context", default_return=None)
def append_today_checkin_status(parts: list[str], user_id: str) -> None:
    if not is_user_checkins_enabled(user_id):
        return

    recent_checkins = get_recent_checkins(user_id, limit=1)
    completed_today = False
    completed_at = ""
    mood_val = None
    energy_val = None

    if recent_checkins:
        ts = checkin_runtime_timestamp(recent_checkins[0])
        mood_val = recent_checkins[0].get("mood")
        energy_val = recent_checkins[0].get("energy")
        if ts:
            completed_today, completed_at = _checkin_completed_today(ts)

    if completed_today:
        details = []
        if mood_val is not None:
            details.append(f"mood was {mood_val} out of 5")
        if energy_val is not None:
            details.append(f"energy was {energy_val} out of 5")
        if details:
            parts.append(
                f"They completed their check-in today at {completed_at}, "
                f"reporting that their {' and '.join(details)}"
            )
        else:
            parts.append(f"They completed their check-in today at {completed_at}")
    else:
        parts.append("They have not completed their check-in for today yet")


@handle_errors("appending recent sent messages context", default_return=None)
def append_recent_sent_messages(
    parts: list[str], user_id: str
) -> list[dict[str, Any]] | None:
    """Return full recent_sent list for task-reminder follow-up."""
    if not is_automated_messages_enabled(user_id):
        return None

    recent_sent_all = get_recent_messages(user_id, category=None, limit=5)
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
            snippet = " ".join(words[:10]) + ("…" if len(words) > 10 else "")
            parts.append(
                f'  - Previously ({timestamp}): A {category} message: "{snippet}"'
            )
    return recent_sent_all


@handle_errors("appending task reminder context", default_return=None)
def append_task_reminder(parts: list[str], recent_sent_all: list[dict[str, Any]] | None) -> None:
    if not recent_sent_all:
        return
    task_msgs = [m for m in recent_sent_all if m.get("category") == "task_reminders"]
    if not task_msgs:
        return
    latest_task = task_msgs[0]
    t_text = str(latest_task.get("sent_text") or "").strip()
    t_ts = str(latest_task.get("sent_at") or "").strip()
    parts.append(f'They received a task reminder at {t_ts}: "{t_text}"')


@handle_errors("appending task data context", default_return=None)
def append_task_data(parts: list[str], user_id: str) -> None:
    if not are_tasks_enabled(user_id):
        return

    active_tasks = load_active_tasks(user_id)
    task_stats = get_user_task_stats(user_id)
    tasks_due_soon = get_tasks_due_soon(user_id, days_ahead=7)

    if task_stats.get("total_count", 0) <= 0:
        return

    parts.append("Their task information:")
    active_count = task_stats.get("active_count", 0)
    completed_count = task_stats.get("completed_count", 0)
    parts.append(
        f"  - They have {active_count} active task{'s' if active_count != 1 else ''}"
    )
    parts.append(
        f"  - They have completed {completed_count} task{'s' if completed_count != 1 else ''} total"
    )

    if tasks_due_soon:
        parts.append(
            f"  - They have {len(tasks_due_soon)} task{'s' if len(tasks_due_soon) != 1 else ''} "
            "due within the next 7 days"
        )
        for task in tasks_due_soon[:3]:
            title = task.get("title", "Untitled task")
            due_date = runtime_task_due_date(task) or ""
            priority = task.get("priority", "normal")
            due_desc = f", due on {due_date}" if due_date else ""
            priority_desc = f" ({priority} priority)" if priority != "normal" else ""
            parts.append(f'    * "{title}"{due_desc}{priority_desc}')

    if len(active_tasks) > len(tasks_due_soon[:3]):
        other_active = [t for t in active_tasks if t not in tasks_due_soon[:3]][:3]
        if other_active:
            parts.append("  - Other active tasks:")
            for task in other_active:
                parts.append(f'    * "{task.get("title", "Untitled task")}"')


@handle_errors("appending schedule details context", default_return=None)
def append_schedule_details(parts: list[str], user_id: str, context: dict[str, Any]) -> None:
    if not is_automated_messages_enabled(user_id):
        return

    profile = context.get("user_profile", {})
    active_schedules = profile.get("active_schedules", [])
    if not active_schedules:
        return

    schedules_data = get_user_data(
        user_id, "schedules", normalize_on_read=True
    ).get("schedules", {})
    if not schedules_data:
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
