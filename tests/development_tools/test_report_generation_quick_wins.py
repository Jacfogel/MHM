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
                        "classification": "passed",
                        "passed_count": 0,
                        "failed_count": 0,
                        "error_count": 0,
                        "skipped_count": 0,
                        "return_code": None,
                    },
                    "no_parallel": {
                        "state": "unknown",
                        "classification": "passed",
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
                    "classification": "passed",
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
def test_ai_priorities_include_tier3_failed_tests_in_immediate_focus(temp_project_copy):
    """Tier 3 failed tests should appear as a ranked immediate-focus priority."""
    service = AIToolsService(project_root=str(temp_project_copy))

    payloads = {
        "analyze_test_coverage": {
            "summary": {"total_issues": 100, "files_affected": 1},
            "details": {
                "overall": {"coverage": 70.0, "statements": 10, "covered": 7, "missed": 3},
                "tier3_test_outcome": {
                    "state": "test_failures",
                    "parallel": {
                        "state": "failed",
                        "classification": "failed",
                        "passed_count": 10,
                        "failed_count": 1,
                        "error_count": 0,
                        "skipped_count": 0,
                        "return_code": 1,
                        "failed_node_ids": [
                            "tests/behavior/test_a.py::TestA::test_one",
                        ],
                    },
                    "no_parallel": {
                        "state": "failed",
                        "classification": "failed",
                        "passed_count": 5,
                        "failed_count": 1,
                        "error_count": 0,
                        "skipped_count": 0,
                        "return_code": 1,
                        "failed_node_ids": [
                            "tests/behavior/test_b.py::TestB::test_two",
                        ],
                    },
                    "failed_node_ids": [
                        "tests/behavior/test_a.py::TestA::test_one",
                        "tests/behavior/test_b.py::TestB::test_two",
                    ],
                },
            },
        }
    }

    def fake_load(tool_name, domain=None, log_source=True):
        return payloads.get(tool_name, {})

    service._load_tool_data = fake_load
    service._load_coverage_summary = lambda: {}
    service._load_dev_tools_coverage = lambda: None

    doc = service._generate_ai_priorities_document()

    assert "Investigate and correct test failures/errors" in doc
    assert "Parallel tests failed=1: tests/behavior/test_a.py::test_one." in doc
    assert "No-parallel tests failed=1: tests/behavior/test_b.py::test_two." in doc
    assert "Failing/erroring test(s):" not in doc
    assert "Review for details:" in doc
    assert (
        "stdout files in development_tools/tests/logs" in doc
        or "development_tools/tests/logs/pytest_parallel_stdout_" in doc
        or "development_tools/tests/logs/pytest_no_parallel_stdout_" in doc
        or "development_tools/tests/logs/pytest_dev_tools_stdout_" in doc
    )
    assert "## Immediate Focus Ranked" in doc


@pytest.mark.unit
def test_tier3_crash_metadata_surfaces_in_status_and_priorities(temp_project_copy):
    """Tier 3 crash classification reason/log path should be rendered in reports."""
    service = AIToolsService(project_root=str(temp_project_copy))

    payloads = {
        "analyze_test_coverage": {
            "summary": {"total_issues": 10, "files_affected": 1},
            "details": {
                "tier3_test_outcome": {
                    "state": "crashed",
                    "parallel": {
                        "state": "passed",
                        "classification": "passed",
                        "classification_reason": "pytest_passed",
                        "actionable_context": "Track completed successfully.",
                        "log_file": "development_tools/tests/logs/pytest_parallel_stdout_2026.log",
                        "return_code_hex": "0x00000000",
                        "passed_count": 10,
                        "failed_count": 0,
                        "error_count": 0,
                        "skipped_count": 0,
                        "return_code": 0,
                    },
                    "no_parallel": {
                        "state": "crashed",
                        "classification": "crashed",
                        "classification_reason": "windows_status_dll_not_found",
                        "actionable_context": "Missing DLL or PATH issue in Python/runtime dependencies.",
                        "log_file": "development_tools/tests/logs/pytest_no_parallel_stdout_2026.log",
                        "return_code_hex": "0xC0000135",
                        "passed_count": 0,
                        "failed_count": 0,
                        "error_count": 0,
                        "skipped_count": 0,
                        "return_code": 3221226505,
                    },
                    "failed_node_ids": [],
                }
            },
        },
        "generate_dev_tools_coverage": {
            "summary": {"total_issues": 0, "files_affected": 0},
            "details": {
                "dev_tools_test_outcome": {
                    "state": "passed",
                    "classification": "passed",
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

    status_doc = service._generate_ai_status_document()
    priorities_doc = service._generate_ai_priorities_document()

    assert "No-Parallel Classification" in status_doc
    assert "windows_status_dll_not_found" in status_doc
    assert "pytest_no_parallel_stdout_2026.log" in status_doc
    assert "classification=crashed, reason=windows_status_dll_not_found" in priorities_doc
    assert "0xC0000135" in priorities_doc


@pytest.mark.unit
def test_quick_wins_exclude_unused_imports_when_in_immediate_focus(temp_project_copy):
    """Unused imports are surfaced in Immediate Focus Ranked only; omitted from Quick Wins to avoid duplication."""
    service = AIToolsService(project_root=str(temp_project_copy))

    payloads = {
        "analyze_unused_imports": {
            "summary": {"total_issues": 7, "files_affected": 3},
            "files": {"core/a.py": 4, "core/b.py": 2, "core/c.py": 1},
            "details": {"by_category": {"obvious_unused": 3}},
        }
    }

    def fake_load(tool_name, domain=None, log_source=True):
        return payloads.get(tool_name, {})

    service._load_tool_data = fake_load
    service._load_coverage_summary = lambda: {}
    service._load_dev_tools_coverage = lambda: None

    doc = service._generate_ai_priorities_document()

    # Unused imports appear in Immediate Focus, not Quick Wins
    assert "Remove obvious unused imports" in doc
    assert "Unused imports (obvious):" not in doc


@pytest.mark.unit
def test_quick_wins_skip_unused_imports_when_no_obvious_items(temp_project_copy):
    """Unused imports quick win should be omitted when no obvious removals exist."""
    service = AIToolsService(project_root=str(temp_project_copy))

    payloads = {
        "analyze_unused_imports": {
            "summary": {"total_issues": 7, "files_affected": 3},
            "files": {"core/a.py": 4, "core/b.py": 2, "core/c.py": 1},
            "details": {
                "by_category": {"obvious_unused": 0},
                "findings": {"obvious_unused": []},
            },
        }
    }

    def fake_load(tool_name, domain=None, log_source=True):
        return payloads.get(tool_name, {})

    service._load_tool_data = fake_load
    service._load_coverage_summary = lambda: {}
    service._load_dev_tools_coverage = lambda: None

    doc = service._generate_ai_priorities_document()

    assert "Unused imports (obvious):" not in doc


@pytest.mark.unit
def test_ai_priorities_include_dependency_pattern_recommendations(temp_project_copy):
    """Immediate focus should include dependency-pattern remediation when risks exist."""
    service = AIToolsService(project_root=str(temp_project_copy))

    payloads = {
        "analyze_dependency_patterns": {
            "details": {
                "circular_dependencies": [
                    ["core/config.py", "core/logger.py"],
                    ["core/error_handling.py", "core/time_utilities.py"],
                ],
                "high_coupling": [
                    {"file": "ai/chatbot.py", "import_count": 21},
                    {"file": "communication/core/channel_orchestrator.py", "import_count": 19},
                ],
            }
        }
    }

    def fake_load(tool_name, domain=None, log_source=True):
        return payloads.get(tool_name, {})

    service._load_tool_data = fake_load
    service._load_coverage_summary = lambda: {}
    service._load_dev_tools_coverage = lambda: None

    doc = service._generate_ai_priorities_document()

    assert "Reduce dependency pattern risk" in doc
    assert "2 circular chain(s) and 2 high-coupling module(s) were detected." in doc
    assert "Top circular chains:" in doc
    assert "Top high-coupling modules:" in doc
    assert "run_development_tools.py audit" in doc


@pytest.mark.unit
def test_ai_priorities_combine_error_handling_phase_actions(temp_project_copy):
    """Error-handling modernization should combine Phase 1 and Phase 2 into one priority."""
    service = AIToolsService(project_root=str(temp_project_copy))

    payloads = {
        "analyze_error_handling": {
            "details": {
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
                    {"file_path": "core/c.py"},
                ],
            }
        }
    }

    def fake_load(tool_name, domain=None, log_source=True):
        return payloads.get(tool_name, {})

    service._load_tool_data = fake_load
    service._load_coverage_summary = lambda: {}
    service._load_dev_tools_coverage = lambda: None

    doc = service._generate_ai_priorities_document()

    assert "Modernize error handling (Phase 1 + Phase 2)" in doc
    assert "Phase 1 (decorator-first): 2 function(s)" in doc
    assert "Phase 2 (exception typing): 3 generic exception raise(s)" in doc
    assert "Phase 1: Replace basic try-except with decorators" not in doc
    assert "Phase 2: Categorize generic exceptions" not in doc


@pytest.mark.unit
def test_ai_status_dependency_patterns_section_includes_top_findings(temp_project_copy):
    """AI_STATUS should include dependency summary counts without deep details."""
    service = AIToolsService(project_root=str(temp_project_copy))

    payloads = {
        "analyze_dependency_patterns": {
            "details": {
                "circular_dependencies": [
                    ["core/config.py", "core/logger.py", "core/config.py"],
                    ["ai/router.py", "communication/bridge.py"],
                ],
                "high_coupling": [
                    {"file": "ai/chatbot.py", "import_count": 21},
                    {"file": "communication/core/channel_orchestrator.py", "import_count": 19},
                ],
            }
        }
    }

    def fake_load(tool_name, domain=None, log_source=True):
        return payloads.get(tool_name, {})

    service._load_tool_data = fake_load
    service._load_coverage_summary = lambda: {}
    service._load_dev_tools_coverage = lambda: None

    doc = service._generate_ai_status_document()

    assert "## Dependency Patterns" in doc
    assert "**Circular Dependencies**: 2 circular dependency chain(s)" in doc
    assert "**High Coupling**: 2 high-coupling module(s)" in doc
    assert "**Top Circular Chains**:" not in doc
    assert "**Top High-Coupling Modules**:" not in doc


@pytest.mark.unit
def test_consolidated_dependency_patterns_include_top_findings(temp_project_copy):
    """Consolidated report dependency section should include top chains/modules."""
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
        "analyze_dependency_patterns": {
            "details": {
                "circular_dependencies": [
                    ["core/config.py", "core/logger.py"],
                    ["core/error_handling.py", "core/time_utilities.py"],
                ],
                "high_coupling": [
                    {"file": "ai/chatbot.py", "import_count": 21},
                    {"file": "communication/core/channel_orchestrator.py", "import_count": 19},
                ],
            }
        }
    }

    def fake_load(tool_name, domain=None, log_source=True):
        return payloads.get(tool_name, {})

    service._load_tool_data = fake_load
    service._load_coverage_summary = lambda: {}
    service._load_dev_tools_coverage = lambda: None

    doc = service._generate_consolidated_report()

    assert "## Dependency Patterns" in doc
    assert "**Top Circular Chains**:" in doc
    assert "**Top High-Coupling Modules**:" in doc


@pytest.mark.unit
def test_ai_priorities_include_dev_tools_coverage_when_normalized_shape(temp_project_copy):
    """DEV_TOOLS_PRIORITIES (dev-tools-scoped) should include the dev-tools coverage priority."""
    service = AIToolsService(project_root=str(temp_project_copy))
    service.dev_tools_only_mode = True

    service.dev_tools_coverage_results = {
        "summary": {"total_issues": 12099, "files_affected": 0},
        "details": {
            "overall": {
                "overall_coverage": 47.0,
                "total_statements": 22829,
                "total_missed": 12099,
            },
            "modules": {
                "development_tools/a.py": {"coverage": 35, "missed": 100, "statements": 150},
                "development_tools/b.py": {"coverage": 42, "missed": 80, "statements": 120},
            },
            "html_dir": "development_tools/tests/htmlcov_dev_tools",
        },
    }

    payloads = {}

    def fake_load(tool_name, domain=None, log_source=True):
        return payloads.get(tool_name, {})

    service._load_tool_data = fake_load
    service._load_coverage_summary = lambda: {}
    service._load_dev_tools_coverage = lambda: None

    doc = service._generate_ai_priorities_document()

    assert "Raise development tools coverage" in doc
    assert "Development tools coverage is 47.0%" in doc


@pytest.mark.unit
def test_ai_priorities_warn_and_support_legacy_raw_dev_tools_shape(
    temp_project_copy
):
    """Legacy raw dev-tools coverage payloads should still work with a warning."""
    service = AIToolsService(project_root=str(temp_project_copy))
    service.dev_tools_only_mode = True

    service.dev_tools_coverage_results = {
        "overall": {
            "overall_coverage": 47.0,
            "total_statements": 22829,
            "total_missed": 12099,
        },
        "modules": {
            "development_tools/a.py": {"coverage": 35, "missed": 100, "statements": 150},
            "development_tools/b.py": {"coverage": 42, "missed": 80, "statements": 120},
        },
        "coverage_collected": True,
        "output_file": "development_tools/tests/jsons/coverage_dev_tools.json",
    }

    payloads = {}

    def fake_load(tool_name, domain=None, log_source=True):
        return payloads.get(tool_name, {})

    service._load_tool_data = fake_load
    service._load_coverage_summary = lambda: {}
    service._load_dev_tools_coverage = lambda: None

    doc = service._generate_ai_priorities_document()

    assert "Raise development tools coverage" in doc
    assert "Development tools coverage is 47.0%" in doc


@pytest.mark.unit
def test_ai_priorities_keeps_dev_tools_coverage_when_modules_below_80(
    temp_project_copy,
):
    """Dev-tools-scoped report keeps the coverage priority when module-level coverage is below 80%."""
    service = AIToolsService(project_root=str(temp_project_copy))
    service.dev_tools_only_mode = True

    service.dev_tools_coverage_results = {
        "summary": {"total_issues": 9000, "files_affected": 0},
        "details": {
            "overall": {
                "overall_coverage": 60.0,
                "total_statements": 25000,
                "total_missed": 10000,
            },
            "modules": {
                "development_tools/run_test_coverage.py": {
                    "coverage": 32.0,
                    "missed": 1000,
                    "statements": 1500,
                },
            },
        },
    }

    service._load_tool_data = lambda *args, **kwargs: {}
    service._load_coverage_summary = lambda: {}
    service._load_dev_tools_coverage = lambda: None

    doc = service._generate_ai_priorities_document()

    assert "Raise development tools coverage" in doc
    assert "remain below the 80% target" in doc


@pytest.mark.unit
def test_ai_priorities_omits_dev_tools_coverage_when_overall_and_modules_meet_target(
    temp_project_copy,
):
    """Dev-tools-scoped report omits the priority when overall >=60 and sampled modules >=80."""
    service = AIToolsService(project_root=str(temp_project_copy))
    service.dev_tools_only_mode = True

    service.dev_tools_coverage_results = {
        "summary": {"total_issues": 1000, "files_affected": 0},
        "details": {
            "overall": {
                "overall_coverage": 60.0,
                "total_statements": 1000,
                "total_missed": 400,
            },
            "modules": {
                "development_tools/high_coverage_a.py": {
                    "coverage": 80.0,
                    "missed": 20,
                    "statements": 100,
                },
                "development_tools/high_coverage_b.py": {
                    "coverage": 85.0,
                    "missed": 15,
                    "statements": 100,
                },
            },
        },
    }

    service._load_tool_data = lambda *args, **kwargs: {}
    service._load_coverage_summary = lambda: {}
    service._load_dev_tools_coverage = lambda: None

    doc = service._generate_ai_priorities_document()

    assert "Raise development tools coverage" not in doc


@pytest.mark.unit
def test_ai_priorities_full_audit_does_not_duplicate_dev_tools_coverage_priority(
    temp_project_copy,
):
    """Full-repo AI_PRIORITIES lists development_tools only under domain coverage, not as its own item."""
    service = AIToolsService(project_root=str(temp_project_copy))
    assert service.dev_tools_only_mode is False

    service.dev_tools_coverage_results = {
        "summary": {"total_issues": 12099, "files_affected": 0},
        "details": {
            "overall": {
                "overall_coverage": 47.0,
                "total_statements": 22829,
                "total_missed": 12099,
            },
            "modules": {
                "development_tools/a.py": {"coverage": 35, "missed": 100, "statements": 150},
            },
        },
    }

    service._load_tool_data = lambda *args, **kwargs: {}
    service._load_coverage_summary = lambda: {
        "modules": [
            {
                "module": "development_tools",
                "coverage": 62.0,
                "missed": 9000,
            },
        ]
    }
    service._load_dev_tools_coverage = lambda: None

    doc = service._generate_ai_priorities_document()

    assert "Raise development tools coverage" not in doc
    assert "Raise coverage for domains below target" in doc
    assert "development_tools" in doc


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


@pytest.mark.unit
def test_linkify_review_paths_single_md():
    from development_tools.shared.service.report_generation import _linkify_review_paths_bullet

    line = "Review for guidance: ai_development_docs/AI_TESTING_GUIDE.md"
    out = _linkify_review_paths_bullet(line)
    assert "[AI_TESTING_GUIDE.md](ai_development_docs/AI_TESTING_GUIDE.md)" in out


@pytest.mark.unit
def test_linkify_review_paths_and_json_with_parenthetical():
    from development_tools.shared.service.report_generation import _linkify_review_paths_bullet

    line = (
        "Review for details: development_docs/LEGACY_REFERENCE_REPORT.md (exact locations)"
    )
    out = _linkify_review_paths_bullet(line)
    assert "[LEGACY_REFERENCE_REPORT.md](development_docs/LEGACY_REFERENCE_REPORT.md)" in out
    assert "(exact locations)" in out


@pytest.mark.unit
def test_linkify_review_paths_comma_separated():
    from development_tools.shared.service.report_generation import _linkify_review_paths_bullet

    line = (
        "Review for guidance: ai_development_docs/A.md, ai_development_docs/B.md"
    )
    out = _linkify_review_paths_bullet(line)
    assert "[A.md](ai_development_docs/A.md)" in out
    assert "[B.md](ai_development_docs/B.md)" in out


@pytest.mark.unit
def test_linkify_review_paths_leaves_non_review_lines():
    from development_tools.shared.service.report_generation import _linkify_review_paths_bullet

    line = "Action: run pytest"
    assert _linkify_review_paths_bullet(line) == line
