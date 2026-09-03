from pathlib import Path
from unittest.mock import Mock, mock_open, patch

import pytest

from ui import request_actions


pytestmark = [pytest.mark.ui]


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


def test_show_request_action_outcome_routes_levels():
    parent = Mock()
    box = Mock()
    request_actions.show_request_action_outcome(parent, None, message_box=box)
    box.information.assert_not_called()

    request_actions.show_request_action_outcome(
        parent,
        request_actions.RequestActionOutcome("info", "T", "ok"),
        message_box=box,
    )
    box.information.assert_called_once_with(parent, "T", "ok")

    request_actions.show_request_action_outcome(
        parent,
        request_actions.RequestActionOutcome("warning", "W", "careful"),
        message_box=box,
    )
    box.warning.assert_called_once_with(parent, "W", "careful")

    request_actions.show_request_action_outcome(
        parent,
        request_actions.RequestActionOutcome("critical", "C", "fail"),
        message_box=box,
    )
    box.critical.assert_called_once_with(parent, "C", "fail")


def test_validate_selected_user_and_service_running():
    parent = Mock()
    box = Mock()
    assert request_actions.validate_selected_user(parent, "user-1", message_box=box) is True
    assert request_actions.validate_selected_user(parent, None, message_box=box) is False
    box.warning.assert_called_once()

    running = Mock()
    running.is_service_running.return_value = (True, 1)
    assert request_actions.validate_service_running(
        parent, running, "Test messages", message_box=box
    ) is True

    stopped = Mock()
    stopped.is_service_running.return_value = (False, None)
    assert request_actions.validate_service_running(
        parent, stopped, "Test messages", message_box=box
    ) is False
    assert box.warning.call_count == 2


def test_get_selected_category_warns_for_placeholder_and_empty_data():
    parent = Mock()
    box = Mock()
    combo = Mock()
    combo.currentIndex.return_value = 0
    assert request_actions.get_selected_category(parent, combo, message_box=box) is None

    combo.currentIndex.return_value = 2
    combo.itemData.return_value = ""
    assert request_actions.get_selected_category(parent, combo, message_box=box) is None

    combo.itemData.return_value = "motivational"
    assert request_actions.get_selected_category(parent, combo, message_box=box) == "motivational"
    assert box.warning.call_count == 2


def test_send_request_wrappers_validate_then_create():
    parent = Mock()
    box = Mock()
    combo = Mock()
    service = Mock()
    outcome = request_actions.RequestActionOutcome("info", "T", "ok")

    with patch.object(request_actions, "validate_selected_user", return_value=False):
        assert request_actions.send_test_message_request(
            parent, "user-1", service, combo, message_box=box
        ) is None

    with patch.object(request_actions, "validate_selected_user", return_value=True), \
        patch.object(request_actions, "validate_service_running", return_value=False):
        assert request_actions.send_checkin_prompt_request(
            parent, "user-1", service, message_box=box
        ) is None

    with patch.object(request_actions, "validate_selected_user", return_value=True), \
        patch.object(request_actions, "validate_service_running", return_value=True), \
        patch.object(request_actions, "get_selected_category", return_value=None):
        assert request_actions.send_test_message_request(
            parent, "user-1", service, combo, message_box=box
        ) is None

    with patch.object(request_actions, "validate_selected_user", return_value=True), \
        patch.object(request_actions, "validate_service_running", return_value=True), \
        patch.object(request_actions, "get_selected_category", return_value="motivational"), \
        patch.object(request_actions, "create_test_message_request", return_value=outcome), \
        patch.object(request_actions, "show_request_action_outcome") as show:
        assert request_actions.send_test_message_request(
            parent, "user-1", service, combo, message_box=box
        ) is outcome
        show.assert_called_once()

    with patch.object(request_actions, "validate_selected_user", return_value=True), \
        patch.object(request_actions, "validate_service_running", return_value=True), \
        patch.object(request_actions, "create_checkin_prompt_request", return_value=outcome), \
        patch.object(request_actions, "show_request_action_outcome"):
        assert request_actions.send_checkin_prompt_request(
            parent, "user-1", service, message_box=box
        ) is outcome

    with patch.object(request_actions, "validate_selected_user", return_value=True), \
        patch.object(request_actions, "validate_service_running", return_value=True), \
        patch.object(request_actions, "create_task_reminder_request", return_value=outcome), \
        patch.object(request_actions, "show_request_action_outcome"):
        assert request_actions.send_task_reminder_request(
            parent,
            "user-1",
            service,
            create_communication_manager=Mock(),
            message_box=box,
        ) is outcome


def test_create_test_message_request_rejects_invalid_category():
    assert request_actions.create_test_message_request("user-1", None) is None
    assert request_actions.create_test_message_request("user-1", "  ") is None


def test_create_checkin_prompt_request_warns_when_preferences_missing():
    with patch.object(request_actions, "get_user_data", return_value={"preferences": None}):
        outcome = request_actions.create_checkin_prompt_request("test-user")
    assert outcome.level == "warning"
    assert "preferences not found" in outcome.message


def test_create_task_reminder_request_warning_paths():
    with patch.object(
        request_actions,
        "_load_attr",
        side_effect=lambda _mod, attr: Mock(return_value=False) if attr == "are_tasks_enabled" else Mock(),
    ), patch.object(request_actions, "get_user_data", return_value={"preferences": {}}):
        outcome = request_actions.create_task_reminder_request(
            "test-user", create_communication_manager=Mock()
        )
    assert outcome.title == "Tasks Not Enabled"

    def load_attr_no_tasks(_mod, attr):
        if attr == "are_tasks_enabled":
            return Mock(return_value=True)
        if attr == "load_active_tasks":
            return Mock(return_value=[])
        return Mock(return_value=False)

    with patch.object(request_actions, "_load_attr", side_effect=load_attr_no_tasks), \
        patch.object(request_actions, "get_user_data", return_value={"preferences": {}}):
        outcome = request_actions.create_task_reminder_request(
            "test-user", create_communication_manager=Mock()
        )
    assert outcome.title == "No Active Tasks"


def test_create_task_reminder_request_reports_unexpected_error():
    with patch.object(request_actions, "get_user_data", side_effect=RuntimeError("boom")):
        outcome = request_actions.create_task_reminder_request(
            "test-user", create_communication_manager=Mock()
        )
    assert outcome.level == "critical"
    assert "Failed to send task reminder" in outcome.message


def test_truncate_and_poll_response_file(tmp_path):
    assert request_actions._truncate_for_dialog("short") == "short"
    assert request_actions._truncate_for_dialog("x" * 120).endswith("...")

    missing = tmp_path / "missing.json"
    with patch.object(request_actions.time, "sleep"):
        assert request_actions._poll_response_file(missing, attempts=2, interval_seconds=0) == {}

    response = tmp_path / "resp.json"
    response.write_text('{"message": "hi"}', encoding="utf-8")
    payload = request_actions._poll_response_file(response, attempts=1, interval_seconds=0)
    assert payload == {"message": "hi"}
    assert not response.exists()


def test_test_message_poll_attempts_uses_ai_timeout():
    with patch(
        "messages.message_data_manager.is_ai_generated_message_category",
        return_value=True,
    ), patch("core.config.AI_PERSONALIZED_MESSAGE_TIMEOUT", 10):
        assert request_actions._test_message_poll_attempts("motivational") >= 30

    with patch(
        "messages.message_data_manager.is_ai_generated_message_category",
        side_effect=RuntimeError("no catalog"),
    ):
        assert request_actions._test_message_poll_attempts("motivational") == 30
