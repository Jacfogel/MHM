"""Real tests for leftover MANUAL_DISCORD_TEST_GUIDE checklist items.

Existing coverage lives in notebook, task-reminder, task-list, and Discord
bot suites. This file fills the remaining checklist gaps with assertions
against handler/InteractionManager behavior, not placeholders.
"""

from __future__ import annotations

import json
import uuid
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from communication.command_handlers.notebook_handler import NotebookHandler
from communication.command_handlers.shared_types import InteractionResponse, ParsedCommand
from communication.message_processing.command_parser import EnhancedCommandParser
from communication.message_processing.conversation_flow_manager import conversation_manager
from communication.message_processing.flows.flow_constants import (
    FLOW_TASK_DUE_DATE,
    FLOW_TASK_PRIORITY,
    TASK_DUE_DATE_SUGGESTIONS,
    TASK_PRIORITY_SUGGESTIONS,
)
from communication.message_processing.interaction_manager import InteractionManager
from notebook.notebook_data_handlers import _get_notebook_file_path
from notebook.notebook_data_manager import (
    create_list,
    create_note,
    get_entry,
    pin_entry,
)
from storage.user_data_v2_base import generate_short_id
from tasks import load_active_tasks
from tasks.task_data_handlers import runtime_task_due_date
from tests.test_helpers.test_utilities import TestUserFactory


def _unique_user(prefix: str) -> str:
    return f"test_checklist_{prefix}_{uuid.uuid4().hex[:8]}"


def _short_id(entry) -> str:
    return entry.short_id or generate_short_id(str(entry.id), str(entry.kind), length=6)


@pytest.mark.behavior
@pytest.mark.communication
@pytest.mark.notebook
class TestManualChecklistNotebookGaps:
    """Checklist 4.2-4.7 items that were not covered by a real handler test."""

    def _user(self, prefix: str, test_data_dir: str) -> str:
        user_id = _unique_user(prefix)
        assert TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
        return user_id

    def _handle(
        self, user_id: str, intent: str, entities: dict, message: str
    ) -> InteractionResponse:
        return NotebookHandler().handle(
            user_id,
            ParsedCommand(
                intent=intent,
                entities=entities,
                confidence=1.0,
                original_message=message,
            ),
        )

    @pytest.mark.file_io
    def test_set_entry_body_replaces_text(self, test_data_dir):
        user_id = self._user("set_body", test_data_dir)
        entry = create_note(user_id, title="Editable", description="old body")
        short_id = _short_id(entry)

        response = self._handle(
            user_id,
            "set_entry_body",
            {"entry_ref": short_id, "text": "new body text"},
            f"!set {short_id} new body text",
        )

        assert response.completed
        assert "updated" in response.message.lower()
        updated = get_entry(user_id, short_id)
        assert updated is not None
        assert updated.description == "new body text"

    @pytest.mark.file_io
    def test_remove_tags_from_entry(self, test_data_dir):
        user_id = self._user("untag", test_data_dir)
        entry = create_note(user_id, title="Tagged", tags=["work", "urgent"])
        short_id = _short_id(entry)

        response = self._handle(
            user_id,
            "remove_tags_from_entry",
            {"entry_ref": short_id, "tags": ["work"]},
            f"!untag {short_id} work",
        )

        assert response.completed
        assert "removed" in response.message.lower()
        updated = get_entry(user_id, short_id)
        assert updated is not None
        assert "work" not in updated.tags
        assert "urgent" in updated.tags

    @pytest.mark.file_io
    def test_unpin_and_archive_unarchive(self, test_data_dir):
        user_id = self._user("org", test_data_dir)
        entry = create_note(user_id, title="Organize me")
        short_id = _short_id(entry)
        assert pin_entry(user_id, str(entry.id), True)

        unpin = self._handle(
            user_id, "unpin_entry", {"entry_ref": short_id}, f"!unpin {short_id}"
        )
        assert unpin.completed
        assert "unpin" in unpin.message.lower()
        assert get_entry(user_id, short_id).pinned is False

        archive = self._handle(
            user_id, "archive_entry", {"entry_ref": short_id}, f"!archive {short_id}"
        )
        assert archive.completed
        assert "archiv" in archive.message.lower()
        assert get_entry(user_id, short_id).status == "archived"

        restore = self._handle(
            user_id,
            "unarchive_entry",
            {"entry_ref": short_id},
            f"!unarchive {short_id}",
        )
        assert restore.completed
        assert get_entry(user_id, short_id).status == "active"

    @pytest.mark.file_io
    def test_set_group_and_list_inbox(self, test_data_dir):
        user_id = self._user("group_inbox", test_data_dir)
        entry = create_note(user_id, title="Inbox note")
        short_id = _short_id(entry)

        grouped = self._handle(
            user_id,
            "set_entry_group",
            {"entry_ref": short_id, "group": "work"},
            f"!group {short_id} work",
        )
        assert grouped.completed
        assert get_entry(user_id, short_id).group == "work"

        inbox_note = create_note(user_id, title="Loose thought")
        inbox = self._handle(user_id, "list_inbox_entries", {}, "!inbox")
        assert inbox.completed
        assert "Loose thought" in inbox.message
        assert inbox_note.title in inbox.message

    @pytest.mark.file_io
    def test_toggle_list_item_undone_and_remove_item(self, test_data_dir):
        user_id = self._user("list_ops", test_data_dir)
        entry = create_list(user_id, title="Groceries", items=["Milk", "Eggs", "Bread"])
        short_id = _short_id(entry)

        done = self._handle(
            user_id,
            "toggle_list_item_done",
            {"entry_ref": short_id, "item_index": 1},
            f"!l done {short_id} 1",
        )
        assert done.completed
        assert get_entry(user_id, short_id).items[0].done is True

        undone = self._handle(
            user_id,
            "toggle_list_item_undone",
            {"entry_ref": short_id, "item_index": 1},
            f"!l undo {short_id} 1",
        )
        assert undone.completed
        assert "undone" in undone.message.lower()
        assert get_entry(user_id, short_id).items[0].done is False

        removed = self._handle(
            user_id,
            "remove_list_item",
            {"entry_ref": short_id, "item_index": 2},
            f"!l remove {short_id} 2",
        )
        assert removed.completed
        assert "removed" in removed.message.lower()
        remaining = [item.text for item in get_entry(user_id, short_id).items]
        assert remaining == ["Milk", "Bread"]

    @pytest.mark.file_io
    def test_create_journal_with_body(self, test_data_dir):
        user_id = self._user("journal", test_data_dir)
        response = self._handle(
            user_id,
            "create_journal",
            {"title": "Today was productive", "description": "Shipped tests"},
            "!j Today was productive",
        )
        assert response.completed
        assert "journal" in response.message.lower() or "saved" in response.message.lower()

        entries_path = _get_notebook_file_path(user_id)
        payload = json.loads(entries_path.read_text(encoding="utf-8"))
        kinds = [item.get("kind") for item in payload.get("entries", [])]
        assert "journal_entry" in kinds

    @pytest.mark.file_io
    def test_quick_note_aliases_create_quick_notes_group(self, test_data_dir):
        user_id = self._user("qnote", test_data_dir)
        parser = EnhancedCommandParser()
        aliases = [
            "qn Project idea",
            "qnote Reminder",
            "quickn Meeting notes",
            "quicknote Shopping list",
            "q note Quick thought",
            "quick note Important reminder",
        ]
        for message in aliases:
            parsed = parser.parse(message)
            assert parsed.parsed_command.intent == "create_quick_note", message
            response = NotebookHandler().handle(user_id, parsed.parsed_command)
            assert response.completed, message
            assert "quick note" in response.message.lower(), response.message

        entries_path = _get_notebook_file_path(user_id)
        payload = json.loads(entries_path.read_text(encoding="utf-8"))
        groups = {item.get("group") for item in payload.get("entries", [])}
        assert "Quick Notes" in groups

    @pytest.mark.file_io
    def test_entries_json_short_ids_groups_and_normalized_tags(self, test_data_dir):
        user_id = self._user("verify_json", test_data_dir)
        response = self._handle(
            user_id,
            "create_note",
            {
                "title": "Work task",
                "description": "Follow up",
                "tags": ["#Work", "URGENT"],
                "group": "work",
            },
            "!n Work task #Work #URGENT",
        )
        assert response.completed

        entries_path = _get_notebook_file_path(user_id)
        payload = json.loads(entries_path.read_text(encoding="utf-8"))
        assert payload.get("schema_version") == 2
        assert isinstance(payload.get("entries"), list)
        entry = payload["entries"][0]
        short_id = entry.get("short_id") or ""
        assert short_id
        assert "-" not in short_id
        assert entry.get("group") == "work"
        assert entry.get("tags") == ["work", "urgent"]

    @pytest.mark.file_io
    def test_recent_pagination_exhausts_without_stale_show_more(self, test_data_dir):
        user_id = self._user("recent_pages", test_data_dir)
        for index in range(5):
            create_note(user_id, title=f"Page Note {index}", description="needle")

        handler = NotebookHandler()
        first = handler.handle(
            user_id,
            ParsedCommand(
                "list_recent_entries",
                {"limit": 2},
                1.0,
                "!recent",
            ),
        )
        actions = (first.rich_data or {}).get("pagination_actions") or []
        assert len(actions) == 1
        page1_text = first.message

        second = handler.handle(
            user_id,
            ParsedCommand(
                actions[0].action,
                actions[0].params | {"offset": actions[0].next_offset, "limit": 2},
                1.0,
                "Show More",
            ),
        )
        assert second.message != page1_text
        second_actions = (second.rich_data or {}).get("pagination_actions") or []
        assert second_actions

        last = handler.handle(
            user_id,
            ParsedCommand(
                second_actions[0].action,
                second_actions[0].params
                | {"offset": second_actions[0].next_offset, "limit": 2},
                1.0,
                "Show More",
            ),
        )
        assert "pagination_actions" not in (last.rich_data or {})


@pytest.mark.behavior
@pytest.mark.communication
@pytest.mark.tasks
@pytest.mark.no_parallel  # conversation_manager.user_states is process-wide
class TestManualChecklistTaskFlows:
    """Checklist 4.1 and 6.1 leftovers through the Discord InteractionManager path."""

    def _user(self, prefix: str, test_data_dir: str) -> str:
        user_id = _unique_user(prefix)
        assert TestUserFactory.create_basic_user(
            user_id, enable_tasks=True, test_data_dir=test_data_dir
        )
        conversation_manager.user_states.pop(user_id, None)
        return user_id

    @patch("scheduler.runtime_access.get_scheduler_manager")
    def test_discord_task_without_due_date_reminder_errors(
        self, mock_get_scheduler, test_data_dir
    ):
        mock_get_scheduler.return_value = MagicMock()
        user_id = self._user("no_due_reminder", test_data_dir)
        manager = InteractionManager()

        first = manager.handle_message(
            user_id, "create task to organize desk", channel_type="discord"
        )
        assert not first.completed
        assert conversation_manager.user_states[user_id]["flow"] == FLOW_TASK_DUE_DATE

        skip = manager.handle_message(user_id, "Skip Question", channel_type="discord")
        assert "priority" in skip.message.lower()

        high = manager.handle_message(user_id, "high", channel_type="discord")
        assert high.completed
        assert user_id not in conversation_manager.user_states

        task = load_active_tasks(user_id)[-1]
        conversation_manager.start_task_reminder_followup(user_id, task["id"])
        reply, completed = conversation_manager._handle_task_reminder_followup(
            user_id, conversation_manager.user_states[user_id], "30 minutes before"
        )
        assert completed
        assert "due date" in reply.lower()

    @patch("scheduler.runtime_access.get_scheduler_manager")
    def test_discord_flow_cancel_clears_created_task(
        self, mock_get_scheduler, test_data_dir
    ):
        mock_get_scheduler.return_value = MagicMock()
        user_id = self._user("cancel_flow", test_data_dir)
        manager = InteractionManager()

        first = manager.handle_message(
            user_id,
            "create task to schedule appointment tomorrow",
            channel_type="discord",
        )
        assert not first.completed
        assert load_active_tasks(user_id)

        cancel = manager.handle_message(user_id, "cancel", channel_type="discord")
        assert cancel.completed
        assert user_id not in conversation_manager.user_states
        assert not load_active_tasks(user_id)

    @patch("scheduler.runtime_access.get_scheduler_manager")
    def test_discord_multiple_tasks_in_sequence(self, mock_get_scheduler, test_data_dir):
        mock_get_scheduler.return_value = MagicMock()
        user_id = self._user("sequence", test_data_dir)
        manager = InteractionManager()

        first = manager.handle_message(
            user_id, "create task to water plants tomorrow", channel_type="discord"
        )
        assert "priority" in first.message.lower()
        skip = manager.handle_message(user_id, "skip", channel_type="discord")
        assert "reminder" in skip.message.lower()
        done = manager.handle_message(user_id, "no reminders", channel_type="discord")
        assert done.completed

        second = manager.handle_message(
            user_id, "create task to call dentist tomorrow", channel_type="discord"
        )
        assert not second.completed
        titles = [task["title"].lower() for task in load_active_tasks(user_id)]
        assert any("water plants" in title for title in titles)
        assert any("dentist" in title for title in titles)

    @patch("scheduler.runtime_access.get_scheduler_manager")
    def test_nt_skip_due_date_high_saves_without_reminder_prompt(
        self, mock_get_scheduler, test_data_dir
    ):
        mock_get_scheduler.return_value = MagicMock()
        user_id = self._user("nt_high", test_data_dir)
        manager = InteractionManager()

        first = manager.handle_message(user_id, "nt call dentist", channel_type="discord")
        assert first.suggestions == list(TASK_DUE_DATE_SUGGESTIONS)
        assert "Skip Question" in first.suggestions
        assert "Undo Task Creation" in first.suggestions

        skip = manager.handle_message(user_id, "Skip Question", channel_type="discord")
        assert skip.suggestions == list(TASK_PRIORITY_SUGGESTIONS)
        assert {"Low", "Medium", "High", "Critical"}.issubset(set(skip.suggestions))
        assert conversation_manager.user_states[user_id]["flow"] == FLOW_TASK_PRIORITY

        saved = manager.handle_message(user_id, "High", channel_type="discord")
        assert saved.completed
        assert user_id not in conversation_manager.user_states
        assert "would you like to set" not in saved.message.lower()
        task = load_active_tasks(user_id)[-1]
        assert task.get("priority") == "high"
        assert runtime_task_due_date(task) is None


@pytest.mark.unit
@pytest.mark.communication
@pytest.mark.tasks
class TestManualChecklistTaskListUi:
    """Checklist 6.1 D leftovers: More hints and picker labels."""

    @pytest.mark.asyncio
    async def test_more_button_shows_update_and_delete_hints(self):
        from communication.communication_channels.discord.ui.task_list_ui import (
            TaskDetailView,
        )

        view = TaskDetailView.__new__(TaskDetailView)
        view.user_id = "user-1"
        view.task_id = "task-abc123"
        view.discord_bot = None
        interaction = AsyncMock()
        with patch(
            "communication.communication_channels.discord.ui.task_list_ui.get_task_by_id",
            return_value={"title": "Buy milk", "short_id": "tbuy001", "id": "task-abc123"},
        ):
            await view.more_button(interaction, MagicMock())  # pyright: ignore[reportCallIssue]

        text = interaction.response.send_message.await_args.args[0]
        assert "update task tbuy001" in text
        assert "delete task tbuy001" in text
        assert interaction.response.send_message.await_args.kwargs["ephemeral"] is True

    def test_task_list_select_includes_title_and_short_id(self):
        from communication.communication_channels.discord.ui.task_list_ui import (
            TaskListSelect,
        )

        captured: dict[str, Any] = {}

        def fake_init(self, **kwargs):
            captured.update(kwargs)

        with patch(
            "communication.communication_channels.discord.ui.task_list_ui.discord.ui.Select.__init__",
            fake_init,
        ):
            TaskListSelect(
                "user-1",
                [{"title": "Call dentist", "task_id": "task-1", "short_id": "tcall01"}],
                None,
            )

        assert captured["placeholder"].startswith("Select a task for details")
        options = captured["options"]
        assert options[0].label == "1. Call dentist"
        assert options[0].description == "tcall01"
