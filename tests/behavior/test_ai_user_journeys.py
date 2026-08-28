"""Mocked AI user journeys through chatbot and handle_user_message.

These replace the safety / routing / capability items on the manual AI
checklist. Tone and phrasing still need occasional live LM Studio review.
"""

from __future__ import annotations

import types
import uuid
from datetime import timedelta
from unittest.mock import MagicMock, patch

import pytest

from ai.chat.action_boundaries import (
    UNCLEAR_USER_INPUT_REPLY,
    find_false_crud_claims,
)
from ai.chat.action_planner import answer_only_plan, clarify_plan
from ai.chat.chatbot import AIChatBotSingleton
from ai.chat.response_generator import get_response_generator
from checkins.checkin_data_manager import store_checkin_response
from communication.command_handlers.shared_types import InteractionResponse, ParsedCommand
from communication.message_processing.command_parser import ParsingResult
from communication.message_processing.conversation_flow_manager import conversation_manager
from communication.message_processing.interaction_manager import (
    InteractionManager,
    handle_user_message,
)
from core import get_user_id_by_identifier
import core.config as app_config
from core.time_utilities import (
    TIMESTAMP_FULL,
    format_timestamp,
    now_datetime_full,
)
from tasks import create_task, load_active_tasks, save_active_tasks
from tasks.task_data_handlers import runtime_task_due_date
from tests.test_helpers.test_utilities import TestUserFactory


pytestmark = [pytest.mark.behavior, pytest.mark.ai]

_FALSE_CRUD_REPLY = (
    "I've created that task for you.\n"
    "I can help you add another if you want."
)


def _unique_username(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


def _create_journey_user(
    test_data_dir: str,
    prefix: str,
    *,
    enable_tasks: bool = True,
    enable_checkins: bool = True,
) -> str:
    username = _unique_username(prefix)
    created = TestUserFactory.create_basic_user(
        username,
        enable_tasks=enable_tasks,
        enable_checkins=enable_checkins,
        test_data_dir=test_data_dir,
    )
    assert created, f"Failed to create journey user {username}"
    return get_user_id_by_identifier(username) or username


def _use_mocked_lm_studio_api(chatbot, return_value=None):
    """Route generate_response through a fake API (not live LM Studio HTTP)."""
    chatbot.lm_studio_available = True
    return (
        patch.object(chatbot, "_ensure_lm_studio_available", return_value=True),
        patch.object(chatbot, "_call_lm_studio_api", return_value=return_value),
    )


def _stub_command_parser(interaction_manager: InteractionManager, parse_fn) -> None:
    real_parser = interaction_manager.command_parser
    interaction_manager.command_parser = types.SimpleNamespace(
        parse=parse_fn,
        _rule_based_parse=real_parser._rule_based_parse,
        get_suggestions=real_parser.get_suggestions,
    )


def _force_low_confidence_parse(interaction_manager: InteractionManager) -> None:
    def _parse(message, user_id=None):
        text = "" if message is None else str(message)
        return ParsingResult(
            ParsedCommand("unknown", {}, 0.05, text),
            0.05,
            "ai_fallback",
        )

    _stub_command_parser(interaction_manager, _parse)


def _mock_planner_plan(plan):
    mock_planner = MagicMock()
    mock_planner.plan_from_message.return_value = plan
    return patch(
        "communication.message_processing.action_plan_executor.get_action_planner",
        return_value=mock_planner,
    )


@pytest.fixture(autouse=True)
def _enable_action_planner(monkeypatch):
    """These journeys mock planner output and require the planner path to run."""
    monkeypatch.setattr(app_config, "AI_ACTION_PLANNER_ENABLED", True)


@pytest.fixture(autouse=True)
def _reset_conversation_state():
    conversation_manager.user_states.clear()
    yield
    conversation_manager.user_states.clear()


@pytest.fixture
def chatbot():
    bot = AIChatBotSingleton()
    original_available = bot.lm_studio_available
    bot.response_cache.clear()
    try:
        yield bot
    finally:
        bot.lm_studio_available = original_available
        bot.response_cache.clear()


@pytest.mark.communication
def test_generate_response_sanitizes_false_crud_chat_reply(test_data_dir, chatbot):
    """Chat replies that claim a completed create are stripped before the user sees them."""
    user_id = _create_journey_user(test_data_dir, "journey-false-crud")
    ensure_patch, api_patch = _use_mocked_lm_studio_api(chatbot, _FALSE_CRUD_REPLY)

    with ensure_patch, api_patch:
        response = chatbot.generate_response(
            "hello",
            user_id=user_id,
            mode="chat",
        )

    assert response
    assert find_false_crud_claims(response) == []
    assert "add another" in response.lower()


@pytest.mark.communication
def test_handle_user_message_chat_fallback_sanitizes_false_crud(test_data_dir, chatbot):
    """handle_user_message chat fallback also runs false-CRUD sanitization."""
    user_id = _create_journey_user(test_data_dir, "journey-crud-msg")
    message = "hello there"
    manager = InteractionManager()
    manager.enable_ai_enhancement = False
    manager.ai_chatbot = chatbot
    _force_low_confidence_parse(manager)
    ensure_patch, api_patch = _use_mocked_lm_studio_api(chatbot, _FALSE_CRUD_REPLY)

    with _mock_planner_plan(answer_only_plan(message, planning_method="test")):
        with ensure_patch, api_patch:
            result = manager.handle_message(user_id, message, "discord")

    assert isinstance(result, InteractionResponse)
    assert result.message
    assert find_false_crud_claims(result.message) == []
    assert load_active_tasks(user_id) == []


@pytest.mark.tasks
@pytest.mark.communication
def test_clear_create_task_command_persists_task(test_data_dir):
    """A clear create-task command persists a real task and does not fake success."""
    user_id = _create_journey_user(test_data_dir, "journey-create-task")

    result = handle_user_message(user_id, "create task take meds", "discord")

    assert result and result.message
    titles = [str(task.get("title", "")).lower() for task in load_active_tasks(user_id)]
    assert "take meds" in titles
    assert find_false_crud_claims(result.message) == []
    assert "take meds" in result.message.lower()


@pytest.mark.tasks
@pytest.mark.communication
def test_everyday_create_task_phrase_persists(test_data_dir):
    """Casual 'I should...' phrasing creates a real task instead of falling through to chat."""
    user_id = _create_journey_user(test_data_dir, "journey-everyday-create")

    result = handle_user_message(user_id, "i should pick up groceries tonight", "discord")

    assert result and result.message
    titles = [str(task.get("title", "")).lower() for task in load_active_tasks(user_id)]
    assert any("pick up groceries" in title for title in titles)
    assert find_false_crud_claims(result.message) == []


@pytest.mark.tasks
@pytest.mark.communication
def test_add_to_my_list_phrase_creates_task(test_data_dir):
    """'add X to my list' creates a task instead of appending to a notebook entry."""
    user_id = _create_journey_user(test_data_dir, "journey-add-to-list")

    result = handle_user_message(user_id, "add laundry to my list", "discord")

    assert result and result.message
    titles = [str(task.get("title", "")).lower() for task in load_active_tasks(user_id)]
    assert any("laundry" in title for title in titles)
    assert find_false_crud_claims(result.message) == []


@pytest.mark.tasks
@pytest.mark.communication
def test_mark_task_done_phrase_completes_task(test_data_dir):
    """'mark <name> done' completes the matching task."""
    user_id = _create_journey_user(test_data_dir, "journey-mark-done")
    tasks = load_active_tasks(user_id)
    tasks.append({"title": "dentist", "id": "tdentist", "short_id": "t1dent"})
    assert save_active_tasks(user_id, tasks)

    result = handle_user_message(user_id, "mark dentist done", "discord")

    assert result and result.message
    assert load_active_tasks(user_id) == []
    assert find_false_crud_claims(result.message) == []


@pytest.mark.tasks
@pytest.mark.communication
def test_still_need_to_phrase_creates_task(test_data_dir):
    """'i still need to...' creates a real task."""
    user_id = _create_journey_user(test_data_dir, "journey-still-need")

    result = handle_user_message(user_id, "i still need to pay rent", "discord")

    assert result and result.message
    titles = [str(task.get("title", "")).lower() for task in load_active_tasks(user_id)]
    assert any("pay rent" in title for title in titles)
    assert find_false_crud_claims(result.message) == []


@pytest.mark.tasks
@pytest.mark.communication
def test_show_my_list_phrase_lists_tasks(test_data_dir):
    """'show my list' lists tasks instead of looking up a notebook entry."""
    user_id = _create_journey_user(test_data_dir, "journey-show-list")
    tasks = load_active_tasks(user_id)
    tasks.append({"title": "laundry", "id": "tlaundry", "short_id": "t1laun"})
    assert save_active_tasks(user_id, tasks)

    result = handle_user_message(user_id, "show my list", "discord")

    assert result and result.message
    assert "laundry" in result.message.lower()
    assert find_false_crud_claims(result.message) == []


@pytest.mark.tasks
@pytest.mark.communication
def test_cross_off_phrase_completes_task(test_data_dir):
    """'cross off X' completes the matching task."""
    user_id = _create_journey_user(test_data_dir, "journey-cross-off")
    tasks = load_active_tasks(user_id)
    tasks.append({"title": "dentist", "id": "tdentist", "short_id": "t1dent"})
    assert save_active_tasks(user_id, tasks)

    result = handle_user_message(user_id, "cross off dentist", "discord")

    assert result and result.message
    assert load_active_tasks(user_id) == []
    assert find_false_crud_claims(result.message) == []


@pytest.mark.tasks
@pytest.mark.communication
def test_make_that_due_updates_recent_task(test_data_dir):
    """After creating a task, 'make that due tomorrow' updates the same task."""
    user_id = _create_journey_user(test_data_dir, "journey-make-that-due")
    create_task(user_id, title="call the dentist")
    result = handle_user_message(user_id, "make that due tomorrow", "discord")

    assert result and result.completed
    tasks = load_active_tasks(user_id)
    dentist = next(
        task for task in tasks if "dentist" in str(task.get("title", "")).lower()
    )
    assert runtime_task_due_date(dentist)
    assert find_false_crud_claims(result.message) == []


@pytest.mark.tasks
@pytest.mark.communication
def test_thats_urgent_updates_recent_task_priority(test_data_dir):
    """'that's urgent' sets priority on the recently created task."""
    user_id = _create_journey_user(test_data_dir, "journey-thats-urgent")
    create_task(user_id, title="call the dentist")
    result = handle_user_message(user_id, "that's urgent", "discord")

    assert result and result.completed
    tasks = load_active_tasks(user_id)
    dentist = next(
        task for task in tasks if "dentist" in str(task.get("title", "")).lower()
    )
    assert str(dentist.get("priority", "")).lower() == "urgent"
    assert find_false_crud_claims(result.message) == []


@pytest.mark.tasks
@pytest.mark.communication
def test_mark_that_done_completes_recent_task(test_data_dir):
    """'mark that done' completes the recently created task."""
    user_id = _create_journey_user(test_data_dir, "journey-mark-that")
    create_task(user_id, title="call the dentist")
    result = handle_user_message(user_id, "mark that done", "discord")

    assert result and result.completed
    assert load_active_tasks(user_id) == []
    assert find_false_crud_claims(result.message) == []


@pytest.mark.tasks
@pytest.mark.communication
def test_ambiguous_add_task_clarifies_without_creating(test_data_dir):
    """Ambiguous task requests ask for details instead of inventing a create."""
    user_id = _create_journey_user(test_data_dir, "journey-ambiguous-task")
    message = "Can you add a task?"
    manager = InteractionManager()
    manager.enable_ai_enhancement = False
    _force_low_confidence_parse(manager)

    with _mock_planner_plan(clarify_plan(message, "What should the task be called?")):
        result = manager.handle_message(user_id, message, "discord")

    assert result and result.message
    assert "what should the task be called" in result.message.lower()
    assert load_active_tasks(user_id) == []
    assert find_false_crud_claims(result.message) == []


@pytest.mark.checkins
def test_checkin_status_prompt_includes_analysis_when_data_exists(
    test_data_dir, chatbot
):
    """Wellness questions with check-ins send honest analysis in the model prompt."""
    user_id = _create_journey_user(test_data_dir, "journey-checkin-data")
    base = now_datetime_full()
    for offset in range(3):
        store_checkin_response(
            user_id,
            {
                "mood": 4,
                "energy": 3,
                "ate_breakfast": True,
                "brushed_teeth": True,
                "submitted_at": format_timestamp(
                    base - timedelta(days=offset), TIMESTAMP_FULL
                ),
            },
        )

    ensure_patch, api_patch = _use_mocked_lm_studio_api(
        chatbot, "Your recent check-ins look steady. How are you feeling today?"
    )
    with ensure_patch, api_patch as mock_api:
        response = chatbot.generate_contextual_response(user_id, "How am I doing?")

    assert response
    assert find_false_crud_claims(response) == []
    mock_api.assert_called()
    messages = mock_api.call_args.kwargs.get("messages") or mock_api.call_args.args[0]
    prompt_text = " ".join(
        str(item.get("content", "")) for item in messages if isinstance(item, dict)
    )
    assert "average mood has been 4.0" in prompt_text
    assert "check-ins" in prompt_text.lower()


@pytest.mark.checkins
def test_checkin_status_reply_is_honest_when_no_checkins(test_data_dir, chatbot):
    """A new user asking how they are doing does not get invented check-in claims."""
    user_id = _create_journey_user(test_data_dir, "journey-checkin-empty")

    response = chatbot.generate_contextual_response(user_id, "How am I doing?")

    assert response
    lowered = response.lower()
    assert "don't have check-in" in lowered or "do not have check-in" in lowered
    assert find_false_crud_claims(response) == []
    assert "average mood" not in lowered


@pytest.mark.tasks
def test_disabled_tasks_prompt_and_reply_stay_within_capabilities(
    test_data_dir, chatbot
):
    """Disabled task management is stated in context and replies do not fake a create."""
    user_id = _create_journey_user(
        test_data_dir,
        "journey-tasks-off",
        enable_tasks=False,
    )

    messages = get_response_generator().create_comprehensive_context_prompt(
        user_id, "can you create a task for me"
    )
    system_content = messages[0]["content"]
    assert "task management is disabled" in system_content
    assert "ACTION BOUNDARIES" in system_content

    ensure_patch, api_patch = _use_mocked_lm_studio_api(chatbot, _FALSE_CRUD_REPLY)
    with ensure_patch, api_patch:
        response = chatbot.generate_response(
            "can you create a task for me",
            user_id=user_id,
            mode="chat",
        )

    assert response
    assert find_false_crud_claims(response) == []
    assert load_active_tasks(user_id) == []


@pytest.mark.communication
def test_numeric_only_prompt_returns_unclear_reply(test_data_dir, chatbot):
    """Digits-only chat input gets the safe unclear reply, not a hallucinated action."""
    user_id = _create_journey_user(test_data_dir, "journey-numeric")

    response = chatbot.generate_response("123456", user_id=user_id, mode="chat")

    assert response == UNCLEAR_USER_INPUT_REPLY
    assert find_false_crud_claims(response) == []


@pytest.mark.communication
def test_numeric_only_handle_user_message_does_not_invent_action(test_data_dir):
    """Digits-only Discord/email input does not create work or claim it did."""
    user_id = _create_journey_user(test_data_dir, "journey-numeric-msg")

    result = handle_user_message(user_id, "123456", "discord")

    assert result and result.message
    assert find_false_crud_claims(result.message) == []
    assert load_active_tasks(user_id) == []
    lowered = result.message.lower()
    assert (
        result.message == UNCLEAR_USER_INPUT_REPLY
        or "not sure" in lowered
        or "rephrase" in lowered
        or "help" in lowered
    )
