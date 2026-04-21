from __future__ import annotations

import pytest

from communication.command_handlers.profile_handler import ProfileHandler
from communication.command_handlers.shared_types import ParsedCommand


pytestmark = [pytest.mark.communication]

class _BadEqIntent:
    def __eq__(self, other):
        raise RuntimeError("bad comparison")


class _BadStr:
    def __str__(self):
        raise RuntimeError("bad str")


class _MostlyDict(dict):
    def __init__(self, fail_keys: set[str]):
        super().__init__()
        self.fail_keys = fail_keys

    def get(self, key, default=None):  # noqa: A003
        if key in self.fail_keys:
            raise RuntimeError(f"fail key: {key}")
        return super().get(key, default)


class _FlakyAccount:
    def __init__(self):
        self.calls = 0

    def __bool__(self):
        return True

    def get(self, key, default=None):  # noqa: A003
        if key == "features":
            self.calls += 1
            if self.calls >= 2:
                raise RuntimeError("second features call fails")
            return {"checkins": "enabled", "task_management": "enabled"}
        return default


@pytest.mark.unit
@pytest.mark.communication
def test_can_handle_internal_exception_returns_false():
    handler = ProfileHandler()
    result = ProfileHandler.can_handle.__wrapped__(handler, _BadEqIntent())
    assert result is False


@pytest.mark.unit
@pytest.mark.communication
def test_handle_show_profile_public_entrypoint(monkeypatch):
    handler = ProfileHandler()
    monkeypatch.setattr(handler, "_handle_show_profile", lambda user_id: "ok")
    assert handler.handle_show_profile("user-1", {}) == "ok"


@pytest.mark.unit
@pytest.mark.communication
def test_show_profile_includes_health_summary_and_normalizes_feature_values(monkeypatch):
    handler = ProfileHandler()

    def fake_get_user_data(user_id, key):
        if key == "account":
            return {
                "account": {
                    "features": {"checkins": "enabled", "task_management": "disabled"}
                }
            }
        if key == "context":
            return {
                "context": {
                    "preferred_name": "Sam",
                    "custom_fields": {
                        "health_conditions": ["A", "B"],
                        "medications_treatments": ["M1"],
                        "allergies_sensitivities": ["Allergy1"],
                    },
                }
            }
        return {"preferences": {}}

    monkeypatch.setattr(
        "communication.command_handlers.profile_handler.get_user_data", fake_get_user_data
    )
    monkeypatch.setattr(handler, "_format_profile_text", lambda *_: "profile text")

    response = handler._handle_show_profile("user-1")
    assert response.completed is True
    assert response.rich_data is not None
    fields = response.rich_data["fields"]
    checkins_field = next(f for f in fields if f["name"] == "Check-ins")
    tasks_field = next(f for f in fields if f["name"] == "Tasks")
    health_field = next(f for f in fields if f["name"] == "Health Summary")
    assert checkins_field["value"] == "Enabled"
    assert tasks_field["value"] == "Disabled"
    assert "2 conditions" in health_field["value"]
    assert "1 medications" in health_field["value"]
    assert "1 allergies" in health_field["value"]


@pytest.mark.unit
@pytest.mark.communication
def test_update_profile_date_of_birth_loved_ones_and_email_failure(monkeypatch):
    handler = ProfileHandler()

    saved_calls = []

    def fake_get_user_data(user_id, key):
        if key == "context":
            return {"context": {"custom_fields": {}}}
        if key == "account":
            return {"account": {"email": "old@example.com"}}
        return {}

    def fake_save_user_data(user_id, key, data):
        saved_calls.append((key, data))
        return key != "account"

    monkeypatch.setattr(
        "communication.command_handlers.profile_handler.get_user_data", fake_get_user_data
    )
    monkeypatch.setattr(
        "communication.command_handlers.profile_handler.save_user_data",
        fake_save_user_data,
    )

    response = handler._handle_update_profile(
        "user-1",
        {
            "date_of_birth": "1991-05-01",
            "loved_ones": "Mom - Family - Mother, Support\nAlex - Friend - Peer",
            "email": "new@example.com",
        },
    )
    assert response.completed is True
    assert "Failed to update email" in response.message
    assert any(call[0] == "account" for call in saved_calls)


@pytest.mark.unit
@pytest.mark.communication
def test_update_profile_loved_ones_non_string_and_email_success(monkeypatch):
    handler = ProfileHandler()

    saved_calls = []

    def fake_get_user_data(user_id, key):
        if key == "context":
            return {"context": {"custom_fields": {}}}
        if key == "account":
            return {"account": {"email": "old@example.com"}}
        return {}

    def fake_save_user_data(user_id, key, data):
        saved_calls.append((key, data))
        return True

    monkeypatch.setattr(
        "communication.command_handlers.profile_handler.get_user_data", fake_get_user_data
    )
    monkeypatch.setattr(
        "communication.command_handlers.profile_handler.save_user_data",
        fake_save_user_data,
    )

    response = handler._handle_update_profile(
        "user-1",
        {
            "loved_ones": [{"name": "A", "type": "Family", "relationships": []}],
            "email": "new@example.com",
        },
    )
    assert response.completed is True
    assert "Profile updated" in response.message
    assert "support network" in response.message
    assert "email" in response.message
    assert any(call[0] == "context" for call in saved_calls)


@pytest.mark.unit
@pytest.mark.communication
def test_format_profile_text_string_gender_and_overflow_loved_ones_and_long_note():
    handler = ProfileHandler()
    text = handler._format_profile_text(
        {
            "email": "person@example.com",
            "account_status": "active",
            "features": {"checkins": "enabled", "task_management": "enabled"},
        },
        {
            "preferred_name": "Taylor",
            "gender_identity": "Non-binary",
            "date_of_birth": "1990-01-01",
            "loved_ones": [
                {"name": "A", "type": "Family", "relationships": ["Support"]},
                {"name": "B", "type": "Family", "relationships": []},
                {"name": "C", "type": "Friend", "relationships": ["Peer"]},
                {"name": "D", "type": "Friend", "relationships": ["Peer"]},
            ],
            "notes_for_ai": ["x" * 120],
        },
        {},
    )
    assert "- Gender Identity: Non-binary" in text
    assert "- Date of Birth: 1990-01-01" in text
    assert "... and 1 more" in text
    assert "- Notes for AI: " in text
    assert "..." in text


@pytest.mark.unit
@pytest.mark.communication
def test_format_profile_text_gender_join_exception_uses_not_set():
    handler = ProfileHandler()
    text = handler._format_profile_text(
        {},
        {"gender_identity": [_BadStr()]},
        {},
    )
    assert "- Gender Identity: Not set" in text


@pytest.mark.unit
@pytest.mark.communication
def test_format_profile_text_inner_warning_paths(monkeypatch):
    handler = ProfileHandler()
    warning_messages = []
    monkeypatch.setattr(
        "communication.command_handlers.profile_handler.logger.warning",
        lambda msg: warning_messages.append(msg),
    )

    context_data = _MostlyDict(
        {
            "custom_fields",
            "interests",
            "goals",
            "loved_ones",
            "notes_for_ai",
        }
    )
    context_data["seed"] = True
    account_data = {"features": {"checkins": "enabled", "task_management": "enabled"}}
    text = handler._format_profile_text(account_data, context_data, {})

    assert "**Your Profile:**" in text
    assert len(warning_messages) >= 5


@pytest.mark.unit
@pytest.mark.communication
def test_format_profile_text_account_features_exception_falls_back_unknown(monkeypatch):
    handler = ProfileHandler()
    warning_messages = []
    monkeypatch.setattr(
        "communication.command_handlers.profile_handler.logger.warning",
        lambda msg: warning_messages.append(msg),
    )

    bad_account = _MostlyDict({"features"})
    bad_account["seed"] = True
    text = handler._format_profile_text(bad_account, {}, {})

    assert "- Check-ins: Unknown" in text
    assert "- Tasks: Unknown" in text
    assert any("account features" in msg.lower() for msg in warning_messages)


@pytest.mark.unit
@pytest.mark.communication
def test_show_profile_normalization_try_exception_is_swallowed(monkeypatch):
    handler = ProfileHandler()

    def fake_get_user_data(user_id, key):
        if key == "account":
            return {"account": _FlakyAccount()}
        if key == "context":
            return {"context": {"preferred_name": "Sam"}}
        return {"preferences": {}}

    monkeypatch.setattr(
        "communication.command_handlers.profile_handler.get_user_data", fake_get_user_data
    )
    monkeypatch.setattr(handler, "_format_profile_text", lambda *_: "profile text")

    response = handler._handle_show_profile("user-1")
    assert response.completed is True
    assert response.rich_data is not None


@pytest.mark.unit
@pytest.mark.communication
def test_format_profile_text_outer_exception_uses_fallback(monkeypatch):
    handler = ProfileHandler()

    class _ExplodesOnGet:
        def get(self, key, default=None):  # noqa: A003
            raise RuntimeError("boom")

    error_messages = []
    monkeypatch.setattr(
        "communication.command_handlers.profile_handler.logger.error",
        lambda msg, **kwargs: error_messages.append(msg),
    )

    text = handler._format_profile_text({}, _ExplodesOnGet(), {})
    assert "- Name: Not set" in text
    assert "- Check-ins: Unknown" in text
    assert any("Error formatting profile text" in msg for msg in error_messages)


@pytest.mark.unit
@pytest.mark.communication
def test_handle_routes_profile_stats_branch(monkeypatch):
    handler = ProfileHandler()
    monkeypatch.setattr(
        handler, "_handle_profile_stats", lambda user_id: "stats-response"
    )
    response = handler.handle(
        "user-1",
        ParsedCommand(
            intent="profile_stats",
            entities={},
            confidence=1.0,
            original_message="profile stats",
        ),
    )
    assert response == "stats-response"
