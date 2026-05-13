# scheduler.py

import schedule
import time
import calendar
import pytz
import threading
import random
import subprocess
import os  # Needed for test mocking (os.path.exists)
from collections.abc import Callable
from datetime import datetime, timedelta
from typing import Any

from core import get_all_user_ids
from core.delivery import SchedulerDeliveryPort
from core.schedule_runtime import get_schedule_time_periods
from core.service_utilities import load_and_localize_datetime
from core.time_utilities import (
    now_datetime_full,
    TIMESTAMP_FULL,
    DATE_ONLY,
    TIME_ONLY_MINUTE,
    TIMESTAMP_MINUTE,
    format_timestamp,
    format_time_compact_hour_minute,
    parse_time_only_minute,
)
from core.logger import get_component_logger
from user.user_context import UserContext
from core.error_handling import handle_errors
from core import get_user_data
from core import scheduler_jobs
from core import scheduler_maintenance
from core import scheduler_task_reminders

# Suppress debug logging from the schedule library to reduce log spam
from core.logger import suppress_noisy_logging

suppress_noisy_logging()

logger = get_component_logger("scheduler")
scheduler_logger = logger
_scheduler_delivery_factory: Callable[[], SchedulerDeliveryPort] | None = None


@handle_errors("configuring scheduler delivery factory", default_return=None)
def set_scheduler_delivery_factory(
    factory: Callable[[], SchedulerDeliveryPort] | None,
) -> None:
    """Configure the delivery factory used by standalone scheduler entry points."""
    global _scheduler_delivery_factory
    _scheduler_delivery_factory = factory


@handle_errors("building standalone scheduler manager", default_return=None)
def _create_standalone_scheduler_manager() -> "SchedulerManager | None":
    """Build a scheduler for standalone entry points using the configured delivery port."""
    if _scheduler_delivery_factory is None:
        logger.error(
            "Scheduler delivery factory is not configured; standalone scheduler action cannot run"
        )
        return None
    return SchedulerManager(_scheduler_delivery_factory())


class SchedulerManager:
    @handle_errors("initializing scheduler manager")
    def __init__(self, delivery: SchedulerDeliveryPort):
        """
        Initialize the SchedulerManager with the delivery surface it needs.

        Args:
            delivery: Object that can send scheduled messages and task reminders.
        """
        self.delivery = delivery
        self.scheduler_thread = None
        self.running = False
        self._stop_event = (
            threading.Event()
        )  # Add stop event for proper thread management
        # Track reminder selection state to provide smooth weighted scheduling across calls
        self._reminder_selection_state: dict[str, float] = {}
        logger.info("SchedulerManager ready")

    @handle_errors("running daily scheduler")
    def run_daily_scheduler(self):
        """
        Starts the daily scheduler in a separate thread that handles all users.
        """

        @handle_errors("scheduler loop", default_return=None)
        def scheduler_loop():
            # Clear all accumulated jobs first to prevent job accumulation
            self.clear_all_accumulated_jobs()

            scheduler_jobs.register_system_daily_jobs(self)

            # Schedule messages for all users immediately on startup (one-time only)
            self.schedule_all_users_immediately()

            # Log job count after daily job scheduling
            active_jobs = len(schedule.jobs)
            logger.info(
                f"Daily job scheduling complete: {active_jobs} total active jobs scheduled"
            )

            loop_count = 0
            while not self._stop_event.is_set():  # Check for stop signal
                schedule.run_pending()
                loop_count += 1

                # Log every 60 iterations (60 minutes) for diagnostic purposes
                if loop_count % 60 == 0:
                    active_jobs = len(schedule.jobs)
                    # Only log if there are actually jobs scheduled - don't log 0 jobs
                    if active_jobs > 0:
                        # Count different types of jobs for more meaningful logging
                        system_jobs = 0
                        user_message_jobs = 0
                        task_jobs = 0

                        for job in schedule.jobs:
                            job_func = job.job_func
                            if not job_func:
                                continue
                            if hasattr(job_func, "func"):
                                if job_func.func == self.perform_daily_log_archival or job_func.func == self.run_full_daily_scheduler:
                                    system_jobs += 1
                                elif (
                                    job_func.func
                                    == self.handle_sending_scheduled_message
                                ):
                                    user_message_jobs += 1
                                elif job_func.func == self.handle_task_reminder:
                                    task_jobs += 1

                        logger.debug(
                            f"Scheduler running: {active_jobs} total jobs ({system_jobs} system, {user_message_jobs} message, {task_jobs} task)"
                        )

                # Use wait instead of sleep to allow immediate shutdown
                # Use shorter timeout to allow responsive shutdown
                if self._stop_event.wait(
                    timeout=10
                ):  # Wait 10 seconds or until stop signal
                    break
            logger.info("Scheduler loop stopped gracefully.")

        self._stop_event.clear()  # Ensure stop event is reset
        self.scheduler_thread = threading.Thread(target=scheduler_loop)
        self.scheduler_thread.daemon = True
        self.scheduler_thread.start()
        logger.info("Scheduler thread started")

        # Update last run time after successful scheduling
        self.last_run_time = time.time()

    @handle_errors("stopping scheduler", default_return=None)
    def stop_scheduler(self):
        """Stops the scheduler thread."""
        if self.scheduler_thread is not None and self.scheduler_thread.is_alive():
            logger.info("Stopping scheduler thread...")
            self._stop_event.set()  # Signal the thread to stop
            self.scheduler_thread.join(
                timeout=10
            )  # Wait up to 10 seconds for clean shutdown
            if self.scheduler_thread.is_alive():
                logger.warning("Scheduler thread didn't stop within timeout period")
            else:
                logger.info("Scheduler thread stopped successfully.")
            self.scheduler_thread = None
        else:
            logger.warning("No active scheduler thread to stop.")

    @handle_errors("resetting and rescheduling daily messages")
    def reset_and_reschedule_daily_messages(self, category, user_id=None):
        """
        Resets scheduled tasks for a specific category and reschedules daily messages for that category.
        """
        # Get the active user ID - either from parameter or UserContext
        active_user_id = UserContext().get_user_id() if user_id is None else user_id

        if not active_user_id:
            logger.error("No active user found during reset and reschedule.")
            return

        # Remove only the scheduled jobs for the active user and the specific category
        schedule.jobs = [
            job
            for job in schedule.jobs
            if not self.is_job_for_category(job, active_user_id, category)
        ]

        # Handle different categories appropriately
        if category == "tasks":
            # For tasks, check if task management is enabled and schedule task reminders
            try:
                # Get user account data
                user_data_result = get_user_data(active_user_id, "account")
                user_account = user_data_result.get("account")
                if (
                    user_account
                    and user_account.get("features", {}).get("task_management")
                    == "enabled"
                ):
                    self.schedule_all_task_reminders(active_user_id)
                    logger.info(f"Rescheduled task reminders for user {active_user_id}")
                else:
                    logger.info(
                        f"Task management disabled for user {active_user_id}, skipping task reminder scheduling"
                    )
            except Exception as e:
                logger.error(
                    f"Error rescheduling task reminders for user {active_user_id}: {e}"
                )
        elif category == "checkin":
            # For check-ins, use the standard scheduling
            self.schedule_daily_message_job(user_id=active_user_id, category=category)
        else:
            # For regular message categories, use the standard scheduling
            self.schedule_daily_message_job(user_id=active_user_id, category=category)

        logger.info(
            f"Scheduler reset and rescheduled daily messages for active user: {active_user_id}, category: {category}."
        )

    @handle_errors("checking if job exists for category", default_return=False)
    def is_job_for_category(self, job, user_id, category):
        """Determines if a job is scheduled for a specific user and category."""
        if job is None:
            # Check all jobs for this user and category
            for existing_job in schedule.jobs:
                job_func = existing_job.job_func
                if not job_func:
                    continue
                # Check if this is a daily scheduler job for this user/category
                if (
                    hasattr(job_func, "func")
                    and job_func.func == self.schedule_daily_message_job
                    and hasattr(job_func, "keywords")
                    and job_func.keywords.get("user_id") == user_id
                    and job_func.keywords.get("category") == category
                ):
                    logger.debug(
                        f"Found existing daily job for user {user_id}, category {category}"
                    )
                    return True
            logger.debug(
                f"No existing daily job found for user {user_id}, category {category}"
            )
            return False
        else:
            # Check specific job
            job_func = job.job_func
            if not job_func:
                return False
            return bool(hasattr(job_func, "func") and job_func.func == self.schedule_daily_message_job and hasattr(job_func, "keywords") and job_func.keywords.get("user_id") == user_id and job_func.keywords.get("category") == category)

    @handle_errors("scheduling all users immediately", default_return=None)
    def schedule_all_users_immediately(self):
        """Schedule daily messages immediately for all users"""
        user_ids = get_all_user_ids()
        if not user_ids:
            logger.warning("No users found for scheduling")
            return

        total_scheduled = 0
        logger.info(f"Starting immediate scheduling for {len(user_ids)} users")

        # Log current time once at the start
        tz = pytz.timezone("America/Regina")
        now_datetime = tz.localize(now_datetime_full())
        logger.info(
            f"Current time for scheduling: {format_timestamp(now_datetime, TIMESTAMP_MINUTE)}"
        )

        for user_id in user_ids:
            try:
                # Schedule regular message categories
                prefs_result = get_user_data(user_id, "preferences")
                categories = prefs_result.get("preferences", {}).get("categories", [])
                if isinstance(categories, list):
                    if categories:  # Only process if list is not empty
                        for category in categories:
                            try:
                                self.schedule_daily_message_job(user_id, category)
                                total_scheduled += 1
                                logger.debug(
                                    f"Scheduled messages for user {user_id}, category {category}"
                                )
                            except Exception as e:
                                logger.error(
                                    f"Failed to schedule for user {user_id}, category {category}: {e}"
                                )
                    # Empty list is fine - no warning needed
                else:
                    logger.warning(
                        f"Expected list for categories, got {type(categories)} for user '{user_id}'"
                    )

                # Schedule check-ins if enabled
                try:
                    # Get user account data
                    user_data_result = get_user_data(user_id, "account")
                    user_account = user_data_result.get("account")
                    if (
                        user_account
                        and user_account.get("features", {}).get("checkins")
                        == "enabled"
                    ):
                        # Check if check-in category exists in schedules
                        time_periods = get_schedule_time_periods(user_id, "checkin")
                        if time_periods:
                            self.schedule_daily_message_job(user_id, "checkin")
                            total_scheduled += 1
                            logger.debug(f"Scheduled check-ins for user {user_id}")
                        else:
                            logger.debug(
                                f"No check-in schedule found for user {user_id}"
                            )
                except Exception as e:
                    logger.error(
                        f"Failed to schedule check-ins for user {user_id}: {e}"
                    )

                # Schedule task reminders if tasks are enabled
                try:
                    self.schedule_all_task_reminders(user_id)
                except Exception as e:
                    logger.error(
                        f"Failed to schedule task reminders for user {user_id}: {e}"
                    )

            except Exception as e:
                logger.error(f"Failed to get categories for user {user_id}: {e}")

        logger.info(
            f"Scheduling complete: {total_scheduled} user/category combinations scheduled (includes checkins if enabled)"
        )

        # Log consolidated scheduler status
        active_jobs = len(schedule.jobs)
        if active_jobs > 0:
            # Count job types for diagnostic purposes
            job_types = {}
            for job in schedule.jobs:
                job_func = job.job_func
                if not job_func:
                    continue

                # schedule often wraps callables (functools.partial) which may not have __name__
                func_obj = job_func.func if hasattr(job_func, "func") else job_func
                job_func_name = getattr(func_obj, "__name__", "UnknownJob")

                job_types[job_func_name] = job_types.get(job_func_name, 0) + 1

            job_type_summary = ", ".join(
                [f"{count} {name}" for name, count in job_types.items()]
            )
            logger.info(
                f"Scheduler status: {active_jobs} total jobs ({job_type_summary})"
            )
        else:
            logger.info("Scheduler status: No active jobs")

    @handle_errors("scheduling new user", default_return=None)
    def schedule_new_user(self, user_id: str):
        """
        Schedule a newly created user immediately.
        This method should be called after a new user is created to add them to the scheduler.

        Args:
            user_id: The ID of the newly created user
        """
        logger.info(f"Scheduling new user: {user_id}")

        try:
            # Schedule regular message categories
            prefs_result = get_user_data(user_id, "preferences")
            categories = prefs_result.get("preferences", {}).get("categories", [])
            if isinstance(categories, list) and categories:
                for category in categories:
                    try:
                        self.schedule_daily_message_job(user_id, category)
                        logger.info(
                            f"Scheduled messages for new user {user_id}, category {category}"
                        )
                    except Exception as e:
                        logger.error(
                            f"Failed to schedule for new user {user_id}, category {category}: {e}"
                        )

            # Schedule check-ins if enabled
            try:
                # Get user account data
                user_data_result = get_user_data(user_id, "account")
                user_account = user_data_result.get("account")
                if (
                    user_account
                    and user_account.get("features", {}).get("checkins") == "enabled"
                ):
                    # Check if check-in category exists in schedules
                    time_periods = get_schedule_time_periods(user_id, "checkin")
                    if time_periods:
                        self.schedule_daily_message_job(user_id, "checkin")
                        logger.info(f"Scheduled check-ins for new user {user_id}")
                    else:
                        logger.debug(
                            f"No check-in schedule found for new user {user_id}"
                        )
            except Exception as e:
                logger.error(
                    f"Failed to schedule check-ins for new user {user_id}: {e}"
                )

            # Schedule task reminders if tasks are enabled
            try:
                self.schedule_all_task_reminders(user_id)
                logger.info(f"Scheduled task reminders for new user {user_id}")
            except Exception as e:
                logger.error(
                    f"Failed to schedule task reminders for new user {user_id}: {e}"
                )

            logger.info(f"Successfully scheduled new user: {user_id}")

        except Exception as e:
            logger.error(f"Failed to schedule new user {user_id}: {e}")
            raise

    @handle_errors("running full daily scheduler")
    def run_full_daily_scheduler(self):
        """
        Runs the full daily scheduler process - same as system startup.
        This includes clearing accumulated jobs, scheduling all users, checkins, task reminders, and checking for weekly backups.
        """
        logger.info("Running full daily scheduler process (01:00 daily job)")

        # Check if weekly backup is needed (before everything else, so it runs before archival at 02:00)
        self.check_and_perform_weekly_backup()

        # Clear all accumulated jobs first to prevent job accumulation
        self.clear_all_accumulated_jobs()

        # Immediately schedule messages for all users (includes checkins and task reminders)
        self.schedule_all_users_immediately()

        # Refresh system and maintenance jobs for the next cycle.
        scheduler_jobs.register_full_daily_maintenance_jobs(self)

        # Log job count after daily job scheduling
        active_jobs = len(schedule.jobs)
        logger.info(
            f"Full daily scheduler complete: {active_jobs} total active jobs scheduled"
        )

    @handle_errors("scheduling daily message job")
    def schedule_daily_message_job(self, user_id, category):
        """
        Schedules daily messages immediately for the specified user and category.
        Schedules one message per active period in the category.
        """
        logger.info(
            f"Scheduling daily messages immediately for user {user_id}, category {category}."
        )

        # Clean up old jobs for this user and category
        self.cleanup_old_tasks(user_id, category)

        # Get all time periods for this user and category
        time_periods = get_schedule_time_periods(user_id, category)
        if not time_periods:
            logger.error(
                f"No time periods found for user {user_id}, category {category}."
            )
            return

        # Schedule a message for each active period
        scheduled_count = 0

        # Avoid hardcoded weekday format strings.
        # Use weekday index + calendar for a stable day-name.
        today_name = calendar.day_name[now_datetime_full().weekday()]

        for period_name, period_data in time_periods.items():
            # Skip the "ALL" period - it should not be scheduled, only used as fallback
            if period_name == "ALL":
                logger.debug(
                    f"Skipping ALL period scheduling for user {user_id}, category {category} - ALL is fallback only"
                )
                continue

            # Check if this period is active (default to active if not specified)
            if period_data.get("active", True):
                # If 'days' is present, only schedule if today is in days or if days contains "ALL"
                if "days" in period_data:
                    days = period_data["days"]
                    if "ALL" in days:
                        # Schedule for all days
                        logger.debug(
                            f"Scheduling period {period_name} for user {user_id}, category {category} (ALL days)"
                        )
                    elif today_name in days:
                        # Schedule for today
                        logger.debug(
                            f"Scheduling period {period_name} for user {user_id}, category {category} (today: {today_name})"
                        )
                    else:
                        logger.debug(
                            f"Skipping period {period_name} for user {user_id}, category {category} (not scheduled for today: {today_name})"
                        )
                        continue

                try:
                    self.schedule_message_for_period(user_id, category, period_name)
                    scheduled_count += 1
                    logger.debug(
                        f"Scheduled message for user {user_id}, category {category}, period {period_name}"
                    )
                except Exception as e:
                    logger.error(
                        f"Failed to schedule message for user {user_id}, category {category}, period {period_name}: {e}"
                    )
            else:
                logger.debug(
                    f"Skipping inactive period {period_name} for user {user_id}, category {category}"
                )

        logger.info(
            f"Scheduled {scheduled_count} messages for user {user_id}, category {category}"
        )

    @handle_errors("scheduling message for specific period")
    def schedule_message_for_period(self, user_id, category, period_name):
        """
        Schedules a message at a random time within a specific period for a user and category.
        """
        logger.info(
            f"Scheduling message for period '{period_name}' for user {user_id}, category {category}."
        )

        max_retries = 10
        retry_count = 0

        while retry_count < max_retries:
            # Get a random time within the specified period
            random_time_str = self.get_random_time_within_period(
                user_id, category, period_name
            )
            if not random_time_str:
                logger.error(
                    f"Could not generate random time for user {user_id}, category {category}, period {period_name}."
                )
                return

            # Try to schedule the message
            try:
                datetime_str = random_time_str
                schedule_datetime = load_and_localize_datetime(
                    datetime_str, "America/Regina"
                )
                now = pytz.timezone("America/Regina").localize(now_datetime_full())

                logger.info(
                    f"Attempting to schedule message for user {user_id}, category {category}, period {period_name} at {schedule_datetime} (now is {now})"
                )

                if not self.is_time_conflict(user_id, schedule_datetime):
                    if schedule_datetime <= now:
                        schedule_datetime += timedelta(days=1)
                        logger.info(
                            f"Adjusted scheduling time to future for user {user_id}: {schedule_datetime}"
                        )

                    time_part = format_timestamp(schedule_datetime, TIME_ONLY_MINUTE)
                    # Schedule as one-time job that will remove itself after execution
                    schedule.every().day.at(time_part).do(
                        self.handle_sending_scheduled_message,
                        user_id=user_id,
                        category=category,
                    )
                    logger.info(
                        f"Successfully scheduled {category} message for user {user_id}, period {period_name} "
                        f"at {time_part} on {format_timestamp(schedule_datetime, DATE_ONLY)}."
                    )

                    # Set the wake timer for the scheduled time
                    self.set_wake_timer(
                        schedule_datetime, user_id, category, period_name
                    )
                    break  # Exit the loop after successfully scheduling the message
                else:
                    logger.info(
                        f"Conflict detected for user {user_id}, category {category}, period {period_name} at {schedule_datetime}. Retrying..."
                    )
                    retry_count += 1

            except Exception as e:
                logger.error(
                    f"Error while scheduling {category} message for user {user_id}, period {period_name}: {str(e)}"
                )
                retry_count += 1

        if retry_count == max_retries:
            logger.warning(
                f"Max retries reached. Could not find a suitable time for user {user_id}, category {category}, period {period_name}."
            )

    @handle_errors("scheduling check-in at exact time")
    def schedule_checkin_at_exact_time(self, user_id, period_name):
        """
        Schedule a check-in at the exact time specified in the period.
        """
        logger.info(f"Scheduling check-in for user {user_id}, period {period_name}")

        try:
            # Get the time periods for check-in category
            time_periods = get_schedule_time_periods(user_id, "checkin")
            if not time_periods or period_name not in time_periods:
                logger.error(
                    f"No time period '{period_name}' found for check-in scheduling for user {user_id}"
                )
                return

            period_data = time_periods[period_name]
            # Use canonical keys with fallback to legacy keys
            checkin_time = period_data.get("start_time") or period_data.get("start")
            if not checkin_time:
                logger.error(
                    f"Missing start time for check-in period {period_name} in user {user_id}"
                )
                return

            # Create datetime for today at the specified time
            tz = pytz.timezone("America/Regina")
            now = tz.localize(now_datetime_full())
            today = now.date()

            # Parse the check-in time (HH:MM)
            checkin_dt = parse_time_only_minute(checkin_time)
            if checkin_dt is None:
                logger.error(f"Invalid check-in time format: {checkin_time}")
                return

            # Build a timezone-aware datetime for today's check-in time.
            # IMPORTANT: with pytz, never pass tzinfo=tz directly; always localize a naive datetime.
            schedule_datetime = tz.localize(datetime.combine(today, checkin_dt.time()))

            # If the time has already passed today, schedule for tomorrow
            if schedule_datetime <= now:
                schedule_datetime += timedelta(days=1)
                logger.info(
                    f"Check-in time has passed today, scheduling for tomorrow: {schedule_datetime}"
                )

            # Schedule the check-in
            time_part = format_timestamp(schedule_datetime, TIME_ONLY_MINUTE)
            schedule.every().day.at(time_part).do(
                self.handle_sending_scheduled_message,
                user_id=user_id,
                category="checkin",
            )
            logger.info(
                f"Successfully scheduled check-in for user {user_id} at {time_part} "
                f"on {format_timestamp(schedule_datetime, DATE_ONLY)}."
            )

            # Set the wake timer for the scheduled time
            self.set_wake_timer(schedule_datetime, user_id, "checkin", period_name)

        except Exception as e:
            logger.error(f"Error scheduling check-in for user {user_id}: {e}")

    @handle_errors("scheduling message at random time")
    def schedule_message_at_random_time(self, user_id, category):
        """
        Schedules a message at a random time within the user's preferred time periods.
        """
        logger.info(
            f"Scheduling message at random time for user {user_id}, category {category}."
        )

        time_periods = get_schedule_time_periods(user_id, category)
        if not time_periods:
            logger.error(
                f"No time periods found for user {user_id}, category {category}."
            )
            return

        available_periods = list(time_periods.keys())
        if not available_periods:
            logger.error(
                f"No available periods for user {user_id}, category {category}."
            )
            return

        selected_period = available_periods[0]
        logger.info(
            f"Using period '{selected_period}' for user {user_id}, category {category}"
        )

        max_retries = 10
        retry_count = 0

        while retry_count < max_retries:
            random_time_str = self.get_random_time_within_period(
                user_id, category, selected_period
            )
            if not random_time_str:
                logger.error(
                    f"Could not generate random time for user {user_id}, category {category}."
                )
                return

            try:
                schedule_datetime = load_and_localize_datetime(
                    random_time_str, "America/Regina"
                )
                now = pytz.timezone("America/Regina").localize(now_datetime_full())

                logger.info(
                    f"Attempting to schedule message for user {user_id}, category {category} at {schedule_datetime} (now is {now})"
                )

                if not self.is_time_conflict(user_id, schedule_datetime):
                    if schedule_datetime <= now:
                        schedule_datetime += timedelta(days=1)
                        logger.info(
                            f"Adjusted scheduling time to future for user {user_id}: {schedule_datetime}"
                        )

                    time_part = format_timestamp(schedule_datetime, TIME_ONLY_MINUTE)
                    schedule.every().day.at(time_part).do(
                        self.handle_sending_scheduled_message,
                        user_id=user_id,
                        category=category,
                    )
                    logger.info(
                        f"Successfully scheduled {category} message for user {user_id} at {time_part} "
                        f"on {format_timestamp(schedule_datetime, DATE_ONLY)}."
                    )

                    self.set_wake_timer(
                        schedule_datetime, user_id, category, selected_period
                    )
                    break
                else:
                    logger.info(
                        f"Conflict detected for user {user_id}, category {category} at {schedule_datetime}. Retrying..."
                    )
                    retry_count += 1

            except Exception as e:
                logger.error(
                    f"Error while scheduling {category} message for user {user_id}: {str(e)}"
                )
                retry_count += 1

        if retry_count == max_retries:
            logger.warning(
                f"Max retries reached. Could not find a suitable time for user {user_id}, category {category}."
            )

    @handle_errors("checking time conflict", default_return=False)
    def is_time_conflict(self, user_id, schedule_datetime):
        """
        Checks if there is a time conflict with any existing scheduled jobs for the user.

        NOTE:
        The `schedule` library commonly uses naive datetimes for `job.next_run`.
        Our schedule_datetime is often tz-aware (pytz). Subtracting naive/aware raises TypeError.
        """
        # Normalize schedule_datetime to naive for comparison against schedule's job.next_run.
        # We intentionally drop tzinfo here because schedule's next_run is not reliably tz-aware.
        if (
            isinstance(schedule_datetime, datetime)
            and schedule_datetime.tzinfo is not None
        ):
            schedule_dt_for_compare = schedule_datetime.replace(tzinfo=None)
        else:
            schedule_dt_for_compare = schedule_datetime

        for job in schedule.jobs:
            job_func = job.job_func
            if not job_func:
                continue

            job_args = getattr(job_func, "args", None)
            if job_args and job_args[0] == user_id:
                job_time = job.next_run
                if not job_time:
                    continue

                # Normalize job_time too (defensive)
                if isinstance(job_time, datetime) and job_time.tzinfo is not None:
                    job_time_for_compare = job_time.replace(tzinfo=None)
                else:
                    job_time_for_compare = job_time

                # Increase conflict window to 2 hours to prevent multiple messages at similar times
                try:
                    if (
                        abs(
                            (
                                job_time_for_compare - schedule_dt_for_compare
                            ).total_seconds()
                        )
                        < 7200
                    ):
                        return True
                except TypeError as e:
                    # Extremely defensive: if something weird slips through, log and treat as no conflict
                    logger.debug(
                        f"TypeError comparing job_time and schedule_datetime for conflict check: {e}"
                    )
                    continue

        return False

    @handle_errors("getting random time within period", default_return=None)
    def get_random_time_within_period(
        self, user_id, category, period, timezone_str="America/Regina"
    ):
        """Get a random time within a specified period for a given category."""
        tz = pytz.timezone(timezone_str)
        now_datetime = tz.localize(now_datetime_full())

        time_periods = get_schedule_time_periods(user_id, category)

        # Add validation for period existence
        if period not in time_periods:
            logger.error(
                f"Period '{period}' not found in time periods for user {user_id}, category {category}. Available periods: {list(time_periods.keys())}"
            )
            return None

        # Use canonical keys with fallback to legacy keys
        start_time = time_periods[period].get("start_time") or time_periods[period].get(
            "start"
        )
        end_time = time_periods[period].get("end_time") or time_periods[period].get(
            "end"
        )

        if not start_time or not end_time:
            logger.error(
                f"Missing start/end time for period {period} in user {user_id}, category {category}"
            )
            return None

        start_dt = parse_time_only_minute(start_time)
        end_dt = parse_time_only_minute(end_time)
        if start_dt is None or end_dt is None:
            logger.error(
                f"Invalid time format for period {period} in user {user_id}, category {category}: start='{start_time}', end='{end_time}'"
            )
            return None

        period_start_time = start_dt.time()
        period_end_time = end_dt.time()

        # Create timezone-aware datetime objects for today.
        # IMPORTANT: with pytz, never pass tzinfo=tz directly; always localize a naive datetime.
        start_datetime = tz.localize(
            datetime.combine(now_datetime.date(), period_start_time)
        )
        end_datetime = tz.localize(
            datetime.combine(now_datetime.date(), period_end_time)
        )

        # If the period has already ended today, schedule for tomorrow
        if end_datetime <= now_datetime or start_datetime <= now_datetime + timedelta(minutes=30):
            start_datetime += timedelta(days=1)
            end_datetime += timedelta(days=1)

        total_seconds = (end_datetime - start_datetime).total_seconds()
        if total_seconds <= 0:
            logger.error("Invalid time range calculated.")
            return None

        random_seconds = random.randint(0, int(total_seconds))
        random_datetime = start_datetime + timedelta(seconds=random_seconds)

        # Final safety check - ensure the time is in the future
        if random_datetime <= now_datetime:
            random_datetime += timedelta(days=1)

        random_time_str = format_timestamp(random_datetime, TIMESTAMP_MINUTE)
        logger.info(f"Scheduled random time: {random_time_str}")
        return random_time_str

    @handle_errors("logging scheduled tasks")
    def log_scheduled_tasks(self):
        """Logs all current and upcoming scheduled tasks in a user-friendly manner."""
        for job in schedule.jobs:
            job_func = job.job_func
            if not job_func:
                continue

            next_run = (
                format_timestamp(job.next_run, TIMESTAMP_FULL)
                if job.next_run
                else "None"
            )

            # Safely resolve function name for schedule-wrapped callables.
            # schedule often wraps functions in functools.partial, which may not have __name__.
            func_obj = job_func.func if hasattr(job_func, "func") else job_func
            task_name = getattr(func_obj, "__name__", "Scheduled Task")

            task_description = (
                str(job_func).split("function ")[-1].split(" at ")[0]
                if "function" in str(job_func)
                else task_name
            )

            category = "Generic Task"
            job_args = getattr(job_func, "args", None)
            if hasattr(job_func, "func") and job_args:
                category = job_args[0]

            logger.info(
                f"Task: {task_description}, Category: {category}, Scheduled at: {job.at_time}, Next run: {next_run}"
            )

    @handle_errors("handling sending scheduled message")
    def handle_sending_scheduled_message(
        self,
        user_id,
        category,
        retry_attempts=3,
        retry_delay=30,
        allow_deferral=True,
    ):
        """
        Handles the sending of scheduled messages with retries.
        This is a one-time job that removes itself after execution.
        """
        if self.delivery is None:
            logger.error("Delivery interface is not initialized.")
            return

        attempt = 0
        while attempt < retry_attempts:
            try:
                # Try to send the message
                send_status = self.delivery.handle_message_sending(
                    user_id=user_id,
                    category=category,
                    is_scheduled_trigger=True,
                    allow_deferral=allow_deferral,
                )
                if send_status.status == "sent":
                    logger.info(
                        f"Message sent successfully for user {user_id}, category {category}."
                    )
                    # Remove this job after successful execution to make it a one-time job
                    self._remove_user_message_job(user_id, category)
                    return  # Exit after successful execution

                if send_status.status == "deferred":
                    logger.info(
                        f"Deferred scheduled message for user {user_id}, category {category}; scheduling one-time retry in 10 minutes."
                    )
                    self._remove_user_message_job(user_id, category)
                    self._schedule_deferred_message_retry(
                        user_id=user_id,
                        category=category,
                        delay_minutes=10,
                        retry_delay=retry_delay,
                    )
                    return

                if send_status.status == "skipped":
                    logger.info(
                        f"Skipping scheduled message for user {user_id}, category {category}: no eligible message content."
                    )
                    self._remove_user_message_job(user_id, category)
                    return
            except Exception as e:
                logger.error(
                    f"Error sending message for user {user_id}, category {category}: {e}"
                )
                attempt += 1
                logger.info(
                    f"Retrying in {retry_delay} seconds... ({attempt}/{retry_attempts})"
                )
                time.sleep(retry_delay)  # Wait before retrying

        # Remove job even if it failed after all retries
        self._remove_user_message_job(user_id, category)

    @handle_errors("scheduling deferred message retry", default_return=False)
    def _schedule_deferred_message_retry(
        self, user_id, category, delay_minutes=10, retry_delay=30
    ) -> bool:
        """Schedule a one-time retry for deferred scheduled sends."""
        retry_dt = now_datetime_full() + timedelta(minutes=delay_minutes)
        retry_time = format_timestamp(retry_dt, TIME_ONLY_MINUTE)
        schedule.every().day.at(retry_time).do(
            self.handle_sending_scheduled_message,
            user_id=user_id,
            category=category,
            retry_attempts=1,
            retry_delay=retry_delay,
            allow_deferral=False,
        )
        logger.info(
            f"Scheduled deferred retry for user {user_id}, category {category} at {retry_time} (allow_deferral=False)."
        )
        return True

    @handle_errors("removing user message job")
    def _remove_user_message_job(self, user_id, category):
        """
        Removes user message jobs from the scheduler after execution.
        This makes user message jobs effectively one-time jobs.
        """
        try:
            # Find and remove jobs for this user and category
            jobs_to_remove = []
            for job in schedule.jobs:
                job_func = job.job_func
                if not job_func:
                    continue
                job_args = getattr(job_func, "args", None)
                if (
                    hasattr(job_func, "func")
                    and job_func.func == self.handle_sending_scheduled_message
                    and job_args
                    and len(job_args) >= 2
                    and job_args[0] == user_id
                    and job_args[1] == category
                ):
                    jobs_to_remove.append(job)

            # Remove the jobs
            for job in jobs_to_remove:
                schedule.jobs.remove(job)
                logger.debug(
                    f"Removed one-time job for user {user_id}, category {category}"
                )

            if jobs_to_remove:
                logger.info(
                    f"Removed {len(jobs_to_remove)} completed message job(s) for user {user_id}, category {category}"
                )

        except Exception as e:
            logger.error(
                f"Error removing user message job for user {user_id}, category {category}: {e}"
            )

    @handle_errors("handling task reminder")
    def handle_task_reminder(self, user_id, task_identifier, retry_attempts=3, retry_delay=30):
        """
        Handles sending task reminders with retries.

        ``task_identifier`` is the task record's canonical ``id`` (or a value that
        ``get_task_by_id`` resolves). Scheduled jobs must pass ``task_identifier=``.
        """
        scheduler_task_reminders.handle_task_reminder(
            self, user_id, task_identifier, retry_attempts, retry_delay
        )

    @handle_errors("setting wake timer")
    def set_wake_timer(
        self, schedule_time, user_id, category, period, wake_ahead_minutes=4
    ):
        """
        Set a Windows scheduled task to wake the computer before a scheduled message.

        Args:
            schedule_time: The datetime when the message is scheduled
            user_id: The user ID
            category: The message category
            period: The time period name
            wake_ahead_minutes: Minutes before schedule_time to wake the computer (default: 4)
        """
        # CRITICAL: Never create real Windows tasks for test users
        # Check if we're in test mode or if user data is in test directory
        if os.getenv("MHM_TESTING") == "1":
            logger.debug(
                f"Skipping wake timer creation for test user {user_id} (MHM_TESTING=1)"
            )
            return

        # Additional safety check: verify user data directory is not in tests directory
        try:
            from core.config import get_user_data_dir, BASE_DATA_DIR

            user_data_dir = get_user_data_dir(user_id)
            if user_data_dir and (
                "tests" in user_data_dir or "test" in BASE_DATA_DIR.lower()
            ):
                logger.debug(
                    f"Skipping wake timer creation for test user {user_id} (test data directory detected)"
                )
                return
        except Exception as e:
            logger.debug(f"Could not verify user data directory for {user_id}: {e}")
            # If we can't verify, err on the side of caution and skip task creation
            if os.getenv("MHM_TESTING") == "1":
                return

        # Adjust the schedule_time to wake the computer a few minutes earlier
        wake_time = schedule_time - timedelta(minutes=wake_ahead_minutes)
        # Task name must not contain : \ / * ? " < > | (Windows restriction; colon was causing 0x80070057)
        time_part_name = format_time_compact_hour_minute(wake_time)
        raw_name = f"Wake_{user_id}_{category}_{period}_{time_part_name}"
        invalid_chars = r'\/*?"<>|:' + "'"
        for char in invalid_chars:
            raw_name = raw_name.replace(char, "_")
        task_name = raw_name[:200] if len(raw_name) > 200 else raw_name  # Stay under path length limit

        task_time = format_timestamp(wake_time, TIME_ONLY_MINUTE)
        task_date = format_timestamp(wake_time, DATE_ONLY)
        # Build trigger time as ISO string; PowerShell will parse as [DateTime] for -At
        trigger_at_str = f"{task_date}T{task_time}:00"

        # PowerShell script to create the task with Wake computer enabled
        # -At expects [DateTime]; parse explicitly to avoid locale/format issues
        ps_command = f"""
        $action = New-ScheduledTaskAction -Execute 'cmd.exe' -Argument '/c exit'
        $at = [DateTime]::ParseExact('{trigger_at_str}', 'yyyy-MM-ddTHH:mm:ss', $null)
        $trigger = New-ScheduledTaskTrigger -Once -At $at
        $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -WakeToRun
        Register-ScheduledTask -TaskName '{task_name}' -Action $action -Trigger $trigger -Settings $settings -Force
        """

        # Execute the PowerShell command and capture the output
        result = subprocess.run(
            ["powershell", "-Command", ps_command], capture_output=True, text=True
        )

        if result.returncode == 0:
            logger.info(
                f"Wake timer set for {format_timestamp(wake_time, TIMESTAMP_MINUTE)} with task {task_name}"
            )
        else:
            logger.error(f"Failed to set wake timer with error: {result.stderr}")
            # Only log detailed info on errors
            logger.debug(f"PowerShell command: {ps_command.strip()}")
            logger.debug(f"PowerShell stdout: {result.stdout}")
            logger.debug(f"PowerShell return code: {result.returncode}")

    @handle_errors("cleaning up old tasks")
    def cleanup_old_tasks(self, user_id, category):
        """Cleans up all tasks (scheduled jobs and system tasks) associated with a given user and category."""
        # Count jobs before cleanup
        initial_job_count = len(schedule.jobs)
        jobs_removed = 0

        # Remove only jobs for this specific user and category
        jobs_to_remove = []
        for job in schedule.jobs:
            if self.is_job_for_category(job, user_id, category):
                jobs_to_remove.append(job)

        # Remove the identified jobs
        for job in jobs_to_remove:
            try:
                schedule.jobs.remove(job)
                jobs_removed += 1
                logger.debug(f"Removed job for user {user_id}, category {category}")
            except ValueError:
                # Job was already removed
                pass

        final_job_count = len(schedule.jobs)
        logger.info(
            f"In-memory scheduler cleanup completed for user {user_id}, category {category}. Removed {jobs_removed} jobs (from {initial_job_count} to {final_job_count} total jobs)."
        )

    # not_duplicate: scheduler_standalone_delegates
    @handle_errors("clearing all accumulated jobs")
    def clear_all_accumulated_jobs(self):
        """Clears all accumulated scheduler jobs and reschedules only the necessary ones."""
        logger.info("Clearing all accumulated scheduler jobs...")

        # Count jobs before cleanup
        initial_job_count = len(schedule.jobs)
        logger.info(
            f"Initial job count: {initial_job_count} (accumulated jobs to be cleared)"
        )

        # Clear all jobs
        schedule.clear()
        logger.info("All scheduler jobs cleared")

        # Don't reschedule daily jobs here - the main scheduler loop will handle that
        # This function is only for clearing accumulated jobs, not scheduling new ones

        final_job_count = len(schedule.jobs)
        jobs_cleared = initial_job_count - final_job_count

        # Log cleanup results in a single message
        if jobs_cleared > 0:
            logger.info(
                f"Job cleanup complete: {jobs_cleared} accumulated jobs cleared"
            )
        elif jobs_cleared == 0:
            logger.debug(
                "Job cleanup complete: No accumulated jobs to clear (system was already clean)"
            )
        else:
            logger.info(
                f"Job cleanup complete: Added {abs(jobs_cleared)} scheduler jobs (system had fewer jobs than expected)"
            )

        scheduler_maintenance.cleanup_scheduler_wake_tasks()

    @handle_errors("scheduling all task reminders")
    def schedule_all_task_reminders(self, user_id):
        """
        Schedule reminders for all active tasks for a user.
        For each reminder period, pick one random task and schedule it at a random time within the period.
        """
        scheduler_task_reminders.schedule_all_task_reminders(self, user_id)

    @handle_errors("selecting task for reminder", default_return=None)
    def select_task_for_reminder(
        self, incomplete_tasks: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """
        Select a task for reminder using priority-based and due date proximity weighting.

        Args:
            incomplete_tasks: List of incomplete tasks to choose from

        Returns:
            Selected task dictionary
        """
        return scheduler_task_reminders.select_task_for_reminder(
            self, incomplete_tasks
        )

    @handle_errors("getting random time within task period")
    def get_random_time_within_task_period(self, start_time, end_time):
        """
        Generate a random time within a task reminder period.
        Args:
            start_time: Start time in HH:MM format (e.g., "17:00")
            end_time: End time in HH:MM format (e.g., "18:00")
        Returns:
            Random time in HH:MM format
        """
        return scheduler_task_reminders.get_random_time_within_task_period(
            start_time, end_time
        )

    @handle_errors("scheduling task reminder at specific time")
    def schedule_task_reminder_at_time(self, user_id, task_identifier, reminder_time):
        """
        Schedule a reminder for a specific task at the specified time (daily).
        """
        return scheduler_task_reminders.schedule_task_reminder_at_time(
            self, user_id, task_identifier, reminder_time
        )

    @handle_errors("scheduling task reminder at specific datetime")
    def schedule_task_reminder_at_datetime(self, user_id, task_identifier, date_str, time_str):
        """
        Schedule a reminder for a specific task at a specific date and time.
        """
        return scheduler_task_reminders.schedule_task_reminder_at_datetime(
            self, user_id, task_identifier, date_str, time_str
        )

    @handle_errors("cleaning up task reminders")
    def cleanup_task_reminders(self, user_id, task_identifier):
        """
        Clean up all reminders for a specific task.

        Finds and removes all APScheduler jobs that call handle_task_reminder for the given task identifier.
        Handles both one-time reminders (schedule_task_reminder_at_datetime) and daily reminders (schedule_task_reminder_at_time).

        Args:
            user_id: The user's ID
            task_identifier: Canonical task ``id`` (or resolved identifier) to clean up reminders for

        Returns:
            bool: True if cleanup succeeded (or no reminders found), False on error
        """
        return scheduler_task_reminders.cleanup_task_reminders(
            self, user_id, task_identifier
        )

    @handle_errors(
        "running orphaned task reminder cleanup scheduler job",
        user_friendly=False,
        default_return=None,
    )
    def cleanup_orphaned_task_reminders(self):
        """
        Periodic cleanup job to remove reminders for tasks that no longer exist.

        Scans all scheduled reminder jobs and verifies the associated tasks still exist.
        Removes reminders for tasks that have been deleted or completed.
        Runs daily at 03:00.
        """
        scheduler_task_reminders.cleanup_orphaned_task_reminders(self)

    @handle_errors(
        "running daily log archival scheduler job",
        user_friendly=False,
        default_return=None,
    )
    def perform_daily_log_archival(self):
        """
        Perform daily log archival to compress old logs and clean up archives.
        This runs automatically at 02:00 daily via the scheduler.
        """
        scheduler_maintenance.perform_daily_log_archival()

    @handle_errors(
        "running weekly backup check scheduler job",
        user_friendly=False,
        default_return=None,
    )
    def check_and_perform_weekly_backup(self):
        """
        Check if a weekly backup is needed and perform it if so.
        Runs during the daily scheduler job at 01:00 (before log archival at 02:00).
        Creates a backup if:
        - No weekly backups exist, OR
        - Last weekly backup is 7+ days old
        Retention is enforced by BackupManager with separate weekly/non-weekly buckets.
        """
        scheduler_maintenance.check_and_perform_weekly_backup()


# Standalone functions for admin UI access
@handle_errors("running full scheduler standalone", default_return=False)
def run_full_scheduler_standalone():
    """
    Standalone function to run the full scheduler for all users.
    This can be called from the admin UI without needing a scheduler instance.
    """
    scheduler_manager = _create_standalone_scheduler_manager()
    if scheduler_manager is None:
        return False

    # Run the full scheduler
    logger.info("Standalone: Running full scheduler for all users")
    scheduler_manager.run_daily_scheduler()

    logger.info("Standalone: Full scheduler started successfully")
    return True


@handle_errors("running user scheduler standalone", default_return=False)
def run_user_scheduler_standalone(user_id):
    """
    Standalone function to run scheduler for a specific user.
    This can be called from the admin UI without needing a scheduler instance.
    """
    scheduler_manager = _create_standalone_scheduler_manager()
    if scheduler_manager is None:
        return False

    # Run scheduler for the specific user
    logger.info(f"Standalone: Running scheduler for user {user_id}")
    scheduler_manager.schedule_new_user(user_id)

    logger.info(f"Standalone: User scheduler started successfully for {user_id}")
    return True


@handle_errors("running category scheduler standalone", default_return=False)
def run_category_scheduler_standalone(user_id, category):
    """
    Standalone function to run scheduler for a specific user and category.
    This can be called from the admin UI without needing a scheduler instance.
    """
    scheduler_manager = _create_standalone_scheduler_manager()
    if scheduler_manager is None:
        return False

    # Run scheduler for the specific user and category
    logger.info(
        f"Standalone: Running category scheduler for user {user_id}, category {category}"
    )
    scheduler_manager.schedule_daily_message_job(user_id, category)

    logger.info(
        f"Standalone: Category scheduler started successfully for {user_id}, {category}"
    )
    return True


@handle_errors("scheduling all task reminders for user", default_return=None)
def schedule_all_task_reminders(user_id):
    """
    Standalone function to schedule all task reminders for a user.
    This can be called from the admin UI without needing a scheduler instance.
    """
    from tasks import are_tasks_enabled

    # Check if tasks are enabled for this user
    if not are_tasks_enabled(user_id):
        logger.debug(f"Tasks not enabled for user {user_id}")
        return

    # For now, just log that scheduling was requested
    # The actual scheduling will happen when the main scheduler starts
    logger.info(f"Task reminder scheduling requested for user {user_id}")
    logger.info("Task reminders will be scheduled when the main scheduler starts")


# Task reminders are now managed consistently with other jobs
# No special cleanup function needed - they're handled by the main scheduler cleanup


# not_duplicate: scheduler_standalone_delegates
@handle_errors("clearing all accumulated jobs standalone", default_return=False)
def clear_all_accumulated_jobs_standalone():
    """
    Standalone function to clear all accumulated scheduler jobs.
    This can be called from the admin UI or service to fix job accumulation issues.
    """
    scheduler_manager = _create_standalone_scheduler_manager()
    if scheduler_manager is None:
        return False

    # Clear all accumulated jobs
    scheduler_manager.clear_all_accumulated_jobs()

    logger.info("Standalone: All accumulated scheduler jobs cleared successfully")
    return True


@handle_errors("processing user schedules", default_return=None)
def process_user_schedules(user_id: str):
    """Process schedules for a specific user."""
    # Get user's categories
    prefs_result = get_user_data(user_id, "preferences")
    categories = prefs_result.get("preferences", {}).get("categories", [])
    if not categories:
        logger.debug(f"No categories found for user {user_id}")
        return

    # Process each category
    for category in categories:
        process_category_schedule(user_id, category)


@handle_errors("processing category schedule", default_return=None)
def process_category_schedule(user_id: str, category: str):
    """Process schedule for a specific user and category."""
    scheduler_manager = _create_standalone_scheduler_manager()
    if scheduler_manager is None:
        return

    # Schedule messages for this category
    scheduler_manager.schedule_daily_message_job(user_id, category)

    logger.info(f"Processed schedule for user {user_id}, category {category}")
