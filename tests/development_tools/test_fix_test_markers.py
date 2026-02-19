"""Unit tests for development_tools.tests.fix_test_markers."""

import json

import pytest

from tests.development_tools.conftest import load_development_tools_module


fix_test_markers = load_development_tools_module("tests.fix_test_markers")


@pytest.mark.unit
def test_add_markers_wrapper_calls_analyzer(monkeypatch):
    called = {}
    project_root = "C:/fake/project"

    class FakeAnalyzer:
        def __init__(self, project_root=None):
            called["project_root"] = project_root

        def add_markers(self, dry_run=False):
            called["dry_run"] = dry_run
            return {"updated": [("x.py", "unit")], "skipped": [], "dry_run": dry_run}

    monkeypatch.setattr(fix_test_markers, "TestMarkerAnalyzer", FakeAnalyzer)

    result = fix_test_markers.add_markers(dry_run=True, project_root=project_root)

    assert called["project_root"] == project_root
    assert called["dry_run"] is True
    assert result["dry_run"] is True
    assert result["updated"] == [("x.py", "unit")]


@pytest.mark.unit
def test_main_json_mode(monkeypatch, capsys):
    monkeypatch.setattr(
        fix_test_markers,
        "add_markers",
        lambda dry_run=False: {"updated": [("a.py", "unit")], "skipped": ["b.py"], "dry_run": dry_run},
    )
    monkeypatch.setattr(fix_test_markers.sys, "argv", ["fix_test_markers.py", "--json"])

    rc = fix_test_markers.main()
    output = json.loads(capsys.readouterr().out)

    assert rc == 0
    assert output["updated"] == [["a.py", "unit"]]
    assert output["skipped"] == ["b.py"]
    assert output["dry_run"] is False


@pytest.mark.unit
def test_main_dry_run_text_mode(monkeypatch, capsys):
    monkeypatch.setattr(
        fix_test_markers,
        "add_markers",
        lambda dry_run=False: {"updated": [("a.py", "unit")], "skipped": ["b.py"], "dry_run": dry_run},
    )
    monkeypatch.setattr(fix_test_markers.sys, "argv", ["fix_test_markers.py", "--dry-run"])

    rc = fix_test_markers.main()
    output = capsys.readouterr().out

    assert rc == 0
    assert "Would update 1 files:" in output
    assert "unit: a.py" in output
    assert "Skipped 1 files" in output
