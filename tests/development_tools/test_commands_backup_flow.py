"""Tests for backup inventory / retention command paths on CommandsMixin."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from tests.development_tools.conftest import load_development_tools_module
from tests.development_tools.test_backup_inventory import _build_policy

policy_models_module = load_development_tools_module("shared.backup_policy_models")
ArtifactRule = policy_models_module.ArtifactRule

service_module = load_development_tools_module("shared.service")
commands_module = sys.modules["development_tools.shared.service.commands"]
AIToolsService = service_module.AIToolsService


@pytest.mark.unit
def test_run_backup_inventory_success_writes_json(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    reports_dir = tmp_path / "development_tools" / "reports"
    reports_dir.mkdir(parents=True)
    (reports_dir / "artifact.json").write_text("{}", encoding="utf-8")

    policy = _build_policy(
        [
            ArtifactRule(
                name="reports",
                paths=["development_tools/reports/*.json"],
                category="B",
            ),
        ]
    )
    monkeypatch.setattr(commands_module, "load_backup_policy", lambda: policy)

    service = AIToolsService(project_root=str(tmp_path))
    result = service.run_backup_inventory()

    assert result["success"] is True
    data = result.get("data")
    assert isinstance(data, dict)
    assert data.get("inventory") is not None
    json_path = Path(result["report_paths"]["json"])
    assert json_path.exists()
    assert json_path.name == "backup_inventory.json"


@pytest.mark.unit
def test_run_backup_inventory_failure_returns_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    policy = _build_policy([])
    monkeypatch.setattr(commands_module, "load_backup_policy", lambda: policy)

    def _boom(*_a, **_k):
        raise RuntimeError("inventory boom")

    monkeypatch.setattr(commands_module, "build_backup_inventory", _boom)

    service = AIToolsService(project_root=str(tmp_path))
    result = service.run_backup_inventory()

    assert result["success"] is False
    assert "inventory boom" in str(result.get("error", ""))


@pytest.mark.unit
def test_run_backup_retention_dry_run_writes_report(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    policy = _build_policy([])
    monkeypatch.setattr(commands_module, "load_backup_policy", lambda: policy)
    fake_plan = {"categories": ["B"], "dummy": True}

    monkeypatch.setattr(
        commands_module,
        "build_retention_plan",
        lambda *_a, **_k: fake_plan,
    )
    captured: dict[str, bool] = {}

    def _apply(plan, dry_run=True):
        captured["dry_run"] = dry_run
        return {"applied": not dry_run}

    monkeypatch.setattr(commands_module, "apply_retention_plan", _apply)

    service = AIToolsService(project_root=str(tmp_path))
    result = service.run_backup_retention(dry_run=True, apply=False)

    assert result["success"] is True
    assert captured.get("dry_run") is True
    payload = result.get("data")
    assert isinstance(payload, dict)
    assert payload.get("plan") == fake_plan
    json_path = Path(result["report_paths"]["json"])
    assert json_path.exists()


@pytest.mark.unit
def test_run_backup_retention_apply_executes_when_not_dry_run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    policy = _build_policy([])
    monkeypatch.setattr(commands_module, "load_backup_policy", lambda: policy)
    monkeypatch.setattr(
        commands_module,
        "build_retention_plan",
        lambda *_a, **_k: {"plan": True},
    )
    captured: dict[str, bool] = {}

    def _apply(_plan, dry_run=True):
        captured["dry_run"] = dry_run
        return {"ok": True}

    monkeypatch.setattr(commands_module, "apply_retention_plan", _apply)

    service = AIToolsService(project_root=str(tmp_path))
    result = service.run_backup_retention(dry_run=False, apply=True)

    assert result["success"] is True
    assert captured.get("dry_run") is False
