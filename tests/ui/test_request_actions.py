from pathlib import Path
from unittest.mock import Mock, mock_open, patch

import pytest

from ui import request_actions


@pytest.mark.ui
def test_create_test_message_request_writes_flag_and_restores_user_context(tmp_path):
    context = Mock()
    context.get_user_id.return_value = "original-user"

    with patch.object(request_actions, "get_flags_dir", return_value=tmp_path), \
        patch.object(request_actions, "now_timestamp_full", return_value="2026-06-06T00:00:00"), \
        patch.object(request_actions, "UserContext", return_value=context), \
        patch.object(
            request_actions,
            "get_user_data",
            return_value={"preferences": {"channel": {"type": "discord"}}},
        ), \
        patch.object(request_actions, "_schedule_stale_request_cleanup") as cleanup:
        outcome = request_actions.create_test_message_request(
            "test-user", "motivational"
        )

    request_file = tmp_path / "test_message_request_test-user_motivational.flag"
    assert request_file.exists()
    assert outcome.level == "info"
    assert outcome.request_file == request_file
    assert "via discord" in outcome.message
    context.set_user_id.assert_any_call("test-user")
    context.set_user_id.assert_called_with("original-user")
    cleanup.assert_called_once_with(request_file)


@pytest.mark.ui
def test_create_checkin_prompt_request_writes_flag_without_live_service(tmp_path):
    request_file = (
        Path(request_actions.__file__).parent.parent
        / "checkin_prompt_request_test-user.flag"
    )
    with patch.object(request_actions, "now_timestamp_full", return_value="2026-06-06T00:00:00"), \
        patch.object(
            request_actions,
            "get_user_data",
            return_value={"preferences": {"channel": {"type": "email"}}},
        ), \
        patch.object(request_actions, "_poll_response_file", return_value={}), \
        patch("builtins.open", mock_open()) as opened:
        outcome = request_actions.create_checkin_prompt_request("test-user")

    assert outcome.level == "info"
    assert outcome.request_file == request_file
    assert "via email" in outcome.message
    opened.assert_called_once_with(request_file, "w")


@pytest.mark.ui
def test_create_checkin_prompt_request_warns_when_channel_missing():
    with patch.object(
        request_actions,
        "get_user_data",
        return_value={"preferences": {"channel": {}}},
    ):
        outcome = request_actions.create_checkin_prompt_request("test-user")

    assert outcome.level == "warning"
    assert outcome.title == "User Configuration Error"


@pytest.mark.ui
def test_create_task_reminder_request_writes_selected_task_flag(tmp_path):
    request_file = (
        Path(request_actions.__file__).parent.parent
        / "task_reminder_request_test-user_task-1.flag"
    )
    scheduler = Mock()
    scheduler.select_task_for_reminder.return_value = {
        "id": "task-1",
        "title": "Take meds",
    }
    scheduler_cls = Mock(return_value=scheduler)

    def load_attr(module_name, attr_name):
        attrs = {
            ("tasks", "are_tasks_enabled"): Mock(return_value=True),
            ("tasks", "load_active_tasks"): Mock(return_value=[{"id": "task-1"}]),
            ("tasks.task_data_handlers", "runtime_task_is_completed"): Mock(
                return_value=False
            ),
            ("scheduler.manager", "SchedulerManager"): scheduler_cls,
        }
        return attrs[(module_name, attr_name)]

    with patch.object(request_actions, "_load_attr", side_effect=load_attr), \
        patch.object(request_actions, "now_timestamp_full", return_value="2026-06-06T00:00:00"), \
        patch.object(
            request_actions,
            "get_user_data",
            return_value={"preferences": {"channel": {"type": "discord"}}},
        ), \
        patch("builtins.open", mock_open()) as opened:
        outcome = request_actions.create_task_reminder_request(
            "test-user",
            create_communication_manager=Mock(return_value=Mock()),
        )

    assert outcome.level == "info"
    assert outcome.request_file == request_file
    assert "Task: Take meds" in outcome.message
    opened.assert_called_once_with(request_file, "w")
