"""Tests for development_tools.shared.host_hooks host adapters."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from development_tools.shared.host_hooks import (
    HostBackupLoadError,
    get_forbidden_host_import_prefixes,
    load_host_backup_manager,
)


@pytest.mark.unit
def test_load_host_backup_manager_returns_none_when_unconfigured(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(
        "development_tools.config.get_host_config",
        lambda: {"backup_manager_module": "", "backup_manager_attr": "backup_manager"},
    )
    assert load_host_backup_manager() is None


@pytest.mark.unit
def test_load_host_backup_manager_raises_when_module_missing(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(
        "development_tools.config.get_host_config",
        lambda: {
            "backup_manager_module": "no_such_host_backup_module_xyz",
            "backup_manager_attr": "backup_manager",
        },
    )
    with pytest.raises(HostBackupLoadError, match="could not be imported"):
        load_host_backup_manager()


@pytest.mark.unit
def test_load_host_backup_manager_loads_module_inside_project_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    pkg = tmp_path / "mhmhostbackupok"
    pkg.mkdir()
    (pkg / "__init__.py").write_text(
        "class BM:\n"
        "    def list_backups(self):\n"
        "        return [{'id': 'ok'}]\n"
        "    def validate_backup(self, backup_path):\n"
        "        return True, []\n"
        "    def restore_backup_to_path(self, backup_path, destination, restore_users=True, restore_config=False):\n"
        "        return True\n"
        "backup_manager = BM()\n",
        encoding="utf-8",
    )
    monkeypatch.syspath_prepend(str(tmp_path))
    sys.modules.pop("mhmhostbackupok", None)
    monkeypatch.setattr(
        "development_tools.config.get_host_config",
        lambda: {
            "backup_manager_module": "mhmhostbackupok",
            "backup_manager_attr": "backup_manager",
        },
    )
    manager = load_host_backup_manager(project_root=tmp_path)
    assert manager is not None
    assert manager.list_backups() == [{"id": "ok"}]


@pytest.mark.unit
def test_load_host_backup_manager_rejects_module_outside_project_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    outside = tmp_path / "outside"
    project = tmp_path / "project"
    outside.mkdir()
    project.mkdir()
    pkg = outside / "mhmhostbackupout"
    pkg.mkdir()
    (pkg / "__init__.py").write_text(
        "backup_manager = type('BM', (), {})()\n",
        encoding="utf-8",
    )
    monkeypatch.syspath_prepend(str(outside))
    sys.modules.pop("mhmhostbackupout", None)
    monkeypatch.setattr(
        "development_tools.config.get_host_config",
        lambda: {
            "backup_manager_module": "mhmhostbackupout",
            "backup_manager_attr": "backup_manager",
        },
    )
    with pytest.raises(HostBackupLoadError, match="not inside project_root"):
        load_host_backup_manager(project_root=project)


@pytest.mark.unit
def test_forbidden_host_import_prefixes_omit_development_tools():
    from development_tools import config

    config.load_external_config()
    prefixes = get_forbidden_host_import_prefixes()
    assert "development_tools" not in prefixes
    assert all(isinstance(p, str) and p for p in prefixes)
