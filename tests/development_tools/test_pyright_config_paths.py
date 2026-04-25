"""Policy: Pyright and Ruff config files exist and are readable (portability baseline).

When adding shared diagnostic keys, update **both** root `pyproject.toml` `[tool.pyright]` and
`development_tools/config/pyrightconfig.json`, then extend `test_pyright_owned_matches_root_diagnostic_and_exclude_keys`.

V4 §7.6 portability acceptance (incremental):
- Owned `development_tools/config/pyrightconfig.json` is valid JSON and suitable for `pyright --project` in dev-tools audits.
- Root Pyright settings live in `pyproject.toml` under `[tool.pyright]` (whole-repo / IDE baseline); policy tests parse TOML.
- Full diagnostic parity (error counts vs root) is deferred: add subprocess-based comparison only after explicit tolerance rules exist.
"""

from __future__ import annotations

import json
import os
import sys
import tomllib
from pathlib import Path

import pytest

project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


def _root_tool_pyright() -> dict:
    data = tomllib.loads((project_root / "pyproject.toml").read_text(encoding="utf-8"))
    sec = data.get("tool", {}).get("pyright")
    assert isinstance(sec, dict), "pyproject.toml must define [tool.pyright]"
    return sec


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
    assert data.get("venv") == ".venv"
    assert data.get("venvPath") == "../.."


@pytest.mark.unit
def test_pyright_owned_and_root_both_declare_type_checking_mode() -> None:
    """Both config stacks declare typeCheckingMode (baseline for future parity work)."""
    root = _root_tool_pyright()
    assert root.get("typeCheckingMode")
    owned = json.loads(
        (project_root / "development_tools" / "config" / "pyrightconfig.json").read_text(
            encoding="utf-8"
        )
    )
    assert owned.get("typeCheckingMode")


@pytest.mark.unit
def test_pyright_include_key_matches_between_root_and_owned() -> None:
    """If either config adds ``include``, keep both in sync (currently both omit it)."""
    root = _root_tool_pyright()
    owned = json.loads(
        (project_root / "development_tools" / "config" / "pyrightconfig.json").read_text(
            encoding="utf-8"
        )
    )
    assert root.get("include") == owned.get("include")


@pytest.mark.unit
def test_pyright_owned_matches_root_diagnostic_and_exclude_keys() -> None:
    """V5 §7.6: owned JSON aligns root `[tool.pyright]` for shared policy keys (venvPath differs by design)."""
    root = _root_tool_pyright()
    owned = json.loads(
        (project_root / "development_tools" / "config" / "pyrightconfig.json").read_text(
            encoding="utf-8"
        )
    )
    for key in (
        "typeCheckingMode",
        "pythonVersion",
        "reportReturnType",
        "reportArgumentType",
        "reportOptionalMemberAccess",
        "reportAttributeAccessIssue",
        "reportGeneralTypeIssues",
        "reportUnboundVariable",
        "reportUnsupportedDunderAll",
        "ignore",
        "exclude",
    ):
        assert owned.get(key) == root.get(key), f"pyrightconfig vs pyproject [tool.pyright] mismatch: {key}"
    assert owned.get("venv") == root.get("venv")
    assert owned.get("venvPath") == "../.."
    assert root.get("venvPath") == "."


@pytest.mark.unit
def test_root_pyright_in_pyproject_exists() -> None:
    """Root Pyright config is [tool.pyright] in pyproject.toml."""
    root = _root_tool_pyright()
    assert root.get("typeCheckingMode")
    assert root.get("venv") == ".venv"
    assert root.get("venvPath") == "."


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


@pytest.mark.unit
def test_root_and_owned_ruff_configs_share_core_policy_keys() -> None:
    """Portability follow-up: keep direct-workflow Ruff mirror aligned with owned dev-tools Ruff config."""
    root = tomllib.loads((project_root / ".ruff.toml").read_text(encoding="utf-8"))
    owned = tomllib.loads(
        (project_root / "development_tools" / "config" / "ruff.toml").read_text(
            encoding="utf-8"
        )
    )
    for key in ("line-length", "target-version", "exclude"):
        assert root.get(key) == owned.get(key), f"ruff mirror drift for key: {key}"
    assert root.get("lint", {}).get("select") == owned.get("lint", {}).get("select")
    assert root.get("lint", {}).get("ignore") == owned.get("lint", {}).get("ignore")


@pytest.mark.unit
def test_dev_tools_pyrightconfig_excludes_tests_data_and_temp() -> None:
    """Owned Pyright config must keep test fixtures and temp trees out of analysis scope."""
    path = project_root / "development_tools" / "config" / "pyrightconfig.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    ex = data.get("exclude", [])
    assert isinstance(ex, list)
    flat = " ".join(str(x) for x in ex)
    assert "tests/data" in flat
    assert "tests/temp" in flat or "tests\\temp" in flat


@pytest.mark.unit
def test_optional_pyright_error_delta_env_documented_in_e2e() -> None:
    """V5 §7.6: e2e test documents PYRIGHT_ERROR_COUNT_MAX_DELTA for optional parity enforcement."""
    src = (project_root / "tests" / "development_tools" / "test_pyright_config_paths.py").read_text(
        encoding="utf-8"
    )
    assert "PYRIGHT_ERROR_COUNT_MAX_DELTA" in src


@pytest.mark.unit
def test_pyright_diagnostic_parity_strategy_note() -> None:
    """V4 §7.6: full error-count parity between root and owned Pyright configs is deferred.

    Strategy: keep both configs until tolerance-based subprocess comparison is defined;
    policy tests require structural readiness (typeCheckingMode, exclude roots) only.
    """
    assert (project_root / "development_tools" / "config" / "pyrightconfig.json").is_file()
    assert (project_root / "pyproject.toml").is_file()
    assert _root_tool_pyright().get("typeCheckingMode")


@pytest.mark.unit
def test_pyright_owned_and_root_both_reference_tests_data_excludes() -> None:
    """Structural alignment: fixture/temp trees stay out of both analysis scopes."""
    owned = json.loads(
        (project_root / "development_tools" / "config" / "pyrightconfig.json").read_text(
            encoding="utf-8"
        )
    )
    ex = owned.get("exclude", [])
    flat = " ".join(str(x) for x in ex)
    assert "tests/data" in flat

    root_ex = _root_tool_pyright().get("exclude", [])
    assert isinstance(root_ex, list)
    root_flat = " ".join(str(x) for x in root_ex)
    assert "tests/data" in root_flat or "tests\\data" in root_flat


@pytest.mark.integration
@pytest.mark.e2e
def test_e2e_pyright_outputjson_parses_for_owned_and_root_projects() -> None:
    """Optional full-run smoke: both `--project` targets emit JSON with a summary block.

    Excluded from default runs (`-m "not e2e"`). Requires `python -m pyright` in PATH/venv.
    """
    import subprocess
    import sys

    check = subprocess.run(
        [sys.executable, "-m", "pyright", "--version"],
        capture_output=True,
        text=True,
        timeout=30,
    )
    if check.returncode != 0:
        pytest.skip("pyright CLI not available")

    def _run(project_rel: str) -> dict[str, object]:
        proc = subprocess.run(
            [
                sys.executable,
                "-m",
                "pyright",
                "--outputjson",
                "--project",
                str(project_root / project_rel),
            ],
            cwd=str(project_root),
            capture_output=True,
            text=True,
            timeout=600,
        )
        raw = (proc.stdout or "").strip()
        assert raw, f"pyright produced no stdout (stderr={proc.stderr!r})"
        payload = json.loads(raw)
        assert "summary" in payload
        return payload

    owned_payload = _run("development_tools/config/pyrightconfig.json")
    root_payload = _run("pyproject.toml")
    assert isinstance(owned_payload["summary"], dict)
    assert isinstance(root_payload["summary"], dict)

    # Optional numeric parity (V5 §7.6): set PYRIGHT_ERROR_COUNT_MAX_DELTA to enforce |delta errors| cap.
    max_delta = os.environ.get("PYRIGHT_ERROR_COUNT_MAX_DELTA")
    if max_delta is not None:
        oe = int(owned_payload["summary"].get("errorCount", 0))  # type: ignore[arg-type]
        re = int(root_payload["summary"].get("errorCount", 0))  # type: ignore[arg-type]
        assert abs(oe - re) <= int(max_delta), (
            f"Owned vs root Pyright errorCount delta {abs(oe - re)} exceeds PYRIGHT_ERROR_COUNT_MAX_DELTA={max_delta}"
        )
