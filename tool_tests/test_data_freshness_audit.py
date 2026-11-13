"""Tests for development_tools.shared.service.data_freshness_audit."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from development_tools.shared.service import data_freshness_audit


@pytest.mark.unit
@pytest.mark.analytics
def test_check_cache_file_for_deleted_files_detects_key_and_value(
    temp_output_dir: Path,
) -> None:
    """Cache scanner should detect deleted file references in keys and string values."""
    cache_file = temp_output_dir / "cache.json"
    payload = {
        "development_tools/shared/operations.py": {"count": 1},
        "items": [
            "development_docs/SESSION_SUMMARY_2025-12-07.md",
            "safe/path.py",
        ],
    }
    cache_file.write_text(json.dumps(payload), encoding="utf-8")

    issues = data_freshness_audit.check_cache_file_for_deleted_files(
        cache_file,
        temp_output_dir,
        {
            "development_tools/shared/operations.py",
            "development_docs/SESSION_SUMMARY_2025-12-07.md",
        },
    )

    issue_paths = {path for path, _ in issues}
    assert "development_tools/shared/operations.py" in issue_paths
    assert "development_docs/SESSION_SUMMARY_2025-12-07.md" in issue_paths


@pytest.mark.unit
@pytest.mark.analytics
def test_check_cache_file_for_deleted_files_reports_read_errors(
    temp_output_dir: Path,
) -> None:
    """Unreadable JSON should produce an error issue instead of raising."""
    cache_file = temp_output_dir / "broken.json"
    cache_file.write_text("{not-json", encoding="utf-8")

    issues = data_freshness_audit.check_cache_file_for_deleted_files(
        cache_file,
        temp_output_dir,
        {"development_tools/shared/operations.py"},
    )

    assert len(issues) == 1
    assert issues[0][0] == ""
    assert "Error reading cache file broken.json" in issues[0][1]


@pytest.mark.unit
@pytest.mark.analytics
def test_verify_file_existence_checks_flags_loop_without_exists(
    temp_output_dir: Path,
) -> None:
    """Static audit should flag file iteration loops missing existence checks."""
    service_dir = temp_output_dir / "development_tools" / "shared" / "service"
    service_dir.mkdir(parents=True, exist_ok=True)

    (service_dir / "data_loading.py").write_text(
        "for file_path in paths:\n"
        "    x = file_path\n",
        encoding="utf-8",
    )
    (service_dir / "report_generation.py").write_text("pass\n", encoding="utf-8")
    (service_dir / "tool_wrappers.py").write_text("pass\n", encoding="utf-8")

    issues = data_freshness_audit.verify_file_existence_checks(temp_output_dir)

    assert any("data_loading.py" in issue for issue in issues)


@pytest.mark.unit
@pytest.mark.analytics
def test_check_generated_reports_for_deleted_files_detects_references(
    temp_output_dir: Path,
) -> None:
    """Report scanner should identify deleted-file references in markdown reports."""
    report_dir = temp_output_dir / "development_tools"
    report_dir.mkdir(parents=True, exist_ok=True)
    (report_dir / "AI_STATUS.md").write_text(
        "Found reference: development_tools/shared/operations.py\n",
        encoding="utf-8",
    )

    issues = data_freshness_audit.check_generated_reports_for_deleted_files(
        temp_output_dir,
        {"development_tools/shared/operations.py"},
    )

    assert issues == [
        ("development_tools/shared/operations.py", "Found in AI_STATUS.md")
    ]


@pytest.mark.unit
@pytest.mark.analytics
def test_audit_data_freshness_returns_expected_summary(
    temp_output_dir: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Top-level audit should aggregate cache/report/code issue counts."""
    report_dir = temp_output_dir / "development_tools"
    report_dir.mkdir(parents=True, exist_ok=True)
    (report_dir / "AI_STATUS.md").write_text(
        "development_tools/shared/operations.py\n",
        encoding="utf-8",
    )

    cache_file = temp_output_dir / "sample_cache.json"
    cache_file.write_text(
        json.dumps({"path": "development_tools/shared/operations.py"}),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        data_freshness_audit,
        "find_all_json_cache_files",
        lambda project_root: [cache_file],
        raising=False,
    )
    monkeypatch.setattr(
        data_freshness_audit,
        "verify_file_existence_checks",
        lambda project_root: ["warning"],
        raising=False,
    )

    results = data_freshness_audit.audit_data_freshness(
        temp_output_dir,
        {"development_tools/shared/operations.py"},
    )

    assert results["summary"]["total_cache_issues"] == 1
    assert results["summary"]["total_report_issues"] == 1
    assert results["summary"]["total_code_issues"] == 1
    assert results["summary"]["cache_files_checked"] == 1
