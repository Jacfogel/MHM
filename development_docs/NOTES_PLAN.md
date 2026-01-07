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
- `tags` (list[str])
- `group` (optional string; e.g., `work`, `health`, `home`)
- `pinned` (bool)
- `archived` (bool)
- `created_at`, `updated_at` (ISO timestamps)

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
- `!n <text>`  
  Create a quick note (no title).  
- `!n <title> | <body>`  
  Create note with title/body split.  
- `!recent [N]`  
  Show last N updated entries (notes + lists + journal).  
- `!show <id_or_title>`  
  Display one entry.  
- `!append <id_or_title> <text>`  
  Append text to entry body.  
- `!tag <id_or_title> <tags...>`  
  Add tags (supports `#tag`, `area:home`, etc.).  
- `!untag <id_or_title> <tags...>`  
  Remove tags.  
- `!s <query>`  
  Search entries (V0: substring).  
- `!pin <id_or_title>` / `!unpin <id_or_title>`  
- `!archive <id_or_title>` / `!unarchive <id_or_title>`

### V1 (lists)
- `!l new <title> [tags...]`
- `!l add <id_or_title> <item text>`
- `!l show <id_or_title>`
- `!l done <id_or_title> <item#>`
- `!l undo <id_or_title> <item#>`

### V2 (organization)
- `!group <id_or_title> <groupname>`
- `!group <groupname>` (show group view)
- `!t <tag>` (show tag view)
- `!pinned`
- `!inbox` (untagged, unarchived recent items)

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

## Notes on future calendar/events
When you add calendar/event support:
- add new `Entry(kind="event")` with event-specific fields
- create a new top-level `events/` feature only if it grows beyond simple entries
- reuse tags/group/search/persistence exactly as notebook does

This roadmap keeps that door open without forcing the decision now.
