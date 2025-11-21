# service.py - MHM Backend Service (No UI)

import signal
import time
import os
import atexit
from datetime import datetime
from pathlib import Path

# Set up logging FIRST before any other imports
from core.logger import setup_logging, get_component_logger
import logging  # kept for tests that patch core.service.logging.getLogger
setup_logging()
logger = get_component_logger('main')
main_logger = logger  # Alias for backward compatibility
discord_logger = get_component_logger('discord')
logger.debug("Logging setup successfully.")

# Start file creation auditor early (developer tool)
try:
        from core.file_auditor import start_auditor
        start_auditor()
except Exception as _fa_err:
    logger.debug(f"File auditor not started: {_fa_err}")

# Import configuration validation
from core.config import validate_and_raise_if_invalid, print_configuration_report

# Import the communication manager (channels auto-register from config)
from communication.core.channel_orchestrator import CommunicationManager
from core.config import LOG_MAIN_FILE, USER_INFO_DIR_PATH, get_user_data_dir
from core.scheduler import SchedulerManager
from core.file_operations import verify_file_access
from core.user_data_handlers import get_all_user_ids
from core.user_data_handlers import get_user_data

# Expose get_user_data at module level so tests
# that patch core.service.get_user_data continue to work.

from core.error_handling import handle_errors, FileOperationError

class InitializationError(Exception):
    """Custom exception for initialization errors."""
    pass

class MHMService:
    # ERROR_HANDLING_EXCLUDE: Service constructor - initialization errors are handled by called methods
    def __init__(self):
        """
        Initialize the MHM backend service.
        
        Sets up communication manager, scheduler manager, and registers emergency shutdown handler.
        """
        self.communication_manager = None
        self.scheduler_manager = None
        self.running = False
        self.startup_time = None  # Track when service started
        # Register atexit handler as backup shutdown method
        atexit.register(self.emergency_shutdown)
        
    @handle_errors("validating configuration")
    def validate_configuration(self):
        """Validate all configuration settings before starting the service."""
        logger.info("Validating configuration...")
        
        # Print configuration report for debugging
        print_configuration_report()
        
        # Validate configuration and get available channels
        available_channels = validate_and_raise_if_invalid()
        
        return available_channels
        
    @handle_errors("initializing paths")
    def initialize_paths(self):
        """
        Initialize and verify all required file paths for the service.
        
        Creates paths for log files, user data directories, and message files for all users.
        
        Returns:
            List[str]: List of all initialized file paths
        """
        paths = [
            LOG_MAIN_FILE,
            USER_INFO_DIR_PATH
        ]
        
        user_ids = get_all_user_ids()
        logger.debug(f"User IDs retrieved: {user_ids}")
        for user_id in user_ids:
            if user_id is None:
                logger.warning("Encountered None user_id in get_all_user_ids()")
                continue
            # Get user categories
            user_data = get_user_data(user_id, 'preferences')
            categories = user_data.get('preferences', {}).get('categories', [])
            if isinstance(categories, list):
                if categories:  # Only process if list is not empty
                    for category in categories:
                        try:
                            # Use new user-specific message file structure
                            from pathlib import Path
                            user_messages_dir = Path(get_user_data_dir(user_id)) / 'messages'
                            path = str(user_messages_dir / f"{category}.json")
                            paths.append(path)
                        except Exception as e:
                            logger.error(f"Error determining file path for category '{category}' and user '{user_id}': {e}")
                # Empty list is fine - no warning needed
            else:
                logger.warning(
                    f"Expected list for categories, got {type(categories)} for user '{user_id}'"
                )

        logger.debug(f"Paths initialized: {paths}")
        return paths

    @handle_errors("checking and fixing logging")
    @handle_errors("testing logging functionality", default_return=False)
    def _check_and_fix_logging__test_logging_functionality(self, test_message):
        """Test if logging functionality works by writing a test message and flushing handlers."""
        logger.debug(test_message)
        
        # Force flush all handlers to ensure messages are written
        root_logger = logging.getLogger()
        for handler in root_logger.handlers:
            if hasattr(handler, 'flush'):
                handler.flush()
        
        # Give more time for file operations and buffering
        time.sleep(0.5)

    @handle_errors("ensuring log file exists", default_return=False)
    def _check_and_fix_logging__ensure_log_file_exists(self):
        """Ensure the log file exists, creating it if necessary."""
        from core.config import LOG_MAIN_FILE
        
        if not os.path.exists(LOG_MAIN_FILE):
            logger.warning("Log file does not exist - logging may have issues")
            # Do not delete or alter the provided path; create the file to satisfy health check
            try:
                with open(LOG_MAIN_FILE, 'a', encoding='utf-8') as _f:
                    _f.write('')
            except Exception:
                raise FileOperationError("Log file missing", details={'log_file': LOG_MAIN_FILE})

    @handle_errors("reading recent log content", default_return="")
    def _check_and_fix_logging__read_recent_log_content(self):
        """Read the last 1000 characters from the log file to check for recent activity."""
        from core.config import LOG_MAIN_FILE
        
        with open(LOG_MAIN_FILE, 'r', encoding='utf-8') as f:
            # Read last 1000 characters to check for recent activity
            f.seek(0, 2)  # Go to end
            file_size = f.tell()
            if file_size > 1000:
                f.seek(file_size - 1000)
            else:
                f.seek(0)
            return f.read()

    @handle_errors("verifying test message present", default_return=False)
    def _check_and_fix_logging__verify_test_message_present(self, recent_content, test_message, test_timestamp):
        """Check if our test message or recent timestamp patterns are present in log content."""
        if (test_message in recent_content or 
            any(str(test_timestamp - i) in recent_content for i in range(60))):
            logger.debug("Logging system verified")
            return True
        return False

    @handle_errors("checking recent activity timestamps", default_return=False)
    def _check_and_fix_logging__check_recent_activity_timestamps(self, recent_content):
        """Check if there's any recent activity within the last 5 minutes using timestamp patterns."""
        import re
        
        current_time = datetime.now()
        recent_pattern = r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})'
        matches = re.findall(recent_pattern, recent_content)
        
        if matches:
            try:
                latest_log_time = datetime.strptime(matches[-1], '%Y-%m-%d %H:%M:%S')
                time_diff = (current_time - latest_log_time).total_seconds()
                
                if time_diff < 300:  # Less than 5 minutes
                    logger.debug("Logging system healthy")
                    return True
            except ValueError:
                pass  # Failed to parse timestamp, continue to restart check
        
        logger.warning("No recent logging activity detected, may need restart")
        return False

    @handle_errors("forcing restart of logging system", default_return=False)
    def _check_and_fix_logging__force_restart_logging_system(self):
        """Force restart the logging system and update the global logger."""
        logger.warning("Logging system verification failed - attempting force restart...")
        
        from core.logger import force_restart_logging
        if force_restart_logging():
            logger.info("Logging system force restarted successfully")
            return True
        else:
            logger.error("Failed to restart logging system")
            return False

    @handle_errors("checking and fixing logging", default_return=None)
    def check_and_fix_logging(self):
        """Check if logging is working and restart if needed"""
        global logger
        
        # Simple test: try to log a message and see if it works
        test_timestamp = int(time.time())
        test_message = f"Logging verification - {test_timestamp}"
        
        # Try logging at different levels to test all handlers
        try:
            self._check_and_fix_logging__test_logging_functionality(test_message)
            self._check_and_fix_logging__ensure_log_file_exists()
            
            # Try to read the last few lines to verify logging is working
            try:
                recent_content = self._check_and_fix_logging__read_recent_log_content()
                
                # Look for our test message or recent timestamp patterns
                if self._check_and_fix_logging__verify_test_message_present(recent_content, test_message, test_timestamp):
                    return
                
                # Check if there's any recent activity (within last 5 minutes)
                if self._check_and_fix_logging__check_recent_activity_timestamps(recent_content):
                    return
            
            except Exception as file_error:
                logger.warning(f"Could not verify log file contents: {file_error}")
                # Don't force restart just because we can't read the file
                # The fact that logger.debug() and logger.warning() worked above is sufficient
                logger.debug("Logging system working despite file read issues")
                return
            
        except Exception as log_error:
            # If we can't even log, then we definitely have a problem
            logger.error(f"Logging system is not working - cannot write log messages: {log_error}")
            # Fall through to restart logic
        
        # Only restart if we have clear evidence of logging failure
        if self._check_and_fix_logging__force_restart_logging_system():
            # Update global logger after successful restart
            logger = get_component_logger('main')

    @handle_errors("starting service")
    def start(self):
        """
        Start the MHM backend service.
        
        Initializes communication channels, scheduler, and begins the main service loop.
        Sets up signal handlers for graceful shutdown.
        """
        logger.info("Starting MHM Backend Service...")
        self.running = True
        
        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        max_retries = 3
        
        try:
            # Step 0: Validate configuration
            logger.info("Step 0: Validating configuration...")
            self.validate_configuration()
            
            # Step 0.5: Check and fix logging if needed
            logger.info("Step 0.5: Checking logging system...")
            self.check_and_fix_logging()
            
            # Automatic cache cleanup (only if needed)
            try:
                from core.auto_cleanup import auto_cleanup_if_needed
                cleanup_performed = auto_cleanup_if_needed()
                if cleanup_performed:
                    logger.info("Automatic cache cleanup completed successfully")
            except Exception as e:
                logger.warning(f"Automatic cache cleanup failed (non-critical): {e}")

            # Step 1: Initialize paths and check file access
            logger.info("Step 1: Initializing paths and checking file access...")
            paths = self.initialize_paths()
            verify_file_access(paths)

            # Step 2: Start CommunicationManager (Email, Discord)
            for attempt in range(max_retries):
                try:
                    self.communication_manager = CommunicationManager()
                    break
                except Exception as e:
                    logger.error(f"Failed to initialize CommunicationManager on attempt {attempt + 1}/{max_retries}: {e}")
                    time.sleep(1)

            if self.communication_manager is None:
                raise InitializationError("Failed to initialize CommunicationManager after retries.")

            # Step 2.5: Initialize communication channels (Discord, Email, etc.)
            logger.info("Step 2.5: Initializing communication channels...")
            try:
                self.communication_manager.initialize_channels_from_config()
                logger.info("Communication channels initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize communication channels: {e}")
                raise InitializationError(f"Failed to initialize communication channels: {e}")

            # Step 3: Start the SchedulerManager
            for attempt in range(max_retries):
                try:
                    self.scheduler_manager = SchedulerManager(self.communication_manager)
                    break
                except Exception as e:
                    logger.error(f"Failed to initialize SchedulerManager on attempt {attempt + 1}/{max_retries}: {e}")
                    time.sleep(1)

            if self.scheduler_manager is None:
                raise InitializationError("Failed to initialize SchedulerManager after retries.")

            # Step 4: Start bots and scheduler
            self.communication_manager.set_scheduler_manager(self.scheduler_manager)
            self.communication_manager.start_all()
            
            # Start scheduler for all users
            logger.info("Starting scheduler...")
            self.scheduler_manager.run_daily_scheduler()

            # Set startup time to prevent processing reschedule requests during startup
            self.startup_time = time.time()

            logger.info("MHM Backend Service initialized successfully and running.")
            
            # Keep the service running
            self.run_service_loop()

        except InitializationError as init_err:
            logger.critical(f"Critical initialization error: {init_err}", exc_info=True)
            self.running = False
        except KeyboardInterrupt:
            logger.info("Service interrupted by user. Shutting down...")
            self.running = False
        except Exception as e:
            logger.error(f"An error occurred in the service: {e}", exc_info=True)
            self.running = False
        finally:
            self.shutdown()

    @handle_errors("running service loop")
    def run_service_loop(self):
        """Keep the service running until shutdown is requested"""
        logger.info("Service is now running. Press Ctrl+C to stop.")
        shutdown_file = Path(__file__).parent.parent / 'shutdown_request.flag'
        
        # Initialize loop counter outside the main loop
        loop_minutes = 0
        
        while self.running:
            # Check for shutdown file every 2 seconds for faster response
            for i in range(30):  # 30 * 2 = 60 seconds total
                if not self.running:
                    break
                
                # Check for shutdown request file every iteration
                if os.path.exists(shutdown_file):
                    # Check if this is a new shutdown request (created after service started)
                    try:
                        file_mtime = os.path.getmtime(shutdown_file)
                        if self.startup_time and file_mtime < self.startup_time:
                            # This is an old shutdown request from before service started
                            logger.debug(f"Ignoring old shutdown request file (created before service startup)")
                            try:
                                os.remove(shutdown_file)
                                logger.debug("Removed old shutdown request file")
                            except Exception as e:
                                logger.warning(f"Could not remove old shutdown file: {e}")
                        else:
                            # This is a new shutdown request
                            logger.info("Shutdown request file detected - initiating graceful shutdown")
                            try:
                                with open(shutdown_file, 'r') as f:
                                    content = f.read().strip()
                                
                                # Parse shutdown request type for better logging
                                if content.startswith("SHUTDOWN_REQUESTED_BY_UI_"):
                                    logger.info("Shutdown requested by UI")
                                elif content.startswith("HEADLESS_SHUTDOWN_REQUESTED_"):
                                    logger.info("Shutdown requested by headless service manager")
                                else:
                                    logger.info(f"Shutdown request details: {content}")
                            except Exception as e:
                                logger.warning(f"Could not read shutdown file: {e}")
                            self.running = False
                            break
                    except Exception as e:
                        logger.warning(f"Error checking shutdown file timestamp: {e}")
                        # If we can't check the timestamp, assume it's new and shut down
                        logger.info("Shutdown request file detected - initiating graceful shutdown")
                        self.running = False
                        break
                
                # Check for request files (optimized: only scan if .flag files exist)
                base_dir = self._check_test_message_requests__get_base_directory()
                if self._has_any_request_files(base_dir):
                    # Only do full scan if request files might exist
                    self.check_test_message_requests()
                    self.check_checkin_prompt_requests()
                    self.check_task_reminder_requests()
                    self.check_reschedule_requests()
                
                time.sleep(2)  # Sleep for 2 seconds
            
            # Enhanced service status logging with useful metrics
            loop_minutes += 1
            if loop_minutes % 60 == 0:  # Changed from 10 to 60 minutes
                # Collect system metrics for enhanced status reporting
                status_metrics = []
                
                # Basic uptime
                status_metrics.append(f"{loop_minutes}m uptime")
                
                # Active scheduler jobs (scheduled tasks, not schedule.jobs)
                if hasattr(self, 'scheduler_manager') and self.scheduler_manager:
                    try:
                        # Get actual scheduler jobs from the scheduler manager
                        active_jobs = len(self.scheduler_manager.get_active_jobs()) if hasattr(self.scheduler_manager, 'get_active_jobs') else 0
                        status_metrics.append(f"{active_jobs} active jobs")
                    except:
                        status_metrics.append("jobs: unknown")
                
                # User count (total registered users in the system)
                try:
                    user_count = len(self.user_manager.get_all_user_ids()) if hasattr(self, 'user_manager') else 0
                    status_metrics.append(f"{user_count} users")
                except:
                    status_metrics.append("users: unknown")
                
                # Memory usage (current process memory consumption in MB)
                try:
                    import psutil
                    process = psutil.Process()
                    memory_mb = process.memory_info().rss / 1024 / 1024
                    status_metrics.append(f"{memory_mb:.1f}MB memory")
                except:
                    pass  # psutil not available, skip memory metric
                
                # Communication channel status
                if self.communication_manager:
                    try:
                        channels = self.communication_manager.get_available_channels()
                        status_metrics.append(f"{len(channels)} channels")
                    except:
                        pass
                
                # Log enhanced status
                metrics_str = ", ".join(status_metrics)
                logger.info(f"Service status: {metrics_str}")
                
                # Enhanced health monitoring - check Discord connectivity status
                if self.communication_manager:
                    try:
                        discord_status = self.communication_manager.get_discord_connectivity_status()
                        if discord_status:
                            connection_status = discord_status.get('connection_status', 'unknown')
                            if connection_status != 'connected':
                                discord_logger.warning(f"Discord connectivity issue detected: {connection_status}")
                                # Log detailed error information if available
                                detailed_errors = discord_status.get('detailed_errors', {})
                                if detailed_errors:
                                    for error_type, error_info in detailed_errors.items():
                                        discord_logger.warning(f"Discord {error_type}: {error_info.get('error_message', 'Unknown error')}")
                            else:
                                # Log successful connection with metrics
                                latency = discord_status.get('latency', 'unknown')
                                guild_count = discord_status.get('guild_count', 'unknown')
                                # Format latency to 4 significant figures
                                if isinstance(latency, (int, float)) and latency != 'unknown':
                                    latency_formatted = f"{latency:.4f}"
                                else:
                                    latency_formatted = str(latency)
                                discord_logger.debug(f"Discord healthy - Latency: {latency_formatted}s, Guilds: {guild_count}")
                    except Exception as e:
                        discord_logger.warning(f"Could not check Discord connectivity status: {e}")
                
        logger.info("Service loop ended.")
        # Clean up shutdown file if it exists
        try:
            if os.path.exists(shutdown_file):
                os.remove(shutdown_file)
                logger.info("Cleanup: Removed shutdown request file")
        except Exception as e:
            logger.warning(f"Could not remove shutdown file: {e}")
        
        # Clean up any remaining test message request files
        self.cleanup_test_message_requests()
        
        # Clean up any remaining reschedule request files  
        self.cleanup_reschedule_requests()
    
    @handle_errors("checking test message requests")
    @handle_errors("getting base directory for test message requests", default_return="")
    def _check_test_message_requests__get_base_directory(self):
        """Get the base directory for test message request files."""
        return os.path.dirname(os.path.dirname(__file__))
    
    @handle_errors("checking if request files exist", default_return=False)
    def _has_any_request_files(self, base_dir):
        """Quick check if any request files exist (optimization to avoid full scan when not needed)."""
        try:
            base_path = Path(base_dir)
            # Quick check: just see if directory has any .flag files
            # This is much faster than iterating all files
            for file_path in base_path.iterdir():
                if file_path.is_file() and file_path.name.endswith('.flag'):
                    return True
            return False
        except Exception:
            return True  # If we can't check, assume files might exist and do full scan

    @handle_errors("discovering test message request files", default_return=[])
    def _check_test_message_requests__discover_request_files(self, base_dir):
        """Discover all test message request files in the base directory."""
        base_path = Path(base_dir)
        request_files = []
        for file_path in base_path.iterdir():
            if file_path.is_file() and file_path.name.startswith('test_message_request_') and file_path.name.endswith('.flag'):
                request_files.append(str(file_path))
        return request_files

    @handle_errors("parsing test message request file", default_return={'user_id': None, 'category': None, 'source': 'unknown'})
    def _check_test_message_requests__parse_request_file(self, request_file):
        """Parse and validate a test message request file."""
        import json
        
        with open(request_file, 'r') as f:
            request_data = json.load(f)
        
        user_id = request_data.get('user_id')
        category = request_data.get('category')
        source = request_data.get('source', 'unknown')
        
        return {
            'user_id': user_id,
            'category': category,
            'source': source
        }

    @handle_errors("validating test message request data", default_return=False)
    def _check_test_message_requests__validate_request_data(self, request_data, filename):
        """Validate request data and check if it should be processed."""
        user_id = request_data['user_id']
        category = request_data['category']
        
        if not user_id or not category:
            logger.warning(f"Invalid test message request in {filename}: missing user_id or category")
            return False
        
        return True

    @handle_errors("processing test message request", default_return=None)
    def _check_test_message_requests__process_valid_request(self, request_data):
        """Process a valid test message request."""
        user_id = request_data['user_id']
        category = request_data['category']
        source = request_data['source']
        
        logger.info(f"Processing test message request from {source}: user={user_id}, category={category}")
        
        # Use the communication manager to send the message
        if self.communication_manager:
            self.communication_manager.handle_message_sending(user_id, category)
            logger.info(f"Test message sent successfully for {user_id}, category={category}")
            
            # Get the actual message that was sent from the communication manager
            actual_message = getattr(self.communication_manager, '_last_sent_message', {}).get('message')
            if actual_message and self.communication_manager._last_sent_message.get('user_id') == user_id and self.communication_manager._last_sent_message.get('category') == category:
                # Write response file with actual message content for UI to read
                self._check_test_message_requests__write_response(user_id, category, actual_message)
        else:
            logger.error("Communication manager not available for test message")
    
    @handle_errors("getting message content for test message", default_return=None)
    def _check_test_message_requests__get_message_content(self, user_id: str, category: str) -> str:
        """Get the actual message content that will be sent."""
        try:
            # Use the same logic as _send_predefined_message to get the message
            from core.schedule_utilities import get_current_time_periods_with_validation, get_current_day_names
            from core.message_management import get_recent_messages
            from pathlib import Path
            from core.config import get_user_data_dir
            from core.file_operations import load_json_data
            
            matching_periods, valid_periods = get_current_time_periods_with_validation(user_id, category)
            
            # Remove 'ALL' from matching_periods if there are other periods
            if 'ALL' in matching_periods and len(matching_periods) > 1:
                matching_periods = [p for p in matching_periods if p != 'ALL']
            if not matching_periods and 'ALL' in valid_periods:
                matching_periods = ['ALL']
            
            # Load messages
            user_messages_dir = Path(get_user_data_dir(user_id)) / 'messages'
            file_path = user_messages_dir / f"{category}.json"
            data = load_json_data(str(file_path))
            
            if data and 'messages' in data:
                current_days = get_current_day_names()
                
                all_messages = [
                    msg for msg in data['messages']
                    if any(day in msg.get('days', []) for day in current_days)
                    and any(period in msg.get('time_periods', []) for period in matching_periods)
                ]
                
                if all_messages:
                    # Apply deduplication
                    recent_messages = get_recent_messages(user_id, category=category, limit=50, days_back=60)
                    recent_content = {msg.get('message', '').strip().lower() for msg in recent_messages if msg.get('message')}
                    
                    available_messages = []
                    for msg in all_messages:
                        message_content = msg.get('message', '').strip()
                        if message_content and message_content.lower() not in recent_content:
                            available_messages.append(msg)
                    
                    if not available_messages:
                        available_messages = all_messages
                    
                    # Use weighted selection (same as CommunicationManager._select_weighted_message)
                    if available_messages:
                        import random
                        specific_period_messages = []
                        all_period_messages = []
                        
                        for msg in available_messages:
                            time_periods = msg.get('time_periods', [])
                            has_specific_periods = any(period != 'ALL' for period in time_periods)
                            if has_specific_periods:
                                specific_period_messages.append(msg)
                            else:
                                all_period_messages.append(msg)
                        
                        # Weighted selection: 70% chance for specific periods, 30% chance for 'ALL' periods
                        if specific_period_messages and random.random() < 0.7:
                            selected_msg = random.choice(specific_period_messages)
                        elif all_period_messages:
                            selected_msg = random.choice(all_period_messages)
                        else:
                            selected_msg = random.choice(available_messages)
                        
                        return selected_msg.get('message', '')
        except Exception as e:
            logger.debug(f"Could not get message content: {e}")
        return None
    
    @handle_errors("writing test message response", default_return=None)
    def _check_test_message_requests__write_response(self, user_id: str, category: str, message: str):
        """Write the actual message content to a response file for the UI to read."""
        try:
            import json
            from datetime import datetime
            base_dir = self._check_test_message_requests__get_base_directory()
            response_file = Path(base_dir) / f'test_message_response_{user_id}_{category}.flag'
            
            response_data = {
                "user_id": user_id,
                "category": category,
                "message": message,
                "timestamp": datetime.now().isoformat()
            }
            
            with open(response_file, 'w') as f:
                json.dump(response_data, f, indent=2)
            
            logger.debug(f"Wrote test message response file: {response_file}")
        except Exception as e:
            logger.debug(f"Could not write response file: {e}")

    def _check_test_message_requests__cleanup_request_file(self, request_file, filename):
        """Clean up a processed request file."""
        try:
            os.remove(request_file)
            logger.info(f"Processed test message request: {filename}")
        except Exception as cleanup_error:
            logger.warning(f"Could not remove request file {filename}: {cleanup_error}")

    @handle_errors("cleaning up problematic test message request file", user_friendly=False, default_return=None)
    def _check_test_message_requests__handle_processing_error(self, request_file, filename, error):
        """Handle errors during request processing."""
        logger.error(f"Error processing test message request {filename}: {error}")
        # Try to remove the problematic file
        os.remove(request_file)
        logger.debug(f"Removed problematic request file: {filename}")

    def check_test_message_requests(self):
        """Check for and process test message request files from admin panel"""
        base_dir = self._check_test_message_requests__get_base_directory()
        request_files = self._check_test_message_requests__discover_request_files(base_dir)
        
        for request_file in request_files:
            filename = os.path.basename(request_file)
            
            try:
                # Parse and validate the request
                request_data = self._check_test_message_requests__parse_request_file(request_file)
                
                if self._check_test_message_requests__validate_request_data(request_data, filename):
                    self._check_test_message_requests__process_valid_request(request_data)
                
                # Clean up the request file
                self._check_test_message_requests__cleanup_request_file(request_file, filename)
                
            except Exception as e:
                self._check_test_message_requests__handle_processing_error(request_file, filename, e)
    
    @handle_errors("checking check-in prompt requests")
    def check_checkin_prompt_requests(self):
        """Check for and process check-in prompt request files from admin panel"""
        base_dir = self._check_test_message_requests__get_base_directory()
        base_path = Path(base_dir)
        
        for file_path in base_path.iterdir():
            if file_path.is_file() and file_path.name.startswith('checkin_prompt_request_') and file_path.name.endswith('.flag'):
                filename = os.path.basename(file_path)
                try:
                    import json
                    with open(file_path, 'r') as f:
                        request_data = json.load(f)
                    
                    user_id = request_data.get('user_id')
                    if user_id and self.communication_manager:
                        # Get user preferences to determine messaging service and recipient
                        from core.user_data_handlers import get_user_data
                        prefs_result = get_user_data(user_id, 'preferences', normalize_on_read=True)
                        preferences = prefs_result.get('preferences')
                        
                        if preferences:
                            messaging_service = preferences.get('channel', {}).get('type')
                            if messaging_service:
                                recipient = self.communication_manager._get_recipient_for_service(user_id, messaging_service, preferences)
                                if recipient:
                                    # Get first question before sending (for response file)
                                    first_question = self._get_checkin_first_question(user_id)
                                    
                                    self.communication_manager._send_checkin_prompt(user_id, messaging_service, recipient)
                                    logger.info(f"Check-in prompt sent successfully for {user_id}")
                                    
                                    # Write response file with first question for UI
                                    if first_question:
                                        self._write_checkin_response(user_id, first_question)
                    
                    # Clean up the request file
                    os.remove(file_path)
                    logger.info(f"Processed check-in prompt request: {filename}")
                except Exception as e:
                    logger.error(f"Error processing check-in prompt request {filename}: {e}")
                    try:
                        os.remove(file_path)
                    except Exception:
                        pass
    
    @handle_errors("getting check-in first question", default_return=None)
    def _get_checkin_first_question(self, user_id: str) -> str:
        """Get the first question that will be asked in the check-in."""
        try:
            from communication.message_processing.conversation_flow_manager import conversation_manager
            from core.user_data_handlers import get_user_data
            
            # Get enabled questions
            prefs_result = get_user_data(user_id, 'preferences')
            checkin_prefs = prefs_result.get('preferences', {}).get('checkin_settings', {})
            enabled_questions = checkin_prefs.get('questions', {})
            
            # Get question order (same logic as service will use)
            question_order = conversation_manager._select_checkin_questions_with_weighting(user_id, enabled_questions)
            if question_order:
                first_question_key = question_order[0]
                first_question = conversation_manager._get_question_text(first_question_key, {})
                return first_question
        except Exception as e:
            logger.debug(f"Could not get check-in first question: {e}")
        return None
    
    @handle_errors("writing check-in response", default_return=None)
    def _write_checkin_response(self, user_id: str, first_question: str):
        """Write the first check-in question to a response file for the UI to read."""
        try:
            import json
            from datetime import datetime
            base_dir = self._check_test_message_requests__get_base_directory()
            response_file = Path(base_dir) / f'checkin_prompt_response_{user_id}.flag'
            
            response_data = {
                "user_id": user_id,
                "first_question": first_question,
                "timestamp": datetime.now().isoformat()
            }
            
            with open(response_file, 'w') as f:
                json.dump(response_data, f, indent=2)
            
            logger.debug(f"Wrote check-in prompt response file: {response_file}")
        except Exception as e:
            logger.debug(f"Could not write check-in response file: {e}")
    
    @handle_errors("checking task reminder requests")
    def check_task_reminder_requests(self):
        """Check for and process task reminder request files from admin panel"""
        base_dir = self._check_test_message_requests__get_base_directory()
        base_path = Path(base_dir)
        
        for file_path in base_path.iterdir():
            if file_path.is_file() and file_path.name.startswith('task_reminder_request_') and file_path.name.endswith('.flag'):
                filename = os.path.basename(file_path)
                try:
                    import json
                    with open(file_path, 'r') as f:
                        request_data = json.load(f)
                    
                    user_id = request_data.get('user_id')
                    task_id = request_data.get('task_id')
                    if user_id and task_id and self.communication_manager:
                        self.communication_manager.handle_task_reminder(user_id, task_id)
                        logger.info(f"Task reminder sent successfully for {user_id}, task {task_id}")
                    
                    # Clean up the request file
                    os.remove(file_path)
                    logger.info(f"Processed task reminder request: {filename}")
                except Exception as e:
                    logger.error(f"Error processing task reminder request {filename}: {e}")
                    try:
                        os.remove(file_path)
                    except Exception:
                        pass
    
    @handle_errors("getting base directory for cleanup", default_return="")
    def _cleanup_test_message_requests__get_base_directory(self):
        """Get the base directory for test message request files."""
        return os.path.dirname(os.path.dirname(__file__))
    
    @handle_errors("checking if file is test message request", default_return=False)
    def _cleanup_test_message_requests__is_test_message_request_file(self, filename):
        """Check if a filename matches the test message request file pattern."""
        return filename.startswith('test_message_request_') and filename.endswith('.flag')
    
    def _cleanup_test_message_requests__remove_request_file(self, request_file, filename):
        """Remove a single test message request file with proper error handling."""
        try:
            os.remove(request_file)
            logger.info(f"Cleanup: Removed test message request file: {filename}")
            return True
        except Exception as e:
            logger.warning(f"Could not remove test message request file {filename}: {e}")
            return False

    @handle_errors("cleaning up test message requests")
    def cleanup_test_message_requests(self):
        """Clean up any remaining test message request files"""
        base_dir = self._cleanup_test_message_requests__get_base_directory()
        base_path = Path(base_dir)
        
        for file_path in base_path.iterdir():
            if file_path.is_file() and self._cleanup_test_message_requests__is_test_message_request_file(file_path.name):
                self._cleanup_test_message_requests__remove_request_file(str(file_path), file_path.name)

    @handle_errors("getting base directory for reschedule requests", default_return="")
    def _check_reschedule_requests__get_base_directory(self):
        """Get the base directory for reschedule request files."""
        return os.path.dirname(os.path.dirname(__file__))

    @handle_errors("discovering reschedule request files", default_return=[])
    def _check_reschedule_requests__discover_request_files(self, base_dir):
        """Discover all reschedule request files in the base directory."""
        base_path = Path(base_dir)
        request_files = []
        for file_path in base_path.iterdir():
            if file_path.is_file() and file_path.name.startswith('reschedule_request_') and file_path.name.endswith('.flag'):
                request_files.append(str(file_path))
        return request_files

    @handle_errors("parsing reschedule request file", default_return={'user_id': None, 'category': None, 'source': 'unknown', 'timestamp': 0})
    def _check_reschedule_requests__parse_request_file(self, request_file):
        """Parse and validate a reschedule request file."""
        import json
        
        with open(request_file, 'r') as f:
            request_data = json.load(f)
        
        user_id = request_data.get('user_id')
        category = request_data.get('category')
        source = request_data.get('source', 'unknown')
        request_timestamp = request_data.get('timestamp', 0)
        
        return {
            'user_id': user_id,
            'category': category,
            'source': source,
            'timestamp': request_timestamp
        }

    @handle_errors("validating reschedule request data", default_return=False)
    def _check_reschedule_requests__validate_request_data(self, request_data, filename):
        """Validate request data and check if it should be processed."""
        user_id = request_data['user_id']
        category = request_data['category']
        request_timestamp = request_data['timestamp']
        
        # Skip old requests that were created before service startup
        if self.startup_time and request_timestamp < self.startup_time:
            logger.debug(f"Ignoring old reschedule request from before service startup: {filename}")
            return False
        
        if not user_id or not category:
            logger.warning(f"Invalid reschedule request in {filename}: missing user_id or category")
            return False
        
        return True

    @handle_errors("processing reschedule request", default_return=None)
    def _check_reschedule_requests__process_valid_request(self, request_data):
        """Process a valid reschedule request."""
        user_id = request_data['user_id']
        category = request_data['category']
        source = request_data['source']
        
        logger.info(f"Processing reschedule request from {source}: user={user_id}, category={category}")
        
        if self.scheduler_manager:
            # Reset and reschedule for this user/category
            self.scheduler_manager.reset_and_reschedule_daily_messages(category, user_id)
            logger.info(f"Reschedule completed for {user_id}, category={category}")
        else:
            logger.error("Scheduler manager not available for reschedule")

    def _check_reschedule_requests__cleanup_request_file(self, request_file, filename):
        """Clean up a processed request file."""
        try:
            os.remove(request_file)
            logger.info(f"Processed reschedule request: {filename}")
        except Exception as cleanup_error:
            logger.warning(f"Could not remove request file {filename}: {cleanup_error}")

    @handle_errors("cleaning up problematic reschedule request file", user_friendly=False, default_return=None)
    def _check_reschedule_requests__handle_processing_error(self, request_file, filename, error):
        """Handle errors during request processing."""
        logger.error(f"Error processing reschedule request {filename}: {error}")
        # Try to remove the problematic file
        os.remove(request_file)
        logger.debug(f"Removed problematic request file: {filename}")

    def check_reschedule_requests(self):
        """Check for and process reschedule request files from UI"""
        base_dir = self._check_reschedule_requests__get_base_directory()
        request_files = self._check_reschedule_requests__discover_request_files(base_dir)
        
        for request_file in request_files:
            filename = os.path.basename(request_file)
            
            try:
                # Parse and validate the request
                request_data = self._check_reschedule_requests__parse_request_file(request_file)
                
                if self._check_reschedule_requests__validate_request_data(request_data, filename):
                    self._check_reschedule_requests__process_valid_request(request_data)
                
                # Clean up the request file
                self._check_reschedule_requests__cleanup_request_file(request_file, filename)
                
            except Exception as e:
                self._check_reschedule_requests__handle_processing_error(request_file, filename, e)

    @handle_errors("cleaning up reschedule requests")
    def cleanup_reschedule_requests(self):
        """Clean up any remaining reschedule request files"""
        base_dir = Path(__file__).parent.parent
        
        for file_path in base_dir.iterdir():
            if file_path.is_file() and file_path.name.startswith('reschedule_request_') and file_path.name.endswith('.flag'):
                try:
                    file_path.unlink()
                    logger.info(f"Cleanup: Removed reschedule request file: {file_path.name}")
                except Exception as e:
                    logger.warning(f"Could not remove reschedule request file {file_path.name}: {e}")

    @handle_errors("shutting down service")
    def shutdown(self):
        """Gracefully shutdown the service"""
        logger.info("Shutting down MHM Backend Service...")
        self.running = False
        
        try:
            if self.communication_manager:
                self.communication_manager.stop_all()
                logger.info("Communication manager stopped")
        except Exception as e:
            logger.error(f"Error stopping communication manager: {e}")
        
        try:
            if self.scheduler_manager:
                self.scheduler_manager.stop_scheduler()
                logger.info("Scheduler manager stopped")
        except Exception as e:
            logger.error(f"Error stopping scheduler manager: {e}")
        
        # Clean up shutdown request file if it exists
        shutdown_file = Path(__file__).parent.parent / 'shutdown_request.flag'
        try:
            if shutdown_file.exists():
                shutdown_file.unlink()
                logger.info("Cleanup: Removed shutdown request file")
        except Exception as e:
            logger.warning(f"Could not remove shutdown file: {e}")
        
        logger.info("MHM Backend Service shutdown complete")

        # Stop file auditor last
        try:
                from core.file_auditor import stop_auditor
                stop_auditor()
        except Exception:
            pass

    @handle_errors("handling shutdown signal", default_return=None)
    def signal_handler(self, signum, frame):
        """
        Handle shutdown signals for graceful service termination.
        
        Args:
            signum: Signal number
            frame: Current stack frame
        """
        logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        self.shutdown()

    @handle_errors("emergency shutdown")
    def emergency_shutdown(self):
        """Emergency shutdown handler registered with atexit"""
        if self.running:
            logger.critical("Emergency shutdown triggered!")
            try:
                self.shutdown()
            except Exception as e:
                logger.critical(f"Error during emergency shutdown: {e}")
                # Force stop communication manager
                try:
                    if self.communication_manager:
                        self.communication_manager.stop_all()
                except:
                    pass
                # Force stop scheduler manager
                try:
                    if self.scheduler_manager:
                        self.scheduler_manager.stop_scheduler()
                except:
                    pass

@handle_errors("getting scheduler manager", default_return=None)
def get_scheduler_manager():
    """Get the scheduler manager instance from the global service.
    Safely handle cases where the global 'service' symbol may not be defined yet.
    """
    try:
        global service
    except NameError:
        return None
    if 'service' in globals() and service and hasattr(service, 'scheduler_manager'):
        return service.scheduler_manager
    return None

@handle_errors("main service function")
def main():
    """
    Main entry point for the MHM backend service.
    
    Creates and starts the service, handling initialization errors and graceful shutdown.
    """
    service = MHMService()
    service.start()

if __name__ == "__main__":
    main() 
