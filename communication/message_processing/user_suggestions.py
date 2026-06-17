# communication/message_processing/user_suggestions.py

"""Personalized user suggestions and response suggestion augmentation."""

from datetime import datetime

from core.error_handling import handle_errors
from core.time_format_constants import DATE_DISPLAY_MONTH_DAY
from core.time_utilities import (
    format_timestamp,
    now_datetime_full,
    parse_date_and_time_minute,
    parse_date_only,
    parse_timestamp_full,
)
from communication.command_handlers.shared_types import InteractionResponse, ParsedCommand


@handle_errors("getting user suggestions", default_return=[])
def get_user_suggestions(user_id: str, context: str = "") -> list:
    """Get personalized suggestions for the user."""
    suggestions: list[str] = []
    now = now_datetime_full()

    @handle_errors("adding suggestion", default_return=None)
    def add_suggestion(text: str) -> None:
        if text and text not in suggestions and len(suggestions) < 5:
            suggestions.append(text)

    try:
        from tasks import load_active_tasks
        from tasks.task_data_handlers import runtime_task_due_date, runtime_task_due_time

        tasks = load_active_tasks(user_id) or []

        @handle_errors("parsing due date", default_return=None)
        def parse_due(task: dict) -> datetime | None:
            due_date = runtime_task_due_date(task)
            due_time = runtime_task_due_time(task)
            if not due_date:
                return None
            if due_time:
                return parse_date_and_time_minute(due_date, due_time)
            return parse_date_only(due_date)

        if tasks:
            dated_tasks = [(task, parse_due(task)) for task in tasks]
            dated_tasks.sort(key=lambda item: item[1] or datetime.max)
            top_task, due_at = dated_tasks[0]
            title = top_task.get("title") or "your top task"

            if due_at:
                due_display = format_timestamp(due_at, DATE_DISPLAY_MONTH_DAY)
                if due_at.date() < now.date():
                    add_suggestion(f'Catch up on "{title}" (was due {due_display})')
                elif due_at.date() == now.date():
                    add_suggestion(f'Finish "{title}" due today')
                else:
                    add_suggestion(f'Plan for "{title}" due {due_display}')
            else:
                add_suggestion(f'Work on "{title}" from your task list')

            if len(tasks) > 1:
                add_suggestion("Show my tasks")
        else:
            add_suggestion("Add a new task for today")

    except Exception:
        add_suggestion("Show my tasks")

    try:
        from checkins.checkin_data_manager import (
            checkin_runtime_timestamp,
            get_recent_checkins,
            is_user_checkins_enabled,
        )

        if is_user_checkins_enabled(user_id):
            recent_checkins = get_recent_checkins(user_id, limit=3) or []
            if recent_checkins:
                latest = recent_checkins[0]
                timestamp_str = checkin_runtime_timestamp(latest)
                timestamp = (
                    parse_timestamp_full(timestamp_str) if timestamp_str else None
                )
                if timestamp and (now.date() - timestamp.date()).days >= 2:
                    add_suggestion("Log a quick check-in for today")
                else:
                    add_suggestion("Review your recent check-ins")
                mood = latest.get("mood")
                if mood:
                    add_suggestion(f"See your mood trend after feeling {mood.lower()}")
            else:
                add_suggestion("Start your first check-in")
    except Exception:
        add_suggestion("Start a check-in")

    try:
        from core import get_user_categories

        categories = get_user_categories(user_id)
        if categories:
            add_suggestion(f"Review your {categories[0]} schedule")
            if len(categories) > 1:
                add_suggestion("Schedule status")
    except Exception:
        add_suggestion("Show my schedule")

    try:
        from checkins.checkin_data_manager import get_recent_checkins

        checkins = get_recent_checkins(user_id, limit=5)
        if checkins and len(checkins) >= 3:
            add_suggestion("View mood trends from this week")
    except Exception:
        add_suggestion("Show my analytics")

    add_suggestion("Show my profile")
    add_suggestion("Help with tasks")

    return suggestions


@handle_errors("augmenting suggestions")
def augment_suggestions(
    parsed_command: ParsedCommand, response: InteractionResponse
) -> InteractionResponse:
    if response.completed:
        return response
    msg = (response.message or "").lower()
    suggestions: list[str] = []
    if "multiple matching tasks" in msg:
        suggestions = ["list tasks", "cancel"]
    elif "confirm delete" in msg:
        suggestions = ["confirm delete", "cancel"]
    elif "did you want to complete this task" in msg:
        suggestions = ["complete task 1", "cancel"]
    elif "what would you like to update for" in msg:
        if parsed_command.intent == "edit_schedule_period":
            suggestions = ["from 9am to 11am", "active off"]
        else:
            suggestions = ["due date tomorrow", "priority high"]
    elif (
        parsed_command.intent in ["update_task", "complete_task", "delete_task"]
        and "which task" in msg
    ):
        suggestions = ["list tasks", "cancel"]
    if suggestions:
        response.suggestions = suggestions[:2]
    return response
