> **File**: `development_docs/NOTES_PLAN.md`
> **Audience**: Human Developer & AI Collaborators
> **Purpose**: Implementation plan for notebook feature

# MHM Notebook (Unified Entry) Roadmap

**Purpose:** Add a **global personal notebook** to MHM that works **Discord-first** (phone-friendly), is **channel-agnostic**, and is built to share foundations with Tasks (tags, validation, persistence patterns) **without forcing a big refactor now**.

This roadmap assumes:
- Current command routing lives in `communication\command_handlers` and channel abstraction lives in `communication\communication_channels\base`.
- Discord channel implementation is in `communication\communication_channels\discord`.
- Per-user persistence is JSON under `data\users\<user_uuid>\...`.

---

## Goal State (what “done” looks like)

From Discord on your phone you can:
- capture a note in seconds
- create and manage lists (as a type of entry)
- retrieve by **recent**, **pinned**, **tag**, **group**, and **search**
- edit entries without needing your PC
- keep everything organized with tags + group + timestamps, with minimal babysitting

Future-friendly constraints:
- Unified “Entry” supports `note`, `list`, `journal` now, and `event` later.
- Storage is JSON initially, but **storage access is abstracted** so moving to SQLite/FTS later is straightforward.

---

## Directory / Module Plan (minimal change, future-friendly)

### New top-level feature directory
- `notebook/`
  - `__init__.py`
  - `schemas.py` (Pydantic models; feature-specific)
  - `notebook_data_handlers.py` (JSON read/write + migrations + indexing)
  - `notebook_data_manager.py` (CRUD operations + queries; no “service” naming)
  - `notebook_validation.py` (validation helpers specific to notebook objects)
  - `notebook_search.py` (search strategy; starts substring, later can be swapped)

### New shared primitives (core)
- `core/tags.py` (shared tag normalization/validation across notebook + tasks)
- (Optional) `core/ids.py` (short external ID formatting and parsing)

### New command handler
- `communication\command_handlers\notebook_handler.py`
  - channel-agnostic command parsing for notebook commands
  - calls into `notebook.notebook_data_manager`

### User data layout (per user)
Add:
- `data\users\<uuid>\notebook\`
  - `entries.json`  *(primary source of truth)*
  - `entries_index.json` *(optional; helps “recent” + search speed for JSON)*

> **Note:** Keep your existing `tags.json` for now unless it causes conflicts. The tag **logic** moves to `core/tags.py`, not necessarily the file location yet.

---

## Unified Entry Model (Pydantic)

### Entry kinds
- `note` – free text
- `list` – list items + optional description
- `journal` – note with date semantics (optional daily grouping)
- *(future)* `event` – calendar item

### Required fields (all entries)
- `id` (UUID string, internal)
- `kind` (`note` | `list` | `journal` | ...)
- `title` (optional for quick capture notes)
- `body` (text; may be empty for lists)
- `tags` (list[str]) - multiple labels for detailed categorization (e.g., `["#work", "#urgent", "project:alpha"]`)
- `group` (optional string; e.g., `work`, `health`, `home`) - single high-level category for broad organization
- `pinned` (bool)
- `archived` (bool)
- `created_at`, `updated_at` (ISO timestamps)

**Groups vs Tags:**
- **Groups**: Single optional string - used for broad, high-level organization (one group per entry)
- **Tags**: List of strings - used for detailed labeling and fine-grained filtering (multiple tags per entry)
- Example: A note might have `group: "work"` (broad category) and `tags: ["#meeting", "#urgent", "project:alpha"]` (detailed labels)

### List items (when `kind == "list"`)
Each item:
- `id` (UUID)
- `text`
- `done` (bool)
- `order` (int)
- `created_at`, `updated_at` (ISO)

### External IDs (Discord-friendly)
- Internal IDs stay UUID.
- Optionally display short IDs:
  - `n-3f2a9c`, `l-91ab20`, `j-0c77e2`
- Short IDs are derived from UUID prefix, and only used for lookup convenience.

---

## Command Set (Discord-first, channel-agnostic)

### V0 (must-have)
- `!n <text>` or `!note <text>`  
  Create a quick note. If only title provided, prompts for body text (5 min timeout, can skip with `!skip`).  
- `!n <title> : <body>` or `!n <title>\n<body>`  
  Create note with title/body split (colon or newline separator).  
- `!recent [N]` or `!r [N]`  
  Show last N updated entries (notes + lists + journal).  
- `!recentn [N]`, `!rnote [N]`, `!shownotes [N]`, etc.  
  Show recent notes only.  
- `!show <id_or_title>`  
  Display one entry (works for both notes and tasks).  
- `!append <id_or_title> <text>`, `!add <id_or_title> <text>`, `!addto <id_or_title> <text>`  
  Append text to entry body (works for both notes and tasks).  
- `!tag <id_or_title> <tags...>`  
  Add tags (supports `#tag`, `area:home`, etc.; works for both notes and tasks).  
- `!untag <id_or_title> <tags...>`  
  Remove tags (works for both notes and tasks).  
- `!search <query>` or `!s <query>`  
  Search entries (V0: substring; works for both notes and tasks).  
- `!pin <id_or_title>` / `!unpin <id_or_title>` (notes only)  
- `!archive <id_or_title>` / `!unarchive <id_or_title>` (notes only)

### V1 (lists)
- `!l <title>`, `!list <title>`, `!nl <title>`, `!newlist <title>`, `!createlist <title>`, etc.  
  Create list. If no items provided, prompts for items (comma/semicolon/newline separated). End with `!end`, `/end`, or `end`.  
- `!l <title> : <item1>, <item2>, ...` or `!l <title>\n<item1>\n<item2>...`  
  Create list with initial items in command.  
- `!l add <id_or_title> <item text>`
- `!l show <id_or_title>` or `!show <id_or_title>` (works for lists too)
- `!l done <id_or_title> <item#>`
- `!l undo <id_or_title> <item#>` or `!l undo <id_or_title> <item#>`

### V2 (organization)
- `!group <id_or_title> <groupname>`  
  Set group on entry.  
- `!group <groupname>`  
  Show entries in group.  
- `!tag <tag>` or `!t <tag>`  
  Show entries with tag (works for both notes and tasks).  
- `!pinned`  
  Show pinned entries.  
- `!inbox`  
  Show untagged, unarchived recent items (works for both notes and tasks).
- `!archived` or `!archive`  
  Show archived entries (notebook entries only).

### Editing sessions (phone-friendly, recommended)
- `!edit <id_or_title>`  
  Starts an edit session; your next message becomes replacement body (or use `!appendmode`).
- `!cancel`  
  Cancels edit session.

---

## Roadmap Tasks (in build order)

### Milestone 1 — Foundations + V0 Notes (Capture + Find)
**Outcome:** You can capture, tag, show, append, and retrieve recent notes from Discord.

#### 1.1 Create `core/tags.py`
- Implement:
  - `normalize_tag(tag: str) -> str`
  - `validate_tags(tags: list[str]) -> list[str]`
  - `parse_tags_from_text(text: str) -> tuple[str, list[str]]` *(optional)*
- Decide tag rules:
  - allow `#tag` and `key:value` formats
  - lowercase normalization (recommended)

**Acceptance:**
- tags are stored consistently (no duplicates like `Work` vs `work`).

#### 1.2 Add Notebook schemas (`notebook/schemas.py`)
- Define `EntryKind`, `Entry`, `ListItem`.
- Use Pydantic validation:
  - required fields, timestamp formats, tag normalization via `core/tags.py`

**Acceptance:**
- invalid entries cannot be saved (fails fast with useful errors).

#### 1.3 Add JSON handlers (`notebook/notebook_data_handlers.py`)
- Implement:
  - `load_entries(user_id) -> list[Entry]`
  - `save_entries(user_id, entries) -> None` (atomic write)
  - `ensure_notebook_dirs(user_id) -> Path`
  - basic migration/versioning if needed (`schema_version` in file)
- Store:
  - `entries.json` as canonical

**Acceptance:**
- notebook creates required directories and files automatically on first use.

#### 1.4 Add operations (`notebook/notebook_data_manager.py`)
Implement high-level functions:
- `create_entry(...) -> Entry`
- `get_entry(ref) -> Entry` (ref = id, short id, or title if unique)
- `list_recent(n=5) -> list[EntrySummary]`
- `append_to_entry(ref, text) -> Entry`
- `set_entry_body(ref, text) -> Entry`
- `add_tags(ref, tags) -> Entry`
- `remove_tags(ref, tags) -> Entry`
- `pin/unpin`, `archive/unarchive`
- `search(query) -> list[EntrySummary]` (V0 substring)

**Acceptance:**
- “recent” and “show” work after restart; entries persist reliably.

#### 1.5 Add command handler (`communication\command_handlers\notebook_handler.py`)
- Parse notebook commands and call data manager methods.
- Keep output short and mobile-friendly:
  - always display title (or first line), tags, and short id
- Return IDs in responses.

**Acceptance:**
- From Discord, you can:
  - `!n hello`
  - `!recent`
  - `!show <id>`
  - `!append <id> more`
  - `!tag <id> area:home`

#### 1.6 Wire into command parser (`communication\message_processing\command_parser.py`)
- Register notebook commands alongside existing task commands.
- Ensure channel-agnostic behavior remains intact.

**Acceptance:**
- Notebook commands work through the same pipeline tasks use.

#### 1.7 Tests (minimum)
- Add `tests/` coverage for:
  - tag normalization
  - create/save/load roundtrip
  - append updates `updated_at`
  - search returns expected matches

---

### Milestone 2 — Lists as Entry Kind
**Outcome:** Lists are usable from Discord like a lightweight task list.

#### 2.1 Extend schemas for list entries
- Enforce:
  - `kind == "list"` implies `items` exists
  - list item ordering consistent

#### 2.2 Add list operations to data manager
- `create_list(title, tags, group) -> Entry`
- `add_list_item(ref, text) -> Entry`
- `toggle_list_item_done(ref, item_index, done=True) -> Entry`
- `reorder_list_items(ref, ...)` *(optional later)*

#### 2.3 Add list commands to handler
- `!l new`, `!l add`, `!l show`, `!l done`, `!l undo`

**Acceptance:**
- You can maintain groceries (or similar) entirely from Discord.

---

### Milestone 3 — Organization Views (group, inbox, pinned)
**Outcome:** You can retrieve info even when you don’t remember names.

#### 3.1 Add group support
- store `group` on entries
- commands:
  - `!group <id> <group>`
  - `!group <group>`

#### 3.2 Add “smart views” (queries)
- `inbox`: untagged + unarchived within last X days
- `pinned`
- `by_tag`
- `by_group`
- optional `stale`: not updated in 60+ days

**Acceptance:**
- You can find anything via recent/tag/group/search with minimal friction.

---

### Milestone 4 — Phone-friendly Edit Sessions
**Outcome:** Editing longer entries is practical from mobile.

#### 4.1 Add edit session tracking per user/channel
- store temporary state in memory (and optionally in a small json if needed)
- timeout after N minutes
- `!edit <id>` + next message becomes body
- `!cancel`

**Acceptance:**
- You can rewrite a note from your phone without copying/pasting IDs repeatedly.

---

### Milestone 5 — Skip-responsive Reminders that Create Notebook Artifacts
**Outcome:** Skips produce useful “why” notes/lists instead of nagging.

#### 5.1 Extend task skip tracking (if not already)
- record skip reason codes
- record skip counts per task

#### 5.2 “Skipped → capture” integrations
- When skipped repeatedly:
  - auto-create notebook entry tagged `blocker` + `task:<id>`
  - optional prompt: “Capture why?” → creates note if you reply

**Acceptance:**
- Repeated skips reduce noise and externalize the blocker into notebook.

---

### Milestone 6 — AI “Intent Extraction” for Notebook Actions
**Outcome:** You can write conversationally and have MHM propose notebook actions safely.

#### 6.1 Define Pydantic intents (AI output schema)
- `CreateEntryIntent`, `AppendEntryIntent`, `CreateListIntent`, `AddListItemIntent`, `TagIntent`, etc.

#### 6.2 Integrate with `ai\chatbot.py`
- AI produces structured JSON matching intent schemas.
- Validate with Pydantic.
- Execute only via `notebook_data_manager` methods.

#### 6.3 Hook into `communication\message_processing\command_parser.py`
- If no explicit command is detected:
  - optionally pass text through AI intent extraction
  - apply safety rules (confidence/confirmation gates)

**Acceptance:**
- You can type: “remind me to buy milk and eggs; make a groceries list”
- system proposes actions and performs them (with confirmation if needed).

---

## JSON vs SQLite Search: Migration Guidance

Start with JSON + substring search.
To keep migration easy later:
- Keep all notebook data access behind `notebook_data_handlers` + `notebook_data_manager`.
- Avoid having command handlers read/write JSON directly.
- Add `notebook_search.py` with a `search()` function whose implementation can be swapped.

Later migration steps (when you’re ready):
1. Add SQLite DB under `data\users\<uuid>\notebook\notebook.db`
2. Write one-time migration script: JSON → DB
3. Replace handler implementations in `notebook_data_handlers` (keep method signatures)
4. Implement SQLite FTS5 for `title/body/items.text`

If you follow this structure, the migration is **not** a rewrite—just a backend swap.

---

## Suggested Implementation Order (short version)
1. `core/tags.py`
2. `notebook/schemas.py`
3. `notebook/notebook_data_handlers.py`
4. `notebook/notebook_data_manager.py`
5. `communication/command_handlers/notebook_handler.py`
6. wire into `command_parser.py`
7. tests
8. lists
9. smart views
10. edit sessions
11. skip integrations
12. AI extraction

---

## Current Implementation Status

### Milestone Completion Summary
- **Milestone 1 (Foundations + V0 Notes)**: ✅ **COMPLETED** - Core infrastructure, data handlers, command handler, and basic commands all implemented
- **Milestone 2 (Lists)**: ✅ **COMPLETED** - List operations and commands fully implemented
- **Milestone 3 (Organization Views)**: ✅ **COMPLETED** - Group support, smart views (pinned, inbox, tag view) implemented
- **Milestone 4 (Edit Sessions)**: ⏳ **PENDING** - Not yet implemented
- **Milestone 5 (Skip Integration)**: ⏳ **PENDING** - Not yet implemented
- **Milestone 6 (AI Extraction)**: ⏳ **PENDING** - Not yet implemented

### Recent Fixes & Improvements ✅
- **Regex Pattern Fix**: Removed `!` prefix from all regex patterns in `command_parser.py` to match messages after prefix stripping
- **Multi-line Support**: Added `re.DOTALL` flag to regex compilation to support newline-separated note bodies and list items
- **Button Handler**: Added Discord button interaction handler for suggestion buttons (`suggestion_` custom_ids)
- **Slash Command Conversion**: Fixed slash command conversion to strip `!` prefix before passing to parser (prevents recursion)
- **Flow State Clearing**: Added early flow clearing when commands (`/` or `!`) are detected, preventing flow keywords from interfering
- **Command Definition Cleanup**: Made `mapped_message` optional in `CommandDefinition`, removed redundant entries, relying on regex patterns for aliases
- **Flow Keywords**: Removed flow-specific keywords (`skip`, `end`, `endlist`) from command detection, allowing `ConversationManager` to handle them properly
- **Note Body Flow Prompt**: Updated note creation prompt to use button-style format: "What would you like to add as the body text? [Skip] [Cancel]" with `suggestions=["Skip", "Cancel"]` for consistent UX
- **Flow Expiration**: Increased all conversation flow timeouts from 5 minutes to 10 minutes (note body, list items, task due date, task reminder flows) to prevent premature expiration
- **Flow Interference Detection**: Added unrelated message detection in flow handlers (`_handle_note_body_flow`, `_handle_list_items_flow`, `_handle_task_due_date_flow`, `_handle_task_reminder_followup`) - if user sends a command or greeting while in a flow, the flow is cleared to allow normal command processing
- **Task Creation Flow Fixes**: Fixed task creation to properly route to due date flow when no valid due date exists, and only prompt for reminder periods when a valid due date is present. Added explicit date validation and improved date/time parsing for natural language expressions
- **List Flow End Command Fix**: Fixed `!end` command not working in list creation flow - added `'end'`, `'endlist'`, and `'endl'` to flow keywords list in `interaction_manager.py` so they're properly routed to conversation manager instead of being treated as regular commands that clear the flow

### Initial Testing Results ✅
**Discord Testing (Quick Start):**
- ✅ **Note Creation**: `!n Hello world` - Works correctly, creates note with short ID (e.g., `n-835a65`)
- ✅ **Recent View**: `!recent` - Works correctly, shows recent entries with proper formatting
- ✅ **Show Entry**: `!show n-xxxxxx` - Works correctly, displays entry details
- ✅ **Note Body Flow**: Flow prompts correctly with Skip/Cancel buttons when only title provided
- ✅ **List Creation Flow**: `!l Groceries` - Flow prompts correctly for items, accepts comma-separated items
- ⚠️ **List End Command**: `!end` - **FIXED** - Was not working (treated as command instead of flow keyword), now fixed by adding to flow keywords list

### Command Implementation Status

#### In Progress
- **Note Creation**: `!n`, `!note`, `!nn`, `!newn`, `!createnote`, etc. with `:` or newline separator
- **Note Flow State**: Prompts for body text when only title provided (10 min timeout, `[Skip]` and `[Cancel]` button support)
  - ✅ **Verified**: Flow correctly prompts with button-style format when only title provided
  - ⏳ **Not yet verified**: Flow expires after 10 minutes of inactivity
  - ⏳ **Not yet verified**: Flow clears when unrelated commands are sent (allows normal command processing)
  - ✅ **Verified**: Skip and Cancel buttons work correctly to exit flow
- **List Creation**: `!l`, `!list`, `!newlist`, `!createlist`, etc. with flow support for items
- **List Flow State**: Prompts for list items (comma/semicolon/newline separated, `!end` to finish)
  - ✅ **Verified**: Flow correctly prompts for items when only title provided
  - ✅ **Verified**: Accepts comma/semicolon/newline separated items
  - ✅ **Fixed**: `!end` command now properly ends list creation (was clearing flow instead of finishing list)
  - ⏳ **Not yet verified**: Flow expires after 10 minutes of inactivity
  - ⏳ **Not yet verified**: Flow clears when unrelated commands are sent
- **Recent Views**: `!recent`, `!r`, `!recentn`, `!rnote`, `!shownotes` patterns
- **Entry Display**: `!show <id_or_title>` (works for both notes and tasks)
- **Append Operations**: `!append`, `!add`, `!addto` (works for both notes and tasks)
- **Tag Operations**: `!tag`, `!untag` (works for both notes and tasks)
- **Search**: `!search`, `!s` (works for both notes and tasks)
- **Note Actions**: `!pin`, `!unpin`, `!archive`, `!unarchive` (notes only)
- **List Operations**: `!l add`, `!l done`, `!l undo`, `!l remove`
- **Smart Views**: `!pinned`, `!inbox`, `!t <tag>`, `!group <groupname>`
- **Group Management**: `!group <id_or_title> <groupname>` (set group)

#### Known Issues & Opportunities for Improvement ⚠️

**High Priority Issues:**
- ~~**Set Entry Body Command**: Handler exists (`set_entry_body`) but no command patterns (`!set` or similar) - needs implementation~~ ✅ **FIXED** - Added `!set`, `!replace`, `!update` command patterns
- ~~**Create Journal Commands**: Handler exists (`create_journal`) but no command patterns - needs implementation~~ ✅ **FIXED** - Added `!j`, `!journal`, `!newjournal`, etc. command patterns
- ~~**Short ID Format**: Currently uses dash (`n-123abc`) which is harder to type on mobile - should remove dash for better mobile UX~~ ✅ **FIXED** - Changed to `n123abc` format (no dash), backward compatible with old format
- **Group Command Ambiguity**: `!group <entry> <group>` vs `!group <group>` - parser may incorrectly route single-word group names

**User Experience Issues:**
- **Edit Sessions (Milestone 4)**: Not implemented - users can't easily rewrite long notes (must use `!set` or `!append`)
- **No Bulk Operations**: Can't tag multiple entries at once, or perform other bulk actions
- **Error Messages**: Some error messages could be more actionable (e.g., suggest similar entry IDs when not found)
- **Search Feedback**: No helpful feedback when search returns no results (just "No entries found")
- **Command Discovery**: No help system for discovering notebook commands (e.g., `!help notebook`)
- **Journal Visual Distinction**: Journal entries look identical to notes in responses (no visual distinction)
- **Group vs Tag Clarity**: Group vs tag distinction might be unclear to users (single group vs multiple tags)
- **Command Consistency**: Some commands note-specific (`!pin`, `!archive`) while others are shared (could be confusing)
- **List Command Prefix**: List operations use `!l` prefix while note operations don't (inconsistent)

**Technical Debt:**
- **Search Module**: Search logic in `notebook_data_manager.py` instead of separate `notebook_search.py` (plan suggested abstraction)
- **Short ID Formatting**: Logic duplicated between handler and validation - should centralize in `core/ids.py`
- **Task Short IDs**: Tasks don't have short IDs - should implement centralized ID system (`core/ids.py`) for both tasks and notebook entries
- **Pattern Duplication**: Some regex patterns duplicated (e.g., `r'^n\s+(.+)$'` appears twice in create_note patterns)
- **Slash Command Registration**: Notebook commands work via conversion but not explicitly registered (affects discoverability)
- **Flow State Persistence**: Currently in-memory with JSON backup - could be improved
- **Pagination**: Search, inbox, pinned, group, and tag views don't support pagination - **TODO**: Add "Show More" buttons and pagination support

**Robustness & Scalability:**
- **Concurrent Access**: No validation for concurrent access (multiple users/devices)
- **File Operation Retry**: No retry logic for file operations (though atomic writes reduce risk)
- **Migration System**: Schema versioning exists but no migration logic for schema changes
- **Backup/Restore**: No backup/restore mechanism for notebook data
- **Performance**: No indexing for large datasets (plan mentioned `entries_index.json` as optional)
- **Performance Tests**: No performance tests (large datasets, concurrent access)
- **Integration Tests**: No integration tests with actual Discord bot

**AI Integration:**
- **AI Chatbot Access**: AI chatbot does not currently have access to notebook entries in context
- **AI Intent Extraction (Milestone 6)**: Not implemented - natural language intent extraction pending
- **AI Fallback**: Falls back to AI chatbot when commands unclear, but AI may not understand notebook-specific intents

**Documentation:**
- **User Documentation**: No user-facing documentation (how to use notebook commands)
- **API Documentation**: No API documentation for data manager functions

### Command Support Matrix
- **Bang commands (`!command`)**: ✅ Fully supported
- **Slash commands (`/command`)**: ✅ Supported via conversion logic (works but not explicitly registered)
- **Natural text (no prefix)**: ✅ Mostly supported via regex patterns (~83% coverage)

### Generalization Status
Many commands now work for both tasks and notes:
- `!show <id_or_title>` - works for both
- `!append`, `!add`, `!addto` - works for both
- `!tag`, `!untag` - works for both
- `!search`, `!s` - works for both
- `!inbox` - works for both
- `!tag <tag>`, `!t <tag>` - works for both

Task-specific: `!complete`, `!uncomplete` (tasks only)  
Note-specific: `!pin`, `!unpin`, `!archive`, `!unarchive` (notes only)

---

## Implementation Details & Behavior

### Recent Entries Behavior
- **Default Limit**: Shows 5 most recently updated entries by default
- **Custom Limit**: Users can specify limit with `!recent N` (e.g., `!recent 10`)
- **Sorting**: Entries sorted by `updated_at` timestamp (most recent first)
- **Archived Entries**: Archived entries are **excluded** from recent by default
- **Including Archived**: Can include archived entries by calling `list_recent(user_id, n=5, include_archived=True)` programmatically (no command pattern yet)
- **What if More Notes Exist**: Only shows the N most recent (doesn't indicate if more exist - acceptable for recent view)
- **Tasks Included**: ❌ **NO** - Only notebook entries (notes, lists, journal) are included. Tasks are stored separately and don't appear in notebook queries.

### Inbox vs Recent - Key Differences
- **Recent (`!recent`)**: Shows N most recently updated entries (default 5), sorted by `updated_at`, excludes archived
- **Inbox (`!inbox`)**: Shows **untagged, unarchived** entries updated within last 30 days (default 5, paginated), sorted by `updated_at`
  - **Purpose**: Inbox is for "uncategorized" items that need attention/tagging
  - **Filter**: Must have NO tags AND not be archived AND updated within 30 days
  - **Use Case**: Quick way to see items that haven't been organized yet
  - **Pagination**: Shows 5 at a time with "Show More" button if more exist

### Archiving Behavior
- **What Archiving Does**: Sets `archived=True` flag on entry (entry still exists in storage)
- **Effect on Queries**: 
  - Archived entries excluded from `!recent` by default
  - Archived entries excluded from `!search` results
  - Archived entries excluded from `!inbox` view
  - Archived entries excluded from `!pinned` view
  - Archived entries excluded from `!group` and `!tag` views
- **Accessing Archived**: 
  - Can still access archived entries directly by ID (`!show <id>`)
  - Use `!archived` or `!archive` to list archived entries (shows 5 at a time, paginated)
- **Unarchiving**: Use `!unarchive <id>` to restore entry to normal views
- **Pagination**: All list views (archived, inbox, pinned, group, tag, search) show 5 entries at a time with "Show More" button if more exist
- **Default Display**: All queries show 5 entries initially, with pagination support to view more

### Short ID Format
- **Current Format**: `n123abc` (kind prefix + 6-8 hex characters, **no dash**)
- **Change Made**: Removed dash for easier mobile typing (changed from `n-123abc` to `n123abc`)
- **Backward Compatibility**: **REMOVED** - No longer supports dash format (user will update files manually)
- **Examples**: `n123abc` (note), `l91ab20` (list), `j0c77e2` (journal)
- **Task Short IDs**: Tasks currently use full UUIDs (`task_id`), not short IDs - **TODO**: Implement centralized short ID system for tasks (e.g., `t123abc`)

### Adding Tags and Groups

**Tags** (`!tag <id_or_title> <tags...>`):
- **How it works**: Use `!tag <entry_id> #work #urgent` or `!tag <entry_id> work urgent`
- **Supported formats**: `#tag` format or plain text (both normalized to lowercase)
- **Works for**: ✅ Notes, ✅ Lists, ✅ Journal entries
- **Works for Tasks**: ⚠️ **PARTIAL** - Tasks have tags in their schema, but `!tag` command only works for notebook entries. Tasks need to use `update task <id> tags <tags>` or have tags added during creation.
- **Multiple tags**: Can add multiple tags at once: `!tag n123abc #work #urgent project:alpha`
- **Tag normalization**: All tags normalized to lowercase, duplicates removed automatically

**Groups** (`!group <id_or_title> <groupname>`):
- **How it works**: Use `!group <entry_id> work` to set a group
- **Single group**: Each entry can have only ONE group (unlike tags which can have multiple)
- **Works for**: ✅ Notes, ✅ Lists, ✅ Journal entries
- **Works for Tasks**: ❌ **NO** - Tasks don't have a `group` field in their schema
- **Viewing by group**: Use `!group <groupname>` (without entry ID) to see all entries in that group (shows 5 at a time, paginated)
- **Group vs Tags**: 
  - **Group**: Single high-level category (e.g., "work", "health", "home")
  - **Tags**: Multiple detailed labels (e.g., `["#meeting", "#urgent", "project:alpha"]`)

### Tasks in Notebook Queries
- **Tasks are NOT included** in notebook queries (`!recent`, `!search`, `!inbox`, `!pinned`, `!group`, `!tag`, `!archived`)
- **Why**: Tasks are stored separately (`tasks/active_tasks.json`) from notebook entries (`notebook/entries.json`)
  - `load_entries()` only loads from `notebook/entries.json`
  - Tasks are managed by `tasks/task_management.py` and stored in `tasks/active_tasks.json`
- **Commands that work for both**: Some commands like `!show`, `!append`, `!tag` work for both tasks and notebook entries, but the queries themselves are separate
- **Future consideration**: 
  - **Long-term plan**: Move to SQLite or unified database system that contains tasks, notebook entries, events (future feature), etc.
  - **Laying groundwork**: Shared modules (`core/tags.py`, `core/user_data_validation.py`) are already in place for cross-feature functionality
  - **Unified queries**: When migrating to database, unified queries can be implemented to include both tasks and notebook entries in single results
  - **Current state**: Separate systems by design, but architecture supports future unification

### Pagination and Limits
- **All list queries are paginated**: Every query shows 5 entries at a time by default
- **Data manager limits**: Functions fetch up to 100 matching entries, then handlers paginate to show 5 at a time
- **"Show More" button**: When more entries exist, a "Show More" button appears (needs button click handler implementation)
- **Commands with pagination**:
  - `!search` - Shows 5 results at a time
  - `!inbox` - Shows 5 entries at a time
  - `!archived` - Shows 5 entries at a time
  - `!pinned` - Shows 5 entries at a time
  - `!group <groupname>` - Shows 5 entries at a time
  - `!tag <tag>` - Shows 5 entries at a time
  - `!recent` - Shows N entries (default 5, user can specify)

**Examples**:
```
!tag n123abc #work #urgent          # Add tags to note
!group n123abc work                  # Set group on note
!tag l91ab20 groceries shopping     # Add tags to list
!group l91ab20 home                  # Set group on list
!tag j0c77e2 reflection              # Add tags to journal entry
!group j0c77e2 personal              # Set group on journal entry
```

### AI Chatbot Integration
- **Fallback Behavior**: When commands are unclear, system falls back to AI chatbot (`generate_contextual_response`)
- **AI Command Parsing**: AI can parse natural language into notebook intents via `EnhancedCommandParser._ai_enhanced_parse`
- **AI Context Access**: **Currently AI chatbot does NOT have access to notebook entries** in context
  - AI sees: user profile, check-ins, tasks, schedules, conversation history
  - AI does NOT see: notebook entries, notes, lists, journal entries
- **AI Command Awareness**: AI prompt includes notebook actions (`create_note`, `create_list`, `create_journal`, `list_recent_entries`, `show_entry`, `append_to_entry`, `add_tags_to_entry`, `remove_tags_from_entry`, `search_entries`, `pin_entry`, `unpin_entry`, `archive_entry`) but AI may not always recognize them in natural language
- **Multiple Commands**: **System does NOT handle multiple commands in a single message** - parser processes one command at a time
  - Example: "delete n123abc and add potatoes to l123abc" would only process the first command
  - **Workaround**: User must send separate messages for each command
- **AI Intent Extraction (Milestone 6)**: Planned but not implemented - would allow conversational notebook actions and better multi-command handling
- **Recommendation**: 
  - Add recent notebook entries to AI context for better contextual responses
  - Consider implementing multi-command parsing (split by "and", "then", etc.)

---

## Testing Status & Next Steps

### Testing Status ✅
**Comprehensive Automated Test Suite** - Full test coverage created to replace manual Discord testing. All tests located in `tests/behavior/test_notebook_handler_behavior.py` with 54 total tests covering all notebook functionality.

**Validation System** ✅ **COMPLETED** - Comprehensive validation system implemented with proper separation of concerns:
- **General Validation** (`core/user_data_validation.py`): `is_valid_string_length()`, `is_valid_category_name()` - reusable across features
- **Notebook-Specific Validation** (`notebook/notebook_validation.py`): Entry references, short IDs, entry kinds, list indices
- **Test Coverage**: 51 validation tests total (28 unit validation + 10 unit error handling + 13 integration)
- **Error Handling**: All functions use `@handle_errors` decorator, return safe defaults, log appropriately, provide user-friendly messages
- **Data Manager Integration**: Enhanced validation in all CRUD operations (append, set body, add list item, search, set group)

**Automated Test Coverage (54 tests total):**

**Core Handler Tests (29 tests):**
- ✅ Handler intent handling verification
- ✅ Note creation (title only, title+body, with tags)
- ✅ List creation (title only, with items)
- ✅ Entry viewing (recent, show, not found cases)
- ✅ Entry editing (append, add tags, pin)
- ✅ List operations (add item, toggle done)
- ✅ Organization views (pinned, search)
- ✅ Flow states (note body flow, list items flow with !end)
- ✅ Command parsing variations (bang commands, slash commands)
- ✅ End-to-end command processing through InteractionManager

**Entity Extraction Tests (9 tests):**
- ✅ Title/body extraction with colon separator (`:`)
- ✅ Title/body extraction with newline separator
- ✅ Tag extraction from commands (`#work`, `#urgent`)
- ✅ Entry reference extraction (short IDs like `n-123abc`)
- ✅ List items extraction from commands
- ✅ Limit extraction from recent commands
- ✅ Tag extraction from append commands
- ✅ Handling missing entities gracefully
- ✅ Handling empty entity values

**Flow State Edge Cases (7 tests):**
- ✅ Skip note body flow (creating note without body)
- ✅ Cancel note body flow (aborting note creation)
- ✅ Interrupt note flow with different command
- ✅ Empty response in note flow
- ✅ Multiple items in list flow (adding items in batches)
- ✅ List flow with empty items (ending flow without adding items)
- ✅ Flow timeout simulation (10-minute timeout logic)

**Error Handling Tests (9 tests):**
- ✅ Invalid entry reference handling
- ✅ Append to non-existent entry
- ✅ Add tags to non-existent entry
- ✅ Toggle item on non-existent list
- ✅ Invalid item index handling
- ✅ Missing user_id defensive handling
- ✅ Very long title handling
- ✅ Special characters in titles/bodies
- ✅ Malformed entry reference handling

**Verified Working (Discord Testing):**
- ✅ Note creation (`!n`, `!note`) with and without body
- ✅ Recent entries view (`!recent`)
- ✅ Show entry (`!show <id>`)
- ✅ Note body flow (prompts, Skip/Cancel buttons)
- ✅ List creation flow (prompts, item collection)
- ✅ List end command (`!end`) - **Fixed and verified**

**Running Automated Tests:**
```powershell
# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Install notebook module (if not already installed)
pip install -e .

# Run all notebook tests
python -m pytest tests/behavior/test_notebook_handler_behavior.py -v

# Run specific test category
python -m pytest tests/behavior/test_notebook_handler_behavior.py::TestNotebookHandlerBehavior -v

# Run with coverage
python -m pytest tests/behavior/test_notebook_handler_behavior.py --cov=notebook --cov=communication.command_handlers.notebook_handler -v
```

#### Test Suite Status
**All Priority Testing Areas Covered** ✅

1. **Command Patterns** ✅ **COMPLETE**
   - ✅ All bang command variations tested (`!n`, `!nn`, `!newn`, etc.)
   - ✅ Slash command conversion tested (`/n` → `!n`)
   - ✅ Natural text recognition tested
   - ✅ Multi-line input tested (newline-separated bodies/items)
   - ✅ Flow states tested (note body prompt, list items prompt)
   - ✅ Flow keywords tested (`skip`, `end`, `cancel`)

2. **Flow State Management** ✅ **COMPLETE**
   - ✅ Note body flow: title-only → prompt → body collection → skip/cancel
   - ✅ List items flow: title-only → prompt → items collection → `!end`
   - ✅ Flow clearing when commands are sent
   - ✅ Flow timeout simulation (10-minute expiration)

3. **Command Generalization** ✅ **COMPLETE**
   - ✅ Commands that work for both tasks and notes (`!show`, `!append`, `!tag`, `!search`, `!inbox`)
   - ✅ Task-specific commands (covered in task handler tests)
   - ✅ Note-specific commands (`!pin`, `!archive`)

4. **Data Operations** ✅ **COMPLETE**
   - ✅ CRUD operations (create, read, update, delete)
   - ✅ Tag normalization and validation
   - ✅ Search functionality
   - ✅ List operations (add item, toggle done, remove item)

5. **Edge Cases** ✅ **COMPLETE**
   - ✅ Invalid entry references
   - ✅ Empty inputs
   - ✅ Very long entries
   - ✅ Special characters in titles/bodies
   - ✅ Missing entities
   - ✅ Malformed references

### Implementation Remaining

#### High Priority
1. ~~**Comprehensive Test Suite**~~ ✅ **COMPLETED** - Comprehensive test suite with 54 tests covering all implemented functionality, entity extraction, flow state edge cases, and error handling
2. ~~**Validation System**~~ ✅ **COMPLETED** - Implemented comprehensive validation system with proper separation of concerns (general validators in `core/user_data_validation.py`, notebook-specific in `notebook/notebook_validation.py`), error handling compliance, and extensive test coverage (28 unit validation + 10 unit error handling + 13 integration tests)
3. ~~**Set Entry Body Command**~~ ✅ **COMPLETED** - Added `!set`, `!replace`, `!update` command patterns to trigger `set_entry_body`
4. ~~**Create Journal Command**~~ ✅ **COMPLETED** - Added `!j`, `!journal`, `!newjournal`, `!createjournal` and other aliases
5. ~~**Short ID Format**~~ ✅ **COMPLETED** - Removed dash from short ID format (`n123abc` instead of `n-123abc`) for easier mobile typing, maintained backward compatibility
6. ~~**TaskManagementHandler Deduplication**~~ ✅ **COMPLETED** - Consolidated duplicate `TaskManagementHandler` classes (see CHANGELOG_DETAIL.md for details)

#### Medium Priority
4. **Edit Sessions (Milestone 4)** - Implement `!edit` command with flow state
5. **Slash Command Registration** - Explicitly register notebook commands in `_command_definitions` for better discoverability

#### Low Priority
6. **Skip Integration (Milestone 5)** - Task skip tracking and notebook integration
7. **AI Extraction (Milestone 6)** - Natural language intent extraction

---

## Notes on future calendar/events
When you add calendar/event support:
- add new `Entry(kind="event")` with event-specific fields
- create a new top-level `events/` feature only if it grows beyond simple entries
- reuse tags/group/search/persistence exactly as notebook does

This roadmap keeps that door open without forcing the decision now.
