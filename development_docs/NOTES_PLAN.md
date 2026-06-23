# MHM Notebook Roadmap

> **File**: `development_docs/NOTES_PLAN.md`  
> **Audience**: Human Developer & AI Collaborators  
> **Purpose**: Current roadmap for the notebook feature  
> **Style**: Actionable, checklist-focused, concise  
> **Last Updated**: 2026-05-17  
> **Current Evidence**: Reviewed against `code_snapshot_project_root_2026-05-16_17-49-25.md`  
> **Parent**: [PLANS.md](PLANS.md)  
> This plan is subordinate to `development_docs/PLANS.md` and must remain consistent with its standards and terminology.

---

## 1. Current Use / Fit

Notebook is intended to become a primary daily-capture tool in MHM, especially from Discord on a phone.

Current priority is no longer basic implementation. The core feature exists. The current priority is making it easier and more reliable to use day-to-day:

1. Validate and polish pagination / Show More behavior in live Discord.
2. Improve command discovery and notebook help text.
3. Make phone-friendly editing practical.
4. Clarify rough edges around group commands, inbox behavior, and visual distinctions.
5. Defer AI extraction, slash-command expansion, and database/FTS work until the AI/command parsing or storage architecture is ready for that larger change.

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
- `communication/command_handlers/notebook_handler.py` handles notebook interactions and calls `notebook/notebook_service.py` rather than doing all business operations directly.

The old plan sections that said to create these modules have been removed because they are completed.

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
- `group`
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
- `group` exists on notebook entries and also exists in the task update field set, so future shared organization work should not assume tasks lack groups.

### Current Inbox Semantics

Current implementation: inbox means **active, untagged notebook entries updated within the last 30 days**.

It is **not** currently based on missing group. It is **not** currently “no group and no tags.”

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
- try `!archived`, `!recent`, `!inbox`, shorter keywords, `!t <tag>`, or `!group <name>` as appropriate

The old “search feedback not implemented” task is complete. Remaining search work is polish, not core implementation.

### Current Pagination / Show More State

Current implementation:

- `core/pagination.py` defines `PageRequest`, `PageResult`, and `paginate_items()`.
- Notebook list/search handlers return channel-neutral pagination metadata in `rich_data["pagination_actions"]`.
- Discord converts pagination metadata into `Show More` buttons with hidden payloads containing the original intent and next offset.
- Discord button handling can route a pagination payload directly back to the appropriate interaction handler.

The old “Show More button loses pagination state” item appears to be addressed in code. Remaining work is live Discord validation and UX polish.

---

## 3. Current Supported Capability Areas

This is a high-level capability map, not a complete alias list. Exact command aliases belong in the parser/handler tests and help text.

### Capture

- Create quick notes.
- Create titled notes.
- Create notes with title and description split by supported separators.
- Create quick notes in the `Quick Notes` group.
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
- List by group.

### Modify

- Append to an entry.
- Replace/set entry description.
- Add tags.
- Remove tags.
- Set group.
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

**Status**: Active  
**Priority**: High

**Problem**: Pagination appears implemented in code, but it still needs live Discord validation and any UX polish found during manual use.

**Tasks**:

- [ ] Manually test `Show More` from Discord for:
  - [ ] `!s <query>`
  - [ ] `!recent`
  - [ ] `!pinned`
  - [ ] `!inbox`
  - [ ] `!archived`
  - [ ] `!t <tag>`
  - [ ] `!group <group>`
- [ ] Confirm the second page preserves the original intent, query/filter, limit, and offset.
- [ ] Confirm repeated Show More clicks continue paging correctly.
- [ ] Confirm button payload cache behavior does not break after multiple notebook interactions.
- [ ] Add or update behavior tests for any bug found during live validation.

**Acceptance**:

- Show More works from Discord without requiring the user to rerun the original command.
- If no more entries remain, no stale Show More button appears on the new response.

---

### 4.2 Improve notebook command discovery

**Status**: Active (help text shipped 2026-06-22; live validation ongoing)  
**Priority**: High

**Problem**: Notebook has many useful commands, but discovery is weak. `NotebookHandler.get_help()` is currently too short to serve as the main user guide.

**Tasks**:

- [x] Add or improve `!help notebook` / notebook-specific help output.
- [x] Group commands by capture, retrieve, modify, lists, and organization.
- [x] Include examples for the commands most useful on a phone.
- [x] Mention current inbox semantics in help text.
- [x] Mention group vs tag distinction briefly.
- [x] Add tests for the help/discovery output.

**Acceptance**:

- A user can discover basic notebook use without reading developer docs.
- Help text is short enough for Discord but complete enough to be useful.

---

### 4.3 Implement phone-friendly edit sessions

**Status**: Planned  
**Priority**: Medium

**Problem**: Replacing long note content from a phone is awkward. `!set` / replace-style commands exist, but they are not a comfortable editing flow for longer entries.

**Proposed behavior**:

- `!edit <id_or_title>` starts an edit session.
- The next non-command message replaces the entry description.
- `!cancel` cancels the edit session.
- Optional later mode: append mode vs replace mode.

**Tasks**:

- [ ] Define edit-session state model and timeout.
- [ ] Decide whether state belongs in the existing conversation flow manager or notebook-specific flow handling.
- [ ] Implement replace flow first; defer append/review modes unless needed.
- [ ] Add skip/cancel handling.
- [ ] Add tests for timeout, cancel, valid replacement, and invalid entry reference.

**Acceptance**:

- Long note replacement can be done from Discord without packing the entire replacement into one command line.

---

### 4.4 Resolve group command ambiguity

**Status**: Active  
**Priority**: Medium

**Problem**: Group commands can mean either:

- list entries in a group: `!group <group>`
- set an entry's group: `!group <entry_ref> <group>`

Single-word groups and short entry references can be ambiguous.

**Tasks**:

- [ ] Review parser behavior for `!group home`, `!group n123abc home`, and title-based references.
- [ ] Decide whether to keep dual-use `!group` or introduce a clearer alias such as `!setgroup <entry_ref> <group>`.
- [ ] Add ambiguity tests.
- [ ] Improve error/help text when a group command is ambiguous.

**Acceptance**:

- Listing a group and setting an entry group are both predictable.
- Ambiguous input does not silently do the wrong thing.

---

### 4.5 Improve journal visual distinction

**Status**: Planned  
**Priority**: Low / Medium

**Problem**: Journal entries can look too much like regular notes in list/show output.

**Tasks**:

- [ ] Make journal entries visually distinct in formatted responses.
- [ ] Consider showing `submitted_at` or a date label for journal entries.
- [ ] Add formatting tests.

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
- bulk group assignment

**Rule**: Do not implement bulk operations until normal single-entry notebook use is smooth and command ambiguity is resolved.

---

## 5. Technical Backlog

### 5.1 Centralize external short IDs

**Status**: Planned  
**Priority**: Medium

**Problem**: Notebook short ID formatting exists, task short IDs exist separately or partially, and the system will likely need a shared external ID strategy.

**Tasks**:

- [ ] Add `core/ids.py` or equivalent shared helper.
- [ ] Centralize short ID creation/parsing.
- [ ] Support notebook prefixes (`n`, `l`, `j`) consistently.
- [ ] Review task short ID behavior and align only where it makes sense.
- [ ] Add collision/ambiguity tests.

**Acceptance**:

- Notebook and task ID display/lookup conventions are clear and not duplicated across handlers.

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

### 5.4 Add notebook entries to AI context later

**Status**: Deferred  
**Priority**: Medium later, not now

Current concern:

- AI/chat context work needs a broader overhaul.
- Notebook entries can contain sensitive personal content.
- Adding notebook content to AI context should be deliberate, scoped, and user-controlled.

Future tasks:

- [ ] Decide what notebook content, if any, can enter AI context.
- [ ] Add opt-in or clear config for notebook context inclusion.
- [ ] Start with small summaries or recent pinned entries, not full notebook dumps.
- [ ] Add tests for privacy boundaries and context size.

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
- Reuse tags, groups, search, and pagination where practical.

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
- Implement recent/search/show/append/set/tag/untag/pin/archive/group/inbox/tag/group/archive views.
- Implement list item add/done/undo/remove operations.
- Add search no-result feedback.
- Add channel-neutral pagination metadata and Discord Show More payload rendering.

Historical details belong in `CHANGELOG_DETAIL.md` / `AI_CHANGELOG.md`, not in this active roadmap.
