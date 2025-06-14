# scheduler.py

import schedule
import time
import pytz
import threading
import random
import subprocess
import os
from datetime import datetime, timedelta

from core import utils
from core.logger import get_logger
from user.user_context import UserContext

logger = get_logger(__name__)

class SchedulerManager:
    def __init__(self, communication_manager):
        try:
            self.communication_manager = communication_manager
            self.scheduler_thread = None
            self._stop_event = threading.Event()  # Add stop event for proper thread management
            logger.info("SchedulerManager initialized successfully.")
        except Exception as e:
            logger.error(f"Error initializing SchedulerManager: {e}", exc_info=True)
            raise

    def run_daily_scheduler(self):
        """
        Starts the daily scheduler in a separate thread that handles all users.
        """
        def scheduler_loop():
            try:
                # Immediately schedule messages for all users when service starts
                self.schedule_all_users_immediately()
                
                # Then set up recurring daily scheduling at 01:00 for all users
                user_ids = utils.get_all_user_ids()
                for user_id in user_ids:
                    categories = utils.get_user_preferences(user_id, ['categories'])
                    for category in categories:
                        # Check if a job already exists for this user and category before scheduling
                        if not self.is_job_for_category(None, user_id, category):
                            schedule.every().day.at("01:00").do(self.schedule_daily_message_job, user_id=user_id, category=category)
                logger.info("Daily scheduler jobs have been scheduled for all users.")
            except Exception as e:
                logger.error(f"Error scheduling daily jobs: {e}", exc_info=True)
                raise
    
            try:
                loop_count = 0
                while not self._stop_event.is_set():  # Check for stop signal
                    schedule.run_pending()
                    loop_count += 1
                    
                    # Log every 15 iterations (15 minutes) for normal operation monitoring
                    if loop_count % 15 == 0:
                        active_jobs = len(schedule.jobs)
                        logger.info(f"Scheduler running: {active_jobs} active jobs scheduled")
                        
                    # Use wait instead of sleep to allow immediate shutdown
                    if self._stop_event.wait(timeout=60):  # Wait 60 seconds or until stop signal
                        break
                logger.info("Scheduler loop stopped gracefully.")
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}", exc_info=True)
                raise

        try:
            self._stop_event.clear()  # Ensure stop event is reset
            self.scheduler_thread = threading.Thread(target=scheduler_loop)
            self.scheduler_thread.daemon = True
            self.scheduler_thread.start()
            logger.info("Daily scheduler started for all users.")
        except Exception as e:
            logger.error(f"Failed to start scheduler thread: {e}", exc_info=True)
            raise

    def stop_scheduler(self):
        """Stops the scheduler thread."""
        try:
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
        except Exception as e:
            logger.error(f"Error stopping scheduler: {e}", exc_info=True)
            raise

    def reset_and_reschedule_daily_messages(self, category):
        """
        Resets scheduled tasks for a specific category and reschedules daily messages for that category.
        """
        try:
            # Get the active user ID
            active_user_id = UserContext().get_user_id()
            if not active_user_id:
                logger.error("No active user found during reset and reschedule.")
                return

            # Remove only the scheduled jobs for the active user and the specific category
            schedule.jobs = [job for job in schedule.jobs if not self.is_job_for_category(job, active_user_id, category)]
        
            # Immediately reschedule a message for the active user and category
            self.schedule_daily_message_job(user_id=active_user_id, category=category)
        
            logger.info(f"Scheduler reset and rescheduled daily messages for active user: {active_user_id}, category: {category}.")
        except Exception as e:
            logger.error(f"Error resetting and rescheduling messages for category {category}: {e}", exc_info=True)
            raise

    def is_job_for_category(self, job, user_id, category):
        """Determines if a job is scheduled for a specific user and category."""
        try:
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
        except Exception as e:
            logger.error(f"Error checking if job exists for category {category}: {e}", exc_info=True)
            raise
    
    def schedule_all_users_immediately(self):
        """
        Schedule messages for all users immediately when the service starts.
        """
        try:
            user_ids = utils.get_all_user_ids()
            total_scheduled = 0
            
            logger.info(f"Starting immediate scheduling for {len(user_ids)} users")
            
            for user_id in user_ids:
                try:
                    categories = utils.get_user_preferences(user_id, ['categories'])
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
                    logger.error(f"Failed to get preferences for user {user_id}: {e}")
            
            logger.info(f"Immediate scheduling completed: {total_scheduled} user/category combinations scheduled")
            
        except Exception as e:
            logger.error(f"Error in schedule_all_users_immediately: {e}", exc_info=True)
            raise

    def schedule_daily_message_job(self, user_id, category):
        """
        Schedules daily messages immediately for the specified user and category.
        """
        try:
            logger.info(f"Scheduling daily messages immediately for user {user_id}, category {category}.")

            # Clean up old jobs for this user and category
            self.cleanup_old_tasks(user_id, category)

            # Schedule a message at a random time for the user and category
            self.schedule_message_at_random_time(user_id=user_id, category=category)
        except Exception as e:
            logger.error(f"Error scheduling daily message for user {user_id}, category {category}: {e}", exc_info=True)
            raise
    
    def schedule_message_at_random_time(self, user_id, category):
        """
        Schedule a message at a random time within each active period for a specific category and user.
        """
        try:
            time_periods = utils.get_schedule_time_periods(user_id, category)
            for period in time_periods:
                if utils.is_schedule_period_active(user_id, category, period):
                    retry_count = 0
                    max_retries = 10  # Set a limit on retries to avoid infinite loops

                    while retry_count < max_retries:
                        datetime_str = self.get_random_time_within_period(user_id, category, period)
                        if datetime_str is None:
                            logger.error(f"Failed to get a valid time for {category} messages during {period}. Check configuration for user {user_id}.")
                            continue

                        schedule_datetime = utils.load_and_localize_datetime(datetime_str, 'America/Regina')
                        now = datetime.now(pytz.timezone('America/Regina'))

                        logger.info(f"Attempting to schedule message for user {user_id}, category {category} at {schedule_datetime} (now is {now})")

                        if not self.is_time_conflict(user_id, schedule_datetime):
                            if schedule_datetime <= now:
                                schedule_datetime += timedelta(days=1)
                                logger.info(f"Adjusted scheduling time to future for user {user_id}: {schedule_datetime}")

                            try:
                                time_part = schedule_datetime.strftime('%H:%M')
                                schedule.every().day.at(time_part).do(self.handle_sending_scheduled_message, user_id=user_id, category=category)
                                logger.info(f"Successfully scheduled {period} {category} message for user {user_id} at {time_part} on {schedule_datetime.strftime('%Y-%m-%d')}.")

                                # Set the wake timer for the scheduled time
                                self.set_wake_timer(schedule_datetime, user_id, category, period)
                                break  # Exit the loop after successfully scheduling the message
                            except Exception as e:
                                logger.error(f"Error while scheduling {category} message at {time_part} for user {user_id}: {str(e)}")
                                raise  # Re-raise to allow higher-level handling
                        else:
                            logger.info(f"Conflict detected for user {user_id}, category {category} at {schedule_datetime}. Retrying...")
                            retry_count += 1

                    if retry_count == max_retries:
                        logger.warning(f"Max retries reached. Could not find a suitable time for user {user_id}, category {category} within {period}.")
        except Exception as e:
            logger.error(f"Error in scheduling message at random time for user {user_id}, category {category}: {e}", exc_info=True)
            raise

    def is_time_conflict(self, user_id, schedule_datetime):
        """Checks if there is a time conflict with any existing scheduled jobs for the user."""
        for job in schedule.jobs:
            if job.job_func.args and job.job_func.args[0] == user_id:
                job_time = job.next_run
                if abs((job_time - schedule_datetime).total_seconds()) < 1800:  # 30 minutes = 1800 seconds
                    return True
        return False

    def get_random_time_within_period(self, user_id, category, period, timezone_str='America/Regina'):
        """Get a random time within a specified period for a given category."""
        try:
            tz = pytz.timezone(timezone_str)
            now_datetime = datetime.now(tz)
            logger.info(f"Current time for scheduling: {now_datetime.strftime('%Y-%m-%d %H:%M')}")    
            
            time_periods = utils.get_schedule_time_periods(user_id, category)
            period_start_time = datetime.strptime(time_periods[period]['start'], "%H:%M").time()
            period_end_time = datetime.strptime(time_periods[period]['end'], "%H:%M").time()

            start_datetime = datetime.combine(now_datetime.date(), period_start_time, tzinfo=tz)
            end_datetime = datetime.combine(now_datetime.date(), period_end_time, tzinfo=tz)

            # Adjust the next day logic for periods that start after the current time
            if start_datetime < now_datetime:
                start_datetime += timedelta(days=1)
                end_datetime += timedelta(days=1)

            total_seconds = (end_datetime - start_datetime).total_seconds()
            if total_seconds <= 0:
                logger.error("Invalid time range calculated.")
                return None

            random_seconds = random.randint(0, int(total_seconds))
            random_datetime = start_datetime + timedelta(seconds=random_seconds)

            # Check if the randomly determined time has already passed and adjust if necessary
            if random_datetime <= now_datetime:
                random_datetime += timedelta(days=1)

            random_time_str = random_datetime.strftime("%Y-%m-%d %H:%M")
            logger.info(f"Scheduled random time: {random_time_str}")
            return random_time_str
        except Exception as e:
            logger.error(f"Error generating random time within period for user {user_id}, category {category}: {e}", exc_info=True)
            raise

    def log_scheduled_tasks(self):
        """Logs all current and upcoming scheduled tasks in a user-friendly manner."""
        try:
            for job in schedule.jobs:
                next_run = job.next_run.strftime('%Y-%m-%d %H:%M:%S') if job.next_run else 'None'
                task_name = job.job_func.__name__ if hasattr(job.job_func, '__name__') else 'Scheduled Task'
                task_description = str(job.job_func).split('function ')[-1].split(' at ')[0] if 'function' in str(job.job_func) else task_name

                category = 'Generic Task'
                if hasattr(job.job_func, 'func') and hasattr(job.job_func, 'args') and job.job_func.args:
                    category = job.job_func.args[0]

                logger.info(f"Task: {task_description}, Category: {category}, Scheduled at: {job.at_time}, Next run: {next_run}")
        except Exception as e:
            logger.error(f"Error logging scheduled tasks: {e}", exc_info=True)

    def handle_sending_scheduled_message(self, user_id, category, retry_attempts=3, retry_delay=30):
        """
        Handles the sending of scheduled messages with retries.
        """
        try:
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
        except Exception as e:
            logger.error(f"Error in scheduled message handler for user {user_id}, category {category}: {e}")
            raise
    
    def set_wake_timer(self, schedule_time, user_id, category, period, wake_ahead_minutes=4):
        try:
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

        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to set wake timer: {e}", exc_info=True)
            raise

    def cleanup_old_tasks(self, user_id, category):
        """Cleans up all tasks (scheduled jobs and system tasks) associated with a given user and category."""
        try:
            # Cleanup in-memory scheduled jobs for the given user and category
            schedule.jobs = [job for job in schedule.jobs if not self.is_job_for_category(job, user_id, category)]
            logger.info(f"In-memory scheduler cleanup completed for user {user_id}, category {category}.")

            # Cleanup system tasks using schtasks command (Windows-specific)
            task_prefix = f"Wake_{user_id}_{category}_"
            result = subprocess.run(['schtasks', '/query', '/fo', 'LIST', '/v'], stdout=subprocess.PIPE, text=True)
            tasks = result.stdout.splitlines()

            for i, line in enumerate(tasks):
                if line.startswith("TaskName:") and task_prefix in line:
                    task_name = line.split(":")[1].strip()
                    logger.info(f"Deleting old system task: {task_name}")
                    subprocess.run(['schtasks', '/delete', '/tn', task_name, '/f'], check=True)

            logger.info(f"System task cleanup completed for user {user_id}, category {category}.")
        except Exception as e:
            logger.error(f"Failed to clean up old tasks for user {user_id}, category {category}: {e}", exc_info=True)
            raise
