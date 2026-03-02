"""Tests for docs command lock handling in CommandsMixin."""

from pathlib import Path

import pytest

from tests.development_tools.conftest import load_development_tools_module


commands_module = load_development_tools_module("shared.service.commands")
lock_state_module = load_development_tools_module("shared.lock_state")
CommandsMixin = commands_module.CommandsMixin


class _BlockingService(CommandsMixin):
    """Minimal service surface for testing docs lock behavior."""

    def __init__(self, project_root: Path):
        self.project_root = project_root

    def run_script(self, *_args, **_kwargs):
        raise AssertionError("run_script should not be called when locks are present")

    def generate_directory_trees(self):
        raise AssertionError(
            "generate_directory_trees should not be called when locks are present"
        )

    def _run_doc_sync_check(self, *_args):
        raise AssertionError(
            "_run_doc_sync_check should not be called when locks are present"
        )


@pytest.mark.unit
def test_run_docs_fails_fast_when_active_default_audit_lock_exists(tmp_path):
    """run_docs should return False and skip generation for active lock files."""
    lock_state_module.write_lock_metadata(
        tmp_path / ".audit_in_progress.lock", lock_type="audit"
    )
    service = _BlockingService(tmp_path)

    result = service.run_docs()

    assert result is False


@pytest.mark.unit
def test_run_docs_detects_active_configured_lock_paths(tmp_path, monkeypatch):
    """Configured active lock-file paths should also block docs generation."""
    custom_lock = tmp_path / "development_tools" / ".custom_audit.lock"
    lock_state_module.write_lock_metadata(custom_lock, lock_type="audit")

    monkeypatch.setattr(
        commands_module,
        "config",
        type(
            "_Cfg",
            (),
            {
                "get_external_value": staticmethod(
                    lambda key, default=None: (
                        "development_tools/.custom_audit.lock"
                        if key == "paths.audit_lock_file"
                        else default
                    )
                )
            },
        )(),
        raising=False,
    )

    service = _BlockingService(tmp_path)

    result = service.run_docs()

    assert result is False


class _PassingService(CommandsMixin):
    """Service that allows docs workflow to complete."""

    def __init__(self, project_root: Path):
        self.project_root = project_root

    def run_script(self, *_args, **_kwargs):
        return {"success": True, "output": "", "error": ""}

    def generate_directory_trees(self):
        return None

    def _run_doc_sync_check(self, *_args):
        return True


@pytest.mark.unit
def test_run_docs_proceeds_when_stale_or_legacy_lock_exists(tmp_path):
    """Stale/malformed lock files should be auto-cleaned and not block docs."""
    stale_payload = {
        "version": 1,
        "lock_type": "audit",
        "pid": 999999,
        "ppid": 1,
        "created_at": 1.0,
        "stale_after_seconds": 5400,
        "host": "test-host",
        "command": "python -m pytest",
    }
    stale_lock = tmp_path / ".audit_in_progress.lock"
    stale_lock.write_text(str(stale_payload), encoding="utf-8")  # malformed JSON legacy payload
    service = _PassingService(tmp_path)

    result = service.run_docs()

    assert result is True
    assert not stale_lock.exists()
