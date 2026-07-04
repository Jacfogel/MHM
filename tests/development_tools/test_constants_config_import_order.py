# TOOL_TIER: core

"""Regression: shared.constants must load JSON before freezing LOCAL_MODULE_PREFIXES.

A former import cycle (config.py eagerly built AUDIT_TIERS → shared → constants →
config before config.py finished) skipped load_external_config(), so coverage only
passed --cov core. See development_tools/config/config.py _get_default_audit_tiers.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_LIVE_CONFIG = _PROJECT_ROOT / "development_tools" / "config" / "development_tools_config.json"
_EXAMPLE_CONFIG = (
    _PROJECT_ROOT / "development_tools" / "config" / "development_tools_config.json.example"
)


def _config_path_for_import_test() -> Path:
    """Use live config when present; otherwise the committed example (CI)."""
    if _LIVE_CONFIG.exists():
        return _LIVE_CONFIG
    if _EXAMPLE_CONFIG.exists():
        return _EXAMPLE_CONFIG
    pytest.skip("No development_tools config or example file available")


def _load_config_then_import_development_tools() -> None:
    _clear_development_tools_modules()
    config_path = _config_path_for_import_test()
    import development_tools.config.config as cfg_mod

    assert cfg_mod.load_external_config(str(config_path)) is True
    import development_tools  # noqa: F401


def _clear_development_tools_modules() -> None:
    for key in list(sys.modules):
        if key == "development_tools" or key.startswith("development_tools."):
            del sys.modules[key]


@pytest.mark.unit
def test_import_development_tools_loads_local_module_prefixes_from_json():
    _load_config_then_import_development_tools()

    from development_tools.shared import constants

    assert "communication" in constants.LOCAL_MODULE_PREFIXES
    assert "core" in constants.LOCAL_MODULE_PREFIXES
    assert constants.CORE_MODULES != ("core",)


@pytest.mark.unit
def test_import_package_config_get_constants_config_has_local_module_prefixes():
    _load_config_then_import_development_tools()

    from development_tools.config import get_constants_config

    cfg = get_constants_config()
    assert isinstance(cfg.get("local_module_prefixes"), list)
    assert "communication" in cfg["local_module_prefixes"]
    assert isinstance(cfg.get("default_docs"), list)
    assert len(cfg["default_docs"]) >= 10
    assert "README.md" in cfg["default_docs"]
    assert "ai_development_docs/AI_LEGACY_COMPATIBILITY_GUIDE.md" in cfg["default_docs"]


@pytest.mark.unit
def test_get_analyze_ai_work_inherits_ai_validation_thresholds():
    _clear_development_tools_modules()
    import development_tools  # noqa: F401

    from development_tools.config import config as cfg_mod

    cfg_mod.load_external_config()
    w = cfg_mod.get_analyze_ai_work_config()
    v = cfg_mod.get_ai_validation_config()
    for key in (
        "completeness_threshold",
        "accuracy_threshold",
        "consistency_threshold",
        "actionable_threshold",
    ):
        assert w[key] == v[key]


@pytest.mark.unit
def test_get_validation_complexity_matches_analyze_functions():
    _clear_development_tools_modules()
    import development_tools  # noqa: F401

    from development_tools.config import config as cfg_mod

    cfg_mod.load_external_config()
    val = cfg_mod.get_validation_config()
    af = cfg_mod.get_analyze_functions_config()
    assert val["moderate_complexity_warning"] == af["moderate_complexity_threshold"]
    assert val["high_complexity_warning"] == af["high_complexity_threshold"]
    assert val["critical_complexity_warning"] == af["critical_complexity_threshold"]


@pytest.mark.unit
def test_get_coverage_tool_config_test_directory_from_paths():
    _clear_development_tools_modules()
    import development_tools  # noqa: F401

    from development_tools.config import config as cfg_mod

    cfg_mod.load_external_config()
    cov = cfg_mod.get_coverage_tool_config()
    assert cov.get("test_directory") == "tests/"
