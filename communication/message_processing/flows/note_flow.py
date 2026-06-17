# communication/message_processing/flows/note_flow.py

"""Note and list conversation flow mixin."""

from datetime import timedelta

from core.error_handling import handle_errors
from core.logger import get_component_logger
from core.time_utilities import now_datetime_full, parse_timestamp_full
from storage.user_data_v2_base import generate_short_id

from communication.message_processing.flows.flow_state import FlowStateMixin

logger = get_component_logger("communication_manager")


class NoteFlowMixin(FlowStateMixin):
    @handle_errors(
        "handling note body flow",
        default_return=(
            "I'm having trouble with the note flow. Please try again.",
            True,
        ),
    )
    def _handle_note_body_flow(
        self, user_id: str, user_state: dict, message_text: str
    ) -> tuple[str, bool]:
        """Handle continuation of note body flow."""
        message_lower = message_text.lower().strip()

        # Check for timeout first (10 minutes)
        started_at_str = user_state.get("started_at")
        if started_at_str:
            # started_at is internal persisted state (string timestamp).
            # Parse strictly using canonical helper.
            started_at = parse_timestamp_full(started_at_str)
            if started_at is not None and (
                now_datetime_full() - started_at
            ) > timedelta(minutes=10):
                # Flow expired
                self._clear_flow_state(user_id, mark_completion=True)
                return (
                    "⏱️ Note flow expired. Please start over with `!n <title>`",
                    True,
                )

        # Check for skip/cancel commands
        skip_keywords = ["skip", "!skip", "/skip"]
        cancel_keywords = ["cancel", "!cancel", "/cancel"]

        # Handle cancel - abort note creation entirely
        if any(
            message_lower == keyword or message_lower.startswith(keyword + " ")
            for keyword in cancel_keywords
        ):
            # User wants to cancel - abort note creation
            flow_data = user_state.get("data", {})
            title = flow_data.get("title", "")

            # Clear flow state
            self._clear_flow_state(user_id, mark_completion=True)

            return (f"❌ Note creation cancelled. '{title}' was not saved.", True)

        # Handle skip - create note without body
        if any(
            message_lower == keyword or message_lower.startswith(keyword + " ")
            for keyword in skip_keywords
        ):
            # User wants to skip body - create note with just title
            flow_data = user_state.get("data", {})
            title = flow_data.get("title", "")
            tags = flow_data.get("tags", [])
            group = flow_data.get("group")

            # Clear flow state
            self._clear_flow_state(user_id, mark_completion=True)

            # Create note without body
            from notebook.notebook_data_manager import create_note

            entry = create_note(
                user_id, title=title, description=None, tags=tags, group=group
            )

            if entry:
                display_short = entry.short_id or generate_short_id(
                    str(entry.id), str(entry.kind), length=6
                )
                return (
                    f"✅ Note created: '{title}' ({display_short})",
                    True,
                )
            else:
                return ("❌ Failed to create note. Please try again.", True)

        # Check if message is clearly unrelated to note body flow (commands or unrelated content)
        unrelated_patterns = [
            r"^/(task|t|nt|ntask|newt|newtask|ct|ctask|createtask|createt|l|list|newl|newlist|cl|createlist|createl)",
            r"^!(task|t|nt|ntask|newt|newtask|ct|ctask|createtask|createt|l|list|newl|newlist|cl|createlist|createl)",
            r"^(create|add|new|show|list|complete|delete|update).*(task|list)",
            r"^(hi|hello|hey|thanks|thank you|bye|goodbye)",
        ]
        import re

        if any(re.match(pattern, message_lower) for pattern in unrelated_patterns):
            # Message is clearly unrelated - clear flow and let it be processed normally
            logger.info(
                f"User {user_id} in note body flow sent unrelated message '{message_text}', clearing flow"
            )
            self._clear_flow_state(user_id, mark_completion=True)
            return ("", True)  # Empty response to let command be processed normally

        # User's message is the body - create the note directly
        flow_data = user_state.get("data", {})
        title = flow_data.get("title", "")
        tags = flow_data.get("tags", [])
        group = flow_data.get("group")
        body = message_text

        # Clear flow state
        self._clear_flow_state(user_id, mark_completion=True)

        # Create note using notebook manager
        from notebook.notebook_data_manager import create_note
        from core.tags import parse_tags_from_text

        # Parse tags from body if present
        if body:
            body, parsed_tags = parse_tags_from_text(body)
            tags.extend(parsed_tags)

        entry = create_note(
            user_id, title=title, description=body, tags=tags, group=group
        )

        if entry:
            display_short = entry.short_id or generate_short_id(
                str(entry.id), str(entry.kind), length=6
            )
            response = f"✅ Note created: '{title}' ({display_short})"
            if entry.tags:
                response += f"\nTags: {', '.join(entry.tags)}"
            return (response, True)
        else:
            return ("❌ Failed to create note. Please try again.", True)
    @handle_errors(
        "handling list items flow",
        default_return=(
            "I'm having trouble with the list flow. Please try again.",
            True,
        ),
    )
    def _handle_list_items_flow(
        self, user_id: str, user_state: dict, message_text: str
    ) -> tuple[str, bool]:
        """Handle continuation of list items flow."""
        message_lower = message_text.lower().strip()

        # Check for end commands
        end_keywords = [
            "end",
            "!end",
            "/end",
            "endlist",
            "!endlist",
            "/endlist",
            "endl",
            "!endl",
            "/endl",
        ]
        if any(
            message_lower == keyword or message_lower.startswith(keyword + " ")
            for keyword in end_keywords
        ):
            # User wants to end list creation
            flow_data = user_state.get("data", {})
            title = flow_data.get("title", "")
            items = flow_data.get("items", [])
            tags = flow_data.get("tags", [])
            group = flow_data.get("group")

            # Clear flow state
            self._clear_flow_state(user_id, mark_completion=True)

            # Create list with collected items
            from notebook.notebook_data_manager import create_list

            # items from flow_data are already strings, create_list expects List[str]
            item_strings = [item.strip() for item in items if item.strip()]
            # Ensure at least one item (create_list will add default if empty, but better to be explicit)
            if not item_strings:
                # User ended flow without adding items - create list with placeholder
                item_strings = ["New item"]
            entry = create_list(
                user_id, title=title, tags=tags, group=group, items=item_strings
            )

            if entry:
                display_short = entry.short_id or generate_short_id(
                    str(entry.id), str(entry.kind), length=6
                )
                return (
                    f"✅ List created: '{title}' ({display_short}) with {len(item_strings)} items",
                    True,
                )
            else:
                return ("❌ Failed to create list. Please try again.", True)

        # Check for timeout first (10 minutes)
        started_at_str = user_state.get("started_at")
        if started_at_str:
            # started_at is internal persisted state (string timestamp).
            # Parse strictly using canonical helper.
            started_at = parse_timestamp_full(started_at_str)
            if started_at is not None and (
                now_datetime_full() - started_at
            ) > timedelta(minutes=10):
                # Flow expired
                self._clear_flow_state(user_id, mark_completion=True)
                return (
                    "⏱️ List flow expired. Please start over with `!l <title>`",
                    True,
                )

        # Check if message is clearly unrelated to list items flow (commands or unrelated content)
        unrelated_patterns = [
            r"^/(n|note|nn|newn|newnote|task|t|nt|ntask|newt|newtask|ct|ctask|createtask|createt)",
            r"^!(n|note|nn|newn|newnote|task|t|nt|ntask|newt|newtask|ct|ctask|createtask|createt)",
            r"^(create|add|new|show|list|complete|delete|update).*(task|note)",
            r"^(hi|hello|hey|thanks|thank you|bye|goodbye)",
        ]
        import re

        if any(re.match(pattern, message_lower) for pattern in unrelated_patterns):
            # Message is clearly unrelated - clear flow and let it be processed normally
            logger.info(
                f"User {user_id} in list items flow sent unrelated message '{message_text}', clearing flow"
            )
            self._clear_flow_state(user_id, mark_completion=True)
            return ("", True)  # Empty response to let command be processed normally

        # Parse items from message (comma, semicolon, or newline separated)
        items_text = message_text
        items = []
        # Try comma first
        if "," in items_text:
            items = [item.strip() for item in items_text.split(",")]
        # Then semicolon
        elif ";" in items_text:
            items = [item.strip() for item in items_text.split(";")]
        # Then newline
        elif "\n" in items_text:
            items = [item.strip() for item in items_text.split("\n")]
        else:
            # Single item
            items = [items_text.strip()]

        # Add to flow data
        flow_data = user_state.get("data", {})
        existing_items = flow_data.get("items", [])
        existing_items.extend([item for item in items if item])
        flow_data["items"] = existing_items
        user_state["data"] = flow_data
        self.user_states[user_id] = user_state
        self._save_user_states()

        item_count = len(existing_items)
        return (
            f"📋 Added {len(items)} item(s). Total: {item_count} items.\n\nAdd more items, or type `!end`, `/end`, or 'end' to finish the list.",
            False,
        )
