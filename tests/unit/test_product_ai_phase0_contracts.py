"""Phase 0 contract tests for product-AI context and action execution boundaries."""

from __future__ import annotations

import ast
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from ai.context.service import build_ai_context_envelope
from ai.prompts.action_catalog import AIActionPlan, AIActionRequest
from communication.command_handlers.shared_types import InteractionResponse
from communication.message_processing.action_plan_executor import ActionPlanExecutor
from communication.message_processing.action_request_adapter import (
    build_parsing_result_from_action_request,
)
from communication.message_processing.structured_command_dispatcher import (
    dispatch_structured_command,
)
from tasks import load_active_tasks
from tests.test_helpers.test_utilities import TestUserFactory

pytestmark = [pytest.mark.unit, pytest.mark.ai]

REPO_ROOT = Path(__file__).resolve().parents[2]
AI_PACKAGE_ROOT = REPO_ROOT / "ai"
DEPRECATION_INVENTORY = (
    REPO_ROOT / "development_tools" / "config" / "jsons" / "DEPRECATION_INVENTORY.json"
)

# Product-AI orchestration must not write user JSON directly; handlers own persistence.
FORBIDDEN_AI_WRITE_CALLS = {
    "save_json_data",
    "user_data_write",
    "UserDataManager",
}


def _iter_ai_python_files() -> list[Path]:
    return sorted(path for path in AI_PACKAGE_ROOT.rglob("*.py") if path.is_file())


def _function_calls_in_file(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                names.add(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                names.add(node.func.attr)
    return names


@pytest.mark.parametrize("forbidden", sorted(FORBIDDEN_AI_WRITE_CALLS))
def test_product_ai_package_avoids_direct_storage_writes(forbidden: str):
    """Product AI modules must route mutations through command handlers, not storage APIs."""
    offenders: list[str] = []
    for path in _iter_ai_python_files():
        if forbidden in _function_calls_in_file(path):
            offenders.append(str(path.relative_to(REPO_ROOT)))
    assert offenders == [], (
        f"ai/ must not call {forbidden} directly; use dispatch_structured_command "
        f"and domain handlers. Offenders: {offenders}"
    )


def test_action_plan_executor_dispatches_through_structured_command_layer():
    """Planned actions must reach handlers via dispatch_structured_command."""
    plan = AIActionPlan(
        response_intent="execute_action",
        source_message="remind me to buy milk",
        actions=(
            AIActionRequest(
                action_name="create_task",
                entities={"title": "Buy milk"},
                confidence=0.9,
                source_message="remind me to buy milk",
            ),
        ),
    )
    executor = ActionPlanExecutor()
    command_parser = MagicMock()
    command_parser.get_suggestions.return_value = []
    ai_chatbot = MagicMock()
    ai_chatbot.is_ai_available.return_value = False

    with patch(
        "communication.message_processing.action_plan_executor.dispatch_structured_command",
        return_value=InteractionResponse("Task created: Buy milk", True),
    ) as dispatch_mock:
        result = executor.execute_plan(
            plan,
            "planner-user",
            "discord",
            command_parser=command_parser,
            ai_chatbot=ai_chatbot,
            enable_ai_enhancement=False,
            command_definitions={},
        )

    dispatch_mock.assert_called_once()
    assert result is not None
    assert "Buy milk" in result.response.message


@pytest.mark.tasks
def test_envelope_reflects_task_after_dispatcher_create(test_data_dir):
    """Context envelope should include a task created through the handler path."""
    user_id = "phase0-envelope-task-user"
    TestUserFactory.create_basic_user(
        user_id,
        enable_tasks=True,
        test_data_dir=test_data_dir,
    )

    request = AIActionRequest(
        action_name="create_task",
        entities={"title": "Phase 0 envelope task"},
        confidence=0.95,
        source_message="create task phase 0 envelope task",
    )
    parsing = build_parsing_result_from_action_request(request)
    assert parsing is not None

    dispatch_structured_command(
        user_id,
        parsing,
        "discord",
        command_parser=MagicMock(get_suggestions=MagicMock(return_value=[])),
        ai_chatbot=MagicMock(is_ai_available=MagicMock(return_value=False)),
        enable_ai_enhancement=False,
        command_definitions={},
    )

    active_titles = [task.get("title") for task in load_active_tasks(user_id)]
    assert "Phase 0 envelope task" in active_titles

    envelope = build_ai_context_envelope(
        user_id,
        requested_intent="phase0_post_action_context",
    )
    assert envelope is not None
    tasks_section = envelope.structured.get("tasks") or {}
    active = tasks_section.get("active") or []
    envelope_titles = [task.get("title") for task in active]
    assert "Phase 0 envelope task" in envelope_titles


def test_product_ai_legacy_bridges_removed_from_active_inventory():
    """Retired product-AI bridges should live in removed_inventory only."""
    inventory = json.loads(DEPRECATION_INVENTORY.read_text(encoding="utf-8"))
    active_ids = {
        entry.get("id") for entry in inventory.get("active_or_candidate_inventory") or []
    }
    removed_ids = {entry.get("id") for entry in inventory.get("removed_inventory") or []}
    assert "prompt_manager_domain_prompt_builders" not in active_ids
    assert "prompt_manager_domain_prompt_builders" in removed_ids


def test_envelope_includes_optional_domains_when_data_exists(test_data_dir, monkeypatch):
    """Phase 0 context coverage: populated users expose core envelope sections."""
    user_id = "phase0-context-coverage-user"
    TestUserFactory.create_basic_user(
        user_id,
        enable_checkins=True,
        enable_tasks=True,
        test_data_dir=test_data_dir,
    )

    envelope = build_ai_context_envelope(
        user_id,
        active_channel="discord",
        requested_intent="phase0_context_coverage",
        prompt_request="show my tasks and messages",
    )
    assert envelope is not None
    structured = envelope.structured

    for section in (
        "account",
        "preferences",
        "personal_context",
        "tasks",
        "checkins",
        "schedules",
        "messages",
        "notebooks",
    ):
        assert section in structured, f"Missing envelope section: {section}"
