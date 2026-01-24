"""Unit tests for auto_cleanup timestamp helpers."""

import json
import shutil
import tempfile
from pathlib import Path
from uuid import uuid4

import pytest

import core.auto_cleanup as auto_cleanup


@pytest.fixture
def tracker_file(monkeypatch):
    """Point the auto_cleanup tracker at a temporary file path."""
    tmp_dir = Path.cwd() / f".autocleanup_logic_{uuid4().hex}"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    path = tmp_dir / ".last_cache_cleanup"
    monkeypatch.setattr(auto_cleanup, "CLEANUP_TRACKER_FILE", str(path))
    yield path
    shutil.rmtree(tmp_dir, ignore_errors=True)


@pytest.mark.unit
def test_get_last_cleanup_timestamp_invalid_json(tracker_file):
    tracker_file.write_text("not json")
    assert auto_cleanup.get_last_cleanup_timestamp() == 0.0


@pytest.mark.unit
def test_should_run_cleanup_recent_false(tracker_file, monkeypatch):
    now = 1_000_000.0
    tracker_file.write_text(json.dumps({"last_cleanup_timestamp": now}))
    monkeypatch.setattr(auto_cleanup.time, "time", lambda: now + 100)

    assert auto_cleanup.should_run_cleanup(interval_days=30) is False


@pytest.mark.unit
def test_should_run_cleanup_old_true(tracker_file, monkeypatch):
    interval_days = 5
    now = 1_000_000.0
    old_ts = now - (interval_days + 1) * 24 * 60 * 60
    tracker_file.write_text(json.dumps({"last_cleanup_timestamp": old_ts}))
    monkeypatch.setattr(auto_cleanup.time, "time", lambda: now)

    assert auto_cleanup.should_run_cleanup(interval_days=interval_days) is True
