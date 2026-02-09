"""Tests for run_dev_tools wrapper script."""

import runpy
import types

import pytest


@pytest.mark.unit
def test_run_dev_tools_invokes_main_and_exits(monkeypatch):
    """run_dev_tools should call run_development_tools.main and exit with its code."""
    fake_module = types.ModuleType("development_tools.run_development_tools")
    fake_module.main = lambda: 7
    monkeypatch.setitem(
        __import__("sys").modules, "development_tools.run_development_tools", fake_module
    )

    with pytest.raises(SystemExit) as excinfo:
        runpy.run_path(
            "development_tools/run_dev_tools.py",
            run_name="__main__",
        )

    assert excinfo.value.code == 7
