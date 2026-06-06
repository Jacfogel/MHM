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

### 2026-06-06 - UI dialog orchestration extraction (Stage 5) **COMPLETED**
- Moved `create_new_user`, all `manage_*` dialog openers, and message/schedule editor orchestration from `ui/ui_app_qt.py` into `ui/dialog_actions.py` (`DialogActions`).
- `MHMManagerUI` keeps thin delegators; lazy dialog imports stay behind `ui.lazy_dependencies._load_attr`.
- Added `tests/ui/test_dialog_actions.py`; `ui_app_qt.py` down to ~1421 lines.
- AI_PRIORITIES follow-up: `@handle_errors` on `user_list_provider`/`dialog_actions` helpers; consolidated duplicate `edit_user_*` paths via `edit_user_category`; removed dead `_prepare_current_user_category_editor` and inlined `_edit_user_category_content`; `doc-fix --fix-ascii` + `docs` regen.

### 2026-06-06 - UI user list provider + ServiceManager bridge removal **COMPLETED**
- Moved user/category combo loading and display-name helpers from `ui/ui_app_qt.py` into `ui/user_list_provider.py`; `MHMManagerUI` delegates via `UserListProvider`.
- Removed the temporary `ui.ui_app_qt.ServiceManager` re-export; callers/tests now import from `ui.service_manager` (package `__init__` unchanged).
- Added `tests/ui/test_user_list_provider.py` and updated combo-helper tests; `ui_app_qt.py` down to ~1719 lines.

### 2026-06-06 - UI scheduler action extraction **COMPLETED**
- Moved full/user/category scheduler calls and UI delivery-factory setup from `ui/ui_app_qt.py` into `ui/scheduler_actions.py`.
- Added focused scheduler action tests while leaving selection validation and final Qt messages in `MHMManagerUI`.
- Standard audit remains at 0 circular chains and 65 high-coupling modules; `ui_app_qt.py` dropped to 2136 lines / total complexity 9112.

### 2026-06-06 - UI status provider extraction **COMPLETED**
- Moved service/channel/tunnel status detection from `ui/ui_app_qt.py` into `ui/status_provider.py`; `MHMManagerUI.update_service_status()` now delegates status decisions and only updates Qt labels.
- Added focused UI tests for Discord activity parsing, Email rotated-log initialization, ngrok process detection, and service-stopped gating.
- Standard audit remains at 0 circular chains and 65 high-coupling modules; `ui_app_qt.py` dropped to 2156 lines / 63 functions / total complexity 9179.

### 2026-06-05 - UI ServiceManager extraction **COMPLETED**
- Moved UI-managed service process control from `ui/ui_app_qt.py` to `ui/service_manager.py`; `MHMManagerUI` now delegates service start/stop/restart/status checks.
- Added temporary `ui.ui_app_qt.ServiceManager` import bridge (removed 2026-06-06 once tests/callers used `ui.service_manager.ServiceManager`).
- Final audit remains at 0 circular chains and 65 high-coupling modules; `ui_app_qt.py` stays out of the high-coupling list and `service_manager.py` is not a new high-coupling offender.

### 2026-06-05 - Runtime delivery error hardening **COMPLETED**
- Email inbound polling now treats `None` from the async receive bridge as no messages and skips malformed payloads instead of logging repeated `NoneType` iteration errors.
- `CommunicationManager.send_message()` now logs channel-provided failure details (`get_error()` / `error_message`) when a channel returns `False`, and logs exception type/message before shared network/communication error handling.
- Added focused regression coverage in `tests/unit/test_channel_orchestrator.py`; verified with `pytest tests/unit/test_channel_orchestrator.py -q` (`48 passed`) and `py_compile` on touched files.

### 2026-06-04 - Priorities fixes: tests, aiohttp, doc links **COMPLETED**
- Stabilized `test_add_schedule_period` / `test_remove_schedule_period` (`@pytest.mark.no_parallel`, `update_user_index_for_test`, targeted schedules read + `clear_user_caches`) - fixes parallel `KeyError: motivational`.
- `report_generation._get_tier3_detail_log_files()` prefers each track's `log_file` from `tier3_test_outcome` (e.g. JUnit XML from `run_test_suite`); falls back to latest `pytest_*_stdout_*.log` only when a track has no `log_file`.
- Fixed invalid JSON in `development_tools/config/jsons/DEPRECATION_INVENTORY.json` (trailing comma in `active_or_candidate_inventory`) - restores `test_deprecation_inventory_loads_and_root_ruff_bridge_active`.
- Raised `aiohttp>=3.14.0` in `requirements.txt` (CVE-2026-34993, CVE-2026-47265).
- `verify_process_cleanup` machine-readable link resolves scoped JSON first; `doc-sync` reports 0 markdown link target hints.

### 2026-06-02 - Profile JSON v2 fleet + v2-only runtime **COMPLETED**
- Fleet migrated to `schema_version: 2` profile envelopes; context normalization (`pronouns`, `reminders_needed`, account-field stripping, ISO timestamps) in `core/profile_v2_io.py`.
- **Phases 4-5**: Unconditional v2 write; v2-only runtime load. Removed migrator, migration runbook, profile v2 audit tooling, and legacy on-disk dual-read/docs. `core/schemas.py` retained for in-memory normalization post-unwrap.
- **Test suite (2026-06-03)**: Fixed remaining parallel failures - AI context tests use `update_user_account` (not flat JSON writes); user-index UI test writes v2 envelopes; tags corrupt-file reinit detects `generic_json` recovery placeholders; tag save gap test asserts v2 disk payload; `test_update_user_index_real_behavior` uses v2 fixtures and mocks aligned with current per-user index API.

### 2026-06-01 - Profile JSON v2 envelopes; backup test fix; domain markers **COMPLETED**
- **Profile v2**: `core/profile_v2_schemas.py`, `core/profile_v2_io.py`, dispatcher branches in `storage/user_data_v2_envelopes.py`; dual-read/write for six files; `PROFILE_V2_WRITE` / `PROFILE_V2_ENFORCE` (default off). Schedules v2 uses `categories` wrapper; chat legacy arrays still load. Follow-up: logging f-strings, registry save helper, behavior test schedule shape, docstrings/error-handling audit items, TODO trimmed to phases 3-5.
- **Legacy inventory fix**: Removed redundant `CategoryScheduleV2Model._normalize_periods_input` (false-positive legacy scan on the v2 schema class). Flat period migration consolidated to `migrate_legacy_schedules_structure` on load and `_build_v2_envelope` on save; `DEPRECATION_INVENTORY.json` search terms narrowed.
- **Test fix**: `test_store_chat_interaction_creates_chat_log` uses `prepare_profile_raw_on_load` so it passes when `PROFILE_V2_WRITE=true` (v2 envelope on disk vs legacy bare list).
- `_users_dir_for_listing()` now honors isolated per-test `tests/data/tmp/<uuid>/users` trees under `MHM_TESTING` instead of always scanning shared `tests/data/users`.
- `test_backup_manager_with_large_user_data_real_behavior` no longer calls `rebuild_user_index()` or long retry/sleep loops; resolves users via the isolated test index only.
- Added `test_get_all_user_ids_lists_isolated_test_tree_when_patched` regression coverage.
- Documented domain marker policy in paired testing guides (category / domain / optional layers). **`@pytest.mark.user`** is the user-domain marker; migrated suite off `user_management`; updated `domain_mapper` config defaults.
- Module-scoped `temp_project_copy` for doc links/headings dev-tools tests (B-001); skipped `test_output_storage_archiving` (mutation-heavy).
- Cleared example-marker hints in `TESTING_GUIDE.md` (renamed `6.2.7. Examples` heading); ASCII already fixed via `doc-fix --fix-ascii`.

### 2026-05-31 - Backup guide alignment and manifest-less cleanup **COMPLETED**
- Added `cleanup_manifest_less_backup_directories()` so legacy `data/backups/` dirs without `manifest.json` are pruned after a 1-hour grace (runs on backup retention and monthly cleanup).
- Paired backup guides now document age-based log archival, `messages/message_data_manager.py` for message archives, and on-demand `user_backup_*.zip` artifacts.
- Audit follow-up: static logging check, Pyright, facade-shim annotation, doc-sync, and function registry regeneration.

### 2026-05-31 - Remove legacy DiscordEventHandler **COMPLETED**
- Removed `event_handler.py`, `DiscordEventHandler`, `get_discord_event_handler`, and lazy exports (`EventContext`/`EventType`) from `communication/__init__.py` after production routing already used `DiscordBot.initialize__register_events` and `discord_*_handler` modules.
- Deleted `tests/unit/test_discord_event_handler.py`; updated spec coverage matrix and `DEPRECATION_INVENTORY.json` (`discord_event_handler_class` -> removed). Regenerated function registry/module-deps docs; `doc-sync` clean after fixing changelog links to removed files.

### 2026-05-30 - Communication refactor stabilization **COMPLETED**
- Restored `conversation_flow_manager.py` after a failed flow-split patch (fixes pytest import/collection crash across communication behavior tests).
- Discord event handlers stay extracted (`discord_*_handler.py` modules); added `@handle_errors` on bot event wrappers and helper functions; moved `DiscordConnectionStatus` to `discord_connection_status.py` to reduce bot/handler circular imports.
- Introduced `discord_handler_protocol.py` (`DiscordHandlerHost`) so handler modules no longer import `bot.py`; added `@handle_errors` on `_on_ready_handler`; legacy `get_discord_event_handler` now logs on use and carries `# devtools: ignore[facade-shims]` after review. Dev-tools error-handling scan excludes Protocol stubs with docstring+ellipsis bodies (not just inline `...`).
- `command_parser` notebook entity helpers retained with `@handle_errors` on shared parse helpers; removed broken incomplete flow-split modules and one-off extraction scripts.
- Changelog ASCII/link quick wins applied via doc-fix and doc-sync.

### 2026-05-28 - Dev-tools complexity thresholds and test hygiene **COMPLETED**
- Raised module refactor thresholds (2000 lines, 4000 total complexity, 10 high+critical functions) and function complexity bands (100/200/300); AI_PRIORITIES wording no longer hardcodes node ranges.
- Docstrings added for `normalize_string_list` and `_valid_time` (audit docstring gap cleared).
- `test_discord_task_reminder_followup.py` marked `no_parallel` for shared `conversation_manager` state (fixes parallel-only Tier 3 flake).
- Coverage sweep (AI_PRIORITIES #1): new unit tests for `scheduler/jobs.py`, `checkin_schemas.py`, `checkin_analytics.py` (helpers + energy/basic analytics/completion paths), and `schedule_document_defaults.py` legacy migration.
- Audit follow-up: dev-tools complexity/decision-support tests and config example synced to 100/200/300 thresholds; UI task-management toggle test marked `no_parallel`; added checkin data manager, communication lazy-import, and checkin_summary fallback coverage.
- Word-boundary fix in `checkin_summary._prompt_mentions_breakfast()` (`\b` patterns; fixes "lately" -> "ate" false match).
- Suite cache invalidation: failed `run_test_suite` runs bust full-suite snapshot reuse even when coverage cache reports success; cache hits require `can_reuse_full_suite_cache()`.
- Error handling on `_prompt_mentions_breakfast` and create-hub button binders; function registry regenerated; AI_CHANGELOG ASCII fix.
- Parallel flake fix for `test_get_all_user_ids_returns_list`; scheduler task-reminder weight/selection unit tests added.
- Coverage sweep (sub-80% domains): storage tests for `validate_v2_document`, presets, and `_apply_fields_filter`; communication tests for Discord `interaction_views`; scheduler tests for `schedule_task_reminder_at_time`.
- Tier 3 parallel flake: `test_update_task_verifies_actual_changes_persist` uses unique user IDs, `wait_until` for disk persistence, and `no_parallel`; Pyright warnings cleared in `test_user_data_read_fields.py`.
- Backup manager parallel crash: [`test_backup_manager_behavior.py`](../tests/behavior/test_backup_manager_behavior.py) fixture uses isolated `test_path_factory` dirs instead of wiping shared `tests/data/users`; unique backup user IDs per test.

### 2026-05-27 - Task templates and Discord create hub **COMPLETED**
- Five built-in templates (medication, appointment, phone call, cleaning, paperwork) with prefilled defaults.
- Discord/text: `task template <name>`, `list task templates`, or `create` / `new` / `add` for button menu + modals (shared title/body/group/tags fields).
- Legacy alignment: no `LEGACY COMPATIBILITY` bridges; removed thin `resolve_template_id` wrapper in favor of `get_builtin_task_template()` returning a `TaskTemplate` (canonical lookup stays in `task_templates.lookup_builtin_template_id`).
- Tests: `test_task_templates.py`, `test_item_form_shared.py`, `test_create_menu_handler.py`.

### 2026-05-26 - Test domain markers (refactor alignment) **Progressed**
- Registered `@pytest.mark.storage` in `pytest.ini` and paired testing guides (`AI_TESTING_GUIDE.md`, `TESTING_GUIDE.md`).
- Retagged check-in and storage tests from `@core` (or redundant `@user_management`) to `@checkins` / `@storage`.
- Second pass: aligned markers with code moved out of `core` into domain packages (`messages`, `user`, `tasks`, `scheduler`, `ui`, `notebook`) and removed stale file/class `@core` where `user_management` / `scheduler` / `ui` already applied. Left `@communication` unchanged except `test_core_message_management_coverage_expansion` -> `@messages` (tests `messages.*`, not channels).
- Added `test_pytest_tests_have_required_domain_marker` (mirrors `analyze_test_markers` / config domain list). Wired `analyze_test_markers` into Tier 3 audit; `--check` now fails the audit when marker gaps exist.
- Regenerated `audit_tool_matrix.json` and `tool_cache_inventory.json` for Tier 3 `analyze_test_markers`; fixed ASCII arrows in changelog entries.
- Extended `development_tools/tests/coverage.ini` `[run] source=` to include `checkins`, `messages`, and `storage` (and full product package list); added policy test; regenerated `TEST_COVERAGE_REPORT.md` scope (rerun coverage for per-domain numbers).
- Coverage cache invalidation now includes `coverage.ini` in tool_hash (fixes stale full-cache reuse after `source=` changes); clears stored full coverage JSON on tool/config bust. Fixed ASCII in changelog; doc-sync clean.

## Archive Notes
Older detailed entries live in `development_docs/changelog_history/` and remain the historical source of truth. Use [CHANGELOG_DETAIL.md](../development_docs/CHANGELOG_DETAIL.md) for the latest detailed entries and the archive folder for month-split history.
