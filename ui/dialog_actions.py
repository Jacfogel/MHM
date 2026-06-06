"""Dialog orchestration helpers for the admin UI."""

from collections.abc import Callable
from importlib import import_module
from typing import Any

from PySide6.QtWidgets import QMessageBox, QWidget


_lazy_dependencies = import_module("ui.lazy_dependencies")
handle_errors = _lazy_dependencies.handle_errors
get_component_logger = _lazy_dependencies.get_component_logger
get_user_data = _lazy_dependencies.get_user_data
save_user_data = _lazy_dependencies.save_user_data
UserContext = _lazy_dependencies.UserContext

logger = get_component_logger("ui")


def _load_attr(module_name: str, attr_name: str):
    """Load a project attribute through the UI lazy dependency boundary."""
    # ERROR_HANDLING_EXCLUDE: low-level lazy import helper; callers are decorated or fail fast.
    return _lazy_dependencies.load_attr(module_name, attr_name)


@handle_errors("requiring current user", default_return=False)
def _require_current_user(parent: QWidget, current_user: str | None) -> bool:
    """Return True when a user is selected; otherwise warn and return False."""
    if current_user:
        return True
    logger.error("No current user selected")
    QMessageBox.warning(parent, "No User Selected", "Please select a user first.")
    return False


class DialogActions:
    """Opens admin dialogs and wires user-changed refresh callbacks."""

    @handle_errors("creating new user", default_return=None)
    def create_new_user(
        self,
        parent: QWidget,
        *,
        refresh_user_list: Callable[[], None],
        create_comm_manager: Callable[[], Any],
    ) -> None:
        """Open the account creator dialog."""
        logger.info("Admin Panel: Opening create new user dialog")
        try:
            AccountCreatorDialog = _load_attr(
                "ui.dialogs.account_creator_dialog", "AccountCreatorDialog"
            )

            temp_comm_manager = create_comm_manager()
            dialog = AccountCreatorDialog(parent, temp_comm_manager)
            dialog.user_changed.connect(refresh_user_list)
            dialog.exec()
            try:
                temp_comm_manager.stop_all()
            except Exception as cleanup_error:
                logger.warning(
                    f"Error cleaning up temporary communication manager: {cleanup_error}"
                )
        except Exception as e:
            logger.error(f"Error opening create account dialog: {e}")
            QMessageBox.critical(
                parent, "Error", f"Failed to open create account dialog: {str(e)}"
            )

    @handle_errors("managing communication settings", default_return=None)
    def manage_communication_settings(
        self,
        parent: QWidget,
        current_user: str | None,
        *,
        on_user_changed: Callable[[], None],
    ) -> None:
        """Open channel management for the selected user."""
        if not _require_current_user(parent, current_user):
            return
        logger.info(
            f"Admin Panel: Opening communication settings for user {current_user}"
        )
        try:
            ChannelManagementDialog = _load_attr(
                "ui.dialogs.channel_management_dialog", "ChannelManagementDialog"
            )

            dialog = ChannelManagementDialog(parent, user_id=current_user)
            dialog.user_changed.connect(on_user_changed)
            dialog.setWindowTitle(f"Channel Settings - {current_user}")
            dialog.exec()
        except Exception as e:
            logger.error(f"Error opening communication settings dialog: {e}")
            QMessageBox.critical(
                parent, "Error", f"Failed to open communication settings: {str(e)}"
            )

    @handle_errors("managing categories", default_return=None)
    def manage_categories(
        self,
        parent: QWidget,
        current_user: str | None,
        *,
        on_user_changed: Callable[[], None],
        reload_categories: Callable[[], None],
    ) -> None:
        """Open category management for the selected user."""
        if not _require_current_user(parent, current_user):
            return
        logger.info(
            f"Admin Panel: Opening category management for user {current_user}"
        )
        try:
            CategoryManagementDialog = _load_attr(
                "ui.dialogs.category_management_dialog", "CategoryManagementDialog"
            )

            dialog = CategoryManagementDialog(parent, current_user)
            dialog.user_changed.connect(on_user_changed)
            dialog.setWindowTitle(f"Category Settings - {current_user}")
            dialog.exec()
            reload_categories()
        except Exception as e:
            logger.error(f"Error opening category management dialog: {e}")
            QMessageBox.critical(
                parent, "Error", f"Failed to open category management: {str(e)}"
            )

    @handle_errors("managing checkins", default_return=None)
    def manage_checkins(
        self,
        parent: QWidget,
        current_user: str | None,
        *,
        on_user_changed: Callable[[], None],
    ) -> None:
        """Open check-in management for the selected user."""
        if not _require_current_user(parent, current_user):
            return
        logger.info(
            f"Admin Panel: Opening check-in management for user {current_user}"
        )
        try:
            CheckinManagementDialog = _load_attr(
                "ui.dialogs.checkin_management_dialog", "CheckinManagementDialog"
            )

            dialog = CheckinManagementDialog(parent, current_user)
            dialog.user_changed.connect(on_user_changed)
            dialog.setWindowTitle(f"Check-in Management - {current_user}")
            dialog.exec()
        except Exception as e:
            logger.error(f"Error opening check-in management: {e}")
            QMessageBox.critical(
                parent, "Error", f"Failed to open check-in management: {str(e)}"
            )

    @handle_errors("managing tasks", default_return=None)
    def manage_tasks(
        self,
        parent: QWidget,
        current_user: str | None,
        *,
        on_user_changed: Callable[[], None],
    ) -> None:
        """Open task management for the selected user."""
        if not _require_current_user(parent, current_user):
            return
        logger.info(
            f"Admin Panel: Opening task management for user {current_user}"
        )
        try:
            TaskManagementDialog = _load_attr(
                "ui.dialogs.task_management_dialog", "TaskManagementDialog"
            )

            dialog = TaskManagementDialog(parent, current_user)
            dialog.user_changed.connect(on_user_changed)
            dialog.setWindowTitle(f"Task Management - {current_user}")
            dialog.exec()
        except Exception as e:
            logger.error(f"Error opening task management dialog: {e}")
            QMessageBox.critical(
                parent, "Error", f"Failed to open task management: {str(e)}"
            )

    @handle_errors("managing task CRUD", default_return=None)
    def manage_task_crud(
        self,
        parent: QWidget,
        current_user: str | None,
    ) -> None:
        """Open task CRUD for the selected user."""
        if not _require_current_user(parent, current_user):
            return
        logger.info(f"Admin Panel: Opening task CRUD for user {current_user}")
        try:
            TaskCrudDialog = _load_attr("ui.dialogs.task_crud_dialog", "TaskCrudDialog")

            dialog = TaskCrudDialog(parent, current_user)
            dialog.setWindowTitle(f"Task CRUD - {current_user}")
            dialog.exec()
        except Exception as e:
            logger.error(f"Error opening task CRUD dialog: {e}")
            QMessageBox.critical(parent, "Error", f"Failed to open task CRUD: {str(e)}")

    @handle_errors("managing personalization", default_return=None)
    def manage_personalization(
        self,
        parent: QWidget,
        current_user: str | None,
        *,
        on_user_changed: Callable[[], None],
    ) -> None:
        """Open personalization settings for the selected user."""
        if not _require_current_user(parent, current_user):
            return
        logger.info(
            f"Admin Panel: Opening personalization management for user {current_user}"
        )
        try:
            UserProfileDialog = _load_attr(
                "ui.dialogs.user_profile_dialog", "UserProfileDialog"
            )

            user_data = get_user_data(current_user, ["context", "account"])
            context_data = user_data.get("context", {})
            account_data = user_data.get("account", {})
            if "timezone" in account_data:
                context_data["timezone"] = account_data["timezone"]

            # ERROR_HANDLING_EXCLUDE: Nested callback function (already wrapped in try-except by parent)
            def on_save(data):
                tz = data.pop("timezone", None)
                updates = {"context": data}
                if tz is not None:
                    updates["account"] = {"timezone": tz}
                save_user_data(current_user, updates)

            dialog = UserProfileDialog(
                parent, current_user, on_save, existing_data=context_data
            )
            dialog.user_changed.connect(on_user_changed)
            dialog.setWindowTitle(f"Personalization Settings - {current_user}")
            dialog.exec()
        except Exception as e:
            logger.error(f"Error opening personalization dialog: {e}")
            QMessageBox.critical(
                parent, "Error", f"Failed to open personalization settings: {str(e)}"
            )

    @handle_errors("managing user analytics", default_return=None)
    def manage_user_analytics(
        self,
        parent: QWidget,
        current_user: str | None,
    ) -> None:
        """Open user analytics for the selected user."""
        if not _require_current_user(parent, current_user):
            return
        logger.info(f"Admin Panel: Opening user analytics for user {current_user}")
        try:
            open_user_analytics_dialog = _load_attr(
                "ui.dialogs.user_analytics_dialog", "open_user_analytics_dialog"
            )

            open_user_analytics_dialog(parent, current_user)
        except Exception as e:
            logger.error(f"Error opening user analytics: {e}")
            QMessageBox.critical(
                parent, "Error", f"Failed to open user analytics: {str(e)}"
            )

    @handle_errors("preparing selected user category editor", default_return=None)
    def prepare_current_user_category_editor(
        self,
        parent: QWidget,
        current_user: str | None,
        category_combo,
        editor_label: str,
    ) -> str | None:
        """Validate user/category selection and load user context for an editor."""
        if not _require_current_user(parent, current_user):
            return None

        current_index = category_combo.currentIndex()
        if current_index <= 0:
            QMessageBox.warning(
                parent,
                "No Category Selected",
                "Please select a category from the dropdown first.",
            )
            return None

        selected_category = category_combo.itemData(current_index)
        logger.info(
            f"Admin Panel: Opening {editor_label} editor for user {current_user}, category {selected_category}"
        )

        UserContext().get_user_id()
        UserContext().set_user_id(current_user)

        user_data_result = get_user_data(current_user, "account")
        user_account = user_data_result.get("account")
        context_result = get_user_data(current_user, "context")
        user_context = context_result.get("context")
        if user_account:
            UserContext().set_internal_username(
                user_account.get("internal_username", "")
            )
            if user_context:
                UserContext().set_preferred_name(user_context.get("preferred_name", ""))
            UserContext().load_user_data(current_user)

        return selected_category

    @handle_errors("editing user category content", default_return=None)
    def edit_user_category(
        self,
        parent: QWidget,
        current_user: str | None,
        category_combo,
        editor_label: str,
    ) -> None:
        """Open the message or schedule editor for the selected user/category."""
        openers = {
            "message": self.open_message_editor,
            "schedule": self.open_schedule_editor,
        }
        open_editor = openers.get(editor_label)
        if open_editor is None:
            logger.error(f"Unknown category editor label: {editor_label}")
            return
        selected_category = self.prepare_current_user_category_editor(
            parent, current_user, category_combo, editor_label
        )
        if not selected_category:
            return
        open_editor(parent, current_user, None, selected_category)

    # not_duplicate: user_category_editor_actions
    @handle_errors("editing user messages", default_return=None)
    def edit_user_messages(
        self,
        parent: QWidget,
        current_user: str | None,
        category_combo,
    ) -> None:
        """Open the message editor for the selected user/category."""
        self.edit_user_category(parent, current_user, category_combo, "message")

    @handle_errors("opening message editor", default_return=None)
    def open_message_editor(
        self,
        parent: QWidget,
        current_user: str | None,
        parent_dialog,
        category: str | None,
    ) -> None:
        """Open the message editing window for a specific category."""
        if not category or not isinstance(category, str):
            logger.error(f"Invalid category: {category}")
            return None

        if not category.strip():
            logger.error("Empty category provided")
            return None

        logger.info(
            f"Admin Panel: Opening message editor for user {current_user}, category {category}"
        )

        if parent_dialog:
            parent_dialog.accept()

        try:
            open_message_editor_dialog = _load_attr(
                "ui.dialogs.message_editor_dialog", "open_message_editor_dialog"
            )

            open_message_editor_dialog(parent, current_user, category)
        except Exception as e:
            logger.error(f"Error opening message editor: {e}")
            QMessageBox.critical(
                parent, "Error", f"Failed to open message editor: {str(e)}"
            )

    # not_duplicate: user_category_editor_actions
    @handle_errors("editing user schedules", default_return=None)
    def edit_user_schedules(
        self,
        parent: QWidget,
        current_user: str | None,
        category_combo,
    ) -> None:
        """Open the schedule editor for the selected user/category."""
        self.edit_user_category(parent, current_user, category_combo, "schedule")

    @handle_errors("opening schedule editor", default_return=None)
    def open_schedule_editor(
        self,
        parent: QWidget,
        current_user: str | None,
        parent_dialog,
        category: str | None,
    ) -> None:
        """Open the schedule editing window for a specific category."""
        if not category or not isinstance(category, str):
            logger.error(f"Invalid category: {category}")
            return None

        if not category.strip():
            logger.error("Empty category provided")
            return None

        logger.info(
            f"Admin Panel: Opening schedule editor for user {current_user}, category {category}"
        )

        if parent_dialog:
            parent_dialog.accept()

        try:
            open_schedule_editor = _load_attr(
                "ui.dialogs.schedule_editor_dialog", "open_schedule_editor"
            )

            # ERROR_HANDLING_EXCLUDE: Nested callback function (already wrapped in try-except by parent)
            def on_schedule_save():
                logger.info(
                    f"Schedule saved for user {current_user}, category {category}"
                )

            success = open_schedule_editor(
                parent, current_user, category, on_schedule_save
            )

            if success:
                logger.info(
                    f"Schedule editor completed successfully for user {current_user}, category {category}"
                )
            else:
                logger.info(
                    f"Schedule editor cancelled for user {current_user}, category {category}"
                )
        except Exception as e:
            logger.error(f"Error opening schedule editor: {e}")
            QMessageBox.critical(
                parent, "Error", f"Failed to open schedule editor: {str(e)}"
            )
