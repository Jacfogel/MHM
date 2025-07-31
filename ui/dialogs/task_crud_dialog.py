from PySide6.QtWidgets import QDialog, QMessageBox, QTableWidgetItem, QHeaderView
from PySide6.QtCore import Qt, Signal
from ui.generated.task_crud_dialog_pyqt import Ui_Dialog_task_crud

# Import core functionality
from tasks.task_management import (
    load_active_tasks, load_completed_tasks, get_user_task_stats, 
    get_tasks_due_soon, complete_task, delete_task
)
from core.error_handling import handle_errors
from core.logger import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)

class TaskCrudDialog(QDialog):
    """Dialog for full CRUD operations on tasks."""
    
    def __init__(self, parent=None, user_id=None):
        """Initialize the task CRUD dialog."""
        super().__init__(parent)
        self.user_id = user_id
        self.ui = Ui_Dialog_task_crud()
        self.ui.setupUi(self)
        
        # Store task data for easy access
        self.active_tasks = []
        self.completed_tasks = []
        
        self.setup_ui()
        self.setup_connections()
        self.load_data()
    
    def setup_ui(self):
        """Setup the UI components."""
        # Setup table headers for active tasks
        self.ui.tableWidget_active_tasks.setColumnCount(7)
        self.ui.tableWidget_active_tasks.setHorizontalHeaderLabels([
            "Title", "Description", "Due Date", "Due Time", "Priority", "Category", "Created"
        ])
        
        # Setup table headers for completed tasks
        self.ui.tableWidget_completed_tasks.setColumnCount(6)
        self.ui.tableWidget_completed_tasks.setHorizontalHeaderLabels([
            "Title", "Description", "Due Date", "Priority", "Category", "Completed"
        ])
        
        # Set column widths
        for table in [self.ui.tableWidget_active_tasks, self.ui.tableWidget_completed_tasks]:
            header = table.horizontalHeader()
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)  # Title
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # Description
            header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Due Date
            if table == self.ui.tableWidget_active_tasks:
                header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Due Time
                header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # Priority
                header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)  # Category
                header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)  # Created
            else:
                header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Priority
                header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # Category
                header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)  # Completed
    
    def setup_connections(self):
        """Setup signal connections."""
        # Active tasks buttons
        self.ui.pushButton_add_new_task.clicked.connect(self.add_new_task)
        self.ui.pushButton_edit_selected_task.clicked.connect(self.edit_selected_task)
        self.ui.pushButton_complete_selected_task.clicked.connect(self.complete_selected_task)
        self.ui.pushButton_delete_selected_task.clicked.connect(self.delete_selected_task)
        self.ui.pushButton_refresh_active_tasks.clicked.connect(self.refresh_active_tasks)
        
        # Completed tasks buttons
        self.ui.pushButton_restore_selected_task.clicked.connect(self.restore_selected_task)
        self.ui.pushButton_delete_completed_task.clicked.connect(self.delete_completed_task)
        self.ui.pushButton_refresh_completed_tasks.clicked.connect(self.refresh_completed_tasks)
        
        # Close button
        self.ui.buttonBox_task_crud.accepted.connect(self.accept)
        self.ui.buttonBox_task_crud.rejected.connect(self.reject)
    
    @handle_errors("loading task data")
    def load_data(self):
        """Load all task data and update displays."""
        try:
            # Load task data
            self.active_tasks = load_active_tasks(self.user_id)
            self.completed_tasks = load_completed_tasks(self.user_id)
            
            # Update tables
            self.refresh_active_tasks()
            self.refresh_completed_tasks()
            
            # Update statistics
            self.update_statistics()
            
        except Exception as e:
            logger.error(f"Error loading task data: {e}")
            QMessageBox.critical(self, "Error", f"Failed to load task data: {e}")
    
    def refresh_active_tasks(self):
        """Refresh the active tasks table."""
        try:
            self.active_tasks = load_active_tasks(self.user_id)
            self.ui.tableWidget_active_tasks.setRowCount(0)
            
            for task in self.active_tasks:
                row = self.ui.tableWidget_active_tasks.rowCount()
                self.ui.tableWidget_active_tasks.insertRow(row)
                
                # Set task data
                self.ui.tableWidget_active_tasks.setItem(row, 0, QTableWidgetItem(task.get('title', '')))
                self.ui.tableWidget_active_tasks.setItem(row, 1, QTableWidgetItem(task.get('description', '')))
                self.ui.tableWidget_active_tasks.setItem(row, 2, QTableWidgetItem(task.get('due_date', '')))
                self.ui.tableWidget_active_tasks.setItem(row, 3, QTableWidgetItem(task.get('due_time', '')))
                self.ui.tableWidget_active_tasks.setItem(row, 4, QTableWidgetItem(task.get('priority', 'medium')))
                self.ui.tableWidget_active_tasks.setItem(row, 5, QTableWidgetItem(task.get('category', '')))
                self.ui.tableWidget_active_tasks.setItem(row, 6, QTableWidgetItem(task.get('created_at', '')))
                
                # Store task ID in the first column for easy access
                self.ui.tableWidget_active_tasks.item(row, 0).setData(Qt.ItemDataRole.UserRole, task.get('task_id'))
            
            self.update_statistics()
            
        except Exception as e:
            logger.error(f"Error refreshing active tasks: {e}")
            QMessageBox.critical(self, "Error", f"Failed to refresh active tasks: {e}")
    
    def refresh_completed_tasks(self):
        """Refresh the completed tasks table."""
        try:
            self.completed_tasks = load_completed_tasks(self.user_id)
            self.ui.tableWidget_completed_tasks.setRowCount(0)
            
            for task in self.completed_tasks:
                row = self.ui.tableWidget_completed_tasks.rowCount()
                self.ui.tableWidget_completed_tasks.insertRow(row)
                
                # Set task data
                self.ui.tableWidget_completed_tasks.setItem(row, 0, QTableWidgetItem(task.get('title', '')))
                self.ui.tableWidget_completed_tasks.setItem(row, 1, QTableWidgetItem(task.get('description', '')))
                self.ui.tableWidget_completed_tasks.setItem(row, 2, QTableWidgetItem(task.get('due_date', '')))
                self.ui.tableWidget_completed_tasks.setItem(row, 3, QTableWidgetItem(task.get('priority', 'medium')))
                self.ui.tableWidget_completed_tasks.setItem(row, 4, QTableWidgetItem(task.get('category', '')))
                self.ui.tableWidget_completed_tasks.setItem(row, 5, QTableWidgetItem(task.get('completed_at', '')))
                
                # Store task ID in the first column for easy access
                self.ui.tableWidget_completed_tasks.item(row, 0).setData(Qt.ItemDataRole.UserRole, task.get('task_id'))
            
            self.update_statistics()
            
        except Exception as e:
            logger.error(f"Error refreshing completed tasks: {e}")
            QMessageBox.critical(self, "Error", f"Failed to refresh completed tasks: {e}")
    
    def update_statistics(self):
        """Update the statistics display."""
        try:
            stats = get_user_task_stats(self.user_id)
            due_soon = get_tasks_due_soon(self.user_id, 7)
            
            self.ui.label_active_tasks_count.setText(f"Active Tasks: {stats.get('active_count', 0)}")
            self.ui.label_completed_tasks_count.setText(f"Completed Tasks: {stats.get('completed_count', 0)}")
            self.ui.label_total_tasks_count.setText(f"Total Tasks: {stats.get('total_count', 0)}")
            self.ui.label_tasks_due_soon.setText(f"Due Soon (7 days): {len(due_soon)}")
            
        except Exception as e:
            logger.error(f"Error updating statistics: {e}")
    
    def get_selected_task_id(self, table):
        """Get the task ID of the selected row in the given table."""
        current_row = table.currentRow()
        if current_row >= 0:
            item = table.item(current_row, 0)
            if item:
                return item.data(Qt.ItemDataRole.UserRole)
        return None
    
    def add_new_task(self):
        """Open dialog to add a new task."""
        try:
            from ui.dialogs.task_edit_dialog import TaskEditDialog
            dialog = TaskEditDialog(self, self.user_id)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self.refresh_active_tasks()
        except Exception as e:
            logger.error(f"Error adding new task: {e}")
            QMessageBox.critical(self, "Error", f"Failed to add new task: {e}")
    
    def edit_selected_task(self):
        """Edit the selected task."""
        try:
            task_id = self.get_selected_task_id(self.ui.tableWidget_active_tasks)
            if not task_id:
                QMessageBox.warning(self, "No Selection", "Please select a task to edit.")
                return
            
            from tasks.task_management import get_task_by_id
            task_data = get_task_by_id(self.user_id, task_id)
            if not task_data:
                QMessageBox.critical(self, "Error", "Task not found.")
                return
            
            from ui.dialogs.task_edit_dialog import TaskEditDialog
            dialog = TaskEditDialog(self, self.user_id, task_data)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self.refresh_active_tasks()
                
        except Exception as e:
            logger.error(f"Error editing task: {e}")
            QMessageBox.critical(self, "Error", f"Failed to edit task: {e}")
    
    def complete_selected_task(self):
        """Mark the selected task as completed."""
        try:
            task_id = self.get_selected_task_id(self.ui.tableWidget_active_tasks)
            if not task_id:
                QMessageBox.warning(self, "No Selection", "Please select a task to complete.")
                return
            
            # Get task data for confirmation
            from tasks.task_management import get_task_by_id
            task_data = get_task_by_id(self.user_id, task_id)
            if not task_data:
                QMessageBox.critical(self, "Error", "Task not found.")
                return
            
            result = QMessageBox.question(
                self, "Complete Task", 
                f"Are you sure you want to mark '{task_data.get('title', '')}' as completed?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if result == QMessageBox.StandardButton.Yes:
                if complete_task(self.user_id, task_id):
                    QMessageBox.information(self, "Success", "Task marked as completed!")
                    self.refresh_active_tasks()
                    self.refresh_completed_tasks()
                else:
                    QMessageBox.critical(self, "Error", "Failed to complete task.")
                    
        except Exception as e:
            logger.error(f"Error completing task: {e}")
            QMessageBox.critical(self, "Error", f"Failed to complete task: {e}")
    
    def delete_selected_task(self):
        """Delete the selected task."""
        try:
            task_id = self.get_selected_task_id(self.ui.tableWidget_active_tasks)
            if not task_id:
                QMessageBox.warning(self, "No Selection", "Please select a task to delete.")
                return
            
            # Get task data for confirmation
            from tasks.task_management import get_task_by_id
            task_data = get_task_by_id(self.user_id, task_id)
            if not task_data:
                QMessageBox.critical(self, "Error", "Task not found.")
                return
            
            result = QMessageBox.question(
                self, "Delete Task", 
                f"Are you sure you want to delete '{task_data.get('title', '')}'?\n\nThis action cannot be undone.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if result == QMessageBox.StandardButton.Yes:
                if delete_task(self.user_id, task_id):
                    QMessageBox.information(self, "Success", "Task deleted successfully!")
                    self.refresh_active_tasks()
                else:
                    QMessageBox.critical(self, "Error", "Failed to delete task.")
                    
        except Exception as e:
            logger.error(f"Error deleting task: {e}")
            QMessageBox.critical(self, "Error", f"Failed to delete task: {e}")
    
    def restore_selected_task(self):
        """Restore a completed task to active status."""
        try:
            task_id = self.get_selected_task_id(self.ui.tableWidget_completed_tasks)
            if not task_id:
                QMessageBox.warning(self, "No Selection", "Please select a task to restore.")
                return
            
            # Get task data for confirmation
            from tasks.task_management import get_task_by_id
            task_data = get_task_by_id(self.user_id, task_id)
            if not task_data:
                QMessageBox.critical(self, "Error", "Task not found.")
                return
            
            result = QMessageBox.question(
                self, "Restore Task", 
                f"Are you sure you want to restore '{task_data.get('title', '')}' to active status?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if result == QMessageBox.StandardButton.Yes:
                from tasks.task_management import restore_task
                if restore_task(self.user_id, task_id):
                    QMessageBox.information(self, "Success", "Task restored successfully!")
                    self.refresh_active_tasks()
                    self.refresh_completed_tasks()
                else:
                    QMessageBox.critical(self, "Error", "Failed to restore task.")
                    
        except Exception as e:
            logger.error(f"Error restoring task: {e}")
            QMessageBox.critical(self, "Error", f"Failed to restore task: {e}")
    
    def delete_completed_task(self):
        """Permanently delete a completed task."""
        try:
            task_id = self.get_selected_task_id(self.ui.tableWidget_completed_tasks)
            if not task_id:
                QMessageBox.warning(self, "No Selection", "Please select a task to delete.")
                return
            
            # Get task data for confirmation
            from tasks.task_management import get_task_by_id
            task_data = get_task_by_id(self.user_id, task_id)
            if not task_data:
                QMessageBox.critical(self, "Error", "Task not found.")
                return
            
            result = QMessageBox.question(
                self, "Delete Completed Task", 
                f"Are you sure you want to permanently delete '{task_data.get('title', '')}'?\n\nThis action cannot be undone.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if result == QMessageBox.StandardButton.Yes:
                if delete_task(self.user_id, task_id):
                    QMessageBox.information(self, "Success", "Task deleted permanently!")
                    self.refresh_completed_tasks()
                else:
                    QMessageBox.critical(self, "Error", "Failed to delete task.")
                    
        except Exception as e:
            logger.error(f"Error deleting completed task: {e}")
            QMessageBox.critical(self, "Error", f"Failed to delete completed task: {e}") 