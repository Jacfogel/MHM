"""Focused unit coverage for core.service request helper paths."""

import json
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from communication.core.message_send_result import MessageSendResult
from core.service import MHMService


@pytest.fixture
def service():
    instance = MHMService()
    instance.communication_manager = Mock()
    return instance


@pytest.mark.unit
@pytest.mark.communication
@pytest.mark.checkins
class TestServiceCheckinRequestHelpers:
    def test_get_checkin_first_question_returns_selected_text(self, service):
        with (
            patch(
                "core.get_user_data",
                return_value={
                    "preferences": {
                        "checkin_settings": {"questions": {"mood": {"enabled": True}}}
                    }
                },
            ),
            patch(
                "communication.message_processing.conversation_flow_manager.conversation_manager._select_checkin_questions_with_weighting",
                return_value=["mood"],
            ),
            patch(
                "communication.message_processing.conversation_flow_manager.conversation_manager._get_question_text",
                return_value="How is your mood today?",
            ),
        ):
            question = service._get_checkin_first_question("user-1")

        assert question == "How is your mood today?"

    def test_write_checkin_response_creates_response_file(
        self, service, test_path_factory
    ):
        base_dir = Path(test_path_factory)
        with patch.object(
            service,
            "_get_service_request_base_directory",
            return_value=str(base_dir),
        ):
            service._write_checkin_response("user-1", "How are you?")

        response_path = base_dir / "checkin_prompt_response_user-1.flag"
        assert response_path.exists()
        payload = json.loads(response_path.read_text(encoding="utf-8"))
        assert payload["user_id"] == "user-1"
        assert payload["first_question"] == "How are you?"
        assert "timestamp" in payload

    def test_check_checkin_prompt_requests_sends_prompt_and_writes_response(
        self, service, test_path_factory
    ):
        base_dir = Path(test_path_factory)
        request_path = base_dir / "checkin_prompt_request_user-1.flag"
        request_path.write_text(json.dumps({"user_id": "user-1"}), encoding="utf-8")

        service.communication_manager.get_recipient_for_service.return_value = (
            "discord_user:user-1"
        )

        with (
            patch.object(
                service,
                "_get_service_request_base_directory",
                return_value=str(base_dir),
            ),
            patch(
                "core.get_user_data",
                return_value={"preferences": {"channel": {"type": "discord"}}},
            ),
            patch(
                "core.service_requests.get_checkin_first_question",
                return_value="What is one win from today?",
            ),
        ):
            service.check_checkin_prompt_requests()

        service.communication_manager.send_checkin_prompt.assert_called_once_with(
            "user-1", "discord", "discord_user:user-1"
        )
        response_path = base_dir / "checkin_prompt_response_user-1.flag"
        assert response_path.exists()
        response_payload = json.loads(response_path.read_text(encoding="utf-8"))
        assert response_payload["first_question"] == "What is one win from today?"
        assert not request_path.exists()

    def test_check_checkin_prompt_requests_skips_without_recipient(
        self, service, test_path_factory
    ):
        base_dir = Path(test_path_factory)
        request_path = base_dir / "checkin_prompt_request_user-2.flag"
        request_path.write_text(json.dumps({"user_id": "user-2"}), encoding="utf-8")

        service.communication_manager.get_recipient_for_service.return_value = None

        with (
            patch.object(
                service,
                "_get_service_request_base_directory",
                return_value=str(base_dir),
            ),
            patch(
                "core.get_user_data",
                return_value={"preferences": {"channel": {"type": "discord"}}},
            ),
            patch.object(service, "_write_checkin_response") as mock_write_response,
        ):
            service.check_checkin_prompt_requests()

        service.communication_manager.send_checkin_prompt.assert_not_called()
        mock_write_response.assert_not_called()
        assert not request_path.exists()


@pytest.mark.unit
@pytest.mark.communication
@pytest.mark.tasks
class TestServiceTaskAndMessageRequestHelpers:
    def test_check_task_reminder_requests_processes_valid_file(
        self, service, test_path_factory
    ):
        base_dir = Path(test_path_factory)
        request_path = base_dir / "task_reminder_request_user-1.flag"
        request_path.write_text(
            json.dumps({"user_id": "user-1", "task_identifier": "task-1"}),
            encoding="utf-8",
        )

        with patch.object(
            service,
            "_get_service_request_base_directory",
            return_value=str(base_dir),
        ):
            service.check_task_reminder_requests()

        service.communication_manager.handle_task_reminder.assert_called_once_with(
            "user-1", "task-1"
        )
        assert not request_path.exists()

    def test_process_valid_test_message_request_writes_response_for_matching_message(
        self, service, test_path_factory
    ):
        base_dir = Path(test_path_factory)
        service.communication_manager.handle_message_sending.return_value = (
            MessageSendResult.sent(
                "user-1", "motivational", sent_text="Keep going!"
            )
        )
        request_data = {
            "user_id": "user-1",
            "category": "motivational",
            "source": "admin_panel",
        }

        with patch.object(
            service,
            "_get_service_request_base_directory",
            return_value=str(base_dir),
        ):
            service._check_test_message_requests__process_valid_request(request_data)

        service.communication_manager.handle_message_sending.assert_called_once_with(
            "user-1", "motivational"
        )
        response_path = base_dir / "test_message_response_user-1_motivational.flag"
        assert response_path.exists()
        response_payload = json.loads(response_path.read_text(encoding="utf-8"))
        assert response_payload["message"] == "Keep going!"

    def test_process_valid_test_message_request_skips_response_on_mismatch(self, service):
        service.communication_manager.handle_message_sending.return_value = (
            MessageSendResult.sent(
                "different-user", "motivational", sent_text="Keep going!"
            )
        )
        request_data = {
            "user_id": "user-1",
            "category": "motivational",
            "source": "admin_panel",
        }

        with patch.object(
            service, "_check_test_message_requests__write_response"
        ) as mock_write_response:
            service._check_test_message_requests__process_valid_request(request_data)

        mock_write_response.assert_not_called()
