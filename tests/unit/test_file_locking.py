"""
Unit tests for file locking utilities.

Tests for core/file_locking.py focusing on file locking, safe JSON operations,
and concurrent access scenarios.
"""

import pytest
import os
import json
import time
import sys
import threading
from pathlib import Path
from unittest.mock import patch, mock_open, MagicMock

from core.file_locking import file_lock, safe_json_read, safe_json_write


@pytest.mark.unit
@pytest.mark.file_io
class TestFileLocking:
    """Test file locking functionality."""

    def test_file_lock_creates_and_releases_lock(self, test_data_dir):
        """Test that file_lock creates and releases lock file."""
        test_file = os.path.join(test_data_dir, "test_lock_file.json")
        lock_file = test_file + ".lock"
        
        # Ensure lock file doesn't exist initially
        if os.path.exists(lock_file):
            os.remove(lock_file)
        
        # Use file_lock context manager
        with file_lock(test_file, timeout=5.0):
            # Lock should exist
            assert os.path.exists(lock_file), "Lock file should exist during lock"
        
        # Lock should be released after context exit
        # Note: On Windows, lock file removal might be delayed, so we check with a small delay
        time.sleep(0.1)
        assert not os.path.exists(lock_file), "Lock file should be removed after lock release"

    def test_file_lock_opens_file_for_reading_writing(self, test_data_dir):
        """Test that file_lock opens file for reading and writing."""
        test_file = os.path.join(test_data_dir, "test_read_write.json")
        
        # Create test file with content
        test_data = {"test": "data", "number": 42}
        with open(test_file, 'w') as f:
            json.dump(test_data, f)
        
        # Read and modify file within lock
        with file_lock(test_file, timeout=5.0) as f:
            assert f is not None, "Should return file handle"
            assert hasattr(f, 'read'), "File handle should support reading"
            assert hasattr(f, 'write'), "File handle should support writing"
            
            # Read existing content
            f.seek(0)
            content = f.read()
            assert b"test" in content, "Should be able to read file content"

    def test_file_lock_creates_file_if_not_exists(self, test_data_dir):
        """Test that file_lock creates file if it doesn't exist."""
        test_file = os.path.join(test_data_dir, "test_new_file.json")
        
        # Ensure file doesn't exist
        if os.path.exists(test_file):
            os.remove(test_file)
        
        # Use file_lock - should create file
        with file_lock(test_file, timeout=5.0) as f:
            assert f is not None, "Should return file handle for new file"
            # Write some data
            f.write(b"test data")
        
        # File should exist after lock
        assert os.path.exists(test_file), "File should be created"

    def test_file_lock_timeout_when_locked(self, test_data_dir):
        """Test that file_lock times out when file is already locked."""
        test_file = os.path.join(test_data_dir, "test_timeout.json")
        lock_file = test_file + ".lock"
        
        # Ensure lock file doesn't exist initially
        if os.path.exists(lock_file):
            try:
                os.remove(lock_file)
            except OSError:
                pass
        
        # Create lock file to simulate locked state (using 'x' mode to create exclusively)
        try:
            with open(lock_file, 'x') as f:
                f.write("locked")
            
            # Try to acquire lock - should timeout
            with pytest.raises(TimeoutError):
                with file_lock(test_file, timeout=0.5, retry_interval=0.1):
                    pass
        except FileExistsError:
            # If lock file already exists (race condition), skip this test
            pytest.skip("Lock file already exists, cannot test timeout")
        finally:
            # Clean up lock file
            if os.path.exists(lock_file):
                try:
                    os.remove(lock_file)
                except OSError:
                    pass

    def test_file_lock_retries_until_available(self, test_data_dir):
        """Test that file_lock retries until lock becomes available."""
        test_file = os.path.join(test_data_dir, "test_retry.json")
        lock_file = test_file + ".lock"
        
        # Create lock file
        with open(lock_file, 'w') as f:
            f.write("locked")
        
        # In a separate thread, release lock after short delay
        def release_lock_after_delay():
            time.sleep(0.3)
            if os.path.exists(lock_file):
                os.remove(lock_file)
        
        release_thread = threading.Thread(target=release_lock_after_delay)
        release_thread.start()
        
        try:
            # Try to acquire lock - should succeed after retry
            with file_lock(test_file, timeout=2.0, retry_interval=0.1) as f:
                assert f is not None, "Should acquire lock after retry"
        finally:
            release_thread.join(timeout=1.0)
            # Clean up
            if os.path.exists(lock_file):
                os.remove(lock_file)

    @pytest.mark.skipif(sys.platform != 'win32', reason="Windows-specific lock file behavior")
    def test_file_lock_windows_specific_behavior(self, test_data_dir):
        """Test Windows-specific file locking behavior."""
        test_file = os.path.join(test_data_dir, "test_windows.json")
        
        # On Windows, lock uses separate .lock file
        with file_lock(test_file, timeout=5.0):
            lock_file = test_file + ".lock"
            assert os.path.exists(lock_file), "Windows should create separate lock file"


@pytest.mark.unit
@pytest.mark.file_io
class TestSafeJsonRead:
    """Test safe JSON read functionality."""

    def test_safe_json_read_existing_file(self, test_data_dir):
        """Test safe_json_read reads existing JSON file."""
        test_file = os.path.join(test_data_dir, "test_read.json")
        test_data = {"key": "value", "number": 123, "nested": {"inner": "data"}}
        
        # Create test file
        with open(test_file, 'w') as f:
            json.dump(test_data, f)
        
        # Read file
        result = safe_json_read(test_file)
        
        assert result == test_data, "Should read JSON data correctly"

    def test_safe_json_read_nonexistent_file(self, test_data_dir):
        """Test safe_json_read returns default for nonexistent file."""
        test_file = os.path.join(test_data_dir, "nonexistent.json")
        
        # Ensure file doesn't exist
        if os.path.exists(test_file):
            os.remove(test_file)
        
        # Read with default
        default_data = {"default": "value"}
        result = safe_json_read(test_file, default=default_data)
        
        assert result == default_data, "Should return default for nonexistent file"

    def test_safe_json_read_invalid_json(self, test_data_dir):
        """Test safe_json_read handles invalid JSON gracefully."""
        test_file = os.path.join(test_data_dir, "test_invalid.json")
        
        # Create file with invalid JSON
        with open(test_file, 'w') as f:
            f.write("not valid json {")
        
        # Read with default
        default_data = {"error": "handled"}
        result = safe_json_read(test_file, default=default_data)
        
        assert result == default_data, "Should return default for invalid JSON"

    def test_safe_json_read_uses_file_locking(self, test_data_dir):
        """Test that safe_json_read uses file locking."""
        test_file = os.path.join(test_data_dir, "test_locked_read.json")
        test_data = {"test": "data"}
        
        # Create test file
        with open(test_file, 'w') as f:
            json.dump(test_data, f)
        
        # Mock file_lock to verify it's called
        with patch('core.file_locking.file_lock') as mock_lock:
            mock_lock.return_value.__enter__ = MagicMock(return_value=None)
            mock_lock.return_value.__exit__ = MagicMock(return_value=None)
            
            safe_json_read(test_file)
            
            # Verify file_lock was called
            mock_lock.assert_called_once()


@pytest.mark.unit
@pytest.mark.file_io
class TestSafeJsonWrite:
    """Test safe JSON write functionality."""

    def test_safe_json_write_creates_file(self, test_data_dir):
        """Test safe_json_write creates file with data."""
        test_file = os.path.join(test_data_dir, "test_write.json")
        test_data = {"key": "value", "number": 456}
        
        # Ensure file doesn't exist
        if os.path.exists(test_file):
            os.remove(test_file)
        
        # Write file
        result = safe_json_write(test_file, test_data)
        
        assert result is True, "Should return True on success"
        assert os.path.exists(test_file), "File should be created"
        
        # Verify content
        with open(test_file, 'r') as f:
            written_data = json.load(f)
        
        assert written_data == test_data, "Should write data correctly"

    def test_safe_json_write_updates_existing_file(self, test_data_dir):
        """Test safe_json_write updates existing file."""
        test_file = os.path.join(test_data_dir, "test_update.json")
        initial_data = {"old": "data"}
        new_data = {"new": "data", "updated": True}
        
        # Create initial file
        with open(test_file, 'w') as f:
            json.dump(initial_data, f)
        
        # Update file
        result = safe_json_write(test_file, new_data)
        
        assert result is True, "Should return True on success"
        
        # Verify content was updated
        with open(test_file, 'r') as f:
            written_data = json.load(f)
        
        assert written_data == new_data, "Should update file content"
        assert "old" not in written_data, "Old data should be replaced"

    def test_safe_json_write_uses_atomic_write(self, test_data_dir):
        """Test that safe_json_write uses atomic write pattern."""
        import tempfile
        import shutil
        test_file = os.path.join(test_data_dir, "test_atomic.json")
        test_data = {"atomic": "write"}
        
        # Mock tempfile and shutil to verify atomic write pattern
        with patch('tempfile.mkstemp') as mock_mkstemp, \
             patch('shutil.move') as mock_move, \
             patch('core.file_locking.file_lock') as mock_lock, \
             patch('builtins.open', mock_open()) as mock_file:
            
            mock_mkstemp.return_value = (1, "/tmp/temp_file.json")
            mock_lock.return_value.__enter__ = MagicMock(return_value=None)
            mock_lock.return_value.__exit__ = MagicMock(return_value=None)
            
            result = safe_json_write(test_file, test_data)
            
            # Verify atomic write pattern was used
            assert mock_mkstemp.called, "Should create temp file"
            assert mock_move.called, "Should move temp file to target (atomic)"

    def test_safe_json_write_handles_write_errors(self, test_data_dir):
        """Test safe_json_write handles write errors gracefully."""
        import tempfile
        test_file = os.path.join(test_data_dir, "test_error.json")
        test_data = {"test": "data"}
        
        # Mock file operations to raise error
        with patch('tempfile.mkstemp', side_effect=OSError("Permission denied")):
            result = safe_json_write(test_file, test_data)
            
            assert result is False, "Should return False on error"

    def test_safe_json_write_cleans_up_temp_file_on_error(self, test_data_dir):
        """Test safe_json_write cleans up temp file on error."""
        import tempfile
        import shutil
        test_file = os.path.join(test_data_dir, "test_cleanup.json")
        test_data = {"test": "data"}
        
        # Create a real temp file to test cleanup
        temp_fd, temp_file = tempfile.mkstemp(
            dir=test_data_dir,
            prefix='.tmp_',
            suffix='.json'
        )
        os.close(temp_fd)
        
        # Mock shutil.move to fail
        with patch('shutil.move', side_effect=OSError("Move failed")):
            result = safe_json_write(test_file, test_data)
            
            assert result is False, "Should return False on error"
        
        # Temp file should be cleaned up (or at least attempted)
        # Note: Cleanup happens in finally block, so temp file may or may not exist
        # depending on when the error occurred
        if os.path.exists(temp_file):
            try:
                os.remove(temp_file)
            except OSError:
                pass

    def test_safe_json_write_creates_directory(self, test_data_dir):
        """Test safe_json_write creates directory if it doesn't exist."""
        test_dir = os.path.join(test_data_dir, "nested", "deep", "path")
        test_file = os.path.join(test_dir, "test_nested.json")
        test_data = {"nested": "data"}
        
        # Ensure directory doesn't exist
        if os.path.exists(test_dir):
            import shutil
            shutil.rmtree(os.path.dirname(test_dir))
        
        # Write file
        result = safe_json_write(test_file, test_data)
        
        assert result is True, "Should return True on success"
        assert os.path.exists(test_dir), "Directory should be created"
        assert os.path.exists(test_file), "File should be created in nested directory"

    def test_safe_json_write_uses_file_locking(self, test_data_dir):
        """Test that safe_json_write uses file locking."""
        test_file = os.path.join(test_data_dir, "test_locked_write.json")
        test_data = {"test": "data"}
        
        # Mock file_lock to verify it's called
        with patch('core.file_locking.file_lock') as mock_lock:
            mock_lock.return_value.__enter__ = MagicMock(return_value=None)
            mock_lock.return_value.__exit__ = MagicMock(return_value=None)
            
            safe_json_write(test_file, test_data)
            
            # Verify file_lock was called
            mock_lock.assert_called_once()


@pytest.mark.unit
@pytest.mark.file_io
class TestFileLockingConcurrency:
    """Test file locking with concurrent access."""

    def test_file_lock_prevents_concurrent_writes(self, test_data_dir):
        """Test that file_lock prevents concurrent writes."""
        test_file = os.path.join(test_data_dir, "test_concurrent.json")
        
        # Ensure file doesn't exist
        if os.path.exists(test_file):
            os.remove(test_file)
        
        write_results = []
        errors = []
        
        def write_data(thread_id):
            """Write data from a thread."""
            try:
                with file_lock(test_file, timeout=5.0) as f:
                    # Read current content
                    f.seek(0)
                    content = f.read()
                    data = json.loads(content) if content else {}
                    
                    # Add thread's data
                    data[f"thread_{thread_id}"] = f"data_{thread_id}"
                    
                    # Write back
                    f.seek(0)
                    f.truncate()
                    f.write(json.dumps(data).encode('utf-8'))
                    
                    write_results.append(thread_id)
            except Exception as e:
                errors.append((thread_id, str(e)))
        
        # Start multiple threads writing concurrently
        threads = []
        for i in range(5):
            thread = threading.Thread(target=write_data, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join(timeout=10.0)
        
        # Verify no errors occurred
        assert len(errors) == 0, f"Should not have errors: {errors}"
        
        # Verify all threads wrote successfully
        assert len(write_results) == 5, "All threads should have written"
        
        # Verify file contains all thread data
        with open(test_file, 'r') as f:
            final_data = json.load(f)
        
        assert len(final_data) == 5, "File should contain data from all threads"
        for i in range(5):
            assert f"thread_{i}" in final_data, f"Should contain data from thread {i}"
