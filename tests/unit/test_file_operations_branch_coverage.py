from pathlib import Path

import pytest
from core.file_operations import determine_file_path, verify_file_access


pytestmark = [pytest.mark.core]

@pytest.mark.unit
@pytest.mark.core
class TestFileOperationsBranchCoverage:
    def test_verify_file_access_invalid_paths_input(self):
        assert verify_file_access(None) is False
        assert verify_file_access("not-a-list") is False

    def test_verify_file_access_invalid_member_type(self):
        assert verify_file_access(["ok", None]) is False

    def test_verify_file_access_missing_file_raises(self):
        # @handle_errors converts FileOperationError into False for callers.
        assert verify_file_access(["C:/definitely/missing/file.json"]) is False

    def test_determine_file_path_rejects_invalid_identifier(self):
        assert determine_file_path("users", None) == ""

    def test_determine_file_path_messages_and_schedules(self, monkeypatch):
        monkeypatch.setattr("core.file_operations.get_user_data_dir", lambda user_id: f"base/{user_id}")

        messages_path = determine_file_path("messages", "motivational/u1")
        schedules_category_path = determine_file_path("schedules", "motivational/u1")
        schedules_default_path = determine_file_path("schedules", "u1")

        assert messages_path.endswith(str(Path("base/u1") / "messages" / "motivational.json"))
        assert schedules_category_path.endswith(str(Path("base/u1") / "schedules" / "motivational.json"))
        assert schedules_default_path.endswith(str(Path("base/u1") / "schedules.json"))

    def test_determine_file_path_messages_invalid_identifier_raises(self):
        # @handle_errors catches FileOperationError and returns default "".
        assert determine_file_path("messages", "justcategory") == ""

    def test_determine_file_path_tasks_invalid_identifier_raises(self):
        assert determine_file_path("tasks", "only-user") == ""

    def test_determine_file_path_unknown_file_type_raises(self):
        assert determine_file_path("mystery", "id") == ""

    def test_determine_file_path_default_messages(self, monkeypatch):
        monkeypatch.setattr("core.file_operations.DEFAULT_MESSAGES_DIR_PATH", "resources/default_messages")
        path = determine_file_path("default_messages", "daily")
        assert path.endswith(str(Path("resources/default_messages") / "daily.json"))
