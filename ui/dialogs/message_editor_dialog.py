"""
Message Editor Dialog

Provides full CRUD operations for user messages including viewing, adding,
editing, and deleting messages in specific categories.
"""

from PySide6.QtWidgets import (QDialog, QMessageBox, QVBoxLayout, QHBoxLayout, 
                               QLabel, QTextEdit, QPushButton, QTableWidgetItem,
                               QCheckBox, QGroupBox, QFormLayout, QLineEdit, QDialogButtonBox,
                               QWidget, QScrollArea)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from ui.generated.message_editor_dialog_pyqt import Ui_Dialog_message_editor

# Import core functionality
from core.message_management import load_user_messages, add_message, edit_message, delete_message
from core.error_handling import handle_errors
from core.logger import setup_logging, get_component_logger
import uuid
from datetime import datetime

setup_logging()
logger = get_component_logger('ui')


class MessageEditDialog(QDialog):
    """Dialog for editing or adding a message."""
    
    @handle_errors("initializing message edit dialog")
    def __init__(self, parent=None, user_id=None, category=None, message_data=None):
        """Initialize the message edit dialog."""
        super().__init__(parent)
        self.user_id = user_id
        self.category = category
        self.message_data = message_data or {}
        self.is_edit = bool(message_data)
        
        self.setWindowTitle(f"{'Edit' if self.is_edit else 'Add'} Message - {category.title()}")
        self.setModal(True)
        self.resize(500, 400)
        
        self.setup_ui()
        self.setup_connections()
        self.load_message_data()
    
    @handle_errors("setting up UI")
    def setup_ui(self):
        """Setup the UI components."""
        layout = QVBoxLayout(self)
        
        # Message text
        message_label = QLabel("Message Text:")
        self.message_text = QTextEdit()
        self.message_text.setMaximumHeight(100)
        layout.addWidget(message_label)
        layout.addWidget(self.message_text)
        
        # Days selection
        days_group = QGroupBox("Days")
        days_layout = QFormLayout(days_group)
        
        self.day_checkboxes = {}
        days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        for day in days:
            checkbox = QCheckBox(day.title())
            self.day_checkboxes[day] = checkbox
            days_layout.addRow(checkbox)
        
        layout.addWidget(days_group)
        
        # Time periods selection
        periods_group = QGroupBox("Time Periods")
        periods_layout = QFormLayout(periods_group)
        
        self.period_checkboxes = {}
        periods = ['morning', 'afternoon', 'evening', 'night']
        for period in periods:
            checkbox = QCheckBox(period.title())
            self.period_checkboxes[period] = checkbox
            periods_layout.addRow(checkbox)
        
        layout.addWidget(periods_group)
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | 
                                     QDialogButtonBox.StandardButton.Cancel)
        layout.addWidget(button_box)
        
        self.button_box = button_box
    
    @handle_errors("setting up connections")
    def setup_connections(self):
        """Setup signal connections."""
        self.button_box.accepted.connect(self.save_message)
        self.button_box.rejected.connect(self.reject)
    
    @handle_errors("loading message data")
    def load_message_data(self):
        """Load existing message data if editing."""
        if self.is_edit and self.message_data:
            # Load message text
            self.message_text.setPlainText(self.message_data.get('message', ''))
            
            # Load days
            days = self.message_data.get('days', [])
            for day, checkbox in self.day_checkboxes.items():
                checkbox.setChecked(day in days)
            
            # Load time periods
            periods = self.message_data.get('time_periods', [])
            for period, checkbox in self.period_checkboxes.items():
                checkbox.setChecked(period in periods)
    
    @handle_errors("saving message")
    def save_message(self):
        """Save the message data."""
        # Validate message text
        message_text = self.message_text.toPlainText().strip()
        if not message_text:
            QMessageBox.warning(self, "Validation Error", "Message text is required.")
            return
        
        # Validate days selection
        selected_days = [day for day, checkbox in self.day_checkboxes.items() if checkbox.isChecked()]
        if not selected_days:
            QMessageBox.warning(self, "Validation Error", "At least one day must be selected.")
            return
        
        # Validate time periods selection
        selected_periods = [period for period, checkbox in self.period_checkboxes.items() if checkbox.isChecked()]
        if not selected_periods:
            QMessageBox.warning(self, "Validation Error", "At least one time period must be selected.")
            return
        
        # Prepare message data
        message_data = {
            'message': message_text,
            'days': selected_days,
            'time_periods': selected_periods
        }
        
        # @handle_errors decorator handles exceptions
        if self.is_edit:
            # Edit existing message
            message_id = self.message_data.get('message_id')
            if message_id:
                edit_message(self.user_id, self.category, message_id, message_data)
                QMessageBox.information(self, "Success", "Message updated successfully.")
            else:
                QMessageBox.critical(self, "Error", "Message ID not found.")
                return
        else:
            # Add new message
            message_id = str(uuid.uuid4())
            message_data['message_id'] = message_id
            message_data['created_at'] = datetime.now().isoformat()
            
            add_message(self.user_id, self.category, message_data)
            QMessageBox.information(self, "Success", "Message added successfully.")
        
        self.accept()


class MessageEditorDialog(QDialog):
    """Dialog for managing messages in a category."""
    
    @handle_errors("initializing message editor dialog")
    def __init__(self, parent=None, user_id=None, category=None):
        """Initialize the message editor dialog."""
        super().__init__(parent)
        self.user_id = user_id
        self.category = category
        self.messages = []
        
        # Setup UI
        self.ui = Ui_Dialog_message_editor()
        self.ui.setupUi(self)
        
        # Setup functionality
        self.setup_connections()
        self.setup_initial_state()
        
        # Load messages
        self.load_messages()
    
    @handle_errors("setting up connections")
    def setup_connections(self):
        """Setup signal connections."""
        self.ui.pushButton_refresh.clicked.connect(self.load_messages)
        self.ui.pushButton_add_message.clicked.connect(self.add_new_message)
        self.ui.pushButton_close.clicked.connect(self.accept)
        self.ui.tableWidget_messages.itemDoubleClicked.connect(self.edit_selected_message)
    
    @handle_errors("setting up initial state")
    def setup_initial_state(self):
        """Setup initial dialog state."""
        # Set window title
        self.setWindowTitle(f"Message Editor - {self.category.title()}")
        
        # Setup table
        self.ui.tableWidget_messages.setColumnCount(4)
        self.ui.tableWidget_messages.setHorizontalHeaderLabels([
            "Message Text", "Days", "Time Periods", "Actions"
        ])
        
        # Enable sorting (but disable during population to avoid issues)
        self.ui.tableWidget_messages.setSortingEnabled(True)
        
        # Set column widths
        self.ui.tableWidget_messages.setColumnWidth(0, 300)  # Message text
        self.ui.tableWidget_messages.setColumnWidth(1, 150)  # Days
        self.ui.tableWidget_messages.setColumnWidth(2, 150)  # Time periods
        self.ui.tableWidget_messages.setColumnWidth(3, 100)  # Actions
    
    @handle_errors("loading messages")
    def load_messages(self):
        """Load messages for the category."""
        # Save current sort state before refreshing
        sort_column = self.ui.tableWidget_messages.horizontalHeader().sortIndicatorSection()
        sort_order = self.ui.tableWidget_messages.horizontalHeader().sortIndicatorOrder()
        
        # @handle_errors decorator handles exceptions
        self.messages = load_user_messages(self.user_id, self.category)
        
        if not self.messages:
            # No messages found - show helpful message
            self.show_no_messages_state()
            return
            
        self.populate_table()
        
        # Restore sort state after populating
        if sort_column >= 0:
            self.ui.tableWidget_messages.horizontalHeader().setSortIndicator(sort_column, sort_order)
        
        self.update_message_count()
    
    @handle_errors("showing no messages state")
    def show_no_messages_state(self):
        """Show state when no messages are found."""
        self.ui.tableWidget_messages.setRowCount(1)
        self.ui.tableWidget_messages.setItem(0, 0, QTableWidgetItem("No messages found for this category"))
        self.ui.tableWidget_messages.setItem(0, 1, QTableWidgetItem(""))
        self.ui.tableWidget_messages.setItem(0, 2, QTableWidgetItem(""))
        self.ui.tableWidget_messages.setItem(0, 3, QTableWidgetItem(""))
        
        # Disable edit/delete buttons
        self.ui.pushButton_edit_message.setEnabled(False)
        self.ui.pushButton_delete_message.setEnabled(False)
        
        self.update_message_count()
    
    @handle_errors("populating table")
    def populate_table(self):
        """Populate the table with messages."""
        # Temporarily disable sorting during population to avoid issues
        self.ui.tableWidget_messages.setSortingEnabled(False)
        
        self.ui.tableWidget_messages.setRowCount(len(self.messages))
        
        for row, message in enumerate(self.messages):
            # Message text (truncated for display)
            message_text = message.get('message', '')
            display_text = message_text[:100] + "..." if len(message_text) > 100 else message_text
            self.ui.tableWidget_messages.setItem(row, 0, QTableWidgetItem(display_text))
            
            # Days
            days = message.get('days', [])
            days_text = ", ".join([day.title() for day in days])
            self.ui.tableWidget_messages.setItem(row, 1, QTableWidgetItem(days_text))
            
            # Time periods
            periods = message.get('time_periods', [])
            periods_text = ", ".join([period.title() for period in periods])
            self.ui.tableWidget_messages.setItem(row, 2, QTableWidgetItem(periods_text))
            
            # Actions
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(2, 2, 2, 2)
            
            edit_btn = QPushButton("Edit")
            edit_btn.setMaximumSize(50, 25)
            edit_btn.clicked.connect(lambda checked, r=row: self.edit_message_by_row(r))
            actions_layout.addWidget(edit_btn)
            
            delete_btn = QPushButton("Delete")
            delete_btn.setMaximumSize(60, 25)
            delete_btn.clicked.connect(lambda checked, r=row: self.delete_message_by_row(r))
            actions_layout.addWidget(delete_btn)
            
            self.ui.tableWidget_messages.setCellWidget(row, 3, actions_widget)
        
        # Re-enable sorting after population
        self.ui.tableWidget_messages.setSortingEnabled(True)
    
    @handle_errors("updating message count")
    def update_message_count(self):
        """Update the message count label."""
        count = len(self.messages)
        self.ui.label_message_count.setText(f"Messages: {count}")
    
    @handle_errors("adding new message")
    def add_new_message(self):
        """Add a new message."""
        dialog = MessageEditDialog(self, self.user_id, self.category)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_messages()
    
    @handle_errors("editing selected message")
    def edit_selected_message(self, item):
        """Edit the selected message."""
        row = item.row()
        self.edit_message_by_row(row)
    
    @handle_errors("editing message by row")
    def edit_message_by_row(self, row):
        """Edit message at the specified row."""
        if 0 <= row < len(self.messages):
            message_data = self.messages[row]
            dialog = MessageEditDialog(self, self.user_id, self.category, message_data)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self.load_messages()
    
    @handle_errors("deleting message by row")
    def delete_message_by_row(self, row):
        """Delete message at the specified row."""
        if 0 <= row < len(self.messages):
            message = self.messages[row]
            message_id = message.get('message_id')
            message_text = message.get('message', '')[:50] + "..." if len(message.get('message', '')) > 50 else message.get('message', '')
            
            # Confirm deletion
            reply = QMessageBox.question(
                self, "Confirm Delete",
                f"Are you sure you want to delete this message?\n\n{message_text}",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                # @handle_errors decorator handles exceptions
                delete_message(self.user_id, self.category, message_id)
                QMessageBox.information(self, "Success", "Message deleted successfully.")
                self.load_messages()


@handle_errors("opening message editor dialog")
def open_message_editor_dialog(parent, user_id, category):
    """Open the message editor dialog."""
    dialog = MessageEditorDialog(parent, user_id, category)
    return dialog.exec()
