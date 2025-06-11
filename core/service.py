# service.py - MHM Backend Service (No UI)

import signal
import sys
import time
import logging
import os
import atexit

# Add parent directory to path so we can import from other modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set up logging FIRST before any other imports
from core.logger import setup_logging, get_logger
setup_logging()
logger = get_logger(__name__)
logger.debug("Logging setup successfully.")

# Register channels BEFORE importing CommunicationManager
from bot.channel_registry import register_all_channels
register_all_channels()

# Now import the rest
from bot.communication_manager import CommunicationManager
from core.config import LOG_FILE_PATH, HERMES_FILE_PATH, USER_INFO_DIR_PATH
from core.scheduler import SchedulerManager
from core.utils import verify_file_access, get_all_user_ids, load_and_ensure_ids, determine_file_path, get_user_preferences

class InitializationError(Exception):
    """Custom exception for initialization errors."""
    pass

class MHMService:
    def __init__(self):
        self.communication_manager = None
        self.scheduler_manager = None
        self.running = False
        # Register atexit handler as backup shutdown method
        atexit.register(self.emergency_shutdown)
        
    def initialize_paths(self):
        paths = [
            LOG_FILE_PATH,
            HERMES_FILE_PATH,
            USER_INFO_DIR_PATH
        ]
        
        try:
            user_ids = get_all_user_ids()
            logger.debug(f"User IDs retrieved: {user_ids}")
            for user_id in user_ids:
                if user_id is None:
                    logger.warning("Encountered None user_id in get_all_user_ids()")
                    continue
                categories = get_user_preferences(user_id, ['categories'])
                if categories and isinstance(categories, list):
                    for category in categories:
                        try:
                            path = determine_file_path('messages', f'{category}/{user_id}')
                            paths.append(path)
                        except ValueError as e:
                            logger.error(f"Error determining file path for category '{category}' and user '{user_id}': {e}")
                else:
                    logger.warning(
                        f"Expected list for categories, got {type(categories)} for user '{user_id}'"
                    )
        except Exception as e:
            logger.error(f"Error initializing paths: {e}", exc_info=True)
            raise

        logger.debug(f"Paths initialized: {paths}")
        return paths

    def check_and_fix_logging(self):
        """Check if logging is working and restart if needed"""
        global logger
        
        try:
            # Test if logging is actually working by checking the file size before/after
            from core.config import LOG_FILE_PATH
            
            # Get current file size
            initial_size = 0
            if os.path.exists(LOG_FILE_PATH):
                initial_size = os.path.getsize(LOG_FILE_PATH)
            
            # Write a test message
            import time
            test_timestamp = int(time.time())
            test_message = f"Logging system test - {test_timestamp}"
            logger.info(test_message)
            
            # Force flush all handlers
            root_logger = logging.getLogger()
            for handler in root_logger.handlers:
                handler.flush()
            
            # Small delay to ensure write completes
            time.sleep(0.2)
            
            # Check if file size increased or if we can find our test message
            logging_working = False
            
            if os.path.exists(LOG_FILE_PATH):
                new_size = os.path.getsize(LOG_FILE_PATH)
                if new_size > initial_size:
                    # File grew, likely working
                    logging_working = True
                else:
                    # Check if we can find our test message in the file
                    try:
                        with open(LOG_FILE_PATH, 'r', encoding='utf-8') as f:
                            content = f.read()
                            if test_message in content:
                                logging_working = True
                    except Exception:
                        pass
            
            if logging_working:
                logger.info("Logging system verified and working properly")
                return
            
            # If we get here, logging is broken
            print("Logging system is not working properly - attempting force restart...")
            
            # Force restart logging
            from core.logger import force_restart_logging
            if force_restart_logging():
                logger = get_logger(__name__)
                logger.info("Logging system force restarted successfully")
            else:
                print("Failed to restart logging system")
                
        except Exception as e:
            print(f"Logging system error: {e}")
            try:
                from core.logger import force_restart_logging
                if force_restart_logging():
                    logger = get_logger(__name__)
                    logger.info("Logging system recovered from error")
            except Exception as restart_error:
                print(f"Failed to restart logging: {restart_error}")

    def start(self):
        """Start the MHM service"""
        max_retries = 3
        
        try:
            logger.info("Starting MHM Backend Service.")
            self.running = True

            # Check and fix logging BEFORE any async operations
            self.check_and_fix_logging()
            logger.info("Logging system verified before channel initialization")

            # Automatic cache cleanup (only if needed)
            try:
                from core.auto_cleanup import auto_cleanup_if_needed
                cleanup_performed = auto_cleanup_if_needed()
                if cleanup_performed:
                    logger.info("Automatic cache cleanup completed successfully")
            except Exception as e:
                logger.warning(f"Automatic cache cleanup failed (non-critical): {e}")

            # Step 1: Initialize paths and check file access
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
            logger.info("Starting scheduler for all users...")
            self.scheduler_manager.run_daily_scheduler()
            logger.info("Scheduler started and running for all users")

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

    def run_service_loop(self):
        """Keep the service running until shutdown is requested"""
        logger.info("Service is now running. Press Ctrl+C to stop.")
        shutdown_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'shutdown_request.flag')
        
        # Initialize loop counter outside the main loop
        loop_minutes = 0
        
        try:
            while self.running:
                # Check for shutdown file every 2 seconds for faster response
                for i in range(30):  # 30 * 2 = 60 seconds total
                    if not self.running:
                        break
                    
                    # Check for shutdown request file every iteration
                    if os.path.exists(shutdown_file):
                        logger.info("Shutdown request file detected - initiating graceful shutdown")
                        try:
                            with open(shutdown_file, 'r') as f:
                                content = f.read().strip()
                            logger.info(f"Shutdown request details: {content}")
                        except Exception as e:
                            logger.warning(f"Could not read shutdown file: {e}")
                        self.running = False
                        break
                    
                    # Check for test message request files
                    self.check_test_message_requests()
                    
                    time.sleep(2)  # Sleep for 2 seconds
                
                # Log heartbeat every 2 minutes (every 2 loop iterations)
                loop_minutes += 1
                if loop_minutes % 2 == 0:
                    logger.info(f"Service running normally ({loop_minutes} minutes uptime)")
                    
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt (Ctrl+C).")
            self.running = False
        except Exception as e:
            logger.error(f"Unexpected error in service loop: {e}", exc_info=True)
            self.running = False
        finally:
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
    
    def check_test_message_requests(self):
        """Check for and process test message request files from admin panel"""
        try:
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
                        
        except Exception as e:
            logger.debug(f"Error checking for test message requests: {e}")  # Debug level since this runs frequently
    
    def cleanup_test_message_requests(self):
        """Clean up any remaining test message request files"""
        try:
            base_dir = os.path.dirname(os.path.dirname(__file__))
            
            for filename in os.listdir(base_dir):
                if filename.startswith('test_message_request_') and filename.endswith('.flag'):
                    request_file = os.path.join(base_dir, filename)
                    try:
                        os.remove(request_file)
                        logger.info(f"Cleanup: Removed test message request file: {filename}")
                    except Exception as e:
                        logger.warning(f"Could not remove test message request file {filename}: {e}")
                        
        except Exception as e:
            logger.warning(f"Error during test message request cleanup: {e}")

    def shutdown(self):
        """Shutdown the service gracefully"""
        logger.info("Shutting down MHM Backend Service.")
        self.running = False
        
        try:
            if self.communication_manager:
                logger.info("Stopping communication manager...")
                self.communication_manager.stop_all()
                logger.info("Communication manager stopped successfully.")
            if self.scheduler_manager:
                logger.info("Stopping scheduler manager...")
                self.scheduler_manager.stop_scheduler()
                logger.info("Scheduler manager stopped successfully.")
        except Exception as e:
            logger.error(f"Error during shutdown: {e}", exc_info=True)
        finally:
            logger.info("MHM Backend Service shutdown complete.")
            # Force flush all logging before exit
            import logging
            logging.shutdown()

    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}. Initiating shutdown...")
        self.running = False
        self.shutdown()

    def emergency_shutdown(self):
        """Emergency shutdown called by atexit - ensures logging even if terminated abruptly"""
        if self.running:  # Only log if we haven't already shut down gracefully
            logger.info("Emergency shutdown triggered (process terminating)")
            self.running = False
            try:
                if self.communication_manager:
                    logger.info("Emergency stop: communication manager")
                    self.communication_manager.stop_all()
                if self.scheduler_manager:
                    logger.info("Emergency stop: scheduler manager")
                    self.scheduler_manager.stop_scheduler()
            except Exception as e:
                logger.error(f"Error during emergency shutdown: {e}")
            finally:
                logger.info("Emergency shutdown complete")
                # Force flush logs
                for handler in logger.handlers:
                    handler.flush()
                logging.shutdown()

def main():
    """Main entry point for the service"""
    service = MHMService()
    
    # Set up signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, service.signal_handler)
    signal.signal(signal.SIGTERM, service.signal_handler)
    
    # On Windows, also handle SIGBREAK (Ctrl+Break)
    if hasattr(signal, 'SIGBREAK'):
        signal.signal(signal.SIGBREAK, service.signal_handler)
    
    try:
        service.start()
    except Exception as e:
        logger.error(f"Service failed to start: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main() 