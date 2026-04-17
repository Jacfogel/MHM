"""Helper-focused tests for development_tools/shared/service/data_loading.py."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from tests.development_tools.conftest import load_development_tools_module

service_module = load_development_tools_module("shared.service")
output_storage_module = load_development_tools_module("shared.output_storage")
AIToolsService = service_module.AIToolsService


@pytest.mark.unit
def test_load_tool_data_prefers_current_tier_results_cache(temp_project_copy: Path):
    service = AIToolsService(project_root=str(temp_project_copy))
    service.current_audit_tier = 2
    service._tools_run_in_current_tier = {"analyze_functions"}
    service.results_cache["analyze_functions"] = {
        "summary": {"total_issues": 1, "files_affected": 1},
        "details": {"total_functions": 10},
    }

    data = service._load_tool_data("analyze_functions")

    assert data["summary"]["total_issues"] == 1
    assert data["details"]["total_functions"] == 10


@pytest.mark.unit
def test_load_tool_data_falls_back_to_standardized_storage(
    temp_project_copy: Path, monkeypatch: pytest.MonkeyPatch
):
    service = AIToolsService(project_root=str(temp_project_copy))
    service.current_audit_tier = 2
    service._tools_run_in_current_tier = set()

    monkeypatch.setattr(
        output_storage_module,
        "load_tool_result",
        lambda *args, **kwargs: {
            "summary": {"total_issues": 0, "files_affected": 0},
            "details": {"loaded_from": "storage"},
        },
    )
    live_output_storage = sys.modules.get("development_tools.shared.output_storage")
    if live_output_storage is not None and live_output_storage is not output_storage_module:
        monkeypatch.setattr(
            live_output_storage,
            "load_tool_result",
            lambda *args, **kwargs: {
                "summary": {"total_issues": 0, "files_affected": 0},
                "details": {"loaded_from": "storage"},
            },
        )

    data = service._load_tool_data("analyze_functions")
    assert data["details"]["loaded_from"] == "storage"


@pytest.mark.unit
def test_load_tool_data_returns_empty_when_no_sources_found(
    temp_project_copy: Path, monkeypatch: pytest.MonkeyPatch
):
    service = AIToolsService(project_root=str(temp_project_copy))
    service.current_audit_tier = 2
    service._tools_run_in_current_tier = set()

    monkeypatch.setattr(
        output_storage_module,
        "load_tool_result",
        lambda *args, **kwargs: None,
    )
    live_output_storage = sys.modules.get("development_tools.shared.output_storage")
    if live_output_storage is not None and live_output_storage is not output_storage_module:
        monkeypatch.setattr(live_output_storage, "load_tool_result", lambda *args, **kwargs: None)
    data = service._load_tool_data("analyze_functions")
    assert data == {}


@pytest.mark.unit
def test_load_dev_tools_coverage_reads_json_and_builds_standard_shape(
    temp_project_copy: Path,
):
    service = AIToolsService(project_root=str(temp_project_copy))
    coverage_path = (
        temp_project_copy
        / "development_tools"
        / "tests"
        / "jsons"
        / "coverage_dev_tools.json"
    )
    coverage_path.parent.mkdir(parents=True, exist_ok=True)
    coverage_path.write_text(
        """
        {
          "files": {
            "development_tools/shared/service/commands.py": {
              "summary": {
                "num_statements": 10,
                "missing_lines": 3,
                "covered_lines": 7,
                "percent_covered": 70.0
              },
              "missing_lines": [2, 4, 8]
            }
          }
        }
        """.strip(),
        encoding="utf-8",
    )

    service._load_dev_tools_coverage()

    details = service.dev_tools_coverage_results["details"]
    assert details["overall"]["overall_coverage"] == 70.0
    assert details["overall"]["total_statements"] == 10
    assert details["overall"]["total_missed"] == 3
    assert details["coverage_collected"] is True
    assert (
        details["modules"]["development_tools/shared/service/commands.py"]["covered"]
        == 7
    )


@pytest.mark.unit
def test_get_dev_tools_coverage_insights_supports_raw_shape(temp_project_copy: Path):
    service = AIToolsService(project_root=str(temp_project_copy))
    service.dev_tools_coverage_results = {
        "overall": {"overall_coverage": 62.1, "total_statements": 100, "total_missed": 38},
        "modules": {
            "development_tools/shared/service/commands.py": {
                "statements": 10,
                "missed": 6,
                "coverage": 40,
                "covered": 4,
                "missing_lines": ["1", "2"],
            },
            "development_tools/shared/service/audit_orchestration.py": {
                "statements": 20,
                "missed": 8,
                "coverage": 60,
                "covered": 12,
                "missing_lines": ["3"],
            },
        },
    }

    insights = service._get_dev_tools_coverage_insights()

    assert insights is not None
    assert insights["overall_pct"] == 62.1
    assert insights["statements"] == 100
    assert insights["covered"] == 62
    assert insights["low_modules"][0]["path"].endswith("commands.py")


@pytest.mark.unit
def test_parse_doc_sync_output_extracts_status_counts_and_files(temp_project_copy: Path):
    service = AIToolsService(project_root=str(temp_project_copy))
    output = """
Status: FAIL
Total Issues: 4
Paired Doc Issues: 2
Path Drift Issues: 1
Top files with most issues:
- docs/foo.md: 2
- docs/bar.md: 1
ASCII Compliance Issues: 1
"""
    parsed = service._parse_doc_sync_output(output)

    assert parsed["status"] == "FAIL"
    assert parsed["total_issues"] == 4
    assert parsed["paired_doc_issues"] == 2
    assert parsed["path_drift_issues"] == 1
    assert parsed["ascii_issues"] == 1
    assert parsed["path_drift_files"] == ["docs/foo.md", "docs/bar.md"]


@pytest.mark.unit
def test_aggregate_doc_sync_results_sums_component_issues(temp_project_copy: Path):
    service = AIToolsService(project_root=str(temp_project_copy))
    all_results = {
        "paired_docs": {"missing_human_docs": ["a.md", "b.md"]},
        "path_drift": {"summary": {"total_issues": 3}, "files": {"x.py": {}, "y.py": {}}},
        "ascii_compliance": {"summary": {"total_issues": 2}},
        "heading_numbering": {"summary": {"total_issues": 1}},
        "missing_addresses": {"summary": {"total_issues": 4}},
        "unconverted_links": {"summary": {"total_issues": 5}},
    }

    summary = service._aggregate_doc_sync_results(all_results)

    assert summary["status"] == "FAIL"
    assert summary["paired_doc_issues"] == 2
    assert summary["path_drift_issues"] == 3
    assert summary["ascii_issues"] == 2
    assert summary["heading_numbering_issues"] == 1
    assert summary["missing_address_issues"] == 4
    assert summary["unconverted_link_issues"] == 5
    assert summary["total_issues"] == 17
    assert summary["path_drift_files"] == ["x.py", "y.py"]


@pytest.mark.unit
def test_aggregate_doc_sync_results_example_markers_advisory_do_not_affect_total(
    temp_project_copy: Path,
):
    """V5 §3.0: example marker hints are counted separately; they do not fail doc sync."""
    service = AIToolsService(project_root=str(temp_project_copy))
    all_results = {
        "paired_docs": {},
        "path_drift": {"summary": {"total_issues": 0}, "files": {}},
        "ascii_compliance": {"summary": {"total_issues": 0}},
        "heading_numbering": {"summary": {"total_issues": 0}},
        "missing_addresses": {"summary": {"total_issues": 0}},
        "unconverted_links": {"summary": {"total_issues": 0}},
        "example_marker_findings": {
            "a.md": ["line 1"],
            "b.md": ["x", "y"],
        },
    }

    summary = service._aggregate_doc_sync_results(all_results)

    assert summary["status"] == "PASS"
    assert summary["total_issues"] == 0
    assert summary["example_marker_hint_count"] == 3


@pytest.mark.unit
def test_parse_ascii_and_heading_outputs_handle_invalid_json(temp_project_copy: Path):
    service = AIToolsService(project_root=str(temp_project_copy))

    ascii_result = service._parse_ascii_compliance_output("not-json")
    heading_result = service._parse_heading_numbering_output("still-not-json")

    assert ascii_result["summary"]["total_issues"] == 0
    assert heading_result["summary"]["total_issues"] == 0


@pytest.mark.unit
def test_parse_legacy_output_extracts_headline_fields(temp_project_copy: Path):
    service = AIToolsService(project_root=str(temp_project_copy))
    output = """
Files with issues: 9
legacy_compatibility_markers: 14
Report saved to: development_docs/LEGACY_REFERENCE_REPORT.md
"""
    parsed = service._parse_legacy_output(output)
    assert parsed["files_with_issues"] == 9
    assert parsed["legacy_markers"] == 14
    assert parsed["report_path"] == "development_docs/LEGACY_REFERENCE_REPORT.md"


@pytest.mark.unit
def test_get_missing_doc_files_handles_non_list(temp_project_copy: Path):
    service = AIToolsService(project_root=str(temp_project_copy))
    service.results_cache["analyze_function_registry"] = {"missing_files": "not-a-list"}
    assert service._get_missing_doc_files(limit=3) == []

    service.results_cache["analyze_function_registry"] = {
        "missing_files": ["a.py", "b.py", "c.py"]
    }
    assert service._get_missing_doc_files(limit=2) == ["a.py", "b.py"]
