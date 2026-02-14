from pathlib import Path

import pytest

from development_tools.docs.fix_version_sync import sync_todo_with_changelog


def _write_required_files(tmp_path: Path, todo_content: str) -> None:
    (tmp_path / "TODO.md").write_text(todo_content, encoding="utf-8")
    changelog_dir = tmp_path / "ai_development_docs"
    changelog_dir.mkdir(parents=True, exist_ok=True)
    (changelog_dir / "AI_CHANGELOG.md").write_text(
        "# AI Changelog\n", encoding="utf-8"
    )


@pytest.mark.unit
def test_sync_todo_with_changelog_classifies_manual_and_auto_cleanable(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    _write_required_files(
        tmp_path,
        "\n".join(
            [
                "# TODO",
                "",
                "## High Priority",
                "**Ship logging gate** - COMPLETED",
                "- [x] Add CI guard workflow",
                "- [X] Document check in logging guide",
                "- [ ] Keep open item for later",
                "~~Old completed item~~",
                "**Complete migration plan**",
            ]
        ),
    )

    result = sync_todo_with_changelog()

    assert result["status"] == "ok"
    assert result["completed_entries"] == 4
    assert result["summary"]["auto_cleanable_count"] == 2
    assert result["summary"]["manual_review_count"] == 2
    assert "auto-cleanable checklist items: 2" in result["dry_run_report"]
    assert "manual-review items: 2" in result["dry_run_report"]

    titles = [entry["title"] for entry in result["entries"]]
    assert "**Complete migration plan**" not in titles


@pytest.mark.unit
def test_sync_todo_with_changelog_returns_zero_summary_when_clean(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    _write_required_files(
        tmp_path,
        "\n".join(
            [
                "# TODO",
                "",
                "## High Priority",
                "- [ ] Open item",
                "**Some task title**",
            ]
        ),
    )

    result = sync_todo_with_changelog()

    assert result["status"] == "ok"
    assert result["completed_entries"] == 0
    assert result["summary"]["auto_cleanable_count"] == 0
    assert result["summary"]["manual_review_count"] == 0
    assert "completed entries detected: 0" in result["dry_run_report"]


@pytest.mark.unit
def test_sync_todo_with_changelog_reports_missing_files(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)

    result = sync_todo_with_changelog()

    assert result["status"] == "ok"
    assert result["completed_entries"] == 0
    assert "required files not found" in result["dry_run_report"]
