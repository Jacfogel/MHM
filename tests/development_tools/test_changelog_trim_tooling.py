"""Tests for changelog check/trim integration in audit orchestration."""

from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from tests.development_tools.conftest import load_development_tools_module

service_module = load_development_tools_module("shared.service")
AIToolsService = service_module.AIToolsService


def _write_recent_changes(changelog_path: Path, entry_count: int) -> None:
    lines = ["# AI Changelog", "", "## Recent Changes (Most Recent First)", ""]
    base_date = datetime.now()
    for idx in range(entry_count):
        entry_date = (base_date - timedelta(days=idx + 1)).strftime("%Y-%m-%d")
        lines.append(f"### {entry_date} - Entry {idx + 1}")
        lines.append("- details")
        lines.append("")
    changelog_path.write_text("\n".join(lines), encoding="utf-8")


@pytest.mark.unit
def test_check_and_trim_changelog_entries_skips_trim_when_within_limit(
    tmp_path, monkeypatch
):
    """When changelog is within limit, trim should not create archive output."""
    monkeypatch.chdir(tmp_path)
    service = AIToolsService(project_root=str(tmp_path))
    logger_mock = MagicMock()
    monkeypatch.setitem(
        service._check_and_trim_changelog_entries.__func__.__globals__,
        "logger",
        logger_mock,
    )

    ai_docs = Path("ai_development_docs")
    ai_docs.mkdir(parents=True, exist_ok=True)
    _write_recent_changes(ai_docs / "AI_CHANGELOG.md", entry_count=10)

    service._check_and_trim_changelog_entries()

    info_messages = [call.args[0] for call in logger_mock.info.call_args_list]
    debug_messages = [call.args[0] for call in logger_mock.debug.call_args_list]
    assert any("Changelog check:" in msg for msg in debug_messages)
    assert not any("Created archive: archive/AI_CHANGELOG_ARCHIVE.md" in msg for msg in info_messages)


@pytest.mark.unit
def test_check_and_trim_changelog_entries_trims_when_over_limit(
    tmp_path, monkeypatch
):
    """When changelog exceeds limit, trim should run and log summary."""
    monkeypatch.chdir(tmp_path)
    service = AIToolsService(project_root=str(tmp_path))
    logger_mock = MagicMock()
    monkeypatch.setitem(
        service._check_and_trim_changelog_entries.__func__.__globals__,
        "logger",
        logger_mock,
    )

    ai_docs = Path("ai_development_docs")
    ai_docs.mkdir(parents=True, exist_ok=True)
    _write_recent_changes(ai_docs / "AI_CHANGELOG.md", entry_count=20)

    service._check_and_trim_changelog_entries()

    archive_file = Path("archive/AI_CHANGELOG_ARCHIVE.md")
    assert archive_file.exists()
    log_messages = [call.args[0] for call in logger_mock.info.call_args_list]
    assert any("Trimmed " in msg and "old changelog entries" in msg for msg in log_messages)
    assert any("Changelog entries kept: 15" in msg for msg in log_messages)
    assert any("Created archive: archive/AI_CHANGELOG_ARCHIVE.md" in msg for msg in log_messages)
