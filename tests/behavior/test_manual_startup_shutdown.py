"""Manual-checklist leftover tests for startup, shutdown, and orphan detection."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from core.service import MHMService
from core.service_utilities import get_service_processes


def _info_messages(logger: MagicMock) -> str:
    return " ".join(str(call.args[0]) for call in logger.info.call_args_list if call.args)


@pytest.mark.behavior
@pytest.mark.core
def test_start_logs_startup_sequence_without_errors():
    service = MHMService()
    mock_cm = MagicMock()
    mock_sm = MagicMock()
    logger = MagicMock()

    with (
        patch("core.service.logger", logger),
        patch("core.service.signal.signal"),
        patch.object(service, "validate_configuration", return_value=["discord"]),
        patch.object(service, "check_and_fix_logging"),
        patch.object(service, "initialize_paths", return_value=["/tmp/mhm-path"]),
        patch("core.service.verify_file_access"),
        patch("core.service.CommunicationManager", return_value=mock_cm),
        patch("core.service.SchedulerManager", return_value=mock_sm),
        patch("core.service.set_scheduler_delivery_factory"),
        patch("scheduler.runtime_access.set_scheduler_manager"),
        patch.object(service, "run_service_loop"),
        patch("core.auto_cleanup.auto_cleanup_if_needed", return_value=False),
        patch("core.auto_cleanup.cleanup_data_directory"),
        patch("core.auto_cleanup.cleanup_tests_data_directory"),
        patch("scheduler.runtime_access.clear_scheduler_manager"),
        patch("core.file_auditor.stop_auditor"),
    ):
        service.start()

    messages = _info_messages(logger)
    assert "Starting MHM Backend Service..." in messages
    assert "Shutting down MHM Backend Service..." in messages
    assert "MHM Backend Service shutdown complete" in messages
    logger.error.assert_not_called()
    logger.critical.assert_not_called()


@pytest.mark.behavior
@pytest.mark.core
def test_shutdown_logs_clean_termination():
    service = MHMService()
    service.running = True
    service.communication_manager = MagicMock()
    service.scheduler_manager = MagicMock()
    logger = MagicMock()

    with (
        patch("core.service.logger", logger),
        patch("scheduler.runtime_access.clear_scheduler_manager"),
        patch("core.file_auditor.stop_auditor"),
    ):
        service.shutdown()

    messages = _info_messages(logger)
    assert "Shutting down MHM Backend Service..." in messages
    assert "MHM Backend Service shutdown complete" in messages
    assert service.running is False
    logger.error.assert_not_called()


@pytest.mark.behavior
@pytest.mark.core
def test_get_service_processes_empty_after_mocked_stop():
    running = MagicMock()
    running.info = {
        "pid": 111,
        "name": "python.exe",
        "cmdline": ["python", "core/service.py"],
        "create_time": 1.0,
        "environ": {"MHM_HEADLESS_SERVICE": "1"},
    }
    running.is_running.return_value = True

    with patch("core.service_utilities.psutil.process_iter", return_value=[running]):
        assert get_service_processes()

    stopped = MagicMock()
    stopped.info = {
        "pid": 111,
        "name": "python.exe",
        "cmdline": ["python", "core/service.py"],
        "create_time": 1.0,
        "environ": {"MHM_HEADLESS_SERVICE": "1"},
    }
    stopped.is_running.return_value = False

    with patch("core.service_utilities.psutil.process_iter", return_value=[stopped]):
        assert get_service_processes() == []


@pytest.mark.behavior
@pytest.mark.core
def test_ui_close_event_shuts_down_components_without_qt_window():
    from tests.conftest import ensure_qt_runtime

    ensure_qt_runtime()
    from ui.ui_app_qt import MHMManagerUI

    ui = MHMManagerUI.__new__(MHMManagerUI)
    shutdown = MagicMock()
    ui.shutdown_ui_components = shutdown
    event = MagicMock()

    MHMManagerUI.closeEvent(ui, event)

    shutdown.assert_called_once()
    event.accept.assert_called_once()
