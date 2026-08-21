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

### 2026-08-11 - Discord package and bot split **COMPLETED**
- Moved Discord modules into `events/`, `ui/`, `onboarding/`, `webhooks/` with search-and-close imports (no legacy shims).
- Merged helpers into `ui/helpers.py`, lifecycle into `events/lifecycle.py`, and absorbed `item_form_shared` into `ui/create_item_ui.py`.
- Extracted rich delivery, connection health, command registration, and webhook tunneling; `bot.py` is now a 545-line lifecycle host.
- Post-audit hygiene: DISCORD_GUIDE path drift, changelog link retargets, docstrings/`@handle_errors`, Ruff/Pyright clean, legacy false-positive comment fixed; `doc-sync` PASS.

### 2026-08-11 - Appropriate coupling reductions (inverted edges) **COMPLETED**
- Public check-in first-question API; `service_requests` no longer calls private flow helpers.
- Scheduler runtime handle in `scheduler.runtime_access`; tasks/admin no longer import `core.service` for the locator.
- Coupling audit signal improved: unique fan-out > 10, exclude `__init__.py`; priorities triage inappropriate edges (not hub shrink).

### 2026-08-10 - LIST_OF_LISTS move and list SSOT cleanup **COMPLETED**
- Moved `LIST_OF_LISTS.md` into `development_tools/`; retargeted pointers.
- Omitted default-copy JSON sections/keys; retired dead `quick_audit.audit_scripts` (Tier 1 = `audit_tiers`).
- Fixed `audit --quick` guide prose; `STORAGE_SCOPE_*` re-exported from `audit_scope`; prompt category/flow alignment test.
- Follow-up: doc-sync path-drift + F401/SIM300 from that SSOT work cleared (`doc-sync` PASS).

### 2026-08-06 - LIST_OF_LISTS consolidation scan, rewrite, and SSOT cleanup **COMPLETED**
- Rewrote LIST_OF_LISTS as current ownership map; trimmed completed-history tables.
- Follow-up: live/example `base_exclusions` -> additions/removals; emptied portable `CONFIG_VALIDATOR` / `DOMAIN_MAPPER_DEFAULTS` / `known_deleted_files`; omitted duplicate JSON keys (`test_run`, `analyze_duplicate_functions`, identity `directory_to_marker`, matching error_handling scalars).
- Same-day hygiene: documented MHM `derived_prefix_excludes.core` (includes `development_tools` in `CORE_MODULES`); fixed `EXPECTED_TOOLS` tier comments/count; shared `_PYTHON_KEYWORDS_SHARED` for path-drift keyword tuples.
- Updated config.py comments that pointed at old LIST_OF_LISTS section numbers.

### 2026-08-04 - Personalized greetings/closings cleanup **COMPLETED**
- Strip `Best regards`, soft day-wishes, help-offer closers, and `--[Your Name]` signatures.
- Normalize to `Hi Name.` on one line (including `Hi Name.\nBody`); drop ungrounded check-in sentences when Data has no `Recent check-ins`.
- Prompts ban Dear/newline-after-name, fake check-in claims, and letter/help-offer closings.

### 2026-08-03 - Personalized prompt + Google Health steps/AZM sync **COMPLETED**
- Removed concrete sample metrics from `generate_personalized_message()` instructions so models cannot parrot `~5.5h` / `~2,400 steps` / `~45 active minutes` when Data has no recent wellness patterns.
- Prompt now: copy only `~` values from the Data block; otherwise write a warm general message with no fabricated sleep/steps/activity numbers.
- Fixed steps/active-zone-minutes `dailyRollUp` 400s: clamp `pageSize` so `window_size_days * page_size <= 90`; re-raise rollup errors so list fallback works.

### 2026-08-02 - Richer Google Health context (rounded sleep/steps) **COMPLETED**
- Pattern text may include rounded sleep/steps/active minutes; HR/HRV remain categorical bands only.
- Multi-day streaks (>=2 days): shorter sleep, lighter activity, or higher activity.
- Signals carry optional `steps` and `active_minutes`; `build_recent_health_patterns()` feeds scheduled messages and chat (`recent_patterns` in health envelope).
- Personalized prompt may use approximate sleep/steps/active minutes and streaks from Data only; truncate limit 700; guidance summary stays tone-only.
- Follow-up: regenerated function registry for health context helpers; Ruff SIM108 cleaned in sleep-hour formatting; doc path drift + ASCII cleanup; shared `activity_effort_band()` for personalization and streak phrasing.

## Archive Notes
Older detailed entries live in `development_docs/changelog_history/` and remain the historical source of truth. Use [CHANGELOG_DETAIL.md](../development_docs/CHANGELOG_DETAIL.md) for the latest detailed entries and the archive folder for month-split history.
