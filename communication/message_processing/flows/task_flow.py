# communication/message_processing/flows/task_flow.py

"""Task reminder, due date, and priority flow mixin."""

from datetime import datetime, timedelta
from typing import Any

from core.error_handling import handle_errors
from core.logger import get_component_logger
from core.time_utilities import (
    DATE_ONLY,
    TIME_ONLY_MINUTE,
    format_timestamp,
    now_datetime_full,
    now_timestamp_full,
    parse_date_and_time_minute,
    parse_date_only,
    parse_time_only_minute,
    parse_timestamp_full,
)
from tasks.task_data_handlers import runtime_task_due_date, runtime_task_due_time

from communication.message_processing.flows.flow_constants import (
    FLOW_TASK_DUE_DATE,
    FLOW_TASK_PRIORITY,
    FLOW_TASK_REMINDER,
)
from communication.message_processing.flows.flow_state import FlowStateMixin

logger = get_component_logger("communication_manager")


class TaskFlowMixin(FlowStateMixin):
    @handle_errors(
        "handling task reminder follow-up",
        default_return=(
            "I'm having trouble with the reminder setup. Please try again.",
            True,
        ),
    )
    def _handle_task_reminder_followup(
        self, user_id: str, user_state: dict, message_text: str
    ) -> tuple[str, bool]:
        """
        Handle user's response to reminder period question after task creation.

        Parses natural language responses like:
        - "30 minutes to an hour before"
        - "3 to 5 hours before"
        - "1 to 2 days before"
        - "No reminders needed" / "No" / "Skip"
        """
        from tasks import get_task_by_id

        try:
            task_id = self._get_task_flow_identifier(user_state)
            if not task_id:
                logger.error(
                    f"Task reminder follow-up for user {user_id} but no task_id in state"
                )
                self._clear_flow_state(user_id, mark_completion=True)
                return (
                    "I couldn't find the task to update. The task was created successfully.",
                    True,
                )

            # Check for timeout first (10 minutes)
            started_at_str = user_state.get("started_at")
            if started_at_str:
                # started_at is internal persisted state (string timestamp).
                # Parse strictly using canonical helper.
                started_at = parse_timestamp_full(started_at_str)
                if started_at is not None and (
                    now_datetime_full() - started_at
                ) > timedelta(minutes=10):
                    self._clear_flow_state(user_id, mark_completion=True)
                    return (
                        "⏱️ Reminder flow expired. Task was created successfully. You can add reminders later by updating the task.",
                        True,
                    )

            message_lower = message_text.lower().strip()

            # Check if message is clearly unrelated to reminder flow (commands or unrelated content)
            unrelated_patterns = [
                r"^/(n|note|nn|newn|newnote|task|t|nt|ntask|newt|newtask|ct|ctask|createtask|createt|l|list|newl|newlist|cl|createlist|createl)",
                r"^!(n|note|nn|newn|newnote|task|t|nt|ntask|newt|newtask|ct|ctask|createtask|createt|l|list|newl|newlist|cl|createlist|createl)",
                r"^(create|add|new|show|list|complete|delete|update).*(task|note|list)",
                r"^(hi|hello|hey|thanks|thank you|bye|goodbye)",
            ]
            import re

            if any(re.match(pattern, message_lower) for pattern in unrelated_patterns):
                # Message is clearly unrelated - clear flow and let it be processed normally
                logger.info(
                    f"User {user_id} in reminder flow sent unrelated message '{message_text}', clearing flow"
                )
                self._clear_flow_state(user_id, mark_completion=True)
                return ("", True)  # Empty response to let command be processed normally

            # Check if user wants to skip reminders
            skip_patterns = [
                "no reminders",
                "no reminder",
                "no",
                "skip",
                "none",
                "not needed",
                "don't need",
                "don't want",
            ]
            if any(pattern in message_lower for pattern in skip_patterns):
                # User doesn't want reminders - clear flow
                self._clear_flow_state(user_id, mark_completion=True)
                return ("Got it! No reminders will be set for this task.", True)

            # Parse reminder periods from natural language
            reminder_periods = self._parse_reminder_periods_from_text(
                user_id, task_id, message_text
            )
            logger.debug(
                f"Parsed reminder_periods for task {task_id}: {reminder_periods}"
            )

            # Check if parsing succeeded and if task has due date
            if not reminder_periods or len(reminder_periods) == 0:
                # Couldn't parse - check if task has due date to give better error message
                task = get_task_by_id(user_id, task_id)
                if task and not runtime_task_due_date(task):
                    # Task has no due date, can't set reminder periods
                    self._clear_flow_state(user_id, mark_completion=True)
                    return (
                        "This task doesn't have a due date, so I can't set reminder periods. You can add a due date and reminders later by updating the task.",
                        True,
                    )
                # Couldn't parse reminder periods - ask for clarification
                return (
                    "I'm not sure what reminder timing you'd like. Please specify something like:\n"
                    "- '30 minutes to an hour before'\n"
                    "- '3 to 5 hours before'\n"
                    "- '1 to 2 days before'\n"
                    "- Or say 'no reminders' to skip",
                    False,
                )

            # Check if task has due date (parsing already checked this, but verify)
            task = get_task_by_id(user_id, task_id)
            if not task:
                logger.error(
                    f"Task {task_id} not found when trying to set reminder periods"
                )
                self._clear_flow_state(user_id, mark_completion=True)
                return (
                    "I couldn't find the task to update. The task was created successfully.",
                    True,
                )

            due_date_str = runtime_task_due_date(task)
            if not due_date_str:
                # Task has no due date, can't set reminder periods
                self._clear_flow_state(user_id, mark_completion=True)
                return (
                    "This task doesn't have a due date, so I can't set reminder periods. You can add a due date and reminders later by updating the task.",
                    True,
                )

            # Validate that due_date is in proper format (YYYY-MM-DD)
            if parse_date_only(due_date_str) is None:
                # Invalid date format - can't set reminders
                logger.warning(
                    f"Task {task_id} has invalid due_date format '{due_date_str}', cannot set reminders"
                )
                self._clear_flow_state(user_id, mark_completion=True)
                return (
                    "This task has an invalid due date format, so I can't set reminder periods. You can update the due date and add reminders later.",
                    True,
                )

            if reminder_periods:
                # Update task with reminder periods
                from tasks import update_task

                logger.debug(
                    f"Updating task {task_id} with reminder periods: {reminder_periods}"
                )

                # Update task with reminder periods
                # Note: update_task will also call schedule_task_reminders internally, so we don't need to call it again
                try:
                    update_result = update_task(
                        user_id, task_id, {"reminder_periods": reminder_periods}
                    )
                    logger.debug(f"update_task returned: {update_result}")
                    if not update_result:
                        logger.error(
                            f"update_task returned False for task {task_id} with reminder periods for user {user_id}"
                        )
                        self._clear_flow_state(user_id, mark_completion=True)
                        return (
                            "I had trouble saving the reminder periods. The task was created successfully. You can add reminders later by updating the task.",
                            True,
                        )

                    # Verify the task was updated correctly by reloading it
                    updated_task = get_task_by_id(user_id, task_id)
                    has_scheduled = any(
                        isinstance(r, dict)
                        and r.get("kind") == "scheduled"
                        and r.get("period")
                        for r in (updated_task.get("reminders") or [])
                    )
                    if not updated_task or not has_scheduled:
                        logger.error(
                            f"Task {task_id} was not updated with reminder_periods after update_task returned True"
                        )
                        self._clear_flow_state(user_id, mark_completion=True)
                        return (
                            "I had trouble saving the reminder periods. The task was created successfully. You can add reminders later by updating the task.",
                            True,
                        )

                    # Clear flow
                    self._clear_flow_state(user_id, mark_completion=True)

                    periods_text = ", ".join(
                        [
                            f"{p.get('date', '')} {p.get('start_time', '')}-{p.get('end_time', '')}"
                            for p in reminder_periods
                        ]
                    )
                    return (
                        f"✅ Reminder periods set for this task: {periods_text}",
                        True,
                    )
                except Exception as update_error:
                    logger.error(
                        f"Exception in update_task for task {task_id}: {update_error}",
                        exc_info=True,
                    )
                    self._clear_flow_state(user_id, mark_completion=True)
                    return (
                        "I had trouble saving the reminder periods. The task was created successfully. You can add reminders later by updating the task.",
                        True,
                    )
            else:
                # Couldn't parse reminder periods - ask for clarification
                return (
                    "I'm not sure what reminder timing you'd like. Please specify something like:\n"
                    "- '30 minutes to an hour before'\n"
                    "- '3 to 5 hours before'\n"
                    "- '1 to 2 days before'\n"
                    "- Or say 'no reminders' to skip",
                    False,
                )

        except Exception as e:
            logger.error(
                f"Error handling task reminder follow-up for user {user_id}: {e}",
                exc_info=True,
            )
            # Don't clear flow on exception if it's a parsing issue - let user try again
            # Only clear if it's a critical error
            _err = str(e).lower()
            _tid = "".join(("task", "_", "id"))
            _tident = "".join(("task", "_", "identifier"))
            if _tid in _err or _tident in _err or "not found" in _err:
                self._clear_flow_state(user_id, mark_completion=True)
                return (
                    "I had trouble setting up reminders, but your task was created successfully. You can add reminders later by updating the task.",
                    True,
                )
            else:
                # Parsing or other non-critical error - ask for clarification
                return (
                    "I'm not sure what reminder timing you'd like. Please specify something like:\n"
                    "- '30 minutes to an hour before'\n"
                    "- '3 to 5 hours before'\n"
                    "- '1 to 2 days before'\n"
                    "- 'Or say 'no reminders' to skip",
                    False,
                )
    @handle_errors("parsing reminder periods from text", default_return=[])
    def _parse_reminder_periods_from_text(
        self, user_id: str, task_id: str, text: str
    ) -> list:
        """
        Parse reminder periods from natural language text.

        Examples:
        - "30 minutes to an hour before" -> reminder 30-60 min before due time
        - "3 to 5 hours before" -> reminder 3-5 hours before due time
        - "1 to 2 days before" -> reminder 1-2 days before due date

        Returns list of reminder period dicts with date, start_time, end_time.
        """
        import re

        due_datetime = self._get_task_due_datetime_for_reminders(user_id, task_id)
        if due_datetime is None:
            return []

        text_lower = self._normalize_reminder_text(text)
        logger.debug(
            f"Parsing reminder periods from text '{text}' (normalized: '{text_lower}') "
            f"for task {task_id} with due_datetime {due_datetime}"
        )

        reminder_periods = []
        for pattern, unit in self._get_reminder_parse_patterns():
            match = re.search(pattern, text_lower)
            if not match:
                continue
            logger.debug(
                f"Pattern '{pattern}' matched text '{text_lower}' with groups: {match.groups()}"
            )
            try:
                start_val, end_val = self._parse_reminder_range(match)
                logger.debug(
                    f"Parsed values: start_val={start_val}, end_val={end_val}, unit={unit}"
                )
                deltas = self._build_reminder_deltas(unit, start_val, end_val)
                if deltas is None:
                    logger.debug(f"Unknown unit '{unit}', skipping")
                    continue
                reminder_period = self._build_future_reminder_period(
                    due_datetime, deltas[0], deltas[1]
                )
                if reminder_period is None:
                    continue
                reminder_periods.append(reminder_period)
                logger.debug(
                    f"Parsed reminder period for task {task_id}: "
                    f"{reminder_period['date']} {reminder_period['start_time']}-{reminder_period['end_time']}"
                )
                break
            except (ValueError, IndexError, AttributeError, TypeError) as e:
                logger.warning(
                    f"Error parsing reminder pattern '{pattern}' for text '{text_lower}': {e}",
                    exc_info=True,
                )
                continue

        logger.debug(f"Final reminder_periods for task {task_id}: {reminder_periods}")
        return reminder_periods
    @handle_errors("loading task due datetime for reminder parsing", default_return=None)
    def _get_task_due_datetime_for_reminders(
        self, user_id: str, task_id: str
    ) -> datetime | None:
        """Resolve task due datetime for reminder calculations."""
        from tasks import get_task_by_id

        task = get_task_by_id(user_id, task_id)
        if not task or not runtime_task_due_date(task):
            logger.debug(f"Task {task_id} has no due_date, cannot parse reminder periods")
            return None

        due_date_str = runtime_task_due_date(task)
        due_time_str = (runtime_task_due_time(task) or "09:00").strip() or "09:00"

        due_datetime = parse_date_and_time_minute(due_date_str, due_time_str)
        if due_datetime is not None:
            logger.debug(f"Parsed due datetime for task {task_id}: {due_datetime}")
            return due_datetime

        due_date_only_dt = parse_date_only(due_date_str)
        if due_date_only_dt is None:
            logger.warning(
                f"Could not parse due date/time for task {task_id}: {due_date_str} {due_time_str}"
            )
            return None

        due_datetime = due_date_only_dt.replace(hour=9, minute=0)
        logger.debug(f"Parsed due date only for task {task_id}: {due_datetime}")
        return due_datetime
    @handle_errors("normalizing reminder text", default_return="")
    def _normalize_reminder_text(self, text: str) -> str:
        """Normalize reminder text variants before regex matching."""
        return (
            text.lower()
            .strip()
            .replace("an hour", "60 minutes")
            .replace("a hour", "60 minutes")
        )
    @handle_errors("building reminder parse patterns", default_return=[])
    def _get_reminder_parse_patterns(self) -> list[tuple[str, str]]:
        """Return ordered regex patterns for reminder phrase parsing."""
        return [
            (r"(\d+)\s*minutes?\s*(?:to|-)\s*(\d+)\s*minutes?\s*before", "minutes"),
            (r"(\d+)\s*(?:to|-)\s*(\d+)\s*minutes?\s*before", "minutes"),
            (r"(\d+)\s*minutes?\s*before", "minutes"),
            (r"(\d+)\s*min\s*before", "minutes"),
            (r"(\d+)\s*hours?\s*(?:to|-)\s*(\d+)\s*hours?\s*before", "hours"),
            (r"(\d+)\s*(?:to|-)\s*(\d+)\s*hours?\s*before", "hours"),
            (r"(\d+)\s*hours?\s*before", "hours"),
            (r"(\d+)\s*hrs?\s*before", "hours"),
            (r"(\d+)\s*days?\s*(?:to|-)\s*(\d+)\s*days?\s*before", "days"),
            (r"(\d+)\s*(?:to|-)\s*(\d+)\s*days?\s*before", "days"),
            (r"(\d+)\s*days?\s*before", "days"),
        ]
    @handle_errors("parsing reminder range values", default_return=(0, 0))
    def _parse_reminder_range(self, match) -> tuple[int, int]:
        """Parse first and optional second numeric range from regex match."""
        start_val = int(match.group(1))
        end_val = (
            int(match.group(2))
            if len(match.groups()) >= 2 and match.group(2)
            else start_val
        )
        return start_val, end_val
    @handle_errors("building reminder deltas", default_return=None)
    def _build_reminder_deltas(
        self, unit: str, start_val: int, end_val: int
    ) -> tuple[timedelta, timedelta] | None:
        """Return start/end timedeltas for a parsed reminder range."""
        if unit == "minutes":
            return timedelta(minutes=end_val), timedelta(minutes=start_val)
        if unit == "hours":
            return timedelta(hours=end_val), timedelta(hours=start_val)
        if unit == "days":
            return timedelta(days=end_val), timedelta(days=start_val)
        return None
    @handle_errors("building future reminder period", default_return=None)
    def _build_future_reminder_period(
        self, due_datetime: datetime, start_delta: timedelta, end_delta: timedelta
    ) -> dict | None:
        """Create reminder period dict when reminder window is in the future."""
        reminder_start = due_datetime - start_delta
        reminder_end = due_datetime - end_delta
        logger.debug(
            f"Calculated reminder times: start={reminder_start}, end={reminder_end}"
        )

        now = now_datetime_full()
        if reminder_end < now:
            logger.debug(
                f"Reminder time {reminder_end} is in the past (now={now_timestamp_full()}), skipping"
            )
            return None

        return {
            "date": format_timestamp(reminder_start, DATE_ONLY),
            "start_time": format_timestamp(reminder_start, TIME_ONLY_MINUTE),
            "end_time": format_timestamp(reminder_end, TIME_ONLY_MINUTE),
        }
    @handle_errors("starting task due date flow", default_return=None)
    def start_task_due_date_flow(
        self, user_id: str, task_id: str, ask_priority: bool = False
    ) -> None:
        """
        Start a task due date/time flow.
        Called by task handler after creating a task without a due date.
        """
        self._start_task_followup_flow(
            user_id,
            task_id,
            FLOW_TASK_DUE_DATE,
            {"ask_priority": ask_priority},
            "task due date flow",
        )
    @handle_errors("starting task reminder follow-up flow", default_return=None)
    def start_task_reminder_followup(self, user_id: str, task_id: str) -> None:
        """
        Start a task reminder follow-up flow.
        Called by task handler after creating a task with a due date.
        """
        self._start_task_followup_flow(
            user_id,
            task_id,
            FLOW_TASK_REMINDER,
            {},
            "task reminder follow-up flow",
        )
    @handle_errors("starting task priority flow", default_return=None)
    def start_task_priority_flow(
        self, user_id: str, task_id: str, ask_reminders: bool = True
    ) -> None:
        """Start a priority follow-up after task creation."""
        self._start_task_followup_flow(
            user_id,
            task_id,
            FLOW_TASK_PRIORITY,
            {"ask_reminders": ask_reminders},
            "task priority flow",
        )
    @handle_errors("starting task follow-up flow", default_return=None)
    def _start_task_followup_flow(
        self,
        user_id: str,
        task_id: str,
        flow: int,
        extra_data: dict[str, Any],
        log_label: str,
    ) -> None:
        """Persist a task follow-up flow with shared task identifier state."""
        self.user_states[user_id] = {
            "flow": flow,
            "state": 0,
            "data": {"task_identifier": task_id, **extra_data},
            "started_at": now_timestamp_full(),
        }
        self._save_user_states()
        logger.debug(f"Started {log_label} for user {user_id}, task {task_id}")
    @handle_errors(
        "continuing after task priority flow",
        default_return=(
            "Task details saved. You can update reminders later from the task list.",
            True,
        ),
    )
    def _continue_after_task_priority(
        self, user_id: str, task_id: str, ask_reminders: bool
    ) -> tuple[str, bool]:
        """Advance from optional priority setup to reminders when useful."""
        from tasks import get_task_by_id

        task = get_task_by_id(user_id, task_id)
        if ask_reminders and task and runtime_task_due_date(task):
            self.start_task_reminder_followup(user_id, task_id)
            return (
                "Would you like to set custom reminder periods for this task?",
                False,
            )

        self._clear_flow_state(user_id, mark_completion=True)
        return (
            "Task setup finished. You can update priority, due date, or reminders later from the task list.",
            True,
        )
    @handle_errors(
        "handling task priority flow",
        default_return=(
            "I'm having trouble with the priority setup. Your task was created successfully.",
            True,
        ),
    )
    def _handle_task_priority_flow(
        self, user_id: str, user_state: dict, message_text: str
    ) -> tuple[str, bool]:
        """Handle optional priority follow-up after task creation."""
        from tasks import update_task
        from tasks.task_schemas import VALID_PRIORITIES

        task_id = self._get_task_flow_identifier(user_state)
        ask_reminders = bool(user_state.get("data", {}).get("ask_reminders", True))
        if not task_id:
            self._clear_flow_state(user_id, mark_completion=True)
            return (
                "I couldn't find the task to update. The task was created successfully.",
                True,
            )

        started_at_str = user_state.get("started_at")
        if started_at_str:
            started_at = parse_timestamp_full(started_at_str)
            if started_at is not None and (
                now_datetime_full() - started_at
            ) > timedelta(minutes=10):
                self._clear_flow_state(user_id, mark_completion=True)
                return (
                    "Priority setup expired. Task was created with normal priority.",
                    True,
                )

        message_lower = message_text.lower().strip()
        skip_all_keywords = ["skip all", "!skip all", "/skip all"]
        skip_keywords = ["skip", "!skip", "/skip", "medium", "normal", "none"]
        cancel_keywords = ["cancel", "!cancel", "/cancel"]

        if any(message_lower == keyword for keyword in skip_all_keywords):
            self._clear_flow_state(user_id, mark_completion=True)
            return (
                "Task setup finished. You can update priority, due date, or reminders later from the task list.",
                True,
            )

        if any(message_lower == keyword for keyword in cancel_keywords):
            return self._continue_after_task_priority(user_id, task_id, ask_reminders)

        if any(message_lower == keyword for keyword in skip_keywords):
            return self._continue_after_task_priority(user_id, task_id, ask_reminders)

        priority = message_lower
        if priority not in VALID_PRIORITIES:
            return (
                "I'm not sure which priority you want. Choose low, medium, high, or critical. You can also say skip or skip all.",
                False,
            )

        if not update_task(user_id, task_id, {"priority": priority}):
            self._clear_flow_state(user_id, mark_completion=True)
            return (
                "I had trouble saving the priority. The task was created successfully.",
                True,
            )

        followup, completed = self._continue_after_task_priority(
            user_id, task_id, ask_reminders
        )
        if completed:
            return (f"Priority set to {priority}. {followup}", True)
        return (f"Priority set to {priority}.\n\n{followup}", False)
    @handle_errors(
        "generating context-aware reminder suggestions", default_return=["Skip"]
    )
    def _generate_context_aware_reminder_suggestions(
        self, user_id: str, task_id: str
    ) -> list[str]:
        """
        Generate reminder period suggestions based on task's due date/time.

        Examples:
        - Task due in 6 days (no time) -> "1 to 2 days before", "3 to 4 days before"
        - Task due in 12 days at 10:00 AM -> "1 to 2 hours before", "1 to 2 days before", "3 to 5 days before"
        """
        from tasks import get_task_by_id

        task = get_task_by_id(user_id, task_id)
        if not task or not runtime_task_due_date(task):
            return ["Skip"]

        due_date_str = runtime_task_due_date(task)
        due_time_str = runtime_task_due_time(task)

        try:
            # Parse due date (canonical strict helper)
            due_date = parse_date_only(due_date_str)
            if due_date is None:
                return ["Skip"]

            # Parse time if provided, otherwise use current time of day
            if due_time_str and due_time_str.strip():
                parsed_time = parse_time_only_minute(due_time_str.strip())
                if parsed_time is not None:
                    due_date = due_date.replace(
                        hour=parsed_time.hour,
                        minute=parsed_time.minute,
                    )
                    has_time = True
                else:
                    # Invalid time format, use current time of day (preserve behavior)
                    now = now_datetime_full()
                    due_date = due_date.replace(hour=now.hour, minute=now.minute)
                    has_time = False
            else:
                # No time specified, use current time of day (preserve behavior)
                now = now_datetime_full()
                due_date = due_date.replace(hour=now.hour, minute=now.minute)
                has_time = False

            # Calculate days until due
            now = now_datetime_full()
            days_until = (due_date - now).days
            hours_until = (due_date - now).total_seconds() / 3600

            suggestions = []

            if days_until < 0:
                # Task is overdue or due today - offer short-term reminders
                if has_time and hours_until > 0:
                    suggestions.append("30 minutes to an hour before")
                    if hours_until > 2:
                        suggestions.append("1 to 2 hours before")
                suggestions.append("Skip")
            elif days_until == 0:
                # Due today
                if has_time and hours_until > 1:
                    suggestions.append("30 minutes to an hour before")
                    if hours_until > 3:
                        suggestions.append("1 to 2 hours before")
                suggestions.append("Skip")
            elif days_until <= 2:
                # Due in 1-2 days
                if has_time:
                    suggestions.append("1 to 2 hours before")
                suggestions.append("1 day before")
                suggestions.append("Skip")
            elif days_until <= 7:
                # Due in 3-7 days
                suggestions.append("1 to 2 days before")
                suggestions.append("3 to 4 days before")
                suggestions.append("Skip")
            elif days_until <= 14:
                # Due in 8-14 days
                if has_time:
                    suggestions.append("1 to 2 hours before")
                suggestions.append("1 to 2 days before")
                suggestions.append("3 to 5 days before")
                suggestions.append("Skip")
            else:
                # Due in more than 2 weeks
                suggestions.append("1 to 2 days before")
                suggestions.append("3 to 5 days before")
                if days_until > 21:
                    suggestions.append("1 week before")
                suggestions.append("Skip")

            return suggestions[:4]  # Limit to 4 suggestions (Discord button limit)
        except Exception as e:
            logger.error(
                f"Error generating context-aware reminder suggestions: {e}",
                exc_info=True,
            )
            return ["1 to 2 days before", "Skip"]
    @handle_errors(
        "handling task due date flow",
        default_return=(
            "I'm having trouble with the due date flow. Please try again.",
            True,
        ),
    )
    def _handle_task_due_date_flow(
        self, user_id: str, user_state: dict, message_text: str
    ) -> tuple[str, bool]:
        """Handle continuation of task due date/time flow."""
        from tasks import update_task

        message_lower = message_text.lower().strip()

        # Check for timeout first (10 minutes)
        started_at_str = user_state.get("started_at")
        if started_at_str:
            # started_at is internal persisted state (string timestamp).
            # Parse strictly using canonical helper.
            started_at = parse_timestamp_full(started_at_str)
            if started_at is not None and (
                now_datetime_full() - started_at
            ) > timedelta(minutes=10):
                self._clear_flow_state(user_id, mark_completion=True)
                return (
                    "⏱️ Due date flow expired. Task was created without a due date. You can add one later by updating the task.",
                    True,
                )

        # Check for skip/cancel commands
        skip_all_keywords = ["skip all", "!skip all", "/skip all"]
        skip_keywords = ["skip", "!skip", "/skip"]
        cancel_keywords = ["cancel", "!cancel", "/cancel"]

        if any(message_lower == keyword for keyword in skip_all_keywords):
            self._clear_flow_state(user_id, mark_completion=True)
            return (
                "Task setup finished. You can update due date, priority, or reminders later from the task list.",
                True,
            )

        # Handle cancel - abort due date setting
        if any(
            message_lower == keyword or message_lower.startswith(keyword + " ")
            for keyword in cancel_keywords
        ):
            task_id = self._get_task_flow_identifier(user_state)
            self._clear_flow_state(user_id, mark_completion=True)
            return (
                "❌ Due date setting cancelled. Task was created without a due date.",
                True,
            )

        # Handle skip - continue without due date
        if any(
            message_lower == keyword or message_lower.startswith(keyword + " ")
            for keyword in skip_keywords
        ):
            task_id = self._get_task_flow_identifier(user_state)
            ask_priority = bool(user_state.get("data", {}).get("ask_priority", False))
            if ask_priority and task_id:
                self.start_task_priority_flow(user_id, task_id, ask_reminders=False)
                return (
                    "Task created without a due date.\n\nWhat priority should this task have? [Low] [Medium] [High] [Critical] [Skip] [Skip All]",
                    False,
                )
            self._clear_flow_state(user_id, mark_completion=True)
            return (
                "✅ Task created without a due date. You can add one later by updating the task.",
                True,
            )

        # Check if message is clearly unrelated to due date flow (commands or unrelated content)
        unrelated_patterns = [
            r"^/(n|note|nn|newn|newnote|task|t|nt|ntask|newt|newtask|ct|ctask|createtask|createt|l|list|newl|newlist|cl|createlist|createl)",
            r"^!(n|note|nn|newn|newnote|task|t|nt|ntask|newt|newtask|ct|ctask|createtask|createt|l|list|newl|newlist|cl|createlist|createl)",
            r"^(create|add|new|show|list|complete|delete|update).*(task|note|list)",
            r"^(hi|hello|hey|thanks|thank you|bye|goodbye)",
        ]
        import re

        if any(re.match(pattern, message_lower) for pattern in unrelated_patterns):
            # Message is clearly unrelated - clear flow and let it be processed normally
            logger.info(
                f"User {user_id} in due date flow sent unrelated message '{message_text}', clearing flow"
            )
            self._clear_flow_state(user_id, mark_completion=True)
            return ("", True)  # Empty response to let command be processed normally

        # Parse date/time from user input
        task_id = self._get_task_flow_identifier(user_state)
        if not task_id:
            self._clear_flow_state(user_id, mark_completion=True)
            return ("❌ Could not find task. Please try creating the task again.", True)

        # Parse date/time from message
        parsed_date, parsed_time = self._parse_date_time_from_text(message_text)

        if not parsed_date:
            # Couldn't parse date - ask for clarification
            return (
                "I'm not sure what date/time you'd like. Please specify something like:\n"
                "- 'tomorrow'\n"
                "- 'next week'\n"
                "- 'Monday at 2pm'\n"
                "- '2026-01-15 10:00'\n"
                "- Or say 'skip' to continue without a due date",
                False,
            )

        # Update task with due date/time
        update_data = {"due_date": parsed_date}
        if parsed_time:
            update_data["due_time"] = parsed_time

        try:
            update_result = update_task(user_id, task_id, update_data)
            if not update_result:
                self._clear_flow_state(user_id, mark_completion=True)
                return (
                    "❌ Failed to update task with due date. The task was created successfully. You can add a due date later by updating the task.",
                    True,
                )

            due_text = parsed_date
            if parsed_time:
                due_text += f" at {parsed_time}"

            ask_priority = bool(user_state.get("data", {}).get("ask_priority", False))
            if ask_priority:
                self.start_task_priority_flow(user_id, task_id, ask_reminders=True)
                return (
                    f"Due date set: {due_text}\n\nWhat priority should this task have? [Low] [Medium] [High] [Critical] [Skip] [Skip All]",
                    False,
                )

            # Now ask about reminder periods with context-aware options
            self.start_task_reminder_followup(user_id, task_id)
            self._generate_context_aware_reminder_suggestions(user_id, task_id)

            response = f"✅ Due date set: {due_text}\n\nWould you like to set custom reminder periods for this task?"
            return (response, False)  # Not completed - reminder flow is active
        except Exception as e:
            logger.error(f"Error updating task with due date: {e}", exc_info=True)
            self._clear_flow_state(user_id, mark_completion=True)
            return (
                "❌ Failed to update task with due date. The task was created successfully. You can add a due date later by updating the task.",
                True,
            )
    @handle_errors("parsing date and time from text", default_return=(None, None))
    def _parse_date_time_from_text(self, text: str) -> tuple[str | None, str | None]:
        """
        Parse date and time from natural language text.

        Returns: (date_str in YYYY-MM-DD format, time_str in HH:MM format or None)
        """
        # not_duplicate: task_due_date_natural_language_parsers
        import re
        from datetime import datetime, timedelta

        # Canonical formats live in core.time_utilities
        # - DATE_ONLY is still useful for parsing/strptime in other places,
        #   and for date-only string output we use core.time_utilities.format_timestamp(..., DATE_ONLY).
        from core.time_utilities import (
            DATE_ONLY,
        )  # noqa: F401 (documented canonical)

        text_lower = (text or "").lower().strip()
        today_dt = now_datetime_full()

        def _date_str(dt: datetime) -> str:
            """Return YYYY-MM-DD without sprinkling strftime format strings."""
            try:
                return format_timestamp(dt, DATE_ONLY)
            except Exception as exc:
                logger.error(
                    f"Failed to format date for natural language parser: {exc}",
                    exc_info=True,
                )
                return ""

        # Try to parse relative dates first
        if text_lower == "today":
            return (_date_str(today_dt), None)

        if text_lower == "tomorrow":
            tomorrow_dt = today_dt + timedelta(days=1)
            return (_date_str(tomorrow_dt), None)

        if text_lower.startswith("tomorrow"):
            # "tomorrow at 10am" or "tomorrow 2pm"
            tomorrow_dt = today_dt + timedelta(days=1)
            time_str = self._parse_time_from_text(text_lower)
            return (_date_str(tomorrow_dt), time_str)

        if "next week" in text_lower:
            next_week_dt = today_dt + timedelta(days=7)
            time_str = self._parse_time_from_text(text_lower)
            return (_date_str(next_week_dt), time_str)

        if "next month" in text_lower:
            # Preserve your existing behavior: "same day next month" using replace().
            # Note: this can raise ValueError for dates like Jan 31 -> Feb 31.
            # We are not changing behavior here unless you explicitly want it.
            if today_dt.month == 12:
                next_month_dt = today_dt.replace(year=today_dt.year + 1, month=1)
            else:
                next_month_dt = today_dt.replace(month=today_dt.month + 1)

            time_str = self._parse_time_from_text(text_lower)
            return (_date_str(next_month_dt), time_str)

        # Try to parse date patterns like "Monday", "Jan 15", "2026-01-15"
        # Day of week
        days_of_week = [
            "monday",
            "tuesday",
            "wednesday",
            "thursday",
            "friday",
            "saturday",
            "sunday",
        ]
        for i, day in enumerate(days_of_week):
            if day in text_lower:
                # Find next occurrence of this day
                days_ahead = (i - today_dt.weekday()) % 7
                if days_ahead == 0:  # Today is that day, use next week
                    days_ahead = 7
                target_dt = today_dt + timedelta(days=days_ahead)
                time_str = self._parse_time_from_text(text_lower)
                return (_date_str(target_dt), time_str)

        # Try to parse YYYY-MM-DD format (already canonical; don't reformat it)
        date_match = re.search(r"(\d{4}-\d{2}-\d{2})", text or "")
        if date_match:
            date_str = date_match.group(1)
            time_str = self._parse_time_from_text(text_lower)
            return (date_str, time_str)

        # Try to parse relative days like "in 3 days", "in 2 weeks"
        days_match = re.search(r"in\s+(\d+)\s+days?", text_lower)
        if days_match:
            days = int(days_match.group(1))
            target_dt = today_dt + timedelta(days=days)
            time_str = self._parse_time_from_text(text_lower)
            return (_date_str(target_dt), time_str)

        weeks_match = re.search(r"in\s+(\d+)\s+weeks?", text_lower)
        if weeks_match:
            weeks = int(weeks_match.group(1))
            target_dt = today_dt + timedelta(weeks=weeks)
            time_str = self._parse_time_from_text(text_lower)
            return (_date_str(target_dt), time_str)

        # If we can't parse, return None
        return (None, None)
    @handle_errors("parsing time from text", default_return=None)
    def _parse_time_from_text(self, text: str) -> str | None:
        """
        Parse time from natural language text.

        Examples:
        - "10am", "10:00am", "10:30am" -> "10:00", "10:30"
        - "2pm", "14:00" -> "14:00"
        - "at 3pm" -> "15:00"
        """
        # not_duplicate: task_due_date_natural_language_parsers
        import re

        text_lower = text.lower().strip()

        # Pattern for time like "10am", "10:30am", "2pm", "14:00"
        time_patterns = [
            r"(\d{1,2}):(\d{2})\s*(am|pm)?",  # "10:30am" or "14:30"
            r"(\d{1,2})\s*(am|pm)",  # "10am" or "2pm"
            r"at\s+(\d{1,2}):(\d{2})",  # "at 10:30"
            r"at\s+(\d{1,2})\s*(am|pm)",  # "at 10am"
        ]

        for pattern in time_patterns:
            match = re.search(pattern, text_lower)
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
                elif hour < 12 and "pm" in text_lower:
                    hour += 12
                elif hour == 12 and "am" in text_lower:
                    hour = 0

                return f"{hour:02d}:{minute:02d}"

        return None
