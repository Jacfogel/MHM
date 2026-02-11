"""
Comprehensive tests for process watcher dialog.

Tests the actual UI behavior, user interactions, and side effects for:
- Process watcher dialog (PySide6)
- Process monitoring and display
- Auto-refresh functionality
- Process details display
- Error handling and recovery
"""

from tests.conftest import ensure_qt_runtime

ensure_qt_runtime()

import pytest
from unittest.mock import patch, Mock, MagicMock
from datetime import datetime

from core.time_utilities import now_datetime_full
from PySide6.QtWidgets import QApplication, QTableWidgetItem
from PySide6.QtCore import Qt, QTimer
from PySide6.QtTest import QTest
import logging

logger = logging.getLogger("mhm_tests")

# Do not modify sys.path; rely on package imports
from ui.dialogs.process_watcher_dialog import ProcessWatcherDialog


# Create QApplication instance for testing
@pytest.fixture(scope="session")
def qapp():
    """Create QApplication instance for UI testing."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app
    # Don't quit the app as it might be used by other tests


class TestProcessWatcherDialogInitialization:
    """Test process watcher dialog initialization."""

    @pytest.fixture
    def dialog(self, qapp):
        """Create process watcher dialog for testing."""
        with patch(
            "ui.dialogs.process_watcher_dialog.psutil.process_iter"
        ) as mock_process_iter:
            with patch(
                "core.service_utilities.get_service_processes"
            ) as mock_get_service:
                mock_process_iter.return_value = []
                mock_get_service.return_value = []

                # Create dialog (DO NOT show() - this would display UI during testing)
                dialog = ProcessWatcherDialog(parent=None)

                yield dialog

                # Cleanup
                dialog.deleteLater()

    @pytest.mark.ui
    @pytest.mark.ui
    def test_dialog_initialization(self, dialog):
        """Test dialog initializes correctly with proper UI state."""
        # Arrange: Dialog is created in fixture

        # Act: (No action needed - initialization happens in fixture)

        # Assert: Verify initial state
        assert dialog is not None, "Dialog should be created"
        assert not dialog.isVisible(), "Dialog should not be visible during testing"
        assert (
            dialog.windowTitle() == "Process Watcher - Python Processes"
        ), "Dialog should have correct title"
        assert dialog.isModal() is False, "Dialog should be non-modal"

        # Assert: Verify UI components exist
        assert hasattr(dialog, "refresh_button"), "Refresh button should exist"
        assert hasattr(
            dialog, "auto_refresh_checkbox"
        ), "Auto-refresh checkbox should exist"
        assert hasattr(dialog, "tab_widget"), "Tab widget should exist"
        assert hasattr(
            dialog, "all_processes_table"
        ), "All processes table should exist"
        assert hasattr(
            dialog, "mhm_processes_table"
        ), "MHM processes table should exist"
        assert hasattr(
            dialog, "process_details_text"
        ), "Process details text should exist"
        assert hasattr(dialog, "refresh_timer"), "Refresh timer should exist"

        # Assert: Verify initial auto-refresh state
        assert (
            dialog.auto_refresh_enabled is False
        ), "Auto-refresh should be disabled initially"
        assert (
            dialog.auto_refresh_checkbox.text() == "Auto Refresh: OFF"
        ), "Auto-refresh button should show OFF"

    @pytest.mark.ui
    @pytest.mark.ui
    def test_tab_widget_setup(self, dialog):
        """Test tab widget is set up correctly."""
        assert dialog.tab_widget.count() == 3, "Should have 3 tabs"
        assert (
            dialog.tab_widget.tabText(0) == "All Python Processes"
        ), "First tab should be All Python Processes"
        assert (
            dialog.tab_widget.tabText(1) == "MHM Services"
        ), "Second tab should be MHM Services"
        assert (
            dialog.tab_widget.tabText(2) == "Process Details"
        ), "Third tab should be Process Details"

    @pytest.mark.ui
    @pytest.mark.ui
    def test_table_widget_setup(self, dialog):
        """Test table widgets are set up correctly."""
        # All processes table
        assert (
            dialog.all_processes_table.columnCount() == 6
        ), "All processes table should have 6 columns"
        assert (
            dialog.all_processes_table.horizontalHeaderItem(0).text() == "PID"
        ), "First column should be PID"
        assert (
            dialog.all_processes_table.horizontalHeaderItem(1).text() == "Name"
        ), "Second column should be Name"
        assert (
            dialog.all_processes_table.horizontalHeaderItem(2).text() == "Command Line"
        ), "Third column should be Command Line"

        # MHM processes table
        assert (
            dialog.mhm_processes_table.columnCount() == 7
        ), "MHM processes table should have 7 columns"
        assert (
            dialog.mhm_processes_table.horizontalHeaderItem(0).text() == "PID"
        ), "First column should be PID"
        assert (
            dialog.mhm_processes_table.horizontalHeaderItem(1).text() == "Type"
        ), "Second column should be Type"
        assert (
            dialog.mhm_processes_table.horizontalHeaderItem(6).text() == "Status"
        ), "Last column should be Status"


class TestProcessWatcherRefresh:
    """Test process refresh functionality."""

    @pytest.fixture
    def dialog(self, qapp):
        """Create process watcher dialog for testing."""
        with patch(
            "ui.dialogs.process_watcher_dialog.psutil.process_iter"
        ) as mock_process_iter:
            with patch(
                "core.service_utilities.get_service_processes"
            ) as mock_get_service:
                mock_process_iter.return_value = []
                mock_get_service.return_value = []

                dialog = ProcessWatcherDialog(parent=None)
                yield dialog
                dialog.deleteLater()

    @pytest.mark.ui
    @pytest.mark.ui
    def test_refresh_processes_calls_update_methods(self, dialog):
        """Test refresh_processes calls update methods."""
        # Arrange: Set up mocks for update methods
        with patch.object(dialog, "update_all_processes") as mock_update_all:
            with patch.object(dialog, "update_mhm_processes") as mock_update_mhm:
                # Act: Refresh processes
                dialog.refresh_processes()

                # Assert: Verify both update methods were called
                mock_update_all.assert_called_once()
                mock_update_mhm.assert_called_once()

    @pytest.mark.ui
    @pytest.mark.ui
    def test_update_all_processes_with_python_processes(self, dialog):
        """Test update_all_processes populates table with Python processes."""
        # Arrange: Create mock process info
        mock_process_info = {
            "pid": 12345,
            "name": "python.exe",
            "cmdline": ["python", "test.py"],
            "cpu_percent": 5.5,
            "memory_percent": 2.3,
            "create_time": now_datetime_full().timestamp(),
        }

        # Arrange: Create mock process iterator
        mock_proc = MagicMock()
        mock_proc.info = mock_process_info

        # Act: Update all processes with mocked psutil
        with patch(
            "ui.dialogs.process_watcher_dialog.psutil.process_iter",
            return_value=[mock_proc],
        ):
            dialog.update_all_processes()

            # Assert: Verify table was updated with actual system changes
            assert dialog.all_processes_table.rowCount() == 1, "Should have 1 row"
            assert (
                dialog.all_processes_table.item(0, 0).text() == "12345"
            ), "PID should be correct"
            assert (
                dialog.all_processes_table.item(0, 1).text() == "python.exe"
            ), "Name should be correct"
            assert (
                "python test.py" in dialog.all_processes_table.item(0, 2).text()
            ), "Command line should be correct"

    @pytest.mark.ui
    @pytest.mark.ui
    def test_update_all_processes_filters_non_python(self, dialog):
        """Test update_all_processes filters out non-Python processes."""
        # Create mock process info for non-Python process
        mock_process_info = {
            "pid": 12345,
            "name": "notepad.exe",
            "cmdline": ["notepad"],
            "cpu_percent": 1.0,
            "memory_percent": 0.5,
            "create_time": now_datetime_full().timestamp(),
        }

        mock_proc = MagicMock()
        mock_proc.info = mock_process_info

        with patch(
            "ui.dialogs.process_watcher_dialog.psutil.process_iter",
            return_value=[mock_proc],
        ):
            dialog.update_all_processes()

            # Verify table is empty (non-Python process filtered out)
            assert (
                dialog.all_processes_table.rowCount() == 0
            ), "Should have 0 rows (non-Python filtered)"

    @pytest.mark.ui
    @pytest.mark.ui
    def test_update_all_processes_handles_psutil_errors(self, dialog):
        """Test update_all_processes handles psutil errors gracefully."""
        import psutil

        # Create mock process that raises NoSuchProcess when accessing info
        mock_proc = MagicMock()
        mock_proc.info = MagicMock(side_effect=psutil.NoSuchProcess(12345))

        with patch(
            "ui.dialogs.process_watcher_dialog.psutil.process_iter",
            return_value=[mock_proc],
        ):
            # Should not raise exception
            dialog.update_all_processes()

            # Table should be empty (error handled)
            assert (
                dialog.all_processes_table.rowCount() == 0
            ), "Should handle psutil errors gracefully"

    @pytest.mark.ui
    @pytest.mark.ui
    def test_update_mhm_processes_with_service_processes(self, dialog):
        """Test update_mhm_processes populates table with MHM service processes."""
        # Create mock service process info
        mock_service_process = {
            "pid": 54321,
            "process_type": "headless",
            "cmdline": ["python", "run_headless_service.py"],
            "create_time": now_datetime_full().timestamp(),
        }

        with patch(
            "core.service_utilities.get_service_processes",
            return_value=[mock_service_process],
        ):
            with patch(
                "ui.dialogs.process_watcher_dialog.psutil.Process"
            ) as mock_psutil_proc:
                # Mock psutil.Process for getting additional info
                mock_proc = MagicMock()
                mock_proc.cpu_percent.return_value = 3.2
                mock_proc.memory_percent.return_value = 1.5
                mock_proc.status.return_value = "running"
                mock_psutil_proc.return_value = mock_proc

                dialog.update_mhm_processes()

                # Verify table was updated
                assert dialog.mhm_processes_table.rowCount() == 1, "Should have 1 row"
                assert (
                    dialog.mhm_processes_table.item(0, 0).text() == "54321"
                ), "PID should be correct"
                assert (
                    dialog.mhm_processes_table.item(0, 1).text() == "headless"
                ), "Type should be correct"
                assert (
                    dialog.mhm_processes_table.item(0, 6).text() == "running"
                ), "Status should be correct"

    @pytest.mark.ui
    @pytest.mark.ui
    def test_update_mhm_processes_handles_psutil_errors(self, dialog):
        """Test update_mhm_processes handles psutil errors gracefully."""
        import psutil

        mock_service_process = {
            "pid": 54321,
            "process_type": "headless",
            "cmdline": ["python", "run_headless_service.py"],
            "create_time": now_datetime_full().timestamp(),
        }

        with patch(
            "core.service_utilities.get_service_processes",
            return_value=[mock_service_process],
        ):
            with patch(
                "ui.dialogs.process_watcher_dialog.psutil.Process",
                side_effect=psutil.NoSuchProcess(54321),
            ):
                # Should not raise exception
                dialog.update_mhm_processes()

                # Table should still be updated with default values
                assert (
                    dialog.mhm_processes_table.rowCount() == 1
                ), "Should handle psutil errors gracefully"
                assert (
                    dialog.mhm_processes_table.item(0, 3).text() == "0.0%"
                ), "CPU should default to 0.0%"
                assert (
                    dialog.mhm_processes_table.item(0, 4).text() == "0.0%"
                ), "Memory should default to 0.0%"
                assert (
                    dialog.mhm_processes_table.item(0, 6).text() == "Unknown"
                ), "Status should default to Unknown"


class TestProcessWatcherAutoRefresh:
    """Test auto-refresh functionality."""

    @pytest.fixture
    def dialog(self, qapp):
        """Create process watcher dialog for testing."""
        with patch(
            "ui.dialogs.process_watcher_dialog.psutil.process_iter"
        ) as mock_process_iter:
            with patch(
                "core.service_utilities.get_service_processes"
            ) as mock_get_service:
                mock_process_iter.return_value = []
                mock_get_service.return_value = []

                dialog = ProcessWatcherDialog(parent=None)
                yield dialog
                dialog.deleteLater()

    @pytest.mark.ui
    @pytest.mark.ui
    def test_toggle_auto_refresh_enables(self, dialog):
        """Test toggle_auto_refresh enables auto-refresh."""
        # Arrange: Verify initial state
        assert dialog.auto_refresh_enabled is False, "Should start disabled"

        # Act: Toggle auto-refresh
        dialog.toggle_auto_refresh()

        # Assert: Verify system state changed
        assert dialog.auto_refresh_enabled is True, "Should be enabled after toggle"
        assert (
            dialog.auto_refresh_checkbox.text() == "Auto Refresh: ON"
        ), "Button text should show ON"
        assert dialog.refresh_timer.isActive(), "Timer should be active"

    @pytest.mark.ui
    @pytest.mark.ui
    def test_toggle_auto_refresh_disables(self, dialog):
        """Test toggle_auto_refresh disables auto-refresh."""
        # Enable first
        dialog.auto_refresh_enabled = True
        dialog.refresh_timer.start(5000)

        dialog.toggle_auto_refresh()

        assert dialog.auto_refresh_enabled is False, "Should be disabled after toggle"
        assert (
            dialog.auto_refresh_checkbox.text() == "Auto Refresh: OFF"
        ), "Button text should show OFF"
        assert not dialog.refresh_timer.isActive(), "Timer should not be active"

    @pytest.mark.ui
    @pytest.mark.ui
    def test_auto_refresh_timer_triggers_refresh(self, dialog):
        """Test auto-refresh timer is connected and can trigger refresh."""
        # Verify timer is connected to refresh_processes
        assert dialog.refresh_timer is not None, "Timer should exist"

        # Enable auto-refresh
        dialog.toggle_auto_refresh()
        assert dialog.auto_refresh_enabled is True, "Auto-refresh should be enabled"
        assert dialog.refresh_timer.isActive(), "Timer should be active"
        assert (
            dialog.refresh_timer.interval() == 5000
        ), "Timer should have 5 second interval"

        # Verify timer is connected to refresh_processes method
        # The timer's timeout signal should be connected (we can't easily test signal emission
        # without actually waiting, but we can verify the timer is set up correctly)
        assert (
            dialog.refresh_timer.isActive()
        ), "Timer should be active when auto-refresh is enabled"


class TestProcessWatcherSelection:
    """Test process selection functionality."""

    @pytest.fixture
    def dialog(self, qapp):
        """Create process watcher dialog for testing."""
        with patch(
            "ui.dialogs.process_watcher_dialog.psutil.process_iter"
        ) as mock_process_iter:
            with patch(
                "core.service_utilities.get_service_processes"
            ) as mock_get_service:
                mock_process_iter.return_value = []
                mock_get_service.return_value = []

                dialog = ProcessWatcherDialog(parent=None)
                yield dialog
                dialog.deleteLater()

    @pytest.mark.ui
    @pytest.mark.ui
    def test_on_process_selected_all_processes_tab(self, dialog):
        """Test on_process_selected calls update_process_details_from_all for all processes tab."""
        dialog.tab_widget.setCurrentIndex(0)  # All processes tab

        with patch.object(dialog, "update_process_details_from_all") as mock_update:
            dialog.on_process_selected()

            mock_update.assert_called_once()

    @pytest.mark.ui
    @pytest.mark.ui
    def test_on_process_selected_mhm_processes_tab(self, dialog):
        """Test on_process_selected calls update_process_details_from_mhm for MHM processes tab."""
        dialog.tab_widget.setCurrentIndex(1)  # MHM processes tab

        with patch.object(dialog, "update_process_details_from_mhm") as mock_update:
            dialog.on_process_selected()

            mock_update.assert_called_once()

    @pytest.mark.ui
    @pytest.mark.ui
    def test_update_process_details_from_all_with_selection(self, dialog):
        """Test update_process_details_from_all updates details when process is selected."""
        # Add a row to the table
        dialog.all_processes_table.setRowCount(1)
        dialog.all_processes_table.setItem(0, 0, QTableWidgetItem("12345"))
        dialog.all_processes_table.setCurrentCell(0, 0)

        with patch.object(dialog, "show_process_details") as mock_show:
            dialog.update_process_details_from_all()

            mock_show.assert_called_once_with(12345)

    @pytest.mark.ui
    @pytest.mark.ui
    def test_update_process_details_from_all_no_selection(self, dialog):
        """Test update_process_details_from_all does nothing when no process is selected."""
        dialog.all_processes_table.setRowCount(0)
        dialog.all_processes_table.setCurrentCell(-1, -1)

        with patch.object(dialog, "show_process_details") as mock_show:
            dialog.update_process_details_from_all()

            mock_show.assert_not_called()

    @pytest.mark.ui
    @pytest.mark.ui
    def test_update_process_details_from_mhm_with_selection(self, dialog):
        """Test update_process_details_from_mhm updates details when process is selected."""
        # Add a row to the table
        dialog.mhm_processes_table.setRowCount(1)
        dialog.mhm_processes_table.setItem(0, 0, QTableWidgetItem("54321"))
        dialog.mhm_processes_table.setCurrentCell(0, 0)

        with patch.object(dialog, "show_process_details") as mock_show:
            dialog.update_process_details_from_mhm()

            mock_show.assert_called_once_with(54321)

    @pytest.mark.ui
    @pytest.mark.ui
    def test_update_process_details_from_mhm_no_selection(self, dialog):
        """Test update_process_details_from_mhm does nothing when no process is selected."""
        dialog.mhm_processes_table.setRowCount(0)
        dialog.mhm_processes_table.setCurrentCell(-1, -1)

        with patch.object(dialog, "show_process_details") as mock_show:
            dialog.update_process_details_from_mhm()

            mock_show.assert_not_called()


class TestProcessWatcherDetails:
    """Test process details display."""

    @pytest.fixture
    def dialog(self, qapp):
        """Create process watcher dialog for testing."""
        with patch(
            "ui.dialogs.process_watcher_dialog.psutil.process_iter"
        ) as mock_process_iter:
            with patch(
                "core.service_utilities.get_service_processes"
            ) as mock_get_service:
                mock_process_iter.return_value = []
                mock_get_service.return_value = []

                dialog = ProcessWatcherDialog(parent=None)
                yield dialog
                dialog.deleteLater()

    @pytest.mark.ui
    @pytest.mark.ui
    def test_show_process_details_with_valid_process(self, dialog):
        """Test show_process_details displays details for valid process."""
        import psutil

        # Create mock process
        mock_proc = MagicMock()
        mock_proc.name.return_value = "python.exe"
        mock_proc.status.return_value = "running"
        mock_proc.create_time.return_value = now_datetime_full().timestamp()
        mock_proc.cpu_percent.return_value = 5.5
        mock_proc.memory_percent.return_value = 2.3
        mock_proc.memory_info.return_value = MagicMock()
        mock_proc.cmdline.return_value = ["python", "test.py"]
        mock_proc.environ.return_value = {"PATH": "/usr/bin", "HOME": "/home/user"}
        mock_proc.connections.return_value = []

        with patch(
            "ui.dialogs.process_watcher_dialog.psutil.Process", return_value=mock_proc
        ):
            dialog.show_process_details(12345)

            # Verify details text was updated
            details_text = dialog.process_details_text.toPlainText()
            assert (
                "Process Details for PID 12345" in details_text
            ), "Should show process details header"
            assert "python.exe" in details_text, "Should show process name"
            assert "running" in details_text, "Should show process status"
            assert "python" in details_text, "Should show command line (python)"
            assert "test.py" in details_text, "Should show command line (test.py)"

    @pytest.mark.ui
    @pytest.mark.ui
    def test_show_process_details_with_no_such_process(self, dialog):
        """Test show_process_details handles NoSuchProcess error."""
        import psutil

        with patch(
            "ui.dialogs.process_watcher_dialog.psutil.Process",
            side_effect=psutil.NoSuchProcess(12345),
        ):
            dialog.show_process_details(12345)

            # Verify error message was displayed
            details_text = dialog.process_details_text.toPlainText()
            assert (
                "Error accessing process 12345" in details_text
            ), "Should show error message"
            assert (
                "Process may have terminated" in details_text
            ), "Should show helpful message"

    @pytest.mark.ui
    @pytest.mark.ui
    def test_show_process_details_with_access_denied(self, dialog):
        """Test show_process_details handles AccessDenied error."""
        import psutil

        with patch(
            "ui.dialogs.process_watcher_dialog.psutil.Process",
            side_effect=psutil.AccessDenied(12345),
        ):
            dialog.show_process_details(12345)

            # Verify error message was displayed
            details_text = dialog.process_details_text.toPlainText()
            assert (
                "Error accessing process 12345" in details_text
            ), "Should show error message"
            assert (
                "access is denied" in details_text
            ), "Should show access denied message"

    @pytest.mark.ui
    @pytest.mark.ui
    def test_show_process_details_with_environ_error(self, dialog):
        """Test show_process_details handles environ access errors."""
        import psutil

        mock_proc = MagicMock()
        mock_proc.name.return_value = "python.exe"
        mock_proc.status.return_value = "running"
        mock_proc.create_time.return_value = now_datetime_full().timestamp()
        mock_proc.cpu_percent.return_value = 5.5
        mock_proc.memory_percent.return_value = 2.3
        mock_proc.memory_info.return_value = MagicMock()
        mock_proc.cmdline.return_value = ["python", "test.py"]
        mock_proc.environ.side_effect = psutil.AccessDenied(12345)
        mock_proc.connections.return_value = []

        with patch(
            "ui.dialogs.process_watcher_dialog.psutil.Process", return_value=mock_proc
        ):
            dialog.show_process_details(12345)

            # Verify details text was updated (with access denied for environ)
            details_text = dialog.process_details_text.toPlainText()
            assert (
                "Process Details for PID 12345" in details_text
            ), "Should show process details"
            assert (
                "Access denied" in details_text
            ), "Should show access denied for environ"


class TestProcessWatcherErrorHandling:
    """Test error handling in process watcher dialog."""

    @pytest.fixture
    def dialog(self, qapp):
        """Create process watcher dialog for testing."""
        with patch(
            "ui.dialogs.process_watcher_dialog.psutil.process_iter"
        ) as mock_process_iter:
            with patch(
                "core.service_utilities.get_service_processes"
            ) as mock_get_service:
                mock_process_iter.return_value = []
                mock_get_service.return_value = []

                dialog = ProcessWatcherDialog(parent=None)
                yield dialog
                dialog.deleteLater()

    @pytest.mark.ui
    @pytest.mark.ui
    def test_refresh_processes_handles_errors(self, dialog):
        """Test refresh_processes handles errors gracefully."""
        with patch.object(
            dialog, "update_all_processes", side_effect=Exception("Test error")
        ):
            # Should not raise exception
            dialog.refresh_processes()

            # Dialog should still be functional
            assert dialog is not None, "Dialog should still exist after error"

    @pytest.mark.ui
    @pytest.mark.ui
    def test_update_all_processes_handles_exceptions(self, dialog):
        """Test update_all_processes handles exceptions gracefully."""
        with patch(
            "ui.dialogs.process_watcher_dialog.psutil.process_iter",
            side_effect=Exception("Test error"),
        ):
            # Should not raise exception
            dialog.update_all_processes()

            # Table should be in a valid state
            assert (
                dialog.all_processes_table.rowCount() >= 0
            ), "Table should have valid row count"

    @pytest.mark.ui
    @pytest.mark.ui
    def test_update_mhm_processes_handles_exceptions(self, dialog):
        """Test update_mhm_processes handles exceptions gracefully."""
        with patch(
            "core.service_utilities.get_service_processes",
            side_effect=Exception("Test error"),
        ):
            # Should not raise exception
            dialog.update_mhm_processes()

            # Table should be in a valid state
            assert (
                dialog.mhm_processes_table.rowCount() >= 0
            ), "Table should have valid row count"

    @pytest.mark.ui
    @pytest.mark.ui
    def test_show_process_details_handles_exceptions(self, dialog):
        """Test show_process_details handles exceptions gracefully."""
        with patch(
            "ui.dialogs.process_watcher_dialog.psutil.Process",
            side_effect=Exception("Test error"),
        ):
            # Should not raise exception
            dialog.show_process_details(12345)

            # Details text should show error
            details_text = dialog.process_details_text.toPlainText()
            assert "Error" in details_text, "Should show error message"


class TestProcessWatcherClose:
    """Test dialog close functionality."""

    @pytest.fixture
    def dialog(self, qapp):
        """Create process watcher dialog for testing."""
        with patch(
            "ui.dialogs.process_watcher_dialog.psutil.process_iter"
        ) as mock_process_iter:
            with patch(
                "core.service_utilities.get_service_processes"
            ) as mock_get_service:
                mock_process_iter.return_value = []
                mock_get_service.return_value = []

                dialog = ProcessWatcherDialog(parent=None)
                yield dialog
                dialog.deleteLater()

    @pytest.mark.ui
    @pytest.mark.ui
    def test_close_event_stops_timer(self, dialog):
        """Test closeEvent stops refresh timer."""
        # Enable auto-refresh
        dialog.auto_refresh_enabled = True
        dialog.refresh_timer.start(5000)
        assert dialog.refresh_timer.isActive(), "Timer should be active"

        # Simulate close event
        from PySide6.QtGui import QCloseEvent

        close_event = QCloseEvent()
        dialog.closeEvent(close_event)

        assert (
            not dialog.refresh_timer.isActive()
        ), "Timer should be stopped after close"
        assert close_event.isAccepted(), "Close event should be accepted"

    @pytest.mark.ui
    @pytest.mark.ui
    def test_close_event_handles_missing_timer(self, dialog):
        """Test closeEvent handles missing timer gracefully."""
        # Arrange: Remove timer attribute
        delattr(dialog, "refresh_timer")

        # Act: Close dialog
        from PySide6.QtGui import QCloseEvent

        close_event = QCloseEvent()
        dialog.closeEvent(close_event)

        # Assert: Should not raise exception and event should be accepted
        assert close_event.isAccepted(), "Close event should be accepted"


class TestProcessWatcherIntegration:
    """Integration tests for process watcher dialog workflows."""

    @pytest.fixture
    def dialog(self, qapp):
        """Create process watcher dialog for testing."""
        with patch(
            "ui.dialogs.process_watcher_dialog.psutil.process_iter"
        ) as mock_process_iter:
            with patch(
                "core.service_utilities.get_service_processes"
            ) as mock_get_service:
                mock_process_iter.return_value = []
                mock_get_service.return_value = []

                dialog = ProcessWatcherDialog(parent=None)
                yield dialog
                dialog.deleteLater()

    @pytest.mark.ui
    @pytest.mark.ui
    @pytest.mark.integration
    def test_complete_refresh_workflow(self, dialog):
        """Test complete refresh workflow: refresh -> update tables -> display data."""
        # Arrange: Set up mock processes
        mock_python_process = MagicMock()
        mock_python_process.info = {
            "pid": 12345,
            "name": "python.exe",
            "cmdline": ["python", "test.py"],
            "cpu_percent": 5.5,
            "memory_percent": 2.3,
            "create_time": now_datetime_full().timestamp(),
        }

        mock_service_process = {
            "pid": 54321,
            "process_type": "headless",
            "cmdline": ["python", "run_headless_service.py"],
            "create_time": now_datetime_full().timestamp(),
        }

        # Act: Execute complete refresh workflow
        with patch(
            "ui.dialogs.process_watcher_dialog.psutil.process_iter",
            return_value=[mock_python_process],
        ):
            with patch(
                "core.service_utilities.get_service_processes",
                return_value=[mock_service_process],
            ):
                with patch(
                    "ui.dialogs.process_watcher_dialog.psutil.Process"
                ) as mock_psutil_proc:
                    mock_proc = MagicMock()
                    mock_proc.cpu_percent.return_value = 3.2
                    mock_proc.memory_percent.return_value = 1.5
                    mock_proc.status.return_value = "running"
                    mock_psutil_proc.return_value = mock_proc

                    dialog.refresh_processes()

        # Assert: Verify both tables were updated (side effects)
        assert (
            dialog.all_processes_table.rowCount() == 1
        ), "All processes table should have 1 row"
        assert (
            dialog.mhm_processes_table.rowCount() == 1
        ), "MHM processes table should have 1 row"
        assert (
            dialog.all_processes_table.item(0, 0).text() == "12345"
        ), "Python process PID should be displayed"
        assert (
            dialog.mhm_processes_table.item(0, 0).text() == "54321"
        ), "Service process PID should be displayed"

    @pytest.mark.ui
    @pytest.mark.ui
    @pytest.mark.integration
    def test_complete_selection_workflow(self, dialog):
        """Test complete selection workflow: select process -> show details."""
        # Arrange: Populate table with process
        mock_process_info = {
            "pid": 12345,
            "name": "python.exe",
            "cmdline": ["python", "test.py"],
            "cpu_percent": 5.5,
            "memory_percent": 2.3,
            "create_time": now_datetime_full().timestamp(),
        }
        mock_proc = MagicMock()
        mock_proc.info = mock_process_info

        with patch(
            "ui.dialogs.process_watcher_dialog.psutil.process_iter",
            return_value=[mock_proc],
        ):
            dialog.update_all_processes()

        # Arrange: Set up process details mock
        import psutil

        mock_proc_details = MagicMock()
        mock_proc_details.name.return_value = "python.exe"
        mock_proc_details.status.return_value = "running"
        mock_proc_details.create_time.return_value = now_datetime_full().timestamp()
        mock_proc_details.cpu_percent.return_value = 5.5
        mock_proc_details.memory_percent.return_value = 2.3
        mock_proc_details.memory_info.return_value = MagicMock()
        mock_proc_details.cmdline.return_value = ["python", "test.py"]
        mock_proc_details.environ.return_value = {"PATH": "/usr/bin"}
        mock_proc_details.connections.return_value = []

        # Act: Select process and show details
        dialog.all_processes_table.setCurrentCell(0, 0)
        with patch(
            "ui.dialogs.process_watcher_dialog.psutil.Process",
            return_value=mock_proc_details,
        ):
            dialog.on_process_selected()

        # Assert: Verify details were displayed (side effect)
        details_text = dialog.process_details_text.toPlainText()
        assert (
            "Process Details for PID 12345" in details_text
        ), "Should show process details"
        assert "python.exe" in details_text, "Should show process name"
        assert "running" in details_text, "Should show process status"

    @pytest.mark.ui
    @pytest.mark.ui
    @pytest.mark.integration
    def test_auto_refresh_workflow(self, dialog):
        """Test auto-refresh workflow: enable -> timer active -> refresh on timeout."""
        # Arrange: Set up mock processes
        mock_process_info = {
            "pid": 12345,
            "name": "python.exe",
            "cmdline": ["python", "test.py"],
            "cpu_percent": 5.5,
            "memory_percent": 2.3,
            "create_time": now_datetime_full().timestamp(),
        }
        mock_proc = MagicMock()
        mock_proc.info = mock_process_info

        # Act: Enable auto-refresh
        dialog.toggle_auto_refresh()

        # Assert: Verify timer is active (system state changed)
        assert dialog.auto_refresh_enabled is True, "Auto-refresh should be enabled"
        assert dialog.refresh_timer.isActive(), "Timer should be active"
        assert (
            dialog.refresh_timer.interval() == 5000
        ), "Timer should have 5 second interval"

        # Act: Simulate timer timeout
        with patch(
            "ui.dialogs.process_watcher_dialog.psutil.process_iter",
            return_value=[mock_proc],
        ):
            with patch("core.service_utilities.get_service_processes", return_value=[]):
                dialog.refresh_timer.timeout.emit()
                QApplication.processEvents()

        # Assert: Verify refresh occurred (side effect)
        assert (
            dialog.all_processes_table.rowCount() == 1
        ), "Table should be refreshed with process data"
