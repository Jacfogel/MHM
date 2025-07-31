from PySide6.QtWidgets import QDialog, QMessageBox, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox, QDateEdit, QTimeEdit, QCheckBox, QPushButton
from PySide6.QtCore import Qt, QDate, QTime
from ui.generated.task_edit_dialog_pyqt import Ui_Dialog_task_edit

# Import core functionality
from tasks.task_management import create_task, update_task
from core.error_handling import handle_errors
from core.logger import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)

class TaskEditDialog(QDialog):
    """Dialog for creating or editing tasks."""
    
    def __init__(self, parent=None, user_id=None, task_data=None):
        """Initialize the task edit dialog."""
        super().__init__(parent)
        self.user_id = user_id
        self.task_data = task_data or {}
        self.is_edit = bool(task_data)
        self.reminder_periods = []
        
        self.ui = Ui_Dialog_task_edit()
        self.ui.setupUi(self)
        
        self.setup_ui()
        self.setup_connections()
        self.load_task_data()
    
    def setup_ui(self):
        """Setup the UI components."""
        # Set dialog title
        title = "Edit Task" if self.is_edit else "Add New Task"
        self.setWindowTitle(title)
        self.ui.label_task_edit_header.setText(title)
        
        # Set default date to today
        self.ui.dateEdit_task_due_date.setDate(QDate.currentDate())
        
        # Set default time to current time
        current_time = QTime.currentTime()
        self.ui.timeEdit_task_due_time.setTime(current_time)
        
        # Set default priority to Medium
        self.ui.comboBox_task_priority.setCurrentText("Medium")
        
        # Initially disable reminder periods section
        self.ui.widget_reminder_periods.setEnabled(False)
    
    def setup_connections(self):
        """Setup signal connections."""
        # Connect checkbox to enable/disable reminder periods
        self.ui.checkBox_enable_reminders.toggled.connect(self.ui.widget_reminder_periods.setEnabled)
        
        # Connect add reminder period button
        self.ui.pushButton_add_reminder_period.clicked.connect(self.add_reminder_period)
        
        # Connect dialog buttons
        self.ui.buttonBox_task_edit.accepted.connect(self.save_task)
        self.ui.buttonBox_task_edit.rejected.connect(self.reject)
    
    def load_task_data(self):
        """Load existing task data into the form."""
        if not self.task_data:
            return
        
        # Load basic task data
        self.ui.lineEdit_task_title.setText(self.task_data.get('title', ''))
        self.ui.textEdit_task_description.setPlainText(self.task_data.get('description', ''))
        self.ui.lineEdit_task_category.setText(self.task_data.get('category', ''))
        
        # Set priority
        priority = self.task_data.get('priority', 'medium')
        if priority:
            priority = priority.capitalize()
            index = self.ui.comboBox_task_priority.findText(priority)
            if index >= 0:
                self.ui.comboBox_task_priority.setCurrentIndex(index)
        
        # Set due date
        due_date = self.task_data.get('due_date')
        if due_date:
            try:
                date = QDate.fromString(due_date, 'yyyy-MM-dd')
                if date.isValid():
                    self.ui.dateEdit_task_due_date.setDate(date)
            except Exception:
                pass
        
        # Set due time
        due_time = self.task_data.get('due_time')
        if due_time:
            try:
                time = QTime.fromString(due_time, 'HH:mm')
                if time.isValid():
                    self.ui.timeEdit_task_due_time.setTime(time)
            except Exception:
                pass
        
        # Load reminder periods
        reminder_periods = self.task_data.get('reminder_periods', [])
        if reminder_periods:
            self.ui.checkBox_enable_reminders.setChecked(True)
            self.reminder_periods = reminder_periods.copy()
            self.render_reminder_periods()
    
    def add_reminder_period(self):
        """Add a new reminder period."""
        self.reminder_periods.append({
            'date': '',
            'start_time': '',
            'end_time': ''
        })
        self.render_reminder_periods()
    
    def render_reminder_periods(self):
        """Render the reminder periods in the UI."""
        # Clear existing widgets
        layout = self.ui.verticalLayout_scrollAreaWidgetContents_reminder_periods
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Add reminder period widgets
        for i, period in enumerate(self.reminder_periods):
            self.render_reminder_period_row(i, period)
    
    def render_reminder_period_row(self, index, period):
        """Render a single reminder period row."""
        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        
        # Date field
        row_layout.addWidget(QLabel("Date:"))
        date_edit = QDateEdit()
        date_edit.setCalendarPopup(True)
        if period.get('date'):
            try:
                date = QDate.fromString(period['date'], 'yyyy-MM-dd')
                if date.isValid():
                    date_edit.setDate(date)
            except Exception:
                pass
        row_layout.addWidget(date_edit)
        
        # Start time fields
        row_layout.addWidget(QLabel("Start:"))
        start_hour = QComboBox()
        start_hour.addItems([''] + [f"{h:02d}" for h in range(1, 13)])
        start_minute = QComboBox()
        start_minute.addItems([''] + [f"{m:02d}" for m in range(0, 60, 5)])
        start_ampm = QComboBox()
        start_ampm.addItems(['', 'AM', 'PM'])
        
        # Set start time values
        start_time = period.get('start_time', '')
        if start_time:
            try:
                h, m = map(int, start_time.split(':'))
                start_ampm.setCurrentText('AM' if h < 12 or h == 24 else 'PM')
                h12 = h % 12
                if h12 == 0: h12 = 12
                start_hour.setCurrentText(f"{h12:02d}")
                start_minute.setCurrentText(f"{m:02d}")
            except Exception:
                pass
        
        row_layout.addWidget(start_hour)
        row_layout.addWidget(QLabel(":"))
        row_layout.addWidget(start_minute)
        row_layout.addWidget(start_ampm)
        
        # End time fields
        row_layout.addWidget(QLabel("End:"))
        end_hour = QComboBox()
        end_hour.addItems([''] + [f"{h:02d}" for h in range(1, 13)])
        end_minute = QComboBox()
        end_minute.addItems([''] + [f"{m:02d}" for m in range(0, 60, 5)])
        end_ampm = QComboBox()
        end_ampm.addItems(['', 'AM', 'PM'])
        
        # Set end time values
        end_time = period.get('end_time', '')
        if end_time:
            try:
                h, m = map(int, end_time.split(':'))
                end_ampm.setCurrentText('AM' if h < 12 or h == 24 else 'PM')
                h12 = h % 12
                if h12 == 0: h12 = 12
                end_hour.setCurrentText(f"{h12:02d}")
                end_minute.setCurrentText(f"{m:02d}")
            except Exception:
                pass
        
        row_layout.addWidget(end_hour)
        row_layout.addWidget(QLabel(":"))
        row_layout.addWidget(end_minute)
        row_layout.addWidget(end_ampm)
        
        # Delete button
        delete_btn = QPushButton("Delete")
        delete_btn.clicked.connect(lambda: self.delete_reminder_period(index))
        row_layout.addWidget(delete_btn)
        
        # Store widgets for later access
        period['__widgets'] = {
            'date': date_edit,
            'start_hour': start_hour,
            'start_minute': start_minute,
            'start_ampm': start_ampm,
            'end_hour': end_hour,
            'end_minute': end_minute,
            'end_ampm': end_ampm
        }
        
        self.ui.verticalLayout_scrollAreaWidgetContents_reminder_periods.addWidget(row_widget)
    
    def delete_reminder_period(self, index):
        """Delete a reminder period."""
        if 0 <= index < len(self.reminder_periods):
            self.reminder_periods.pop(index)
            self.render_reminder_periods()
    
    def validate_form(self):
        """Validate the form data."""
        title = self.ui.lineEdit_task_title.text().strip()
        if not title:
            QMessageBox.warning(self, "Validation Error", "Title is required.")
            self.ui.lineEdit_task_title.setFocus()
            return False
        
        return True
    
    def collect_reminder_periods(self):
        """Collect reminder period data from the UI."""
        reminder_periods = []
        
        for period in self.reminder_periods:
            widgets = period.get('__widgets', {})
            
            date = widgets.get('date', QDateEdit()).date().toString('yyyy-MM-dd')
            start_hour = widgets.get('start_hour', QComboBox()).currentText()
            start_minute = widgets.get('start_minute', QComboBox()).currentText()
            start_ampm = widgets.get('start_ampm', QComboBox()).currentText()
            end_hour = widgets.get('end_hour', QComboBox()).currentText()
            end_minute = widgets.get('end_minute', QComboBox()).currentText()
            end_ampm = widgets.get('end_ampm', QComboBox()).currentText()
            
            # Only save if both start and end hour are set
            if date and start_hour and end_hour:
                try:
                    # Convert to 24-hour format
                    sh24 = int(start_hour)
                    sm = int(start_minute) if start_minute else 0
                    eh24 = int(end_hour)
                    em = int(end_minute) if end_minute else 0
                    
                    if start_ampm == 'PM' and sh24 != 12:
                        sh24 += 12
                    if start_ampm == 'AM' and sh24 == 12:
                        sh24 = 0
                    if end_ampm == 'PM' and eh24 != 12:
                        eh24 += 12
                    if end_ampm == 'AM' and eh24 == 12:
                        eh24 = 0
                    
                    reminder_periods.append({
                        'date': date,
                        'start_time': f"{sh24:02d}:{sm:02d}",
                        'end_time': f"{eh24:02d}:{em:02d}"
                    })
                except Exception:
                    continue
        
        return reminder_periods
    
    @handle_errors("saving task")
    def save_task(self):
        """Save the task data."""
        try:
            if not self.validate_form():
                return
            
            # Collect form data
            title = self.ui.lineEdit_task_title.text().strip()
            description = self.ui.textEdit_task_description.toPlainText().strip()
            category = self.ui.lineEdit_task_category.text().strip()
            priority = self.ui.comboBox_task_priority.currentText().lower()
            
            # Get due date and time
            due_date = self.ui.dateEdit_task_due_date.date().toString('yyyy-MM-dd')
            due_time = self.ui.timeEdit_task_due_time.time().toString('HH:mm')
            
            # Collect reminder periods if enabled
            reminder_periods = None
            if self.ui.checkBox_enable_reminders.isChecked():
                reminder_periods = self.collect_reminder_periods()
            
            # Prepare task data
            task_data = {
                'title': title,
                'description': description,
                'due_date': due_date,
                'due_time': due_time,
                'priority': priority,
                'category': category
            }
            
            if reminder_periods:
                task_data['reminder_periods'] = reminder_periods
            
            # Save task
            if self.is_edit:
                # Update existing task
                task_id = self.task_data.get('task_id')
                if update_task(self.user_id, task_id, task_data):
                    QMessageBox.information(self, "Success", "Task updated successfully!")
                    self.accept()
                else:
                    QMessageBox.critical(self, "Error", "Failed to update task.")
            else:
                # Create new task
                task_id = create_task(
                    self.user_id,
                    title,
                    description,
                    due_date,
                    due_time,
                    priority,
                    category,
                    reminder_periods
                )
                if task_id:
                    QMessageBox.information(self, "Success", "Task created successfully!")
                    self.accept()
                else:
                    QMessageBox.critical(self, "Error", "Failed to create task.")
                    
        except Exception as e:
            logger.error(f"Error saving task: {e}")
            QMessageBox.critical(self, "Error", f"Failed to save task: {e}") 