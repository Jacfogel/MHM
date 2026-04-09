"""DEV_TOOLS_* status report scope labels and snapshot coverage (§2.8)."""

import pytest

from tests.development_tools.conftest import load_development_tools_module


service_module = load_development_tools_module("shared.service")
AIToolsService = service_module.AIToolsService


@pytest.mark.unit
def test_dev_tools_scoped_status_snapshot_uses_package_coverage_not_stale_overall(
    temp_project_copy,
):
    service = AIToolsService(project_root=str(temp_project_copy))
    service.dev_tools_only_mode = True
    service._tier3_skipped_main_tracks = True
    service.dev_tools_coverage_results = {
        "summary": {"total_issues": 0, "files_affected": 0},
        "details": {
            "overall": {
                "overall_coverage": 61.7,
                "total_statements": 1000,
                "total_missed": 383,
            },
            "modules": {},
            "coverage_collected": True,
        },
    }

    def _fake_load(tool_name, domain=None, log_source=True):
        base = {
            "analyze_function_registry": {
                "summary": {"total_issues": 0, "files_affected": 0, "status": "PASS"},
                "details": {"coverage": "100.00%", "missing": {"count": 0, "files": {}}},
            },
            "analyze_functions": {
                "summary": {"total_issues": 0, "files_affected": 0, "status": "PASS"},
                "details": {
                    "total_functions": 5,
                    "undocumented": 0,
                    "critical_complexity": 0,
                    "high_complexity": 0,
                    "moderate_complexity": 0,
                },
            },
            "analyze_error_handling": {
                "summary": {"total_issues": 0, "files_affected": 0, "status": "PASS"},
                "details": {
                    "analyze_error_handling": 100.0,
                    "functions_missing_error_handling": 0,
                },
            },
            "analyze_module_refactor_candidates": {
                "summary": {"total_issues": 1, "files_affected": 1, "status": "WARN"},
                "details": {},
            },
        }
        return base.get(tool_name, {})

    service._load_tool_data = _fake_load
    service._load_coverage_summary = lambda: {
        "overall": {
            "coverage": 99.9,
            "covered": 999,
            "statements": 1000,
        },
        "primary_overall": {},
    }
    service._load_dev_tools_coverage = lambda: None

    doc = service._generate_ai_status_document()

    assert "Development Tools Package Coverage (this pass)" in doc
    assert "61.7" in doc and "617" in doc.replace(" ", "")
    assert "999" not in doc.split("## Snapshot")[1].split("## Documentation Signals")[0]
    assert "Full-repo test coverage" not in doc
    assert "Scope note" in doc
    assert "see DEV_TOOLS_PRIORITIES" in doc
    assert "audit --full --dev-tools-only" in doc


@pytest.mark.unit
def test_dev_tools_scoped_status_consolidated_reference_links(temp_project_copy):
    service = AIToolsService(project_root=str(temp_project_copy))
    service.dev_tools_only_mode = True
    # Minimal doc: exercise consolidated header + reference block only if we hit it.
    # _generate_consolidated_report is large; patch _load_tool_data to return empty dicts for most tools.
    service.current_audit_tier = 3

    def _empty_load(tool_name, domain=None, log_source=True, **kwargs):
        return {}

    service._load_tool_data = _empty_load
    service._load_coverage_summary = lambda: None
    service._get_static_analysis_snapshot = lambda: {}
    service._get_canonical_metrics = lambda: {}

    consolidated = service._generate_consolidated_report()
    assert "DEV_TOOLS_PRIORITIES.md" in consolidated
    assert "Full-repo status (not produced by this run)" in consolidated
