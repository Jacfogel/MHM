"""Tests for AI_PRIORITIES quick wins formatting."""

import pytest

from tests.development_tools.conftest import load_development_tools_module

service_module = load_development_tools_module("shared.service")
AIToolsService = service_module.AIToolsService


@pytest.mark.unit
def test_quick_wins_include_top_offenders_and_fix_commands(temp_project_copy):
    """Quick wins should include standardized top-offender details for doc tools."""
    service = AIToolsService(project_root=str(temp_project_copy))

    payloads = {
        "analyze_ascii_compliance": {
            "summary": {"total_issues": 3, "files_affected": 2},
            "files": {"docs/A.md": 2, "docs/B.md": 1},
        },
        "analyze_heading_numbering": {
            "summary": {"total_issues": 2, "files_affected": 1},
            "files": {"docs/C.md": 2},
        },
        "analyze_missing_addresses": {
            "summary": {"total_issues": 1, "files_affected": 1},
            "details": {"detailed_issues": {"docs/D.md": ["Missing file address in header"]}},
        },
        "analyze_unconverted_links": {
            "summary": {"total_issues": 4, "files_affected": 2},
            "files": {"docs/E.md": 3, "docs/F.md": 1},
        },
    }

    def fake_load(tool_name, domain=None, log_source=True):
        return payloads.get(tool_name, {})

    service._load_tool_data = fake_load
    service._load_coverage_summary = lambda: {}
    service._load_dev_tools_coverage = lambda: None

    doc = service._generate_ai_priorities_document()

    assert "ASCII compliance:" in doc
    assert "Heading numbering:" in doc
    assert "Missing addresses:" in doc
    assert "Unconverted links:" in doc
    assert "Top offenders:" in doc
    assert "doc-fix --fix-ascii" in doc
    assert "doc-fix --number-headings" in doc
    assert "doc-fix --add-addresses" in doc
    assert "doc-fix --convert-links" in doc
    assert "run_development_tools.py doc-sync" in doc


@pytest.mark.unit
def test_ai_priorities_hides_tier3_test_outcome_when_clean(temp_project_copy):
    """AI_PRIORITIES should omit Tier 3 test outcome section when there is no action needed."""
    service = AIToolsService(project_root=str(temp_project_copy))

    payloads = {
        "analyze_test_coverage": {
            "summary": {"total_issues": 0, "files_affected": 0},
            "details": {
                "tier3_test_outcome": {
                    "state": "clean",
                    "parallel": {
                        "state": "unknown",
                        "passed_count": 0,
                        "failed_count": 0,
                        "error_count": 0,
                        "skipped_count": 0,
                        "return_code": None,
                    },
                    "no_parallel": {
                        "state": "unknown",
                        "passed_count": 0,
                        "failed_count": 0,
                        "error_count": 0,
                        "skipped_count": 0,
                        "return_code": None,
                    },
                }
            },
        },
        "generate_dev_tools_coverage": {
            "summary": {"total_issues": 0, "files_affected": 0},
            "details": {
                "dev_tools_test_outcome": {
                    "state": "passed",
                    "passed_count": 10,
                    "failed_count": 0,
                    "error_count": 0,
                    "skipped_count": 0,
                    "return_code": 0,
                }
            },
        },
    }

    def fake_load(tool_name, domain=None, log_source=True):
        return payloads.get(tool_name, {})

    service._load_tool_data = fake_load
    service._load_coverage_summary = lambda: {}
    service._load_dev_tools_coverage = lambda: None

    doc = service._generate_ai_priorities_document()

    assert "## Tier 3 Test Outcome" not in doc
    assert "Fix Tier 3 coverage run failures" not in doc
    assert "Fix Tier 3 failing/erroring tests" not in doc


@pytest.mark.unit
def test_consolidated_report_marks_cached_overlap_data(temp_project_copy):
    """Consolidated report should identify cached overlap data instead of showing not-run."""
    service = AIToolsService(project_root=str(temp_project_copy))

    payloads = {
        "analyze_function_registry": {
            "summary": {"total_issues": 0, "files_affected": 0},
            "details": {"coverage": "100.0%", "totals": {"functions_documented": 1}},
        },
        "analyze_functions": {
            "summary": {"total_issues": 0, "files_affected": 0},
            "details": {
                "total_functions": 1,
                "undocumented": 0,
                "critical_complexity": 0,
                "high_complexity": 0,
                "moderate_complexity": 0,
            },
        },
        "analyze_documentation": {
            "summary": {"total_issues": 0, "files_affected": 0},
            "details": {
                "section_overlaps": {},
                "consolidation_recommendations": [],
                "overlap_data_source": "cached",
            },
        }
    }

    def fake_load(tool_name, domain=None, log_source=True):
        return payloads.get(tool_name, {})

    service._load_tool_data = fake_load
    service._load_coverage_summary = lambda: {}
    service._load_dev_tools_coverage = lambda: None

    doc = service._generate_consolidated_report()

    assert "## Documentation Overlap" in doc
    assert "No overlaps detected (cached overlap data)" in doc
    assert "Overlap analysis not run" not in doc
