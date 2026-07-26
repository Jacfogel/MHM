import contextlib
import logging
import sys
from pathlib import Path

import pytest


pytestmark = [pytest.mark.core]

@pytest.mark.unit
@pytest.mark.core
def test_component_logger_propagate_and_handlers(tmp_path, monkeypatch):
    # Test with individual component logging (disable consolidated mode)
    monkeypatch.setenv("MHM_TESTING", "1")
    monkeypatch.setenv("TEST_VERBOSE_LOGS", "1")
    monkeypatch.setenv("TEST_CONSOLIDATED_LOGGING", "0")  # Disable consolidated logging
    # Redirect logs under a temporary directory
    logs_dir = tmp_path / "logs"
    monkeypatch.setenv("LOGS_DIR", str(logs_dir))

    # Force re-import to honor env changes
    if 'core.logger' in sys.modules:
        del sys.modules['core.logger']
    from core.logger import get_component_logger

    comp = get_component_logger('discord')
    # Access underlying stdlib logger
    std_logger = comp.logger  # type: ignore[attr-defined]

    # propagate should be False to avoid app.log duplication
    assert std_logger.propagate is False

    # Should have at least two handlers: component file + errors handler
    handlers = list(std_logger.handlers)
    assert len(handlers) >= 2

    # Component file handler should write to discord.log
    base_filenames = [getattr(h, 'baseFilename', '') for h in handlers]
    assert any(Path(f).name == 'discord.log' for f in base_filenames if f)

    # Errors handler should write to errors.log (remapped under tests/logs)
    assert any(Path(f).name == 'errors.log' for f in base_filenames if f)

    # Ensure discord handler level is DEBUG for richer details
    discord_levels = [getattr(h, 'level', None) for h in handlers if getattr(h, 'baseFilename', '').endswith('discord.log')]
    assert any(lvl == 10 for lvl in discord_levels)  # 10 == logging.DEBUG


@pytest.mark.unit
@pytest.mark.core
def test_errors_routed_to_tests_logs_in_verbose_mode(tmp_path, monkeypatch):
    # Test with individual component logging (disable consolidated mode)
    monkeypatch.setenv("MHM_TESTING", "1")
    monkeypatch.setenv("TEST_VERBOSE_LOGS", "1")
    monkeypatch.setenv("TEST_CONSOLIDATED_LOGGING", "0")  # Disable consolidated logging
    logs_dir = tmp_path / "logs"
    monkeypatch.setenv("LOGS_DIR", str(logs_dir))

    if 'core.logger' in sys.modules:
        del sys.modules['core.logger']
    from core.logger import get_component_logger

    comp = get_component_logger('ai')
    std_logger = comp.logger  # type: ignore[attr-defined]
    # Emit an error and ensure tests/logs/errors.log exists
    std_logger.error("unit-test error message")

    errors_log = logs_dir / 'errors.log'
    assert errors_log.exists(), "errors.log should be created under tests/logs in verbose test mode"
    assert "unit-test error message" in errors_log.read_text(encoding='utf-8')


@pytest.mark.unit
@pytest.mark.core
def test_consolidated_logging_mode(tmp_path, monkeypatch):
    """Test that consolidated logging works correctly."""
    # Test with consolidated logging enabled (default)
    monkeypatch.setenv("MHM_TESTING", "1")
    monkeypatch.setenv("TEST_VERBOSE_LOGS", "1")
    monkeypatch.setenv("TEST_CONSOLIDATED_LOGGING", "1")  # Enable consolidated logging
    # Use a temporary directory to avoid conflicts with other tests
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir()
    monkeypatch.setenv("LOGS_DIR", str(logs_dir))

    if 'core.logger' in sys.modules:
        del sys.modules['core.logger']
    from core.logger import get_component_logger

    comp = get_component_logger('ai')
    std_logger = comp.logger  # type: ignore[attr-defined]
    
    # In consolidated mode, should have the consolidated handler attached
    handlers = list(std_logger.handlers)
    assert len(handlers) >= 1, "Consolidated logging should have the consolidated handler attached"
    
    # Emit a log message
    std_logger.error("consolidated test error message")
    
    # In consolidated mode, individual log files should not be created
    errors_log = logs_dir / 'errors.log'
    assert not errors_log.exists(), "Individual errors.log should not be created in consolidated mode"
    
    # The consolidated log should contain the message
    consolidated_log = logs_dir / 'test_consolidated.log'
    if consolidated_log.exists():
        log_content = consolidated_log.read_text(encoding='utf-8')
        assert "consolidated test error message" in log_content, "Message should be in consolidated log"


@pytest.mark.unit
@pytest.mark.core
def test_error_handler_dual_writes_to_errors_log(tmp_path, monkeypatch):
    """mhm.error_handler ERROR lines should land in errors.log after setup."""
    monkeypatch.setenv("MHM_TESTING", "1")
    monkeypatch.setenv("TEST_VERBOSE_LOGS", "1")
    monkeypatch.setenv("TEST_CONSOLIDATED_LOGGING", "0")
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir()
    monkeypatch.setenv("LOGS_DIR", str(logs_dir))

    if "core.logger" in sys.modules:
        del sys.modules["core.logger"]
    from core.logger import setup_error_handler_logging

    error_logger = logging.getLogger("mhm.error_handler")
    # Drop any prior file handlers from other tests; keep StreamHandlers
    for handler in list(error_logger.handlers):
        base = getattr(handler, "baseFilename", "") or ""
        if base:
            with contextlib.suppress(Exception):
                handler.close()
            error_logger.removeHandler(handler)

    setup_error_handler_logging()
    setup_error_handler_logging()  # idempotent

    file_handlers = [
        h
        for h in error_logger.handlers
        if Path(str(getattr(h, "baseFilename", "") or "")).name == "errors.log"
    ]
    assert len(file_handlers) == 1, "Should attach exactly one errors.log handler"
    assert error_logger.propagate is False

    marker = "unit-test error_handler dual-write message"
    error_logger.error(marker)
    for handler in file_handlers:
        handler.flush()

    errors_log = logs_dir / "errors.log"
    assert errors_log.exists(), "errors.log should be created for mhm.error_handler"
    assert marker in errors_log.read_text(encoding="utf-8")


@pytest.mark.unit
@pytest.mark.core
def test_component_name_aliases_to_communication_manager(tmp_path, monkeypatch):
    """Busy communication aliases should share communication_manager.log."""
    monkeypatch.setenv("MHM_TESTING", "1")
    monkeypatch.setenv("TEST_VERBOSE_LOGS", "1")
    monkeypatch.setenv("TEST_CONSOLIDATED_LOGGING", "0")
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir()
    monkeypatch.setenv("LOGS_DIR", str(logs_dir))

    if "core.logger" in sys.modules:
        del sys.modules["core.logger"]
    from core import logger as logger_mod

    logger_mod._component_loggers.clear()

    orch = logger_mod.get_component_logger("channel_orchestrator")
    account = logger_mod.get_component_logger("account_handler")
    retry = logger_mod.get_component_logger("retry_manager")
    checkin = logger_mod.get_component_logger("checkin_handler")
    canonical = logger_mod.get_component_logger("communication_manager")

    assert orch is account is retry is checkin is canonical
    assert orch.logger.name == "mhm.communication_manager"

    filenames = [
        Path(str(getattr(h, "baseFilename", "") or "")).name
        for h in orch.logger.handlers
    ]
    assert "communication_manager.log" in filenames
    assert "app.log" not in filenames


@pytest.mark.unit
@pytest.mark.core
def test_component_name_aliases_ai_ui_discord_and_main(tmp_path, monkeypatch):
    """AI/UI/discord/domain aliases should resolve to canonical sinks."""
    monkeypatch.setenv("MHM_TESTING", "1")
    monkeypatch.setenv("TEST_VERBOSE_LOGS", "1")
    monkeypatch.setenv("TEST_CONSOLIDATED_LOGGING", "0")
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir()
    monkeypatch.setenv("LOGS_DIR", str(logs_dir))
    # conftest points LOG_MAIN_FILE at the consolidated placeholder; override for this test
    monkeypatch.setenv("LOG_MAIN_FILE", str(logs_dir / "app.log"))

    if "core.logger" in sys.modules:
        del sys.modules["core.logger"]
    from core import logger as logger_mod

    logger_mod._component_loggers.clear()

    cases = (
        ("ai_context", "ai", "ai.log"),
        ("ai_conversation", "ai", "ai.log"),
        ("ui_widgets", "ui", "ui.log"),
        ("admin_panel", "ui", "ui.log"),
        ("discord_api", "discord", "discord.log"),
        ("tasks", "main", "app.log"),
        ("notebook_data_manager", "main", "app.log"),
        ("headless_service", "main", "app.log"),
        ("launcher", "main", "app.log"),
    )

    for alias, canonical, expected_file in cases:
        logger_mod._component_loggers.clear()
        aliased = logger_mod.get_component_logger(alias)
        target = logger_mod.get_component_logger(canonical)
        assert aliased is target, f"{alias} should share logger with {canonical}"
        assert aliased.logger.name == f"mhm.{canonical}"
        filenames = [
            Path(str(getattr(h, "baseFilename", "") or "")).name
            for h in aliased.logger.handlers
        ]
        assert expected_file in filenames, f"{alias} should write to {expected_file}"


@pytest.mark.unit
@pytest.mark.core
def test_bootstrap_raw_loggers_dual_write_to_errors_log(tmp_path, monkeypatch):
    """network_probe / time_utilities / config ERROR should hit errors.log."""
    monkeypatch.setenv("MHM_TESTING", "1")
    monkeypatch.setenv("TEST_VERBOSE_LOGS", "1")
    monkeypatch.setenv("TEST_CONSOLIDATED_LOGGING", "0")
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir()
    monkeypatch.setenv("LOGS_DIR", str(logs_dir))

    if "core.logger" in sys.modules:
        del sys.modules["core.logger"]
    from core.logger import setup_error_handler_logging

    for name in ("mhm.network_probe", "mhm.time_utilities", "mhm.config"):
        target = logging.getLogger(name)
        for handler in list(target.handlers):
            base = getattr(handler, "baseFilename", "") or ""
            if base:
                with contextlib.suppress(Exception):
                    handler.close()
                target.removeHandler(handler)

    setup_error_handler_logging()

    markers = []
    for name in ("mhm.network_probe", "mhm.time_utilities", "mhm.config"):
        target = logging.getLogger(name)
        assert _has_errors_handler(target), f"{name} missing errors.log handler"
        assert target.propagate is True
        marker = f"unit-test {name} bootstrap error"
        markers.append(marker)
        target.error(marker)
        for handler in target.handlers:
            if hasattr(handler, "flush"):
                handler.flush()

    errors_text = (logs_dir / "errors.log").read_text(encoding="utf-8")
    for marker in markers:
        assert marker in errors_text


def _has_errors_handler(target: logging.Logger) -> bool:
    return any(
        Path(str(getattr(h, "baseFilename", "") or "")).name == "errors.log"
        for h in target.handlers
    )

