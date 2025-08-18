# ui_app_qt.py - MHM Management UI (PySide6-based)

import sys
import os
import subprocess
import psutil
import time
from pathlib import Path

# Add parent directory to path so we can import from core
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# PySide6 imports
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QMessageBox, QFileDialog, 
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QComboBox, QGroupBox, QGridLayout, QWidget, QTabWidget, QDialogButtonBox, QCheckBox
)
from PySide6.QtCore import Qt, QTimer, QThread, Signal
from PySide6.QtGui import QFont, QIcon

# Set up logging
from core.logger import setup_logging, get_logger, get_component_logger
setup_logging()
logger = get_component_logger('ui')
ui_logger = logger

# Import configuration validation
from core.config import validate_all_configuration, ConfigValidationError

# Import comprehensive error handling
from core.error_handling import (
    error_handler, DataError, FileOperationError, handle_errors
)

from user.user_context import UserContext
from core.user_data_handlers import get_all_user_ids
from core.user_data_handlers import get_user_data
from core.user_data_validation import title_case
import core.config as cfg

# Import generated UI for main window
from ui.generated.admin_panel_pyqt import Ui_ui_app_mainwindow

class ServiceManager:
    """Manages the MHM backend service process"""
    
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
        """Check if the MHM service is running"""
        # Look for python processes running service.py
        service_pids = []
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            # Skip if process info is not accessible (already terminated)
            if not proc.info['name'] or 'python' not in proc.info['name'].lower():
                continue
            
            cmdline = proc.info.get('cmdline', [])
            if cmdline and any('service.py' in arg for arg in cmdline):
                # Double-check process is still running
                if proc.is_running():
                    service_pids.append(proc.info['pid'])
        
        if service_pids:
            return True, service_pids[0]  # Return first PID
        return False, None
    
    @handle_errors("starting service", default_return=False)
    def start_service(self):
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
        service_path = os.path.join(os.path.dirname(__file__), '..', 'core', 'service.py')
        
        logger.debug(f"Service path: {service_path}")
        
        # Ensure we use the venv Python explicitly
        script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        venv_python = os.path.join(script_dir, '.venv', 'Scripts', 'python.exe')
        if os.path.exists(venv_python):
            python_executable = venv_python
        else:
            python_executable = sys.executable
        
        logger.debug(f"Using Python: {python_executable}")
        
        # Set up environment to ensure venv is used
        env = os.environ.copy()
        venv_scripts_dir = os.path.join(script_dir, '.venv', 'Scripts')
        if os.path.exists(venv_scripts_dir):
            # Add venv Scripts directory to PATH to ensure it's found first
            env['PATH'] = venv_scripts_dir + os.pathsep + env.get('PATH', '')
        
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
        """Stop the MHM backend service"""
        is_running, pid = self.is_service_running()
        if not is_running:
            logger.info("Stop service requested but service is not running")
            QMessageBox.information(None, "Service Status", "MHM Service is not running")
            return True
        
        logger.info(f"Stop service requested for PID: {pid}")
        
        # Create shutdown request file
        shutdown_file = os.path.join(os.path.dirname(__file__), '..', 'shutdown_request.flag')
        try:
            with open(shutdown_file, 'w') as f:
                f.write(f"SHUTDOWN_REQUESTED_BY_UI_{time.time()}")
            logger.info(f"Created shutdown request file: {shutdown_file}")
        except Exception as e:
            logger.warning(f"Could not create shutdown file: {e}")
        
        # Try to terminate ALL service processes
        found_processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if not proc.info['name'] or 'python' not in proc.info['name'].lower():
                    continue
                cmdline = proc.info.get('cmdline', [])
                if cmdline and any('service.py' in arg for arg in cmdline):
                    if proc.is_running():
                        found_processes.append(proc)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        
        if not found_processes:
            # Wait-and-retry loop to confirm service is stopped
            max_retries = 6  # 3 seconds total
            for _ in range(max_retries):
                is_running, current_pid = self.is_service_running()
                if not is_running:
                    break
                time.sleep(0.5)
            is_running, current_pid = self.is_service_running()
            if not is_running:
                logger.info("Service is not running - stop operation successful")
                QMessageBox.information(None, "Service Status", "Service is already stopped")
                return True
            else:
                logger.info(f"Service still detected with different PID {current_pid} - considering stop successful")
                QMessageBox.information(None, "Service Status", "Service processes cleaned up successfully")
                return True
        else:
            if len(found_processes) > 1:
                logger.info(f"Found {len(found_processes)} service processes, cleaning up all instances")
            else:
                logger.info(f"Found {len(found_processes)} service process, terminating")
            all_terminated = True
            
            for proc in found_processes:
                proc_pid = proc.info['pid']
                try:
                    proc.terminate()
                    logger.debug(f"Terminated process {proc_pid}")
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    logger.debug(f"Process {proc_pid} already terminated or access denied")
                    continue
            
            # Wait for processes to terminate
            time.sleep(1)
            
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
                logger.info("Service stopped successfully")
                QMessageBox.information(None, "Service Status", "MHM Service stopped successfully")
                return True
            else:
                logger.warning(f"Service still running with PID {current_pid} after termination attempts")
                QMessageBox.warning(None, "Service Status", f"Service may still be running (PID: {current_pid})")
                return False
    
    @handle_errors("restarting service", default_return=False)
    def restart_service(self):
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
        
    def load_ui(self):
        """Load the UI from the .ui file"""
        ui_file_path = os.path.join(os.path.dirname(__file__), 'designs', 'admin_panel.ui')
        if not os.path.exists(ui_file_path):
            raise FileNotFoundError(f"UI file not found: {ui_file_path}")

        # Load and apply the QSS theme
        self.load_theme()
        
    def load_theme(self):
        """Load and apply the QSS theme from the styles directory"""
        try:
            # Path to the QSS theme file
            theme_path = os.path.join(os.path.dirname(__file__), '..', 'styles', 'admin_theme.qss')
            
            if os.path.exists(theme_path):
                with open(theme_path, 'r', encoding='utf-8') as f:
                    theme_content = f.read()
                
                # Apply the theme to the application
                self.setStyleSheet(theme_content)
                logger.info(f"QSS theme loaded successfully from: {theme_path}")
            else:
                logger.warning(f"QSS theme file not found: {theme_path}")
                
        except Exception as e:
            logger.error(f"Failed to load QSS theme: {e}")
        
    def connect_signals(self):
        """Connect UI signals to slots"""
        # Service management buttons
        self.ui.pushButton_start_service.clicked.connect(self.start_service)
        self.ui.pushButton_stop_service.clicked.connect(self.stop_service)
        self.ui.pushButton_restart_service.clicked.connect(self.restart_service)
        self.ui.pushButton_refresh_server_status.clicked.connect(self.update_service_status)
        
        # User management
        self.ui.pushButton_create_new_user.clicked.connect(self.create_new_user)
        self.ui.comboBox_users.currentTextChanged.connect(self.on_user_selected)
        
        # User action buttons
        self.ui.pushButton_communication_settings.clicked.connect(self.manage_communication_settings)
        self.ui.pushButton_personalization.clicked.connect(self.manage_personalization)
        self.ui.pushButton_category_management.clicked.connect(self.manage_categories)
        self.ui.pushButton_checkin_settings.clicked.connect(self.manage_checkins)
        self.ui.pushButton_task_management.clicked.connect(self.manage_tasks)
        self.ui.pushButton_task_crud.clicked.connect(self.manage_task_crud)
        
        # Category actions
        self.ui.comboBox_user_categories.currentTextChanged.connect(self.on_category_selected)
        self.ui.pushButton_edit_messages.clicked.connect(self.edit_user_messages)
        self.ui.pushButton_edit_schedules.clicked.connect(self.edit_user_schedules)
        self.ui.pushButton_send_test_message.clicked.connect(self.send_test_message)
        
        # Menu actions
        self.ui.actionToggle_Verbose_Logging.triggered.connect(self.toggle_logging_verbosity)
        self.ui.actionView_Log_File.triggered.connect(self.view_log_file)
        self.ui.actionView_Cache_Status.triggered.connect(self.view_cache_status)
        self.ui.actionForce_Clean_Cache.triggered.connect(self.force_clean_cache)
        self.ui.actionValidate_Configuration.triggered.connect(self.validate_configuration)
        self.ui.actionView_All_Users.triggered.connect(self.view_all_users_summary)
        self.ui.actionSystem_Health_Check.triggered.connect(self.system_health_check)
        
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
    
    def update_service_status(self):
        """Update the service status display"""
        is_running, pid = self.service_manager.is_service_running()
        
        if is_running:
            self.ui.label_service_status.setText(f"Service Status: Running (PID: {pid})")
            self.ui.label_service_status.setStyleSheet("color: green; font-weight: bold;")
        else:
            self.ui.label_service_status.setText("Service Status: Stopped")
            self.ui.label_service_status.setStyleSheet("color: red; font-weight: bold;")
    
    def start_service(self):
        """Start the MHM service"""
        if self.service_manager.start_service():
            self.update_service_status()
    
    def stop_service(self):
        """Stop the MHM service"""
        if self.service_manager.stop_service():
            self.update_service_status()
    
    def restart_service(self):
        """Restart the MHM service"""
        if self.service_manager.restart_service():
            self.update_service_status()
    
    @handle_errors("refreshing user list", default_return=None)
    def refresh_user_list(self):
        """Refresh the user list in the combo box using user index"""
        try:
            from core.user_data_manager import load_json_data
            from core.config import BASE_DATA_DIR
            
            # Remember the currently selected user
            current_user_id = self.current_user
            
            # Load user index
            index_file = os.path.join(cfg.BASE_DATA_DIR, "user_index.json")
            index_data = load_json_data(index_file) or {}
            
            self.ui.comboBox_users.clear()
            self.ui.comboBox_users.addItem("Select a user...")
            
            # Sort users by preferred name, then internal username
            sorted_users = sorted(
                index_data.items(),
                key=lambda x: (
                    x[1].get('preferred_name', '') or x[1].get('internal_username', ''),
                    x[1].get('internal_username', '')
                )
            )
            
            for user_id, user_info in sorted_users:
                if not user_info.get('active', True):
                    continue  # Skip inactive users
                    
                internal_username = user_info.get('internal_username', 'Unknown')
                channel_type = user_info.get('channel_type', 'unknown')
                enabled_features = user_info.get('enabled_features', [])
                
                # Build display name with channel type and features
                feature_summary = []
                if 'automated_messages' in enabled_features:
                    categories = [f for f in enabled_features if f not in ['automated_messages', 'checkins', 'task_management']]
                    if categories:
                        # Apply title_case to category names for display
                        # Replace underscores with spaces before applying title_case
                        formatted_categories = [title_case(cat.replace('_', ' ')) for cat in categories]
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
            # Fallback to directory scanning if index fails
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
                formatted_category = title_case(category.replace('_', ' '))
                self.ui.comboBox_user_categories.addItem(formatted_category, category)
                
        except Exception as e:
            logger.error(f"Error loading user categories: {e}")
            self.current_user_categories = []
    
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
    
    def enable_content_management(self):
        """Enable content management buttons"""
        self.ui.pushButton_communication_settings.setEnabled(True)
        self.ui.pushButton_personalization.setEnabled(True)
        self.ui.pushButton_category_management.setEnabled(True)
        self.ui.pushButton_checkin_settings.setEnabled(True)
        self.ui.pushButton_task_management.setEnabled(True)
        self.ui.pushButton_task_crud.setEnabled(True)
        
        # Enable category actions group
        self.ui.groupBox_category_actions.setEnabled(True)
    
    def disable_content_management(self):
        """Disable content management buttons"""
        self.ui.pushButton_communication_settings.setEnabled(False)
        self.ui.pushButton_personalization.setEnabled(False)
        self.ui.pushButton_category_management.setEnabled(False)
        self.ui.pushButton_checkin_settings.setEnabled(False)
        self.ui.pushButton_task_management.setEnabled(False)
        self.ui.pushButton_task_crud.setEnabled(False)
        
        # Disable category actions group
        self.ui.groupBox_category_actions.setEnabled(False)
        
        # Clear category combo box
        self.ui.comboBox_user_categories.clear()
        self.ui.comboBox_user_categories.addItem("Select a category...")
    
    # Placeholder methods for user actions - these will need to be implemented
    # based on your existing functionality from the Tkinter version
    
    @handle_errors("creating new user")
    def create_new_user(self):
        """Open dialog to create a new user"""
        logger.info("Admin Panel: Opening create new user dialog")
        try:
            from ui.dialogs.account_creator_dialog import AccountCreatorDialog
            from bot.communication_manager import CommunicationManager
            from bot.channel_registry import register_all_channels
            register_all_channels()
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

    @handle_errors("managing communication settings")
    def manage_communication_settings(self):
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

    @handle_errors("managing categories")
    def manage_categories(self):
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

    @handle_errors("managing checkins")
    def manage_checkins(self):
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

    @handle_errors("managing tasks")
    def manage_tasks(self):
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

    @handle_errors("managing task CRUD")
    def manage_task_crud(self):
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

    @handle_errors("managing personalization")
    def manage_personalization(self):
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
    
    @handle_errors("editing user messages")
    def edit_user_messages(self):
        """Open message editing interface for selected user"""
        if not self.current_user:
            QMessageBox.warning(self, "No User Selected", "Please select a user first.")
            return
            
        logger.info(f"Admin Panel: Opening message editor for user {self.current_user}")
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
        
        # Get user categories
        prefs_result = get_user_data(self.current_user, 'preferences')
        categories = prefs_result.get('preferences', {}).get('categories', [])
        
        if not categories:
            logger.info(f"Admin Panel: User {self.current_user} has no message categories configured")
            QMessageBox.information(self, "No Categories", "This user has no message categories configured.")
            return
        
        # Open category selection dialog
        category_dialog = QDialog(self)
        category_dialog.setWindowTitle(f"Select Category - {self.current_user}")
        category_dialog.setModal(True)
        category_dialog.resize(300, 200)
        
        layout = QVBoxLayout(category_dialog)
        
        title_label = QLabel("Select message category to edit:")
        title_label.setFont(QFont("Arial", 12))
        layout.addWidget(title_label)
        
        for category in categories:
            # Replace underscores with spaces before applying title_case
            formatted_category = title_case(category.replace('_', ' '))
            button = QPushButton(formatted_category)
            button.clicked.connect(lambda checked, c=category: self.open_message_editor(category_dialog, c))
            layout.addWidget(button)
        
        category_dialog.exec()

    @handle_errors("opening message editor")
    def open_message_editor(self, parent_dialog, category):
        """Open the message editing window for a specific category"""
        logger.info(f"Admin Panel: Opening message editor for user {self.current_user}, category {category}")
        parent_dialog.accept()
        
        try:
            # For now, show a message that this feature is being migrated
            QMessageBox.information(self, "Feature in Migration", 
                f"Message editing for category '{category}' is currently being migrated from Tkinter to PySide6.\n\n"
                "This feature will be available in the next update.")
            
        except Exception as e:
            logger.error(f"Error opening message editor: {e}")
            QMessageBox.critical(self, "Error", f"Failed to open message editor: {str(e)}")
    
    @handle_errors("editing user schedules")
    def edit_user_schedules(self):
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

    @handle_errors("opening schedule editor")
    def open_schedule_editor(self, parent_dialog, category):
        """Open the schedule editing window for a specific category"""
        logger.info(f"Admin Panel: Opening schedule editor for user {self.current_user}, category {category}")
        
        # Close parent dialog if it exists
        if parent_dialog:
            parent_dialog.accept()
        
        try:
            from ui.dialogs.schedule_editor_dialog import open_schedule_editor
            
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
    
    @handle_errors("sending test message")
    def send_test_message(self):
        """Send a test message to the selected user"""
        if not self.current_user:
            QMessageBox.warning(self, "No User Selected", "Please select a user first.")
            return
        
        # Check if service is running
        is_running, pid = self.service_manager.is_service_running()
        if not is_running:
            QMessageBox.warning(self, "Service Not Running", 
                               "MHM Service is not running. Test messages require the service to be active.\n\n"
                               "To send a test message:\n"
                               "1. Click 'Start Service' above\n"
                               "2. Wait for service to initialize\n"
                               "3. Try sending the test message again\n\n"
                               "The admin panel does not create its own communication channels.")
            return
        
        # Get the currently selected category from the dropdown
        current_index = self.ui.comboBox_user_categories.currentIndex()
        if current_index <= 0:  # No category selected or "Select a category..." is selected
            QMessageBox.warning(self, "No Category Selected", "Please select a category from the dropdown above.")
            return
        
        # Get the actual category value from the combo box data
        category = self.ui.comboBox_user_categories.itemData(current_index)
        if not category:
            QMessageBox.warning(self, "Invalid Category", "Please select a valid category from the dropdown.")
            return
        
        logger.info(f"Admin Panel: Preparing test message for user {self.current_user}, category {category}")
        
        # Confirm the test message
        self.confirm_test_message(category)

    @handle_errors("confirming test message")
    def confirm_test_message(self, category):
        """Confirm and send test message"""
        result = QMessageBox.question(self, "Confirm Test Message", 
                                     f"Send a test {category} message to {self.current_user}?\n\n"
                                     f"This will send a random message from their {category} collection.",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if result == QMessageBox.StandardButton.Yes:
            logger.info(f"Admin Panel: Test message confirmed for user {self.current_user}, category {category}")
            # Actually send the test message using communication manager
            self.send_actual_test_message(category)
        else:
            logger.info(f"Admin Panel: Test message cancelled for user {self.current_user}, category {category}")

    @handle_errors("sending actual test message")
    def send_actual_test_message(self, category):
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
        
        # Use the same directory structure as the shutdown flag
        base_dir = os.path.dirname(os.path.dirname(__file__))  # Go up to MHM root
        request_file = os.path.join(base_dir, f'test_message_request_{self.current_user}_{category}.flag')
        
        test_request = {
            "user_id": self.current_user,
            "category": category,
            "timestamp": datetime.now().isoformat(),
            "source": "admin_panel"
        }
        
        with open(request_file, 'w') as f:
            json.dump(test_request, f, indent=2)
        
        QMessageBox.information(self, "Test Message Requested", 
                               f"Test {category} message request created for {self.current_user}.\n\n"
                               f"The running service will check for this request and send the message.\n\n"
                               f"Note: Current implementation creates a request file.\n"
                               f"Future versions will have direct service communication.\n\n"
                               f"Request file: {os.path.basename(request_file)}")
        
        logger.info(f"Admin Panel: Test message request file created: {request_file}")
        
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
    
    # Debug and admin methods
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
    
    @handle_errors("viewing log file")
    def view_log_file(self):
        """Open the log file in the default text editor."""
        import webbrowser
        from core.config import LOG_FILE_PATH
        webbrowser.open(LOG_FILE_PATH)
    
    @handle_errors("viewing cache status")
    def view_cache_status(self):
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
    
    @handle_errors("forcing cache cleanup")
    def force_clean_cache(self):
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
    
    @handle_errors("validating configuration")
    def validate_configuration(self):
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
            BASE_DATA_DIR, LOG_FILE_PATH, LOG_LEVEL, LM_STUDIO_BASE_URL, 
            AI_TIMEOUT_SECONDS, SCHEDULER_INTERVAL, EMAIL_SMTP_SERVER, EMAIL_IMAP_SERVER, 
            EMAIL_SMTP_USERNAME, DISCORD_BOT_TOKEN
        )
        
        config_values = [
            ("Base Data Directory", BASE_DATA_DIR),
            ("Log File", LOG_FILE_PATH),
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
- LOG_FILE_PATH (default: app.log)
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

For detailed setup instructions, see the README.md file.
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
                    from bot.communication_manager import CommunicationManager
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
            required_dirs = [cfg.BASE_DATA_DIR, cfg.USER_INFO_DIR_PATH]
            for dir_path in required_dirs:
                exists = os.path.exists(dir_path)
                status = "✓" if exists else "✗"
                text_widget.append(f"{status} Directory {dir_path}: {'Exists' if exists else 'Missing'}\n")
            
            # Check for common issues
            text_widget.append("\nChecking for common issues...\n")
            
            # Check for orphaned message files
            if os.path.exists(cfg.USER_INFO_DIR_PATH):
                orphaned_files = 0
                for root, dirs, files in os.walk(cfg.USER_INFO_DIR_PATH):
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

    def closeEvent(self, event):
        """Handle window close event"""
        self.shutdown_ui_components()
        event.accept()
    
    @handle_errors("shutting down UI components")
    def shutdown_ui_components(self):
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

