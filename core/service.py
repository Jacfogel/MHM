# service.py - MHM Backend Service (No UI)

import signal
import sys
import time
import os
import atexit
from datetime import datetime
from typing import List

# Add parent directory to path so we can import from other modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set up logging FIRST before any other imports
from core.logger import setup_logging, get_logger, get_component_logger
import logging  # kept for tests that patch core.service.logging.getLogger
setup_logging()
logger = get_component_logger('main')
main_logger = logger  # Alias for backward compatibility
discord_logger = get_component_logger('discord')
logger.debug("Logging setup successfully.")

# Start file creation auditor early (developer tool)
try:
        from ai_tools.file_auditor import start_auditor
        start_auditor()
except Exception as _fa_err:
    logger.debug(f"File auditor not started: {_fa_err}")

# Import configuration validation
from core.config import validate_and_raise_if_invalid, print_configuration_report, ConfigValidationError

# Import the communication manager (channels auto-register from config)
from communication.core.channel_orchestrator import CommunicationManager
from core.config import LOG_MAIN_FILE, USER_INFO_DIR_PATH, get_user_data_dir
from core.scheduler import SchedulerManager
from core.file_operations import verify_file_access, determine_file_path
from core.user_data_handlers import get_all_user_ids
from core.user_data_handlers import get_user_data

# Expose get_user_data at module level so tests
# that patch core.service.get_user_data continue to work.

from core.error_handling import (
    error_handler, DataError, FileOperationError, handle_errors
)

class InitializationError(Exception):
    """Custom exception for initialization errors."""
    pass

class MHMService:
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
        main_logger.info("Service configuration validation started")
        
        # Print configuration report for debugging
        print_configuration_report()
        
        # Validate configuration and get available channels
        available_channels = validate_and_raise_if_invalid()
        
        logger.info(f"Configuration validation passed. Available channels: {', '.join(available_channels)}")
        main_logger.info("Service configuration validation completed", available_channels=available_channels)
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
    def check_and_fix_logging(self):
        """Check if logging is working and restart if needed"""
        global logger
        
        # Simple test: try to log a message and see if it works
        test_timestamp = int(time.time())
        test_message = f"Logging verification - {test_timestamp}"
        
        # Try logging at different levels to test all handlers
        try:
            logger.debug(test_message)
            
            # Force flush all handlers to ensure messages are written
            root_logger = logging.getLogger()
            for handler in root_logger.handlers:
                if hasattr(handler, 'flush'):
                    handler.flush()
            
            # Give more time for file operations and buffering
            time.sleep(0.5)
            
            # Check if log file exists and is accessible
            from core.config import LOG_MAIN_FILE
            if not os.path.exists(LOG_MAIN_FILE):
                logger.warning("Log file does not exist - logging may have issues")
                raise Exception("Log file missing")
            
            # Try to read the last few lines to verify logging is working
            try:
                with open(LOG_MAIN_FILE, 'r', encoding='utf-8') as f:
                    # Read last 1000 characters to check for recent activity
                    f.seek(0, 2)  # Go to end
                    file_size = f.tell()
                    if file_size > 1000:
                        f.seek(file_size - 1000)
                    else:
                        f.seek(0)
                    recent_content = f.read()
                    
                    # Look for our test message or recent timestamp patterns
                    if (test_message in recent_content or 
                        any(str(test_timestamp - i) in recent_content for i in range(60))):
                        logger.debug("Logging system verified")
                        return
                    else:
                        # Check if there's any recent activity (within last 5 minutes)
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
                                    return
                            except ValueError:
                                pass  # Failed to parse timestamp, continue to restart check
                        
                        logger.warning("No recent logging activity detected, may need restart")
            
            except Exception as file_error:
                logger.warning(f"Could not verify log file contents: {file_error}")
                # Don't force restart just because we can't read the file
                # The fact that logger.debug() and logger.warning() worked above is sufficient
                logger.debug("Logging system working despite file read issues")
                return
            
        except Exception as log_error:
            # If we can't even log, then we definitely have a problem
            logger.error(
                "Logging system is not working - cannot write log messages: %s",
                log_error,
            )
            # Fall through to restart logic
        
        # Only restart if we have clear evidence of logging failure
        logger.warning(
            "Logging system verification failed - attempting force restart..."
        )
        
        # Force restart logging
        from core.logger import force_restart_logging
        if force_restart_logging():
            logger = get_component_logger('main')
            logger.info("Logging system force restarted successfully")
        else:
            logger.error("Failed to restart logging system")

    @handle_errors("starting service")
    def start(self):
        """
        Start the MHM backend service.
        
        Initializes communication channels, scheduler, and begins the main service loop.
        Sets up signal handlers for graceful shutdown.
        """
        logger.info("Starting MHM Backend Service...")
        main_logger.info("MHM backend service startup initiated")
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

            # Step 2: Start CommunicationManager (Telegram, Email, Discord)
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
            main_logger.info("MHM backend service initialized successfully", startup_time=self.startup_time)
            
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
        shutdown_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'shutdown_request.flag')
        
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
                
                # Check for test message request files
                self.check_test_message_requests()
                
                # Check for reschedule request files
                self.check_reschedule_requests()
                
                time.sleep(2)  # Sleep for 2 seconds
            
            # Log heartbeat every 10 minutes instead of every 2 minutes to reduce log spam
            loop_minutes += 1
            if loop_minutes % 10 == 0:
                logger.info(f"Service running normally ({loop_minutes} minutes uptime)")
                
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
                                discord_logger.debug(f"Discord healthy - Latency: {latency}s, Guilds: {guild_count}")
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
    def check_test_message_requests(self):
        """Check for and process test message request files from admin panel"""
        base_dir = os.path.dirname(os.path.dirname(__file__))
        
        # Look for test message request files
        for filename in os.listdir(base_dir):
            if filename.startswith('test_message_request_') and filename.endswith('.flag'):
                request_file = os.path.join(base_dir, filename)
                
                try:
                    # Read and process the request
                    with open(request_file, 'r') as f:
                        import json
                        request_data = json.load(f)
                    
                    user_id = request_data.get('user_id')
                    category = request_data.get('category')
                    source = request_data.get('source', 'unknown')
                    
                    if user_id and category:
                        logger.info(f"Processing test message request from {source}: user={user_id}, category={category}")
                        
                        # Use the communication manager to send the message
                        if self.communication_manager:
                            self.communication_manager.handle_message_sending(user_id, category)
                            logger.info(f"Test message sent successfully for {user_id}, category={category}")
                        else:
                            logger.error("Communication manager not available for test message")
                    else:
                        logger.warning(f"Invalid test message request in {filename}: missing user_id or category")
                    
                    # Remove the processed request file
                    os.remove(request_file)
                    logger.info(f"Processed test message request: {filename}")
                    
                except Exception as e:
                    logger.error(f"Error processing test message request {filename}: {e}")
                    # Try to remove the problematic file
                    try:
                        os.remove(request_file)
                        logger.debug(f"Removed problematic request file: {filename}")
                    except Exception as cleanup_error:
                        logger.warning(f"Could not remove problematic request file {filename}: {cleanup_error}")
    
    @handle_errors("cleaning up test message requests")
    def cleanup_test_message_requests(self):
        """Clean up any remaining test message request files"""
        base_dir = os.path.dirname(os.path.dirname(__file__))
        
        for filename in os.listdir(base_dir):
            if filename.startswith('test_message_request_') and filename.endswith('.flag'):
                request_file = os.path.join(base_dir, filename)
                try:
                    os.remove(request_file)
                    logger.info(f"Cleanup: Removed test message request file: {filename}")
                except Exception as e:
                    logger.warning(f"Could not remove test message request file {filename}: {e}")

    @handle_errors("checking reschedule requests")
    def check_reschedule_requests(self):
        """Check for and process reschedule request files from UI"""
        base_dir = os.path.dirname(os.path.dirname(__file__))
        
        # Look for reschedule request files
        for filename in os.listdir(base_dir):
            if filename.startswith('reschedule_request_') and filename.endswith('.flag'):
                request_file = os.path.join(base_dir, filename)
                
                try:
                    # Read and process the request
                    with open(request_file, 'r') as f:
                        import json
                        request_data = json.load(f)
                    
                    user_id = request_data.get('user_id')
                    category = request_data.get('category')
                    source = request_data.get('source', 'unknown')
                    request_timestamp = request_data.get('timestamp', 0)
                    
                    # Skip old requests that were created before service startup
                    if self.startup_time and request_timestamp < self.startup_time:
                        logger.debug(f"Ignoring old reschedule request from before service startup: {filename}")
                        os.remove(request_file)
                        continue
                    
                    if user_id and category:
                        # Process the reschedule request
                        logger.info(f"Processing reschedule request from {source}: user={user_id}, category={category}")
                        
                        if self.scheduler_manager:
                            # Reset and reschedule for this user/category
                            self.scheduler_manager.reset_and_reschedule_daily_messages(category, user_id)
                            logger.info(f"Reschedule completed for {user_id}, category={category}")
                        else:
                            logger.error("Scheduler manager not available for reschedule")
                    else:
                        logger.warning(f"Invalid reschedule request in {filename}: missing user_id or category")
                    
                    # Remove the processed request file
                    os.remove(request_file)
                    logger.info(f"Processed reschedule request: {filename}")
                    
                except Exception as e:
                    logger.error(f"Error processing reschedule request {filename}: {e}")
                    # Try to remove the problematic file
                    try:
                        os.remove(request_file)
                        logger.debug(f"Removed problematic request file: {filename}")
                    except Exception as cleanup_error:
                        logger.warning(f"Could not remove problematic request file {filename}: {cleanup_error}")

    @handle_errors("cleaning up reschedule requests")
    def cleanup_reschedule_requests(self):
        """Clean up any remaining reschedule request files"""
        base_dir = os.path.dirname(os.path.dirname(__file__))
        
        for filename in os.listdir(base_dir):
            if filename.startswith('reschedule_request_') and filename.endswith('.flag'):
                request_file = os.path.join(base_dir, filename)
                try:
                    os.remove(request_file)
                    logger.info(f"Cleanup: Removed reschedule request file: {filename}")
                except Exception as e:
                    logger.warning(f"Could not remove reschedule request file {filename}: {e}")

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
        
        logger.info("MHM Backend Service shutdown complete")

        # Stop file auditor last
        try:
                from ai_tools.file_auditor import stop_auditor
                stop_auditor()
        except Exception:
            pass

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

# Import get_user_categories from user_management to avoid duplication
from core.user_management import get_user_categories

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