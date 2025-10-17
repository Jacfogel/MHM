import logging
from pathlib import Path

import pytest


@pytest.mark.behavior
def test_component_logs_isolation_and_errors_capture(tmp_path, monkeypatch):
    """Verify component logs go to their files, do not duplicate into app.log, and errors go to errors.log."""
    # Arrange test logs directory
    test_logs = tmp_path / "logs"
    test_logs.mkdir()
    (test_logs / "backups").mkdir()
    (test_logs / "archive").mkdir()

    # Point env to tests mode with verbose component logs in tests/logs
    monkeypatch.setenv("MHM_TESTING", "1")
    monkeypatch.setenv("TEST_VERBOSE_LOGS", "1")
    # Disable consolidated logging for this test to allow individual component files
    monkeypatch.setenv("TEST_CONSOLIDATED_LOGGING", "0")

    # Redirect LOGS_DIR to tests/logs and ensure core.logger picks this up before first import
    monkeypatch.setenv("LOGS_DIR", str(test_logs))
    # Force re-import of core.logger to honor new env in this test process
    import sys
    if 'core.logger' in sys.modules:
        del sys.modules['core.logger']
    from core.logger import get_component_logger
    # Touch component loggers after ensuring remap is active

    # Act: write to discord (INFO) and raise an ERROR via scheduler
    discord_logger = get_component_logger('discord')
    scheduler_logger = get_component_logger('scheduler')
    main_logger = logging.getLogger()  # root

    discord_logger.info("obs-test: discord info")
    scheduler_logger.error("obs-test: scheduler error")
    main_logger.info("obs-test: root info")

    # Assert: files exist under tests/logs
    discord_log = test_logs / "discord.log"
    scheduler_log = test_logs / "scheduler.log"
    app_log = test_logs / "app.log"
    errors_log = Path("logs") / "errors.log"  # errors still go to normal errors.log by design

    assert discord_log.exists(), "discord.log should exist in tests/logs"
    assert scheduler_log.exists(), "scheduler.log should exist in tests/logs"

    # Read contents
    d_text = discord_log.read_text(encoding='utf-8')
    s_text = scheduler_log.read_text(encoding='utf-8')
    a_text = app_log.read_text(encoding='utf-8') if app_log.exists() else ""

    assert "obs-test: discord info" in d_text, "discord info should be in discord.log"
    assert "obs-test: scheduler error" in s_text, "scheduler error should be in scheduler.log"

    # Since component loggers have propagate=False, these entries must not appear in app.log
    assert "obs-test: discord info" not in a_text
    assert "obs-test: scheduler error" not in a_text

    # And errors must be duplicated into errors log; since in test mode we remap
    # component logs but not errors, allow either tests/logs/errors.log or logs/errors.log
    alt_errors_log = test_logs / "errors.log"
    candidate_errors = [errors_log, alt_errors_log]
    found_error = False
    for path in candidate_errors:
        if path.exists():
            e_text = path.read_text(encoding='utf-8')
            if "obs-test: scheduler error" in e_text:
                found_error = True
                break
    assert found_error, "errors log should contain the scheduler error"


