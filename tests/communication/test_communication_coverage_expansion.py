"""
Scenario tests for communication modules below the 80% domain target.

Targets: discord_interaction_router, create_item_ui, checkin_flow, task_flow edges.
"""

from __future__ import annotations

import uuid
from datetime import timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

from communication.command_handlers.shared_types import InteractionResponse
from communication.message_processing.conversation_flow_manager import ConversationManager
from communication.message_processing.flows.flow_constants import (
    CHECKIN_MOOD,
    FLOW_CHECKIN,
    FLOW_TASK_REMINDER,
)
from core.time_utilities import (
    TIMESTAMP_FULL,
    format_timestamp,
    now_datetime_full,
    now_timestamp_full,
)
from tests.test_helpers.test_utilities import TestUserFactory


def _discord_interaction(**attrs) -> discord.Interaction:
    """Minimal interaction mock that passes isinstance(..., discord.Interaction)."""
    interaction = MagicMock(spec=discord.Interaction)
    for key, value in attrs.items():
        setattr(interaction, key, value)
    return interaction


def _past_timestamp(minutes: int) -> str:
    return format_timestamp(
        now_datetime_full() - timedelta(minutes=minutes), TIMESTAMP_FULL
    )


def _unique_user(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


@pytest.fixture
def flow_manager(monkeypatch):
    monkeypatch.setattr(ConversationManager, "_load_user_states", lambda self: None)
    monkeypatch.setattr(
        ConversationManager, "_expire_inactive_checkins", lambda self, user_id=None: None
    )
    monkeypatch.setattr(ConversationManager, "_save_user_states", lambda self: None)
    return ConversationManager()


@pytest.mark.unit
@pytest.mark.communication
class TestDiscordInteractionRouter:
    """Route component and application-command interactions."""

    @pytest.mark.asyncio
    async def test_routes_component_interaction(self):
        from communication.communication_channels.discord.discord_interaction_router import (
            handle_discord_interaction,
        )

        bot = MagicMock()
        interaction = MagicMock()
        interaction.type = discord.InteractionType.component
        interaction.data = {}

        with patch(
            "communication.communication_channels.discord.discord_interaction_router._handle_component_interaction",
            new_callable=AsyncMock,
        ) as mock_component:
            await handle_discord_interaction(bot, interaction)
        mock_component.assert_awaited_once_with(bot, interaction)

    @pytest.mark.asyncio
    async def test_routes_application_command_interaction(self):
        from communication.communication_channels.discord.discord_interaction_router import (
            handle_discord_interaction,
        )

        bot = MagicMock()
        interaction = MagicMock()
        interaction.type = discord.InteractionType.application_command

        with patch(
            "communication.communication_channels.discord.discord_interaction_router._handle_application_command_interaction",
            new_callable=AsyncMock,
        ) as mock_app:
            await handle_discord_interaction(bot, interaction)
        mock_app.assert_awaited_once_with(bot, interaction)

    @pytest.mark.asyncio
    async def test_component_missing_custom_id_is_noop(self):
        from communication.communication_channels.discord.discord_interaction_router import (
            _handle_component_interaction,
        )

        interaction = MagicMock()
        interaction.data = {}
        await _handle_component_interaction(MagicMock(), interaction)

    @pytest.mark.asyncio
    async def test_welcome_create_button_starts_creation_flow(self):
        from communication.communication_channels.discord.discord_interaction_router import (
            _handle_welcome_button,
        )

        interaction = _discord_interaction(user=MagicMock(name="tester"))

        with patch(
            "communication.communication_channels.discord.account_flow_handler.start_account_creation_flow",
            new_callable=AsyncMock,
        ) as mock_create:
            await _handle_welcome_button(
                MagicMock(), interaction, "welcome_create_12345"
            )
        mock_create.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_welcome_link_button_starts_linking_flow(self):
        from communication.communication_channels.discord.discord_interaction_router import (
            _handle_welcome_button,
        )

        interaction = _discord_interaction(user=MagicMock(name="tester"))

        with patch(
            "communication.communication_channels.discord.account_flow_handler.start_account_linking_flow",
            new_callable=AsyncMock,
        ) as mock_link:
            await _handle_welcome_button(
                MagicMock(), interaction, "welcome_link_67890"
            )
        mock_link.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_checkin_task_prefix_returns_early(self):
        from communication.communication_channels.discord.discord_interaction_router import (
            _handle_component_interaction,
        )

        interaction = MagicMock()
        interaction.data = {"custom_id": "checkin_start_abc"}
        with patch(
            "communication.communication_channels.discord.discord_interaction_router._handle_suggestion_button",
            new_callable=AsyncMock,
        ) as mock_suggestion:
            await _handle_component_interaction(MagicMock(), interaction)
        mock_suggestion.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_suggestion_button_no_label_sends_error(self):
        from communication.communication_channels.discord.discord_interaction_router import (
            _handle_suggestion_button,
        )

        interaction = AsyncMock()
        interaction.user.id = 999
        interaction.data = {"custom_id": "suggestion_0"}

        with patch(
            "communication.communication_channels.discord.discord_interaction_router._extract_suggestion_button_label",
            return_value=None,
        ):
            await _handle_suggestion_button(MagicMock(), interaction, "suggestion_0")

        interaction.followup.send.assert_awaited_once()
        assert "could not process" in interaction.followup.send.await_args.args[0].lower()

    @pytest.mark.asyncio
    async def test_suggestion_button_unregistered_user(self):
        from communication.communication_channels.discord.discord_interaction_router import (
            _handle_suggestion_button,
        )

        interaction = AsyncMock()
        interaction.user.id = 111
        with patch(
            "communication.communication_channels.discord.discord_interaction_router._extract_suggestion_button_label",
            return_value="List tasks",
        ), patch(
            "communication.communication_channels.discord.discord_interaction_router.get_user_id_by_identifier",
            return_value=None,
        ):
            await _handle_suggestion_button(MagicMock(), interaction, "suggestion_0")

        assert "not found" in interaction.followup.send.await_args.args[0].lower()

    @pytest.mark.asyncio
    async def test_suggestion_button_success_with_intent_payload(self):
        from communication.communication_channels.discord.discord_interaction_router import (
            _handle_suggestion_button,
        )

        bot = MagicMock()
        bot._suggestion_button_payloads = {
            "suggestion_1": {"intent": "list_tasks", "entities": {}}
        }
        bot._has_display_rich_data.return_value = False
        bot._get_action_row_inputs.return_value = ([], [])

        interaction = AsyncMock()
        interaction.user.id = 222
        mock_handler = MagicMock()
        mock_handler.handle.return_value = InteractionResponse("Your tasks.", True)

        with patch(
            "communication.communication_channels.discord.discord_interaction_router._extract_suggestion_button_label",
            return_value="List tasks",
        ), patch(
            "communication.communication_channels.discord.discord_interaction_router.get_user_id_by_identifier",
            return_value="internal-user",
        ), patch(
            "communication.command_handlers.interaction_handlers.get_interaction_handler",
            return_value=mock_handler,
        ):
            await _handle_suggestion_button(bot, interaction, "suggestion_1")

        interaction.followup.send.assert_awaited_once_with(content="Your tasks.")

    def test_extract_suggestion_label_from_component(self):
        from communication.communication_channels.discord.discord_interaction_router import (
            _extract_suggestion_button_label,
        )

        interaction = MagicMock()
        interaction.component = MagicMock(label="Done")
        interaction.data = None
        interaction.message = None
        assert _extract_suggestion_button_label(interaction, "suggestion_0") == "Done"

    def test_extract_suggestion_label_from_message_children(self):
        from communication.communication_channels.discord.discord_interaction_router import (
            _extract_suggestion_button_label,
        )

        child = MagicMock()
        child.custom_id = "suggestion_2"
        child.label = "Cancel"
        row = MagicMock()
        row.children = [child]
        interaction = MagicMock()
        interaction.component = None
        interaction.data = {}
        interaction.message = MagicMock(components=[row])
        assert _extract_suggestion_button_label(interaction, "suggestion_2") == "Cancel"

    def test_build_suggestion_response_via_message_handler(self):
        from communication.communication_channels.discord.discord_interaction_router import (
            _build_suggestion_button_response,
        )

        bot = MagicMock()
        bot._suggestion_button_payloads = {"suggestion_3": "list tasks"}
        with patch(
            "communication.message_processing.interaction_manager.handle_user_message",
            return_value=InteractionResponse("Tasks listed.", True),
        ) as mock_handle:
            response = _build_suggestion_button_response(
                bot, "suggestion_3", "List tasks", "user-abc"
            )
        assert response.message == "Tasks listed."
        mock_handle.assert_called_once_with("user-abc", "list tasks", "discord")

    def test_build_suggestion_response_unknown_notebook_intent(self):
        from communication.communication_channels.discord.discord_interaction_router import (
            _build_suggestion_button_response,
        )

        bot = MagicMock()
        bot._suggestion_button_payloads = {
            "suggestion_nb": {"intent": "append_to_entry", "entities": {"entry_id": "1"}}
        }
        with patch(
            "communication.command_handlers.interaction_handlers.get_interaction_handler",
            return_value=None,
        ):
            response = _build_suggestion_button_response(
                bot, "suggestion_nb", "Append", "user-abc"
            )
        assert "could not continue" in response.message.lower()

    @pytest.mark.asyncio
    async def test_send_suggestion_followup_embed_and_view(self):
        from communication.communication_channels.discord.discord_interaction_router import (
            _send_suggestion_followup,
        )

        bot = MagicMock()
        bot._has_display_rich_data.return_value = True
        bot._create_discord_embed.return_value = MagicMock()
        bot._get_action_row_inputs.return_value = (["OK"], [{}])
        bot._create_action_row.return_value = MagicMock()
        interaction = AsyncMock()
        response = InteractionResponse("Rich", rich_data={"title": "T"}, suggestions=["OK"])

        await _send_suggestion_followup(bot, interaction, response)
        kwargs = interaction.followup.send.await_args.kwargs
        assert kwargs["embed"] is not None
        assert kwargs["view"] is not None

    @pytest.mark.asyncio
    async def test_start_command_welcome_sends_dm(self):
        from communication.communication_channels.discord.discord_interaction_router import (
            _handle_start_command_welcome,
        )

        interaction = _discord_interaction()
        interaction.response = MagicMock()
        interaction.response.is_done = MagicMock(return_value=False)
        interaction.response.send_message = AsyncMock()
        interaction.user.send = AsyncMock()

        with patch(
            "communication.communication_channels.discord.welcome_handler.get_welcome_message",
            return_value="Welcome!",
        ), patch(
            "communication.communication_channels.discord.welcome_handler.mark_as_welcomed"
        ):
            await _handle_start_command_welcome(interaction, "discord-999")

        interaction.user.send.assert_awaited_once_with("Welcome!")
        interaction.response.send_message.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_application_command_welcome_unlinked_user(self):
        from communication.communication_channels.discord.discord_interaction_router import (
            _handle_application_command_interaction,
        )

        bot = MagicMock()
        interaction = _discord_interaction()
        interaction.user.id = 333
        interaction.user.send = AsyncMock()
        interaction.command = MagicMock()
        interaction.command.name = "help"

        with patch(
            "communication.communication_channels.discord.discord_interaction_router.get_user_id_by_identifier",
            return_value=None,
        ), patch(
            "communication.communication_channels.discord.welcome_handler.has_been_welcomed",
            return_value=False,
        ), patch(
            "communication.communication_channels.discord.welcome_handler.get_welcome_message",
            return_value="Welcome new user!",
        ), patch(
            "communication.communication_channels.discord.welcome_handler.mark_as_welcomed"
        ):
            await _handle_application_command_interaction(bot, interaction)

        interaction.user.send.assert_awaited_once_with("Welcome new user!")

    @pytest.mark.asyncio
    async def test_application_command_start_unlinked_routes_to_start_welcome(self):
        from communication.communication_channels.discord.discord_interaction_router import (
            _handle_application_command_interaction,
        )

        bot = MagicMock()
        interaction = _discord_interaction()
        interaction.user.id = 444
        interaction.command = MagicMock()
        interaction.command.name = "start"

        with patch(
            "communication.communication_channels.discord.discord_interaction_router.get_user_id_by_identifier",
            return_value=None,
        ), patch(
            "communication.communication_channels.discord.discord_interaction_router._handle_start_command_welcome",
            new_callable=AsyncMock,
        ) as mock_start:
            await _handle_application_command_interaction(bot, interaction)

        mock_start.assert_awaited_once_with(interaction, "444")

    @pytest.mark.asyncio
    async def test_suggestion_button_build_failure_sends_error(self):
        from communication.communication_channels.discord.discord_interaction_router import (
            _handle_suggestion_button,
        )

        bot = MagicMock()
        bot._suggestion_button_payloads = {}
        interaction = AsyncMock()
        interaction.user.id = 555

        with patch(
            "communication.communication_channels.discord.discord_interaction_router._extract_suggestion_button_label",
            return_value="List tasks",
        ), patch(
            "communication.communication_channels.discord.discord_interaction_router.get_user_id_by_identifier",
            return_value="user-555",
        ), patch(
            "communication.communication_channels.discord.discord_interaction_router._build_suggestion_button_response",
            return_value=None,
        ):
            await _handle_suggestion_button(bot, interaction, "suggestion_x")

        assert "error occurred" in interaction.followup.send.await_args.args[0].lower()
        from communication.communication_channels.discord.discord_interaction_router import (
            _handle_start_command_welcome,
        )

        interaction = _discord_interaction()
        interaction.response = MagicMock()
        interaction.response.is_done = MagicMock(return_value=False)
        interaction.response.send_message = AsyncMock()
        interaction.user.send = AsyncMock(side_effect=discord.Forbidden(MagicMock(), ""))

        with patch(
            "communication.communication_channels.discord.welcome_handler.get_welcome_message",
            return_value="Welcome!",
        ), patch(
            "communication.communication_channels.discord.welcome_handler.mark_as_welcomed"
        ):
            await _handle_start_command_welcome(interaction, "discord-888")

        interaction.response.send_message.assert_awaited_once()
        send_args = interaction.response.send_message.await_args
        assert send_args is not None
        assert "Discord ID" in send_args.args[0]


@pytest.mark.unit
@pytest.mark.communication
class TestCreateItemUi:
    """Discord create hub helpers and view factory."""

    def test_internal_user_id_missing_user(self):
        from communication.communication_channels.discord.create_item_ui import (
            _internal_user_id,
        )

        interaction = MagicMock(user=None)
        assert _internal_user_id(interaction) is None

    def test_internal_user_id_resolves_account(self):
        from communication.communication_channels.discord.create_item_ui import (
            _internal_user_id,
        )

        interaction = MagicMock()
        interaction.user.id = 55555
        with patch("core.get_user_id_by_identifier", return_value="uid-555"):
            assert _internal_user_id(interaction) == "uid-555"

    def test_run_handler_missing_handler_returns_fallback(self):
        from communication.communication_channels.discord.create_item_ui import _run_handler

        with patch(
            "communication.command_handlers.interaction_handlers.get_interaction_handler",
            return_value=None,
        ):
            response = _run_handler("u1", "unknown_intent", {}, "msg")
        assert "could not run" in response.message.lower()

    def test_run_handler_delegates_to_handler(self):
        from communication.communication_channels.discord.create_item_ui import _run_handler

        mock_handler = MagicMock()
        mock_handler.handle.return_value = InteractionResponse("Created.", True)
        with patch(
            "communication.command_handlers.interaction_handlers.get_interaction_handler",
            return_value=mock_handler,
        ):
            response = _run_handler("u1", "create_task", {"title": "X"}, "create task")
        assert response.message == "Created."
        mock_handler.handle.assert_called_once()

    def test_create_hub_rich_data_marker(self):
        from communication.communication_channels.discord.create_item_ui import (
            create_hub_rich_data,
        )

        data = create_hub_rich_data("user-xyz")
        assert data["interaction_view"] == "create_hub"
        assert data["user_id"] == "user-xyz"

    def test_get_create_hub_view_has_template_and_modal_buttons(self):
        from communication.communication_channels.discord.create_item_ui import (
            CREATE_HUB_PREFIX,
            get_create_hub_view,
        )

        class MockView:
            def __init__(self, *args, **kwargs):
                self.children = []

            def add_item(self, item):
                self.children.append(item)

        class MockButton:
            def __init__(self, *args, **kwargs):
                self.custom_id = kwargs.get("custom_id")
                self.label = kwargs.get("label")
                self.callback = None

        with patch(
            "communication.communication_channels.discord.create_item_ui.discord.ui.View",
            MockView,
        ), patch(
            "communication.communication_channels.discord.create_item_ui.discord.ui.Button",
            MockButton,
        ):
            view = get_create_hub_view("user-hub", discord_bot=None)

        custom_ids = [item.custom_id for item in view.children]
        assert any(cid.startswith(f"{CREATE_HUB_PREFIX}tpl_medication") for cid in custom_ids)
        assert any("custom_task" in cid for cid in custom_ids)
        assert any("quick_note" in cid for cid in custom_ids)
        assert any("new_note" in cid for cid in custom_ids)

    @pytest.mark.asyncio
    async def test_hub_run_template_task_no_account(self):
        from communication.communication_channels.discord.create_item_ui import (
            _hub_run_template_task,
        )

        interaction = AsyncMock()
        with patch(
            "communication.communication_channels.discord.create_item_ui._internal_user_id",
            return_value=None,
        ):
            await _hub_run_template_task(interaction, None, "medication")
        interaction.response.send_message.assert_awaited_once_with(
            "Account not found.", ephemeral=True
        )

    @pytest.mark.asyncio
    async def test_hub_run_template_task_success(self):
        from communication.communication_channels.discord.create_item_ui import (
            _hub_run_template_task,
        )

        interaction = AsyncMock()
        with patch(
            "communication.communication_channels.discord.create_item_ui._internal_user_id",
            return_value="user-1",
        ), patch(
            "communication.communication_channels.discord.create_item_ui._run_handler",
            return_value=InteractionResponse("Task from template.", True),
        ), patch(
            "communication.communication_channels.discord.create_item_ui.deliver_handler_response",
            new_callable=AsyncMock,
        ) as mock_deliver:
            await _hub_run_template_task(interaction, MagicMock(), "appointment")
        interaction.response.defer.assert_awaited_once()
        mock_deliver.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_modal_button_callback_no_account(self):
        from communication.communication_channels.discord.create_item_ui import (
            _bind_modal_button_callback,
        )

        callback = _bind_modal_button_callback(
            "custom task", None, lambda _uid, _bot: MagicMock()
        )
        interaction = AsyncMock()
        with patch(
            "communication.communication_channels.discord.create_item_ui._internal_user_id",
            return_value=None,
        ):
            await callback(interaction)
        interaction.response.send_message.assert_awaited_once_with(
            "Account not found.", ephemeral=True
        )

    @pytest.mark.asyncio
    async def test_modal_button_callback_opens_modal(self):
        from communication.communication_channels.discord.create_item_ui import (
            _bind_modal_button_callback,
        )

        modal = MagicMock()
        callback = _bind_modal_button_callback(
            "quick note", None, lambda _uid, _bot: modal
        )
        interaction = AsyncMock()
        with patch(
            "communication.communication_channels.discord.create_item_ui._internal_user_id",
            return_value="user-1",
        ):
            await callback(interaction)
        interaction.response.send_modal.assert_awaited_once_with(modal)


@pytest.mark.unit
@pytest.mark.communication
class TestCheckinFlowExpansion:
    """Additional checkin_flow paths via ConversationManager."""

    def test_personalized_welcome_first_checkin(self, flow_manager):
        user_id = _unique_user("welcome_first")
        with patch(
            "communication.message_processing.flows.checkin_flow.get_recent_checkins",
            return_value=[],
        ):
            message = flow_manager._get_personalized_welcome(user_id, 3)
        assert "first check-in" in message.lower()
        assert "3 quick questions" in message

    def test_personalized_welcome_high_mood(self, flow_manager):
        user_id = _unique_user("welcome_high")
        with patch(
            "communication.message_processing.flows.checkin_flow.get_recent_checkins",
            return_value=[{"mood": 5}, {"mood": 4}],
        ):
            message = flow_manager._get_personalized_welcome(user_id, 2)
        assert "pretty good" in message.lower()

    def test_personalized_welcome_low_mood(self, flow_manager):
        user_id = _unique_user("welcome_low")
        with patch(
            "communication.message_processing.flows.checkin_flow.get_recent_checkins",
            return_value=[{"mood": 1}, {"mood": 2}],
        ):
            message = flow_manager._get_personalized_welcome(user_id, 2)
        assert "support you" in message.lower()

    def test_handle_checkin_cancel_clears_flow(self, flow_manager):
        user_id = _unique_user("checkin_cancel")
        flow_manager.user_states[user_id] = {
            "flow": FLOW_CHECKIN,
            "state": CHECKIN_MOOD,
            "data": {},
            "question_order": ["mood"],
            "current_question_index": 0,
        }
        reply, completed = flow_manager._handle_checkin(
            user_id, flow_manager.user_states[user_id], "/cancel"
        )
        assert completed
        assert "canceled" in reply.lower()
        assert user_id not in flow_manager.user_states

    def test_handle_checkin_inactivity_expiry(self, flow_manager):
        user_id = _unique_user("checkin_idle")
        flow_manager.user_states[user_id] = {
            "flow": FLOW_CHECKIN,
            "state": CHECKIN_MOOD,
            "data": {},
            "question_order": ["mood"],
            "current_question_index": 0,
            "last_activity": _past_timestamp(200),
        }
        reply, completed = flow_manager._handle_checkin(
            user_id, flow_manager.user_states[user_id], "feeling okay"
        )
        assert completed
        assert "expired" in reply.lower()


@pytest.mark.unit
@pytest.mark.communication
class TestTaskFlowExpansion:
    """Task reminder follow-up edge paths."""

    def test_reminder_followup_missing_task_id_clears_flow(self, flow_manager):
        user_id = _unique_user("reminder_no_task")
        flow_manager.user_states[user_id] = {
            "flow": FLOW_TASK_REMINDER,
            "state": 0,
            "data": {},
            "started_at": now_timestamp_full(),
        }
        reply, completed = flow_manager._handle_task_reminder_followup(
            user_id, flow_manager.user_states[user_id], "1 hour before"
        )
        assert completed
        assert "couldn't find the task" in reply.lower()
        assert user_id not in flow_manager.user_states

    def test_reminder_followup_skip_no_reminders(self, flow_manager):
        user_id = _unique_user("reminder_skip")
        flow_manager.user_states[user_id] = {
            "flow": FLOW_TASK_REMINDER,
            "state": 0,
            "data": {"task_identifier": "task-1"},
            "started_at": now_timestamp_full(),
        }
        reply, completed = flow_manager._handle_task_reminder_followup(
            user_id, flow_manager.user_states[user_id], "no reminders needed"
        )
        assert completed
        assert "no reminders" in reply.lower()
        assert user_id not in flow_manager.user_states

    def test_reminder_followup_unrelated_command_clears_flow(self, flow_manager):
        user_id = _unique_user("reminder_unrelated")
        flow_manager.user_states[user_id] = {
            "flow": FLOW_TASK_REMINDER,
            "state": 0,
            "data": {"task_identifier": "task-1"},
            "started_at": now_timestamp_full(),
        }
        reply, completed = flow_manager._handle_task_reminder_followup(
            user_id, flow_manager.user_states[user_id], "create task buy milk"
        )
        assert completed
        assert reply == ""
        assert user_id not in flow_manager.user_states

    def test_reminder_followup_no_due_date_on_task(self, flow_manager, test_data_dir):
        user_id = _unique_user("reminder_no_due")
        TestUserFactory.create_basic_user(
            user_id, enable_tasks=True, test_data_dir=test_data_dir
        )
        from tasks import create_task

        task_id = create_task(user_id, title="No due task")
        flow_manager.user_states[user_id] = {
            "flow": FLOW_TASK_REMINDER,
            "state": 0,
            "data": {"task_identifier": task_id},
            "started_at": now_timestamp_full(),
        }
        reply, completed = flow_manager._handle_task_reminder_followup(
            user_id, flow_manager.user_states[user_id], "gibberish timing"
        )
        assert completed
        assert "doesn't have a due date" in reply.lower()
        assert user_id not in flow_manager.user_states

    def test_reminder_followup_timeout_expires_flow(self, flow_manager):
        user_id = _unique_user("reminder_timeout")
        flow_manager.user_states[user_id] = {
            "flow": FLOW_TASK_REMINDER,
            "state": 0,
            "data": {"task_identifier": "task-1"},
            "started_at": _past_timestamp(15),
        }
        reply, completed = flow_manager._handle_task_reminder_followup(
            user_id, flow_manager.user_states[user_id], "1 hour before"
        )
        assert completed
        assert "expired" in reply.lower()
        assert user_id not in flow_manager.user_states
        user_id = _unique_user("reminder_timeout")
        flow_manager.user_states[user_id] = {
            "flow": FLOW_TASK_REMINDER,
            "state": 0,
            "data": {"task_identifier": "task-1"},
            "started_at": _past_timestamp(15),
        }
        reply, completed = flow_manager._handle_task_reminder_followup(
            user_id, flow_manager.user_states[user_id], "1 hour before"
        )
        assert completed
        assert "expired" in reply.lower()
        assert user_id not in flow_manager.user_states


@pytest.mark.integration
@pytest.mark.communication
class TestCheckinFlowNoQuestionsEnabled:
    """Start check-in when preferences have no enabled questions."""

    def test_start_dynamic_checkin_no_questions(self, test_data_dir):
        user_id = _unique_user("no_questions")
        TestUserFactory.create_basic_user(
            user_id, enable_checkins=True, test_data_dir=test_data_dir
        )
        manager = ConversationManager()
        with patch(
            "communication.message_processing.flows.checkin_flow.get_user_data",
            return_value={"preferences": {"checkin_settings": {"questions": {}}}},
        ), patch.object(manager, "_get_cached_checkin_order", return_value=None), patch.object(
            manager, "_select_checkin_questions_with_weighting", return_value=[]
        ):
            message, completed = manager._start_dynamic_checkin(user_id)
        assert completed
        assert "not enabled" in message.lower() or "configure" in message.lower()
