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
    monkeypatch.setattr(version_sync_module, "_EXCLUDE_PATTERNS", [])
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


@pytest.mark.unit
def test_is_generated_file_normalizes_path_separators(monkeypatch):
    monkeypatch.setattr(version_sync_module, "GENERATED_AI_DOCS", ["ai_development_docs/sample_generated.md"])
    monkeypatch.setattr(version_sync_module, "GENERATED_DOCS", [])

    assert version_sync_module.is_generated_file("ai_development_docs/sample_generated.md") is True
    assert version_sync_module.is_generated_file(r"ai_development_docs\sample_generated.md") is True
    assert version_sync_module.is_generated_file("./ai_development_docs/sample_generated.md") is True


@pytest.mark.unit
def test_should_track_file_unknown_scope_returns_false():
    assert version_sync_module.should_track_file("docs/any.md", scope="not_a_real_scope") is False


@pytest.mark.unit
def test_should_track_file_scope_all_returns_true():
    assert version_sync_module.should_track_file("any/path/file.xyz", scope="all") is True


@pytest.mark.unit
def test_extract_version_info_fills_defaults():
    version, date_str = version_sync_module.extract_version_info("body without version keys")
    assert version == "1.0.0"
    assert date_str == version_sync_module.get_current_date()


@pytest.mark.unit
def test_get_file_modification_date_on_stat_failure(monkeypatch):
    def _raise(_path):
        raise OSError("no stat")

    monkeypatch.setattr(version_sync_module.os.path, "getmtime", _raise)
    out = version_sync_module.get_file_modification_date("/nonexistent/path.md")
    assert out == version_sync_module.get_current_date()
