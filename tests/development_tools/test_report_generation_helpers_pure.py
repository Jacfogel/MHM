"""Unit tests for small, deterministic helpers on ReportGenerationMixin."""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.development_tools.conftest import load_development_tools_module

service_module = load_development_tools_module("shared.service")
AIToolsService = service_module.AIToolsService


@pytest.mark.unit
def test_path_is_under_development_tools_dir_relative_and_outside(temp_project_copy: Path) -> None:
    service = AIToolsService(project_root=str(temp_project_copy))
    (temp_project_copy / "development_tools" / "pkg").mkdir(parents=True, exist_ok=True)

    assert service._path_is_under_development_tools_dir("development_tools/pkg/a.py") is True
    assert service._path_is_under_development_tools_dir("development_tools") is True
    assert service._path_is_under_development_tools_dir("ui/main.py") is False
    assert service._path_is_under_development_tools_dir("") is False
    assert service._path_is_under_development_tools_dir("  ") is False


@pytest.mark.unit
def test_path_is_under_development_tools_dir_absolute_under_anchor(temp_project_copy: Path) -> None:
    service = AIToolsService(project_root=str(temp_project_copy))
    inner = temp_project_copy / "development_tools" / "inner.py"
    inner.parent.mkdir(parents=True, exist_ok=True)
    inner.write_text("x", encoding="utf-8")

    assert service._path_is_under_development_tools_dir(str(inner)) is True


@pytest.mark.unit
def test_coerce_int_and_extract_file_issue_counts(temp_project_copy: Path) -> None:
    service = AIToolsService(project_root=str(temp_project_copy))

    assert service._coerce_int(None, 3) == 3
    assert service._coerce_int("12", 0) == 12
    assert service._coerce_int("nope", 7) == 7
    assert service._coerce_int(3.9, 0) == 3

    from_files = {
        "files": {"a.py": 2, "b.py": "4", "skip": "x"},
        "details": {"detailed_issues": {"c.py": ["u"]}},
    }
    counts = service._extract_file_issue_counts(from_files)
    assert counts["a.py"] == 2
    assert counts["b.py"] == 4
    assert "skip" not in counts
    assert "c.py" not in counts

    from_details = {
        "details": {
            "detailed_issues": {
                "d.py": ["i1", "i2"],
                "e.py": 5,
            }
        }
    }
    counts2 = service._extract_file_issue_counts(from_details)
    assert counts2["d.py"] == 2
    assert counts2["e.py"] == 5


@pytest.mark.unit
def test_pip_audit_elapsed_suffix_branches(temp_project_copy: Path) -> None:
    service = AIToolsService(project_root=str(temp_project_copy))

    assert service._pip_audit_elapsed_suffix({}) == ""
    assert service._pip_audit_elapsed_suffix("not-a-dict") == ""  # type: ignore[arg-type]

    sub = service._pip_audit_elapsed_suffix(
        {"pip_audit_execution_state": "executed_subprocess", "pip_audit_subprocess_seconds": 1.234}
    )
    assert "pip-audit subprocess" in sub
    assert "1.23" in sub

    assert "reused cached pip-audit" in service._pip_audit_elapsed_suffix(
        {"pip_audit_execution_state": "requirements_lock_cache_hit"}
    )
    assert "MHM_PIP_AUDIT_SKIP" in service._pip_audit_elapsed_suffix(
        {"pip_audit_execution_state": "skipped_env"}
    )

    bad_sub = service._pip_audit_elapsed_suffix(
        {"pip_audit_execution_state": "executed_subprocess", "pip_audit_subprocess_seconds": "x"}
    )
    assert bad_sub == ""


@pytest.mark.unit
def test_normalize_test_node_id_and_failed_nodes(temp_project_copy: Path) -> None:
    service = AIToolsService(project_root=str(temp_project_copy))

    assert service._normalize_test_node_id("") == ""
    assert service._normalize_test_node_id("tests/a.py::test_one") == "tests/a.py::test_one"
    assert (
        service._normalize_test_node_id("tests/a.py::TestC::test_one")
        == "tests/a.py::test_one"
    )

    outcome = {
        "failed_node_ids": [
            "tests/a.py::TestC::test_one",
            "tests/a.py::TestC::test_one",
            "tests/a.py::test_two",
        ]
    }
    assert service._get_track_failed_nodes(outcome) == [
        "tests/a.py::test_one",
        "tests/a.py::test_two",
    ]
    assert service._get_track_failed_nodes({"failed_node_ids": "bad"}) == []  # type: ignore[dict-item]
    assert service._get_track_failed_nodes({}) == []


@pytest.mark.unit
def test_tier3_track_skipped_for_audit_scope_and_effective_state(
    temp_project_copy: Path,
) -> None:
    service = AIToolsService(project_root=str(temp_project_copy))

    assert service._tier3_track_skipped_for_audit_scope({}) is False
    assert service._tier3_track_skipped_for_audit_scope(
        {"classification_reason": "not_run_this_audit_scope"}
    ) is True

    assert service._effective_tier3_state_from_outcome({}) == "coverage_failed"
    assert service._effective_tier3_state_from_outcome("not-a-dict") == "unknown"  # type: ignore[arg-type]
    assert (
        service._effective_tier3_state_from_outcome({"state": "coverage_failed"})
        == "coverage_failed"
    )
    all_unknown = {
        "parallel": {"classification": "unknown"},
        "no_parallel": {"classification": "unknown"},
        "development_tools": {"classification": "unknown"},
    }
    assert service._effective_tier3_state_from_outcome(all_unknown) == "coverage_failed"

    clean = {
        "parallel": {"classification": "passed"},
        "no_parallel": {"classification": "skipped"},
        "development_tools": {"classification": "passed"},
    }
    assert service._effective_tier3_state_from_outcome(clean) == "clean"

    custom_labels = {
        "parallel": {"classification": "custom"},
        "no_parallel": {"classification": "custom"},
        "development_tools": {"classification": "custom"},
    }
    assert service._effective_tier3_state_from_outcome(custom_labels) == "unknown"


@pytest.mark.unit
def test_resolve_report_path_and_markdown_href(temp_project_copy: Path) -> None:
    service = AIToolsService(project_root=str(temp_project_copy))
    rel = service._resolve_report_path("development_tools/reports/x.md")
    assert rel == temp_project_copy / "development_tools" / "reports" / "x.md"

    abs_path = (temp_project_copy / "abs_out.md").resolve()
    abs_path.write_text("", encoding="utf-8")
    got = service._resolve_report_path(str(abs_path))
    assert got.resolve() == abs_path

    nested = temp_project_copy / "development_tools" / "sub" / "t.md"
    nested.parent.mkdir(parents=True, exist_ok=True)
    nested.write_text("", encoding="utf-8")
    href = service._markdown_href_from_dev_tools_report(nested)
    assert href.replace("\\", "/") == "sub/t.md"


@pytest.mark.unit
def test_count_duplicate_affected_files_and_filter_groups_dev_tools(
    temp_project_copy: Path,
) -> None:
    service = AIToolsService(project_root=str(temp_project_copy))

    groups = [
        {
            "functions": [
                {"file": "a.py"},
                {"file": "b.py"},
            ]
        },
        {"functions": [{"file": "a.py"}]},
        {"not": "a-group"},
    ]
    assert service._count_duplicate_affected_files(groups) == 2

    (temp_project_copy / "development_tools" / "d1.py").parent.mkdir(parents=True, exist_ok=True)
    (temp_project_copy / "development_tools" / "d1.py").write_text("", encoding="utf-8")
    (temp_project_copy / "development_tools" / "d2.py").write_text("", encoding="utf-8")

    mixed = [
        {
            "functions": [
                {"file": "development_tools/d1.py"},
                {"file": "development_tools/d2.py"},
            ]
        },
        {
            "functions": [
                {"file": "development_tools/d1.py"},
                {"file": "ui/x.py"},
            ]
        },
    ]
    filtered = service._filter_duplicate_groups_dev_tools(mixed)
    assert len(filtered) == 1
    assert service._count_duplicate_affected_files_dev_tools(mixed) == 2


@pytest.mark.unit
def test_scoped_obvious_unused_import_metrics_counts(temp_project_copy: Path) -> None:
    service = AIToolsService(project_root=str(temp_project_copy))

    payload = {
        "details": {
            "findings": {
                "obvious_unused": [
                    {"file": "development_tools/a.py"},
                    {"file": "ui/b.py"},
                    {"file": "development_tools/a.py"},
                ],
                "type_hints_only": [
                    {"file": "development_tools/c.py"},
                    {"file": "ui/d.py"},
                ],
            }
        }
    }
    obvious, type_only, per_file = service._scoped_obvious_unused_import_metrics(payload)
    assert obvious == 2
    assert type_only == 1
    assert per_file.get("development_tools/a.py") == 2


@pytest.mark.unit
def test_scoped_unused_imports_status_metrics_none_and_totals(
    temp_project_copy: Path,
) -> None:
    service = AIToolsService(project_root=str(temp_project_copy))

    assert service._scoped_unused_imports_status_metrics({}) is None
    assert service._scoped_unused_imports_status_metrics({"details": {"findings": {}}}) is None

    data = {
        "details": {
            "findings": {
                "obvious_unused": [{"file": "development_tools/x.py"}],
                "other_cat": [{"file": "ui/y.py"}],
            }
        }
    }
    total, nfiles, by_cat = service._scoped_unused_imports_status_metrics(data)
    assert total == 1
    assert nfiles == 1
    assert by_cat == {"obvious_unused": 1}


@pytest.mark.unit
def test_test_marker_gap_metrics_branches(temp_project_copy: Path) -> None:
    service = AIToolsService(project_root=str(temp_project_copy))

    c1, d1, m1, dom1 = service._test_marker_gap_metrics(None)
    assert (c1, d1, m1, dom1) == (0, 0, [], [])

    nested = {
        "details": {
            "missing_count": 2,
            "missing_domain_count": 1,
            "missing": [{"file": "a.py"}],
            "missing_domain": [{"file": "b.py"}],
        }
    }
    c2, d2, m2, dom2 = service._test_marker_gap_metrics(nested)
    assert (c2, d2) == (2, 1)
    assert len(m2) == 1 and len(dom2) == 1

    legacy = {"missing_count": 1, "missing": [{"x": 1}]}
    c3, d3, m3, dom3 = service._test_marker_gap_metrics(legacy)
    assert (c3, d3, dom3) == (1, 0, [])

    summary_only = {"summary": {"total_issues": 4}, "missing": []}
    c4, d4, _, _ = service._test_marker_gap_metrics(summary_only)
    assert (c4, d4) == (4, 0)


@pytest.mark.unit
def test_get_code_docstring_metrics_from_payload(temp_project_copy: Path) -> None:
    service = AIToolsService(project_root=str(temp_project_copy))

    payload = {
        "details": {
            "total_functions": 10,
            "undocumented": 3,
        }
    }
    m = service._get_code_docstring_metrics(payload)
    assert m["total"] == 10
    assert m["undocumented"] == 3
    assert m["documented"] == 7
    assert m["coverage"] == pytest.approx(70.0)

    clamped = {
        "details": {
            "total_functions": 5,
            "undocumented": 99,
        }
    }
    m2 = service._get_code_docstring_metrics(clamped)
    assert m2["undocumented"] == 5
    assert m2["documented"] == 0


@pytest.mark.unit
def test_top_test_marker_files_bullet_formats(temp_project_copy: Path) -> None:
    service = AIToolsService(project_root=str(temp_project_copy))

    issues = [
        {"file": "tests/unit/a.py", "name": "t1"},
        {"file": "tests/unit/a.py", "name": "t2"},
        {"file": "tests/unit/b.py", "name": "t3"},
        {"file": "tests/unit/c.py", "name": "t4"},
    ]
    line = service._top_test_marker_files_bullet(issues, limit=2)
    assert line is not None
    assert "Top files:" in line
    assert "a.py" in line
    # Overflow hint is appended then passed through _format_list_for_display, which may truncate.
    assert "+1" in line
