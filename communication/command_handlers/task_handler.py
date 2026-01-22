# communication/command_handlers/task_handler.py

"""
Task management command handler.

This module handles all task-related interactions including creating,
listing, completing, deleting, updating, and getting statistics for tasks.
"""

from typing import Any
from datetime import datetime, timedelta
import re

from core.logger import get_component_logger
from core.error_handling import handle_errors
from core.time_utilities import (
    DATE_ONLY,
    format_timestamp,
    parse_date_only,
    now_datetime_full,
)
from tasks.task_management import (
    create_task,
    load_active_tasks,
    complete_task,
    delete_task,
    update_task,
    get_user_task_stats,
    get_tasks_due_soon,
)

from .base_handler import InteractionHandler, InteractionResponse, ParsedCommand

logger = get_component_logger("communication_manager")
handlers_logger = logger

# Pending confirmations (simple in-memory store)
PENDING_DELETIONS: dict[str, str] = {}


class TaskManagementHandler(InteractionHandler):
    """Handler for task management interactions"""

    @handle_errors("checking if can handle intent")
    def can_handle(self, intent: str) -> bool:
        """Check if this handler can handle the given intent."""
        return intent in [
            "create_task",
            "list_tasks",
            "complete_task",
            "uncomplete_task",
            "delete_task",
            "update_task",
            "task_stats",
        ]

    @handle_errors(
        "handling task management interaction",
        default_return=InteractionResponse(
            "I'm having trouble with task management right now. Please try again.", True
        ),
    )
    def handle(
        self, user_id: str, parsed_command: ParsedCommand
    ) -> InteractionResponse:
        """Handle task management interactions."""
        intent = parsed_command.intent
        entities = parsed_command.entities

        if intent == "create_task":
            return self._handle_create_task(user_id, entities)
        elif intent == "list_tasks":
            return self._handle_list_tasks(user_id, entities)
        elif intent == "complete_task":
            return self._handle_complete_task(user_id, entities)
        elif intent == "uncomplete_task":
            return self._handle_uncomplete_task(user_id, entities)
        elif intent == "delete_task":
            return self._handle_delete_task(user_id, entities)
        elif intent == "update_task":
            return self._handle_update_task(user_id, entities)
        elif intent == "task_stats":
            return self._handle_task_stats(user_id, entities)
        else:
            return InteractionResponse(
                f"I don't understand that task command. Try: {', '.join(self.get_examples())}",
                True,
            )

    @handle_errors(
        "handling task creation",
        default_return=InteractionResponse(
            "I'm having trouble creating your task. Please try again.", True
        ),
    )
    def _handle_create_task(
        self, user_id: str, entities: dict[str, Any]
    ) -> InteractionResponse:
        """Handle task creation"""
        title = entities.get("title")
        if not title:
            return InteractionResponse(
                "What would you like to name the task?",
                completed=False,
                suggestions=[
                    "Call mom",
                    "Buy groceries",
                    "Schedule dentist appointment",
                ],
            )

        # Extract other task properties
        description = entities.get("description", "")
        due_date = entities.get("due_date")
        due_time = entities.get(
            "due_time"
        )  # Extract time if present (e.g., "Friday at noon")
        priority = entities.get("priority", "medium")
        tags = entities.get("tags", [])
        recurrence_pattern = entities.get("recurrence_pattern")
        recurrence_interval = entities.get("recurrence_interval", 1)

        # If no recurrence pattern specified, check user's default settings
        if not recurrence_pattern:
            try:
                from core.user_data_handlers import get_user_data

                user_data = get_user_data(user_id, "preferences")
                preferences = user_data.get("preferences", {})
                task_settings = preferences.get("task_settings", {})
                recurring_settings = task_settings.get("recurring_settings", {})

                # Use default pattern if available
                default_pattern = recurring_settings.get("default_recurrence_pattern")
                if default_pattern:
                    recurrence_pattern = default_pattern
                    recurrence_interval = recurring_settings.get(
                        "default_recurrence_interval", 1
                    )
            except Exception as e:
                # If there's an error loading preferences, continue without defaults
                pass

        # Convert relative dates to proper dates and extract time
        valid_due_time = None
        if due_date:
            # If due_date contains time info (e.g., "Friday at noon"), parse it
            # Extract time from patterns like "next Tuesday at 11:00", "Friday at noon", "at 11:00"
            time_match = re.search(
                r"(?:next\s+)?(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday)\s+at\s+(\d{1,2}(?::\d{2})?\s*(?:am|pm)?|noon|midnight)",
                due_date.lower(),
            )
            if not time_match:
                # Also check for standalone "at [time]" pattern
                time_match = re.search(
                    r"at\s+(\d{1,2}(?::\d{2})?\s*(?:am|pm)?|noon|midnight)",
                    due_date.lower(),
                )

            if time_match:
                time_str = time_match.group(1)
                # Parse time to HH:MM format
                parsed_time = self._parse_time_string(time_str)
                if parsed_time:
                    valid_due_time = parsed_time
                # Remove time from due_date string for date parsing
                due_date = re.sub(r"\s+at\s+.*", "", due_date, flags=re.IGNORECASE)

            # Parse the date
            due_date = self._handle_create_task__parse_relative_date(due_date)

        # If due_time was extracted separately, use it
        if due_time and not valid_due_time:
            parsed_time = self._parse_time_string(due_time)
            if parsed_time:
                valid_due_time = parsed_time

        # Validate priority
        valid_priorities = ["low", "medium", "high", "urgent", "critical"]
        if priority not in valid_priorities:
            logger.warning(
                f"Invalid priority '{priority}' provided, defaulting to 'medium'"
            )
            priority = "medium"

        # Validate recurrence pattern
        valid_patterns = ["daily", "weekly", "monthly", "yearly"]
        if recurrence_pattern and recurrence_pattern not in valid_patterns:
            logger.warning(
                f"Invalid recurrence_pattern '{recurrence_pattern}' provided, ignoring"
            )
            recurrence_pattern = None  # Validate due_date format if provided (due_date was already parsed above)
        valid_due_date = None
        if (
            due_date and due_date.strip()
        ):  # Check for None, empty string, or whitespace-only
            # Strict parse (external input) via core.time_utilities
            if parse_date_only(due_date) is not None:
                valid_due_date = due_date
            else:
                # Still invalid after parsing - treat as no due date
                logger.warning(
                    f"Could not parse due_date '{due_date}' to valid date format, treating as no due date"
                )
                valid_due_date = None

        # Create the task with enhanced properties
        task_data = {
            "title": title,
            "description": description,
            "due_date": valid_due_date,
            "due_time": (
                valid_due_time if valid_due_date else None
            ),  # Only set time if we have a valid date
            "priority": priority,
            "tags": tags,
        }

        # Add recurring task fields if specified
        if recurrence_pattern:
            task_data["recurrence_pattern"] = recurrence_pattern
            task_data["recurrence_interval"] = recurrence_interval

            # Use default repeat_after_completion setting if available
            try:
                from core.user_data_handlers import get_user_data

                user_data = get_user_data(user_id, "preferences")
                preferences = user_data.get("preferences", {})
                task_settings = preferences.get("task_settings", {})
                recurring_settings = task_settings.get("recurring_settings", {})
                task_data["repeat_after_completion"] = recurring_settings.get(
                    "default_repeat_after_completion", True
                )
            except Exception as e:
                # Default to True if there's an error loading preferences
                task_data["repeat_after_completion"] = True

        task_id = create_task(user_id=user_id, **task_data)

        if task_id:
            response = f"✅ Task created: '{title}'"
            if valid_due_date:
                due_display = valid_due_date
                if valid_due_time:
                    due_display += f" at {valid_due_time}"
                response += f" (due: {due_display})"
            if priority != "medium":
                response += f" (priority: {priority})"
            if tags:
                response += f" (tags: {', '.join(tags)})"
            if recurrence_pattern:
                interval_text = f"every {recurrence_interval} {recurrence_pattern}"
                if recurrence_interval == 1:
                    interval_text = (
                        f"every {recurrence_pattern[:-2]}"  # Remove 'ly' for singular
                    )
                response += f" (repeats: {interval_text})"

            from communication.message_processing.conversation_flow_manager import (
                conversation_manager,
            )

            # If no valid due date/time, ask for it first
            # Explicitly check for None, empty string, or invalid date
            if (
                valid_due_date is None
                or not valid_due_date
                or not valid_due_date.strip()
            ):
                logger.debug(
                    f"Task {task_id} has no valid due date (valid_due_date={valid_due_date}), starting due date flow"
                )
                conversation_manager.start_task_due_date_flow(user_id, task_id)
                response += "\n\nWhat would you like to add as the due date and/or time for this task? [Skip] [Cancel]"
                return InteractionResponse(
                    response, completed=False, suggestions=["Skip", "Cancel"]
                )
            else:
                # Task has valid due date - ask about reminder periods with context-aware options
                logger.debug(
                    f"Task {task_id} has valid due date ({valid_due_date}), starting reminder flow"
                )
                conversation_manager.start_task_reminder_followup(user_id, task_id)
                reminder_suggestions = (
                    conversation_manager._generate_context_aware_reminder_suggestions(
                        user_id, task_id
                    )
                )
                response += (
                    "\n\nWould you like to set custom reminder periods for this task?"
                )
                return InteractionResponse(
                    response, completed=False, suggestions=reminder_suggestions
                )
        else:
            return InteractionResponse(
                "❌ Failed to create task. Please try again.", True
            )

    @handle_errors("parsing time string", default_return=None)
    def _parse_time_string(self, time_str: str) -> str | None:
        """Parse time string to HH:MM format"""
        import re

        time_str_lower = time_str.lower().strip()

        # Handle "noon" and "midnight"
        if time_str_lower == "noon":
            return "12:00"
        elif time_str_lower == "midnight":
            return "00:00"

        # Pattern for time like "10am", "10:30am", "2pm", "14:00"
        time_patterns = [
            r"(\d{1,2}):(\d{2})\s*(am|pm)?",  # "10:30am" or "14:30"
            r"(\d{1,2})\s*(am|pm)",  # "10am" or "2pm"
        ]

        for pattern in time_patterns:
            match = re.search(pattern, time_str_lower)
            if match:
                groups = match.groups()
                hour = int(groups[0])
                minute = (
                    int(groups[1])
                    if len(groups) > 1 and groups[1] and groups[1].isdigit()
                    else 0
                )

                # Check for AM/PM
                if len(groups) > 2 and groups[-1]:
                    am_pm = groups[-1].lower()
                    if am_pm == "pm" and hour != 12:
                        hour += 12
                    elif am_pm == "am" and hour == 12:
                        hour = 0
                elif hour < 12 and "pm" in time_str_lower:
                    hour += 12
                elif hour == 12 and "am" in time_str_lower:
                    hour = 0

                return f"{hour:02d}:{minute:02d}"

        return None

    @handle_errors("parsing relative date")
    def _handle_create_task__parse_relative_date(self, date_str: str) -> str:
        """Convert relative date strings to proper dates"""
        import re

        date_str_lower = date_str.lower().strip()

        # Internal in-memory datetime arithmetic: use canonical now + strict parse.
        now_dt = now_datetime_full()

        if date_str_lower == "today":
            return format_timestamp(now_dt, DATE_ONLY)
        elif date_str_lower == "tomorrow":
            return format_timestamp(now_dt + timedelta(days=1), DATE_ONLY)
        elif date_str_lower == "next week":
            return format_timestamp(now_dt + timedelta(days=7), DATE_ONLY)
        elif date_str_lower == "next month":
            # Simple next month calculation
            if now_dt.month == 12:
                next_month = now_dt.replace(year=now_dt.year + 1, month=1)
            else:
                next_month = now_dt.replace(month=now_dt.month + 1)
            return format_timestamp(next_month, DATE_ONLY)
        elif date_str_lower.startswith("in "):
            # Parse "in X hours", "in X days", or "in X weeks"
            hours_match = re.search(r"in\s+(\d+)\s+hours?", date_str_lower)
            if hours_match:
                hours = int(hours_match.group(1))
                target_datetime = now_dt + timedelta(hours=hours)
                return format_timestamp(target_datetime, DATE_ONLY)
            days_match = re.search(r"in\s+(\d+)\s+days?", date_str_lower)
            if days_match:
                days = int(days_match.group(1))
                return format_timestamp(now_dt + timedelta(days=days), DATE_ONLY)
            weeks_match = re.search(r"in\s+(\d+)\s+weeks?", date_str_lower)
            if weeks_match:
                weeks = int(weeks_match.group(1))
                return format_timestamp(now_dt + timedelta(weeks=weeks), DATE_ONLY)
        elif date_str_lower.startswith("next "):
            # Parse "next Tuesday", "next Monday", etc.
            days_of_week = [
                "monday",
                "tuesday",
                "wednesday",
                "thursday",
                "friday",
                "saturday",
                "sunday",
            ]
            day_match = re.search(
                r"next\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)",
                date_str_lower,
            )
            if day_match:
                day_name = day_match.group(1).lower()
                day_index = days_of_week.index(day_name)
                # Find next occurrence of this day (always next week since "next" is specified)
                days_ahead = (day_index - now_dt.weekday()) % 7
                if days_ahead == 0:  # Today is that day, use next week
                    days_ahead = 7
                else:
                    # Add 7 to get next week's occurrence (since "next" means next week, not this week)
                    days_ahead += 7
                return format_timestamp(now_dt + timedelta(days=days_ahead), DATE_ONLY)
            # If "next" doesn't match a day, try other "next" patterns
            elif "next week" in date_str_lower:
                return format_timestamp(now_dt + timedelta(days=7), DATE_ONLY)
            elif "next month" in date_str_lower:
                if now_dt.month == 12:
                    next_month = now_dt.replace(year=now_dt.year + 1, month=1)
                else:
                    next_month = now_dt.replace(month=now_dt.month + 1)
                return format_timestamp(next_month, DATE_ONLY)
        elif re.match(
            r"(monday|tuesday|wednesday|thursday|friday|saturday|sunday)",
            date_str_lower,
        ):
            # Parse day of week (e.g., "Friday", "Friday at noon") - without "next"
            days_of_week = [
                "monday",
                "tuesday",
                "wednesday",
                "thursday",
                "friday",
                "saturday",
                "sunday",
            ]
            day_match = re.search(
                r"(monday|tuesday|wednesday|thursday|friday|saturday|sunday)",
                date_str_lower,
            )
            if day_match:
                day_name = day_match.group(1).lower()
                day_index = days_of_week.index(day_name)
                # Find next occurrence of this day
                days_ahead = (day_index - now_dt.weekday()) % 7
                if days_ahead == 0:  # Today is that day, use next week
                    days_ahead = 7
                return (now_dt + timedelta(days=days_ahead)).date().isoformat()

        # Return as-is if it's already a proper date or unknown format
        return date_str

    @handle_errors("handling task listing")
    def _handle_list_tasks(
        self, user_id: str, entities: dict[str, Any]
    ) -> InteractionResponse:
        """Handle task listing with enhanced filtering and details"""
        tasks = load_active_tasks(user_id)

        if not tasks:
            return InteractionResponse(
                "You have no active tasks. Great job staying on top of things! 🎉", True
            )

        # Apply filters
        filter_type = entities.get("filter")
        priority_filter = entities.get("priority")
        tag_filter = entities.get("tag")

        # Apply filters and get filtered tasks
        filtered_tasks = self._handle_list_tasks__apply_filters(
            user_id, tasks, filter_type, priority_filter, tag_filter
        )
        if not filtered_tasks:
            return self._handle_list_tasks__no_tasks_response(
                filter_type, priority_filter, tag_filter
            )

        # Sort tasks by priority and due date
        sorted_tasks = self._handle_list_tasks__sort_tasks(filtered_tasks)

        # Format task list with enhanced details
        task_list = self._handle_list_tasks__format_list(sorted_tasks)

        # Build response with filter info
        filter_info = self._handle_list_tasks__build_filter_info(
            filter_type, priority_filter, tag_filter
        )
        response = self._handle_list_tasks__build_response(
            task_list, filter_info, len(sorted_tasks)
        )

        # Generate contextual suggestions
        suggestions = self._handle_list_tasks__generate_suggestions(
            sorted_tasks, filter_info
        )

        # Create rich data for Discord embeds
        rich_data = self._handle_list_tasks__create_rich_data(filter_info, sorted_tasks)

        return InteractionResponse(
            response,
            True,
            rich_data=rich_data,
            suggestions=suggestions if suggestions else None,
        )

    @handle_errors("applying task filters")
    def _handle_list_tasks__apply_filters(
        self, user_id, tasks, filter_type, priority_filter, tag_filter
    ):
        """Apply filters to tasks and return filtered list."""
        filtered_tasks = tasks.copy()

        # Apply filter type
        if filter_type == "due_soon":
            filtered_tasks = get_tasks_due_soon(user_id, days_ahead=7)
        elif filter_type == "overdue":
            today = format_timestamp(now_datetime_full(), DATE_ONLY)
            filtered_tasks = [
                task
                for task in filtered_tasks
                if task.get("due_date") and task["due_date"] < today
            ]
        elif filter_type == "high_priority":
            filtered_tasks = [
                task for task in filtered_tasks if task.get("priority") == "high"
            ]

        # Apply priority filter
        if priority_filter and priority_filter in ["low", "medium", "high"]:
            filtered_tasks = [
                task
                for task in filtered_tasks
                if task.get("priority") == priority_filter
            ]

        # Apply tag filter
        if tag_filter:
            filtered_tasks = [
                task for task in filtered_tasks if tag_filter in task.get("tags", [])
            ]

        return filtered_tasks

    @handle_errors("handling no tasks response")
    def _handle_list_tasks__no_tasks_response(
        self, filter_type, priority_filter, tag_filter
    ):
        """Get appropriate response when no tasks match filters."""
        if filter_type == "due_soon":
            return InteractionResponse("No tasks due in the next 7 days! 🎉", True)
        elif filter_type == "overdue":
            return InteractionResponse("No overdue tasks! 🎉", True)
        elif filter_type == "high_priority":
            return InteractionResponse("No high priority tasks! 🎉", True)
        elif priority_filter:
            return InteractionResponse(f"No {priority_filter} priority tasks! 🎉", True)
        elif tag_filter:
            return InteractionResponse(f"No tasks with tag '{tag_filter}'! 🎉", True)
        else:
            return InteractionResponse(
                "You have no active tasks. Great job staying on top of things! 🎉", True
            )

    @handle_errors("sorting tasks")
    def _handle_list_tasks__sort_tasks(self, tasks):
        """Sort tasks by priority and due date."""
        priority_order = {"high": 0, "medium": 1, "low": 2}
        return sorted(
            tasks,
            key=lambda x: (
                priority_order.get(x.get("priority", "medium"), 1),
                x.get("due_date") or "9999-12-31",  # Handle None due_date properly
            ),
        )

    @handle_errors("formatting task list")
    def _handle_list_tasks__format_list(self, tasks):
        """Format task list with enhanced details."""
        task_list = []
        for i, task in enumerate(tasks[:10], 1):  # Limit to 10 tasks
            priority_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(
                task.get("priority", "medium"), "🟡"
            )

            # Format due date with urgency indicator
            due_info = self._handle_list_tasks__format_due_date(task.get("due_date"))

            # Add recurring task indicator
            recurrence_info = ""
            if task.get("recurrence_pattern"):
                pattern = task.get("recurrence_pattern")
                interval = task.get("recurrence_interval", 1)
                if interval == 1:
                    recurrence_info = f" 🔄 {pattern[:-2]}"  # Remove 'ly' for singular
                else:
                    recurrence_info = f" 🔄 every {interval} {pattern}"

            # Add tags if present
            tags = task.get("tags", [])
            tags_info = f" [tags: {', '.join(tags)}]" if tags else ""

            # Add description preview if present
            description = task.get("description", "")
            desc_info = (
                f" - {description[:50]}..."
                if description and len(description) > 50
                else f" - {description}" if description else ""
            )

            task_list.append(
                f"{i}. {priority_emoji} {task['title']}{due_info}{recurrence_info}{tags_info}{desc_info}"
            )

        return task_list

    @handle_errors("formatting due date")
    def _handle_list_tasks__format_due_date(self, due_date):
        """Format due date with urgency indicator."""
        if not due_date:
            return ""

        today = format_timestamp(now_datetime_full(), DATE_ONLY)
        if due_date < today:
            return f" (OVERDUE: {due_date})"
        elif due_date == today:
            return f" (due TODAY: {due_date})"
        else:
            return f" (due: {due_date})"

    @handle_errors("building filter info")
    def _handle_list_tasks__build_filter_info(
        self, filter_type, priority_filter, tag_filter
    ):
        """Build filter information list."""
        filter_info = []
        if filter_type:
            filter_info.append(f"filter: {filter_type}")
        if priority_filter:
            filter_info.append(f"priority: {priority_filter}")
        if tag_filter:
            filter_info.append(f"tag: {tag_filter}")
        return filter_info

    @handle_errors("building response")
    def _handle_list_tasks__build_response(self, task_list, filter_info, total_tasks):
        """Build the main task list response."""
        response = "**Your Active Tasks"
        if filter_info:
            response += f" ({', '.join(filter_info)})"
        response += ":**\n" + "\n".join(task_list)

        if total_tasks > 10:
            response += f"\n... and {total_tasks - 10} more tasks"

        return response

    @handle_errors("generating suggestions")
    def _handle_list_tasks__generate_suggestions(self, tasks, filter_info):
        """Generate contextual suggestions based on current state."""
        suggestions = []

        # Only add suggestions if we have tasks and no filters are applied
        if not filter_info and len(tasks) > 0:
            # Add one contextual "show" suggestion if available
            contextual_suggestion = self._handle_list_tasks__get_suggestion(tasks)
            if contextual_suggestion:
                suggestions.append(contextual_suggestion)

            # Add action-oriented suggestions (only relevant to listing context)
            suggestions.append("Add a reminder to a task")
            suggestions.append("Edit a task")

        # If we don't have enough suggestions, add general ones
        while len(suggestions) < 3:
            if "Create a new task" not in suggestions:
                suggestions.append("Create a new task")
            elif "Show all tasks" not in suggestions:
                suggestions.append("Show all tasks")
            else:
                break

        # Limit to exactly 3 suggestions
        return suggestions[:3]

    @handle_errors("getting suggestion")
    def _handle_list_tasks__get_suggestion(self, tasks):
        """Get contextual show suggestion based on task analysis."""
        # Scheduler/UI state comparisons: use canonical now + strict parse.
        now_dt = now_datetime_full()

        today = format_timestamp(now_dt, DATE_ONLY)

        # Check for overdue tasks first
        overdue_count = sum(
            1 for task in tasks if task.get("due_date") and task["due_date"] < today
        )
        if overdue_count > 0:
            return f"Show {overdue_count} overdue tasks"

        # Check for high priority tasks
        high_priority_count = sum(1 for task in tasks if task.get("priority") == "high")
        if high_priority_count > 0:
            return f"Show {high_priority_count} high priority tasks"

        # Check for tasks due soon (within 3 days)
        soon_cutoff = format_timestamp(now_dt + timedelta(days=3), DATE_ONLY)
        due_soon_count = sum(
            1
            for task in tasks
            if task.get("due_date") and task["due_date"] <= soon_cutoff
        )
        if due_soon_count > 0:
            return f"Show {due_soon_count} tasks due soon"

        return None

    @handle_errors("creating rich data")
    def _handle_list_tasks__create_rich_data(self, filter_info, tasks):
        """Create rich data for Discord embeds."""
        rich_data = {"type": "task", "title": "Your Active Tasks", "fields": []}

        # Add filter info as a field if filters are applied
        if filter_info:
            rich_data["fields"].append(
                {
                    "name": "Filters Applied",
                    "value": ", ".join(filter_info),
                    "inline": True,
                }
            )

        # Add task count as a field
        rich_data["fields"].append(
            {"name": "Task Count", "value": f"{len(tasks)} tasks", "inline": True}
        )

        # Add priority breakdown as a field
        priority_counts = {}
        for task in tasks:
            priority = task.get("priority", "medium")
            priority_counts[priority] = priority_counts.get(priority, 0) + 1

        if priority_counts:
            priority_str = ", ".join(
                [f"{count} {priority}" for priority, count in priority_counts.items()]
            )
            rich_data["fields"].append(
                {"name": "Priority Breakdown", "value": priority_str, "inline": True}
            )

        return rich_data

    @handle_errors("handling task completion")
    def _handle_complete_task(
        self, user_id: str, entities: dict[str, Any]
    ) -> InteractionResponse:
        """Handle task completion"""
        task_identifier = entities.get("task_identifier")
        if not task_identifier:
            # If no specific task mentioned, suggest the most likely task
            tasks = load_active_tasks(user_id)
            if not tasks:
                return InteractionResponse(
                    "Which task would you like to complete? You currently have no active tasks. "
                    "You can create a task or list your tasks to choose one.",
                    completed=False,
                    suggestions=["list tasks", "cancel"],
                )

            # Find the most urgent task (overdue, then high priority, then due soon)
            suggested_task = self._handle_complete_task__find_most_urgent_task(tasks)

            if suggested_task:
                # Suggest the most urgent task
                task_title = suggested_task.get("title", "Unknown Task")
                task_id = suggested_task.get("task_id", "")
                short_id = task_id[:8] if task_id else ""

                response = f"💡 **Did you want to complete this task?**\n\n"
                response += f"**{task_title}**\n"

                # Add task details
                if suggested_task.get("due_date"):
                    response += f"📅 Due: {suggested_task['due_date']}\n"
                if suggested_task.get("priority"):
                    response += f"⚡ Priority: {suggested_task['priority'].title()}\n"

                response += f"\n**To complete it:**\n"
                response += f"• Reply: `complete task {short_id}`\n"
                response += f'• Or: `complete task "{task_title}"`\n'
                response += f"• Or: `list tasks` to see all your tasks"

                return InteractionResponse(response, completed=False)
            else:
                return InteractionResponse(
                    "Which task would you like to complete? Please specify the task number or name, or use 'list tasks' to see all your tasks.",
                    completed=False,
                )

        # Try to find task with disambiguation
        tasks = load_active_tasks(user_id)
        candidates = self._get_task_candidates(tasks, task_identifier)
        if len(candidates) > 1:
            preview = "\n".join(
                [f"{i+1}. {t['title']}" for i, t in enumerate(candidates[:5])]
            )
            suffix = "\nIf you meant one of these, reply with 'complete task <number>'."
            return InteractionResponse(
                f"I found multiple matching tasks:\n{preview}{suffix}", completed=False
            )
        task = candidates[0] if candidates else None

        if not task:
            return InteractionResponse(
                "❌ Task not found. Please check the task number or name.", True
            )

        # Complete the task
        if complete_task(user_id, task.get("task_id", task.get("id"))):
            return InteractionResponse(f"✅ Completed: {task['title']}", True)
        else:
            return InteractionResponse(
                "❌ Failed to complete task. Please try again.", True
            )

    @handle_errors("handling task deletion")
    def _handle_delete_task(
        self, user_id: str, entities: dict[str, Any]
    ) -> InteractionResponse:
        """Handle task deletion"""
        task_identifier = entities.get("task_identifier")
        if not task_identifier:
            # If user confirms without identifier, use pending deletion if available
            pending_id = PENDING_DELETIONS.pop(user_id, None)
            if pending_id:
                if delete_task(user_id, pending_id):
                    return InteractionResponse("🗑️ Deleted.", True)
                return InteractionResponse(
                    "❌ Failed to delete task. Please try again.", True
                )
            else:
                return InteractionResponse(
                    "Which task would you like to delete? Please specify the task number or name.",
                    completed=False,
                )

        # Try to find task with disambiguation
        tasks = load_active_tasks(user_id)
        candidates = self._get_task_candidates(tasks, task_identifier)
        if len(candidates) > 1:
            preview = "\n".join(
                [f"{i+1}. {t['title']}" for i, t in enumerate(candidates[:5])]
            )
            suffix = "\nIf you meant one of these, reply with 'delete task <number>'."
            return InteractionResponse(
                f"I found multiple matching tasks:\n{preview}{suffix}", completed=False
            )
        task = candidates[0] if candidates else None

        if not task:
            return InteractionResponse(
                "❌ Task not found. Please check the task number or name.", True
            )

        # For name-based selection, require a simple confirmation step
        # Only numeric IDs and exact task IDs allow immediate deletion
        identifier_str = str(task_identifier).strip().lower()
        is_numeric = identifier_str.isdigit()
        is_exact_id = identifier_str in [
            str(task.get("task_id", "")).lower(),
            str(task.get("id", "")).lower(),
        ]
        if not is_numeric and not is_exact_id:
            # Name-based deletion requires confirmation
            PENDING_DELETIONS[user_id] = task.get("task_id", task.get("id"))
            title = task.get("title", "this task")
            return InteractionResponse(
                f"Confirm delete: {title}. Reply 'confirm delete' to proceed.",
                completed=False,
            )

        # Delete immediately for numeric or id-based selection
        if delete_task(user_id, task.get("task_id", task.get("id"))):
            return InteractionResponse(f"🗑️ Deleted: {task['title']}", True)
        else:
            return InteractionResponse(
                "❌ Failed to delete task. Please try again.", True
            )

    @handle_errors("handling task update")
    def _handle_update_task(
        self, user_id: str, entities: dict[str, Any]
    ) -> InteractionResponse:
        """Handle task updates"""
        task_identifier = entities.get("task_identifier")
        if not task_identifier:
            return InteractionResponse(
                "Which task would you like to update? Please specify the task number or name.",
                completed=False,
            )

        # Try to find the task with disambiguation
        tasks = load_active_tasks(user_id)
        candidates = self._get_task_candidates(tasks, task_identifier)
        if len(candidates) > 1:
            preview = "\n".join(
                [f"{i+1}. {t['title']}" for i, t in enumerate(candidates[:5])]
            )
            suffix = "\nIf you meant one of these, reply with 'update task <number> due date <date>' (or other field)."
            return InteractionResponse(
                f"I found multiple matching tasks:\n{preview}{suffix}", completed=False
            )
        task = candidates[0] if candidates else None

        if not task:
            return InteractionResponse(
                "❌ Task not found. Please check the task number or name.", True
            )

        # Prepare updates
        updates = {}
        if "title" in entities:
            updates["title"] = entities["title"]
        if "description" in entities:
            updates["description"] = entities["description"]
        if "due_date" in entities:
            updates["due_date"] = entities["due_date"]
        if "priority" in entities:
            updates["priority"] = entities["priority"]

        if not updates:
            # Provide targeted, actionable prompts without generic suggestions
            prompt = (
                "What would you like to update for '"
                f"{task.get('title', 'this task')}"
                "'? You can say, for example:\n"
                "• 'update task "
                f"{task_identifier}"
                " due date tomorrow'\n"
                "• 'update task "
                f"{task_identifier}"
                " priority high'\n"
                "• 'update task "
                f"{task_identifier}"
                " title Brush your teeth tonight'"
            )
            return InteractionResponse(prompt, completed=False, suggestions=[])

        # Update the task
        if update_task(user_id, task.get("task_id", task.get("id")), updates):
            return InteractionResponse(f"✅ Updated: {task['title']}", True)
        else:
            return InteractionResponse(
                "❌ Failed to update task. Please try again.", True
            )

    @handle_errors("handling task statistics")
    def _handle_task_stats(
        self, user_id: str, entities: dict[str, Any]
    ) -> InteractionResponse:
        """Handle task statistics with dynamic time periods"""
        # Get time period information
        days = entities.get("days", 7)
        period_name = entities.get("period_name", "this week")
        offset = entities.get("offset", 0)

        try:
            from core.checkin_analytics import CheckinAnalytics

            analytics = CheckinAnalytics()

            # Get task statistics for the specified period
            task_stats = analytics.get_task_weekly_stats(user_id, days)
            if "error" in task_stats:
                return InteractionResponse(
                    f"You don't have enough check-in data for {period_name} statistics yet. Try completing some check-ins first!",
                    True,
                )

            # Get overall task stats
            overall_stats = get_user_task_stats(user_id)

            response = f"**📊 Task Statistics for {period_name.title()}:**\n\n"

            # Show habit-based task completion
            if task_stats:
                response += "**Daily Habits:**\n"
                for task_name, stats in task_stats.items():
                    completion_rate = stats.get("completion_rate", 0)
                    completed_days = stats.get("completed_days", 0)
                    total_days = stats.get("total_days", 0)

                    # Add emoji based on completion rate
                    if completion_rate >= 80:
                        emoji = "🟢"
                    elif completion_rate >= 60:
                        emoji = "🟡"
                    else:
                        emoji = "🔴"

                    response += f"{emoji} **{task_name}:** {completion_rate}% ({completed_days}/{total_days} days)\n"

                response += "\n"

            # Show overall task statistics
            active_tasks = overall_stats.get("active_tasks", 0)
            completed_tasks = overall_stats.get("completed_tasks", 0)
            total_tasks = active_tasks + completed_tasks

            if total_tasks > 0:
                overall_completion_rate = (completed_tasks / total_tasks) * 100
                response += f"**Overall Task Progress:**\n"
                response += f"📋 **Active Tasks:** {active_tasks}\n"
                response += f"✅ **Completed Tasks:** {completed_tasks}\n"
                response += f"📊 **Completion Rate:** {overall_completion_rate:.1f}%\n"
            else:
                response += "**No tasks found.** Create some tasks to get started!\n"

            return InteractionResponse(response, True)

        except Exception as e:
            logger.error(f"Error showing task statistics for user {user_id}: {e}")
            return InteractionResponse(
                "I'm having trouble showing your task statistics right now. Please try again.",
                True,
            )

    @handle_errors("finding task by identifier")
    def _find_task_by_identifier(
        self, tasks: list[dict], identifier: str
    ) -> dict | None:
        """
        Find a task by number, name, or task_id.

        Shared method to eliminate code duplication. Used by complete, delete, and update handlers.

        Args:
            tasks: List of task dictionaries to search
            identifier: Task identifier (number, name, or task_id)

        Returns:
            Task dictionary if found, None otherwise
        """
        if not identifier or not tasks:
            return None

        # Try as task_id first (UUID)
        for task in tasks:
            if task.get("task_id") == identifier or task.get("id") == identifier:
                return task

        # Try as short ID (8-character prefix)
        if isinstance(identifier, str) and len(identifier) == 8:
            for task in tasks:
                tid = task.get("task_id", "")
                if tid.startswith(identifier):
                    return task

        # Try as number
        try:
            task_num = int(identifier)
            if 1 <= task_num <= len(tasks):
                return tasks[task_num - 1]
        except ValueError:
            pass

        # Try as name with improved matching
        identifier_lower = identifier.lower().strip()

        # First try exact match
        for task in tasks:
            if identifier_lower == task["title"].lower():
                return task

        # Then try contains match
        for task in tasks:
            if identifier_lower in task["title"].lower():
                return task

        # Then try word-based matching for common task patterns
        identifier_words = set(identifier_lower.split())
        for task in tasks:
            task_words = set(task["title"].lower().split())
            # Check if any identifier words match task words
            if identifier_words & task_words:  # Set intersection
                return task

        # Finally try fuzzy matching for common variations
        common_variations = {
            "teeth": ["brush", "brushing", "tooth", "dental"],
            "hair": ["wash", "washing", "shampoo"],
            "dishes": ["wash", "washing", "clean", "cleaning"],
            "laundry": ["wash", "washing", "clothes"],
            "exercise": ["workout", "gym", "run", "running", "walk", "walking"],
            "medication": ["meds", "medicine", "pill", "pills"],
            "appointment": ["doctor", "dentist", "meeting", "call"],
        }

        for task in tasks:
            task_lower = task["title"].lower()
            for variation_key, variations in common_variations.items():
                if identifier_lower in variations or identifier_lower == variation_key:
                    if any(var in task_lower for var in variations + [variation_key]):
                        return task

        return None

    @handle_errors("finding task by identifier for completion")
    def _handle_complete_task__find_task_by_identifier(
        self, tasks: list[dict], identifier: str
    ) -> dict | None:
        """Find a task by number, name, or task_id - delegates to shared method."""
        return self._find_task_by_identifier(tasks, identifier)

    @handle_errors("finding task by identifier for deletion")
    def _handle_delete_task__find_task_by_identifier(
        self, tasks: list[dict], identifier: str
    ) -> dict | None:
        """Find a task by number, name, or task_id - delegates to shared method."""
        return self._find_task_by_identifier(tasks, identifier)

    @handle_errors("finding task by identifier for update")
    def _handle_update_task__find_task_by_identifier(
        self, tasks: list[dict], identifier: str
    ) -> dict | None:
        """Find a task by number, name, or task_id - delegates to shared method."""
        return self._find_task_by_identifier(tasks, identifier)

    @handle_errors("getting task candidates", default_return=[])
    def _get_task_candidates(self, tasks: list[dict], identifier: str) -> list[dict]:
        """Return candidate tasks matching identifier by id, number, or name."""
        matches: list[dict] = []
        # Exact id
        for t in tasks:
            if identifier == t.get("task_id") or identifier == t.get("id"):
                return [t]
        # Short id
        if isinstance(identifier, str) and len(identifier) == 8:
            for t in tasks:
                tid = t.get("task_id", "")
                if tid.startswith(identifier):
                    matches.append(t)
            if matches:
                return matches
        # Number
        try:
            n = int(identifier)
            if 1 <= n <= len(tasks):
                return [tasks[n - 1]]
        except ValueError:
            # Invalid number format - continue to name-based matching
            pass
        # Name-based
        ident = str(identifier).lower().strip()
        exact = [t for t in tasks if t.get("title", "").lower() == ident]
        if exact:
            return exact
        contains = [t for t in tasks if ident in t.get("title", "").lower()]
        if contains:
            return contains
        words = set(ident.split())
        word_hits = [
            t for t in tasks if words & set(t.get("title", "").lower().split())
        ]
        if word_hits:
            return word_hits
        return []

    @handle_errors("finding most urgent task", default_return=None)
    def _handle_complete_task__find_most_urgent_task(
        self, tasks: list[dict]
    ) -> dict | None:
        """Find the most urgent task based on priority and due date"""
        if not tasks:
            return None

        # Internal scheduler/UI state: always use canonical DATE_ONLY formatting.
        today = format_timestamp(now_datetime_full(), DATE_ONLY)

        # Priority order: overdue > critical > high > medium > low
        priority_order = {"critical": 5, "high": 4, "medium": 3, "low": 2}

        most_urgent = None
        highest_score = -1

        for task in tasks:
            score = 0

            # Check if overdue (highest priority)
            due_date = task.get("due_date")
            if due_date and due_date < today:
                score += 1000  # Overdue tasks get highest priority

            # Add priority score
            priority = task.get("priority", "medium")
            score += priority_order.get(priority, 0)
            # Add due date proximity bonus (closer = higher score)
            if due_date:
                # Persisted internal state: tasks store due_date as DATE_ONLY (YYYY-MM-DD).
                # Use strict parsing so invalid values are safely ignored.
                due_dt = parse_date_only(due_date)
                today_dt = parse_date_only(today)
                if due_dt and today_dt:
                    days_until_due = (due_dt - today_dt).days
                    if days_until_due <= 0:  # Due today or overdue
                        score += 50
                    elif days_until_due <= 1:  # Due tomorrow
                        score += 30
                    elif days_until_due <= 3:  # Due this week
                        score += 10

            if score > highest_score:
                highest_score = score
                most_urgent = task

        return most_urgent

    @handle_errors("getting help")
    def get_help(self) -> str:
        """Get help text for task management commands."""
        return "Help with task management - create, list, complete, delete, and update tasks"

    @handle_errors("getting examples")
    def get_examples(self) -> list[str]:
        """Get example commands for task management."""
        return [
            "create task 'Call mom tomorrow'",
            "list tasks",
            "complete task 1",
            "delete task 'Buy groceries'",
            "update task 2 priority high",
            "task stats",
        ]
