"""Platform-branch coverage tests for core.file_locking."""

from __future__ import annotations

import importlib
import sys
import types
from pathlib import Path
from unittest.mock import patch

import pytest

import core.file_locking as file_locking_mod


pytestmark = [pytest.mark.core]

@pytest.fixture
def unix_file_locking_module(monkeypatch):
    """Reload core.file_locking as if running on Unix (non-win32)."""
    original_platform = sys.platform

    fake_fcntl = types.SimpleNamespace(LOCK_EX=1, LOCK_NB=2, LOCK_UN=8)
    fake_fcntl.flock = lambda fd, flags: None

    monkeypatch.setattr(sys, "platform", "linux")
    monkeypatch.setitem(sys.modules, "fcntl", fake_fcntl)

    unix_mod = importlib.reload(file_locking_mod)
    yield unix_mod

    # Restore module implementation for the real platform after test completes.
    monkeypatch.setattr(sys, "platform", original_platform)
    importlib.reload(file_locking_mod)


@pytest.mark.unit
@pytest.mark.file_io
@pytest.mark.core
class TestFileLockingPlatformBranches:
    def test_windows_lock_path_oserror_timeout_branch(self, test_data_dir):
        target = Path(test_data_dir) / "windows_oserror_timeout.json"

        # Force OSError on lock-file creation path to exercise timeout branch.
        with patch("builtins.open", side_effect=OSError("lock create failed")):
            with pytest.raises(TimeoutError, match="Could not acquire lock"):
                with file_locking_mod.file_lock(
                    str(target), timeout=0.0, retry_interval=0.0
                ):
                    pass

    def test_unix_file_lock_success_and_unlock(self, unix_file_locking_module, test_data_dir):
        target = Path(test_data_dir) / "unix_success.json"

        calls = []

        def _flock(fd, flags):
            calls.append(flags)

        unix_file_locking_module.fcntl.flock = _flock

        with unix_file_locking_module.file_lock(str(target), timeout=1.0, retry_interval=0.0) as handle:
            assert handle is not None

        assert unix_file_locking_module.fcntl.LOCK_EX | unix_file_locking_module.fcntl.LOCK_NB in calls
        assert unix_file_locking_module.fcntl.LOCK_UN in calls
        assert target.exists()

    def test_unix_file_lock_timeout_in_flock_retry_loop(self, unix_file_locking_module, test_data_dir):
        target = Path(test_data_dir) / "unix_flock_timeout.json"

        def _flock_raises(fd, flags):
            raise OSError("busy")

        unix_file_locking_module.fcntl.flock = _flock_raises

        with pytest.raises(TimeoutError, match="Could not acquire lock"):
            with unix_file_locking_module.file_lock(
                str(target), timeout=0.0, retry_interval=0.0
            ):
                pass

    @pytest.mark.timeout(5)
    def test_unix_file_lock_timeout_ignores_frozen_time_time(
        self, unix_file_locking_module, test_data_dir
    ):
        """A patched time.time must not keep a busy flock retrying until pytest-timeout."""
        import time

        target = Path(test_data_dir) / "unix_frozen_time.json"

        def _flock_raises(fd, flags):
            if flags & unix_file_locking_module.fcntl.LOCK_UN:
                return None
            raise OSError("busy")

        unix_file_locking_module.fcntl.flock = _flock_raises
        started = time.monotonic()
        with patch.object(unix_file_locking_module.time, "time", return_value=1000.0):
            with pytest.raises(TimeoutError, match="Could not acquire lock"):
                with unix_file_locking_module.file_lock(
                    str(target), timeout=0.2, retry_interval=0.05
                ):
                    pass
        assert time.monotonic() - started < 2.0

    def test_unix_file_lock_reenters_same_thread(
        self, unix_file_locking_module, test_data_dir
    ):
        """Same-thread nested locks must not flock a second fd (Linux deadlock)."""
        target = Path(test_data_dir) / "unix_reentry.json"
        holders: set[int] = set()

        def _flock(fd, flags):
            if flags & unix_file_locking_module.fcntl.LOCK_UN:
                holders.discard(fd)
                return None
            if holders and fd not in holders:
                raise OSError("busy")
            holders.add(fd)
            return None

        unix_file_locking_module.fcntl.flock = _flock
        with unix_file_locking_module.file_lock(str(target), timeout=0.5, retry_interval=0.01) as outer:
            assert outer is not None
            with unix_file_locking_module.file_lock(
                str(target), timeout=0.5, retry_interval=0.01
            ) as inner:
                inner.seek(0)
                inner.write(b"{}")
                assert inner.tell() == 2

    def test_unix_file_lock_timeout_in_outer_open_loop(self, unix_file_locking_module, test_data_dir):
        target = Path(test_data_dir) / "unix_open_timeout.json"

        # Exercise outer OSError retry/timeout branch around opening the file.
        with patch("builtins.open", side_effect=OSError("open failed")):
            with pytest.raises(TimeoutError, match="Could not acquire lock"):
                with unix_file_locking_module.file_lock(
                    str(target), timeout=0.0, retry_interval=0.0
                ):
                    pass
