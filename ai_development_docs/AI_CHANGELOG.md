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

### 2026-07-03 - Fix nightly CI: 26 CI-only test failures across 4 rounds **COMPLETED**
- **Rounds 1-3 (15 fixes)**: Pytest 9.1 `--durations` compat; basetemp cleanup; email/Discord/headless/ServiceManager/UI schedule mock fixes; gitignored config skips; writable `tmp_path` for Linux.
- **Round 4 (11 fixes)**: Process-group tests now `skipif(os.name != "nt")` since spoofing `os.name='nt'` on Linux crashes `Path()`; eliminated `no_parallel` markers + fixed policy violation. `is_local_module`/directory-tree/quick-status tests skip or mock when gitignored config absent. File locking tests platform-aware (`fcntl` on Linux, lock-file on Windows). Google health fixture tests skip when gitignored fixtures absent. `validate_core_paths` uses writable `tmp_path`.
- Root cause pattern: tests pass locally (env vars, config files, Windows paths) but fail on CI (Linux, no credentials, no gitignored config/fixtures). Underlying theme: `tests/test_helpers/fixtures/` and `development_tools_config.json` are gitignored.

### 2026-07-03 - Add unused functions detection tool **COMPLETED**
- Added `analyze_unused_functions.py` dev tool that uses AST analysis to find functions/methods never referenced anywhere in the codebase.
- CLI command: `python development_tools/run_development_tools.py unused-functions` (supports `--include-tests`, `--include-dev-tools`, `--private-only`, `--max-results`, `--json`).
- Filters out dunder methods, test functions, framework-decorated functions, and `__init__.py` exports to reduce false positives.
- Integrated into Tier 2 audit pipeline; results surface in `AI_STATUS.md`, `AI_PRIORITIES.md`, and `CONSOLIDATED_REPORT.md`.

### 2026-07-02 - Product AI context foundation **COMPLETED**
- Added canonical product-AI context envelope, metadata-only action catalog, and explicit prompt-flow ownership (`ai/context/service.py`, `ai/prompts/action_catalog.py`, `ai/prompts/flows.py`).
- Migrated `ContextBuilder` and conversational context assembly to read from `AIContextEnvelope` (`ai/context/builder.py`, `ai/context/assembly.py`).
- Consolidated product-AI prompts to four flow-aligned categories (`persona`, `reply_rules`, `data_honesty`, `action_boundaries`) plus runtime `available_actions` injection; removed duplicate `CONVERSATIONAL_CONTEXT_INSTRUCTIONS` and stopped stacking the 54-line assistant prompt on chat composition.
- Wired `action_interpretation` and `action_result_response` flows into runtime composition (`command_interpreter`, `assemble_action_result_messages`, `response_enhancer`).
- Added `AIActionPlan`, action planner, and action plan executor (`ai/chat/action_planner.py`, `communication/message_processing/action_plan_executor.py`); low-confidence routing behind `AI_ACTION_PLANNER_ENABLED` (default off).
- Added `AIActionRequest` -> `ParsedCommand` adapter and execution metadata (`communication/message_processing/action_request_adapter.py`) with tests proving `create_task` routes through `dispatch_structured_command`.
- Reorganized `ai/` into pipeline subpackages (`client/`, `context/`, `prompts/`, `chat/`, `fallback/`) and migrated imports across communication, tests, and scripts; removed legacy flat-module shims.
- Updated `PRODUCT_AI_RESPONSE_INFLUENCE_AUDIT.md` to reflect current status: enable `AI_ACTION_PLANNER_ENABLED` to use planner on low-confidence messages; multi-action plans and primary-path planner routing remain future work.
- Removed `enhance_conversational_engagement()` post-processing; follow-up behavior is prompt-owned via `reply_rules.txt`. Fixed import-boundary and function-registry tests for `ai/` subpackages; repaired doc path drift (`doc-fix`, `docs`, `doc-sync`). Marked intentional duplicate-function groups with `# devtools: intentional[duplicate-functions]:` (`period_row_read_only_decomposition` on nine `PeriodRowWidget._set_read_only__*` helpers; `rule_based_entity_extractors` on six `command_parser` rule-based entity extractors); duplicate analyzer now reports 0 groups.
- **Fix (nightly CI)**: Added Ubuntu Qt/X11 system packages to `.github/workflows/nightly-tests.yml` for headless PySide6 UI tests; nightly runs use `--no-domain-cache` on GitHub Actions and `run_test_suite` now keeps subprocess stdout small when writing `--output-file`.
- **Fix (parallel flake)**: `test_user_with_all_features` now waits for preferences to flush, aligns schedule categories, and retries schedule saves (matching `TestUserFactory.create_user_with_schedules`); schedule day names use schema-valid capitalization. Schedule assertions normalize v2 `categories` wrappers via `_schedule_categories_from_loaded()`.
- **Context DRY**: Extracted `_assemble_product_flow_messages()` and `_phrase_recent_sent_messages()` to deduplicate assembly/phraser helpers flagged by duplicate-function analysis.

### 2026-06-30 - Tier 3 quick tests + nightly full suite **COMPLETED**
- Tier 3 `audit --full` runs **quick** pytest profile (`not slow`) via `run_test_suite --profile quick`.
- New `nightly-test-suite` command runs **full** profile (includes slow tests); GitHub Actions nightly workflow added.
- Suite cache is profile-aware (`last_suite_profile`); config adds `test_run.profiles` quick/full.
- **Fix**: `NameError` on `strict` in `_run_test_suite_profile` crashed audits after pytest; command doc/group parity for `nightly-test-suite`.
- **Fix (`personalized` category)**: [`channel_orchestrator.py`](../communication/core/channel_orchestrator.py) now calls `generate_personalized_message()` instead of `generate_contextual_response()` - avoids generic chat fallback when LM Studio context overflows.
- **Fix (personalized truncation + duplicate test sends)**: Explicit `mode="personalized"` in [`chatbot.py`](../ai/chat/chatbot.py) - prompt word "message" no longer triggers command mode (60-token cutoff). Admin test button disables while sending.
- **Fix (model format leaks + UI guard)**: Strip `## INPUT` / `## OUTPUT` training markers from AI output; stop sequences on personalized calls. Initialize `_test_message_in_flight` in UI `__init__` (was broken by `__getattr__` delegation).
- **Fix (duplicate test sends + Google Health context)**: UI now polls up to ~60s for AI test messages. Personalized messages include coarse Google Health signals via `build_personalized_wellness_context()` with fallback to the latest synced signal when today's sync is missing.
- **Fix (UI freeze + health priority)**: Test-message wait runs on a background `QThread` (no main-window freeze). When Google Health confidence is medium/high, stale check-ins are omitted from the personalized prompt.
- **Fix (identical test personalized messages)**: Admin test sends pass `skip_ai_cache=True` so `generate_personalized_message()` bypasses the 5-minute response cache and requests fresh wording each time.
- **Fix (placeholder sign-offs)**: Personalized prompts forbid letter-style closings; `strip_letter_signoffs()` removes trailing `Take care, [Your Name]` and similar leaks.
- **Fix (multi-draft model output)**: `keep_first_personalized_block()` keeps only the first greeting block when LM Studio returns several complete messages in one reply.
- **Audit hygiene**: Pyright warning on `_StubService.nightly_result`; ASCII doc-fix + doc-sync; function registry regen (`docs`); removed unused `get_recent_responses` import; `@handle_errors` + docstrings on `_TestMessageRequestWorker`; `test_add/remove_schedule_period` marked `no_parallel` (xdist schedules cache flake).
- Docs updated across paired testing and dev-tools guides.

### 2026-06-29 - Faster default test runs **COMPLETED**
- `pytest.ini`: quiet defaults (removed always-on `--verbose`, disabled `log_cli`; consolidated file logs unchanged).
- `run_tests.py`: `--quick` iteration profile; parallel runs use `--dist=loadscope` and up to 6 auto workers; default `-q` unless `--verbose`.
- Slow tests: scope `build_user_index` / `get_all_user_summaries` to fixture users (fixes ~150s+ scan of shared `tests/data/users`).
- Parallel isolation: ~35 tests refactored off `no_parallel` (account handler, user management, user creation, utilities demo) via UUID users and locked index helpers. **Batch 2** (~29): `test_account_lifecycle.py` (9), `test_account_management_real_behavior.py` (6), `test_user_data_manager.py` (14) - scoped rebuild patches, `test_path_factory` backup dirs, `_resolve_test_user_id` helper. **Batch 3**: `test_user_creation.py` integration tests drop full index rebuilds; parser behavior tests mock `AIChatBotSingleton.generate_response` except `@pytest.mark.ai`. Follow-up: `test_user_creation.py` parallel flake fixes (`_read_channel_type`, schedules via `update_user_schedules`).
- Tier 3 audit: `run_test_suite.py` aligned with runner settings; 4-worker cap during audit to reduce contention with parallel static analysis.
- Docs: paired testing guides updated with `--quick`, loadscope, and Tier 3 scope notes.

### 2026-06-28 - Google Health V1 complete **COMPLETED**
- Reconnect notice on auth auto-pause; per-user timezone sync (30-min poll); optional Fernet token encryption.
- Admin UI **Google Health** connect panel ([`google_health_settings_dialog.py`](../ui/dialogs/google_health_settings_dialog.py)); shared [`user_settings.py`](../integrations/google_health/user_settings.py).
- Tests: notifications, sync schedule, token crypto, user settings, dialog actions; health handler refactored.
- **Audit hygiene**: GOOGLE_HEALTH_GUIDE path drift; error handling + docstrings; function registry regen; Ruff clean; stabilized `test_validate_and_raise_if_invalid` (mock); fixed `test_validate_and_raise_if_invalid_failure` reload/class mismatch flake; removed unused `ConfigValidationError` import in `test_config.py`.
- **`personalized` category**: Added to `CATEGORIES`; consolidated `ai_personalized` alias (removed - same code path, never used). AI-generated at send time via `is_ai_generated_message_category()`; no message library file required.
- **Category UI**: [`category_selection_widget.py`](../ui/widgets/category_selection_widget.py) now builds checkboxes from `get_message_categories()` instead of a hardcoded list.
- **Audit hygiene**: Error handling on new helpers; test/domain-mapper/registry/ASCII fixes from dev-tools priorities.
- **Google Health hygiene**: Full docstring + `@handle_errors` pass on `integrations/google_health/`; broke config/token_crypto import cycle; data_handlers Phase 1 migration.
- **Google Health hygiene (2)**: Remaining docstrings (`_add_guidance`, async connect `_run`) and `@handle_errors` on schemas empty factories, notifications, token_crypto, data_handlers `_now`.
- **Doc hygiene**: Fixed stale markdown link in `DEV_TOOLS_CONSOLIDATED_REPORT.md` (ephemeral audit JSON); `report_generation.py` always uses backtick paths for `jsons/` targets so doc-sync stays clean.

### 2026-06-27 - Google Health read-only integration **COMPLETED**
- Added `integrations/google_health/` package: OAuth connect, automated 1-2x daily sync, daily summaries, derived wellness signals, and deterministic message guidance (no raw metrics to AI).
- Per-user storage under `data/users/{user_id}/health/`; feature flag `account.features.google_health` (`enabled` | `disabled` | `paused`).
- Discord commands via [`health_handler.py`](../communication/command_handlers/health_handler.py); scheduler jobs in [`health_sync_jobs.py`](../scheduler/health_sync_jobs.py).
- AI context: [`core/health_context_builder.py`](../core/health_context_builder.py) + `append_health_guidance` in conversational context assembly.
- Tests: unit/behavior/integration under `tests/unit/test_google_health_*`, `tests/behavior/test_health_handler_behavior.py`, `tests/integration/test_health_scheduler_job.py`.
- **Fix (same session):** Google Health API client now uses kebab-case endpoints and type-specific list filters (`sleep.interval.end_time`, `steps.interval.start_time`, `daily_*.date`); added pagination and richer response parsing so sync populates `daily_summaries.json`. Steps/HR/HRV/active-minutes parsing fixed for Google field names (`civilStartTime`, `beatsPerMinute`, `averageHeartRateVariabilityMilliseconds`, `activeZoneMinutes`). Long lookback: steps/active minutes use chunked `dailyRollUp` (14-day Google limit, correct civil range format); upsert merges fields; API errors re-raise so chunked list fallback runs.
- **Discord fix**: Health commands excluded from AI response enhancement (deterministic status/connect text was being rewritten with wrong facts).
- Docs: [GOOGLE_HEALTH_GUIDE.md](../integrations/google_health/GOOGLE_HEALTH_GUIDE.md), [USER_DATA_MODEL.md](../core/USER_DATA_MODEL.md) Section 2.3.5, [CONFIGURATION_REFERENCE.md](../CONFIGURATION_REFERENCE.md), [HEALTH_INTEGRATION_PLAN.md](../development_docs/HEALTH_INTEGRATION_PLAN.md) (V0 complete + V1/deferred backlog).
- **Audit hygiene**: Docstrings + `@handle_errors` on health handler help methods and `response_enhancer._should_skip_ai_enhancement`; f-string logging fixes; test isolation for `GOOGLE_HEALTH_ENABLED`; schema/feature test updates for `google_health`; `google_health_file` in test log path mocks; function registry regenerated (`docs`).
- **Audit follow-up**: `@handle_errors` on OAuth `_notify`; domain markers on Google Health tests; unused import cleanup; Ruff UP035/SIM105; doc-fix (ASCII, headings, links).
- **Audit follow-up (2)**: `# devtools: ignore[facade-shims]` on Pydantic feature validators; fixed [CONFIGURATION_REFERENCE.md](../CONFIGURATION_REFERENCE.md) Google Health guide link; stabilized `test_validate_and_raise_if_invalid_failure` (mock + `GOOGLE_HEALTH_ENABLED` isolation).

### 2026-06-27 - Phrase settings generalization + admin UI **COMPLETED**
- Moved natural-language defaults to `preferences.natural_language_defaults` (not task-only); logic in [`core/natural_language_defaults.py`](../core/natural_language_defaults.py); shipped defaults in [`resources/default_natural_language_defaults.json`](../resources/default_natural_language_defaults.json).
- **Migration complete**: legacy `task_settings.natural_language_defaults` read bridge and one-time migration helpers removed (fleet verified clean). Old phrases (`show task language settings`, `set task tonight to 8pm`) still parse to canonical intents.
- Discord: dedicated [`natural_language_handler.py`](../communication/command_handlers/natural_language_handler.py) - `show phrase settings`, `set tonight to 8pm`.
- Admin UI: **Phrase Settings** button + [`natural_language_settings_dialog.py`](../ui/dialogs/natural_language_settings_dialog.py) / [`natural_language_settings_widget.py`](../ui/widgets/natural_language_settings_widget.py) - separate from Task Management widget.
- Tests: [`test_natural_language_defaults.py`](../tests/unit/test_natural_language_defaults.py), [`test_natural_language_handler_behavior.py`](../tests/behavior/test_natural_language_handler_behavior.py).
- **Audit hygiene**: Regenerated function registry (`docs`); Ruff UP035/UP037 fix in [`core/natural_language_defaults.py`](../core/natural_language_defaults.py).
- **Audit follow-up**: `@handle_errors` on `_get_cached_builtin_defaults`; f-string logging (static check); removed unused `tasks/task_natural_language_defaults.py` shim; fixed TASKS_PLAN and changelog link drift; doc-fix ASCII/links + doc-sync.

### 2026-06-26 - Journal entry visual distinction + NLP mode detection **COMPLETED**
- Journal list lines and detail view in [`notebook_handler.py`](../communication/command_handlers/notebook_handler.py) now show **Journal** label plus `submitted_at` date (`Jun 15` or `Mar 04, 2025` when not current year).
- Centralized `_format_entry_list_line()` across inbox, search, group/tag, pinned, recent, and archived lists so journal entries use the journal icon consistently.
- **NLP mode detection**: [`command_interpreter.py`](../ai/prompts/command_interpreter.py) expanded keywords (`append`, `inbox`, `group`, `template`, `search`, etc.) and `_COMMAND_PHRASE_HINTS` for `show inbox`, `search for`, `append note to task`, `tasks in group`, `help notebook` without misclassifying emotional chat.
- Tests in [`test_notebook_handler_pagination_formatting.py`](../tests/unit/test_notebook_handler_pagination_formatting.py), [`test_command_interpreter.py`](../tests/unit/test_command_interpreter.py), [`test_natural_language_command_detection.py`](../tests/behavior/test_natural_language_command_detection.py); [NOTES_PLAN.md](../development_docs/NOTES_PLAN.md) section 4.5 marked complete.

### 2026-06-24 - Task list UI tests + task notes + group filter **COMPLETED**
- Added [`test_task_list_ui.py`](../tests/communication/test_task_list_ui.py) (17 tests) for Discord task picker/detail: flow starters (due date, priority, reminders), handler delegation, view factory, select callback, and detail button paths.
- Added **section 6.1.D** to [`MANUAL_DISCORD_TEST_GUIDE.md`](../tests/MANUAL_DISCORD_TEST_GUIDE.md) for live validation of `show my tasks` dropdown, detail buttons, and Show More pagination.
- **Task notes**: `append note to task` / `add note to task` commands (`append_note_to_task` intent), `update task ... note ...` replaces description; help text and examples updated in [`task_handler.py`](../communication/command_handlers/task_handler.py).
- **Task groups**: `show tasks in group work` / `list tasks group:medical` filter lists; group shown in list lines and detail view; Show More pagination preserves group filter.
- **Task tags**: Task create/update/filter paths now use `core/tags.py` normalization (`sanitize_task_tags`, case-insensitive tag filter); `TaskV2Model` validates tags on load.
- **Task NL defaults**: Per-user `task_settings.natural_language_defaults` (`tonight`, `after work/school`, time-of-day, weekend `this week`); loaded via [`core/natural_language_defaults.py`](../core/natural_language_defaults.py) (originally `tasks/task_natural_language_defaults.py`).
- **Audit hygiene**: Broke task module cycles (`task_time_parsing.py`, `task_tag_helpers.py`); docstrings + error handling on new helpers; function registry regenerated; Phase 1 decorator migration on NL defaults; removed unused re-exports from `task_validation.py`.
- **Audit hygiene**: Fixed Ruff/Pyright on task list UI tests; ASCII compliance in changelogs + manual guide; hardened parallel flakes in `test_storage_scenarios`, `test_schedule_period_lifecycle`, and `test_get_user_data_fields_scalar_list_and_dict` (core `get_user_data` import + index refresh; v2 envelope fallback in test shim).

### 2026-06-22 - Notebook help + task follow-up button fix **COMPLETED**
- Added `NOTEBOOK_HELP_TEXT` in [`notebook_handler.py`](../communication/command_handlers/notebook_handler.py) - capture/retrieve/modify/lists sections, inbox semantics, groups vs tags, and Show More paging note.
- Wired `help notebook` / `examples notebook` through [`interaction_handlers.py`](../communication/command_handlers/interaction_handlers.py) and parser patterns in [`command_parser.py`](../communication/message_processing/command_parser.py); general help and commands list now mention notebook.
- **Fix**: Task priority step after due-date Skip lacked Discord buttons - [`flow_message_dispatcher.py`](../communication/message_processing/flow_message_dispatcher.py) now attaches `TASK_DUE_DATE_SUGGESTIONS` / `TASK_PRIORITY_SUGGESTIONS` for active flows; [`bot.py`](../communication/communication_channels/discord/bot.py) stores suggestion label as button payload.
- **UX**: Due-date buttons are **Skip Question**, **Skip All**, **Undo Task Creation**; **cancel**/**delete task** delete the in-progress task; **undo**/**back** go one step back; timeout (10 min) + unrelated message acts like **Skip All** across task/notebook flows.
- **Architecture**: Shared flow control in `flow_command_helpers.py`, `flow_control_mixin.py` - universal keywords, timeout, unrelated detection, and `try_flow_control_command()` for tasks, notes, lists; ready for journal/events/checkins.
- **Flows**: Step-aware unrelated detection; cancel synonyms; explicit outcome messages; journal multi-step body flow; priority buttons aligned with due-date set. Live-test fixes: no reminder prompt without due date; Discord control buttons grey (skip) / red (undo) vs blue suggestions; note/journal last step without Skip All; list End List + Undo List Creation every step.
- **Fix (live validation)**: Day-based reminders (`1 to 2 days before`) pick **one** day in range with a **09:00-17:00** window (not two reminders); minute/hour single-value phrases get at least a 1-hour window.
- **Audit cleanup**: Shared `discord_user_resolution.internal_user_id`; error handling on task list UI inits; fixed stale list-format test; removed redundant due-date legacy regex; registry + ASCII doc-fix.
- **Fix (live validation)**: `tomorrow at 2pm` now sets task `due_time`; reminder math uses parsed time instead of 09:00 default.
- **Fix**: `show tasks` no longer duplicates the list; **Show More** pagination; due times in list; removed broken filter shortcut buttons.
- **Feature**: Discord task picker select + detail view (due date / priority / reminders / complete / more flows).
- **Fix**: Due-date flow accepts `YYYY MM DD` and `YYYY/MM/DD` in addition to `YYYY-MM-DD` (`parse_flexible_date_only` in `core/time_utilities.py`).
- **Audit hygiene**: Restored `DISCORD_BOT_TOKEN` import; Ruff/Pyright clean; fixed parallel test failures; `@handle_errors` on `_attach_flow_suggestions`; function registry regenerated; ASCII changelog fix applied. Flow audit: docstrings on task/note flow helpers; `# error_handling_exclude` on pure keyword predicates; removed thin-wrapper `is_task_flow_skip_*` facades. Security/docs: pinned `msgpack>=1.2.1` (GHSA-6v7p-g79w-8964); report generator uses plain paths for gitignored audit JSON links.

### 2026-06-21 - Communication coverage expansion and test hygiene **COMPLETED**
- Added [`test_communication_coverage_expansion.py`](../tests/communication/test_communication_coverage_expansion.py) (39 tests) targeting AI priority #1 gaps: `discord_interaction_router.py`, `create_item_ui.py`, `checkin_flow.py`, and `task_flow.py` reminder/flow edge paths.
- Extended [`test_message_processing_scenarios.py`](../tests/communication/test_message_processing_scenarios.py) with `discord_response_delivery` embed-only, view-only, and ephemeral branches; extended [`test_status_provider.py`](../tests/ui/test_status_provider.py) with Discord/email/ngrok status and `tail_file_lines` paths.
- Focused coverage on targeted modules: `discord_interaction_router` ~77%, `create_item_ui` ~61% (up from ~17% / ~25%); all **167** tests under `tests/communication/` pass.
- Hygiene: removed unused `ParsedCommand` import (Ruff F401); `_discord_interaction()` uses `MagicMock(spec=discord.Interaction)`; guarded `await_args` before `.args[0]` (Pyright 0 warnings on the file).

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

## Archive Notes
Older detailed entries live in `development_docs/changelog_history/` and remain the historical source of truth. Use [CHANGELOG_DETAIL.md](../development_docs/CHANGELOG_DETAIL.md) for the latest detailed entries and the archive folder for month-split history.
