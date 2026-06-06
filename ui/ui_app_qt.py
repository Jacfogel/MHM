import sys
import os
import pathlib
from importlib import import_module
from pathlib import Path

# Add parent directory to path so we can import from core
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# PySide6 imports
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QMessageBox,
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QWidget,
)
from PySide6.QtCore import QTimer
from PySide6.QtGui import QFont


def _load_attr(module_name: str, attr_name: str):
    """Load a project attribute through the UI lazy dependency boundary."""
    # ERROR_HANDLING_EXCLUDE: low-level lazy import helper; callers are decorated or fail fast.
    return _lazy_dependencies.load_attr(module_name, attr_name)


_lazy_dependencies = import_module("ui.lazy_dependencies")
handle_errors = _lazy_dependencies.handle_errors
now_datetime_full = _lazy_dependencies.now_datetime_full
now_timestamp_full = _lazy_dependencies.now_timestamp_full
setup_logging = _lazy_dependencies.setup_logging
get_component_logger = _lazy_dependencies.get_component_logger

setup_logging()
logger = get_component_logger("ui")
ui_logger = logger

core_config = import_module("core.config")
import contextlib

validate_all_configuration = _lazy_dependencies.validate_all_configuration
get_flags_dir = _lazy_dependencies.get_flags_dir
UserContext = _lazy_dependencies.UserContext
get_all_user_ids = _lazy_dependencies.get_all_user_ids
get_user_data = _lazy_dependencies.get_user_data
Ui_ui_app_mainwindow = _lazy_dependencies.Ui_ui_app_mainwindow
StatusProvider = import_module("ui.status_provider").StatusProvider
UserListProvider = import_module("ui.user_list_provider").UserListProvider
DialogActions = import_module("ui.dialog_actions").DialogActions
USER_COMBO_PLACEHOLDER = import_module("ui.user_list_provider").USER_COMBO_PLACEHOLDER
CATEGORY_COMBO_PLACEHOLDER = (
    import_module("ui.user_list_provider").CATEGORY_COMBO_PLACEHOLDER
)
scheduler_actions = import_module("ui.scheduler_actions")


@handle_errors("creating communication manager for UI action", re_raise=True)
def _create_communication_manager():
    """Create a communication manager without importing it at UI module load time."""
    CommunicationManager = _load_attr(
        "communication.core.channel_orchestrator", "CommunicationManager"
    )

    return CommunicationManager()


class MHMManagerUI(QMainWindow):
    """Main MHM Management UI using PySide6"""

    # ERROR_HANDLING_EXCLUDE: UI constructor - calls methods with error handling (load_ui, connect_signals, initialize_ui)
    def __init__(self):
        """Initialize the object."""
        super().__init__()
        self.service_manager = import_module("ui.service_manager").ServiceManager()
        self.status_provider = StatusProvider(self.service_manager)
        self.user_list_provider = UserListProvider()
        self.dialog_actions = DialogActions()
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
        if os.getenv("MHM_TESTING") != "1":
            self.status_timer.start(5000)  # Update every 5 seconds
            # Initial status update
            self.update_service_status()

    @handle_errors("loading UI", default_return=None)
    def load_ui(self):
        """Load the UI from the .ui file"""
        ui_file_path = Path(__file__).parent / "designs" / "admin_panel.ui"
        if not ui_file_path.exists():
            raise FileNotFoundError(f"UI file not found: {ui_file_path}")

        # Load and apply the QSS theme
        self.load_theme()

    @handle_errors("loading theme", user_friendly=False, default_return=None)
    def load_theme(self):
        """Load and apply the QSS theme from the styles directory"""
        # Path to the QSS theme file
        theme_path = Path(__file__).parent.parent / "styles" / "admin_theme.qss"

        # Test code may monkeypatch Path with generic mocks. Guard against
        # non-pathlike objects so we never pass file-descriptor-like values to open().
        if not isinstance(theme_path, (str, bytes, pathlib.Path)):
            logger.warning("Theme path is not path-like; skipping theme load")
            return

        if theme_path.exists():
            with open(theme_path, encoding="utf-8") as f:
                theme_content = f.read()

            # Apply the theme to the application
            self.setStyleSheet(theme_content)
            logger.info(f"QSS theme loaded successfully from: {theme_path}")
        else:
            logger.warning(f"QSS theme file not found: {theme_path}")

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
        self.ui.pushButton_communication_settings.clicked.connect(
            self.manage_communication_settings
        )
        self.ui.pushButton_personalization.clicked.connect(self.manage_personalization)
        self.ui.pushButton_category_management.clicked.connect(self.manage_categories)
        self.ui.pushButton_user_analytics.clicked.connect(self.manage_user_analytics)
        self.ui.pushButton_checkin_settings.clicked.connect(self.manage_checkins)
        self.ui.pushButton_task_management.clicked.connect(self.manage_tasks)
        self.ui.pushButton_task_crud.clicked.connect(self.manage_task_crud)
        self.ui.pushButton_run_user_scheduler.clicked.connect(self.run_user_scheduler)

        # Category actions
        self.ui.comboBox_user_categories.currentTextChanged.connect(
            self.on_category_selected
        )
        self.ui.pushButton_edit_messages.clicked.connect(self.edit_user_messages)
        self.ui.pushButton_edit_schedules.clicked.connect(self.edit_user_schedules)
        self.ui.pushButton_send_test_message.clicked.connect(self.send_test_message)
        self.ui.pushButton_run_category_scheduler.clicked.connect(
            self.run_category_scheduler
        )

        # User actions
        self.ui.pushButton_send_checkin_prompt.clicked.connect(self.send_checkin_prompt)
        self.ui.pushButton_send_task_reminder.clicked.connect(self.send_task_reminder)

        # Menu actions
        self.ui.actionToggle_Verbose_Logging.triggered.connect(
            self.toggle_logging_verbosity
        )
        self.ui.actionView_Log_File.triggered.connect(self.view_log_file)
        self.ui.actionProcess_Watcher.triggered.connect(self.open_process_watcher)
        self.ui.actionView_Cache_Status.triggered.connect(self.view_cache_status)
        self.ui.actionForce_Clean_Cache.triggered.connect(self.force_clean_cache)
        self.ui.actionValidate_Configuration.triggered.connect(
            self.validate_configuration
        )
        self.ui.actionView_All_Users.triggered.connect(self.view_all_users_summary)
        self.ui.actionSystem_Health_Check.triggered.connect(self.system_health_check)

    @handle_errors("initializing UI", default_return=None)
    def initialize_ui(self):
        """Initialize the UI state"""
        # Disable category management until user is selected
        self.disable_content_management()

        if os.getenv("MHM_TESTING") == "1":
            return

        # Update user index automatically on startup
        self.update_user_index_on_startup()

        # Load user list
        self.refresh_user_list()

    @handle_errors("updating user index on startup", default_return=None)
    def update_user_index_on_startup(self):
        """Automatically update the user index when the admin panel starts"""
        rebuild_user_index = _load_attr(
            "storage.user_data_operations", "rebuild_user_index"
        )

        logger.info("Admin Panel: Updating user index on startup...")

        success = rebuild_user_index()
        if success:
            logger.info("Admin Panel: User index updated successfully on startup")
        else:
            logger.warning("Admin Panel: Failed to update user index on startup")

    @handle_errors("updating service status", default_return=None)
    def update_service_status(self):
        """Update the service status display"""
        is_running, pid = self.status_provider.check_service_status()

        if is_running:
            self.ui.label_service_status.setText(
                f"Service Status: Running (PID: {pid})"
            )
            self.ui.label_service_status.setStyleSheet(
                "color: green; font-weight: bold;"
            )
        else:
            self.ui.label_service_status.setText("Service Status: Stopped")
            self.ui.label_service_status.setStyleSheet("color: red; font-weight: bold;")

        # Update Discord channel status
        discord_running = self.status_provider.check_discord_status()
        if discord_running:
            self.ui.label_discord_status.setText("Discord Channel: Running")
            self.ui.label_discord_status.setStyleSheet(
                "color: green; font-weight: bold;"
            )
        else:
            self.ui.label_discord_status.setText("Discord Channel: Stopped")
            self.ui.label_discord_status.setStyleSheet("color: red; font-weight: bold;")

        # Update Email channel status
        email_running = self.status_provider.check_email_status()
        if email_running:
            self.ui.label_email_status.setText("Email Channel: Running")
            self.ui.label_email_status.setStyleSheet("color: green; font-weight: bold;")
        else:
            self.ui.label_email_status.setText("Email Channel: Stopped")
            self.ui.label_email_status.setStyleSheet("color: red; font-weight: bold;")

        # Update ngrok tunnel status
        ngrok_status = self.status_provider.check_ngrok_status()
        if ngrok_status["running"]:
            pid_text = f" (PID: {ngrok_status['pid']})" if ngrok_status["pid"] else ""
            self.ui.label_ngrok_status.setText(f"ngrok tunnel: Running{pid_text}")
            self.ui.label_ngrok_status.setStyleSheet("color: green; font-weight: bold;")
        else:
            self.ui.label_ngrok_status.setText("ngrok tunnel: Stopped")
            self.ui.label_ngrok_status.setStyleSheet("color: red; font-weight: bold;")
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

    @handle_errors("running full scheduler", default_return=None)
    def run_full_scheduler(self):
        """Run the full scheduler for all users"""
        success = scheduler_actions.run_full_scheduler(_create_communication_manager)

        if success:
            QMessageBox.information(
                None, "Scheduler", "Full scheduler started successfully for all users"
            )
        else:
            QMessageBox.warning(None, "Scheduler", "Failed to start full scheduler")

    @handle_errors("running user scheduler", default_return=None)
    def run_user_scheduler(self):
        """Run scheduler for the selected user"""
        if not self.current_user:
            QMessageBox.warning(None, "Scheduler", "Please select a user first")
            return

        success = scheduler_actions.run_user_scheduler(self.current_user)

        if success:
            QMessageBox.information(
                None,
                "Scheduler",
                f"User scheduler started successfully for {self.current_user}",
            )
        else:
            QMessageBox.warning(
                None,
                "Scheduler",
                f"Failed to start user scheduler for {self.current_user}",
            )

    @handle_errors("running category scheduler", default_return=None)
    def run_category_scheduler(self):
        """Run scheduler for the selected user and category"""
        if not self.current_user:
            QMessageBox.warning(None, "Scheduler", "Please select a user first")
            return

        category = self.ui.comboBox_user_categories.currentText()
        if not category:
            QMessageBox.warning(None, "Scheduler", "Please select a category first")
            return

        success = scheduler_actions.run_category_scheduler(self.current_user, category)

        if success:
            QMessageBox.information(
                None,
                "Scheduler",
                f"Category scheduler started successfully for {self.current_user}, {category}",
            )
        else:
            QMessageBox.warning(
                None,
                "Scheduler",
                f"Failed to start category scheduler for {self.current_user}, {category}",
            )

    @handle_errors("refreshing user list", default_return=None)
    def refresh_user_list(self):
        """
        Refresh the user list with validation.

        Returns:
            None: Always returns None
        """
        # Remember the currently selected user before any operations
        current_user_id = self.current_user

        # Block signals during refresh to prevent empty string errors
        self.ui.comboBox_users.blockSignals(True)
        try:
            self._populate_active_users_in_combo_box()

        except Exception as e:
            logger.error(f"Error refreshing user list: {e}")
            self._refresh_user_list_fallback(e)
        finally:
            # Always re-enable signals, even if an error occurred
            self.ui.comboBox_users.blockSignals(False)

        # Reselect the previously selected user if it still exists
        self._reselect_user_if_present(current_user_id)

    @handle_errors("resetting user combo box", default_return=None)
    def _reset_user_combo_box(self):
        """Clear user combo and add placeholder entry."""
        self.ui.comboBox_users.clear()
        self.ui.comboBox_users.addItem(USER_COMBO_PLACEHOLDER)

    @handle_errors("populating active users in combo box", default_return=None)
    def _populate_active_users_in_combo_box(self):
        """Populate user combo box from active user metadata."""
        self._reset_user_combo_box()
        provider = self.user_list_provider
        for user_data in provider.collect_active_users_for_combo():
            self.ui.comboBox_users.addItem(
                provider.build_user_combo_display_name(user_data)
            )

    @handle_errors("refreshing user list fallback", default_return=None)
    def _refresh_user_list_fallback(self, original_error: Exception):
        """Fallback user list refresh using minimal account/context reads."""
        try:
            self._reset_user_combo_box()
            for display_name in self.user_list_provider.collect_fallback_display_names():
                self.ui.comboBox_users.addItem(display_name)
        except Exception as fallback_error:
            logger.error(f"Fallback user list refresh also failed: {fallback_error}")
            QMessageBox.warning(
                self, "Error", f"Failed to refresh user list: {original_error}"
            )

    @handle_errors("reselecting previously active user", default_return=None)
    def _reselect_user_if_present(self, current_user_id: str | None):
        """Reselect prior active user if still present in combo list."""
        item_texts = [
            self.ui.comboBox_users.itemText(index)
            for index in range(self.ui.comboBox_users.count())
        ]
        index = UserListProvider.find_reselect_index(item_texts, current_user_id)
        if index is None:
            return
        item_text = self.ui.comboBox_users.itemText(index)
        self.ui.comboBox_users.setCurrentIndex(index)
        self.on_user_selected(item_text)

    @handle_errors("handling user selection", default_return=None)
    def on_user_selected(self, user_display):
        """
        Handle user selection with validation.

        Returns:
            None: Always returns None
        """
        # Validate user_display
        # Empty strings are expected during combo box refresh, so handle gracefully
        if not user_display:
            return None

        if not isinstance(user_display, str):
            logger.error(
                f"Invalid user_display type: {type(user_display)}, value: {user_display}"
            )
            return None

        if not user_display.strip():
            # Empty or whitespace-only string - expected during refresh, return silently
            return None

        if user_display == USER_COMBO_PLACEHOLDER:
            self.current_user = None
            self.disable_content_management()
            return

        try:
            user_id = UserListProvider.parse_user_id_from_display(user_display)
            if not user_id:
                logger.warning(
                    "Admin Panel: Could not parse user_id from selected_display: "
                    f"'{user_display}'"
                )
                self.disable_content_management()
                return

            self.current_user = user_id
            user_data_result = get_user_data(user_id, "account")
            user_account = user_data_result.get("account")
            if user_account:
                self.load_user_categories(user_id)
                self.enable_content_management()
                logger.info(
                    f"Admin Panel: User selected for management: {user_id} "
                    f"({user_account.get('internal_username', 'Unknown')})"
                )
            else:
                QMessageBox.warning(
                    self, "User Error", f"Could not load user account for {user_id}"
                )
                self.disable_content_management()
                return

        except Exception as e:
            logger.error(f"Error handling user selection: {e}")
            QMessageBox.warning(self, "Error", f"Failed to load user: {e}")
            self.disable_content_management()

    @handle_errors("loading user categories", user_friendly=False, default_return=None)
    def load_user_categories(self, user_id):
        """Load categories for the selected user"""
        self.current_user_categories = self.user_list_provider.load_category_names(
            user_id
        )

        self.ui.comboBox_user_categories.clear()
        self.ui.comboBox_user_categories.addItem(CATEGORY_COMBO_PLACEHOLDER)

        for category in self.current_user_categories:
            self.ui.comboBox_user_categories.addItem(
                UserListProvider.format_category_display(category),
                category,
            )

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
        has_category = bool(
            actual_category and actual_category != CATEGORY_COMBO_PLACEHOLDER
        )

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
        """Open dialog to create a new user."""
        self.dialog_actions.create_new_user(
            self,
            refresh_user_list=self.refresh_user_list,
            create_comm_manager=_create_communication_manager,
        )

    @handle_errors("managing communication settings", default_return=None)
    def manage_communication_settings(self):
        """Open channel management for the selected user."""
        self.dialog_actions.manage_communication_settings(
            self,
            self.current_user,
            on_user_changed=self.refresh_user_list,
        )

    @handle_errors("managing categories", default_return=None)
    def manage_categories(self):
        """Open category management for the selected user."""
        self.dialog_actions.manage_categories(
            self,
            self.current_user,
            on_user_changed=self.refresh_user_list,
            reload_categories=lambda: self.load_user_categories(self.current_user),
        )

    @handle_errors("managing checkins", default_return=None)
    def manage_checkins(self):
        """Open check-in management for the selected user."""
        self.dialog_actions.manage_checkins(
            self,
            self.current_user,
            on_user_changed=self.refresh_user_list,
        )

    @handle_errors("managing tasks", default_return=None)
    def manage_tasks(self):
        """Open task management for the selected user."""
        self.dialog_actions.manage_tasks(
            self,
            self.current_user,
            on_user_changed=self.refresh_user_list,
        )

    @handle_errors("managing task CRUD", default_return=None)
    def manage_task_crud(self):
        """Open task CRUD for the selected user."""
        self.dialog_actions.manage_task_crud(self, self.current_user)

    @handle_errors("managing personalization", default_return=None)
    def manage_personalization(self):
        """Open personalization settings for the selected user."""
        self.dialog_actions.manage_personalization(
            self,
            self.current_user,
            on_user_changed=self.refresh_user_list,
        )

    @handle_errors("managing user analytics", default_return=None)
    def manage_user_analytics(self):
        """Open user analytics for the selected user."""
        self.dialog_actions.manage_user_analytics(self, self.current_user)

    @handle_errors("delegating user category editor", default_return=None)
    def _open_user_category_editor(self, editor_label: str) -> None:
        """Delegate message or schedule editing for the selected user/category."""
        self.dialog_actions.edit_user_category(
            self,
            self.current_user,
            self.ui.comboBox_user_categories,
            editor_label,
        )

    # not_duplicate: user_category_editor_actions
    @handle_errors("editing user messages", default_return=None)
    def edit_user_messages(self):
        """Open message editing for the selected user/category."""
        self._open_user_category_editor("message")

    @handle_errors("opening message editor", default_return=None)
    def open_message_editor(self, parent_dialog, category):
        """Open the message editor for a category."""
        self.dialog_actions.open_message_editor(
            self, self.current_user, parent_dialog, category
        )

    # not_duplicate: user_category_editor_actions
    @handle_errors("editing user schedules", default_return=None)
    def edit_user_schedules(self):
        """Open schedule editing for the selected user/category."""
        self._open_user_category_editor("schedule")

    @handle_errors("opening schedule editor", default_return=None)
    def open_schedule_editor(self, parent_dialog, category):
        """Open the schedule editor for a category."""
        self.dialog_actions.open_schedule_editor(
            self, self.current_user, parent_dialog, category
        )

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
            QMessageBox.warning(
                self,
                "Service Not Running",
                "MHM Service is not running. Test messages require the service to be active.\n\n"
                "To send a test message:\n"
                "1. Click 'Start Service' above\n"
                "2. Wait for service to initialize\n"
                "3. Try sending the test message again\n\n"
                "The admin panel does not create its own communication channels.",
            )
            return False
        return True

    @handle_errors("getting selected category", default_return=None)
    def _send_test_message__get_selected_category(self):
        """Get and validate the selected category from the dropdown."""
        current_index = self.ui.comboBox_user_categories.currentIndex()
        if (
            current_index <= 0
        ):  # No category selected or "Select a category..." is selected
            QMessageBox.warning(
                self,
                "No Category Selected",
                "Please select a category from the dropdown above.",
            )
            return None

        category = self.ui.comboBox_user_categories.itemData(current_index)
        if not category:
            QMessageBox.warning(
                self,
                "Invalid Category",
                "Please select a valid category from the dropdown.",
            )
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

        logger.info(
            f"Admin Panel: Preparing test message for user {self.current_user}, category {category}"
        )

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

        logger.info(
            f"Admin Panel: Creating test message request for user {self.current_user}, category {category}"
        )

        # Create a test message request using the same pattern as shutdown requests
        import json

        # Use the same directory structure as the shutdown flag
        base_dir = get_flags_dir()
        request_file = (
            base_dir / f"test_message_request_{self.current_user}_{category}.flag"
        )

        test_request = {
            "user_id": self.current_user,
            "category": category,
            "timestamp": now_timestamp_full(),
            "source": "admin_panel",
        }

        with open(request_file, "w") as f:
            json.dump(test_request, f, indent=2)
        logger.info(f"Admin Panel: Test message request file created: {request_file}")

        # Wait briefly for service to process and write response file with actual message
        actual_message = "Message will be selected from your collection"
        channel_name = "unknown"
        response_file = (
            base_dir / f"test_message_response_{self.current_user}_{category}.flag"
        )

        # Wait up to 3 seconds for the service to process and write the response
        import time

        for _ in range(30):  # Check 30 times over 3 seconds
            if response_file.exists():
                try:
                    with open(response_file) as f:
                        response_data = json.load(f)
                    actual_message = response_data.get("message", actual_message)
                    # Clean up response file
                    with contextlib.suppress(Exception):
                        os.remove(response_file)
                    break
                except Exception as e:
                    logger.debug(f"Could not read response file: {e}")
            time.sleep(0.1)  # Wait 100ms between checks

        # Get channel name for dialog
        prefs_result = get_user_data(
            self.current_user, "preferences", normalize_on_read=True
        )
        preferences = prefs_result.get("preferences", {})
        channel_name = preferences.get("channel", {}).get("type", "unknown")

        # Truncate message if too long for dialog
        if len(actual_message) > 100:
            actual_message = actual_message[:97] + "..."

        QMessageBox.information(
            self,
            "Test Message Sent",
            f"Test {category} message sent to {self.current_user} via {channel_name}.\n\n"
            f"Message: {actual_message}",
        )

        # Optional: Clean up old request files after a short delay
        # Skip cleanup thread during test execution to avoid Qt threading issues in subprocesses
        import sys

        is_test_env = "pytest" in sys.modules or "PYTEST_CURRENT_TEST" in os.environ
        if not is_test_env:
            import threading

            @handle_errors(
                "cleaning up old request file", user_friendly=False, default_return=None
            )
            def cleanup_old_requests():
                import time

                try:
                    time.sleep(300)  # Wait 5 minutes
                    if os.path.exists(request_file):
                        os.remove(request_file)
                        logger.debug(f"Cleaned up old request file: {request_file}")
                except Exception as e:
                    # Silently handle any errors in cleanup thread (e.g., Qt access violations in subprocesses)
                    logger.debug(f"Cleanup thread error (ignored): {e}")

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
            QMessageBox.warning(
                self,
                "Service Not Running",
                "MHM Service is not running. Check-in prompts require the service to be active.\n\n"
                "To send a check-in prompt:\n"
                "1. Click 'Start Service' above\n"
                "2. Wait for service to initialize\n"
                "3. Try sending the check-in prompt again",
            )
            return

        logger.info(f"Admin Panel: Sending check-in prompt to user {self.current_user}")

        # Get user preferences to determine messaging service and recipient
        prefs_result = get_user_data(
            self.current_user, "preferences", normalize_on_read=True
        )
        preferences = prefs_result.get("preferences")

        if not preferences:
            QMessageBox.warning(
                self,
                "User Configuration Error",
                f"User preferences not found for {self.current_user}.",
            )
            return

        messaging_service = preferences.get("channel", {}).get("type")
        if not messaging_service:
            QMessageBox.warning(
                self,
                "User Configuration Error",
                f"No messaging service configured for {self.current_user}.",
            )
            return

        # Create check-in prompt request file (same pattern as test messages)
        # The service will pick this up and send the check-in prompt
        import json
        import time

        base_dir = Path(__file__).parent.parent
        request_file = base_dir / f"checkin_prompt_request_{self.current_user}.flag"

        checkin_request = {
            "user_id": self.current_user,
            "timestamp": now_timestamp_full(),
            "source": "admin_panel",
        }

        with open(request_file, "w") as f:
            json.dump(checkin_request, f, indent=2)

        # Wait briefly for service to process and write response file with actual first question
        first_question = "Check-in questions"
        response_file = base_dir / f"checkin_prompt_response_{self.current_user}.flag"

        # Wait up to 3 seconds for the service to process and write the response
        for _ in range(30):  # Check 30 times over 3 seconds
            if response_file.exists():
                try:
                    with open(response_file) as f:
                        response_data = json.load(f)
                    first_question = response_data.get("first_question", first_question)
                    # Clean up response file
                    with contextlib.suppress(Exception):
                        os.remove(response_file)
                    break
                except Exception as e:
                    logger.debug(f"Could not read check-in response file: {e}")
            time.sleep(0.1)  # Wait 100ms between checks

        # Truncate if too long
        if len(first_question) > 100:
            first_question = first_question[:97] + "..."

        QMessageBox.information(
            self,
            "Check-in Prompt Sent",
            f"Check-in prompt sent to {self.current_user} via {messaging_service}.\n\n"
            f"First question: {first_question}",
        )
        logger.info(
            f"Admin Panel: Check-in prompt request file created: {request_file}"
        )

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
            QMessageBox.warning(
                self,
                "Service Not Running",
                "MHM Service is not running. Task reminders require the service to be active.\n\n"
                "To send a task reminder:\n"
                "1. Click 'Start Service' above\n"
                "2. Wait for service to initialize\n"
                "3. Try sending the task reminder again",
            )
            return

        logger.info(
            f"Admin Panel: Preparing task reminder for user {self.current_user}"
        )

        try:
            # Get user preferences first (needed for channel check)
            prefs_result = get_user_data(
                self.current_user, "preferences", normalize_on_read=True
            )
            preferences = prefs_result.get("preferences")

            # Check if tasks are enabled for this user
            are_tasks_enabled = _load_attr("tasks", "are_tasks_enabled")
            load_active_tasks = _load_attr("tasks", "load_active_tasks")
            runtime_task_is_completed = _load_attr(
                "tasks.task_data_handlers", "runtime_task_is_completed"
            )

            if not are_tasks_enabled(self.current_user):
                QMessageBox.warning(
                    self,
                    "Tasks Not Enabled",
                    f"Tasks are not enabled for {self.current_user}.",
                )
                return

            # Get active tasks
            active_tasks = load_active_tasks(self.current_user)
            if not active_tasks:
                QMessageBox.warning(
                    self,
                    "No Active Tasks",
                    f"{self.current_user} has no active tasks to remind about.",
                )
                return

            # Filter out completed tasks
            incomplete_tasks = [
                task for task in active_tasks if not runtime_task_is_completed(task)
            ]
            if not incomplete_tasks:
                QMessageBox.warning(
                    self,
                    "No Incomplete Tasks",
                    f"All tasks for {self.current_user} are already completed.",
                )
                return

            # Use scheduler's weighted selection for proper priority-based semi-random selection
            # Note: We create a temporary scheduler manager just for task selection
            # The actual sending will be done by the service when it processes the request file
            SchedulerManager = _load_attr("scheduler.manager", "SchedulerManager")

            # Create temporary instances for task selection only
            temp_comm_manager = _create_communication_manager()
            scheduler_manager = SchedulerManager(temp_comm_manager)

            # Select task using priority-based weighting (considers priority, due dates, etc.)
            selected_task = scheduler_manager.select_task_for_reminder(incomplete_tasks)

            if not selected_task:
                QMessageBox.warning(
                    self,
                    "Task Selection Error",
                    "Could not select a task for reminder.",
                )
                return

            task_id = selected_task.get("id")
            task_title = selected_task.get("title", "Untitled Task")

            if not task_id:
                QMessageBox.warning(
                    self, "Invalid Task", "Selected task has no id."
                )
                return

            # Get channel name for dialog
            messaging_service = (
                preferences.get("channel", {}).get("type") if preferences else None
            )
            channel_name = messaging_service if messaging_service else "unknown"

            # Create task reminder request file (same pattern as test messages)
            # The service will pick this up and send the task reminder
            import json

            base_dir = Path(__file__).parent.parent
            request_file = (
                base_dir / f"task_reminder_request_{self.current_user}_{task_id}.flag"
            )

            task_reminder_request = {
                "user_id": self.current_user,
                "task_identifier": task_id,
                "timestamp": now_timestamp_full(),
                "source": "admin_panel",
            }

            with open(request_file, "w") as f:
                json.dump(task_reminder_request, f, indent=2)

            QMessageBox.information(
                self,
                "Task Reminder Sent",
                f"Task reminder sent to {self.current_user} via {channel_name}.\n\n"
                f"Task: {task_title}",
            )
            logger.info(
                f"Admin Panel: Task reminder request file created: {request_file}"
            )

        except Exception as e:
            logger.error(f"Error sending task reminder: {e}")
            QMessageBox.critical(
                self, "Error", f"Failed to send task reminder: {str(e)}"
            )

    # Debug and admin methods
    @handle_errors("toggling logging verbosity", default_return=None)
    def toggle_logging_verbosity(self):
        """Toggle logging verbosity and update menu."""
        toggle_verbose_logging = _load_attr("core.logger", "toggle_verbose_logging")

        is_verbose = toggle_verbose_logging()

        # Update the menu text
        verbose_status = "ON" if is_verbose else "OFF"
        self.ui.actionToggle_Verbose_Logging.setText(
            f"Toggle Verbose Logging (Currently: {verbose_status})"
        )

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
        LOG_MAIN_FILE = _load_attr("core.config", "LOG_MAIN_FILE")

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
            ProcessWatcherDialog = _load_attr(
                "ui.dialogs.process_watcher_dialog", "ProcessWatcherDialog"
            )

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
        get_cleanup_status = _load_attr("core.auto_cleanup", "get_cleanup_status")
        find_pycache_dirs = _load_attr("core.auto_cleanup", "find_pycache_dirs")
        find_pyc_files = _load_attr("core.auto_cleanup", "find_pyc_files")
        calculate_cache_size = _load_attr("core.auto_cleanup", "calculate_cache_size")

        # Get cleanup status
        status = get_cleanup_status()

        # Get current cache size
        pycache_dirs = find_pycache_dirs(".")
        pyc_files = find_pyc_files(".")
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
ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â¢ {len(pycache_dirs)} __pycache__ directories
ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â¢ {len(pyc_files)} standalone .pyc files
ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â¢ Total size: {current_size / 1024:.1f} KB ({current_size / (1024 * 1024):.2f} MB)"""

        status_text.setPlainText(status_content)
        layout.addWidget(status_text)

        # Buttons
        button_layout = QHBoxLayout()

        force_clean_button = QPushButton("Force Clean")
        force_clean_button.clicked.connect(
            lambda: [self.force_clean_cache(), status_window.accept()]
        )
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
        perform_cleanup = _load_attr("core.auto_cleanup", "perform_cleanup")
        update_cleanup_timestamp = _load_attr(
            "core.auto_cleanup", "update_cleanup_timestamp"
        )

        # Ask for confirmation
        result = QMessageBox.question(
            self,
            "Force Cache Cleanup",
            "This will force cleanup of all Python cache files regardless of when they were last cleaned.\n\nAre you sure you want to continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if result == QMessageBox.StandardButton.Yes:
            success = perform_cleanup()
            if success:
                update_cleanup_timestamp()
                QMessageBox.information(
                    self, "Cache Cleanup", "Force cache cleanup completed successfully!"
                )
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
        from PySide6.QtWidgets import QTabWidget, QTextEdit

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
        summary_text = result["summary"]
        if result["valid"]:
            summary_color = "green"
            summary_icon = "ÃƒÂ¢Ã…â€œÃ¢â‚¬Å“"
        else:
            summary_color = "red"
            summary_icon = "ÃƒÂ¢Ã…â€œÃ¢â‚¬â€"

        summary_label = QLabel(f"{summary_icon} {summary_text}")
        summary_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        summary_label.setStyleSheet(f"color: {summary_color};")
        layout.addWidget(summary_label)

        # Available channels
        if result["available_channels"]:
            channels_label = QLabel(
                f"Available Channels: {', '.join(result['available_channels'])}"
            )
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
        if result["errors"]:
            errors_widget = QWidget()
            errors_layout = QVBoxLayout(errors_widget)

            errors_text = QTextEdit()
            errors_text.setReadOnly(True)

            for i, error in enumerate(result["errors"], 1):
                errors_text.append(f"{i}. {error}\n")

            errors_layout.addWidget(errors_text)
            tab_widget.addTab(errors_widget, f"Errors ({len(result['errors'])})")

        # Warnings tab
        if result["warnings"]:
            warnings_widget = QWidget()
            warnings_layout = QVBoxLayout(warnings_widget)

            warnings_text = QTextEdit()
            warnings_text.setReadOnly(True)

            for i, warning in enumerate(result["warnings"], 1):
                warnings_text.append(f"{i}. {warning}\n")

            warnings_layout.addWidget(warnings_text)
            tab_widget.addTab(warnings_widget, f"Warnings ({len(result['warnings'])})")

        # Current Configuration tab
        config_widget = QWidget()
        config_layout = QVBoxLayout(config_widget)

        config_text = QTextEdit()
        config_text.setReadOnly(True)

        # Add current configuration values
        BASE_DATA_DIR = _load_attr("core.config", "BASE_DATA_DIR")
        LOG_MAIN_FILE = _load_attr("core.config", "LOG_MAIN_FILE")
        LOG_LEVEL = _load_attr("core.config", "LOG_LEVEL")
        LM_STUDIO_BASE_URL = _load_attr("core.config", "LM_STUDIO_BASE_URL")
        AI_TIMEOUT_SECONDS = _load_attr("core.config", "AI_TIMEOUT_SECONDS")
        SCHEDULER_INTERVAL = _load_attr("core.config", "SCHEDULER_INTERVAL")
        EMAIL_SMTP_SERVER = _load_attr("core.config", "EMAIL_SMTP_SERVER")
        EMAIL_IMAP_SERVER = _load_attr("core.config", "EMAIL_IMAP_SERVER")
        EMAIL_SMTP_USERNAME = _load_attr("core.config", "EMAIL_SMTP_USERNAME")
        DISCORD_BOT_TOKEN = _load_attr("core.config", "DISCORD_BOT_TOKEN")

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
            (
                "Discord Bot Token",
                "Configured" if DISCORD_BOT_TOKEN else "Not configured",
            ),
        ]

        for name, value in config_values:
            config_text.append(f"{name}: {value}\n")

        config_layout.addWidget(config_text)
        tab_widget.addTab(config_widget, "Current Configuration")

        # Buttons
        button_layout = QHBoxLayout()

        if not result["valid"]:
            fix_button = QPushButton("Fix Configuration")
            fix_button.clicked.connect(
                lambda: self.show_configuration_help(report_window)
            )
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

    @handle_errors("viewing all users summary", user_friendly=True, default_return=None)
    def view_all_users_summary(self):
        """Show a summary of all users in the system."""
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
                user_data_result = get_user_data(user_id, "account")
                user_account = user_data_result.get("account")
                # Get user context
                context_result = get_user_data(user_id, "context")
                user_context = context_result.get("context")
                if user_account:
                    username = user_account.get("internal_username", "Unknown")
                    preferred_name = (
                        user_context.get("preferred_name", "") if user_context else ""
                    )
                    prefs_result = get_user_data(user_id, "preferences")
                    prefs = prefs_result.get("preferences", {})
                    categories = prefs.get("categories", [])
                    messaging_service = prefs.get("channel", {}).get("type", "Unknown")

                    summary_text += f"User: {username}"
                    if preferred_name:
                        summary_text += f" ({preferred_name})"
                    summary_text += "\n"
                    summary_text += f"  ID: {user_id}\n"
                    summary_text += f"  Service: {messaging_service}\n"
                    summary_text += f"  Categories: {', '.join(categories) if categories else 'None'}\n"
                    summary_text += "\n"

            text_widget.setPlainText(summary_text)

        close_button = QPushButton("Close")
        close_button.clicked.connect(summary_window.accept)
        layout.addWidget(close_button)

        summary_window.exec()

    @handle_errors(
        "performing system health check", user_friendly=True, default_return=None
    )
    def system_health_check(self):
        """Perform a basic system health check."""
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
        text_widget.append(
            f"ÃƒÂ¢Ã…â€œÃ¢â‚¬Å“ Service Status: {'Running' if is_running else 'Stopped'}"
        )
        if is_running:
            text_widget.append(f" (PID: {pid})")
        text_widget.append("\n")

        # Check Discord connectivity status if service is running
        if is_running:
            try:
                # Create communication manager to check Discord status
                comm_manager = _create_communication_manager()
                discord_status = comm_manager.get_channel_connectivity_status("discord")

                if discord_status:
                    connection_status = discord_status.get(
                        "connection_status", "unknown"
                    )
                    if connection_status == "connected":
                        latency = discord_status.get("latency", "unknown")
                        guild_count = discord_status.get("guild_count", "unknown")
                        text_widget.append(
                            f"ÃƒÂ¢Ã…â€œÃ¢â‚¬Å“ Discord Status: Connected (Latency: {latency}s, Guilds: {guild_count})\n"
                        )
                    else:
                        text_widget.append(
                            f"ÃƒÂ¢Ã…Â¡Ã‚Â  Discord Status: {connection_status.title()}\n"
                        )

                        # Show detailed error information
                        detailed_errors = discord_status.get("detailed_errors", {})
                        if detailed_errors:
                            for error_type, error_info in detailed_errors.items():
                                error_msg = error_info.get(
                                    "error_message", "Unknown error"
                                )
                                text_widget.append(
                                    f"  - {error_type.title()}: {error_msg}\n"
                                )
                else:
                    text_widget.append("? Discord Status: Unable to check\n")
            except Exception as e:
                text_widget.append(f"? Discord Status: Error checking status - {e}\n")
        else:
            text_widget.append("? Discord Status: Service not running\n")

        # Check user count
        user_ids = get_all_user_ids()
        text_widget.append(f"ÃƒÂ¢Ã…â€œÃ¢â‚¬Å“ Total Users: {len(user_ids)}\n")

        # Check data directories
        required_dirs = [core_config.BASE_DATA_DIR, core_config.USER_INFO_DIR_PATH]
        for dir_path in required_dirs:
            exists = os.path.exists(dir_path)
            status = "ÃƒÂ¢Ã…â€œÃ¢â‚¬Å“" if exists else "ÃƒÂ¢Ã…â€œÃ¢â‚¬â€"
            text_widget.append(
                f"{status} Directory {dir_path}: {'Exists' if exists else 'Missing'}\n"
            )

        # Check for common issues
        text_widget.append("\nChecking for common issues...\n")

        # Check for orphaned message files
        if os.path.exists(core_config.USER_INFO_DIR_PATH):
            orphaned_files = 0
            for _root, _dirs, files in os.walk(core_config.USER_INFO_DIR_PATH):
                for file in files:
                    if file.endswith(".json"):
                        # Extract user_id from filename
                        user_id = file.replace(".json", "")
                        if user_id not in user_ids:
                            orphaned_files += 1

            if orphaned_files == 0:
                text_widget.append("ÃƒÂ¢Ã…â€œÃ¢â‚¬Å“ No orphaned message files found\n")
            else:
                text_widget.append(f"ÃƒÂ¢Ã…Â¡Ã‚Â  Found {orphaned_files} orphaned message files\n")

        text_widget.append("\nHealth check complete.\n")

        close_button = QPushButton("Close")
        close_button.clicked.connect(health_window.accept)
        layout.addWidget(close_button)

        health_window.exec()

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
        logger.debug(
            "Admin panel cleanup complete - no communication channels to stop."
        )
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
