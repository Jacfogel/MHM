"""Tests for dev-tools-only report scope (V5 §2.8)."""

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
