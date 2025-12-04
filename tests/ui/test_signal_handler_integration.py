"""
Signal handler integration tests for UI components.

These tests verify that Qt signal handlers are correctly connected and can
accept the parameters that signals emit. This catches signature mismatches
that would otherwise only appear at runtime.

Tests cover:
- Signal handler parameter acceptance
- Signal connection integrity
- Import availability for signal-related classes
- Real signal emission (not just direct method calls)
"""
from tests.conftest import ensure_qt_runtime

ensure_qt_runtime()

import pytest
from unittest.mock import patch, MagicMock
from PySide6.QtWidgets import QApplication, QLineEdit, QCheckBox
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest


@pytest.fixture(scope="session")
def qapp():
    """Create QApplication instance for UI testing."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


class TestAccountCreatorDialogSignalHandlers:
    """Test signal handlers in AccountCreatorDialog accept correct parameters."""
    
    @pytest.fixture
    def dialog(self, qapp, test_data_dir, mock_config):
        """Create account creation dialog for testing."""
        from ui.dialogs.account_creator_dialog import AccountCreatorDialog
        from unittest.mock import Mock
        
        # Create a mock communication manager
        mock_comm_manager = Mock()
        mock_comm_manager.get_active_channels.return_value = ['email', 'discord']
        
        dialog = AccountCreatorDialog(parent=None, communication_manager=mock_comm_manager)
        yield dialog
        dialog.close()
        dialog.deleteLater()
    
    @pytest.mark.ui
    @pytest.mark.user_management
    @pytest.mark.regression
    @pytest.mark.critical
    def test_username_textChanged_signal_handler_accepts_parameter(self, dialog):
        """Test that on_username_changed accepts text parameter from textChanged signal.
        
        This test would catch the signature mismatch where the handler only
        accepted 'self' but the signal emits a text parameter.
        """
        # Arrange - Get the line edit widget
        username_edit = dialog.ui.lineEdit_username
        assert username_edit is not None, "Username line edit should exist"
        
        # Verify the handler can accept the parameter that textChanged signal emits
        # textChanged signal emits (str) - the new text
        # This would fail with TypeError if signature was wrong (e.g., only accepts self)
        try:
            # Simulate what the signal would do - call handler with text parameter
            dialog.on_username_changed("testtext")
        except TypeError as e:
            if "takes" in str(e) and "positional argument" in str(e):
                pytest.fail(
                    f"Handler signature mismatch: on_username_changed should accept text parameter "
                    f"from textChanged signal, but got TypeError: {e}"
                )
            raise
        
        # Also verify it works when called with no parameter (backward compatibility)
        try:
            dialog.on_username_changed()
        except TypeError as e:
            pytest.fail(f"Handler should also work with no parameter (default), but got TypeError: {e}")
        
        # Verify signal is actually connected and works
        initial_username = dialog.username
        username_edit.setText("newusername")
        QApplication.processEvents()
        # The handler should have updated the username
        assert dialog.username == "newusername", "Signal handler should update username when text changes"
    
    @pytest.mark.ui
    @pytest.mark.user_management
    @pytest.mark.regression
    @pytest.mark.critical
    def test_preferred_name_textChanged_signal_handler_accepts_parameter(self, dialog):
        """Test that on_preferred_name_changed accepts text parameter from textChanged signal."""
        # Arrange
        preferred_name_edit = dialog.ui.lineEdit_preferred_name
        assert preferred_name_edit is not None, "Preferred name line edit should exist"
        
        # Verify handler accepts parameter that textChanged signal emits
        try:
            dialog.on_preferred_name_changed("testname")
        except TypeError as e:
            if "takes" in str(e) and "positional argument" in str(e):
                pytest.fail(
                    f"Handler signature mismatch: on_preferred_name_changed should accept text parameter "
                    f"from textChanged signal, but got TypeError: {e}"
                )
            raise
        
        # Verify it works with no parameter too
        try:
            dialog.on_preferred_name_changed()
        except TypeError as e:
            pytest.fail(f"Handler should also work with no parameter (default), but got TypeError: {e}")
        
        # Verify signal connection works
        preferred_name_edit.setText("New Name")
        QApplication.processEvents()
        assert dialog.preferred_name == "New Name", "Signal handler should update preferred name"
    
    @pytest.mark.ui
    @pytest.mark.user_management
    @pytest.mark.regression
    def test_account_creator_dialog_imports_available(self, dialog):
        """Test that all required PySide6 imports are available.
        
        This catches missing imports like QSizePolicy, QDialogButtonBox, Qt
        that are used in setup methods.
        """
        # Test that setup methods can run without NameError
        try:
            # These methods use QSizePolicy, QDialogButtonBox, Qt
            dialog.setup_feature_group_boxes()
            dialog.setup_connections()
        except NameError as e:
            pytest.fail(f"Missing import detected: {e}")
        except Exception as e:
            # Other exceptions are OK (e.g., widget not found), but NameError indicates missing import
            if "not defined" in str(e) or "NameError" in str(type(e).__name__):
                pytest.fail(f"Missing import detected: {e}")


class TestDynamicListFieldSignalHandlers:
    """Test signal handlers in DynamicListField accept correct parameters."""
    
    @pytest.fixture
    def widget(self, qapp):
        """Create DynamicListField for testing."""
        from ui.widgets.dynamic_list_field import DynamicListField
        
        widget = DynamicListField(
            parent=None,
            preset_label="Test Item",
            editable=True,
            checked=False
        )
        yield widget
        widget.close()
        widget.deleteLater()
    
    @pytest.mark.ui
    @pytest.mark.regression
    @pytest.mark.critical
    def test_textEdited_signal_handler_accepts_parameter(self, widget):
        """Test that on_text_changed accepts text parameter from textEdited signal.
        
        This test would catch the signature mismatch where the handler only
        accepted 'self' but textEdited signal emits a text parameter.
        """
        # Arrange
        line_edit = widget.ui.lineEdit_dynamic_list_field
        assert line_edit is not None, "Line edit should exist"
        
        # Verify handler accepts parameter that textEdited signal emits
        # textEdited signal emits (str) - the new text
        try:
            widget.on_text_changed("testtext")
        except TypeError as e:
            if "takes" in str(e) and "positional argument" in str(e):
                pytest.fail(
                    f"Handler signature mismatch: on_text_changed should accept text parameter "
                    f"from textEdited signal, but got TypeError: {e}"
                )
            raise
        
        # Verify it works with no parameter too
        try:
            widget.on_text_changed()
        except TypeError as e:
            pytest.fail(f"Handler should also work with no parameter (default), but got TypeError: {e}")
    
    @pytest.mark.ui
    @pytest.mark.regression
    @pytest.mark.critical
    def test_checkbox_toggled_signal_handler_accepts_parameter(self, widget):
        """Test that on_checkbox_toggled accepts checked parameter from toggled signal.
        
        This test would catch the signature mismatch where the handler only
        accepted 'self' but toggled signal emits a boolean parameter.
        """
        # Arrange
        checkbox = widget.ui.checkBox__dynamic_list_field
        assert checkbox is not None, "Checkbox should exist"
        
        # Verify handler accepts parameter that toggled signal emits
        # toggled signal emits (bool) - the new checked state
        try:
            widget.on_checkbox_toggled(True)
            widget.on_checkbox_toggled(False)
        except TypeError as e:
            if "takes" in str(e) and "positional argument" in str(e):
                pytest.fail(
                    f"Handler signature mismatch: on_checkbox_toggled should accept checked parameter "
                    f"from toggled signal, but got TypeError: {e}"
                )
            raise
        
        # Verify it works with no parameter too
        try:
            widget.on_checkbox_toggled()
        except TypeError as e:
            pytest.fail(f"Handler should also work with no parameter (default), but got TypeError: {e}")


class TestUISignalConnectionIntegrity:
    """Test that signal connections are properly set up and handlers work."""
    
    @pytest.mark.ui
    @pytest.mark.regression
    @pytest.mark.critical
    def test_signal_handlers_dont_raise_on_signal_emission(self, qapp, test_data_dir, mock_config):
        """Test that signal handlers don't raise exceptions when signals fire.
        
        This is a broader integration test that verifies the actual signal
        connections work end-to-end without errors being swallowed.
        """
        from ui.dialogs.account_creator_dialog import AccountCreatorDialog
        from communication.core.channel_orchestrator import CommunicationManager
        
        # Capture any exceptions that occur during signal handling
        exceptions_caught = []
        
        def exception_handler(exc_type, exc_value, exc_traceback):
            exceptions_caught.append((exc_type, exc_value))
        
        import sys
        original_excepthook = sys.excepthook
        sys.excepthook = exception_handler
        
        try:
            from unittest.mock import Mock
            mock_comm_manager = Mock()
            mock_comm_manager.get_active_channels.return_value = ['email', 'discord']
            dialog = AccountCreatorDialog(parent=None, communication_manager=mock_comm_manager)
            
            # Trigger signals that should call handlers
            dialog.ui.lineEdit_username.setText("testuser")
            QApplication.processEvents()
            
            dialog.ui.lineEdit_preferred_name.setText("Test Name")
            QApplication.processEvents()
            
            # Check for TypeErrors which indicate signature mismatches
            type_errors = [e for e in exceptions_caught if e[0] == TypeError]
            if type_errors:
                error_messages = [str(e[1]) for e in type_errors]
                # Filter for signature-related errors
                signature_errors = [msg for msg in error_messages if "takes" in msg and "positional argument" in msg]
                if signature_errors:
                    pytest.fail(
                        f"Signal handlers raised TypeError (likely signature mismatch): {signature_errors}"
                    )
            dialog.close()
            dialog.deleteLater()
        finally:
            sys.excepthook = original_excepthook
    
    @pytest.mark.ui
    @pytest.mark.regression
    def test_dynamic_list_field_signals_dont_raise(self, qapp):
        """Test that DynamicListField signal handlers don't raise exceptions."""
        from ui.widgets.dynamic_list_field import DynamicListField
        
        exceptions_caught = []
        
        def exception_handler(exc_type, exc_value, exc_traceback):
            exceptions_caught.append((exc_type, exc_value))
        
        import sys
        original_excepthook = sys.excepthook
        sys.excepthook = exception_handler
        
        try:
            widget = DynamicListField(
                parent=None,
                preset_label="Test",
                editable=True,
                checked=False
            )
            
            # Trigger signals
            widget.ui.lineEdit_dynamic_list_field.setText("test")
            QApplication.processEvents()
            
            widget.ui.checkBox__dynamic_list_field.setChecked(True)
            QApplication.processEvents()
            
            # Check for TypeErrors
            type_errors = [e for e in exceptions_caught if e[0] == TypeError]
            if type_errors:
                error_messages = [str(e[1]) for e in type_errors]
                pytest.fail(
                    f"Signal handlers raised TypeError: {error_messages}"
                )
            
            widget.close()
            widget.deleteLater()
        finally:
            sys.excepthook = original_excepthook

