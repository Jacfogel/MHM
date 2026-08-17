"""Tests for B-016 arbitrary audit-scope helpers and CLI mutual exclusion."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from development_tools.shared.audit_scope import (
    AuditScopeError,
    filter_tools_for_audit_scope_mvp,
    is_known_storage_scope,
    is_path_derived_storage_scope,
    normalize_audit_scope_rel_path,
    resolve_audit_scope,
    storage_slug_for_rel_path,
)
from development_tools.shared.audit_storage_scope import (
    effective_storage_scope,
    get_audit_storage_scope,
    reset_audit_storage_scope,
    set_audit_storage_scope,
)
from development_tools.shared.cli_interface import _audit_command
from development_tools.shared.audit_tiers import get_tier2_groups


@pytest.mark.unit
def test_normalize_rejects_traversal_and_absolute() -> None:
    with pytest.raises(AuditScopeError):
        normalize_audit_scope_rel_path("../outside")
    with pytest.raises(AuditScopeError):
        normalize_audit_scope_rel_path("/abs/path")
    with pytest.raises(AuditScopeError):
        normalize_audit_scope_rel_path("C:/windows")
    assert normalize_audit_scope_rel_path("communication/") == "communication"
    assert normalize_audit_scope_rel_path("ui\\widgets") == "ui/widgets"


@pytest.mark.unit
def test_storage_slug_and_known_scope() -> None:
    assert storage_slug_for_rel_path("communication") == "scope_communication"
    assert storage_slug_for_rel_path("ui/widgets") == "scope_ui_widgets"
    assert is_path_derived_storage_scope("scope_communication")
    assert is_known_storage_scope("full")
    assert is_known_storage_scope("dev_tools")
    assert is_known_storage_scope("scope_communication")
    assert not is_known_storage_scope("evil/../x")


@pytest.mark.unit
def test_resolve_audit_scope_requires_existing_dir(tmp_path: Path) -> None:
    (tmp_path / "communication").mkdir()
    rel, slug = resolve_audit_scope(tmp_path, "communication/")
    assert rel == "communication"
    assert slug == "scope_communication"
    with pytest.raises(AuditScopeError):
        resolve_audit_scope(tmp_path, "missing_pkg")


@pytest.mark.unit
def test_effective_storage_scope_accepts_path_slug() -> None:
    token = set_audit_storage_scope("scope_communication")
    try:
        assert get_audit_storage_scope() == "scope_communication"
        assert effective_storage_scope() == "scope_communication"
        assert effective_storage_scope("scope_ui") == "scope_ui"
    finally:
        reset_audit_storage_scope(token)
    with pytest.raises(ValueError):
        set_audit_storage_scope("not a valid scope")


@pytest.mark.unit
def test_filter_tools_for_audit_scope_mvp() -> None:
    supported, skipped = filter_tools_for_audit_scope_mvp(
        ["analyze_functions", "analyze_documentation_sync", "analyze_error_handling"]
    )
    assert supported == ["analyze_functions", "analyze_error_handling"]
    assert "analyze_documentation_sync" in skipped


@pytest.mark.unit
def test_get_tier2_groups_filters_for_custom_scope() -> None:
    service = MagicMock()
    service.dev_tools_only_mode = False
    service.audit_scope_path = "communication"
    service.audit_scope_slug = "scope_communication"
    service.run_analyze_functions = MagicMock()
    service.run_analyze_error_handling = MagicMock()
    service.run_analyze_duplicate_functions = MagicMock()
    service.run_analyze_unused_functions = MagicMock()
    service.run_analyze_facade_shims = MagicMock()
    service.run_analyze_module_refactor_candidates = MagicMock()
    service.run_analyze_package_exports = MagicMock()
    service.run_analyze_module_imports = MagicMock()
    service.run_analyze_dependency_patterns = MagicMock()
    service.run_analyze_module_dependencies = MagicMock()
    service.run_analyze_function_registry = MagicMock()
    # Unsupported callables still present on service but should be filtered out
    service.run_analyze_documentation_sync = MagicMock()

    independent, dependent = get_tier2_groups(service)
    indep_names = [n for n, _ in independent]
    dep_names = [n for group in dependent for n, _ in group]
    assert "analyze_functions" in indep_names
    assert "analyze_documentation_sync" not in dep_names
    assert "analyze_documentation_sync" in service._audit_scope_skipped_tools


@pytest.mark.unit
def test_audit_command_rejects_scope_with_dev_tools_only(tmp_path: Path) -> None:
    service = MagicMock()
    service.project_root = tmp_path
    service.dev_tools_only_mode = False
    (tmp_path / "communication").mkdir()
    rc = _audit_command(
        service, ["--audit-scope", "communication", "--dev-tools-only"]
    )
    assert rc == 2
    service.run_audit.assert_not_called()


@pytest.mark.unit
def test_audit_command_sets_scope_fields(tmp_path: Path) -> None:
    service = MagicMock()
    service.project_root = tmp_path
    service.dev_tools_only_mode = False
    service.run_audit.return_value = True
    (tmp_path / "communication").mkdir()
    rc = _audit_command(service, ["--audit-scope", "communication"])
    assert rc == 0
    assert service.audit_scope_path == "communication"
    assert service.audit_scope_slug == "scope_communication"
    service.run_audit.assert_called_once()
