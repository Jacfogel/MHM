"""Unit tests for Discord task reminder and snooze-choice views."""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from communication.communication_channels.discord.ui.task_reminder_view import (
    get_task_reminder_view,
    get_task_simplify_view,
    get_task_snooze_choice_view,
    restore_task_reminder_views,
)


def _labels(view):
    return [child.label for child in view.children if hasattr(child, "label")]


@pytest.mark.unit
@pytest.mark.communication
@pytest.mark.tasks
class TestTaskBreakdownReview:
    @pytest.mark.asyncio
    async def test_cancel_saves_nothing_and_clears_text_confirmation(self, mock_interaction_factory):
        from communication.command_handlers.task_handler import PENDING_SIMPLIFY

        view = get_task_simplify_view("user-1", "task-1", "Call dentist", ["Find the number"])
        PENDING_SIMPLIFY["user-1"] = {"task_id": "task-1", "steps": ["Find the number"]}
        with patch("tasks.task_breakdown.add_task_subtasks") as save:
            await next(child for child in view.children if getattr(child, "label", "") == "Cancel").callback(
                mock_interaction_factory()
            )
        save.assert_not_called()
        assert "user-1" not in PENDING_SIMPLIFY
        assert view.is_finished()
        assert all(child.disabled for child in view.children)

    @pytest.mark.asyncio
    async def test_other_account_cannot_save_review(self, mock_interaction_factory):
        view = get_task_simplify_view("user-1", "task-1", "Call dentist", ["Find the number"])
        interaction = mock_interaction_factory()
        with patch("core.get_user_id_by_identifier", return_value="other-user"), patch(
            "tasks.task_breakdown.add_task_subtasks"
        ) as save:
            assert await view.interaction_check(interaction) is False
            await view.add_steps(interaction, ["Find the number"])
        save.assert_not_called()

    @pytest.mark.asyncio
    async def test_unavailable_review_accepts_own_step_without_ai(self, mock_interaction_factory):
        from tasks.task_breakdown import TaskBreakdownResult

        view = get_task_simplify_view("user-1", "task-1", "Call dentist", [])
        assert _labels(view) == ["Add my own step", "Cancel"]
        interaction = mock_interaction_factory()
        await next(child for child in view.children if child.label == "Add my own step").callback(interaction)
        modal = interaction.response.send_modal.call_args.args[0]
        modal.step_input._value = "Find the number"
        with patch("core.get_user_id_by_identifier", return_value="user-1"), patch(
            "tasks.task_breakdown.add_task_subtasks", return_value=TaskBreakdownResult(True, "Added one step.")
        ) as save, patch("ai.client.openai_client.call_openai_api") as model:
            await modal.on_submit(mock_interaction_factory())
        save.assert_called_once_with("user-1", "task-1", ["Find the number"])
        model.assert_not_called()
        assert view.is_finished()

    @pytest.mark.asyncio
    async def test_cancelled_modal_cannot_save(self, mock_interaction_factory):
        view = get_task_simplify_view("user-1", "task-1", "Call dentist", [])
        interaction = mock_interaction_factory()
        await next(child for child in view.children if child.label == "Add my own step").callback(interaction)
        modal = interaction.response.send_modal.call_args.args[0]
        modal.step_input._value = "Find the number"
        view.finish_review()
        with patch("core.get_user_id_by_identifier", return_value="user-1"), patch(
            "tasks.task_breakdown.add_task_subtasks"
        ) as save:
            await modal.on_submit(mock_interaction_factory())
        save.assert_not_called()


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
    async def test_restart_registers_saved_reminder_buttons(self):
        client = Mock()
        with (
            patch("core.user_management.get_all_user_ids", return_value=["user-1"]),
            patch("tasks.task_data_handlers.load_active_tasks", return_value=[
                {"id": "task-1", "title": "Call dentist"}
            ]),
            patch("tasks.task_data_handlers.load_completed_tasks", return_value=[
                {"id": "task-2", "title": "Done task"}
            ]),
        ):
            restore_task_reminder_views(client)
        assert client.add_view.call_count == 2
        views = [call.args[0] for call in client.add_view.call_args_list]
        assert all(view.is_persistent() for view in views)
        assert views[0].children[1].custom_id == "task_remind_later_user-1_task-1"

    @pytest.mark.asyncio
    async def test_reminder_view_has_complete_later_and_more_buttons(self):
        view = get_task_reminder_view("user-1", "task-1", "Call dentist")
        assert view is not None
        assert view.timeout is None
        assert _labels(view) == [
            "Done",
            "Snooze",
            "More",
            "Leave me alone",
            "Break down with AI",
        ]
        break_button = next(
            child for child in view.children if child.label == "Break down with AI"
        )
        assert break_button.row == 0
        assert str(break_button.style).endswith("primary")

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
        button = next(child for child in view.children if child.label == "Snooze")
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
        button = next(child for child in view.children if child.label == "Snooze")
        interaction = mock_interaction_factory()
        with patch("core.get_user_id_by_identifier", return_value=None):
            await button.callback(interaction)
        message = interaction.followup.send.call_args.args[0]
        assert "account" in message.lower()

    @pytest.mark.asyncio
    async def test_skip_button_routes_skip_command(self, mock_interaction_factory):
        view = get_task_reminder_view("user-1", "task-1", "Call dentist")
        button = next(child for child in view.children if child.label == "Leave me alone")
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
    async def test_break_down_button_suggests_steps(self, mock_interaction_factory):
        view = get_task_reminder_view("user-1", "task-1", "Call dentist")
        button = next(child for child in view.children if child.label == "Break down with AI")
        interaction = mock_interaction_factory()
        fake_response = type(
            "Resp",
            (),
            {
                "message": "Here are smaller steps.",
                "completed": False,
                "rich_data": {"steps": ["Find the number"]},
            },
        )()
        with (
            patch("core.get_user_id_by_identifier", return_value="user-1"),
            patch(
                "communication.message_processing.interaction_manager.handle_user_message",
                return_value=fake_response,
            ) as handle_message,
            patch(
                "communication.communication_channels.discord.ui.task_reminder_view.get_task_simplify_view",
                return_value="breakdown-view",
            ),
        ):
            await button.callback(interaction)
        handle_message.assert_called_once_with("user-1", "simplify task task-1", "discord")
        kwargs = interaction.followup.send.call_args.kwargs
        assert kwargs["view"] == "breakdown-view"
        assert kwargs["ephemeral"] is True
