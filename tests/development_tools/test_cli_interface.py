"""Tests for development_tools.shared.cli_interface."""

import builtins
import json

import pytest

from tests.development_tools.conftest import load_development_tools_module


class _StubService:
    def __init__(self, *, audit_success=True):
        self.audit_success = audit_success
        self.dev_tools_only_mode = False
        self.exclusion_calls = []
        self.audit_calls = []
        self.module_refactor_calls = []
        self.cleanup_calls = []
        self.docs_calls = 0
        self.validate_calls = 0
        self.config_calls = 0
        self.workflow_calls = []
        self.decision_support_result = {"success": True}
        self.version_sync_scopes = []
        self.status_should_raise = False
        self.system_signals_calls = 0
        self.doc_sync_calls = 0
        self.doc_fix_calls = []
        self.coverage_calls = 0
        self.legacy_calls = 0
        self.unused_imports_result = {"success": True}
        self.unused_imports_report_result = {"success": True}
        self.duplicate_function_calls = []
        self.trees_calls = 0
        self.help_calls = 0
        self.backup_inventory_calls = 0
        self.backup_retention_calls = []
        self.backup_drill_calls = []
        self.backup_verify_calls = []

    def set_exclusion_config(self, include_tests=False, include_dev_tools=False):
        self.exclusion_calls.append((include_tests, include_dev_tools))

    def run_audit(self, quick=False, full=False, include_overlap=False, strict=False):
        self.audit_calls.append((quick, full, include_overlap, strict))
        return self.audit_success

    def run_analyze_module_refactor_candidates(
        self, include_tests=False, include_dev_tools=False
    ):
        self.module_refactor_calls.append((include_tests, include_dev_tools))
        return {"success": True, "data": {"example": 1}}

    def run_cleanup(
        self,
        *,
        cache,
        test_data,
        reports,
        coverage,
        full,
        dry_run,
        include_tool_caches,
    ):
        self.cleanup_calls.append(
            {
                "cache": cache,
                "test_data": test_data,
                "reports": reports,
                "coverage": coverage,
                "full": full,
                "dry_run": dry_run,
                "include_tool_caches": include_tool_caches,
            }
        )
        return {"success": True, "data": {"total_removed": 0, "total_failed": 0}}

    def run_docs(self):
        self.docs_calls += 1
        return True

    def run_validate(self):
        self.validate_calls += 1
        return True

    def run_config(self):
        self.config_calls += 1
        return True

    def run_workflow(self, task_type):
        self.workflow_calls.append(task_type)
        return True

    def run_decision_support(self):
        return self.decision_support_result

    def run_version_sync(self, scope):
        self.version_sync_scopes.append(scope)
        return True

    def run_status(self):
        if self.status_should_raise:
            raise RuntimeError("status failed")

    def run_analyze_system_signals(self):
        self.system_signals_calls += 1
        return True

    def run_documentation_sync(self):
        self.doc_sync_calls += 1
        return True

    def run_documentation_fix(self, *, fix_type, dry_run):
        self.doc_fix_calls.append((fix_type, dry_run))
        return True

    def run_coverage_regeneration(self):
        self.coverage_calls += 1
        return True

    def run_legacy_cleanup(self):
        self.legacy_calls += 1
        return True

    def run_analyze_unused_imports(self):
        return self.unused_imports_result

    def run_unused_imports_report(self):
        return self.unused_imports_report_result

    def run_analyze_duplicate_functions(
        self, *, min_overall=None, min_name=None, consider_body_similarity=False
    ):
        self.duplicate_function_calls.append((min_overall, min_name))
        return {"success": True}

    def generate_directory_trees(self):
        self.trees_calls += 1
        return True

    def show_help(self):
        self.help_calls += 1

    def run_backup_inventory(self):
        self.backup_inventory_calls += 1
        return {"success": True}

    def run_backup_retention(self, *, dry_run, apply):
        self.backup_retention_calls.append((dry_run, apply))
        return {"success": True}

    def run_backup_drill(self, *, backup_path, restore_users, restore_config):
        self.backup_drill_calls.append((backup_path, restore_users, restore_config))
        return {"success": True}

    def run_backup_health_check(self, *, run_drill):
        self.backup_verify_calls.append(run_drill)
        return {"success": True}


@pytest.fixture
def cli_module():
    return load_development_tools_module("shared.cli_interface")


@pytest.mark.unit
def test_audit_command_parses_include_all_and_strict(cli_module):
    """Audit command should wire parsed flags to service methods."""
    service = _StubService(audit_success=True)

    code = cli_module._audit_command(
        service, ["--quick", "--include-all", "--strict", "--overlap"]
    )

    assert code == 0
    assert service.exclusion_calls == [(True, True)]
    assert service.audit_calls == [(True, False, True, True)]
    assert service.dev_tools_only_mode is False


@pytest.mark.unit
def test_audit_command_sets_dev_tools_only_mode(cli_module):
    """--dev-tools-only should flag service for scoped scan and DEV_TOOLS_* report paths."""
    service = _StubService(audit_success=True)

    code = cli_module._audit_command(service, ["--quick", "--dev-tools-only"])

    assert code == 0
    assert service.dev_tools_only_mode is True


@pytest.mark.unit
def test_audit_command_returns_nonzero_when_service_fails(cli_module):
    """Audit command should return 1 when run_audit fails."""
    service = _StubService(audit_success=False)

    code = cli_module._audit_command(service, [])

    assert code == 1
    assert service.exclusion_calls == [(False, False)]
    assert service.audit_calls == [(False, False, False, False)]


@pytest.mark.unit
def test_full_audit_alias_enables_full_mode(cli_module):
    """full-audit alias should behave like audit --full."""
    service = _StubService(audit_success=True)

    code = cli_module._full_audit_command(service, ["--strict"])

    assert code == 0
    assert service.audit_calls == [(False, True, False, True)]


@pytest.mark.unit
def test_module_refactor_candidates_json_output(cli_module, monkeypatch):
    """module-refactor-candidates should print JSON payload when requested."""
    service = _StubService(audit_success=True)
    printed = []
    monkeypatch.setattr(builtins, "print", lambda msg="": printed.append(msg))

    code = cli_module._module_refactor_candidates_command(
        service, ["--json", "--include-all"]
    )

    assert code == 0
    assert service.exclusion_calls == [(True, True)]
    assert service.module_refactor_calls == [(True, True)]
    parsed = json.loads(printed[0])
    assert parsed["example"] == 1


@pytest.mark.unit
def test_cleanup_defaults_clean_all_major_categories(cli_module):
    """cleanup with no flags should clean cache/test-data/coverage."""
    service = _StubService(audit_success=True)

    code = cli_module._cleanup_command(service, [])

    assert code == 0
    assert len(service.cleanup_calls) == 1
    call = service.cleanup_calls[0]
    assert call["cache"] is True
    assert call["test_data"] is True
    assert call["coverage"] is True
    assert call["include_tool_caches"] is True


@pytest.mark.unit
def test_cleanup_unknown_argument_returns_usage_error(cli_module):
    """cleanup should return argparse usage code for unknown args."""
    service = _StubService(audit_success=True)

    code = cli_module._cleanup_command(service, ["--does-not-exist"])

    assert code == 2
    assert service.cleanup_calls == []


@pytest.mark.unit
def test_docs_command_argument_validation(cli_module):
    service = _StubService()
    assert cli_module._docs_command(service, ["--bad"]) == 2
    assert service.docs_calls == 0
    assert cli_module._docs_command(service, []) == 0
    assert service.docs_calls == 1


@pytest.mark.unit
def test_workflow_command_requires_task_type(cli_module):
    service = _StubService()
    assert cli_module._workflow_command(service, []) == 2
    assert cli_module._workflow_command(service, ["nightly-audit"]) == 0
    assert service.workflow_calls == ["nightly-audit"]


@pytest.mark.unit
def test_doc_fix_command_parsing_and_conflict(cli_module):
    service = _StubService()

    ok = cli_module._doc_fix_command(service, ["--fix-ascii", "--dry-run"])
    assert ok == 0
    assert service.doc_fix_calls == [("fix-ascii", True)]

    conflict = cli_module._doc_fix_command(service, ["--fix-ascii", "--convert-links"])
    assert conflict == 2


@pytest.mark.unit
def test_doc_fix_full_alias_maps_to_all(cli_module):
    service = _StubService()

    code = cli_module._doc_fix_command(service, ["--full"])
    assert code == 0
    assert service.doc_fix_calls == [("all", False)]


@pytest.mark.unit
def test_status_command_exception_path(cli_module):
    service = _StubService()
    service.status_should_raise = True

    code = cli_module._status_command(service, [])
    assert code == 1


@pytest.mark.unit
def test_unused_imports_commands_validate_args_and_status(cli_module):
    service = _StubService()

    assert cli_module._unused_imports_command(service, ["--help"]) == 0
    assert cli_module._unused_imports_command(service, ["--bad"]) == 2
    assert cli_module._unused_imports_report_command(service, ["--help"]) == 0
    assert cli_module._unused_imports_report_command(service, ["--bad"]) == 2

    service.unused_imports_result = {"success": False}
    assert cli_module._unused_imports_command(service, []) == 1


@pytest.mark.unit
def test_duplicate_functions_command_wires_flags(cli_module):
    service = _StubService()

    code = cli_module._duplicate_functions_command(
        service,
        ["--include-all", "--min-overall", "0.8", "--min-name", "0.6"],
    )

    assert code == 0
    assert service.exclusion_calls == [(True, True)]
    assert service.duplicate_function_calls == [(0.8, 0.6)]


@pytest.mark.unit
def test_backup_subcommands_wire_to_service(cli_module):
    service = _StubService()

    assert cli_module._backup_command(service, ["inventory"]) == 0
    assert service.backup_inventory_calls == 1

    assert cli_module._backup_command(service, ["retention", "--apply", "--dry-run"]) == 0
    assert service.backup_retention_calls == [(False, True)]

    assert cli_module._backup_command(
        service, ["drill", "--backup-path", "x.zip", "--restore-config"]
    ) == 0
    assert service.backup_drill_calls == [("x.zip", True, True)]

    assert cli_module._backup_command(service, ["verify", "--skip-drill"]) == 0
    assert service.backup_verify_calls == [False]


@pytest.mark.unit
def test_list_commands_contains_expected_aliases(cli_module):
    names = [c.name for c in cli_module.list_commands()]
    assert "audit" in names
    assert "full-audit" in names
    assert "clean-up" in names
