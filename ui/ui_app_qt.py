import sys
import os
import subprocess
import psutil
import time
import re
from pathlib import Path
from datetime import datetime

# Add parent directory to path so we can import from core
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from run_mhm import resolve_python_interpreter, prepare_launch_environment

# PySide6 imports
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QMessageBox,
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QWidget
)
from PySide6.QtCore import QTimer
from PySide6.QtGui import QFont

# Set up logging
from core.logger import setup_logging, get_component_logger
setup_logging()
logger = get_component_logger('ui')
ui_logger = logger

# Import configuration validation
from core.config import validate_all_configuration

# Import comprehensive error handling
from core.error_handling import handle_errors

from user.user_context import UserContext
from core.user_data_handlers import get_all_user_ids
from core.user_data_handlers import get_user_data
from core.user_data_validation import _shared__title_case
import core.config

# Import generated UI for main window
from ui.generated.admin_panel_pyqt import Ui_ui_app_mainwindow

class ServiceManager:
    """Manages the MHM backend service process"""
    
    @handle_errors("initializing service manager", default_return=None)
    def __init__(self):
        """Initialize the object."""
        self.service_process = None
        
    @handle_errors("validating configuration before start", default_return=False)
    def validate_configuration_before_start(self):
        """Validate configuration before attempting to start the service."""
        result = validate_all_configuration()
        
        if not result['valid']:
            error_message = "Configuration validation failed:\n\n"
            for error in result['errors']:
                error_message += f"• {error}\n"
            
            if result['warnings']:
                error_message += "\nWarnings:\n"
                for warning in result['warnings']:
                    error_message += f"• {warning}\n"
            
            QMessageBox.critical(None, "Configuration Error", error_message)
            return False
        
        # Filter out non-critical warnings that don't need popup
        critical_warnings = []
        for warning in result['warnings']:
            # Skip warnings about default values and auto-creation settings
            if any(skip_phrase in warning.lower() for skip_phrase in [
                'using default',
                'auto_create_user_dirs is enabled',
                'not set (using default)'
            ]):
                # Log these warnings but don't show popup
                logger.info(f"Configuration note: {warning}")
                continue
            critical_warnings.append(warning)
        
        # Only show popup for critical warnings
        if critical_warnings:
            warning_message = "Configuration warnings:\n\n"
            for warning in critical_warnings:
                warning_message += f"• {warning}\n"
            warning_message += "\nThe service will start, but you may want to address these warnings."
            QMessageBox.warning(None, "Configuration Warnings", warning_message)
        
        if not result['available_channels']:
            QMessageBox.warning(None, "No Communication Channels", 
                               "No communication channels are configured. The service will start but won't be able to send messages.")
        
        return True
        
    @handle_errors("checking service status", default_return=(False, None))
    def is_service_running(self):
        """
        Check if the MHM service is running with validation.
        
        Returns:
            tuple: (is_running, process_info)
        """
        """Check if the MHM service is running"""
        # Look for python processes running service.py as their main script
        service_pids = []
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            # Skip if process info is not accessible (already terminated)
            if not proc.info['name'] or 'python' not in proc.info['name'].lower():
                continue
            
            cmdline = proc.info.get('cmdline', [])
            # Only detect processes that are actually running service.py as their main script
            # Check if the last argument in cmdline is service.py (the main script being run)
            if (cmdline and len(cmdline) >= 2 and 
                cmdline[-1].endswith('service.py') and 
                'service.py' in cmdline[-1]):
                # Double-check process is still running
                if proc.is_running():
                    service_pids.append(proc.info['pid'])
        
        if service_pids:
            return True, service_pids[0]  # Return first PID
        return False, None
    
    @handle_errors("starting service", default_return=False)
    def start_service(self):
        """
        Start the MHM backend service with validation.
        
        Returns:
            bool: True if successful, False if failed
        """
        """Start the MHM backend service"""
        # Validate configuration before starting
        if not self.validate_configuration_before_start():
            return False
        
        is_running, pid = self.is_service_running()
        if is_running:
            logger.debug(f"Service already running with PID {pid}")
            QMessageBox.information(None, "Service Status", f"MHM Service is already running (PID: {pid})")
            return True
        
        # Start the service - updated path
        service_path = Path(__file__).parent.parent / 'core' / 'service.py'
        
        logger.debug(f"Service path: {service_path}")
        
        # Ensure we use the venv Python explicitly
        script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        python_executable = resolve_python_interpreter(script_dir)

        logger.debug(f"Using Python: {python_executable}")

        # Set up environment to ensure venv is used
        env = prepare_launch_environment(script_dir)
        
        # Run the service in the background without showing a console window
        if os.name == 'nt':  # Windows
            # Run without showing console window
            self.service_process = subprocess.Popen([
                python_executable, service_path
            ], env=env, cwd=script_dir, creationflags=subprocess.CREATE_NO_WINDOW)
        else:  # Unix/Linux/Mac
            # Run in background
            self.service_process = subprocess.Popen([
                python_executable, service_path
            ], env=env, cwd=script_dir, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        logger.debug("Service process started, waiting for initialization...")
        # Give it a moment to start
        time.sleep(2)
        
        is_running, pid = self.is_service_running()
        if is_running:
            logger.info(f"Service started with PID {pid}")
            QMessageBox.information(None, "Service Status", f"MHM Service started successfully (PID: {pid})")
            return True
        else:
            logger.error("Failed to start service")
            QMessageBox.critical(None, "Service Error", "Failed to start MHM Service")
            return False
    
    @handle_errors("stopping service", default_return=False)
    def stop_service(self):
        """
        Stop the MHM backend service with validation.
        
        Returns:
            bool: True if successful, False if failed
        """
        """Stop the MHM backend service"""
        is_running, pid = self.is_service_running()
        if not is_running:
            logger.info("Stop service requested but service is not running")
            QMessageBox.information(None, "Service Status", "MHM Service is not running")
            return True
        
        logger.info(f"Stop service requested for PID: {pid}")
        
        # Create shutdown request file
        shutdown_file = Path(__file__).parent.parent / 'shutdown_request.flag'
        try:
            with open(shutdown_file, 'w') as f:
                f.write(f"SHUTDOWN_REQUESTED_BY_UI_{time.time()}")
            logger.info(f"Created shutdown request file: {shutdown_file}")
        except Exception as e:
            logger.warning(f"Could not create shutdown file: {e}")
        
        # Wait for graceful shutdown (service checks shutdown file every 2 seconds)
        # Give it time to detect the file and shut down gracefully
        # Discord bot shutdown can take time (closing connections, stopping ngrok, etc.)
        logger.info("Waiting for graceful shutdown...")
        max_wait_time = 20  # Wait up to 20 seconds for graceful shutdown (Discord can take time)
        wait_interval = 0.5
        waited = 0
        
        while waited < max_wait_time:
            is_running, current_pid = self.is_service_running()
            if not is_running:
                logger.info("Service stopped gracefully")
                QMessageBox.information(None, "Service Status", "MHM Service stopped successfully")
                return True
            time.sleep(wait_interval)
            waited += wait_interval
            # Log progress every 5 seconds
            if int(waited) % 5 == 0:
                logger.debug(f"Still waiting for graceful shutdown... ({int(waited)}s elapsed)")
        
        # If graceful shutdown didn't work, force terminate
        logger.warning("Graceful shutdown timeout - forcing termination")
        
        # Try to terminate ALL service processes
        found_processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if not proc.info['name'] or 'python' not in proc.info['name'].lower():
                    continue
                cmdline = proc.info.get('cmdline', [])
                # Only detect processes that are actually running service.py as their main script
                # Check if the last argument in cmdline is service.py (the main script being run)
                if (cmdline and len(cmdline) >= 2 and 
                    cmdline[-1].endswith('service.py') and 
                    'service.py' in cmdline[-1]):
                    if proc.is_running():
                        found_processes.append(proc)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        
        if not found_processes:
            # Service already stopped
            logger.info("Service is not running - stop operation successful")
            QMessageBox.information(None, "Service Status", "Service is already stopped")
            return True
        else:
            if len(found_processes) > 1:
                logger.info(f"Found {len(found_processes)} service processes, cleaning up all instances")
            else:
                logger.info(f"Found {len(found_processes)} service process, terminating")
            
            for proc in found_processes:
                proc_pid = proc.info['pid']
                try:
                    proc.terminate()
                    logger.debug(f"Terminated process {proc_pid}")
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    logger.debug(f"Process {proc_pid} already terminated or access denied")
                    continue
            
            # Wait for processes to terminate
            time.sleep(2)
            
            # Force kill if still running
            for proc in found_processes:
                try:
                    if proc.is_running():
                        proc.kill()
                        logger.debug(f"Force killed process {proc.info['pid']}")
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # Final check
            time.sleep(0.5)
            is_running, current_pid = self.is_service_running()
            if not is_running:
                logger.info("Service stopped successfully (force termination)")
                QMessageBox.information(None, "Service Status", "MHM Service stopped successfully")
                return True
            else:
                logger.warning(f"Service still running with PID {current_pid} after termination attempts")
                QMessageBox.warning(None, "Service Status", f"Service may still be running (PID: {current_pid})")
                return False
    
    @handle_errors("restarting service", default_return=False)
    def restart_service(self):
        """
        Restart the MHM backend service with validation.
        
        Returns:
            bool: True if successful, False if failed
        """
        """Restart the MHM backend service"""
        logger.info("Restart service requested")
        
        # Stop the service
        if not self.stop_service():
            logger.error("Failed to stop service during restart")
            return False
        
        # Wait a moment for cleanup
        time.sleep(1)
        
        # Start the service
        if not self.start_service():
            logger.error("Failed to start service during restart")
            return False
        
        logger.info("Service restart completed successfully")
        return True


class MHMManagerUI(QMainWindow):
    """Main MHM Management UI using PySide6"""
    
    # ERROR_HANDLING_EXCLUDE: UI constructor - calls methods with error handling (load_ui, connect_signals, initialize_ui)
    def __init__(self):
        """Initialize the object."""
        super().__init__()
        self.service_manager = ServiceManager()
        self.current_user = None
        self.current_user_categories = []
        # Load the generated UI
        self.ui = Ui_ui_app_mainwindow()
        self.ui.setupUi(self)
        # Load the UI file (theme, etc.)
        self.load_ui()
        # Connect signals
        self.connect_signals()
        # Initialize UI state
        self.initialize_ui()
        # Set up timer for status updates
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_service_status)
        self.status_timer.start(5000)  # Update every 5 seconds
        # Initial status update
        self.update_service_status()
        
    @handle_errors("loading UI", default_return=None)
    def load_ui(self):
        """Load the UI from the .ui file"""
        ui_file_path = Path(__file__).parent / 'designs' / 'admin_panel.ui'
        if not ui_file_path.exists():
            raise FileNotFoundError(f"UI file not found: {ui_file_path}")

        # Load and apply the QSS theme
        self.load_theme()
        
    def load_theme(self):
        """Load and apply the QSS theme from the styles directory"""
        try:
            # Path to the QSS theme file
            theme_path = Path(__file__).parent.parent / 'styles' / 'admin_theme.qss'
            
            if theme_path.exists():
                with open(theme_path, 'r', encoding='utf-8') as f:
                    theme_content = f.read()
                
                # Apply the theme to the application
                self.setStyleSheet(theme_content)
                logger.info(f"QSS theme loaded successfully from: {theme_path}")
            else:
                logger.warning(f"QSS theme file not found: {theme_path}")
                
        except Exception as e:
            logger.error(f"Failed to load QSS theme: {e}")
        
    @handle_errors("connecting UI signals", default_return=None)
    def connect_signals(self):
        """Connect UI signals to slots"""
        # Service management buttons
        self.ui.pushButton_start_service.clicked.connect(self.start_service)
        self.ui.pushButton_stop_service.clicked.connect(self.stop_service)
        self.ui.pushButton_restart_service.clicked.connect(self.restart_service)

        self.ui.pushButton_run_scheduler.clicked.connect(self.run_full_scheduler)
        
        # User management
        self.ui.pushButton_create_new_user.clicked.connect(self.create_new_user)
        self.ui.comboBox_users.currentTextChanged.connect(self.on_user_selected)
        
        # User action buttons
        self.ui.pushButton_communication_settings.clicked.connect(self.manage_communication_settings)
        self.ui.pushButton_personalization.clicked.connect(self.manage_personalization)
        self.ui.pushButton_category_management.clicked.connect(self.manage_categories)
        self.ui.pushButton_user_analytics.clicked.connect(self.manage_user_analytics)
        self.ui.pushButton_checkin_settings.clicked.connect(self.manage_checkins)
        self.ui.pushButton_task_management.clicked.connect(self.manage_tasks)
        self.ui.pushButton_task_crud.clicked.connect(self.manage_task_crud)
        self.ui.pushButton_run_user_scheduler.clicked.connect(self.run_user_scheduler)
        
        # Category actions
        self.ui.comboBox_user_categories.currentTextChanged.connect(self.on_category_selected)
        self.ui.pushButton_edit_messages.clicked.connect(self.edit_user_messages)
        self.ui.pushButton_edit_schedules.clicked.connect(self.edit_user_schedules)
        self.ui.pushButton_send_test_message.clicked.connect(self.send_test_message)
        self.ui.pushButton_run_category_scheduler.clicked.connect(self.run_category_scheduler)
        
        # User actions
        self.ui.pushButton_send_checkin_prompt.clicked.connect(self.send_checkin_prompt)
        self.ui.pushButton_send_task_reminder.clicked.connect(self.send_task_reminder)
        
        # Menu actions
        self.ui.actionToggle_Verbose_Logging.triggered.connect(self.toggle_logging_verbosity)
        self.ui.actionView_Log_File.triggered.connect(self.view_log_file)
        self.ui.actionProcess_Watcher.triggered.connect(self.open_process_watcher)
        self.ui.actionView_Cache_Status.triggered.connect(self.view_cache_status)
        self.ui.actionForce_Clean_Cache.triggered.connect(self.force_clean_cache)
        self.ui.actionValidate_Configuration.triggered.connect(self.validate_configuration)
        self.ui.actionView_All_Users.triggered.connect(self.view_all_users_summary)
        self.ui.actionSystem_Health_Check.triggered.connect(self.system_health_check)
        
    @handle_errors("initializing UI", default_return=None)
    def initialize_ui(self):
        """Initialize the UI state"""
        # Disable category management until user is selected
        self.disable_content_management()
        
        # Update user index automatically on startup
        self.update_user_index_on_startup()
        
        # Load user list
        self.refresh_user_list()
    
    @handle_errors("updating user index on startup", default_return=None)
    def update_user_index_on_startup(self):
        """Automatically update the user index when the admin panel starts"""
        try:
            from core.user_data_manager import rebuild_user_index
            logger.info("Admin Panel: Updating user index on startup...")
            
            success = rebuild_user_index()
            if success:
                logger.info("Admin Panel: User index updated successfully on startup")
            else:
                logger.warning("Admin Panel: Failed to update user index on startup")
                
        except Exception as e:
            logger.error(f"Admin Panel: Error updating user index on startup: {e}")
            # Don't show error to user - this is a background maintenance task
    
    @handle_errors("updating service status", default_return=None)
    def update_service_status(self):
        """Update the service status display"""
        is_running, pid = self.service_manager.is_service_running()
        
        if is_running:
            self.ui.label_service_status.setText(f"Service Status: Running (PID: {pid})")
            self.ui.label_service_status.setStyleSheet("color: green; font-weight: bold;")
        else:
            self.ui.label_service_status.setText("Service Status: Stopped")
            self.ui.label_service_status.setStyleSheet("color: red; font-weight: bold;")
        
        # Update Discord channel status
        discord_running = self._check_discord_status()
        if discord_running:
            self.ui.label_discord_status.setText("Discord Channel: Running")
            self.ui.label_discord_status.setStyleSheet("color: green; font-weight: bold;")
        else:
            self.ui.label_discord_status.setText("Discord Channel: Stopped")
            self.ui.label_discord_status.setStyleSheet("color: red; font-weight: bold;")
        
        # Update Email channel status
        email_running = self._check_email_status()
        if email_running:
            self.ui.label_email_status.setText("Email Channel: Running")
            self.ui.label_email_status.setStyleSheet("color: green; font-weight: bold;")
        else:
            self.ui.label_email_status.setText("Email Channel: Stopped")
            self.ui.label_email_status.setStyleSheet("color: red; font-weight: bold;")
        
        # Update ngrok tunnel status
        ngrok_status = self._check_ngrok_status()
        if ngrok_status['running']:
            pid_text = f" (PID: {ngrok_status['pid']})" if ngrok_status['pid'] else ""
            self.ui.label_ngrok_status.setText(f"ngrok tunnel: Running{pid_text}")
            self.ui.label_ngrok_status.setStyleSheet("color: green; font-weight: bold;")
        else:
            self.ui.label_ngrok_status.setText("ngrok tunnel: Stopped")
            self.ui.label_ngrok_status.setStyleSheet("color: red; font-weight: bold;")
    
    @handle_errors("checking Discord channel status", default_return=False)
    def _check_discord_status(self) -> bool:
        """Check if Discord channel is actually running and connected
        
        IMPORTANT: This will NEVER return True if the service is stopped.
        Channels cannot run without the service, so we check service status first.
        
        Checks for:
        1. Initialization messages ("Discord bot initialized successfully" or "Discord connection status changed to: connected")
        2. Recent activity (messages received/sent, "Discord healthy" status)
        3. Falls back to assuming running if service is running and Discord is configured
        """
        try:
            # First check if service is running - channels can't run without the service
            is_running, service_pid = self.service_manager.is_service_running()
            if not is_running:
                return False  # Service stopped = channel stopped (guaranteed)
            
            # Check if Discord is configured
            from core.config import DISCORD_BOT_TOKEN
            if not DISCORD_BOT_TOKEN:
                return False
            
            # Check logs: if service is running, look for initialization message
            # and check if there's a shutdown message after it
            # Also check for recent activity as evidence Discord is running
            try:
                discord_log_file = Path(__file__).parent.parent / 'logs' / 'discord.log'
                if discord_log_file.exists():
                    with open(discord_log_file, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = f.readlines()
                    
                    # Find the most recent initialization message
                    last_init_time = None
                    last_shutdown_time = None
                    last_activity_time = None
                    
                    # Check for recent activity indicators (messages, health checks)
                    activity_indicators = [
                        'DISCORD_MESSAGE_RECEIVED',
                        'DISCORD_MESSAGE_PROCESS',
                        'Discord message handled successfully',
                        'Discord channel message sent',
                        'Discord healthy'
                    ]
                    
                    for line in reversed(lines):
                        # Look for initialization messages
                        if 'Discord bot initialized successfully' in line or 'Discord connection status changed to: connected' in line:
                            timestamp_match = re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', line)
                            if timestamp_match and last_init_time is None:
                                try:
                                    last_init_time = datetime.strptime(timestamp_match.group(1), '%Y-%m-%d %H:%M:%S')
                                except ValueError:
                                    pass
                        
                        # Look for shutdown messages
                        if 'Discord bot shutdown completed' in line:
                            timestamp_match = re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', line)
                            if timestamp_match and last_shutdown_time is None:
                                try:
                                    last_shutdown_time = datetime.strptime(timestamp_match.group(1), '%Y-%m-%d %H:%M:%S')
                                except ValueError:
                                    pass
                        
                        # Look for recent activity (more reliable indicator than just initialization)
                        if any(indicator in line for indicator in activity_indicators):
                            timestamp_match = re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', line)
                            if timestamp_match and last_activity_time is None:
                                try:
                                    last_activity_time = datetime.strptime(timestamp_match.group(1), '%Y-%m-%d %H:%M:%S')
                                except ValueError:
                                    pass
                    
                    # If we found recent activity (within last 5 minutes), Discord is definitely running
                    if last_activity_time:
                        time_since_activity = (datetime.now() - last_activity_time).total_seconds()
                        if time_since_activity < 300:  # Within last 5 minutes
                            return True
                    
                    # If we found an initialization, check if shutdown happened after it
                    if last_init_time:
                        # Check if initialization is recent (within last hour) to handle improper shutdowns
                        # If initialization is very old and service was restarted, channel might not be running
                        time_since_init = (datetime.now() - last_init_time).total_seconds()
                        
                        if last_shutdown_time is None or last_shutdown_time < last_init_time:
                            # Initialized and not shut down (or shutdown was before initialization)
                            # But if initialization is very old (>1 hour), be cautious - might be stale
                            if time_since_init < 3600:  # Within last hour
                                return True
                            # Old initialization - check if service PID suggests a restart
                            # If service PID changed, this is a new service instance
                            # We can't easily check this, so assume running if service is running
                            # (Better to show running than stopped if uncertain)
                            return True
                        # Shutdown happened after initialization - check if it's been restarted since
                        # Look for any initialization after the shutdown
                        for line in lines:
                            if 'Discord bot initialized successfully' in line or 'Discord connection status changed to: connected' in line:
                                timestamp_match = re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', line)
                                if timestamp_match:
                                    try:
                                        init_time = datetime.strptime(timestamp_match.group(1), '%Y-%m-%d %H:%M:%S')
                                        if init_time > last_shutdown_time:
                                            # Check if this restart is recent
                                            time_since_restart = (datetime.now() - init_time).total_seconds()
                                            if time_since_restart < 3600:  # Within last hour
                                                return True
                                    except ValueError:
                                        pass
                    else:
                        # No initialization found - but if we have recent activity, Discord is running
                        if last_activity_time:
                            time_since_activity = (datetime.now() - last_activity_time).total_seconds()
                            if time_since_activity < 3600:  # Within last hour
                                return True
                        # No initialization and no recent activity - channel likely not running
                        # But fall through to fallback logic below
                        pass
            except Exception as e:
                logger.debug(f"Error checking Discord logs: {e}")
                # Fallback: if service is running and Discord is configured, assume it's running
                # This handles cases where logs are unavailable
                return True
            
            # Fallback: if service is running and Discord is configured, assume it's running
            # This handles cases where logs don't have the expected messages but Discord is working
            return True
        except Exception as e:
            logger.debug(f"Error checking Discord status: {e}")
            return False
    
    @handle_errors("checking Email channel status", default_return=False)
    def _check_email_status(self) -> bool:
        """Check if Email channel is actually initialized and running
        
        IMPORTANT: This will NEVER return True if the service is stopped.
        Channels cannot run without the service, so we check service status first.
        """
        try:
            # First check if service is running - channels can't run without the service
            is_running, service_pid = self.service_manager.is_service_running()
            if not is_running:
                return False  # Service stopped = channel stopped (guaranteed)
            
            # Check if Email is configured
            from core.config import EMAIL_SMTP_SERVER, EMAIL_IMAP_SERVER, EMAIL_SMTP_USERNAME, EMAIL_SMTP_PASSWORD
            if not all([EMAIL_SMTP_SERVER, EMAIL_IMAP_SERVER, EMAIL_SMTP_USERNAME, EMAIL_SMTP_PASSWORD]):
                return False
            
            # Check logs: if service is running, look for initialization message
            # and check if there's a shutdown message after it
            # Also verify the service PID matches to detect restarts
            try:
                email_log_file = Path(__file__).parent.parent / 'logs' / 'email.log'
                if email_log_file.exists():
                    with open(email_log_file, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = f.readlines()
                    
                    # Find the most recent initialization and shutdown messages
                    last_init_time = None
                    last_shutdown_time = None
                    
                    for line in reversed(lines):
                        # Look for initialization messages
                        if 'EmailBot initialized successfully' in line:
                            timestamp_match = re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', line)
                            if timestamp_match and last_init_time is None:
                                try:
                                    last_init_time = datetime.strptime(timestamp_match.group(1), '%Y-%m-%d %H:%M:%S')
                                except ValueError:
                                    pass
                        
                        # Look for shutdown messages
                        if 'EmailBot stopped' in line:
                            timestamp_match = re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', line)
                            if timestamp_match and last_shutdown_time is None:
                                try:
                                    last_shutdown_time = datetime.strptime(timestamp_match.group(1), '%Y-%m-%d %H:%M:%S')
                                except ValueError:
                                    pass
                    
                    # If we found an initialization, check if shutdown happened after it
                    if last_init_time:
                        # Check if initialization is recent (within last hour) to handle improper shutdowns
                        # If initialization is very old and service was restarted, channel might not be running
                        time_since_init = (datetime.now() - last_init_time).total_seconds()
                        
                        if last_shutdown_time is None or last_shutdown_time < last_init_time:
                            # Initialized and not shut down (or shutdown was before initialization)
                            # But if initialization is very old (>1 hour), be cautious - might be stale
                            if time_since_init < 3600:  # Within last hour
                                return True
                            # Old initialization - check if service PID suggests a restart
                            # If service PID changed, this is a new service instance
                            # We can't easily check this, so assume running if service is running
                            # (Better to show running than stopped if uncertain)
                            return True
                        # Shutdown happened after initialization - check if it's been restarted since
                        # Look for any initialization after the shutdown
                        for line in lines:
                            if 'EmailBot initialized successfully' in line:
                                timestamp_match = re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', line)
                                if timestamp_match:
                                    try:
                                        init_time = datetime.strptime(timestamp_match.group(1), '%Y-%m-%d %H:%M:%S')
                                        if init_time > last_shutdown_time:
                                            # Check if this restart is recent
                                            time_since_restart = (datetime.now() - init_time).total_seconds()
                                            if time_since_restart < 3600:  # Within last hour
                                                return True
                                    except ValueError:
                                        pass
                    else:
                        # No initialization found - channel never started or logs are empty
                        # If service is running but no init message, channel likely failed to start
                        return False
            except Exception as e:
                logger.debug(f"Error checking Email logs: {e}")
                # Fallback: if service is running and Email is configured, assume it's running
                # This handles cases where logs are unavailable
                return True
            
            return False
        except Exception as e:
            logger.debug(f"Error checking Email status: {e}")
            return False
    
    @handle_errors("checking ngrok tunnel status", default_return={'running': False, 'pid': None})
    def _check_ngrok_status(self) -> dict:
        """Check if ngrok tunnel is running and return PID"""
        try:
            # Look for ngrok processes
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if not proc.info['name']:
                        continue
                    
                    # Check if process name contains 'ngrok'
                    proc_name = proc.info['name'].lower()
                    if 'ngrok' in proc_name:
                        # Check if it's actually running
                        if proc.is_running():
                            # Verify it's an HTTP tunnel (check cmdline)
                            cmdline = proc.info.get('cmdline', [])
                            if cmdline and 'http' in ' '.join(cmdline).lower():
                                return {'running': True, 'pid': proc.info['pid']}
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
            
            return {'running': False, 'pid': None}
        except Exception as e:
            logger.debug(f"Error checking ngrok status: {e}")
            return {'running': False, 'pid': None}
    
    @handle_errors("starting service", default_return=None)
    def start_service(self):
        """Start the MHM service"""
        if self.service_manager.start_service():
            self.update_service_status()
    
    @handle_errors("stopping service", default_return=None)
    def stop_service(self):
        """Stop the MHM service"""
        if self.service_manager.stop_service():
            self.update_service_status()
    
    @handle_errors("restarting service", default_return=None)
    def restart_service(self):
        """Restart the MHM service"""
        if self.service_manager.restart_service():
            self.update_service_status()
    
    def run_full_scheduler(self):
        """Run the full scheduler for all users"""
        try:
            from core.scheduler import run_full_scheduler_standalone
            
            logger.info("UI: Running full scheduler for all users")
            success = run_full_scheduler_standalone()
            
            if success:
                QMessageBox.information(None, "Scheduler", "Full scheduler started successfully for all users")
            else:
                QMessageBox.warning(None, "Scheduler", "Failed to start full scheduler")
        except Exception as e:
            logger.error(f"UI: Error running full scheduler: {e}")
            QMessageBox.critical(None, "Scheduler Error", f"Failed to run full scheduler: {e}")
    
    def run_user_scheduler(self):
        """Run scheduler for the selected user"""
        if not self.current_user:
            QMessageBox.warning(None, "Scheduler", "Please select a user first")
            return
        
        try:
            from core.scheduler import run_user_scheduler_standalone
            
            logger.info(f"UI: Running scheduler for user {self.current_user}")
            success = run_user_scheduler_standalone(self.current_user)
            
            if success:
                QMessageBox.information(None, "Scheduler", f"User scheduler started successfully for {self.current_user}")
            else:
                QMessageBox.warning(None, "Scheduler", f"Failed to start user scheduler for {self.current_user}")
        except Exception as e:
            logger.error(f"UI: Error running user scheduler: {e}")
            QMessageBox.critical(None, "Scheduler Error", f"Failed to run user scheduler: {e}")
    
    def run_category_scheduler(self):
        """Run scheduler for the selected user and category"""
        if not self.current_user:
            QMessageBox.warning(None, "Scheduler", "Please select a user first")
            return
        
        category = self.ui.comboBox_user_categories.currentText()
        if not category:
            QMessageBox.warning(None, "Scheduler", "Please select a category first")
            return
        
        try:
            from core.scheduler import run_category_scheduler_standalone
            
            logger.info(f"UI: Running category scheduler for user {self.current_user}, category {category}")
            success = run_category_scheduler_standalone(self.current_user, category)
            
            if success:
                QMessageBox.information(None, "Scheduler", f"Category scheduler started successfully for {self.current_user}, {category}")
            else:
                QMessageBox.warning(None, "Scheduler", f"Failed to start category scheduler for {self.current_user}, {category}")
        except Exception as e:
            logger.error(f"UI: Error running category scheduler: {e}")
            QMessageBox.critical(None, "Scheduler Error", f"Failed to run category scheduler: {e}")
    
    @handle_errors("refreshing user list", default_return=None)
    def refresh_user_list(self):
        """
        Refresh the user list with validation.
        
        Returns:
            None: Always returns None
        """
        """Refresh the user list in the combo box by reading user account files"""
        try:
            # Remember the currently selected user
            current_user_id = self.current_user
            
            # Get all user IDs from directories
            user_ids = get_all_user_ids()
            
            self.ui.comboBox_users.clear()
            self.ui.comboBox_users.addItem("Select a user...")
            
            # Collect user data for sorting
            users_data = []
            for user_id in user_ids:
                # Get user account, preferences, and context
                user_data_result = get_user_data(user_id, ['account', 'preferences', 'context'])
                user_account = user_data_result.get('account', {})
                user_preferences = user_data_result.get('preferences', {})
                user_context = user_data_result.get('context', {})
                
                if not user_account:
                    continue
                
                # Skip inactive users
                if user_account.get('account_status') != 'active':
                    continue
                
                internal_username = user_account.get('internal_username', 'Unknown')
                channel_type = user_preferences.get('channel', {}).get('type', 'unknown')
                preferred_name = user_context.get('preferred_name', '')
                
                # Determine enabled features
                features = user_account.get('features', {})
                enabled_features = []
                if features.get('automated_messages') == 'enabled':
                    enabled_features.append('automated_messages')
                    categories = user_preferences.get('categories', [])
                    enabled_features.extend(categories)
                if features.get('checkins') == 'enabled':
                    enabled_features.append('checkins')
                if features.get('task_management') == 'enabled':
                    enabled_features.append('task_management')
                
                users_data.append({
                    'user_id': user_id,
                    'internal_username': internal_username,
                    'preferred_name': preferred_name,
                    'channel_type': channel_type,
                    'enabled_features': enabled_features
                })
            
            # Sort users by preferred name, then internal username
            sorted_users = sorted(
                users_data,
                key=lambda x: (
                    x['preferred_name'] or x['internal_username'],
                    x['internal_username']
                )
            )
            
            # Build display names and add to combo box
            for user_data in sorted_users:
                user_id = user_data['user_id']
                internal_username = user_data['internal_username']
                channel_type = user_data['channel_type']
                enabled_features = user_data['enabled_features']
                
                # Build display name with channel type and features
                feature_summary = []
                if 'automated_messages' in enabled_features:
                    categories = [f for f in enabled_features if f not in ['automated_messages', 'checkins', 'task_management']]
                    if categories:
                        # Apply title_case to category names for display
                        # Replace underscores with spaces before applying title_case
                        formatted_categories = [_shared__title_case(cat.replace('_', ' ')) for cat in categories]
                        feature_summary.append(f"Messages: {', '.join(formatted_categories)}")
                if 'checkins' in enabled_features:
                    feature_summary.append("Check-ins")
                if 'task_management' in enabled_features:
                    feature_summary.append("Tasks")
                
                feature_text = f" [{', '.join(feature_summary)}]" if feature_summary else ""
                display_name = f"{internal_username} ({channel_type}){feature_text} - {user_id}"
                self.ui.comboBox_users.addItem(display_name)
                
        except Exception as e:
            logger.error(f"Error refreshing user list: {e}")
            # Minimal fallback to directory scanning
            try:
                user_ids = get_all_user_ids()
                self.ui.comboBox_users.clear()
                self.ui.comboBox_users.addItem("Select a user...")
                
                for user_id in user_ids:
                    # Get user account
                    user_data_result = get_user_data(user_id, 'account')
                    user_account = user_data_result.get('account')
                    internal_username = user_account.get('internal_username', 'Unknown') if user_account else 'Unknown'
                    # Get user context
                    context_result = get_user_data(user_id, 'context')
                    user_context = context_result.get('context')
                    preferred_name = user_context.get('preferred_name', '') if user_context else ''
                    if preferred_name:
                        display_name = f"{preferred_name} ({internal_username}) - {user_id}"
                    else:
                        display_name = f"{internal_username} - {user_id}"
                    self.ui.comboBox_users.addItem(display_name)
            except Exception as fallback_error:
                logger.error(f"Fallback user list refresh also failed: {fallback_error}")
                QMessageBox.warning(self, "Error", f"Failed to refresh user list: {e}")
        
        # Reselect the previously selected user if it still exists
        if current_user_id:
            for i in range(self.ui.comboBox_users.count()):
                item_text = self.ui.comboBox_users.itemText(i)
                if f" - {current_user_id}" in item_text:
                    self.ui.comboBox_users.setCurrentIndex(i)
                    # Trigger the selection handler to reload user data
                    self.on_user_selected(item_text)
                    break
    
    @handle_errors("handling user selection", default_return=None)
    def on_user_selected(self, user_display):
        """
        Handle user selection with validation.
        
        Returns:
            None: Always returns None
        """
        # Validate user_display
        if not user_display or not isinstance(user_display, str):
            logger.error(f"Invalid user_display: {user_display}")
            return None
            
        if not user_display.strip():
            logger.error("Empty user_display provided")
            return None
        """Handle user selection from combo box"""
        if not user_display or user_display == "Select a user...":
            self.current_user = None
            self.disable_content_management()
            return
        
        try:
            # Extract user_id from display name (format: "Name - user_id")
            if " - " in user_display:
                user_id = user_display.split(" - ")[-1]
            self.current_user = user_id
            # Get user account
            user_data_result = get_user_data(user_id, 'account')
            user_account = user_data_result.get('account')
            if user_account:
                # Load user categories
                self.load_user_categories(user_id)
                self.enable_content_management()
                logger.info(f"Admin Panel: User selected for management: {user_id} ({user_account.get('internal_username', 'Unknown')})")
            else:
                QMessageBox.warning(self, "User Error", f"Could not load user account for {user_id}")
                self.disable_content_management()
                return
            if " - " not in user_display:
                logger.warning(f"Admin Panel: Could not parse user_id from selected_display: '{user_display}'")
                self.disable_content_management()
                return
                
        except Exception as e:
            logger.error(f"Error handling user selection: {e}")
            QMessageBox.warning(self, "Error", f"Failed to load user: {e}")
            self.disable_content_management()
    
    def load_user_categories(self, user_id):
        """Load categories for the selected user"""
        try:
            # Load user preferences
            prefs_result = get_user_data(user_id, 'preferences')
            prefs = prefs_result.get('preferences') or {}
            if prefs and 'categories' in prefs:
                categories = prefs['categories']
                # Handle both list and dictionary formats
                if isinstance(categories, dict):
                    self.current_user_categories = list(categories.keys())
                elif isinstance(categories, list):
                    self.current_user_categories = categories
                else:
                    self.current_user_categories = []
            else:
                self.current_user_categories = []
            
            # Update category combo box
            self.ui.comboBox_user_categories.clear()
            self.ui.comboBox_user_categories.addItem("Select a category...")
            
            for category in self.current_user_categories:
                # Store the original category name as data, display the formatted name
                # Replace underscores with spaces before applying title_case
                formatted_category = _shared__title_case(category.replace('_', ' '))
                self.ui.comboBox_user_categories.addItem(formatted_category, category)
                
        except Exception as e:
            logger.error(f"Error loading user categories: {e}")
            self.current_user_categories = []
    
    @handle_errors("handling category selection", default_return=None)
    def on_category_selected(self, category):
        """Handle category selection"""
        # Get the actual category value from the combo box data
        current_index = self.ui.comboBox_user_categories.currentIndex()
        if current_index > 0:  # Skip the "Select a category..." item
            actual_category = self.ui.comboBox_user_categories.itemData(current_index)
        else:
            actual_category = None
        
        # Enable/disable category action buttons based on selection
        has_category = bool(actual_category and actual_category != "Select a category...")
        
        self.ui.pushButton_edit_messages.setEnabled(has_category)
        self.ui.pushButton_edit_schedules.setEnabled(has_category)
        self.ui.pushButton_send_test_message.setEnabled(has_category)
    
    @handle_errors("enabling content management", default_return=None)
    def enable_content_management(self):
        """Enable content management buttons"""
        self.ui.pushButton_communication_settings.setEnabled(True)
        self.ui.pushButton_personalization.setEnabled(True)
        self.ui.pushButton_category_management.setEnabled(True)
        self.ui.pushButton_checkin_settings.setEnabled(True)
        self.ui.pushButton_task_management.setEnabled(True)
        self.ui.pushButton_task_crud.setEnabled(True)
        self.ui.pushButton_user_analytics.setEnabled(True)
        self.ui.pushButton_run_user_scheduler.setEnabled(True)
        
        # Enable category actions group
        self.ui.groupBox_category_actions.setEnabled(True)
        
        # Enable user actions group
        self.ui.groupBox_user_actions.setEnabled(True)
    
    @handle_errors("disabling content management", default_return=None)
    def disable_content_management(self):
        """Disable content management buttons"""
        self.ui.pushButton_communication_settings.setEnabled(False)
        self.ui.pushButton_personalization.setEnabled(False)
        self.ui.pushButton_category_management.setEnabled(False)
        self.ui.pushButton_checkin_settings.setEnabled(False)
        self.ui.pushButton_task_management.setEnabled(False)
        self.ui.pushButton_task_crud.setEnabled(False)
        self.ui.pushButton_user_analytics.setEnabled(False)
        self.ui.pushButton_run_user_scheduler.setEnabled(False)
        
        # Disable category actions group
        self.ui.groupBox_category_actions.setEnabled(False)
        
        # Disable user actions group
        self.ui.groupBox_user_actions.setEnabled(False)
        
        # Clear category combo box
        self.ui.comboBox_user_categories.clear()
        self.ui.comboBox_user_categories.addItem("Select a category...")
    
    # Placeholder methods for user actions - these will need to be implemented
    # based on your existing functionality from the Tkinter version
    
    @handle_errors("creating new user", default_return=None)
    def create_new_user(self):
        """
        Create new user with validation.
        
        Returns:
            None: Always returns None
        """
        """Open dialog to create a new user"""
        logger.info("Admin Panel: Opening create new user dialog")
        try:
            from ui.dialogs.account_creator_dialog import AccountCreatorDialog
            from communication.core.channel_orchestrator import CommunicationManager
            temp_comm_manager = CommunicationManager()
            dialog = AccountCreatorDialog(self, temp_comm_manager)
            dialog.user_changed.connect(self.refresh_user_list)
            dialog.exec()
            try:
                temp_comm_manager.stop_all()
            except Exception as cleanup_error:
                logger.warning(f"Error cleaning up temporary communication manager: {cleanup_error}")
        except Exception as e:
            logger.error(f"Error opening create account dialog: {e}")
            QMessageBox.critical(self, "Error", f"Failed to open create account dialog: {str(e)}")

    @handle_errors("managing communication settings", default_return=None)
    def manage_communication_settings(self):
        """
        Manage communication settings with validation.
        
        Returns:
            None: Always returns None
        """
        # Validate current_user
        if not self.current_user:
            logger.error("No current user selected")
            return None
        if not self.current_user:
            QMessageBox.warning(self, "No User Selected", "Please select a user first.")
            return
        logger.info(f"Admin Panel: Opening communication settings for user {self.current_user}")
        try:
            from ui.dialogs.channel_management_dialog import ChannelManagementDialog
            dialog = ChannelManagementDialog(self, user_id=self.current_user)
            dialog.user_changed.connect(self.refresh_user_list)
            dialog.setWindowTitle(f"Channel Settings - {self.current_user}")
            dialog.exec()
        except Exception as e:
            logger.error(f"Error opening communication settings dialog: {e}")
            QMessageBox.critical(self, "Error", f"Failed to open communication settings: {str(e)}")

    @handle_errors("managing categories", default_return=None)
    def manage_categories(self):
        """
        Manage categories with validation.
        
        Returns:
            None: Always returns None
        """
        # Validate current_user
        if not self.current_user:
            logger.error("No current user selected")
            return None
        if not self.current_user:
            QMessageBox.warning(self, "No User Selected", "Please select a user first.")
            return
        logger.info(f"Admin Panel: Opening category management for user {self.current_user}")
        try:
            from ui.dialogs.category_management_dialog import CategoryManagementDialog
            dialog = CategoryManagementDialog(self, self.current_user)
            dialog.user_changed.connect(self.refresh_user_list)
            dialog.setWindowTitle(f"Category Settings - {self.current_user}")
            dialog.exec()
            self.load_user_categories(self.current_user)
        except Exception as e:
            logger.error(f"Error opening category management dialog: {e}")
            QMessageBox.critical(self, "Error", f"Failed to open category management: {str(e)}")

    @handle_errors("managing checkins", default_return=None)
    def manage_checkins(self):
        """
        Manage checkins with validation.
        
        Returns:
            None: Always returns None
        """
        # Validate current_user
        if not self.current_user:
            logger.error("No current user selected")
            return None
        if not self.current_user:
            QMessageBox.warning(self, "No User Selected", "Please select a user first.")
            return
        logger.info(f"Admin Panel: Opening check-in management for user {self.current_user}")
        try:
            from ui.dialogs.checkin_management_dialog import CheckinManagementDialog
            dialog = CheckinManagementDialog(self, self.current_user)
            dialog.user_changed.connect(self.refresh_user_list)
            dialog.setWindowTitle(f"Check-in Management - {self.current_user}")
            dialog.exec()
        except Exception as e:
            logger.error(f"Error opening check-in management: {e}")
            QMessageBox.critical(self, "Error", f"Failed to open check-in management: {str(e)}")

    @handle_errors("managing tasks", default_return=None)
    def manage_tasks(self):
        """
        Manage tasks with validation.
        
        Returns:
            None: Always returns None
        """
        # Validate current_user
        if not self.current_user:
            logger.error("No current user selected")
            return None
        if not self.current_user:
            QMessageBox.warning(self, "No User Selected", "Please select a user first.")
            return
        logger.info(f"Admin Panel: Opening task management for user {self.current_user}")
        try:
            from ui.dialogs.task_management_dialog import TaskManagementDialog
            dialog = TaskManagementDialog(self, self.current_user)
            dialog.user_changed.connect(self.refresh_user_list)
            dialog.setWindowTitle(f"Task Management - {self.current_user}")
            dialog.exec()
        except Exception as e:
            logger.error(f"Error opening task management dialog: {e}")
            QMessageBox.critical(self, "Error", f"Failed to open task management: {str(e)}")

    @handle_errors("managing task CRUD", default_return=None)
    def manage_task_crud(self):
        """
        Manage task CRUD with validation.
        
        Returns:
            None: Always returns None
        """
        # Validate current_user
        if not self.current_user:
            logger.error("No current user selected")
            return None
        if not self.current_user:
            QMessageBox.warning(self, "No User Selected", "Please select a user first.")
            return
        logger.info(f"Admin Panel: Opening task CRUD for user {self.current_user}")
        try:
            from ui.dialogs.task_crud_dialog import TaskCrudDialog
            dialog = TaskCrudDialog(self, self.current_user)
            dialog.setWindowTitle(f"Task CRUD - {self.current_user}")
            dialog.exec()
        except Exception as e:
            logger.error(f"Error opening task CRUD dialog: {e}")
            QMessageBox.critical(self, "Error", f"Failed to open task CRUD: {str(e)}")

    @handle_errors("managing personalization", default_return=None)
    def manage_personalization(self):
        """
        Manage personalization with validation.
        
        Returns:
            None: Always returns None
        """
        # Validate current_user
        if not self.current_user:
            logger.error("No current user selected")
            return None
        if not self.current_user:
            QMessageBox.warning(self, "No User Selected", "Please select a user first.")
            return
        logger.info(f"Admin Panel: Opening personalization management for user {self.current_user}")
        try:
            from ui.dialogs.user_profile_dialog import UserProfileDialog
            from core.user_data_handlers import get_user_data, update_user_context
            # Load user context and account data
            user_data = get_user_data(self.current_user, ['context', 'account'])
            context_data = user_data.get('context', {})
            account_data = user_data.get('account', {})
            # Merge timezone from account.json into context_data for the dialog
            if 'timezone' in account_data:
                context_data['timezone'] = account_data['timezone']
            # Custom save handler to split timezone
            # ERROR_HANDLING_EXCLUDE: Nested callback function (already wrapped in try-except by parent)
            def on_save(data):
                tz = data.pop('timezone', None)
                # Use centralized save_user_data for both context and account updates
                from core.user_data_handlers import save_user_data
                updates = {'context': data}
                if tz is not None:
                    updates['account'] = {'timezone': tz}
                save_user_data(self.current_user, updates)
            dialog = UserProfileDialog(self, self.current_user, on_save, existing_data=context_data)
            dialog.user_changed.connect(self.refresh_user_list)
            dialog.setWindowTitle(f"Personalization Settings - {self.current_user}")
            dialog.exec()
        except Exception as e:
            logger.error(f"Error opening personalization dialog: {e}")
            QMessageBox.critical(self, "Error", f"Failed to open personalization settings: {str(e)}")
    
    @handle_errors("managing user analytics", default_return=None)
    def manage_user_analytics(self):
        """
        Manage user analytics with validation.
        
        Returns:
            None: Always returns None
        """
        # Validate current_user
        if not self.current_user:
            logger.error("No current user selected")
            return None
        """Open user analytics interface for selected user"""
        if not self.current_user:
            QMessageBox.warning(self, "No User Selected", "Please select a user first.")
            return
        logger.info(f"Admin Panel: Opening user analytics for user {self.current_user}")
        try:
            from ui.dialogs.user_analytics_dialog import open_user_analytics_dialog
            open_user_analytics_dialog(self, self.current_user)
        except Exception as e:
            logger.error(f"Error opening user analytics: {e}")
            QMessageBox.critical(self, "Error", f"Failed to open user analytics: {str(e)}")
    
    @handle_errors("editing user messages", default_return=None)
    def edit_user_messages(self):
        """
        Edit user messages with validation.
        
        Returns:
            None: Always returns None
        """
        # Validate current_user
        if not self.current_user:
            logger.error("No current user selected")
            return None
        """Open message editing interface for selected user"""
        if not self.current_user:
            QMessageBox.warning(self, "No User Selected", "Please select a user first.")
            return
        
        # Check if a category is selected
        current_index = self.ui.comboBox_user_categories.currentIndex()
        if current_index <= 0:  # No category selected or "Select a category..." selected
            QMessageBox.warning(self, "No Category Selected", "Please select a category from the dropdown first.")
            return
        
        selected_category = self.ui.comboBox_user_categories.itemData(current_index)
        logger.info(f"Admin Panel: Opening message editor for user {self.current_user}, category {selected_category}")
        
        # Temporarily set the user context for editing
        original_user = UserContext().get_user_id()
        UserContext().set_user_id(self.current_user)
        
        # Load the user's full data to get internal_username and other details
        user_data_result = get_user_data(self.current_user, 'account')
        user_account = user_data_result.get('account')
        # Get user context
        context_result = get_user_data(self.current_user, 'context')
        user_context = context_result.get('context')
        if user_account:
            UserContext().set_internal_username(user_account.get('internal_username', ''))
            if user_context:
                UserContext().set_preferred_name(user_context.get('preferred_name', ''))
            # Load the full user data into UserContext
            UserContext().load_user_data(self.current_user)
        
        # Open the message editor directly with the selected category
        self.open_message_editor(None, selected_category)

    @handle_errors("opening message editor", default_return=None)
    def open_message_editor(self, parent_dialog, category):
        """
        Open message editor with validation.
        
        Returns:
            None: Always returns None
        """
        # Validate category
        if not category or not isinstance(category, str):
            logger.error(f"Invalid category: {category}")
            return None
            
        if not category.strip():
            logger.error("Empty category provided")
            return None
        """Open the message editing window for a specific category"""
        logger.info(f"Admin Panel: Opening message editor for user {self.current_user}, category {category}")
        
        # Close parent dialog if it exists
        if parent_dialog:
            parent_dialog.accept()
        
        try:
            from ui.dialogs.message_editor_dialog import open_message_editor_dialog
            open_message_editor_dialog(self, self.current_user, category)
            
        except Exception as e:
            logger.error(f"Error opening message editor: {e}")
            QMessageBox.critical(self, "Error", f"Failed to open message editor: {str(e)}")
    
    @handle_errors("editing user schedules", default_return=None)
    def edit_user_schedules(self):
        """
        Edit user schedules with validation.
        
        Returns:
            None: Always returns None
        """
        # Validate current_user
        if not self.current_user:
            logger.error("No current user selected")
            return None
        """Open schedule editing interface for selected user"""
        if not self.current_user:
            QMessageBox.warning(self, "No User Selected", "Please select a user first.")
            return
        
        # Check if a category is selected
        current_index = self.ui.comboBox_user_categories.currentIndex()
        if current_index <= 0:  # No category selected or "Select a category..." selected
            QMessageBox.warning(self, "No Category Selected", "Please select a category from the dropdown first.")
            return
        
        selected_category = self.ui.comboBox_user_categories.itemData(current_index)
        logger.info(f"Admin Panel: Opening schedule editor for user {self.current_user}, category {selected_category}")
        
        # Temporarily set the user context for editing
        original_user = UserContext().get_user_id()
        UserContext().set_user_id(self.current_user)
        
        # Load the user's full data to get internal_username and other details
        user_data_result = get_user_data(self.current_user, 'account')
        user_account = user_data_result.get('account')
        # Get user context
        context_result = get_user_data(self.current_user, 'context')
        user_context = context_result.get('context')
        if user_account:
            UserContext().set_internal_username(user_account.get('internal_username', ''))
            if user_context:
                UserContext().set_preferred_name(user_context.get('preferred_name', ''))
            # Load the full user data into UserContext
            UserContext().load_user_data(self.current_user)
        
        # Open the schedule editor directly with the selected category
        self.open_schedule_editor(None, selected_category)

    @handle_errors("opening schedule editor", default_return=None)
    def open_schedule_editor(self, parent_dialog, category):
        """
        Open schedule editor with validation.
        
        Returns:
            None: Always returns None
        """
        # Validate category
        if not category or not isinstance(category, str):
            logger.error(f"Invalid category: {category}")
            return None
            
        if not category.strip():
            logger.error("Empty category provided")
            return None
        """Open the schedule editing window for a specific category"""
        logger.info(f"Admin Panel: Opening schedule editor for user {self.current_user}, category {category}")
        
        # Close parent dialog if it exists
        if parent_dialog:
            parent_dialog.accept()
        
        try:
            from ui.dialogs.schedule_editor_dialog import open_schedule_editor
            
            # ERROR_HANDLING_EXCLUDE: Nested callback function (already wrapped in try-except by parent)
            def on_schedule_save():
                """Callback when schedule is saved."""
                logger.info(f"Schedule saved for user {self.current_user}, category {category}")
            
            success = open_schedule_editor(self, self.current_user, category, on_schedule_save)
            
            if success:
                logger.info(f"Schedule editor completed successfully for user {self.current_user}, category {category}")
            else:
                logger.info(f"Schedule editor cancelled for user {self.current_user}, category {category}")
                
        except Exception as e:
            logger.error(f"Error opening schedule editor: {e}")
            QMessageBox.critical(self, "Error", f"Failed to open schedule editor: {str(e)}")
    
    @handle_errors("validating user selection", default_return=False)
    def _send_test_message__validate_user_selection(self):
        """Validate that a user is selected."""
        if not self.current_user:
            QMessageBox.warning(self, "No User Selected", "Please select a user first.")
            return False
        return True
    
    @handle_errors("validating service status", default_return=False)
    def _send_test_message__validate_service_running(self):
        """Validate that the service is running."""
        is_running, pid = self.service_manager.is_service_running()
        if not is_running:
            QMessageBox.warning(self, "Service Not Running", 
                               "MHM Service is not running. Test messages require the service to be active.\n\n"
                               "To send a test message:\n"
                               "1. Click 'Start Service' above\n"
                               "2. Wait for service to initialize\n"
                               "3. Try sending the test message again\n\n"
                               "The admin panel does not create its own communication channels.")
            return False
        return True
    
    @handle_errors("getting selected category", default_return=None)
    def _send_test_message__get_selected_category(self):
        """Get and validate the selected category from the dropdown."""
        current_index = self.ui.comboBox_user_categories.currentIndex()
        if current_index <= 0:  # No category selected or "Select a category..." is selected
            QMessageBox.warning(self, "No Category Selected", "Please select a category from the dropdown above.")
            return None
        
        category = self.ui.comboBox_user_categories.itemData(current_index)
        if not category:
            QMessageBox.warning(self, "Invalid Category", "Please select a valid category from the dropdown.")
            return None
        
        return category

    @handle_errors("sending test message", default_return=None)
    def send_test_message(self):
        """
        Send test message with validation.
        
        Returns:
            None: Always returns None
        """
        """Send a test message to the selected user"""
        # Validate user selection
        if not self._send_test_message__validate_user_selection():
            return
        
        # Validate service is running
        if not self._send_test_message__validate_service_running():
            return
        
        # Get and validate selected category
        category = self._send_test_message__get_selected_category()
        if not category:
            return
        
        logger.info(f"Admin Panel: Preparing test message for user {self.current_user}, category {category}")
        
        # Send the test message directly (no confirmation needed)
        self.send_actual_test_message(category)

    @handle_errors("sending test message", default_return=None)
    def send_actual_test_message(self, category):
        """
        Send actual test message with validation.
        
        Returns:
            None: Always returns None
        """
        # Validate category
        if not category or not isinstance(category, str):
            logger.error(f"Invalid category: {category}")
            return None
            
        if not category.strip():
            logger.error("Empty category provided")
            return None
        """Send a test message via the running service"""
        # Since service is running, we'll create a minimal communication to the service
        # For now, we'll use a simple approach: create a test message file that the service can pick up
        # This is safer than trying to inject into the running service's communication channels
        
        # Store original user context and set to selected user
        original_user = UserContext().get_user_id()
        UserContext().set_user_id(self.current_user)
        
        logger.info(f"Admin Panel: Creating test message request for user {self.current_user}, category {category}")
        
        # Create a test message request using the same pattern as shutdown requests
        from datetime import datetime
        import json
        from pathlib import Path
        
        # Use the same directory structure as the shutdown flag
        base_dir = Path(__file__).parent.parent  # Go up to MHM root
        request_file = base_dir / f'test_message_request_{self.current_user}_{category}.flag'
        
        test_request = {
            "user_id": self.current_user,
            "category": category,
            "timestamp": datetime.now().isoformat(),
            "source": "admin_panel"
        }
        
        try:
            with open(request_file, 'w') as f:
                json.dump(test_request, f, indent=2)
            logger.info(f"Admin Panel: Test message request file created: {request_file}")
        except Exception as e:
            logger.error(f"Failed to create test message request file: {e}")
            QMessageBox.critical(self, "Error", f"Failed to create test message request file: {str(e)}")
            return
        
        # Wait briefly for service to process and write response file with actual message
        actual_message = "Message will be selected from your collection"
        channel_name = "unknown"
        response_file = base_dir / f'test_message_response_{self.current_user}_{category}.flag'
        
        # Wait up to 3 seconds for the service to process and write the response
        import time
        for _ in range(30):  # Check 30 times over 3 seconds
            if response_file.exists():
                try:
                    with open(response_file, 'r') as f:
                        response_data = json.load(f)
                    actual_message = response_data.get('message', actual_message)
                    # Clean up response file
                    try:
                        os.remove(response_file)
                    except Exception:
                        pass
                    break
                except Exception as e:
                    logger.debug(f"Could not read response file: {e}")
            time.sleep(0.1)  # Wait 100ms between checks
        
        # Get channel name for dialog
        try:
            from core.user_data_handlers import get_user_data
            prefs_result = get_user_data(self.current_user, 'preferences', normalize_on_read=True)
            preferences = prefs_result.get('preferences', {})
            channel_name = preferences.get('channel', {}).get('type', 'unknown')
        except Exception as e:
            logger.debug(f"Could not get channel name: {e}")
        
        # Truncate message if too long for dialog
        if len(actual_message) > 100:
            actual_message = actual_message[:97] + "..."
        
        QMessageBox.information(self, "Test Message Sent", 
                               f"Test {category} message sent to {self.current_user} via {channel_name}.\n\n"
                               f"Message: {actual_message}")
        
        # Optional: Clean up old request files after a short delay
        import threading
        def cleanup_old_requests():
            import time
            time.sleep(300)  # Wait 5 minutes
            try:
                if os.path.exists(request_file):
                    os.remove(request_file)
                    logger.debug(f"Cleaned up old request file: {request_file}")
            except Exception as cleanup_error:
                logger.warning(f"Could not clean up request file: {cleanup_error}")
        
        cleanup_thread = threading.Thread(target=cleanup_old_requests, daemon=True)
        cleanup_thread.start()
        
        # Restore original user context
        if original_user:
            UserContext().set_user_id(original_user)
        else:
            UserContext().set_user_id(None)
    
    @handle_errors("sending check-in prompt", default_return=None)
    def send_checkin_prompt(self):
        """
        Send a check-in prompt to the selected user for testing purposes.
        
        Returns:
            None: Always returns None
        """
        # Validate user selection
        if not self.current_user:
            QMessageBox.warning(self, "No User Selected", "Please select a user first.")
            return
        
        # Validate service is running
        is_running, pid = self.service_manager.is_service_running()
        if not is_running:
            QMessageBox.warning(self, "Service Not Running", 
                               "MHM Service is not running. Check-in prompts require the service to be active.\n\n"
                               "To send a check-in prompt:\n"
                               "1. Click 'Start Service' above\n"
                               "2. Wait for service to initialize\n"
                               "3. Try sending the check-in prompt again")
            return
        
        logger.info(f"Admin Panel: Sending check-in prompt to user {self.current_user}")
        
        try:
            # Get user preferences to determine messaging service and recipient
            from core.user_data_handlers import get_user_data
            prefs_result = get_user_data(self.current_user, 'preferences', normalize_on_read=True)
            preferences = prefs_result.get('preferences')
            
            if not preferences:
                QMessageBox.warning(self, "User Configuration Error", 
                                   f"User preferences not found for {self.current_user}.")
                return
            
            messaging_service = preferences.get('channel', {}).get('type')
            if not messaging_service:
                QMessageBox.warning(self, "User Configuration Error", 
                                   f"No messaging service configured for {self.current_user}.")
                return
            
            # Create check-in prompt request file (same pattern as test messages)
            # The service will pick this up and send the check-in prompt
            from datetime import datetime
            import json
            import time
            base_dir = Path(__file__).parent.parent
            request_file = base_dir / f'checkin_prompt_request_{self.current_user}.flag'
            
            checkin_request = {
                "user_id": self.current_user,
                "timestamp": datetime.now().isoformat(),
                "source": "admin_panel"
            }
            
            with open(request_file, 'w') as f:
                json.dump(checkin_request, f, indent=2)
            
            # Wait briefly for service to process and write response file with actual first question
            first_question = "Check-in questions"
            response_file = base_dir / f'checkin_prompt_response_{self.current_user}.flag'
            
            # Wait up to 3 seconds for the service to process and write the response
            for _ in range(30):  # Check 30 times over 3 seconds
                if response_file.exists():
                    try:
                        with open(response_file, 'r') as f:
                            response_data = json.load(f)
                        first_question = response_data.get('first_question', first_question)
                        # Clean up response file
                        try:
                            os.remove(response_file)
                        except Exception:
                            pass
                        break
                    except Exception as e:
                        logger.debug(f"Could not read check-in response file: {e}")
                time.sleep(0.1)  # Wait 100ms between checks
            
            # Truncate if too long
            if len(first_question) > 100:
                first_question = first_question[:97] + "..."
            
            QMessageBox.information(self, "Check-in Prompt Sent", 
                                   f"Check-in prompt sent to {self.current_user} via {messaging_service}.\n\n"
                                   f"First question: {first_question}")
            logger.info(f"Admin Panel: Check-in prompt request file created: {request_file}")
            
        except Exception as e:
            logger.error(f"Error sending check-in prompt: {e}")
            QMessageBox.critical(self, "Error", f"Failed to send check-in prompt: {str(e)}")
    
    @handle_errors("sending task reminder", default_return=None)
    def send_task_reminder(self):
        """
        Send a task reminder to the selected user for testing purposes.
        
        Returns:
            None: Always returns None
        """
        # Validate user selection
        if not self.current_user:
            QMessageBox.warning(self, "No User Selected", "Please select a user first.")
            return
        
        # Validate service is running
        is_running, pid = self.service_manager.is_service_running()
        if not is_running:
            QMessageBox.warning(self, "Service Not Running", 
                               "MHM Service is not running. Task reminders require the service to be active.\n\n"
                               "To send a task reminder:\n"
                               "1. Click 'Start Service' above\n"
                               "2. Wait for service to initialize\n"
                               "3. Try sending the task reminder again")
            return
        
        logger.info(f"Admin Panel: Preparing task reminder for user {self.current_user}")
        
        try:
            # Get user preferences first (needed for channel check)
            from core.user_data_handlers import get_user_data
            prefs_result = get_user_data(self.current_user, 'preferences', normalize_on_read=True)
            preferences = prefs_result.get('preferences')
            
            # Check if tasks are enabled for this user
            from tasks.task_management import are_tasks_enabled, load_active_tasks
            if not are_tasks_enabled(self.current_user):
                QMessageBox.warning(self, "Tasks Not Enabled", 
                                   f"Tasks are not enabled for {self.current_user}.")
                return
            
            # Get active tasks
            active_tasks = load_active_tasks(self.current_user)
            if not active_tasks:
                QMessageBox.warning(self, "No Active Tasks", 
                                   f"{self.current_user} has no active tasks to remind about.")
                return
            
            # Filter out completed tasks
            incomplete_tasks = [task for task in active_tasks if not task.get('completed', False)]
            if not incomplete_tasks:
                QMessageBox.warning(self, "No Incomplete Tasks", 
                                   f"All tasks for {self.current_user} are already completed.")
                return
            
            # Use scheduler's weighted selection for proper priority-based semi-random selection
            # Note: We create a temporary scheduler manager just for task selection
            # The actual sending will be done by the service when it processes the request file
            from core.scheduler import SchedulerManager
            from communication.core.channel_orchestrator import CommunicationManager
            
            # Create temporary instances for task selection only
            temp_comm_manager = CommunicationManager()
            scheduler_manager = SchedulerManager(temp_comm_manager)
            
            # Select task using priority-based weighting (considers priority, due dates, etc.)
            selected_task = scheduler_manager.select_task_for_reminder(incomplete_tasks)
            
            if not selected_task:
                QMessageBox.warning(self, "Task Selection Error", 
                                   "Could not select a task for reminder.")
                return
            
            task_id = selected_task.get('task_id')
            task_title = selected_task.get('title', 'Untitled Task')
            
            if not task_id:
                QMessageBox.warning(self, "Invalid Task", 
                                   "Selected task has no task_id.")
                return
            
            # Get channel name for dialog
            messaging_service = preferences.get('channel', {}).get('type') if preferences else None
            channel_name = messaging_service if messaging_service else "unknown"
            
            # Create task reminder request file (same pattern as test messages)
            # The service will pick this up and send the task reminder
            from datetime import datetime
            import json
            base_dir = Path(__file__).parent.parent
            request_file = base_dir / f'task_reminder_request_{self.current_user}_{task_id}.flag'
            
            task_reminder_request = {
                "user_id": self.current_user,
                "task_id": task_id,
                "timestamp": datetime.now().isoformat(),
                "source": "admin_panel"
            }
            
            with open(request_file, 'w') as f:
                json.dump(task_reminder_request, f, indent=2)
            
            QMessageBox.information(self, "Task Reminder Sent", 
                                   f"Task reminder sent to {self.current_user} via {channel_name}.\n\n"
                                   f"Task: {task_title}")
            logger.info(f"Admin Panel: Task reminder request file created: {request_file}")
            
        except Exception as e:
            logger.error(f"Error sending task reminder: {e}")
            QMessageBox.critical(self, "Error", f"Failed to send task reminder: {str(e)}")
    
    # Debug and admin methods
    @handle_errors("toggling logging verbosity", default_return=None)
    def toggle_logging_verbosity(self):
        """Toggle logging verbosity and update menu."""
        from core.logger import toggle_verbose_logging, get_verbose_mode
        is_verbose = toggle_verbose_logging()
        
        # Update the menu text
        verbose_status = "ON" if is_verbose else "OFF"
        self.ui.actionToggle_Verbose_Logging.setText(f"Toggle Verbose Logging (Currently: {verbose_status})")
        
        # Show status message
        status = "enabled" if is_verbose else "disabled"
        QMessageBox.information(self, "Logging", f"Verbose logging has been {status}")
    
    @handle_errors("viewing log file", default_return=None)
    def view_log_file(self):
        """
        View log file with validation.
        
        Returns:
            None: Always returns None
        """
        """Open the log file in the default text editor."""
        import webbrowser
        from core.config import LOG_MAIN_FILE
        webbrowser.open(LOG_MAIN_FILE)
    
    @handle_errors("opening process watcher", default_return=None)
    def open_process_watcher(self):
        """
        Open process watcher with validation.
        
        Returns:
            None: Always returns None
        """
        """Open the process watcher dialog."""
        try:
            from ui.dialogs.process_watcher_dialog import ProcessWatcherDialog
            dialog = ProcessWatcherDialog(self)
            dialog.show()
            logger.debug("Process watcher dialog opened")
        except Exception as e:
            logger.error(f"Error opening process watcher: {e}")
            QMessageBox.critical(self, "Error", f"Failed to open process watcher: {e}")
    
    @handle_errors("viewing cache status", default_return=None)
    def view_cache_status(self):
        """
        View cache status with validation.
        
        Returns:
            None: Always returns None
        """
        """Show cache cleanup status and information."""
        from core.auto_cleanup import get_cleanup_status, find_pycache_dirs, find_pyc_files, calculate_cache_size
        import os
        
        # Get cleanup status
        status = get_cleanup_status()
        
        # Get current cache size
        pycache_dirs = find_pycache_dirs('.')
        pyc_files = find_pyc_files('.')
        current_size = calculate_cache_size(pycache_dirs, pyc_files)
        
        # Create status window
        status_window = QDialog(self)
        status_window.setWindowTitle("Cache Cleanup Status")
        status_window.setModal(True)
        status_window.resize(450, 350)
        
        layout = QVBoxLayout(status_window)
        
        # Status information
        title_label = QLabel("Cache Cleanup Status")
        title_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        layout.addWidget(title_label)
        
        # Status details
        status_text = QTextEdit()
        status_text.setReadOnly(True)
        status_text.setMaximumHeight(200)
        
        status_content = f"""Last cleanup: {status['last_cleanup']}
Days since cleanup: {status['days_since']}
Next cleanup: {status['next_cleanup']}

Current cache files found:
• {len(pycache_dirs)} __pycache__ directories
• {len(pyc_files)} standalone .pyc files
• Total size: {current_size / 1024:.1f} KB ({current_size / (1024*1024):.2f} MB)"""
        
        status_text.setPlainText(status_content)
        layout.addWidget(status_text)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        force_clean_button = QPushButton("Force Clean")
        force_clean_button.clicked.connect(lambda: [self.force_clean_cache(), status_window.accept()])
        button_layout.addWidget(force_clean_button)
        
        close_button = QPushButton("Close")
        close_button.clicked.connect(status_window.accept)
        button_layout.addWidget(close_button)
        
        layout.addLayout(button_layout)
        
        status_window.exec()
    
    @handle_errors("forcing cache cleanup", default_return=None)
    def force_clean_cache(self):
        """
        Force cache cleanup with validation.
        
        Returns:
            None: Always returns None
        """
        """Force cache cleanup regardless of schedule."""
        from core.auto_cleanup import perform_cleanup, update_cleanup_timestamp
        
        # Ask for confirmation
        result = QMessageBox.question(self, "Force Cache Cleanup", 
                                     "This will force cleanup of all Python cache files regardless of when they were last cleaned.\n\nAre you sure you want to continue?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if result == QMessageBox.StandardButton.Yes:
            success = perform_cleanup()
            if success:
                update_cleanup_timestamp()
                QMessageBox.information(self, "Cache Cleanup", "Force cache cleanup completed successfully!")
                logger.info("Force cache cleanup completed successfully")
            else:
                QMessageBox.critical(self, "Error", "Cache cleanup failed")
    
    @handle_errors("validating configuration", default_return=None)
    def validate_configuration(self):
        """
        Validate configuration with validation.
        
        Returns:
            None: Always returns None
        """
        """Show detailed configuration validation report."""
        from core.config import validate_all_configuration
        from PySide6.QtWidgets import QTabWidget, QTextEdit, QScrollArea
        
        result = validate_all_configuration()
        
        # Create validation report window
        report_window = QDialog(self)
        report_window.setWindowTitle("Configuration Validation Report")
        report_window.setModal(True)
        report_window.resize(700, 600)
        
        layout = QVBoxLayout(report_window)
        
        # Title
        title_label = QLabel("Configuration Validation Report")
        title_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        layout.addWidget(title_label)
        
        # Summary
        summary_text = result['summary']
        if result['valid']:
            summary_color = "green"
            summary_icon = "✓"
        else:
            summary_color = "red"
            summary_icon = "✗"
        
        summary_label = QLabel(f"{summary_icon} {summary_text}")
        summary_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        summary_label.setStyleSheet(f"color: {summary_color};")
        layout.addWidget(summary_label)
        
        # Available channels
        if result['available_channels']:
            channels_label = QLabel(f"Available Channels: {', '.join(result['available_channels'])}")
            channels_label.setFont(QFont("Arial", 10))
            channels_label.setStyleSheet("color: blue;")
            layout.addWidget(channels_label)
        else:
            channels_label = QLabel("No communication channels available")
            channels_label.setFont(QFont("Arial", 10))
            channels_label.setStyleSheet("color: orange;")
            layout.addWidget(channels_label)
        
        # Create tab widget
        tab_widget = QTabWidget()
        layout.addWidget(tab_widget)
        
        # Errors tab
        if result['errors']:
            errors_widget = QWidget()
            errors_layout = QVBoxLayout(errors_widget)
            
            errors_text = QTextEdit()
            errors_text.setReadOnly(True)
            
            for i, error in enumerate(result['errors'], 1):
                errors_text.append(f"{i}. {error}\n")
            
            errors_layout.addWidget(errors_text)
            tab_widget.addTab(errors_widget, f"Errors ({len(result['errors'])})")
        
        # Warnings tab
        if result['warnings']:
            warnings_widget = QWidget()
            warnings_layout = QVBoxLayout(warnings_widget)
            
            warnings_text = QTextEdit()
            warnings_text.setReadOnly(True)
            
            for i, warning in enumerate(result['warnings'], 1):
                warnings_text.append(f"{i}. {warning}\n")
            
            warnings_layout.addWidget(warnings_text)
            tab_widget.addTab(warnings_widget, f"Warnings ({len(result['warnings'])})")
        
        # Current Configuration tab
        config_widget = QWidget()
        config_layout = QVBoxLayout(config_widget)
        
        config_text = QTextEdit()
        config_text.setReadOnly(True)
        
        # Add current configuration values
        from core.config import (
            BASE_DATA_DIR, LOG_MAIN_FILE, LOG_LEVEL, LM_STUDIO_BASE_URL, 
            AI_TIMEOUT_SECONDS, SCHEDULER_INTERVAL, EMAIL_SMTP_SERVER, EMAIL_IMAP_SERVER, 
            EMAIL_SMTP_USERNAME, DISCORD_BOT_TOKEN
        )
        
        config_values = [
            ("Base Data Directory", BASE_DATA_DIR),
            ("Log File", LOG_MAIN_FILE),
            ("Log Level", LOG_LEVEL),
            ("LM Studio URL", LM_STUDIO_BASE_URL),
            ("AI Timeout", f"{AI_TIMEOUT_SECONDS}s"),
            ("Scheduler Interval", f"{SCHEDULER_INTERVAL}s"),
            ("Email SMTP Server", EMAIL_SMTP_SERVER or "Not configured"),
            ("Email IMAP Server", EMAIL_IMAP_SERVER or "Not configured"),
            ("Email Username", EMAIL_SMTP_USERNAME or "Not configured"),
            ("Discord Bot Token", "Configured" if DISCORD_BOT_TOKEN else "Not configured"),
        ]
        
        for name, value in config_values:
            config_text.append(f"{name}: {value}\n")
        
        config_layout.addWidget(config_text)
        tab_widget.addTab(config_widget, "Current Configuration")
        
        # Buttons
        button_layout = QHBoxLayout()
        
        if not result['valid']:
            fix_button = QPushButton("Fix Configuration")
            fix_button.clicked.connect(lambda: self.show_configuration_help(report_window))
            button_layout.addWidget(fix_button)
        
        close_button = QPushButton("Close")
        close_button.clicked.connect(report_window.accept)
        button_layout.addWidget(close_button)
        
        layout.addLayout(button_layout)
        
        report_window.exec()

    @handle_errors("showing configuration help", default_return=None)
    def show_configuration_help(self, parent_window):
        """Show help for fixing configuration issues."""
        help_window = QDialog(parent_window)
        help_window.setWindowTitle("Configuration Help")
        help_window.setModal(True)
        help_window.resize(600, 500)
        
        layout = QVBoxLayout(help_window)
        
        help_text = QTextEdit()
        help_text.setReadOnly(True)
        layout.addWidget(help_text)
        
        help_content = """
CONFIGURATION HELP

To fix configuration issues, you need to set up environment variables. Create a .env file in the MHM root directory with the following variables:

REQUIRED SETTINGS:
=================

1. COMMUNICATION CHANNELS (at least one required):
   - For Email: EMAIL_SMTP_SERVER, EMAIL_IMAP_SERVER, EMAIL_SMTP_USERNAME, EMAIL_SMTP_PASSWORD
   - For Discord: DISCORD_BOT_TOKEN

2. AI CONFIGURATION:
   - LM_STUDIO_BASE_URL (default: http://localhost:1234/v1)
   - LM_STUDIO_API_KEY (default: lm-studio)
   - LM_STUDIO_MODEL (default: deepseek-llm-7b-chat)

OPTIONAL SETTINGS:
=================

- BASE_DATA_DIR (default: data)
- LOG_MAIN_FILE (default: app.log)
- LOG_LEVEL (default: INFO)
- AI_TIMEOUT_SECONDS (default: 30)
- SCHEDULER_INTERVAL (default: 60)
- AUTO_CREATE_USER_DIRS (default: true)

EXAMPLE .env FILE:
=================

EMAIL_SMTP_SERVER=smtp.gmail.com
EMAIL_IMAP_SERVER=imap.gmail.com
EMAIL_SMTP_USERNAME=your-email@gmail.com
EMAIL_SMTP_PASSWORD=your-app-password

# OR for Discord:
DISCORD_BOT_TOKEN=your-discord-bot-token

# AI Configuration:
LM_STUDIO_BASE_URL=http://localhost:1234/v1
LM_STUDIO_API_KEY=lm-studio
LM_STUDIO_MODEL=deepseek-llm-7b-chat

# Optional settings:
LOG_LEVEL=INFO
AI_TIMEOUT_SECONDS=30
SCHEDULER_INTERVAL=60

SETUP INSTRUCTIONS:
==================

1. Create a .env file in the MHM root directory
2. Add the required environment variables
3. Restart the MHM application
4. Run "Validate Configuration" again to check

For detailed setup instructions, see the ui/UI_GUIDE.md file.
"""
        
        help_text.setPlainText(help_content)
        
        close_button = QPushButton("Close")
        close_button.clicked.connect(help_window.accept)
        layout.addWidget(close_button)
        
        help_window.exec()
    
    def view_all_users_summary(self):
        """Show a summary of all users in the system."""
        try:
            user_ids = get_all_user_ids()
            
            # Create summary window
            summary_window = QDialog(self)
            summary_window.setWindowTitle("All Users Summary")
            summary_window.setModal(True)
            summary_window.resize(600, 400)
            
            layout = QVBoxLayout(summary_window)
            
            title_label = QLabel("All Users Summary")
            title_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
            layout.addWidget(title_label)
            
            # Create scrollable text area
            text_widget = QTextEdit()
            text_widget.setReadOnly(True)
            layout.addWidget(text_widget)
            
            if not user_ids:
                text_widget.setPlainText("No users found in the system.\n")
            else:
                summary_text = f"Total users: {len(user_ids)}\n\n"
                
                for user_id in user_ids:
                    # Get user account
                    user_data_result = get_user_data(user_id, 'account')
                    user_account = user_data_result.get('account')
                    # Get user context
                    context_result = get_user_data(user_id, 'context')
                    user_context = context_result.get('context')
                    if user_account:
                        username = user_account.get('internal_username', 'Unknown')
                        preferred_name = user_context.get('preferred_name', '') if user_context else ''
                        prefs_result = get_user_data(user_id, 'preferences')
                        prefs = prefs_result.get('preferences', {})
                        categories = prefs.get('categories', [])
                        messaging_service = prefs.get('channel', {}).get('type', 'Unknown')
                        
                        summary_text += f"User: {username}"
                        if preferred_name:
                            summary_text += f" ({preferred_name})"
                        summary_text += f"\n"
                        summary_text += f"  ID: {user_id}\n"
                        summary_text += f"  Service: {messaging_service}\n"
                        summary_text += f"  Categories: {', '.join(categories) if categories else 'None'}\n"
                        summary_text += "\n"
                
                text_widget.setPlainText(summary_text)
            
            close_button = QPushButton("Close")
            close_button.clicked.connect(summary_window.accept)
            layout.addWidget(close_button)
            
            summary_window.exec()
            
        except Exception as e:
            logger.error(f"Failed to show users summary: {e}")
            QMessageBox.critical(self, "Error", f"Failed to load users summary: {e}")
    
    def system_health_check(self):
        """Perform a basic system health check."""
        try:
            # Create health check window
            health_window = QDialog(self)
            health_window.setWindowTitle("System Health Check")
            health_window.setModal(True)
            health_window.resize(500, 400)
            
            layout = QVBoxLayout(health_window)
            
            title_label = QLabel("System Health Check")
            title_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
            layout.addWidget(title_label)
            
            # Create scrollable text area
            text_widget = QTextEdit()
            text_widget.setReadOnly(True)
            layout.addWidget(text_widget)
            
            # Perform checks
            text_widget.append("Running system health checks...\n\n")
            
            # Check service status
            is_running, pid = self.service_manager.is_service_running()
            text_widget.append(f"✓ Service Status: {'Running' if is_running else 'Stopped'}")
            if is_running:
                text_widget.append(f" (PID: {pid})")
            text_widget.append("\n")
            
            # Check Discord connectivity status if service is running
            if is_running:
                try:
                    # Import communication manager to check Discord status
                    from communication.core.channel_orchestrator import CommunicationManager
                    comm_manager = CommunicationManager()
                    discord_status = comm_manager.get_discord_connectivity_status()
                    
                    if discord_status:
                        connection_status = discord_status.get('connection_status', 'unknown')
                        if connection_status == 'connected':
                            latency = discord_status.get('latency', 'unknown')
                            guild_count = discord_status.get('guild_count', 'unknown')
                            text_widget.append(f"✓ Discord Status: Connected (Latency: {latency}s, Guilds: {guild_count})\n")
                        else:
                            text_widget.append(f"⚠ Discord Status: {connection_status.title()}\n")
                            
                            # Show detailed error information
                            detailed_errors = discord_status.get('detailed_errors', {})
                            if detailed_errors:
                                for error_type, error_info in detailed_errors.items():
                                    error_msg = error_info.get('error_message', 'Unknown error')
                                    text_widget.append(f"  - {error_type.title()}: {error_msg}\n")
                    else:
                        text_widget.append("? Discord Status: Unable to check\n")
                except Exception as e:
                    text_widget.append(f"? Discord Status: Error checking status - {e}\n")
            else:
                text_widget.append("? Discord Status: Service not running\n")
            
            # Check user count
            user_ids = get_all_user_ids()
            text_widget.append(f"✓ Total Users: {len(user_ids)}\n")
            
            # Check data directories
            required_dirs = [core.config.BASE_DATA_DIR, core.config.USER_INFO_DIR_PATH]
            for dir_path in required_dirs:
                exists = os.path.exists(dir_path)
                status = "✓" if exists else "✗"
                text_widget.append(f"{status} Directory {dir_path}: {'Exists' if exists else 'Missing'}\n")
            
            # Check for common issues
            text_widget.append("\nChecking for common issues...\n")
            
            # Check for orphaned message files
            if os.path.exists(core.config.USER_INFO_DIR_PATH):
                orphaned_files = 0
                for root, dirs, files in os.walk(core.config.USER_INFO_DIR_PATH):
                    for file in files:
                        if file.endswith('.json'):
                            # Extract user_id from filename
                            user_id = file.replace('.json', '')
                            if user_id not in user_ids:
                                orphaned_files += 1
                
                if orphaned_files == 0:
                    text_widget.append("✓ No orphaned message files found\n")
                else:
                    text_widget.append(f"⚠ Found {orphaned_files} orphaned message files\n")
            
            text_widget.append("\nHealth check complete.\n")
            
            close_button = QPushButton("Close")
            close_button.clicked.connect(health_window.accept)
            layout.addWidget(close_button)
            
            health_window.exec()
            
        except Exception as e:
            logger.error(f"Failed to perform health check: {e}")
            QMessageBox.critical(self, "Error", f"Failed to perform health check: {e}")

    @handle_errors("handling window close event", default_return=None)
    def closeEvent(self, event):
        """Handle window close event"""
        self.shutdown_ui_components()
        event.accept()
    
    @handle_errors("shutting down UI components", default_return=None)
    def shutdown_ui_components(self):
        """
        Shutdown UI components with validation.
        
        Returns:
            None: Always returns None
        """
        """Shutdown any UI-created components gracefully"""
        logger.info("Shutting down admin panel.")
        # Admin panel no longer creates its own communication manager
        logger.debug("Admin panel cleanup complete - no communication channels to stop.")
        logger.info("Admin panel shutdown complete.")


@handle_errors("starting UI application")
def main():
    """Main entry point for the Qt-based UI application"""
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("MHM Admin Panel")
    app.setApplicationVersion("1.0")
    
    # Create and show the main window
    window = MHMManagerUI()
    window.show()
    
    # Start the event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

