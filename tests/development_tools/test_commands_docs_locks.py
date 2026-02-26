"""Tests for docs command lock handling in CommandsMixin."""

from pathlib import Path

import pytest

from tests.development_tools.conftest import load_development_tools_module


commands_module = load_development_tools_module("shared.service.commands")
CommandsMixin = commands_module.CommandsMixin


class _DummyService(CommandsMixin):
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
def test_run_docs_fails_fast_when_default_audit_lock_exists(tmp_path):
    """run_docs should return False and skip generation when lock files exist."""
    (tmp_path / ".audit_in_progress.lock").write_text("", encoding="utf-8")
    service = _DummyService(tmp_path)

    result = service.run_docs()

    assert result is False


@pytest.mark.unit
def test_run_docs_detects_configured_lock_paths(tmp_path, monkeypatch):
    """Configured lock-file paths should also block docs generation."""
    custom_lock = tmp_path / "development_tools" / ".custom_audit.lock"
    custom_lock.parent.mkdir(parents=True, exist_ok=True)
    custom_lock.write_text("", encoding="utf-8")

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

    service = _DummyService(tmp_path)

    result = service.run_docs()

    assert result is False
