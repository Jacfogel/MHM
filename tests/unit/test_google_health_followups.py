"""Boundary, identity, pagination, and historical-baseline regressions."""

from unittest.mock import Mock

import pytest

from core.profile_v2_schemas import PreferencesV2EnvelopeModel
from integrations.google_health import client, auth, signal_builder

pytestmark = [pytest.mark.unit, pytest.mark.integrations]


@pytest.mark.parametrize("messages,chat", [(False, True), (True, False), (False, False), (True, True)])
def test_independent_personalization_boundaries(monkeypatch, messages, chat):
    from core import health_signals
    from core.health_context_builder import build_personalized_google_health_context
    from ai.context.service import _build_health_context
    monkeypatch.setattr(health_signals, "get_google_health_feature_state", lambda _: "enabled")
    monkeypatch.setattr(health_signals, "get_user_data", lambda *a: {
        "preferences": {"health_personalization": {"use_in_messages": messages, "use_in_chat": chat}}
    })
    monkeypatch.setattr("core.health_context_builder.build_recent_health_patterns", lambda _: "patterns")
    monkeypatch.setattr("core.health_context_builder.build_safe_health_guidance_summary", lambda _: "guidance")
    monkeypatch.setattr("ai.context.service.build_recent_health_patterns", lambda _: "patterns")
    monkeypatch.setattr("ai.context.service.build_safe_health_guidance_summary", lambda _: "guidance")
    assert ("patterns" in build_personalized_google_health_context("a")) is messages
    assert _build_health_context("a")["available"] is chat
    monkeypatch.setattr(health_signals, "get_google_health_feature_state", lambda _: "paused")
    assert not health_signals.health_personalization_allowed("a", surface="messages")
    assert not health_signals.health_personalization_allowed("a", surface="chat")


def test_missing_preferences_preserve_enabled_account_behavior(monkeypatch):
    from core import health_signals
    prefs = PreferencesV2EnvelopeModel(updated_at="2026-11-06 01:00:00").model_dump()
    assert prefs["health_personalization"] == {"use_in_messages": True, "use_in_chat": True}
    monkeypatch.setattr(health_signals, "get_google_health_feature_state", lambda _: "enabled")
    monkeypatch.setattr(health_signals, "get_user_data", lambda *a: {"preferences": {}})
    assert health_signals.health_personalization_allowed("a", surface="chat")


def test_chat_opt_out_blocks_cached_and_live_fallback_health(monkeypatch):
    from core.health_context_builder import health_wellness_snippet_from_context
    monkeypatch.setattr("core.health_signals.health_personalization_allowed", lambda *a, **k: False)
    live = Mock(return_value="private live health data")
    monkeypatch.setattr("core.health_context_builder.build_user_facing_signal_wellness_snippet", live)
    assert health_wellness_snippet_from_context({"health_guidance_summary": "private cached health"}, user_id="a") == ""
    assert health_wellness_snippet_from_context({}, user_id="a") == ""
    live.assert_not_called()


def test_unverified_connect_cannot_enable_account_or_sync(monkeypatch):
    from integrations.google_health import user_settings
    monkeypatch.setattr(user_settings, "run_oauth_connect_flow", lambda _: None)
    enable, sync = Mock(), Mock()
    monkeypatch.setattr(user_settings, "update_user_account", enable)
    monkeypatch.setattr(user_settings, "sync_user_health_data", sync)
    assert not user_settings.run_connect_flow("a")[0]
    enable.assert_not_called()
    sync.assert_not_called()


@pytest.mark.parametrize("window,valid", [(6, False), (7, True), (14, True), (90, True), (91, False)])
def test_baseline_configuration_bounds(monkeypatch, window, valid):
    from core import config
    monkeypatch.setattr(config, "GOOGLE_HEALTH_ENABLED", True)
    monkeypatch.setattr(config, "GOOGLE_HEALTH_CLIENT_ID", "fixture-client")
    monkeypatch.setattr(config, "GOOGLE_HEALTH_CLIENT_SECRET", "fixture-secret")
    monkeypatch.setattr(config, "GOOGLE_HEALTH_BASELINE_WINDOW_DAYS", window)
    _, errors, _ = config.validate_google_health_configuration()
    assert (not any("BASELINE_WINDOW" in error for error in errors)) is valid


def test_identity_saved_only_from_authenticated_identity_response(monkeypatch):
    monkeypatch.setattr(client, "is_google_health_testing_mode", lambda: False)
    response = Mock(status_code=200)
    response.json.return_value = {"healthUserId": "verified-123", "legacyUserId": "wrong"}
    get = Mock(return_value=response)
    monkeypatch.setattr(client.requests, "get", get)
    monkeypatch.setattr(auth, "load_auth", lambda _: {"google_user_id": "old", "refresh_token": "keep"})
    save = Mock(return_value=True)
    monkeypatch.setattr(auth, "save_auth", save)
    assert auth.save_tokens_for_user("a", {"access_token": "token", "refresh_token": "new", "google_user_id": "forged"})
    assert save.call_args.args[1]["google_user_id"] == "verified-123"
    assert get.call_args.args[0].endswith("/users/me/identity")
    assert get.call_args.kwargs["headers"]["Authorization"] == "Bearer token"
    response.json.return_value = {"legacyUserId": "wrong"}
    save.reset_mock()
    assert not auth.save_tokens_for_user("a", {"access_token": "token"})
    save.assert_not_called()


@pytest.mark.parametrize("page_size,expected", [(25, 58), (None, 2)])
def test_complete_pagination_measured_before_and_after(monkeypatch, page_size, expected):
    monkeypatch.setattr(client, "is_google_health_testing_mode", lambda: False)
    def get(_url, *, params, **_kwargs):
        start = int(params.get("pageToken", 0))
        end = min(start + params["pageSize"], 1440)
        response = Mock(status_code=200)
        response.json.return_value = {
            "dataPoints": [{"id": i} for i in range(start, end)],
            "nextPageToken": str(end) if end < 1440 else "",
        }
        return response
    monkeypatch.setattr(client.requests, "get", get)
    with client.track_request_counts() as counts:
        records = client.list_data_points("token", "daily-resting-heart-rate", page_size=page_size)
    assert [r["id"] for r in records] == list(range(1440))
    assert counts == {"daily-resting-heart-rate": expected}
    print(f"PAGINATION page_size={page_size}: pages={counts}")


def test_sleep_page_size_stays_within_provider_cap(monkeypatch):
    monkeypatch.setattr(client, "is_google_health_testing_mode", lambda: False)
    response = Mock(status_code=200)
    response.json.return_value = {}
    get = Mock(return_value=response)
    monkeypatch.setattr(client.requests, "get", get)
    client.list_data_points("token", "sleep", page_size=10000)
    assert get.call_args.kwargs["params"]["pageSize"] == 25


def test_baseline_window_excludes_future_stale_and_sparse_history(monkeypatch):
    monkeypatch.setattr(signal_builder, "BASELINE_WINDOW_DAYS", 7)
    rows = [{"date": "2026-11-06", "steps": 8000},
            {"date": "2026-11-07", "steps": 1},
            {"date": "2026-10-29", "steps": 1}]
    rows += [{"date": f"2026-11-{day:02}", "steps": 8000} for day in range(1, 6)]
    signal = signal_builder.build_signal_for_date("2026-11-06", rows)
    assert signal["baseline_days_used"] == 5
    assert signal["confidence"] == "low"
    assert signal["message_guidance"] == []


def test_personalization_persists_and_reads_fresh_per_user(test_data_dir):
    from core import get_user_data, update_user_account, update_user_preferences
    from core.health_signals import health_personalization_allowed
    from tests.test_helpers.test_utilities import TestUserFactory
    users = []
    for label in ("health-pref-a", "health-pref-b"):
        assert TestUserFactory.create_basic_user(label, test_data_dir=test_data_dir)
        uid = TestUserFactory.get_test_user_id_by_label(label, test_data_dir)
        assert uid
        update_user_account(uid, {"features": {"google_health": "enabled"}})
        users.append(uid)
    assert update_user_preferences(users[0], {"health_personalization": {"use_in_messages": False, "use_in_chat": True}})
    assert not health_personalization_allowed(users[0], surface="messages")
    assert health_personalization_allowed(users[0], surface="chat")
    assert health_personalization_allowed(users[1], surface="messages")
    assert get_user_data(users[0], "preferences")["preferences"]["health_personalization"]["use_in_messages"] is False
