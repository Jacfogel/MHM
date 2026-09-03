"""ServiceManager start/stop paths that do not launch a real process."""

from unittest.mock import Mock, patch

import pytest

from ui.service_manager import ServiceManager

pytestmark = [pytest.mark.ui, pytest.mark.unit]


def test_start_service_reports_failure_when_process_does_not_appear():
    manager = ServiceManager()
    with patch.object(manager, "validate_configuration_before_start", return_value=True), \
        patch.object(manager, "is_service_running", return_value=(False, None)), \
        patch("ui.service_manager.subprocess.Popen", return_value=Mock()), \
        patch("ui.service_manager.resolve_python_interpreter", return_value="python"), \
        patch("ui.service_manager.prepare_launch_environment", return_value={}), \
        patch("ui.service_manager.time.sleep"), \
        patch("ui.service_manager.QMessageBox") as msgbox:
        assert manager.start_service() is False
    msgbox.critical.assert_called_once()


def test_stop_service_force_terminates_after_timeout(tmp_path):
    manager = ServiceManager()
    proc = Mock()
    proc.info = {
        "pid": 99,
        "name": "python.exe",
        "cmdline": ["python", "C:/project/core/service.py"],
    }
    proc.is_running.return_value = True
    calls = {"n": 0}

    def fake_is_running():
        calls["n"] += 1
        if calls["n"] < 42:
            return True, 99
        return False, None

    with patch.object(manager, "is_service_running", side_effect=fake_is_running), \
        patch("ui.service_manager.time.sleep"), \
        patch("ui.service_manager.get_flags_dir", return_value=tmp_path), \
        patch("ui.service_manager.psutil.process_iter", return_value=[proc]), \
        patch("ui.service_manager.QMessageBox"):
        assert manager.stop_service() is True

    proc.terminate.assert_called()
    assert (tmp_path / "shutdown_request.flag").exists()
