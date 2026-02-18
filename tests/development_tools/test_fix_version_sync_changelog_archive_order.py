"""Tests for changelog archive ordering during trim operations."""

from pathlib import Path

import pytest

from tests.development_tools.conftest import load_development_tools_module

version_sync_module = load_development_tools_module("docs.fix_version_sync")


@pytest.mark.unit
def test_trim_changelog_prepends_new_entries_to_archive_top(
    temp_project_copy, monkeypatch
):
    """Newly trimmed entries should be prepended before existing archive entries."""
    monkeypatch.chdir(temp_project_copy)

    ai_docs = Path("ai_development_docs")
    archive_dir = Path("archive")
    ai_docs.mkdir(parents=True, exist_ok=True)
    archive_dir.mkdir(parents=True, exist_ok=True)

    changelog = ai_docs / "AI_CHANGELOG.md"
    changelog.write_text(
        "\n".join(
            [
                "# AI Changelog",
                "",
                "## Recent Changes (Most Recent First)",
                "",
                "### 2026-02-18 - Keep this recent entry",
                "- kept",
                "",
                "### 2026-01-01 - Move this to archive",
                "- archived",
                "",
            ]
        ),
        encoding="utf-8",
    )

    archive = archive_dir / "AI_CHANGELOG_ARCHIVE.md"
    archive.write_text(
        "\n".join(
            [
                "# AI Changelog Archive",
                "",
                "## Archived Entries",
                "",
                "### 2025-12-01 - Existing archived entry",
                "- existing",
                "",
            ]
        ),
        encoding="utf-8",
    )

    result = version_sync_module.trim_ai_changelog_entries(days_to_keep=30, max_entries=15)
    assert isinstance(result, dict)
    assert result.get("archive_created") is True

    archive_text = archive.read_text(encoding="utf-8")
    new_pos = archive_text.find("### 2026-01-01 - Move this to archive")
    old_pos = archive_text.find("### 2025-12-01 - Existing archived entry")
    assert new_pos != -1
    assert old_pos != -1
    assert new_pos < old_pos

