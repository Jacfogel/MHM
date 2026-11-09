"""Task command failures give safe recovery steps instead of empty responses."""

from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from communication.command_handlers import task_handler
from communication.command_handlers.shared_types import InteractionResponse, ParsedCommand

pytestmark = [pytest.mark.behavior, pytest.mark.communication, pytest.mark.tasks]


@pytest.mark.parametrize("raises", [False, True], ids=["unconfirmed", "exception"])
@pytest.mark.parametrize(
    "intent,service_method,entities,recovery",
    [
        ("create_task", "create_task", {"title": "Private title"}, "list tasks"),
        ("create_task_from_template", "build_task_data_from_template",
         {"template_ref": "phone_call"}, "template"),
        ("complete_task", "complete_task", {"task_identifier": "1"}, "complete task"),
        ("uncomplete_task", "restore_task", {"task_identifier": "1"}, "list tasks"),
        ("delete_task", "delete_task", {"task_identifier": "1"}, "delete task"),
        ("update_task", "update_task", {"task_identifier": "1", "priority": "high"}, "task details"),
        ("append_note_to_task", "append_task_description",
         {"task_identifier": "1", "note_text": "Private note"}, "Keep a copy"),
        ("add_link_to_task", "append_task_link",
         {"task_identifier": "1", "link_url": "https://private.example"}, "Keep the URL"),
        ("remove_link_from_task", "remove_task_link",
         {"task_identifier": "1", "link_url": "https://private.example"}, "remove link"),
    ],
)
def test_task_command_failure_has_recovery(
    monkeypatch, intent, service_method, entities, recovery, raises
):
    """Exercise each command's service rejection and unexpected exception boundary."""
    service = Mock()
    task = {"id": "task-1", "title": "Private title", "short_id": "abc123"}
    service.load_active_tasks.return_value = [task]
    service.load_completed_tasks.return_value = [task]
    service.get_completed_task_candidates.return_value = [task]
    service.task_identifier.side_effect = lambda row: row["id"]
    service.task_short_identifier.side_effect = lambda row: row["short_id"]
    service.get_task_template.return_value = SimpleNamespace(template_id="phone_call")
    service.prepare_create_task_data.return_value = SimpleNamespace(
        task_data={"title": "Private title"}, valid_due_date=None,
        valid_due_time=None, priority="medium", priority_was_provided=False,
        tags=[], recurrence_pattern=None, recurrence_interval=1,
    )
    operation = getattr(service, service_method)
    operation.return_value = "missing" if service_method in {
        "append_task_link", "remove_task_link"
    } else False
    if raises:
        operation.side_effect = RuntimeError("sensitive exception details")
    monkeypatch.setattr(task_handler, "_task_service", lambda: service)
    log_error = Mock()
    monkeypatch.setattr(task_handler.logger, "error", log_error)
    handler = task_handler.TaskManagementHandler()
    monkeypatch.setattr(handler, "_get_task_candidates", lambda *_: [task])

    # Restore is routed as 'uncomplete_task' by handle().
    response = handler.handle(
        "failure-test-user", ParsedCommand(intent, entities, 1.0, "")
    )

    operation.assert_called_once()
    assert isinstance(response, InteractionResponse)
    assert response.completed
    assert recovery in response.message
    assert "sensitive exception details" not in response.message
    assert "Private" not in response.message
    assert "https://private.example" not in response.message
    if not raises:
        log_error.assert_called_once()
        assert "failure-test-user" in log_error.call_args.args[0]
        if intent not in {"create_task", "create_task_from_template"}:
            assert "task-1" in log_error.call_args.args[0]


def test_confirmed_delete_failure_explains_how_to_retry(monkeypatch):
    """A consumed deletion confirmation needs a fresh explicit delete command."""
    service = Mock()
    service.delete_task.return_value = False
    monkeypatch.setattr(task_handler, "_task_service", lambda: service)
    user_id = "confirmed-delete-failure"
    task_handler.PENDING_DELETIONS[user_id] = "task-1"
    response = task_handler.TaskManagementHandler()._handle_delete_task(user_id, {})
    assert "list tasks" in response.message
    assert "delete task <number>" in response.message
    assert user_id not in task_handler.PENDING_DELETIONS
    service.delete_task.assert_called_once_with(user_id, "task-1")
