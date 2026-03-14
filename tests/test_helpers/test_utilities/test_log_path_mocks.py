"""
Helper for creating complete log path mocks for tests.
"""

from pathlib import Path


class TestLogPathMocks:
    """Helper class for creating complete log path mocks for tests"""

    @staticmethod
    def create_complete_log_paths_mock(base_dir: str) -> dict[str, str]:
        """
        Create a complete mock dictionary for _get_log_paths_for_environment()
        that includes all required keys including ai_dev_tools_file.

        Args:
            base_dir: Base directory for logs (e.g., test_data_dir / "logs")

        Returns:
            Dict with all log path keys required by the logger system
        """

        base_path = Path(base_dir)

        return {
            "base_dir": str(base_path),
            "backup_dir": str(base_path / "backups"),
            "archive_dir": str(base_path / "archive"),
            "main_file": str(base_path / "app.log"),
            "discord_file": str(base_path / "discord.log"),
            "ai_file": str(base_path / "ai.log"),
            "user_activity_file": str(base_path / "user_activity.log"),
            "errors_file": str(base_path / "errors.log"),
            "communication_manager_file": str(base_path / "communication_manager.log"),
            "email_file": str(base_path / "email.log"),
            "ui_file": str(base_path / "ui.log"),
            "file_ops_file": str(base_path / "file_ops.log"),
            "scheduler_file": str(base_path / "scheduler.log"),
            "schedule_utilities_file": str(base_path / "schedule_utilities.log"),
            "analytics_file": str(base_path / "analytics.log"),
            "message_file": str(base_path / "message.log"),
            "backup_file": str(base_path / "backup.log"),
            "checkin_dynamic_file": str(base_path / "checkin_dynamic.log"),
            "ai_dev_tools_file": str(base_path / "ai_dev_tools.log"),
        }
