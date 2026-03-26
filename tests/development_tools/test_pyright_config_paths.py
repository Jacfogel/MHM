"""Policy: Pyright and Ruff config files exist and are readable (portability baseline).

V4 §7.6 portability acceptance (incremental):
- Owned `development_tools/config/pyrightconfig.json` is valid JSON and suitable for `pyright --project` in dev-tools audits.
- Root `pyrightconfig.json` remains the whole-repo / IDE baseline (JSONC); policy tests only require presence of core keys in text.
- Full diagnostic parity (error counts vs root) is deferred: add subprocess-based comparison only after explicit tolerance rules exist.
"""

from __future__ import annotations

import json
import sys
import tomllib
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
def test_dev_tools_pyrightconfig_has_typing_and_exclude_roots() -> None:
    """Owned Pyright JSON must be self-contained enough for `pyright --project` audits."""
    path = project_root / "development_tools" / "config" / "pyrightconfig.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    assert "typeCheckingMode" in data
    assert isinstance(data.get("exclude"), list) and len(data["exclude"]) > 0


@pytest.mark.unit
def test_pyright_owned_and_root_both_declare_type_checking_mode() -> None:
    """Both config stacks declare typeCheckingMode (baseline for future parity work)."""
    root_text = (project_root / "pyrightconfig.json").read_text(encoding="utf-8")
    assert '"typeCheckingMode"' in root_text
    owned = json.loads(
        (project_root / "development_tools" / "config" / "pyrightconfig.json").read_text(
            encoding="utf-8"
        )
    )
    assert owned.get("typeCheckingMode")


@pytest.mark.unit
def test_root_pyrightconfig_exists() -> None:
    """Root config uses JSONC (// comments); require file and core keys only."""
    path = project_root / "pyrightconfig.json"
    assert path.is_file(), f"Missing {path}"
    text = path.read_text(encoding="utf-8")
    assert '"typeCheckingMode"' in text
    assert '"venv"' in text


@pytest.mark.unit
def test_dev_tools_ruff_toml_exists_and_parses() -> None:
    path = project_root / "development_tools" / "config" / "ruff.toml"
    assert path.is_file(), f"Missing {path}"
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    assert "line-length" in data or "exclude" in data


@pytest.mark.unit
def test_root_ruff_toml_exists_for_direct_ruff_workflows() -> None:
    """Compatibility mirror for `ruff check .` (see DEVELOPMENT_TOOLS_GUIDE §7.6)."""
    path = project_root / ".ruff.toml"
    assert path.is_file(), f"Missing {path}"
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    assert "line-length" in data or "exclude" in data
