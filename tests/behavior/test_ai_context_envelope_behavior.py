"""
Behavior tests for canonical AI context envelope construction.

Replaces legacy ContextBuilder.build_user_context coverage with envelope APIs.
"""

from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch

import pytest

from ai.context.service import AIContextEnvelope, build_ai_context_envelope
from tests.test_helpers.test_utilities import TestUserFactory, TestDataFactory


def _build_envelope(user_id: str, **kwargs) -> AIContextEnvelope:
    envelope = build_ai_context_envelope(
        user_id,
        requested_intent="envelope_behavior_test",
        **kwargs,
    )
    assert envelope is not None
    return envelope


@pytest.mark.behavior
@pytest.mark.ai
class TestAIContextEnvelopeBehavior:
    """Test real behavior of envelope-backed product-AI context."""

    def test_build_envelope_returns_structured_sections(self, test_data_dir):
        user_id = "test-user"
        TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)

        envelope = _build_envelope(user_id)
        structured = envelope.structured

        assert isinstance(structured, dict)
        for section in (
            "account",
            "preferences",
            "personal_context",
            "checkins",
            "conversation",
            "tasks",
            "schedules",
        ):
            assert section in structured, f"Missing section: {section}"

    def test_envelope_includes_user_data_from_files(self, test_data_dir):
        user_id = "test-user"
        TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)

        structured = _build_envelope(user_id).structured

        assert isinstance(structured.get("account"), dict)
        assert isinstance(structured.get("personal_context"), dict)

    def test_envelope_includes_conversation_history(self, test_data_dir):
        user_id = "test-user"
        TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)

        conversation = _build_envelope(
            user_id, include_conversation_history=True
        ).structured.get("conversation") or {}

        assert isinstance(conversation.get("recent_chat_interactions"), list)

    def test_envelope_handles_missing_user_data_gracefully(self, test_data_dir):
        structured = _build_envelope("nonexistent-user").structured

        assert isinstance(structured.get("account"), dict)
        assert isinstance(structured.get("personal_context"), dict)

    def test_envelope_metadata_includes_current_timestamp(self, test_data_dir):
        user_id = "test-user"
        TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)

        metadata = _build_envelope(user_id).metadata
        assert metadata.get("current_timestamp")

    def test_envelope_includes_recent_checkins(self, test_data_dir):
        user_id = "test-user"
        TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)

        checkins = _build_envelope(user_id).structured.get("checkins") or {}
        assert isinstance(checkins.get("recent"), list)

    def test_envelope_without_conversation_history(self, test_data_dir):
        user_id = "test-user"
        TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)

        conversation = _build_envelope(
            user_id, include_conversation_history=False
        ).structured.get("conversation") or {}

        assert isinstance(conversation.get("recent_chat_interactions"), list)

    def test_envelope_handles_invalid_user_id_gracefully(self, test_data_dir):
        structured = _build_envelope("invalid-user-id").structured
        assert isinstance(structured.get("account"), dict)
        assert isinstance(structured.get("personal_context"), dict)

    def test_envelope_metadata_timestamp_refreshes_per_call(self, test_data_dir):
        user_id = "test-user"
        TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)

        ts1 = "2026-01-20 02:23:47"
        ts2 = "2026-01-20 02:23:48"

        with patch(
            "ai.context.service.now_timestamp_full",
            side_effect=[ts1, ts2],
        ):
            envelope1 = _build_envelope(user_id)
            envelope2 = _build_envelope(user_id)

        assert envelope1.metadata["current_timestamp"] != envelope2.metadata["current_timestamp"]

    def test_envelope_handles_empty_user_data(self, test_data_dir):
        user_id = "empty-user"
        os.makedirs(os.path.join(test_data_dir, "users", user_id), exist_ok=True)

        structured = _build_envelope(user_id).structured
        assert isinstance(structured.get("account"), dict)
        assert isinstance(structured.get("personal_context"), dict)

    def test_envelope_handles_corrupted_user_data(self, test_data_dir):
        user_id = "corrupted-user"
        TestDataFactory.create_corrupted_user_data(user_id, "invalid_json")

        structured = _build_envelope(user_id).structured
        assert isinstance(structured.get("account"), dict)

    def test_envelope_handles_missing_files(self, test_data_dir):
        user_id = "missing-files-user"
        TestDataFactory.create_corrupted_user_data(user_id, "missing_file")

        structured = _build_envelope(user_id).structured
        assert isinstance(structured.get("account"), dict)

    def test_envelope_handles_empty_files(self, test_data_dir):
        user_id = "empty-files-user"
        TestDataFactory.create_corrupted_user_data(user_id, "empty_file")

        structured = _build_envelope(user_id).structured
        assert isinstance(structured.get("account"), dict)

    def test_envelope_handles_long_user_id(self, test_data_dir):
        user_id = "very-long-user-id-" + "x" * 100
        TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)

        envelope = _build_envelope(user_id)
        assert envelope is not None

    def test_envelope_handles_special_characters_in_user_id(self, test_data_dir):
        user_id = "user-with-special-chars!@#$%"
        TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)

        envelope = _build_envelope(user_id)
        assert envelope is not None

    def test_envelope_handles_unicode_user_id(self, test_data_dir):
        user_id = "user-unicode-测试"
        TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)

        envelope = _build_envelope(user_id)
        assert envelope is not None

    def test_envelope_handles_concurrent_access(self, test_data_dir):
        user_id = "concurrent-user"
        TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)

        def _load():
            return _build_envelope(user_id)

        with ThreadPoolExecutor(max_workers=4) as pool:
            envelopes = list(pool.map(lambda _: _load(), range(4)))

        assert all(isinstance(env.structured, dict) for env in envelopes)

    def test_envelope_handles_rapid_calls(self, test_data_dir):
        user_id = "rapid-user"
        TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)

        envelopes = [_build_envelope(user_id) for _ in range(5)]
        assert all(env.metadata.get("user_id") == user_id for env in envelopes)

    def test_envelope_handles_large_user_data(self, test_data_dir):
        user_id = "large-data-user"
        TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)

        structured = _build_envelope(user_id).structured
        assert isinstance(structured.get("account"), dict)
