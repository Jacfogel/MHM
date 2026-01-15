# communication/command_handlers/notebook_handler.py

"""
Notebook command handler.

This module handles all notebook-related interactions including creating,
viewing, updating, and searching notebook entries (notes, lists, journal).
"""

from typing import Dict, List, Any, Optional
from datetime import datetime

from core.logger import get_component_logger
from core.error_handling import handle_errors
from core.tags import parse_tags_from_text

from communication.command_handlers.base_handler import InteractionHandler
from communication.command_handlers.shared_types import (
    InteractionResponse,
    ParsedCommand,
)
from notebook.notebook_data_manager import (
    get_entry,
    list_recent,
    append_to_entry_body,
    set_entry_body,
    add_tags,
    remove_tags,
    search_entries,
    pin_entry,
    archive_entry,
    add_list_item,
    toggle_list_item_done,
    remove_list_item,
    set_group,
    list_by_group,
    list_pinned,
    list_inbox,
    list_by_tag,
    list_archived,
    create_note,
    create_list,
    create_journal,
)
from notebook.schemas import Entry
from notebook.notebook_validation import format_short_id

logger = get_component_logger("communication_manager")
handlers_logger = logger


class NotebookHandler(InteractionHandler):
    """Handler for notebook management interactions."""

    @handle_errors("checking if can handle notebook intent", default_return=False)
    def can_handle(self, intent: str) -> bool:
        """Check if this handler can handle the given intent."""
        if not intent:
            return False
        return intent in [
            "create_note",
            "create_quick_note",
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
            "list_archived_entries",
        ]

    @handle_errors(
        "handling notebook interaction",
        default_return=InteractionResponse(
            "I'm having trouble with your notebook right now. Please try again.", True
        ),
    )
    def handle(
        self, user_id: str, parsed_command: ParsedCommand
    ) -> InteractionResponse:
        """Handle notebook interactions."""
        intent = parsed_command.intent
        entities = parsed_command.entities

        if intent == "create_note":
            return self._handle_create_note(user_id, entities)
        elif intent == "create_quick_note":
            return self._handle_create_quick_note(user_id, entities)
        elif intent == "create_list":
            return self._handle_create_list(user_id, entities)
        elif intent == "create_journal":
            return self._handle_create_journal(user_id, entities)
        elif intent == "list_recent_entries":
            return self._handle_list_recent(user_id, entities)
        elif intent == "show_entry":
            return self._handle_show_entry(user_id, entities)
        elif intent == "append_to_entry":
            return self._handle_append_to_entry(user_id, entities)
        elif intent == "set_entry_body":
            return self._handle_set_entry_body(user_id, entities)
        elif intent == "add_tags_to_entry":
            return self._handle_add_tags(user_id, entities)
        elif intent == "remove_tags_from_entry":
            return self._handle_remove_tags(user_id, entities)
        elif intent == "search_entries":
            return self._handle_search_entries(user_id, entities)
        elif intent == "pin_entry":
            return self._handle_pin_entry(user_id, entities, True)
        elif intent == "unpin_entry":
            return self._handle_pin_entry(user_id, entities, False)
        elif intent == "archive_entry":
            return self._handle_archive_entry(user_id, entities, True)
        elif intent == "unarchive_entry":
            return self._handle_archive_entry(user_id, entities, False)
        elif intent == "add_list_item":
            return self._handle_add_list_item(user_id, entities)
        elif intent == "toggle_list_item_done":
            return self._handle_toggle_list_item_done(user_id, entities)
        elif intent == "toggle_list_item_undone":
            return self._handle_toggle_list_item_done(user_id, entities, done=False)
        elif intent == "remove_list_item":
            return self._handle_remove_list_item(user_id, entities)
        elif intent == "list_recent_notes":
            return self._handle_list_recent(user_id, entities, notes_only=True)
        elif intent == "set_entry_group":
            return self._handle_set_group(user_id, entities)
        elif intent == "list_entries_by_group":
            return self._handle_list_by_group(user_id, entities)
        elif intent == "list_pinned_entries":
            return self._handle_list_pinned(user_id)
        elif intent == "list_inbox_entries":
            return self._handle_list_inbox(user_id)
        elif intent == "list_entries_by_tag":
            return self._handle_list_by_tag(user_id, entities)
        elif intent == "list_archived_entries":
            return self._handle_list_archived(user_id, entities)
        else:
            return InteractionResponse(
                f"I don't understand that notebook command. Try: {', '.join(self.get_examples())}",
                True,
            )

    # Create handlers
    @handle_errors("handling create note")
    def _handle_create_note(
        self, user_id: str, entities: Dict[str, Any]
    ) -> InteractionResponse:
        """Handle note creation."""
        from communication.message_processing.conversation_flow_manager import (
            FLOW_NOTE_BODY,
            conversation_manager,
        )

        title = entities.get("title")
        body = entities.get("body")
        tags = entities.get("tags", [])
        group = entities.get("group")

        # Check if user is in a note body flow (continuing from previous prompt)
        # This shouldn't happen here since flow is handled in conversation_manager,
        # but handle it just in case
        user_state = conversation_manager.user_states.get(user_id, {})
        if user_state.get("flow") == FLOW_NOTE_BODY and body:
            # Flow was already handled, but we have the body now
            flow_data = user_state.get("data", {})
            title = flow_data.get("title", title)
            tags = flow_data.get("tags", tags)
            group = flow_data.get("group", group)

        # If both title and body are missing, prompt for title
        if not title and not body:
            return InteractionResponse(
                "📝 What would you like to name this note? (You can add body text after)",
                False,
            )

        # If no body provided and we have a title, start flow to prompt for it
        if not body and title:
            # Parse tags from title first
            title, parsed_tags = parse_tags_from_text(title)
            tags.extend(parsed_tags)

            # Start flow to prompt for body
            conversation_manager.user_states[user_id] = {
                "flow": FLOW_NOTE_BODY,
                "state": 0,
                "data": {"title": title, "tags": tags, "group": group},
                "started_at": datetime.now().isoformat(),
            }
            conversation_manager._save_user_states()
            return InteractionResponse(
                f"📝 Note title: '{title}'\n\nWhat would you like to add as the body text? [Skip] [Cancel]",
                False,
                suggestions=["Skip", "Cancel"],
            )

        # If no title but body exists, use body as title (for simple notes like "!n My quick thought")
        if not title and body:
            title = body
            body = None

        # Parse tags from body if present
        if body:
            body, parsed_tags = parse_tags_from_text(body)
            tags.extend(parsed_tags)
        elif title:
            # Also parse tags from title if body is None
            title, parsed_tags = parse_tags_from_text(title)
            tags.extend(parsed_tags)

        entry = create_note(user_id, title=title, body=body, tags=tags, group=group)

        if entry:
            short_id = self._format_entry_id(entry)
            # Show title if available, otherwise body, otherwise "Untitled"
            display_name = entry.title or entry.body or "Untitled"
            response = f"✅ Note created: '{display_name}' ({short_id})"
            if entry.tags:
                response += f"\nTags: {', '.join(entry.tags)}"
            return InteractionResponse(response, True)
        else:
            return InteractionResponse(
                "❌ Failed to create note. Please try again.", True
            )

    @handle_errors("handling create quick note")
    def _handle_create_quick_note(
        self, user_id: str, entities: Dict[str, Any]
    ) -> InteractionResponse:
        """Handle quick note creation - no body text required, automatically grouped as 'Quick Notes'."""
        from datetime import datetime

        title = entities.get("title")
        tags = entities.get("tags", [])
        # Quick notes are always in "Quick Notes" group
        group = "Quick Notes"

        # If no title provided, use a default
        if not title or not title.strip():
            # Use timestamp as default title for quick notes
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
            title = f"Quick Note - {timestamp}"

        # Parse tags from title if present
        if title:
            title, parsed_tags = parse_tags_from_text(title)
            tags.extend(parsed_tags)

        # Create note with title only, no body, always in "Quick Notes" group
        entry = create_note(user_id, title=title, body=None, tags=tags, group=group)

        if entry:
            short_id = self._format_entry_id(entry)
            response = f"✅ Quick note created: '{entry.title}' ({short_id})"
            if entry.tags:
                response += f"\nTags: {', '.join(entry.tags)}"
            return InteractionResponse(response, True)
        else:
            return InteractionResponse(
                "❌ Failed to create quick note. Please try again.", True
            )

    @handle_errors("handling create list")
    def _handle_create_list(
        self, user_id: str, entities: Dict[str, Any]
    ) -> InteractionResponse:
        """Handle list creation."""
        from communication.message_processing.conversation_flow_manager import (
            FLOW_LIST_ITEMS,
            conversation_manager,
        )

        title = entities.get("title")
        tags = entities.get("tags", [])
        group = entities.get("group")
        items = entities.get("items", [])

        if not title:
            return InteractionResponse("What would you like to name the list?", False)

        # If no items provided, start flow to collect them
        if not items:
            # Parse tags from title first
            from core.tags import parse_tags_from_text

            title, parsed_tags = parse_tags_from_text(title)
            tags.extend(parsed_tags)

            # Start flow to prompt for items
            conversation_manager.user_states[user_id] = {
                "flow": FLOW_LIST_ITEMS,
                "state": 0,
                "data": {"title": title, "tags": tags, "group": group, "items": []},
                "started_at": datetime.now().isoformat(),
            }
            conversation_manager._save_user_states()
            return InteractionResponse(
                f"📋 List: '{title}'\n\nAdd list items (separated by commas, semicolons, or new lines). Type `!end`, `/end`, or 'end' to finish.",
                False,
                suggestions=["End List", "Cancel"],
            )

        # Items provided, create list immediately
        entry = create_list(user_id, title=title, tags=tags, group=group, items=items)

        if entry:
            short_id = self._format_entry_id(entry)
            response = (
                f"✅ List created: '{title}' ({short_id}) with {len(items)} items"
            )
            if entry.tags:
                response += f"\nTags: {', '.join(entry.tags)}"
            return InteractionResponse(response, True)
        else:
            return InteractionResponse(
                "❌ Failed to create list. Please try again.", True
            )

    @handle_errors("handling create journal")
    def _handle_create_journal(
        self, user_id: str, entities: Dict[str, Any]
    ) -> InteractionResponse:
        """Handle journal entry creation."""
        title = entities.get("title")
        body = entities.get("body")
        tags = entities.get("tags", [])
        group = entities.get("group")

        entry = create_journal(user_id, title=title, body=body, tags=tags, group=group)

        if entry:
            short_id = self._format_entry_id(entry)
            response = (
                f"✅ Journal entry created: '{entry.title or 'Untitled'}' ({short_id})"
            )
            if entry.tags:
                response += f"\nTags: {', '.join(entry.tags)}"
            return InteractionResponse(response, True)
        else:
            return InteractionResponse(
                "❌ Failed to create journal entry. Please try again.", True
            )

    # Read handlers
    @handle_errors("handling list recent")
    def _handle_list_recent(
        self, user_id: str, entities: Dict[str, Any], notes_only: bool = False
    ) -> InteractionResponse:
        """Handle listing recent entries."""
        n = entities.get("limit", 5)
        if isinstance(n, str):
            try:
                n = int(n)
            except ValueError:
                n = 5

        entries = list_recent(user_id, n=n)

        # Filter to notes only if requested
        if notes_only:
            entries = [e for e in entries if e.kind == "note"]

        if not entries:
            return InteractionResponse(
                (
                    "No recent entries found."
                    if not notes_only
                    else "No recent notes found."
                ),
                True,
            )

        response_parts = [
            f"📝 Recent {'notes' if notes_only else 'entries'} ({len(entries)}):"
        ]
        for entry in entries:
            short_id = self._format_entry_id(entry)
            title = entry.title or "Untitled"
            kind_icon = {"note": "📄", "list": "📋", "journal": "📔"}.get(
                entry.kind, "📝"
            )
            response_parts.append(f"{kind_icon} {title} ({short_id})")

        return InteractionResponse("\n".join(response_parts), True)

    @handle_errors("handling show entry")
    def _handle_show_entry(
        self, user_id: str, entities: Dict[str, Any]
    ) -> InteractionResponse:
        """Handle showing an entry."""
        entry_ref = entities.get("entry_ref")

        if not entry_ref:
            return InteractionResponse(
                "Which entry would you like to see? (Provide ID or title)", False
            )

        entry = get_entry(user_id, entry_ref)

        if not entry:
            return InteractionResponse(f"❌ Entry not found: {entry_ref}", True)

        return InteractionResponse(self._format_entry_response(entry), True)

    # Update handlers
    @handle_errors("handling append to entry")
    def _handle_append_to_entry(
        self, user_id: str, entities: Dict[str, Any]
    ) -> InteractionResponse:
        """Handle appending to entry body."""
        entry_ref = entities.get("entry_ref")
        text = entities.get("text") or entities.get("body")

        if not entry_ref:
            return InteractionResponse(
                "Which entry would you like to append to?", False
            )
        if not text:
            return InteractionResponse("What would you like to add?", False)

        entry = append_to_entry_body(user_id, entry_ref, text)

        if entry:
            short_id = self._format_entry_id(entry)
            return InteractionResponse(
                f"✅ Appended to '{entry.title or 'Untitled'}' ({short_id})", True
            )
        else:
            return InteractionResponse(
                f"❌ Failed to append. Entry not found or invalid.", True
            )

    @handle_errors("handling set entry body")
    def _handle_set_entry_body(
        self, user_id: str, entities: Dict[str, Any]
    ) -> InteractionResponse:
        """Handle setting entry body."""
        entry_ref = entities.get("entry_ref")
        text = entities.get("text") or entities.get("body")

        if not entry_ref:
            return InteractionResponse("Which entry would you like to edit?", False)
        if not text:
            return InteractionResponse("What should the new content be?", False)

        entry = set_entry_body(user_id, entry_ref, text)

        if entry:
            short_id = self._format_entry_id(entry)
            return InteractionResponse(
                f"✅ Updated '{entry.title or 'Untitled'}' ({short_id})", True
            )
        else:
            return InteractionResponse(
                f"❌ Failed to update. Entry not found or invalid.", True
            )

    @handle_errors("handling add tags")
    def _handle_add_tags(
        self, user_id: str, entities: Dict[str, Any]
    ) -> InteractionResponse:
        """Handle adding tags to entry."""
        entry_ref = entities.get("entry_ref")
        tags = entities.get("tags", [])

        if not entry_ref:
            return InteractionResponse("Which entry would you like to tag?", False)
        if not tags:
            return InteractionResponse("Which tags would you like to add?", False)

        entry = add_tags(user_id, entry_ref, tags)

        if entry:
            short_id = self._format_entry_id(entry)
            return InteractionResponse(
                f"✅ Tags added to '{entry.title or 'Untitled'}' ({short_id}): {', '.join(entry.tags)}",
                True,
            )
        else:
            return InteractionResponse(f"❌ Failed to add tags. Entry not found.", True)

    @handle_errors("handling remove tags")
    def _handle_remove_tags(
        self, user_id: str, entities: Dict[str, Any]
    ) -> InteractionResponse:
        """Handle removing tags from entry."""
        entry_ref = entities.get("entry_ref")
        tags = entities.get("tags", [])

        if not entry_ref:
            return InteractionResponse("Which entry would you like to untag?", False)
        if not tags:
            return InteractionResponse("Which tags would you like to remove?", False)

        entry = remove_tags(user_id, entry_ref, tags)

        if entry:
            short_id = self._format_entry_id(entry)
            return InteractionResponse(
                f"✅ Tags removed from '{entry.title or 'Untitled'}' ({short_id})", True
            )
        else:
            return InteractionResponse(
                f"❌ Failed to remove tags. Entry not found.", True
            )

    @handle_errors("handling search entries")
    def _handle_search_entries(
        self, user_id: str, entities: Dict[str, Any]
    ) -> InteractionResponse:
        """Handle searching entries."""
        query = entities.get("query")
        offset = entities.get("offset", 0)
        limit = entities.get("limit", 5)

        if not query:
            return InteractionResponse("What would you like to search for?", False)

        entries = search_entries(
            user_id, query, limit=100
        )  # Get all matches, paginate in handler

        if not entries:
            return InteractionResponse(f"No entries found matching '{query}'.", True)

        total = len(entries)
        paginated = entries[offset : offset + limit]
        has_more = offset + limit < total

        response_parts = [f"🔍 Found {total} entries:"]
        for entry in paginated:
            short_id = self._format_entry_id(entry)
            title = entry.title or "Untitled"
            response_parts.append(f"• {title} ({short_id})")

        if has_more:
            remaining = total - (offset + limit)
            response_parts.append(f"\n... and {remaining} more")

        suggestions = []
        if has_more:
            # Add "Show More" button with pagination info
            next_offset = offset + limit
            suggestions.append(f"Show More ({min(limit, remaining)} more)")

        return InteractionResponse(
            "\n".join(response_parts),
            True,
            suggestions=suggestions if suggestions else None,
        )

    @handle_errors("handling pin entry")
    def _handle_pin_entry(
        self, user_id: str, entities: Dict[str, Any], pinned: bool
    ) -> InteractionResponse:
        """Handle pinning/unpinning entry."""
        entry_ref = entities.get("entry_ref")

        if not entry_ref:
            return InteractionResponse(
                "Which entry would you like to pin/unpin?", False
            )

        entry = pin_entry(user_id, entry_ref, pinned)

        if entry:
            action = "pinned" if pinned else "unpinned"
            short_id = self._format_entry_id(entry)
            return InteractionResponse(
                f"✅ {action.capitalize()} '{entry.title or 'Untitled'}' ({short_id})",
                True,
            )
        else:
            return InteractionResponse(
                f"❌ Failed to pin/unpin. Entry not found.", True
            )

    @handle_errors("handling archive entry")
    def _handle_archive_entry(
        self, user_id: str, entities: Dict[str, Any], archived: bool
    ) -> InteractionResponse:
        """Handle archiving/unarchiving entry."""
        entry_ref = entities.get("entry_ref")

        if not entry_ref:
            return InteractionResponse(
                "Which entry would you like to archive/unarchive?", False
            )

        entry = archive_entry(user_id, entry_ref, archived)

        if entry:
            action = "archived" if archived else "unarchived"
            short_id = self._format_entry_id(entry)
            return InteractionResponse(
                f"✅ {action.capitalize()} '{entry.title or 'Untitled'}' ({short_id})",
                True,
            )
        else:
            return InteractionResponse(
                f"❌ Failed to archive/unarchive. Entry not found.", True
            )

    # List item handlers
    @handle_errors("handling add list item")
    def _handle_add_list_item(
        self, user_id: str, entities: Dict[str, Any]
    ) -> InteractionResponse:
        """Handle adding item to list."""
        entry_ref = entities.get("entry_ref")
        item_text = entities.get("item_text") or entities.get("text")

        if not entry_ref:
            return InteractionResponse("Which list would you like to add to?", False)
        if not item_text:
            return InteractionResponse("What item would you like to add?", False)

        entry = add_list_item(user_id, entry_ref, item_text)

        if entry:
            short_id = self._format_entry_id(entry)
            return InteractionResponse(
                f"✅ Added item to '{entry.title}' ({short_id})", True
            )
        else:
            return InteractionResponse(
                f"❌ Failed to add item. List not found or invalid.", True
            )

    @handle_errors("handling toggle list item done")
    def _handle_toggle_list_item_done(
        self, user_id: str, entities: Dict[str, Any]
    ) -> InteractionResponse:
        """Handle toggling list item done status."""
        entry_ref = entities.get("entry_ref")
        item_index = entities.get("item_index")
        done = entities.get("done", True)

        if not entry_ref:
            return InteractionResponse("Which list?", False)
        if item_index is None:
            return InteractionResponse("Which item number?", False)

        try:
            item_index = int(item_index) - 1  # Convert to 0-based
        except (ValueError, TypeError):
            return InteractionResponse("Invalid item number.", True)

        entry = toggle_list_item_done(user_id, entry_ref, item_index, done)

        if entry:
            short_id = self._format_entry_id(entry)
            action = "marked done" if done else "marked undone"
            return InteractionResponse(
                f"✅ Item {item_index + 1} {action} in '{entry.title}' ({short_id})",
                True,
            )
        else:
            return InteractionResponse(
                f"❌ Failed to toggle item. List not found or invalid.", True
            )

    @handle_errors("handling remove list item")
    def _handle_remove_list_item(
        self, user_id: str, entities: Dict[str, Any]
    ) -> InteractionResponse:
        """Handle removing item from list."""
        entry_ref = entities.get("entry_ref")
        item_index = entities.get("item_index")

        if not entry_ref:
            return InteractionResponse("Which list?", False)
        if item_index is None:
            return InteractionResponse("Which item number?", False)

        try:
            item_index = int(item_index) - 1  # Convert to 0-based
        except (ValueError, TypeError):
            return InteractionResponse("Invalid item number.", True)

        entry = remove_list_item(user_id, entry_ref, item_index)

        if entry:
            short_id = self._format_entry_id(entry)
            return InteractionResponse(
                f"✅ Removed item {item_index + 1} from '{entry.title}' ({short_id})",
                True,
            )
        else:
            return InteractionResponse(
                f"❌ Failed to remove item. List not found or invalid.", True
            )

    # Organization handlers
    @handle_errors("handling set group")
    def _handle_set_group(
        self, user_id: str, entities: Dict[str, Any]
    ) -> InteractionResponse:
        """Handle setting entry group."""
        entry_ref = entities.get("entry_ref")
        group = entities.get("group")

        if not entry_ref:
            return InteractionResponse("Which entry?", False)
        if not group:
            return InteractionResponse("What group name?", False)

        entry = set_group(user_id, entry_ref, group)

        if entry:
            short_id = self._format_entry_id(entry)
            return InteractionResponse(
                f"✅ Set group '{group}' for '{entry.title or 'Untitled'}' ({short_id})",
                True,
            )
        else:
            return InteractionResponse(
                f"❌ Failed to set group. Entry not found.", True
            )

    @handle_errors("handling list by group")
    def _handle_list_by_group(
        self, user_id: str, entities: Dict[str, Any]
    ) -> InteractionResponse:
        """Handle listing entries by group."""
        group = entities.get("group")
        offset = entities.get("offset", 0)
        limit = entities.get("limit", 5)

        if not group:
            return InteractionResponse("Which group?", False)

        entries = list_by_group(
            user_id, group, limit=100
        )  # Get all matches, paginate in handler

        if not entries:
            return InteractionResponse(f"No entries found in group '{group}'.", True)

        total = len(entries)
        paginated = entries[offset : offset + limit]
        has_more = offset + limit < total

        response_parts = [f"📁 Group '{group}' ({total} entries):"]
        for entry in paginated:
            short_id = self._format_entry_id(entry)
            response_parts.append(f"• {entry.title or 'Untitled'} ({short_id})")

        if has_more:
            remaining = total - (offset + limit)
            response_parts.append(f"\n... and {remaining} more")

        suggestions = []
        if has_more:
            remaining = total - (offset + limit)
            suggestions.append(f"Show More ({min(limit, remaining)} more)")

        return InteractionResponse(
            "\n".join(response_parts),
            True,
            suggestions=suggestions if suggestions else None,
        )

    @handle_errors("handling list pinned")
    def _handle_list_pinned(
        self, user_id: str, entities: Optional[Dict[str, Any]] = None
    ) -> InteractionResponse:
        """Handle listing pinned entries."""
        if entities is None:
            entities = {}
        offset = entities.get("offset", 0)
        limit = entities.get("limit", 5)

        entries = list_pinned(user_id, limit=100)  # Get up to 100, paginate in handler

        if not entries:
            return InteractionResponse("No pinned entries found.", True)

        total = len(entries)
        paginated = entries[offset : offset + limit]
        has_more = offset + limit < total

        response_parts = [f"📌 Pinned entries ({total}):"]
        for entry in paginated:
            short_id = self._format_entry_id(entry)
            response_parts.append(f"• {entry.title or 'Untitled'} ({short_id})")

        if has_more:
            remaining = total - (offset + limit)
            response_parts.append(f"\n... and {remaining} more")

        suggestions = []
        if has_more:
            remaining = total - (offset + limit)
            suggestions.append(f"Show More ({min(limit, remaining)} more)")

        return InteractionResponse(
            "\n".join(response_parts),
            True,
            suggestions=suggestions if suggestions else None,
        )

    @handle_errors("handling list inbox")
    def _handle_list_inbox(
        self, user_id: str, entities: Optional[Dict[str, Any]] = None
    ) -> InteractionResponse:
        """Handle listing inbox entries."""
        if entities is None:
            entities = {}
        offset = entities.get("offset", 0)
        limit = entities.get("limit", 5)

        entries = list_inbox(user_id, limit=100)  # Get up to 100, paginate in handler

        if not entries:
            return InteractionResponse("Inbox is empty.", True)

        total = len(entries)
        paginated = entries[offset : offset + limit]
        has_more = offset + limit < total

        response_parts = [f"📥 Inbox ({total} entries):"]
        for entry in paginated:
            short_id = self._format_entry_id(entry)
            response_parts.append(f"• {entry.title or 'Untitled'} ({short_id})")

        if has_more:
            remaining = total - (offset + limit)
            response_parts.append(f"\n... and {remaining} more")

        suggestions = []
        if has_more:
            remaining = total - (offset + limit)
            suggestions.append(f"Show More ({min(limit, remaining)} more)")

        return InteractionResponse(
            "\n".join(response_parts),
            True,
            suggestions=suggestions if suggestions else None,
        )

    @handle_errors("handling list by tag")
    def _handle_list_by_tag(
        self, user_id: str, entities: Dict[str, Any]
    ) -> InteractionResponse:
        """Handle listing entries by tag."""
        tag = entities.get("tag")
        offset = entities.get("offset", 0)
        limit = entities.get("limit", 5)

        if not tag:
            return InteractionResponse("Which tag?", False)

        entries = list_by_tag(
            user_id, tag, limit=100
        )  # Get all matches, paginate in handler

        if not entries:
            return InteractionResponse(f"No entries found with tag '{tag}'.", True)

        total = len(entries)
        paginated = entries[offset : offset + limit]
        has_more = offset + limit < total

        response_parts = [f"🏷️ Tag '{tag}' ({total} entries):"]
        for entry in paginated:
            short_id = self._format_entry_id(entry)
            response_parts.append(f"• {entry.title or 'Untitled'} ({short_id})")

        if has_more:
            remaining = total - (offset + limit)
            response_parts.append(f"\n... and {remaining} more")

        suggestions = []
        if has_more:
            remaining = total - (offset + limit)
            suggestions.append(f"Show More ({min(limit, remaining)} more)")

        return InteractionResponse(
            "\n".join(response_parts),
            True,
            suggestions=suggestions if suggestions else None,
        )

    @handle_errors("handling list archived")
    def _handle_list_archived(
        self, user_id: str, entities: Optional[Dict[str, Any]] = None
    ) -> InteractionResponse:
        """Handle listing archived entries."""
        if entities is None:
            entities = {}
        offset = entities.get("offset", 0)
        limit = entities.get("limit", 5)

        entries = list_archived(
            user_id, limit=100
        )  # Get all matches, paginate in handler

        if not entries:
            return InteractionResponse("No archived entries found.", True)

        total = len(entries)
        paginated = entries[offset : offset + limit]
        has_more = offset + limit < total

        response_parts = [f"🗄️ Archived entries ({total}):"]
        for entry in paginated:
            short_id = self._format_entry_id(entry)
            kind_icon = {"note": "📄", "list": "📋", "journal": "📔"}.get(
                entry.kind, "📝"
            )
            response_parts.append(
                f"{kind_icon} {entry.title or 'Untitled'} ({short_id})"
            )

        if has_more:
            remaining = total - (offset + limit)
            response_parts.append(f"\n... and {remaining} more")

        suggestions = []
        if has_more:
            remaining = total - (offset + limit)
            suggestions.append(f"Show More ({min(limit, remaining)} more)")

        return InteractionResponse(
            "\n".join(response_parts),
            True,
            suggestions=suggestions if suggestions else None,
        )

    # Helper methods
    @handle_errors("formatting entry ID", default_return="unknown")
    def _format_entry_id(self, entry: Entry) -> str:
        """Format entry ID as short ID (e.g., n3f2a9c - no dash for easier mobile typing)."""
        short_id = format_short_id(entry.id, entry.kind)
        # Fallback if format_short_id returns None (shouldn't happen, but safety check)
        if short_id is None:
            # Fallback to simple format
            short_id_fragment = str(entry.id).replace("-", "")[:6]
            kind_prefix = entry.kind[0]  # 'n', 'l', or 'j'
            return f"{kind_prefix}{short_id_fragment}"
        return short_id

    @handle_errors("formatting entry response", default_return="Error formatting entry")
    def _format_entry_response(self, entry: Entry) -> str:
        """Formats a single entry for display."""
        short_id = self._format_entry_id(entry)
        kind_icon = {"note": "📄", "list": "📋", "journal": "📔"}.get(entry.kind, "📝")

        response_parts = [f"{kind_icon} **{entry.title or 'Untitled'}** ({short_id})"]
        if entry.group:
            response_parts.append(f"Group: {entry.group}")
        if entry.tags:
            response_parts.append(f"Tags: {', '.join(entry.tags)}")
        if entry.pinned:
            response_parts.append("📌 Pinned")
        if entry.archived:
            response_parts.append("🗄️ Archived")

        if entry.body:
            response_parts.append(f"\n{entry.body}")

        if entry.kind == "list" and entry.items:
            response_parts.append("\n**Items:**")
            for i, item in enumerate(entry.items):
                status = "✅" if item.done else "⬜"
                response_parts.append(f"{status} {i+1}. {item.text}")

        return "\n".join(response_parts)

    @handle_errors(
        "getting notebook help", default_return="Notebook commands help unavailable"
    )
    def get_help(self) -> str:
        """Get help text for notebook commands."""
        return "Manage your personal notes, lists, and journal entries. Use `!n` to create notes, `!l` for lists, `!recent` to see recent entries, and `!s` to search."

    @handle_errors("getting notebook examples", default_return=[])
    def get_examples(self) -> List[str]:
        """Get example commands for notebook."""
        return [
            "!n My quick thought",
            "!n Meeting Notes | Discuss project X, follow up on Y",
            "!recent",
            "!show n123abc",
            "!append My thought | More details here",
            "!tag My thought #idea #work",
            "!s project X",
            "!l new Groceries #home",
            "!l add Groceries Milk",
            "!l done Groceries 1",
            "!pinned",
            "!inbox",
        ]
