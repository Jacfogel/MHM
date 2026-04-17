"""Tests for dev-tools-only report scope (V5 §2.8)."""

from pathlib import Path

import pytest

from tests.development_tools.conftest import load_development_tools_module

service_module = load_development_tools_module("shared.service")
AIToolsService = service_module.AIToolsService


@pytest.mark.unit
def test_dev_tools_scoped_report_helper_matches_flag(temp_project_copy) -> None:
    service = AIToolsService(project_root=str(temp_project_copy))
    assert service._is_dev_tools_scoped_report() is False
    service.dev_tools_only_mode = True
    assert service._is_dev_tools_scoped_report() is True


@pytest.mark.unit
def test_audit_source_cmd_display_appends_dev_tools_only(temp_project_copy) -> None:
    service = AIToolsService(project_root=str(temp_project_copy))
    service.dev_tools_only_mode = True
    cmd = service._audit_source_cmd_display(
        "python development_tools/run_development_tools.py audit --full"
    )
    assert "--dev-tools-only" in cmd
    assert cmd.count("--dev-tools-only") == 1


@pytest.mark.unit
def test_audit_source_cmd_display_idempotent_when_suffix_present(temp_project_copy) -> None:
    service = AIToolsService(project_root=str(temp_project_copy))
    service.dev_tools_only_mode = True
    base = "python development_tools/run_development_tools.py audit --full --dev-tools-only"
    assert service._audit_source_cmd_display(base) == base


@pytest.mark.unit
def test_full_audit_status_explains_unified_dev_tools_coverage(temp_project_copy: Path) -> None:
    service = AIToolsService(project_root=str(temp_project_copy))
    service._tier3_skipped_main_tracks = False
    service._tier3_skipped_dev_track = True
    service._load_tool_data = lambda *args, **kwargs: {
        "summary": {"total_issues": 0, "files_affected": 0},
        "details": {
            "overall": {"coverage": 69.9, "covered": 38474, "statements": 55017},
            "modules": [],
        },
    } if args[:1] == ("analyze_test_coverage",) else {}
    service.dev_tools_coverage_results = {
        "details": {
            "overall": {"overall_coverage": 62.1, "total_statements": 25045, "total_missed": 9492},
            "modules": {},
        }
    }

    doc = service._generate_ai_status_document()

    assert "Separate `--dev-tools-only` refresh not run in this full-repo Tier 3 pass." in doc
    assert "overall coverage line above already includes `development_tools`" in doc


@pytest.mark.unit
def test_full_audit_priorities_use_duplicate_group_file_count_from_details(
    temp_project_copy: Path,
) -> None:
    service = AIToolsService(project_root=str(temp_project_copy))
    service._load_coverage_summary = lambda: {}
    service._load_dev_tools_coverage = lambda: None

    duplicate_payload = {
        "summary": {"total_issues": 2, "files_affected": 0},
        "details": {
            "duplicate_groups": [
                {
                    "functions": [
                        {"full_name": "a.one", "file": "pkg/a.py"},
                        {"full_name": "b.one", "file": "pkg/b.py"},
                    ],
                    "similarity_range": {"max": 0.9},
                },
                {
                    "functions": [
                        {"full_name": "c.one", "file": "pkg/c.py"},
                        {"full_name": "a.two", "file": "pkg/a.py"},
                    ],
                    "similarity_range": {"max": 0.8},
                },
            ]
        },
    }

    service._load_tool_data = lambda tool_name, domain=None, log_source=True: (
        duplicate_payload if tool_name == "analyze_duplicate_functions" else {}
    )

    doc = service._generate_ai_priorities_document()

    assert "2 potential duplicate groups across 3 files." in doc
