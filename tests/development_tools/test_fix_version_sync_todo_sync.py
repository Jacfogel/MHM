from pathlib import Path

import pytest

from development_tools.docs.fix_version_sync import (
    _classify_completed_todo_line,
    _find_todo_scan_start,
    sync_todo_with_changelog,
)


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
    assert result.get("apply_performed") is False
    assert result.get("auto_clean_lines_removed") == 0
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
    assert result.get("apply_performed") is False


@pytest.mark.unit
def test_sync_todo_with_changelog_reports_missing_files(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)

    result = sync_todo_with_changelog()

    assert result["status"] == "ok"
    assert result["completed_entries"] == 0
    assert "required files not found" in result["dry_run_report"]
    assert result.get("apply_performed") is False


@pytest.mark.unit
def test_sync_todo_apply_removes_only_checklist_lines(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    _write_required_files(
        tmp_path,
        "\n".join(
            [
                "# TODO",
                "",
                "## High Priority",
                "- [x] Done checklist item",
                "- [ ] Still open",
                "**Title with COMPLETED**",
            ]
        ),
    )

    result = sync_todo_with_changelog(apply_auto_clean=True)

    assert result["status"] == "ok"
    assert result.get("apply_performed") is True
    assert result.get("auto_clean_lines_removed") == 1
    updated = (tmp_path / "TODO.md").read_text(encoding="utf-8")
    assert "Done checklist item" not in updated
    assert "- [ ] Still open" in updated
    assert "COMPLETED" in updated


@pytest.mark.unit
def test_find_todo_scan_start_skips_preamble_until_first_heading():
    lines = [
        "# TODO",
        "Intro line",
        "",
        "## High Priority",
        "- [ ] open",
    ]
    assert _find_todo_scan_start(lines) == 3


@pytest.mark.unit
@pytest.mark.parametrize(
    ("line", "expected_type"),
    [
        ("- [x] done item", "checklist_checked"),
        ("~~Legacy done~~", "strikethrough"),
        ("Task status: COMPLETED", "trailing_status_marker"),
        ("Refactor parser (DONE)", "trailing_status_marker"),
        ("✅ completed migration", "emoji_status_marker"),
        ("**DONE**", "bold_status_marker"),
    ],
)
def test_classify_completed_todo_line_detects_supported_completion_markers(
    line: str, expected_type: str
):
    is_done, marker_type = _classify_completed_todo_line(line)
    assert is_done is True
    assert marker_type == expected_type
