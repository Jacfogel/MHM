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

### 2026-08-21 - Stop personalized message homework leaks **COMPLETED**
- Scheduled personalized Discord messages now run personalized post-process (the live path had been cleaning them as chat).
- Letter sign-offs, `[Your Name]`, and `Use Case` / `Scenario` writing-prompt dumps are cut before send.
- Follow-up: `_line_is_letter_signoff()` uses `@handle_errors` and is in the function registry.

### 2026-08-21 - Quiet missing personalized.json on startup **COMPLETED**
- Service startup no longer verifies AI-generated message categories (`personalized` has no library file).
- Rechecked v1/v2 ordering flakes: `audit --full` is green; a serial run of the listed files still fails 4 tests that pass alone.

### 2026-08-21 - Google Health dead refresh token logging **COMPLETED**
- Shared `is_google_health_testing_mode()` in `integrations/google_health/testing.py`; HTTP 400 refresh now logs reconnect-required instead of a generic status.
- Sync auto-pause still sends one reconnect notice; `last_error` uses the dead-token message.

### 2026-08-21 - Fix hourly status zeros and cleanup log routing **COMPLETED**
- Hourly `Service status` now counts real scheduler jobs, users, and active channels instead of missing APIs that always reported 0.
- Data-directory/auto-cleanup logs go to `file_ops.log`; backup deletions log at INFO with a removal summary.

### 2026-08-21 - Audit issue counts reach AI_PRIORITIES **COMPLETED**
- Documentation placeholder hits are read from `analyze_documentation` `details` and become Quick Wins ([TODO.md](../TODO.md) skipped).
- Function-registry extras (documented but not in the scan) are a Watch List item; missing rows stay Immediate Focus.
- Package-export "missing" now means `from package import Name` without `__all__`/re-export, not every public submodule name.
- Follow-up: bare TODO / [TODO.md](../TODO.md) mentions are not placeholders; registry extras scan `project.key_files` even when those paths are excluded. Code fences, inline backticks, and changelog files are also ignored.

### 2026-08-21 - Shared function scan for audit pipeline **COMPLETED**
- Audits parse the function-analysis file set once; `analyze_functions` runs first in Tier 2 and feeds patterns, decision support, duplicates, unused, facades, and refactor.
- `analyze_function_patterns` and `decision_support` moved out of `audit --quick` (Tier 1).
- Config caches use content hash after mtime; timestamp-only saves of `development_tools_config.json` no longer bust the test suite.
- Shared-scan unit tests skip path exclusions so pytest temp dirs are scanned.
- Standalone CLI for those tools still scans when no shared parse exists.

### 2026-08-19 - High-complexity function helpers where splits add value **COMPLETED**
- Notebook entity extraction, profile text, and the custom-question dialog now use named helpers for the real parsing/formatting/template jobs.
- Left constructor-style complexity scores and other dense single-job functions alone.
- Shared backup retention in `cleanup_old_backup_artifacts`; reminder HH:MM combo helpers; `parse()` keyword/intent lists moved to module constants.
- Per-user scheduler jobs, AI prompt wording (tasks, schedules, features, today check-in, reminders, mood), and due-date flow dates/times now share one implementation instead of copied policy.
- User-index lookup keys, command-response skip-line filters, and check-in "and a half" parsing each have one helper.
- `_format_profile_text` uses `@handle_errors` (Phase 1); stray decorator removed from gender formatting. Registry regenerated for the new helpers. Pyright warning on the exploding profile test stub is gone. Complexity queues skip `__init__`. Changelog ASCII: replaced Unicode arrows with `->`.

### 2026-08-18 - Notebook handler uses public conversation flow APIs **COMPLETED**
- Public `start_note_body_flow` / `start_journal_body_flow` / `start_list_items_flow` / `start_entry_edit_flow` (and `get_note_body_flow_data`) on the note-flow mixin.
- `notebook_handler` no longer writes `conversation_manager.user_states` or calls `_save_user_states`.
- Same coupling pattern as the Aug 11 check-in public API; user-visible notebook prompts unchanged.

### 2026-08-17 - Retire unused-imports analyzer (ruff F401) **COMPLETED**
- Removed `analyze_unused_imports` / `generate_unused_imports_report` and the unused-imports CLI/report; F401 is covered by `analyze_ruff`.
- Dropped dedicated Unused Imports sections from status/priorities/consolidated generators.
- Use `python -m ruff check --select F401` when you want an import-only lint pass.
- Same-session hygiene: pip-audit floors `aiohttp>=3.14.3` and `cryptography>=50.0.0`; leftover F401 on `test_tool_wrappers_cache_helpers.py`; demoted historical changelog hrefs to retired unused-imports paths to backticks.
- Doc-sync freshness watches both changelogs. Audit changelog trim/TODO classify now run before Tier 2 doc-sync so those edits do not leave a stale path-drift cache. Qualified changelog paths in DEVELOPMENT_TOOLS_GUIDE so path-drift no longer flags bare `AI_CHANGELOG.md` / `CHANGELOG_DETAIL.md`; converted those four paths to markdown links so unconverted-links is clean.

### 2026-08-16 - Audit cache: storage leaf, scoped doc-sync, legacy I/O skip **COMPLETED**
- `domain_dependencies.storage` is now a leaf so a storage-only edit does not walk through `core` and invalidate the whole product suite.
- Doc-sync freshness reads scoped `docs/jsons/scopes/<scope>/` results (the old flat `docs/jsons/` path always missed).
- Path-drift uses the same skip as the other doc subchecks; freshness ignores changelog/generated-report mtimes so audit trim does not force a 60s rescan.
- Legacy scan cache hits reuse stored matches without re-reading files; the INTENTIONAL LEGACY 10-line probe runs only on cache misses.

### 2026-08-16 - Module refactor size metrics **COMPLETED**
- Module-split queue now uses line count and top-level function/method count (defaults 1500 / 40).
- Dropped AST-node-sum "complexity" from that tool; function complexity stays on `analyze_functions`.
- Restored valid `DEPRECATION_INVENTORY.json` after a broken `removed_inventory` insert failed three inventory-load tests.
- Split `storage/user_data_operations.py` into backup/index/summaries/user-info modules; operations.py is a thin `UserDataManager` facade. Storage tests green (manager, scenarios, create/delete, coverage patches retargeted). Follow-up: docstrings/`@handle_errors` on the three new helpers; `# not_duplicate` on facade export/backup delegates.
- AI_PRIORITIES shows `N lines, M functions` instead of unreadable `total_function_complexity` totals.

## Archive Notes
Older detailed entries live in `development_docs/changelog_history/` and remain the historical source of truth. Use [CHANGELOG_DETAIL.md](../development_docs/CHANGELOG_DETAIL.md) for the latest detailed entries and the archive folder for month-split history.
