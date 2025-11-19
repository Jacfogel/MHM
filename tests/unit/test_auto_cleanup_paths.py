"""Unit tests for auto_cleanup path configuration."""

import importlib
from pathlib import Path

import pytest

import core.config as config_module
import core.auto_cleanup as auto_cleanup


@pytest.mark.unit
def test_update_cleanup_timestamp_respects_test_data_dir(monkeypatch, tmp_path):
    """Ensure cleanup tracker file is written inside configured test data directory."""
    global config_module, auto_cleanup

    original_tracker_path = Path(auto_cleanup.CLEANUP_TRACKER_FILE)

    with monkeypatch.context() as context:
        context.setenv("MHM_TESTING", "1")
        context.setenv("TEST_DATA_DIR", str(tmp_path))

        config_module = importlib.reload(config_module)
        auto_cleanup = importlib.reload(auto_cleanup)

        auto_cleanup.update_cleanup_timestamp()
        tracker_path = Path(auto_cleanup.CLEANUP_TRACKER_FILE)

        assert tracker_path.exists(), "Tracker file should be created inside configured directory"
        assert tracker_path.parent == tmp_path
        assert tracker_path == tmp_path / ".last_cache_cleanup"

    config_module = importlib.reload(config_module)
    auto_cleanup = importlib.reload(auto_cleanup)
    assert Path(auto_cleanup.CLEANUP_TRACKER_FILE) == original_tracker_path
