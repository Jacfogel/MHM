import sys
import os
import pathlib
from functools import partial
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
DialogActions = import_module("ui.dialog_actions").DialogActions
UserSelectionController = import_module(
    "ui.user_selection_controller"
).UserSelectionController
scheduler_actions = import_module("ui.scheduler_actions")
request_actions = import_module("ui.request_actions")
status_view_updater = import_module("ui.status_view_updater")


@handle_errors("creating communication manager for UI action", re_raise=True)
def _create_communication_manager():
    """Create a communication manager without importing it at UI module load time."""
    CommunicationManager = _load_attr(
        "communication.core.channel_orchestrator", "CommunicationManager"
    )

    return CommunicationManager()


@handle_errors("copying user selection state to UI shell", default_return=None)
def _copy_user_selection_state(window):
    """Copy controller selection state onto shell attributes."""
    window.current_user = window.user_selection.current_user
    window.current_user_categories = window.user_selection.current_user_categories


class MHMManagerUI(QMainWindow):
    """Main MHM Management UI using PySide6"""

    # ERROR_HANDLING_EXCLUDE: UI constructor - calls methods with error handling (load_ui, connect_signals, initialize_ui)
    def __init__(self):
        """Initialize the object."""
        super().__init__()
        self.service_manager = import_module("ui.service_manager").ServiceManager()
        self.status_provider = StatusProvider(self.service_manager)
        self.dialog_actions = DialogActions()
        self.admin_actions = AdminActions()
        # Load the generated UI
        self.ui = Ui_ui_app_mainwindow()
        self.ui.setupUi(self)
        self.user_selection = UserSelectionController(
            self.ui, get_user_data_func=get_user_data
        )
        self.current_user = self.user_selection.current_user
        self.current_user_categories = self.user_selection.current_user_categories
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

    @handle_errors("resolving delegated UI action", re_raise=True)
    def __getattr__(self, name):
        """Resolve thin UI action delegates without defining each as a method."""
        delegated_action = DELEGATED_UI_ACTIONS.get(name)
        if delegated_action is None:
            raise AttributeError(name)
        return partial(delegated_action, self)

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
        self.ui.pushButton_phrase_settings.clicked.connect(self.manage_phrase_settings)
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
        status_view_updater.update_status_labels(self.ui, self.status_provider)

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
        """Refresh the user list with validation."""
        self.user_selection.refresh_user_list(self)
        _copy_user_selection_state(self)

    @handle_errors("handling user selection", default_return=None)
    def on_user_selected(self, user_display):
        """Handle user selection with validation."""
        self.user_selection.on_user_selected(user_display, parent_window=self)
        _copy_user_selection_state(self)

    @handle_errors("loading user categories", user_friendly=False, default_return=None)
    def load_user_categories(self, user_id):
        """Load categories for the selected user."""
        self.user_selection.load_user_categories(user_id)
        _copy_user_selection_state(self)

    @handle_errors("handling category selection", default_return=None)
    def on_category_selected(self, category):
        """Handle category selection"""
        self.user_selection.on_category_selected()

    @handle_errors("enabling content management", default_return=None)
    def enable_content_management(self):
        """Enable content management buttons"""
        self.user_selection.enable_content_management()

    @handle_errors("disabling content management", default_return=None)
    def disable_content_management(self):
        """Disable content management buttons"""
        self.user_selection.disable_content_management()

    @handle_errors("creating new user", default_return=None)
    def create_new_user(self):
        """Open dialog to create a new user."""
        self.dialog_actions.create_new_user(
            self,
            refresh_user_list=self.refresh_user_list,
            create_comm_manager=_create_communication_manager,
        )

    @handle_errors("sending test message", default_return=None)
    def send_test_message(self):
        """Send a test message to the selected user"""
        if not request_actions.validate_selected_user(
            self, self.current_user, message_box=QMessageBox
        ):
            return
        if not request_actions.validate_service_running(
            self, self.service_manager, "Test messages", message_box=QMessageBox
        ):
            return
        category = request_actions.get_selected_category(
            self, self.ui.comboBox_user_categories, message_box=QMessageBox
        )
        if not category:
            return
        logger.info(
            f"Admin Panel: Preparing test message for user {self.current_user}, category {category}"
        )
        self.send_actual_test_message(category)

    @handle_errors("sending test message", default_return=None)
    def send_actual_test_message(self, category):
        """Create a service-handled test-message request."""
        outcome = request_actions.create_test_message_request(
            self.current_user,
            category,
        )
        request_actions.show_request_action_outcome(
            self, outcome, message_box=QMessageBox
        )

    @handle_errors("sending check-in prompt", default_return=None)
    def send_checkin_prompt(self):
        """Create a service-handled check-in prompt request."""
        request_actions.send_checkin_prompt_request(
            self, self.current_user, self.service_manager, message_box=QMessageBox
        )

    @handle_errors("sending task reminder", default_return=None)
    def send_task_reminder(self):
        """Create a service-handled task reminder request."""
        request_actions.send_task_reminder_request(
            self,
            self.current_user,
            self.service_manager,
            create_communication_manager=_create_communication_manager,
            message_box=QMessageBox,
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


DELEGATED_UI_ACTIONS = {
    "manage_communication_settings": lambda self: self.dialog_actions.manage_communication_settings(
        self,
        self.current_user,
        on_user_changed=self.refresh_user_list,
    ),
    "manage_categories": lambda self: self.dialog_actions.manage_categories(
        self,
        self.current_user,
        on_user_changed=self.refresh_user_list,
        reload_categories=lambda: self.load_user_categories(self.current_user),
    ),
    "manage_checkins": lambda self: self.dialog_actions.manage_checkins(
        self,
        self.current_user,
        on_user_changed=self.refresh_user_list,
    ),
    "manage_tasks": lambda self: self.dialog_actions.manage_tasks(
        self,
        self.current_user,
        on_user_changed=self.refresh_user_list,
    ),
    "manage_task_crud": lambda self: self.dialog_actions.manage_task_crud(
        self, self.current_user
    ),
    "manage_personalization": lambda self: self.dialog_actions.manage_personalization(
        self,
        self.current_user,
        on_user_changed=self.refresh_user_list,
    ),
    "manage_phrase_settings": lambda self: self.dialog_actions.manage_phrase_settings(
        self,
        self.current_user,
        on_user_changed=self.refresh_user_list,
    ),
    "manage_user_analytics": lambda self: self.dialog_actions.manage_user_analytics(
        self, self.current_user
    ),
    "edit_user_messages": lambda self: self.dialog_actions.edit_user_category(
        self,
        self.current_user,
        self.ui.comboBox_user_categories,
        "message",
    ),
    "open_message_editor": lambda self, parent_dialog, category: self.dialog_actions.open_message_editor(
        self, self.current_user, parent_dialog, category
    ),
    "edit_user_schedules": lambda self: self.dialog_actions.edit_user_category(
        self,
        self.current_user,
        self.ui.comboBox_user_categories,
        "schedule",
    ),
    "open_schedule_editor": lambda self, parent_dialog, category: self.dialog_actions.open_schedule_editor(
        self, self.current_user, parent_dialog, category
    ),
    "toggle_logging_verbosity": lambda self: self.admin_actions.toggle_logging_verbosity(
        self, self.ui.actionToggle_Verbose_Logging
    ),
    "view_log_file": lambda self: self.admin_actions.view_log_file(),
    "open_process_watcher": lambda self: self.admin_actions.open_process_watcher(self),
    "view_cache_status": lambda self: self.admin_actions.view_cache_status(
        self,
        force_clean_cache=self.force_clean_cache,
    ),
    "force_clean_cache": lambda self: self.admin_actions.force_clean_cache(self),
    "validate_configuration": lambda self: self.admin_actions.validate_configuration(
        self
    ),
    "show_configuration_help": lambda self, parent_window: self.admin_actions.show_configuration_help(
        parent_window
    ),
    "view_all_users_summary": lambda self: self.admin_actions.view_all_users_summary(
        self
    ),
    "system_health_check": lambda self: self.admin_actions.system_health_check(
        self,
        service_manager=self.service_manager,
        create_communication_manager=_create_communication_manager,
    ),
}


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
