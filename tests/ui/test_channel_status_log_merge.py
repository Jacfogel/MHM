"""Tests for admin panel channel status log merging (rotation-aware)."""

import pytest

from ui.ui_app_qt import _merge_rotated_channel_log_lines


pytestmark = [pytest.mark.ui]

@pytest.mark.unit
@pytest.mark.ui
def test_merge_rotated_channel_log_lines_includes_backup_with_init(tmp_path):
    """Init line in a rotated file under LOG_BACKUP_DIR pattern must be visible to the UI."""
    backup_dir = tmp_path / "backups"
    backup_dir.mkdir()
    primary = tmp_path / "email.log"
    primary.write_text(
        "2026-04-02 12:00:00 - mhm.email - INFO - ping\n",
        encoding="utf-8",
    )
    rotated = backup_dir / "email.log.2026-04-01"
    rotated.write_text(
        "2026-04-01 10:00:00 - mhm.email - INFO - EmailBot initialized successfully.\n",
        encoding="utf-8",
    )
    lines = _merge_rotated_channel_log_lines(primary, backup_dir)
    assert any("EmailBot initialized successfully" in ln for ln in lines)


@pytest.mark.unit
@pytest.mark.ui
def test_merge_rotated_channel_log_lines_primary_only(tmp_path):
    primary = tmp_path / "discord.log"
    primary.write_text("2026-04-02 12:00:00 - mhm.discord - INFO - ok\n", encoding="utf-8")
    lines = _merge_rotated_channel_log_lines(primary, tmp_path / "missing_backups")
    assert len(lines) == 1
    assert "ok" in lines[0]
