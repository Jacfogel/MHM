"""
Unit tests for ai/fallback_responses boundary behavior.
"""

import ast
from pathlib import Path

import pytest
from unittest.mock import patch

from ai.chat.action_boundaries import FALSE_CRUD_SUCCESS_SUBSTRINGS
from ai.fallback import (
    FallbackCategory,
    FallbackResponses,
    build_contextual_fallback,
    get_fallback_responses,
)
from ai.chat.interaction_types import AIInteractionType, interaction_type_for_mode


FALSE_SUCCESS_PHRASES = FALSE_CRUD_SUCCESS_SUBSTRINGS

FALSE_CAPABILITY_PHRASES = (
    "i've accessed",
    "i accessed your",
    "i can see your private",
    "successfully completed",
    "i've completed that for you",
    "done! i've",
)

FALLBACK_PACKAGE_DIR = Path(__file__).resolve().parent.parent.parent / "ai" / "fallback"
FORBIDDEN_IMPORT_PREFIXES = (
    "communication.",
    "communication/",
    "discord",
    "email",
)


def _collect_imports_from_file(py_file: Path) -> set[str]:
    tree = ast.parse(py_file.read_text(encoding="utf-8"))
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module)
    return imports


@pytest.mark.unit
@pytest.mark.ai
class TestInteractionTypes:
    """Test mode to interaction type mapping."""

    def test_interaction_type_for_chat_mode(self):
        assert interaction_type_for_mode("chat") == AIInteractionType.CONVERSATIONAL

    def test_interaction_type_for_command_mode(self):
        assert interaction_type_for_mode("command") == AIInteractionType.COMMAND_INTERPRETATION

    def test_interaction_type_for_clarification_mode(self):
        assert interaction_type_for_mode("command_with_clarification") == AIInteractionType.CLARIFICATION

    def test_interaction_type_for_none_defaults_to_conversational(self):
        assert interaction_type_for_mode(None) == AIInteractionType.CONVERSATIONAL

    def test_interaction_type_for_personalized_mode(self):
        assert interaction_type_for_mode("personalized") == AIInteractionType.PERSONALIZED_MESSAGE


@pytest.mark.unit
@pytest.mark.ai
class TestFallbackImportBoundary:
    """ai/fallback_responses must not import channel or communication adapters."""

    def test_fallback_package_does_not_import_communication_or_channels(self):
        violations: list[str] = []
        for py_file in FALLBACK_PACKAGE_DIR.glob("*.py"):
            for module_name in _collect_imports_from_file(py_file):
                lower = module_name.lower()
                if any(lower.startswith(prefix) or prefix in lower for prefix in FORBIDDEN_IMPORT_PREFIXES):
                    violations.append(f"{py_file.name}: {module_name}")
        assert not violations, (
            "Fallback package must stay AI-layer only; found forbidden imports:\n"
            + "\n".join(violations)
        )


@pytest.mark.unit
@pytest.mark.ai
class TestFallbackResponses:
    """Test fallback response generation boundaries."""

    @pytest.fixture
    def fallback(self):
        return FallbackResponses()

    @patch("ai.fallback.data_access.get_user_data", return_value={})
    @patch("ai.fallback.data_access.get_recent_responses", return_value=[])
    def test_contextual_returns_non_empty_for_chat_like_prompt(
        self, _mock_recent, _mock_user_data, fallback
    ):
        response = fallback.contextual("I'm feeling overwhelmed today", user_id="user-test")
        assert response
        assert isinstance(response, str)
        assert len(response.strip()) > 0

    @patch("ai.fallback.data_access.get_user_data", return_value={})
    @patch("ai.fallback.data_access.get_recent_responses", return_value=[])
    def test_contextual_returns_non_empty_for_command_like_prompt(
        self, _mock_recent, _mock_user_data, fallback
    ):
        response = fallback.contextual("create task buy milk", user_id="user-test")
        assert response
        assert isinstance(response, str)

    @patch("ai.fallback.data_access.get_user_data", return_value={})
    @patch("ai.fallback.data_access.get_recent_responses", return_value=[])
    def test_contextual_does_not_claim_action_success(
        self, _mock_recent, _mock_user_data, fallback
    ):
        prompts = [
            "hello",
            "I'm stressed",
            "create task buy milk",
            "how am I doing",
            "remind me tomorrow",
        ]
        for prompt in prompts:
            response = fallback.contextual(prompt, user_id="user-test").lower()
            for phrase in FALSE_SUCCESS_PHRASES:
                assert phrase not in response, (
                    f"Fallback for '{prompt}' must not claim success: found '{phrase}'"
                )

    @patch("ai.fallback.data_access.get_user_data", return_value={})
    @patch("ai.fallback.data_access.get_recent_responses", return_value=[])
    def test_contextual_does_not_claim_ai_success_or_data_access(
        self, _mock_recent, _mock_user_data, fallback
    ):
        prompts = [
            "connection error",
            "how am I doing",
            "I'm overwhelmed",
            "thank you",
        ]
        for prompt in prompts:
            response = fallback.contextual(prompt, user_id="user-test").lower()
            for phrase in FALSE_CAPABILITY_PHRASES + FALSE_SUCCESS_PHRASES:
                assert phrase not in response, (
                    f"Fallback for '{prompt}' must not claim capability: found '{phrase}'"
                )

    @patch("ai.fallback.data_access.get_user_data", return_value={})
    @patch("ai.fallback.data_access.get_recent_responses", return_value=[])
    def test_technical_prompt_uses_technical_category(
        self, _mock_recent, _mock_user_data
    ):
        _text, category = build_contextual_fallback("connection error", "user-test")
        assert category == FallbackCategory.TECHNICAL_UNAVAILABLE

    @patch("ai.fallback.data_access.get_user_data", return_value={})
    @patch("ai.fallback.data_access.get_recent_responses", return_value=[])
    def test_new_user_progress_prompt_uses_new_user_category(
        self, _mock_recent, _mock_user_data
    ):
        _text, category = build_contextual_fallback("how am I doing lately", "user-test")
        assert category == FallbackCategory.NEW_USER_NO_CONTEXT

    @patch("ai.fallback.data_access.get_user_data", return_value={"context": {"preferred_name": "Sam"}})
    @patch(
        "ai.fallback.data_access.get_recent_responses",
        return_value=[
            {"mood": 3, "energy": 3, "ate_breakfast": True},
            {"mood": 4, "energy": 4, "ate_breakfast": False},
        ],
    )
    def test_breakfast_prompt_with_checkins_uses_checkin_category(
        self, _mock_recent, _mock_user_data
    ):
        _text, category = build_contextual_fallback("did I eat breakfast", "user-test")
        assert category == FallbackCategory.CHECKIN_SUMMARY

    @patch("ai.fallback.data_access.get_user_data", return_value={"context": {}})
    @patch(
        "ai.fallback.data_access.get_recent_responses",
        return_value=[{"mood": None, "energy": None}],
    )
    def test_mood_count_without_data_uses_data_unavailable_category(
        self, _mock_recent, _mock_user_data
    ):
        _text, category = build_contextual_fallback("how many times mood", "user-test")
        assert category == FallbackCategory.DATA_UNAVAILABLE

    @patch("ai.fallback.data_access.get_user_data", return_value={"context": {}})
    @patch("ai.fallback.data_access.get_recent_responses", return_value=[])
    def test_personalized_returns_non_empty(self, _mock_recent, _mock_user_data, fallback):
        response = fallback.personalized("user-test")
        assert response
        assert len(response.strip()) > 0

    @patch("ai.fallback.data_access.get_user_data", return_value={"context": {}})
    @patch("ai.fallback.data_access.get_recent_responses", return_value=[])
    def test_personalized_category(self, _mock_recent, _mock_user_data):
        from ai.fallback.personalized import build_personalized_message

        _text, category = build_personalized_message("user-test")
        assert category == FallbackCategory.PERSONALIZED_MESSAGE

    def test_get_fallback_responses_returns_singleton(self):
        assert get_fallback_responses() is get_fallback_responses()

    def test_personalize_with_profile_name_injects_name(self, fallback):
        result = fallback.personalize_with_profile_name(
            "Hello! How are you?",
            ["Active user"],
            {"preferred_name": "Alex"},
        )
        assert "Alex" in result
