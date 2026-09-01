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

### 2026-09-01 - Completing a task no longer leaves a duplicate active copy **COMPLETED**
- `complete_task` and `restore_task` now write active and completed lists in one save, so a leftover task cannot reappear as still active after a successful complete.
- "That" after completing a different recent task still resolves to no task, instead of the leftover.

### 2026-08-31 - Google Health coverage for connect, auth, and notices **COMPLETED**
- Unit tests now cover OAuth connect/refresh, user settings, health JSON recovery, reconnect notices, and the Google Health HTTP client (pagination, rollup fallback, parsers, sleep/steps/active-minute merges).
- Google Health tests: 156 passed; `integrations` measured at 95% on that set. `client.py` is 99%; remaining gap is mostly `signal_builder.py` / `sync_manager.py` edge cases.
- Coverage cache no longer treats a selective product-domain run as a full snapshot: missing cache does not imply a full run, tool/config invalidation keeps the merge base, and 0% `development_tools` from unrun tests is merged back from the prior JSON.
- Coverage pytest waits ignore spurious Windows SIGINT/control events (same multi-tap stop as audit: 5 Ctrl+C within 2s). A stray console event no longer aborts `--dev-tools-only` at 0%. Dev-tools coverage tests now stub `_run_pytest_wait`; changelog ASCII quotes restored.

### 2026-08-30 - Create hub splits tasks from notes **COMPLETED**
- Discord `create` hub first row is Call, Clean, Forms, Custom task; second row is green notes. Meds/Appt stay on `list task templates`.
- Call and Clean forms prefill title `Call` / `Clean` with due `this week`.
- Copy is "First row starts a task." (green note buttons are unlabeled).

### 2026-08-30 - Task CRUD multi-select and completed-task delete **COMPLETED**
- Completed-tab **Delete Permanently** failed because `delete_task` only searched active tasks.
- Task tables now allow Ctrl/Shift multi-select; delete, restore, and complete apply to all selected rows.
- Category column is filled in both tables.

### 2026-08-29 - Discord appointment form submit no longer fails silently **COMPLETED**
- `create` hub copy labels the first row as new-task buttons and green as notes; the template keyword list is not repeated under the buttons.
- Task-list Show More now attaches the picker dropdown on later pages (`deliver_handler_response` resolves `interaction_view`).
- Create-hub nested modal `__init__` methods use `@handle_errors`; function registry regenerated.
- Create-hub task modals use a stable `create_hub_modal_task:{template}` custom id, `timeout=None`, and the Discord interaction router handles `modal_submit` even after restart or the in-memory 3-minute modal timeout.

### 2026-08-28 - Chat follow-ups can update the task you just mentioned **COMPLETED**
- `make that due tomorrow`, `that's urgent`, and `mark that done` apply to the recently mentioned or created task.
- Ambiguous "that" asks which task; it does not jump to a leftover task after you complete a different one.
- Thinking-out-loud (`i should...`, `i gotta...`) asks before saving; `dont forget to` still creates immediately.
- Bot copy says "task list", not "list", so tasks stay distinct from notebook lists.
- After a which-task prompt, a number or name applies the remembered update (`1.` no longer gets the unclear-chat reply).
- Notes added during the due-date follow-up stay on that task and keep the due-date buttons.
- Function registry regenerated; yes/no offer matchers folded into `_matches_task_offer_reply`.

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

## Archive Notes
Older detailed entries live in `development_docs/changelog_history/` and remain the historical source of truth. Use [CHANGELOG_DETAIL.md](../development_docs/CHANGELOG_DETAIL.md) for the latest detailed entries and the archive folder for month-split history.

