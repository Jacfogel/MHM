# MHM Notebook Roadmap

> **File**: `development_docs/NOTES_PLAN.md`  
> **Audience**: Human Developer & AI Collaborators  
> **Purpose**: Current roadmap for the notebook feature  
> **Style**: Actionable, checklist-focused, concise  
> **Last Updated**: 2026-09-24  
> **Current Evidence**: Validated against live codebase 2026-09-24 (notebook package, Discord handler, website notes page, AI context)  
> **Parent**: [PLANS.md](PLANS.md)  
> This plan is subordinate to `development_docs/PLANS.md` and must remain consistent with its standards and terminology.

---

## 1. Current Use / Fit

Notebook is a daily-capture tool on Discord and on the website notebook page.

The core feature exists. The model notebook slice is titles of recent entries, pinned entries, and a short summary when an entry has no title. Home shows a few of those titles under the capture box.

1. Pagination / Show More behavior is covered by pytest (`test_paginated_notebook_views_include_pagination_action`, `test_recent_pagination_exhausts_without_stale_show_more`). Optional live Discord is visual only.
2. Command discovery help text shipped 2026-06-22; `|` separators aligned 2026-07-29. A live Discord spot-check is optional.
3. Phone-friendly `!edit` sessions shipped 2026-07-29 (replace flow + cancel/timeout).
4. Notebook groups were removed 2026-09-24. Tags remain. Journal visuals shipped 2026-06-26.
5. Defer bulk organization, database/FTS search, and event entries.

---

## 2. Current State

### Implemented / Current

The notebook feature is now implemented as a real feature package, not just a proposed module layout.

Current notebook modules:

- `notebook/__init__.py`
- `notebook/notebook_data_handlers.py`
- `notebook/notebook_data_manager.py`
- `notebook/notebook_schemas.py`
- `notebook/notebook_service.py`
- `notebook/notebook_validation.py`

Current shared support:

- `core/tags.py` provides shared tag normalization and validation.
- `core/pagination.py` provides channel-neutral pagination helpers.
- `core/ids.py` provides shared external short-ID create/parse/display (`t`/`n`/`l`/`j`, ...).
- `communication/command_handlers/notebook_handler.py` handles notebook interactions and calls `notebook/notebook_service.py` rather than doing all business operations directly. Multi-step create/edit prompts start through public `ConversationManager` APIs (`start_note_body_flow`, `start_list_items_flow`, `start_journal_body_flow`, `start_entry_edit_flow`); the handler does not write private flow state.

The old plan sections that said to create these modules have been removed because they are completed.

The website notebook is a second current surface: `website/notes.html`, `website/notes.js`, and `GET`/`POST`/`PATCH /api/notes` in `core/web_account_service.py`. It creates notes, journal entries, and lists; searches; filters by tag; and offers Active, Pinned, Inbox, and Archived views. Edit covers title, description, list items, tags, pin, and archive. It does not use groups.

### Current Entry Model

The current Pydantic model lives in `notebook/notebook_schemas.py`.

Current entry kinds:

- `note`
- `list`
- `journal_entry`

Current important fields:

- `id`
- `short_id`
- `kind`
- `title`
- `description`
- `category`
- `status` (`active`, `archived`, `deleted`)
- `items`
- `tags`
- `pinned`
- `submitted_at`
- `source`
- `linked_item_ids`
- `created_at`
- `updated_at`
- `archived_at`
- `deleted_at`
- `metadata`

Notes:

- Use `description`, not `body`, when referring to the current schema.
- Use `journal_entry`, not `journal`, when referring to the current schema value.
- Archived/deleted state is represented by `status` plus timestamps, not by an `archived: bool` field.
- Notes and tasks do not have a group field. Tags are the labels.

### Current Inbox Semantics

Current implementation: inbox means **active, untagged notebook entries updated within the last 30 days**.

Keep this behavior unless there is a deliberate product decision to change it.

### Current Search Semantics

Current implementation:

- case-insensitive substring search
- searches active notebook entries only
- searches title, description, and list item text
- excludes archived entries
- sorts by `updated_at` descending when possible

Search no-result feedback now exists and explains:

- search is substring-based
- archived entries are excluded
- try `!archived`, `!recent`, `!inbox`, shorter keywords, or `!t <tag>` as appropriate

The old “search feedback not implemented” task is complete. Remaining search work is polish, not core implementation.

### Current Pagination / Show More State

Current implementation:

- `core/pagination.py` defines `PageRequest`, `PageResult`, and `paginate_items()`.
- Notebook list/search handlers return channel-neutral pagination metadata in `rich_data["pagination_actions"]`.
- Discord converts pagination metadata into `Show More` buttons with hidden payloads containing the original intent and next offset.
- Discord button handling can route a pagination payload directly back to the appropriate interaction handler.

The old “Show More button loses pagination state” item is covered by pytest. Remaining work is optional live visual polish.

---

## 3. Current Supported Capability Areas

This is a high-level capability map, not a complete alias list. Exact command aliases belong in the parser/handler tests and help text.

### Capture

- Create quick notes.
- Create titled notes.
- Create notes with title and description split by supported separators.
- Create lists.
- Create journal entries.

### Retrieve

- Recent entries.
- Recent notes.
- Show one entry by full UUID, short ID, or title when resolvable.
- Search entries.
- List pinned entries.
- List inbox entries.
- List archived entries.
- List by tag.

### Modify

- Append to an entry.
- Replace/set entry description.
- Add tags.
- Remove tags.
- Pin/unpin.
- Archive/unarchive.

### List Operations

- Add list item.
- Mark list item done.
- Mark list item not done.
- Remove list item.

---

## 4. Active Backlog

### 4.1 Validate and polish live Discord pagination

**Status**: Automated (2026-08-23); optional live visual check  
**Priority**: Low

**Problem**: Pagination metadata and Discord Show More rendering are implemented. Behavior is covered by pytest. See `tests/MANUAL_DISCORD_TEST_GUIDE.md` §6.2.

**Tasks**:

- [x] `Show More` preserves intent/filter for `!s`, `!recent`, `!pinned`, `!inbox`, `!archived`, and `!t <tag>` (`test_paginated_notebook_views_include_pagination_action`). Group filters were removed 2026-09-24.
- [x] Second page preserves query/filter/limit/offset (same test)
- [x] Repeated Show More until exhausted drops the stale button (`test_recent_pagination_exhausts_without_stale_show_more`)
- [ ] Optional: glance at the real Discord client if button styling or expired-button UX changes

**Acceptance**:

- Show More works without requiring the user to rerun the original command.
- If no more entries remain, no stale Show More button appears on the new response.

---

### 4.2 Improve notebook command discovery

**Status**: Active (help text shipped 2026-06-22; polish / accuracy remaining)  
**Priority**: Medium

**Problem**: Core help discovery is in place via `NOTEBOOK_HELP_TEXT` / `NotebookHandler.get_help()` and `help notebook`. Title/body `|` separators and optional append `|` now match help examples (2026-07-29). Live Discord confirmation that users can find commands from help alone is still useful.

**Tasks**:

- [x] Add or improve `!help notebook` / notebook-specific help output.
- [x] Group commands by capture, retrieve, modify, lists, and organization.
- [x] Include examples for the commands most useful on a phone.
- [x] Mention current inbox semantics in help text.
- [x] Mention that tags are labels. Groups were removed 2026-09-24.
- [x] Add tests for the help/discovery output.
- [x] Align help/examples with real separators: parser accepts newline, `|`, and `:` for title/body; append strips optional leading `|` (2026-07-29).
- [x] Everyday capture phrasing (2026-08-26): `jot down...`, `write down...`, `make a note of...`, `note to self...`, `remember that...`, `add a note about...`, `keep in mind that...`, `write this down...`, `put this in my notes...`, `don't let me forget that...` save the thought immediately instead of prompting for a body. `show my notes` lists notes.
- [ ] Spot-check live Discord that `help notebook` / `examples notebook` are discoverable and accurate.

**Acceptance**:

- A user can discover basic notebook use without reading developer docs.
- Help text is short enough for Discord but complete enough to be useful.
- Documented separators and examples match parser behavior.

---

### 4.3 Implement phone-friendly edit sessions

**Status**: Completed (2026-07-29)  
**Priority**: Medium

**Problem**: Replacing long note content from a phone is awkward. One-shot `!set` still works; longer edits needed a multi-message flow.

**Shipped behavior**:

- `!edit <short_id>` / `!editn <ref>` / `!edit note <title>` / `!edit entry <title>` starts `FLOW_ENTRY_EDIT`.
- The next non-command message replaces the entry description via `replace_entry_body`.
- `cancel` / `skip` / timeout clear the flow without writing.
- Lists are rejected (use list item commands).
- Optional later: append mode vs replace mode (not started).

**Tasks**:

- [x] Define edit-session state model and timeout (reuse conversation flow; 10-minute `CONVERSATION_FLOW_TIMEOUT_MINUTES`).
- [x] Reuse conversation flow manager (`FLOW_ENTRY_EDIT` in `note_flow.py`).
- [x] Implement replace flow first; defer append/review modes unless needed.
- [x] Add skip/cancel handling (both abandon without write).
- [x] Add tests for timeout, cancel, valid replacement, and invalid entry reference.

**Acceptance**:

- Long note replacement can be done from Discord without packing the entire replacement into one command line.

---

### 4.4 Group commands

**Status**: Removed (2026-09-24)  
**Priority**: Done

Tasks and notes use tags. `!group` and `!setgroup` are gone from the parser, handler, stored entries, AI actions, and the website notes API. Do not restore them. Detail stays in Section 8.

---

### 4.5 Improve journal visual distinction

**Status**: Completed (2026-06-26)  
**Priority**: Low / Medium

**Problem**: Journal entries can look too much like regular notes in list/show output.

**Tasks**:

- [x] Make journal entries visually distinct in formatted responses (2026-06-26: journal label + submitted date in list/detail formatting).
- [x] Consider showing `submitted_at` or a date label for journal entries.
- [x] Add formatting tests.

**Acceptance**:

- Journal entries are clearly recognizable without making notebook output noisy.

---

### 4.6 Add bulk operations only after core use feels good

**Status**: Deferred  
**Priority**: Low

**Possible operations**:

- bulk tag
- bulk untag
- bulk archive

**Rule**: Do not implement bulk operations until normal single-entry notebook use feels smooth. Edit sessions and Show More behavior are covered in code and tests. Optional live Discord is visual only. Groups are not part of this work.

---

## 5. Technical Backlog

### 5.1 Centralize external short IDs

**Status**: Done  
**Priority**: Medium

**Problem**: Notebook short ID formatting exists, task short IDs exist separately or partially, and the system will likely need a shared external ID strategy.

**Tasks**:

- [x] Add `core/ids.py` or equivalent shared helper.
- [x] Centralize short ID creation/parsing.
- [x] Support notebook prefixes (`n`, `l`, `j`) and task prefix (`t`) consistently.
- [x] Review task short ID behavior and align only where it makes sense.
- [x] Add collision/ambiguity tests.

**Acceptance**:

- Notebook and task ID display/lookup conventions are clear and not duplicated across handlers.
- Shared helpers live in [`core/ids.py`](../core/ids.py); storage re-exports `generate_short_id` for compatibility.
- Notebook entry refs accept `n`/`l`/`j` (and bare hex); `t...` is a shared short ID but not a notebook entry ref.

---

### 5.2 Keep search simple unless usage proves otherwise

**Status**: Deferred  
**Priority**: Low

Current substring search is acceptable for JSON storage.

Do not create `notebook_search.py`, SQLite, or FTS just because the old roadmap mentioned them. Revisit only if one of these becomes true:

- search gets slow with real data
- search ranking becomes important
- fuzzy matching is needed
- notebook and tasks need unified search
- storage moves to SQLite anyway

---

### 5.3 Extract more reusable item organization helpers only when duplication is real

**Status**: Deferred  
**Priority**: Low / Medium

Old plan proposed:

- `core/item_filters.py`
- `core/item_tags.py`
- `core/item_groups.py`

Do not add these yet just to satisfy the old roadmap. Extract them only when tasks, notebook, and future events are clearly duplicating behavior.

Current reusable helpers already in place:

- `core/tags.py`
- `core/pagination.py`

---

### 5.4 Fit notebook content in the model context

**Status**: Completed (2026-09-25)  
**Priority**: Medium

This is a context-size limit, the same kind of constraint as listing action names only so a 2048-token model can hold the prompt. It is not a privacy setting, and it does not add an opt-in toggle.

**Decision (2026-09-24)**: The notebook slice sent to the model is titles of recent entries and pinned entries. An entry with no title contributes a short summary instead of a title. Full descriptions, list items, and metadata stay out so the slice stays small.

**Current code**: `ai/context/service.py` `_build_notebook_context` sends up to 10 recent entries and up to 10 pinned entries. Each item is a title, or an 80-character summary when the title is missing. The prompt line lists those labels. Full descriptions stay out. Home shows up to five of those titles under the capture box.

**Tasks**:

- [x] Include a bounded recent-notebook slice in AI context.
- [x] Decide the default: recent titles, pinned entries, and a short summary when the title is missing.
- [x] Replace the full-entry dump with that smaller slice (2026-09-25).
- [x] Add tests that the model slice includes those titles, pinned entries, and untitled summaries, and that full descriptions stay out.
- [x] Show a few recent titles on Home after capture.

---

### 5.5 Revisit skip integration only if the product value is clear

**Status**: Deferred  
**Priority**: Low until clarified

Old idea: if a user repeatedly skips a task reminder, MHM could create a notebook entry tagged `blocker` / linked to the task, or ask “Capture why?”

Do not implement until the desired behavior is clearer.

Questions to answer first:

- Should skipped reminders create notebook entries automatically?
- Should the bot ask before capturing?
- Should this belong to Tasks, Notebook, or a shared reflection/check-in flow?
- How do we avoid making reminders feel more annoying?

---

## 6. Future Event / Calendar Direction

Notebook can eventually support event-like entries, but do not force that now.

Future options:

- Add `Entry(kind="event")` only if events are simple and notebook-like.
- Create a separate `events/` feature if events grow into scheduling, reminders, recurrence, attendees, or calendar sync.
- Reuse tags, search, and pagination where practical.

---

## 7. Validation Commands

Use focused tests while changing notebook behavior:

```powershell
python -m pytest tests/behavior/test_notebook_handler_behavior.py tests/unit/test_notebook_handler_edge_cases.py tests/unit/test_notebook_handler_pagination_formatting.py tests/unit/test_notebook_list_v2_round_trip.py tests/unit/test_notebook_service.py tests/unit/test_notebook_validation.py -q
```

Use broader validation before merging larger notebook/command-parser changes:

```powershell
python run_tests.py --mode development
python development_tools/run_development_tools.py audit --quick
```

Use full audit when a change touches command routing, shared core helpers, or persistence:

```powershell
python development_tools/run_development_tools.py audit --full
```

---

## 8. Completed / Removed From Active Roadmap

The following are no longer active roadmap tasks because the codebase now contains the relevant implementation:

- Create `notebook/` feature package.
- Create notebook schemas.
- Create notebook JSON data handlers.
- Create notebook data manager CRUD/query operations.
- Create notebook service/use-case layer.
- Create notebook command handler.
- Add shared tag normalization in `core/tags.py`.
- Add shared pagination helpers in `core/pagination.py`.
- Implement notes, lists, and journal entries.
- Implement recent/search/show/append/set/tag/untag/pin/archive/inbox views. Groups were removed 2026-09-24.
- Implement list item add/done/undo/remove operations.
- Add search no-result feedback.
- Add channel-neutral pagination metadata and Discord Show More payload rendering.
- Align title/body `|` separators with help text.
- Notebook groups, including `!group` and `!setgroup`, were removed 2026-09-24 from storage, Discord commands, AI actions, and the website notes API. Tags remain.
- Website notebook page: create, search, tag filter, pin, archive, and list-item editing.
- Phone-friendly `!edit` replace sessions (`FLOW_ENTRY_EDIT`).

Historical details belong in `CHANGELOG_DETAIL.md` / `AI_CHANGELOG.md`, not in this active roadmap.
