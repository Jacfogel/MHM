import sys
from pathlib import Path

import pytest


@pytest.mark.unit
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


