# communication/message_processing/flows/note_flow.py

"""Note, journal, and list conversation flow mixin."""

from typing import Any

from core.error_handling import handle_errors
from core.ids import display_short_id
from core.logger import get_component_logger
from core.time_utilities import now_timestamp_full

from communication.message_processing.flows.flow_constants import (
    FLOW_ENTRY_EDIT,
    FLOW_JOURNAL_BODY,
    FLOW_LIST_ITEMS,
    FLOW_NOTE_BODY,
)

from communication.message_processing.flows.flow_command_helpers import (
    ENTRY_EDIT_CANCEL_KEYWORDS,
    ENTRY_EDIT_CANCELLED_MESSAGE,
    JOURNAL_FLOW_UNDO_CREATION_KEYWORDS,
    JOURNAL_NOT_SAVED_TEMPLATE,
    JOURNAL_SAVED_TITLE_ONLY_TEMPLATE,
    JOURNAL_SAVED_WITH_BODY_TEMPLATE,
    LIST_FLOW_UNDO_CREATION_KEYWORDS,
    LIST_NOT_SAVED_TEMPLATE,
    LIST_SAVED_TEMPLATE,
    LIST_STEP_BACK_REMOVED_TEMPLATE,
    NOTE_FLOW_UNDO_CREATION_KEYWORDS,
    NOTE_NOT_SAVED_TEMPLATE,
    NOTE_SAVED_TITLE_ONLY_TEMPLATE,
    NOTE_SAVED_WITH_BODY_TEMPLATE,
    is_journal_flow_step_back_message,
    is_note_flow_step_back_message,
    is_skip_question_message,
    is_unrelated_entry_edit_message,
    is_unrelated_journal_body_message,
    is_unrelated_list_items_message,
    is_unrelated_note_body_message,
    message_matches_keyword,
)
from communication.message_processing.flows.flow_control_mixin import FlowControlMixin

logger = get_component_logger("communication_manager")


class NoteFlowMixin(FlowControlMixin):
    # error_handling_exclude: pure short-id formatting; no I/O
    def _entry_short_id(self, entry) -> str:
        """Format a notebook entry short id for user-facing messages."""
        return display_short_id(
            short_id=getattr(entry, "short_id", None),
            record_id=entry.id,
            kind=str(entry.kind),
        )

    # error_handling_exclude: called from decorated flow handlers
    def _finalize_note_without_body(
        self, user_id: str, user_state: dict
    ) -> tuple[str, bool]:
        """Save note with title/tags only (Skip / timeout on body step)."""
        flow_data = user_state.get("data", {})
        title = flow_data.get("title", "")
        tags = flow_data.get("tags", [])
        group = flow_data.get("group")
        self._clear_flow_state(user_id, mark_completion=True)

        from notebook.notebook_data_manager import create_note

        entry = create_note(
            user_id, title=title, description=None, tags=tags, group=group
        )
        if entry:
            short_id = self._entry_short_id(entry)
            return (NOTE_SAVED_TITLE_ONLY_TEMPLATE.format(title=title, short_id=short_id), True)
        return ("Failed to save note. Please try again.", True)

    # error_handling_exclude: called from decorated flow handlers
    def _finalize_journal_without_body(
        self, user_id: str, user_state: dict
    ) -> tuple[str, bool]:
        """Save journal entry with title/tags only (Skip / timeout on body step)."""
        flow_data = user_state.get("data", {})
        title = flow_data.get("title", "")
        tags = flow_data.get("tags", [])
        group = flow_data.get("group")
        self._clear_flow_state(user_id, mark_completion=True)

        from notebook.notebook_data_manager import create_journal

        entry = create_journal(
            user_id, title=title, description=None, tags=tags, group=group
        )
        if entry:
            short_id = self._entry_short_id(entry)
            return (
                JOURNAL_SAVED_TITLE_ONLY_TEMPLATE.format(title=title, short_id=short_id),
                True,
            )
        return ("Failed to save journal entry. Please try again.", True)

    # error_handling_exclude: called from decorated flow handlers
    def _finalize_list_from_state(
        self, user_id: str, user_state: dict
    ) -> tuple[str, bool]:
        """Persist collected list items and end the list flow."""
        flow_data = user_state.get("data", {})
        title = flow_data.get("title", "")
        items = flow_data.get("items", [])
        tags = flow_data.get("tags", [])
        group = flow_data.get("group")
        self._clear_flow_state(user_id, mark_completion=True)

        from notebook.notebook_data_manager import create_list

        item_strings = [item.strip() for item in items if item.strip()]
        if not item_strings:
            item_strings = ["New item"]
        entry = create_list(
            user_id, title=title, tags=tags, group=group, items=item_strings
        )
        if entry:
            short_id = self._entry_short_id(entry)
            return (
                LIST_SAVED_TEMPLATE.format(
                    title=title, short_id=short_id, count=len(item_strings)
                ),
                True,
            )
        return ("Failed to save list. Please try again.", True)

    # error_handling_exclude: called from decorated flow handlers
    def _cancel_note_creation(self, user_id: str, user_state: dict) -> tuple[str, bool]:
        """Abandon note creation without saving."""
        title = user_state.get("data", {}).get("title", "")
        self._clear_flow_state(user_id, mark_completion=True)
        return (NOTE_NOT_SAVED_TEMPLATE.format(title=title), True)

    # error_handling_exclude: called from decorated flow handlers
    def _cancel_journal_creation(self, user_id: str, user_state: dict) -> tuple[str, bool]:
        """Abandon journal entry creation without saving."""
        title = user_state.get("data", {}).get("title", "")
        self._clear_flow_state(user_id, mark_completion=True)
        return (JOURNAL_NOT_SAVED_TEMPLATE.format(title=title), True)

    # error_handling_exclude: called from decorated flow handlers
    def _cancel_list_creation(self, user_id: str, user_state: dict) -> tuple[str, bool]:
        """Abandon list creation without saving."""
        title = user_state.get("data", {}).get("title", "")
        self._clear_flow_state(user_id, mark_completion=True)
        return (LIST_NOT_SAVED_TEMPLATE.format(title=title), True)

    # error_handling_exclude: called from decorated flow handlers
    def _cancel_entry_edit(self, user_id: str, user_state: dict) -> tuple[str, bool]:
        """Abandon edit session without writing (entry already exists)."""
        self._clear_flow_state(user_id, mark_completion=True)
        return (ENTRY_EDIT_CANCELLED_MESSAGE, True)

    # error_handling_exclude: called from decorated flow handlers
    def _note_body_step_back(self, user_id: str, user_state: dict) -> tuple[str, bool]:
        """Body step is the only interactive step — back saves title only."""
        return self._finalize_note_without_body(user_id, user_state)

    # error_handling_exclude: called from decorated flow handlers
    def _journal_body_step_back(self, user_id: str, user_state: dict) -> tuple[str, bool]:
        """Body step is the only interactive step — back saves title only."""
        return self._finalize_journal_without_body(user_id, user_state)

    # error_handling_exclude: called from decorated flow handlers
    def _list_items_step_back(self, user_id: str, user_state: dict) -> tuple[str, bool]:
        """Remove the last item batch and prompt for more or end list."""
        flow_data = user_state.get("data", {})
        batches: list[list[str]] = list(flow_data.get("item_batches", []))
        if not batches:
            items = flow_data.get("items", [])
            if items:
                batches = [list(items)]
            else:
                return self._cancel_list_creation(user_id, user_state)

        removed_batch = batches.pop()
        removed_count = len(removed_batch)
        flat_items = [item for batch in batches for item in batch]
        flow_data["item_batches"] = batches
        flow_data["items"] = flat_items
        user_state["data"] = flow_data
        self.user_states[user_id] = user_state
        self._save_user_states()

        if not flat_items and not batches:
            return (
                f"Removed last entry ({removed_count} item(s)). No items yet.\n\n"
                "Add items, or type `!end` to finish the list.",
                False,
            )

        return (
            LIST_STEP_BACK_REMOVED_TEMPLATE.format(
                count=removed_count, remaining=len(flat_items)
            )
            + "\n\nAdd more items, or type `!end` to finish the list.",
            False,
        )

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

        control = self._try_flow_control_command(
            user_id,
            user_state,
            message_lower,
            self._build_flow_control_handlers(
                on_skip_all=lambda: self._finalize_note_without_body(user_id, user_state),
                on_skip_question=lambda: self._finalize_note_without_body(
                    user_id, user_state
                ),
                on_undo_creation=lambda: self._cancel_note_creation(user_id, user_state),
                on_step_back=lambda: self._note_body_step_back(user_id, user_state),
                is_unrelated=is_unrelated_note_body_message,
                on_timeout_unrelated=lambda: self._finalize_note_without_body(
                    user_id, user_state
                ),
                skip_question_checker=is_skip_question_message,
                undo_creation_checker=lambda msg: message_matches_keyword(
                    msg, NOTE_FLOW_UNDO_CREATION_KEYWORDS
                ),
                step_back_checker=is_note_flow_step_back_message,
            ),
            flow_label="note body flow",
        )
        if control is not None:
            return control

        flow_data = user_state.get("data", {})
        title = flow_data.get("title", "")
        tags = flow_data.get("tags", [])
        group = flow_data.get("group")
        body = message_text
        self._clear_flow_state(user_id, mark_completion=True)

        from notebook.notebook_data_manager import create_note
        from core.tags import parse_tags_from_text

        if body:
            body, parsed_tags = parse_tags_from_text(body)
            tags.extend(parsed_tags)

        entry = create_note(
            user_id, title=title, description=body, tags=tags, group=group
        )

        if entry:
            short_id = self._entry_short_id(entry)
            response = NOTE_SAVED_WITH_BODY_TEMPLATE.format(title=title, short_id=short_id)
            if entry.tags:
                response += f"\nTags: {', '.join(entry.tags)}"
            return (response, True)
        return ("Failed to save note. Please try again.", True)

    @handle_errors(
        "handling journal body flow",
        default_return=(
            "I'm having trouble with the journal flow. Please try again.",
            True,
        ),
    )
    def _handle_journal_body_flow(
        self, user_id: str, user_state: dict, message_text: str
    ) -> tuple[str, bool]:
        """Handle continuation of journal body flow."""
        message_lower = message_text.lower().strip()

        control = self._try_flow_control_command(
            user_id,
            user_state,
            message_lower,
            self._build_flow_control_handlers(
                on_skip_all=lambda: self._finalize_journal_without_body(
                    user_id, user_state
                ),
                on_skip_question=lambda: self._finalize_journal_without_body(
                    user_id, user_state
                ),
                on_undo_creation=lambda: self._cancel_journal_creation(user_id, user_state),
                on_step_back=lambda: self._journal_body_step_back(user_id, user_state),
                is_unrelated=is_unrelated_journal_body_message,
                on_timeout_unrelated=lambda: self._finalize_journal_without_body(
                    user_id, user_state
                ),
                skip_question_checker=is_skip_question_message,
                undo_creation_checker=lambda msg: message_matches_keyword(
                    msg, JOURNAL_FLOW_UNDO_CREATION_KEYWORDS
                ),
                step_back_checker=is_journal_flow_step_back_message,
            ),
            flow_label="journal body flow",
        )
        if control is not None:
            return control

        flow_data = user_state.get("data", {})
        title = flow_data.get("title", "")
        tags = flow_data.get("tags", [])
        group = flow_data.get("group")
        body = message_text
        self._clear_flow_state(user_id, mark_completion=True)

        from notebook.notebook_data_manager import create_journal
        from core.tags import parse_tags_from_text

        if body:
            body, parsed_tags = parse_tags_from_text(body)
            tags.extend(parsed_tags)

        entry = create_journal(
            user_id, title=title, description=body, tags=tags, group=group
        )

        if entry:
            short_id = self._entry_short_id(entry)
            response = JOURNAL_SAVED_WITH_BODY_TEMPLATE.format(
                title=title, short_id=short_id
            )
            if entry.tags:
                response += f"\nTags: {', '.join(entry.tags)}"
            return (response, True)
        return ("Failed to save journal entry. Please try again.", True)

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

        control = self._try_flow_control_command(
            user_id,
            user_state,
            message_lower,
            self._build_flow_control_handlers(
                on_skip_all=lambda: self._finalize_list_from_state(user_id, user_state),
                on_finish=lambda: self._finalize_list_from_state(user_id, user_state),
                on_undo_creation=lambda: self._cancel_list_creation(user_id, user_state),
                on_step_back=lambda: self._list_items_step_back(user_id, user_state),
                is_unrelated=is_unrelated_list_items_message,
                on_timeout_unrelated=lambda: self._finalize_list_from_state(
                    user_id, user_state
                ),
                undo_creation_checker=lambda msg: message_matches_keyword(
                    msg, LIST_FLOW_UNDO_CREATION_KEYWORDS
                ),
            ),
            flow_label="list items flow",
        )
        if control is not None:
            return control

        items_text = message_text
        items = []
        if "," in items_text:
            items = [item.strip() for item in items_text.split(",")]
        elif ";" in items_text:
            items = [item.strip() for item in items_text.split(";")]
        elif "\n" in items_text:
            items = [item.strip() for item in items_text.split("\n")]
        else:
            items = [items_text.strip()]

        flow_data = user_state.get("data", {})
        batches: list[list[str]] = list(flow_data.get("item_batches", []))
        new_batch = [item for item in items if item]
        if new_batch:
            batches.append(new_batch)
        flat_items = [item for batch in batches for item in batch]
        flow_data["item_batches"] = batches
        flow_data["items"] = flat_items
        user_state["data"] = flow_data
        self.user_states[user_id] = user_state
        self._save_user_states()

        item_count = len(flat_items)
        return (
            f"Added {len(new_batch)} item(s). Total: {item_count} items.\n\n"
            "Add more items, or type `!end`, `/end`, or 'end' to finish the list.",
            False,
        )

    @handle_errors(
        "handling entry edit flow",
        default_return=(
            "I'm having trouble with the edit flow. Please try again.",
            True,
        ),
    )
    def _handle_entry_edit_flow(
        self, user_id: str, user_state: dict, message_text: str
    ) -> tuple[str, bool]:
        """Handle phone-friendly replace edit: next message replaces entry description."""
        message_lower = message_text.lower().strip()

        control = self._try_flow_control_command(
            user_id,
            user_state,
            message_lower,
            self._build_flow_control_handlers(
                # Skip and cancel both abandon without writing (entry already exists).
                on_skip_all=lambda: self._cancel_entry_edit(user_id, user_state),
                on_skip_question=lambda: self._cancel_entry_edit(user_id, user_state),
                on_undo_creation=lambda: self._cancel_entry_edit(user_id, user_state),
                on_step_back=lambda: self._cancel_entry_edit(user_id, user_state),
                is_unrelated=is_unrelated_entry_edit_message,
                on_timeout_unrelated=lambda: self._cancel_entry_edit(user_id, user_state),
                skip_question_checker=is_skip_question_message,
                undo_creation_checker=lambda msg: message_matches_keyword(
                    msg, ENTRY_EDIT_CANCEL_KEYWORDS
                ),
            ),
            flow_label="entry edit flow",
        )
        if control is not None:
            return control

        flow_data = user_state.get("data", {})
        entry_ref = flow_data.get("entry_ref")
        if not entry_ref:
            self._clear_flow_state(user_id, mark_completion=True)
            return ("Edit session lost its entry reference. Please try `!edit` again.", True)

        body = message_text.strip()
        if not body:
            return (
                "Send the new body text for this entry, or type `cancel` to leave it unchanged.",
                False,
            )

        self._clear_flow_state(user_id, mark_completion=True)

        from notebook.notebook_service import replace_entry_body

        result = replace_entry_body(user_id, entry_ref, body)
        entry = result.entry if result else None
        if entry:
            short_id = self._entry_short_id(entry)
            title = entry.title or "Untitled"
            return (f"✅ Updated '{title}' ({short_id})", True)
        return (
            "❌ Failed to update. Entry not found or cannot be edited (lists use item commands).",
            True,
        )

    # not_duplicate: notebook flow persist (no task identifier/history)
    @handle_errors("starting notebook conversation flow", default_return=None)
    def _start_notebook_flow(
        self,
        user_id: str,
        flow: int,
        data: dict[str, Any],
        log_label: str,
    ) -> None:
        """Persist a notebook conversation flow for the next inbound message."""
        self.user_states[user_id] = {
            "flow": flow,
            "state": 0,
            "data": dict(data),
            "started_at": now_timestamp_full(),
        }
        self._save_user_states()
        logger.debug(f"Started {log_label} for user {user_id}")

    @handle_errors("getting note body flow data", default_return=None)
    def get_note_body_flow_data(self, user_id: str) -> dict[str, Any] | None:
        """Return a copy of note-body flow data when that flow is active."""
        state = self.user_states.get(user_id) or {}
        if state.get("flow") != FLOW_NOTE_BODY:
            return None
        data = state.get("data")
        return dict(data) if isinstance(data, dict) else {}

    @handle_errors("starting note body flow", default_return=None)
    def start_note_body_flow(
        self,
        user_id: str,
        *,
        title: str,
        tags: list[str] | None = None,
        group: str | None = None,
    ) -> None:
        """Start a note-body prompt flow. Called after a title-only create-note command."""
        self._start_notebook_flow(
            user_id,
            FLOW_NOTE_BODY,
            {"title": title, "tags": list(tags or []), "group": group},
            "note body flow",
        )

    @handle_errors("starting journal body flow", default_return=None)
    def start_journal_body_flow(
        self,
        user_id: str,
        *,
        title: str,
        tags: list[str] | None = None,
        group: str | None = None,
    ) -> None:
        """Start a journal-body prompt flow. Called after a title-only create-journal command."""
        self._start_notebook_flow(
            user_id,
            FLOW_JOURNAL_BODY,
            {"title": title, "tags": list(tags or []), "group": group},
            "journal body flow",
        )

    @handle_errors("starting list items flow", default_return=None)
    def start_list_items_flow(
        self,
        user_id: str,
        *,
        title: str,
        tags: list[str] | None = None,
        group: str | None = None,
    ) -> None:
        """Start a list-item collection flow. Called after a title-only create-list command."""
        self._start_notebook_flow(
            user_id,
            FLOW_LIST_ITEMS,
            {
                "title": title,
                "tags": list(tags or []),
                "group": group,
                "items": [],
                "item_batches": [],
            },
            "list items flow",
        )

    @handle_errors("starting entry edit flow", default_return=None)
    def start_entry_edit_flow(
        self,
        user_id: str,
        *,
        entry_ref: str,
        short_id: str,
        title: str,
    ) -> None:
        """Start a replace-edit session. Next free-text message becomes the new body."""
        self._start_notebook_flow(
            user_id,
            FLOW_ENTRY_EDIT,
            {"entry_ref": entry_ref, "short_id": short_id, "title": title},
            "entry edit flow",
        )
