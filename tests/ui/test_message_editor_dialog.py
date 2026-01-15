"""
Comprehensive tests for message editor dialog.

Tests the actual UI behavior, user interactions, and side effects for:
- Message editor dialog (PySide6)
- Message CRUD operations
- Message validation
- Error handling and recovery
"""

from tests.conftest import ensure_qt_runtime

ensure_qt_runtime()

import pytest
from unittest.mock import patch, Mock, MagicMock
from PySide6.QtWidgets import QApplication, QTableWidgetItem
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
import logging
logger = logging.getLogger("mhm_tests")

# Do not modify sys.path; rely on package imports
from ui.dialogs.message_editor_dialog import (
    MessageEditDialog,
    MessageEditorDialog,
    open_message_editor_dialog
)
from tests.test_utilities import TestUserFactory

# Create QApplication instance for testing
@pytest.fixture(scope="session")
def qapp():
    """Create QApplication instance for UI testing."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app
    # Don't quit the app as it might be used by other tests


class TestMessageEditDialogInitialization:
    """Test message edit dialog initialization."""
    
    @pytest.fixture
    def dialog_add(self, qapp, test_data_dir):
        """Create message edit dialog for adding messages."""
        # Create test user
        user_id = "test_message_user"
        TestUserFactory.create_basic_user(user_id, enable_checkins=True, test_data_dir=test_data_dir)
        
        # Get actual user ID
        from core.user_data_handlers import get_user_id_by_identifier
        actual_user_id = get_user_id_by_identifier(user_id)
        if actual_user_id is None:
            actual_user_id = user_id
        
        # Create dialog for adding (no message_data)
        dialog = MessageEditDialog(parent=None, user_id=actual_user_id, category="motivation")
        
        yield dialog
        
        # Cleanup
        dialog.deleteLater()
    
    @pytest.fixture
    def dialog_edit(self, qapp, test_data_dir):
        """Create message edit dialog for editing messages."""
        # Create test user
        user_id = "test_message_user_edit"
        TestUserFactory.create_basic_user(user_id, enable_checkins=True, test_data_dir=test_data_dir)
        
        # Get actual user ID
        from core.user_data_handlers import get_user_id_by_identifier
        actual_user_id = get_user_id_by_identifier(user_id)
        if actual_user_id is None:
            actual_user_id = user_id
        
        # Create message data for editing
        message_data = {
            'message_id': 'test_message_id',
            'message': 'Test message text',
            'days': ['monday', 'tuesday'],
            'time_periods': ['morning', 'afternoon']
        }
        
        # Create dialog for editing
        dialog = MessageEditDialog(parent=None, user_id=actual_user_id, category="motivation", message_data=message_data)
        
        yield dialog
        
        # Cleanup
        dialog.deleteLater()
    
    @pytest.mark.ui
    def test_dialog_initialization_add_mode(self, dialog_add):
        """Test: Dialog initializes correctly in add mode"""
        # Arrange: Dialog is created in fixture
        
        # Act: (No action needed - initialization happens in fixture)
        
        # Assert: Verify initial state
        assert dialog_add is not None, "Dialog should be created"
        assert not dialog_add.isVisible(), "Dialog should not be visible during testing"
        assert "Add Message" in dialog_add.windowTitle(), "Dialog should have correct title for add mode"
        assert dialog_add.is_edit == False, "Dialog should be in add mode"
        assert dialog_add.user_id is not None, "User ID should be set"
        assert dialog_add.category == "motivation", "Category should be set"
        
        # Assert: Verify UI components exist
        assert hasattr(dialog_add, 'message_text'), "Message text widget should exist"
        assert hasattr(dialog_add, 'day_checkboxes'), "Day checkboxes should exist"
        assert hasattr(dialog_add, 'period_checkboxes'), "Period checkboxes should exist"
        assert hasattr(dialog_add, 'button_box'), "Button box should exist"
    
    @pytest.mark.ui
    def test_dialog_initialization_edit_mode(self, dialog_edit):
        """Test: Dialog initializes correctly in edit mode"""
        # Arrange: Dialog is created in fixture
        
        # Act: (No action needed - initialization happens in fixture)
        
        # Assert: Verify initial state
        assert dialog_edit is not None, "Dialog should be created"
        assert "Edit Message" in dialog_edit.windowTitle(), "Dialog should have correct title for edit mode"
        assert dialog_edit.is_edit == True, "Dialog should be in edit mode"
        assert dialog_edit.message_data is not None, "Message data should be set"
        
        # Assert: Verify message data is loaded
        assert dialog_edit.message_text.toPlainText() == "Test message text", "Message text should be loaded"
        
        # Assert: Verify days are checked
        assert dialog_edit.day_checkboxes['monday'].isChecked(), "Monday should be checked"
        assert dialog_edit.day_checkboxes['tuesday'].isChecked(), "Tuesday should be checked"
        assert not dialog_edit.day_checkboxes['wednesday'].isChecked(), "Wednesday should not be checked"
        
        # Assert: Verify periods are checked
        assert dialog_edit.period_checkboxes['morning'].isChecked(), "Morning should be checked"
        assert dialog_edit.period_checkboxes['afternoon'].isChecked(), "Afternoon should be checked"
        assert not dialog_edit.period_checkboxes['evening'].isChecked(), "Evening should not be checked"


class TestMessageEditDialogValidation:
    """Test message edit dialog validation."""
    
    @pytest.fixture
    def dialog(self, qapp, test_data_dir):
        """Create message edit dialog for testing."""
        # Create test user
        user_id = "test_message_user_validation"
        TestUserFactory.create_basic_user(user_id, enable_checkins=True, test_data_dir=test_data_dir)
        
        # Get actual user ID
        from core.user_data_handlers import get_user_id_by_identifier
        actual_user_id = get_user_id_by_identifier(user_id)
        if actual_user_id is None:
            actual_user_id = user_id
        
        # Create dialog
        dialog = MessageEditDialog(parent=None, user_id=actual_user_id, category="motivation")
        
        yield dialog
        
        # Cleanup
        dialog.deleteLater()
    
    @pytest.mark.ui
    def test_validation_empty_message_text(self, dialog):
        """Test: Validation fails when message text is empty"""
        # Arrange: Dialog is created in fixture
        dialog.message_text.setPlainText("")
        
        # Act: Try to save (should show validation error)
        with patch('PySide6.QtWidgets.QMessageBox.warning') as mock_warning:
            dialog.save_message()
            
            # Assert: Should show validation error
            mock_warning.assert_called_once()
            call_args = mock_warning.call_args
            assert "Message text is required" in str(call_args), "Should show message text validation error"
    
    @pytest.mark.ui
    def test_validation_no_days_selected(self, dialog):
        """Test: Validation fails when no days are selected"""
        # Arrange: Dialog is created in fixture
        dialog.message_text.setPlainText("Test message")
        # Uncheck all days
        for checkbox in dialog.day_checkboxes.values():
            checkbox.setChecked(False)
        # Check at least one period
        dialog.period_checkboxes['morning'].setChecked(True)
        
        # Act: Try to save (should show validation error)
        with patch('PySide6.QtWidgets.QMessageBox.warning') as mock_warning:
            dialog.save_message()
            
            # Assert: Should show validation error
            mock_warning.assert_called_once()
            call_args = mock_warning.call_args
            assert "At least one day must be selected" in str(call_args), "Should show days validation error"
    
    @pytest.mark.ui
    def test_validation_no_periods_selected(self, dialog):
        """Test: Validation fails when no time periods are selected"""
        # Arrange: Dialog is created in fixture
        dialog.message_text.setPlainText("Test message")
        # Check at least one day
        dialog.day_checkboxes['monday'].setChecked(True)
        # Uncheck all periods
        for checkbox in dialog.period_checkboxes.values():
            checkbox.setChecked(False)
        
        # Act: Try to save (should show validation error)
        with patch('PySide6.QtWidgets.QMessageBox.warning') as mock_warning:
            dialog.save_message()
            
            # Assert: Should show validation error
            mock_warning.assert_called_once()
            call_args = mock_warning.call_args
            assert "At least one time period must be selected" in str(call_args), "Should show periods validation error"
    
    @pytest.mark.ui
    def test_validation_success(self, dialog):
        """Test: Validation succeeds when all fields are valid"""
        # Arrange: Dialog is created in fixture
        dialog.message_text.setPlainText("Test message")
        dialog.day_checkboxes['monday'].setChecked(True)
        dialog.period_checkboxes['morning'].setChecked(True)
        
        # Verify dialog is in add mode
        assert dialog.is_edit == False, "Dialog should be in add mode"
        
        # Act: Try to save (should succeed)
        with patch('ui.dialogs.message_editor_dialog.add_message') as mock_add, \
             patch('PySide6.QtWidgets.QMessageBox.information') as mock_info, \
             patch.object(dialog, 'accept') as mock_accept:
            dialog.save_message()
            
            # Assert: Should call add_message (validation passed, so save should proceed)
            mock_add.assert_called_once()
            # Assert: Should show success message
            mock_info.assert_called_once()
            call_args = mock_info.call_args
            assert "Message added successfully" in str(call_args), "Should show success message"
            # Assert: Should accept dialog
            mock_accept.assert_called_once()


class TestMessageEditDialogSave:
    """Test message edit dialog save functionality."""
    
    @pytest.fixture
    def dialog_add(self, qapp, test_data_dir):
        """Create message edit dialog for adding messages."""
        # Create test user
        user_id = "test_message_user_save"
        TestUserFactory.create_basic_user(user_id, enable_checkins=True, test_data_dir=test_data_dir)
        
        # Get actual user ID
        from core.user_data_handlers import get_user_id_by_identifier
        actual_user_id = get_user_id_by_identifier(user_id)
        if actual_user_id is None:
            actual_user_id = user_id
        
        # Create dialog
        dialog = MessageEditDialog(parent=None, user_id=actual_user_id, category="motivation")
        
        yield dialog
        
        # Cleanup
        dialog.deleteLater()
    
    @pytest.fixture
    def dialog_edit(self, qapp, test_data_dir):
        """Create message edit dialog for editing messages."""
        # Create test user
        user_id = "test_message_user_save_edit"
        TestUserFactory.create_basic_user(user_id, enable_checkins=True, test_data_dir=test_data_dir)
        
        # Get actual user ID
        from core.user_data_handlers import get_user_id_by_identifier
        actual_user_id = get_user_id_by_identifier(user_id)
        if actual_user_id is None:
            actual_user_id = user_id
        
        # Create message data
        message_data = {
            'message_id': 'test_message_id',
            'message': 'Test message text',
            'days': ['monday'],
            'time_periods': ['morning']
        }
        
        # Create dialog
        dialog = MessageEditDialog(parent=None, user_id=actual_user_id, category="motivation", message_data=message_data)
        
        yield dialog
        
        # Cleanup
        dialog.deleteLater()
    
    @pytest.mark.ui
    def test_save_adds_new_message(self, dialog_add):
        """Test: Save adds new message correctly"""
        # Arrange: Dialog is created in fixture
        dialog_add.message_text.setPlainText("New test message")
        dialog_add.day_checkboxes['monday'].setChecked(True)
        dialog_add.day_checkboxes['tuesday'].setChecked(True)
        dialog_add.period_checkboxes['morning'].setChecked(True)
        dialog_add.period_checkboxes['afternoon'].setChecked(True)
        
        # Act: Save message
        with patch('ui.dialogs.message_editor_dialog.add_message') as mock_add, \
             patch('PySide6.QtWidgets.QMessageBox.information') as mock_info, \
             patch.object(dialog_add, 'accept') as mock_accept:
            dialog_add.save_message()
            
            # Assert: Should call add_message with correct data
            mock_add.assert_called_once()
            call_args = mock_add.call_args
            assert call_args[0][0] == dialog_add.user_id, "Should pass user_id"
            assert call_args[0][1] == dialog_add.category, "Should pass category"
            message_data = call_args[0][2]
            assert message_data['message'] == "New test message", "Should pass message text"
            assert 'monday' in message_data['days'], "Should include monday"
            assert 'tuesday' in message_data['days'], "Should include tuesday"
            assert 'morning' in message_data['time_periods'], "Should include morning"
            assert 'afternoon' in message_data['time_periods'], "Should include afternoon"
            assert 'message_id' in message_data, "Should include message_id"
            assert 'created_at' in message_data, "Should include created_at"
            
            # Assert: Should show success message
            mock_info.assert_called_once()
            # Assert: Should accept dialog
            mock_accept.assert_called_once()
    
    @pytest.mark.ui
    def test_save_edits_existing_message(self, dialog_edit):
        """Test: Save edits existing message correctly"""
        # Arrange: Dialog is created in fixture
        dialog_edit.message_text.setPlainText("Updated test message")
        dialog_edit.day_checkboxes['wednesday'].setChecked(True)
        dialog_edit.period_checkboxes['evening'].setChecked(True)
        
        # Act: Save message
        with patch('ui.dialogs.message_editor_dialog.edit_message') as mock_edit, \
             patch('PySide6.QtWidgets.QMessageBox.information') as mock_info, \
             patch.object(dialog_edit, 'accept') as mock_accept:
            dialog_edit.save_message()
            
            # Assert: Should call edit_message with correct data
            mock_edit.assert_called_once()
            call_args = mock_edit.call_args
            assert call_args[0][0] == dialog_edit.user_id, "Should pass user_id"
            assert call_args[0][1] == dialog_edit.category, "Should pass category"
            assert call_args[0][2] == 'test_message_id', "Should pass message_id"
            message_data = call_args[0][3]
            assert message_data['message'] == "Updated test message", "Should pass updated message text"
            assert 'wednesday' in message_data['days'], "Should include wednesday"
            assert 'evening' in message_data['time_periods'], "Should include evening"
            
            # Assert: Should show success message
            mock_info.assert_called_once()
            # Assert: Should accept dialog
            mock_accept.assert_called_once()
    
    @pytest.mark.ui
    def test_save_edit_fails_without_message_id(self, dialog_edit):
        """Test: Save edit fails when message_id is missing"""
        # Arrange: Dialog is created in fixture
        dialog_edit.message_data = {}  # Remove message_id
        dialog_edit.message_text.setPlainText("Updated test message")
        dialog_edit.day_checkboxes['monday'].setChecked(True)
        dialog_edit.period_checkboxes['morning'].setChecked(True)
        
        # Act: Try to save
        with patch('PySide6.QtWidgets.QMessageBox.critical') as mock_critical:
            dialog_edit.save_message()
            
            # Assert: Should show error message
            mock_critical.assert_called_once()
            call_args = mock_critical.call_args
            assert "Message ID not found" in str(call_args), "Should show message ID error"


class TestMessageEditorDialogInitialization:
    """Test message editor dialog initialization."""
    
    @pytest.fixture
    def dialog(self, qapp, test_data_dir):
        """Create message editor dialog for testing."""
        # Create test user
        user_id = "test_message_editor_user"
        TestUserFactory.create_basic_user(user_id, enable_checkins=True, test_data_dir=test_data_dir)
        
        # Get actual user ID
        from core.user_data_handlers import get_user_id_by_identifier
        actual_user_id = get_user_id_by_identifier(user_id)
        if actual_user_id is None:
            actual_user_id = user_id
        
        # Mock load_user_messages to return test data
        with patch('ui.dialogs.message_editor_dialog.load_user_messages') as mock_load:
            mock_load.return_value = [
                {
                    'message_id': 'msg1',
                    'message': 'Test message 1',
                    'days': ['monday', 'tuesday'],
                    'time_periods': ['morning']
                },
                {
                    'message_id': 'msg2',
                    'message': 'Test message 2',
                    'days': ['wednesday'],
                    'time_periods': ['afternoon', 'evening']
                }
            ]
            
            # Create dialog
            dialog = MessageEditorDialog(parent=None, user_id=actual_user_id, category="motivation")
            
            yield dialog
            
            # Cleanup
            dialog.deleteLater()
    
    @pytest.mark.ui
    def test_dialog_initialization(self, dialog):
        """Test: Dialog initializes correctly"""
        # Arrange: Dialog is created in fixture
        
        # Act: (No action needed - initialization happens in fixture)
        
        # Assert: Verify initial state
        assert dialog is not None, "Dialog should be created"
        assert not dialog.isVisible(), "Dialog should not be visible during testing"
        assert "Message Editor" in dialog.windowTitle(), "Dialog should have correct title"
        assert dialog.user_id is not None, "User ID should be set"
        assert dialog.category == "motivation", "Category should be set"
        
        # Assert: Verify UI components exist
        assert hasattr(dialog, 'ui'), "UI should be set up"
        assert hasattr(dialog.ui, 'tableWidget_messages'), "Table widget should exist"
        assert hasattr(dialog.ui, 'pushButton_refresh'), "Refresh button should exist"
        assert hasattr(dialog.ui, 'pushButton_add_message'), "Add message button should exist"
        assert hasattr(dialog.ui, 'pushButton_close'), "Close button should exist"
    
    @pytest.mark.ui
    def test_table_setup(self, dialog):
        """Test: Table is set up correctly"""
        # Arrange: Dialog is created in fixture
        
        # Act: (No action needed - setup happens in fixture)
        
        # Assert: Verify table configuration
        assert dialog.ui.tableWidget_messages.columnCount() == 4, "Table should have 4 columns"
        headers = [dialog.ui.tableWidget_messages.horizontalHeaderItem(i).text() 
                   for i in range(dialog.ui.tableWidget_messages.columnCount())]
        assert "Message Text" in headers, "Should have Message Text column"
        assert "Days" in headers, "Should have Days column"
        assert "Time Periods" in headers, "Should have Time Periods column"
        assert "Actions" in headers, "Should have Actions column"
    
    @pytest.mark.ui
    def test_messages_loaded(self, dialog):
        """Test: Messages are loaded correctly"""
        # Arrange: Dialog is created in fixture
        
        # Act: (No action needed - loading happens in fixture)
        
        # Assert: Verify messages are loaded
        assert len(dialog.messages) == 2, "Should load 2 messages"
        assert dialog.ui.tableWidget_messages.rowCount() == 2, "Table should have 2 rows"
        
        # Assert: Verify first message is displayed
        item = dialog.ui.tableWidget_messages.item(0, 0)
        assert item is not None, "First message should be displayed"
        assert "Test message 1" in item.text(), "Should display first message text"
        
        # Assert: Verify days are displayed
        item = dialog.ui.tableWidget_messages.item(0, 1)
        assert item is not None, "Days should be displayed"
        assert "Monday" in item.text() or "Tuesday" in item.text(), "Should display days"
        
        # Assert: Verify periods are displayed
        item = dialog.ui.tableWidget_messages.item(0, 2)
        assert item is not None, "Periods should be displayed"
        assert "Morning" in item.text(), "Should display periods"


class TestMessageEditorDialogOperations:
    """Test message editor dialog operations."""
    
    @pytest.fixture
    def dialog(self, qapp, test_data_dir):
        """Create message editor dialog for testing."""
        # Create test user
        user_id = "test_message_editor_ops"
        TestUserFactory.create_basic_user(user_id, enable_checkins=True, test_data_dir=test_data_dir)
        
        # Get actual user ID
        from core.user_data_handlers import get_user_id_by_identifier
        actual_user_id = get_user_id_by_identifier(user_id)
        if actual_user_id is None:
            actual_user_id = user_id
        
        # Mock load_user_messages to return test data
        with patch('ui.dialogs.message_editor_dialog.load_user_messages') as mock_load:
            mock_load.return_value = [
                {
                    'message_id': 'msg1',
                    'message': 'Test message 1',
                    'days': ['monday'],
                    'time_periods': ['morning']
                }
            ]
            
            # Create dialog
            dialog = MessageEditorDialog(parent=None, user_id=actual_user_id, category="motivation")
            
            yield dialog
            
            # Cleanup
            dialog.deleteLater()
    
    @pytest.mark.ui
    def test_refresh_messages(self, dialog):
        """Test: Refresh button reloads messages"""
        # Arrange: Dialog is created in fixture
        with patch('ui.dialogs.message_editor_dialog.load_user_messages') as mock_load:
            mock_load.return_value = [
                {
                    'message_id': 'msg2',
                    'message': 'Test message 2',
                    'days': ['tuesday'],
                    'time_periods': ['afternoon']
                }
            ]
            
            # Act: Click refresh button
            dialog.ui.pushButton_refresh.click()
            
            # Assert: Should reload messages
            mock_load.assert_called_once_with(dialog.user_id, dialog.category)
            assert len(dialog.messages) == 1, "Should reload messages"
            assert dialog.messages[0]['message_id'] == 'msg2', "Should load new message"
    
    @pytest.mark.ui
    def test_add_new_message(self, dialog):
        """Test: Add new message button opens edit dialog"""
        # Arrange: Dialog is created in fixture
        with patch('ui.dialogs.message_editor_dialog.MessageEditDialog') as mock_dialog_class, \
             patch.object(dialog, 'load_messages') as mock_load:
            mock_dialog = MagicMock()
            mock_dialog.exec.return_value = 1  # Accepted
            mock_dialog_class.return_value = mock_dialog
            
            # Act: Click add message button
            dialog.add_new_message()
            
            # Assert: Should create edit dialog
            mock_dialog_class.assert_called_once()
            # Assert: Should reload messages after accept
            mock_load.assert_called_once()
    
    @pytest.mark.ui
    def test_edit_message_by_row(self, dialog):
        """Test: Edit message by row opens edit dialog"""
        # Arrange: Dialog is created in fixture
        # Ensure we have messages
        assert len(dialog.messages) > 0, "Should have messages to edit"
        message_data = dialog.messages[0]
        
        with patch('ui.dialogs.message_editor_dialog.MessageEditDialog') as mock_dialog_class, \
             patch.object(dialog, 'load_messages') as mock_load:
            mock_dialog = MagicMock()
            mock_dialog.exec.return_value = 1  # Accepted (QDialog.DialogCode.Accepted)
            mock_dialog_class.return_value = mock_dialog
            
            # Act: Edit message at row 0
            dialog.edit_message_by_row(0)
            
            # Assert: Should create edit dialog with message data
            mock_dialog_class.assert_called_once()
            call_args = mock_dialog_class.call_args
            # Check that message_data is passed (it's the 4th positional arg: parent, user_id, category, message_data)
            assert len(call_args[0]) >= 4, "Should pass at least 4 arguments"
            passed_message_data = call_args[0][3]
            assert passed_message_data == message_data, f"Should pass message data. Expected {message_data}, got {passed_message_data}"
            # Assert: Should reload messages after accept
            mock_load.assert_called_once()
    
    @pytest.mark.ui
    def test_delete_message_by_row(self, dialog):
        """Test: Delete message by row deletes message"""
        # Arrange: Dialog is created in fixture
        # Ensure we have messages
        assert len(dialog.messages) > 0, "Should have messages to delete"
        message_id = dialog.messages[0].get('message_id')
        
        with patch('ui.dialogs.message_editor_dialog.delete_message', return_value=None) as mock_delete, \
             patch('PySide6.QtWidgets.QMessageBox.question') as mock_question, \
             patch('PySide6.QtWidgets.QMessageBox.information') as mock_info, \
             patch.object(dialog, 'load_messages') as mock_load:
            from PySide6.QtWidgets import QMessageBox
            mock_question.return_value = QMessageBox.StandardButton.Yes
            
            # Act: Delete message at row 0
            dialog.delete_message_by_row(0)
            
            # Assert: Should show confirmation
            mock_question.assert_called_once()
            # Assert: Should delete message
            mock_delete.assert_called_once_with(dialog.user_id, dialog.category, message_id)
            # Assert: Should show success message
            mock_info.assert_called_once()
            # Assert: Should reload messages
            mock_load.assert_called_once()
    
    @pytest.mark.ui
    def test_delete_message_cancelled(self, dialog):
        """Test: Delete message cancelled does not delete"""
        # Arrange: Dialog is created in fixture
        with patch('ui.dialogs.message_editor_dialog.delete_message', return_value=None) as mock_delete, \
             patch('PySide6.QtWidgets.QMessageBox.question') as mock_question:
            mock_question.return_value = 0  # No
            
            # Act: Delete message at row 0 (but cancel)
            dialog.delete_message_by_row(0)
            
            # Assert: Should show confirmation
            mock_question.assert_called_once()
            # Assert: Should not delete message
            mock_delete.assert_not_called()
    
    @pytest.mark.ui
    def test_show_no_messages_state(self, dialog):
        """Test: Show no messages state when no messages found"""
        # Arrange: Dialog is created in fixture
        dialog.messages = []
        
        # Act: Show no messages state
        dialog.show_no_messages_state()
        
        # Assert: Should show no messages message
        assert dialog.ui.tableWidget_messages.rowCount() == 1, "Should have 1 row for no messages"
        item = dialog.ui.tableWidget_messages.item(0, 0)
        assert item is not None, "Should have item"
        assert "No messages found" in item.text(), "Should show no messages message"
        
        # Note: The UI may not have separate edit/delete buttons - they're in the table cells
        # So we just verify the table state is correct


class TestMessageEditorDialogOpenFunction:
    """Test open_message_editor_dialog function."""
    
    @pytest.mark.ui
    def test_open_message_editor_dialog(self, qapp, test_data_dir):
        """Test: open_message_editor_dialog opens dialog"""
        # Arrange: Create test user
        user_id = "test_message_editor_open"
        TestUserFactory.create_basic_user(user_id, enable_checkins=True, test_data_dir=test_data_dir)
        
        # Get actual user ID
        from core.user_data_handlers import get_user_id_by_identifier
        actual_user_id = get_user_id_by_identifier(user_id)
        if actual_user_id is None:
            actual_user_id = user_id
        
        # Mock load_user_messages and dialog.exec to avoid hanging
        with patch('ui.dialogs.message_editor_dialog.load_user_messages') as mock_load, \
             patch('ui.dialogs.message_editor_dialog.MessageEditorDialog') as mock_dialog_class:
            mock_load.return_value = []
            mock_dialog = MagicMock()
            mock_dialog.exec.return_value = 1  # Accepted
            mock_dialog_class.return_value = mock_dialog
            
            # Act: Open dialog
            result = open_message_editor_dialog(parent=None, user_id=actual_user_id, category="motivation")
            
            # Assert: Should create dialog
            mock_dialog_class.assert_called_once()
            # Assert: Should return dialog result
            assert result == 1, "Should return dialog result"

