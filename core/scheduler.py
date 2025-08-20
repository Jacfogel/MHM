# scheduler.py

import schedule
import time
import pytz
import threading
import random
import subprocess
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any

from core.user_data_handlers import get_all_user_ids
from core.schedule_management import get_schedule_time_periods, is_schedule_period_active, get_current_time_periods_with_validation
from core.service_utilities import load_and_localize_datetime
from core.logger import get_logger, get_component_logger
from user.user_context import UserContext
from core.error_handling import (
    error_handler, SchedulerError, CommunicationError, handle_errors
)
from core.user_data_handlers import get_user_data

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
        logger.info("SchedulerManager ready")

    @handle_errors("running daily scheduler")
    def run_daily_scheduler(self):
        """
        Starts the daily scheduler in a separate thread that handles all users.
        """
        def scheduler_loop():
            try:
                # Immediately schedule messages for all users when service starts
                self.schedule_all_users_immediately()
                
                # Then set up recurring daily scheduling at 01:00 for all users
                user_ids = get_all_user_ids()
                for user_id in user_ids:
                    # Get user categories
                    prefs_result = get_user_data(user_id, 'preferences')
                    categories = prefs_result.get('preferences', {}).get('categories', [])
                    for category in categories:
                        # Check if a job already exists for this user and category before scheduling
                        if not self.is_job_for_category(None, user_id, category):
                            schedule.every().day.at("01:00").do(self.schedule_daily_message_job, user_id=user_id, category=category)
            except Exception as e:
                logger.error(f"Error scheduling daily jobs: {e}")
                raise
    
            try:
                loop_count = 0
                while not self._stop_event.is_set():  # Check for stop signal
                    schedule.run_pending()
                    loop_count += 1
                    
                    # Log every 60 iterations (60 minutes / 1 hour) instead of every 15 to reduce log spam
                    if loop_count % 60 == 0:
                        active_jobs = len(schedule.jobs)
                        # Only log if there are actually jobs scheduled - don't log 0 jobs
                        if active_jobs > 0:
                            logger.info(f"Scheduler running: {active_jobs} active jobs scheduled")
                        
                    # Use wait instead of sleep to allow immediate shutdown
                    if self._stop_event.wait(timeout=60):  # Wait 60 seconds or until stop signal
                        break
                logger.info("Scheduler loop stopped gracefully.")
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}")
                raise

        self._stop_event.clear()  # Ensure stop event is reset
        self.scheduler_thread = threading.Thread(target=scheduler_loop)
        self.scheduler_thread.daemon = True
        self.scheduler_thread.start()
        logger.info("Scheduler thread started")
        
        # Update last run time after successful scheduling
        self.last_run_time = time.time()

    @handle_errors("stopping scheduler")
    def stop_scheduler(self):
        """Stops the scheduler thread."""
        if self.scheduler_thread is not None and self.scheduler_thread.is_alive():
            logger.info("Stopping scheduler thread...")
            self._stop_event.set()  # Signal the thread to stop
            self.scheduler_thread.join(timeout=5)  # Wait up to 5 seconds for clean shutdown
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
                if existing_job.job_func.args and existing_job.job_func.args[0] == user_id and existing_job.job_func.args[1] == category:
                    return True
            return False
        else:
            # Check specific job
            if job.job_func.args and job.job_func.args[0] == user_id and job.job_func.args[1] == category:
                return True
            return False
    
    @handle_errors("scheduling all users immediately")
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
        
        logger.info(f"Scheduling complete: {total_scheduled} user/category combinations scheduled")

    @handle_errors("scheduling new user")
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
                return  # Exit after successful execution
            except Exception as e:
                logger.error(f"Error sending message for user {user_id}, category {category}: {e}")
                attempt += 1
                logger.info(f"Retrying in {retry_delay} seconds... ({attempt}/{retry_attempts})")
                time.sleep(retry_delay)  # Wait before retrying

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
        # Store jobs we want to keep (not for this user/category)
        jobs_to_keep = []
        for job in schedule.jobs:
            if not self.is_job_for_category(job, user_id, category):
                jobs_to_keep.append(job)
        
        # Clear all jobs and reschedule only the ones we want to keep
        schedule.clear()
        for job in jobs_to_keep:
            # Re-add the job with its original schedule
            if hasattr(job, 'at_time') and job.at_time:
                # Ensure at_time is a string and in the correct format
                at_time_str = str(job.at_time)
                # Extract just the time part if it's a full datetime string
                if ' ' in at_time_str:
                    at_time_str = at_time_str.split(' ')[1]  # Get time part only
                # Handle times with seconds (HH:MM:SS) by extracting just HH:MM
                if ':' in at_time_str:
                    time_parts = at_time_str.split(':')
                    if len(time_parts) >= 2:
                        # Take just HH:MM part
                        at_time_str = f"{time_parts[0]}:{time_parts[1]}"
                        try:
                            schedule.every().day.at(at_time_str).do(job.job_func, *job.job_func.args)
                            # Only log re-added jobs at TRACE level or when troubleshooting
                        except Exception as e:
                            logger.warning(f"Could not re-add job with time {at_time_str}: {e}")
                    else:
                        logger.warning(f"Invalid time format for job: {at_time_str}")
                else:
                    logger.warning(f"Invalid time format for job: {at_time_str}")
            else:
                logger.debug(f"Skipping job without valid at_time: {getattr(job, 'at_time', 'None')}")
        
        logger.info(f"In-memory scheduler cleanup completed for user {user_id}, category {category}.")

        # Cleanup system tasks using schtasks command (Windows-specific)
        task_prefix = f"Wake_{user_id}_{category}_"
        try:
            result = subprocess.run(['schtasks', '/query', '/fo', 'LIST', '/v'], 
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if result.returncode != 0:
                logger.debug(f"Could not query system tasks: {result.stderr}")
                logger.info(f"System task cleanup completed for user {user_id}, category {category} (no tasks to clean).")
                return
            
            tasks = result.stdout.splitlines()
            tasks_deleted = 0

            for i, line in enumerate(tasks):
                if line.startswith("TaskName:") and task_prefix in line:
                    task_name = line.split(":")[1].strip()
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

            logger.info(f"System task cleanup completed for user {user_id}, category {category}.")
            if tasks_deleted > 0:
                logger.debug(f"Deleted {tasks_deleted} old system tasks")
                
        except Exception as query_error:
            logger.debug(f"Error querying system tasks for cleanup: {query_error}")
            logger.info(f"System task cleanup skipped for user {user_id}, category {category} (query failed).")

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
    def select_task_for_reminder(self, incomplete_tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Select a task for reminder using priority-based and due date proximity weighting.
        
        Args:
            incomplete_tasks: List of incomplete tasks to choose from
            
        Returns:
            Selected task dictionary
        """
        try:
            from datetime import datetime, timedelta
            import random
            
            if not incomplete_tasks:
                return None
            
            # If only one task, return it
            if len(incomplete_tasks) == 1:
                return incomplete_tasks[0]
            
            # Calculate weights for each task
            task_weights = []
            today = datetime.now().date()
            
            for task in incomplete_tasks:
                weight = 1.0  # Base weight
                
                # Priority weighting with new levels
                priority = task.get('priority', 'medium').lower()
                priority_multipliers = {
                    'critical': 3.0,  # Critical priority tasks 3x more likely
                    'high': 2.0,      # High priority tasks 2x more likely
                    'medium': 1.5,    # Medium priority tasks 1.5x more likely
                    'low': 1.0,       # Low priority tasks base weight
                    'none': 0.8       # No priority tasks slightly less likely
                }
                weight *= priority_multipliers.get(priority, 1.0)
                
                # Sliding scale due date proximity weighting
                due_date_str = task.get('due_date')
                if due_date_str:
                    try:
                        due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
                        days_until_due = (due_date - today).days
                        
                        # Sliding scale calculation
                        if days_until_due < 0:
                            # Overdue tasks: exponential increase based on how overdue
                            # Formula: 2.5 + (days_overdue * 0.1), max 4.0
                            days_overdue = abs(days_until_due)
                            overdue_multiplier = min(2.5 + (days_overdue * 0.1), 4.0)
                            weight *= overdue_multiplier
                        elif days_until_due == 0:
                            # Due today: maximum weight
                            weight *= 2.5
                        elif days_until_due <= 7:
                            # Due within a week: sliding scale from 2.5 to 1.0
                            # Formula: 2.5 - (days_until_due * 0.2)
                            proximity_multiplier = max(2.5 - (days_until_due * 0.2), 1.0)
                            weight *= proximity_multiplier
                        elif days_until_due <= 30:
                            # Due within a month: sliding scale from 1.0 to 0.8
                            # Formula: 1.0 - (days_until_due - 7) * 0.01
                            month_multiplier = max(1.0 - (days_until_due - 7) * 0.01, 0.8)
                            weight *= month_multiplier
                        else:
                            # Due later than a month: base weight
                            weight *= 0.8
                    except ValueError:
                        # Invalid date format, use base weight
                        pass
                else:
                    # No due date: slight reduction to encourage setting due dates
                    weight *= 0.9
                
                task_weights.append((task, weight))
            
            # Normalize weights to sum to 1.0
            total_weight = sum(weight for _, weight in task_weights)
            if total_weight == 0:
                # Fallback to random selection if all weights are 0
                return random.choice(incomplete_tasks)
            
            # Create probability distribution
            probabilities = [weight / total_weight for _, weight in task_weights]
            
            # Select task based on weighted probabilities
            selected_task = random.choices(
                [task for task, _ in task_weights],
                weights=probabilities,
                k=1
            )[0]
            
            logger.debug(f"Selected task '{selected_task.get('title', 'Unknown')}' with priority '{selected_task.get('priority', 'medium')}' and due date '{selected_task.get('due_date', 'None')}'")
            
            return selected_task
            
        except Exception as e:
            logger.error(f"Error selecting task for reminder: {e}")
            # Fallback to random selection
            return random.choice(incomplete_tasks) if incomplete_tasks else None

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
    def cleanup_task_reminders(self, user_id, task_id=None):
        """
        Clean up task reminders for a user or specific task.
        """
        try:
            jobs_to_keep = []
            for job in schedule.jobs:
                # Keep jobs that are not task reminders for this user/task
                if (job.job_func.__name__ != 'handle_task_reminder' or
                    job.job_func.args[0] != user_id or
                    (task_id and job.job_func.args[1] != task_id)):
                    jobs_to_keep.append(job)
            
            # Clear all jobs and reschedule only the ones we want to keep
            schedule.clear()
            for job in jobs_to_keep:
                # Re-add the job with its original schedule
                if hasattr(job, 'at_time') and job.at_time:
                    at_time_str = str(job.at_time)
                    if ' ' in at_time_str:
                        at_time_str = at_time_str.split(' ')[1]
                    if ':' in at_time_str:
                        time_parts = at_time_str.split(':')
                        if len(time_parts) >= 2:
                            at_time_str = f"{time_parts[0]}:{time_parts[1]}"
                            try:
                                schedule.every().day.at(at_time_str).do(job.job_func, *job.job_func.args)
                            except Exception as e:
                                logger.warning(f"Could not re-add job with time {at_time_str}: {e}")
            
            if task_id:
                logger.info(f"Cleaned up task reminders for user {user_id}, task {task_id}")
            else:
                logger.info(f"Cleaned up all task reminders for user {user_id}")
                
        except Exception as e:
            logger.error(f"Error cleaning up task reminders for user {user_id}: {e}")

# Standalone functions for admin UI access
@handle_errors("scheduling all task reminders for user")
def schedule_all_task_reminders(user_id):
    """
    Standalone function to schedule all task reminders for a user.
    This can be called from the admin UI without needing a scheduler instance.
    """
    try:
        from tasks.task_management import are_tasks_enabled
        
        # Check if tasks are enabled for this user
        if not are_tasks_enabled(user_id):
            logger.debug(f"Tasks not enabled for user {user_id}")
            return
        
        # For now, just log that scheduling was requested
        # The actual scheduling will happen when the main scheduler starts
        logger.info(f"Task reminder scheduling requested for user {user_id}")
        logger.info("Task reminders will be scheduled when the main scheduler starts")
        
    except Exception as e:
        logger.error(f"Error in task reminder scheduling request for user {user_id}: {e}")

@handle_errors("cleaning up task reminders for user")
def cleanup_task_reminders(user_id, task_id=None):
    """
    Standalone function to clean up task reminders for a user.
    This can be called from the admin UI without needing a scheduler instance.
    """
    try:
        # For now, just log that cleanup was requested
        # The actual cleanup will happen when the main scheduler restarts
        if task_id:
            logger.info(f"Task reminder cleanup requested for user {user_id}, task {task_id}")
        else:
            logger.info(f"Task reminder cleanup requested for user {user_id}")
        logger.info("Task reminders will be cleaned up when the main scheduler restarts")
        
    except Exception as e:
        logger.error(f"Error in task reminder cleanup request for user {user_id}: {e}")

def get_user_categories(user_id: str) -> List[str]:
    """Get user's message categories."""
    try:
        prefs_result = get_user_data(user_id, 'preferences')
        categories = prefs_result.get('preferences', {}).get('categories', [])
        if categories is None:
            return []
        elif isinstance(categories, list):
            return categories
        elif isinstance(categories, dict):
            return list(categories.keys())
        else:
            return []
    except Exception as e:
        logger.error(f"Error getting categories for user {user_id}: {e}")
        return []

def process_user_schedules(user_id: str):
    """Process schedules for a specific user."""
    try:
        # Get user's categories
        prefs_result = get_user_data(user_id, 'preferences')
        categories = prefs_result.get('preferences', {}).get('categories', [])
        if not categories:
            logger.debug(f"No categories found for user {user_id}")
            return
        
        # Process each category
        for category in categories:
            process_category_schedule(user_id, category)
            
    except Exception as e:
        logger.error(f"Error processing schedules for user {user_id}: {e}")

def process_category_schedule(user_id: str, category: str):
    """Process schedule for a specific user and category."""
    try:
        # Create a scheduler instance to process this category
        from bot.communication_manager import CommunicationManager
        
        communication_manager = CommunicationManager()
        scheduler_manager = SchedulerManager(communication_manager)
        
        # Schedule messages for this category
        scheduler_manager.schedule_daily_message_job(user_id, category)
        
        logger.info(f"Processed schedule for user {user_id}, category {category}")
        
    except Exception as e:
        logger.error(f"Error processing schedule for user {user_id}, category {category}: {e}")

def get_user_task_preferences(user_id: str) -> Dict[str, Any]:
    """Get user's task preferences."""
    try:
        prefs_result = get_user_data(user_id, 'preferences')
        task_prefs = prefs_result.get('preferences', {}).get('task_management', {})
        if task_prefs is None:
            return {}
        return task_prefs
    except Exception as e:
        logger.error(f"Error getting task preferences for user {user_id}: {e}")
        return {}

def get_user_checkin_preferences(user_id: str) -> Dict[str, Any]:
    """Get user's check-in preferences."""
    try:
        prefs_result = get_user_data(user_id, 'preferences')
        checkin_prefs = prefs_result.get('preferences', {}).get('checkin_settings', {})
        if checkin_prefs is None:
            return {}
        return checkin_prefs
    except Exception as e:
        logger.error(f"Error getting check-in preferences for user {user_id}: {e}")
        return {}
