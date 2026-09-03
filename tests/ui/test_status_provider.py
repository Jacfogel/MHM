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


def test_ngrok_status_false_when_not_running():
    provider = StatusProvider(_service_manager())
    with patch("ui.status_provider.psutil.process_iter", return_value=[]):
        assert provider.check_ngrok_status() == {"running": False, "pid": None}


def test_discord_status_false_when_token_missing():
    provider = StatusProvider(_service_manager())
    with patch("ui.status_provider._load_attr", return_value=None):
        assert provider.check_discord_status() is False


def test_discord_status_true_for_recent_init_log(tmp_path: Path):
    primary = tmp_path / "discord.log"
    backup_dir = tmp_path / "backup"
    backup_dir.mkdir()
    now = status_provider.now_datetime_full()
    primary.write_text(
        f"{(now - timedelta(minutes=5)).strftime('%Y-%m-%d %H:%M:%S')} - "
        "Discord bot initialized successfully\n",
        encoding="utf-8",
    )

    provider = StatusProvider(_service_manager())
    with patch("ui.status_provider._load_attr", return_value="token"), patch.object(
        status_provider.core_config, "LOG_DISCORD_FILE", str(primary)
    ), patch.object(status_provider.core_config, "LOG_BACKUP_DIR", str(backup_dir)):
        assert provider.check_discord_status() is True


def test_email_status_false_when_service_stopped():
    provider = StatusProvider(_service_manager(running=False))
    assert provider.check_email_status() is False


def test_email_status_false_when_credentials_incomplete():
    provider = StatusProvider(_service_manager())
    with patch(
        "ui.status_provider._load_attr",
        side_effect=lambda _mod, attr: "smtp" if "SMTP_SERVER" in attr else None,
    ):
        assert provider.check_email_status() is False


def test_email_status_true_for_recent_activity(tmp_path: Path):
    primary = tmp_path / "email.log"
    backup_dir = tmp_path / "backup"
    backup_dir.mkdir()
    now = status_provider.now_datetime_full()
    primary.write_text(
        f"{(now - timedelta(seconds=30)).strftime('%Y-%m-%d %H:%M:%S')} - "
        "Email sent to user@example.com\n",
        encoding="utf-8",
    )

    provider = StatusProvider(_service_manager())
    with patch("ui.status_provider._load_attr", return_value="configured"), patch.object(
        status_provider.core_config, "LOG_EMAIL_FILE", str(primary)
    ), patch.object(status_provider.core_config, "LOG_BACKUP_DIR", str(backup_dir)):
        assert provider.check_email_status() is True


def test_check_service_status_delegates_to_manager():
    manager = _service_manager(running=True)
    provider = StatusProvider(manager)
    assert provider.check_service_status() == (True, 12345)
    manager.is_service_running.assert_called_once()


def test_tail_file_lines_missing_file_returns_empty(tmp_path: Path):
    assert status_provider.tail_file_lines(tmp_path / "missing.log", 10) == []


def test_tail_file_lines_truncates_to_max(tmp_path: Path):
    log_path = tmp_path / "app.log"
    log_path.write_text("".join(f"line {i}\n" for i in range(20)), encoding="utf-8")
    lines = status_provider.tail_file_lines(log_path, 5)
    assert len(lines) == 5
    assert lines[0] == "line 15\n"
    assert lines[-1] == "line 19\n"


def test_discord_status_true_for_stale_activity_without_init(tmp_path: Path):
    primary = tmp_path / "discord.log"
    backup_dir = tmp_path / "backup"
    backup_dir.mkdir()
    now = status_provider.now_datetime_full()
    primary.write_text(
        f"{(now - timedelta(minutes=10)).strftime('%Y-%m-%d %H:%M:%S')} - Discord healthy\n",
        encoding="utf-8",
    )
    provider = StatusProvider(_service_manager())
    with patch("ui.status_provider._load_attr", return_value="token"), patch.object(
        status_provider.core_config, "LOG_DISCORD_FILE", str(primary)
    ), patch.object(status_provider.core_config, "LOG_BACKUP_DIR", str(backup_dir)):
        assert provider.check_discord_status() is True


def test_discord_status_true_when_shutdown_is_after_init(tmp_path: Path):
    primary = tmp_path / "discord.log"
    backup_dir = tmp_path / "backup"
    backup_dir.mkdir()
    now = status_provider.now_datetime_full()
    init_ts = (now - timedelta(hours=2)).strftime("%Y-%m-%d %H:%M:%S")
    shutdown_ts = (now - timedelta(minutes=5)).strftime("%Y-%m-%d %H:%M:%S")
    primary.write_text(
        f"{init_ts} - Discord bot initialized successfully\n"
        f"{shutdown_ts} - Discord bot shutdown completed\n",
        encoding="utf-8",
    )
    provider = StatusProvider(_service_manager())
    with patch("ui.status_provider._load_attr", return_value="token"), patch.object(
        status_provider.core_config, "LOG_DISCORD_FILE", str(primary)
    ), patch.object(status_provider.core_config, "LOG_BACKUP_DIR", str(backup_dir)):
        assert provider.check_discord_status() is True


def test_discord_status_skips_unparseable_timestamps(tmp_path: Path):
    primary = tmp_path / "discord.log"
    backup_dir = tmp_path / "backup"
    backup_dir.mkdir()
    primary.write_text(
        "2026-09-02 12:00:00 - Discord bot initialized successfully\n"
        "2026-09-02 12:01:00 - Discord healthy\n",
        encoding="utf-8",
    )
    provider = StatusProvider(_service_manager())
    with patch("ui.status_provider._load_attr", return_value="token"), patch.object(
        status_provider.core_config, "LOG_DISCORD_FILE", str(primary)
    ), patch.object(status_provider.core_config, "LOG_BACKUP_DIR", str(backup_dir)), patch(
        "ui.status_provider.parse_timestamp_full", return_value=None
    ):
        assert provider.check_discord_status() is True


def test_discord_status_true_when_log_merge_raises(tmp_path: Path):
    provider = StatusProvider(_service_manager())
    with patch("ui.status_provider._load_attr", return_value="token"), patch(
        "ui.status_provider.merge_rotated_channel_log_lines",
        side_effect=OSError("unreadable"),
    ):
        assert provider.check_discord_status() is True


def test_discord_status_false_when_service_check_raises():
    manager = Mock()
    manager.is_service_running.side_effect = RuntimeError("status failed")
    provider = StatusProvider(manager)
    assert provider.check_discord_status() is False


def test_email_status_true_for_stale_activity_without_init(tmp_path: Path):
    primary = tmp_path / "email.log"
    backup_dir = tmp_path / "backup"
    backup_dir.mkdir()
    now = status_provider.now_datetime_full()
    primary.write_text(
        f"{(now - timedelta(minutes=10)).strftime('%Y-%m-%d %H:%M:%S')} - Email sent to user@example.com\n",
        encoding="utf-8",
    )
    provider = StatusProvider(_service_manager())
    with patch("ui.status_provider._load_attr", return_value="configured"), patch.object(
        status_provider.core_config, "LOG_EMAIL_FILE", str(primary)
    ), patch.object(status_provider.core_config, "LOG_BACKUP_DIR", str(backup_dir)):
        assert provider.check_email_status() is True


def test_email_status_true_when_shutdown_is_after_init(tmp_path: Path):
    primary = tmp_path / "email.log"
    backup_dir = tmp_path / "backup"
    backup_dir.mkdir()
    now = status_provider.now_datetime_full()
    init_ts = (now - timedelta(hours=2)).strftime("%Y-%m-%d %H:%M:%S")
    shutdown_ts = (now - timedelta(minutes=5)).strftime("%Y-%m-%d %H:%M:%S")
    primary.write_text(
        f"{init_ts} - EmailBot initialized successfully\n"
        f"{shutdown_ts} - EmailBot stopped\n",
        encoding="utf-8",
    )
    provider = StatusProvider(_service_manager())
    with patch("ui.status_provider._load_attr", return_value="configured"), patch.object(
        status_provider.core_config, "LOG_EMAIL_FILE", str(primary)
    ), patch.object(status_provider.core_config, "LOG_BACKUP_DIR", str(backup_dir)):
        assert provider.check_email_status() is True


def test_email_status_true_when_log_merge_raises():
    provider = StatusProvider(_service_manager())
    with patch("ui.status_provider._load_attr", return_value="configured"), patch(
        "ui.status_provider.merge_rotated_channel_log_lines",
        side_effect=OSError("unreadable"),
    ):
        assert provider.check_email_status() is True


def test_ngrok_status_skips_empty_name_and_non_http():
    empty = Mock()
    empty.info = {"pid": 1, "name": "", "cmdline": ["ngrok", "http"]}
    other = Mock()
    other.info = {"pid": 2, "name": "ngrok.exe", "cmdline": ["ngrok", "start"]}
    other.is_running.return_value = True
    denied = Mock()
    denied.info = {"pid": 3, "name": "ngrok.exe", "cmdline": ["ngrok", "http"]}
    denied.is_running.side_effect = status_provider.psutil.AccessDenied()

    provider = StatusProvider(_service_manager())
    with patch(
        "ui.status_provider.psutil.process_iter",
        return_value=[empty, other, denied],
    ):
        assert provider.check_ngrok_status() == {"running": False, "pid": None}


def test_ngrok_status_false_when_process_iter_raises():
    provider = StatusProvider(_service_manager())
    with patch(
        "ui.status_provider.psutil.process_iter",
        side_effect=RuntimeError("psutil down"),
    ):
        assert provider.check_ngrok_status() == {"running": False, "pid": None}
