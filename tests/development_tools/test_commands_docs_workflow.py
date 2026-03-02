"""Workflow-oriented tests for CommandsMixin docs and lock helpers."""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.development_tools.conftest import load_development_tools_module

service_module = load_development_tools_module("shared.service")
lock_state_module = load_development_tools_module("shared.lock_state")
AIToolsService = service_module.AIToolsService


@pytest.mark.unit
def test_run_docs_success_executes_all_steps(
    temp_project_copy: Path, monkeypatch: pytest.MonkeyPatch
):
    service = AIToolsService(project_root=str(temp_project_copy))
    calls: list[str] = []

    def _run_script(name: str, *_args, **_kwargs):
        calls.append(name)
        return {"success": True, "output": "", "error": "", "returncode": 0}

    monkeypatch.setattr(service, "run_script", _run_script)
    monkeypatch.setattr(
        service,
        "generate_directory_trees",
        lambda: calls.append("generate_directory_trees"),
    )
    monkeypatch.setattr(
        service, "_run_doc_sync_check", lambda: calls.append("_run_doc_sync_check") or True
    )

    assert service.run_docs() is True
    assert calls == [
        "generate_function_registry",
        "generate_module_dependencies",
        "generate_directory_trees",
        "_run_doc_sync_check",
    ]


@pytest.mark.unit
def test_run_docs_returns_false_when_any_substep_fails(
    temp_project_copy: Path, monkeypatch: pytest.MonkeyPatch
):
    service = AIToolsService(project_root=str(temp_project_copy))

    def _run_script(name: str, *_args, **_kwargs):
        if name == "generate_module_dependencies":
            return {"success": False, "output": "", "error": "failed", "returncode": 1}
        return {"success": True, "output": "", "error": "", "returncode": 0}

    monkeypatch.setattr(service, "run_script", _run_script)
    monkeypatch.setattr(service, "generate_directory_trees", lambda: None)
    monkeypatch.setattr(service, "_run_doc_sync_check", lambda: False)

    assert service.run_docs() is False


@pytest.mark.unit
def test_get_existing_audit_related_locks_returns_only_present(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    service = AIToolsService(project_root=str(tmp_path))
    lock_a = tmp_path / ".audit_in_progress.lock"
    lock_b = tmp_path / ".coverage_in_progress.lock"
    lock_c = tmp_path / ".coverage_dev_tools_in_progress.lock"
    lock_state_module.write_lock_metadata(lock_a, lock_type="audit")
    lock_state_module.write_lock_metadata(lock_c, lock_type="coverage_dev_tools")

    locks = service._get_existing_audit_related_locks()
    lock_set = {str(p) for p in locks}

    assert str(lock_a) in lock_set
    assert str(lock_c) in lock_set
    assert str(lock_b) not in lock_set
