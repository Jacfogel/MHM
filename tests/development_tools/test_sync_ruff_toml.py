"""Tests for development_tools.config.sync_ruff_toml."""

from pathlib import Path

import pytest

from tests.development_tools.conftest import load_development_tools_module


sync_module = load_development_tools_module("config.sync_ruff_toml")


@pytest.mark.unit
def test_sync_ruff_toml_writes_owned_config_and_root_compat(tmp_path):
    owned_path = sync_module.sync_ruff_toml(
        tmp_path,
        config_path="development_tools/config/ruff.toml",
        sync_root_compat=True,
    )

    assert owned_path == tmp_path / "development_tools" / "config" / "ruff.toml"
    assert owned_path.exists()
    assert (tmp_path / ".ruff.toml").exists()


@pytest.mark.unit
def test_sync_ruff_toml_no_root_compat(tmp_path):
    owned_path = sync_module.sync_ruff_toml(
        tmp_path,
        config_path="development_tools/config/ruff.toml",
        sync_root_compat=False,
    )

    assert owned_path.exists()
    assert not (tmp_path / ".ruff.toml").exists()


@pytest.mark.unit
def test_sync_ruff_toml_deterministic_content(tmp_path):
    owned_path = sync_module.sync_ruff_toml(
        tmp_path,
        config_path=Path("development_tools/config/ruff.toml"),
        sync_root_compat=False,
    )
    first = owned_path.read_text(encoding="utf-8")

    sync_module.sync_ruff_toml(
        tmp_path,
        config_path=Path("development_tools/config/ruff.toml"),
        sync_root_compat=False,
    )
    second = owned_path.read_text(encoding="utf-8")

    assert first == second
