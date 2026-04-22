"""Helper-focused tests for development_tools/shared/service/data_loading.py."""

from __future__ import annotations

import json
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


@pytest.mark.unit
def test_config_validation_summary_from_payload_requires_sections(
    temp_project_copy: Path,
):
    service = AIToolsService(project_root=str(temp_project_copy))
    assert service._config_validation_summary_from_payload({"summary": {}}) is None
    assert service._config_validation_summary_from_payload({"details": {}}) is None


@pytest.mark.unit
def test_config_validation_summary_from_payload_merges_validation_flags(
    temp_project_copy: Path,
):
    service = AIToolsService(project_root=str(temp_project_copy))
    payload = {
        "summary": {
            "total_issues": 0,
            "files_affected": 0,
            "config_valid": False,
            "config_complete": False,
        },
        "details": {
            "summary": {"config_valid": False, "config_complete": False},
            "validation": {"config_structure_valid": True},
            "completeness": {"sections_complete": True},
            "recommendations": ["fix a"],
            "tools_analysis": {"k": 1},
        },
    }
    out = service._config_validation_summary_from_payload(payload)
    assert out is not None
    assert out["config_valid"] is True
    assert out["config_complete"] is True
    assert out["recommendations"] == ["fix a"]
    assert out["tools_analysis"] == {"k": 1}


@pytest.mark.unit
def test_load_config_validation_summary_prefers_results_cache(
    temp_project_copy: Path,
):
    service = AIToolsService(project_root=str(temp_project_copy))
    service._tools_run_in_current_tier = {"analyze_config"}
    service.results_cache["analyze_config"] = {
        "summary": {"total_issues": 0, "files_affected": 0},
        "details": {
            "summary": {"config_valid": True, "config_complete": True},
            "recommendations": [],
            "tools_analysis": {},
        },
    }
    got = service._load_config_validation_summary()
    assert got is not None
    assert got.get("config_valid") is True


@pytest.mark.unit
def test_load_config_validation_summary_reads_legacy_json_file(
    temp_project_copy: Path, monkeypatch: pytest.MonkeyPatch
):
    service = AIToolsService(project_root=str(temp_project_copy))
    service._tools_run_in_current_tier = set()
    cfg_dir = (
        temp_project_copy / "development_tools" / "config" / "jsons"
    )
    cfg_dir.mkdir(parents=True, exist_ok=True)
    inner = {
        "summary": {"total_issues": 1, "files_affected": 1},
        "details": {
            "summary": {"config_valid": False, "config_complete": True},
            "recommendations": [],
            "tools_analysis": {},
        },
    }
    (cfg_dir / "analyze_config_results.json").write_text(
        json.dumps({"data": inner}),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        output_storage_module,
        "load_tool_result",
        lambda *args, **kwargs: None,
    )
    live_output_storage = sys.modules.get("development_tools.shared.output_storage")
    if live_output_storage is not None and live_output_storage is not output_storage_module:
        monkeypatch.setattr(live_output_storage, "load_tool_result", lambda *a, **k: None)

    got = service._load_config_validation_summary()
    assert got is not None
    assert got.get("total_issues") == 1


@pytest.mark.unit
def test_parse_doc_subchecks_json_and_non_json(temp_project_copy: Path):
    service = AIToolsService(project_root=str(temp_project_copy))
    std = {"summary": {"total_issues": 3, "files_affected": 2}, "details": {}}
    blob = json.dumps(std)

    for parser in (
        service._parse_path_drift_output,
        service._parse_missing_addresses_output,
        service._parse_unconverted_links_output,
    ):
        empty = parser("")
        assert empty.get("summary", {}).get("total_issues") == 0
        bad = parser("{not json")
        assert bad.get("summary", {}).get("total_issues") == 0
        ok = parser(blob)
        assert ok["summary"]["total_issues"] == 3
        assert ok["summary"]["files_affected"] == 2


@pytest.mark.unit
def test_parse_module_dependency_report_extracts_metrics(temp_project_copy: Path):
    service = AIToolsService(project_root=str(temp_project_copy))
    text = """
Files scanned: 12
Total imports found: 99
Dependencies documented: 80
Standard library imports: 10
Third-party imports: 20
Local imports: 60
Total missing dependencies: 2
[FILE] a.py: missing doc
[DIR] b/ - ENTIRE FILE MISSING
"""
    out = service._parse_module_dependency_report(text)
    assert out is not None
    assert out["files_scanned"] == 12
    assert out["total_imports"] == 99
    assert out["missing_dependencies"] == 2
    assert "a.py" in out["missing_files"]
    assert any("b/" in s for s in out["missing_sections"])
    assert service._parse_module_dependency_report("") is None


@pytest.mark.unit
def test_parse_test_results_from_output_seed_summary_and_failures(
    temp_project_copy: Path,
):
    service = AIToolsService(project_root=str(temp_project_copy))
    text = """
pytest foo --randomly-seed=424242
2 failed, 10 passed, 1 skipped, 0 warnings
=========================== short test summary info ===========================
FAILED tests/unit/test_x.py::test_one - assert 0
FAILED tests/unit/test_y.py::test_two
"""
    r = service._parse_test_results_from_output(text)
    assert r["random_seed"] == "424242"
    assert r["failed_count"] == 2
    assert r["passed_count"] == 10
    assert r["skipped_count"] == 1
    assert r["warnings_count"] == 0
    assert any(
        x.startswith("tests/unit/test_x.py::test_one") for x in r["failed_tests"]
    )
    assert service._parse_test_results_from_output("")["failed_count"] == 0


@pytest.mark.unit
def test_get_system_status_lists_key_files_and_audit_timestamp(
    temp_project_copy: Path,
):
    service = AIToolsService(project_root=str(temp_project_copy))
    ok_file = temp_project_copy / "present.txt"
    ok_file.write_text("ok", encoding="utf-8")
    service.key_files = [str(ok_file), str(temp_project_copy / "absent.txt")]

    results_dir = (
        temp_project_copy
        / "development_tools"
        / "reports"
        / "scopes"
        / "full"
    )
    results_dir.mkdir(parents=True, exist_ok=True)
    (results_dir / "analysis_detailed_results.json").write_text(
        json.dumps({"timestamp": "2026-04-22T12:00:00"}),
        encoding="utf-8",
    )

    status = service._get_system_status()
    assert "[OK]" in status and "present.txt" in status
    assert "[MISSING]" in status and "absent.txt" in status
    assert "2026-04-22T12:00:00" in status
