"""Failed saves retain conversation drafts and do not claim completion."""

from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from communication.message_processing.flows.note_flow import NoteFlowMixin
from communication.message_processing.flows.checkin_flow import CheckinFlowMixin

pytestmark = [pytest.mark.behavior, pytest.mark.communication]


@pytest.mark.parametrize(
    "method,storage_method,body",
    [
        ("_finalize_note_without_body", "create_note", None),
        ("_finalize_journal_without_body", "create_journal", None),
        ("_finalize_list_from_state", "create_list", None),
        ("_handle_note_body_flow", "create_note", "Private draft #work"),
        ("_handle_journal_body_flow", "create_journal", "Private draft #work"),
    ],
)
@pytest.mark.notebook
def test_notebook_failed_save_retains_draft_then_success_clears(monkeypatch, method, storage_method, body):
    from notebook import notebook_data_manager
    flow = NoteFlowMixin()
    state = {"data": {"title": "Draft title", "tags": [], "items": ["Draft item"]}}
    flow.user_states = {"draft-user": state}
    flow._save_user_states = Mock()
    flow._try_flow_control_command = Mock(return_value=None)
    flow._entry_short_id = Mock(return_value="n123abc")
    flow._clear_flow_state = Mock(side_effect=lambda user_id, **_: flow.user_states.pop(user_id))
    persist = Mock(return_value=None)
    monkeypatch.setattr(notebook_data_manager, storage_method, persist)
    args = ("draft-user", state) if body is None else ("draft-user", state, body)
    reply, completed = getattr(flow, method)(*args)
    assert not completed
    assert "couldn't confirm" in reply
    assert flow.user_states["draft-user"] is state
    assert state["data"]["items"] == ["Draft item"]
    assert state["data"]["tags"] == []
    if body:
        assert state["data"]["draft_body"] == body
    flow._clear_flow_state.assert_not_called()

    persist.return_value = SimpleNamespace(tags=[])
    _, completed = getattr(flow, method)(*args)
    assert completed
    assert "draft-user" not in flow.user_states
    flow._clear_flow_state.assert_called_once()


@pytest.mark.parametrize("failure", ["email", "profile", "exception"])
def test_profile_save_failure_gives_check_before_retry(monkeypatch, failure):
    from communication.command_handlers import profile_handler
    apply = Mock(return_value=SimpleNamespace(
        failed_field="email" if failure == "email" else None, success=False
    ))
    if failure == "exception":
        apply.side_effect = RuntimeError("PRIVATE ERROR")
    monkeypatch.setattr(profile_handler, "apply_profile_updates", apply)
    response = profile_handler.ProfileHandler()._handle_update_profile(
        "profile-user", {"email": "private@example.com"}
    )
    assert "show my profile" in response.message
    assert "couldn't confirm" in response.message
    assert "PRIVATE" not in response.message
    assert "private@example.com" not in response.message


@pytest.mark.parametrize("appending", [False, True])
@pytest.mark.notebook
def test_failed_notebook_edit_retains_text_and_session(monkeypatch, appending):
    from notebook import notebook_service
    flow = NoteFlowMixin()
    state = {"data": {"entry_ref": "n123abc", "mode": "append" if appending else "replace"}}
    flow.user_states = {"draft-user": state}
    flow._save_user_states = Mock()
    flow._clear_flow_state = Mock()
    flow._try_flow_control_command = Mock(return_value=None)
    persist = Mock(side_effect=RuntimeError("PRIVATE ERROR"))
    monkeypatch.setattr(notebook_service, "append_entry_body" if appending else "replace_entry_body", persist)
    reply, completed = flow._handle_entry_edit_flow("draft-user", state, "Private edit")
    assert not completed
    assert "PRIVATE ERROR" not in reply
    assert state["data"]["draft_body"] == "Private edit"
    flow._clear_flow_state.assert_not_called()


@pytest.mark.checkins
def test_checkin_failed_save_retries_same_submission_before_completion(monkeypatch):
    from checkins import checkin_data_manager
    flow = CheckinFlowMixin()
    state = {"data": {"mood": 3}, "question_order": ["mood"], "current_question_index": 1}
    flow.user_states = {"checkin-user": state}
    flow._save_user_states = Mock()
    flow._clear_flow_state = Mock()
    flow._generate_completion_message = Mock(return_value="Check-in saved")
    persist = Mock(side_effect=[False, True])
    monkeypatch.setattr(checkin_data_manager, "store_checkin_response", persist)
    reply, completed = flow._complete_checkin("checkin-user", state)
    assert not completed
    assert "retry" in reply
    assert "recorded what I could" not in reply
    assert state["data"]["mood"] == 3
    flow._clear_flow_state.assert_not_called()
    flow._generate_completion_message.assert_not_called()
    reply, completed = flow._handle_checkin("checkin-user", state, "retry")
    assert completed
    assert reply == "Check-in saved"
    first, second = [call.args[1] for call in persist.call_args_list]
    assert first["id"] == second["id"]
    assert first["submitted_at"] == second["submitted_at"]
    flow._clear_flow_state.assert_called_once()
