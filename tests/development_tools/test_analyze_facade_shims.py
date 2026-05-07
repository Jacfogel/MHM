"""Tests for analyze_facade_shims advisory tool."""

from pathlib import Path
from unittest.mock import patch

import pytest

from tests.development_tools.conftest import load_development_tools_module


@pytest.fixture
def facade_module():
    return load_development_tools_module("functions.analyze_facade_shims")


def _write_inventory(root: Path) -> None:
    inventory = root / "development_tools" / "config" / "jsons" / "DEPRECATION_INVENTORY.json"
    inventory.parent.mkdir(parents=True, exist_ok=True)
    inventory.write_text(
        """
{
  "active_or_candidate_inventory": [
    {
      "id": "legacy_bridge",
      "status": "active_bridge",
      "search_terms": ["LegacyBridge"]
    }
  ],
  "removed_inventory": []
}
        """.strip(),
        encoding="utf-8",
    )


def _analyze(facade_module, root: Path):
    with (
        patch.object(facade_module.config, "get_project_root", return_value=str(root)),
        patch.object(facade_module.config, "get_scan_directories", return_value=["core"]),
        patch.object(
            facade_module.config,
            "get_external_value",
            return_value={
                "deprecation_inventory_file": "development_tools/config/jsons/DEPRECATION_INVENTORY.json"
            },
        ),
    ):
        return facade_module.analyze_project()


def _analyze_low_signal(facade_module, root: Path):
    with (
        patch.object(facade_module.config, "get_project_root", return_value=str(root)),
        patch.object(facade_module.config, "get_scan_directories", return_value=["core"]),
        patch.object(
            facade_module.config,
            "get_external_value",
            return_value={
                "deprecation_inventory_file": "development_tools/config/jsons/DEPRECATION_INVENTORY.json"
            },
        ),
    ):
        return facade_module.analyze_project(include_low_signal=True)


@pytest.mark.unit
def test_detects_import_re_export_alias(facade_module, tmp_path):
    _write_inventory(tmp_path)
    core = tmp_path / "core"
    core.mkdir()
    (core / "bridge.py").write_text(
        "from core.current import CurrentService as LegacyBridge\n",
        encoding="utf-8",
    )

    result = _analyze(facade_module, tmp_path)

    findings = result["details"]["findings"]
    assert result["summary"]["total_issues"] == 1
    assert findings[0]["kind"] == "re_export_alias"
    assert findings[0]["inventory_id"] == "legacy_bridge"


@pytest.mark.unit
def test_detects_thin_delegating_wrapper(facade_module, tmp_path):
    _write_inventory(tmp_path)
    core = tmp_path / "core"
    core.mkdir()
    (core / "facade.py").write_text(
        "def task_facade(user_id):\n    return current_task_service(user_id)\n",
        encoding="utf-8",
    )

    result = _analyze(facade_module, tmp_path)

    finding = result["details"]["findings"][0]
    assert finding["kind"] == "thin_wrapper"
    assert finding["target"] == "current_task_service"
    assert "thin_delegating_wrapper" in finding["signals"]


@pytest.mark.unit
def test_filters_plain_thin_delegating_wrapper_by_default(facade_module, tmp_path):
    _write_inventory(tmp_path)
    core = tmp_path / "core"
    core.mkdir()
    (core / "helpers.py").write_text(
        "def get_current_user(user_id):\n    return user_repository.get(user_id)\n",
        encoding="utf-8",
    )

    result = _analyze(facade_module, tmp_path)

    assert result["summary"]["total_issues"] == 0
    assert result["details"]["low_signal_candidates_filtered"] == 1


@pytest.mark.unit
def test_include_low_signal_restores_plain_thin_wrapper(facade_module, tmp_path):
    _write_inventory(tmp_path)
    core = tmp_path / "core"
    core.mkdir()
    (core / "helpers.py").write_text(
        "def get_current_user(user_id):\n    return user_repository.get(user_id)\n",
        encoding="utf-8",
    )

    result = _analyze_low_signal(facade_module, tmp_path)

    finding = result["details"]["findings"][0]
    assert result["summary"]["total_issues"] == 1
    assert finding["symbol"] == "get_current_user"
    assert finding["signals"] == ["thin_delegating_wrapper"]


@pytest.mark.unit
def test_respects_ignore_marker(facade_module, tmp_path):
    _write_inventory(tmp_path)
    core = tmp_path / "core"
    core.mkdir()
    (core / "facade.py").write_text(
        "# devtools: ignore[facade-shims]: documented bridge\n"
        "def task_facade(user_id):\n"
        "    return current_task_service(user_id)\n",
        encoding="utf-8",
    )

    result = _analyze(facade_module, tmp_path)

    assert result["summary"]["total_issues"] == 0


@pytest.mark.unit
def test_respects_standard_exclusions(facade_module, tmp_path, monkeypatch):
    _write_inventory(tmp_path)
    core = tmp_path / "core"
    core.mkdir()
    (core / "facade.py").write_text(
        "def task_facade(user_id):\n    return current_task_service(user_id)\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(facade_module, "should_exclude_file", lambda *_args: True)

    result = _analyze(facade_module, tmp_path)

    assert result["summary"]["total_issues"] == 0


@pytest.mark.unit
def test_main_json_output(facade_module, capsys):
    with (
        patch.object(
            facade_module,
            "analyze_project",
            return_value={"summary": {"total_issues": 0, "files_affected": 0}, "details": {"findings": []}},
        ),
        patch("sys.argv", ["analyze_facade_shims.py", "--json"]),
    ):
        assert facade_module.main() == 0

    assert '"findings": []' in capsys.readouterr().out
