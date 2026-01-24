"""Unit tests for auto_cleanup path configuration."""

import shutil
from pathlib import Path
from uuid import uuid4

import pytest

import core.auto_cleanup as auto_cleanup


@pytest.mark.unit
def test_update_cleanup_timestamp_respects_test_data_dir(monkeypatch):
    """Ensure the cleanup tracker honors a custom test data directory."""

    original_tracker_file = Path(auto_cleanup.CLEANUP_TRACKER_FILE)
    tmp_dir = Path(Path.cwd()) / f".autocleanup_temp_{uuid4().hex}"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    try:
        tmp_tracker = tmp_dir / auto_cleanup.CLEANUP_TRACKER_FILENAME
        with monkeypatch.context() as context:
            context.setattr(
                auto_cleanup,
                "CLEANUP_TRACKER_FILE",
                str(tmp_tracker),
            )

            auto_cleanup.update_cleanup_timestamp()
            assert tmp_tracker.exists()
            assert tmp_tracker.parent == tmp_dir
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)

    assert Path(auto_cleanup.CLEANUP_TRACKER_FILE) == original_tracker_file
