from datetime import timedelta
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from ui import status_provider
from ui.status_provider import StatusProvider


pytestmark = [pytest.mark.ui, pytest.mark.unit]


def _service_manager(running=True):
    manager = Mock()
    manager.is_service_running.return_value = (running, 12345 if running else None)
    return manager


def test_discord_status_false_when_service_stopped():
    provider = StatusProvider(_service_manager(running=False))

    assert provider.check_discord_status() is False


def test_discord_status_true_for_recent_activity(tmp_path: Path):
    primary = tmp_path / "discord.log"
    backup_dir = tmp_path / "backup"
    backup_dir.mkdir()
    now = status_provider.now_datetime_full()
    primary.write_text(
        f"{(now - timedelta(seconds=30)).strftime('%Y-%m-%d %H:%M:%S')} - Discord healthy\n",
        encoding="utf-8",
    )

    provider = StatusProvider(_service_manager())
    with patch("ui.status_provider._load_attr", return_value="token"), patch.object(
        status_provider.core_config, "LOG_DISCORD_FILE", str(primary)
    ), patch.object(status_provider.core_config, "LOG_BACKUP_DIR", str(backup_dir)):
        assert provider.check_discord_status() is True


def test_email_status_uses_rotated_initialization_log(tmp_path: Path):
    primary = tmp_path / "email.log"
    backup_dir = tmp_path / "backup"
    backup_dir.mkdir()
    primary.write_text("", encoding="utf-8")
    rotated = backup_dir / "email.log.2026-06-05"
    rotated.write_text(
        "2026-06-05 10:00:00 - mhm.email - INFO - EmailBot initialized successfully.\n",
        encoding="utf-8",
    )

    provider = StatusProvider(_service_manager())
    with patch("ui.status_provider._load_attr", return_value="configured"), patch.object(
        status_provider.core_config, "LOG_EMAIL_FILE", str(primary)
    ), patch.object(status_provider.core_config, "LOG_BACKUP_DIR", str(backup_dir)):
        assert provider.check_email_status() is True


def test_ngrok_status_detects_running_http_tunnel():
    proc = Mock()
    proc.info = {"pid": 222, "name": "ngrok.exe", "cmdline": ["ngrok", "http", "8080"]}
    proc.is_running.return_value = True

    provider = StatusProvider(_service_manager())
    with patch("ui.status_provider.psutil.process_iter", return_value=[proc]):
        assert provider.check_ngrok_status() == {"running": True, "pid": 222}
