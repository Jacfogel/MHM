> **File**: `development_docs/NOTES_PLAN.md`
> **Audience**: Human Developer & AI Collaborators
> **Purpose**: Implementation plan for notebook feature

Notebook Implementation Task List
0) Create the new feature skeleton

Add top-level directory: notebook/

Add files:

notebook/__init__.py

notebook/schemas.py (pydantic schemas)

notebook/notebook_data_handlers.py (read/write JSON, migrations)

notebook/notebook_data_manager.py (CRUD operations + queries)

notebook/notebook_validation.py (validation helpers, if needed)

Add per-user data directory conventions:

data/users/<user_uuid>/notebook/

Decide file name now: entries.json (single file for everything)

Optional later: entries.archive.json or entries_archived.json (don’t do now unless you need it)

Outcome: repo has a dedicated notebook module with a clear “handlers + manager + schemas” structure.

1) Define the Unified Entry schema (pydantic)

In notebook/schemas.py, define:

Entry (single type)

entry_id: uuid

kind: Literal["note","list","journal"] (start with these 3)

title: Optional[str]

body: Optional[str] (notes/journal use; list can still have body for context)

items: Optional[List[ListItem]] (only for kind="list")

tags: List[str] (normalized)

group: Optional[str] (single string group)

pinned: bool

archived: bool

created_at: datetime

updated_at: datetime

ListItem

item_id: uuid

text: str

done: bool

order: int

created_at: datetime

updated_at: datetime

Decide and implement tag normalization rules (don’t overbuild):

strip whitespace

lowercase

optionally remove leading #

Outcome: one schema supports current and future entry types.

2) Add shared helpers (minimal, optional but recommended)

Add core/tags.py with:

normalize_tag(tag: str) -> str

normalize_tags(tags: list[str]) -> list[str]

validate_tag(tag: str) -> None (length rules, allowed chars)

Add core/ids.py with short id utilities (optional but useful for Discord):

format_short_id(kind: str, entry_id: UUID, length: int = 6) -> str → n-3f2a9c

parse_short_id(text: str) -> (kind_prefix, short_fragment)

In notebook manager, allow lookup by:

full UUID

short id fragment (with collision handling)

title (if unique)

Outcome: entries can be referenced on phone without typing UUIDs.

3) Implement NotebookDataHandlers (JSON persistence)

In notebook/notebook_data_handlers.py implement:

Resolve user notebook path:

data/users/<uuid>/notebook/entries.json

load_entries(user_id) -> list[Entry]

if file missing: return []

validate JSON with pydantic

if schema versioning exists later, migrate

save_entries(user_id, entries) -> None

atomic write (write temp, replace)

optional: create backups (follow your existing pattern)

Choose a file format now and stick to it:

Either:

{"schema_version": 1, "entries": [...]} (recommended)

or a raw list [...] (faster, less structured)

Outcome: notebook data loads/saves reliably for each user.

4) Implement NotebookDataManager (CRUD + queries)

In notebook/notebook_data_manager.py implement operations:

Create

create_note(user_id, title, body, tags, group) -> Entry

create_list(user_id, title, tags, group, body=None) -> Entry

create_journal(user_id, title=None, body, tags, group=None) -> Entry

Read

get_entry(user_id, entry_ref) -> Entry
entry_ref can be id / short id / title

list_recent(user_id, limit=5, include_archived=False) -> list[Entry]

list_by_tag(user_id, tag, limit=20) -> list[Entry]

list_by_group(user_id, group, limit=20) -> list[Entry]

Update

append_to_entry_body(user_id, entry_ref, text) -> Entry

set_entry_body(user_id, entry_ref, text) -> Entry

rename_entry(user_id, entry_ref, new_title) -> Entry

set_group(user_id, entry_ref, group) -> Entry

add_tags(user_id, entry_ref, tags) -> Entry

remove_tags(user_id, entry_ref, tags) -> Entry

pin_entry(user_id, entry_ref, pinned=True) -> Entry

archive_entry(user_id, entry_ref, archived=True) -> Entry

List item ops (only for kind="list")

add_list_item(user_id, entry_ref, text) -> Entry

set_list_item_done(user_id, entry_ref, item_index_or_id, done=True) -> Entry

remove_list_item(user_id, entry_ref, item_index_or_id) -> Entry

reorder_list_items(user_id, entry_ref, new_order) -> Entry (can defer)

Search (V0)

search_entries(user_id, query, limit=10) -> list[Entry]

implement simple case-insensitive substring across:

title

body

list item texts

Add a single internal helper:

_save_updated_entry(user_id, entry, all_entries) updates updated_at, persists once.

Outcome: notebook feature is usable without Discord/UI changes beyond calling these functions.

5) Add channel-agnostic command handler for Notebook

Create: communication/command_handlers/notebook_handler.py

Mirror the style of task_handler.py

Parse commands + call notebook manager functions

Return formatted responses (short + usable on phone)

Define your minimum command set (implement in this order):

!n <text> (create note)

!recent

!show <ref>

!append <ref> <text>

!tag <ref> <tags...>

!s <query>

!l new <name>

!l add <ref> <item>

!l show <ref>

!l done <ref> <#>

Wire it into communication/message_processing/command_parser.py

Add routing so notebook commands are recognized alongside tasks.

Outcome: you can run the global notebook from Discord immediately.

6) Add “Edit session” (mobile-friendly editing)

Add an “edit mode” flow (fits your conversational pipeline):

!edit <ref>

bot replies: “Send the new content within 10 minutes. !cancel to cancel.”

Your next message becomes the new body (or append, depending on mode)

Store pending edit session in a small per-user in-memory map (or user_context.json if needed)

This likely touches:

user/context_manager.py

user/user_context.py

communication/message_processing pipeline

Outcome: you can do real edits from your phone without fiddly command formatting.

7) Organization features (grouping, pinned, inbox view)

Add commands:

!pinned

!pin <ref> / !unpin <ref>

!archive <ref> / !unarchive <ref>

!group <ref> <groupname>

!group <groupname> (show entries in group)

!inbox (untagged + unarchived + recent)

Outcome: notebook stays findable without you manually curating it.

8) Skip-aware reminders integration (later, but planned)

Extend task skip handling so it can create notebook entries:

If a task is skipped N times, create:

kind="note"

title: Blocker: <task name>

tags: blocker, task:<task_id>

body: “Skipped at …” + last prompt

This touches:

tasks/task_management.py

existing task command handler

notebook manager create functions

Outcome: “skips” turn into captured blockers instead of endless nagging.

9) AI extraction from conversation (after notebook commands are stable)

Define pydantic intent schemas (probably in ai/ or core/schemas.py):

CreateEntryIntent, AddListItemIntent, TagIntent, etc.

Update ai/chatbot.py to output structured JSON intents.

In communication/message_processing/command_parser.py, add:

if no explicit command but message looks like an instruction:

call AI

validate intent with pydantic

execute via notebook manager

respond with “created/updated X”

Outcome: you can talk naturally and have it extract “make a note/list” actions.

About SQLite FTS later (migration risk)

If you follow the above and keep all notebook operations behind NotebookDataHandlers + NotebookDataManager, moving from JSON → SQLite later is not scary:

replace only the handler implementation

keep manager signatures the same

write one migration script that reads entries.json and inserts rows

So: start with JSON is fine, as long as you keep the abstraction boundary.

Your immediate next 3 tasks (if you want the fastest useful version)

Create notebook/schemas.py + entries.json format

Implement notebook_data_handlers.py (load/save) + notebook_data_manager.py (create note + recent + show)

Add notebook_handler.py with !n, !recent, !show

That gets you real value from Discord quickly.