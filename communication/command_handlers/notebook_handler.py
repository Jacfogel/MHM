# communication/command_handlers/notebook_handler.py

"""
Notebook command handler.

This module handles all notebook-related interactions including creating,
viewing, updating, and searching notebook entries (notes, lists, journal).
"""

from collections.abc import Callable
from typing import Any

from core.logger import get_component_logger
from core.error_handling import handle_errors
from core.pagination import PageRequest, paginate_items
from core.time_utilities import now_timestamp_full
from core.tags import parse_tags_from_text

from communication.command_handlers.base_handler import InteractionHandler
from communication.command_handlers.shared_types import (
    InteractionResponse,
    PaginationAction,
    ParsedCommand,
)
from notebook.notebook_service import (
    add_entry_tags,
    add_item_to_list,
    get_entry,
    append_entry_body,
    archive_notebook_entry,
    create_journal_from_command,
    create_list_from_command,
    create_note_from_command,
    create_quick_note_from_command,
    delete_list_item,
    list_archived_entries,
    list_entries_by_group,
    list_entries_by_tag,
    list_inbox_entries,
    list_pinned_entries,
    list_recent_entries,
    pin_notebook_entry,
    remove_entry_tags,
    replace_entry_body,
    search_entries_for_display,
    set_entry_group,
    set_list_item_done,
)
from notebook.notebook_schemas import Entry
from notebook.notebook_validation import format_short_id

logger = get_component_logger("communication_manager")
handlers_logger = logger

DEFAULT_PAGE_SIZE = 5
MAX_PAGE_SIZE = 25
MAX_NOTEBOOK_RESULTS = 100


@handle_errors(
    "building notebook page request",
    default_return=PageRequest(limit=DEFAULT_PAGE_SIZE, offset=0),
    user_friendly=False,
)
def _page_request(entities: dict[str, Any]) -> PageRequest:
    """Build a notebook page request from command entities."""
    return PageRequest.from_values(
        limit=entities.get("limit", DEFAULT_PAGE_SIZE),
        offset=entities.get("offset", 0),
        default_limit=DEFAULT_PAGE_SIZE,
        max_limit=MAX_PAGE_SIZE,
    )


@handle_errors(
    "building notebook pagination metadata",
    default_return={"pagination_actions": []},
    user_friendly=False,
)
def _pagination_action_rich_data(
    action: str,
    params: dict[str, Any],
    page: Any,
) -> dict[str, Any]:
    """Return channel-neutral metadata for rendering a next-page action."""
    action_params = {
        key: value for key, value in params.items() if key not in {"offset", "limit"}
    }
    return {
        "pagination_actions": [
            PaginationAction(
                domain="notebook",
                action=action,
                params=action_params,
                limit=page.limit,
                offset=page.offset,
                next_offset=page.next_offset or page.offset + page.limit,
                remaining_count=page.remaining_count,
            )
        ]
    }


# not_duplicate: notebook_empty_result_messages
@handle_errors(
    "formatting empty notebook search message",
    default_return=(
        "No entries found. Try !recent, !inbox, or !archived for archived notes."
    ),
    user_friendly=False,
)
def _format_no_search_hits_message(query: str) -> str:
    """Build the Discord/user message when search has no matches.

    Explains substring search, archived exclusion, and next-step commands.
    """
    lines = [
        f"No entries found matching '{query}'.",
        "",
        "Search is case-insensitive and matches text inside titles, note bodies, and list items.",
        "Archived entries are not included - try !archived if something might be archived.",
        "",
        "Try one distinctive word from the title or body, a shorter keyword, or browse with !recent / !inbox.",
        "For tags or groups, use !t <tag> or !group <name> instead of search.",
    ]
    return "\n".join(lines)


# not_duplicate: notebook_empty_result_messages
@handle_errors(
    "formatting empty notebook group message",
    default_return="No entries in that group. Try !recent or check spelling.",
    user_friendly=False,
)
def _format_no_group_hits_message(group: str) -> str:
    """Build the user message when listing by group returns no entries."""
    lines = [
        f"No entries found in group '{group}'.",
        "",
        "Check the spelling. Assign a group with !group <entry_id> <groupname>.",
        "Browse recent entries with !recent to see what you have.",
    ]
    return "\n".join(lines)


# not_duplicate: notebook_empty_result_messages
@handle_errors(
    "formatting empty notebook tag message",
    default_return="No entries with that tag. Try !recent or !t with another tag.",
    user_friendly=False,
)
def _format_no_tag_hits_message(tag: str) -> str:
    """Build the user message when listing by tag returns no entries."""
    lines = [
        f"No entries found with tag '{tag}'.",
        "",
        "Tags are normalized to lowercase. Add tags with !tag <entry_id> <tags...>.",
        "Try !recent or another !t <tag> to explore.",
    ]
    return "\n".join(lines)


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
            return self._handle_list_pinned(user_id, entities)
        elif intent == "list_inbox_entries":
            return self._handle_list_inbox(user_id, entities)
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
        self, user_id: str, entities: dict[str, Any]
    ) -> InteractionResponse:
        """Handle note creation."""
        from communication.message_processing.conversation_flow_manager import (
            conversation_manager,
        )
        from communication.message_processing.flows.flow_constants import FLOW_NOTE_BODY

        title = entities.get("title")
        description = entities.get("description")
        tags = entities.get("tags", [])
        group = entities.get("group")

        # Check if user is in a note body flow (continuing from previous prompt)
        # This shouldn't happen here since flow is handled in conversation_manager,
        # but handle it just in case
        user_state = conversation_manager.user_states.get(user_id, {})
        if user_state.get("flow") == FLOW_NOTE_BODY and description:
            # Flow was already handled, but we have the body now
            flow_data = user_state.get("data", {})
            title = flow_data.get("title", title)
            tags = flow_data.get("tags", tags)
            group = flow_data.get("group", group)

        # If both title and body are missing, prompt for title
        if not title and not description:
            return InteractionResponse(
                "📝 What would you like to name this note? (You can add body text after)",
                False,
            )

        # If no description provided and we have a title, start flow to prompt for it
        if not description and title:
            # Parse tags from title first
            title, parsed_tags = parse_tags_from_text(title)
            tags.extend(parsed_tags)

            # Start flow to prompt for body
            conversation_manager.user_states[user_id] = {
                "flow": FLOW_NOTE_BODY,
                "state": 0,
                "data": {"title": title, "tags": tags, "group": group},
                "started_at": now_timestamp_full(),
            }
            conversation_manager._save_user_states()
            return InteractionResponse(
                f"📝 Note title: '{title}'\n\nWhat would you like to add as the body text? [Skip] [Cancel]",
                False,
                suggestions=["Skip", "Cancel"],
            )

        result = create_note_from_command(
            user_id,
            {
                "title": title,
                "description": description,
                "tags": tags,
                "group": group,
            },
        )
        entry = result.entry if result else None

        if entry:
            short_id = self._format_entry_id(entry)
            # Show title if available, otherwise body, otherwise "Untitled"
            display_name = entry.title or entry.description or "Untitled"
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
        self, user_id: str, entities: dict[str, Any]
    ) -> InteractionResponse:
        """Handle quick note creation - no body text required, automatically grouped as 'Quick Notes'."""

        result = create_quick_note_from_command(user_id, entities)
        entry = result.entry if result else None

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
        self, user_id: str, entities: dict[str, Any]
    ) -> InteractionResponse:
        """Handle list creation."""
        from communication.message_processing.conversation_flow_manager import (
            conversation_manager,
        )
        from communication.message_processing.flows.flow_constants import FLOW_LIST_ITEMS

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
                "started_at": now_timestamp_full(),
            }
            conversation_manager._save_user_states()
            return InteractionResponse(
                f"📋 List: '{title}'\n\nAdd list items (separated by commas, semicolons, or new lines). Type `!end`, `/end`, or 'end' to finish.",
                False,
                suggestions=["End List", "Cancel"],
            )

        result = create_list_from_command(
            user_id,
            {"title": title, "tags": tags, "group": group, "items": items},
        )
        entry = result.entry if result else None

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
        self, user_id: str, entities: dict[str, Any]
    ) -> InteractionResponse:
        """Handle journal entry creation."""
        result = create_journal_from_command(user_id, entities)
        entry = result.entry if result else None

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
        self, user_id: str, entities: dict[str, Any], notes_only: bool = False
    ) -> InteractionResponse:
        """Handle listing recent entries."""
        page_request = _page_request(entities)

        result = list_recent_entries(
            user_id, notes_only=notes_only, limit=MAX_NOTEBOOK_RESULTS
        )
        entries = result.entries

        if not entries:
            return InteractionResponse(
                (
                    "No recent entries found."
                    if not notes_only
                    else "No recent notes found."
                ),
                True,
            )

        page = paginate_items(entries, page_request)

        response_parts = [
            f"📝 Recent {'notes' if notes_only else 'entries'} ({len(entries)}):"
        ]
        for entry in page.items:
            short_id = self._format_entry_id(entry)
            title = entry.title or "Untitled"
            kind_icon = {"note": "📄", "list": "📋", "journal_entry": "📔"}.get(
                entry.kind, "📝"
            )
            response_parts.append(f"{kind_icon} {title} ({short_id})")

        rich_data = None
        if page.has_more:
            remaining = page.remaining_count
            response_parts.append(f"\n... and {remaining} more")
            intent = "list_recent_notes" if notes_only else "list_recent_entries"
            rich_data = _pagination_action_rich_data(intent, entities, page)

        return InteractionResponse(
            "\n".join(response_parts),
            True,
            rich_data=rich_data,
        )

    @handle_errors("handling show entry")
    def _handle_show_entry(
        self, user_id: str, entities: dict[str, Any]
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
        self, user_id: str, entities: dict[str, Any]
    ) -> InteractionResponse:
        """Handle appending to entry body."""
        entry_ref = entities.get("entry_ref")
        text = entities.get("text")

        if not entry_ref:
            return InteractionResponse(
                "Which entry would you like to append to?", False
            )
        if not text:
            return InteractionResponse("What would you like to add?", False)

        result = append_entry_body(user_id, entry_ref, text)
        entry = result.entry if result else None

        if entry:
            short_id = self._format_entry_id(entry)
            return InteractionResponse(
                f"✅ Appended to '{entry.title or 'Untitled'}' ({short_id})", True
            )
        else:
            return InteractionResponse(
                "❌ Failed to append. Entry not found or invalid.", True
            )

    @handle_errors("handling set entry body")
    def _handle_set_entry_body(
        self, user_id: str, entities: dict[str, Any]
    ) -> InteractionResponse:
        """Handle setting entry body."""
        entry_ref = entities.get("entry_ref")
        text = entities.get("text")

        if not entry_ref:
            return InteractionResponse("Which entry would you like to edit?", False)
        if not text:
            return InteractionResponse("What should the new content be?", False)

        result = replace_entry_body(user_id, entry_ref, text)
        entry = result.entry if result else None

        if entry:
            short_id = self._format_entry_id(entry)
            return InteractionResponse(
                f"✅ Updated '{entry.title or 'Untitled'}' ({short_id})", True
            )
        else:
            return InteractionResponse(
                "❌ Failed to update. Entry not found or invalid.", True
            )

    @handle_errors("handling add tags")
    def _handle_add_tags(
        self, user_id: str, entities: dict[str, Any]
    ) -> InteractionResponse:
        """Handle adding tags to entry."""
        entry_ref = entities.get("entry_ref")
        tags = entities.get("tags", [])

        if not entry_ref:
            return InteractionResponse("Which entry would you like to tag?", False)
        if not tags:
            return InteractionResponse("Which tags would you like to add?", False)

        result = add_entry_tags(user_id, entry_ref, tags)
        entry = result.entry if result else None

        if entry:
            short_id = self._format_entry_id(entry)
            return InteractionResponse(
                f"✅ Tags added to '{entry.title or 'Untitled'}' ({short_id}): {', '.join(entry.tags)}",
                True,
            )
        else:
            return InteractionResponse("❌ Failed to add tags. Entry not found.", True)

    @handle_errors("handling remove tags")
    def _handle_remove_tags(
        self, user_id: str, entities: dict[str, Any]
    ) -> InteractionResponse:
        """Handle removing tags from entry."""
        entry_ref = entities.get("entry_ref")
        tags = entities.get("tags", [])

        if not entry_ref:
            return InteractionResponse("Which entry would you like to untag?", False)
        if not tags:
            return InteractionResponse("Which tags would you like to remove?", False)

        result = remove_entry_tags(user_id, entry_ref, tags)
        entry = result.entry if result else None

        if entry:
            short_id = self._format_entry_id(entry)
            return InteractionResponse(
                f"✅ Tags removed from '{entry.title or 'Untitled'}' ({short_id})", True
            )
        else:
            return InteractionResponse(
                "❌ Failed to remove tags. Entry not found.", True
            )

    @handle_errors("handling search entries")
    def _handle_search_entries(
        self, user_id: str, entities: dict[str, Any]
    ) -> InteractionResponse:
        """Handle searching entries."""
        query = entities.get("query")
        page_request = _page_request(entities)

        if not query:
            return InteractionResponse("What would you like to search for?", False)

        result = search_entries_for_display(user_id, query, limit=100)
        entries = result.entries

        if not entries:
            return InteractionResponse(_format_no_search_hits_message(query), True)

        page = paginate_items(entries, page_request)

        response_parts = [f"🔍 Found {page.total} entries:"]
        for entry in page.items:
            short_id = self._format_entry_id(entry)
            title = entry.title or "Untitled"
            response_parts.append(f"• {title} ({short_id})")

        if page.has_more:
            remaining = page.remaining_count
            response_parts.append(f"\n... and {remaining} more")

        rich_data = None
        if page.has_more:
            rich_data = _pagination_action_rich_data("search_entries", entities, page)

        return InteractionResponse(
            "\n".join(response_parts),
            True,
            rich_data=rich_data,
        )

    @handle_errors(
        "applying notebook entry change",
        default_return=InteractionResponse(
            "Something went wrong with that notebook entry. Please try again.",
            True,
        ),
    )
    def _apply_entry_ref_mutation(
        self,
        user_id: str,
        entities: dict[str, Any],
        flag: bool,
        *,
        missing_ref_message: str,
        mutator: Callable[[str, Any, bool], Any],
        active_label: str,
        inactive_label: str,
        failure_message: str,
    ) -> InteractionResponse:
        """Pin/unpin or archive/unarchive by entry_ref; shared helper for pin/archive handlers."""
        entry_ref = entities.get("entry_ref")
        if not entry_ref:
            return InteractionResponse(missing_ref_message, False)

        result = mutator(user_id, entry_ref, flag)
        entry = getattr(result, "entry", result)
        if entry:
            action = active_label if flag else inactive_label
            short_id = self._format_entry_id(entry)
            return InteractionResponse(
                f"✅ {action.capitalize()} '{entry.title or 'Untitled'}' ({short_id})",
                True,
            )
        return InteractionResponse(failure_message, True)

    # not_duplicate: notebook_pin_archive_entry_wrappers
    @handle_errors(
        "handling pin entry",
        default_return=InteractionResponse(
            "Something went wrong pinning that notebook entry. Please try again.",
            True,
        ),
    )
    def _handle_pin_entry(
        self, user_id: str, entities: dict[str, Any], pinned: bool
    ) -> InteractionResponse:
        """Handle pinning/unpinning entry."""
        return self._apply_entry_ref_mutation(
            user_id,
            entities,
            pinned,
            missing_ref_message="Which entry would you like to pin/unpin?",
            mutator=pin_notebook_entry,
            active_label="pinned",
            inactive_label="unpinned",
            failure_message="❌ Failed to pin/unpin. Entry not found.",
        )

    # not_duplicate: notebook_pin_archive_entry_wrappers
    @handle_errors(
        "handling archive entry",
        default_return=InteractionResponse(
            "Something went wrong archiving that notebook entry. Please try again.",
            True,
        ),
    )
    def _handle_archive_entry(
        self, user_id: str, entities: dict[str, Any], archived: bool
    ) -> InteractionResponse:
        """Handle archiving/unarchiving entry."""
        return self._apply_entry_ref_mutation(
            user_id,
            entities,
            archived,
            missing_ref_message=(
                "Which entry would you like to archive/unarchive?"
            ),
            mutator=archive_notebook_entry,
            active_label="archived",
            inactive_label="unarchived",
            failure_message="❌ Failed to archive/unarchive. Entry not found.",
        )

    # List item handlers
    @handle_errors("handling add list item")
    def _handle_add_list_item(
        self, user_id: str, entities: dict[str, Any]
    ) -> InteractionResponse:
        """Handle adding item to list."""
        entry_ref = entities.get("entry_ref")
        item_text = entities.get("item_text") or entities.get("text")

        if not entry_ref:
            return InteractionResponse("Which list would you like to add to?", False)
        if not item_text:
            return InteractionResponse("What item would you like to add?", False)

        result = add_item_to_list(user_id, entry_ref, item_text)
        entry = result.entry if result else None

        if entry:
            short_id = self._format_entry_id(entry)
            return InteractionResponse(
                f"✅ Added item to '{entry.title}' ({short_id})", True
            )
        else:
            return InteractionResponse(
                "❌ Failed to add item. List not found or invalid.", True
            )

    @handle_errors("handling toggle list item done")
    def _handle_toggle_list_item_done(
        self, user_id: str, entities: dict[str, Any]
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

        result = set_list_item_done(user_id, entry_ref, item_index, done)
        entry = result.entry if result else None

        if entry:
            short_id = self._format_entry_id(entry)
            action = "marked done" if done else "marked undone"
            return InteractionResponse(
                f"✅ Item {item_index + 1} {action} in '{entry.title}' ({short_id})",
                True,
            )
        else:
            return InteractionResponse(
                "❌ Failed to toggle item. List not found or invalid.", True
            )

    @handle_errors("handling remove list item")
    def _handle_remove_list_item(
        self, user_id: str, entities: dict[str, Any]
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

        result = delete_list_item(user_id, entry_ref, item_index)
        entry = result.entry if result else None

        if entry:
            short_id = self._format_entry_id(entry)
            return InteractionResponse(
                f"✅ Removed item {item_index + 1} from '{entry.title}' ({short_id})",
                True,
            )
        else:
            return InteractionResponse(
                "❌ Failed to remove item. List not found or invalid.", True
            )

    # Organization handlers
    @handle_errors("handling set group")
    def _handle_set_group(
        self, user_id: str, entities: dict[str, Any]
    ) -> InteractionResponse:
        """Handle setting entry group."""
        entry_ref = entities.get("entry_ref")
        group = entities.get("group")

        if not entry_ref:
            return InteractionResponse("Which entry?", False)
        if not group:
            return InteractionResponse("What group name?", False)

        result = set_entry_group(user_id, entry_ref, group)
        entry = result.entry if result else None

        if entry:
            short_id = self._format_entry_id(entry)
            return InteractionResponse(
                f"✅ Set group '{group}' for '{entry.title or 'Untitled'}' ({short_id})",
                True,
            )
        else:
            return InteractionResponse(
                "❌ Failed to set group. Entry not found.", True
            )

    @handle_errors(
        "building paginated list response",
        default_return=InteractionResponse("Error building list.", True),
    )
    def _build_paginated_list_response(
        self,
        entries: list[Entry],
        header: str,
        offset: int,
        limit: int,
        *,
        show_more_intent: str | None = None,
        show_more_entities: dict[str, Any] | None = None,
    ) -> InteractionResponse:
        """Build a paginated list response for group/tag-style list handlers."""
        page = paginate_items(entries, PageRequest(limit=limit, offset=offset))

        response_parts = [header]
        for entry in page.items:
            short_id = self._format_entry_id(entry)
            response_parts.append(f"• {entry.title or 'Untitled'} ({short_id})")

        if page.has_more:
            remaining = page.remaining_count
            response_parts.append(f"\n... and {remaining} more")

        rich_data = None
        if page.has_more:
            remaining = page.remaining_count
            if show_more_intent is None:
                if "Group '" in header:
                    group = header.split("Group '", 1)[1].split("'", 1)[0]
                    show_more_intent = "list_entries_by_group"
                    show_more_entities = {"group": group}
                elif "Tag '" in header:
                    tag = header.split("Tag '", 1)[1].split("'", 1)[0]
                    show_more_intent = "list_entries_by_tag"
                    show_more_entities = {"tag": tag}
            if show_more_intent is not None:
                rich_data = _pagination_action_rich_data(
                    show_more_intent, show_more_entities or {}, page
                )

        return InteractionResponse(
            "\n".join(response_parts),
            True,
            rich_data=rich_data,
        )

    # not_duplicate: handle_list_by_group_tag
    @handle_errors("handling list by group")
    def _handle_list_by_group(
        self, user_id: str, entities: dict[str, Any]
    ) -> InteractionResponse:
        """Handle listing entries by group."""
        group = entities.get("group")
        page_request = _page_request(entities)

        if not group:
            return InteractionResponse("Which group?", False)

        result = list_entries_by_group(user_id, group, limit=100)
        entries = result.entries

        if not entries:
            return InteractionResponse(_format_no_group_hits_message(group), True)

        return self._build_paginated_list_response(
            entries,
            f"📁 Group '{group}' ({len(entries)} entries):",
            page_request.offset,
            page_request.limit,
        )

    @handle_errors("handling list pinned")
    def _handle_list_pinned(
        self, user_id: str, entities: dict[str, Any] | None = None
    ) -> InteractionResponse:
        """Handle listing pinned entries."""
        if entities is None:
            entities = {}
        page_request = _page_request(entities)

        result = list_pinned_entries(user_id, limit=100)
        entries = result.entries

        if not entries:
            return InteractionResponse("No pinned entries found.", True)

        page = paginate_items(entries, page_request)

        response_parts = [f"📌 Pinned entries ({page.total}):"]
        for entry in page.items:
            short_id = self._format_entry_id(entry)
            response_parts.append(f"• {entry.title or 'Untitled'} ({short_id})")

        if page.has_more:
            remaining = page.remaining_count
            response_parts.append(f"\n... and {remaining} more")

        rich_data = None
        if page.has_more:
            rich_data = _pagination_action_rich_data(
                "list_pinned_entries", entities, page
            )

        return InteractionResponse(
            "\n".join(response_parts),
            True,
            rich_data=rich_data,
        )

    @handle_errors("handling list inbox")
    def _handle_list_inbox(
        self, user_id: str, entities: dict[str, Any] | None = None
    ) -> InteractionResponse:
        """Handle listing inbox entries."""
        if entities is None:
            entities = {}
        page_request = _page_request(entities)

        result = list_inbox_entries(user_id, limit=100)
        entries = result.entries

        if not entries:
            return InteractionResponse("Inbox is empty.", True)

        page = paginate_items(entries, page_request)

        response_parts = [f"📥 Inbox ({page.total} entries):"]
        for entry in page.items:
            short_id = self._format_entry_id(entry)
            response_parts.append(f"• {entry.title or 'Untitled'} ({short_id})")

        if page.has_more:
            remaining = page.remaining_count
            response_parts.append(f"\n... and {remaining} more")

        rich_data = None
        if page.has_more:
            rich_data = _pagination_action_rich_data(
                "list_inbox_entries", entities, page
            )

        return InteractionResponse(
            "\n".join(response_parts),
            True,
            rich_data=rich_data,
        )

    # not_duplicate: handle_list_by_group_tag
    @handle_errors("handling list by tag")
    def _handle_list_by_tag(
        self, user_id: str, entities: dict[str, Any]
    ) -> InteractionResponse:
        """Handle listing entries by tag."""
        tag = entities.get("tag")
        page_request = _page_request(entities)

        if not tag:
            return InteractionResponse("Which tag?", False)

        result = list_entries_by_tag(user_id, tag, limit=100)
        entries = result.entries

        if not entries:
            return InteractionResponse(_format_no_tag_hits_message(tag), True)

        return self._build_paginated_list_response(
            entries,
            f"🏷️ Tag '{tag}' ({len(entries)} entries):",
            page_request.offset,
            page_request.limit,
        )

    @handle_errors("handling list archived")
    def _handle_list_archived(
        self, user_id: str, entities: dict[str, Any] | None = None
    ) -> InteractionResponse:
        """Handle listing archived entries."""
        if entities is None:
            entities = {}
        page_request = _page_request(entities)

        result = list_archived_entries(user_id, limit=100)
        entries = result.entries

        if not entries:
            return InteractionResponse("No archived entries found.", True)

        page = paginate_items(entries, page_request)

        response_parts = [f"🗄️ Archived entries ({page.total}):"]
        for entry in page.items:
            short_id = self._format_entry_id(entry)
            kind_icon = {"note": "📄", "list": "📋", "journal_entry": "📔"}.get(
                entry.kind, "📝"
            )
            response_parts.append(
                f"{kind_icon} {entry.title or 'Untitled'} ({short_id})"
            )

        if page.has_more:
            remaining = page.remaining_count
            response_parts.append(f"\n... and {remaining} more")

        rich_data = None
        if page.has_more:
            rich_data = _pagination_action_rich_data(
                "list_archived_entries", entities, page
            )

        return InteractionResponse(
            "\n".join(response_parts),
            True,
            rich_data=rich_data,
        )

    # Helper methods
    @handle_errors("formatting entry ID", default_return="unknown")
    def _format_entry_id(self, entry: Entry) -> str:
        """Format entry ID as short ID (e.g., n3f2a9c - no dash for easier mobile typing)."""
        if getattr(entry, "short_id", None):
            return str(entry.short_id).strip()
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
        kind_icon = {"note": "📄", "list": "📋", "journal_entry": "📔"}.get(
            entry.kind, "📝"
        )

        response_parts = [f"{kind_icon} **{entry.title or 'Untitled'}** ({short_id})"]
        if entry.group:
            response_parts.append(f"Group: {entry.group}")
        if entry.tags:
            response_parts.append(f"Tags: {', '.join(entry.tags)}")
        if entry.pinned:
            response_parts.append("📌 Pinned")
        if entry.status == "archived":
            response_parts.append("🗄️ Archived")

        if entry.description:
            response_parts.append(f"\n{entry.description}")

        if entry.kind == "list" and entry.items:
            response_parts.append("\n**Items:**")
            for i, item in enumerate(entry.items):
                status = "✅" if item.done else "⬜"
                response_parts.append(f"{status} {i + 1}. {item.text}")

        return "\n".join(response_parts)

    @handle_errors(
        "getting notebook help", default_return="Notebook commands help unavailable"
    )
    def get_help(self) -> str:
        """Get help text for notebook commands."""
        return "Manage your personal notes, lists, and journal entries. Use `!n` to create notes, `!l` for lists, `!recent` to see recent entries, and `!s` to search."

    @handle_errors("getting notebook examples", default_return=[])
    def get_examples(self) -> list[str]:
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
