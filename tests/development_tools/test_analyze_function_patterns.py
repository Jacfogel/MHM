"""Tests for development_tools/functions/analyze_function_patterns.py."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from tests.development_tools.conftest import load_development_tools_module

patterns_module = load_development_tools_module("functions.analyze_function_patterns")
analyze_function_patterns = patterns_module.analyze_function_patterns
main = patterns_module.main


@pytest.mark.unit
def test_analyze_function_patterns_detects_expected_patterns(monkeypatch: pytest.MonkeyPatch):
    """Detect class/function patterns across all major buckets."""
    monkeypatch.setattr(patterns_module, "should_exclude_file", lambda *_args, **_kwargs: False)

    actual_functions = {
        "src/module.py": {
            "classes": [
                {
                    "name": "MessageHandler",
                    "methods": [{"name": "can_handle"}, {"name": "handle"}],
                    "has_docstring": True,
                },
                {
                    "name": "LifecycleManager",
                    "methods": [{"name": "start"}, {"name": "shutdown"}],
                    "has_docstring": False,
                },
                {
                    "name": "ThingFactory",
                    "methods": [{"name": "create"}],
                    "has_docstring": True,
                },
                {
                    "name": "DashboardWidget",
                    "methods": [{"name": "render"}],
                    "has_docstring": True,
                },
                {
                    "name": "SettingsDialog",
                    "methods": [{"name": "open"}],
                    "has_docstring": True,
                },
                {
                    "name": "UserValidator",
                    "methods": [{"name": "validate_user"}],
                    "has_docstring": False,
                },
                {
                    "name": "UserSchema",
                    "methods": [{"name": "dict"}],
                    "decorators": ["BaseModel"],
                    "has_docstring": True,
                },
                {
                    "name": "ScopedResource",
                    "methods": [{"name": "__enter__"}, {"name": "__exit__"}],
                    "has_docstring": False,
                },
            ],
            "functions": [
                {"name": "main", "has_docstring": True},
                {"name": "load_user_profile", "has_docstring": True},
                {"name": "send_message_to_channel", "has_docstring": False},
                {"name": "handle_error_response", "has_docstring": True},
                {"name": "create_schedule_job", "has_docstring": False},
                {"name": "handle_errors", "has_docstring": True},
            ],
        }
    }

    patterns = analyze_function_patterns(actual_functions)

    assert len(patterns["handlers"]) == 1
    assert len(patterns["managers"]) == 1
    assert len(patterns["factories"]) == 1
    assert len(patterns["widgets"]) == 1
    assert len(patterns["dialogs"]) == 1
    assert len(patterns["validators"]) == 1
    assert len(patterns["schemas"]) == 1
    assert len(patterns["context_managers"]) == 1
    assert len(patterns["entry_points"]) == 1
    assert len(patterns["data_access"]) == 1
    assert len(patterns["communication"]) == 1
    assert len(patterns["error_handlers"]) == 2
    assert len(patterns["schedulers"]) == 1
    assert len(patterns["decorators"]) == 1


@pytest.mark.unit
def test_analyze_function_patterns_skips_excluded_and_test_paths(monkeypatch: pytest.MonkeyPatch):
    """Excluded files are skipped and test files do not produce non-entrypoint runtime buckets."""
    monkeypatch.setattr(
        patterns_module,
        "should_exclude_file",
        lambda file_path, **_kwargs: file_path.endswith("excluded.py"),
    )

    actual_functions = {
        "src/excluded.py": {
            "classes": [{"name": "MessageHandler", "methods": [{"name": "handle"}]}],
            "functions": [{"name": "main"}],
        },
        "tests/test_runtime_patterns.py": {
            "classes": [],
            "functions": [
                {"name": "load_user_profile"},
                {"name": "send_message_now"},
                {"name": "handle_error_case"},
                {"name": "create_schedule"},
                {"name": "main"},
            ],
        },
    }

    patterns = analyze_function_patterns(actual_functions)

    assert not patterns["handlers"]
    assert not patterns["data_access"]
    assert not patterns["communication"]
    assert not patterns["error_handlers"]
    assert not patterns["schedulers"]
    assert len(patterns["entry_points"]) == 1


@pytest.mark.unit
def test_main_json_with_input_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]):
    """CLI emits JSON when --json and --input are provided."""
    monkeypatch.setattr(patterns_module, "should_exclude_file", lambda *_args, **_kwargs: False)

    input_payload = {
        "src/module.py": {
            "classes": [{"name": "DashboardWidget", "methods": [{"name": "render"}]}],
            "functions": [{"name": "main", "has_docstring": True}],
        }
    }
    input_path = tmp_path / "functions.json"
    input_path.write_text(json.dumps(input_payload), encoding="utf-8")

    monkeypatch.setattr(
        "sys.argv",
        ["analyze_function_patterns.py", "--json", "--input", str(input_path)],
    )

    main()
    output = capsys.readouterr().out
    parsed = json.loads(output)

    assert len(parsed["widgets"]) == 1
    assert len(parsed["entry_points"]) == 1


@pytest.mark.unit
def test_main_uses_scan_all_python_files_when_no_input(monkeypatch: pytest.MonkeyPatch):
    """CLI falls back to function scanning when no --input file is provided."""
    analyze_functions_module = load_development_tools_module("functions.analyze_functions")
    monkeypatch.setattr(
        analyze_functions_module,
        "scan_all_python_files",
        lambda: {
            "src/scanned.py": {
                "classes": [],
                "functions": [{"name": "handle_errors", "has_docstring": True}],
            }
        },
    )
    monkeypatch.setattr(patterns_module, "should_exclude_file", lambda *_args, **_kwargs: False)
    calls = []
    monkeypatch.setattr(patterns_module.logger, "info", lambda message: calls.append(message))
    monkeypatch.setattr("sys.argv", ["analyze_function_patterns.py"])

    main()

    assert any("decorators: 1 found" in str(message) for message in calls)
