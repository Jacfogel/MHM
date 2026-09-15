"""Unit tests for Discord task reminder and snooze-choice views."""

from unittest.mock import AsyncMock, patch

import pytest

from communication.communication_channels.discord.ui.task_reminder_view import (
    get_task_reminder_view,
    get_task_snooze_choice_view,
)


def _labels(view):
    return [child.label for child in view.children if hasattr(child, "label")]


@pytest.fixture
def mock_interaction_factory():
    def _create(discord_user_id=123456789):
        mock = AsyncMock()
        mock.user.id = discord_user_id
        mock.response.defer = AsyncMock()
        mock.response.send_message = AsyncMock()
        mock.response.send_modal = AsyncMock()
        mock.followup.send = AsyncMock()
        return mock

    return _create


@pytest.mark.unit
@pytest.mark.communication
@pytest.mark.tasks
class TestTaskReminderView:
    @pytest.mark.asyncio
    async def test_reminder_view_has_complete_later_and_more_buttons(self):
        view = get_task_reminder_view("user-1", "task-1", "Call dentist")
        assert view is not None
        assert view.timeout is None
        assert _labels(view) == [
            "Complete Task",
            "Remind Me Later",
            "More",
            "Skip",
            "Simplify",
        ]

    @pytest.mark.asyncio
    async def test_snooze_choice_view_has_four_options_before_evening(self):
        with patch(
            "tasks.task_reminder_snooze.tonight_snooze_label", return_value="Tonight"
        ):
            view = get_task_snooze_choice_view("user-1", "task-1", "Call dentist")
        assert view is not None
        assert _labels(view) == ["1 hour", "Tonight", "Next week", "Custom"]

    @pytest.mark.asyncio
    async def test_snooze_choice_view_uses_tomorrow_morning_after_evening(self):
        with patch(
            "tasks.task_reminder_snooze.tonight_snooze_label",
            return_value="Tomorrow morning",
        ):
            view = get_task_snooze_choice_view("user-1", "task-1", "Call dentist")
        assert view is not None
        assert _labels(view) == ["1 hour", "Tomorrow morning", "Next week", "Custom"]

    @pytest.mark.asyncio
    async def test_evening_choice_snoozes_until_tomorrow_morning(
        self, mock_interaction_factory
    ):
        with patch(
            "tasks.task_reminder_snooze.tonight_snooze_label",
            return_value="Tomorrow morning",
        ):
            view = get_task_snooze_choice_view("user-1", "task-1", "Call dentist")
        button = next(
            child for child in view.children if child.label == "Tomorrow morning"
        )
        interaction = mock_interaction_factory()
        fake_response = type("Resp", (), {"message": "I'll remind you then."})()
        with (
            patch("core.get_user_id_by_identifier", return_value="user-1"),
            patch(
                "communication.message_processing.interaction_manager.handle_user_message",
                return_value=fake_response,
            ) as handle_message,
        ):
            await button.callback(interaction)
        handle_message.assert_called_once_with(
            "user-1", "snooze task task-1 until tomorrow morning", "discord"
        )

    @pytest.mark.asyncio
    async def test_remind_later_asks_when_and_attaches_choices(
        self, mock_interaction_factory
    ):
        view = get_task_reminder_view("user-1", "task-1", "Call dentist")
        button = next(child for child in view.children if child.label == "Remind Me Later")
        interaction = mock_interaction_factory()
        fake_response = type(
            "Resp", (), {"message": "When should I remind you?", "completed": False}
        )()
        with (
            patch(
                "core.get_user_id_by_identifier", return_value="user-1"
            ),
            patch(
                "communication.message_processing.interaction_manager.handle_user_message",
                return_value=fake_response,
            ) as handle_message,
            patch(
                "communication.communication_channels.discord.ui.task_reminder_view.get_task_snooze_choice_view",
                return_value="snooze-view",
            ),
        ):
            await button.callback(interaction)
        handle_message.assert_called_once_with("user-1", "snooze task task-1", "discord")
        interaction.followup.send.assert_called_once()
        kwargs = interaction.followup.send.call_args.kwargs
        assert kwargs["view"] == "snooze-view"
        assert kwargs["ephemeral"] is True

    @pytest.mark.asyncio
    async def test_remind_later_unlinked_user_does_not_snooze(
        self, mock_interaction_factory
    ):
        view = get_task_reminder_view("user-1", "task-1", "Call dentist")
        button = next(child for child in view.children if child.label == "Remind Me Later")
        interaction = mock_interaction_factory()
        with patch("core.get_user_id_by_identifier", return_value=None):
            await button.callback(interaction)
        message = interaction.followup.send.call_args.args[0]
        assert "account" in message.lower()

    @pytest.mark.asyncio
    async def test_skip_button_routes_skip_command(self, mock_interaction_factory):
        view = get_task_reminder_view("user-1", "task-1", "Call dentist")
        button = next(child for child in view.children if child.label == "Skip")
        interaction = mock_interaction_factory()
        fake_response = type("Resp", (), {"message": "Okay. I skipped this time."})()
        with (
            patch("core.get_user_id_by_identifier", return_value="user-1"),
            patch(
                "communication.message_processing.interaction_manager.handle_user_message",
                return_value=fake_response,
            ) as handle_message,
        ):
            await button.callback(interaction)
        handle_message.assert_called_once_with("user-1", "skip task task-1", "discord")

    @pytest.mark.asyncio
    async def test_simplify_button_opens_modal(self, mock_interaction_factory):
        view = get_task_reminder_view("user-1", "task-1", "Call dentist")
        button = next(child for child in view.children if child.label == "Simplify")
        interaction = mock_interaction_factory()
        await button.callback(interaction)
        interaction.response.send_modal.assert_called_once()
