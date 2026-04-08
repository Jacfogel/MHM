"""Additional helper-path tests for development_tools/shared/output_storage.py."""

import json
from unittest.mock import patch

import pytest

from tests.development_tools.conftest import load_development_tools_module


output_storage = load_development_tools_module("shared.output_storage")
scope_storage = load_development_tools_module("shared.audit_storage_scope")


@pytest.mark.unit
def test_get_domain_from_tool_name_fallback_patterns(tmp_path):
    """Tool-name heuristics should map to expected domains."""
    assert output_storage._get_domain_from_tool_name("analyze_functions", tmp_path) == "functions"
    assert output_storage._get_domain_from_tool_name("analyze_documentation_sync", tmp_path) == "docs"
    assert output_storage._get_domain_from_tool_name("analyze_error_handling", tmp_path) == "error_handling"
    assert output_storage._get_domain_from_tool_name("run_test_coverage", tmp_path) == "tests"
    assert output_storage._get_domain_from_tool_name("analyze_dependency_patterns", tmp_path) == "imports"
    assert output_storage._get_domain_from_tool_name("analyze_legacy_references", tmp_path) == "legacy"
    assert output_storage._get_domain_from_tool_name("analyze_config", tmp_path) == "config"
    assert output_storage._get_domain_from_tool_name("analyze_ai_work", tmp_path) == "ai_work"
    assert output_storage._get_domain_from_tool_name("quick_status", tmp_path) == "reports"
    assert output_storage._get_domain_from_tool_name("unknown_tool", tmp_path) == "reports"


@pytest.mark.unit
def test_validate_result_files_exist_filters_deleted_and_updates_counts(tmp_path):
    """Validation should remove deleted file references and update summary counts."""
    existing = tmp_path / "docs" / "ok.md"
    existing.parent.mkdir(parents=True, exist_ok=True)
    existing.write_text("ok", encoding="utf-8")

    payload = {
        "files": {"docs/ok.md": ["issue1"], "docs/missing.md": ["issue2", "issue3"]},
        "file_count": 2,
        "total_issues": 3,
        "nested": {"files": {"docs/missing2.md": 5, "docs/ok.md": 1}, "file_count": 2, "total_issues": 6},
    }
    validated = output_storage._validate_result_files_exist(payload, tmp_path)

    assert list(validated["files"].keys()) == ["docs/ok.md"]
    assert validated["file_count"] == 1
    assert validated["total_issues"] == 1
    assert list(validated["nested"]["files"].keys()) == ["docs/ok.md"]
    assert validated["nested"]["total_issues"] == 1


@pytest.mark.unit
def test_load_tool_cache_removes_corrupted_cache(tmp_path):
    """Corrupted cache JSON should return None and delete the cache file."""
    cache_dir = tmp_path / "development_tools" / "docs" / "jsons" / "scopes" / "full"
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_file = cache_dir / ".bad_tool_cache.json"
    cache_file.write_text("{not-json", encoding="utf-8")

    result = output_storage.load_tool_cache("bad_tool", domain="docs", project_root=tmp_path)
    assert result is None
    assert not cache_file.exists()


@pytest.mark.unit
def test_get_all_tool_results_prefers_newer_timestamp(tmp_path):
    """Aggregation should keep the newest result when a tool appears in multiple domains."""
    docs_dir = tmp_path / "development_tools" / "docs" / "jsons" / "scopes" / "full"
    reports_dir = tmp_path / "development_tools" / "reports" / "jsons" / "scopes" / "full"
    docs_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)

    (docs_dir / "same_tool_results.json").write_text(
        json.dumps({"timestamp": "2026-02-25T10:00:00", "data": {"source": "docs"}}),
        encoding="utf-8",
    )
    (reports_dir / "same_tool_results.json").write_text(
        json.dumps({"timestamp": "2026-02-26T10:00:00", "data": {"source": "reports"}}),
        encoding="utf-8",
    )

    results = output_storage.get_all_tool_results(
        project_root=tmp_path, audit_scope=scope_storage.STORAGE_SCOPE_FULL
    )
    assert "same_tool" in results
    assert results["same_tool"]["data"]["source"] == "reports"


@pytest.mark.unit
def test_load_tool_result_returns_none_on_invalid_normalized_payload(tmp_path):
    """load_tool_result should return None when normalization raises ValueError."""
    result_dir = tmp_path / "development_tools" / "docs" / "jsons" / "scopes" / "full"
    result_dir.mkdir(parents=True, exist_ok=True)
    result_file = result_dir / "demo_tool_results.json"
    result_file.write_text(json.dumps({"data": {"x": 1}}), encoding="utf-8")

    with patch(
        "development_tools.shared.result_format.normalize_to_standard_format",
        side_effect=ValueError("bad format"),
    ):
        loaded = output_storage.load_tool_result(
            "demo_tool", domain="docs", project_root=tmp_path, normalize=True
        )

    assert loaded is None
