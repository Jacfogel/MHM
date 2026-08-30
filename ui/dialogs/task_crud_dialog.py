# pyright: reportAttributeAccessIssue=false, reportOptionalMemberAccess=false

"""Task CRUD Dialog"""

from PySide6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QHeaderView,
    QMessageBox,
    QTableWidgetItem,
)
from PySide6.QtCore import Qt
from ui.generated.task_crud_dialog_pyqt import Ui_Dialog_task_crud

# Import core functionality
from tasks import (
    load_active_tasks,
    load_completed_tasks,
    get_user_task_stats,
    get_tasks_due_soon,
    complete_task,
    delete_task,
)
from tasks.task_data_handlers import (
    runtime_task_completed_at,
    runtime_task_due_date,
    runtime_task_due_time,
)
from core.error_handling import handle_errors
from core.logger import setup_logging, get_component_logger

setup_logging()
logger = get_component_logger("ui")
dialog_logger = logger


class TaskCrudDialog(QDialog):
    """Dialog for full CRUD operations on tasks."""

    # ERROR_HANDLING_EXCLUDE: Dialog constructor - calls methods with error handling (setup_ui, setup_connections)
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

    @handle_errors("setting up task CRUD UI", default_return=None)
    def setup_ui(self):
        """Setup the UI components."""
        # Setup table headers for active tasks
        self.ui.tableWidget_active_tasks.setColumnCount(7)
        self.ui.tableWidget_active_tasks.setHorizontalHeaderLabels(
            [
                "Title",
                "Description",
                "Due Date",
                "Due Time",
                "Priority",
                "Category",
                "Created",
            ]
        )

        # Setup table headers for completed tasks
        self.ui.tableWidget_completed_tasks.setColumnCount(6)
        self.ui.tableWidget_completed_tasks.setHorizontalHeaderLabels(
            ["Title", "Description", "Due Date", "Priority", "Category", "Completed"]
        )

        # Enable sorting on both tables
        self.ui.tableWidget_active_tasks.setSortingEnabled(True)
        self.ui.tableWidget_completed_tasks.setSortingEnabled(True)

        # Set column widths and allow Ctrl/Shift multi-select
        for table in [
            self.ui.tableWidget_active_tasks,
            self.ui.tableWidget_completed_tasks,
        ]:
            table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
            table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
            header = table.horizontalHeader()
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)  # Title
            header.setSectionResizeMode(
                1, QHeaderView.ResizeMode.Stretch
            )  # Description
            header.setSectionResizeMode(
                2, QHeaderView.ResizeMode.ResizeToContents
            )  # Due Date
            if table == self.ui.tableWidget_active_tasks:
                header.setSectionResizeMode(
                    3, QHeaderView.ResizeMode.ResizeToContents
                )  # Due Time
                header.setSectionResizeMode(
                    4, QHeaderView.ResizeMode.ResizeToContents
                )  # Priority
                header.setSectionResizeMode(
                    5, QHeaderView.ResizeMode.ResizeToContents
                )  # Category
                header.setSectionResizeMode(
                    6, QHeaderView.ResizeMode.ResizeToContents
                )  # Created
            else:
                header.setSectionResizeMode(
                    3, QHeaderView.ResizeMode.ResizeToContents
                )  # Priority
                header.setSectionResizeMode(
                    4, QHeaderView.ResizeMode.ResizeToContents
                )  # Category
                header.setSectionResizeMode(
                    5, QHeaderView.ResizeMode.ResizeToContents
                )  # Completed

    @handle_errors("setting up task CRUD connections", default_return=None)
    def setup_connections(self):
        """Setup signal connections."""
        # Active tasks buttons
        self.ui.pushButton_add_new_task.clicked.connect(self.add_new_task)
        self.ui.pushButton_edit_selected_task.clicked.connect(self.edit_selected_task)
        self.ui.pushButton_complete_selected_task.clicked.connect(
            self.complete_selected_task
        )
        self.ui.pushButton_delete_selected_task.clicked.connect(
            self.delete_selected_task
        )
        self.ui.pushButton_refresh_active_tasks.clicked.connect(
            self.refresh_active_tasks
        )

        # Completed tasks buttons
        self.ui.pushButton_restore_selected_task.clicked.connect(
            self.restore_selected_task
        )
        self.ui.pushButton_delete_completed_task.clicked.connect(
            self.delete_completed_task
        )
        self.ui.pushButton_refresh_completed_tasks.clicked.connect(
            self.refresh_completed_tasks
        )

        # Close button
        self.ui.buttonBox_task_crud.accepted.connect(self.accept)
        self.ui.buttonBox_task_crud.rejected.connect(self.reject)

    # not_duplicate: unrelated_load_data_methods
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

    @handle_errors("refreshing active tasks", user_friendly=True, default_return=None)
    def refresh_active_tasks(self):
        """Refresh the active tasks table."""
        # not_duplicate: task_crud_refresh_lists
        # Save current sort state before refreshing
        sort_column = (
            self.ui.tableWidget_active_tasks.horizontalHeader().sortIndicatorSection()
        )
        sort_order = (
            self.ui.tableWidget_active_tasks.horizontalHeader().sortIndicatorOrder()
        )

        self.active_tasks = load_active_tasks(self.user_id)

        # Temporarily disable sorting during population
        self.ui.tableWidget_active_tasks.setSortingEnabled(False)
        self.ui.tableWidget_active_tasks.setRowCount(0)

        for task in self.active_tasks:
            row = self.ui.tableWidget_active_tasks.rowCount()
            self.ui.tableWidget_active_tasks.insertRow(row)

            # Set task data
            self.ui.tableWidget_active_tasks.setItem(
                row, 0, QTableWidgetItem(task.get("title", ""))
            )
            self.ui.tableWidget_active_tasks.setItem(
                row, 1, QTableWidgetItem(task.get("description", ""))
            )
            self.ui.tableWidget_active_tasks.setItem(
                row, 2, QTableWidgetItem(runtime_task_due_date(task) or "")
            )
            self.ui.tableWidget_active_tasks.setItem(
                row, 3, QTableWidgetItem(runtime_task_due_time(task) or "")
            )
            self.ui.tableWidget_active_tasks.setItem(
                row, 4, QTableWidgetItem(task.get("priority", "medium"))
            )
            self.ui.tableWidget_active_tasks.setItem(
                row, 5, QTableWidgetItem(task.get("category", ""))
            )
            self.ui.tableWidget_active_tasks.setItem(
                row, 6, QTableWidgetItem(task.get("created_at", ""))
            )

            # Store task ID in the first column for easy access
            self.ui.tableWidget_active_tasks.item(row, 0).setData(
                Qt.ItemDataRole.UserRole, task.get("id")
            )

        # Re-enable sorting and restore sort state
        self.ui.tableWidget_active_tasks.setSortingEnabled(True)
        if sort_column >= 0:
            self.ui.tableWidget_active_tasks.horizontalHeader().setSortIndicator(
                sort_column, sort_order
            )

        self.update_statistics()

    @handle_errors(
        "refreshing completed tasks", user_friendly=True, default_return=None
    )
    def refresh_completed_tasks(self):
        """Refresh the completed tasks table."""
        # not_duplicate: task_crud_refresh_lists
        # Save current sort state before refreshing
        sort_column = (
            self.ui.tableWidget_completed_tasks.horizontalHeader().sortIndicatorSection()
        )
        sort_order = (
            self.ui.tableWidget_completed_tasks.horizontalHeader().sortIndicatorOrder()
        )

        self.completed_tasks = load_completed_tasks(self.user_id)

        # Temporarily disable sorting during population
        self.ui.tableWidget_completed_tasks.setSortingEnabled(False)
        self.ui.tableWidget_completed_tasks.setRowCount(0)

        for task in self.completed_tasks:
            row = self.ui.tableWidget_completed_tasks.rowCount()
            self.ui.tableWidget_completed_tasks.insertRow(row)

            # Set task data
            self.ui.tableWidget_completed_tasks.setItem(
                row, 0, QTableWidgetItem(task.get("title", ""))
            )
            self.ui.tableWidget_completed_tasks.setItem(
                row, 1, QTableWidgetItem(task.get("description", ""))
            )
            self.ui.tableWidget_completed_tasks.setItem(
                row, 2, QTableWidgetItem(runtime_task_due_date(task) or "")
            )
            self.ui.tableWidget_completed_tasks.setItem(
                row, 3, QTableWidgetItem(task.get("priority", "medium"))
            )
            self.ui.tableWidget_completed_tasks.setItem(
                row, 4, QTableWidgetItem(task.get("category", ""))
            )
            self.ui.tableWidget_completed_tasks.setItem(
                row, 5, QTableWidgetItem(runtime_task_completed_at(task) or "")
            )

            # Store task ID in the first column for easy access
            self.ui.tableWidget_completed_tasks.item(row, 0).setData(
                Qt.ItemDataRole.UserRole, task.get("id")
            )

        # Re-enable sorting and restore sort state
        self.ui.tableWidget_completed_tasks.setSortingEnabled(True)
        if sort_column >= 0:
            self.ui.tableWidget_completed_tasks.horizontalHeader().setSortIndicator(
                sort_column, sort_order
            )

        self.update_statistics()

    @handle_errors("updating statistics", user_friendly=False, default_return=None)
    def update_statistics(self):
        """Update the statistics display."""
        stats = get_user_task_stats(self.user_id)
        due_soon = get_tasks_due_soon(self.user_id, 7)

        self.ui.label_active_tasks_count.setText(
            f"Active Tasks: {stats.get('active_count', 0)}"
        )
        self.ui.label_completed_tasks_count.setText(
            f"Completed Tasks: {stats.get('completed_count', 0)}"
        )
        self.ui.label_total_tasks_count.setText(
            f"Total Tasks: {stats.get('total_count', 0)}"
        )
        self.ui.label_tasks_due_soon.setText(f"Due Soon (7 days): {len(due_soon)}")

    @handle_errors("getting selected task pairs", default_return=[])
    def get_selected_task_pairs(self, table):
        """Return [(task_id, title), ...] for selected rows in the given table."""
        pairs = []
        seen = set()
        selection_model = table.selectionModel()
        if selection_model is None:
            return []
        for index in selection_model.selectedRows():
            item = table.item(index.row(), 0)
            if not item:
                continue
            task_id = item.data(Qt.ItemDataRole.UserRole)
            if not task_id or task_id in seen:
                continue
            seen.add(task_id)
            pairs.append((task_id, item.text() or "Untitled"))
        return pairs

    @handle_errors("getting selected task IDs", default_return=[])
    def get_selected_task_ids(self, table):
        """Get task IDs for all selected rows in the given table."""
        return [task_id for task_id, _ in self.get_selected_task_pairs(table)]

    @handle_errors("confirming task dialog action", default_return=False)
    def _confirm_yes_no(self, title, message):
        """Show a Yes/No confirmation dialog. Returns True if the user chose Yes."""
        result = QMessageBox.question(
            self,
            title,
            message,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        return result == QMessageBox.StandardButton.Yes

    @handle_errors("reporting task batch result", default_return=None)
    def _report_batch_result(self, failed_titles, *, success_one, success_many, count):
        """Show success or a list of failed titles after a batch action."""
        if failed_titles:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to process {len(failed_titles)} task(s): {', '.join(failed_titles)}.",
            )
            return
        QMessageBox.information(
            self, "Success", success_one if count == 1 else success_many
        )

    @handle_errors("adding new task", user_friendly=True, default_return=None)
    def add_new_task(self):
        """Open dialog to add a new task."""
        from ui.dialogs.task_edit_dialog import TaskEditDialog

        dialog = TaskEditDialog(self, self.user_id)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.refresh_active_tasks()

    @handle_errors("editing task", user_friendly=True, default_return=None)
    def edit_selected_task(self):
        """Edit the selected task."""
        task_ids = self.get_selected_task_ids(self.ui.tableWidget_active_tasks)
        if not task_ids:
            QMessageBox.warning(self, "No Selection", "Please select a task to edit.")
            return
        if len(task_ids) > 1:
            QMessageBox.warning(
                self, "Multiple Selection", "Please select a single task to edit."
            )
            return
        task_id = task_ids[0]

        from tasks import get_task_by_id

        task_data = get_task_by_id(self.user_id, task_id)
        if not task_data:
            QMessageBox.critical(self, "Error", "Task not found.")
            return

        from ui.dialogs.task_edit_dialog import TaskEditDialog

        dialog = TaskEditDialog(self, self.user_id, task_data)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.refresh_active_tasks()

    @handle_errors("completing task", user_friendly=True, default_return=None)
    def complete_selected_task(self):
        """Mark the selected task(s) as completed."""
        pairs = self.get_selected_task_pairs(self.ui.tableWidget_active_tasks)
        if not pairs:
            QMessageBox.warning(
                self, "No Selection", "Please select a task to complete."
            )
            return

        if len(pairs) == 1:
            task_id, title = pairs[0]
            from ui.dialogs.task_completion_dialog import TaskCompletionDialog

            completion_dialog = TaskCompletionDialog(self, title)
            if completion_dialog.exec() != QDialog.DialogCode.Accepted:
                return
            completion_data = completion_dialog.get_completion_data()
            if complete_task(self.user_id, task_id, completion_data):
                QMessageBox.information(self, "Success", "Task marked as completed!")
                self.refresh_active_tasks()
                self.refresh_completed_tasks()
            else:
                QMessageBox.critical(self, "Error", "Failed to complete task.")
            return

        if not self._confirm_yes_no(
            "Complete Tasks",
            f"Mark {len(pairs)} selected tasks as complete?",
        ):
            return
        failed = []
        for task_id, title in pairs:
            if not complete_task(self.user_id, task_id):
                failed.append(title)
        self._report_batch_result(
            failed,
            success_one="Task marked as completed!",
            success_many=f"Marked {len(pairs)} tasks as completed!",
            count=len(pairs),
        )
        self.refresh_active_tasks()
        self.refresh_completed_tasks()

    @handle_errors(
        "deleting selected tasks from table", user_friendly=True, default_return=None
    )
    def _delete_selected_from_table(self, table, *, permanent: bool):
        """Delete all selected rows in the given table."""
        pairs = self.get_selected_task_pairs(table)
        if not pairs:
            QMessageBox.warning(self, "No Selection", "Please select a task to delete.")
            return

        count = len(pairs)
        if count == 1:
            title = pairs[0][1]
            if permanent:
                box_title = "Delete Completed Task"
                prompt = (
                    f"Are you sure you want to permanently delete '{title}'?\n\n"
                    "This action cannot be undone."
                )
            else:
                box_title = "Delete Task"
                prompt = (
                    f"Are you sure you want to delete '{title}'?\n\n"
                    "This action cannot be undone."
                )
        elif permanent:
            box_title = "Delete Tasks"
            prompt = (
                f"Are you sure you want to permanently delete {count} selected tasks?\n\n"
                "This action cannot be undone."
            )
        else:
            box_title = "Delete Tasks"
            prompt = (
                f"Are you sure you want to delete {count} selected tasks?\n\n"
                "This action cannot be undone."
            )

        if not self._confirm_yes_no(box_title, prompt):
            return

        failed = []
        for task_id, title in pairs:
            if not delete_task(self.user_id, task_id):
                failed.append(title)
        if failed:
            if count == 1:
                QMessageBox.critical(self, "Error", "Failed to delete task.")
            else:
                QMessageBox.critical(
                    self,
                    "Error",
                    f"Failed to delete {len(failed)} task(s): {', '.join(failed)}.",
                )
        elif permanent:
            message = (
                "Task deleted permanently!"
                if count == 1
                else f"Deleted {count} tasks permanently!"
            )
            QMessageBox.information(self, "Success", message)
        else:
            message = (
                "Task deleted successfully!"
                if count == 1
                else f"Deleted {count} tasks successfully!"
            )
            QMessageBox.information(self, "Success", message)

        if table is self.ui.tableWidget_active_tasks:
            self.refresh_active_tasks()
        else:
            self.refresh_completed_tasks()

    @handle_errors("deleting task", user_friendly=True, default_return=None)
    def delete_selected_task(self):
        """Delete the selected active task(s)."""
        self._delete_selected_from_table(
            self.ui.tableWidget_active_tasks, permanent=False
        )

    @handle_errors("restoring task", user_friendly=True, default_return=None)
    def restore_selected_task(self):
        """Restore selected completed task(s) to active status."""
        pairs = self.get_selected_task_pairs(self.ui.tableWidget_completed_tasks)
        if not pairs:
            QMessageBox.warning(
                self, "No Selection", "Please select a task to restore."
            )
            return

        from tasks import restore_task

        count = len(pairs)
        if count == 1:
            prompt = (
                f"Are you sure you want to restore '{pairs[0][1]}' to active status?"
            )
        else:
            prompt = f"Are you sure you want to restore {count} selected tasks to active status?"
        if not self._confirm_yes_no("Restore Task", prompt):
            return

        failed = []
        for task_id, title in pairs:
            if not restore_task(self.user_id, task_id):
                failed.append(title)
        self._report_batch_result(
            failed,
            success_one="Task restored successfully!",
            success_many=f"Restored {count} tasks successfully!",
            count=count,
        )
        self.refresh_active_tasks()
        self.refresh_completed_tasks()

    @handle_errors("deleting completed task", user_friendly=True, default_return=None)
    def delete_completed_task(self):
        """Permanently delete selected completed task(s)."""
        self._delete_selected_from_table(
            self.ui.tableWidget_completed_tasks, permanent=True
        )
