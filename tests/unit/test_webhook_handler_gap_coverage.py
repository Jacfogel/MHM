"""Targeted gap-coverage tests for Discord webhook handler."""

from __future__ import annotations

import asyncio
from concurrent.futures import Future
from types import SimpleNamespace

import pytest

from communication.communication_channels.discord import webhook_handler as wh


def _auth_event(user_id: str = "12345", username: str = "julie") -> dict:
    return {
        "event": {
            "type": wh.EVENT_APPLICATION_AUTHORIZED,
            "data": {"user": {"id": user_id, "username": username}},
        }
    }


@pytest.mark.unit
@pytest.mark.communication
class TestWebhookHandlerGapCoverage:
    def test_verify_signature_exception_path(self):
        # int signature triggers TypeError at signature slicing in debug line.
        assert wh.verify_webhook_signature(123, "timestamp", b"{}", "public_key") is False

    def test_handle_application_authorized_outer_exception_path(self):
        # event_data=None triggers outer exception branch.
        assert wh.handle_application_authorized(None, bot_instance=None) is False

    def test_handle_application_authorized_update_username_failure_and_successful_dm(self, monkeypatch):
        marks = []
        sent = []

        class _Loop:
            def is_closed(self):
                return False

        class _User:
            async def send(self, message, view=None):
                sent.append((message, view))

        class _Bot:
            def __init__(self):
                self.loop = _Loop()

            async def fetch_user(self, user_id: int):
                return _User()

        bot_instance = SimpleNamespace(bot=_Bot())

        monkeypatch.setattr(
            "communication.core.welcome_manager.has_been_welcomed",
            lambda user_id, channel_type="discord": False,
        )
        monkeypatch.setattr(
            "communication.core.welcome_manager.mark_as_welcomed",
            lambda user_id, channel_type="discord": marks.append((user_id, channel_type)),
        )
        monkeypatch.setattr(
            "communication.communication_channels.discord.welcome_handler.get_welcome_message",
            lambda *args, **kwargs: "welcome",
        )
        monkeypatch.setattr(
            "communication.communication_channels.discord.welcome_handler.get_welcome_message_view",
            lambda user_id: "view",
        )
        monkeypatch.setattr(
            "core.user_data_handlers.get_user_id_by_identifier",
            lambda discord_user_id: "internal-user",
        )
        monkeypatch.setattr(
            "core.user_data_handlers.update_user_account",
            lambda user_id, data: (_ for _ in ()).throw(RuntimeError("db write failed")),
        )
        monkeypatch.setattr(wh, "_is_testing_environment", lambda: False)

        async def _no_sleep(_seconds):
            return None

        monkeypatch.setattr(asyncio, "sleep", _no_sleep)

        def _run_coroutine_threadsafe(coro, loop):
            # Execute coroutine in test thread to cover _send_welcome_dm internals.
            result = asyncio.run(coro)
            fut = Future()
            fut.set_result(result)
            return fut

        monkeypatch.setattr(asyncio, "run_coroutine_threadsafe", _run_coroutine_threadsafe)

        result = wh.handle_application_authorized(_auth_event(), bot_instance=bot_instance)
        assert result is True
        assert sent == [("welcome", "view")]
        assert marks == [("12345", "discord")]

    def test_handle_application_authorized_loop_closed_during_schedule(self, monkeypatch):
        marks = []

        class _TogglingLoop:
            def __init__(self):
                self.calls = 0

            def is_closed(self):
                self.calls += 1
                # First check (line 164) False, second check (line 203) True.
                return self.calls >= 2

        class _Bot:
            def __init__(self):
                self.loop = _TogglingLoop()

        bot_instance = SimpleNamespace(bot=_Bot())

        monkeypatch.setattr(
            "communication.core.welcome_manager.has_been_welcomed",
            lambda user_id, channel_type="discord": False,
        )
        monkeypatch.setattr(
            "communication.core.welcome_manager.mark_as_welcomed",
            lambda user_id, channel_type="discord": marks.append((user_id, channel_type)),
        )
        monkeypatch.setattr(
            "communication.communication_channels.discord.welcome_handler.get_welcome_message",
            lambda *args, **kwargs: "welcome",
        )
        monkeypatch.setattr(
            "core.user_data_handlers.get_user_id_by_identifier",
            lambda discord_user_id: None,
        )

        result = wh.handle_application_authorized(_auth_event(), bot_instance=bot_instance)
        assert result is False
        # mark_as_welcomed called with default channel_type in this branch.
        assert marks and marks[0][0] == "12345"

    def test_handle_application_authorized_future_none_branch(self, monkeypatch):
        marks = []

        class _Loop:
            def is_closed(self):
                return False

        class _Bot:
            def __init__(self):
                self.loop = _Loop()

        bot_instance = SimpleNamespace(bot=_Bot())

        monkeypatch.setattr(
            "communication.core.welcome_manager.has_been_welcomed",
            lambda user_id, channel_type="discord": False,
        )
        monkeypatch.setattr(
            "communication.core.welcome_manager.mark_as_welcomed",
            lambda user_id, channel_type="discord": marks.append((user_id, channel_type)),
        )
        monkeypatch.setattr(
            "communication.communication_channels.discord.welcome_handler.get_welcome_message",
            lambda *args, **kwargs: "welcome",
        )
        monkeypatch.setattr(
            "core.user_data_handlers.get_user_id_by_identifier",
            lambda discord_user_id: None,
        )
        monkeypatch.setattr(wh, "_is_testing_environment", lambda: False)
        monkeypatch.setattr(asyncio, "run_coroutine_threadsafe", lambda coro, loop: None)

        result = wh.handle_application_authorized(_auth_event(), bot_instance=bot_instance)
        assert result is False
        assert marks and marks[0][0] == "12345"

    def test_handle_application_authorized_runtime_error_branch(self, monkeypatch):
        marks = []

        class _Loop:
            def is_closed(self):
                return False

        class _Bot:
            def __init__(self):
                self.loop = _Loop()

        bot_instance = SimpleNamespace(bot=_Bot())

        monkeypatch.setattr(
            "communication.core.welcome_manager.has_been_welcomed",
            lambda user_id, channel_type="discord": False,
        )
        monkeypatch.setattr(
            "communication.core.welcome_manager.mark_as_welcomed",
            lambda user_id, channel_type="discord": marks.append((user_id, channel_type)),
        )
        monkeypatch.setattr(
            "communication.communication_channels.discord.welcome_handler.get_welcome_message",
            lambda *args, **kwargs: "welcome",
        )
        monkeypatch.setattr(
            "core.user_data_handlers.get_user_id_by_identifier",
            lambda discord_user_id: None,
        )
        monkeypatch.setattr(
            asyncio,
            "run_coroutine_threadsafe",
            lambda coro, loop: (_ for _ in ()).throw(RuntimeError("event loop closed")),
        )

        result = wh.handle_application_authorized(_auth_event(), bot_instance=bot_instance)
        assert result is False
        assert marks and marks[0][0] == "12345"

    def test_handle_webhook_event_exception_branch(self, monkeypatch):
        monkeypatch.setattr(
            "communication.core.welcome_manager.clear_welcomed_status",
            lambda user_id, channel_type="discord": (_ for _ in ()).throw(RuntimeError("boom")),
        )
        event_data = {
            "event": {"data": {"user": {"id": "12345", "username": "julie"}}}
        }
        assert wh.handle_webhook_event(wh.EVENT_APPLICATION_DEAUTHORIZED, event_data, None) is False
