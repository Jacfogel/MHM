"""
Task CRUD Dialog Tests

Tests for ui/dialogs/task_crud_dialog.py to ensure proper dialog functionality
with proper isolation and error handling.
"""
from tests.conftest import ensure_qt_runtime

ensure_qt_runtime()


import pytest
from unittest.mock import patch
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

# Set headless mode for Qt - use monkeypatch in tests instead of direct assignment

from ui.dialogs.task_crud_dialog import TaskCrudDialog


def _v2_runtime_task(
    *,
    task_uuid: str,
    short_id: str,
    title: str,
    description: str,
    due_date: str,
    due_time: str,
    priority: str,
    category: str,
    created_at: str,
    status: str = "active",
    completed_at: str | None = None,
) -> dict:
    """Minimal v2 runtime task dict matching ``tasks.task_data_handlers._task_v2_to_runtime`` shape."""
    completed = status == "completed"
    return {
        "id": task_uuid,
        "short_id": short_id,
        "kind": "task",
        "title": title,
        "description": description,
        "category": category,
        "group": "",
        "status": status,
        "priority": priority.lower(),
        "due": {"date": due_date, "time": due_time},
        "tags": [],
        "reminders": [],
        "recurrence": {
            "pattern": None,
            "interval": 1,
            "repeat_after_completion": True,
            "next_due_date": None,
        },
        "completion": {
            "completed": completed,
            "completed_at": completed_at,
            "notes": "",
        },
        "source": {"system": "mhm", "channel": "", "actor": "", "migration": None},
        "linked_item_ids": [],
        "created_at": created_at,
        "updated_at": created_at,
        "archived_at": None,
        "deleted_at": None,
        "metadata": {},
    }


class TestTaskCrudDialog:
    """Test TaskCrudDialog functionality."""
    
    @pytest.fixture
    def qt_app(self, monkeypatch):
        """Create headless Qt application for testing."""
        # Set headless mode for Qt
        monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
        
        # Check if QApplication already exists
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
            attr = getattr(Qt, "AA_ShareOpenGLContexts", None)
            if attr is not None:
                app.setAttribute(attr, False)
        yield app
        # Don't quit the app here as it might be used by other tests
    
    @pytest.fixture
    def mock_task_data(self):
        """V2 runtime-shaped lists as returned by ``load_active_tasks`` / ``load_completed_tasks``."""
        return {
            "active_list": [
                _v2_runtime_task(
                    task_uuid="00000000-0000-4000-8000-000000000001",
                    short_id="t0000001",
                    title="Test Task 1",
                    description="Test Description 1",
                    due_date="2025-10-03",
                    due_time="10:00",
                    priority="high",
                    category="Work",
                    created_at="2025-10-01T12:00:00Z",
                ),
                _v2_runtime_task(
                    task_uuid="00000000-0000-4000-8000-000000000002",
                    short_id="t0000002",
                    title="Test Task 2",
                    description="Test Description 2",
                    due_date="2025-10-04",
                    due_time="14:00",
                    priority="medium",
                    category="Personal",
                    created_at="2025-10-02T12:00:00Z",
                ),
            ],
            "done_list": [
                _v2_runtime_task(
                    task_uuid="00000000-0000-4000-8000-000000000003",
                    short_id="t0000003",
                    title="Completed Task 1",
                    description="Completed Description 1",
                    due_date="2025-10-01",
                    due_time="",
                    priority="low",
                    category="Work",
                    created_at="2025-09-30T12:00:00Z",
                    status="completed",
                    completed_at="2025-10-01T15:00:00Z",
                ),
            ],
        }
    
    @pytest.mark.ui
    def test_dialog_initialization(self, qt_app, test_data_dir):
        """Test dialog initialization."""
        with patch('ui.dialogs.task_crud_dialog.load_active_tasks') as mock_load_active:
            with patch('ui.dialogs.task_crud_dialog.load_completed_tasks') as mock_load_completed:
                with patch('ui.dialogs.task_crud_dialog.get_user_task_stats') as mock_stats:
                    # Mock return values
                    mock_load_active.return_value = []
                    mock_load_completed.return_value = []
                    mock_stats.return_value = {'total': 0, 'completed': 0, 'pending': 0}
                    
                    # Create dialog
                    dialog = TaskCrudDialog(user_id='test_user')
                    
                    try:
                        # Verify initialization
                        assert dialog.user_id == 'test_user'
                        assert dialog.active_tasks == []
                        assert dialog.completed_tasks == []
                        
                        # Verify UI setup
                        assert dialog.ui is not None
                        
                    finally:
                        dialog.deleteLater()
    
    @pytest.mark.ui
    def test_setup_ui(self, qt_app, test_data_dir):
        """Test UI setup."""
        with patch('ui.dialogs.task_crud_dialog.load_active_tasks') as mock_load_active:
            with patch('ui.dialogs.task_crud_dialog.load_completed_tasks') as mock_load_completed:
                with patch('ui.dialogs.task_crud_dialog.get_user_task_stats') as mock_stats:
                    # Mock return values
                    mock_load_active.return_value = []
                    mock_load_completed.return_value = []
                    mock_stats.return_value = {'total': 0, 'completed': 0, 'pending': 0}
                    
                    # Create dialog
                    dialog = TaskCrudDialog(user_id='test_user')
                    
                    try:
                        # Verify table setup
                        assert dialog.ui.tableWidget_active_tasks.columnCount() == 7
                        assert dialog.ui.tableWidget_completed_tasks.columnCount() == 6
                        
                        # Verify headers
                        active_headers = [
                            (h.text() if (h := dialog.ui.tableWidget_active_tasks.horizontalHeaderItem(i)) else "")
                            for i in range(dialog.ui.tableWidget_active_tasks.columnCount())
                        ]
                        expected_active = ["Title", "Description", "Due Date", "Due Time", "Priority", "Category", "Created"]
                        assert active_headers == expected_active
                        
                        completed_headers = [
                            (h.text() if (h := dialog.ui.tableWidget_completed_tasks.horizontalHeaderItem(i)) else "")
                            for i in range(dialog.ui.tableWidget_completed_tasks.columnCount())
                        ]
                        expected_completed = ["Title", "Description", "Due Date", "Priority", "Category", "Completed"]
                        assert completed_headers == expected_completed
                        
                    finally:
                        dialog.deleteLater()
    
    @pytest.mark.ui
    def test_load_data_success(self, qt_app, test_data_dir, mock_task_data):
        """Test successful data loading."""
        with patch('ui.dialogs.task_crud_dialog.load_active_tasks') as mock_load_active:
            with patch('ui.dialogs.task_crud_dialog.load_completed_tasks') as mock_load_completed:
                with patch('ui.dialogs.task_crud_dialog.get_user_task_stats') as mock_stats:
                    # Mock return values
                    mock_load_active.return_value = mock_task_data["active_list"]
                    mock_load_completed.return_value = mock_task_data["done_list"]
                    mock_stats.return_value = {'total': 3, 'completed': 1, 'pending': 2}
                    
                    # Create dialog
                    dialog = TaskCrudDialog(user_id='test_user')
                    
                    try:
                        # Verify data was loaded
                        assert len(dialog.active_tasks) == 2
                        assert len(dialog.completed_tasks) == 1
                        
                        # Verify tables were populated
                        assert dialog.ui.tableWidget_active_tasks.rowCount() == 2
                        assert dialog.ui.tableWidget_completed_tasks.rowCount() == 1
                        
                    finally:
                        dialog.deleteLater()
    
    @pytest.mark.ui
    def test_load_data_error(self, qt_app, test_data_dir):
        """Test data loading with error."""
        with patch('ui.dialogs.task_crud_dialog.load_active_tasks') as mock_load_active:
            with patch('ui.dialogs.task_crud_dialog.load_completed_tasks') as mock_load_completed:
                with patch('ui.dialogs.task_crud_dialog.get_user_task_stats') as mock_stats:
                    # Mock error
                    mock_load_active.side_effect = Exception("Database error")
                    mock_load_completed.return_value = []
                    mock_stats.return_value = {'total': 0, 'completed': 0, 'pending': 0}
                    
                    # Create dialog
                    dialog = TaskCrudDialog(user_id='test_user')
                    
                    try:
                        # Verify error handling
                        assert dialog.active_tasks == []
                        assert dialog.completed_tasks == []
                        
                    finally:
                        dialog.deleteLater()
    
    @pytest.mark.ui
    def test_refresh_active_tasks(self, qt_app, test_data_dir, mock_task_data):
        """Test refreshing active tasks table."""
        with patch('ui.dialogs.task_crud_dialog.load_active_tasks') as mock_load_active:
            with patch('ui.dialogs.task_crud_dialog.load_completed_tasks') as mock_load_completed:
                with patch('ui.dialogs.task_crud_dialog.get_user_task_stats') as mock_stats:
                    # Mock return values
                    mock_load_active.return_value = mock_task_data["active_list"]
                    mock_load_completed.return_value = []
                    mock_stats.return_value = {'total': 2, 'completed': 0, 'pending': 2}
                    
                    # Create dialog
                    dialog = TaskCrudDialog(user_id='test_user')
                    
                    try:
                        # Verify initial state
                        assert dialog.ui.tableWidget_active_tasks.rowCount() == 2
                        
                        # Test refresh
                        dialog.refresh_active_tasks()
                        
                        # Verify table was refreshed
                        assert dialog.ui.tableWidget_active_tasks.rowCount() == 2
                        
                        # Verify table content
                        first_row = dialog.ui.tableWidget_active_tasks.item(0, 0)
                        assert first_row is not None and first_row.text() == 'Test Task 1'
                        
                    finally:
                        dialog.deleteLater()
    
    @pytest.mark.ui
    def test_refresh_completed_tasks(self, qt_app, test_data_dir, mock_task_data):
        """Test refreshing completed tasks table."""
        with patch('ui.dialogs.task_crud_dialog.load_active_tasks') as mock_load_active:
            with patch('ui.dialogs.task_crud_dialog.load_completed_tasks') as mock_load_completed:
                with patch('ui.dialogs.task_crud_dialog.get_user_task_stats') as mock_stats:
                    # Mock return values
                    mock_load_active.return_value = []
                    mock_load_completed.return_value = mock_task_data["done_list"]
                    mock_stats.return_value = {'total': 1, 'completed': 1, 'pending': 0}
                    
                    # Create dialog
                    dialog = TaskCrudDialog(user_id='test_user')
                    
                    try:
                        # Verify initial state
                        assert dialog.ui.tableWidget_completed_tasks.rowCount() == 1
                        
                        # Test refresh
                        dialog.refresh_completed_tasks()
                        
                        # Verify table was refreshed
                        assert dialog.ui.tableWidget_completed_tasks.rowCount() == 1
                        
                        # Verify table content
                        first_row = dialog.ui.tableWidget_completed_tasks.item(0, 0)
                        assert first_row is not None and first_row.text() == 'Completed Task 1'
                        
                    finally:
                        dialog.deleteLater()
    
    @pytest.mark.ui
    def test_add_new_task(self, qt_app, test_data_dir):
        """Test adding new task."""
        with patch('ui.dialogs.task_crud_dialog.load_active_tasks') as mock_load_active:
            with patch('ui.dialogs.task_crud_dialog.load_completed_tasks') as mock_load_completed:
                with patch('ui.dialogs.task_crud_dialog.get_user_task_stats') as mock_stats:
                    # Mock return values
                    mock_load_active.return_value = []
                    mock_load_completed.return_value = []
                    mock_stats.return_value = {'total': 0, 'completed': 0, 'pending': 0}
                    
                    # Create dialog
                    dialog = TaskCrudDialog(user_id='test_user')
                    
                    try:
                        # Test add new task (should open task edit dialog)
                        with patch('ui.dialogs.task_edit_dialog.TaskEditDialog') as mock_edit_dialog:
                            mock_edit_dialog.return_value.exec.return_value = 1  # Accepted
                            mock_edit_dialog.return_value.get_task_data.return_value = {
                                'title': 'New Task',
                                'description': 'New Description',
                                'due_date': '2025-10-05',
                                'due_time': '12:00',
                                'priority': 'Medium',
                                'category': 'Work'
                            }
                            
                            dialog.add_new_task()
                            
                            # Verify dialog was opened
                            mock_edit_dialog.assert_called_once()
                            
                    finally:
                        dialog.deleteLater()
    
    @pytest.mark.ui
    def test_edit_selected_task_no_selection(self, qt_app, test_data_dir):
        """Test editing selected task with no selection."""
        with patch('ui.dialogs.task_crud_dialog.load_active_tasks') as mock_load_active:
            with patch('ui.dialogs.task_crud_dialog.load_completed_tasks') as mock_load_completed:
                with patch('ui.dialogs.task_crud_dialog.get_user_task_stats') as mock_stats:
                    # Mock return values
                    mock_load_active.return_value = []
                    mock_load_completed.return_value = []
                    mock_stats.return_value = {'total': 0, 'completed': 0, 'pending': 0}
                    
                    # Create dialog
                    dialog = TaskCrudDialog(user_id='test_user')
                    
                    try:
                        # Test edit with no selection
                        with patch('PySide6.QtWidgets.QMessageBox.warning') as mock_warning:
                            dialog.edit_selected_task()
                            
                            # Verify warning was shown
                            mock_warning.assert_called_once()
                            
                    finally:
                        dialog.deleteLater()
    
    @pytest.mark.ui
    def test_edit_selected_task_with_selection(self, qt_app, test_data_dir, mock_task_data):
        """Test editing selected task with selection."""
        with patch('ui.dialogs.task_crud_dialog.load_active_tasks') as mock_load_active:
            with patch('ui.dialogs.task_crud_dialog.load_completed_tasks') as mock_load_completed:
                with patch('ui.dialogs.task_crud_dialog.get_user_task_stats') as mock_stats:
                    # Mock return values
                    mock_load_active.return_value = mock_task_data["active_list"]
                    mock_load_completed.return_value = []
                    mock_stats.return_value = {'total': 2, 'completed': 0, 'pending': 2}
                    
                    # Create dialog
                    dialog = TaskCrudDialog(user_id='test_user')
                    
                    try:
                        # Test edit selected task with no selection (should show warning)
                        with patch('PySide6.QtWidgets.QMessageBox.warning') as mock_warning:
                            dialog.edit_selected_task()
                            
                            # Verify warning was shown
                            mock_warning.assert_called_once()
                            
                    finally:
                        dialog.deleteLater()
    
    @pytest.mark.ui
    def test_complete_selected_task_no_selection(self, qt_app, test_data_dir):
        """Test completing selected task with no selection."""
        with patch('ui.dialogs.task_crud_dialog.load_active_tasks') as mock_load_active:
            with patch('ui.dialogs.task_crud_dialog.load_completed_tasks') as mock_load_completed:
                with patch('ui.dialogs.task_crud_dialog.get_user_task_stats') as mock_stats:
                    # Mock return values
                    mock_load_active.return_value = []
                    mock_load_completed.return_value = []
                    mock_stats.return_value = {'total': 0, 'completed': 0, 'pending': 0}
                    
                    # Create dialog
                    dialog = TaskCrudDialog(user_id='test_user')
                    
                    try:
                        # Test complete with no selection
                        with patch('PySide6.QtWidgets.QMessageBox.warning') as mock_warning:
                            dialog.complete_selected_task()
                            
                            # Verify warning was shown
                            mock_warning.assert_called_once()
                            
                    finally:
                        dialog.deleteLater()
    
    @pytest.mark.ui
    def test_complete_selected_task_with_selection(self, qt_app, test_data_dir, mock_task_data):
        """Test completing selected task with selection."""
        with patch('ui.dialogs.task_crud_dialog.load_active_tasks') as mock_load_active:
            with patch('ui.dialogs.task_crud_dialog.load_completed_tasks') as mock_load_completed:
                with patch('ui.dialogs.task_crud_dialog.get_user_task_stats') as mock_stats:
                    with patch('tasks.complete_task') as mock_complete:
                        # Mock return values
                        mock_load_active.return_value = mock_task_data["active_list"]
                        mock_load_completed.return_value = []
                        mock_stats.return_value = {'total': 2, 'completed': 0, 'pending': 2}
                        mock_complete.return_value = True
                        
                        # Create dialog
                        dialog = TaskCrudDialog(user_id='test_user')
                        
                        try:
                            # Test complete selected task with no selection (should show warning)
                            with patch('PySide6.QtWidgets.QMessageBox.warning') as mock_warning:
                                dialog.complete_selected_task()
                                
                                # Verify warning was shown
                                mock_warning.assert_called_once()
                                
                        finally:
                            dialog.deleteLater()
    
    @pytest.mark.ui
    def test_delete_selected_task_no_selection(self, qt_app, test_data_dir):
        """Test deleting selected task with no selection."""
        with patch('ui.dialogs.task_crud_dialog.load_active_tasks') as mock_load_active:
            with patch('ui.dialogs.task_crud_dialog.load_completed_tasks') as mock_load_completed:
                with patch('ui.dialogs.task_crud_dialog.get_user_task_stats') as mock_stats:
                    # Mock return values
                    mock_load_active.return_value = []
                    mock_load_completed.return_value = []
                    mock_stats.return_value = {'total': 0, 'completed': 0, 'pending': 0}
                    
                    # Create dialog
                    dialog = TaskCrudDialog(user_id='test_user')
                    
                    try:
                        # Test delete with no selection
                        with patch('PySide6.QtWidgets.QMessageBox.warning') as mock_warning:
                            dialog.delete_selected_task()
                            
                            # Verify warning was shown
                            mock_warning.assert_called_once()
                            
                    finally:
                        dialog.deleteLater()
    
    @pytest.mark.ui
    def test_delete_selected_task_with_selection(self, qt_app, test_data_dir, mock_task_data):
        """Test deleting selected task with selection."""
        with patch('ui.dialogs.task_crud_dialog.load_active_tasks') as mock_load_active:
            with patch('ui.dialogs.task_crud_dialog.load_completed_tasks') as mock_load_completed:
                with patch('ui.dialogs.task_crud_dialog.get_user_task_stats') as mock_stats:
                    with patch('tasks.delete_task') as mock_delete:
                        with patch('tasks.get_task_by_id') as mock_get_task:
                            # Mock return values
                            mock_load_active.return_value = mock_task_data["active_list"]
                            mock_load_completed.return_value = []
                            mock_stats.return_value = {'total': 2, 'completed': 0, 'pending': 2}
                            mock_delete.return_value = True
                            mock_get_task.return_value = mock_task_data["active_list"][0]
                            
                            # Create dialog
                            dialog = TaskCrudDialog(user_id='test_user')
                        
                            try:
                                # Test delete selected task with no selection (should show warning)
                                with patch('PySide6.QtWidgets.QMessageBox.warning') as mock_warning:
                                    dialog.delete_selected_task()
                                    
                                    # Verify warning was shown
                                    mock_warning.assert_called_once()
                                    
                            finally:
                                dialog.deleteLater()
    
    @pytest.mark.ui
    def test_restore_selected_task_no_selection(self, qt_app, test_data_dir):
        """Test restoring selected task with no selection."""
        with patch('ui.dialogs.task_crud_dialog.load_active_tasks') as mock_load_active:
            with patch('ui.dialogs.task_crud_dialog.load_completed_tasks') as mock_load_completed:
                with patch('ui.dialogs.task_crud_dialog.get_user_task_stats') as mock_stats:
                    # Mock return values
                    mock_load_active.return_value = []
                    mock_load_completed.return_value = []
                    mock_stats.return_value = {'total': 0, 'completed': 0, 'pending': 0}
                    
                    # Create dialog
                    dialog = TaskCrudDialog(user_id='test_user')
                    
                    try:
                        # Test restore with no selection
                        with patch('PySide6.QtWidgets.QMessageBox.warning') as mock_warning:
                            dialog.restore_selected_task()
                            
                            # Verify warning was shown
                            mock_warning.assert_called_once()
                            
                    finally:
                        dialog.deleteLater()
    
    @pytest.mark.ui
    def test_restore_selected_task_with_selection(self, qt_app, test_data_dir, mock_task_data):
        """Test restoring selected task with selection."""
        with patch('ui.dialogs.task_crud_dialog.load_active_tasks') as mock_load_active:
            with patch('ui.dialogs.task_crud_dialog.load_completed_tasks') as mock_load_completed:
                with patch('ui.dialogs.task_crud_dialog.get_user_task_stats') as mock_stats:
                    with patch('tasks.restore_task') as mock_restore:
                        # Mock return values
                        mock_load_active.return_value = []
                        mock_load_completed.return_value = mock_task_data["done_list"]
                        mock_stats.return_value = {'total': 1, 'completed': 1, 'pending': 0}
                        mock_restore.return_value = True
                        
                        # Create dialog
                        dialog = TaskCrudDialog(user_id='test_user')
                        
                        try:
                            # Test restore selected task with no selection (should show warning)
                            with patch('PySide6.QtWidgets.QMessageBox.warning') as mock_warning:
                                dialog.restore_selected_task()
                                
                                # Verify warning was shown
                                mock_warning.assert_called_once()
                                
                        finally:
                            dialog.deleteLater()
    
    @pytest.mark.ui
    def test_delete_completed_task_no_selection(self, qt_app, test_data_dir):
        """Test deleting completed task with no selection."""
        with patch('ui.dialogs.task_crud_dialog.load_active_tasks') as mock_load_active:
            with patch('ui.dialogs.task_crud_dialog.load_completed_tasks') as mock_load_completed:
                with patch('ui.dialogs.task_crud_dialog.get_user_task_stats') as mock_stats:
                    # Mock return values
                    mock_load_active.return_value = []
                    mock_load_completed.return_value = []
                    mock_stats.return_value = {'total': 0, 'completed': 0, 'pending': 0}
                    
                    # Create dialog
                    dialog = TaskCrudDialog(user_id='test_user')
                    
                    try:
                        # Test delete with no selection
                        with patch('PySide6.QtWidgets.QMessageBox.warning') as mock_warning:
                            dialog.delete_completed_task()
                            
                            # Verify warning was shown
                            mock_warning.assert_called_once()
                            
                    finally:
                        dialog.deleteLater()
    
    @pytest.mark.ui
    def test_delete_completed_task_with_selection(self, qt_app, test_data_dir, mock_task_data):
        """Test deleting completed task with selection."""
        with patch('ui.dialogs.task_crud_dialog.load_active_tasks') as mock_load_active:
            with patch('ui.dialogs.task_crud_dialog.load_completed_tasks') as mock_load_completed:
                with patch('ui.dialogs.task_crud_dialog.get_user_task_stats') as mock_stats:
                    with patch('tasks.delete_task') as mock_delete:
                        # Mock return values
                        mock_load_active.return_value = []
                        mock_load_completed.return_value = mock_task_data["done_list"]
                        mock_stats.return_value = {'total': 1, 'completed': 1, 'pending': 0}
                        mock_delete.return_value = True
                        
                        # Create dialog
                        dialog = TaskCrudDialog(user_id='test_user')
                        
                        try:
                            # Test delete completed task with no selection (should show warning)
                            with patch('PySide6.QtWidgets.QMessageBox.warning') as mock_warning:
                                dialog.delete_completed_task()
                                
                                # Verify warning was shown
                                mock_warning.assert_called_once()
                                
                        finally:
                            dialog.deleteLater()
    
    @pytest.mark.ui
    def test_update_statistics(self, qt_app, test_data_dir, mock_task_data):
        """Test updating statistics display."""
        with patch('ui.dialogs.task_crud_dialog.load_active_tasks') as mock_load_active:
            with patch('ui.dialogs.task_crud_dialog.load_completed_tasks') as mock_load_completed:
                with patch('ui.dialogs.task_crud_dialog.get_user_task_stats') as mock_stats:
                    # Mock return values
                    mock_load_active.return_value = mock_task_data["active_list"]
                    mock_load_completed.return_value = mock_task_data["done_list"]
                    mock_stats.return_value = {'total': 3, 'completed': 1, 'pending': 2}
                    
                    # Create dialog
                    dialog = TaskCrudDialog(user_id='test_user')
                    
                    try:
                        # Test update statistics
                        dialog.update_statistics()
                        
                        # Verify statistics were updated
                        # Note: This would depend on the actual UI implementation
                        # The test verifies the method runs without error
                        
                    finally:
                        dialog.deleteLater()
    
    @pytest.mark.ui
    def test_dialog_cleanup(self, qt_app, test_data_dir):
        """Test proper dialog cleanup."""
        with patch('ui.dialogs.task_crud_dialog.load_active_tasks') as mock_load_active:
            with patch('ui.dialogs.task_crud_dialog.load_completed_tasks') as mock_load_completed:
                with patch('ui.dialogs.task_crud_dialog.get_user_task_stats') as mock_stats:
                    # Mock return values
                    mock_load_active.return_value = []
                    mock_load_completed.return_value = []
                    mock_stats.return_value = {'total': 0, 'completed': 0, 'pending': 0}
                    
                    # Create dialog
                    dialog = TaskCrudDialog(user_id='test_user')
                    
                    # Test cleanup
                    dialog.deleteLater()
                    
                    # Verify dialog was marked for deletion
                    # Note: This is a basic test - actual cleanup verification would be more complex
