"""Report generators should surface a full problem payload, not only clean/empty data.

These scenarios exercise the status, priorities, and consolidated builders when
audits find real issues (low coverage, complexity, doc drift, coupling, etc.).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.development_tools.conftest import (
    load_development_tools_module,
    temp_project_copy_paths,
)

service_module = load_development_tools_module("shared.service")
AIToolsService = service_module.AIToolsService


@pytest.fixture(scope="module")
def temp_project_copy():
    """One demo-tree copy per module (report generation uses patched loaders)."""
    fixture_path = Path(__file__).parent.parent / "fixtures" / "development_tools_demo"
    yield from temp_project_copy_paths(fixture_path.resolve())


def _problem_payloads() -> dict[str, dict]:
    """Tool JSON shapes that trigger issue branches in all three report mixins."""
    return {
        "analyze_function_registry": {
            "summary": {"total_issues": 4, "files_affected": 2, "status": "WARN"},
            "details": {
                "coverage": "92.00%",
                "missing": {
                    "count": 4,
                    "files": {
                        "core/alpha.py": ["missing_one", "missing_two"],
                        "ui/beta.py": ["undocumented_widget"],
                        "tasks/gamma.py": ["helper_a"],
                        "notebook/delta.py": ["helper_b"],
                        "storage/epsilon.py": ["helper_c"],
                    },
                },
                "totals": {"functions_documented": 90, "functions_found": 100},
            },
        },
        "analyze_functions": {
            "summary": {"total_issues": 12, "files_affected": 3, "status": "WARN"},
            "details": {
                "total_functions": 2467,
                "undocumented": 8,
                "critical_complexity": 87,
                "high_complexity": 115,
                "moderate_complexity": 297,
                "critical_complexity_examples": [
                    {
                        "function": "_extract_task_entities",
                        "name": "_extract_task_entities",
                        "file": "communication/message_processing/command_parser.py",
                        "complexity": 64,
                    },
                    {
                        "function": "build_user_facing_signal_wellness_snippet",
                        "file": "core/health_context_builder.py",
                        "complexity": 51,
                    },
                ],
                "high_complexity_examples": [
                    {
                        "function": "_format_health_signal_coarse",
                        "file": "core/health_context_builder.py",
                        "complexity": 38,
                    }
                ],
                "undocumented_examples": [
                    {
                        "function": "legacy_helper",
                        "file": "core/legacy_helper.py",
                        "complexity": 12,
                    },
                    {"name": "no_file_helper", "complexity": 3},
                    "plain_string_helper",
                ],
            },
        },
        "analyze_error_handling": {
            "summary": {"total_issues": 6, "files_affected": 2, "status": "WARN"},
            "details": {
                "analyze_error_handling": 54.0,
                "error_handling_coverage": 54.0,
                "functions_missing_error_handling": 6,
                "total_functions": 13,
                "functions_with_error_handling": 7,
                "functions_with_decorators": 5,
                "worst_modules": [
                    {
                        "module": "development_tools.docs",
                        "coverage": 40.0,
                        "missing": 3,
                        "total": 5,
                    },
                    {
                        "module": "ui.widgets",
                        "coverage": 70.0,
                        "missing": 2,
                        "total": 7,
                    },
                ],
                "phase1_total": 2,
                "phase1_by_priority": {"high": 1, "medium": 1, "low": 0},
                "phase1_candidates": [
                    {"file_path": "core/a.py", "priority": "high"},
                    {"file_path": "core/b.py", "priority": "medium"},
                ],
                "phase2_total": 3,
                "phase2_by_type": {"Exception": 2, "ValueError": 1},
                "phase2_exceptions": [
                    {"file_path": "core/a.py"},
                    {"file_path": "core/c.py"},
                ],
                "recommendations": ["Add @handle_errors to remaining helpers"],
            },
        },
        "analyze_documentation": {
            "summary": {"total_issues": 3, "files_affected": 2, "status": "WARN"},
            "details": {
                "section_overlaps": {
                    "Logging": ["LOGGING_GUIDE.md", "AI_LOGGING_GUIDE.md", "README.md"],
                    "Testing": ["TESTING_GUIDE.md", "AI_TESTING_GUIDE.md"],
                },
                "consolidation_recommendations": [
                    {
                        "category": "guides",
                        "files": ["A.md", "B.md", "C.md"],
                        "suggestion": "Merge overlapping logging sections",
                    }
                ],
                "overlap_data_source": "fresh",
                "artifacts": [{"file": "docs/stale.md"}],
                "duplicates": [{"file": "docs/dup.md"}],
                "placeholders": [
                    {"file": "TODO.md", "text": "ignored"},
                    {"file": "docs/WIP.md", "text": "TODO later"},
                ],
            },
        },
        "analyze_documentation_sync": {
            "summary": {
                "total_issues": 9,
                "files_affected": 4,
                "status": "FAIL",
            },
            "details": {
                "path_drift_issues": 2,
                "markdown_link_target_issues": 1,
                "paired_doc_issues": 2,
                "ascii_issues": 1,
                "heading_numbering_issues": 1,
                "missing_address_issues": 1,
                "unconverted_link_issues": 1,
                "path_drift_files": ["docs/drift.md"],
                "example_marker_hint_count": 4,
                "example_marker_findings": {
                    "docs/ex1.md": [10, 11],
                    "docs/ex2.md": [3],
                    "docs/ex3.md": [1],
                    "docs/ex4.md": [8],
                },
            },
        },
        "analyze_ascii_compliance": {
            "summary": {"total_issues": 2, "files_affected": 1, "status": "FAIL"},
            "files": {"docs/ascii.md": 2},
        },
        "analyze_heading_numbering": {
            "summary": {"total_issues": 1, "files_affected": 1, "status": "FAIL"},
            "files": {"docs/headings.md": 1},
        },
        "analyze_missing_addresses": {
            "summary": {"total_issues": 1, "files_affected": 1, "status": "FAIL"},
            "details": {"detailed_issues": {"docs/addresses.md": ["Missing file address"]}},
        },
        "analyze_unconverted_links": {
            "summary": {"total_issues": 3, "files_affected": 1, "status": "FAIL"},
            "files": {"docs/links.md": 3},
        },
        "analyze_todo_sync": {
            "summary": {"total_issues": 1, "files_affected": 1, "status": "WARN"},
            "details": {"completed_still_listed": 1},
        },
        "analyze_legacy_references": {
            "summary": {"total_issues": 2, "files_affected": 2, "status": "WARN"},
            "details": {
                "legacy_markers": 3,
                "report_path": "development_docs/LEGACY_REFERENCE_REPORT.md",
            },
        },
        "analyze_test_markers": {
            "summary": {"total_issues": 5, "files_affected": 2, "status": "FAIL"},
            "details": {
                "missing_count": 3,
                "missing_domain_count": 2,
                "missing": [
                    {"file": "tests/unit/test_a.py", "name": "test_one"},
                    {"file": "tests/unit/test_a.py", "name": "test_two"},
                    {"file": "tests/behavior/test_b.py", "name": "test_three"},
                ],
                "missing_domain": [
                    {"file": "tests/unit/test_c.py", "name": "test_domain"},
                    {"file": "tests/unit/test_d.py", "name": "test_domain_two"},
                ],
            },
        },
        "analyze_backup_health": {
            "summary": {
                "status": "FAIL",
                "success": False,
                "passed_checks": 4,
                "total_checks": 7,
                "latest_backup_path": "data/backups/weekly_backup_old",
                "latest_backup_created_at": "2026-07-01 01:00:00",
            },
            "details": {
                "checks": [
                    {"name": "weekly_backup_present", "success": True, "details": {"path": "ok"}},
                    {
                        "name": "weekly_backup_recent_enough",
                        "success": False,
                        "details": {"age_days": 40},
                    },
                    {"name": "restore_drill", "success": False, "details": "drill skipped"},
                    "not-a-dict",
                ]
            },
        },
        "verify_process_cleanup": {
            "summary": {"total_issues": 2, "files_affected": 0, "status": "WARN"},
            "details": {"platform": "win32", "candidate_orphans": 2},
        },
        "analyze_ruff": {
            "summary": {"total_issues": 4, "files_affected": 2, "status": "FAIL"},
            "details": {
                "tool_available": True,
                "violations_by_rule": {"F401": 3, "E402": 1},
            },
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
        "analyze_bandit": {
            "summary": {"total_issues": 2, "files_affected": 1, "status": "FAIL"},
            "details": {"tool_available": True, "medium_or_high": 2},
        },
        "analyze_pip_audit": {
            "summary": {"total_issues": 1, "files_affected": 1, "status": "WARN"},
            "details": {
                "tool_available": True,
                "pip_audit_execution_state": "executed_subprocess",
                "pip_audit_subprocess_seconds": 1.25,
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
        "analyze_vulture": {
            "summary": {"total_issues": 5, "files_affected": 2, "status": "FAIL"},
            "details": {"tool_available": True, "dead_code": 5},
        },
        "analyze_dependency_patterns": {
            "summary": {"total_issues": 4, "files_affected": 4, "status": "WARN"},
            "details": {
                "circular_dependencies": [
                    ["core/config.py", "core/logger.py", "core/config.py"],
                    ["ai/router.py", "communication/bridge.py"],
                    ["tasks/a.py", "tasks/b.py"],
                ],
                "high_coupling": [
                    {"file": "ai/chatbot.py", "import_count": 21},
                    {"file": "communication/core/channel_orchestrator.py", "import_count": 19},
                    {"file": "core/service.py", "import_count": 17},
                ],
            },
        },
        "analyze_dev_tools_import_boundaries": {
            "summary": {"total_issues": 2, "files_affected": 2, "status": "FAIL"},
            "details": {
                "violations": [
                    {"file": "development_tools/foo.py", "module": "core.logger"},
                    {"file": "development_tools/bar.py", "module": "core.config"},
                ]
            },
        },
        "analyze_duplicate_functions": {
            "summary": {"total_issues": 2, "files_affected": 0, "status": "WARN"},
            "details": {
                "groups_capped": True,
                "cache": {"total_files": 10, "cached_files": 4, "scanned_files": 6},
                "duplicate_groups": [
                    {
                        "functions": [
                            {"name": "save_a", "file": "core/a.py"},
                            {"name": "save_b", "file": "core/b.py"},
                        ],
                        "similarity_range": {"max": 0.95, "min": 0.9},
                    },
                    {
                        "functions": [
                            {"name": "load_a", "file": "ui/a.py"},
                            {"name": "load_b", "file": "ui/b.py"},
                            {"name": "load_c", "file": "ui/c.py"},
                        ],
                        "similarity_range": {"max": 0.88},
                    },
                ],
            },
        },
        "analyze_unused_functions": {
            "summary": {
                "total_issues": 2,
                "files_affected": 2,
                "total_definitions_scanned": 80,
            },
            "details": {
                "unused_functions": [
                    {
                        "full_name": "core.foo.old_helper",
                        "file": "core/foo.py",
                        "line": 12,
                    },
                    {
                        "full_name": "ui.bar.dead_fn",
                        "file": "ui/bar.py",
                        "line": 40,
                    },
                ]
            },
        },
        "analyze_facade_shims": {
            "summary": {"total_issues": 1, "files_affected": 1, "status": "WARN"},
            "details": {
                "findings": [
                    {
                        "file": "core/facade.py",
                        "line": 10,
                        "symbol": "old_task",
                        "kind": "thin_wrapper",
                        "target": "new_task",
                    }
                ]
            },
        },
        "analyze_module_refactor_candidates": {
            "summary": {"total_issues": 3, "files_affected": 3, "status": "WARN"},
            "details": {
                "candidates": [
                    {
                        "file": "communication/message_processing/command_parser.py",
                        "lines": 2668,
                        "functions": 45,
                    },
                    {"file": "core/logger.py", "lines": 1805, "functions": 45},
                    {
                        "file": "ui/widgets/checkin_settings_widget.py",
                        "lines": 1497,
                        "functions": 47,
                    },
                ]
            },
        },
        "analyze_module_imports": {
            "summary": {"total_issues": 0, "files_affected": 0, "status": "PASS"},
            "details": {
                "data": {
                    "core/config.py": {"total_imports": 8},
                    "ai/chatbot.py": {"total_imports": 21},
                }
            },
        },
        "analyze_function_patterns": {
            "summary": {"total_issues": 1, "files_affected": 1},
            "details": {
                "handlers": [
                    {
                        "class": "BareHandler",
                        "file": "communication/h.py",
                        "methods": 9,
                        "has_doc": False,
                    },
                    {
                        "class": "DocumentedHandler",
                        "file": "communication/d.py",
                        "methods": 2,
                        "has_doc": True,
                    },
                ]
            },
        },
        "analyze_ai_work": {
            "summary": {"total_issues": 1, "files_affected": 1, "status": "WARN"},
            "output": "AI Work Validation: NEEDS ATTENTION - structural validation issues detected",
        },
        "decision_support": {
            "summary": {"total_issues": 87, "files_affected": 10},
            "details": {
                "total_functions": 2467,
                "moderate_complexity": 297,
                "high_complexity": 115,
                "critical_complexity": 87,
                "critical_complexity_examples": [
                    {
                        "function": "cached_critical",
                        "file": "core/cached.py",
                        "complexity": 70,
                    }
                ],
                "high_complexity_examples": [
                    {
                        "function": "cached_high",
                        "file": "core/cached.py",
                        "complexity": 40,
                    }
                ],
            },
        },
        "analyze_test_coverage": {
            "summary": {"total_issues": 100, "files_affected": 1},
            "details": {
                "overall": {
                    "coverage": 78.5,
                    "statements": 29245,
                    "covered": 22948,
                    "missed": 6297,
                }
            },
        },
    }


def _coverage_summary() -> dict:
    return {
        "overall": {
            "coverage": "78.5%",
            "covered": 22948,
            "statements": 29245,
            "missed": 6297,
        },
        "modules": [
            {
                "module": "development_tools",
                "coverage": 78.5,
                "missed": 6297,
                "statements": 29245,
            },
            {"module": "ui", "coverage": "72.4", "missed": 2000, "statements": 7377},
        ],
        "worst_files": [
            {
                "path": "development_tools/shared/service/report_generation_consolidated.py",
                "coverage": 31.0,
                "missing": 1063,
            }
        ],
    }


def _wire_problem_service(service: AIToolsService, temp_project_copy: Path) -> None:
    payloads = _problem_payloads()

    docs = temp_project_copy / "docs"
    docs.mkdir(exist_ok=True)
    (docs / "ascii.md").write_text("ascii", encoding="utf-8")
    (docs / "headings.md").write_text("headings", encoding="utf-8")
    (docs / "addresses.md").write_text("addresses", encoding="utf-8")
    (docs / "links.md").write_text("links", encoding="utf-8")

    reports = temp_project_copy / "development_docs"
    reports.mkdir(exist_ok=True)
    (reports / "TEST_COVERAGE_REPORT.md").write_text("# coverage\n", encoding="utf-8")
    (reports / "LEGACY_REFERENCE_REPORT.md").write_text("# legacy\n", encoding="utf-8")

    def fake_load(tool_name, domain=None, log_source=True, **kwargs):
        return payloads.get(tool_name, {})

    service.current_audit_tier = 3
    service._audit_in_progress = False
    service._load_tool_data = fake_load
    service._load_coverage_summary = _coverage_summary
    service._load_dev_tools_coverage = lambda: None
    service._load_results_file_safe = lambda: None
    service._load_config_validation_summary = lambda: {
        "config_valid": False,
        "config_complete": False,
        "tools_using_config": 10,
        "total_tools": 12,
        "recommendations": ["Import config in remaining tools"],
        "tools_analysis": {
            "analyze_ruff": {"imports_config": False, "issues": ["missing import"]},
            "analyze_docs": {"imports_config": True, "issues": ["import config omitted"]},
        },
    }
    service.results_cache = {
        "analyze_functions": payloads["analyze_functions"],
        "decision_support": payloads["decision_support"],
    }
    service.dev_tools_coverage_results = {
        "summary": {"total_issues": 0, "files_affected": 0},
        "details": {
            "overall": {
                "overall_coverage": 78.5,
                "total_statements": 29245,
                "total_missed": 6297,
            },
            "modules": {
                "development_tools/shared/service/report_generation_consolidated.py": {
                    "coverage": 31.0,
                    "missed": 1063,
                    "statements": 1545,
                }
            },
        },
    }
    service.system_signals = {"summary": {"status": "WARN"}, "details": {}}
    service._get_system_signals_details = lambda data: {
        "system_health": {
            "overall_status": "WARN",
            "audit_freshness": "<24 hours",
            "test_coverage_status": "Below target",
            "severity_levels": {
                "CRITICAL": ["development_tools coverage below 80%"],
                "WARNING": ["high fan-out in chatbot.py"],
            },
        },
        "recent_activity": {
            "recent_changes": ["a.py", "b.py", "c.py", "d.py"],
        },
    }


@pytest.mark.unit
def test_problem_payload_renders_status_priorities_and_consolidated(
    temp_project_copy: Path,
) -> None:
    """A dirty audit snapshot should appear in all three generated reports."""
    service = AIToolsService(project_root=str(temp_project_copy))
    _wire_problem_service(service, temp_project_copy)

    status_doc = service._generate_ai_status_document()
    priorities_doc = service._generate_ai_priorities_document()
    consolidated_doc = service._generate_consolidated_report()

    assert "Tier 3 (Full Audit)" in status_doc
    assert "## Snapshot" in status_doc
    assert "Error Handling Coverage" in status_doc
    assert "## Documentation Signals" in status_doc
    assert "## Documentation Overlap" in status_doc
    assert "Section Overlaps" in status_doc or "sections duplicated" in status_doc
    assert "## Test Coverage" in status_doc
    assert "development_tools" in status_doc
    assert "## Test Markers" in status_doc
    assert "Missing Category Markers" in status_doc
    assert "## Static Analysis" in status_doc
    assert "Bandit" in status_doc
    assert "Vulture" in status_doc
    assert "## Dependency Patterns" in status_doc
    assert "## Import Boundary" in status_doc
    assert "non-approved core import" in status_doc
    assert "## Legacy References" in status_doc
    assert "still reference legacy patterns" in status_doc
    assert "Potential Duplicate Groups" in status_doc
    assert "Unused/Uncalled Functions" in status_doc
    assert "Facade/Shim Candidates" in status_doc
    assert "Large Modules" in status_doc
    assert "NEEDS ATTENTION" in status_doc
    assert "## Backup Health" in status_doc
    assert "FAIL" in status_doc
    assert "## System Signals" in status_doc
    assert "development_tools coverage below 80%" in status_doc

    assert "## Immediate Focus Ranked" in priorities_doc
    assert "Raise coverage for domains below target" in priorities_doc
    assert "Reduce dependency pattern risk" in priorities_doc
    assert "Refactor high-complexity functions" in priorities_doc or "complexity" in priorities_doc.lower()
    assert "Triage documentation example-marker hints" in priorities_doc
    assert "doc-fix --fix-ascii" in priorities_doc or "ASCII" in priorities_doc

    assert "## Executive Summary" in consolidated_doc
    assert "## Documentation Status" in consolidated_doc
    assert "## Documentation Overlap" in consolidated_doc
    assert "`Logging` appears in:" in consolidated_doc or "Logging" in consolidated_doc
    assert "Consolidation Opportunities" in consolidated_doc
    assert "## Error Handling" in consolidated_doc
    assert "Phase 1 Candidates" in consolidated_doc
    assert "Top candidate modules" in consolidated_doc
    assert "## Test Coverage" in consolidated_doc
    assert "Domains with Lowest Coverage" in consolidated_doc
    assert "Modules with Lowest Coverage" in consolidated_doc
    assert "## Complexity & Refactoring" in consolidated_doc
    assert "_extract_task_entities" in consolidated_doc
    assert "## Function Patterns" in consolidated_doc
    assert "Handler Classes" in consolidated_doc
    assert "Duplicate Function Groups" in consolidated_doc
    assert "old_helper" in consolidated_doc
    assert "## Module Imports" in consolidated_doc
    assert "Total Imports" in consolidated_doc
    assert "## Dependency Patterns" in consolidated_doc
    assert "Circular Dependencies" in consolidated_doc
    assert "## Import Boundary" in consolidated_doc
    assert "development_tools/foo.py" in consolidated_doc
    assert "## Backup Health" in consolidated_doc
    assert "Weekly Backup Recency" in consolidated_doc
    assert "Restore Drill" in consolidated_doc
    assert "Tools missing config module import" in consolidated_doc
    assert "Pytest process cleanup" in consolidated_doc or "orphan" in consolidated_doc.lower()


@pytest.mark.unit
def test_dev_tools_scoped_problem_payload_uses_scoped_headers(
    temp_project_copy: Path,
) -> None:
    """Dev-tools-only mode should label all three reports as scoped snapshots."""
    service = AIToolsService(project_root=str(temp_project_copy))
    _wire_problem_service(service, temp_project_copy)
    service.dev_tools_only_mode = True

    status_doc = service._generate_ai_status_document()
    priorities_doc = service._generate_ai_priorities_document()
    consolidated_doc = service._generate_consolidated_report()

    assert "Development Tools Status - Scoped Snapshot" in status_doc
    assert "DEV_TOOLS_STATUS.md" in status_doc
    assert "Development Tools Priorities - Immediate Next Steps" in priorities_doc
    assert "DEV_TOOLS_PRIORITIES.md" in priorities_doc
    assert "Development Tools Consolidated Report" in consolidated_doc
    assert "DEV_TOOLS_CONSOLIDATED_REPORT.md" in consolidated_doc
    assert "`development_tools/` scan" in consolidated_doc or "development_tools/" in status_doc


@pytest.mark.unit
def test_mid_audit_write_and_tier1_headers(temp_project_copy: Path) -> None:
    """Mid-audit writes and Tier 1 source lines should still produce a document."""
    service = AIToolsService(project_root=str(temp_project_copy))
    _wire_problem_service(service, temp_project_copy)
    service.current_audit_tier = None
    service._audit_in_progress = True

    status_doc = service._generate_ai_status_document()
    assert "run_development_tools.py status" in status_doc

    service._audit_in_progress = False
    service.current_audit_tier = 1
    priorities_doc = service._generate_ai_priorities_document()
    consolidated_doc = service._generate_consolidated_report()
    assert "audit --quick" in priorities_doc
    assert "Tier 1 (Quick Audit)" in consolidated_doc


@pytest.mark.unit
def test_validation_poor_and_fair_status_lines(temp_project_copy: Path) -> None:
    """Validation copy should distinguish POOR vs FAIR vs generic status text."""
    service = AIToolsService(project_root=str(temp_project_copy))
    _wire_problem_service(service, temp_project_copy)

    payloads = _problem_payloads()
    payloads["analyze_ai_work"] = {"output": "Result: POOR documentation coverage"}

    def fake_load(tool_name, domain=None, log_source=True, **kwargs):
        return payloads.get(tool_name, {})

    service._load_tool_data = fake_load
    poor_status = service._generate_ai_status_document()
    poor_consolidated = service._generate_consolidated_report()
    assert "POOR" in poor_status
    assert "POOR" in poor_consolidated

    payloads["analyze_ai_work"] = {"output": "Result: FAIR structural score"}
    fair_status = service._generate_ai_status_document()
    assert "NEEDS ATTENTION" in fair_status

    payloads["analyze_ai_work"] = {"output": "Validation finished with notes"}
    generic_status = service._generate_ai_status_document()
    assert "Status available" in generic_status
