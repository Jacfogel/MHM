"""Unit coverage for Discord interaction view factories."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from communication.communication_channels.discord import interaction_views as views


@pytest.mark.unit
@pytest.mark.communication
class TestDeferIfNoRunningLoop:
    def test_without_running_loop_returns_deferred_factory(self):
        factory = MagicMock(return_value="view-object")

        result = views._defer_if_no_running_loop(factory, "user-1")

        assert callable(result)
        assert result() == "view-object"
        factory.assert_called_once_with("user-1")

    def test_with_running_loop_calls_factory_immediately(self):
        factory = MagicMock(return_value="immediate-view")

        with patch("asyncio.get_running_loop", return_value=MagicMock()):
            result = views._defer_if_no_running_loop(factory, "user-1", "arg2")

        assert result == "immediate-view"
        factory.assert_called_once_with("user-1", "arg2")


@pytest.mark.unit
@pytest.mark.communication
class TestInteractionViewFactories:
    def test_create_checkin_view_delegates(self, monkeypatch):
        mock_view = MagicMock()
        monkeypatch.setattr(
            "communication.communication_channels.discord.checkin_view.get_checkin_view",
            lambda user_id: mock_view,
        )

        result = views.create_checkin_view("user-1")
        view = result() if callable(result) else result

        assert view == mock_view

    def test_create_create_hub_view_passes_discord_bot(self, monkeypatch):
        bot = MagicMock()
        captured = {}

        def fake_get_create_hub_view(user_id, discord_bot):
            captured["user_id"] = user_id
            captured["discord_bot"] = discord_bot
            return "hub-view"

        monkeypatch.setattr(
            "communication.communication_channels.discord.create_item_ui.get_create_hub_view",
            fake_get_create_hub_view,
        )

        result = views.create_create_hub_view("user-1", discord_bot=bot)
        view = result() if callable(result) else result

        assert view == "hub-view"
        assert captured == {"user_id": "user-1", "discord_bot": bot}

    def test_create_task_reminder_view_passes_task_metadata(self, monkeypatch):
        captured = {}

        def fake_get_task_reminder_view(user_id, task_identifier, task_title):
            captured.update(
                {
                    "user_id": user_id,
                    "task_identifier": task_identifier,
                    "task_title": task_title,
                }
            )
            return "reminder-view"

        monkeypatch.setattr(
            "communication.communication_channels.discord.task_reminder_view.get_task_reminder_view",
            fake_get_task_reminder_view,
        )

        result = views.create_task_reminder_view(
            "user-1", task_identifier="task-9", task_title="Take meds"
        )
        view = result() if callable(result) else result

        assert view == "reminder-view"
        assert captured == {
            "user_id": "user-1",
            "task_identifier": "task-9",
            "task_title": "Take meds",
        }

    def test_create_task_reminder_view_default_title(self, monkeypatch):
        captured = {}

        def fake_get_task_reminder_view(user_id, task_identifier, task_title):
            captured["task_title"] = task_title
            return "reminder-view"

        monkeypatch.setattr(
            "communication.communication_channels.discord.task_reminder_view.get_task_reminder_view",
            fake_get_task_reminder_view,
        )

        result = views.create_task_reminder_view("user-1", task_identifier="task-9")
        if callable(result):
            result()

        assert captured["task_title"] == "Untitled Task"
