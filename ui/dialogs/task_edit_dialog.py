from PySide6.QtWidgets import QDialog, QMessageBox, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox, QDateEdit, QTimeEdit, QCheckBox, QPushButton, QListWidget, QListWidgetItem, QButtonGroup, QRadioButton
from PySide6.QtCore import Qt, QDate, QTime
from ui.generated.task_edit_dialog_pyqt import Ui_Dialog_task_edit

# Import core functionality
from tasks.task_management import create_task, update_task
from core.error_handling import handle_errors
from core.logger import setup_logging, get_logger
from ui.widgets.tag_widget import TagWidget

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
        
        # Load existing tags if editing
        if self.is_edit and self.task_data.get('tags'):
            self.selected_tags = self.task_data['tags'].copy()
        else:
            self.selected_tags = []
        
        self.ui = Ui_Dialog_task_edit()
        self.ui.setupUi(self)
        
        # Replace the existing tag widget with our TagWidget in selection mode
        self.tag_widget = TagWidget(self, user_id, mode="selection", selected_tags=self.selected_tags, title="Tags")
        layout = self.ui.verticalLayout_tags.layout()
        # Remove existing widgets
        while layout.count():
            item = layout.takeAt(0)
            w = item.widget()
            if w:
                w.setParent(None)
        layout.addWidget(self.tag_widget)
        
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
        
        # Setup priority combo box with None option
        self.ui.comboBox_task_priority.clear()
        self.ui.comboBox_task_priority.addItems(["None", "Low", "Medium", "High"])
        self.ui.comboBox_task_priority.setCurrentText("Medium")
        
        # Setup due time components
        self.setup_due_time_components()
        
        # Tags are now handled by TagSelectionWidget
        
        # Enable reminders by default
        self.ui.checkBox_enable_reminders.setChecked(True)
        
        # Enable reminder periods section by default since reminders are enabled
        self.ui.widget_reminder_periods.setEnabled(True)
    
    def setup_due_time_components(self):
        """Setup the due time input components."""
        # Populate hour combo box with blank option first, then 1-12
        self.ui.comboBox_due_time_hour.clear()
        self.ui.comboBox_due_time_hour.addItem("")  # Blank option
        self.ui.comboBox_due_time_hour.addItems([f"{h:02d}" for h in range(1, 13)])
        self.ui.comboBox_due_time_hour.setCurrentText("")  # Default to blank
        
        # Populate minute combo box with blank option first, then 0, 15, 30, 45
        self.ui.comboBox_due_time_minute.clear()
        self.ui.comboBox_due_time_minute.addItem("")  # Blank option
        self.ui.comboBox_due_time_minute.addItems([f"{m:02d}" for m in [0, 15, 30, 45]])
        self.ui.comboBox_due_time_minute.setCurrentText("")  # Default to blank
        
        # Setup AM/PM radio buttons
        self.due_time_am_pm_group = QButtonGroup(self)
        self.due_time_am_pm_group.addButton(self.ui.radioButton_due_time_am)
        self.due_time_am_pm_group.addButton(self.ui.radioButton_due_time_pm)
        self.ui.radioButton_due_time_am.setChecked(True)
        
        # Connect hour/minute changes to auto-sync
        self.ui.comboBox_due_time_hour.currentTextChanged.connect(self.on_hour_changed)
        self.ui.comboBox_due_time_minute.currentTextChanged.connect(self.on_minute_changed)
    
    def on_hour_changed(self, hour_text):
        """Handle hour selection change."""
        if hour_text and not self.ui.comboBox_due_time_minute.currentText():
            # If hour is set but minute is blank, set minute to 00
            self.ui.comboBox_due_time_minute.setCurrentText("00")
        elif not hour_text:
            # If hour is blank, set minute to blank too
            self.ui.comboBox_due_time_minute.setCurrentText("")
    
    def on_minute_changed(self, minute_text):
        """Handle minute selection change."""
        if minute_text and not self.ui.comboBox_due_time_hour.currentText():
            # If minute is set but hour is blank, set hour to 12
            self.ui.comboBox_due_time_hour.setCurrentText("12")
        # Don't change hour when minute is set to blank
    
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
                    self.set_due_time_from_24h(time)
            except Exception:
                pass
        
        # Load reminder periods
        reminder_periods = self.task_data.get('reminder_periods', [])
        if reminder_periods:
            self.ui.checkBox_enable_reminders.setChecked(True)
            self.reminder_periods = reminder_periods.copy()
            self.render_reminder_periods()
        
        # Load quick reminders
        quick_reminders = self.task_data.get('quick_reminders', [])
        if quick_reminders:
            self.ui.checkBox_enable_reminders.setChecked(True)
            # Set the appropriate checkboxes based on stored quick reminders
            if '5-10min' in quick_reminders:
                self.ui.checkBox_reminder_5min.setChecked(True)
            if '1-2hour' in quick_reminders:
                self.ui.checkBox_reminder_10min.setChecked(True)
            if '1-2day' in quick_reminders:
                self.ui.checkBox_reminder_1hour.setChecked(True)
            if '1-2week' in quick_reminders:
                self.ui.checkBox_reminder_2hour.setChecked(True)
            if '30min-1hour' in quick_reminders:
                self.ui.checkBox_reminder_3hour.setChecked(True)
            if '3-5day' in quick_reminders:
                self.ui.checkBox_reminder_4hour.setChecked(True)
    
    def set_due_time_from_24h(self, time):
        """Set due time components from 24-hour time."""
        hour = time.hour()
        minute = time.minute()
        
        # Convert to 12-hour format
        if hour == 0:
            hour_12 = 12
            is_pm = False
        elif hour == 12:
            hour_12 = 12
            is_pm = True
        elif hour > 12:
            hour_12 = hour - 12
            is_pm = True
        else:
            hour_12 = hour
            is_pm = False
        
        # Set components
        self.ui.comboBox_due_time_hour.setCurrentText(f"{hour_12:02d}")
        self.ui.comboBox_due_time_minute.setCurrentText(f"{minute:02d}")
        self.ui.radioButton_due_time_am.setChecked(not is_pm)
        self.ui.radioButton_due_time_pm.setChecked(is_pm)
    
    def get_due_time_as_24h(self):
        """Get due time as 24-hour format string."""
        hour_text = self.ui.comboBox_due_time_hour.currentText()
        minute_text = self.ui.comboBox_due_time_minute.currentText()
        
        # If either hour or minute is blank, no due time
        if not hour_text or not minute_text:
            return None
        
        try:
            hour = int(hour_text)
            minute = int(minute_text)
            is_pm = self.ui.radioButton_due_time_pm.isChecked()
            
            # Convert to 24-hour format
            if is_pm and hour != 12:
                hour += 12
            elif not is_pm and hour == 12:
                hour = 0
            
            return f"{hour:02d}:{minute:02d}"
        except ValueError:
            return None
    
    def add_reminder_period(self):
        """Add a new reminder period."""
        self.reminder_periods.append({
            'date': QDate.currentDate().toString('yyyy-MM-dd'),
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
        if not self.ui.lineEdit_task_title.text().strip():
            QMessageBox.warning(self, "Validation Error", "Task title is required.")
            return False
        return True
    
    def collect_reminder_periods(self):
        """Collect reminder period data from the UI."""
        periods = []
        for period in self.reminder_periods:
            widgets = period.get('__widgets', {})
            
            # Get date
            date_widget = widgets.get('date')
            date = date_widget.date().toString('yyyy-MM-dd') if date_widget else ''
            
            # Get start time
            start_hour = widgets.get('start_hour', QComboBox()).currentText()
            start_minute = widgets.get('start_minute', QComboBox()).currentText()
            start_ampm = widgets.get('start_ampm', QComboBox()).currentText()
            
            start_time = ''
            if start_hour and start_minute and start_ampm:
                h = int(start_hour)
                m = int(start_minute)
                if start_ampm == 'PM' and h != 12:
                    h += 12
                elif start_ampm == 'AM' and h == 12:
                    h = 0
                start_time = f"{h:02d}:{m:02d}"
            
            # Get end time
            end_hour = widgets.get('end_hour', QComboBox()).currentText()
            end_minute = widgets.get('end_minute', QComboBox()).currentText()
            end_ampm = widgets.get('end_ampm', QComboBox()).currentText()
            
            end_time = ''
            if end_hour and end_minute and end_ampm:
                h = int(end_hour)
                m = int(end_minute)
                if end_ampm == 'PM' and h != 12:
                    h += 12
                elif end_ampm == 'AM' and h == 12:
                    h = 0
                end_time = f"{h:02d}:{m:02d}"
            
            if date and start_time and end_time:
                periods.append({
                    'date': date,
                    'start_time': start_time,
                    'end_time': end_time
                })
        
        return periods
    
    def collect_quick_reminders(self):
        """Collect quick reminder options."""
        quick_reminders = []
        if self.ui.checkBox_reminder_5min.isChecked():
            quick_reminders.append('5-10min')
        if self.ui.checkBox_reminder_10min.isChecked():
            quick_reminders.append('1-2hour')
        if self.ui.checkBox_reminder_1hour.isChecked():
            quick_reminders.append('1-2day')
        if self.ui.checkBox_reminder_2hour.isChecked():
            quick_reminders.append('1-2week')
        if self.ui.checkBox_reminder_3hour.isChecked():
            quick_reminders.append('30min-1hour')
        if self.ui.checkBox_reminder_4hour.isChecked():
            quick_reminders.append('3-5day')
        return quick_reminders
    
    def collect_selected_tags(self):
        """Collect selected tags from the tag widget."""
        return self.tag_widget.get_selected_tags()
    
    @handle_errors("saving task")
    def save_task(self):
        """Save the task data."""
        if not self.validate_form():
            return
        
        try:
            # Collect form data
            title = self.ui.lineEdit_task_title.text().strip()
            description = self.ui.textEdit_task_description.toPlainText().strip()
            priority = self.ui.comboBox_task_priority.currentText().lower()
            if priority == "none":
                priority = ""
            
            due_date = self.ui.dateEdit_task_due_date.date().toString('yyyy-MM-dd')
            due_time = self.get_due_time_as_24h()
            
            # Collect tags
            tags = self.collect_selected_tags()
            
            # Collect reminders
            reminder_periods = []
            quick_reminders = []
            if self.ui.checkBox_enable_reminders.isChecked():
                # Add custom reminder periods
                reminder_periods.extend(self.collect_reminder_periods())
                
                # Add quick reminders
                quick_reminders = self.collect_quick_reminders()
                # TODO: Convert quick reminders to actual reminder periods based on due date/time
            
            # Prepare task data
            task_data = {
                'title': title,
                'description': description,
                'priority': priority,
                'due_date': due_date,
                'due_time': due_time,
                'tags': tags,
                'reminder_periods': reminder_periods,
                'quick_reminders': quick_reminders
            }
            
            if self.is_edit:
                # Update existing task
                success = update_task(self.user_id, self.task_data['task_id'], task_data)
                if success:
                    QMessageBox.information(self, "Success", "Task updated successfully!")
                    self.accept()
                else:
                    QMessageBox.critical(self, "Error", "Failed to update task.")
            else:
                # Create new task
                task_id = create_task(
                    user_id=self.user_id,
                    title=title,
                    description=description,
                    due_date=due_date,
                    due_time=due_time,
                    priority=priority,
                    reminder_periods=reminder_periods,
                    tags=tags,
                    quick_reminders=quick_reminders
                )
                if task_id:
                    QMessageBox.information(self, "Success", "Task created successfully!")
                    self.accept()
                else:
                    QMessageBox.critical(self, "Error", "Failed to create task.")
                    
        except Exception as e:
            logger.error(f"Error saving task: {e}")
            QMessageBox.critical(self, "Error", f"Failed to save task: {e}") 