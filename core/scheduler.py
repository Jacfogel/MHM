# scheduler.py

import schedule
import time
import pytz
import threading
import random
import subprocess
import os  # Needed for test mocking (os.path.exists)
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from core.user_data_handlers import get_all_user_ids
from core.schedule_management import get_schedule_time_periods
from core.service_utilities import load_and_localize_datetime
from core.logger import get_component_logger
from user.user_context import UserContext
from core.error_handling import handle_errors
from core.user_data_handlers import get_user_data
from core.backup_manager import backup_manager

# Suppress debug logging from the schedule library to reduce log spam
from core.logger import suppress_noisy_logging
suppress_noisy_logging()

logger = get_component_logger('scheduler')
scheduler_logger = logger

class SchedulerManager:
    @handle_errors("initializing scheduler manager")
    def __init__(self, communication_manager):
        """
        Initialize the SchedulerManager with communication manager.
        
        Args:
            communication_manager: The communication manager for sending messages
        """
        self.communication_manager = communication_manager
        self.scheduler_thread = None
        self.running = False
        self._stop_event = threading.Event()  # Add stop event for proper thread management
        # Track reminder selection state to provide smooth weighted scheduling across calls
        self._reminder_selection_state: Dict[str, float] = {}
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
            
            # Schedule daily log archival at 02:00
            schedule.every().day.at("02:00").do(self.perform_daily_log_archival)
            logger.info("Scheduled new daily job for log archival at 02:00")
            
            # Schedule a single full daily scheduler job at 01:00 to handle complete system initialization
            # This ensures checkins, task reminders, full cleanup, and weekly backups (if needed) happen daily
            schedule.every().day.at("01:00").do(self.run_full_daily_scheduler)
            logger.info("Scheduled full daily scheduler job at 01:00 (includes checkins, task reminders, cleanup, and backup check)")
            
            # Schedule messages for all users immediately on startup (one-time only)
            self.schedule_all_users_immediately()
            
            # Log job count after daily job scheduling
            active_jobs = len(schedule.jobs)
            logger.info(f"Daily job scheduling complete: {active_jobs} total active jobs scheduled")
    
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
                            if hasattr(job.job_func, 'func'):
                                if job.job_func.func == self.perform_daily_log_archival:
                                    system_jobs += 1
                                elif job.job_func.func == self.run_full_daily_scheduler:
                                    system_jobs += 1
                                elif job.job_func.func == self.handle_sending_scheduled_message:
                                    user_message_jobs += 1
                                elif job.job_func.func == self.handle_task_reminder:
                                    task_jobs += 1
                        
                        logger.info(f"Scheduler running: {active_jobs} total jobs ({system_jobs} system, {user_message_jobs} message, {task_jobs} task)")
                    
                # Use wait instead of sleep to allow immediate shutdown
                # Use shorter timeout to allow responsive shutdown
                if self._stop_event.wait(timeout=10):  # Wait 10 seconds or until stop signal
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
            self.scheduler_thread.join(timeout=10)  # Wait up to 10 seconds for clean shutdown
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
        if user_id is None:
            active_user_id = UserContext().get_user_id()
        else:
            active_user_id = user_id
            
        if not active_user_id:
            logger.error("No active user found during reset and reschedule.")
            return

        # Remove only the scheduled jobs for the active user and the specific category
        schedule.jobs = [job for job in schedule.jobs if not self.is_job_for_category(job, active_user_id, category)]
    
        # Handle different categories appropriately
        if category == "tasks":
            # For tasks, check if task management is enabled and schedule task reminders
            try:
                # Get user account data
                user_data_result = get_user_data(active_user_id, 'account')
                user_account = user_data_result.get('account')
                if user_account and user_account.get('features', {}).get('task_management') == 'enabled':
                    self.schedule_all_task_reminders(active_user_id)
                    logger.info(f"Rescheduled task reminders for user {active_user_id}")
                else:
                    logger.info(f"Task management disabled for user {active_user_id}, skipping task reminder scheduling")
            except Exception as e:
                logger.error(f"Error rescheduling task reminders for user {active_user_id}: {e}")
        elif category == "checkin":
            # For check-ins, use the standard scheduling
            self.schedule_daily_message_job(user_id=active_user_id, category=category)
        else:
            # For regular message categories, use the standard scheduling
            self.schedule_daily_message_job(user_id=active_user_id, category=category)
    
        logger.info(f"Scheduler reset and rescheduled daily messages for active user: {active_user_id}, category: {category}.")

    @handle_errors("checking if job exists for category", default_return=False)
    def is_job_for_category(self, job, user_id, category):
        """Determines if a job is scheduled for a specific user and category."""
        if job is None:
            # Check all jobs for this user and category
            for existing_job in schedule.jobs:
                # Check if this is a daily scheduler job for this user/category
                if (hasattr(existing_job.job_func, 'func') and 
                    existing_job.job_func.func == self.schedule_daily_message_job and 
                    hasattr(existing_job.job_func, 'keywords') and 
                    existing_job.job_func.keywords.get('user_id') == user_id and 
                    existing_job.job_func.keywords.get('category') == category):
                    logger.debug(f"Found existing daily job for user {user_id}, category {category}")
                    return True
            logger.debug(f"No existing daily job found for user {user_id}, category {category}")
            return False
        else:
            # Check specific job
            if (hasattr(job.job_func, 'func') and 
                job.job_func.func == self.schedule_daily_message_job and 
                hasattr(job.job_func, 'keywords') and 
                job.job_func.keywords.get('user_id') == user_id and 
                job.job_func.keywords.get('category') == category):
                return True
            return False
    
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
        tz = pytz.timezone('America/Regina')
        now_datetime = datetime.now(tz)
        logger.info(f"Current time for scheduling: {now_datetime.strftime('%Y-%m-%d %H:%M')}")
        
        for user_id in user_ids:
            try:
                # Schedule regular message categories
                prefs_result = get_user_data(user_id, 'preferences')
                categories = prefs_result.get('preferences', {}).get('categories', [])
                if isinstance(categories, list):
                    if categories:  # Only process if list is not empty
                        for category in categories:
                            try:
                                self.schedule_daily_message_job(user_id, category)
                                total_scheduled += 1
                                logger.debug(f"Scheduled messages for user {user_id}, category {category}")
                            except Exception as e:
                                logger.error(f"Failed to schedule for user {user_id}, category {category}: {e}")
                    # Empty list is fine - no warning needed
                else:
                    logger.warning(f"Expected list for categories, got {type(categories)} for user '{user_id}'")
                
                # Schedule check-ins if enabled
                try:
                    # Get user account data
                    user_data_result = get_user_data(user_id, 'account')
                    user_account = user_data_result.get('account')
                    if user_account and user_account.get('features', {}).get('checkins') == 'enabled':
                        # Check if check-in category exists in schedules
                        time_periods = get_schedule_time_periods(user_id, "checkin")
                        if time_periods:
                            self.schedule_daily_message_job(user_id, "checkin")
                            total_scheduled += 1
                            logger.debug(f"Scheduled check-ins for user {user_id}")
                        else:
                            logger.debug(f"No check-in schedule found for user {user_id}")
                except Exception as e:
                    logger.error(f"Failed to schedule check-ins for user {user_id}: {e}")
                    
                # Schedule task reminders if tasks are enabled
                try:
                    self.schedule_all_task_reminders(user_id)
                except Exception as e:
                    logger.error(f"Failed to schedule task reminders for user {user_id}: {e}")
                    
            except Exception as e:
                logger.error(f"Failed to get categories for user {user_id}: {e}")
        
        logger.info(f"Scheduling complete: {total_scheduled} user/category combinations scheduled (includes checkins if enabled)")
        
        # Log consolidated scheduler status
        active_jobs = len(schedule.jobs)
        if active_jobs > 0:
            # Count job types for diagnostic purposes
            job_types = {}
            for job in schedule.jobs:
                job_func_name = job.job_func.__name__
                job_types[job_func_name] = job_types.get(job_func_name, 0) + 1
            
            job_type_summary = ", ".join([f"{count} {name}" for name, count in job_types.items()])
            logger.info(f"Scheduler status: {active_jobs} total jobs ({job_type_summary})")
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
            prefs_result = get_user_data(user_id, 'preferences')
            categories = prefs_result.get('preferences', {}).get('categories', [])
            if isinstance(categories, list) and categories:
                for category in categories:
                    try:
                        self.schedule_daily_message_job(user_id, category)
                        logger.info(f"Scheduled messages for new user {user_id}, category {category}")
                    except Exception as e:
                        logger.error(f"Failed to schedule for new user {user_id}, category {category}: {e}")
            
            # Schedule check-ins if enabled
            try:
                # Get user account data
                user_data_result = get_user_data(user_id, 'account')
                user_account = user_data_result.get('account')
                if user_account and user_account.get('features', {}).get('checkins') == 'enabled':
                    # Check if check-in category exists in schedules
                    time_periods = get_schedule_time_periods(user_id, "checkin")
                    if time_periods:
                        self.schedule_daily_message_job(user_id, "checkin")
                        logger.info(f"Scheduled check-ins for new user {user_id}")
                    else:
                        logger.debug(f"No check-in schedule found for new user {user_id}")
            except Exception as e:
                logger.error(f"Failed to schedule check-ins for new user {user_id}: {e}")
                
            # Schedule task reminders if tasks are enabled
            try:
                self.schedule_all_task_reminders(user_id)
                logger.info(f"Scheduled task reminders for new user {user_id}")
            except Exception as e:
                logger.error(f"Failed to schedule task reminders for new user {user_id}: {e}")
                
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
        
        # Schedule daily log archival at 02:00 (after user scheduling)
        schedule.every().day.at("02:00").do(self.perform_daily_log_archival)
        logger.info("Scheduled new daily job for log archival at 02:00")
        
        # Schedule the next day's full daily scheduler job at 01:00
        schedule.every().day.at("01:00").do(self.run_full_daily_scheduler)
        logger.info("Scheduled full daily scheduler job at 01:00 (includes checkins, task reminders, cleanup, and backup check)")
        
        # Schedule periodic orphaned reminder cleanup at 03:00 daily
        schedule.every().day.at("03:00").do(self.cleanup_orphaned_task_reminders)
        logger.info("Scheduled daily orphaned task reminder cleanup at 03:00")
        
        # Schedule data directory cleanup at 04:00 daily (after backups and reminders)
        try:
            from core.auto_cleanup import cleanup_data_directory, cleanup_tests_data_directory
            schedule.every().day.at("04:00").do(cleanup_data_directory)
            logger.info("Scheduled daily data directory cleanup at 04:00")
            # Also clean up tests/data directory
            schedule.every().day.at("04:05").do(cleanup_tests_data_directory)
            logger.info("Scheduled daily tests data directory cleanup at 04:05")
        except Exception as e:
            logger.warning(f"Failed to schedule data directory cleanup: {e}")
        
        # Log job count after daily job scheduling
        active_jobs = len(schedule.jobs)
        logger.info(f"Full daily scheduler complete: {active_jobs} total active jobs scheduled")

    @handle_errors("scheduling daily message job")
    def schedule_daily_message_job(self, user_id, category):
        """
        Schedules daily messages immediately for the specified user and category.
        Schedules one message per active period in the category.
        """
        logger.info(f"Scheduling daily messages immediately for user {user_id}, category {category}.")

        # Clean up old jobs for this user and category
        self.cleanup_old_tasks(user_id, category)

        # Get all time periods for this user and category
        time_periods = get_schedule_time_periods(user_id, category)
        if not time_periods:
            logger.error(f"No time periods found for user {user_id}, category {category}.")
            return

        # Schedule a message for each active period
        scheduled_count = 0
        from datetime import datetime
        today_name = datetime.now().strftime('%A')
        for period_name, period_data in time_periods.items():
            # Skip the "ALL" period - it should not be scheduled, only used as fallback
            if period_name == "ALL":
                logger.debug(f"Skipping ALL period scheduling for user {user_id}, category {category} - ALL is fallback only")
                continue
            # Check if this period is active (default to active if not specified)
            if period_data.get('active', True):
                # If 'days' is present, only schedule if today is in days or if days contains "ALL"
                if 'days' in period_data:
                    days = period_data['days']
                    if "ALL" in days:
                        # Schedule for all days
                        logger.debug(f"Scheduling period {period_name} for user {user_id}, category {category} (ALL days)")
                    elif today_name in days:
                        # Schedule for today
                        logger.debug(f"Scheduling period {period_name} for user {user_id}, category {category} (today: {today_name})")
                    else:
                        logger.debug(f"Skipping period {period_name} for user {user_id}, category {category} (not scheduled for today: {today_name})")
                        continue
                try:
                    self.schedule_message_for_period(user_id, category, period_name)
                    scheduled_count += 1
                    logger.debug(f"Scheduled message for user {user_id}, category {category}, period {period_name}")
                except Exception as e:
                    logger.error(f"Failed to schedule message for user {user_id}, category {category}, period {period_name}: {e}")
            else:
                logger.debug(f"Skipping inactive period {period_name} for user {user_id}, category {category}")

        logger.info(f"Scheduled {scheduled_count} messages for user {user_id}, category {category}")

    @handle_errors("scheduling message for specific period")
    def schedule_message_for_period(self, user_id, category, period_name):
        """
        Schedules a message at a random time within a specific period for a user and category.
        """
        logger.info(f"Scheduling message for period '{period_name}' for user {user_id}, category {category}.")

        max_retries = 10
        retry_count = 0

        while retry_count < max_retries:
            # Get a random time within the specified period
            random_time_str = self.get_random_time_within_period(user_id, category, period_name)
            if not random_time_str:
                logger.error(f"Could not generate random time for user {user_id}, category {category}, period {period_name}.")
                return

            # Try to schedule the message
            try:
                datetime_str = random_time_str
                schedule_datetime = load_and_localize_datetime(datetime_str, 'America/Regina')
                now = datetime.now(pytz.timezone('America/Regina'))

                logger.info(f"Attempting to schedule message for user {user_id}, category {category}, period {period_name} at {schedule_datetime} (now is {now})")

                if not self.is_time_conflict(user_id, schedule_datetime):
                    if schedule_datetime <= now:
                        schedule_datetime += timedelta(days=1)
                        logger.info(f"Adjusted scheduling time to future for user {user_id}: {schedule_datetime}")

                    time_part = schedule_datetime.strftime('%H:%M')
                    # Schedule as one-time job that will remove itself after execution
                    schedule.every().day.at(time_part).do(self.handle_sending_scheduled_message, user_id=user_id, category=category)
                    logger.info(f"Successfully scheduled {category} message for user {user_id}, period {period_name} at {time_part} on {schedule_datetime.strftime('%Y-%m-%d')}.")

                    # Set the wake timer for the scheduled time
                    self.set_wake_timer(schedule_datetime, user_id, category, period_name)
                    break  # Exit the loop after successfully scheduling the message
                else:
                    logger.info(f"Conflict detected for user {user_id}, category {category}, period {period_name} at {schedule_datetime}. Retrying...")
                    retry_count += 1

            except Exception as e:
                logger.error(f"Error while scheduling {category} message for user {user_id}, period {period_name}: {str(e)}")
                retry_count += 1

        if retry_count == max_retries:
            logger.warning(f"Max retries reached. Could not find a suitable time for user {user_id}, category {category}, period {period_name}.")

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
                logger.error(f"No time period '{period_name}' found for check-in scheduling for user {user_id}")
                return

            period_data = time_periods[period_name]
            # Use canonical keys with fallback to legacy keys
            checkin_time = period_data.get('start_time') or period_data.get('start')
            if not checkin_time:
                logger.error(f"Missing start time for check-in period {period_name} in user {user_id}")
                return
            
            # Create datetime for today at the specified time
            tz = pytz.timezone('America/Regina')
            now = datetime.now(tz)
            today = now.date()
            
            # Parse the check-in time
            hour, minute = map(int, checkin_time.split(':'))
            schedule_datetime = datetime.combine(today, datetime.min.time().replace(hour=hour, minute=minute), tzinfo=tz)
            
            # If the time has already passed today, schedule for tomorrow
            if schedule_datetime <= now:
                schedule_datetime += timedelta(days=1)
                logger.info(f"Check-in time has passed today, scheduling for tomorrow: {schedule_datetime}")

            # Schedule the check-in
            time_part = schedule_datetime.strftime('%H:%M')
            schedule.every().day.at(time_part).do(self.handle_sending_scheduled_message, user_id=user_id, category="checkin")
            logger.info(f"Successfully scheduled check-in for user {user_id} at {time_part} on {schedule_datetime.strftime('%Y-%m-%d')}.")

            # Set the wake timer for the scheduled time
            self.set_wake_timer(schedule_datetime, user_id, "checkin", period_name)
            
        except Exception as e:
            logger.error(f"Error scheduling check-in for user {user_id}: {e}")

    @handle_errors("scheduling message at random time")
    def schedule_message_at_random_time(self, user_id, category):
        """
        Schedules a message at a random time within the user's preferred time periods.
        """
        logger.info(f"Scheduling message at random time for user {user_id}, category {category}.")

        # Get all available time periods for this user and category
        time_periods = get_schedule_time_periods(user_id, category)
        if not time_periods:
            logger.error(f"No time periods found for user {user_id}, category {category}.")
            return

        # Use the first available period (they're already sorted by start time)
        available_periods = list(time_periods.keys())
        if not available_periods:
            logger.error(f"No available periods for user {user_id}, category {category}.")
            return

        # Use the first period (they're already sorted by start time)
        selected_period = available_periods[0]
        logger.info(f"Using period '{selected_period}' for user {user_id}, category {category}")

        max_retries = 10
        retry_count = 0

        while retry_count < max_retries:
            # Get a random time within the selected period
            random_time_str = self.get_random_time_within_period(user_id, category, selected_period)
            if not random_time_str:
                logger.error(f"Could not generate random time for user {user_id}, category {category}.")
                return

            # Try to schedule the message
            try:
                datetime_str = random_time_str
                schedule_datetime = load_and_localize_datetime(datetime_str, 'America/Regina')
                now = datetime.now(pytz.timezone('America/Regina'))

                logger.info(f"Attempting to schedule message for user {user_id}, category {category} at {schedule_datetime} (now is {now})")

                if not self.is_time_conflict(user_id, schedule_datetime):
                    if schedule_datetime <= now:
                        schedule_datetime += timedelta(days=1)
                        logger.info(f"Adjusted scheduling time to future for user {user_id}: {schedule_datetime}")

                    time_part = schedule_datetime.strftime('%H:%M')
                    schedule.every().day.at(time_part).do(self.handle_sending_scheduled_message, user_id=user_id, category=category)
                    logger.info(f"Successfully scheduled {category} message for user {user_id} at {time_part} on {schedule_datetime.strftime('%Y-%m-%d')}.")

                    # Set the wake timer for the scheduled time
                    self.set_wake_timer(schedule_datetime, user_id, category, selected_period)
                    break  # Exit the loop after successfully scheduling the message
                else:
                    logger.info(f"Conflict detected for user {user_id}, category {category} at {schedule_datetime}. Retrying...")
                    retry_count += 1

            except Exception as e:
                logger.error(f"Error while scheduling {category} message for user {user_id}: {str(e)}")
                retry_count += 1

        if retry_count == max_retries:
            logger.warning(f"Max retries reached. Could not find a suitable time for user {user_id}, category {category}.")

    @handle_errors("checking time conflict", default_return=False)
    def is_time_conflict(self, user_id, schedule_datetime):
        """Checks if there is a time conflict with any existing scheduled jobs for the user."""
        for job in schedule.jobs:
            if job.job_func.args and job.job_func.args[0] == user_id:
                job_time = job.next_run
                # Increase conflict window to 2 hours to prevent multiple messages at similar times
                if abs((job_time - schedule_datetime).total_seconds()) < 7200:  # 2 hours = 7200 seconds
                    return True
        return False

    @handle_errors("getting random time within period", default_return=None)
    def get_random_time_within_period(self, user_id, category, period, timezone_str='America/Regina'):
        """Get a random time within a specified period for a given category."""
        tz = pytz.timezone(timezone_str)
        now_datetime = datetime.now(tz)
        
        time_periods = get_schedule_time_periods(user_id, category)
        
        # Add validation for period existence
        if period not in time_periods:
            logger.error(f"Period '{period}' not found in time periods for user {user_id}, category {category}. Available periods: {list(time_periods.keys())}")
            return None
            
        # Use canonical keys with fallback to legacy keys
        start_time = time_periods[period].get('start_time') or time_periods[period].get('start')
        end_time = time_periods[period].get('end_time') or time_periods[period].get('end')
        
        if not start_time or not end_time:
            logger.error(f"Missing start/end time for period {period} in user {user_id}, category {category}")
            return None
            
        period_start_time = datetime.strptime(start_time, "%H:%M").time()
        period_end_time = datetime.strptime(end_time, "%H:%M").time()

        # Create datetime objects for today
        start_datetime = datetime.combine(now_datetime.date(), period_start_time, tzinfo=tz)
        end_datetime = datetime.combine(now_datetime.date(), period_end_time, tzinfo=tz)

        # If the period has already ended today, schedule for tomorrow
        if end_datetime <= now_datetime:
            start_datetime += timedelta(days=1)
            end_datetime += timedelta(days=1)
        # If the period is currently active or about to start within the next 30 minutes, schedule for tomorrow
        elif start_datetime <= now_datetime + timedelta(minutes=30):
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

        random_time_str = random_datetime.strftime("%Y-%m-%d %H:%M")
        logger.info(f"Scheduled random time: {random_time_str}")
        return random_time_str

    @handle_errors("logging scheduled tasks")
    def log_scheduled_tasks(self):
        """Logs all current and upcoming scheduled tasks in a user-friendly manner."""
        for job in schedule.jobs:
            next_run = job.next_run.strftime('%Y-%m-%d %H:%M:%S') if job.next_run else 'None'
            task_name = job.job_func.__name__ if hasattr(job.job_func, '__name__') else 'Scheduled Task'
            task_description = str(job.job_func).split('function ')[-1].split(' at ')[0] if 'function' in str(job.job_func) else task_name

            category = 'Generic Task'
            if hasattr(job.job_func, 'func') and hasattr(job.job_func, 'args') and job.job_func.args:
                category = job.job_func.args[0]

            logger.info(f"Task: {task_description}, Category: {category}, Scheduled at: {job.at_time}, Next run: {next_run}")

    @handle_errors("handling sending scheduled message")
    def handle_sending_scheduled_message(self, user_id, category, retry_attempts=3, retry_delay=30):
        """
        Handles the sending of scheduled messages with retries.
        This is a one-time job that removes itself after execution.
        """
        if self.communication_manager is None:
            logger.error("Communication manager is not initialized.")
            return

        attempt = 0
        while attempt < retry_attempts:
            try:
                # Try to send the message
                self.communication_manager.handle_message_sending(user_id, category)
                logger.info(f"Message sent successfully for user {user_id}, category {category}.")
                
                # Remove this job after successful execution to make it a one-time job
                self._remove_user_message_job(user_id, category)
                return  # Exit after successful execution
            except Exception as e:
                logger.error(f"Error sending message for user {user_id}, category {category}: {e}")
                attempt += 1
                logger.info(f"Retrying in {retry_delay} seconds... ({attempt}/{retry_attempts})")
                time.sleep(retry_delay)  # Wait before retrying
        
        # Remove job even if it failed after all retries
        self._remove_user_message_job(user_id, category)

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
                if (hasattr(job.job_func, 'func') and 
                    job.job_func.func == self.handle_sending_scheduled_message and
                    len(job.job_func.args) >= 2 and
                    job.job_func.args[0] == user_id and 
                    job.job_func.args[1] == category):
                    jobs_to_remove.append(job)
            
            # Remove the jobs
            for job in jobs_to_remove:
                schedule.jobs.remove(job)
                logger.debug(f"Removed one-time job for user {user_id}, category {category}")
            
            if jobs_to_remove:
                logger.info(f"Removed {len(jobs_to_remove)} completed message job(s) for user {user_id}, category {category}")
            
        except Exception as e:
            logger.error(f"Error removing user message job for user {user_id}, category {category}: {e}")

    @handle_errors("handling task reminder")
    def handle_task_reminder(self, user_id, task_id, retry_attempts=3, retry_delay=30):
        """
        Handles sending task reminders with retries.
        """
        if self.communication_manager is None:
            logger.error("Communication manager is not initialized.")
            return

        attempt = 0
        while attempt < retry_attempts:
            try:
                # Import task management functions
                from tasks.task_management import get_task_by_id, update_task
                
                # Get the task details
                task = get_task_by_id(user_id, task_id)
                if not task:
                    logger.error(f"Task {task_id} not found for user {user_id}")
                    return
                
                # Check if task is still active and not already completed
                if task.get('completed', False):
                    logger.info(f"Task {task_id} is already completed, skipping reminder")
                    return
                
                # Send the task reminder via communication manager
                self.communication_manager.handle_task_reminder(user_id, task_id)
                
                # Mark reminder as sent
                update_task(user_id, task_id, {'reminder_sent': True})
                
                logger.info(f"Task reminder sent successfully for user {user_id}, task {task_id}")
                return  # Exit after successful execution
                
            except Exception as e:
                logger.error(f"Error sending task reminder for user {user_id}, task {task_id}: {e}")
                attempt += 1
                logger.info(f"Retrying in {retry_delay} seconds... ({attempt}/{retry_attempts})")
                time.sleep(retry_delay)  # Wait before retrying
    
    @handle_errors("setting wake timer")
    def set_wake_timer(self, schedule_time, user_id, category, period, wake_ahead_minutes=4):
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
        if os.getenv('MHM_TESTING') == '1':
            logger.debug(f"Skipping wake timer creation for test user {user_id} (MHM_TESTING=1)")
            return
        
        # Additional safety check: verify user data directory is not in tests directory
        try:
            from core.config import get_user_data_dir, BASE_DATA_DIR
            user_data_dir = get_user_data_dir(user_id)
            if user_data_dir and ('tests' in user_data_dir or 'test' in BASE_DATA_DIR.lower()):
                logger.debug(f"Skipping wake timer creation for test user {user_id} (test data directory detected)")
                return
        except Exception as e:
            logger.debug(f"Could not verify user data directory for {user_id}: {e}")
            # If we can't verify, err on the side of caution and skip task creation
            if os.getenv('MHM_TESTING') == '1':
                return
        
        # Adjust the schedule_time to wake the computer a few minutes earlier
        wake_time = schedule_time - timedelta(minutes=wake_ahead_minutes)
        task_name = f"Wake_{user_id}_{category}_{period}_{wake_time.strftime('%H%M')}"
        task_time = wake_time.strftime("%H:%M")
        task_date = wake_time.strftime("%Y-%m-%d")

        # PowerShell script to create the task with Wake computer enabled
        ps_command = f"""
        $action = New-ScheduledTaskAction -Execute 'cmd.exe' -Argument '/c exit'
        $trigger = New-ScheduledTaskTrigger -Once -At "{task_date}T{task_time}:00"
        $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -WakeToRun
        Register-ScheduledTask -TaskName "{task_name}" -Action $action -Trigger $trigger -Settings $settings -Force
        """

        # Execute the PowerShell command and capture the output
        result = subprocess.run(["powershell", "-Command", ps_command], capture_output=True, text=True)

        if result.returncode == 0:
            logger.info(f"Wake timer set for {wake_time.strftime('%Y-%m-%d %H:%M')} with task {task_name}")
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
        logger.info(f"In-memory scheduler cleanup completed for user {user_id}, category {category}. Removed {jobs_removed} jobs (from {initial_job_count} to {final_job_count} total jobs).")
    
    @handle_errors("clearing all accumulated jobs")
    def clear_all_accumulated_jobs(self):
        """Clears all accumulated scheduler jobs and reschedules only the necessary ones."""
        logger.info("Clearing all accumulated scheduler jobs...")
        
        # Count jobs before cleanup
        initial_job_count = len(schedule.jobs)
        logger.info(f"Initial job count: {initial_job_count} (accumulated jobs to be cleared)")
        
        # Clear all jobs
        schedule.clear()
        logger.info("All scheduler jobs cleared")
        
        # Don't reschedule daily jobs here - the main scheduler loop will handle that
        # This function is only for clearing accumulated jobs, not scheduling new ones
        
        final_job_count = len(schedule.jobs)
        jobs_cleared = initial_job_count - final_job_count
        
        # Log cleanup results in a single message
        if jobs_cleared > 0:
            logger.info(f"Job cleanup complete: {jobs_cleared} accumulated jobs cleared")
        elif jobs_cleared == 0:
            logger.debug("Job cleanup complete: No accumulated jobs to clear (system was already clean)")
        else:
            logger.info(f"Job cleanup complete: Added {abs(jobs_cleared)} scheduler jobs (system had fewer jobs than expected)")

        # Cleanup system tasks for all users/categories
        logger.info("Starting system task cleanup for all users...")
        system_tasks_cleaned = 0
        
        try:
            result = subprocess.run(['schtasks', '/query', '/fo', 'LIST', '/v'], 
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if result.returncode != 0:
                logger.debug(f"Could not query system tasks: {result.stderr}")
                logger.info("System task cleanup completed (no tasks to clean).")
                return
            
            tasks = result.stdout.splitlines()
            tasks_deleted = 0

            # Get user IDs for task cleanup
            user_ids = get_all_user_ids()
            
            # Look for tasks with our user ID prefixes
            for line in tasks:
                if line.startswith("TaskName:"):
                    task_name = line.split(":")[1].strip()
                    # Check if this is one of our MHM wake tasks
                    if "Wake_" in task_name and any(user_id in task_name for user_id in user_ids):
                        logger.info(f"Deleting old system task: {task_name}")
                        try:
                            # Use check=False to prevent exceptions on missing tasks
                            del_result = subprocess.run(['schtasks', '/delete', '/tn', task_name, '/f'], 
                                                      stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False)
                            if del_result.returncode == 0:
                                tasks_deleted += 1
                                logger.debug(f"Successfully deleted task: {task_name}")
                            else:
                                # Task probably doesn't exist anymore - this is fine
                                logger.debug(f"Task {task_name} may already be deleted: {del_result.stderr}")
                        except Exception as del_error:
                            logger.debug(f"Error deleting task {task_name}: {del_error}")

            logger.info(f"System task cleanup completed: {tasks_deleted} tasks deleted.")
            if tasks_deleted > 0:
                logger.debug(f"Deleted {tasks_deleted} old system tasks")
                
        except Exception as query_error:
            logger.debug(f"Error querying system tasks for cleanup: {query_error}")
            logger.info(f"System task cleanup skipped (query failed).")

    @handle_errors("scheduling all task reminders")
    def schedule_all_task_reminders(self, user_id):
        """
        Schedule reminders for all active tasks for a user.
        For each reminder period, pick one random task and schedule it at a random time within the period.
        """
        try:
            from tasks.task_management import load_active_tasks, are_tasks_enabled
            from core.schedule_management import get_schedule_time_periods
            import random
            
            # Check if tasks are enabled for this user
            if not are_tasks_enabled(user_id):
                logger.debug(f"Tasks not enabled for user {user_id}")
                return
            
            # Get user's configured task reminder periods from the periods structure
            task_periods = get_schedule_time_periods(user_id, 'tasks')
            if not task_periods:
                logger.debug(f"No task reminder periods configured for user {user_id}")
                return
            
            # Load active tasks
            active_tasks = load_active_tasks(user_id)
            
            # Filter to only incomplete tasks
            incomplete_tasks = [task for task in active_tasks if not task.get('completed', False)]
            
            if not incomplete_tasks:
                logger.debug(f"No incomplete tasks found for user {user_id}")
                return
            
            scheduled_count = 0
            
            # For each active task reminder period, pick one random task and schedule it
            for period_name, period_data in task_periods.items():
                if not period_data.get('active', True):
                    continue
                
                # Pick one random task for this period
                selected_task = self.select_task_for_reminder(incomplete_tasks)
                
                if not selected_task:
                    logger.debug(f"No task selected for period {period_name} for user {user_id}")
                    continue
                
                # Use canonical keys with fallback to legacy keys for task reminder periods
                start_time = period_data.get('start_time') or period_data.get('start')
                end_time = period_data.get('end_time') or period_data.get('end')
                
                if not start_time or not end_time:
                    logger.warning(f"Missing start/end time for task reminder period '{period_name}' in user {user_id}")
                    continue
                
                # Generate a random time within the period
                random_time = self.get_random_time_within_task_period(start_time, end_time)
                if not random_time:
                    logger.warning(f"Could not generate random time for period {start_time}-{end_time}")
                    continue
                
                # Schedule the task reminder
                if self.schedule_task_reminder_at_time(user_id, selected_task['task_id'], random_time):
                    scheduled_count += 1
                    logger.info(f"Scheduled reminder for task '{selected_task['title']}' at {random_time} (period: {period_name} {start_time}-{end_time})")
            
            logger.info(f"Scheduled {scheduled_count} task reminders for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error scheduling task reminders for user {user_id}: {e}")

    @handle_errors("selecting task for reminder with priority and due date weighting")
    def _select_task_for_reminder__handle_edge_cases(self, incomplete_tasks):
        """Handle edge cases for task selection."""
        if not incomplete_tasks:
            return None
        
        # If only one task, return it
        if len(incomplete_tasks) == 1:
            return incomplete_tasks[0]
        
        return "PROCEED"  # Signal to continue with normal processing

    @handle_errors("calculating priority weight for task reminder")
    def _select_task_for_reminder__calculate_priority_weight(self, task):
        """Calculate priority-based weight for a task."""
        priority = task.get('priority', 'medium').lower()
        priority_multipliers = {
            'critical': 3.0,  # Critical priority tasks 3x more likely
            'high': 2.0,      # High priority tasks 2x more likely
            'medium': 1.5,    # Medium priority tasks 1.5x more likely
            'low': 1.0,       # Low priority tasks base weight
            'none': 0.8       # No priority tasks slightly less likely
        }
        return priority_multipliers.get(priority, 1.0)

    def _select_task_for_reminder__calculate_due_date_weight(self, task, today):
        """Calculate due date proximity weight for a task."""
        due_date_str = task.get('due_date')
        if not due_date_str:
            # No due date: slight reduction to encourage setting due dates
            return 0.9
        
        try:
            from datetime import datetime
            due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
            days_until_due = (due_date - today).days
            
            # Sliding scale calculation
            if days_until_due < 0:
                # Overdue tasks: exponential increase based on how overdue
                # Formula: 2.5 + (days_overdue * 0.1), max 4.0
                days_overdue = abs(days_until_due)
                return min(2.5 + (days_overdue * 0.1), 4.0)
            elif days_until_due == 0:
                # Due today: maximum weight
                return 2.5
            elif days_until_due <= 7:
                # Due within a week: sliding scale from 2.5 to 1.0
                # Formula: 2.5 - (days_until_due * 0.2)
                return max(2.5 - (days_until_due * 0.2), 1.0)
            elif days_until_due <= 30:
                # Due within a month: sliding scale from 1.0 to 0.8
                # Formula: 1.0 - (days_until_due - 7) * 0.01
                return max(1.0 - (days_until_due - 7) * 0.01, 0.8)
            else:
                # Due later than a month: base weight
                return 0.8
        except ValueError:
            # Invalid date format, use base weight
            return 1.0

    @handle_errors("calculating task weights for reminder selection")
    def _select_task_for_reminder__calculate_task_weights(self, incomplete_tasks, today):
        """Calculate weights for all tasks."""
        task_weights = []
        
        for task in incomplete_tasks:
            weight = 1.0  # Base weight
            
            # Apply priority weighting
            priority_multiplier = self._select_task_for_reminder__calculate_priority_weight(task)
            weight *= priority_multiplier
            
            # Apply due date proximity weighting
            due_date_multiplier = self._select_task_for_reminder__calculate_due_date_weight(task, today)
            weight *= due_date_multiplier
            
            task_weights.append((task, weight))
        
        return task_weights

    @handle_errors("building task key for reminder selection", default_return="")
    def _select_task_for_reminder__task_key(self, task: Dict[str, Any], index: int) -> str:
        """Build a stable key for tracking reminder selection state."""
        candidate_keys = [
            str(task.get('id') or '').strip(),
            str(task.get('task_id') or '').strip(),
            str(task.get('uuid') or '').strip(),
            str(task.get('title') or '').strip()
        ]
        # Fall back to index when no identifier data is present
        base_key = next((key for key in candidate_keys if key), f"idx-{index}")
        return f"{base_key}|{index}"
    
    @handle_errors("selecting task by weight for reminder", default_return=None)
    def _select_task_for_reminder__select_task_by_weight(self, task_weights, incomplete_tasks):
        """Select a task based on calculated weights using weighted random selection."""
        import random
        
        if not task_weights:
            return random.choice(incomplete_tasks) if incomplete_tasks else None
        
        total_weight = sum(weight for _, weight in task_weights)
        if total_weight <= 0:
            # Fallback to random selection if all weights are zero or invalid
            return random.choice(incomplete_tasks)
        
        # Use weighted random selection for proper semi-random behavior
        # This ensures higher-weighted tasks are more likely but not always selected
        rand_value = random.uniform(0, total_weight)
        cumulative_weight = 0.0
        
        # Clean up stale state first
        active_keys = {self._select_task_for_reminder__task_key(t, i) 
                      for i, (t, _) in enumerate(task_weights)}
        for key in list(self._reminder_selection_state.keys()):
            if key not in active_keys:
                self._reminder_selection_state.pop(key, None)
        
        for index, (task, weight) in enumerate(task_weights):
            cumulative_weight += weight
            if rand_value <= cumulative_weight:
                # Update accumulated state for smooth distribution over time
                task_key = self._select_task_for_reminder__task_key(task, index)
                previous_score = self._reminder_selection_state.get(task_key, 0.0)
                self._reminder_selection_state[task_key] = previous_score + weight
                
                return task
        
        # Fallback to last task if something went wrong
        return task_weights[-1][0] if task_weights else random.choice(incomplete_tasks)

    @handle_errors("selecting task for reminder", default_return=None)
    def select_task_for_reminder(self, incomplete_tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Select a task for reminder using priority-based and due date proximity weighting.
        
        Args:
            incomplete_tasks: List of incomplete tasks to choose from
            
        Returns:
            Selected task dictionary
        """
        from datetime import datetime
        
        # Handle edge cases
        edge_case_result = self._select_task_for_reminder__handle_edge_cases(incomplete_tasks)
        if edge_case_result != "PROCEED":
            return edge_case_result
        
        # Calculate weights for each task
        today = datetime.now().date()
        task_weights = self._select_task_for_reminder__calculate_task_weights(incomplete_tasks, today)
        
        # Select task based on weights
        selected_task = self._select_task_for_reminder__select_task_by_weight(task_weights, incomplete_tasks)
        
        logger.debug(f"Selected task '{selected_task.get('title', 'Unknown')}' with priority '{selected_task.get('priority', 'medium')}' and due date '{selected_task.get('due_date', 'None')}'")
        
        return selected_task

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
        try:
            from datetime import datetime, timedelta
            import random
            
            # Parse start and end times
            start_dt = datetime.strptime(start_time, "%H:%M")
            end_dt = datetime.strptime(end_time, "%H:%M")
            
            # If end time is before start time, it means the period spans midnight
            # For now, we'll assume it's the same day
            if end_dt < start_dt:
                end_dt += timedelta(days=1)
            
            # Calculate total seconds in the period
            total_seconds = (end_dt - start_dt).total_seconds()
            
            if total_seconds <= 0:
                logger.error(f"Invalid time range: {start_time} to {end_time}")
                return None
            
            # Generate random seconds within the period
            random_seconds = random.randint(0, int(total_seconds))
            random_dt = start_dt + timedelta(seconds=random_seconds)
            
            # Format as HH:MM
            random_time = random_dt.strftime("%H:%M")
            
            logger.debug(f"Generated random time {random_time} within period {start_time}-{end_time}")
            return random_time
            
        except Exception as e:
            logger.error(f"Error generating random time within period {start_time}-{end_time}: {e}")
            return None

    @handle_errors("scheduling task reminder at specific time")
    def schedule_task_reminder_at_time(self, user_id, task_id, reminder_time):
        """
        Schedule a reminder for a specific task at the specified time (daily).
        """
        try:
            from tasks.task_management import get_task_by_id
            
            # Get the task to verify it exists and is active
            task = get_task_by_id(user_id, task_id)
            if not task:
                logger.error(f"Task {task_id} not found for user {user_id}")
                return False
            
            if task.get('completed', False):
                logger.info(f"Task {task_id} is already completed, skipping reminder scheduling")
                return False
            
            # Parse the reminder time
            try:
                hour, minute = map(int, reminder_time.split(':'))
                time_str = f"{hour:02d}:{minute:02d}"
            except ValueError:
                logger.error(f"Invalid reminder time format: {reminder_time}")
                return False
            
            # Schedule the task reminder
            schedule.every().day.at(time_str).do(self.handle_task_reminder, user_id=user_id, task_id=task_id)
            
            # Set wake timer for the task reminder
            from datetime import datetime, timedelta
            import pytz
            
            # Create datetime for today at the specified time
            tz = pytz.timezone('America/Regina')
            now = datetime.now(tz)
            today = now.date()
            
            # Parse the reminder time
            hour, minute = map(int, time_str.split(':'))
            schedule_datetime = datetime.combine(today, datetime.min.time().replace(hour=hour, minute=minute), tzinfo=tz)
            
            # If the time has already passed today, schedule for tomorrow
            if schedule_datetime <= now:
                schedule_datetime += timedelta(days=1)
            
            # Set wake timer for task reminder
            self.set_wake_timer(schedule_datetime, user_id, "tasks", "task_reminder")
            
            logger.info(f"Scheduled daily task reminder for user {user_id}, task {task_id} at {time_str}")
            return True
            
        except Exception as e:
            logger.error(f"Error scheduling task reminder for user {user_id}, task {task_id}: {e}")
            return False

    @handle_errors("scheduling task reminder")
    def schedule_task_reminder(self, user_id, task_id, reminder_time):
        """
        Legacy function for backward compatibility.
        Schedule a reminder for a specific task at the specified time.
        """
        return self.schedule_task_reminder_at_time(user_id, task_id, reminder_time)

    @handle_errors("scheduling task reminder at specific datetime")
    def schedule_task_reminder_at_datetime(self, user_id, task_id, date_str, time_str):
        """
        Schedule a reminder for a specific task at a specific date and time.
        """
        try:
            from tasks.task_management import get_task_by_id
            from datetime import datetime, timedelta
            
            # Get the task to verify it exists and is active
            task = get_task_by_id(user_id, task_id)
            if not task:
                logger.error(f"Task {task_id} not found for user {user_id}")
                return False
            
            if task.get('completed', False):
                logger.info(f"Task {task_id} is already completed, skipping reminder scheduling")
                return False
            
            # Parse the date and time
            try:
                reminder_datetime = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
            except ValueError:
                logger.error(f"Invalid date/time format: {date_str} {time_str}")
                return False
            
            # Check if the reminder time is in the past
            if reminder_datetime < datetime.now():
                logger.debug(f"Reminder time {reminder_datetime} is in the past, skipping")
                return False
            
            # Calculate delay until the reminder time
            delay_seconds = (reminder_datetime - datetime.now()).total_seconds()
            
            # Schedule the task reminder
            schedule.every(delay_seconds).seconds.do(self.handle_task_reminder, user_id=user_id, task_id=task_id)
            
            logger.info(f"Scheduled one-time task reminder for user {user_id}, task {task_id} at {reminder_datetime}")
            return True
            
        except Exception as e:
            logger.error(f"Error scheduling task reminder for user {user_id}, task {task_id}: {e}")
            return False

    @handle_errors("cleaning up task reminders")
    def cleanup_task_reminders(self, user_id, task_id):
        """
        Clean up all reminders for a specific task.
        
        Finds and removes all APScheduler jobs that call handle_task_reminder for the given task_id.
        Handles both one-time reminders (schedule_task_reminder_at_datetime) and daily reminders (schedule_task_reminder_at_time).
        
        Args:
            user_id: The user's ID
            task_id: The task ID to clean up reminders for
            
        Returns:
            bool: True if cleanup succeeded (or no reminders found), False on error
        """
        try:
            if not user_id or not task_id:
                logger.error(f"Invalid parameters for cleanup_task_reminders: user_id={user_id}, task_id={task_id}")
                return False
            
            # Count jobs before cleanup
            initial_job_count = len(schedule.jobs)
            jobs_to_remove = []
            
            # Find all jobs that call handle_task_reminder with this user_id and task_id
            for job in schedule.jobs:
                try:
                    # Check if this is a task reminder job
                    # Jobs created by schedule_task_reminder_at_datetime use: schedule.every(delay).seconds.do(handle_task_reminder, user_id=..., task_id=...)
                    # Jobs created by schedule_task_reminder_at_time use: schedule.every().day.at(time).do(handle_task_reminder, user_id=..., task_id=...)
                    
                    # Check if job function is handle_task_reminder
                    if hasattr(job.job_func, 'func') and job.job_func.func == self.handle_task_reminder:
                        # Check keyword arguments for user_id and task_id
                        if hasattr(job.job_func, 'keywords'):
                            kwargs = job.job_func.keywords
                            if kwargs.get('user_id') == user_id and kwargs.get('task_id') == task_id:
                                jobs_to_remove.append(job)
                                logger.debug(f"Found reminder job for task {task_id}, user {user_id}")
                    
                    # Also check positional arguments (some job types may use args instead of keywords)
                    elif hasattr(job.job_func, 'args') and len(job.job_func.args) >= 2:
                        args = job.job_func.args
                        # handle_task_reminder signature: (self, user_id, task_id, ...)
                        if len(args) >= 2 and args[0] == user_id and args[1] == task_id:
                            # Verify it's actually handle_task_reminder
                            if hasattr(job.job_func, 'func') and job.job_func.func == self.handle_task_reminder:
                                jobs_to_remove.append(job)
                                logger.debug(f"Found reminder job for task {task_id}, user {user_id} (positional args)")
                
                except Exception as e:
                    # Skip jobs that can't be inspected
                    logger.debug(f"Could not inspect job for cleanup: {e}")
                    continue
            
            # Remove the identified jobs
            jobs_removed = 0
            for job in jobs_to_remove:
                try:
                    schedule.jobs.remove(job)
                    jobs_removed += 1
                    logger.debug(f"Removed reminder job for task {task_id}, user {user_id}")
                except ValueError:
                    # Job was already removed
                    pass
            
            final_job_count = len(schedule.jobs)
            logger.info(f"Cleaned up {jobs_removed} reminder job(s) for task {task_id}, user {user_id} "
                       f"(from {initial_job_count} to {final_job_count} total jobs)")
            
            return True
            
        except Exception as e:
            logger.error(f"Error cleaning up task reminders for task {task_id}, user {user_id}: {e}")
            return False

    @handle_errors("cleaning up orphaned task reminders")
    def cleanup_orphaned_task_reminders(self):
        """
        Periodic cleanup job to remove reminders for tasks that no longer exist.
        
        Scans all scheduled reminder jobs and verifies the associated tasks still exist.
        Removes reminders for tasks that have been deleted or completed.
        Runs daily at 03:00.
        """
        try:
            logger.info("Starting periodic cleanup of orphaned task reminders")
            
            # Get all active users (we'll need to scan their tasks)
            from core.user_data_handlers import get_all_user_ids
            user_ids = get_all_user_ids()
            
            orphaned_count = 0
            total_checked = 0
            
            # Find all task reminder jobs
            jobs_to_check = []
            for job in schedule.jobs:
                try:
                    # Check if this is a task reminder job
                    if hasattr(job.job_func, 'func') and job.job_func.func == self.handle_task_reminder:
                        if hasattr(job.job_func, 'keywords'):
                            kwargs = job.job_func.keywords
                            user_id = kwargs.get('user_id')
                            task_id = kwargs.get('task_id')
                            if user_id and task_id:
                                jobs_to_check.append((job, user_id, task_id))
                                total_checked += 1
                except Exception as e:
                    logger.debug(f"Could not inspect job for orphaned cleanup: {e}")
                    continue
            
            # Check each job's task still exists
            from tasks.task_management import get_task_by_id
            
            for job, user_id, task_id in jobs_to_check:
                try:
                    task = get_task_by_id(user_id, task_id)
                    if not task:
                        # Task doesn't exist - remove the reminder job
                        try:
                            schedule.jobs.remove(job)
                            orphaned_count += 1
                            logger.info(f"Removed orphaned reminder for non-existent task {task_id}, user {user_id}")
                        except ValueError:
                            # Job was already removed
                            pass
                    elif task.get('completed', False):
                        # Task is completed - remove the reminder job
                        try:
                            schedule.jobs.remove(job)
                            orphaned_count += 1
                            logger.info(f"Removed reminder for completed task {task_id}, user {user_id}")
                        except ValueError:
                            # Job was already removed
                            pass
                except Exception as e:
                    logger.debug(f"Error checking task {task_id} for user {user_id}: {e}")
                    continue
            
            logger.info(f"Orphaned reminder cleanup complete: checked {total_checked} reminders, removed {orphaned_count} orphaned reminders")
            
        except Exception as e:
            logger.error(f"Error during orphaned task reminder cleanup: {e}", exc_info=True)

    @handle_errors("performing daily log archival")
    def perform_daily_log_archival(self):
        """
        Perform daily log archival to compress old logs and clean up archives.
        This runs automatically at 02:00 daily via the scheduler.
        """
        try:
            from core.logger import compress_old_logs, cleanup_old_archives
            
            logger.info("Starting daily log archival process")
            
            # Compress logs older than 7 days
            compressed_count = compress_old_logs()
            logger.info(f"Daily log archival: compressed {compressed_count} old log files")
            
            # Clean up archives older than 30 days
            cleaned_count = cleanup_old_archives()
            logger.info(f"Daily log archival: cleaned {cleaned_count} old archive files")
            
            logger.info("Daily log archival process completed successfully")
            
        except Exception as e:
            logger.error(f"Error during daily log archival: {e}")

    @handle_errors("checking and performing weekly backup")
    def check_and_perform_weekly_backup(self):
        """
        Check if a weekly backup is needed and perform it if so.
        Runs during the daily scheduler job at 01:00 (before log archival at 02:00).
        Creates a backup if:
        - No backups exist, OR
        - Last backup is 7+ days old
        Keeps last 10 backups with 30-day retention as configured in BackupManager.
        """
        try:
            # Get list of existing backups
            backups = backup_manager.list_backups()
            
            # Check if backup is needed
            needs_backup = False
            
            if not backups:
                logger.info("No existing backups found - creating first backup")
                needs_backup = True
            else:
                # Get the most recent backup (list is sorted newest first)
                last_backup = backups[0]
                last_backup_time = datetime.fromisoformat(last_backup['created_at'])
                days_since_backup = (datetime.now() - last_backup_time).days
                
                if days_since_backup >= 7:
                    logger.info(f"Last backup was {days_since_backup} days ago - creating new backup")
                    needs_backup = True
                else:
                    logger.debug(f"Backup not needed - last backup was {days_since_backup} days ago")
            
            # Create backup if needed
            if needs_backup:
                logger.info("Starting weekly backup process")
                
                backup_path = backup_manager.create_backup(
                    backup_name=f"weekly_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    include_users=True,
                    include_config=True,
                    include_logs=False
                )
                
                if backup_path:
                    logger.info(f"Weekly backup completed successfully: {backup_path}")
                    
                    # Check backup health
                    backups = backup_manager.list_backups()
                    if backups:
                        latest_backup = backups[0]
                        backup_time = datetime.fromisoformat(latest_backup['created_at'])
                        days_old = (datetime.now() - backup_time).days
                        backup_size_mb = latest_backup.get('file_size', 0) / (1024 * 1024)
                        logger.info(f"Backup health: Latest backup is {days_old} days old, size: {backup_size_mb:.2f} MB")
                    else:
                        logger.warning("No backups found after creation - backup health check failed")
                else:
                    logger.error("Weekly backup failed - no backup path returned")
            
        except Exception as e:
            logger.error(f"Error during weekly backup check: {e}")

    # Task reminders are now managed consistently with other jobs
    # No special cleanup function needed - they're handled by the main scheduler cleanup

# Standalone functions for admin UI access
@handle_errors("running full scheduler standalone", default_return=False)
@handle_errors("running full scheduler standalone", default_return=False)
def run_full_scheduler_standalone():
    """
    Standalone function to run the full scheduler for all users.
    This can be called from the admin UI without needing a scheduler instance.
    """
    from communication.core.channel_orchestrator import CommunicationManager
    from core.scheduler import SchedulerManager
    
    # Create communication manager and scheduler manager
    communication_manager = CommunicationManager()
    scheduler_manager = SchedulerManager(communication_manager)
    
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
    from communication.core.channel_orchestrator import CommunicationManager
    from core.scheduler import SchedulerManager
    
    # Create communication manager and scheduler manager
    communication_manager = CommunicationManager()
    scheduler_manager = SchedulerManager(communication_manager)
    
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
    from communication.core.channel_orchestrator import CommunicationManager
    from core.scheduler import SchedulerManager
    
    # Create communication manager and scheduler manager
    communication_manager = CommunicationManager()
    scheduler_manager = SchedulerManager(communication_manager)
    
    # Run scheduler for the specific user and category
    logger.info(f"Standalone: Running category scheduler for user {user_id}, category {category}")
    scheduler_manager.schedule_daily_message_job(user_id, category)
    
    logger.info(f"Standalone: Category scheduler started successfully for {user_id}, {category}")
    return True

@handle_errors("scheduling all task reminders for user", default_return=None)
def schedule_all_task_reminders(user_id):
    """
    Standalone function to schedule all task reminders for a user.
    This can be called from the admin UI without needing a scheduler instance.
    """
    from tasks.task_management import are_tasks_enabled
    
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

@handle_errors("clearing all accumulated jobs standalone", default_return=False)
def clear_all_accumulated_jobs_standalone():
    """
    Standalone function to clear all accumulated scheduler jobs.
    This can be called from the admin UI or service to fix job accumulation issues.
    """
    from communication.core.channel_orchestrator import CommunicationManager
    
    # Create communication manager and scheduler manager
    communication_manager = CommunicationManager()
    scheduler_manager = SchedulerManager(communication_manager)
    
    # Clear all accumulated jobs
    scheduler_manager.clear_all_accumulated_jobs()
    
    logger.info("Standalone: All accumulated scheduler jobs cleared successfully")
    return True

@handle_errors("processing user schedules", default_return=None)
def process_user_schedules(user_id: str):
    """Process schedules for a specific user."""
    # Get user's categories
    prefs_result = get_user_data(user_id, 'preferences')
    categories = prefs_result.get('preferences', {}).get('categories', [])
    if not categories:
        logger.debug(f"No categories found for user {user_id}")
        return
    
    # Process each category
    for category in categories:
        process_category_schedule(user_id, category)

@handle_errors("processing category schedule", default_return=None)
def process_category_schedule(user_id: str, category: str):
    """Process schedule for a specific user and category."""
    # Create a scheduler instance to process this category
    from communication.core.channel_orchestrator import CommunicationManager
    
    communication_manager = CommunicationManager()
    scheduler_manager = SchedulerManager(communication_manager)
    
    # Schedule messages for this category
    scheduler_manager.schedule_daily_message_job(user_id, category)
    
    logger.info(f"Processed schedule for user {user_id}, category {category}")
