# scheduler.py

import schedule
import time
import pytz
import threading
import random
import subprocess
import os
from datetime import datetime, timedelta
import logging

from core.user_management import get_all_user_ids, get_user_preferences
from core.schedule_management import get_schedule_time_periods, is_schedule_period_active, get_current_time_periods_with_validation
from core.service_utilities import load_and_localize_datetime
from core.logger import get_logger
from user.user_context import UserContext
from core.error_handling import (
    error_handler, SchedulerError, CommunicationError, handle_errors
)

# Suppress debug logging from the schedule library to reduce log spam
schedule_logger = logging.getLogger('schedule')
schedule_logger.setLevel(logging.WARNING)

logger = get_logger(__name__)

class SchedulerManager:
    @handle_errors("initializing scheduler manager")
    def __init__(self, communication_manager):
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
                    categories = get_user_preferences(user_id, ['categories'])
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
    
        # Immediately reschedule a message for the active user and category
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
                categories = get_user_preferences(user_id, ['categories'])
                if categories and isinstance(categories, list):
                    for category in categories:
                        try:
                            self.schedule_daily_message_job(user_id, category)
                            total_scheduled += 1
                            logger.debug(f"Scheduled messages for user {user_id}, category {category}")
                        except Exception as e:
                            logger.error(f"Failed to schedule for user {user_id}, category {category}: {e}")
                else:
                    logger.warning(f"No valid categories found for user {user_id}")
            except Exception as e:
                logger.error(f"Failed to get categories for user {user_id}: {e}")
        
        logger.info(f"Scheduling complete: {total_scheduled} user/category combinations scheduled")

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
        for period_name, period_data in time_periods.items():
            # Check if this period is active (default to active if not specified)
            if period_data.get('active', True):
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
            
        period_start_time = datetime.strptime(time_periods[period]['start'], "%H:%M").time()
        period_end_time = datetime.strptime(time_periods[period]['end'], "%H:%M").time()

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
    
    @handle_errors("setting wake timer")
    def set_wake_timer(self, schedule_time, user_id, category, period, wake_ahead_minutes=4):
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
                            logger.debug(f"Re-added job with time: {at_time_str}")
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
