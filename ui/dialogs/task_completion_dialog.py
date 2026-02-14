# task_completion_dialog.py
# pyright: ignore[reportAttributeAccessIssue, reportOptionalMemberAccess]

"""Task Completion Dialog"""

from PySide6.QtWidgets import QDialog, QButtonGroup
from PySide6.QtCore import QDate, QTime
from ui.generated.task_completion_dialog_pyqt import Ui_Dialog_task_completion

# Import core functionality
from core.error_handling import handle_errors
from core.logger import setup_logging, get_component_logger

setup_logging()
logger = get_component_logger("ui")
dialog_logger = logger


class TaskCompletionDialog(QDialog):
    """Dialog for specifying task completion details."""

    @handle_errors("initializing task completion dialog")
    def __init__(self, parent=None, task_title=""):
        """Initialize the task completion dialog."""
        try:
            super().__init__(parent)
            self.task_title = task_title or ""

            self.ui = Ui_Dialog_task_completion()
            self.ui.setupUi(self)

            self.setup_ui()
            self.setup_connections()
            logger.debug(
                f"Task completion dialog initialized for task: {self.task_title}"
            )
        except Exception as e:
            logger.error(f"Error initializing task completion dialog: {e}")
            raise

    @handle_errors("setting up task completion dialog UI")
    def setup_ui(self):
        """Setup the UI components."""
        try:
            # Set completion date to today
            self.ui.dateEdit_completion_date.setDate(QDate.currentDate())

            # Setup completion time components
            self.setup_completion_time_components()

            # Update header with task title
            if self.task_title:
                self.ui.label_task_completion_header.setText(
                    f"When did you complete '{self.task_title}'?"
                )

            logger.debug("Task completion dialog UI setup completed")
        except Exception as e:
            logger.error(f"Error setting up task completion dialog UI: {e}")
            raise

    @handle_errors("setting up completion time components")
    def setup_completion_time_components(self):
        """Setup the completion time input components."""
        try:
            # Populate hour combo box (1-12)
            self.ui.comboBox_completion_hour.clear()
            self.ui.comboBox_completion_hour.addItems(
                [f"{h:02d}" for h in range(1, 13)]
            )

            # Populate minute combo box (0, 15, 30, 45)
            self.ui.comboBox_completion_minute.clear()
            self.ui.comboBox_completion_minute.addItems(
                [f"{m:02d}" for m in [0, 15, 30, 45]]
            )

            # Setup AM/PM radio buttons
            self.completion_am_pm_group = QButtonGroup(self)
            self.completion_am_pm_group.addButton(self.ui.radioButton_completion_am)
            self.completion_am_pm_group.addButton(self.ui.radioButton_completion_pm)

            # Set to current time
            current_time = QTime.currentTime()
            hour_12 = current_time.hour() % 12
            if hour_12 == 0:
                hour_12 = 12
            self.ui.comboBox_completion_hour.setCurrentText(f"{hour_12:02d}")

            # Find closest minute option
            current_minute = current_time.minute()
            minute_options = [0, 15, 30, 45]
            closest_minute = min(minute_options, key=lambda x: abs(x - current_minute))
            self.ui.comboBox_completion_minute.setCurrentText(f"{closest_minute:02d}")

            # Set AM/PM
            if current_time.hour() >= 12:
                self.ui.radioButton_completion_pm.setChecked(True)
            else:
                self.ui.radioButton_completion_am.setChecked(True)

            logger.debug("Completion time components setup completed")
        except Exception as e:
            logger.error(f"Error setting up completion time components: {e}")
            raise

    @handle_errors("setting up task completion dialog connections")
    def setup_connections(self):
        """Setup signal connections."""
        try:
            # Connect dialog buttons
            self.ui.buttonBox_task_completion.accepted.connect(self.accept)
            self.ui.buttonBox_task_completion.rejected.connect(self.reject)
            logger.debug("Task completion dialog connections setup completed")
        except Exception as e:
            logger.error(f"Error setting up task completion dialog connections: {e}")
            raise

    @handle_errors("getting completion date", default_return="")
    def get_completion_date(self):
        """Get completion date as string."""
        try:
            date = self.ui.dateEdit_completion_date.date()
            if not date.isValid():
                logger.warning("Invalid completion date selected")
                return ""
            return date.toString("yyyy-MM-dd")
        except Exception as e:
            logger.error(f"Error getting completion date: {e}")
            return ""

    @handle_errors("getting completion time", default_return="00:00")
    def get_completion_time(self):
        """Get completion time as 24-hour format string."""
        try:
            hour_text = self.ui.comboBox_completion_hour.currentText()
            minute_text = self.ui.comboBox_completion_minute.currentText()

            if not hour_text or not minute_text:
                logger.warning("Invalid time selection")
                return "00:00"

            hour = int(hour_text)
            minute = int(minute_text)
            is_pm = self.ui.radioButton_completion_pm.isChecked()

            # Convert to 24-hour format
            if is_pm and hour != 12:
                hour += 12
            elif not is_pm and hour == 12:
                hour = 0

            return f"{hour:02d}:{minute:02d}"
        except (ValueError, AttributeError) as e:
            logger.error(f"Error getting completion time: {e}")
            return "00:00"

    @handle_errors("getting completion notes", default_return="")
    def get_completion_notes(self):
        """Get completion notes."""
        try:
            notes = self.ui.textEdit_completion_notes.toPlainText().strip()
            return notes
        except Exception as e:
            logger.error(f"Error getting completion notes: {e}")
            return ""

    @handle_errors("getting completion data", default_return={})
    def get_completion_data(self):
        """Get all completion data as a dictionary."""
        try:
            data = {
                "completion_date": self.get_completion_date(),
                "completion_time": self.get_completion_time(),
                "completion_notes": self.get_completion_notes(),
            }
            logger.debug(f"Retrieved completion data: {data}")
            return data
        except Exception as e:
            logger.error(f"Error getting completion data: {e}")
            return {
                "completion_date": "",
                "completion_time": "00:00",
                "completion_notes": "",
            }
