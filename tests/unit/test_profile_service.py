"""Unit coverage for profile command service helpers."""

from unittest.mock import patch

import pytest

from user import profile_service


@pytest.mark.unit
@pytest.mark.user_management
def test_load_profile_sections_reads_expected_data_types():
    values = {
        "account": {"account": {"internal_username": "jules"}},
        "context": {"context": {"preferred_name": "Julie"}},
        "preferences": {"preferences": {"timezone": "America/Regina"}},
    }

    with patch("user.profile_service.get_user_data", side_effect=lambda _u, kind: values[kind]):
        sections = profile_service.load_profile_sections("u1")

    assert sections.account["internal_username"] == "jules"
    assert sections.context["preferred_name"] == "Julie"
    assert sections.preferences["timezone"] == "America/Regina"


@pytest.mark.unit
@pytest.mark.user_management
def test_apply_profile_updates_normalizes_lists_and_saves_context():
    saved = {}

    def fake_save(_user_id, kind, data):
        saved[kind] = data
        return True

    with patch(
        "user.profile_service.get_user_data",
        return_value={"context": {"custom_fields": {}}},
    ), patch("user.profile_service.save_user_data", side_effect=fake_save):
        result = profile_service.apply_profile_updates(
            "u1",
            {
                "health_conditions": "asthma, migraine",
                "interests": "music, hiking",
                "notes_for_ai": "Use concise reminders",
            },
        )

    assert result.success is True
    assert result.updates == ["health conditions", "interests", "notes for AI"]
    assert saved["context"]["custom_fields"]["health_conditions"] == [
        "asthma",
        "migraine",
    ]
    assert saved["context"]["interests"] == ["music", "hiking"]
    assert saved["context"]["notes_for_ai"] == ["Use concise reminders"]
