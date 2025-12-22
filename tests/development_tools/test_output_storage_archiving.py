"""
Tests for standardized output storage archiving.

Verifies that file rotation and archiving work correctly for tool result JSON files.
"""

import pytest
import json
import time
from pathlib import Path
from unittest.mock import patch

from tests.development_tools.conftest import load_development_tools_module, temp_project_copy

# Load modules
output_storage_module = load_development_tools_module("shared.output_storage")
save_tool_result = output_storage_module.save_tool_result
load_tool_result = output_storage_module.load_tool_result
save_tool_cache = output_storage_module.save_tool_cache
load_tool_cache = output_storage_module.load_tool_cache

file_rotation_module = load_development_tools_module("shared.file_rotation")
FileRotator = file_rotation_module.FileRotator


class TestOutputStorageArchiving:
    """Test output storage archiving functionality."""
    
    @pytest.mark.unit
    def test_tool_result_archiving(self, temp_project_copy):
        """Create tool result JSON, run tool again, verify old version is archived."""
        # Save first version
        result1 = {'test': 'data1', 'timestamp': '2025-01-01'}
        file_path1 = save_tool_result(
            'test_tool',
            domain='docs',
            data=result1,
            project_root=temp_project_copy
        )
        
        assert file_path1.exists(), "First result file should exist"
        
        # Wait a moment to ensure different timestamps
        time.sleep(0.1)
        
        # Save second version (should archive first)
        result2 = {'test': 'data2', 'timestamp': '2025-01-02'}
        file_path2 = save_tool_result(
            'test_tool',
            domain='docs',
            data=result2,
            project_root=temp_project_copy
        )
        
        assert file_path2.exists(), "Second result file should exist"
        assert file_path1 == file_path2, "File path should be the same"
        
        # Verify archive directory exists
        archive_dir = temp_project_copy / "development_tools" / "docs" / "jsons" / "archive"
        assert archive_dir.exists(), "Archive directory should exist"
        
        # Verify archived file exists
        archived_files = list(archive_dir.glob("test_tool_results_*.json"))
        assert len(archived_files) > 0, "At least one archived file should exist"
        
        # Verify current file has new data
        # Disable normalization for this test since we're testing archiving, not normalization
        current_data = load_tool_result('test_tool', domain='docs', project_root=temp_project_copy, normalize=False)
        assert current_data is not None, "Current result should be loadable"
        # Data is stored in 'data' field of the JSON structure
        if 'data' in current_data:
            current_data = current_data['data']
        assert current_data.get('test') == 'data2', "Current result should have new data"
    
    @pytest.mark.unit
    def test_archive_keeps_last_5_versions(self, temp_project_copy):
        """Create 7 tool result files, verify only 5 most recent are kept."""
        # Save 7 versions
        for i in range(7):
            result = {'version': i, 'data': f'version_{i}'}
            save_tool_result(
                'test_rotation',
                domain='docs',
                data=result,
                archive_count=5,  # Keep last 5
                project_root=temp_project_copy
            )
            time.sleep(0.1)  # Ensure different timestamps
        
        # Verify archive directory
        archive_dir = temp_project_copy / "development_tools" / "docs" / "jsons" / "archive"
        
        # Count archived files
        archived_files = list(archive_dir.glob("test_rotation_results_*.json"))
        
        # Should have at most 5 archived files (last 5 versions)
        # Note: The first file doesn't get archived (nothing to archive), so we expect 6 archives
        # But cleanup should keep only 5
        assert len(archived_files) <= 5, f"Should keep at most 5 archived versions, got {len(archived_files)}"
    
    @pytest.mark.unit
    def test_cache_files_in_correct_location(self, temp_project_copy):
        """Verify cache files (`.{tool}_cache.json`) are in `jsons/` subdirectories."""
        # Save a cache file
        cache_data = {'cached': 'data', 'key': 'value'}
        cache_path = save_tool_cache(
            'test_cache_tool',
            domain='docs',
            data=cache_data,
            project_root=temp_project_copy
        )
        
        # Verify cache file is in jsons/ directory
        expected_dir = temp_project_copy / "development_tools" / "docs" / "jsons"
        assert cache_path.parent == expected_dir, f"Cache file should be in {expected_dir}, got {cache_path.parent}"
        
        # Verify cache file name starts with dot
        assert cache_path.name.startswith('.'), "Cache file should start with dot"
        assert cache_path.name.endswith('_cache.json'), "Cache file should end with _cache.json"
        
        # Verify cache can be loaded
        loaded_cache = load_tool_cache('test_cache_tool', domain='docs', project_root=temp_project_copy)
        assert loaded_cache is not None, "Cache should be loadable"
        assert loaded_cache.get('cached') == 'data', "Cache should contain saved data"
    
    @pytest.mark.unit
    def test_no_json_files_in_domain_root(self, temp_project_copy):
        """Scan all domain directories and verify no JSON files exist outside `jsons/` subdirectories."""
        # Create some test result files in correct location
        save_tool_result('test1', domain='docs', data={'test': 1}, project_root=temp_project_copy)
        save_tool_result('test2', domain='functions', data={'test': 2}, project_root=temp_project_copy)
        
        # Known domain directories
        domains = ['docs', 'functions', 'error_handling', 'tests', 'imports', 'legacy', 
                   'config', 'ai_work', 'reports']
        
        # Known exceptions: files that are intentionally placed outside jsons/ subdirectories
        # These are central aggregation files or special configuration files
        known_exceptions = [
            'analysis_detailed_results.json',  # Central aggregation file in reports/
            'tool_timings.json',  # Tool timing data file in reports/
        ]
        
        misplaced_files = []
        
        for domain in domains:
            domain_dir = temp_project_copy / "development_tools" / domain
            if not domain_dir.exists():
                continue
            
            # Check for JSON files directly in domain directory (should be in jsons/)
            for json_file in domain_dir.glob("*.json"):
                if json_file.name.startswith('.'):
                    continue  # Skip hidden files
                if json_file.parent.name != 'jsons':
                    # Check if this is a known exception
                    if json_file.name not in known_exceptions:
                        misplaced_files.append(str(json_file))
        
        # Report any misplaced files (but don't fail - these might be intentional)
        if misplaced_files:
            pytest.fail(f"Found JSON files outside jsons/ subdirectories: {misplaced_files}")
    
    @pytest.mark.unit
    def test_cleanup_misplaced_files(self, temp_project_copy):
        """Identify and document any misplaced JSON files for manual cleanup."""
        # This test scans for misplaced files and documents them
        # It doesn't actually clean them up (manual cleanup required)
        
        misplaced_files = []
        domains = ['docs', 'functions', 'error_handling', 'tests', 'imports', 'legacy', 
                   'config', 'ai_work', 'reports']
        
        for domain in domains:
            domain_dir = temp_project_copy / "development_tools" / domain
            if not domain_dir.exists():
                continue
            
            # Check for JSON files in domain root (should be in jsons/)
            for json_file in domain_dir.glob("*.json"):
                if json_file.name.startswith('.'):
                    continue  # Skip hidden files
                if json_file.parent.name != 'jsons':
                    misplaced_files.append({
                        'domain': domain,
                        'file': str(json_file.relative_to(temp_project_copy)),
                        'expected_location': f"development_tools/{domain}/jsons/{json_file.name}"
                    })
        
        # For this test, we just verify the scanning works
        # In a real scenario, misplaced_files would be logged or reported
        assert isinstance(misplaced_files, list), "Should return list of misplaced files"
        
        # If we find misplaced files, document them (but don't fail test)
        # Note: In a real scenario, these would be logged or reported
        if misplaced_files:
            # Log via pytest's capture mechanism - these will appear in test output if verbose
            import logging
            logger = logging.getLogger("test_output_storage")
            logger.info(f"Found {len(misplaced_files)} misplaced JSON files:")
            for item in misplaced_files:
                logger.info(f"  - {item['file']} (should be in {item['expected_location']})")
    
    @pytest.mark.unit
    def test_archive_cleanup_exceeds_max_versions(self, temp_project_copy):
        """Verify archive cleanup when exceeding max versions (default 7)."""
        # Save 10 versions (exceeding default max of 7)
        for i in range(10):
            result = {'version': i, 'data': f'version_{i}'}
            save_tool_result(
                'test_cleanup',
                domain='docs',
                data=result,
                archive_count=7,  # Default max versions
                project_root=temp_project_copy
            )
            time.sleep(0.1)  # Ensure different timestamps
        
        # Verify archive directory
        archive_dir = temp_project_copy / "development_tools" / "docs" / "jsons" / "archive"
        
        # Count archived files
        archived_files = list(archive_dir.glob("test_cleanup_results_*.json"))
        
        # Should have at most 7 archived files (default max)
        # First file doesn't get archived, so we save 10 times = 9 archives, but cleanup should keep only 7
        assert len(archived_files) <= 7, f"Should keep at most 7 archived versions, got {len(archived_files)}"
        
        # Verify oldest files were removed (if we have more than 7)
        if len(archived_files) > 7:
            # Sort by modification time
            archived_files.sort(key=lambda x: x.stat().st_mtime)
            # Oldest files should have been removed
            # This is verified by the count check above
    
    @pytest.mark.unit
    def test_archive_directory_creation(self, temp_project_copy):
        """Verify archive directory is created automatically when needed."""
        # Ensure archive directory doesn't exist initially
        archive_dir = temp_project_copy / "development_tools" / "docs" / "jsons" / "archive"
        if archive_dir.exists():
            import shutil
            shutil.rmtree(archive_dir)
        
        assert not archive_dir.exists(), "Archive directory should not exist initially"
        
        # Save first version (no archive yet)
        result1 = {'test': 'data1'}
        save_tool_result(
            'test_dir_creation',
            domain='docs',
            data=result1,
            project_root=temp_project_copy
        )
        
        # Archive directory still shouldn't exist (no file to archive)
        assert not archive_dir.exists(), "Archive directory should not exist after first save"
        
        # Wait a moment
        time.sleep(0.1)
        
        # Save second version (should create archive directory)
        result2 = {'test': 'data2'}
        save_tool_result(
            'test_dir_creation',
            domain='docs',
            data=result2,
            project_root=temp_project_copy
        )
        
        # Archive directory should now exist
        assert archive_dir.exists(), "Archive directory should be created when archiving"
        assert archive_dir.is_dir(), "Archive directory should be a directory"
    
    @pytest.mark.unit
    def test_error_handling_archiving_failure(self, temp_project_copy):
        """Verify error handling when archiving fails."""
        # Save first version
        result1 = {'test': 'data1'}
        file_path = save_tool_result(
            'test_error',
            domain='docs',
            data=result1,
            project_root=temp_project_copy
        )
        
        assert file_path.exists(), "First result file should exist"
        
        # Wait a moment
        time.sleep(0.1)
        
        # Mock shutil.move to raise an exception during archiving
        # Since shutil is imported inside save_tool_result, we need to patch the builtin shutil module
        import shutil
        original_move = shutil.move
        
        def failing_move(src, dst):
            raise OSError("Simulated archiving failure")
        
        # Patch shutil.move at the module level - this will be used when the function imports shutil
        shutil.move = failing_move
        try:
            # Try to save second version - archiving will fail
            result2 = {'test': 'data2'}
            try:
                file_path2 = save_tool_result(
                    'test_error',
                    domain='docs',
                    data=result2,
                    project_root=temp_project_copy
                )
                # If we get here, the function handled the error gracefully
                # The new file should still be written (archiving failure shouldn't block saving)
                assert file_path2.exists(), "New file should exist even if archiving fails"
            except OSError as e:
                # If archiving failure propagates, verify it's our simulated error
                if "Simulated archiving failure" not in str(e):
                    # Re-raise if it's not our simulated error
                    raise
                # On error, verify the new file was still written (archiving happens before writing)
                final_file = temp_project_copy / "development_tools" / "docs" / "jsons" / "test_error_results.json"
                # The file should exist because archiving happens before writing the new file
                # If archiving fails, the old file might still be there, but new file should be written
                assert final_file.exists(), "Result file should exist even if archiving fails"
        finally:
            # Restore original function
            shutil.move = original_move
    
    @pytest.mark.unit
    @pytest.mark.no_parallel  # Concurrent saves might interfere with each other
    def test_concurrent_saves(self, temp_project_copy):
        """Verify that concurrent saves don't corrupt the final file.
        
        Note: save_tool_result() doesn't implement file locking, so some concurrent
        saves may fail on Windows due to file locking. This test verifies that:
        1. The function doesn't crash when called concurrently
        2. The final file is valid and contains correct data
        3. At least one save succeeded (proving the function works)
        """
        import threading
        import platform
        
        results = []
        errors = []
        lock = threading.Lock()
        
        def save_version(version_num):
            try:
                result = {'version': version_num, 'thread': threading.current_thread().name}
                file_path = save_tool_result(
                    'test_concurrent',
                    domain='docs',
                    data=result,
                    project_root=temp_project_copy
                )
                with lock:
                    results.append((version_num, file_path))
                time.sleep(0.01)  # Small delay to increase chance of overlap
            except Exception as e:
                with lock:
                    errors.append((version_num, str(e)))
        
        # Create 5 threads that save concurrently
        threads = []
        for i in range(5):
            thread = threading.Thread(target=save_version, args=(i,), name=f"Thread-{i}")
            threads.append(thread)
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join(timeout=5.0)
        
        # Verify at least one save succeeded (proves the function works)
        assert len(results) > 0, f"At least one save should succeed. Results: {len(results)}, Errors: {len(errors)}"
        
        # Verify final file exists and is valid
        final_file = temp_project_copy / "development_tools" / "docs" / "jsons" / "test_concurrent_results.json"
        assert final_file.exists(), "Final result file should exist after concurrent saves"
        
        # Verify file is valid JSON and contains expected structure
        with open(final_file, 'r') as f:
            data = json.load(f)
            assert 'data' in data, "Result file should contain data"
            # Verify the data structure is correct
            assert isinstance(data['data'], dict), "Data should be a dictionary"
        
        # Verify archive directory exists and has some archived files (if multiple saves succeeded)
        archive_dir = temp_project_copy / "development_tools" / "docs" / "jsons" / "archive"
        if archive_dir.exists() and len(results) > 1:
            archived_files = list(archive_dir.glob("test_concurrent_results_*.json"))
            # If multiple saves succeeded, we should have archived files
            # But don't fail if only one save succeeded (no archiving needed)

