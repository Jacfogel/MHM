"""Tests for deprecation inventory sync guard in legacy tooling."""

from pathlib import Path
from types import SimpleNamespace

import pytest

from tests.development_tools.conftest import load_development_tools_module

tool_wrappers_module = load_development_tools_module("shared.service.tool_wrappers")
ToolWrappersMixin = tool_wrappers_module.ToolWrappersMixin


class _DummyService(ToolWrappersMixin):
    """Minimal service harness for testing ToolWrappersMixin guard helpers."""

    def __init__(self, project_root: Path):
        self.project_root = project_root


def _completed(returncode: int = 0, stdout: str = "", stderr: str = ""):
    """Build a subprocess-like completed process object."""
    return SimpleNamespace(returncode=returncode, stdout=stdout, stderr=stderr)


def _legacy_marker_line() -> str:
    """Build marker content without embedding the full marker literal in this source file."""
    return "+ # LEGACY" " COMPATIBILITY: temporary bridge\n"


@pytest.mark.unit
def test_inventory_guard_fails_when_deprecation_like_changes_without_inventory_update(
    tmp_path, monkeypatch
):
    """Guard should fail when trigger changes exist but inventory file is not updated."""
    inventory_path = tmp_path / "development_tools" / "config" / "DEPRECATION_INVENTORY.json"
    inventory_path.parent.mkdir(parents=True, exist_ok=True)
    inventory_path.write_text('{"active_or_candidate_inventory": [], "removed_inventory": []}', encoding="utf-8")

    sample_file = tmp_path / "core" / "sample.py"
    sample_file.parent.mkdir(parents=True, exist_ok=True)
    sample_file.write_text("value = 1\n", encoding="utf-8")

    def fake_run(cmd, **kwargs):
        if cmd[:3] == ["git", "status", "--porcelain"]:
            return _completed(stdout=" M core/sample.py\n")
        if cmd[:2] == ["git", "diff"]:
            return _completed(stdout=_legacy_marker_line())
        raise AssertionError(f"Unexpected command: {cmd}")

    monkeypatch.setattr(tool_wrappers_module.subprocess, "run", fake_run)

    service = _DummyService(tmp_path)
    result = service._check_deprecation_inventory_sync(
        "development_tools/config/DEPRECATION_INVENTORY.json"
    )

    assert result["check_passed"] is False
    assert result["status"] == "failed"
    assert (
        result["reason"]
        == "inventory_not_updated_for_deprecation_like_changes"
    )
    assert "core/sample.py" in result["trigger_files"]


@pytest.mark.unit
def test_inventory_guard_passes_when_inventory_file_is_updated(tmp_path, monkeypatch):
    """Guard should pass when inventory file is part of the same change set."""
    inventory_path = tmp_path / "development_tools" / "config" / "DEPRECATION_INVENTORY.json"
    inventory_path.parent.mkdir(parents=True, exist_ok=True)
    inventory_path.write_text('{"active_or_candidate_inventory": [], "removed_inventory": []}', encoding="utf-8")

    sample_file = tmp_path / "core" / "sample.py"
    sample_file.parent.mkdir(parents=True, exist_ok=True)
    sample_file.write_text("value = 2\n", encoding="utf-8")

    def fake_run(cmd, **kwargs):
        if cmd[:3] == ["git", "status", "--porcelain"]:
            return _completed(
                stdout=(
                    " M development_tools/config/DEPRECATION_INVENTORY.json\n"
                    " M core/sample.py\n"
                )
            )
        if cmd[:2] == ["git", "diff"]:
            return _completed(stdout=_legacy_marker_line())
        raise AssertionError(f"Unexpected command: {cmd}")

    monkeypatch.setattr(tool_wrappers_module.subprocess, "run", fake_run)

    service = _DummyService(tmp_path)
    result = service._check_deprecation_inventory_sync(
        "development_tools/config/DEPRECATION_INVENTORY.json"
    )

    assert result["check_passed"] is True
    assert result["status"] == "passed"
    assert result["reason"] == "inventory_updated_in_change_set"


@pytest.mark.unit
def test_inventory_guard_ignores_test_files(tmp_path, monkeypatch):
    """Guard should ignore test-file changes even when trigger keywords are present."""
    inventory_path = tmp_path / "development_tools" / "config" / "DEPRECATION_INVENTORY.json"
    inventory_path.parent.mkdir(parents=True, exist_ok=True)
    inventory_path.write_text('{"active_or_candidate_inventory": [], "removed_inventory": []}', encoding="utf-8")

    test_file = tmp_path / "tests" / "unit" / "test_example.py"
    test_file.parent.mkdir(parents=True, exist_ok=True)
    test_file.write_text("value = 1\n", encoding="utf-8")

    def fake_run(cmd, **kwargs):
        if cmd[:3] == ["git", "status", "--porcelain"]:
            return _completed(stdout=" M tests/unit/test_example.py\n")
        if cmd[:2] == ["git", "diff"]:
            return _completed(stdout=_legacy_marker_line())
        raise AssertionError(f"Unexpected command: {cmd}")

    monkeypatch.setattr(tool_wrappers_module.subprocess, "run", fake_run)

    service = _DummyService(tmp_path)
    result = service._check_deprecation_inventory_sync(
        "development_tools/config/DEPRECATION_INVENTORY.json"
    )

    assert result["check_passed"] is True
    assert result["status"] == "passed"
    assert result["reason"] == "no_deprecation_like_changes_detected"
    assert result["trigger_files"] == []


@pytest.mark.unit
def test_inventory_guard_ignores_generated_reports(tmp_path, monkeypatch):
    """Guard should ignore configured generated report files."""
    inventory_path = tmp_path / "development_tools" / "config" / "DEPRECATION_INVENTORY.json"
    inventory_path.parent.mkdir(parents=True, exist_ok=True)
    inventory_path.write_text('{"active_or_candidate_inventory": [], "removed_inventory": []}', encoding="utf-8")

    report_file = tmp_path / "development_tools" / "AI_PRIORITIES.md"
    report_file.parent.mkdir(parents=True, exist_ok=True)
    report_file.write_text("placeholder\n", encoding="utf-8")

    def fake_run(cmd, **kwargs):
        if cmd[:3] == ["git", "status", "--porcelain"]:
            return _completed(stdout=" M development_tools/AI_PRIORITIES.md\n")
        if cmd[:2] == ["git", "diff"]:
            return _completed(stdout=_legacy_marker_line())
        raise AssertionError(f"Unexpected command: {cmd}")

    monkeypatch.setattr(tool_wrappers_module.subprocess, "run", fake_run)

    service = _DummyService(tmp_path)
    result = service._check_deprecation_inventory_sync(
        "development_tools/config/DEPRECATION_INVENTORY.json"
    )

    assert result["check_passed"] is True
    assert result["status"] == "passed"
    assert result["reason"] == "no_deprecation_like_changes_detected"
    assert result["trigger_files"] == []
