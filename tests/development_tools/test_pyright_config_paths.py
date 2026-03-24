"""Policy: Pyright config files exist and parse as JSON (portability baseline)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


@pytest.mark.unit
def test_dev_tools_pyrightconfig_exists_and_is_json() -> None:
    path = project_root / "development_tools" / "config" / "pyrightconfig.json"
    assert path.is_file(), f"Missing {path}"
    data = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(data, dict)


@pytest.mark.unit
def test_root_pyrightconfig_exists() -> None:
    """Root config uses JSONC (// comments); require file and core keys only."""
    path = project_root / "pyrightconfig.json"
    assert path.is_file(), f"Missing {path}"
    text = path.read_text(encoding="utf-8")
    assert '"typeCheckingMode"' in text
    assert '"venv"' in text
