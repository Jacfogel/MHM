#!/usr/bin/env python3
"""
Test Cleanup Utility for MHM Testing Framework.

This module provides utilities for:
- Cleaning up test user data
- Resetting test environments
- Managing test data isolation
- Validating test data integrity
"""

import os
import shutil
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

# Do not modify sys.path; rely on package imports

from core.config import BASE_DATA_DIR, USER_INFO_DIR_PATH
from core.service_utilities import now_filename_timestamp
from core.logger import get_component_logger

logger = get_component_logger("main")

# Define project root for this module
project_root = Path(__file__).parent.parent.parent


class CleanupManager:
    """Manages test data cleanup and isolation."""

    def __init__(self, test_data_dir: str | None = None):
        """Initialize the cleanup manager."""
        self.test_data_dir = test_data_dir or BASE_DATA_DIR
        self.user_dir = USER_INFO_DIR_PATH
        self.backup_dir = Path(project_root) / "tests" / "logs" / "backups"
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def cleanup_test_users(self, user_ids: list[str] | None = None) -> bool:
        """Clean up test user data.

        Args:
            user_ids: List of user IDs to clean up. If None, cleans up all test users.

        Returns:
            bool: True if cleanup was successful, False otherwise.
        """
        try:
            if not os.path.exists(self.user_dir):
                logger.warning(f"User directory does not exist: {self.user_dir}")
                return True

            if user_ids is None:
                # Find all test users
                user_ids = self._find_test_users()

            if not user_ids:
                logger.info("No test users found to clean up")
                return True

            logger.info(f"Cleaning up {len(user_ids)} test users: {user_ids}")

            for user_id in user_ids:
                self._cleanup_single_user(user_id)

            logger.info("Test user cleanup completed successfully")
            return True

        except Exception as e:
            logger.error(f"Error during test user cleanup: {e}")
            return False

    def _find_test_users(self) -> list[str]:
        """Find all test users in the user directory."""
        test_users = []

        if not os.path.exists(self.user_dir):
            return test_users

        for item in os.listdir(self.user_dir):
            item_path = os.path.join(self.user_dir, item)
            if os.path.isdir(item_path):
                # Check if it's a test user by looking for account.json
                account_file = os.path.join(item_path, "account.json")
                if os.path.exists(account_file):
                    try:
                        with open(account_file, "r") as f:
                            account_data = json.load(f)
                            user_id = account_data.get("user_id", item)
                            # Consider it a test user if it starts with 'test' or has test-like patterns
                            if (
                                user_id.startswith("test")
                                or "test" in user_id.lower()
                                or user_id.endswith("-test")
                            ):
                                test_users.append(user_id)
                    except Exception as e:
                        logger.warning(f"Error reading account file for {item}: {e}")

        return test_users

    def _cleanup_single_user(self, user_id: str) -> bool:
        """Clean up a single test user."""
        try:
            user_path = os.path.join(self.user_dir, user_id)

            if not os.path.exists(user_path):
                logger.warning(f"User directory does not exist: {user_path}")
                return True

            # Create backup before deletion
            backup_path = self._create_user_backup(user_id, user_path)

            # Remove the user directory
            shutil.rmtree(user_path)
            logger.info(f"Cleaned up test user: {user_id} (backup: {backup_path})")

            return True

        except Exception as e:
            logger.error(f"Error cleaning up user {user_id}: {e}")
            return False

    def _create_user_backup(self, user_id: str, user_path: str) -> str:
        """Create a backup of user data before cleanup."""
        timestamp = now_filename_timestamp()
        backup_name = f"test_user_backup_{user_id}_{timestamp}.zip"
        backup_path = self.backup_dir / backup_name

        try:
            shutil.make_archive(str(backup_path).replace(".zip", ""), "zip", user_path)
            return str(backup_path)
        except Exception as e:
            logger.warning(f"Failed to create backup for {user_id}: {e}")
            return "backup_failed"

    def reset_test_environment(self) -> bool:
        """Reset the entire test environment."""
        try:
            logger.info("Resetting test environment...")

            # Clean up test users
            self.cleanup_test_users()

            # Clean up test logs (keep only recent ones)
            self._cleanup_old_test_logs()

            # Clean up temporary test files
            self._cleanup_temp_files()

            logger.info("Test environment reset completed")
            return True

        except Exception as e:
            logger.error(f"Error resetting test environment: {e}")
            return False

    def _cleanup_old_test_logs(self, keep_days: int = 7) -> None:
        """Clean up old test log files."""
        try:
            test_logs_dir = Path(project_root) / "tests" / "logs"
            if not test_logs_dir.exists():
                return

            cutoff_time = datetime.now().timestamp() - (keep_days * 24 * 60 * 60)

            for log_file in test_logs_dir.glob("*.log"):
                if log_file.stat().st_mtime < cutoff_time:
                    log_file.unlink()
                    logger.debug(f"Removed old test log: {log_file}")

        except Exception as e:
            logger.warning(f"Error cleaning up old test logs: {e}")

    def _cleanup_temp_files(self) -> None:
        """Clean up temporary test files."""
        try:
            # Clean up any temporary files in the project root
            temp_patterns = ["*.tmp", "*.temp", "*_test_*"]

            for pattern in temp_patterns:
                for temp_file in Path(project_root).glob(pattern):
                    if temp_file.is_file():
                        temp_file.unlink()
                        logger.debug(f"Removed temp file: {temp_file}")

        except Exception as e:
            logger.warning(f"Error cleaning up temp files: {e}")

    def validate_test_data_integrity(self) -> dict[str, Any]:
        """Validate the integrity of test data."""
        results = {"valid": True, "issues": [], "test_users": [], "orphaned_files": []}

        try:
            # Check test users
            test_users = self._find_test_users()
            results["test_users"] = test_users

            for user_id in test_users:
                user_path = os.path.join(self.user_dir, user_id)
                if not self._validate_user_data(user_id, user_path):
                    results["valid"] = False
                    results["issues"].append(f"Invalid user data for {user_id}")

            # Check for orphaned files
            orphaned = self._find_orphaned_files()
            if orphaned:
                results["orphaned_files"] = orphaned
                results["issues"].append(f"Found {len(orphaned)} orphaned files")

        except Exception as e:
            results["valid"] = False
            results["issues"].append(f"Validation error: {e}")

        return results

    def _validate_user_data(self, user_id: str, user_path: str) -> bool:
        """Validate a single user's data integrity."""
        try:
            required_files = ["account.json", "preferences.json", "user_context.json"]

            for required_file in required_files:
                file_path = os.path.join(user_path, required_file)
                if not os.path.exists(file_path):
                    logger.warning(
                        f"Missing required file for {user_id}: {required_file}"
                    )
                    return False

                # Try to load JSON
                try:
                    with open(file_path, "r") as f:
                        json.load(f)
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON in {user_id}/{required_file}")
                    return False

            return True

        except Exception as e:
            logger.error(f"Error validating user {user_id}: {e}")
            return False

    def _find_orphaned_files(self) -> list[str]:
        """Find orphaned files in the user directory."""
        orphaned = []

        if not os.path.exists(self.user_dir):
            return orphaned

        for item in os.listdir(self.user_dir):
            item_path = os.path.join(self.user_dir, item)

            # Check if it's a directory without proper user structure
            if os.path.isdir(item_path):
                account_file = os.path.join(item_path, "account.json")
                if not os.path.exists(account_file):
                    orphaned.append(item)
            # Check if it's a file (shouldn't be any files directly in user directory)
            elif os.path.isfile(item_path):
                orphaned.append(item)

        return orphaned


def main():
    """Command-line interface for test cleanup."""
    import argparse

    parser = argparse.ArgumentParser(description="MHM Test Cleanup Utility")
    parser.add_argument(
        "--cleanup-users", action="store_true", help="Clean up all test users"
    )
    parser.add_argument(
        "--reset-env", action="store_true", help="Reset entire test environment"
    )
    parser.add_argument(
        "--validate", action="store_true", help="Validate test data integrity"
    )
    parser.add_argument("--users", nargs="+", help="Specific user IDs to clean up")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)

    cleanup_manager = CleanupManager()

    if args.cleanup_users:
        success = cleanup_manager.cleanup_test_users(args.users)
        logging.getLogger("mhm_tests").info(
            f"User cleanup: {'SUCCESS' if success else 'FAILED'}"
        )

    if args.reset_env:
        success = cleanup_manager.reset_test_environment()
        logging.getLogger("mhm_tests").info(
            f"Environment reset: {'SUCCESS' if success else 'FAILED'}"
        )

    if args.validate:
        results = cleanup_manager.validate_test_data_integrity()
        _logger = logging.getLogger("mhm_tests")
        _logger.info(f"Data integrity: {'VALID' if results['valid'] else 'INVALID'}")
        if results["issues"]:
            _logger.warning("Issues found:")
            for issue in results["issues"]:
                _logger.warning(f"  - {issue}")
        if results["test_users"]:
            _logger.info(f"Test users: {results['test_users']}")
        if results["orphaned_files"]:
            _logger.info(f"Orphaned files: {results['orphaned_files']}")

    if not any([args.cleanup_users, args.reset_env, args.validate]):
        parser.print_help()


if __name__ == "__main__":
    main()
