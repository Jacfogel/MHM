"""Static analysis report integration tests for AI status/priorities/consolidated docs."""

import pytest

from tests.development_tools.conftest import load_development_tools_module


service_module = load_development_tools_module("shared.service")
AIToolsService = service_module.AIToolsService


@pytest.mark.unit
def test_static_analysis_sections_render_in_generated_reports(temp_project_copy):
    service = AIToolsService(project_root=str(temp_project_copy))

    payloads = {
        "analyze_ruff": {
            "summary": {"total_issues": 4, "files_affected": 2, "status": "FAIL"},
            "details": {"violations_by_rule": {"F401": 3, "E402": 1}},
        },
        "analyze_pyright": {
            "summary": {"total_issues": 3, "files_affected": 2, "status": "FAIL"},
            "details": {
                "errors": 2,
                "warnings": 1,
                "tool_available": True,
                "top_error_files": [{"file": "core/a.py", "count": 2}],
                "top_warning_files": [{"file": "ui/b.py", "count": 1}],
            },
        },
        "analyze_pip_audit": {
            "summary": {"total_issues": 1, "files_affected": 1, "status": "WARN"},
            "details": {
                "tool_available": True,
                "vulnerable_packages_with_fix": 0,
                "vulnerable_packages_without_fix": 1,
                "vulnerable_packages": [
                    {
                        "name": "pip",
                        "version": "26.0.1",
                        "vuln_count": 1,
                        "example_id": "CVE-2026-3219",
                        "fix_available": False,
                        "fix_versions": [],
                    }
                ],
            },
        },
        "analyze_function_registry": {
            "summary": {"total_issues": 0, "files_affected": 0, "status": "PASS"},
            "details": {"coverage": "100.00%", "missing": {"count": 0, "files": {}}},
        },
        "analyze_functions": {
            "summary": {"total_issues": 0, "files_affected": 0, "status": "PASS"},
            "details": {
                "total_functions": 10,
                "undocumented": 0,
                "critical_complexity": 0,
                "high_complexity": 0,
                "moderate_complexity": 0,
            },
        },
    }

    def _fake_load(tool_name, domain=None, log_source=True):
        return payloads.get(tool_name, {})

    service._load_tool_data = _fake_load
    service._load_coverage_summary = lambda: {}
    service._load_dev_tools_coverage = lambda: None

    status_doc = service._generate_ai_status_document()
    priorities_doc = service._generate_ai_priorities_document()
    consolidated_doc = service._generate_consolidated_report()

    assert "## Static Analysis" in status_doc
    assert "Ruff" in status_doc and "Pyright" in status_doc
    assert "Address Ruff findings" in priorities_doc
    assert "Address Pyright findings" in priorities_doc
    assert "Review pip-audit dependency vulnerabilities" in priorities_doc
    assert "no advisory fix version is currently published" in priorities_doc
    assert "No fixed version is currently reported" in priorities_doc
    assert "## Static Analysis" in consolidated_doc
    assert "Top Pyright Error Files: a.py (2)" in consolidated_doc
    assert "Top Pyright Warning Files: b.py (1)" in consolidated_doc
    assert "Top pip-audit packages: pip (1, no fixed version reported)" in consolidated_doc
