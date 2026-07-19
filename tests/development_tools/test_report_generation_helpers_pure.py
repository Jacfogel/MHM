"""Unit tests for small, deterministic helpers on ReportGenerationMixin."""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.development_tools.conftest import load_development_tools_module, temp_project_copy_paths

service_module = load_development_tools_module("shared.service")
AIToolsService = service_module.AIToolsService


@pytest.fixture(scope="module")
def temp_project_copy():
    """One demo-tree copy per module (avoids ~5s copytree setup per test)."""
    fixture_path = Path(__file__).parent.parent / "fixtures" / "development_tools_demo"
    yield from temp_project_copy_paths(fixture_path.resolve())


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
    assert "DEV_TOOLS_PIP_AUDIT_SKIP" in service._pip_audit_elapsed_suffix(
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

    assert service._effective_tier3_state_from_outcome({}) == "unknown"
    assert service._effective_tier3_state_from_outcome("not-a-dict") == "unknown"  # type: ignore[arg-type]
    assert service._effective_tier3_state_from_outcome({"state": "crashed"}) == "crashed"
    all_unknown = {
        "parallel": {"classification": "unknown"},
        "no_parallel": {"classification": "unknown"},
        "development_tools": {"classification": "unknown"},
    }
    assert service._effective_tier3_state_from_outcome(all_unknown) == "unknown"
    unclassified_run = {
        "parallel": {"classification": "unknown", "return_code": 2},
        "no_parallel": {"classification": "unknown", "return_code": 2},
        "development_tools": {"classification": "unknown", "return_code": 2},
    }
    assert service._effective_tier3_state_from_outcome(unclassified_run) == "unknown"

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


@pytest.mark.unit
def test_static_analysis_snapshot_defaults_and_normalizes(temp_project_copy: Path) -> None:
    service = AIToolsService(project_root=str(temp_project_copy))
    payloads = {
        "analyze_ruff": {
            "summary": {"total_issues": "3", "files_affected": "2", "status": "WARN"},
            "details": {"tool_available": True, "rule_counts": {"F401": 3}},
        },
        "analyze_pyright": {
            "summary": "bad",
            "details": "bad",
        },
        "analyze_bandit": None,
        "analyze_pip_audit": {
            "summary": {"total_issues": "x", "files_affected": 1},
            "details": {"tool_available": False},
        },
    }

    service._load_tool_data = lambda tool, *_args, **_kwargs: payloads.get(tool)

    snapshot = service._get_static_analysis_snapshot()

    assert snapshot["analyze_ruff"]["available"] is True
    assert snapshot["analyze_ruff"]["summary"]["total_issues"] == 3
    assert snapshot["analyze_pyright"]["summary"]["total_issues"] == 0
    assert snapshot["analyze_bandit"]["available"] is False
    assert snapshot["analyze_pip_audit"]["available"] is False


@pytest.mark.unit
def test_decision_and_system_signal_details_normalize_or_default(temp_project_copy: Path) -> None:
    service = AIToolsService(project_root=str(temp_project_copy))

    decision = service._get_decision_support_details(
        {"summary": {"total_issues": 1}, "details": {"critical_complexity": 2}}
    )
    signals = service._get_system_signals_details(
        {"summary": {"total_issues": 0}, "details": {"status": "ok"}}
    )

    assert isinstance(decision, dict)
    assert isinstance(signals, dict)
    assert service._get_decision_support_details(["bad"]) == {}
    assert service._get_system_signals_details({"summary": []}) == {}


@pytest.mark.unit
def test_get_tier3_test_outcome_merges_dev_tools_cached_track(
    temp_project_copy: Path,
) -> None:
    service = AIToolsService(project_root=str(temp_project_copy))
    payloads = {
        "analyze_test_coverage": {
            "details": {
                "tier3_test_outcome": {
                    "state": "test_failures",
                    "parallel": {"classification": "failed"},
                }
            }
        },
        "generate_dev_tools_coverage": {
            "details": {
                "dev_tools_test_outcome": {
                    "state": "passed",
                    "classification": "passed",
                }
            }
        },
    }
    service._load_tool_data = lambda tool, *_args, **_kwargs: payloads.get(tool, {})

    outcome = service._get_tier3_test_outcome()

    assert outcome["parallel"]["classification"] == "failed"
    assert outcome["development_tools"]["classification"] == "passed"


@pytest.mark.unit
def test_get_tier3_test_outcome_does_not_merge_dev_tools_without_main_outcome(
    temp_project_copy: Path,
) -> None:
    """Coverage-only cache must not synthesize a tier3 outcome from dev-tools data alone."""
    service = AIToolsService(project_root=str(temp_project_copy))
    payloads = {
        "analyze_test_coverage": {
            "details": {"overall": {"coverage": 70.0}},
        },
        "generate_dev_tools_coverage": {
            "details": {
                "dev_tools_test_outcome": {
                    "classification": "unknown",
                }
            }
        },
    }
    service._load_tool_data = lambda tool, *_args, **_kwargs: payloads.get(tool, {})

    assert service._get_tier3_test_outcome() == {}


@pytest.mark.unit
def test_tier3_test_outcome_is_cached_for_report_by_audit_tier(
    temp_project_copy: Path,
) -> None:
    service = AIToolsService(project_root=str(temp_project_copy))
    service.current_audit_tier = 2
    assert service._tier3_test_outcome_is_cached_for_report() is True
    service.current_audit_tier = 3
    service.tier3_test_outcome = {"state": "test_failures"}
    assert service._tier3_test_outcome_is_cached_for_report() is False
    service.tier3_test_outcome = {}
    assert service._tier3_test_outcome_is_cached_for_report() is True


@pytest.mark.unit
def test_effective_tier3_state_unknown_without_run_evidence(
    temp_project_copy: Path,
) -> None:
    service = AIToolsService(project_root=str(temp_project_copy))
    assert service._effective_tier3_state_from_outcome({}) == "unknown"
    assert (
        service._effective_tier3_state_from_outcome(
            {"development_tools": {"classification": "unknown"}}
        )
        == "unknown"
    )
    assert (
        service._effective_tier3_state_from_outcome(
            {
                "state": "test_failures",
                "parallel": {"classification": "failed", "failed_count": 1},
            }
        )
        == "test_failures"
    )


@pytest.mark.unit
def test_append_tier3_test_outcome_lines_respects_actionable_and_skipped_tracks(
    temp_project_copy: Path,
) -> None:
    service = AIToolsService(project_root=str(temp_project_copy))
    service.tier3_test_outcome = {
        "state": "test_failures",
        "parallel": {
            "classification": "skipped",
            "classification_reason": "not_run_this_audit_scope",
        },
        "no_parallel": {"classification": "passed", "passed_count": 4, "return_code": 0},
        "development_tools": {
            "classification": "failed",
            "classification_reason": "pytest_failed",
            "failed_count": 1,
            "return_code": 1,
            "log_file": "development_tools/tests/logs/pytest_dev_tools_stdout_x.log",
            "actionable_context": "Inspect dev tools log.",
        },
        "failed_node_ids": ["tests/dev/test_a.py::TestA::test_one"],
    }

    clean_lines: list[str] = []
    service._append_tier3_test_outcome_lines(clean_lines, actionable_only=True)
    assert clean_lines
    assert not any(line.startswith("- **Parallel Track**") for line in clean_lines)
    assert any("Development Tools Track" in line for line in clean_lines)
    assert any("tests/dev/test_a.py::TestA::test_one" in line for line in clean_lines)

    service.tier3_test_outcome = {
        "state": "clean",
        "parallel": {"classification": "passed"},
        "no_parallel": {"classification": "skipped"},
        "development_tools": {"classification": "skipped"},
    }
    omitted: list[str] = []
    service._append_tier3_test_outcome_lines(omitted, actionable_only=True)
    assert omitted == []


@pytest.mark.unit
def test_recent_tier3_log_files_selects_latest_per_track(temp_project_copy: Path) -> None:
    service = AIToolsService(project_root=str(temp_project_copy))
    logs = temp_project_copy / "development_tools" / "tests" / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    older = logs / "pytest_parallel_stdout_old.log"
    newer = logs / "pytest_parallel_stdout_new.log"
    no_parallel = logs / "pytest_no_parallel_stdout_one.log"
    older.write_text("old", encoding="utf-8")
    newer.write_text("new", encoding="utf-8")
    no_parallel.write_text("np", encoding="utf-8")
    import os
    import time

    os.utime(older, (time.time() - 10, time.time() - 10))
    os.utime(newer, (time.time(), time.time()))

    selected = service._get_recent_tier3_log_files(
        include_parallel=True,
        include_no_parallel=True,
        include_dev_tools=False,
    )

    assert "development_tools/tests/logs/pytest_parallel_stdout_new.log" in selected
    assert "development_tools/tests/logs/pytest_no_parallel_stdout_one.log" in selected
    assert all("old" not in item for item in selected)


@pytest.mark.unit
def test_tier3_detail_log_files_prefer_outcome_track_log_file(
    temp_project_copy: Path,
) -> None:
    """Track log_file from tier3_test_outcome wins over newer stdout logs on disk."""
    service = AIToolsService(project_root=str(temp_project_copy))
    logs = temp_project_copy / "development_tools" / "tests" / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    stdout = logs / "pytest_parallel_stdout_newer.log"
    stdout.write_text("stdout", encoding="utf-8")
    junit = (
        temp_project_copy
        / "development_tools"
        / "tests"
        / "jsons"
        / "test_suite_junit"
        / "parallel.xml"
    )
    junit.parent.mkdir(parents=True, exist_ok=True)
    junit.write_text("<testsuites/>", encoding="utf-8")

    outcome = {
        "state": "test_failures",
        "parallel": {
            "classification": "failed",
            "failed_count": 1,
            "log_file": str(junit),
        },
    }
    selected = service._get_tier3_detail_log_files(
        outcome,
        include_parallel=True,
        include_no_parallel=False,
        include_dev_tools=False,
    )

    assert selected == ["development_tools/tests/jsons/test_suite_junit/parallel.xml"]
    assert all("pytest_parallel_stdout" not in item for item in selected)


@pytest.mark.unit
def test_tier3_detail_log_files_fall_back_to_stdout_when_track_has_no_log_file(
    temp_project_copy: Path,
) -> None:
    service = AIToolsService(project_root=str(temp_project_copy))
    logs = temp_project_copy / "development_tools" / "tests" / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    stdout = logs / "pytest_parallel_stdout_only.log"
    stdout.write_text("stdout", encoding="utf-8")

    outcome = {
        "state": "test_failures",
        "parallel": {"classification": "failed", "failed_count": 1},
    }
    selected = service._get_tier3_detail_log_files(
        outcome,
        include_parallel=True,
        include_no_parallel=False,
        include_dev_tools=False,
    )

    assert selected == ["development_tools/tests/logs/pytest_parallel_stdout_only.log"]


@pytest.mark.unit
def test_verify_process_cleanup_lines_cover_platform_and_candidates(
    temp_project_copy: Path,
) -> None:
    service = AIToolsService(project_root=str(temp_project_copy))

    assert "No data" in service._lines_for_verify_process_cleanup_status_snapshot(None)[0]
    assert "N/A" in service._lines_for_verify_process_cleanup_status_snapshot(
        {"details": {"platform": "linux"}, "summary": {}}
    )[0]
    warn = service._lines_for_verify_process_cleanup_status_snapshot(
        {
            "details": {"platform": "win32"},
            "summary": {"total_issues": 2, "status": "WARN"},
        }
    )
    assert "WARN" in warn[0]

    json_path = (
        temp_project_copy
        / "development_tools"
        / "tests"
        / "jsons"
        / "verify_process_cleanup_results.json"
    )
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text("{}", encoding="utf-8")
    section = service._lines_for_verify_process_cleanup_consolidated_section(
        {
            "details": {
                "platform": "win32",
                "orphaned_processes_found": True,
                "orphaned_processes": [{"pid": 123, "is_pytest": True}],
            },
            "summary": {"total_issues": 1, "status": "WARN"},
        }
    )
    joined = "\n".join(section)
    assert "candidate count=1" in joined
    assert "PID 123" in joined
    assert "verify_process_cleanup_results.json" in joined


@pytest.mark.unit
def test_scoped_tool_result_path_full_vs_dev_tools(temp_project_copy: Path) -> None:
    service = AIToolsService(project_root=str(temp_project_copy))

    assert service._scoped_tool_result_path("functions", "analyze_functions") == (
        "development_tools/functions/jsons/scopes/full/analyze_functions_results.json"
    )
    service.dev_tools_only_mode = True
    assert service._scoped_tool_result_path("docs", "analyze_path_drift") == (
        "development_tools/docs/jsons/scopes/dev_tools/analyze_path_drift_results.json"
    )


@pytest.mark.unit
def test_filter_circular_and_high_coupling_dev_tools(temp_project_copy: Path) -> None:
    service = AIToolsService(project_root=str(temp_project_copy))

    chains = [
        ["ui/a.py", "ui/b.py"],
        ["development_tools/shared/x.py", "ui/y.py"],
        "not-a-list",
        [],
    ]
    kept = service._filter_circular_dependencies_dev_tools(chains)
    assert kept == [["development_tools/shared/x.py", "ui/y.py"]]

    items = [
        {"file": "development_tools/shared/service/core.py", "fan_in": 9},
        {"file": "communication/bot.py", "fan_in": 12},
        {"file": ""},
        "skip",
    ]
    coupled = service._filter_high_coupling_dev_tools(items)
    assert len(coupled) == 1
    assert coupled[0]["file"].endswith("core.py")


@pytest.mark.unit
def test_track_classification_label_and_summary_branches(
    temp_project_copy: Path,
) -> None:
    service = AIToolsService(project_root=str(temp_project_copy))

    assert service._track_classification_label("bad") == "unknown"
    assert service._track_classification_label({}) == "unknown"
    assert service._track_classification_label({"classification": "  failed  "}) == "failed"

    passed = service._format_track_classification_summary(
        "Parallel",
        {
            "classification": "passed",
            "classification_reason": "unknown",
            "return_code_hex": "0x0",
            "log_file": "logs/p.log",
            "actionable_context": "ignore-me",
        },
    )
    assert "Parallel" in passed
    assert "passed" in passed
    assert "return_hex=0x0" in passed
    assert "log=" not in passed
    assert "hint=" not in passed

    failed = service._format_track_classification_summary(
        "Serial",
        {
            "classification": "failed",
            "classification_reason": "test_failures",
            "log_file": "  logs/fail.log  ",
            "actionable_context": "  re-run track  ",
        },
    )
    assert "reason=test_failures" in failed
    assert "log=logs/fail.log" in failed
    assert "hint=re-run track" in failed


@pytest.mark.unit
def test_normalize_tier3_log_file_ref_branches(temp_project_copy: Path) -> None:
    service = AIToolsService(project_root=str(temp_project_copy))

    assert service._normalize_tier3_log_file_ref(None) is None
    assert service._normalize_tier3_log_file_ref("  ") is None
    assert (
        service._normalize_tier3_log_file_ref("development_tools/tests/logs/x.log")
        == "development_tools/tests/logs/x.log"
    )

    abs_inside = temp_project_copy / "development_tools" / "tests" / "logs" / "y.log"
    abs_inside.parent.mkdir(parents=True, exist_ok=True)
    abs_inside.write_text("y", encoding="utf-8")
    assert service._normalize_tier3_log_file_ref(str(abs_inside)) == (
        "development_tools/tests/logs/y.log"
    )

    outside = Path("C:/Windows/Temp/outside.log") if (temp_project_copy.drive) else Path("/tmp/outside.log")
    normalized = service._normalize_tier3_log_file_ref(str(outside))
    assert normalized is not None
    assert "outside.log" in normalized.replace("\\", "/")


@pytest.mark.unit
def test_load_results_file_safe_skips_test_directory(
    temp_project_copy: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    service = AIToolsService(project_root=str(temp_project_copy))
    assert service._is_test_directory(temp_project_copy) is True
    assert service._load_results_file_safe() is None

    results_path = service._get_results_file_path()
    results_path.parent.mkdir(parents=True, exist_ok=True)
    results_path.write_text('{"ok": true}', encoding="utf-8")
    monkeypatch.setattr(service, "_is_test_directory", lambda _p: False)
    assert service._load_results_file_safe() == {"ok": True}

    results_path.write_text("{not-json", encoding="utf-8")
    assert service._load_results_file_safe() is None


@pytest.mark.unit
def test_identify_critical_issues_and_generate_action_items(
    temp_project_copy: Path,
) -> None:
    service = AIToolsService(project_root=str(temp_project_copy))
    service.results_cache = {
        "analyze_functions": {"coverage": "80%"},
        "decision_support": ["High complexity in foo", "other insight"],
    }
    service._last_failed_audits = ["analyze_ruff"]

    issues = service._identify_critical_issues()
    assert any("Low documentation coverage: 80.0%" in i for i in issues)
    assert "Failed audit: analyze_ruff" in issues

    service.results_cache["analyze_functions"] = {"coverage": "not-a-number"}
    assert service._identify_critical_issues() == ["Failed audit: analyze_ruff"]

    actions = service._generate_action_items()
    assert any("Improve documentation coverage" in a for a in actions) is False
    service.results_cache["analyze_functions"] = {"coverage": "90%"}
    actions = service._generate_action_items()
    assert any("Improve documentation coverage (currently 90.0%)" in a for a in actions)
    assert any("Refactor high complexity" in a for a in actions)
    assert "Review TODO.md for next development priorities" in actions


@pytest.mark.unit
def test_tier3_outcome_has_run_evidence_matrix(temp_project_copy: Path) -> None:
    service = AIToolsService(project_root=str(temp_project_copy))

    assert service._tier3_outcome_has_run_evidence({}) is False
    assert service._tier3_outcome_has_run_evidence("bad") is False
    assert service._tier3_outcome_has_run_evidence({"state": "unknown"}) is False
    assert service._tier3_outcome_has_run_evidence({"state": "test_failures"}) is True
    assert (
        service._tier3_outcome_has_run_evidence(
            {"parallel": {"classification_reason": "not_run_this_audit_scope"}}
        )
        is True
    )
    assert (
        service._tier3_outcome_has_run_evidence(
            {"no_parallel": {"classification": "passed"}}
        )
        is True
    )
    assert (
        service._tier3_outcome_has_run_evidence(
            {"development_tools": {"return_code": 1}}
        )
        is True
    )
    assert (
        service._tier3_outcome_has_run_evidence(
            {"parallel": {"classification": "unknown", "return_code": 0}}
        )
        is False
    )


@pytest.mark.unit
def test_get_code_docstring_metrics_edge_cases(
    temp_project_copy: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    service = AIToolsService(project_root=str(temp_project_copy))

    empty = service._get_code_docstring_metrics(
        {"details": {"total_functions": 0, "undocumented": 0}}
    )
    assert empty["total"] == 0
    assert empty["coverage"] is None

    monkeypatch.setattr(service, "_load_tool_data", lambda *_a, **_k: None, raising=True)
    assert service._get_code_docstring_metrics(None) == {
        "total": 0,
        "undocumented": 0,
        "documented": 0,
        "coverage": None,
    }

    loaded = {"details": {"total_functions": -5, "undocumented": 99}}
    monkeypatch.setattr(
        service, "_load_tool_data", lambda *_a, **_k: loaded, raising=True
    )
    clamped = service._get_code_docstring_metrics("not-a-dict")
    # Negative total clamps to 0; undocumented clamp only applies when total > 0.
    assert clamped["total"] == 0
    assert clamped["undocumented"] == 99
    assert clamped["coverage"] is None


@pytest.mark.unit
def test_top_test_marker_files_bullet_empty_and_junk(
    temp_project_copy: Path,
) -> None:
    service = AIToolsService(project_root=str(temp_project_copy))

    assert service._top_test_marker_files_bullet([]) is None
    assert service._top_test_marker_files_bullet(["skip", 1, {"name": "x"}]) is None
    bullet = service._top_test_marker_files_bullet(
        [
            {"file": "tests/a.py", "name": "t1"},
            {"file": "tests/a.py", "name": "t2"},
            {"file": "tests/b.py", "name": "t3"},
        ]
    )
    assert bullet is not None
    assert "Top files:" in bullet
    assert "a.py" in bullet


@pytest.mark.unit
def test_get_results_file_path_dev_tools_scope(temp_project_copy: Path) -> None:
    service = AIToolsService(project_root=str(temp_project_copy))
    full_path = service._get_results_file_path()
    assert "scopes" in str(full_path).replace("\\", "/")
    assert "full" in str(full_path).replace("\\", "/")

    service.dev_tools_only_mode = True
    scoped = service._get_results_file_path()
    assert "dev_tools" in str(scoped).replace("\\", "/")
