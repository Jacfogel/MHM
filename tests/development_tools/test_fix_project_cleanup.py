"""
Tests for fix_project_cleanup.py.

Tests project cleanup functionality including cache directory removal,
coverage file cleanup, and test data cleanup.
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from tests.development_tools.conftest import load_development_tools_module, temp_project_copy


# Load the module
cleanup_module = load_development_tools_module("shared.fix_project_cleanup")
ProjectCleanup = cleanup_module.ProjectCleanup
main = cleanup_module.main


class TestProjectCleanup:
    """Test ProjectCleanup class functionality."""
    
    @pytest.mark.unit
    def test_init_default_project_root(self, temp_project_copy):
        """Test initialization with default project root."""
        with patch('development_tools.shared.fix_project_cleanup.config') as mock_config:
            mock_config.get_project_root.return_value = str(temp_project_copy)
            
            cleanup = ProjectCleanup()
            
            assert cleanup.project_root == Path(temp_project_copy).resolve(), \
                "Project root should be resolved path"
    
    @pytest.mark.unit
    def test_init_custom_project_root(self, temp_project_copy):
        """Test initialization with custom project root."""
        custom_root = temp_project_copy / "custom"
        custom_root.mkdir()
        
        cleanup = ProjectCleanup(project_root=custom_root)
        
        assert cleanup.project_root == custom_root.resolve(), \
            "Project root should be custom path"
    
    @pytest.mark.unit
    def test_find_directories(self, temp_project_copy):
        """Test finding directories by pattern."""
        cleanup = ProjectCleanup(project_root=temp_project_copy)
        
        # Create test directories
        (temp_project_copy / "module1" / "__pycache__").mkdir(parents=True)
        (temp_project_copy / "module2" / "__pycache__").mkdir(parents=True)
        (temp_project_copy / "other_dir").mkdir()
        
        directories = cleanup.find_directories("__pycache__")
        
        assert len(directories) >= 2, "Should find at least 2 __pycache__ directories"
        assert all("__pycache__" in str(d) for d in directories), \
            "All found directories should contain pattern"
    
    @pytest.mark.unit
    def test_find_directories_excludes_git_venv(self, temp_project_copy):
        """Test that find_directories excludes .git and venv directories."""
        cleanup = ProjectCleanup(project_root=temp_project_copy)
        
        # Create directories that should be excluded
        (temp_project_copy / ".git" / "hooks").mkdir(parents=True)
        (temp_project_copy / "venv" / "lib").mkdir(parents=True)
        (temp_project_copy / ".venv" / "lib").mkdir(parents=True)
        
        # These should not be found even if they match pattern
        directories = cleanup.find_directories("hooks")
        
        # Should not find .git/hooks
        assert not any(".git" in str(d) for d in directories), \
            "Should not find directories in .git"
    
    @pytest.mark.unit
    def test_find_files(self, temp_project_copy):
        """Test finding files by pattern."""
        cleanup = ProjectCleanup(project_root=temp_project_copy)
        
        # Create test files
        (temp_project_copy / "file1.coverage").write_text("test")
        # Create directory first, then file inside it
        (temp_project_copy / "subdir").mkdir(parents=True)
        (temp_project_copy / "subdir" / "file2.coverage").write_text("test")
        
        files = cleanup.find_files(".coverage")
        
        assert len(files) >= 2, "Should find at least 2 .coverage files"
        assert all(".coverage" in str(f) for f in files), \
            "All found files should contain pattern"
    
    @pytest.mark.unit
    def test_get_size_file(self, temp_project_copy):
        """Test getting size of a file."""
        cleanup = ProjectCleanup(project_root=temp_project_copy)
        
        test_file = temp_project_copy / "test.txt"
        test_file.write_text("test content")
        
        size = cleanup.get_size(test_file)
        
        assert isinstance(size, str), "Size should be a string"
        assert "B" in size or "KB" in size, "Size should have unit"
    
    @pytest.mark.unit
    def test_get_size_directory(self, temp_project_copy):
        """Test getting size of a directory."""
        cleanup = ProjectCleanup(project_root=temp_project_copy)
        
        test_dir = temp_project_copy / "test_dir"
        test_dir.mkdir()
        (test_dir / "file1.txt").write_text("content1")
        (test_dir / "file2.txt").write_text("content2")
        
        size = cleanup.get_size(test_dir)
        
        assert isinstance(size, str), "Size should be a string"
        assert "B" in size or "KB" in size, "Size should have unit"
    
    @pytest.mark.unit
    def test_get_size_nonexistent(self, temp_project_copy):
        """Test getting size of nonexistent path."""
        cleanup = ProjectCleanup(project_root=temp_project_copy)
        
        nonexistent = temp_project_copy / "nonexistent"
        size = cleanup.get_size(nonexistent)
        
        assert size == "0 B", "Nonexistent path should return 0 B"
    
    @pytest.mark.unit
    def test_remove_path_file_dry_run(self, temp_project_copy):
        """Test removing a file in dry run mode."""
        cleanup = ProjectCleanup(project_root=temp_project_copy)
        
        test_file = temp_project_copy / "test.txt"
        test_file.write_text("test")
        
        success, message = cleanup.remove_path(test_file, dry_run=True)
        
        assert success is True, "Should succeed in dry run"
        assert "Would remove" in message, "Message should indicate dry run"
        assert test_file.exists(), "File should still exist in dry run"
    
    @pytest.mark.unit
    def test_remove_path_file_actual(self, temp_project_copy):
        """Test actually removing a file."""
        cleanup = ProjectCleanup(project_root=temp_project_copy)
        
        test_file = temp_project_copy / "test.txt"
        test_file.write_text("test")
        
        success, message = cleanup.remove_path(test_file, dry_run=False)
        
        assert success is True, "Should succeed"
        assert "Removed file" in message, "Message should indicate removal"
        assert not test_file.exists(), "File should be removed"
    
    @pytest.mark.unit
    def test_remove_path_directory_actual(self, temp_project_copy):
        """Test actually removing a directory."""
        cleanup = ProjectCleanup(project_root=temp_project_copy)
        
        test_dir = temp_project_copy / "test_dir"
        test_dir.mkdir()
        (test_dir / "file.txt").write_text("test")
        
        success, message = cleanup.remove_path(test_dir, dry_run=False)
        
        assert success is True, "Should succeed"
        assert "Removed directory" in message, "Message should indicate removal"
        assert not test_dir.exists(), "Directory should be removed"
    
    @pytest.mark.unit
    def test_remove_path_nonexistent(self, temp_project_copy):
        """Test removing a nonexistent path."""
        cleanup = ProjectCleanup(project_root=temp_project_copy)
        
        nonexistent = temp_project_copy / "nonexistent"
        success, message = cleanup.remove_path(nonexistent, dry_run=False)
        
        assert success is False, "Should fail for nonexistent path"
        assert "Does not exist" in message, "Message should indicate missing path"
    
    @pytest.mark.unit
    def test_cleanup_cache_directories(self, temp_project_copy):
        """Test cleaning up __pycache__ directories."""
        cleanup = ProjectCleanup(project_root=temp_project_copy)
        
        # Create cache directories
        (temp_project_copy / "module1" / "__pycache__").mkdir(parents=True)
        (temp_project_copy / "module2" / "__pycache__").mkdir(parents=True)
        
        removed, failed = cleanup.cleanup_cache_directories(dry_run=False)
        
        assert removed >= 2, "Should remove at least 2 cache directories"
        assert failed == 0, "Should not have failures"
    
    @pytest.mark.unit
    def test_cleanup_cache_directories_dry_run(self, temp_project_copy):
        """Test cleaning up cache directories in dry run mode."""
        cleanup = ProjectCleanup(project_root=temp_project_copy)
        
        # Create cache directories
        (temp_project_copy / "module1" / "__pycache__").mkdir(parents=True)
        
        removed, failed = cleanup.cleanup_cache_directories(dry_run=True)
        
        assert removed >= 1, "Should report removal in dry run"
        # Directories should still exist
        assert (temp_project_copy / "module1" / "__pycache__").exists(), \
            "Directory should still exist in dry run"

    @pytest.mark.unit
    def test_cleanup_cache_directories_include_tool_caches(self, temp_project_copy):
        """Tool cache cleanup should remove both standardized cache forms and derived cache artifacts."""
        cleanup = ProjectCleanup(project_root=temp_project_copy)

        docs_jsons = temp_project_copy / "development_tools" / "docs" / "jsons"
        tests_jsons = temp_project_copy / "development_tools" / "tests" / "jsons"
        docs_jsons.mkdir(parents=True, exist_ok=True)
        tests_jsons.mkdir(parents=True, exist_ok=True)

        # Hidden standardized cache.
        hidden_cache = docs_jsons / ".analyze_ascii_compliance_cache.json"
        hidden_cache.write_text("{}")
        # Non-hidden cache (coverage caches use this form).
        regular_cache = tests_jsons / "test_file_coverage_cache.json"
        regular_cache.write_text("{}")
        # Derived cache artifact used by freshness checks.
        derived_cache = tests_jsons / "coverage.json"
        derived_cache.write_text("{}")
        # Docs subcheck result used by mtime cache freshness.
        docs_result = docs_jsons / "analyze_ascii_compliance_results.json"
        docs_result.write_text("{}")

        removed, failed = cleanup.cleanup_cache_directories(
            dry_run=False, include_tool_caches=True
        )

        assert removed >= 4, "Should remove tool cache artifacts"
        assert failed == 0, "Should not fail tool cache cleanup"
        assert not hidden_cache.exists(), "Hidden cache should be removed"
        assert not regular_cache.exists(), "Regular cache should be removed"
        assert not derived_cache.exists(), "Derived cache should be removed"
        assert not docs_result.exists(), "Docs result cache artifact should be removed"
    
    @pytest.mark.unit
    def test_cleanup_pytest_cache(self, temp_project_copy):
        """Test cleaning up .pytest_cache directories."""
        cleanup = ProjectCleanup(project_root=temp_project_copy)
        
        # Create pytest cache
        (temp_project_copy / ".pytest_cache").mkdir()
        (temp_project_copy / ".pytest_cache" / "v").mkdir()
        
        removed, failed = cleanup.cleanup_pytest_cache(dry_run=False)
        
        assert removed >= 1, "Should remove pytest cache"
        assert failed == 0, "Should not have failures"
    
    @pytest.mark.unit
    def test_cleanup_coverage_files(self, temp_project_copy):
        """Test cleaning up .coverage files."""
        cleanup = ProjectCleanup(project_root=temp_project_copy)
        
        # Create coverage files
        (temp_project_copy / ".coverage").write_text("test")
        # Create directory first, then file inside it
        (temp_project_copy / "subdir").mkdir(parents=True)
        (temp_project_copy / "subdir" / ".coverage").write_text("test")
        
        removed, failed = cleanup.cleanup_coverage_files(dry_run=False)
        
        assert removed >= 1, "Should remove coverage files"
        assert failed == 0, "Should not have failures"
    
    @pytest.mark.unit
    def test_cleanup_coverage_logs_no_directory(self, temp_project_copy):
        """Test cleaning up coverage logs when directory doesn't exist."""
        cleanup = ProjectCleanup(project_root=temp_project_copy)
        
        removed, failed = cleanup.cleanup_coverage_logs(dry_run=False)
        
        assert removed == 0, "Should remove nothing if directory doesn't exist"
        assert failed == 0, "Should not have failures"
    
    @pytest.mark.unit
    def test_cleanup_coverage_logs_keeps_recent(self, temp_project_copy):
        """Test that coverage log cleanup keeps 2 most recent files."""
        cleanup = ProjectCleanup(project_root=temp_project_copy)
        
        # Create coverage logs directory
        logs_dir = temp_project_copy / "development_tools" / "logs" / "coverage_regeneration"
        logs_dir.mkdir(parents=True)
        
        # Create multiple log files (simulating different timestamps)
        for i in range(5):
            log_file = logs_dir / f"pytest_stdout_20250101_00000{i}.log"
            log_file.write_text(f"log content {i}")
            # Set modification time (older files have lower mtime)
            import time
            log_file.touch()
            time.sleep(0.01)  # Small delay to ensure different mtimes
        
        removed, failed = cleanup.cleanup_coverage_logs(dry_run=False)
        
        # Should keep 2 most recent, remove 3 older
        assert removed >= 3, "Should remove older log files"
        assert failed == 0, "Should not have failures"
        
        # Verify only 2 files remain
        remaining_logs = list(logs_dir.glob("*.log"))
        assert len(remaining_logs) <= 2, "Should keep only 2 most recent files"
    
    @pytest.mark.unit
    def test_cleanup_test_temp_dirs_no_directory(self, temp_project_copy):
        """Test cleaning up test temp dirs when directory doesn't exist."""
        cleanup = ProjectCleanup(project_root=temp_project_copy)
        
        # Ensure the directory doesn't exist
        test_data_dir = temp_project_copy / "tests" / "data"
        if test_data_dir.exists():
            import shutil
            shutil.rmtree(test_data_dir)
        
        removed, failed = cleanup.cleanup_test_temp_dirs(dry_run=False)
        
        assert removed == 0, "Should remove nothing if directory doesn't exist"
        assert failed == 0, "Should not have failures"
    
    @pytest.mark.unit
    def test_cleanup_test_temp_dirs_pytest_dirs(self, temp_project_copy):
        """Test cleaning up pytest temporary directories."""
        cleanup = ProjectCleanup(project_root=temp_project_copy)
        
        # Create test data directory with pytest temp dirs
        test_data = temp_project_copy / "tests" / "data"
        test_data.mkdir(parents=True, exist_ok=True)
        (test_data / "pytest-of-user").mkdir(exist_ok=True)
        (test_data / "pytest-of-user-1").mkdir(exist_ok=True)
        
        removed, failed = cleanup.cleanup_test_temp_dirs(dry_run=False)
        
        assert removed >= 2, "Should remove pytest temp directories"
        assert failed == 0, "Should not have failures"
    
    @pytest.mark.unit
    def test_cleanup_test_user_data_no_directory(self, temp_project_copy):
        """Test cleaning up test user data when directory doesn't exist."""
        cleanup = ProjectCleanup(project_root=temp_project_copy)
        
        removed, failed = cleanup.cleanup_test_user_data(dry_run=False)
        
        assert removed == 0, "Should remove nothing if directory doesn't exist"
        assert failed == 0, "Should not have failures"
    
    @pytest.mark.unit
    def test_cleanup_test_user_data_removes_test_users(self, temp_project_copy):
        """Test cleaning up test user data directories."""
        cleanup = ProjectCleanup(project_root=temp_project_copy)
        
        # Create users directory with test users
        users_dir = temp_project_copy / "data" / "users"
        users_dir.mkdir(parents=True)
        (users_dir / "test_user1").mkdir()
        (users_dir / "test_user2").mkdir()
        (users_dir / "real_user").mkdir()  # Should not be removed
        
        removed, failed = cleanup.cleanup_test_user_data(dry_run=False)
        
        assert removed >= 2, "Should remove test user directories"
        assert failed == 0, "Should not have failures"
        assert (users_dir / "real_user").exists(), "Real user should not be removed"
    
    @pytest.mark.unit
    def test_cleanup_all_default(self, temp_project_copy):
        """Test cleanup_all with default parameters."""
        cleanup = ProjectCleanup(project_root=temp_project_copy)
        
        # Create some test files
        (temp_project_copy / "module" / "__pycache__").mkdir(parents=True)
        (temp_project_copy / ".coverage").write_text("test")
        
        results = cleanup.cleanup_all(dry_run=False)
        
        assert isinstance(results, dict), "Results should be a dictionary"
        assert 'total_removed' in results, "Results should have total_removed"
        assert 'total_failed' in results, "Results should have total_failed"
        assert results['total_removed'] >= 0, "Should have non-negative removed count"
    
    @pytest.mark.unit
    def test_cleanup_all_selective_categories(self, temp_project_copy):
        """Test cleanup_all with selective categories."""
        cleanup = ProjectCleanup(project_root=temp_project_copy)
        
        # Create test files
        (temp_project_copy / "module" / "__pycache__").mkdir(parents=True)
        (temp_project_copy / ".coverage").write_text("test")
        
        # Only clean cache, not coverage
        results = cleanup.cleanup_all(
            dry_run=False,
            cache=True,
            coverage=False,
            test_data=False
        )
        
        assert isinstance(results, dict), "Results should be a dictionary"
        # Cache should be cleaned
        assert results['cache']['removed'] >= 0, "Cache cleanup should run"
        # Coverage should not be cleaned
        assert results['coverage']['removed'] == 0, "Coverage should not be cleaned"
    
    @pytest.mark.unit
    def test_cleanup_all_dry_run(self, temp_project_copy):
        """Test cleanup_all in dry run mode."""
        cleanup = ProjectCleanup(project_root=temp_project_copy)
        
        # Create test files
        test_file = temp_project_copy / ".coverage"
        test_file.write_text("test")
        
        results = cleanup.cleanup_all(dry_run=True)
        
        assert isinstance(results, dict), "Results should be a dictionary"
        # File should still exist
        assert test_file.exists(), "File should still exist in dry run"


class TestProjectCleanupMain:
    """Test main() function for CLI interface."""
    
    @pytest.mark.unit
    def test_main_dry_run(self, temp_project_copy):
        """Test main function with --dry-run flag."""
        with patch('development_tools.shared.fix_project_cleanup.ProjectCleanup') as mock_cleanup_class:
            mock_cleanup = MagicMock()
            mock_cleanup_class.return_value = mock_cleanup
            mock_cleanup.cleanup_all.return_value = {
                'total_removed': 5,
                'total_failed': 0
            }
            
            with patch('sys.argv', ['fix_project_cleanup.py', '--dry-run']):
                result = main()
            
            assert result == 0, "Should exit with success code"
            mock_cleanup.cleanup_all.assert_called_once()
            call_kwargs = mock_cleanup.cleanup_all.call_args[1]
            assert call_kwargs['dry_run'] is True, "Should use dry run mode"
    
    @pytest.mark.unit
    def test_main_all_flag(self, temp_project_copy):
        """Test main function with --all flag."""
        with patch('development_tools.shared.fix_project_cleanup.ProjectCleanup') as mock_cleanup_class:
            mock_cleanup = MagicMock()
            mock_cleanup_class.return_value = mock_cleanup
            mock_cleanup.cleanup_all.return_value = {
                'total_removed': 10,
                'total_failed': 0
            }
            
            with patch('sys.argv', ['fix_project_cleanup.py', '--all']):
                result = main()
            
            assert result == 0, "Should exit with success code"
            call_kwargs = mock_cleanup.cleanup_all.call_args[1]
            assert call_kwargs['cache'] is True, "Should clean cache"
            assert call_kwargs['test_data'] is True, "Should clean test data"
            assert call_kwargs['coverage'] is True, "Should clean coverage"
    
    @pytest.mark.unit
    def test_main_json_output(self, temp_project_copy):
        """Test main function with --json flag."""
        with patch('development_tools.shared.fix_project_cleanup.ProjectCleanup') as mock_cleanup_class:
            mock_cleanup = MagicMock()
            mock_cleanup_class.return_value = mock_cleanup
            mock_cleanup.cleanup_all.return_value = {
                'total_removed': 3,
                'total_failed': 0
            }
            
            with patch('sys.argv', ['fix_project_cleanup.py', '--json']):
                with patch('builtins.print') as mock_print:
                    result = main()
            
            assert result == 0, "Should exit with success code"
            # Should print JSON
            mock_print.assert_called()
            # Check that JSON was printed (first call should be JSON)
            call_args = mock_print.call_args[0][0]
            assert 'total_removed' in call_args, "Should print JSON with total_removed"
    
    @pytest.mark.unit
    def test_main_exit_code_on_failure(self, temp_project_copy):
        """Test main function exit code when cleanup fails."""
        with patch('development_tools.shared.fix_project_cleanup.ProjectCleanup') as mock_cleanup_class:
            mock_cleanup = MagicMock()
            mock_cleanup_class.return_value = mock_cleanup
            mock_cleanup.cleanup_all.return_value = {
                'total_removed': 5,
                'total_failed': 2
            }
            
            with patch('sys.argv', ['fix_project_cleanup.py']):
                result = main()
            
            assert result == 1, "Should exit with error code when failures occur"
