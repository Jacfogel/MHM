"""Unit tests for the MHM Manager UI launcher."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

import run_mhm


@pytest.mark.unit
@pytest.mark.core
def test_main_returns_1_when_ui_app_missing(monkeypatch: pytest.MonkeyPatch):
    original_exists = Path.exists

    def fake_exists(self: Path) -> bool:
        if self.name == "ui_app_qt.py":
            return False
        return original_exists(self)

    monkeypatch.setattr(Path, "exists", fake_exists)
    with (
        patch.object(run_mhm, "setup_logging"),
        patch.object(run_mhm, "get_component_logger", return_value=MagicMock()),
    ):
        assert run_mhm.main() == 1


@pytest.mark.unit
@pytest.mark.core
def test_main_launches_ui_with_venv_python_and_launch_env():
    popen = MagicMock()
    launch_env = {"PYTHONPATH": "project", "VIRTUAL_ENV": "venv"}
    script_dir = Path(run_mhm.__file__).resolve().parent
    ui_path = script_dir / "ui" / "ui_app_qt.py"
    if not ui_path.exists():
        pytest.skip("ui/ui_app_qt.py is required for the success-path launcher test")

    with (
        patch.object(run_mhm, "setup_logging"),
        patch.object(run_mhm, "get_component_logger", return_value=MagicMock()),
        patch.object(run_mhm, "resolve_python_interpreter", return_value="C:/venv/python.exe") as resolve_py,
        patch.object(run_mhm, "prepare_launch_environment", return_value=launch_env) as prepare_env,
        patch.object(run_mhm.subprocess, "Popen", popen),
    ):
        assert run_mhm.main() == 0

    resolve_py.assert_called_once_with(str(script_dir))
    prepare_env.assert_called_once_with(str(script_dir))
    popen.assert_called_once()
    command = popen.call_args[0][0]
    kwargs = popen.call_args.kwargs
    assert command[0] == "C:/venv/python.exe"
    assert Path(command[1]) == ui_path
    assert kwargs["env"] == launch_env
    assert kwargs["cwd"] == str(script_dir)
    assert kwargs["shell"] is False
