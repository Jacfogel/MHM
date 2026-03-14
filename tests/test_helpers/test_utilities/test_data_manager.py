"""
Manages test data directories and cleanup.
"""

import logging
import os
import shutil
import uuid

from core.file_locking import safe_json_write

logger = logging.getLogger(__name__)


class TestDataManager:
    """Manages test data directories and cleanup"""

    @staticmethod
    def setup_test_environment() -> tuple:
        """
        Create isolated test environment with temporary directories.
        Optimized: Uses session-scoped base tmp directory (created once).

        Returns:
            tuple: (test_dir, test_data_dir, test_test_data_dir)
        """
        # Create temporary test directory
        # Use per-test path under tests/data instead of system temp
        from tests.conftest import tests_data_dir  # reuse base

        base_tmp = os.path.join(tests_data_dir, "tmp")
        # Base tmp directory should already exist from session fixture, but ensure it exists
        os.makedirs(base_tmp, exist_ok=True)
        test_dir = os.path.join(base_tmp, f"mhm_test_{uuid.uuid4().hex}")
        os.makedirs(test_dir, exist_ok=True)
        test_data_dir = os.path.join(test_dir, "data")
        test_test_data_dir = os.path.join(test_dir, "tests", "data")

        # Create directory structure (batch creation for efficiency)
        dirs_to_create = [
            test_data_dir,
            test_test_data_dir,
            os.path.join(test_data_dir, "users"),
            os.path.join(test_test_data_dir, "users"),
        ]
        for dir_path in dirs_to_create:
            os.makedirs(dir_path, exist_ok=True)

        # Create test user index with flat lookup structure
        # Use file locking to prevent race conditions in parallel test execution
        user_index = {
            "last_updated": "2025-01-01T00:00:00",
            "test-user-basic": "test-user-basic",  # username → UUID
            "test-user-full": "test-user-full",  # username → UUID
        }

        safe_json_write(
            os.path.join(test_data_dir, "user_index.json"), user_index, indent=2
        )

        return test_dir, test_data_dir, test_test_data_dir

    @staticmethod
    def cleanup_test_environment(test_dir: str) -> None:
        """
        Clean up test environment and remove temporary files

        Args:
            test_dir: Path to the test directory to clean up
        """
        try:
            if not test_dir:
                return
            # Prefer letting the per-test factory and session cleanup handle removal.
            # As a fallback, remove with ignore_errors to avoid intermittent failures on Windows.
            if os.path.exists(test_dir):
                shutil.rmtree(test_dir, ignore_errors=True)
        except Exception as e:
            logger.warning(f"Could not clean up test directory {test_dir}: {e}")
