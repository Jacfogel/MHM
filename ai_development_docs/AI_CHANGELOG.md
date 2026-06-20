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

### 2026-06-18 - Scheduler, storage, and communication domain coverage **COMPLETED**
- Added `tests/unit/test_scheduler_manager_coverage.py` with scenario tests for `reset_and_reschedule_daily_messages`, `schedule_message_at_random_time`, deferred/skipped send paths, standalone helpers, and `task_reminders` module branches.
- Extended `tests/unit/test_scheduler_jobs.py` (cleanup import failure) and `tests/core/test_scheduler_maintenance.py` (nonzero delete stderr path).
- Scheduler package coverage on scheduler-focused tests: **83%** (was ~76%); `manager.py` **81%**, `task_reminders.py` **82%**.
- Added `tests/core/test_storage_scenarios.py` (17 tests) for `user_data_read` normalization/ID repair, `user_data_write` merge/cross-file invariants/transactions, and `user_data_operations` module wrappers, analytics, and index helpers.
- Added `tests/communication/test_message_processing_scenarios.py` (74 tests) for `user_suggestions`, `response_enhancer`, `parsing_shortcuts`, `flow_message_dispatcher`, communication `command_registry`, `discord_response_delivery`, `discord_guild_handlers`, and `email/inbound_processor` scenario paths.
- Communication targets now at **100%** on `user_suggestions.py` and `flow_message_dispatcher.py` in focused runs; re-run `audit --full` to refresh domain totals in `TEST_COVERAGE_REPORT.md`.
- Hygiene: fixed `datetime.now()` policy violation and unused `MagicMock` import in scheduler coverage tests (Ruff F401 + `test_no_datetime_now_in_tests`).
- Dev tools: `MissingMarkerFinder` now honors module-level `pytestmark` (fixes false-positive "16 missing category markers" for UI action tests that already had `pytestmark = [pytest.mark.ui, pytest.mark.unit]`).

### 2026-06-17 - Admin account provisioning extraction **COMPLETED**
- Extracted account creation business logic from `ui/dialogs/account_creator_dialog.py` into `core/admin_account_provisioning.py` (`provision_admin_account`, preference building, task tags, index retry, scheduler hook).
- Dialog calls `provision_admin_account` directly from `_validate_and_accept__create_account`; removed `create_account()` wrapper (not kept for tests).
- Provisioning behavior tests moved to `tests/unit/test_admin_account_provisioning.py`; UI tests no longer depend on a dialog provisioning method.
- Hygiene follow-up: added `@pytest.mark.user` and `no_parallel` reason comments on provisioning tests; removed unused `typing.Any` import; regenerated function registry (`docs`).

### 2026-06-16 - Channel orchestrator cleanup + interaction_manager decomposition **COMPLETED**
- Removed ~10 thin private `_` methods from `channel_orchestrator.py` that only forwarded to owned dispatchers; `handle_message_sending` now calls `checkin_dispatcher` and `predefined_dispatcher` directly.
- Kept public delivery-port facades (`send_checkin_prompt`, `handle_task_reminder`, `get_recipient_for_service`) per `SchedulerDeliveryPort` / `ServiceRequestDeliveryPort`.
- Fixed check-in round-trip: `CheckinPromptDispatcher.handle_scheduled_checkin` calls `self.send_checkin_prompt` instead of bouncing through `CommunicationManager`.
- Decomposed `interaction_manager.py` (~1647 -> ~283 lines) into `command_registry`, `prefix_command_processor`, `flow_message_dispatcher`, `parsing_shortcuts`, `structured_command_dispatcher`, `response_enhancer`, `help_responses`, `user_suggestions`; public API unchanged.
- Removed `message_router.py` shim; classification tests now use `message_route_classifier.py`; `message_router_shim` closed in deprecation inventory.
- Fixed parallel flake in `test_mark_as_welcomed_delegates_to_manager` (isolated welcome tracking paths + unique user IDs).
- **CI**: Fixed `logging-enforcement` Tooling Policy Consistency job (pytest 9.1 + `--strict-config` rejected invalid `pytest.ini` keys `collect_ignore` and `env`); moved ignores/env to `tests/conftest.py`.
- **Validation**: `validate_user_update` for schedules now unwraps/strips v2 envelope metadata before merge (fixes parallel flake when `test-user` cache had `schema_version`/`updated_at`); schedule tests use unique user IDs.
- **Doc hygiene**: Replaced non-ASCII em dash in `CHANGELOG_DETAIL.md` (ASCII compliance).

### 2026-06-10 - UI shell + communication coupling refactor **COMPLETED**
- Finalized the UI-only coupling refactor: `ui_app_qt.py` is now a thin Qt shell delegating selection, status rendering, request actions, scheduler/admin/dialog actions, and service control to focused UI modules.
- Split `conversation_flow_manager.py` into mixin modules under `communication/message_processing/flows/` (state, check-in, task, note flows); public API unchanged; preserved legacy persisted-state migration bridge.
- Centralized handler lazy-loading in `handler_registry.py`; trimmed duplicate imports in `interaction_handlers.py`, `channel_orchestrator.py`, and `interaction_manager.py`.
- Post-split cleanup: fixed missing `timedelta` import in `note_flow.py` (notebook flow test failures), removed 23 unused constant re-exports from `conversation_flow_manager.py` (constants now imported from `flow_constants`), and pointed tests/callers at `flow_constants` via search-and-close.
- Follow-up fixes: resolved `ParsedCommand` UnboundLocalError in `interaction_manager.py` (shortcut paths for "complete task" / "confirm delete"); regenerated function registry; doc-sync/ASCII quick wins.
- Dev-tools: high-coupling metric now uses **unique local module fan-out** (not raw duplicate import statements); bumped `aiohttp>=3.14.1` to clear pip-audit CVEs.
- Pyright: flow domain mixins inherit `FlowStateMixin` for typed shared state API; moved `clear_stuck_flows` to `flow_state.py` (55 warnings -> 0). ASCII fix in `CHANGELOG_DETAIL.md`.
- Duplicate-function triage: `# not_duplicate: task_due_date_natural_language_parsers` on `_parse_date_time_from_text` / `_parse_time_from_text` in `task_flow.py` (intentional date+time parser decomposition).

### 2026-06-06 - UI admin action extraction (Stage 7) **COMPLETED**
- Moved admin menu/system actions from `ui/ui_app_qt.py` into `ui/admin_actions.py`, including cache status/cleanup, config validation/help, all-users summary, log opening, verbose logging, process watcher opening, and system health reporting.
- `MHMManagerUI` now keeps signal-compatible wrappers that delegate to `AdminActions`; `ui_app_qt.py` is down to ~888 lines.
- Added `tests/ui/test_admin_actions.py`; targeted UI main/core/behavior suites pass after the extraction.

### 2026-06-06 - UI request action extraction (Stage 6) **COMPLETED**
- Moved test-message, check-in prompt, and task-reminder request-file creation/polling from `ui/ui_app_qt.py` into `ui/request_actions.py`.
- `MHMManagerUI` now keeps selection/service validation and final Qt message display while request actions return UI-neutral outcomes.
- Added `tests/ui/test_request_actions.py`; updated stale behavior-test patching to the new request-action owner.
- Verification: `py_compile`, focused request-action tests, and targeted UI main/core/behavior suites pass.

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

## Archive Notes
Older detailed entries live in `development_docs/changelog_history/` and remain the historical source of truth. Use [CHANGELOG_DETAIL.md](../development_docs/CHANGELOG_DETAIL.md) for the latest detailed entries and the archive folder for month-split history.
