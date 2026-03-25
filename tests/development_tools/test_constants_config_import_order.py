# TOOL_TIER: core

"""Regression: shared.constants must load JSON before freezing LOCAL_MODULE_PREFIXES.

A former import cycle (config.py eagerly built AUDIT_TIERS → shared → constants →
config before config.py finished) skipped load_external_config(), so coverage only
passed --cov core. See development_tools/config/config.py _get_default_audit_tiers.
"""

from __future__ import annotations

import sys

import pytest


def _clear_development_tools_modules() -> None:
    for key in list(sys.modules):
        if key == "development_tools" or key.startswith("development_tools."):
            del sys.modules[key]


@pytest.mark.unit
def test_import_development_tools_loads_local_module_prefixes_from_json():
    _clear_development_tools_modules()
    import development_tools  # noqa: F401

    from development_tools.shared import constants

    assert "communication" in constants.LOCAL_MODULE_PREFIXES
    assert "core" in constants.LOCAL_MODULE_PREFIXES
    assert constants.CORE_MODULES != ("core",)


@pytest.mark.unit
def test_import_package_config_get_constants_config_has_local_module_prefixes():
    _clear_development_tools_modules()
    import development_tools  # noqa: F401

    from development_tools.config import get_constants_config

    cfg = get_constants_config()
    assert isinstance(cfg.get("local_module_prefixes"), list)
    assert "communication" in cfg["local_module_prefixes"]
