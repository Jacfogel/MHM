"""Safe failure behavior for prompt helpers identified by the project audit."""

from unittest.mock import Mock

import pytest

from ai.chat import action_planner, response_postprocess
from ai.prompts import planning
from ai.prompts.action_catalog import AIActionCatalog

pytestmark = [pytest.mark.unit, pytest.mark.ai]


def test_history_read_failure_omits_assistant_reference(monkeypatch):
    from user.context_manager import user_context_manager

    monkeypatch.setattr(
        user_context_manager,
        "get_session_conversation_history",
        Mock(side_effect=OSError("Synthetic history read failure")),
    )
    assert action_planner._recent_assistant_turns_for_planning("synthetic-user") == []


def test_invalid_followup_input_cannot_enable_history_reference():
    assert action_planner._needs_assistant_reference(None) is False  # type: ignore[arg-type]


def test_invalid_selection_cannot_supply_entity_grounding():
    assert action_planner._selected_assistant_grounding(None, ["Water plants"]) == ""  # type: ignore[arg-type]


def test_invalid_response_does_not_trigger_a_canned_replacement():
    assert response_postprocess._needs_content_repair(object()) is False  # type: ignore[arg-type]


def test_invalid_field_metadata_is_not_silently_converted_to_an_empty_contract():
    catalog = AIActionCatalog({"broken": Mock(fields=None)})
    with pytest.raises(TypeError):
        catalog.to_planning_field_contract()


def test_contract_failure_stops_prompt_generation_before_any_api_call(monkeypatch):
    request = Mock()
    monkeypatch.setattr(action_planner, "call_openai_api", request)
    monkeypatch.setattr(
        planning,
        "get_action_catalog",
        Mock(side_effect=RuntimeError("Synthetic catalog failure")),
    )
    with pytest.raises(RuntimeError):
        planning.build_planning_system_prompt()
    assert (
        action_planner.ActionPlanner().build_planning_messages(
            None, "create task Water plants"
        )
        == []
    )
    request.assert_not_called()
