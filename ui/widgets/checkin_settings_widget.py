# checkin_settings_widget.py - Check-in settings widget implementation

from PySide6.QtWidgets import (
    QWidget,
    QMessageBox,
    QCheckBox,
    QHBoxLayout,
    QPushButton,
    QVBoxLayout,
    QGroupBox,
    QLabel,
    QSpinBox,
    QComboBox,
    QFormLayout,
)
from PySide6.QtCore import Qt
from ui.generated.checkin_settings_widget_pyqt import Ui_Form_checkin_settings

# Import core functionality
from core.ui_management import (
    load_period_widgets_for_category,
    collect_period_data_from_widgets,
)
from core.user_data_handlers import get_user_data
from core.error_handling import handle_errors
from core.logger import setup_logging, get_component_logger

# Import our period row widget
from ui.widgets.period_row_widget import PeriodRowWidget

setup_logging()
logger = get_component_logger("ui")
widget_logger = logger


class CheckinSettingsWidget(QWidget):
    """Widget for check-in settings configuration."""

    @handle_errors("initializing checkin settings widget")
    def __init__(self, parent=None, user_id=None):
        """Initialize the object."""
        super().__init__(parent)
        self.user_id = user_id
        self.ui = Ui_Form_checkin_settings()
        self.ui.setupUi(self)
        # Initialize data structures
        self.period_widgets = []
        self.deleted_periods = []  # For undo functionality
        self.deleted_questions = []  # For undo functionality
        # Track dynamically created question checkboxes (for new questions and custom questions)
        self.dynamic_question_checkboxes = (
            {}
        )  # question_key -> (always_checkbox, sometimes_checkbox, edit_button, delete_button, container_widget)
        # Track always/sometimes checkboxes for hardcoded questions too
        self.question_always_checkboxes = {}  # question_key -> QCheckBox (Always)
        self.question_sometimes_checkboxes = {}  # question_key -> QCheckBox (Sometimes)
        # Track category group boxes
        self.category_group_boxes = {}  # category_key -> QGroupBox

        # Initialize min/max question count controls
        self.min_questions_spinbox = None
        self.max_questions_spinbox = None
        self._adjusting_from_max = False  # Flag to prevent validation from interfering
        self._setup_question_count_controls()

        self.setup_connections()
        self.load_existing_data()
        self.ui.scrollAreaWidgetContents_checkin_time_periods.setVisible(True)

    @handle_errors("handling show event")
    def showEvent(self, event):
        """
        Handle widget show event.

        Called when the widget becomes visible. Re-validate question counts to ensure
        spinboxes have correct ranges when the dialog is shown.

        Args:
            event: The show event object
        """
        super().showEvent(event)
        # Re-validate to ensure spinboxes have correct ranges when dialog is shown
        if self.min_questions_spinbox and self.max_questions_spinbox:
            self._validate_question_counts()

    @handle_errors("setting up connections")
    def setup_connections(self):
        """Setup signal connections."""
        # Connect time period buttons
        self.ui.pushButton_add_new_checkin_time_period.clicked.connect(
            lambda: self.add_new_period()
        )
        self.ui.pushButton_undo_last__checkin_time_period_delete.clicked.connect(
            self.undo_last_time_period_delete
        )
        # Connect question buttons
        self.ui.pushButton_add_new_checkin_question.clicked.connect(
            self.add_new_question
        )
        self.ui.pushButton_undo_last_checkin_question_delete.clicked.connect(
            self.undo_last_question_delete
        )

        # Connect question checkboxes
        self.connect_question_checkboxes()

    @handle_errors("connecting question checkboxes")
    def connect_question_checkboxes(self):
        """Connect all question checkboxes to track changes."""
        # Note: All checkboxes (always/sometimes) are now created dynamically
        # and connected in set_question_checkboxes when they're created
        pass

    @handle_errors("setting up question count controls")
    def _setup_question_count_controls(self):
        """Add min/max question count controls below the questions list."""
        # Create a group box for question count configuration
        self.count_group = QGroupBox("Question Count Settings")
        count_layout = QFormLayout(self.count_group)
        count_layout.setSpacing(8)

        # Min questions spinbox
        self.min_questions_spinbox = QSpinBox()
        self.min_questions_spinbox.setMinimum(1)
        self.min_questions_spinbox.setMaximum(50)
        self.min_questions_spinbox.setValue(1)
        self.min_questions_spinbox.setToolTip(
            "Minimum number of questions to ask per check-in. Must be at least the number of 'always include' questions (+1 if any 'sometimes' questions are enabled)."
        )
        count_layout.addRow("Minimum Questions:", self.min_questions_spinbox)

        # Max questions spinbox
        self.max_questions_spinbox = QSpinBox()
        self.max_questions_spinbox.setMinimum(1)
        self.max_questions_spinbox.setMaximum(50)
        self.max_questions_spinbox.setValue(8)
        self.max_questions_spinbox.setToolTip(
            "Maximum number of questions to ask per check-in. Must be >= minimum and <= total enabled questions."
        )
        count_layout.addRow("Maximum Questions:", self.max_questions_spinbox)

        # Connect spinboxes to validate each other and adjust dynamically
        self.min_questions_spinbox.valueChanged.connect(self._on_min_changed)
        self.max_questions_spinbox.valueChanged.connect(self._on_max_changed)

        # Add to questions group box layout (below the scroll area)
        questions_layout = self.ui.verticalLayout_groupBox_checkin_questions
        questions_layout.addWidget(self.count_group)

    @handle_errors("validating question counts")
    def _validate_question_counts(self, skip_min_adjust=False):
        """Validate min/max question counts based on enabled questions.

        Args:
            skip_min_adjust: If True, don't adjust min value even if it's below min_required.
                             Used when max is reduced below min to allow min to match max.
        """
        if not self.min_questions_spinbox or not self.max_questions_spinbox:
            return

        # Count always and sometimes questions from current UI state
        always_count = 0
        sometimes_count = 0
        total_enabled = 0

        # Check dynamic checkboxes
        for question_key, widgets in self.dynamic_question_checkboxes.items():
            always_cb = widgets.get("always_checkbox")
            sometimes_cb = widgets.get("sometimes_checkbox")

            if always_cb and always_cb.isChecked():
                always_count += 1
                total_enabled += 1
            elif sometimes_cb and sometimes_cb.isChecked():
                sometimes_count += 1
                total_enabled += 1

        # Calculate minimum required
        # Minimum must be at least always_count (doesn't depend on sometimes questions)
        min_required = max(always_count, 1)  # Absolute minimum is 1

        # Maximum allowed: if sometimes questions > 0, max is total_enabled - 1 (leave room for variety)
        # Otherwise, max is total_enabled
        if sometimes_count > 0 and total_enabled > 0:
            max_allowed = total_enabled - 1
        else:
            max_allowed = total_enabled if total_enabled > 0 else 50

        # Minimum maximum: if sometimes questions > 0, minimum max is always_count + 1
        # Otherwise, minimum max is just always_count (or current min, whichever is higher)
        if sometimes_count > 0:
            min_maximum = always_count + 1
        else:
            min_maximum = always_count
        min_maximum = max(min_maximum, min_required)  # Must be at least min_required

        # Ensure max_allowed is at least min_maximum
        max_allowed = max(max_allowed, min_maximum)

        # Store current values before updating ranges
        current_min = self.min_questions_spinbox.value()
        current_max = self.max_questions_spinbox.value()

        # Update min spinbox range (can go from min_required up to max_allowed)
        # But if skip_min_adjust is True, allow min to go below min_required temporarily
        if skip_min_adjust:
            # Allow min to go as low as 1 (absolute minimum) to match reduced max
            self.min_questions_spinbox.setMinimum(1)
        else:
            self.min_questions_spinbox.setMinimum(min_required)
        self.min_questions_spinbox.setMaximum(max_allowed)

        # Adjust current min value if needed, and adjust max if min exceeds it
        # Skip min adjustment if we're in the middle of adjusting from max change
        if not skip_min_adjust:
            if current_min < min_required:
                self.min_questions_spinbox.setValue(min_required)
                current_min = min_required
            elif current_min > max_allowed:
                self.min_questions_spinbox.setValue(max_allowed)
                current_min = max_allowed

        # If min was adjusted and now exceeds max, adjust max to match min
        if current_min > current_max:
            current_max = current_min

        # Update max spinbox range
        # Minimum max must be at least min_maximum (always_count + 1 if sometimes > 0, else always_count)
        # But also must be >= current min
        max_minimum = max(min_maximum, current_min)
        self.max_questions_spinbox.setMinimum(max_minimum)
        self.max_questions_spinbox.setMaximum(max_allowed)

        # Adjust current max value if needed
        if current_max < max_minimum:
            self.max_questions_spinbox.setValue(max_minimum)
        elif current_max > max_allowed:
            self.max_questions_spinbox.setValue(max_allowed)

    @handle_errors("handling min questions changed")
    def _on_min_changed(self, value):
        """Handle minimum questions value change - adjust max if needed."""
        if not self.max_questions_spinbox:
            return

        # If min exceeds max, adjust max to match min
        if value > self.max_questions_spinbox.value():
            self.max_questions_spinbox.setValue(value)

        # Revalidate to update ranges
        self._validate_question_counts()

    @handle_errors("handling max questions changed")
    def _on_max_changed(self, value):
        """Handle maximum questions value change - adjust min if needed."""
        if not self.min_questions_spinbox:
            return

        current_min = self.min_questions_spinbox.value()

        # If max is less than min, adjust min to match max
        if value < current_min:
            # Set flag to prevent validation from interfering
            self._adjusting_from_max = True

            # Block signals on both spinboxes to prevent recursive validation
            if self.min_questions_spinbox:
                self.min_questions_spinbox.blockSignals(True)
            if self.max_questions_spinbox:
                self.max_questions_spinbox.blockSignals(True)

            # Temporarily remove min's minimum constraint to allow it to go down
            if self.min_questions_spinbox:
                old_min_min = self.min_questions_spinbox.minimum()
                old_min_max = self.min_questions_spinbox.maximum()
                # Set min to allow it to go down to at least the new max value
                self.min_questions_spinbox.setMinimum(1)  # Absolute minimum
                self.min_questions_spinbox.setMaximum(max(value, old_min_max))
                # Set the value - this must happen after setting minimum to 1
                self.min_questions_spinbox.setValue(value)

            # Unblock signals
            if self.min_questions_spinbox:
                self.min_questions_spinbox.blockSignals(False)
            if self.max_questions_spinbox:
                self.max_questions_spinbox.blockSignals(False)

            # Revalidate, but skip min adjustment since we just set it
            self._validate_question_counts(skip_min_adjust=True)

            # Clear flag
            self._adjusting_from_max = False
        else:
            # Revalidate to update ranges
            self._validate_question_counts()

    @handle_errors("handling question toggle")
    def on_question_toggled(self, checked):
        """Handle question checkbox toggle."""
        # Validate question counts when questions are toggled
        self._validate_question_counts()

    @handle_errors("loading existing check-in data")
    def load_existing_data(self):
        """Load existing check-in data."""
        if not self.user_id:
            logger.info(
                "CheckinSettingsWidget: No user_id provided - creating new user mode"
            )
            # For new user creation, add a default period and set default questions
            self.add_new_period()
            self.set_question_checkboxes({})  # Use defaults
            return

        logger.info(
            f"CheckinSettingsWidget: Loading periods for user_id={self.user_id}"
        )
        # Use the new reusable function to load period widgets
        self.period_widgets = load_period_widgets_for_category(
            layout=self.ui.verticalLayout_scrollAreaWidgetContents_checkin_time_periods,
            user_id=self.user_id,
            category="checkin",
            parent_widget=self,
            widget_list=self.period_widgets,
            delete_callback=self.remove_period_row,
        )
        # Get user preferences
        prefs_result = get_user_data(self.user_id, "preferences")
        prefs = prefs_result.get("preferences") or {}
        checkin_settings = prefs.get("checkin_settings", {})
        questions = checkin_settings.get("questions", {})

        # Merge custom questions into questions dict if they're not already there
        # This ensures new custom questions appear with their saved always_include state
        from core.checkin_dynamic_manager import dynamic_checkin_manager

        custom_questions = dynamic_checkin_manager.get_custom_questions(self.user_id)
        for custom_key, custom_def in custom_questions.items():
            if custom_key not in questions:
                # New custom question - add it with its saved state
                questions[custom_key] = {
                    "enabled": custom_def.get("enabled", True),
                    "always_include": custom_def.get("always_include", True),
                    "sometimes_include": custom_def.get("sometimes_include", False),
                }

        # Set question checkboxes based on saved preferences FIRST
        # This ensures questions are loaded before we set min/max ranges
        self.set_question_checkboxes(questions)

        # Load min/max question counts AFTER questions are loaded
        if self.min_questions_spinbox:
            self.min_questions_spinbox.setValue(
                checkin_settings.get("min_questions", 1)
            )
        if self.max_questions_spinbox:
            self.max_questions_spinbox.setValue(
                checkin_settings.get("max_questions", 8)
            )

        # Validate to set proper ranges based on loaded questions
        self._validate_question_counts()

    @handle_errors("refreshing question display")
    def _refresh_question_display(self):
        """Refresh the question display from current in-memory state.

        Similar to tag_widget.refresh_tag_list() - updates display without reloading from preferences.
        """
        # Get current state from UI checkboxes
        current_questions = {}
        for question_key, widgets in self.dynamic_question_checkboxes.items():
            always_cb = widgets.get("always_checkbox")
            sometimes_cb = widgets.get("sometimes_checkbox")
            if always_cb or sometimes_cb:
                current_questions[question_key] = {
                    "always_include": always_cb.isChecked() if always_cb else False,
                    "sometimes_include": (
                        sometimes_cb.isChecked() if sometimes_cb else False
                    ),
                    "enabled": (always_cb.isChecked() if always_cb else False)
                    or (sometimes_cb.isChecked() if sometimes_cb else False),
                }

        # Rebuild display with current state
        self.set_question_checkboxes(current_questions)

    @handle_errors("setting question checkboxes")
    def set_question_checkboxes(self, questions):
        """Set question checkboxes based on saved preferences.

        Groups questions by category and creates Always/Sometimes checkboxes for each.
        """
        # Import the dynamic checkin manager
        from core.checkin_dynamic_manager import dynamic_checkin_manager

        # Get all available questions from the dynamic manager (include custom questions)
        available_questions = dynamic_checkin_manager.get_enabled_questions_for_ui(
            self.user_id
        )
        categories = dynamic_checkin_manager.get_categories()

        # Use QTimer to defer the update slightly to prevent blanking
        from PySide6.QtCore import QTimer

        scroll_widget = self.ui.widget_checkin_questions_container

        # Store the current scroll position
        scroll_area = self.ui.scrollArea_checkin_questions
        scroll_position = scroll_area.verticalScrollBar().value()

        # Hide the container widget (not the scroll area) during rebuild
        scroll_widget.setVisible(False)

        try:
            # Clear existing dynamic checkboxes and category groups
            self._clear_dynamic_question_checkboxes()
            self._clear_category_groups()

            # Group questions by category
            questions_by_category = {}
            for question_key, question_info in available_questions.items():
                category = question_info.get("category", "general")
                if category not in questions_by_category:
                    questions_by_category[category] = []
                questions_by_category[category].append((question_key, question_info))

            # Get the scroll area widget container (already retrieved above)

            # Clear existing layout if any
            existing_layout = scroll_widget.layout()
            if existing_layout:
                while existing_layout.count():
                    item = existing_layout.takeAt(0)
                    widget = item.widget()
                    if widget:
                        widget.setParent(None)
                        widget.deleteLater()

            # Create new vertical layout for categories
            scroll_layout = QVBoxLayout(scroll_widget)
            scroll_layout.setSpacing(10)
            scroll_layout.setContentsMargins(4, 4, 4, 4)

            # Create category groups - reorganized categories
            # Mood, Energy (includes sleep), Health/Medical, Activities/Habits/Growth
            category_order = ["mood", "energy", "health", "activities"]
            for category_key in category_order:
                if category_key not in questions_by_category:
                    continue

                # Create group box for this category
                category_info = categories.get(category_key, {})
                # Use titlecase for display
                category_name = category_info.get(
                    "name", category_key.replace("_", " ").title()
                )
                category_name = (
                    category_name.title()
                    if category_name
                    else category_key.replace("_", " ").title()
                )
                category_desc = category_info.get("description", "")

                group_box = QGroupBox(category_name)
                if category_desc:
                    group_box.setToolTip(category_desc)
                group_layout = QVBoxLayout(group_box)
                group_layout.setSpacing(4)
                group_layout.setContentsMargins(8, 8, 8, 8)

                # Add questions for this category
                for question_key, question_info in questions_by_category[category_key]:
                    # Get saved question data, or use defaults for new questions
                    question_data = questions.get(question_key, {})
                    # If question not in saved data but exists in available_questions, use defaults
                    if not question_data:
                        # New question (e.g., just added custom question) - use defaults
                        if question_key.startswith("custom_"):
                            # Custom question defaults to always enabled
                            question_data = {
                                "enabled": True,
                                "always_include": True,
                                "sometimes_include": False,
                            }
                        else:
                            # Predefined question - use enabled_by_default
                            question_data = {
                                "enabled": question_info.get(
                                    "enabled_by_default", False
                                ),
                                "always_include": False,
                                "sometimes_include": question_info.get(
                                    "enabled_by_default", False
                                ),
                            }
                    display_name = question_info.get("ui_display_name", question_key)

                    # Create question row
                    question_row = QWidget()
                    row_layout = QHBoxLayout(question_row)
                    row_layout.setContentsMargins(0, 2, 0, 2)
                    row_layout.setSpacing(8)

                    # Question name label with type hint
                    # Extract type hint if present in display_name, or add it based on question type
                    question_type = question_info.get("type", "unknown")
                    type_hints = {
                        "scale_1_5": " (1-5 scale)",
                        "yes_no": " (yes/no)",
                        "number": " (number)",
                        "optional_text": " (text)",
                        "time_pair": " (time pair)",
                    }
                    type_hint = type_hints.get(question_type, "")

                    # If display_name doesn't already have the hint, add it
                    if type_hint and not display_name.endswith(type_hint):
                        display_name_with_hint = display_name + type_hint
                    else:
                        display_name_with_hint = display_name

                    name_label = QLabel(display_name_with_hint)
                    name_label.setMinimumWidth(200)
                    row_layout.addWidget(name_label)

                    # Always checkbox
                    always_checkbox = QCheckBox("Always")
                    always_checkbox.setToolTip(
                        "Check this to always ask this question in every check-in"
                    )
                    always_checkbox.toggled.connect(
                        lambda checked: self._validate_question_counts()
                    )
                    always_checkbox.toggled.connect(
                        lambda checked, key=question_key: self._on_always_toggled(
                            key, checked
                        )
                    )
                    row_layout.addWidget(always_checkbox)

                    # Sometimes checkbox
                    sometimes_checkbox = QCheckBox("Sometimes")
                    sometimes_checkbox.setToolTip(
                        "Check this to sometimes include this question for variety (not asked every check-in)"
                    )
                    sometimes_checkbox.toggled.connect(
                        lambda checked: self._validate_question_counts()
                    )
                    sometimes_checkbox.toggled.connect(
                        lambda checked, key=question_key: self._on_sometimes_toggled(
                            key, checked
                        )
                    )
                    row_layout.addWidget(sometimes_checkbox)

                    # Set initial states
                    always_include = question_data.get("always_include", False)
                    sometimes_include = question_data.get(
                        "sometimes_include", False
                    ) or (not always_include and question_data.get("enabled", False))

                    always_checkbox.setChecked(always_include)
                    sometimes_checkbox.setChecked(
                        sometimes_include and not always_include
                    )

                    # For custom questions, add edit and delete buttons
                    edit_button = None
                    delete_button = None
                    if question_key.startswith("custom_"):
                        edit_button = QPushButton("Edit")
                        edit_button.setMaximumWidth(50)
                        edit_button.clicked.connect(
                            lambda checked=False, key=question_key: self._edit_custom_question(
                                key
                            )
                        )
                        row_layout.addWidget(edit_button)

                        delete_button = QPushButton("Delete")
                        delete_button.setMaximumWidth(60)
                        delete_button.clicked.connect(
                            lambda checked=False, key=question_key: self._delete_custom_question(
                                key
                            )
                        )
                        row_layout.addWidget(delete_button)

                    row_layout.addStretch()
                    group_layout.addWidget(question_row)

                    # Store references
                    self.dynamic_question_checkboxes[question_key] = {
                        "always_checkbox": always_checkbox,
                        "sometimes_checkbox": sometimes_checkbox,
                        "edit_button": edit_button,
                        "delete_button": delete_button,
                        "container": question_row,
                    }

                scroll_layout.addWidget(group_box)
                self.category_group_boxes[category_key] = group_box

            # Add stretch at the end
            scroll_layout.addStretch()
        finally:
            # Show the container widget again
            scroll_widget.setVisible(True)
            # Restore scroll position
            scroll_area.verticalScrollBar().setValue(scroll_position)
            # Force immediate repaint
            scroll_widget.repaint()
            scroll_area.repaint()

    @handle_errors("handling always checkbox toggle")
    def _on_always_toggled(self, question_key: str, checked: bool):
        """Handle always checkbox toggle - ensure sometimes is unchecked if always is checked."""
        widgets = self.dynamic_question_checkboxes.get(question_key)
        if widgets and widgets.get("sometimes_checkbox"):
            if checked:
                widgets["sometimes_checkbox"].setChecked(False)

    @handle_errors("handling sometimes checkbox toggle")
    def _on_sometimes_toggled(self, question_key: str, checked: bool):
        """Handle sometimes checkbox toggle - ensure always is unchecked if sometimes is checked."""
        widgets = self.dynamic_question_checkboxes.get(question_key)
        if widgets and widgets.get("always_checkbox"):
            if checked:
                widgets["always_checkbox"].setChecked(False)

    @handle_errors("clearing category groups")
    def _clear_category_groups(self):
        """Remove all category group boxes."""
        scroll_widget = self.ui.widget_checkin_questions_container
        scroll_layout = scroll_widget.layout()
        if scroll_layout:
            while scroll_layout.count():
                item = scroll_layout.takeAt(0)
                widget = item.widget()
                if widget:
                    widget.setParent(None)
                    widget.deleteLater()
        self.category_group_boxes.clear()

    @handle_errors("clearing dynamic question checkboxes")
    def _clear_dynamic_question_checkboxes(self):
        """Remove all dynamically created question checkboxes."""
        for question_key, widgets in list(self.dynamic_question_checkboxes.items()):
            container = widgets.get("container")
            if container:
                container.setParent(None)
                container.deleteLater()

        self.dynamic_question_checkboxes.clear()
        self.question_always_checkboxes.clear()
        self.question_sometimes_checkboxes.clear()

    @handle_errors("getting default question state")
    def get_default_question_state(self, question_key):
        """Get default enabled state for a question."""
        # Import the dynamic checkin manager
        from core.checkin_dynamic_manager import dynamic_checkin_manager

        # Get the default enabled state from the dynamic manager (include custom questions)
        available_questions = dynamic_checkin_manager.get_enabled_questions_for_ui(
            self.user_id
        )
        question_data = available_questions.get(question_key, {})
        return question_data.get("enabled", False)

    @handle_errors("finding lowest available period number")
    def find_lowest_available_period_number(self):
        """Find the lowest available integer (2+) that's not currently used in period names."""
        used_numbers = set()

        # Check existing period widgets
        for widget in self.period_widgets:
            period_name = widget.get_period_data().get("name", "")
            # Extract number from names like "Check-in Reminder 2", "Check-in Reminder 3", etc.
            if "Check-in Reminder " in period_name:
                try:
                    number = int(period_name.split("Check-in Reminder ")[1])
                    used_numbers.add(number)
                except (ValueError, IndexError):
                    pass

        # Find the lowest available number starting from 2
        number = 2
        while number in used_numbers:
            number += 1

        return number

    @handle_errors("adding new check-in period")
    def add_new_period(self, checked=None, period_name=None, period_data=None):
        """Add a new time period using the PeriodRowWidget."""
        logger.info(
            f"CheckinSettingsWidget: add_new_period called with period_name={period_name}, period_data={period_data}"
        )
        if period_name is None:
            # Use descriptive name for default periods (title case for consistency with task widget)
            if len(self.period_widgets) == 0:
                period_name = "Check-in Reminder Default"
            else:
                # Find the lowest available number for new periods
                next_number = self.find_lowest_available_period_number()
                period_name = f"Check-in Reminder {next_number}"
        if not isinstance(period_name, str):
            logger.warning(
                f"CheckinSettingsWidget: period_name is not a string: {period_name} (type: {type(period_name)})"
            )
            period_name = str(period_name)
        if period_data is None:
            period_data = {
                "start_time": "18:00",
                "end_time": "20:00",
                "active": True,
                "days": ["ALL"],
            }
        # Defensive: ensure period_data is a dict
        if not isinstance(period_data, dict):
            logger.warning(
                f"CheckinSettingsWidget: period_data is not a dict: {period_data} (type: {type(period_data)})"
            )
            period_data = {
                "start_time": "18:00",
                "end_time": "20:00",
                "active": True,
                "days": ["ALL"],
            }
        # Create the period row widget
        period_widget = PeriodRowWidget(self, period_name, period_data)
        # Connect the delete signal
        period_widget.delete_requested.connect(self.remove_period_row)
        # Add to the scroll area layout
        layout = self.ui.verticalLayout_scrollAreaWidgetContents_checkin_time_periods
        layout.addWidget(period_widget)
        # Store reference
        self.period_widgets.append(period_widget)
        return period_widget

    @handle_errors("removing period row")
    def remove_period_row(self, row_widget):
        """Remove a period row and store it for undo."""
        # Prevent deletion of the last period
        if len(self.period_widgets) <= 1:
            QMessageBox.warning(
                self,
                "Cannot Delete Last Period",
                "You must have at least one time period. Please add another period before deleting this one.",
            )
            return

        # Store the deleted period data for undo
        if isinstance(row_widget, PeriodRowWidget):
            period_data = row_widget.get_period_data()
            deleted_data = {
                "period_name": period_data["name"],
                "start_time": period_data["start_time"],
                "end_time": period_data["end_time"],
                "active": period_data["active"],
                "days": period_data["days"],
            }
            self.deleted_periods.append(deleted_data)

        # Remove from layout and widget list
        layout = self.ui.verticalLayout_scrollAreaWidgetContents_checkin_time_periods
        layout.removeWidget(row_widget)
        row_widget.setParent(None)
        row_widget.deleteLater()

        if row_widget in self.period_widgets:
            self.period_widgets.remove(row_widget)

    @handle_errors("undoing last time period delete")
    def undo_last_time_period_delete(self):
        """Undo the last time period deletion."""
        if not self.deleted_periods:
            QMessageBox.information(self, "No Deletions", "No deletions to undo.")
            return

        # Get the last deleted period
        deleted_data = self.deleted_periods.pop()

        # Recreate the period
        period_data = {
            "start_time": deleted_data["start_time"],
            "end_time": deleted_data["end_time"],
            "active": deleted_data["active"],
            "days": deleted_data.get("days", ["ALL"]),
        }

        # Add it back
        self.add_new_period(
            period_name=deleted_data["period_name"], period_data=period_data
        )

    @handle_errors("adding new question")
    def add_new_question(self):
        """Add a new check-in question."""
        if not self.user_id:
            QMessageBox.warning(
                self, "No User", "Cannot add custom questions without a user ID."
            )
            return

        self._show_question_dialog()

    @handle_errors("showing question dialog")
    def _show_question_dialog(self, question_key=None, question_def=None):
        """Show dialog for adding or editing a custom question.

        Args:
            question_key: If provided, edit existing question; otherwise create new
            question_def: Existing question definition (for editing)
        """
        from PySide6.QtWidgets import (
            QDialog,
            QVBoxLayout,
            QHBoxLayout,
            QLabel,
            QLineEdit,
            QComboBox,
            QPushButton,
            QDialogButtonBox,
            QFormLayout,
            QGroupBox,
            QTextEdit,
        )
        from core.checkin_dynamic_manager import dynamic_checkin_manager

        # Create dialog
        dialog = QDialog(self)
        dialog.setWindowTitle(
            "Edit Custom Check-in Question"
            if question_key
            else "Add Custom Check-in Question"
        )
        dialog.resize(600, 500)  # Make it wider

        main_layout = QVBoxLayout(dialog)
        main_layout.setSpacing(10)

        # Template selection (only for new questions)
        if not question_key:
            template_group = QGroupBox("Start from Template (Optional)")
            template_layout = QVBoxLayout(template_group)

            template_combo = QComboBox()
            template_combo.addItem("-- Start from scratch --", None)

            templates = dynamic_checkin_manager.get_question_templates()
            for template_key, template_data in templates.items():
                display_name = template_data.get("ui_display_name", template_key)
                template_combo.addItem(display_name, template_key)

            template_layout.addWidget(template_combo)
            main_layout.addWidget(template_group)

            def on_template_selected(index):
                try:
                    if index > 0:  # Not "Start from scratch"
                        template_key = template_combo.currentData()
                        if template_key and template_key in templates:
                            template = templates[template_key]
                            # Get question text without type hints
                            question_text = template.get("question_text", "")
                            question_text_edit.setText(question_text)

                            # Get display name without type hints
                            display_name = template.get("ui_display_name", "")
                            # Remove type hint if present (e.g., "CPAP use (yes/no)" -> "CPAP use")
                            display_name = (
                                display_name.split(" (")[0]
                                if " (" in display_name
                                else display_name
                            )
                            display_name_edit.setText(display_name)

                            # Set type
                            type_key = template.get("type", "yes_no")
                            for i in range(type_combo.count()):
                                if type_combo.itemData(i) == type_key:
                                    type_combo.setCurrentIndex(i)
                                    break

                            # Set category
                            cat_key = template.get("category", "health")
                            for i in range(category_combo.count()):
                                if category_combo.itemData(i) == cat_key:
                                    category_combo.setCurrentIndex(i)
                                    break
                except Exception as e:
                    logger.error(
                        f"Error handling template selection: {e}", exc_info=True
                    )
                    # Show user-friendly error message
                    from PySide6.QtWidgets import QMessageBox

                    QMessageBox.warning(
                        dialog,
                        "Template Selection Error",
                        f"An error occurred while loading the template. Please try again or start from scratch.\n\nError: {str(e)}",
                    )

            template_combo.currentIndexChanged.connect(on_template_selected)

        # Form layout for question fields
        form_group = QGroupBox("Question Details")
        form_layout = QFormLayout(form_group)
        form_layout.setSpacing(8)
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        # Question text input with guidance
        question_text_edit = QTextEdit()
        question_text_edit.setMaximumHeight(60)
        question_text_edit.setPlaceholderText("Enter your question...")
        if question_def:
            question_text_edit.setText(question_def.get("question_text", ""))
        question_text_label = QLabel("Question Text:")
        question_text_hint = QLabel(
            "Use 'you' to match included questions (e.g., 'How are you feeling today?')"
        )
        question_text_hint.setStyleSheet(
            "color: gray; font-size: 9pt; margin-top: 2px;"
        )
        question_text_hint.setWordWrap(True)
        form_layout.addRow(question_text_label, question_text_edit)
        # Add hint with minimal spacing (empty label to align with form field)
        form_layout.addRow("", question_text_hint)

        # Question type selection with formatted options
        type_combo = QComboBox()
        type_options = {
            "scale_1_5": "Scale of 1 (Low) to 5 (High)",
            "yes_no": "Yes/No",
            "number": "Number",
            "optional_text": "Free Text (Optional)",
            "time_pair": "Time Pair (HH:MM)",
        }
        for type_key, type_display in type_options.items():
            type_combo.addItem(type_display, type_key)
        if question_def:
            type_key = question_def.get("type", "yes_no")
            for i in range(type_combo.count()):
                if type_combo.itemData(i) == type_key:
                    type_combo.setCurrentIndex(i)
                    break
        form_layout.addRow("Question Type:", type_combo)

        # Category selection with titlecase display
        category_combo = QComboBox()
        categories = dynamic_checkin_manager.get_categories()
        category_keys = (
            list(categories.keys())
            if categories
            else ["mood", "energy", "health", "activities"]
        )
        for cat_key in category_keys:
            cat_info = categories.get(cat_key, {})
            cat_name = cat_info.get("name", cat_key.replace("_", " ").title())
            cat_name = (
                cat_name.title() if cat_name else cat_key.replace("_", " ").title()
            )
            category_combo.addItem(cat_name, cat_key)
        if question_def:
            cat_key = question_def.get("category", "health")
            for i in range(category_combo.count()):
                if category_combo.itemData(i) == cat_key:
                    category_combo.setCurrentIndex(i)
                    break
        form_layout.addRow("Category:", category_combo)

        # Display name input with guidance
        display_name_edit = QLineEdit()
        display_name_edit.setPlaceholderText("Leave empty to use question text")
        if question_def:
            display_name = question_def.get("ui_display_name", "")
            # Remove type hint if present (for editing existing questions)
            display_name = (
                display_name.split(" (")[0] if " (" in display_name else display_name
            )
            display_name_edit.setText(display_name)
        display_name_label = QLabel("Display Name (for UI):")
        display_name_hint = QLabel(
            "Short name shown in the question list. Type hint will be added automatically."
        )
        display_name_hint.setStyleSheet("color: gray; font-size: 10pt;")
        form_layout.addRow(display_name_label, display_name_edit)
        form_layout.addRow("", display_name_hint)

        main_layout.addWidget(form_group)

        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        main_layout.addWidget(button_box)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            question_text = question_text_edit.toPlainText().strip()
            if not question_text:
                QMessageBox.warning(
                    self, "Empty Question", "Please enter a question text."
                )
                return

            question_type = type_combo.currentData()  # Get the actual type key
            category = category_combo.currentData()  # Get the actual category key
            display_name = display_name_edit.text().strip() or question_text

            # Use existing key if editing, otherwise generate new one
            if question_key:
                final_key = question_key
            else:
                import re

                final_key = re.sub(r"[^a-z0-9_]", "_", question_text.lower()[:50])
                final_key = f"custom_{final_key}"

                # Check if key already exists
                existing_custom = dynamic_checkin_manager.get_custom_questions(
                    self.user_id
                )
                counter = 1
                original_key = final_key
                while final_key in existing_custom:
                    final_key = f"{original_key}_{counter}"
                    counter += 1

            # Build validation rules based on type
            validation = {}
            if question_type == "scale_1_5":
                validation = {
                    "min": 1,
                    "max": 5,
                    "error_message": f"Please enter a number between 1 and 5 for {display_name}.",
                }
            elif question_type == "number":
                validation = {
                    "min": 0,
                    "max": 100,
                    "error_message": f"Please enter a number for {display_name}.",
                }
            elif question_type == "yes_no":
                validation = {
                    "error_message": f"Please answer with yes/no, y/n, or similar for {display_name}."
                }
            elif question_type == "optional_text":
                validation = {
                    "error_message": f"This is optional - you can just press enter to skip {display_name}."
                }
            elif question_type == "time_pair":
                validation = {
                    "error_message": f"Please provide both times in HH:MM format (e.g., '23:30' and '07:00') for {display_name}."
                }

            # Add type hint to display name (matching format of included questions)
            type_hints = {
                "scale_1_5": " (1-5 scale)",
                "yes_no": " (yes/no)",
                "number": " (number)",
                "optional_text": " (text)",
                "time_pair": " (time pair)",
            }
            type_hint = type_hints.get(question_type, "")
            if display_name and not display_name.endswith(type_hint):
                display_name_with_hint = display_name + type_hint
            else:
                display_name_with_hint = display_name

            # Create question definition
            # New questions default to always_include=True
            is_new_question = question_key is None
            new_question_def = {
                "type": question_type,
                "question_text": question_text,
                "ui_display_name": display_name_with_hint,  # Include type hint
                "category": category,
                "validation": validation,
                "enabled": True,  # Always enabled when created
                "always_include": (
                    True
                    if is_new_question
                    else question_def.get("always_include", False)
                ),  # Default to always for new questions
                "sometimes_include": False,  # Never sometimes for new questions
            }

            # Save the custom question
            if dynamic_checkin_manager.save_custom_question(
                self.user_id, final_key, new_question_def
            ):
                action = "updated" if question_key else "added"
                QMessageBox.information(
                    self,
                    f"Question {action.title()}",
                    f"Custom question '{display_name}' has been {action} successfully.\n\n"
                    "You can enable/disable it in the check-in questions list.",
                )
                # Preserve current min/max values
                current_min = (
                    self.min_questions_spinbox.value()
                    if self.min_questions_spinbox
                    else 1
                )
                current_max = (
                    self.max_questions_spinbox.value()
                    if self.max_questions_spinbox
                    else 8
                )

                # Get current state from UI and add the new question
                current_questions = {}
                for q_key, widgets in self.dynamic_question_checkboxes.items():
                    always_cb = widgets.get("always_checkbox")
                    sometimes_cb = widgets.get("sometimes_checkbox")
                    if always_cb or sometimes_cb:
                        current_questions[q_key] = {
                            "always_include": (
                                always_cb.isChecked() if always_cb else False
                            ),
                            "sometimes_include": (
                                sometimes_cb.isChecked() if sometimes_cb else False
                            ),
                            "enabled": (always_cb.isChecked() if always_cb else False)
                            or (sometimes_cb.isChecked() if sometimes_cb else False),
                        }

                # Add the new question with its saved state
                current_questions[final_key] = {
                    "enabled": new_question_def.get("enabled", True),
                    "always_include": new_question_def.get("always_include", True),
                    "sometimes_include": new_question_def.get(
                        "sometimes_include", False
                    ),
                }

                # Rebuild display with updated state (like tag_widget.refresh_tag_list())
                self.set_question_checkboxes(current_questions)

                # Validate to set proper ranges
                self._validate_question_counts()

                # Restore min/max values only if they're still within valid ranges
                if self.min_questions_spinbox:
                    min_valid = max(
                        self.min_questions_spinbox.minimum(),
                        min(current_min, self.min_questions_spinbox.maximum()),
                    )
                    self.min_questions_spinbox.setValue(min_valid)
                if self.max_questions_spinbox:
                    max_valid = max(
                        self.max_questions_spinbox.minimum(),
                        min(current_max, self.max_questions_spinbox.maximum()),
                    )
                    self.max_questions_spinbox.setValue(max_valid)

                # Final validation
                self._validate_question_counts()
            else:
                QMessageBox.critical(
                    self,
                    "Error",
                    f"Failed to save the custom question. Please try again.",
                )

    @handle_errors("editing custom question")
    def _edit_custom_question(self, question_key):
        """Edit an existing custom question."""
        from core.checkin_dynamic_manager import dynamic_checkin_manager

        custom_questions = dynamic_checkin_manager.get_custom_questions(self.user_id)
        if question_key not in custom_questions:
            QMessageBox.warning(
                self,
                "Question Not Found",
                f"Custom question '{question_key}' not found.",
            )
            return

        question_def = custom_questions[question_key]
        self._show_question_dialog(question_key, question_def)

    @handle_errors("deleting custom question")
    def _delete_custom_question(self, question_key):
        """Delete a custom question."""
        from core.checkin_dynamic_manager import dynamic_checkin_manager

        custom_questions = dynamic_checkin_manager.get_custom_questions(self.user_id)
        if question_key not in custom_questions:
            QMessageBox.warning(
                self,
                "Question Not Found",
                f"Custom question '{question_key}' not found.",
            )
            return

        question_def = custom_questions[question_key]
        display_name = question_def.get("ui_display_name", question_key)

        reply = QMessageBox.question(
            self,
            "Delete Question",
            f"Are you sure you want to delete the custom question '{display_name}'?\n\n"
            "You can use the 'Undo Last Delete' button to restore it if needed.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            if dynamic_checkin_manager.delete_custom_question(
                self.user_id, question_key
            ):
                QMessageBox.information(
                    self,
                    "Question Deleted",
                    f"Custom question '{display_name}' has been deleted.",
                )
                # Store for undo
                self.deleted_questions.append(
                    {"key": question_key, "definition": question_def}
                )
                # Preserve current min/max values
                current_min = (
                    self.min_questions_spinbox.value()
                    if self.min_questions_spinbox
                    else 1
                )
                current_max = (
                    self.max_questions_spinbox.value()
                    if self.max_questions_spinbox
                    else 8
                )

                # Get current state from UI and remove the deleted question
                current_questions = {}
                for q_key, widgets in self.dynamic_question_checkboxes.items():
                    # Skip the deleted question
                    if q_key == question_key:
                        continue
                    always_cb = widgets.get("always_checkbox")
                    sometimes_cb = widgets.get("sometimes_checkbox")
                    if always_cb or sometimes_cb:
                        current_questions[q_key] = {
                            "always_include": (
                                always_cb.isChecked() if always_cb else False
                            ),
                            "sometimes_include": (
                                sometimes_cb.isChecked() if sometimes_cb else False
                            ),
                            "enabled": (always_cb.isChecked() if always_cb else False)
                            or (sometimes_cb.isChecked() if sometimes_cb else False),
                        }

                # Rebuild display with updated state (like tag_widget.refresh_tag_list())
                self.set_question_checkboxes(current_questions)

                # Validate to set proper ranges
                self._validate_question_counts()

                # Restore min/max values only if they're still within valid ranges
                if self.min_questions_spinbox:
                    min_valid = max(
                        self.min_questions_spinbox.minimum(),
                        min(current_min, self.min_questions_spinbox.maximum()),
                    )
                    self.min_questions_spinbox.setValue(min_valid)
                if self.max_questions_spinbox:
                    max_valid = max(
                        self.max_questions_spinbox.minimum(),
                        min(current_max, self.max_questions_spinbox.maximum()),
                    )
                    self.max_questions_spinbox.setValue(max_valid)

                # Final validation
                self._validate_question_counts()
            else:
                QMessageBox.critical(
                    self,
                    "Error",
                    "Failed to delete the custom question. Please try again.",
                )

    @handle_errors("undoing last question delete")
    def undo_last_question_delete(self):
        """Undo the last question deletion."""
        if not self.deleted_questions:
            QMessageBox.information(
                self, "No Deletions", "No question deletions to undo."
            )
            return

        # Get the last deleted question
        deleted_question = self.deleted_questions.pop()
        question_key = deleted_question["key"]
        question_def = deleted_question["definition"]

        # Restore the question
        from core.checkin_dynamic_manager import dynamic_checkin_manager

        if dynamic_checkin_manager.save_custom_question(
            self.user_id, question_key, question_def
        ):
            display_name = question_def.get("ui_display_name", question_key)
            QMessageBox.information(
                self,
                "Question Restored",
                f"Custom question '{display_name}' has been restored.",
            )
            # Preserve current min/max values
            current_min = (
                self.min_questions_spinbox.value() if self.min_questions_spinbox else 1
            )
            current_max = (
                self.max_questions_spinbox.value() if self.max_questions_spinbox else 8
            )

            # Get current state from UI and add the restored question
            current_questions = {}
            for q_key, widgets in self.dynamic_question_checkboxes.items():
                always_cb = widgets.get("always_checkbox")
                sometimes_cb = widgets.get("sometimes_checkbox")
                if always_cb or sometimes_cb:
                    current_questions[q_key] = {
                        "always_include": always_cb.isChecked() if always_cb else False,
                        "sometimes_include": (
                            sometimes_cb.isChecked() if sometimes_cb else False
                        ),
                        "enabled": (always_cb.isChecked() if always_cb else False)
                        or (sometimes_cb.isChecked() if sometimes_cb else False),
                    }

            # Add the restored question with its saved state
            current_questions[question_key] = {
                "enabled": question_def.get("enabled", True),
                "always_include": question_def.get("always_include", True),
                "sometimes_include": question_def.get("sometimes_include", False),
            }

            # Rebuild display with updated state (like tag_widget.refresh_tag_list())
            self.set_question_checkboxes(current_questions)

            # Validate to set proper ranges
            self._validate_question_counts()

            # Restore min/max values only if they're still within valid ranges
            if self.min_questions_spinbox:
                min_valid = max(
                    self.min_questions_spinbox.minimum(),
                    min(current_min, self.min_questions_spinbox.maximum()),
                )
                self.min_questions_spinbox.setValue(min_valid)
            if self.max_questions_spinbox:
                max_valid = max(
                    self.max_questions_spinbox.minimum(),
                    min(current_max, self.max_questions_spinbox.maximum()),
                )
                self.max_questions_spinbox.setValue(max_valid)

            # Final validation
            self._validate_question_counts()
        else:
            QMessageBox.critical(
                self,
                "Error",
                "Failed to restore the custom question. Please try again.",
            )

    @handle_errors("getting check-in settings")
    def get_checkin_settings(self):
        """Get the current check-in settings."""
        # Use the new reusable function to collect period data
        time_periods = collect_period_data_from_widgets(self.period_widgets, "checkin")

        # Import the dynamic checkin manager
        from core.checkin_dynamic_manager import dynamic_checkin_manager

        # Get available questions from dynamic manager for labels (include custom questions)
        available_questions = dynamic_checkin_manager.get_enabled_questions_for_ui(
            self.user_id
        )

        # Get enabled state and always/sometimes from all question checkboxes
        questions = {}
        for question_key, widgets in self.dynamic_question_checkboxes.items():
            if question_key in available_questions:
                always_cb = widgets.get("always_checkbox")
                sometimes_cb = widgets.get("sometimes_checkbox")

                always_include = always_cb.isChecked() if always_cb else False
                sometimes_include = sometimes_cb.isChecked() if sometimes_cb else False
                enabled = always_include or sometimes_include

                questions[question_key] = {
                    "enabled": enabled,
                    "label": available_questions[question_key].get(
                        "ui_display_name", question_key
                    ),
                    "always_include": always_include,
                    "sometimes_include": sometimes_include,
                }

        # Get min/max question counts
        min_questions = (
            self.min_questions_spinbox.value() if self.min_questions_spinbox else 1
        )
        max_questions = (
            self.max_questions_spinbox.value() if self.max_questions_spinbox else 8
        )

        return {
            "time_periods": time_periods,
            "questions": questions,
            "min_questions": min_questions,
            "max_questions": max_questions,
        }

    @handle_errors("setting checkin settings")
    def set_checkin_settings(self, settings):
        """Set the check-in settings."""
        if not settings:
            return

        # Clear existing period widgets
        for widget in self.period_widgets:
            layout = (
                self.ui.verticalLayout_scrollAreaWidgetContents_checkin_time_periods
            )
            layout.removeWidget(widget)
            widget.setParent(None)
            widget.deleteLater()
        self.period_widgets.clear()

        # Add time periods
        time_periods = settings.get("time_periods", {})
        for period_name, period_data in time_periods.items():
            self.add_new_period(period_name, period_data)

        # Set questions
        questions = settings.get("questions", {})
        self.set_question_checkboxes(questions)

        # Set min/max question counts
        if self.min_questions_spinbox:
            min_questions = settings.get("min_questions", 1)
            self.min_questions_spinbox.setValue(min_questions)
        if self.max_questions_spinbox:
            max_questions = settings.get("max_questions", 8)
            self.max_questions_spinbox.setValue(max_questions)

        # Validate after setting values
        self._validate_question_counts()
