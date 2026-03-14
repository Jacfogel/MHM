"""
Convenience functions for test environment setup and cleanup.
"""

import logging
from typing import Any

from tests.test_helpers.test_utilities.test_data_manager import TestDataManager
from tests.test_helpers.test_utilities.test_user_factory import TestUserFactory

logger = logging.getLogger(__name__)


def create_test_user(
    user_id: str,
    user_type: str = "basic",
    test_data_dir: str | None = None,
    **kwargs: Any,
) -> bool:
    """
    Convenience function to create test users with different configurations

    Args:
        user_id: Unique identifier for the test user
        user_type: Type of user to create. Options:
            - "basic": Basic user with configurable features
            - "discord": Discord-specific user
            - "email": Email-specific user

            - "full": Full featured user with all capabilities
            - "minimal": Minimal user with only messaging
            - "health": Health-focused user
            - "task": Task/productivity-focused user
            - "disability": User with accessibility considerations
            - "complex_checkins": User with complex check-in configurations
            - "limited_data": User with minimal data (like real users)
            - "inconsistent": User with inconsistent/partial data
            - "custom_fields": User with custom field configurations
            - "scheduled": User with custom schedule configurations
        test_data_dir: Test data directory to use (required for modern test approach)
        **kwargs: Additional arguments passed to the specific creation method

    Returns:
        bool: True if user was created successfully, False otherwise
    """
    try:
        if user_type == "basic":
            enable_checkins = kwargs.get("enable_checkins", True)
            enable_tasks = kwargs.get("enable_tasks", True)
            return TestUserFactory.create_basic_user(
                user_id, enable_checkins, enable_tasks, test_data_dir
            )

        elif user_type == "discord":
            discord_user_id = kwargs.get("discord_user_id")
            return TestUserFactory.create_discord_user(
                user_id, discord_user_id, test_data_dir
            )

        elif user_type == "email":
            email = kwargs.get("email")
            return TestUserFactory.create_email_user(user_id, email, test_data_dir)

        elif user_type == "full":
            return TestUserFactory.create_full_featured_user(user_id, test_data_dir)

        elif user_type == "minimal":
            return TestUserFactory.create_minimal_user(user_id, test_data_dir)

        elif user_type == "health":
            return TestUserFactory.create_user_with_health_focus(user_id, test_data_dir)

        elif user_type == "task":
            return TestUserFactory.create_user_with_task_focus(user_id, test_data_dir)

        elif user_type == "disability":
            return TestUserFactory.create_user_with_disabilities(user_id, test_data_dir)

        elif user_type == "complex_checkins":
            return TestUserFactory.create_user_with_complex_checkins(
                user_id, test_data_dir
            )

        elif user_type == "limited_data":
            return TestUserFactory.create_user_with_limited_data(user_id, test_data_dir)

        elif user_type == "inconsistent":
            return TestUserFactory.create_user_with_inconsistent_data(
                user_id, test_data_dir
            )

        else:
            logger.error(f"Unknown user type: {user_type}")
            return False

    except Exception as e:
        logger.error(f"Error creating test user {user_id} of type {user_type}: {e}")
        return False


def setup_test_data_environment() -> tuple:
    """
    Convenience function to set up test data environment

    Returns:
        tuple: (test_dir, test_data_dir, test_test_data_dir)
    """
    return TestDataManager.setup_test_environment()


def cleanup_test_data_environment(test_dir: str) -> None:
    """
    Convenience function to clean up test data environment

    Args:
        test_dir: Path to the test directory to clean up
    """
    TestDataManager.cleanup_test_environment(test_dir)
