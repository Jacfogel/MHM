# communication/command_handlers/task_handler.py

"""
Task management command handler.

This module handles all task-related interactions including creating,
listing, completing, deleting, updating, and getting statistics for tasks.
"""

import importlib
from datetime import datetime
from typing import Any

from core.logger import get_component_logger
from core.error_handling import handle_errors
from core.pagination import PageRequest, paginate_items
from core.time_utilities import now_datetime_full
from .base_handler import InteractionHandler, InteractionResponse, ParsedCommand
from .task_analytics_handler import TaskAnalyticsHandler
from communication.command_handlers.shared_types import PaginationAction
from communication.message_processing.flows.flow_constants import (
    TASK_DUE_DATE_SUGGESTIONS,
    TASK_PRIORITY_SUGGESTIONS,
)

from tasks.task_data_handlers import (
    runtime_task_due_date,
    runtime_task_due_time,
    runtime_task_recurrence_interval,
    runtime_task_recurrence_pattern,
)

# Lazy import: ``from tasks import task_service`` would run ``tasks/__init__.py`` at module load
# and can worsen circular-import issues during core.service bootstrap.
_task_service_mod = None


@handle_errors("loading task service module", default_return=None, re_raise=True)
def _task_service():
    """Return the cached ``tasks.task_service`` module (lazy import for circular-import safety)."""
    global _task_service_mod
    if _task_service_mod is None:
        from tasks import task_service as _ts

        _task_service_mod = _ts
    return _task_service_mod


logger = get_component_logger("communication_manager")
handlers_logger = logger
TASK_ANALYTICS_HANDLER = TaskAnalyticsHandler()

TASK_LIST_PAGE_SIZE = 10
TASK_LIST_MAX_PAGE_SIZE = 25

# Channel-neutral task help (single source for `help tasks` and handler.get_help).
TASK_HELP_TEXT = """**Task Management Help:**
Manage tasks with natural language or short commands.

**Create** (talk normally — dates/priority/tags can be in the same message):
• `i need to call the dentist this week`
• `remind me to submit forms tomorrow morning`
• `nt buy milk tonight #groceries`
• `new task urgent: fix login before Friday group:work`
• `remind me to take medication every morning at 8am` (recurring)

**List & stats:**
• `show my tasks` / `list tasks` / `/tasks`
• `task stats` / `how am I doing with my tasks this week?`

**Complete, delete, update:**
• `complete task 1` / `done Call mom`
• `delete task 2` / `delete Buy groceries`
• `update task 1 priority high due tomorrow`
• `update task 1 note insurance form is on the counter` (replace notes)
• `append note to task 1 call back before 5pm` (add to notes without replacing)

**Shortcuts:** `nt`, `ntask`, `ct`, `ctask`, `createtask` + title (same as create)

**Tags & groups:** `#health` in the message; `group:medical` or `in group:medical`

**Due phrases:** `tomorrow`, `tonight`, `this week`, `before Friday`, `after work` / `after school` (weekend `this week` means the coming week)

**Templates** (quick-add with defaults):
• `create` / `new` / `add` — Discord button menu (templates + custom task + notes)
• `task template medication` / `task template appointment`
• `create task from template phone_call Call dentist`
• `list task templates` — see all built-in templates

**After create:** If due/priority/reminders are missing, I may ask follow-up questions — use the buttons or reply with a date/time, priority, **Skip Question**, **Skip All**, **back**/**undo** (one step back), or **cancel**/**Undo Task Creation** (delete the new task).

**More:** `help tasks`, `examples tasks`, or `/tasks`"""


# not_duplicate: task_identifier_service_facade
@handle_errors("resolving task identifier", default_return="")
def _task_identifier(task: dict[str, Any]) -> str:
    """Return canonical task identifier for command routing."""
    return _task_service().task_identifier(task)


# not_duplicate: task_identifier_service_facade
@handle_errors("resolving task short identifier", default_return="")
def _task_short_identifier(task: dict[str, Any]) -> str:
    """Return canonical short_id for task matching/display."""
    return _task_service().task_short_identifier(task)


@handle_errors("advancing date by one calendar month", re_raise=True)
def _add_one_calendar_month(dt: datetime) -> datetime:
    """Advance *dt* by one calendar month, clamping the day to the target month's last day."""
    return _task_service().add_one_calendar_month(dt)

# Pending confirmations (simple in-memory store)
PENDING_DELETIONS: dict[str, str] = {}


class TaskManagementHandler(InteractionHandler):
    """Handler for task management interactions"""

    @handle_errors("checking if can handle intent")
    def can_handle(self, intent: str) -> bool:
        """Check if this handler can handle the given intent."""
        return intent in [
            "create_task",
            "create_task_from_template",
            "list_task_templates",
            "list_tasks",
            "complete_task",
            "uncomplete_task",
            "delete_task",
            "update_task",
            "append_note_to_task",
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
        elif intent == "create_task_from_template":
            return self._handle_create_task_from_template(user_id, entities)
        elif intent == "list_task_templates":
            return self._handle_list_task_templates(user_id, entities)
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
        elif intent == "append_note_to_task":
            return self._handle_append_note_to_task(user_id, entities)
        elif intent == "task_stats":
            return TASK_ANALYTICS_HANDLER.handle_task_stats(user_id, entities)
        else:
            return InteractionResponse(
                f"I don't understand that task command. Try: {', '.join(self.get_examples())}",
                True,
            )

    @handle_errors(
        "listing tasks",
        default_return=InteractionResponse(
            "I'm having trouble listing your tasks. Please try again.", True
        ),
    )
    def handle_list_tasks(
        self, user_id: str, entities: dict[str, Any]
    ) -> InteractionResponse:
        """Public entry point for /tasks (list tasks)."""
        return self._handle_list_tasks(user_id, entities)

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

        prepared = _task_service().prepare_create_task_data(
            user_id, entities, now_dt=now_datetime_full()
        )
        task_data = prepared.task_data
        valid_due_date = prepared.valid_due_date
        valid_due_time = prepared.valid_due_time
        priority = prepared.priority
        priority_was_provided = prepared.priority_was_provided
        tags = prepared.tags
        recurrence_pattern = prepared.recurrence_pattern
        recurrence_interval = prepared.recurrence_interval

        task_id = _task_service().create_task(user_id=user_id, **task_data)

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
                singular_recurrence = {
                    "daily": "day",
                    "weekly": "week",
                    "monthly": "month",
                    "yearly": "year",
                }.get(recurrence_pattern, recurrence_pattern)
                interval_text = f"every {recurrence_interval} {singular_recurrence}s"
                if recurrence_interval == 1:
                    interval_text = f"every {singular_recurrence}"
                response += f" (repeats: {interval_text})"

            conversation_manager = importlib.import_module(
                "communication.message_processing.conversation_flow_manager"
            ).conversation_manager

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
                conversation_manager.start_task_due_date_flow(
                    user_id, task_id, ask_priority=not priority_was_provided
                )
                response += "\n\nWhat would you like to add as the due date and/or time for this task?"
                return InteractionResponse(
                    response,
                    completed=False,
                    suggestions=list(TASK_DUE_DATE_SUGGESTIONS),
                )
            elif not priority_was_provided:
                logger.debug(
                    f"Task {task_id} has no explicit priority, starting priority flow"
                )
                conversation_manager.start_task_priority_flow(
                    user_id, task_id, ask_reminders=True
                )
                response += "\n\nWhat priority should this task have?"
                return InteractionResponse(
                    response,
                    completed=False,
                    suggestions=list(TASK_PRIORITY_SUGGESTIONS),
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

    @handle_errors(
        "handling task creation from template",
        default_return=InteractionResponse(
            "I'm having trouble creating that task from a template. Please try again.", True
        ),
    )
    def _handle_create_task_from_template(
        self, user_id: str, entities: dict[str, Any]
    ) -> InteractionResponse:
        """Create a task using a built-in template plus optional overrides."""
        template_ref = entities.get("template_ref") or entities.get("template_id")
        if not template_ref:
            return InteractionResponse(
                "Which template would you like? Try `list task templates`.",
                completed=False,
                suggestions=["list task templates", "task template medication"],
            )

        template = _task_service().get_builtin_task_template(str(template_ref))
        if not template:
            help_text = _task_service().get_task_templates_help_text()
            return InteractionResponse(
                f"I don't recognize template '{template_ref}'.\n\nAvailable templates:\n{help_text}",
                completed=True,
            )

        task_data = _task_service().build_task_data_from_template(
            user_id,
            template.template_id,
            title=entities.get("title"),
            description=entities.get("description"),
            due_date=entities.get("due_date"),
            due_time=entities.get("due_time"),
            priority=entities.get("priority"),
            tags=entities.get("tags"),
            group=entities.get("group"),
            now_dt=now_datetime_full(),
        )
        if not task_data:
            return InteractionResponse(
                "❌ Failed to build task from template. Please try again.", True
            )

        merged_entities: dict[str, Any] = {
            "title": task_data.get("title"),
            "description": task_data.get("description", ""),
            "priority": task_data.get("priority"),
            "tags": task_data.get("tags", []),
            "group": task_data.get("group", ""),
        }
        if task_data.get("due_date"):
            merged_entities["due_date"] = task_data["due_date"]
        if task_data.get("due_time"):
            merged_entities["due_time"] = task_data["due_time"]
        if task_data.get("recurrence_pattern"):
            merged_entities["recurrence_pattern"] = task_data["recurrence_pattern"]
            merged_entities["recurrence_interval"] = task_data.get("recurrence_interval", 1)

        return self._handle_create_task(user_id, merged_entities)

    @handle_errors(
        "listing task templates",
        default_return=InteractionResponse(
            "I'm having trouble listing task templates. Please try again.", True
        ),
    )
    def _handle_list_task_templates(
        self, user_id: str, entities: dict[str, Any]
    ) -> InteractionResponse:
        """List built-in task templates."""
        lines = [
            "**Task templates** — use `task template <name>` or `create task from template <name>`:",
            "",
            _task_service().get_task_templates_help_text(),
            "",
            "Optional title override: `task template phone_call Call dentist`",
        ]
        return InteractionResponse("\n".join(lines), completed=True)

    @handle_errors("parsing time string", default_return=None)
    def _parse_time_string(self, time_str: str) -> str | None:
        """Parse time string to HH:MM format"""
        return _task_service().parse_time_string(time_str)

    @handle_errors("defaulting due date for recurring task time", default_return=None)
    def _default_due_date_for_recurring_time(self, due_time: str) -> str | None:
        """Return today for future recurring times, otherwise tomorrow."""
        return _task_service().default_due_date_for_recurring_time(
            due_time, now_dt=now_datetime_full()
        )

    @handle_errors("parsing relative date")
    def _handle_create_task__parse_relative_date(self, date_str: str) -> str:
        """Convert relative date strings to proper dates"""
        return _task_service().parse_relative_date(date_str, now_dt=now_datetime_full())

    @handle_errors("handling task listing")
    def _handle_list_tasks(
        self, user_id: str, entities: dict[str, Any]
    ) -> InteractionResponse:
        """Handle task listing with enhanced filtering and details"""
        tasks = _task_service().load_active_tasks(user_id)

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

        page_request = PageRequest.from_values(
            limit=entities.get("limit", TASK_LIST_PAGE_SIZE),
            offset=entities.get("offset", 0),
            default_limit=TASK_LIST_PAGE_SIZE,
            max_limit=TASK_LIST_MAX_PAGE_SIZE,
        )
        page = paginate_items(sorted_tasks, page_request)

        # Format task list with enhanced details (current page only)
        task_list = self._handle_list_tasks__format_list(page.items, page.offset)

        # Build response with filter info
        filter_info = self._handle_list_tasks__build_filter_info(
            filter_type, priority_filter, tag_filter
        )
        response = self._handle_list_tasks__build_response(
            task_list, filter_info, page, sorted_tasks
        )

        # Generate contextual suggestions
        suggestions = self._handle_list_tasks__generate_suggestions(
            sorted_tasks, filter_info
        )

        # Pagination + Discord task picker (select menu on list page)
        rich_data = self._handle_list_tasks__build_list_rich_data(
            user_id,
            page,
            page.items,
            filter_type=filter_type,
            priority_filter=priority_filter,
            tag_filter=tag_filter,
        )

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
        return _task_service().filter_tasks(
            user_id,
            tasks,
            filter_type,
            priority_filter,
            tag_filter,
            now_dt=now_datetime_full(),
        )

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
        return _task_service().sort_tasks_by_priority_and_due_date(tasks)

    @handle_errors("formatting task list")
    def _handle_list_tasks__format_list(self, tasks, start_index: int = 0):
        """Format task list with enhanced details."""
        task_list = []
        priority_emoji = {
            "critical": "🔴",
            "urgent": "🔴",
            "high": "🔴",
            "medium": "🟡",
            "low": "🟢",
        }
        for i, task in enumerate(tasks, start_index + 1):
            emoji = priority_emoji.get(task.get("priority", "medium"), "🟡")

            due_info = self._handle_list_tasks__format_due_date(
                runtime_task_due_date(task),
                runtime_task_due_time(task),
            )

            # Add recurring task indicator
            recurrence_info = ""
            pattern = runtime_task_recurrence_pattern(task)
            if pattern:
                interval = runtime_task_recurrence_interval(task)
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
                f"{i}. {emoji} {task['title']}{due_info}{recurrence_info}{tags_info}{desc_info}"
            )

        return task_list

    @handle_errors("formatting due date")
    def _handle_list_tasks__format_due_date(self, due_date, due_time=None):
        """Format due date with urgency indicator and optional time."""
        return _task_service().format_due_date_status(
            due_date, now_dt=now_datetime_full(), due_time=due_time
        )

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
    def _handle_list_tasks__build_response(
        self, task_list, filter_info, page, all_tasks
    ):
        """Build the main task list response."""
        response = "**Your Active Tasks"
        if filter_info:
            response += f" ({', '.join(filter_info)})"
        response += ":**\n" + "\n".join(task_list)

        if page.has_more:
            response += f"\n... and {page.remaining_count} more tasks"

        priority_counts: dict[str, int] = {}
        for task in all_tasks:
            priority = task.get("priority", "medium")
            priority_counts[priority] = priority_counts.get(priority, 0) + 1

        if priority_counts:
            priority_str = ", ".join(
                f"{count} {priority}"
                for priority, count in sorted(priority_counts.items())
            )
            response += f"\n\n_{page.total} tasks | {priority_str}_"
        else:
            response += f"\n\n_{page.total} tasks_"

        if page.items:
            response += "\n\n_Select a task below for details and actions._"

        return response

    @handle_errors("building list rich data", default_return=None)
    def _handle_list_tasks__build_list_rich_data(
        self,
        user_id: str,
        page,
        page_tasks,
        *,
        filter_type=None,
        priority_filter=None,
        tag_filter=None,
    ):
        """Pagination metadata and Discord task-list picker payload."""
        rich_data = self._handle_list_tasks__build_pagination_rich_data(
            page,
            filter_type=filter_type,
            priority_filter=priority_filter,
            tag_filter=tag_filter,
        )
        if not page_tasks:
            return rich_data

        picker_data = {
            "interaction_view": "task_list",
            "user_id": user_id,
            "task_list_items": [
                {
                    "task_id": _task_identifier(task),
                    "short_id": _task_short_identifier(task),
                    "title": task.get("title") or "Untitled",
                }
                for task in page_tasks
            ],
        }
        if rich_data:
            return {**rich_data, **picker_data}
        return picker_data

    @handle_errors("building task list pagination metadata", default_return=None)
    def _handle_list_tasks__build_pagination_rich_data(
        self,
        page,
        *,
        filter_type=None,
        priority_filter=None,
        tag_filter=None,
    ):
        """Return channel-neutral Show More metadata when more tasks exist."""
        if not page.has_more or page.next_offset is None:
            return None

        params: dict[str, Any] = {}
        if filter_type:
            params["filter"] = filter_type
        if priority_filter:
            params["priority"] = priority_filter
        if tag_filter:
            params["tag"] = tag_filter

        return {
            "pagination_actions": [
                PaginationAction(
                    domain="tasks",
                    action="list_tasks",
                    params=params,
                    limit=page.limit,
                    offset=page.offset,
                    next_offset=page.next_offset,
                    remaining_count=page.remaining_count,
                )
            ]
        }

    @handle_errors("generating suggestions")
    def _handle_list_tasks__generate_suggestions(self, tasks, filter_info):
        """Task list uses Show More pagination only; no filter shortcut buttons."""
        del tasks, filter_info
        return []

    # not_duplicate: task_mutation_handlers
    @handle_errors("handling task completion")
    def _handle_complete_task(
        self, user_id: str, entities: dict[str, Any]
    ) -> InteractionResponse:
        """Handle task completion"""
        task_identifier = entities.get("task_identifier")
        if not task_identifier:
            # If no specific task mentioned, suggest the most likely task
            tasks = _task_service().load_active_tasks(user_id)
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
                task_id = _task_identifier(suggested_task)
                short_id = _task_short_identifier(suggested_task) or (task_id[:8] if task_id else "")

                response = "💡 **Did you want to complete this task?**\n\n"
                response += f"**{task_title}**\n"

                # Add task details
                if suggested_due := runtime_task_due_date(suggested_task):
                    response += f"📅 Due: {suggested_due}\n"
                if suggested_task.get("priority"):
                    response += f"⚡ Priority: {suggested_task['priority'].title()}\n"

                response += "\n**To complete it:**\n"
                response += f"• Reply: `complete task {short_id}`\n"
                response += f'• Or: `complete task "{task_title}"`\n'
                response += "• Or: `list tasks` to see all your tasks"

                return InteractionResponse(response, completed=False)
            else:
                return InteractionResponse(
                    "Which task would you like to complete? Please specify the task number or name, or use 'list tasks' to see all your tasks.",
                    completed=False,
                )

        # Try to find task with disambiguation
        tasks = _task_service().load_active_tasks(user_id)
        candidates = self._get_task_candidates(tasks, task_identifier)
        if len(candidates) > 1:
            preview = "\n".join(
                [f"{i + 1}. {t['title']}" for i, t in enumerate(candidates[:5])]
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
        if _task_service().complete_task(user_id, _task_identifier(task)):
            return InteractionResponse(f"✅ Completed: {task['title']}", True)
        else:
            return InteractionResponse(
                "❌ Failed to complete task. Please try again.", True
            )

    @handle_errors(
        "handling task uncomplete (restore)",
        default_return=InteractionResponse(
            "I'm having trouble restoring that task. Please try again.", True
        ),
    )
    def _handle_uncomplete_task(
        self, user_id: str, entities: dict[str, Any]
    ) -> InteractionResponse:
        """Handle uncomplete/restore: move a completed task back to active."""
        task_identifier = entities.get("task_identifier")
        if not task_identifier:
            completed_tasks = _task_service().load_completed_tasks(user_id)
            if not completed_tasks:
                return InteractionResponse(
                    "You have no completed tasks to restore.", True
                )
            return InteractionResponse(
                "Which task would you like to restore? Specify the task number or name, or use 'list tasks' to see completed ones.",
                completed=False,
            )
        completed_tasks = _task_service().load_completed_tasks(user_id)
        candidates = _task_service().get_completed_task_candidates(
            completed_tasks, task_identifier
        )
        task = candidates[0] if candidates else None
        if not task:
            return InteractionResponse(
                "❌ Completed task not found. Please check the task number or name.",
                True,
            )
        task_id = _task_identifier(task)
        if _task_service().restore_task(user_id, task_id):
            return InteractionResponse(
                f"✅ Restored to active: {task.get('title', 'Task')}", True
            )
        return InteractionResponse("❌ Failed to restore task. Please try again.", True)

    # not_duplicate: task_mutation_handlers
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
                if _task_service().delete_task(user_id, pending_id):
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
        tasks = _task_service().load_active_tasks(user_id)
        candidates = self._get_task_candidates(tasks, task_identifier)
        if len(candidates) > 1:
            preview = "\n".join(
                [f"{i + 1}. {t['title']}" for i, t in enumerate(candidates[:5])]
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
        is_exact_id = identifier_str in [_task_identifier(task).lower(), _task_short_identifier(task).lower()]
        if not is_numeric and not is_exact_id:
            # Name-based deletion requires confirmation
            PENDING_DELETIONS[user_id] = _task_identifier(task)
            title = task.get("title", "this task")
            return InteractionResponse(
                f"Confirm delete: {title}. Reply 'confirm delete' to proceed.",
                completed=False,
            )

        # Delete immediately for numeric or id-based selection
        if _task_service().delete_task(user_id, _task_identifier(task)):
            return InteractionResponse(f"🗑️ Deleted: {task['title']}", True)
        else:
            return InteractionResponse(
                "❌ Failed to delete task. Please try again.", True
            )

    # not_duplicate: task_mutation_handlers
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
        tasks = _task_service().load_active_tasks(user_id)
        candidates = self._get_task_candidates(tasks, task_identifier)
        if len(candidates) > 1:
            preview = "\n".join(
                [f"{i + 1}. {t['title']}" for i, t in enumerate(candidates[:5])]
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
            # Resolve relative dates (e.g. "tomorrow") to YYYY-MM-DD so task validation accepts them
            raw_due = entities["due_date"]
            resolved_due = self._handle_create_task__parse_relative_date(
                raw_due if isinstance(raw_due, str) else str(raw_due)
            )
            updates["due_date"] = resolved_due
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
                " title Brush your teeth tonight'\n"
                "• 'update task "
                f"{task_identifier}"
                " note Room 204, bring insurance card'\n"
                "• 'append note to task "
                f"{task_identifier}"
                " call back before 5pm'"
            )
            return InteractionResponse(prompt, completed=False, suggestions=[])

        # Update the task
        if _task_service().update_task(user_id, _task_identifier(task), updates):
            return InteractionResponse(f"✅ Updated: {task['title']}", True)
        else:
            return InteractionResponse(
                "❌ Failed to update task. Please try again.", True
            )

    @handle_errors("handling append note to task")
    def _handle_append_note_to_task(
        self, user_id: str, entities: dict[str, Any]
    ) -> InteractionResponse:
        """Append text to a task description without replacing existing notes."""
        task_identifier = entities.get("task_identifier")
        note_text = entities.get("note_text")

        if not task_identifier:
            return InteractionResponse(
                "Which task should I add a note to? Try: append note to task 1 your note here.",
                completed=False,
            )
        if not note_text:
            return InteractionResponse(
                "What note should I add? Try: append note to task 1 your note here.",
                completed=False,
            )

        tasks = _task_service().load_active_tasks(user_id)
        candidates = self._get_task_candidates(tasks, task_identifier)
        if len(candidates) > 1:
            preview = "\n".join(
                [f"{i + 1}. {t['title']}" for i, t in enumerate(candidates[:5])]
            )
            suffix = (
                "\nIf you meant one of these, reply with "
                "'append note to task <number> your note'."
            )
            return InteractionResponse(
                f"I found multiple matching tasks:\n{preview}{suffix}",
                completed=False,
            )
        task = candidates[0] if candidates else None

        if not task:
            return InteractionResponse(
                "❌ Task not found. Please check the task number or name.", True
            )

        if _task_service().append_task_description(
            user_id, _task_identifier(task), note_text
        ):
            return InteractionResponse(
                f"✅ Note added to: {task['title']}", True
            )
        return InteractionResponse(
            "❌ Failed to add note. Please try again.", True
        )


    # not_duplicate: task_identifier_service_facade
    @handle_errors("finding task by identifier")
    def _find_task_by_identifier(
        self, tasks: list[dict], identifier: str
    ) -> dict | None:
        """
        Find a task by number, name, canonical id, or short_id.

        Shared method to eliminate code duplication. Used by complete, delete, and update handlers.

        Args:
            tasks: List of task dictionaries to search
            identifier: Task identifier (number, name, id, or short_id)

        Returns:
            Task dictionary if found, None otherwise
        """
        return _task_service().find_task_by_identifier(tasks, identifier)

    @handle_errors("getting task candidates", default_return=[])
    def _get_task_candidates(self, tasks: list[dict], identifier: str) -> list[dict]:
        """Return candidate tasks matching identifier by id, number, or name."""
        return _task_service().get_task_candidates(tasks, identifier)

    @handle_errors("finding most urgent task", default_return=None)
    def _handle_complete_task__find_most_urgent_task(
        self, tasks: list[dict]
    ) -> dict | None:
        """Find the most urgent task based on priority and due date"""
        return _task_service().find_most_urgent_task(tasks)

    @handle_errors("getting help", default_return=TASK_HELP_TEXT)
    def get_help(self) -> str:
        """Get help text for task management commands."""
        return TASK_HELP_TEXT

    @handle_errors("getting examples", default_return=[])
    def get_examples(self) -> list[str]:
        """Get example commands for task management."""
        return [
            "i need to call the dentist this week",
            "remind me to submit forms tomorrow morning",
            "nt buy milk tonight #groceries",
            "create task to water plants every 2 weeks",
            "show my tasks",
            "complete task 1",
            "delete task Buy groceries",
            "update task 2 priority urgent due friday",
            "update task 1 note insurance form is on the counter",
            "append note to task 1 call back before 5pm",
            "task stats",
            "how am I doing with my tasks this week?",
            "task template medication",
            "create task from template appointment",
            "list task templates",
        ]
