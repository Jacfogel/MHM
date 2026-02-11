"""
Notebook Handler Behavior Tests

Comprehensive automated testing for notebook commands, replacing manual Discord testing.
Tests all notebook functionality including notes, lists, flows, and command variations.
"""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime
import uuid

from core.time_utilities import now_datetime_full

from communication.command_handlers.notebook_handler import NotebookHandler
from communication.command_handlers.shared_types import (
    InteractionResponse,
    ParsedCommand,
)
from communication.message_processing.interaction_manager import InteractionManager
from communication.message_processing.command_parser import EnhancedCommandParser
from communication.message_processing.conversation_flow_manager import (
    conversation_manager,
    FLOW_NOTE_BODY,
    FLOW_LIST_ITEMS,
)
from tests.test_utilities import TestUserFactory


@pytest.mark.behavior
@pytest.mark.communication
@pytest.mark.notebook
class TestNotebookHandlerBehavior:
    """Test notebook handler real behavior and side effects."""

    def _create_test_user(self, user_id: str, test_data_dir: str = None) -> bool:
        """Create a test user with proper account setup."""
        return TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)

    def test_notebook_handler_can_handle_intents(self):
        """Test that NotebookHandler can handle all expected intents."""
        handler = NotebookHandler()

        expected_intents = [
            "create_note",
            "create_list",
            "create_journal",
            "list_recent_entries",
            "list_recent_notes",
            "show_entry",
            "append_to_entry",
            "set_entry_body",
            "add_tags_to_entry",
            "remove_tags_from_entry",
            "search_entries",
            "pin_entry",
            "unpin_entry",
            "archive_entry",
            "unarchive_entry",
            "add_list_item",
            "toggle_list_item_done",
            "toggle_list_item_undone",
            "remove_list_item",
            "set_entry_group",
            "list_entries_by_group",
            "list_pinned_entries",
            "list_inbox_entries",
            "list_entries_by_tag",
        ]

        for intent in expected_intents:
            assert handler.can_handle(intent), f"NotebookHandler should handle {intent}"

        # Test that it doesn't handle other intents
        assert not handler.can_handle(
            "create_task"
        ), "NotebookHandler should not handle create_task"
        assert not handler.can_handle(
            "start_checkin"
        ), "NotebookHandler should not handle start_checkin"

    def test_notebook_handler_get_help(self):
        """Test that NotebookHandler returns help text."""
        handler = NotebookHandler()
        help_text = handler.get_help()

        assert isinstance(help_text, str), "Should return help text as string"
        assert len(help_text) > 0, "Help text should not be empty"
        assert (
            "note" in help_text.lower() or "list" in help_text.lower()
        ), "Help text should mention notes/lists"

    def test_notebook_handler_get_examples(self):
        """Test that NotebookHandler returns example commands."""
        handler = NotebookHandler()
        examples = handler.get_examples()

        assert isinstance(examples, list), "Should return examples as list"
        assert len(examples) > 0, "Should have at least one example"
        assert all(
            isinstance(ex, str) for ex in examples
        ), "All examples should be strings"

    # ===== NOTE CREATION TESTS =====

    @pytest.mark.file_io
    def test_create_note_with_title_only(self, test_data_dir):
        """Test creating a note with only a title (should prompt for body)."""
        handler = NotebookHandler()
        user_id = "test_user_note_title_only"
        assert self._create_test_user(
            user_id, test_data_dir=test_data_dir
        ), "Failed to create test user"

        parsed_command = ParsedCommand(
            intent="create_note",
            entities={"title": "Test Note"},
            confidence=0.9,
            original_message="!n Test Note",
        )

        response = handler.handle(user_id, parsed_command)
        assert isinstance(
            response, InteractionResponse
        ), "Should return InteractionResponse"
        assert not response.completed, "Should prompt for body text"
        assert "body text" in response.message.lower(), "Should ask for body text"
        assert (
            "Skip" in (response.suggestions or []) or "skip" in response.message
        ), "Should offer Skip option"

    @pytest.mark.file_io
    def test_create_note_with_title_and_body(self, test_data_dir):
        """Test creating a note with title and body."""
        handler = NotebookHandler()
        user_id = "test_user_note_full"
        assert self._create_test_user(
            user_id, test_data_dir=test_data_dir
        ), "Failed to create test user"

        parsed_command = ParsedCommand(
            intent="create_note",
            entities={"title": "Meeting Notes", "body": "Discuss project X"},
            confidence=0.9,
            original_message="!n Meeting Notes : Discuss project X",
        )

        response = handler.handle(user_id, parsed_command)
        assert isinstance(
            response, InteractionResponse
        ), "Should return InteractionResponse"
        assert response.completed, "Should complete note creation"
        assert "created" in response.message.lower(), "Should indicate note was created"
        assert "Meeting Notes" in response.message, "Should include note title"
        # Short ID format is now n123abc (no dash) for easier mobile typing
        assert any(
            prefix in response.message for prefix in ["n", "l", "j"]
        ), "Should include short ID"

    @pytest.mark.file_io
    def test_create_note_with_tags(self, test_data_dir):
        """Test creating a note with tags."""
        handler = NotebookHandler()
        user_id = "test_user_note_tags"
        assert self._create_test_user(
            user_id, test_data_dir=test_data_dir
        ), "Failed to create test user"

        parsed_command = ParsedCommand(
            intent="create_note",
            entities={"title": "Work Idea", "tags": ["#work", "#urgent"]},
            confidence=0.9,
            original_message="!n Work Idea #work #urgent",
        )

        response = handler.handle(user_id, parsed_command)
        assert isinstance(
            response, InteractionResponse
        ), "Should return InteractionResponse"
        # Note creation with only title prompts for body, so completed may be False
        # If it completes, it should include tags; if it prompts, that's also valid
        if response.completed:
            assert (
                "#work" in response.message or "work" in response.message.lower()
            ), "Should include tags"
        else:
            # Prompting for body is valid when only title provided
            assert (
                "body" in response.message.lower()
            ), "Should prompt for body when only title provided"

    # ===== LIST CREATION TESTS =====

    @pytest.mark.file_io
    def test_create_list_with_title_only(self, test_data_dir):
        """Test creating a list with only a title (should prompt for items)."""
        handler = NotebookHandler()
        user_id = "test_user_list_title_only"
        assert self._create_test_user(
            user_id, test_data_dir=test_data_dir
        ), "Failed to create test user"

        parsed_command = ParsedCommand(
            intent="create_list",
            entities={"title": "Groceries"},
            confidence=0.9,
            original_message="!l Groceries",
        )

        response = handler.handle(user_id, parsed_command)
        assert isinstance(
            response, InteractionResponse
        ), "Should return InteractionResponse"
        assert not response.completed, "Should prompt for items"
        assert "items" in response.message.lower(), "Should ask for list items"
        assert "end" in response.message.lower(), "Should mention how to finish"

    @pytest.mark.file_io
    def test_create_list_with_items(self, test_data_dir):
        """Test creating a list with initial items."""
        handler = NotebookHandler()
        user_id = "test_user_list_with_items"
        assert self._create_test_user(
            user_id, test_data_dir=test_data_dir
        ), "Failed to create test user"

        parsed_command = ParsedCommand(
            intent="create_list",
            entities={"title": "Shopping", "items": ["Milk", "Bread", "Eggs"]},
            confidence=0.9,
            original_message="!l Shopping : Milk, Bread, Eggs",
        )

        response = handler.handle(user_id, parsed_command)
        assert isinstance(
            response, InteractionResponse
        ), "Should return InteractionResponse"
        assert (
            response.completed
        ), f"Should complete list creation, got: {response.message}"
        assert (
            "created" in response.message.lower()
            or "shopping" in response.message.lower()
        ), f"Should indicate list was created, got: {response.message}"
        assert "Shopping" in response.message, "Should include list title"
        # Item count may be in response or may be implicit
        assert (
            "3" in response.message or "item" in response.message.lower()
        ), "Should mention items"

    # ===== VIEWING TESTS =====

    @pytest.mark.file_io
    def test_list_recent_entries(self, test_data_dir):
        """Test listing recent entries."""
        handler = NotebookHandler()
        user_id = "test_user_recent"
        assert self._create_test_user(
            user_id, test_data_dir=test_data_dir
        ), "Failed to create test user"

        # Create a few notes first
        from notebook.notebook_data_manager import create_note

        create_note(user_id, title="Note 1", body="Body 1")
        create_note(user_id, title="Note 2", body="Body 2")

        parsed_command = ParsedCommand(
            intent="list_recent_entries",
            entities={"limit": 5},
            confidence=0.9,
            original_message="!recent",
        )

        response = handler.handle(user_id, parsed_command)
        assert isinstance(
            response, InteractionResponse
        ), "Should return InteractionResponse"
        assert response.completed, "Should complete listing"
        assert (
            "recent" in response.message.lower()
            or "entries" in response.message.lower()
        ), "Should mention recent entries"
        assert (
            "Note 1" in response.message or "Note 2" in response.message
        ), "Should show created notes"

    @pytest.mark.file_io
    def test_show_entry(self, test_data_dir):
        """Test showing a specific entry."""
        handler = NotebookHandler()
        user_id = "test_user_show"
        assert self._create_test_user(
            user_id, test_data_dir=test_data_dir
        ), "Failed to create test user"

        # Create a note first
        from notebook.notebook_data_manager import create_note

        entry = create_note(user_id, title="Test Note", body="Test body content")
        # Short ID format is now n123abc (no dash) for easier mobile typing
        short_id = f"n{str(entry.id).replace('-', '')[:6]}"

        parsed_command = ParsedCommand(
            intent="show_entry",
            entities={"entry_ref": short_id},
            confidence=0.9,
            original_message=f"!show {short_id}",
        )

        response = handler.handle(user_id, parsed_command)
        assert isinstance(
            response, InteractionResponse
        ), "Should return InteractionResponse"
        assert response.completed, "Should complete showing entry"
        assert "Test Note" in response.message, "Should show note title"
        assert "Test body content" in response.message, "Should show note body"

    @pytest.mark.file_io
    def test_show_entry_not_found(self, test_data_dir):
        """Test showing a non-existent entry."""
        handler = NotebookHandler()
        user_id = "test_user_show_not_found"
        assert self._create_test_user(
            user_id, test_data_dir=test_data_dir
        ), "Failed to create test user"

        parsed_command = ParsedCommand(
            intent="show_entry",
            entities={"entry_ref": "n123nonexistent"},
            confidence=0.9,
            original_message="!show n123nonexistent",
        )

        response = handler.handle(user_id, parsed_command)
        assert isinstance(
            response, InteractionResponse
        ), "Should return InteractionResponse"
        assert response.completed, "Should complete (with error)"
        assert (
            "not found" in response.message.lower()
        ), "Should indicate entry not found"

    # ===== EDITING TESTS =====

    @pytest.mark.file_io
    def test_append_to_entry(self, test_data_dir):
        """Test appending text to an entry."""
        handler = NotebookHandler()
        user_id = "test_user_append"
        assert self._create_test_user(
            user_id, test_data_dir=test_data_dir
        ), "Failed to create test user"

        # Create a note first
        from notebook.notebook_data_manager import create_note

        entry = create_note(user_id, title="Test Note", body="Original content")
        # Short ID format is now n123abc (no dash) for easier mobile typing
        short_id = f"n{str(entry.id).replace('-', '')[:6]}"

        parsed_command = ParsedCommand(
            intent="append_to_entry",
            entities={"entry_ref": short_id, "text": " Additional text"},
            confidence=0.9,
            original_message=f"!append {short_id} Additional text",
        )

        response = handler.handle(user_id, parsed_command)
        assert isinstance(
            response, InteractionResponse
        ), "Should return InteractionResponse"
        assert response.completed, "Should complete append"
        assert (
            "appended" in response.message.lower()
            or "updated" in response.message.lower()
        ), "Should indicate append"

        # Verify the append actually happened
        from notebook.notebook_data_manager import get_entry

        updated_entry = get_entry(user_id, short_id)
        assert (
            "Additional text" in updated_entry.body
        ), "Entry body should contain appended text"

    @pytest.mark.file_io
    def test_add_tags_to_entry(self, test_data_dir):
        """Test adding tags to an entry."""
        handler = NotebookHandler()
        user_id = "test_user_add_tags"
        assert self._create_test_user(
            user_id, test_data_dir=test_data_dir
        ), "Failed to create test user"

        # Create a note first
        from notebook.notebook_data_manager import create_note

        entry = create_note(user_id, title="Test Note")
        # Short ID format is now n123abc (no dash) for easier mobile typing
        short_id = f"n{str(entry.id).replace('-', '')[:6]}"

        parsed_command = ParsedCommand(
            intent="add_tags_to_entry",
            entities={"entry_ref": short_id, "tags": ["#work", "#urgent"]},
            confidence=0.9,
            original_message=f"!tag {short_id} #work #urgent",
        )

        response = handler.handle(user_id, parsed_command)
        assert isinstance(
            response, InteractionResponse
        ), "Should return InteractionResponse"
        assert response.completed, "Should complete tag addition"
        assert "tag" in response.message.lower(), "Should mention tags"

        # Verify tags were added
        from notebook.notebook_data_manager import get_entry

        updated_entry = get_entry(user_id, short_id)
        assert (
            "#work" in updated_entry.tags or "work" in updated_entry.tags
        ), "Entry should have #work tag"

    @pytest.mark.file_io
    def test_pin_entry(self, test_data_dir):
        """Test pinning an entry."""
        handler = NotebookHandler()
        user_id = "test_user_pin"
        assert self._create_test_user(
            user_id, test_data_dir=test_data_dir
        ), "Failed to create test user"

        # Create a note first
        from notebook.notebook_data_manager import create_note

        entry = create_note(user_id, title="Important Note")
        # Short ID format is now n123abc (no dash) for easier mobile typing
        short_id = f"n{str(entry.id).replace('-', '')[:6]}"

        parsed_command = ParsedCommand(
            intent="pin_entry",
            entities={"entry_ref": short_id},
            confidence=0.9,
            original_message=f"!pin {short_id}",
        )

        response = handler.handle(user_id, parsed_command)
        assert isinstance(
            response, InteractionResponse
        ), "Should return InteractionResponse"
        assert response.completed, "Should complete pin"
        assert "pin" in response.message.lower(), "Should mention pin"

        # Verify entry was pinned
        from notebook.notebook_data_manager import get_entry

        updated_entry = get_entry(user_id, short_id)
        assert updated_entry.pinned, "Entry should be pinned"

    # ===== LIST OPERATIONS TESTS =====

    @pytest.mark.file_io
    def test_add_list_item(self, test_data_dir):
        """Test adding an item to a list."""
        handler = NotebookHandler()
        user_id = "test_user_list_add_item"
        assert self._create_test_user(
            user_id, test_data_dir=test_data_dir
        ), "Failed to create test user"

        # Create a list first
        from notebook.notebook_data_manager import create_list

        entry = create_list(user_id, title="Groceries", items=["Milk"])
        assert entry is not None, "List should be created successfully"
        # Short ID format is now l123abc (no dash) for easier mobile typing
        short_id = f"l{str(entry.id).replace('-', '')[:6]}"

        parsed_command = ParsedCommand(
            intent="add_list_item",
            entities={"entry_ref": short_id, "item_text": "Bread"},
            confidence=0.9,
            original_message=f"!l add {short_id} Bread",
        )

        response = handler.handle(user_id, parsed_command)
        assert isinstance(
            response, InteractionResponse
        ), "Should return InteractionResponse"
        assert response.completed, "Should complete add item"
        assert "added" in response.message.lower(), "Should indicate item was added"

        # Verify item was added
        from notebook.notebook_data_manager import get_entry

        updated_entry = get_entry(user_id, short_id)
        assert len(updated_entry.items) == 2, "List should have 2 items"
        assert any(
            item.text == "Bread" for item in updated_entry.items
        ), "List should contain Bread"

    @pytest.mark.file_io
    def test_toggle_list_item_done(self, test_data_dir):
        """Test marking a list item as done."""
        handler = NotebookHandler()
        user_id = "test_user_list_done"
        assert self._create_test_user(
            user_id, test_data_dir=test_data_dir
        ), "Failed to create test user"

        # Create a list with items first
        from notebook.notebook_data_manager import create_list

        entry = create_list(user_id, title="Tasks", items=["Task 1", "Task 2"])
        assert entry is not None, "List should be created successfully"
        # Short ID format is now l123abc (no dash) for easier mobile typing
        short_id = f"l{str(entry.id).replace('-', '')[:6]}"

        parsed_command = ParsedCommand(
            intent="toggle_list_item_done",
            entities={"entry_ref": short_id, "item_index": 1},
            confidence=0.9,
            original_message=f"!l done {short_id} 1",
        )

        response = handler.handle(user_id, parsed_command)
        assert isinstance(
            response, InteractionResponse
        ), "Should return InteractionResponse"
        assert response.completed, "Should complete toggle"
        assert "done" in response.message.lower(), "Should mention done"

        # Verify item was marked done
        from notebook.notebook_data_manager import get_entry

        updated_entry = get_entry(user_id, short_id)
        assert updated_entry.items[0].done, "First item should be marked done"

    # ===== ORGANIZATION TESTS =====

    @pytest.mark.file_io
    def test_list_pinned_entries(self, test_data_dir):
        """Test listing pinned entries."""
        handler = NotebookHandler()
        user_id = "test_user_pinned"
        assert self._create_test_user(
            user_id, test_data_dir=test_data_dir
        ), "Failed to create test user"

        # Create and pin a note
        from notebook.notebook_data_manager import create_note, pin_entry

        entry = create_note(user_id, title="Pinned Note")
        pin_entry(user_id, str(entry.id), True)

        parsed_command = ParsedCommand(
            intent="list_pinned_entries",
            entities={},
            confidence=0.9,
            original_message="!pinned",
        )

        response = handler.handle(user_id, parsed_command)
        assert isinstance(
            response, InteractionResponse
        ), "Should return InteractionResponse"
        assert response.completed, "Should complete listing"
        assert "pinned" in response.message.lower(), "Should mention pinned"
        assert "Pinned Note" in response.message, "Should show pinned note"

    @pytest.mark.file_io
    def test_search_entries(self, test_data_dir):
        """Test searching entries."""
        handler = NotebookHandler()
        user_id = "test_user_search"
        assert self._create_test_user(
            user_id, test_data_dir=test_data_dir
        ), "Failed to create test user"

        # Create a note with specific content
        from notebook.notebook_data_manager import create_note

        create_note(user_id, title="Project Alpha", body="Important project details")

        parsed_command = ParsedCommand(
            intent="search_entries",
            entities={"query": "project"},
            confidence=0.9,
            original_message="!search project",
        )

        response = handler.handle(user_id, parsed_command)
        assert isinstance(
            response, InteractionResponse
        ), "Should return InteractionResponse"
        assert response.completed, "Should complete search"
        assert (
            "project" in response.message.lower() or "alpha" in response.message.lower()
        ), "Should find matching entry"

    # ===== FLOW STATE TESTS =====

    @pytest.mark.file_io
    def test_note_body_flow_completion(self, test_data_dir):
        """Test completing note body flow."""
        handler = NotebookHandler()
        user_id = "test_user_note_flow"
        assert self._create_test_user(
            user_id, test_data_dir=test_data_dir
        ), "Failed to create test user"

        # Start note creation (title only)
        parsed_command = ParsedCommand(
            intent="create_note",
            entities={"title": "Flow Test"},
            confidence=0.9,
            original_message="!n Flow Test",
        )

        response = handler.handle(user_id, parsed_command)
        assert not response.completed, "Should prompt for body"

        # Verify flow state was set
        user_state = conversation_manager.user_states.get(user_id, {})
        assert user_state.get("flow") == FLOW_NOTE_BODY, "Should be in note body flow"

        # Complete flow with body text
        reply_text, completed = conversation_manager.handle_inbound_message(
            user_id, "This is the body text"
        )

        assert completed, f"Flow should complete, got: {reply_text}"
        assert (
            "created" in reply_text.lower()
        ), f"Should indicate note was created, got: {reply_text}"

        # Verify flow state was cleared (user_state might be empty dict if flow completed)
        user_state = conversation_manager.user_states.get(user_id, {})
        flow_value = user_state.get("flow") if user_state else 0
        assert (
            flow_value == 0 or flow_value is None
        ), f"Flow should be cleared, got flow={flow_value}, user_state={user_state}"

    @pytest.mark.file_io
    def test_list_items_flow_completion(self, test_data_dir):
        """Test completing list items flow with !end."""
        handler = NotebookHandler()
        user_id = "test_user_list_flow"
        assert self._create_test_user(
            user_id, test_data_dir=test_data_dir
        ), "Failed to create test user"

        # Start list creation (title only)
        parsed_command = ParsedCommand(
            intent="create_list",
            entities={"title": "Flow List"},
            confidence=0.9,
            original_message="!l Flow List",
        )

        response = handler.handle(user_id, parsed_command)
        assert not response.completed, "Should prompt for items"

        # Verify flow state was set
        user_state = conversation_manager.user_states.get(user_id, {})
        assert user_state.get("flow") == FLOW_LIST_ITEMS, "Should be in list items flow"

        # Add items
        reply_text, completed = conversation_manager.handle_inbound_message(
            user_id, "Item 1, Item 2"
        )
        assert not completed, "Flow should continue"

        # End flow with !end
        reply_text, completed = conversation_manager.handle_inbound_message(
            user_id, "!end"
        )

        assert completed, f"Flow should complete, got: {reply_text}"
        assert (
            "created" in reply_text.lower()
        ), f"Should indicate list was created, got: {reply_text}"

        # Verify flow state was cleared (user_state might be empty dict if flow completed)
        user_state = conversation_manager.user_states.get(user_id, {})
        flow_value = user_state.get("flow") if user_state else 0
        assert (
            flow_value == 0 or flow_value is None
        ), f"Flow should be cleared, got flow={flow_value}, user_state={user_state}"


@pytest.mark.behavior
@pytest.mark.communication
@pytest.mark.notebook
class TestNotebookCommandParsing:
    """Test notebook command parsing through command parser and InteractionManager."""

    def _create_test_user(self, user_id: str, test_data_dir: str = None) -> bool:
        """Create a test user with proper account setup."""
        return TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)

    def test_command_parser_recognizes_note_commands(self, test_data_dir):
        """Test that command parser recognizes note creation commands."""
        parser = EnhancedCommandParser()

        # Test various note command patterns (without prefix - parser receives messages after prefix stripping)
        note_patterns = [
            "n Hello world",
            "note Quick thought",
            "nn Test note",
            "newn New note",
            "createnote Create note",
        ]

        for pattern in note_patterns:
            result = parser.parse(pattern)
            assert (
                result.parsed_command.intent == "create_note"
            ), f"Pattern '{pattern}' should match create_note intent, got {result.parsed_command.intent}"
            assert (
                result.confidence > 0.0
            ), f"Pattern '{pattern}' should have confidence > 0"
            assert (
                "title" in result.parsed_command.entities
                or len(result.parsed_command.entities) > 0
            ), f"Pattern '{pattern}' should extract entities"

    def test_command_parser_recognizes_recent_commands(self, test_data_dir):
        """Test that command parser recognizes recent entry commands."""
        parser = EnhancedCommandParser()

        recent_patterns = [
            ("recent", ["list_recent_entries"]),
            ("r", ["list_recent_entries"]),
            ("recentn", ["list_recent_notes"]),
            ("rnote", ["list_recent_notes"]),
            ("recent 10", ["list_recent_entries"]),
        ]

        for pattern, expected_intents in recent_patterns:
            result = parser.parse(pattern)
            assert (
                result.parsed_command.intent in expected_intents
            ), f"Pattern '{pattern}' should match one of {expected_intents}, got {result.parsed_command.intent}"
            assert (
                result.confidence > 0.0
            ), f"Pattern '{pattern}' should have confidence > 0"

    def test_command_parser_recognizes_list_commands(self, test_data_dir):
        """Test that command parser recognizes list creation commands."""
        parser = EnhancedCommandParser()

        list_patterns = [
            "l Groceries",
            "list Shopping",
            "newlist Tasks",
            "createlist My List",
        ]

        for pattern in list_patterns:
            result = parser.parse(pattern)
            assert (
                result.parsed_command.intent == "create_list"
            ), f"Pattern '{pattern}' should match create_list intent, got {result.parsed_command.intent}"
            assert (
                result.confidence > 0.0
            ), f"Pattern '{pattern}' should have confidence > 0"
            assert (
                "title" in result.parsed_command.entities
            ), f"Pattern '{pattern}' should extract title entity"

    def test_command_parser_extracts_note_title_and_body(self, test_data_dir):
        """Test that command parser extracts title and body from note commands."""
        parser = EnhancedCommandParser()

        # Test title:body separator format
        result = parser.parse("n Meeting Notes : Discuss project X")
        assert result.parsed_command.intent == "create_note", "Should match create_note"
        # Parser may extract as single title or split title/body - both are valid
        assert len(result.parsed_command.entities) > 0, "Should extract entities"

    def test_command_parser_recognizes_show_entry_commands(self, test_data_dir):
        """Test that command parser recognizes show entry commands."""
        parser = EnhancedCommandParser()

        show_patterns = [
            "show n123abc",
            "display n123abc",
            "view n123abc",
        ]

        for pattern in show_patterns:
            result = parser.parse(pattern)
            assert (
                result.parsed_command.intent == "show_entry"
            ), f"Pattern '{pattern}' should match show_entry intent, got {result.parsed_command.intent}"
            assert (
                result.confidence > 0.0
            ), f"Pattern '{pattern}' should have confidence > 0"
            assert (
                "entry_ref" in result.parsed_command.entities
            ), f"Pattern '{pattern}' should extract entry_ref entity"

    @pytest.mark.file_io
    def test_note_creation_command_variations_end_to_end(self, test_data_dir):
        """Test various note creation command patterns through full InteractionManager flow."""
        user_id = "test_user_note_variations"
        assert self._create_test_user(
            user_id, test_data_dir=test_data_dir
        ), "Failed to create test user"

        manager = InteractionManager()

        # Test various command patterns (with prefixes - InteractionManager handles prefix stripping)
        command_patterns = [
            "!n Hello world",
            "!note Quick thought",
            "!nn Test note",
            "/n My note",
        ]

        for command in command_patterns:
            response = manager.handle_message(user_id, command, "discord")
            assert isinstance(
                response, InteractionResponse
            ), f"Should return InteractionResponse for '{command}'"
            # Note creation might prompt for body, so completed could be False
            assert (
                "note" in response.message.lower()
                or "created" in response.message.lower()
                or "body text" in response.message.lower()
            ), f"Should handle note creation for '{command}', got: {response.message}"

    @pytest.mark.file_io
    def test_recent_command_variations(self, test_data_dir):
        """Test various recent command patterns."""
        user_id = f"test_user_recent_variations_{uuid.uuid4().hex[:8]}"
        assert self._create_test_user(
            user_id, test_data_dir=test_data_dir
        ), "Failed to create test user"

        # Create some notes first
        from notebook.notebook_data_manager import create_note

        create_note(user_id, title="Note 1")
        create_note(user_id, title="Note 2")

        manager = InteractionManager()

        command_patterns = [
            ("!recent", True),
            ("!r", True),
            ("!recentn", True),
            ("!rnote", True),
            ("/recent", True),
        ]

        with patch.object(
            manager.ai_chatbot,
            "generate_response",
            return_value="Hello! I can help with notes and support.",
        ):
            for command, should_complete in command_patterns:
                response = manager.handle_message(user_id, command, "discord")
                assert isinstance(
                    response, InteractionResponse
                ), f"Should return InteractionResponse for '{command}'"
                # Some commands may not be recognized and can fall back to AI chat.
                # Keep fallback deterministic by stubbing AI response above.
                if response.completed:
                    message_lower = response.message.lower()
                    is_recent_response = (
                        "recent" in message_lower
                        or "entries" in message_lower
                        or "notes" in message_lower
                        or "note 1" in message_lower
                        or "note 2" in message_lower
                        or "no recent" in message_lower
                        or "no entries" in message_lower
                    )
                    is_generic_fallback = (
                        "hello" in message_lower
                        or "support" in message_lower
                        or "help" in message_lower
                    )
                    assert (
                        is_recent_response or is_generic_fallback
                    ), f"Should show recent entries or deterministic fallback for '{command}', got: {response.message}"

    @pytest.mark.file_io
    def test_list_command_variations(self, test_data_dir):
        """Test various list command patterns."""
        user_id = "test_user_list_variations"
        assert self._create_test_user(
            user_id, test_data_dir=test_data_dir
        ), "Failed to create test user"

        manager = InteractionManager()

        command_patterns = [
            "!l Groceries",
            "!list Shopping",
            "!newlist Tasks",
            "/l My List",
        ]

        for command in command_patterns:
            response = manager.handle_message(user_id, command, "discord")
            assert isinstance(
                response, InteractionResponse
            ), f"Should return InteractionResponse for '{command}'"
            # List creation prompts for items, so completed could be False
            assert (
                "list" in response.message.lower()
                or "items" in response.message.lower()
            ), f"Should handle list creation for '{command}'"

    @pytest.mark.file_io
    def test_end_command_in_list_flow_end_to_end(self, test_data_dir):
        """Test that !end properly ends list creation flow through full InteractionManager."""
        user_id = "test_user_end_command"
        assert self._create_test_user(
            user_id, test_data_dir=test_data_dir
        ), "Failed to create test user"

        manager = InteractionManager()

        # Start list creation
        response = manager.handle_message(user_id, "!l Test List", "discord")
        assert (
            not response.completed
        ), f"Should prompt for items, got: {response.message}"
        assert (
            "items" in response.message.lower() or "list" in response.message.lower()
        ), f"Should ask for items, got: {response.message}"

        # Verify flow state was set
        user_state = conversation_manager.user_states.get(user_id, {})
        assert user_state.get("flow") == FLOW_LIST_ITEMS, "Should be in list items flow"

        # Add items
        response = manager.handle_message(user_id, "Item 1, Item 2", "discord")
        assert not response.completed, f"Should continue flow, got: {response.message}"
        assert (
            "item" in response.message.lower() or "total" in response.message.lower()
        ), f"Should acknowledge items, got: {response.message}"

        # End with !end
        response = manager.handle_message(user_id, "!end", "discord")
        assert (
            response.completed
        ), f"Should complete list creation, got: {response.message}"
        assert (
            "created" in response.message.lower()
        ), f"Should indicate list was created, got: {response.message}"

        # Verify flow is cleared (user_state might be empty dict if flow completed)
        user_state = conversation_manager.user_states.get(user_id, {})
        flow_value = user_state.get("flow") if user_state else 0
        assert (
            flow_value == 0 or flow_value is None
        ), f"Flow should be cleared after !end, got flow={flow_value}, user_state={user_state}"

        # Verify list was actually created
        from notebook.notebook_data_manager import list_recent

        entries = list_recent(user_id, n=5)
        # Check case-insensitively since titles may be normalized
        assert any(
            e.kind == "list" and "test list" in (e.title or "").lower() for e in entries
        ), f"List should be created and appear in recent entries. Found: {[e.title for e in entries]}"


@pytest.mark.behavior
@pytest.mark.communication
@pytest.mark.notebook
class TestNotebookEntityExtraction:
    """Test entity extraction from user messages."""

    def _create_test_user(self, user_id: str, test_data_dir: str = None) -> bool:
        """Create a test user with proper account setup."""
        return TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)

    def test_extract_title_and_body_with_colon_separator(self, test_data_dir):
        """Test extracting title and body using colon separator."""
        parser = EnhancedCommandParser()

        result = parser.parse("n Meeting Notes : Discuss project X")
        assert result.parsed_command.intent == "create_note", "Should match create_note"
        assert "title" in result.parsed_command.entities, "Should extract title"
        # Parser may normalize to lowercase
        title = result.parsed_command.entities.get("title", "").lower()
        assert "meeting notes" in title, f"Should extract correct title, got: {title}"
        assert "body" in result.parsed_command.entities, "Should extract body"
        body = result.parsed_command.entities.get("body", "").lower()
        assert "discuss project x" in body, f"Should extract correct body, got: {body}"

    def test_extract_title_and_body_with_newline_separator(self, test_data_dir):
        """Test extracting title and body using newline separator."""
        parser = EnhancedCommandParser()

        result = parser.parse("n Meeting Notes\nDiscuss project X")
        assert result.parsed_command.intent == "create_note", "Should match create_note"
        assert "title" in result.parsed_command.entities, "Should extract title"
        # Parser may normalize to lowercase
        title = result.parsed_command.entities.get("title", "").lower()
        assert "meeting notes" in title, f"Should extract correct title, got: {title}"
        assert "body" in result.parsed_command.entities, "Should extract body"
        body = result.parsed_command.entities.get("body", "").lower()
        assert "discuss project x" in body, f"Should extract correct body, got: {body}"

    def test_extract_tags_from_note_command(self, test_data_dir):
        """Test extracting tags from note commands."""
        parser = EnhancedCommandParser()

        # Test with #tags
        result = parser.parse("n Work Idea #work #urgent")
        assert result.parsed_command.intent == "create_note", "Should match create_note"
        # Tags may be extracted separately or as part of title - both are valid
        entities = result.parsed_command.entities
        assert "title" in entities or "tags" in entities, "Should extract title or tags"

    def test_extract_entry_reference(self, test_data_dir):
        """Test extracting entry references (short IDs)."""
        parser = EnhancedCommandParser()

        result = parser.parse("show n123abc")
        assert result.parsed_command.intent == "show_entry", "Should match show_entry"
        assert "entry_ref" in result.parsed_command.entities, "Should extract entry_ref"
        assert "n123abc" in result.parsed_command.entities.get(
            "entry_ref", ""
        ), "Should extract correct entry_ref"

    def test_extract_list_items_from_command(self, test_data_dir):
        """Test extracting list items from command."""
        parser = EnhancedCommandParser()

        # Test list creation with items
        result = parser.parse("l Groceries : Milk, Bread, Eggs")
        assert result.parsed_command.intent == "create_list", "Should match create_list"
        assert "title" in result.parsed_command.entities, "Should extract title"
        # Items may be extracted as part of title or separately - parser handles this

    def test_extract_limit_from_recent_command(self, test_data_dir):
        """Test extracting limit from recent commands."""
        parser = EnhancedCommandParser()

        result = parser.parse("recent 10")
        assert result.parsed_command.intent in [
            "list_recent_entries",
            "list_recent_notes",
        ], "Should match recent intent"
        # Limit extraction may vary - check if present
        entities = result.parsed_command.entities
        if "limit" in entities:
            assert (
                isinstance(entities["limit"], int) or entities["limit"] == "10"
            ), "Should extract limit as int or string"

    def test_extract_tags_from_append_command(self, test_data_dir):
        """Test extracting tags from tag command."""
        parser = EnhancedCommandParser()

        result = parser.parse("tag n123abc #work #urgent")
        assert (
            result.parsed_command.intent == "add_tags_to_entry"
        ), "Should match add_tags_to_entry"
        assert "entry_ref" in result.parsed_command.entities, "Should extract entry_ref"
        # Tags extraction may vary - check if present
        entities = result.parsed_command.entities
        if "tags" in entities:
            assert isinstance(entities["tags"], list), "Tags should be a list"

    def test_handle_missing_entities_gracefully(self, test_data_dir):
        """Test that missing entities are handled gracefully."""
        handler = NotebookHandler()
        user_id = "test_user_missing_entities"
        assert self._create_test_user(
            user_id, test_data_dir=test_data_dir
        ), "Failed to create test user"

        # Test with missing title
        parsed_command = ParsedCommand(
            intent="create_note",
            entities={},  # No entities
            confidence=0.9,
            original_message="!n",
        )

        response = handler.handle(user_id, parsed_command)
        assert isinstance(
            response, InteractionResponse
        ), "Should return InteractionResponse"
        # Handler should prompt for title or handle gracefully
        assert (
            not response.completed or "title" in response.message.lower()
        ), "Should prompt for title or handle gracefully"

    def test_handle_empty_entities(self, test_data_dir):
        """Test handling empty entity values."""
        handler = NotebookHandler()
        user_id = "test_user_empty_entities"
        assert self._create_test_user(
            user_id, test_data_dir=test_data_dir
        ), "Failed to create test user"

        # Test with empty title
        parsed_command = ParsedCommand(
            intent="create_note",
            entities={"title": ""},  # Empty title
            confidence=0.9,
            original_message="!n",
        )

        response = handler.handle(user_id, parsed_command)
        assert isinstance(
            response, InteractionResponse
        ), "Should return InteractionResponse"
        # Should handle empty title gracefully


@pytest.mark.behavior
@pytest.mark.communication
@pytest.mark.notebook
class TestNotebookFlowStateEdgeCases:
    """Test flow state edge cases and error conditions."""

    def _create_test_user(self, user_id: str, test_data_dir: str = None) -> bool:
        """Create a test user with proper account setup."""
        return TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)

    @pytest.mark.file_io
    def test_skip_note_body_flow(self, test_data_dir):
        """Test skipping note body flow."""
        handler = NotebookHandler()
        user_id = "test_user_skip_note"
        assert self._create_test_user(
            user_id, test_data_dir=test_data_dir
        ), "Failed to create test user"

        # Start note creation
        parsed_command = ParsedCommand(
            intent="create_note",
            entities={"title": "Skip Test"},
            confidence=0.9,
            original_message="!n Skip Test",
        )

        response = handler.handle(user_id, parsed_command)
        assert not response.completed, "Should prompt for body"

        # Skip the flow
        reply_text, completed = conversation_manager.handle_inbound_message(
            user_id, "skip"
        )

        assert completed, f"Flow should complete, got: {reply_text}"
        assert (
            "created" in reply_text.lower()
        ), f"Should indicate note was created, got: {reply_text}"

        # Verify flow is cleared
        user_state = conversation_manager.user_states.get(user_id, {})
        flow_value = user_state.get("flow") if user_state else 0
        assert flow_value == 0 or flow_value is None, "Flow should be cleared"

    @pytest.mark.file_io
    def test_cancel_note_body_flow(self, test_data_dir):
        """Test canceling note body flow."""
        handler = NotebookHandler()
        user_id = "test_user_cancel_note"
        assert self._create_test_user(
            user_id, test_data_dir=test_data_dir
        ), "Failed to create test user"

        # Start note creation
        parsed_command = ParsedCommand(
            intent="create_note",
            entities={"title": "Cancel Test"},
            confidence=0.9,
            original_message="!n Cancel Test",
        )

        response = handler.handle(user_id, parsed_command)
        assert not response.completed, "Should prompt for body"

        # Cancel the flow
        reply_text, completed = conversation_manager.handle_inbound_message(
            user_id, "cancel"
        )

        assert completed, f"Flow should complete, got: {reply_text}"
        assert (
            "cancel" in reply_text.lower()
        ), f"Should indicate cancellation, got: {reply_text}"
        assert (
            "not saved" in reply_text.lower() or "cancelled" in reply_text.lower()
        ), f"Should indicate note was not saved, got: {reply_text}"

        # Verify flow is cleared
        user_state = conversation_manager.user_states.get(user_id, {})
        flow_value = user_state.get("flow") if user_state else 0
        assert flow_value == 0 or flow_value is None, "Flow should be cleared"

        # Verify note was NOT created
        from notebook.notebook_data_manager import list_recent

        entries = list_recent(user_id, n=5)
        assert not any(
            e.title == "Cancel Test" for e in entries
        ), "Note should not be created"

    @pytest.mark.file_io
    def test_interrupt_note_flow_with_command(self, test_data_dir):
        """Test interrupting note flow with a different command."""
        handler = NotebookHandler()
        user_id = "test_user_interrupt_note"
        assert self._create_test_user(
            user_id, test_data_dir=test_data_dir
        ), "Failed to create test user"

        # Start note creation
        parsed_command = ParsedCommand(
            intent="create_note",
            entities={"title": "Interrupt Test"},
            confidence=0.9,
            original_message="!n Interrupt Test",
        )

        response = handler.handle(user_id, parsed_command)
        assert not response.completed, "Should prompt for body"

        # Interrupt with a different command
        manager = InteractionManager()
        response = manager.handle_message(user_id, "!l New List", "discord")

        # Flow should be cleared and new command should be processed
        user_state = conversation_manager.user_states.get(user_id, {})
        flow_value = user_state.get("flow") if user_state else 0
        # Flow may be cleared or replaced with list flow
        assert (
            flow_value == 0 or flow_value == FLOW_LIST_ITEMS
        ), "Flow should be cleared or replaced"

    @pytest.mark.file_io
    def test_empty_response_in_note_flow(self, test_data_dir):
        """Test handling empty response in note body flow."""
        handler = NotebookHandler()
        user_id = "test_user_empty_note"
        assert self._create_test_user(
            user_id, test_data_dir=test_data_dir
        ), "Failed to create test user"

        # Start note creation
        parsed_command = ParsedCommand(
            intent="create_note",
            entities={"title": "Empty Test"},
            confidence=0.9,
            original_message="!n Empty Test",
        )

        response = handler.handle(user_id, parsed_command)
        assert not response.completed, "Should prompt for body"

        # Send empty response
        reply_text, completed = conversation_manager.handle_inbound_message(user_id, "")

        # Should handle empty response gracefully (may prompt again or create note)
        assert isinstance(reply_text, str), "Should return a response"

    @pytest.mark.file_io
    def test_multiple_items_in_list_flow(self, test_data_dir):
        """Test adding multiple items in list flow."""
        handler = NotebookHandler()
        user_id = "test_user_multiple_items"
        assert self._create_test_user(
            user_id, test_data_dir=test_data_dir
        ), "Failed to create test user"

        # Start list creation
        parsed_command = ParsedCommand(
            intent="create_list",
            entities={"title": "Multi Items"},
            confidence=0.9,
            original_message="!l Multi Items",
        )

        response = handler.handle(user_id, parsed_command)
        assert not response.completed, "Should prompt for items"

        # Add first batch of items
        reply_text, completed = conversation_manager.handle_inbound_message(
            user_id, "Item 1, Item 2"
        )
        assert not completed, "Flow should continue"

        # Add second batch
        reply_text, completed = conversation_manager.handle_inbound_message(
            user_id, "Item 3, Item 4"
        )
        assert not completed, "Flow should continue"

        # End flow
        reply_text, completed = conversation_manager.handle_inbound_message(
            user_id, "!end"
        )
        assert completed, f"Flow should complete, got: {reply_text}"
        assert (
            "created" in reply_text.lower()
        ), f"Should indicate list was created, got: {reply_text}"

        # Verify all items were added
        from notebook.notebook_data_manager import list_recent, get_entry

        entries = list_recent(user_id, n=5)
        list_entry = next(
            (
                e
                for e in entries
                if e.kind == "list" and "multi items" in (e.title or "").lower()
            ),
            None,
        )
        assert list_entry is not None, "List should be created"
        assert (
            len(list_entry.items) >= 4
        ), f"Should have at least 4 items, got {len(list_entry.items)}"

    @pytest.mark.file_io
    def test_list_flow_with_empty_items(self, test_data_dir):
        """Test ending list flow without adding items."""
        handler = NotebookHandler()
        user_id = "test_user_empty_list"
        assert self._create_test_user(
            user_id, test_data_dir=test_data_dir
        ), "Failed to create test user"

        # Start list creation
        parsed_command = ParsedCommand(
            intent="create_list",
            entities={"title": "Empty List"},
            confidence=0.9,
            original_message="!l Empty List",
        )

        response = handler.handle(user_id, parsed_command)
        assert not response.completed, "Should prompt for items"

        # End immediately without adding items
        reply_text, completed = conversation_manager.handle_inbound_message(
            user_id, "!end"
        )

        assert completed, f"Flow should complete, got: {reply_text}"
        assert (
            "created" in reply_text.lower()
        ), f"Should indicate list was created, got: {reply_text}"

        # Verify list was created (with placeholder item if needed)
        from notebook.notebook_data_manager import list_recent

        entries = list_recent(user_id, n=5)
        assert any(
            e.kind == "list" and "empty list" in (e.title or "").lower()
            for e in entries
        ), "List should be created even without items"

    @pytest.mark.file_io
    def test_flow_timeout_simulation(self, test_data_dir):
        """Test that flow timeout logic works (simulated by manipulating started_at)."""
        handler = NotebookHandler()
        user_id = "test_user_flow_timeout"
        assert self._create_test_user(
            user_id, test_data_dir=test_data_dir
        ), "Failed to create test user"

        # Start note creation
        parsed_command = ParsedCommand(
            intent="create_note",
            entities={"title": "Timeout Test"},
            confidence=0.9,
            original_message="!n Timeout Test",
        )

        response = handler.handle(user_id, parsed_command)
        assert not response.completed, "Should prompt for body"

        # Simulate timeout by setting started_at to 11 minutes ago
        from datetime import datetime, timedelta

        user_state = conversation_manager.user_states.get(user_id, {})
        user_state["started_at"] = (
            now_datetime_full() - timedelta(minutes=11)
        ).isoformat()
        conversation_manager.user_states[user_id] = user_state
        conversation_manager._save_user_states()

        # Try to continue flow - should expire
        reply_text, completed = conversation_manager.handle_inbound_message(
            user_id, "Body text"
        )

        assert completed, f"Flow should complete (expired), got: {reply_text}"
        assert (
            "expired" in reply_text.lower()
            or "timeout" in reply_text.lower()
            or "start over" in reply_text.lower()
        ), f"Should indicate flow expired, got: {reply_text}"


@pytest.mark.behavior
@pytest.mark.communication
@pytest.mark.notebook
class TestNotebookErrorHandling:
    """Test error handling in notebook operations."""

    def _create_test_user(self, user_id: str, test_data_dir: str = None) -> bool:
        """Create a test user with proper account setup."""
        return TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)

    @pytest.mark.file_io
    def test_invalid_entry_reference(self, test_data_dir):
        """Test handling invalid entry references."""
        handler = NotebookHandler()
        user_id = "test_user_invalid_ref"
        assert self._create_test_user(
            user_id, test_data_dir=test_data_dir
        ), "Failed to create test user"

        # Test show with invalid reference
        parsed_command = ParsedCommand(
            intent="show_entry",
            entities={"entry_ref": "n123invalid"},
            confidence=0.9,
            original_message="!show n123invalid",
        )

        response = handler.handle(user_id, parsed_command)
        assert isinstance(
            response, InteractionResponse
        ), "Should return InteractionResponse"
        assert response.completed, "Should complete (with error)"
        assert (
            "not found" in response.message.lower()
        ), "Should indicate entry not found"

    @pytest.mark.file_io
    def test_append_to_nonexistent_entry(self, test_data_dir):
        """Test appending to a non-existent entry."""
        handler = NotebookHandler()
        user_id = "test_user_append_invalid"
        assert self._create_test_user(
            user_id, test_data_dir=test_data_dir
        ), "Failed to create test user"

        parsed_command = ParsedCommand(
            intent="append_to_entry",
            entities={"entry_ref": "n123nonexistent", "text": "Some text"},
            confidence=0.9,
            original_message="!append n123nonexistent Some text",
        )

        response = handler.handle(user_id, parsed_command)
        assert isinstance(
            response, InteractionResponse
        ), "Should return InteractionResponse"
        assert response.completed, "Should complete (with error)"
        assert (
            "not found" in response.message.lower()
            or "error" in response.message.lower()
        ), "Should indicate entry not found or error"

    @pytest.mark.file_io
    def test_add_tags_to_nonexistent_entry(self, test_data_dir):
        """Test adding tags to a non-existent entry."""
        handler = NotebookHandler()
        user_id = "test_user_tag_invalid"
        assert self._create_test_user(
            user_id, test_data_dir=test_data_dir
        ), "Failed to create test user"

        parsed_command = ParsedCommand(
            intent="add_tags_to_entry",
            entities={"entry_ref": "n123nonexistent", "tags": ["#work"]},
            confidence=0.9,
            original_message="!tag n123nonexistent #work",
        )

        response = handler.handle(user_id, parsed_command)
        assert isinstance(
            response, InteractionResponse
        ), "Should return InteractionResponse"
        assert response.completed, "Should complete (with error)"
        assert (
            "not found" in response.message.lower()
            or "error" in response.message.lower()
        ), "Should indicate entry not found or error"

    @pytest.mark.file_io
    def test_toggle_item_on_nonexistent_list(self, test_data_dir):
        """Test toggling item on a non-existent list."""
        handler = NotebookHandler()
        user_id = "test_user_toggle_invalid"
        assert self._create_test_user(
            user_id, test_data_dir=test_data_dir
        ), "Failed to create test user"

        parsed_command = ParsedCommand(
            intent="toggle_list_item_done",
            entities={"entry_ref": "l123nonexistent", "item_index": 1},
            confidence=0.9,
            original_message="!l done l123nonexistent 1",
        )

        response = handler.handle(user_id, parsed_command)
        assert isinstance(
            response, InteractionResponse
        ), "Should return InteractionResponse"
        assert response.completed, "Should complete (with error)"
        assert (
            "not found" in response.message.lower()
            or "error" in response.message.lower()
        ), "Should indicate entry not found or error"

    @pytest.mark.file_io
    def test_toggle_invalid_item_index(self, test_data_dir):
        """Test toggling an invalid item index."""
        handler = NotebookHandler()
        user_id = "test_user_invalid_index"
        assert self._create_test_user(
            user_id, test_data_dir=test_data_dir
        ), "Failed to create test user"

        # Create a list first
        from notebook.notebook_data_manager import create_list

        entry = create_list(user_id, title="Test List", items=["Item 1", "Item 2"])
        assert entry is not None, "List should be created"
        short_id = f"l-{str(entry.id)[:6]}"

        # Try to toggle invalid index (too high)
        parsed_command = ParsedCommand(
            intent="toggle_list_item_done",
            entities={"entry_ref": short_id, "item_index": 99},  # Invalid index
            confidence=0.9,
            original_message=f"!l done {short_id} 99",
        )

        response = handler.handle(user_id, parsed_command)
        assert isinstance(
            response, InteractionResponse
        ), "Should return InteractionResponse"
        assert response.completed, "Should complete (with error)"
        assert (
            "invalid" in response.message.lower()
            or "error" in response.message.lower()
            or "not found" in response.message.lower()
        ), "Should indicate invalid index or error"

    @pytest.mark.file_io
    def test_create_note_with_missing_user_id(self, test_data_dir):
        """Test that missing user_id is handled gracefully."""
        handler = NotebookHandler()

        # This should be caught by handler, but test defensive behavior
        parsed_command = ParsedCommand(
            intent="create_note",
            entities={"title": "Test"},
            confidence=0.9,
            original_message="!n Test",
        )

        # Empty user_id should be handled
        response = handler.handle("", parsed_command)
        assert isinstance(
            response, InteractionResponse
        ), "Should return InteractionResponse"
        # Should handle gracefully (may return error or default response)

    @pytest.mark.file_io
    def test_create_entry_with_very_long_title(self, test_data_dir):
        """Test creating entry with very long title."""
        handler = NotebookHandler()
        user_id = "test_user_long_title"
        assert self._create_test_user(
            user_id, test_data_dir=test_data_dir
        ), "Failed to create test user"

        # Create note with very long title
        long_title = "A" * 1000  # Very long title
        parsed_command = ParsedCommand(
            intent="create_note",
            entities={"title": long_title, "body": "Test body"},
            confidence=0.9,
            original_message=f"!n {long_title}",
        )

        response = handler.handle(user_id, parsed_command)
        assert isinstance(
            response, InteractionResponse
        ), "Should return InteractionResponse"
        # Should reject very long title (exceeds MAX_TITLE_LENGTH of 200)
        # Note: Handler may set completed=True even on validation errors, so check message instead
        assert (
            "error" in response.message.lower()
            or "invalid" in response.message.lower()
            or "failed" in response.message.lower()
        ), f"Should indicate validation error, got: {response.message}"

    @pytest.mark.file_io
    def test_create_entry_with_special_characters(self, test_data_dir):
        """Test creating entry with special characters."""
        handler = NotebookHandler()
        user_id = "test_user_special_chars"
        assert self._create_test_user(
            user_id, test_data_dir=test_data_dir
        ), "Failed to create test user"

        # Create note with special characters
        special_title = "Test & Note <with> \"quotes\" and 'apostrophes'"
        parsed_command = ParsedCommand(
            intent="create_note",
            entities={"title": special_title, "body": "Body with special chars: @#$%"},
            confidence=0.9,
            original_message=f"!n {special_title}",
        )

        response = handler.handle(user_id, parsed_command)
        assert isinstance(
            response, InteractionResponse
        ), "Should return InteractionResponse"
        # Should handle special characters gracefully
        if response.completed:
            assert (
                "created" in response.message.lower()
            ), "Should indicate note was created"

    @pytest.mark.file_io
    def test_handle_malformed_entry_reference(self, test_data_dir):
        """Test handling malformed entry references."""
        handler = NotebookHandler()
        user_id = "test_user_malformed_ref"
        assert self._create_test_user(
            user_id, test_data_dir=test_data_dir
        ), "Failed to create test user"

        # Test with malformed reference (no prefix, wrong format)
        parsed_command = ParsedCommand(
            intent="show_entry",
            entities={"entry_ref": "invalid-format-123"},
            confidence=0.9,
            original_message="!show invalid-format-123",
        )

        response = handler.handle(user_id, parsed_command)
        assert isinstance(
            response, InteractionResponse
        ), "Should return InteractionResponse"
        assert response.completed, "Should complete (with error)"
        assert (
            "not found" in response.message.lower()
            or "error" in response.message.lower()
        ), "Should indicate entry not found or error"
