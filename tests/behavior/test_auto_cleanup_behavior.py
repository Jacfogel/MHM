"""
Behavior tests for auto_cleanup module.

Tests real behavior and side effects for automated Python cache cleanup functionality.
Focuses on file system operations, timestamp tracking, and cleanup logic.
"""

import pytest
import os
import json
import time
import shutil
from pathlib import Path
from unittest.mock import patch, Mock
from datetime import datetime, timedelta

# Add project root to path
project_root = Path(__file__).parent.parent
import sys
sys.path.insert(0, str(project_root))

from core.auto_cleanup import (
    get_last_cleanup_timestamp,
    update_cleanup_timestamp,
    should_run_cleanup,
    find_pycache_dirs,
    find_pyc_files,
    calculate_cache_size,
    perform_cleanup,
    auto_cleanup_if_needed,
    get_cleanup_status,
    CLEANUP_TRACKER_FILE,
    DEFAULT_CLEANUP_INTERVAL_DAYS
)

class TestAutoCleanupTimestampBehavior:
    """Test timestamp tracking functionality with real behavior verification."""
    
    @pytest.fixture
    def temp_tracker_file(self, test_data_dir):
        """Create temporary tracker file for testing."""
        tracker_path = Path(test_data_dir) / CLEANUP_TRACKER_FILE
        yield tracker_path
        # Cleanup
        if tracker_path.exists():
            tracker_path.unlink()
    
    @pytest.mark.behavior
    @pytest.mark.file_io
    @pytest.mark.critical
    @pytest.mark.regression
    def test_get_last_cleanup_timestamp_no_file_real_behavior(self, temp_tracker_file):
        """REAL BEHAVIOR TEST: Test getting timestamp when no tracker file exists."""
        # ✅ VERIFY REAL BEHAVIOR: No file exists initially
        assert not temp_tracker_file.exists(), "Tracker file should not exist initially"
        
        # ✅ VERIFY REAL BEHAVIOR: Returns 0 when no file exists
        with patch('core.auto_cleanup.CLEANUP_TRACKER_FILE', str(temp_tracker_file)):
            timestamp = get_last_cleanup_timestamp()
            assert timestamp == 0, "Should return 0 when no tracker file exists"
    
    @pytest.mark.behavior
    @pytest.mark.file_io
    @pytest.mark.critical
    @pytest.mark.regression
    def test_get_last_cleanup_timestamp_with_file_real_behavior(self, temp_tracker_file):
        """REAL BEHAVIOR TEST: Test getting timestamp from existing tracker file."""
        # ✅ VERIFY REAL BEHAVIOR: Create test tracker file
        test_timestamp = time.time()
        test_data = {
            'last_cleanup_timestamp': test_timestamp,
            'last_cleanup_date': datetime.now().isoformat()
        }
        
        with open(temp_tracker_file, 'w') as f:
            json.dump(test_data, f)
        
        assert temp_tracker_file.exists(), "Tracker file should be created"
        
        # ✅ VERIFY REAL BEHAVIOR: Returns correct timestamp
        with patch('core.auto_cleanup.CLEANUP_TRACKER_FILE', str(temp_tracker_file)):
            timestamp = get_last_cleanup_timestamp()
            assert timestamp == test_timestamp, "Should return correct timestamp from file"
    
    @pytest.mark.behavior
    @pytest.mark.file_io
    @pytest.mark.critical
    @pytest.mark.regression
    def test_update_cleanup_timestamp_real_behavior(self, temp_tracker_file):
        """REAL BEHAVIOR TEST: Test updating cleanup timestamp creates file with correct data."""
        # ✅ VERIFY REAL BEHAVIOR: No file exists initially
        assert not temp_tracker_file.exists(), "Tracker file should not exist initially"
        
        # ✅ VERIFY REAL BEHAVIOR: Update timestamp creates file
        with patch('core.auto_cleanup.CLEANUP_TRACKER_FILE', str(temp_tracker_file)):
            update_cleanup_timestamp()
        
        assert temp_tracker_file.exists(), "Tracker file should be created"
        
        # ✅ VERIFY REAL BEHAVIOR: File contains correct data structure
        with open(temp_tracker_file, 'r') as f:
            data = json.load(f)
        
        assert 'last_cleanup_timestamp' in data, "Should contain timestamp"
        assert 'last_cleanup_date' in data, "Should contain date"
        assert isinstance(data['last_cleanup_timestamp'], (int, float)), "Timestamp should be numeric"
        assert isinstance(data['last_cleanup_date'], str), "Date should be string"

class TestAutoCleanupLogicBehavior:
    """Test cleanup logic and decision making with real behavior verification."""
    
    @pytest.fixture
    def temp_tracker_file(self, test_data_dir):
        """Create temporary tracker file for testing."""
        tracker_path = Path(test_data_dir) / CLEANUP_TRACKER_FILE
        yield tracker_path
        # Cleanup
        if tracker_path.exists():
            tracker_path.unlink()
    
    @pytest.mark.behavior
    @pytest.mark.file_io
    @pytest.mark.critical
    @pytest.mark.regression
    def test_should_run_cleanup_never_cleaned_real_behavior(self, temp_tracker_file):
        """REAL BEHAVIOR TEST: Test cleanup decision when never cleaned before."""
        # ✅ VERIFY REAL BEHAVIOR: No tracker file exists
        assert not temp_tracker_file.exists(), "Tracker file should not exist"
        
        # ✅ VERIFY REAL BEHAVIOR: Should run cleanup when never cleaned
        with patch('core.auto_cleanup.CLEANUP_TRACKER_FILE', str(temp_tracker_file)):
            should_cleanup = should_run_cleanup()
            assert should_cleanup is True, "Should run cleanup when never cleaned before"
    
    @pytest.mark.behavior
    @pytest.mark.file_io
    @pytest.mark.critical
    @pytest.mark.regression
    def test_should_run_cleanup_recent_cleanup_real_behavior(self, temp_tracker_file):
        """REAL BEHAVIOR TEST: Test cleanup decision when recently cleaned."""
        # ✅ VERIFY REAL BEHAVIOR: Create recent timestamp
        recent_timestamp = time.time() - (1 * 24 * 60 * 60)  # 1 day ago
        test_data = {
            'last_cleanup_timestamp': recent_timestamp,
            'last_cleanup_date': datetime.fromtimestamp(recent_timestamp).isoformat()
        }
        
        with open(temp_tracker_file, 'w') as f:
            json.dump(test_data, f)
        
        # ✅ VERIFY REAL BEHAVIOR: Should not run cleanup when recently cleaned
        with patch('core.auto_cleanup.CLEANUP_TRACKER_FILE', str(temp_tracker_file)):
            should_cleanup = should_run_cleanup()
            assert should_cleanup is False, "Should not run cleanup when recently cleaned"
    
    @pytest.mark.behavior
    @pytest.mark.file_io
    @pytest.mark.critical
    @pytest.mark.regression
    def test_should_run_cleanup_old_cleanup_real_behavior(self, temp_tracker_file):
        """REAL BEHAVIOR TEST: Test cleanup decision when last cleanup was old."""
        # ✅ VERIFY REAL BEHAVIOR: Create old timestamp
        old_timestamp = time.time() - (35 * 24 * 60 * 60)  # 35 days ago
        test_data = {
            'last_cleanup_timestamp': old_timestamp,
            'last_cleanup_date': datetime.fromtimestamp(old_timestamp).isoformat()
        }
        
        with open(temp_tracker_file, 'w') as f:
            json.dump(test_data, f)
        
        # ✅ VERIFY REAL BEHAVIOR: Should run cleanup when old cleanup
        with patch('core.auto_cleanup.CLEANUP_TRACKER_FILE', str(temp_tracker_file)):
            should_cleanup = should_run_cleanup()
            assert should_cleanup is True, "Should run cleanup when last cleanup was old"
    
    @pytest.mark.behavior
    @pytest.mark.file_io
    @pytest.mark.critical
    @pytest.mark.regression
    def test_should_run_cleanup_custom_interval_real_behavior(self, temp_tracker_file):
        """REAL BEHAVIOR TEST: Test cleanup decision with custom interval."""
        # ✅ VERIFY REAL BEHAVIOR: Create timestamp at custom interval boundary
        custom_interval = 7  # 7 days
        boundary_timestamp = time.time() - (custom_interval * 24 * 60 * 60)
        test_data = {
            'last_cleanup_timestamp': boundary_timestamp,
            'last_cleanup_date': datetime.fromtimestamp(boundary_timestamp).isoformat()
        }
        
        with open(temp_tracker_file, 'w') as f:
            json.dump(test_data, f)
        
        # ✅ VERIFY REAL BEHAVIOR: Should run cleanup at custom interval boundary
        with patch('core.auto_cleanup.CLEANUP_TRACKER_FILE', str(temp_tracker_file)):
            should_cleanup = should_run_cleanup(interval_days=custom_interval)
            assert should_cleanup is True, "Should run cleanup at custom interval boundary"

class TestAutoCleanupFileDiscoveryBehavior:
    """Test file discovery functionality with real behavior verification."""
    
    @pytest.fixture
    def temp_test_dir(self, test_data_dir):
        """Create temporary test directory with cache files."""
        test_dir = Path(test_data_dir) / "cache_test"
        test_dir.mkdir(exist_ok=True)
        
        # Create some __pycache__ directories
        pycache1 = test_dir / "__pycache__"
        pycache1.mkdir(exist_ok=True)
        (pycache1 / "test.pyc").write_text("test")
        
        pycache2 = test_dir / "subdir" / "__pycache__"
        pycache2.mkdir(parents=True, exist_ok=True)
        (pycache2 / "subtest.pyc").write_text("subtest")
        
        # Create some standalone .pyc files
        (test_dir / "standalone.pyc").write_text("standalone")
        (test_dir / "subdir" / "another.pyc").write_text("another")
        
        yield test_dir
        
        # Cleanup
        shutil.rmtree(test_dir, ignore_errors=True)
    
    @pytest.mark.behavior
    @pytest.mark.file_io
    @pytest.mark.critical
    @pytest.mark.regression
    def test_find_pycache_dirs_real_behavior(self, temp_test_dir):
        """REAL BEHAVIOR TEST: Test finding __pycache__ directories."""
        # ✅ VERIFY REAL BEHAVIOR: Find all __pycache__ directories
        pycache_dirs = find_pycache_dirs(temp_test_dir)
        
        assert len(pycache_dirs) == 2, "Should find 2 __pycache__ directories"
        
        # ✅ VERIFY REAL BEHAVIOR: Directories are correct
        dir_paths = [Path(d) for d in pycache_dirs]
        assert temp_test_dir / "__pycache__" in dir_paths, "Should find root __pycache__"
        assert temp_test_dir / "subdir" / "__pycache__" in dir_paths, "Should find subdir __pycache__"
    
    @pytest.mark.behavior
    @pytest.mark.file_io
    @pytest.mark.critical
    @pytest.mark.regression
    def test_find_pyc_files_real_behavior(self, temp_test_dir):
        """REAL BEHAVIOR TEST: Test finding .pyc files."""
        # ✅ VERIFY REAL BEHAVIOR: Find all .pyc files
        pyc_files = find_pyc_files(temp_test_dir)
        
        assert len(pyc_files) == 4, "Should find 4 .pyc files (2 in __pycache__ + 2 standalone)"
        
        # ✅ VERIFY REAL BEHAVIOR: Files are correct
        file_paths = [Path(f) for f in pyc_files]
        assert temp_test_dir / "standalone.pyc" in file_paths, "Should find standalone .pyc"
        assert temp_test_dir / "subdir" / "another.pyc" in file_paths, "Should find subdir .pyc"
    
    @pytest.mark.behavior
    @pytest.mark.file_io
    @pytest.mark.critical
    @pytest.mark.regression
    def test_calculate_cache_size_real_behavior(self, temp_test_dir):
        """REAL BEHAVIOR TEST: Test calculating cache size."""
        # ✅ VERIFY REAL BEHAVIOR: Calculate total cache size
        pycache_dirs = find_pycache_dirs(temp_test_dir)
        pyc_files = find_pyc_files(temp_test_dir)
        
        total_size = calculate_cache_size(pycache_dirs, pyc_files)
        
        # ✅ VERIFY REAL BEHAVIOR: Size is positive and reasonable
        assert total_size > 0, "Cache size should be positive"
        assert total_size < 1024 * 1024, "Cache size should be reasonable (< 1MB for test files)"

class TestAutoCleanupStatusBehavior:
    """Test cleanup status functionality with real behavior verification."""
    
    @pytest.fixture
    def temp_tracker_file(self, test_data_dir):
        """Create temporary tracker file for testing."""
        tracker_path = Path(test_data_dir) / CLEANUP_TRACKER_FILE
        yield tracker_path
        # Cleanup
        if tracker_path.exists():
            tracker_path.unlink()
    
    @pytest.mark.behavior
    @pytest.mark.file_io
    @pytest.mark.critical
    @pytest.mark.regression
    def test_get_cleanup_status_never_cleaned_real_behavior(self, temp_tracker_file):
        """REAL BEHAVIOR TEST: Test status when never cleaned before."""
        # ✅ VERIFY REAL BEHAVIOR: No tracker file exists
        assert not temp_tracker_file.exists(), "Tracker file should not exist"
        
        # ✅ VERIFY REAL BEHAVIOR: Status shows never cleaned
        with patch('core.auto_cleanup.CLEANUP_TRACKER_FILE', str(temp_tracker_file)):
            status = get_cleanup_status()
        
        assert status['last_cleanup'] == 'Never', "Should show never cleaned"
        assert status['days_since'] == float('inf'), "Should show infinite days since"
        assert status['next_cleanup'] == 'On next startup', "Should show next cleanup on startup"
    
    @pytest.mark.behavior
    @pytest.mark.file_io
    @pytest.mark.critical
    @pytest.mark.regression
    def test_get_cleanup_status_recent_cleanup_real_behavior(self, temp_tracker_file):
        """REAL BEHAVIOR TEST: Test status when recently cleaned."""
        # ✅ VERIFY REAL BEHAVIOR: Create recent timestamp
        recent_timestamp = time.time() - (5 * 24 * 60 * 60)  # 5 days ago
        test_data = {
            'last_cleanup_timestamp': recent_timestamp,
            'last_cleanup_date': datetime.fromtimestamp(recent_timestamp).isoformat()
        }
        
        with open(temp_tracker_file, 'w') as f:
            json.dump(test_data, f)
        
        # ✅ VERIFY REAL BEHAVIOR: Status shows recent cleanup
        with patch('core.auto_cleanup.CLEANUP_TRACKER_FILE', str(temp_tracker_file)):
            status = get_cleanup_status()
        
        assert status['last_cleanup'] != 'Never', "Should show cleanup date"
        # Allow for timezone/rounding differences (4-6 days is acceptable for 5-day test)
        assert 4 <= status['days_since'] <= 6, f"Should show correct days since (got {status['days_since']})"
        assert status['next_cleanup'] != 'Overdue', "Should show future cleanup date"
    
    @pytest.mark.behavior
    @pytest.mark.file_io
    @pytest.mark.critical
    @pytest.mark.regression
    def test_get_cleanup_status_overdue_cleanup_real_behavior(self, temp_tracker_file):
        """REAL BEHAVIOR TEST: Test status when cleanup is overdue."""
        # ✅ VERIFY REAL BEHAVIOR: Create old timestamp
        old_timestamp = time.time() - (35 * 24 * 60 * 60)  # 35 days ago
        test_data = {
            'last_cleanup_timestamp': old_timestamp,
            'last_cleanup_date': datetime.fromtimestamp(old_timestamp).isoformat()
        }
        
        with open(temp_tracker_file, 'w') as f:
            json.dump(test_data, f)
        
        # ✅ VERIFY REAL BEHAVIOR: Status shows overdue cleanup
        with patch('core.auto_cleanup.CLEANUP_TRACKER_FILE', str(temp_tracker_file)):
            status = get_cleanup_status()
        
        assert status['last_cleanup'] != 'Never', "Should show cleanup date"
        assert status['days_since'] == 35, "Should show correct days since"
        assert status['next_cleanup'] == 'Overdue', "Should show overdue status"

class TestAutoCleanupIntegrationBehavior:
    """Test integrated cleanup functionality with real behavior verification."""
    
    @pytest.fixture
    def temp_test_environment(self, test_data_dir):
        """Create temporary test environment with cache files and tracker."""
        test_dir = Path(test_data_dir) / "cleanup_integration_test"
        test_dir.mkdir(exist_ok=True)
        
        # Create cache files
        pycache = test_dir / "__pycache__"
        pycache.mkdir(exist_ok=True)
        (pycache / "test.pyc").write_text("test content")
        
        (test_dir / "standalone.pyc").write_text("standalone content")
        
        # Create tracker file
        tracker_path = test_dir / CLEANUP_TRACKER_FILE
        
        yield test_dir, tracker_path
        
        # Cleanup
        shutil.rmtree(test_dir, ignore_errors=True)
    
    @pytest.mark.behavior
    @pytest.mark.file_io
    @pytest.mark.critical
    @pytest.mark.regression
    def test_perform_cleanup_real_behavior(self, temp_test_environment):
        """REAL BEHAVIOR TEST: Test performing actual cleanup."""
        test_dir, tracker_path = temp_test_environment
        
        # ✅ VERIFY REAL BEHAVIOR: Cache files exist initially
        assert (test_dir / "__pycache__").exists(), "__pycache__ should exist initially"
        assert (test_dir / "standalone.pyc").exists(), "standalone.pyc should exist initially"
        
        # ✅ VERIFY REAL BEHAVIOR: Perform cleanup
        with patch('core.auto_cleanup.CLEANUP_TRACKER_FILE', str(tracker_path)):
            success = perform_cleanup(test_dir)
        
        assert success is True, "Cleanup should succeed"
        
        # ✅ VERIFY REAL BEHAVIOR: Cache files are removed
        assert not (test_dir / "__pycache__").exists(), "__pycache__ should be removed"
        assert not (test_dir / "standalone.pyc").exists(), "standalone.pyc should be removed"
    
    @pytest.mark.behavior
    @pytest.mark.file_io
    @pytest.mark.critical
    @pytest.mark.regression
    def test_auto_cleanup_if_needed_real_behavior(self, temp_test_environment):
        """REAL BEHAVIOR TEST: Test automatic cleanup decision and execution."""
        test_dir, tracker_path = temp_test_environment
        
        # ✅ VERIFY REAL BEHAVIOR: No tracker file exists initially
        assert not tracker_path.exists(), "Tracker file should not exist initially"
        
        # ✅ VERIFY REAL BEHAVIOR: Auto cleanup should run and succeed
        with patch('core.auto_cleanup.CLEANUP_TRACKER_FILE', str(tracker_path)):
            result = auto_cleanup_if_needed(test_dir)
        
        assert result is True, "Auto cleanup should be performed"
        
        # ✅ VERIFY REAL BEHAVIOR: Tracker file is created
        assert tracker_path.exists(), "Tracker file should be created after cleanup"
        
        # ✅ VERIFY REAL BEHAVIOR: Cache files are removed
        assert not (test_dir / "__pycache__").exists(), "__pycache__ should be removed"
        assert not (test_dir / "standalone.pyc").exists(), "standalone.pyc should be removed"
    
    @pytest.mark.behavior
    @pytest.mark.file_io
    @pytest.mark.critical
    @pytest.mark.regression
    def test_auto_cleanup_if_needed_not_needed_real_behavior(self, temp_test_environment):
        """REAL BEHAVIOR TEST: Test auto cleanup when not needed."""
        test_dir, tracker_path = temp_test_environment
        
        # ✅ VERIFY REAL BEHAVIOR: Create recent timestamp
        recent_timestamp = time.time() - (1 * 24 * 60 * 60)  # 1 day ago
        test_data = {
            'last_cleanup_timestamp': recent_timestamp,
            'last_cleanup_date': datetime.fromtimestamp(recent_timestamp).isoformat()
        }
        
        with open(tracker_path, 'w') as f:
            json.dump(test_data, f)
        
        # ✅ VERIFY REAL BEHAVIOR: Auto cleanup should not run
        with patch('core.auto_cleanup.CLEANUP_TRACKER_FILE', str(tracker_path)):
            result = auto_cleanup_if_needed(test_dir)
        
        assert result is False, "Auto cleanup should not be performed when not needed"
        
        # ✅ VERIFY REAL BEHAVIOR: Cache files still exist
        assert (test_dir / "__pycache__").exists(), "__pycache__ should still exist"
        assert (test_dir / "standalone.pyc").exists(), "standalone.pyc should still exist" 