"""Cache/helper coverage for shared/service/tool_wrappers.py."""

from __future__ import annotations

import time
from types import SimpleNamespace
from pathlib import Path
from unittest.mock import patch

import pytest

from tests.development_tools.conftest import load_development_tools_module

service_module = load_development_tools_module("shared.service")
tool_wrappers_module = load_development_tools_module("shared.service.tool_wrappers")
AIToolsService = service_module.AIToolsService


@pytest.mark.unit
def test_compute_source_signature_changes_when_source_changes(tmp_path: Path):
    """Signature changes when file content changes (uses content hash, not just mtime)."""
    service = AIToolsService(project_root=str(tmp_path))
    # Use development_tools/static_checks path to mirror production scanning and avoid
    # exclusion patterns; isolated dir ensures only our file affects the signature.
    src_dir = tmp_path / "development_tools" / "static_checks"
    src_dir.mkdir(parents=True)
    src_file = src_dir / "code.py"
    src_file.write_text("value = 1\n", encoding="utf-8")

    # tmp_path often lives under pytest temp dirs; those paths are excluded from scans.
    # Disable exclusions so the isolated file participates in the signature.
    with patch(
        "development_tools.shared.standard_exclusions.should_exclude_file",
        return_value=False,
    ):
        sig_before = service._compute_source_signature()
        src_file.write_text("value = 2\n", encoding="utf-8")
        # Force visibility: read back to ensure write is committed (Windows fs sync)
        assert src_file.read_text(encoding="utf-8") == "value = 2\n"
        time.sleep(0.05)
        sig_after = service._compute_source_signature()

    assert isinstance(sig_before, str) and sig_before
    assert isinstance(sig_after, str) and sig_after
    assert sig_before != sig_after, (
        "Signature should change when file content changes; "
        "possible filesystem/mtime sync issue"
    )


@pytest.mark.unit
def test_compute_source_signature_changes_when_pyproject_toml_changes(tmp_path: Path):
    """Static-check cache must invalidate when only pyproject.toml changes (e.g. [tool.pyright])."""
    (tmp_path / "development_tools" / "static_checks").mkdir(parents=True)
    src_file = tmp_path / "development_tools" / "static_checks" / "code.py"
    src_file.write_text("x = 1\n", encoding="utf-8")
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text('[project]\nname = "t"\nversion = "0"\n', encoding="utf-8")

    with patch(
        "development_tools.shared.standard_exclusions.should_exclude_file",
        return_value=False,
    ):
        service = AIToolsService(project_root=str(tmp_path))
        sig_before = service._compute_source_signature()
        pyproject.write_text(
            '[project]\nname = "t"\nversion = "0"\n[tool.pyright]\nexclude = ["archive"]\n',
            encoding="utf-8",
        )
        sig_after = service._compute_source_signature()

    assert isinstance(sig_before, str) and sig_before
    assert isinstance(sig_after, str) and sig_after
    assert sig_before != sig_after


@pytest.mark.unit
def test_compute_source_signature_changes_when_development_tools_config_changes(
    tmp_path: Path,
):
    """Static-check cache must invalidate when only development_tools_config.json changes."""
    (tmp_path / "development_tools" / "static_checks").mkdir(parents=True)
    (tmp_path / "development_tools" / "config").mkdir(parents=True)
    src_file = tmp_path / "development_tools" / "static_checks" / "code.py"
    src_file.write_text("x = 1\n", encoding="utf-8")
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text('[project]\nname = "t"\nversion = "0"\n', encoding="utf-8")
    dev_cfg = tmp_path / "development_tools" / "config" / "development_tools_config.json"
    dev_cfg.write_text('{"version": 1, "x": 1}\n', encoding="utf-8")

    with patch(
        "development_tools.shared.standard_exclusions.should_exclude_file",
        return_value=False,
    ):
        service = AIToolsService(project_root=str(tmp_path))
        sig_before = service._compute_source_signature()
        dev_cfg.write_text('{"version": 1, "x": 2}\n', encoding="utf-8")
        sig_after = service._compute_source_signature()

    assert isinstance(sig_before, str) and sig_before
    assert isinstance(sig_after, str) and sig_after
    assert sig_before != sig_after


@pytest.mark.unit
def test_compute_source_signature_changes_when_root_ruff_toml_changes(tmp_path: Path):
    """Optional root .ruff.toml participates in static-check invalidation when present."""
    (tmp_path / "development_tools" / "static_checks").mkdir(parents=True)
    (tmp_path / "development_tools" / "config").mkdir(parents=True)
    src_file = tmp_path / "development_tools" / "static_checks" / "code.py"
    src_file.write_text("x = 1\n", encoding="utf-8")
    (tmp_path / "pyproject.toml").write_text("[project]\nname = \"t\"\n", encoding="utf-8")
    (tmp_path / "development_tools" / "config" / "development_tools_config.json").write_text(
        "{}\n", encoding="utf-8"
    )
    (tmp_path / "development_tools" / "config" / "pyrightconfig.json").write_text(
        "{}\n", encoding="utf-8"
    )
    (tmp_path / "development_tools" / "config" / "ruff.toml").write_text(
        "[lint]\n", encoding="utf-8"
    )
    root_ruff = tmp_path / ".ruff.toml"
    root_ruff.write_text("# a\n", encoding="utf-8")

    with patch(
        "development_tools.shared.standard_exclusions.should_exclude_file",
        return_value=False,
    ):
        service = AIToolsService(project_root=str(tmp_path))
        sig_before = service._compute_source_signature()
        root_ruff.write_text("# b\n", encoding="utf-8")
        sig_after = service._compute_source_signature()

    assert isinstance(sig_before, str) and sig_before
    assert isinstance(sig_after, str) and sig_after
    assert sig_before != sig_after


@pytest.mark.unit
def test_static_check_cache_metadata_from_shard_run_partial():
    meta = tool_wrappers_module._static_check_cache_metadata_from_analyzer_details(
        {
            "shard_run": {
                "mode": "sharded",
                "fragment_cache_hits": 1,
                "fragment_cache_misses": 2,
                "subprocesses": 2,
            }
        }
    )
    assert meta["cache_mode"] == "partial_cache"
    assert meta["fragment_hits"] == 1
    assert meta["fragment_misses"] == 2


@pytest.mark.unit
def test_static_check_cache_metadata_from_shard_run_all_hits():
    meta = tool_wrappers_module._static_check_cache_metadata_from_analyzer_details(
        {
            "shard_run": {
                "mode": "sharded",
                "fragment_cache_hits": 3,
                "fragment_cache_misses": 0,
                "subprocesses": 0,
            }
        }
    )
    assert meta["cache_mode"] == "cache_hit"


@pytest.mark.unit
def test_static_check_cache_metadata_includes_parity_note():
    meta = tool_wrappers_module._static_check_cache_metadata_from_analyzer_details(
        {"shard_run": {"parity_note": "subset", "fragment_cache_hits": 0, "fragment_cache_misses": 1}}
    )
    assert meta["parity_note"] == "subset"


@pytest.mark.unit
def test_run_analyze_unused_imports_parses_multiline_json_output(
    temp_project_copy: Path, monkeypatch: pytest.MonkeyPatch
):
    service = AIToolsService(project_root=str(temp_project_copy))
    stdout = """prelude log line
{
  "summary": {"total_issues": 2, "files_affected": 1},
  "details": {"stats": {"cache_hits": 1, "cache_misses": 1, "files_scanned": 2}}
}
trailing log line
"""
    monkeypatch.setattr(
        tool_wrappers_module.subprocess,
        "run",
        lambda *args, **kwargs: SimpleNamespace(
            returncode=1,
            stdout=stdout,
            stderr="non-zero due to findings",
        ),
        raising=True,
    )
    monkeypatch.setattr(
        tool_wrappers_module, "save_tool_result", lambda *_args, **_kwargs: None
    )

    result = service.run_analyze_unused_imports()

    assert result["success"] is True
    assert result["issues_found"] is True
    assert result["data"]["summary"]["total_issues"] == 2
    assert service._tool_cache_metadata["analyze_unused_imports"]["cache_mode"] == "partial_cache"
