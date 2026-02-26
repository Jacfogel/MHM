"""CLI behavior tests for imports/analyze_module_imports.py."""

import sys

import pytest

from tests.development_tools.conftest import load_development_tools_module


imports_module = load_development_tools_module("imports.analyze_module_imports")


@pytest.mark.unit
def test_main_logs_summary_for_file(monkeypatch):
    """main() should log categorized counts when --file is provided."""
    messages = []

    class StubAnalyzer:
        def extract_imports_from_file(self, _file_path):
            return {
                "standard_library": [{"module": "json"}],
                "third_party": [{"module": "requests"}],
                "local": [{"module": "core.config"}],
            }

        def scan_all_python_files(self):
            return {}

    monkeypatch.setattr(
        imports_module,
        "ModuleImportAnalyzer",
        lambda: StubAnalyzer(),
    )
    monkeypatch.setattr(sys, "argv", ["analyze_module_imports.py", "--file", "demo.py"])
    monkeypatch.setattr(imports_module.logger, "info", lambda message: messages.append(message))

    exit_code = imports_module.main()

    assert exit_code == 0
    assert messages == [
        "Imports from demo.py:",
        "  Standard library: 1",
        "  Third-party: 1",
        "  Local: 1",
    ]


@pytest.mark.unit
def test_main_logs_summary_for_scan(monkeypatch):
    """main() should log scanned file count and total imports for --scan."""
    messages = []

    class StubAnalyzer:
        def extract_imports_from_file(self, _file_path):
            return {}

        def scan_all_python_files(self):
            return {
                "core/config.py": {"total_imports": 3},
                "ui/main_window.py": {"total_imports": 2},
            }

    monkeypatch.setattr(
        imports_module,
        "ModuleImportAnalyzer",
        lambda: StubAnalyzer(),
    )
    monkeypatch.setattr(sys, "argv", ["analyze_module_imports.py", "--scan"])
    monkeypatch.setattr(imports_module.logger, "info", lambda message: messages.append(message))

    exit_code = imports_module.main()

    assert exit_code == 0
    assert messages == [
        "Scanned 2 files",
        "Total imports: 5",
    ]
