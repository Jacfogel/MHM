"""Tests for file discovery behavior in docs/fix_version_sync.py."""

from pathlib import Path

import pytest

from tests.development_tools.conftest import load_development_tools_module


version_sync_module = load_development_tools_module("docs.fix_version_sync")


@pytest.mark.unit
def test_find_trackable_files_skips_standard_excluded_paths(monkeypatch, tmp_path: Path):
    """find_trackable_files should skip shared excluded directories/files."""
    included = tmp_path / "docs" / "keep.md"
    excluded_script = tmp_path / "scripts" / "skip.md"
    excluded_cache = tmp_path / ".ruff_cache" / "skip.md"
    excluded_tests_data = tmp_path / "tests" / "data" / "skip.md"

    for path in [included, excluded_script, excluded_cache, excluded_tests_data]:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("content", encoding="utf-8")

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(version_sync_module, "EXCLUDE_PATTERNS", [])
    monkeypatch.setattr(
        version_sync_module,
        "should_track_file",
        lambda file_path, scope: str(file_path).endswith(".md"),
    )

    found = {str(Path(p)).replace("\\", "/").lstrip("./") for p in version_sync_module.find_trackable_files("docs")}

    assert "docs/keep.md" in found
    assert "scripts/skip.md" not in found
    assert ".ruff_cache/skip.md" not in found
    assert "tests/data/skip.md" not in found
