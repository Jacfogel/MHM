"""Tests for development_tools package __init__ public API."""

import sys
from pathlib import Path

import pytest

from tests.development_tools.conftest import load_development_tools_module, project_root


def _get_real_development_tools_module():
    """Ensure the project-root development_tools package is loaded and return it (not tests.development_tools)."""
    # If "development_tools" is already the tests subpackage, remove it so the loader loads the real one
    current = sys.modules.get("development_tools")
    if current is not None and getattr(current, "__file__", None):
        if Path(current.__file__).resolve().parent == (project_root / "tests" / "development_tools"):
            del sys.modules["development_tools"]
    load_development_tools_module("shared.result_format")
    return sys.modules["development_tools"]


@pytest.mark.unit
def test_package_exports_shared_utilities():
    """development_tools package should export shared utilities (__init__.py runs when loader loads package)."""
    dt = _get_real_development_tools_module()

    assert hasattr(dt, "should_exclude_file"), "should_exclude_file should be exported"
    assert hasattr(dt, "get_exclusions"), "get_exclusions should be exported"
    assert hasattr(dt, "is_local_module"), "is_local_module should be exported"
    assert hasattr(dt, "is_standard_library_module"), "is_standard_library_module should be exported"
    assert hasattr(dt, "config"), "config subpackage should be available"


@pytest.mark.unit
def test_package_all_list_matches_exports():
    """__all__ should list the documented public API."""
    dt = _get_real_development_tools_module()

    assert hasattr(dt, "__all__"), "package should define __all__"
    assert "config" in dt.__all__
    assert "should_exclude_file" in dt.__all__
    assert "get_exclusions" in dt.__all__
    assert "is_local_module" in dt.__all__
    assert "is_standard_library_module" in dt.__all__
