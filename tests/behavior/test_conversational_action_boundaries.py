"""Behavior tests for conversational action-suggestion boundaries (no false CRUD claims)."""

import pytest

from ai.conversational_context.action_boundaries import (
    FALSE_CRUD_SUCCESS_SUBSTRINGS,
    find_false_crud_claims,
    response_has_false_crud_claim,
)
from ai.conversational_context.assembly import assemble_comprehensive_messages
from ai.conversational_context.instructions import CONVERSATIONAL_CONTEXT_INSTRUCTIONS
from ai.fallback_responses import FallbackResponses
from ai.response_generator import get_response_generator
from core import get_user_data, get_user_id_by_identifier
from core.config import get_user_file_path
from core.file_operations import save_json_data
from tests.ai.ai_response_validator import AIResponseValidator
from tests.test_helpers.test_utilities import (
    TestUserFactory,
    cleanup_test_data_environment,
    setup_test_data_environment,
)


# Samples that must NOT trigger false-CRUD detection (suggestions / offers only).
SAFE_SUGGESTION_RESPONSES = (
    "I can help you create a task. Try saying 'create task buy milk'.",
    "Would you like to add a reminder? You can say 'remind me tomorrow at 9am'.",
    "Task management is disabled on your account, so I can't add tasks right now.",
    "To list your tasks, say 'show my tasks'.",
    "I haven't created anything yet, but I can walk you through it.",
)

# Samples that must trigger detection (false completion claims).
UNSAFE_FALSE_CRUD_RESPONSES = (
    ("I've created that task for you.", "claims task/item was created"),
    ("Done! Your task has been added.", "claims task/item was created"),
    ("I updated your schedule for tomorrow.", "claims item was updated or deleted"),
    ("I deleted the old task.", "claims item was updated or deleted"),
    ("I've completed that for you.", "claims action was completed on user's behalf"),
    ("Based on your recent data, you seem stressed.", "claims data access or analysis not shown in context"),
)


@pytest.mark.behavior
@pytest.mark.ai
class TestActionBoundaryDetection:
    """Shared detector used by validator and fallback/conversational review."""

    @pytest.mark.parametrize("response", SAFE_SUGGESTION_RESPONSES)
    def test_safe_suggestions_do_not_trigger_false_crud_detection(self, response):
        assert find_false_crud_claims(response) == []

    @pytest.mark.parametrize("response,expected_label", UNSAFE_FALSE_CRUD_RESPONSES)
    def test_unsafe_responses_trigger_expected_labels(self, response, expected_label):
        labels = find_false_crud_claims(response)
        assert expected_label in labels

    def test_negated_completion_does_not_false_positive(self):
        assert not response_has_false_crud_claim(
            "I haven't created a task yet, but I can help if you'd like."
        )


@pytest.mark.behavior
@pytest.mark.ai
class TestConversationalPromptActionBoundaries:
    """Prompt contract: instructions and assembled context enforce action boundaries."""

    def test_instructions_include_action_boundary_rules(self):
        assert "ACTION BOUNDARIES" in CONVERSATIONAL_CONTEXT_INSTRUCTIONS
        assert "no false CRUD claims" in CONVERSATIONAL_CONTEXT_INSTRUCTIONS
        assert "I've created that task for you" in CONVERSATIONAL_CONTEXT_INSTRUCTIONS
        assert "you can say" in CONVERSATIONAL_CONTEXT_INSTRUCTIONS.lower()

    def setup_method(self):
        self.test_dir, self.test_data_dir, _ = setup_test_data_environment()

    def teardown_method(self):
        cleanup_test_data_environment(self.test_dir)

    def _set_automated_messages_feature(self, user_id: str, enabled: bool) -> None:
        actual_id = get_user_id_by_identifier(user_id) or user_id
        account_result = get_user_data(actual_id, "account")
        account = account_result.get("account") or {}
        features = dict(account.get("features") or {})
        features["automated_messages"] = "enabled" if enabled else "disabled"
        account["features"] = features
        save_json_data(account, get_user_file_path(actual_id, "account"))

    def test_assembled_prompt_includes_action_boundaries_and_disabled_tasks(
        self, monkeypatch
    ):
        monkeypatch.setenv("TEST_DATA_DIR", self.test_data_dir)
        monkeypatch.setenv("MHM_TEST_DATA_DIR", self.test_data_dir)
        monkeypatch.setenv("MHM_TESTING", "1")

        user_id = "user_action_boundary_prompt"
        assert TestUserFactory.create_basic_user(
            user_id,
            enable_checkins=False,
            enable_tasks=False,
            test_data_dir=self.test_data_dir,
        )
        self._set_automated_messages_feature(user_id, enabled=False)

        messages = get_response_generator().create_comprehensive_context_prompt(
            user_id, "can you create a task for me"
        )
        system_content = messages[0]["content"]
        assert "ACTION BOUNDARIES" in system_content
        assert "task management is disabled" in system_content
        assert "no false CRUD claims" in system_content

    def test_assemble_messages_includes_wellness_and_boundary_instructions(
        self, monkeypatch
    ):
        monkeypatch.setenv("TEST_DATA_DIR", self.test_data_dir)
        monkeypatch.setenv("MHM_TEST_DATA_DIR", self.test_data_dir)
        monkeypatch.setenv("MHM_TESTING", "1")

        user_id = "user_action_boundary_assembly"
        assert TestUserFactory.create_basic_user(
            user_id, enable_tasks=True, test_data_dir=self.test_data_dir
        )

        messages = assemble_comprehensive_messages(
            user_id,
            "create a task to buy milk",
            "You are a supportive wellness assistant.",
        )
        system_content = messages[0]["content"]
        assert "supportive wellness assistant" in system_content
        assert "ACTION BOUNDARIES" in system_content
        assert messages[1]["content"] == "create a task to buy milk"


@pytest.mark.behavior
@pytest.mark.ai
class TestAIResponseValidatorFalseCrudClaims:
    """Validator flags false CRUD claims for manual AI quality review."""

    @pytest.mark.parametrize("response", [r[0] for r in UNSAFE_FALSE_CRUD_RESPONSES])
    def test_validator_fails_on_false_crud_claims(self, response):
        result = AIResponseValidator.validate_response(
            response, prompt="create a task", test_type="chat"
        )
        assert not result["valid"]
        assert any("false crud" in issue.lower() for issue in result["issues"])

    @pytest.mark.parametrize("response", SAFE_SUGGESTION_RESPONSES)
    def test_validator_passes_safe_suggestions(self, response):
        result = AIResponseValidator.validate_response(
            response, prompt="create a task", test_type="chat"
        )
        crud_issues = [i for i in result["issues"] if "false crud" in i.lower()]
        assert crud_issues == []


@pytest.mark.behavior
@pytest.mark.ai
class TestFallbackResponsesActionBoundaries:
    """Fallback paths must not claim CRUD success (regression guard)."""

    @pytest.fixture
    def fallback(self):
        return FallbackResponses()

    @pytest.mark.parametrize(
        "prompt",
        [
            "hello",
            "create task buy milk",
            "delete my task",
            "schedule a reminder tomorrow",
            "how am I doing",
        ],
    )
    def test_contextual_fallback_avoids_false_crud_substrings(
        self, fallback, prompt, monkeypatch
    ):
        from unittest.mock import patch

        with (
            patch("ai.fallback_responses.data_access.get_user_data", return_value={}),
            patch(
                "ai.fallback_responses.data_access.get_recent_responses",
                return_value=[],
            ),
        ):
            response = fallback.contextual(prompt, user_id="user-boundary-test").lower()
        for phrase in FALSE_CRUD_SUCCESS_SUBSTRINGS:
            assert phrase not in response, (
                f"Fallback for '{prompt}' must not claim success: found '{phrase}'"
            )
        assert not response_has_false_crud_claim(response)
