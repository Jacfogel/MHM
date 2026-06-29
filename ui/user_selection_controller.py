"""User and category selection state controller for the admin UI."""

from importlib import import_module

from PySide6.QtWidgets import QMessageBox


_lazy_dependencies = import_module("ui.lazy_dependencies")
handle_errors = _lazy_dependencies.handle_errors
logger = _lazy_dependencies.get_component_logger("ui")
get_user_data = _lazy_dependencies.get_user_data

_user_list_provider = import_module("ui.user_list_provider")
UserListProvider = _user_list_provider.UserListProvider
USER_COMBO_PLACEHOLDER = _user_list_provider.USER_COMBO_PLACEHOLDER
CATEGORY_COMBO_PLACEHOLDER = _user_list_provider.CATEGORY_COMBO_PLACEHOLDER


class UserSelectionController:
    """Own user/category combo state transitions for the admin UI shell."""

    @handle_errors("initializing user selection controller", default_return=None)
    def __init__(
        self,
        ui,
        provider: UserListProvider | None = None,
        get_user_data_func=None,
    ):
        self.ui = ui
        self.provider = provider or UserListProvider()
        self.get_user_data = get_user_data_func or get_user_data
        self.current_user: str | None = None
        self.current_user_categories: list[str] = []

    @handle_errors("refreshing user list", default_return=None)
    def refresh_user_list(self, parent_window) -> None:
        """Refresh the user combo box while preserving selection when possible."""
        current_user_id = self.current_user
        self.ui.comboBox_users.blockSignals(True)
        try:
            self.populate_active_users()
        except Exception as e:
            logger.error(f"Error refreshing user list: {e}")
            self.refresh_user_list_fallback(parent_window, e)
        finally:
            self.ui.comboBox_users.blockSignals(False)
        self.reselect_user_if_present(current_user_id)

    @handle_errors("resetting user combo box", default_return=None)
    def reset_user_combo_box(self) -> None:
        """Clear user combo and add placeholder entry."""
        self.ui.comboBox_users.clear()
        self.ui.comboBox_users.addItem(USER_COMBO_PLACEHOLDER)

    @handle_errors("populating active users in combo box", default_return=None)
    def populate_active_users(self) -> None:
        """Populate user combo box from active user metadata."""
        self.reset_user_combo_box()
        for user_data in self.provider.collect_active_users_for_combo():
            self.ui.comboBox_users.addItem(
                self.provider.build_user_combo_display_name(user_data)
            )

    @handle_errors("refreshing user list fallback", default_return=None)
    def refresh_user_list_fallback(self, parent_window, original_error: Exception):
        """Fallback user list refresh using minimal account/context reads."""
        try:
            self.reset_user_combo_box()
            for display_name in self.provider.collect_fallback_display_names():
                self.ui.comboBox_users.addItem(display_name)
        except Exception as fallback_error:
            logger.error(f"Fallback user list refresh also failed: {fallback_error}")
            QMessageBox.warning(
                parent_window, "Error", f"Failed to refresh user list: {original_error}"
            )

    @handle_errors("reselecting previously active user", default_return=None)
    def reselect_user_if_present(self, current_user_id: str | None) -> None:
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
        self.on_user_selected(item_text, parent_window=None)

    @handle_errors("handling user selection", default_return=None)
    def on_user_selected(self, user_display, parent_window=None) -> str | None:
        """Handle user combo selection and return the selected user id."""
        if not user_display:
            return self.current_user
        if not isinstance(user_display, str):
            logger.error(
                f"Invalid user_display type: {type(user_display)}, value: {user_display}"
            )
            return self.current_user
        if not user_display.strip():
            return self.current_user
        if user_display == USER_COMBO_PLACEHOLDER:
            self.current_user = None
            self.disable_content_management()
            return self.current_user

        try:
            user_id = UserListProvider.parse_user_id_from_display(user_display)
            if not user_id:
                logger.warning(
                    "Admin Panel: Could not parse user_id from selected_display: "
                    f"'{user_display}'"
                )
                self.disable_content_management()
                return self.current_user

            self.current_user = user_id
            user_data_result = self.get_user_data(user_id, "account")
            user_account = user_data_result.get("account")
            if user_account:
                self.load_user_categories(user_id)
                self.enable_content_management()
                logger.info(
                    f"Admin Panel: User selected for management: {user_id} "
                    f"({user_account.get('internal_username', 'Unknown')})"
                )
                return self.current_user

            QMessageBox.warning(
                parent_window, "User Error", f"Could not load user account for {user_id}"
            )
            self.disable_content_management()
        except Exception as e:
            logger.error(f"Error handling user selection: {e}")
            QMessageBox.warning(parent_window, "Error", f"Failed to load user: {e}")
            self.disable_content_management()
        return self.current_user

    @handle_errors("loading user categories", user_friendly=False, default_return=[])
    def load_user_categories(self, user_id: str) -> list[str]:
        """Load categories for the selected user into the category combo."""
        self.current_user_categories = self.provider.load_category_names(user_id)
        self.ui.comboBox_user_categories.clear()
        self.ui.comboBox_user_categories.addItem(CATEGORY_COMBO_PLACEHOLDER)
        for category in self.current_user_categories:
            self.ui.comboBox_user_categories.addItem(
                UserListProvider.format_category_display(category),
                category,
            )
        return self.current_user_categories

    @handle_errors("handling category selection", default_return=None)
    def on_category_selected(self) -> str | None:
        """Update category action enablement and return selected category data."""
        current_index = self.ui.comboBox_user_categories.currentIndex()
        actual_category = (
            self.ui.comboBox_user_categories.itemData(current_index)
            if current_index > 0
            else None
        )
        has_category = bool(
            actual_category and actual_category != CATEGORY_COMBO_PLACEHOLDER
        )
        self.ui.pushButton_edit_messages.setEnabled(has_category)
        self.ui.pushButton_edit_schedules.setEnabled(has_category)
        self.ui.pushButton_send_test_message.setEnabled(has_category)
        return actual_category if has_category else None

    @handle_errors("enabling content management", default_return=None)
    def enable_content_management(self) -> None:
        """Enable content management controls."""
        self._set_content_controls_enabled(True)

    @handle_errors("disabling content management", default_return=None)
    def disable_content_management(self) -> None:
        """Disable content management controls and reset the category combo."""
        self._set_content_controls_enabled(False)
        self.ui.comboBox_user_categories.clear()
        self.ui.comboBox_user_categories.addItem(CATEGORY_COMBO_PLACEHOLDER)

    @handle_errors("setting content management enabled state", default_return=None)
    def _set_content_controls_enabled(self, enabled: bool) -> None:
        """Set all user/content action controls to the same enabled state."""
        for widget in [
            self.ui.pushButton_communication_settings,
            self.ui.pushButton_personalization,
            self.ui.pushButton_phrase_settings,
            self.ui.pushButton_google_health,
            self.ui.pushButton_category_management,
            self.ui.pushButton_checkin_settings,
            self.ui.pushButton_task_management,
            self.ui.pushButton_task_crud,
            self.ui.pushButton_user_analytics,
            self.ui.pushButton_run_user_scheduler,
            self.ui.groupBox_category_actions,
            self.ui.groupBox_user_actions,
        ]:
            widget.setEnabled(enabled)
