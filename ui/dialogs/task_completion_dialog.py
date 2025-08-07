from PySide6.QtWidgets import QDialog, QMessageBox, QButtonGroup
from PySide6.QtCore import Qt, QDate, QTime
from ui.generated.task_completion_dialog_pyqt import Ui_Dialog_task_completion

# Import core functionality
from core.error_handling import handle_errors
from core.logger import setup_logging, get_logger, get_component_logger

setup_logging()
logger = get_logger(__name__)
dialog_logger = get_component_logger('main')

class TaskCompletionDialog(QDialog):
    """Dialog for specifying task completion details."""
    
    def __init__(self, parent=None, task_title=""):
        """Initialize the task completion dialog."""
        super().__init__(parent)
        self.task_title = task_title
        
        self.ui = Ui_Dialog_task_completion()
        self.ui.setupUi(self)
        
        self.setup_ui()
        self.setup_connections()
    
    def setup_ui(self):
        """Setup the UI components."""
        # Set completion date to today
        self.ui.dateEdit_completion_date.setDate(QDate.currentDate())
        
        # Setup completion time components
        self.setup_completion_time_components()
        
        # Update header with task title
        if self.task_title:
            self.ui.label_task_completion_header.setText(f"When did you complete '{self.task_title}'?")
    
    def setup_completion_time_components(self):
        """Setup the completion time input components."""
        # Populate hour combo box (1-12)
        self.ui.comboBox_completion_hour.clear()
        self.ui.comboBox_completion_hour.addItems([f"{h:02d}" for h in range(1, 13)])
        
        # Populate minute combo box (0, 15, 30, 45)
        self.ui.comboBox_completion_minute.clear()
        self.ui.comboBox_completion_minute.addItems([f"{m:02d}" for m in [0, 15, 30, 45]])
        
        # Setup AM/PM radio buttons
        self.completion_am_pm_group = QButtonGroup(self)
        self.completion_am_pm_group.addButton(self.ui.radioButton_completion_am)
        self.completion_am_pm_group.addButton(self.ui.radioButton_completion_pm)
        
        # Set to current time
        current_time = QTime.currentTime()
        hour_12 = current_time.hour() % 12
        if hour_12 == 0: hour_12 = 12
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
    
    def setup_connections(self):
        """Setup signal connections."""
        # Connect dialog buttons
        self.ui.buttonBox_task_completion.accepted.connect(self.accept)
        self.ui.buttonBox_task_completion.rejected.connect(self.reject)
    
    def get_completion_date(self):
        """Get completion date as string."""
        return self.ui.dateEdit_completion_date.date().toString('yyyy-MM-dd')
    
    def get_completion_time(self):
        """Get completion time as 24-hour format string."""
        hour = int(self.ui.comboBox_completion_hour.currentText())
        minute = int(self.ui.comboBox_completion_minute.currentText())
        is_pm = self.ui.radioButton_completion_pm.isChecked()
        
        # Convert to 24-hour format
        if is_pm and hour != 12:
            hour += 12
        elif not is_pm and hour == 12:
            hour = 0
        
        return f"{hour:02d}:{minute:02d}"
    
    def get_completion_notes(self):
        """Get completion notes."""
        return self.ui.textEdit_completion_notes.toPlainText().strip()
    
    def get_completion_data(self):
        """Get all completion data as a dictionary."""
        return {
            'completion_date': self.get_completion_date(),
            'completion_time': self.get_completion_time(),
            'completion_notes': self.get_completion_notes()
        } 