"""
Behavior tests for InteractionManager routing when AI_ACTION_PLANNER_ENABLED is on.

Uses mocked planner output so tests do not require LM Studio or Discord.
"""

from __future__ import annotations

import types
import uuid
from unittest.mock import MagicMock, patch

import pytest

import core.config as app_config
from ai.chat.action_planner import answer_only_plan, clarify_plan
from ai.prompts.action_catalog import AIActionPlan, AIActionRequest
from communication.command_handlers.shared_types import InteractionResponse, ParsedCommand
from communication.message_processing.command_parser import ParsingResult
from communication.message_processing.conversation_flow_manager import conversation_manager
from communication.message_processing.interaction_manager import InteractionManager
from core import get_user_data, get_user_id_by_identifier
from tasks import (
    complete_task,
    create_task,
    load_active_tasks,
    load_completed_tasks,
)
from tests.test_helpers.test_utilities import TestUserFactory


pytestmark = [pytest.mark.behavior, pytest.mark.ai, pytest.mark.communication]


def _stub_command_parser(interaction_manager: InteractionManager, parse_fn) -> None:
    """Replace parser on this manager only; do not mutate the shared singleton."""
    real_parser = interaction_manager.command_parser
    interaction_manager.command_parser = types.SimpleNamespace(
        parse=parse_fn,
        _rule_based_parse=real_parser._rule_based_parse,
        get_suggestions=real_parser.get_suggestions,
    )


def _force_low_confidence_parse(interaction_manager: InteractionManager) -> None:
    """Force messages onto the contextual-chat / planner path."""

    def _parse(message, user_id=None):
        text = "" if message is None else str(message)
        return ParsingResult(
            ParsedCommand("unknown", {}, 0.05, text),
            0.05,
            "ai_fallback",
        )

    _stub_command_parser(interaction_manager, _parse)


def _force_high_confidence_create_task(interaction_manager: InteractionManager) -> None:
    """Force structured-command path with a confident create_task parse."""

    def _parse(message, user_id=None):
        text = "" if message is None else str(message)
        return ParsingResult(
            ParsedCommand("create_task", {"title": "Buy milk"}, 0.95, text),
            0.95,
            "rule_based",
        )

    _stub_command_parser(interaction_manager, _parse)


def _mock_planner_plan(plan):
    """Patch get_action_planner in the executor module used by InteractionManager."""
    mock_planner = MagicMock()
    mock_planner.plan_from_message.return_value = plan
    return patch(
        "communication.message_processing.action_plan_executor.get_action_planner",
        return_value=mock_planner,
    )


def _suppress_planner_result_aware(interaction_manager: InteractionManager) -> None:
    """Routing/parity tests assert handler outcomes, not LM Studio reply wording."""
    ai_chatbot = MagicMock()
    ai_chatbot.is_ai_available.return_value = False
    interaction_manager.ai_chatbot = ai_chatbot


@pytest.fixture
def planner_enabled(monkeypatch):
    """Enable the action planner flag for one test."""
    monkeypatch.setattr(app_config, "AI_ACTION_PLANNER_ENABLED", True)


@pytest.fixture(autouse=True)
def _reset_conversation_state():
    """Keep check-in flow state isolated across routing tests."""
    conversation_manager.user_states.clear()
    yield
    conversation_manager.user_states.clear()


@pytest.mark.tasks
def test_planner_execute_action_creates_task(test_data_dir, planner_enabled):
    """Low-confidence message + execute_action plan routes through dispatcher."""
    user_id = "planner-routing-create-task"
    TestUserFactory.create_basic_user(
        user_id,
        enable_tasks=True,
        test_data_dir=test_data_dir,
    )
    message = "could you remind me tomorrow about the dentist"
    plan = AIActionPlan(
        response_intent="execute_action",
        actions=(
            AIActionRequest(
                action_name="create_task",
                entities={"title": "Dentist appointment"},
                confidence=0.92,
                source_message=message,
            ),
        ),
        source_message=message,
        planning_method="test",
    )

    interaction_manager = InteractionManager()
    interaction_manager.enable_ai_enhancement = False
    _suppress_planner_result_aware(interaction_manager)
    _force_low_confidence_parse(interaction_manager)

    with _mock_planner_plan(plan):
        response = interaction_manager.handle_message(user_id, message, "discord")

    assert response is not None
    assert "Dentist appointment" in response.message
    titles = [task.get("title") for task in load_active_tasks(user_id)]
    assert "Dentist appointment" in titles


def test_planner_clarify_returns_question(test_data_dir, planner_enabled):
    """Clarify plans return the planner question without side effects."""
    user_id = "planner-routing-clarify"
    TestUserFactory.create_basic_user(
        user_id,
        enable_tasks=True,
        test_data_dir=test_data_dir,
    )
    message = "add a task"
    plan = clarify_plan(message, "What should the task be called?")

    interaction_manager = InteractionManager()
    interaction_manager.enable_ai_enhancement = False
    _force_low_confidence_parse(interaction_manager)

    with _mock_planner_plan(plan):
        response = interaction_manager.handle_message(user_id, message, "discord")

    assert response is not None
    assert response.message == "What should the task be called?"
    assert response.completed is True
    assert load_active_tasks(user_id) == []


def test_planner_answer_only_uses_chat_generation(test_data_dir, planner_enabled):
    """Answer-only plans delegate to chat response generation."""
    user_id = "planner-routing-answer"
    TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
    message = "I'm feeling overwhelmed today"
    plan = answer_only_plan(message, planning_method="test")

    interaction_manager = InteractionManager()
    interaction_manager.enable_ai_enhancement = False
    _force_low_confidence_parse(interaction_manager)
    interaction_manager.ai_chatbot = MagicMock()
    interaction_manager.ai_chatbot.generate_response.return_value = (
        "That sounds hard. Want to talk through what's on your plate?"
    )

    with _mock_planner_plan(plan):
        response = interaction_manager.handle_message(user_id, message, "discord")

    assert response is not None
    assert "overwhelmed" in response.message.lower() or "plate" in response.message.lower()
    interaction_manager.ai_chatbot.generate_response.assert_called_once_with(
        message,
        user_id=user_id,
        mode="chat",
    )


def test_planner_none_falls_back_to_contextual_chat(test_data_dir, planner_enabled):
    """When planning returns None, InteractionManager uses contextual chat."""
    user_id = "planner-routing-fallback"
    TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
    message = "what should I focus on this week?"

    interaction_manager = InteractionManager()
    interaction_manager.enable_ai_enhancement = False
    _force_low_confidence_parse(interaction_manager)
    interaction_manager._handle_contextual_chat = MagicMock(
        return_value=InteractionResponse("Contextual chat fallback reply.", True)
    )

    with _mock_planner_plan(None):
        response = interaction_manager.handle_message(user_id, message, "discord")

    assert response is not None
    assert response.message == "Contextual chat fallback reply."
    interaction_manager._handle_contextual_chat.assert_called_once_with(
        user_id, message, "discord"
    )


@pytest.mark.tasks
def test_planner_none_retries_partial_structured_command(test_data_dir, planner_enabled):
    """When planner returns None but parse had usable intent, dispatch structured command."""
    user_id = "planner-routing-partial"
    TestUserFactory.create_basic_user(
        user_id,
        enable_tasks=True,
        test_data_dir=test_data_dir,
    )
    message = "maybe add task partial parse test"

    interaction_manager = InteractionManager()
    interaction_manager.enable_ai_enhancement = False

    def _parse(message, user_id=None):
        text = "" if message is None else str(message)
        return ParsingResult(
            ParsedCommand(
                "create_task",
                {"title": "Partial parse test"},
                0.2,
                text,
            ),
            0.2,
            "rule_based",
        )

    _stub_command_parser(interaction_manager, _parse)

    with _mock_planner_plan(None):
        response = interaction_manager.handle_message(user_id, message, "discord")

    assert response is not None
    titles = [task.get("title") for task in load_active_tasks(user_id)]
    assert "Partial parse test" in titles


def _force_confident_parse(
    interaction_manager: InteractionManager,
    intent: str,
    entities: dict,
    *,
    confidence: float = 0.95,
    message: str = "test message",
) -> None:
    """Force structured-command path with a confident parse for a given intent."""

    def _parse(msg, user_id=None):
        text = "" if msg is None else str(msg)
        return ParsingResult(
            ParsedCommand(intent, entities, confidence, text),
            confidence,
            "rule_based",
        )

    _stub_command_parser(interaction_manager, _parse)


def _execute_action_plan(message: str, action_name: str, entities: dict) -> AIActionPlan:
    """Build an execute_action plan for parity tests."""
    return AIActionPlan(
        response_intent="execute_action",
        actions=(
            AIActionRequest(
                action_name=action_name,
                entities=entities,
                confidence=0.92,
                source_message=message,
            ),
        ),
        source_message=message,
        planning_method="test",
    )


def _run_intent_parity(
    test_data_dir,
    planner_enabled,
    *,
    rule_user: str,
    planner_user: str,
    message: str,
    intent: str,
    entities: dict,
    seed_user,
    assert_parity,
    enable_tasks: bool = True,
    enable_checkins: bool = True,
) -> None:
    """Run the same intent through rule-parser and planner paths."""
    TestUserFactory.create_basic_user(
        rule_user,
        enable_tasks=enable_tasks,
        enable_checkins=enable_checkins,
        test_data_dir=test_data_dir,
    )
    TestUserFactory.create_basic_user(
        planner_user,
        enable_tasks=enable_tasks,
        enable_checkins=enable_checkins,
        test_data_dir=test_data_dir,
    )
    seed_user(rule_user)
    seed_user(planner_user)

    rule_manager = InteractionManager()
    rule_manager.enable_ai_enhancement = False
    _force_confident_parse(rule_manager, intent, entities, message=message)
    rule_response = rule_manager.handle_message(rule_user, message, "discord")

    planner_manager = InteractionManager()
    planner_manager.enable_ai_enhancement = False
    _suppress_planner_result_aware(planner_manager)
    _force_low_confidence_parse(planner_manager)
    plan = _execute_action_plan(message, intent, entities)

    with _mock_planner_plan(plan):
        planner_response = planner_manager.handle_message(
            planner_user, message, "discord"
        )

    assert rule_response is not None
    assert planner_response is not None
    assert_parity(rule_user, planner_user, rule_response, planner_response)


def _run_task_intent_parity(
    test_data_dir,
    planner_enabled,
    *,
    rule_user: str,
    planner_user: str,
    message: str,
    intent: str,
    entities: dict,
    seed_user,
    assert_parity,
) -> None:
    """Run the same task intent through rule-parser and planner paths."""
    _run_intent_parity(
        test_data_dir,
        planner_enabled,
        rule_user=rule_user,
        planner_user=planner_user,
        message=message,
        intent=intent,
        entities=entities,
        seed_user=seed_user,
        assert_parity=assert_parity,
        enable_tasks=True,
        enable_checkins=True,
    )


def _resolved_user_id(user_id: str) -> str:
    return get_user_id_by_identifier(user_id) or user_id


def _preferred_name(user_id: str) -> str | None:
    resolved = _resolved_user_id(user_id)
    data = get_user_data(resolved, "context", normalize_on_read=True)
    return (data.get("context") or {}).get("preferred_name")


def _active_task_by_title(user_id: str, title: str) -> dict | None:
    return next(
        (task for task in load_active_tasks(user_id) if task.get("title") == title),
        None,
    )


def _completed_task_by_title(user_id: str, title: str) -> dict | None:
    return next(
        (task for task in load_completed_tasks(user_id) if task.get("title") == title),
        None,
    )


@pytest.mark.tasks
def test_create_task_parity_rule_parser_vs_planner(test_data_dir, planner_enabled):
    """create_task via high-confidence rule parse matches planner execute_action outcome."""
    task_title = "Buy groceries"
    message = "add task buy groceries"

    rule_user = "parity-create-rule"
    TestUserFactory.create_basic_user(
        rule_user,
        enable_tasks=True,
        test_data_dir=test_data_dir,
    )
    rule_manager = InteractionManager()
    rule_manager.enable_ai_enhancement = False
    _force_confident_parse(
        rule_manager,
        "create_task",
        {"title": task_title},
        message=message,
    )
    rule_response = rule_manager.handle_message(rule_user, message, "discord")

    planner_user = "parity-create-planner"
    TestUserFactory.create_basic_user(
        planner_user,
        enable_tasks=True,
        test_data_dir=test_data_dir,
    )
    planner_manager = InteractionManager()
    planner_manager.enable_ai_enhancement = False
    _suppress_planner_result_aware(planner_manager)
    _force_low_confidence_parse(planner_manager)
    plan = _execute_action_plan(message, "create_task", {"title": task_title})

    with _mock_planner_plan(plan):
        planner_response = planner_manager.handle_message(
            planner_user, message, "discord"
        )

    assert rule_response is not None
    assert planner_response is not None
    rule_titles = [task.get("title") for task in load_active_tasks(rule_user)]
    planner_titles = [task.get("title") for task in load_active_tasks(planner_user)]
    assert task_title in rule_titles
    assert task_title in planner_titles


@pytest.mark.tasks
def test_list_tasks_parity_rule_parser_vs_planner(test_data_dir, planner_enabled):
    """list_tasks via rule parse and planner path both surface the same active task."""
    task_title = "Water plants"
    message = "show my tasks"

    rule_user = "parity-list-rule"
    TestUserFactory.create_basic_user(
        rule_user,
        enable_tasks=True,
        test_data_dir=test_data_dir,
    )
    create_task(rule_user, task_title, due_date="2026-07-15")

    rule_manager = InteractionManager()
    rule_manager.enable_ai_enhancement = False
    _force_confident_parse(rule_manager, "list_tasks", {}, message=message)
    rule_response = rule_manager.handle_message(rule_user, message, "discord")

    planner_user = "parity-list-planner"
    TestUserFactory.create_basic_user(
        planner_user,
        enable_tasks=True,
        test_data_dir=test_data_dir,
    )
    create_task(planner_user, task_title, due_date="2026-07-15")

    planner_manager = InteractionManager()
    planner_manager.enable_ai_enhancement = False
    _suppress_planner_result_aware(planner_manager)
    _force_low_confidence_parse(planner_manager)
    plan = _execute_action_plan(message, "list_tasks", {})

    with _mock_planner_plan(plan):
        planner_response = planner_manager.handle_message(
            planner_user, message, "discord"
        )

    assert rule_response is not None
    assert planner_response is not None
    assert task_title in rule_response.message
    assert task_title in planner_response.message


@pytest.mark.tasks
def test_complete_task_parity_rule_parser_vs_planner(test_data_dir, planner_enabled):
    """complete_task via rule parse and planner path both complete the same task."""
    task_title = "Call dentist"
    message = f"complete task {task_title}"

    rule_user = "parity-complete-rule"
    TestUserFactory.create_basic_user(
        rule_user,
        enable_tasks=True,
        test_data_dir=test_data_dir,
    )
    create_task(rule_user, task_title, due_date="2026-07-15")

    rule_manager = InteractionManager()
    rule_manager.enable_ai_enhancement = False
    _force_confident_parse(
        rule_manager,
        "complete_task",
        {"task_identifier": task_title},
        message=message,
    )
    rule_response = rule_manager.handle_message(rule_user, message, "discord")

    planner_user = "parity-complete-planner"
    TestUserFactory.create_basic_user(
        planner_user,
        enable_tasks=True,
        test_data_dir=test_data_dir,
    )
    create_task(planner_user, task_title, due_date="2026-07-15")

    planner_manager = InteractionManager()
    planner_manager.enable_ai_enhancement = False
    _suppress_planner_result_aware(planner_manager)
    _force_low_confidence_parse(planner_manager)
    plan = _execute_action_plan(
        message,
        "complete_task",
        {"task_identifier": task_title},
    )

    with _mock_planner_plan(plan):
        planner_response = planner_manager.handle_message(
            planner_user, message, "discord"
        )

    assert rule_response is not None
    assert planner_response is not None
    assert load_active_tasks(rule_user) == []
    assert load_active_tasks(planner_user) == []
    assert any(
        task.get("title") == task_title for task in load_completed_tasks(rule_user)
    )
    assert any(
        task.get("title") == task_title for task in load_completed_tasks(planner_user)
    )


@pytest.mark.tasks
def test_update_task_parity_rule_parser_vs_planner(test_data_dir, planner_enabled):
    """update_task via rule parse and planner path both persist the same field changes."""
    task_title = "Weekly report"
    message = "update task 1 priority high"
    entities = {"task_identifier": "1", "priority": "high"}

    def seed(user_id: str) -> None:
        create_task(user_id, task_title, due_date="2026-07-15", priority="low")

    def assert_parity(rule_user, planner_user, rule_response, planner_response):
        del rule_response, planner_response
        for user_id in (rule_user, planner_user):
            task = _active_task_by_title(user_id, task_title)
            assert task is not None
            assert task.get("priority") == "high"

    _run_task_intent_parity(
        test_data_dir,
        planner_enabled,
        rule_user="parity-update-rule",
        planner_user="parity-update-planner",
        message=message,
        intent="update_task",
        entities=entities,
        seed_user=seed,
        assert_parity=assert_parity,
    )


@pytest.mark.tasks
def test_delete_task_parity_rule_parser_vs_planner(test_data_dir, planner_enabled):
    """delete_task via rule parse and planner path both remove the task."""
    task_title = "Old reminder"
    message = "delete task 1"
    entities = {"task_identifier": "1"}

    def seed(user_id: str) -> None:
        create_task(user_id, task_title, due_date="2026-07-15")

    def assert_parity(rule_user, planner_user, rule_response, planner_response):
        del rule_response, planner_response
        assert load_active_tasks(rule_user) == []
        assert load_active_tasks(planner_user) == []

    _run_task_intent_parity(
        test_data_dir,
        planner_enabled,
        rule_user="parity-delete-rule",
        planner_user="parity-delete-planner",
        message=message,
        intent="delete_task",
        entities=entities,
        seed_user=seed,
        assert_parity=assert_parity,
    )


@pytest.mark.tasks
def test_append_note_to_task_parity_rule_parser_vs_planner(test_data_dir, planner_enabled):
    """append_note_to_task via both paths appends the same note text."""
    task_title = "Pharmacy pickup"
    note_text = "Call before noon"
    message = f"append note to task 1 {note_text}"
    entities = {"task_identifier": "1", "note_text": note_text}

    def seed(user_id: str) -> None:
        create_task(user_id, task_title, due_date="2026-07-15")

    def assert_parity(rule_user, planner_user, rule_response, planner_response):
        del rule_response, planner_response
        for user_id in (rule_user, planner_user):
            task = _active_task_by_title(user_id, task_title)
            assert task is not None
            assert note_text in (task.get("description") or "")

    _run_task_intent_parity(
        test_data_dir,
        planner_enabled,
        rule_user="parity-append-note-rule",
        planner_user="parity-append-note-planner",
        message=message,
        intent="append_note_to_task",
        entities=entities,
        seed_user=seed,
        assert_parity=assert_parity,
    )


@pytest.mark.tasks
def test_task_stats_parity_rule_parser_vs_planner(test_data_dir, planner_enabled):
    """task_stats via both paths returns the same summary markers."""
    task_title = "High priority chore"
    message = "show task stats"
    entities = {"days": 7, "period_name": "this week"}
    # Unique users: fixed parity-stats-* names reuse xdist dirs and accumulate tasks.
    suffix = uuid.uuid4().hex[:8]

    def seed(user_id: str) -> None:
        create_task(
            user_id,
            task_title,
            due_date="2026-07-15",
            priority="high",
        )

    def assert_parity(rule_user, planner_user, rule_response, planner_response):
        for response in (rule_response, planner_response):
            lowered = response.message.lower()
            assert "task statistics" in lowered
            assert "active tasks" in lowered
            assert "high: 1 tasks" in lowered

    _run_task_intent_parity(
        test_data_dir,
        planner_enabled,
        rule_user=f"parity-stats-rule-{suffix}",
        planner_user=f"parity-stats-planner-{suffix}",
        message=message,
        intent="task_stats",
        entities=entities,
        seed_user=seed,
        assert_parity=assert_parity,
    )


@pytest.mark.tasks
def test_uncomplete_task_parity_rule_parser_vs_planner(test_data_dir, planner_enabled):
    """uncomplete_task via both paths restores the same completed task to active."""
    task_title = "Restore me"
    message = f"restore task {task_title}"
    entities = {"task_identifier": task_title}

    def seed(user_id: str) -> None:
        create_task(user_id, task_title, due_date="2026-07-15")
        complete_task(user_id, task_title)

    def assert_parity(rule_user, planner_user, rule_response, planner_response):
        del rule_response, planner_response
        for user_id in (rule_user, planner_user):
            assert _active_task_by_title(user_id, task_title) is not None
            assert _completed_task_by_title(user_id, task_title) is None

    _run_task_intent_parity(
        test_data_dir,
        planner_enabled,
        rule_user="parity-uncomplete-rule",
        planner_user="parity-uncomplete-planner",
        message=message,
        intent="uncomplete_task",
        entities=entities,
        seed_user=seed,
        assert_parity=assert_parity,
    )


def _execute_multi_action_plan(
    message: str, actions: tuple[AIActionRequest, ...]
) -> AIActionPlan:
    """Build a multi-action execute_action plan for routing tests."""
    return AIActionPlan(
        response_intent="execute_action",
        actions=actions,
        source_message=message,
        planning_method="test",
    )


@pytest.mark.tasks
def test_planner_multi_action_plan_executes_sequentially(test_data_dir, planner_enabled):
    """Low-confidence message + multi-action plan runs each action in order."""
    user_id = "planner-routing-multi-action"
    task_title = "Sort mail"
    message = "bump task 1 priority and show tasks"
    TestUserFactory.create_basic_user(
        user_id,
        enable_tasks=True,
        test_data_dir=test_data_dir,
    )
    create_task(user_id, task_title, due_date="2026-07-15", priority="low")

    plan = _execute_multi_action_plan(
        message,
        (
            AIActionRequest(
                action_name="update_task",
                entities={"task_identifier": "1", "priority": "high"},
                confidence=0.92,
                source_message=message,
            ),
            AIActionRequest(
                action_name="list_tasks",
                entities={},
                confidence=0.92,
                source_message=message,
            ),
        ),
    )

    interaction_manager = InteractionManager()
    interaction_manager.enable_ai_enhancement = False
    _suppress_planner_result_aware(interaction_manager)
    _force_low_confidence_parse(interaction_manager)

    with _mock_planner_plan(plan):
        response = interaction_manager.handle_message(user_id, message, "discord")

    assert response is not None
    assert task_title in response.message
    assert "updated" in response.message.lower()
    task = _active_task_by_title(user_id, task_title)
    assert task is not None
    assert task.get("priority") == "high"


@pytest.mark.tasks
def test_high_confidence_parse_skips_planner(test_data_dir, planner_enabled):
    """Confident structured commands bypass the planner even when it is enabled."""
    user_id = "planner-routing-skip"
    TestUserFactory.create_basic_user(
        user_id,
        enable_tasks=True,
        test_data_dir=test_data_dir,
    )
    message = "add task buy milk"

    interaction_manager = InteractionManager()
    interaction_manager.enable_ai_enhancement = False
    _force_high_confidence_create_task(interaction_manager)

    mock_planner = MagicMock()

    with patch(
        "communication.message_processing.action_plan_executor.get_action_planner",
        return_value=mock_planner,
    ):
        response = interaction_manager.handle_message(user_id, message, "discord")

    assert response is not None
    mock_planner.plan_from_message.assert_not_called()
    titles = [task.get("title") for task in load_active_tasks(user_id)]
    assert "Buy milk" in titles


def test_planner_disabled_uses_contextual_chat(test_data_dir, monkeypatch):
    """With planner off, low-confidence messages go straight to contextual chat."""
    monkeypatch.setattr(app_config, "AI_ACTION_PLANNER_ENABLED", False)
    user_id = "planner-routing-disabled"
    TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
    message = "I'm having a rough day"

    interaction_manager = InteractionManager()
    interaction_manager.enable_ai_enhancement = False
    _force_low_confidence_parse(interaction_manager)
    interaction_manager._handle_contextual_chat = MagicMock(
        return_value=InteractionResponse("Chat path without planner.", True)
    )

    mock_planner = MagicMock()
    with patch(
        "communication.message_processing.action_plan_executor.get_action_planner",
        return_value=mock_planner,
    ):
        response = interaction_manager.handle_message(user_id, message, "discord")

    assert response is not None
    assert response.message == "Chat path without planner."
    mock_planner.plan_from_message.assert_not_called()
    interaction_manager._handle_contextual_chat.assert_called_once()


@pytest.mark.checkins
def test_checkin_status_parity_rule_parser_vs_planner(test_data_dir, planner_enabled):
    """checkin_status via both paths returns the same status class message."""
    message = "checkin status"
    entities: dict = {}

    def assert_parity(rule_user, planner_user, rule_response, planner_response):
        del rule_user, planner_user
        for response in (rule_response, planner_response):
            lowered = response.message.lower()
            assert "check-in" in lowered or "checkin" in lowered

    _run_intent_parity(
        test_data_dir,
        planner_enabled,
        rule_user="parity-checkin-status-rule",
        planner_user="parity-checkin-status-planner",
        message=message,
        intent="checkin_status",
        entities=entities,
        seed_user=lambda _user_id: None,
        assert_parity=assert_parity,
        enable_tasks=False,
        enable_checkins=True,
    )


@pytest.mark.checkins
def test_start_checkin_parity_rule_parser_vs_planner(test_data_dir, planner_enabled):
    """start_checkin via both paths enters the same check-in flow state."""
    message = "start checkin"
    entities: dict = {}

    def assert_parity(rule_user, planner_user, rule_response, planner_response):
        assert rule_response.completed == planner_response.completed
        for user_id, response in (
            (rule_user, rule_response),
            (planner_user, planner_response),
        ):
            del user_id
            lowered = response.message.lower()
            assert "check-in" in lowered or "checkin" in lowered

    _run_intent_parity(
        test_data_dir,
        planner_enabled,
        rule_user="parity-start-checkin-rule",
        planner_user="parity-start-checkin-planner",
        message=message,
        intent="start_checkin",
        entities=entities,
        seed_user=lambda _user_id: None,
        assert_parity=assert_parity,
        enable_tasks=False,
        enable_checkins=True,
    )


@pytest.mark.checkins
def test_checkin_history_parity_rule_parser_vs_planner(test_data_dir, planner_enabled):
    """checkin_history via both paths returns the same no-data style response."""
    message = "checkin history"
    entities = {"days": 7}

    def assert_parity(rule_user, planner_user, rule_response, planner_response):
        del rule_user, planner_user
        for response in (rule_response, planner_response):
            lowered = response.message.lower()
            assert "check-in" in lowered or "checkin" in lowered

    _run_intent_parity(
        test_data_dir,
        planner_enabled,
        rule_user="parity-checkin-history-rule",
        planner_user="parity-checkin-history-planner",
        message=message,
        intent="checkin_history",
        entities=entities,
        seed_user=lambda _user_id: None,
        assert_parity=assert_parity,
        enable_tasks=False,
        enable_checkins=True,
    )


def test_show_profile_parity_rule_parser_vs_planner(test_data_dir, planner_enabled):
    """show_profile via both paths returns formatted profile text."""
    message = "show profile"
    entities: dict = {}

    def assert_parity(rule_user, planner_user, rule_response, planner_response):
        del rule_user, planner_user
        for response in (rule_response, planner_response):
            lowered = response.message.lower()
            assert "profile" in lowered
            assert not response.message.strip().startswith("{")

    _run_intent_parity(
        test_data_dir,
        planner_enabled,
        rule_user="parity-show-profile-rule",
        planner_user="parity-show-profile-planner",
        message=message,
        intent="show_profile",
        entities=entities,
        seed_user=lambda _user_id: None,
        assert_parity=assert_parity,
        enable_tasks=False,
        enable_checkins=False,
    )


def test_update_profile_parity_rule_parser_vs_planner(test_data_dir, planner_enabled):
    """update_profile via both paths persists the same preferred name."""
    new_name = "Domain Parity"
    message = f"update profile name {new_name}"
    entities = {"name": new_name}

    def assert_parity(rule_user, planner_user, rule_response, planner_response):
        del rule_response, planner_response
        assert _preferred_name(rule_user) == new_name
        assert _preferred_name(planner_user) == new_name

    _run_intent_parity(
        test_data_dir,
        planner_enabled,
        rule_user="parity-update-profile-rule",
        planner_user="parity-update-profile-planner",
        message=message,
        intent="update_profile",
        entities=entities,
        seed_user=lambda _user_id: None,
        assert_parity=assert_parity,
        enable_tasks=False,
        enable_checkins=False,
    )


def test_profile_stats_parity_rule_parser_vs_planner(test_data_dir, planner_enabled):
    """profile_stats via both paths returns statistics summary markers."""
    message = "profile stats"
    entities: dict = {}

    def assert_parity(rule_user, planner_user, rule_response, planner_response):
        del rule_user, planner_user
        for response in (rule_response, planner_response):
            assert "statistics" in response.message.lower()

    _run_intent_parity(
        test_data_dir,
        planner_enabled,
        rule_user="parity-profile-stats-rule",
        planner_user="parity-profile-stats-planner",
        message=message,
        intent="profile_stats",
        entities=entities,
        seed_user=lambda _user_id: None,
        assert_parity=assert_parity,
        enable_tasks=True,
        enable_checkins=True,
    )


def test_show_schedule_parity_rule_parser_vs_planner(test_data_dir, planner_enabled):
    """show_schedule via both paths returns schedule summary text."""
    message = "show schedule"
    entities: dict = {}

    def assert_parity(rule_user, planner_user, rule_response, planner_response):
        del rule_user, planner_user
        for response in (rule_response, planner_response):
            assert "schedule" in response.message.lower()

    _run_intent_parity(
        test_data_dir,
        planner_enabled,
        rule_user="parity-show-schedule-rule",
        planner_user="parity-show-schedule-planner",
        message=message,
        intent="show_schedule",
        entities=entities,
        seed_user=lambda _user_id: None,
        assert_parity=assert_parity,
        enable_tasks=False,
        enable_checkins=False,
    )


def test_schedule_status_parity_rule_parser_vs_planner(test_data_dir, planner_enabled):
    """schedule_status via both paths returns schedule status summary markers."""
    message = "schedule status"
    entities: dict = {}

    def assert_parity(rule_user, planner_user, rule_response, planner_response):
        del rule_user, planner_user
        for response in (rule_response, planner_response):
            lowered = response.message.lower()
            assert "schedule" in lowered
            assert "status" in lowered

    _run_intent_parity(
        test_data_dir,
        planner_enabled,
        rule_user="parity-schedule-status-rule",
        planner_user="parity-schedule-status-planner",
        message=message,
        intent="schedule_status",
        entities=entities,
        seed_user=lambda _user_id: None,
        assert_parity=assert_parity,
        enable_tasks=False,
        enable_checkins=False,
    )


@pytest.mark.tasks
def test_create_task_from_template_parity_rule_parser_vs_planner(
    test_data_dir, planner_enabled
):
    """create_task_from_template creates the same titled task on both paths."""
    task_title = "Call dentist"
    message = "task template phone_call Call dentist"
    entities = {"template_ref": "phone_call", "title": task_title}

    def assert_parity(rule_user, planner_user, rule_response, planner_response):
        assert rule_response is not None
        assert planner_response is not None
        rule_titles = [task.get("title") for task in load_active_tasks(rule_user)]
        planner_titles = [task.get("title") for task in load_active_tasks(planner_user)]
        assert task_title in rule_titles
        assert task_title in planner_titles

    _run_task_intent_parity(
        test_data_dir,
        planner_enabled,
        rule_user="parity-tpl-create-rule",
        planner_user="parity-tpl-create-planner",
        message=message,
        intent="create_task_from_template",
        entities=entities,
        seed_user=lambda _user_id: None,
        assert_parity=assert_parity,
    )


@pytest.mark.tasks
def test_list_task_templates_parity_rule_parser_vs_planner(
    test_data_dir, planner_enabled
):
    """list_task_templates returns the same built-in template names on both paths."""
    message = "list task templates"
    entities: dict = {}

    def assert_parity(rule_user, planner_user, rule_response, planner_response):
        del rule_user, planner_user
        for response in (rule_response, planner_response):
            lowered = response.message.lower()
            assert "medication" in lowered
            assert "paperwork" in lowered
            assert "phone_call" in lowered or "phone call" in lowered

    _run_task_intent_parity(
        test_data_dir,
        planner_enabled,
        rule_user="parity-tpl-list-rule",
        planner_user="parity-tpl-list-planner",
        message=message,
        intent="list_task_templates",
        entities=entities,
        seed_user=lambda _user_id: None,
        assert_parity=assert_parity,
    )


@pytest.mark.tasks
def test_show_create_hub_parity_rule_parser_vs_planner(test_data_dir, planner_enabled):
    """show_create_hub returns the create-hub view markers on both paths."""
    message = "create"
    entities: dict = {}

    def assert_parity(rule_user, planner_user, rule_response, planner_response):
        del rule_user, planner_user
        for response in (rule_response, planner_response):
            assert response.completed
            assert response.rich_data
            assert response.rich_data.get("interaction_view") == "create_hub"
            assert "template" in response.message.lower()

    _run_task_intent_parity(
        test_data_dir,
        planner_enabled,
        rule_user="parity-create-hub-rule",
        planner_user="parity-create-hub-planner",
        message=message,
        intent="show_create_hub",
        entities=entities,
        seed_user=lambda _user_id: None,
        assert_parity=assert_parity,
    )
