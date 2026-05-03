# Orphaned scheduled task-reminder cleanup (schedule library job scan).

from __future__ import annotations

import schedule
import random
import time
from datetime import datetime, timedelta
from typing import Any

import pytz

from core.error_handling import handle_errors
from core.logger import get_component_logger
from core.time_utilities import (
    TIME_ONLY_MINUTE,
    format_timestamp,
    now_datetime_full,
    parse_date_only,
    parse_time_only_minute,
    parse_timestamp_minute,
)
from tasks.task_data_handlers import runtime_task_is_completed

logger = get_component_logger("scheduler")


@handle_errors("handling task reminder")
def handle_task_reminder(
    scheduler_manager: Any,
    user_id: str,
    task_identifier: str,
    retry_attempts: int = 3,
    retry_delay: int = 30,
) -> None:
    """
    Send a task reminder with retries through the scheduler communication manager.

    ``task_identifier`` is the task record's canonical ``id`` or another value
    accepted by ``tasks.get_task_by_id``.
    """
    if scheduler_manager.communication_manager is None:
        logger.error("Communication manager is not initialized.")
        return

    attempt = 0
    while attempt < retry_attempts:
        try:
            from tasks import get_task_by_id, update_task

            task = get_task_by_id(user_id, task_identifier)
            if not task:
                logger.error(f"Task {task_identifier} not found for user {user_id}")
                return

            if runtime_task_is_completed(task):
                logger.info(
                    f"Task {task_identifier} is already completed, skipping reminder"
                )
                return

            scheduler_manager.communication_manager.handle_task_reminder(
                user_id, task_identifier
            )
            update_task(user_id, task_identifier, {"reminder_sent": True})

            logger.info(
                f"Task reminder sent successfully for user {user_id}, task {task_identifier}"
            )
            return

        except Exception as e:
            logger.error(
                f"Error sending task reminder for user {user_id}, task {task_identifier}: {e}"
            )
            attempt += 1
            logger.info(
                f"Retrying in {retry_delay} seconds... ({attempt}/{retry_attempts})"
            )
            time.sleep(retry_delay)


@handle_errors("scheduling all task reminders")
def schedule_all_task_reminders(scheduler_manager: Any, user_id: str) -> None:
    """
    Schedule one active task reminder per configured task reminder period.

    For each active period, one incomplete task is selected with weighted
    priority/due-date logic and scheduled at a random time within that period.
    """
    try:
        from core.schedule_runtime import get_schedule_time_periods
        from tasks import are_tasks_enabled, load_active_tasks

        if not are_tasks_enabled(user_id):
            logger.debug(f"Tasks not enabled for user {user_id}")
            return

        task_periods = get_schedule_time_periods(user_id, "tasks")
        if not task_periods:
            logger.debug(f"No task reminder periods configured for user {user_id}")
            return

        active_tasks = load_active_tasks(user_id)
        incomplete_tasks = [
            task for task in active_tasks if not runtime_task_is_completed(task)
        ]

        if not incomplete_tasks:
            logger.debug(f"No incomplete tasks found for user {user_id}")
            return

        scheduled_count = 0

        for period_name, period_data in task_periods.items():
            if not period_data.get("active", True):
                continue

            selected_task = scheduler_manager.select_task_for_reminder(
                incomplete_tasks
            )
            if not selected_task:
                logger.debug(
                    f"No task selected for period {period_name} for user {user_id}"
                )
                continue

            start_time = period_data.get("start_time")
            end_time = period_data.get("end_time")
            if not start_time or not end_time:
                logger.warning(
                    f"Missing start/end time for task reminder period '{period_name}' in user {user_id}"
                )
                continue

            random_time = scheduler_manager.get_random_time_within_task_period(
                start_time, end_time
            )
            if not random_time:
                logger.warning(
                    f"Could not generate random time for period {start_time}-{end_time}"
                )
                continue

            selected_task_id = str(selected_task.get("id") or "").strip()
            if not selected_task_id:
                logger.warning(
                    f"Skipping task reminder for user {user_id}: selected task missing canonical id"
                )
                continue

            if scheduler_manager.schedule_task_reminder_at_time(
                user_id, selected_task_id, random_time
            ):
                scheduled_count += 1
                logger.info(
                    f"Scheduled reminder for task '{selected_task['title']}' at {random_time} (period: {period_name} {start_time}-{end_time})"
                )

        logger.info(f"Scheduled {scheduled_count} task reminders for user {user_id}")

    except Exception as e:
        logger.error(f"Error scheduling task reminders for user {user_id}: {e}")


@handle_errors("selecting task for reminder with priority and due date weighting")
def handle_task_selection_edge_cases(incomplete_tasks: list[dict[str, Any]]) -> Any:
    """Handle trivial task-selection cases before weighted selection."""
    if not incomplete_tasks:
        return None
    if len(incomplete_tasks) == 1:
        return incomplete_tasks[0]
    return "PROCEED"


@handle_errors("calculating priority weight for task reminder")
def calculate_priority_weight(task: dict[str, Any]) -> float:
    """Calculate priority-based reminder selection weight for a task."""
    priority = task.get("priority", "medium").lower()
    priority_multipliers = {
        "critical": 3.0,
        "high": 2.0,
        "medium": 1.5,
        "low": 1.0,
        "none": 0.8,
    }
    return priority_multipliers.get(priority, 1.0)


@handle_errors(
    "calculating due date weight for reminder selection",
    default_return=1.0,
    user_friendly=False,
)
def calculate_due_date_weight(task: dict[str, Any], today) -> float:
    """Calculate due-date proximity reminder selection weight for a task."""
    from tasks.task_data_handlers import runtime_task_due_date

    due_date_str = runtime_task_due_date(task)
    if not due_date_str:
        return 0.9

    due_date_dt = parse_date_only(due_date_str)
    if due_date_dt is None:
        return 1.0

    due_date = due_date_dt.date()
    days_until_due = (due_date - today).days

    if days_until_due < 0:
        days_overdue = abs(days_until_due)
        return min(2.5 + (days_overdue * 0.1), 4.0)
    if days_until_due == 0:
        return 2.5
    if days_until_due <= 7:
        return max(2.5 - (days_until_due * 0.2), 1.0)
    if days_until_due <= 30:
        return max(1.0 - (days_until_due - 7) * 0.01, 0.8)
    return 0.8


@handle_errors("calculating task weights for reminder selection")
def calculate_task_weights(incomplete_tasks: list[dict[str, Any]], today) -> list:
    """Calculate combined priority and due-date weights for reminder candidates."""
    task_weights = []
    for task in incomplete_tasks:
        weight = 1.0
        weight *= calculate_priority_weight(task)
        weight *= calculate_due_date_weight(task, today)
        task_weights.append((task, weight))
    return task_weights


@handle_errors("building task key for reminder selection", default_return="")
def task_selection_key(task: dict[str, Any], index: int) -> str:
    """Build a stable key for tracking reminder selection state."""
    candidate_keys = [
        str(task.get("id") or "").strip(),
        str(task.get("short_id") or "").strip(),
        str(task.get("uuid") or "").strip(),
        str(task.get("title") or "").strip(),
    ]
    base_key = next((key for key in candidate_keys if key), f"idx-{index}")
    return f"{base_key}|{index}"


@handle_errors("selecting task by weight for reminder", default_return=None)
def select_task_by_weight(
    scheduler_manager: Any,
    task_weights: list,
    incomplete_tasks: list[dict[str, Any]],
) -> dict[str, Any] | None:
    """Select a reminder candidate using weighted random selection."""
    if not task_weights:
        return random.choice(incomplete_tasks) if incomplete_tasks else None

    total_weight = sum(weight for _, weight in task_weights)
    if total_weight <= 0:
        return random.choice(incomplete_tasks)

    rand_value = random.uniform(0, total_weight)
    cumulative_weight = 0.0

    active_keys = {
        task_selection_key(task, index)
        for index, (task, _) in enumerate(task_weights)
    }
    selection_state = scheduler_manager._reminder_selection_state
    for key in list(selection_state.keys()):
        if key not in active_keys:
            selection_state.pop(key, None)

    for index, (task, weight) in enumerate(task_weights):
        cumulative_weight += weight
        if rand_value <= cumulative_weight:
            task_key = task_selection_key(task, index)
            previous_score = selection_state.get(task_key, 0.0)
            selection_state[task_key] = previous_score + weight
            return task

    return task_weights[-1][0] if task_weights else random.choice(incomplete_tasks)


@handle_errors("selecting task for reminder", default_return=None)
def select_task_for_reminder(
    scheduler_manager: Any, incomplete_tasks: list[dict[str, Any]]
) -> dict[str, Any] | None:
    """Select a task for reminder using priority and due-date weighting."""
    edge_case_result = handle_task_selection_edge_cases(incomplete_tasks)
    if edge_case_result != "PROCEED":
        return edge_case_result

    today = now_datetime_full().date()
    task_weights = calculate_task_weights(incomplete_tasks, today)
    selected_task = select_task_by_weight(
        scheduler_manager, task_weights, incomplete_tasks
    )

    from tasks.task_data_handlers import runtime_task_due_date

    logger.debug(
        f"Selected task '{selected_task.get('title', 'Unknown')}' with priority '{selected_task.get('priority', 'medium')}' and due date '{runtime_task_due_date(selected_task) or 'None'}'"
    )
    return selected_task


@handle_errors("getting random time within task period")
def get_random_time_within_task_period(start_time: str, end_time: str) -> str | None:
    """Generate a random HH:MM time within a task reminder period."""
    try:
        start_dt = parse_time_only_minute(start_time)
        end_dt = parse_time_only_minute(end_time)
        if start_dt is None or end_dt is None:
            logger.error(f"Invalid time range: {start_time} to {end_time}")
            return None

        if end_dt < start_dt:
            end_dt += timedelta(days=1)

        total_seconds = (end_dt - start_dt).total_seconds()
        if total_seconds <= 0:
            logger.error(f"Invalid time range: {start_time} to {end_time}")
            return None

        random_seconds = random.randint(0, int(total_seconds))
        random_dt = start_dt + timedelta(seconds=random_seconds)
        random_time = format_timestamp(random_dt, TIME_ONLY_MINUTE)
        logger.debug(
            f"Generated random time {random_time} within period {start_time}-{end_time}"
        )
        return random_time

    except Exception as e:
        logger.error(
            f"Error generating random time within period {start_time}-{end_time}: {e}"
        )
        return None


@handle_errors("scheduling task reminder at specific time")
def schedule_task_reminder_at_time(
    scheduler_manager: Any, user_id: str, task_identifier: str, reminder_time: str
) -> bool:
    """Schedule a daily reminder for one task at an HH:MM time."""
    try:
        from tasks import get_task_by_id

        task = get_task_by_id(user_id, task_identifier)
        if not task:
            logger.error(f"Task {task_identifier} not found for user {user_id}")
            return False

        if runtime_task_is_completed(task):
            logger.info(
                f"Task {task_identifier} is already completed, skipping reminder scheduling"
            )
            return False

        try:
            hour, minute = map(int, reminder_time.split(":"))
            time_str = f"{hour:02d}:{minute:02d}"
        except ValueError:
            logger.error(f"Invalid reminder time format: {reminder_time}")
            return False

        schedule.every().day.at(time_str).do(
            scheduler_manager.handle_task_reminder,
            user_id=user_id,
            task_identifier=task_identifier,
        )

        tz = pytz.timezone("America/Regina")
        now = tz.localize(now_datetime_full())
        today = now.date()
        hour, minute = map(int, time_str.split(":"))
        schedule_time_obj = datetime.min.time().replace(hour=hour, minute=minute)
        schedule_datetime = tz.localize(datetime.combine(today, schedule_time_obj))
        if schedule_datetime <= now:
            schedule_datetime += timedelta(days=1)

        scheduler_manager.set_wake_timer(
            schedule_datetime, user_id, "tasks", "task_reminder"
        )

        logger.info(
            f"Scheduled daily task reminder for user {user_id}, task {task_identifier} at {time_str}"
        )
        return True

    except Exception as e:
        logger.error(
            f"Error scheduling task reminder for user {user_id}, task {task_identifier}: {e}"
        )
        return False


@handle_errors("scheduling task reminder at specific datetime")
def schedule_task_reminder_at_datetime(
    scheduler_manager: Any,
    user_id: str,
    task_identifier: str,
    date_str: str,
    time_str: str,
) -> bool:
    """Schedule a one-time reminder for one task at a specific date and time."""
    try:
        from tasks import get_task_by_id

        task = get_task_by_id(user_id, task_identifier)
        if not task:
            logger.error(f"Task {task_identifier} not found for user {user_id}")
            return False

        if runtime_task_is_completed(task):
            logger.info(
                f"Task {task_identifier} is already completed, skipping reminder scheduling"
            )
            return False

        reminder_datetime = parse_timestamp_minute(f"{date_str} {time_str}")
        if reminder_datetime is None:
            logger.error(f"Invalid date/time format: {date_str} {time_str}")
            return False

        if reminder_datetime < now_datetime_full():
            logger.debug(f"Reminder time {reminder_datetime} is in the past, skipping")
            return False

        delay_seconds = (reminder_datetime - now_datetime_full()).total_seconds()
        delay_seconds_int = max(1, int(delay_seconds))
        schedule.every(delay_seconds_int).seconds.do(
            scheduler_manager.handle_task_reminder,
            user_id=user_id,
            task_identifier=task_identifier,
        )

        logger.info(
            f"Scheduled one-time task reminder for user {user_id}, task {task_identifier} at {reminder_datetime}"
        )
        return True

    except Exception as e:
        logger.error(
            f"Error scheduling task reminder for user {user_id}, task {task_identifier}: {e}"
        )
        return False


@handle_errors("cleaning up task reminders")
def cleanup_task_reminders(
    scheduler_manager: Any, user_id: str, task_identifier: str
) -> bool:
    """Remove scheduled reminder jobs for a specific task."""
    try:
        if not user_id or not task_identifier:
            logger.error(
                f"Invalid parameters for cleanup_task_reminders: user_id={user_id}, task_identifier={task_identifier}"
            )
            return False

        initial_job_count = len(schedule.jobs)
        jobs_to_remove = []

        for job in schedule.jobs:
            try:
                job_func = job.job_func
                if not job_func:
                    continue
                if (
                    hasattr(job_func, "func")
                    and job_func.func == scheduler_manager.handle_task_reminder
                ):
                    if hasattr(job_func, "keywords"):
                        kwargs = job_func.keywords
                        if (
                            kwargs.get("user_id") == user_id
                            and kwargs.get("task_identifier") == task_identifier
                        ):
                            jobs_to_remove.append(job)
                            logger.debug(
                                f"Found reminder job for task {task_identifier}, user {user_id}"
                            )
                else:
                    args = getattr(job_func, "args", None)
                    if args and len(args) >= 2:
                        if args[0] == user_id and args[1] == task_identifier:
                            if (
                                hasattr(job_func, "func")
                                and job_func.func
                                == scheduler_manager.handle_task_reminder
                            ):
                                jobs_to_remove.append(job)
                                logger.debug(
                                    f"Found reminder job for task {task_identifier}, user {user_id} (positional args)"
                                )
            except Exception as e:
                logger.debug(f"Could not inspect job for cleanup: {e}")
                continue

        jobs_removed = 0
        for job in jobs_to_remove:
            try:
                schedule.jobs.remove(job)
                jobs_removed += 1
                logger.debug(
                    f"Removed reminder job for task {task_identifier}, user {user_id}"
                )
            except ValueError:
                pass

        final_job_count = len(schedule.jobs)
        logger.info(
            f"Cleaned up {jobs_removed} reminder job(s) for task {task_identifier}, user {user_id} "
            f"(from {initial_job_count} to {final_job_count} total jobs)"
        )
        return True

    except Exception as e:
        logger.error(
            f"Error cleaning up task reminders for task {task_identifier}, user {user_id}: {e}"
        )
        return False


@handle_errors("cleaning up orphaned task reminders")
def cleanup_orphaned_task_reminders(scheduler_manager: Any) -> None:
    try:
        logger.info("Starting periodic cleanup of orphaned task reminders")
        from core import get_all_user_ids

        get_all_user_ids()

        orphaned_count = 0
        total_checked = 0
        jobs_to_check = []
        handle_fn = scheduler_manager.handle_task_reminder

        for job in schedule.jobs:
            try:
                job_func = job.job_func
                if not job_func:
                    continue
                if (
                    hasattr(job_func, "func") and job_func.func == handle_fn
                ) and hasattr(job_func, "keywords"):
                    kwargs = job_func.keywords
                    user_id = kwargs.get("user_id")
                    task_identifier = kwargs.get("task_identifier")
                    if user_id and task_identifier:
                        jobs_to_check.append((job, user_id, task_identifier))
                        total_checked += 1
            except Exception as e:
                logger.debug(f"Could not inspect job for orphaned cleanup: {e}")
                continue

        for job, user_id, task_identifier in jobs_to_check:
            try:
                from tasks import get_task_by_id

                task = get_task_by_id(user_id, task_identifier)
                if not task:
                    try:
                        schedule.jobs.remove(job)
                        orphaned_count += 1
                        logger.info(
                            f"Removed orphaned reminder for non-existent task {task_identifier}, user {user_id}"
                        )
                    except ValueError:
                        pass
                elif runtime_task_is_completed(task):
                    try:
                        schedule.jobs.remove(job)
                        orphaned_count += 1
                        logger.info(
                            f"Removed reminder for completed task {task_identifier}, user {user_id}"
                        )
                    except ValueError:
                        pass
            except Exception as e:
                logger.debug(
                    f"Error checking task {task_identifier} for user {user_id}: {e}"
                )
                continue

        logger.info(
            f"Orphaned reminder cleanup complete: checked {total_checked} reminders, removed {orphaned_count} orphaned reminders"
        )
    except Exception as e:
        logger.error(
            f"Error during orphaned task reminder cleanup: {e}", exc_info=True
        )
