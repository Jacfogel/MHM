"""Additional unit coverage for core.service message request helper utilities."""

from pathlib import Path
from unittest.mock import patch, call

import pytest

from core.service import MHMService


@pytest.fixture
def service():
    return MHMService()


@pytest.mark.unit
@pytest.mark.communication
@pytest.mark.messages
class TestServiceMessageContentHelpers:
    def test_validate_test_message_request_data_rejects_missing_fields(self, service):
        with patch("core.service.logger") as mock_logger:
            ok = service._check_test_message_requests__validate_request_data(
                {"user_id": None, "category": "motivational", "source": "ui"},
                "test_message_request_1.flag",
            )

        assert ok is False
        mock_logger.warning.assert_called_once()

    def test_has_any_request_files_returns_false_for_empty_directory(self, service, test_path_factory):
        base_dir = str(test_path_factory)

        assert service._has_any_request_files(base_dir) is False

    def test_has_any_request_files_returns_true_when_flag_exists(self, service, test_path_factory):
        base_dir = Path(test_path_factory)
        (base_dir / "test_message_request_demo.flag").write_text("{}", encoding="utf-8")

        assert service._has_any_request_files(str(base_dir)) is True

    def test_has_any_request_files_returns_true_when_scan_errors(self, service):
        with patch("core.service.Path.iterdir", side_effect=Exception("scan failed")):
            assert service._has_any_request_files("C:/does-not-matter") is True

    def test_get_message_content_selects_non_recent_specific_period_message(self, service):
        with (
            patch(
                "core.schedule_management.get_current_time_periods_with_validation",
                return_value=(["ALL", "morning"], ["ALL", "morning"]),
            ),
            patch(
                "core.schedule_management.get_current_day_names",
                return_value=["MONDAY"],
            ),
            patch(
                "core.message_management.load_user_messages",
                return_value=[
                    {
                        "message": "recent message",
                        "days": ["MONDAY"],
                        "time_periods": ["morning"],
                    },
                    {
                        "message": "fresh message",
                        "days": ["MONDAY"],
                        "time_periods": ["morning"],
                    },
                ],
            ),
            patch(
                "core.message_management.get_recent_messages",
                return_value=[{"message": "recent message"}],
            ),
            patch("core.config.get_user_data_dir", return_value="C:/tmp/user-1"),
            patch("random.random", return_value=0.2),
            patch("random.choice", side_effect=lambda items: items[0]),
        ):
            content = service._check_test_message_requests__get_message_content(
                "user-1", "motivational"
            )

        assert content == "fresh message"

    def test_get_message_content_returns_none_when_no_messages_match(self, service):
        with (
            patch(
                "core.schedule_management.get_current_time_periods_with_validation",
                return_value=(["morning"], ["morning"]),
            ),
            patch(
                "core.schedule_management.get_current_day_names",
                return_value=["MONDAY"],
            ),
            patch(
                "core.message_management.load_user_messages",
                return_value=[],
            ),
            patch("core.config.get_user_data_dir", return_value="C:/tmp/user-1"),
        ):
            content = service._check_test_message_requests__get_message_content(
                "user-1", "motivational"
            )

        assert content is None

    def test_discover_request_files_filters_to_test_message_flags(
        self, service, test_path_factory
    ):
        base_dir = Path(test_path_factory)
        (base_dir / "test_message_request_a.flag").write_text("{}", encoding="utf-8")
        (base_dir / "task_reminder_request_a.flag").write_text("{}", encoding="utf-8")
        (base_dir / "random.txt").write_text("x", encoding="utf-8")

        files = service._check_test_message_requests__discover_request_files(
            str(base_dir)
        )

        assert len(files) == 1
        assert files[0].endswith("test_message_request_a.flag")

    def test_parse_request_file_defaults_source_to_unknown(self, service, test_path_factory):
        base_dir = Path(test_path_factory)
        request_path = base_dir / "test_message_request_parse.flag"
        request_path.write_text(
            '{"user_id": "user-1", "category": "motivational"}', encoding="utf-8"
        )

        data = service._check_test_message_requests__parse_request_file(str(request_path))

        assert data["user_id"] == "user-1"
        assert data["category"] == "motivational"
        assert data["source"] == "unknown"

    def test_cleanup_request_file_removes_file(self, service, test_path_factory):
        base_dir = Path(test_path_factory)
        request_path = base_dir / "test_message_request_cleanup.flag"
        request_path.write_text("{}", encoding="utf-8")

        service._cleanup_request_file_after_process(
            str(request_path), request_path.name, "test message"
        )

        assert not request_path.exists()

    def test_check_test_message_requests_processes_valid_request_and_cleans_up(self, service):
        with (
            patch.object(service, "_check_test_message_requests__get_base_directory", return_value="C:/tmp"),
            patch.object(
                service,
                "_check_test_message_requests__discover_request_files",
                return_value=["C:/tmp/test_message_request_1.flag"],
            ),
            patch.object(
                service,
                "_check_test_message_requests__parse_request_file",
                return_value={"user_id": "u1", "category": "motivational", "source": "ui"},
            ),
            patch.object(
                service,
                "_check_test_message_requests__validate_request_data",
                return_value=True,
            ),
            patch.object(service, "_check_test_message_requests__process_valid_request") as mock_process,
            patch.object(service, "_cleanup_request_file_after_process") as mock_cleanup,
        ):
            service.check_test_message_requests()

        mock_process.assert_called_once_with(
            {"user_id": "u1", "category": "motivational", "source": "ui"}
        )
        mock_cleanup.assert_called_once_with(
            "C:/tmp/test_message_request_1.flag",
            "test_message_request_1.flag",
            "test message",
        )

    def test_check_test_message_requests_skips_invalid_but_still_cleans_up(self, service):
        with (
            patch.object(service, "_check_test_message_requests__get_base_directory", return_value="C:/tmp"),
            patch.object(
                service,
                "_check_test_message_requests__discover_request_files",
                return_value=[
                    "C:/tmp/test_message_request_1.flag",
                    "C:/tmp/test_message_request_2.flag",
                ],
            ),
            patch.object(
                service,
                "_check_test_message_requests__parse_request_file",
                side_effect=[
                    {"user_id": None, "category": "motivational", "source": "ui"},
                    {"user_id": "u2", "category": "health", "source": "ui"},
                ],
            ),
            patch.object(
                service,
                "_check_test_message_requests__validate_request_data",
                side_effect=[False, True],
            ),
            patch.object(service, "_check_test_message_requests__process_valid_request") as mock_process,
            patch.object(service, "_cleanup_request_file_after_process") as mock_cleanup,
        ):
            service.check_test_message_requests()

        mock_process.assert_called_once_with(
            {"user_id": "u2", "category": "health", "source": "ui"}
        )
        assert mock_cleanup.call_args_list == [
            call(
                "C:/tmp/test_message_request_1.flag",
                "test_message_request_1.flag",
                "test message",
            ),
            call(
                "C:/tmp/test_message_request_2.flag",
                "test_message_request_2.flag",
                "test message",
            ),
        ]
