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
)
from PySide6.QtCore import QTimer


def _load_attr(module_name: str, attr_name: str):
    """Load a project attribute through the UI lazy dependency boundary."""
    # ERROR_HANDLING_EXCLUDE: low-level lazy import helper; callers are decorated or fail fast.
    return _lazy_dependencies.load_attr(module_name, attr_name)


_lazy_dependencies = import_module("ui.lazy_dependencies")
handle_errors = _lazy_dependencies.handle_errors
now_datetime_full = _lazy_dependencies.now_datetime_full
setup_logging = _lazy_dependencies.setup_logging
get_component_logger = _lazy_dependencies.get_component_logger

setup_logging()
logger = get_component_logger("ui")
ui_logger = logger

get_user_data = _lazy_dependencies.get_user_data
Ui_ui_app_mainwindow = _lazy_dependencies.Ui_ui_app_mainwindow
AdminActions = import_module("ui.admin_actions").AdminActions
StatusProvider = import_module("ui.status_provider").StatusProvider
UserListProvider = import_module("ui.user_list_provider").UserListProvider
DialogActions = import_module("ui.dialog_actions").DialogActions
USER_COMBO_PLACEHOLDER = import_module("ui.user_list_provider").USER_COMBO_PLACEHOLDER
CATEGORY_COMBO_PLACEHOLDER = (
    import_module("ui.user_list_provider").CATEGORY_COMBO_PLACEHOLDER
)
scheduler_actions = import_module("ui.scheduler_actions")
request_actions = import_module("ui.request_actions")


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
        self.admin_actions = AdminActions()
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

    @handle_errors("showing request action outcome", default_return=None)
    def _show_request_action_outcome(self, outcome):
        """Display a UI-neutral request action outcome."""
        if outcome is None:
            return
        if outcome.level == "info":
            QMessageBox.information(self, outcome.title, outcome.message)
        elif outcome.level == "warning":
            QMessageBox.warning(self, outcome.title, outcome.message)
        elif outcome.level == "critical":
            QMessageBox.critical(self, outcome.title, outcome.message)

    @handle_errors("sending test message", default_return=None)
    def send_actual_test_message(self, category):
        """Create a service-handled test-message request."""
        outcome = request_actions.create_test_message_request(
            self.current_user,
            category,
        )
        self._show_request_action_outcome(outcome)

    @handle_errors("sending check-in prompt", default_return=None)
    def send_checkin_prompt(self):
        """Create a service-handled check-in prompt request."""
        if not self.current_user:
            QMessageBox.warning(self, "No User Selected", "Please select a user first.")
            return

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

        outcome = request_actions.create_checkin_prompt_request(self.current_user)
        self._show_request_action_outcome(outcome)

    @handle_errors("sending task reminder", default_return=None)
    def send_task_reminder(self):
        """Create a service-handled task reminder request."""
        if not self.current_user:
            QMessageBox.warning(self, "No User Selected", "Please select a user first.")
            return

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

        outcome = request_actions.create_task_reminder_request(
            self.current_user,
            create_communication_manager=_create_communication_manager,
        )
        self._show_request_action_outcome(outcome)

    @handle_errors("toggling logging verbosity", default_return=None)
    def toggle_logging_verbosity(self):
        """Toggle logging verbosity and update menu."""
        self.admin_actions.toggle_logging_verbosity(
            self, self.ui.actionToggle_Verbose_Logging
        )

    @handle_errors("viewing log file", default_return=None)
    def view_log_file(self):
        """Open the log file in the default text editor."""
        self.admin_actions.view_log_file()

    @handle_errors("opening process watcher", default_return=None)
    def open_process_watcher(self):
        """Open the process watcher dialog."""
        self.admin_actions.open_process_watcher(self)

    @handle_errors("viewing cache status", default_return=None)
    def view_cache_status(self):
        """Show cache cleanup status and information."""
        self.admin_actions.view_cache_status(
            self,
            force_clean_cache=self.force_clean_cache,
        )

    @handle_errors("forcing cache cleanup", default_return=None)
    def force_clean_cache(self):
        """Force cache cleanup regardless of schedule."""
        self.admin_actions.force_clean_cache(self)

    @handle_errors("validating configuration", default_return=None)
    def validate_configuration(self):
        """Show detailed configuration validation report."""
        self.admin_actions.validate_configuration(self)

    @handle_errors("showing configuration help", default_return=None)
    def show_configuration_help(self, parent_window):
        """Show help for fixing configuration issues."""
        self.admin_actions.show_configuration_help(parent_window)

    @handle_errors("viewing all users summary", user_friendly=True, default_return=None)
    def view_all_users_summary(self):
        """Show a summary of all users in the system."""
        self.admin_actions.view_all_users_summary(self)

    @handle_errors(
        "performing system health check", user_friendly=True, default_return=None
    )
    def system_health_check(self):
        """Perform a basic system health check."""
        self.admin_actions.system_health_check(
            self,
            service_manager=self.service_manager,
            create_communication_manager=_create_communication_manager,
        )

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
