# checkin_management_dialog.py - Check-in management dialog implementation

"""Check-in management dialog implementation."""

# PySide6 imports
from PySide6.QtWidgets import QDialog, QMessageBox, QWidget
from PySide6.QtCore import Signal

# Set up logging
from core.logger import setup_logging, get_component_logger

setup_logging()
logger = get_component_logger("ui")
dialog_logger = logger

# Import core functionality
from core.schedule_management import set_schedule_periods, clear_schedule_periods_cache
from core.user_data_handlers import update_user_preferences, update_user_account
from core.user_data_handlers import get_user_data
from core.error_handling import handle_errors
from core.user_data_validation import validate_schedule_periods

# Import widget
from ui.widgets.checkin_settings_widget import CheckinSettingsWidget
from ui.generated.checkin_management_dialog_pyqt import Ui_Dialog_checkin_management


class CheckinManagementDialog(QDialog):
    """Dialog for managing check-in settings."""

    user_changed = Signal()

    @handle_errors("initializing checkin management dialog", default_return=None)
    def __init__(self, parent=None, user_id=None):
        """Initialize the object."""
        try:
            super().__init__(parent)
            self.user_id = user_id
            self.ui = Ui_Dialog_checkin_management()
            self.ui.setupUi(self)
            # Load user account to set groupbox checked state
            checkins_enabled = False
            if self.user_id:
                user_data_result = get_user_data(self.user_id, "account")
                account = user_data_result.get("account") or {}
                features = account.get("features", {})
                checkins_enabled = features.get("checkins") == "enabled"
            self.ui.groupBox_checkBox_enable_checkins.setChecked(checkins_enabled)
            # Create check-in settings widget
            self.checkin_widget = CheckinSettingsWidget(self, self.user_id)

            # Get references to the group boxes
            questions_group = self.checkin_widget.ui.groupBox_checkin_questions
            periods_group = self.checkin_widget.ui.groupBox_checkin_time_periods

            # Remove periods group from original layout (keep questions in widget for now)
            original_layout = (
                self.checkin_widget.ui.verticalLayout_Form_checkin_settings
            )
            original_layout.removeWidget(periods_group)

            # Hide periods in the widget (we'll show it in the frequency tab)
            periods_group.setVisible(False)

            # Add the entire widget to questions tab (so it stays active)
            questions_layout = self.ui.widget_placeholder_checkin_settings.layout()
            while questions_layout.count():
                item = questions_layout.takeAt(0)
                w = item.widget()
                if w:
                    w.setParent(None)
            questions_layout.addWidget(self.checkin_widget)

            # Show periods group in frequency tab
            periods_group.setVisible(True)
            frequency_layout = self.ui.widget_placeholder_frequency_settings.layout()
            while frequency_layout.count():
                item = frequency_layout.takeAt(0)
                w = item.widget()
                if w:
                    w.setParent(None)
            frequency_layout.addWidget(periods_group)
            # Connect Save/Cancel
            self.ui.buttonBox_save_cancel.accepted.connect(self.save_checkin_settings)
            self.ui.buttonBox_save_cancel.rejected.connect(self.reject)
            # Wire up groupbox checkbox logic
            self.ui.groupBox_checkBox_enable_checkins.toggled.connect(
                self.on_enable_checkins_toggled
            )
            self.on_enable_checkins_toggled(
                self.ui.groupBox_checkBox_enable_checkins.isChecked()
            )
        except Exception as e:
            logger.error(f"Error initializing checkin management dialog: {e}")
            raise

    @handle_errors("toggling checkins", default_return=None)
    def on_enable_checkins_toggled(self, checked):
        try:
            # Enable/disable all children except the groupbox itself
            for child in self.ui.groupBox_checkBox_enable_checkins.findChildren(
                QWidget
            ):
                if child is not self.ui.groupBox_checkBox_enable_checkins:
                    child.setEnabled(checked)

            # If check-ins are being enabled and no periods exist, create a default period
            if checked and not self.checkin_widget.period_widgets:
                logger.info(
                    "Check-ins enabled with no periods - creating default period"
                )
                self.checkin_widget.add_new_period()
        except Exception as e:
            logger.error(f"Error toggling checkins: {e}")
            raise

    @handle_errors("loading user checkin data", default_return=None)
    def load_user_checkin_data(self):
        """Load the user's current check-in settings"""
        if not self.user_id:
            return
        try:
            # Load user preferences
            prefs_result = get_user_data(self.user_id, "preferences")
            prefs = prefs_result.get("preferences") or {}
            checkin_settings = prefs.get("checkin_settings", {})
            self.checkin_widget.set_checkin_settings(checkin_settings)
        except Exception as e:
            logger.error(f"Error loading check-in data for user {self.user_id}: {e}")

    @handle_errors("saving checkin settings", default_return=False)
    def save_checkin_settings(self):
        """Save the check-in settings back to user preferences"""
        if not self.user_id:
            self.accept()
            return
        try:
            checkin_settings = self.checkin_widget.get_checkin_settings()
            time_periods = checkin_settings.get("time_periods", {})

            # Only validate periods if check-ins are enabled
            checkins_enabled = self.ui.groupBox_checkBox_enable_checkins.isChecked()

            if checkins_enabled:
                # Validate periods before saving
                is_valid, errors = validate_schedule_periods(time_periods, "check-ins")
                if not is_valid:
                    QMessageBox.warning(self, "Validation Error", errors[0])
                    return

                # Validate min/max question counts
                min_questions = checkin_settings.get("min_questions", 1)
                max_questions = checkin_settings.get("max_questions", 8)

                # Count always and sometimes questions
                questions = checkin_settings.get("questions", {})
                always_count = sum(
                    1 for q in questions.values() if q.get("always_include", False)
                )
                sometimes_count = sum(
                    1 for q in questions.values() if q.get("sometimes_include", False)
                )
                total_enabled = always_count + sometimes_count

                # Ensure at least one question is enabled if check-ins are enabled
                if total_enabled == 0:
                    QMessageBox.warning(
                        self,
                        "No Questions Enabled",
                        "Please enable at least one question (Always or Sometimes) before saving.",
                    )
                    return

                # Calculate minimum required
                # Minimum must be at least always_count (doesn't depend on sometimes questions)
                min_required = max(always_count, 1)

                # Calculate maximum allowed: if sometimes questions > 0, max is total_enabled - 1
                # Otherwise, max is total_enabled
                if sometimes_count > 0:
                    max_allowed = total_enabled - 1
                else:
                    max_allowed = total_enabled

                # Minimum maximum: if sometimes questions > 0, minimum max is always_count + 1
                # Otherwise, minimum max is just always_count
                if sometimes_count > 0:
                    min_maximum = always_count + 1
                else:
                    min_maximum = always_count
                min_maximum = max(
                    min_maximum, min_required
                )  # Must be at least min_required

                # Ensure max_allowed is at least min_maximum
                max_allowed = max(max_allowed, min_maximum)

                if min_questions < min_required:
                    QMessageBox.warning(
                        self,
                        "Invalid Minimum",
                        f"Minimum questions ({min_questions}) must be at least {min_required} "
                        f"(number of 'always' questions: {always_count}).",
                    )
                    return

                if max_questions < min_questions:
                    QMessageBox.warning(
                        self,
                        "Invalid Maximum",
                        f"Maximum questions ({max_questions}) must be >= minimum ({min_questions}).",
                    )
                    return

                if max_questions > max_allowed:
                    QMessageBox.warning(
                        self,
                        "Invalid Maximum",
                        f"Maximum questions ({max_questions}) cannot exceed {max_allowed} "
                        f"(total enabled questions: {total_enabled}"
                        + (
                            f", minus 1 because you have 'sometimes' questions enabled"
                            if sometimes_count > 0
                            else ""
                        )
                        + ").",
                    )
                    return

            # Note: We always save time periods, even when disabled, so users don't lose their work
            # If check-ins are disabled, the periods will be saved but not used by the system

            # Always validate duplicate names, regardless of enablement status
            period_names = [
                w.get_period_data().get("name")
                for w in self.checkin_widget.period_widgets
            ]
            if len(period_names) != len(set(period_names)):
                QMessageBox.warning(
                    self,
                    "Duplicate Names",
                    "Two or more time periods have the same name.\n\nPlease rename duplicates before saving.",
                )
                return

            # Save time periods to schedule management
            logger.info(
                f"Saving check-in time periods for user {self.user_id}: {time_periods}"
            )
            set_schedule_periods(self.user_id, "checkin", time_periods)
            clear_schedule_periods_cache(self.user_id, "checkin")

            # Get current preferences and update check-in settings
            prefs_result = get_user_data(self.user_id, "preferences")
            prefs = prefs_result.get("preferences") or {}

            # Preserve custom_questions if they exist
            existing_checkin_settings = prefs.get("checkin_settings", {})
            custom_questions = existing_checkin_settings.get("custom_questions", {})

            prefs["checkin_settings"] = {
                "questions": checkin_settings.get("questions", {}),
                "custom_questions": custom_questions,  # Preserve custom questions
                "min_questions": checkin_settings.get("min_questions", 1),
                "max_questions": checkin_settings.get("max_questions", 8),
            }

            # Save updated preferences
            update_user_preferences(self.user_id, prefs)

            # Update user account features
            user_data_result = get_user_data(self.user_id, "account")
            account = user_data_result.get("account") or {}
            if "features" not in account:
                account["features"] = {}
            account["features"]["checkins"] = (
                "enabled" if checkins_enabled else "disabled"
            )
            update_user_account(self.user_id, account)

            QMessageBox.information(
                self, "Check-in Settings Saved", "Check-in settings saved successfully."
            )
            self.user_changed.emit()
            self.accept()

        except Exception as e:
            logger.error(f"Error saving check-in settings for user {self.user_id}: {e}")
            QMessageBox.critical(
                self, "Error", f"Failed to save check-in settings: {str(e)}"
            )

    @handle_errors("getting checkin settings", default_return={})
    def get_checkin_settings(self):
        """Get the current check-in settings."""
        try:
            return self.checkin_widget.get_checkin_settings()
        except Exception as e:
            logger.error(f"Error getting checkin settings: {e}")
            return {}

    @handle_errors("setting checkin settings", default_return=None)
    def set_checkin_settings(self, settings):
        """Set the check-in settings."""
        try:
            self.checkin_widget.set_checkin_settings(settings)
        except Exception as e:
            logger.error(f"Error setting checkin settings: {e}")
            raise
