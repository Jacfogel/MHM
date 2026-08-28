# AI Changelog - Brief Summary for AI Context
> **File**: `ai_development_docs/AI_CHANGELOG.md`
> **Audience**: AI collaborators (Cursor, Codex, etc.)
> **Purpose**: Lightweight summary of recent changes
> **Style**: Concise, essential-only, scannable
> **See [development_docs/CHANGELOG_DETAIL.md](../development_docs/CHANGELOG_DETAIL.md) for the full history**

## Overview
This file is a lightweight summary of recent changes for AI collaborators. It provides essential context without overwhelming detail. For the complete historical record, see [CHANGELOG_DETAIL.md](../development_docs/CHANGELOG_DETAIL.md).

## How to Update This File
1. Add a new entry at the top summarising the change in 2-4 bullets.
2. Keep the title short: "YYYY-MM-DD - Brief Title **COMPLETED**".
3. Reference affected areas only when essential for decision-making.
4. Move older entries to archive\AI_CHANGELOG_ARCHIVE.md to stay within 10-15 total.
Template:
```markdown
### YYYY-MM-DD - Brief Title **COMPLETED**
- Key accomplishment in one sentence
- Extra critical detail if needed
- User impact or follow-up note
```
Guidelines:
- Keep entries concise
- Focus on what was accomplished and why it matters
- Limit entries to 1 per chat session. Exceptions may be made for multiple unrelated changes
- Maintain chronological order (most recent first)
- REMOVE OLDER ENTRIES when adding new ones to keep context short
- Target 10-15 recent entries maximum for optimal AI context window usage

## Recent Changes (Most Recent First)

### 2026-08-28 - Chat follow-ups can update the task you just mentioned **COMPLETED**
- `make that due tomorrow`, `that's urgent`, and `mark that done` apply to the recently mentioned or created task.
- Ambiguous "that" asks which task; confirmations stay calm instead of teaching command syntax.
- Live LM Studio tone review is still remaining.

### 2026-08-27 - Tasks can store web links **COMPLETED**
- Tasks keep http(s) URLs in a `links` field, with add/remove commands and create-time URL capture.
- Labels are optional (`add the portal link to the dentist task: https://...`).
- Nested URL-strip callback lifted to `_replace_url_match` (docstring + error handling); function registry refreshed.
- File/image attachments are still deferred.

### 2026-08-26 - Chat follow-ups can create the task you just described **COMPLETED**
- Action planner includes up to two recent user turns so "yeah add that as a task" can reuse a title you already said.
- Titles still must match those recent words (example titles like "pack hiking bag" stay blocked).
- Compact planning prompt is unchanged besides that short recent-turn block.

### 2026-08-26 - Discord task templates open a prefilled form **COMPLETED**
- Create-hub template buttons open a prefilled modal; submit keeps template defaults (recurrence, priority, tags).
- `list task templates` now attaches the same Discord button row as `create`.
- Relative due phrases from the form (`tomorrow at 2pm`) parse as overrides.

### 2026-08-26 - Nightly health-sync and coverage-cache test isolation **COMPLETED**
- Health sync/schedule tests resolve the factory UUID and patch `is_google_health_testing_mode` instead of setting `MHM_TESTING=0`.
- Dev-tools coverage cache no longer treats empty mtime scans as changed; config path is the project under test.
- Schedule reads no longer re-enter `get_user_data("schedules")` during finalize, and no longer call `ensure_all_categories_have_schedules` on read (that wrote `Motivational Message Default` over Evening after cache clear). `schedule_categories` keeps a `categories` map even with extra envelope keys.
- `safe_json_read` uses the locked handle (Linux double-open under flock returned `{}`).
- Nightly `--basetemp` under `tests/data` no longer trips those node IDs.

### 2026-08-26 - Everyday task phrasing creates and completes real work **COMPLETED**
- Parser now treats `i should...`, `dont forget to...`, `mark X done`, `what is on my list`, `add X to my list`, `i gotta...`, `i still need to...`, `i'm supposed to...`, `don't let me forget to...`, `make sure i...`, `show my list`, `what's left`, `cross off X`, and `show overdue tasks` as real task commands.
- Title/ID cleanup: `create a task for laundry` keeps title `laundry`; `I completed the dentist task` looks up `dentist`; `add a note to the dentist task: ...` appends a task note instead of making a notebook note.
- Notebook capture: `jot down...`, `write down...`, `make a note of...`, `note to self...`, `remember that...`, `add a note about...`, `keep in mind that...`, `write this down...`, and `don't let me forget that...` save a note immediately instead of asking for a body. `show my notes` lists notes instead of looking up an entry named "my notes".
- Command-list parity: AI prompts/catalog/planning summaries use the live parser intent set; `ACTION: create note` and `start check-in` canonicalize through `command_registry` (the only AI module allowed to import communication). Help/examples updated. Live Discord feel-check is still remaining.

### 2026-08-25 - Split custom-question dialog into form, template, and save jobs **COMPLETED**
- `_show_question_dialog` is now an orchestrator (821 -> 218 AST nodes); form, template picker, and save are separate helpers.
- Combo population, category labels, and the saved payload are independently testable.
- Add/edit custom-question behavior is unchanged.

### 2026-08-25 - Check-in settings min/max and question-list glitches **COMPLETED**
- Maximum questions can be lowered below the current minimum; minimum follows (the max spinbox is no longer locked to current min).
- Adding/deleting custom questions reuses the scroll-area layout instead of creating a second orphaned layout that left the list blank.
- Helper/unit coverage for bounds and layout reuse; full widget tests pass with `MHM_QT_UI_FORCE=1`.
- `ensure_vbox_layout` raises `UserInterfaceError` (not `TypeError`) when a non-vbox layout is already installed.

### 2026-08-25 - v2 envelopes in memory for account/preferences/schedules **COMPLETED**
- `get_user_data` account/preferences/schedules now return the same v2 envelopes as on disk; `core/schemas.py` is gone.
- Use `schedule_categories()` for category maps and `account_extra()` for metadata extras; wrap is idempotent (no empty-`categories` wipe).
- Phrase settings (`natural_language_defaults`) persist on the preferences envelope.
- Period wrapping is in `schedule_period_normalize.py` (breaks the `profile_v2_io` / `schedule_document_defaults` import cycle). Lint/type cleanup + docs regen for registry/path drift.
- Full `python run_tests.py`: 5181 passed. Headless restart succeeded. Docs/path-drift clean; ruff/pyright PASS.

### 2026-08-23 - Map project-wide manual testing checklist to real tests **COMPLETED**
- MANUAL_TESTING_GUIDE section 10 maps startup/UI/schedule/email/health/restart items to pytest; leftovers are in `tests/behavior/test_manual_*.py`.
- Task reminders skip a second send when `reminder_sent` is already true, and that flag now persists.
- Live leftovers: inbox, OAuth, visual layout, AI tone. Tray and snooze are N/A.

### 2026-08-23 - Map Discord checklist items to real tests **COMPLETED**
- Every MANUAL_DISCORD_TEST_GUIDE item maps to a real pytest; leftovers are in `tests/behavior/test_discord_manual_checklist.py`.
- Fixed `toggle_list_item_undone` (`done=False` kwarg) and extracted `/start` DM-disabled coverage.
- Live Discord is visual/tone only; run the mapped pytest files after Discord changes.
- Follow-up: path-drift now uses repo-root test paths; Pyright on the new checklist file is clean.
- Follow-up: coverage-cache scratch tests inject the built-in domain map (xdist isolation); pip floor is 26.2 for PYSEC-2026-3721.

### 2026-08-23 - Remove placeholder and always-pass tests **COMPLETED**
- Deleted Discord/UI automation stub files and `debug_file_paths.py` (they only asserted True).
- Converted remaining `assert True` tests to real checks; factory demo fallbacks now fail instead of hiding lookup bugs.
- Policy guard `test_no_assert_true_placeholders` keeps new placeholders out.
- Typed the helper as `ast.Module` so the audit Pyright warning is gone.
- Fast interaction-manager helper no longer leaks `AI_ACTION_PLANNER_ENABLED=False`; ambiguous-task journey enables the planner via monkeypatch.
- Added the missing `unit` marker on the v2 envelope schedule-cache validation test.

### 2026-08-22 - Automated AI user journeys replace safety manual checks **COMPLETED**
- Mocked pytest journeys in `tests/behavior/test_ai_user_journeys.py` cover false-CRUD sanitization, create-task persistence, ambiguous-task clarification, check-in honesty, disabled-task limits, and numeric-only input.
- Live suite category 18 (`tests/ai/test_ai_live_journeys.py`) runs the same contracts against LM Studio and FAILs automatically instead of PARTIAL.
- Path-drift fix: `TESTING_GUIDE.md` links that file as `ai/test_ai_live_journeys.py` so doc-sync can resolve it.
- Manual AI review is tone/phrasing only. Live suite stays out of `run_tests.py`.

### 2026-08-22 - Stop Discord send tests waiting 10s on an empty queue **COMPLETED**
- Three Discord send tests now seed `_result_queue` instead of waiting out the 10s poll.
- `run_tests.py` no longer pauses LM Studio by default (that combo hung the full suite at 98%).
- Autouse fixture blocks leaked LM Studio HTTP; chatbot tests mock `_call_lm_studio_api`.

### 2026-08-22 - One shared check-in analysis core **COMPLETED**
- Chat, fallback, and the analytics UI now use `checkins/analysis.py` for breakfast/mood/energy/wellness.
- The envelope stores that analysis once; contextual chat builds the envelope once and reuses it.
- Wellness no longer invents a 50 for missing sleep/habits; named scores still need 3 check-ins.

## Archive Notes
Older detailed entries live in `development_docs/changelog_history/` and remain the historical source of truth. Use [CHANGELOG_DETAIL.md](../development_docs/CHANGELOG_DETAIL.md) for the latest detailed entries and the archive folder for month-split history.

