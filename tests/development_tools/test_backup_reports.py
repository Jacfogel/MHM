"""Tests for backup_reports helper utilities."""

from unittest.mock import patch

import pytest

from tests.development_tools.conftest import load_development_tools_module

backup_reports = load_development_tools_module("shared.backup_reports")


@pytest.mark.unit
def test_resolve_output_path_relative_uses_project_root(tmp_path):
    resolved = backup_reports._resolve_output_path(tmp_path, "development_tools/reports/out.json")
    assert resolved == (tmp_path / "development_tools/reports/out.json").resolve()


@pytest.mark.unit
def test_resolve_output_path_absolute_is_preserved(tmp_path):
    absolute_path = (tmp_path / "reports" / "out.json").resolve()
    resolved = backup_reports._resolve_output_path(tmp_path, str(absolute_path))
    assert resolved == absolute_path


@pytest.mark.unit
def test_write_json_report_uses_rotation_defaults(tmp_path):
    payload = {"summary": {"ok": True}}

    with patch.object(backup_reports, "create_output_file") as mock_create:
        output_path = backup_reports.write_json_report(
            tmp_path,
            "development_tools/reports/backup.json",
            payload,
            rotate=True,
        )

    mock_create.assert_called_once()
    call_args = mock_create.call_args
    assert call_args.kwargs["rotate"] is True
    assert call_args.kwargs["max_versions"] == 7
    assert call_args.kwargs["project_root"] == tmp_path
    assert '"ok": true' in call_args.args[1]
    assert output_path == (tmp_path / "development_tools/reports/backup.json").resolve()


@pytest.mark.unit
def test_write_markdown_report_uses_rotation_defaults(tmp_path):
    content = "# report\n"

    with patch.object(backup_reports, "create_output_file") as mock_create:
        output_path = backup_reports.write_markdown_report(
            tmp_path,
            "development_tools/reports/backup.md",
            content,
            rotate=False,
        )

    mock_create.assert_called_once()
    call_args = mock_create.call_args
    assert call_args.kwargs["rotate"] is False
    assert call_args.kwargs["max_versions"] == 7
    assert call_args.kwargs["project_root"] == tmp_path
    assert call_args.args[1] == content
    assert output_path == (tmp_path / "development_tools/reports/backup.md").resolve()


@pytest.mark.unit
def test_build_inventory_markdown_renders_rule_details():
    inventory = {
        "summary": {"total_rules": 2, "enabled_rules": 1, "rules_with_files": 1},
        "rules": [
            {
                "name": "daily_backups",
                "category": "B",
                "ownership": "development_tools",
                "trigger": "nightly",
                "producer": "backup_command",
                "file_count": 3,
                "latest_modified": "2026-02-26T00:00:00",
            }
        ],
    }

    rendered = backup_reports.build_inventory_markdown(inventory)

    assert "# Backup Inventory Report" in rendered
    assert "- Total rules: 2" in rendered
    assert "- Enabled rules: 1" in rendered
    assert "- daily_backups" in rendered
    assert "category: B" in rendered
    assert "files: 3" in rendered


@pytest.mark.unit
def test_build_retention_markdown_renders_actions():
    plan = {
        "summary": {
            "target_category": "B",
            "owner": "development_tools",
            "rules_scanned": 2,
            "planned_actions": 1,
        }
    }
    result = {
        "summary": {
            "dry_run": True,
            "attempted": 1,
            "deleted": 0,
            "failed": 0,
            "freed_bytes": 1024,
        },
        "actions": [
            {"status": "planned", "file_path": "reports/archive/a.json", "reason": "retention"}
        ],
    }

    rendered = backup_reports.build_retention_markdown(plan, result)

    assert "# Backup Retention Report" in rendered
    assert "- Target category: B" in rendered
    assert "- Dry run: True" in rendered
    assert "- Freed bytes: 1024" in rendered
    assert "[planned] reports/archive/a.json (retention)" in rendered


@pytest.mark.unit
def test_build_restore_drill_markdown_includes_missing_paths_and_error():
    report = {
        "summary": {
            "success": False,
            "backup_path": "backups/latest",
            "restore_destination": "tests/data/tmp/restore",
            "restored_file_count": 1,
            "error": "restore failed",
        },
        "verification": {
            "required_paths_ok": False,
            "min_file_count_ok": True,
            "missing_required_paths": ["tests/data/users", "logs"],
        },
    }

    rendered = backup_reports.build_restore_drill_markdown(report)

    assert "# Backup Restore Drill Report" in rendered
    assert "- Success: False" in rendered
    assert "- required_paths_ok: False" in rendered
    assert "- min_file_count_ok: True" in rendered
    assert "- missing_required_paths: tests/data/users, logs" in rendered
    assert "## Error" in rendered
    assert "- restore failed" in rendered
