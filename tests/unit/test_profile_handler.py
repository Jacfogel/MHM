"""Tests for profile handler utilities."""

from unittest.mock import patch

import pytest

from communication.command_handlers.profile_handler import ProfileHandler


@pytest.mark.unit
def test_format_profile_text_includes_health_and_support():
    handler = ProfileHandler()
    account_data = {
        "email": "test@example.com",
        "account_status": "active",
        "features": {"checkins": "enabled", "task_management": "disabled"},
    }
    context_data = {
        "preferred_name": "Casey",
        "gender_identity": ["Non-binary"],
        "custom_fields": {
            "health_conditions": ["Asthma"],
            "medications_treatments": ["Inhaler"],
            "allergies_sensitivities": ["Dust"],
        },
        "interests": ["Hiking"],
        "goals": ["Wellness"],
        "loved_ones": [
            {"name": "Alex", "type": "Friend", "relationships": ["Support"]},
        ],
        "notes_for_ai": ["Help me stay consistent"],
    }
    preferences_data = {"preferences": {"categories": ["motivational"]}}

    result = handler._format_profile_text(account_data, context_data, preferences_data)

    assert "Asthma" in result
    assert "Alex" in result
    assert "Check-ins: Enabled" in result
    assert "Tasks: Disabled" in result


@pytest.mark.unit
def test_handle_update_profile_returns_success(monkeypatch):
    handler = ProfileHandler()

    def fake_get_user_data(user_id, data_type):
        if data_type == "context":
            return {"context": {"custom_fields": {}}}
        if data_type == "account":
            return {"account": {}}
        return {}

    monkeypatch.setattr(
        "communication.command_handlers.profile_handler.get_user_data",
        fake_get_user_data,
    )
    monkeypatch.setattr(
        "communication.command_handlers.profile_handler.save_user_data",
        lambda user_id, key, data: True,
    )

    response = handler._handle_update_profile(
        "user123",
        {
            "name": "Casey",
            "health_conditions": "Asthma",
            "notes_for_ai": "I like gentle nudges",
        },
    )

    assert response.completed
    assert "Profile updated" in response.message


@pytest.mark.unit
def test_handle_profile_stats_formats_values(monkeypatch):
    handler = ProfileHandler()

    monkeypatch.setattr(
        "communication.command_handlers.profile_handler.get_user_task_stats",
        lambda user_id: {"active_count": 2, "completed_count": 5, "completion_rate": 80},
    )
    monkeypatch.setattr(
        "communication.command_handlers.profile_handler.get_recent_checkins",
        lambda user_id, limit: [{"id": 1}, {"id": 2}],
    )

    response = handler._handle_profile_stats("user123")

    assert "Active tasks: 2" in response.message
    assert "Completed tasks: 5" in response.message
    assert "Check-ins this month: 2" in response.message
