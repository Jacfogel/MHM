"""Unit tests for Discord task list picker and detail views."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from communication.command_handlers.shared_types import InteractionResponse


@pytest.mark.unit
@pytest.mark.communication
class TestTaskListUiHelpers:
    """Pure helpers and handler delegation in task_list_ui."""

    def test_task_flow_response_not_found(self):
        from communication.communication_channels.discord.task_list_ui import (
            _task_flow_response,
        )

        with patch(
            "communication.communication_channels.discord.task_list_ui.get_task_by_id",
            return_value=None,
        ):
            response = _task_flow_response("user-1", "missing-id", "due_date")
        assert response.message == "Task not found."
        assert response.completed is True

    def test_task_flow_response_due_date_starts_flow(self):
        from communication.communication_channels.discord.task_list_ui import (
            _task_flow_response,
        )

        task = {"title": "Buy milk", "id": "task-1"}
        with patch(
            "communication.communication_channels.discord.task_list_ui.get_task_by_id",
            return_value=task,
        ), patch(
            "communication.communication_channels.discord.task_list_ui.conversation_manager"
        ) as mock_cm:
            response = _task_flow_response("user-1", "task-1", "due_date")

        mock_cm.start_task_due_date_flow.assert_called_once_with(
            "user-1", "task-1", ask_priority=False
        )
        assert "Buy milk" in response.message
        assert response.completed is False
        assert "Skip Question" in response.suggestions

    def test_task_flow_response_priority_asks_reminders_when_due_set(self):
        from communication.communication_channels.discord.task_list_ui import (
            _task_flow_response,
        )

        task = {"title": "Call dentist", "id": "task-2"}
        with patch(
            "communication.communication_channels.discord.task_list_ui.get_task_by_id",
            return_value=task,
        ), patch(
            "communication.communication_channels.discord.task_list_ui.runtime_task_due_date",
            return_value="2026-06-25",
        ), patch(
            "communication.communication_channels.discord.task_list_ui.conversation_manager"
        ) as mock_cm:
            response = _task_flow_response("user-1", "task-2", "priority")

        mock_cm.start_task_priority_flow.assert_called_once_with(
            "user-1", "task-2", ask_reminders=True
        )
        assert "priority" in response.message.lower()
        assert "Critical" in response.suggestions

    def test_task_flow_response_reminders_requires_due_date(self):
        from communication.communication_channels.discord.task_list_ui import (
            _task_flow_response,
        )

        task = {"title": "Organize desk", "id": "task-3"}
        with patch(
            "communication.communication_channels.discord.task_list_ui.get_task_by_id",
            return_value=task,
        ), patch(
            "communication.communication_channels.discord.task_list_ui.runtime_task_due_date",
            return_value=None,
        ):
            response = _task_flow_response("user-1", "task-3", "reminders")

        assert "due date" in response.message.lower()
        assert response.completed is True

    def test_task_flow_response_reminders_starts_followup(self):
        from communication.communication_channels.discord.task_list_ui import (
            _task_flow_response,
        )

        task = {"title": "Groceries", "id": "task-4"}
        with patch(
            "communication.communication_channels.discord.task_list_ui.get_task_by_id",
            return_value=task,
        ), patch(
            "communication.communication_channels.discord.task_list_ui.runtime_task_due_date",
            return_value="2026-06-24",
        ), patch(
            "communication.communication_channels.discord.task_list_ui.conversation_manager"
        ) as mock_cm:
            mock_cm._generate_context_aware_reminder_suggestions.return_value = [
                "30 minutes before"
            ]
            response = _task_flow_response("user-1", "task-4", "reminders")

        mock_cm.start_task_reminder_followup.assert_called_once_with(
            "user-1", "task-4"
        )
        assert "reminder" in response.message.lower()
        assert response.completed is False

    def test_run_handler_intent_missing_handler(self):
        from communication.communication_channels.discord.task_list_ui import (
            _run_handler_intent,
        )

        with patch(
            "communication.command_handlers.interaction_handlers.get_interaction_handler",
            return_value=None,
        ):
            response = _run_handler_intent("u1", "unknown", {}, "msg")
        assert "could not run" in response.message.lower()

    def test_run_handler_intent_delegates(self):
        from communication.communication_channels.discord.task_list_ui import (
            _run_handler_intent,
        )

        mock_handler = MagicMock()
        mock_handler.handle.return_value = InteractionResponse("Done.", True)
        with patch(
            "communication.command_handlers.interaction_handlers.get_interaction_handler",
            return_value=mock_handler,
        ):
            response = _run_handler_intent(
                "u1", "complete_task", {"task_identifier": "t1"}, "complete task t1"
            )
        assert response.message == "Done."
        mock_handler.handle.assert_called_once()

    def test_format_task_detail_not_found(self):
        from communication.communication_channels.discord.task_list_ui import (
            _format_task_detail,
        )

        with patch(
            "communication.communication_channels.discord.task_list_ui.get_task_by_id",
            return_value=None,
        ):
            assert _format_task_detail("u1", "missing") == "Task not found."

    def test_format_task_detail_delegates_to_service(self):
        from communication.communication_channels.discord.task_list_ui import (
            _format_task_detail,
        )

        task = {"title": "Test", "id": "task-5"}
        with patch(
            "communication.communication_channels.discord.task_list_ui.get_task_by_id",
            return_value=task,
        ), patch(
            "tasks.task_service.format_task_detail_display",
            return_value="**Test**\n**Priority:** medium",
        ) as mock_format:
            text = _format_task_detail("u1", "task-5")

        mock_format.assert_called_once_with(task)
        assert "**Test**" in text


@pytest.mark.unit
@pytest.mark.communication
class TestTaskListViewFactory:
    """View factory and select wiring."""

    def test_get_task_list_view_returns_none_when_empty(self):
        from communication.communication_channels.discord.task_list_ui import (
            get_task_list_view,
        )

        assert get_task_list_view("user-1", None, None) is None
        assert get_task_list_view("user-1", [], []) is None

    def test_get_task_list_view_adds_select_for_items(self):
        from communication.communication_channels.discord.task_list_ui import (
            TASK_LIST_SELECT_PREFIX,
            get_task_list_view,
        )

        class MockView:
            def __init__(self, *args, **kwargs):
                self.children = []

            def add_item(self, item):
                self.children.append(item)

        class MockSelect:
            def __init__(self, user_id, task_items, discord_bot=None):
                self.user_id = user_id
                self.custom_id = f"{TASK_LIST_SELECT_PREFIX}{user_id}"
                self.options = list(task_items or [])

        with patch(
            "communication.communication_channels.discord.task_list_ui.discord.ui.View",
            MockView,
        ), patch(
            "communication.communication_channels.discord.task_list_ui.TaskListSelect",
            MockSelect,
        ):
            view = get_task_list_view(
                "user-picker",
                [{"title": "Task A", "task_id": "t1", "short_id": "ta1bcd"}],
                None,
            )

        assert view is not None
        assert len(view.children) == 1
        select = view.children[0]
        assert select.custom_id == f"{TASK_LIST_SELECT_PREFIX}user-picker"
        assert len(select.options) == 1

    def test_get_task_list_view_adds_show_more_button(self):
        from communication.communication_channels.discord.task_list_ui import (
            get_task_list_view,
        )

        class MockView:
            def __init__(self, *args, **kwargs):
                self.children = []

            def add_item(self, item):
                self.children.append(item)

        class MockButton:
            def __init__(self, *args, **kwargs):
                self.label = kwargs.get("label")
                self.custom_id = kwargs.get("custom_id")
                self.callback = None

        mock_bot = MagicMock()
        mock_bot._pagination_action_button_data.return_value = (
            "Show More",
            {"intent": "list_tasks", "entities": {"offset": 10}},
        )

        with patch(
            "communication.communication_channels.discord.task_list_ui.discord.ui.View",
            MockView,
        ), patch(
            "communication.communication_channels.discord.task_list_ui.discord.ui.Button",
            MockButton,
        ):
            view = get_task_list_view(
                "user-page",
                [{"title": "T", "task_id": "t1"}],
                [{"type": "show_more"}],
                discord_bot=mock_bot,
            )

        assert view is not None
        assert len(view.children) == 2
        button = view.children[1]
        assert button.label == "Show More"
        assert button.callback is not None


@pytest.mark.unit
@pytest.mark.communication
class TestTaskListSelectCallback:
    """Async select and detail view interactions."""

    @pytest.mark.asyncio
    async def test_select_callback_no_account(self):
        from communication.communication_channels.discord.task_list_ui import (
            TaskListSelect,
        )

        select = MagicMock(spec=TaskListSelect)
        select.user_id = "user-1"
        select.values = ["task-1"]
        select.discord_bot = None

        interaction = AsyncMock()
        with patch(
            "communication.communication_channels.discord.task_list_ui._internal_user_id",
            return_value=None,
        ):
            await TaskListSelect.callback(select, interaction)

        interaction.response.send_message.assert_awaited_once_with(
            "Account not found.", ephemeral=True
        )

    @pytest.mark.asyncio
    async def test_select_callback_shows_detail_view(self):
        from communication.communication_channels.discord.task_list_ui import (
            TaskListSelect,
        )

        select = MagicMock(spec=TaskListSelect)
        select.user_id = "user-1"
        select.values = ["task-abc"]
        select.discord_bot = MagicMock()

        interaction = AsyncMock()
        mock_view = MagicMock()
        with patch(
            "communication.communication_channels.discord.task_list_ui._internal_user_id",
            return_value="user-1",
        ), patch(
            "communication.communication_channels.discord.task_list_ui._format_task_detail",
            return_value="**Task detail**",
        ), patch(
            "communication.communication_channels.discord.task_list_ui.TaskDetailView",
            return_value=mock_view,
        ):
            await TaskListSelect.callback(select, interaction)

        interaction.response.send_message.assert_awaited_once_with(
            "**Task detail**", view=mock_view, ephemeral=True
        )

    @pytest.mark.asyncio
    async def test_detail_start_flow_no_account(self):
        from communication.communication_channels.discord.task_list_ui import (
            TaskDetailView,
        )

        view = TaskDetailView.__new__(TaskDetailView)
        view.user_id = "user-1"
        view.task_id = "task-1"
        view.discord_bot = None

        interaction = AsyncMock()
        with patch(
            "communication.communication_channels.discord.task_list_ui._internal_user_id",
            return_value=None,
        ):
            await view._start_flow(interaction, "due_date")

        interaction.response.send_message.assert_awaited_once_with(
            "Account not found.", ephemeral=True
        )

    @pytest.mark.asyncio
    async def test_detail_start_flow_delivers_response(self):
        from communication.communication_channels.discord.task_list_ui import (
            TaskDetailView,
        )

        view = TaskDetailView.__new__(TaskDetailView)
        view.user_id = "user-1"
        view.task_id = "task-1"
        view.discord_bot = MagicMock()

        interaction = AsyncMock()
        flow_response = InteractionResponse("Set due date?", False, suggestions=["Skip"])
        with patch(
            "communication.communication_channels.discord.task_list_ui._internal_user_id",
            return_value="user-1",
        ), patch(
            "communication.communication_channels.discord.task_list_ui._task_flow_response",
            return_value=flow_response,
        ), patch(
            "communication.communication_channels.discord.task_list_ui.deliver_handler_response",
            new_callable=AsyncMock,
        ) as mock_deliver:
            await view._start_flow(interaction, "due_date")

        interaction.response.defer.assert_awaited_once_with(ephemeral=True)
        mock_deliver.assert_awaited_once_with(
            interaction, flow_response, view.discord_bot, ephemeral=True
        )

    @pytest.mark.asyncio
    async def test_detail_complete_button_runs_handler(self):
        from communication.communication_channels.discord.task_list_ui import (
            TaskDetailView,
        )

        class MockButton:
            def __init__(self, *args, **kwargs):
                self.label = kwargs.get("label")
                self.callback = None

        with patch(
            "communication.communication_channels.discord.task_list_ui.discord.ui.View.__init__",
            lambda self, *args, **kwargs: None,
        ), patch(
            "communication.communication_channels.discord.task_list_ui.discord.ui.button",
            lambda **kwargs: (lambda fn: fn),
        ):
            view = TaskDetailView("user-1", "task-done", MagicMock())

        interaction = AsyncMock()
        with patch(
            "communication.communication_channels.discord.task_list_ui._internal_user_id",
            return_value="user-1",
        ), patch(
            "communication.communication_channels.discord.task_list_ui._run_handler_intent",
            return_value=InteractionResponse("Task completed.", True),
        ):
            await view.complete_button(interaction, MockButton())  # pyright: ignore[reportCallIssue]

        interaction.response.defer.assert_awaited_once_with(ephemeral=True)
        interaction.followup.send.assert_awaited_once_with(
            "Task completed.", ephemeral=True
        )
