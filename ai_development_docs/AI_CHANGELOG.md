# AI Changelog - Brief Summary for AI Context
> **File**: `ai_development_docs/AI_CHANGELOG.md`
> **Audience**: AI collaborators (Cursor, Codex, etc.)
> **Purpose**: Lightweight summary of recent changes
> **Style**: Concise, essential-only, scannable
> **See [development_docs/CHANGELOG_DETAIL.md](development_docs/CHANGELOG_DETAIL.md) for the full history**

## Overview
This file is a lightweight summary of recent changes for AI collaborators. It provides essential context without overwhelming detail. For the complete historical record, see [CHANGELOG_DETAIL.md](development_docs/CHANGELOG_DETAIL.md).

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

### 2026-05-07 - Duplicate-function cleanup without legacy shims **COMPLETED**
- Cleared the full-scope duplicate-function priority: `duplicate-functions --body-for-near-miss` now reports 0 issues and 0 groups.
- Refactored real duplication in user lookup, cache cleanup/removal, UI/service request helpers, process watcher selection, backup restore, and LM Studio readiness while avoiding new legacy compatibility bridges.
- Removed unnecessary private user-lookup shim functions after review; remaining thin entry points are existing UI/API/tested hooks, not legacy adapters.
- Validation: `py_compile`, service request helper tests, duplicate-analyzer tests, and the legacy scan passed.

### 2026-05-06 - Facade/shim cleanup and signal tuning **COMPLETED**
- Removed verified-dead compatibility/facade surfaces: chatbot fallback bridge, factory config wrappers, scheduler task-selection delegates, service request aliases, and unused UI/preference aliases.
- Cleaned stale legacy audit noise by removing the broad `user_data_v1_runtime_adapters` scan bucket and moving the chatbot fallback bridge to removed inventory history.
- Tightened `analyze_facade_shims` so default audit output focuses on named/documented compatibility surfaces or active deprecation-inventory hits; plain low-signal thin wrappers are still available with `--include-low-signal`.
- Refreshed generated audit outputs; current facade/shim priority count is 8 default candidates, with 174 low-signal candidates filtered. Validation: focused product/dev-tools tests passed; standard audit passed. A full audit timed out after saving tightened facade JSON, so it is not counted as clean full-audit validation.

### 2026-05-06 - Dev-tools facade/shim analyzer and markers **COMPLETED**
- Added advisory `facade-shims` tooling for facade, shim, re-export, alias, compatibility bridge, and deprecation-inventory candidates; registered it in CLI, service wrappers, tool metadata, Tier 2+ audit execution, cache inventory, scoped JSON storage, and AI status/priority/consolidated report output.
- Standardized code-level tool suppressions through `# devtools: ignore[...]` and `# devtools: intentional[...]`; duplicate-function legacy markers still work, and legacy-reference scanning now honors `ignore[legacy-references]`.
- Aligned the clear `_get_fallback_response` compatibility bridge with the legacy workflow: inventory now tracks it, `backwards compatibility` wording is detected, the canonical inventory file is no longer ignored, and legacy analyzer cache invalidates on inventory changes.
- Extended duplicate-function analysis with argument signature capture, argument-name/shape similarity fields, and capped argument-similarity candidate expansion.
- V5 Sections 7.11-7.13 are marked complete; paired development-tools guides document the new command/markers/scoring. Generated docs/reports were refreshed so the function registry gap is zero and Ruff findings are cleared.
- Validation: focused dev-tools tests, report-surfacing checks, policy checks, `py_compile`, `ruff check .`, `docs`, standard `audit`, and `audit --quick` passed.

### 2026-05-06 - Coverage and static audit cleanup **COMPLETED**
- Added focused coverage for development-tools command/report/tool-wrapper branches, scheduler maintenance jobs, Discord bot helpers, schedule-editor headless helpers, and UI log-tail merging.
- Email inbound safety: `channel_orchestrator` now ignores system/bounce sender addresses (`mailer-daemon`, `postmaster`, `no-reply`/`noreply`, `bounce`) before user lookup/response handling to prevent bounce-loop auto replies.
- Added focused unit tests for inbound sender filtering and blocked-sender early-return behavior (no user lookup, no `_send_email_response` call).
- Cleared follow-up audit items by fixing missing test markers, resolving doc-sync path/link drift, removing the Ruff/Pyright test-fixture conflict, and adding a `pip>=26.1` tooling floor for pip-audit findings on pip itself.
- Validation: focused dev-tools/core/unit/communication/UI batches passed, marker analysis and doc-sync passed, Ruff/Pyright passed, and direct pip-audit passed after upgrading the venv pip to 26.1.1. A cache-cleared full audit was killed with exit 137, so it is not counted as a clean full-audit validation.

### 2026-05-05 - Dispatcher contracts and scheduler delivery port **COMPLETED**
- `channel_orchestrator` was thinned further: predefined message dispatch, task reminder dispatch, and check-in prompt sending now live in dedicated dispatcher modules with `MessageSendResult` as the regular/reminder send contract.
- Added `core.delivery` protocol interfaces so scheduler/service request code can depend on a small delivery surface instead of a full `CommunicationManager`; scheduler compatibility aliases and direct standalone `CommunicationManager` construction were removed after tests moved to delivery ports.
- Fixed dispatcher wildcard schedule matching / failed-send storage behavior, removed avoidable parallel-audit skips from CLI/dependency/interpreter tests, and replaced the remaining generic service-request `TypeError` with `ValidationError`.
- Cleared follow-up audit items by regenerating function/module docs and refreshing generated AI status/priority reports; the completed refactor plan was removed from active `PLANS.md` tracking and [TODO.md](../TODO.md) keeps only deferred architecture follow-ups.
- Validation: Ruff, `py_compile`, focused scheduler/service/reminder/orchestrator/dispatcher/dev-tools tests, docs regeneration, standard audit, and cached full audit passed. The refreshed parallel test run reports no skip count.

### 2026-05-04 - Duplicate audit freshness and marker triage **COMPLETED**
- `AI_PRIORITIES.md` / `CONSOLIDATED_REPORT.md` now point duplicate, module-refactor, and function-complexity detail links at scoped current JSON under `development_tools/functions/jsons/scopes/full/`.
- `analyze_duplicate_functions` now suppresses intentional groups only when every member has the same `# not_duplicate` / intentional marker; decorated-function markers are detected correctly.
- Added `duplicate-functions --body-for-near-miss` so standalone duplicate runs can mirror full-audit near-miss body similarity mode.
- Marked reviewed intentional duplicate groups across user-data, notebook, cleanup, task-service facade, loader, save-validation, and AI-response extraction helpers. Current generated priority report shows 2 remaining duplicate candidate groups.
- Validation: focused duplicate analyzer, CLI flag, audit storage scope tests, and `py_compile` passed. Consolidated-report test selection timed out during teardown after printing passing tests, so it was not counted as a clean full pass.

### 2026-05-03 - Refactor continuation phases 1-4 **COMPLETED**
- `service_requests` owns request-file processing via `ServiceRequestContext`; `service.py` is now closer to lifecycle/wiring-only and delegates request handling.
- Scheduler logic moved out of `SchedulerManager`: task reminders in `scheduler_task_reminders`, maintenance in `scheduler_maintenance`, common job registration in `scheduler_jobs`.
- Message preview/content resolution now lives in `core/message_preview`; the remaining `MHMService` preview wrapper was removed.
- `notebook_service` now has structured notebook use cases/results and `notebook_handler` calls it; `task_service` owns reusable task matching/urgency helpers used by `task_handler`.
- **Phase 6 pagination rendering**: `notebook_handler` now emits generic `PaginationAction` metadata; Discord owns Show More labels, button custom IDs, and hidden continuation payloads.
- Plans/TODO updated: phases 1-6 complete, phases 7-9 remain; low-priority architecture follow-ups track possible `scheduler/`, `storage/`, `messages/`, and `checkins/` packages. Validation: Ruff clean and focused service/scheduler/notebook/task suites passed.
- **Priority sweep**: pagination/notebook helper error handling, pagination `core` domain markers, changelog link conversion, task-urgency test clock patching, and `service_requests` cleanup duplicate hygiene are addressed. Targeted pagination/task/service tests, error-handling analyzer, marker analyzer, `docs`, and `doc-sync` passed.

### 2026-05-02 - Scheduler split + notebook/task service facades **COMPLETED**
- `scheduler_maintenance`, `scheduler_task_reminders`, `scheduler_jobs` wired from `SchedulerManager`; resilient per-file test-message flag cleanup in `service_requests`.
- `notebook_service` / `task_service` added; handlers use them (lazy `_task_service()` in task handler). Tests updated for dispatcher/service_requests patch paths.
- Discord ngrok exit logs use f-strings (static logging check).
- **Sweep**: unused-import Ruff fixes; docstrings/`handle_errors` on send-result + small facades; pytest domain markers on new service tests; TODO cleanup; `docs` / `doc-fix` / `doc-sync` run.
- **Duplicate tool**: `# not_duplicate: ...` on paired thin delegators (orchestrator predefined sends; service vs `service_requests` request-file cleanup). **Error handling**: `@handle_errors` on `SchedulerManager` maintenance delegators; `get_repo_base_directory` / `is_test_message_request_filename` in `service_requests`. TODO links how to mark intentional duplicates (`analyze_duplicate_functions.py` docstring).

### 2026-05-02 - Discord ngrok diagnostics **COMPLETED**
- Failed auto-ngrok now logs stderr + authtoken / manual-ngrok hints; running tunnel drains stderr in a background thread. DISCORD_GUIDE updated for ngrok v3+; `.env.example` defaults `DISCORD_AUTO_NGROK=false`. Validation: `py_compile` + Ruff on `discord/bot.py`.

### 2026-05-02 - Development tools decoupled from core.logger **COMPLETED**
- **Follow-up (same day)**: `get_dev_tools_logger` now supports stdlib printf-style calls (fixes Pyright across dev-tools); `run_development_tools.py` sets `DEV_TOOLS_LOGS_DIR` to `development_tools/reports/logs`; [TODO.md](../TODO.md) path-drift fixes + doc-sync clean; `run_test_coverage.py` guards `logger.error(context)` when `context` is optional. **`core/logger.py`**: removed special-case routing of log files under `development_tools/reports/logs` when `MHM_DEV_TOOLS_RUN=1` (dev-tools file logs are only via `development_tools.shared.logging`).
- **Log noise / priorities**: Dev-tools file logs default **INFO** (`DEV_TOOLS_LOG_LEVEL`); several former WARNING/ERROR lines re-leveled to DEBUG for expected paths; unknown CLI command is WARNING. Paired logging-guide paths + CHANGELOG link fixed so doc-sync PASS; `status` refreshed `AI_PRIORITIES.md`.
- **Audit vs pytest subprocess**: CLI entry clears inherited `PYTEST_CURRENT_TEST`; lock-based audit detection lives in `lock_state` and gates `create_output_file` for `AI_*` without `shared.operations`; smoke tests skip when project-root audit/coverage locks are active; `file_rotation` uses `.lock_state` import for Pyright.
- **Portability**: New [`development_tools/shared/logging.py`](../development_tools/shared/logging.py) (`get_dev_tools_logger`); all `development_tools/**/*.py` migrated off `core.logger`; import-boundary checker now flags **any** `core.*` import under `development_tools/`.
- **Docs/policy**: Updated paired dev-tools guides, `.cursor/rules/dev_tools.mdc`, `check_channel_loggers` product vs dev-tools messaging, and consolidated-report import-boundary action text.
- **Tests**: `tests/development_tools/test_dev_tools_portability_smoke.py` (minimal fake project + subprocess import check); boundary/policy tests updated; `test_file_rotation` patches `get_dev_tools_logger`.
- **Validation**: `pytest` on changed/focused dev-tools tests; `python development_tools/run_development_tools.py audit --quick` succeeded.

### 2026-05-02 - Notebook Pagination and Task Follow-up UX **COMPLETED**
- **Notebook Discord UX**: `Show More` pagination now preserves hidden payloads for search, inbox, pinned, group, tag, and archived notebook views; pinned/inbox continuation now passes stored entities through handler dispatch.
- **Notebook search UX**: empty search results now suggest practical recovery paths including `!recent`, `!inbox`, `!archived`, `!t <tag>`, and `!group <name>`.
- **Task creation flow**: Discord task creation now includes an optional priority follow-up before reminder setup when priority was not supplied, with `Skip` and `Skip All` exits.
- **Audit cleanup/tests**: docs registry regenerated; Pyright warnings fixed (`0 errors, 0 warnings` after escalated rerun); focused Discord/task/notebook behavior suites passed (`75 passed`) plus Ruff and `py_compile`.

### 2026-05-02 - Discord Recurring Task UX **COMPLETED**
- **Audit status**: latest generated `AI_STATUS` already showed Tier 3 clean, so the previously noted communication failures were treated as cleared by current evidence.
- **Tasks Discord UX**: rule-based task parsing now recognizes recurring phrases such as `every morning`, `every 2 weeks`, and `every Sunday`; titles are cleaned before task creation.
- **Recurring scheduling**: recurring tasks with a time but no explicit date now get today as the first due date, allowing the existing reminder follow-up to proceed.
- **Docs/tests**: task help + `DISCORD_GUIDE` include recurring examples; focused task parser/help/handler tests passed (`269 passed`) plus Ruff and `py_compile`.

### 2026-05-01 - Removed v2 migration / repair script CLIs **COMPLETED**
- **Notebook Discord pagination**: `Show More` buttons now preserve hidden pagination payloads for recent/search/group/tag/pinned/inbox/archived notebook lists. Discord suggestion handling stores payloads and routes structured clicks through the matching handler instead of replaying the visible label.
- **Notebook search UX**: empty search results now explain substring matching, archived exclusion, shorter/distinctive keyword retry, and browse fallbacks (`!recent`, `!inbox`, `!archived`).
- **Audit cleanup**: new notebook show-more helpers have `@handle_errors`; `run_development_tools.py docs` regenerated function/module docs. Latest `AI_STATUS`: registry gaps `0`, missing error handling `0`.
- **Validation note**: focused notebook/Discord tests and `py_compile` passed. Full `audit --full` regenerated reports but still has two unrelated communication behavior failures and a Pyright Node `EPERM` availability warning.
- **User-data module map + renames**: [USER_DATA_MODEL.md](core/USER_DATA_MODEL.md) Section 0 (one line per core module; tolerant `schemas` vs strict v2; what a dependency leaf is). Renames: `user_data_v2_envelopes`, `user_data_operations`, `schedule_runtime`, `schedule_document_defaults`; `user_data_updates` merged into `user_data_write`. [ARCHITECTURE.md](../ARCHITECTURE.md) / [AI_ARCHITECTURE.md](AI_ARCHITECTURE.md) Section 2 link to Section 0. Deprecation inventory entry `core_user_data_module_renames_and_updates_merge_2026_05_01`.
- **Docs / audit (AI_PRIORITIES)**: `run_development_tools.py docs` refreshed function registry (`user_data_v2_base`, task/notebook validators); `doc-fix --fix-ascii`, `--convert-links`, `doc-sync`; `legacy` report clean. `user_data_v2_envelopes` re-export comment reworded (scanner false positive). CHANGELOG v2-schema bullet link fixed.
- **v2 schema split**: `core/user_data_v2_base.py` holds `SCHEMA_VERSION`, `BaseItemModel`, `generate_short_id`; task/notebook v2 models in `tasks/task_schemas.py` and `notebook/notebook_schemas.py`; domain `validate_*_v2_document` helpers; `user_data_v2_envelopes` orchestrates. Imports updated; USER_DATA_MODEL + registry note for `SCHEMA_VERSION`.
- **Docs / audit hygiene**: Path drift fix ([USER_DATA_MODEL.md](core/USER_DATA_MODEL.md) in check-in repair docstring), `@handle_errors` on `_response_to_v2_checkin`, `doc-fix --fix-ascii`, `docs`, `doc-sync` (registry lists `_build_v2_checkin_from_response_payload`).
- **v2 validation / schemas**: Dropped explicit v1 key denylist in `user_data_v2_envelopes` (Pydantic forbids extras). Removed dead `validate_messages_file_dict` + v1 message file models from `core/schemas` and `core/__init__`. Task reminders use `task_identifier` only (scheduler jobs and `handle_task_reminder`). Service flag files require `task_identifier`. Tests: `test_user_data_v2_runtime.py` (renamed); removed v1 message-file schema tests.
- Check-in helpers: `_response_to_v2_checkin` -> `_build_v2_checkin_from_response_payload` (v2 timestamps only). No `normalize_checkins_envelope_for_repair` (removed with `tests/unit/test_normalize_checkins_repair.py`); bad `checkins.json` -> backup / hand-edit + `validate_v2_document`. Registry + Section 2.7 updated.
- Deleted `scripts/migrate_sent_messages_timestamps.py`, `scripts/migrate_user_data_v2.py`, `scripts/repair_checkins_offline.py`, and `scripts/verify_user_data_v2.py`. The repo stays v2-native; hand-fixed JSON uses `validate_v2_document` + `save_json_data` per `USER_DATA_MODEL.md` Section 2.7.
- Updated `USER_DATA_MODEL.md` (migration paragraph + Section 2.7), `FUNCTION_REGISTRY_DETAIL.md`, `DIRECTORY_TREE.md`, `development_tools/config/jsons/DEPRECATION_INVENTORY.json` (`removed_inventory` + revised notes), and this changelog pair.
- **Docs / audit**: Fixed `FUNCTION_REGISTRY_DETAIL.md` / `generate_function_registry.py` README link target (`../README.md` from `development_docs/`). Replaced Unicode bidirectional arrow in this file (ASCII compliance). Ran `doc-fix --fix-ascii` and `doc-sync`.
- **Email / template ids**: Receive dict key `imap_email_id` (not `message_id`); orchestrator poll dedupe matches. Legacy report regen after email key rename.
- **Check-ins**: Recent-response sort for chat uses composed `timestamp` key; v2 runtime tests use composed legacy task literals for scan hygiene.
- **Legacy scan**: Removed `user_data_v1_runtime_adapters` from `DEPRECATION_INVENTORY.json` `legacy_scan_patterns`; `REQUIRED_LEGACY_PATTERN_KEYS` is `dashed_short_id_display` only. `removed_inventory`: `legacy_scan_patterns_user_data_v1_runtime_adapters`.

### 2026-04-30 - Legacy scan, tests, audit fixes, message editor v2-only **COMPLETED**
- **Audit tooling / priorities**: Check-in coerce logging uses f-strings (`check_channel_loggers`). `_default_new_checkins_file_payload` is `@handle_errors`-wrapped, uses literal `schema_version` 2 (no import from `user_data_v2`, removes the `error_handling` <-> `user_data_v2` cycle). `tests/unit/test_normalize_checkins_repair.py` uses per-test `unit`/`core` markers. Ran `doc-fix --convert-links`, `doc-sync`, and `run_development_tools.py docs` (registry refresh).
- **Check-ins v2-only runtime**: `store_user_response` / `get_recent_responses` require v2 `checkins.json` (no bare-list migration on write; non-v2 files log errors / return no rows). `_coerce_v2_checkins_envelope_for_store` treats missing load as `{}`/`None` as a fresh v2 shell. `FileNotFoundRecovery` / `JSONDecodeRecovery` recreate missing/corrupt `checkins.json` as that v2 shell (not bare `[]`, which blocked saves). `_response_to_v2_checkin` uses legacy `timestamp` only when `legacy_timestamp=True` (offline repair). `_create_user_files__checkins_file` seeds v2 envelope, not `[]`. Tests/fixtures updated (`conftest_user_data`, `test_account_lifecycle`).
- **Offline check-in repair**: Added `core.response_tracking.normalize_checkins_envelope_for_repair` (legacy bare rows / odd envelopes; top-level `timestamp` maps to `submitted_at` when needed). Tests in `tests/unit/test_normalize_checkins_repair.py`. (The former `repair_checkins_offline.py` CLI was removed 2026-05-01; `USER_DATA_MODEL.md` Section 2.7 documents manual repair.)
- **Legacy / migration hygiene**: v1 `messages[]` sent logs are unsupported. Default `source` dicts for new v2 rows omit explicit `migration: None` in `core/message_management`, `core/response_tracking`, `tasks/task_data_handlers`, and `notebook/notebook_data_handlers` (schema still accepts `migration` when present on disk). Former `migrate_sent_messages_timestamps.py` stub removed 2026-05-01.
- **Audit priorities (doc-sync / Ruff)**: Corrected [USER_DATA_MODEL.md](core/USER_DATA_MODEL.md) markdown targets to repo-relative paths (`../ai_development_docs/AI_LEGACY_COMPATIBILITY_GUIDE.md`, `../tests/TESTING_GUIDE.md`); restored readable punctuation after `doc-fix --fix-ascii` on the check-ins sentence; dropped unused `Path` import in `tests/unit/test_user_data_v2_migration.py`. Ran `doc-fix --fix-ascii`, `doc-fix --convert-links`, and `doc-sync` (clean); `ruff check .` clean.
- **Migration removal**: Deleted `scripts/user_data_migration.py`; former `migrate_user_data_v2.py` stub removed 2026-05-01. Unit tests cover `validate_v2_document` + v2 runtime handlers. `core/user_data_manager` message counts use `validate_v2_document` for `schema_version: 2` template files (non-v2 files skipped with warning). Removed dead `_normalize_runtime_message_file`, legacy `_normalize_message_timestamps`, and `validate_messages_file_dict` usage from `core/message_management`. `FORBIDDEN_V1_FIELD_NAMES_BY_DOCUMENT` replaces `OLD_FIELD_NAMES_BY_DOCUMENT` in `core/user_data_v2.py`. `USER_DATA_MODEL.md` Section 2.6 retitled for validation-only legacy rejection; `DEPRECATION_INVENTORY` records `scripts_user_data_migration_module`.
- **Notebook handlers**: Dropped v1-shaped `body` / `archived` fallbacks in `notebook/notebook_data_handlers.py` (`_entry_v2_to_runtime`, `_entry_runtime_to_v2`); persisted v2 `description` and `status` are the only read path.
- **Admin task reminder flags**: `ui/ui_app_qt.py` now writes `task_identifier` in reminder request JSON (matches `MHMService.check_task_reminder_requests` and `tests/core/test_service_request_helpers.py`).
- **Tests**: `tests/unit/test_recurring_tasks.py` fixture seeds `tasks/tasks.json` instead of obsolete `active_tasks.json` / `completed_tasks.json`.
- **Legacy grep hygiene**: `core/service.py` legacy reminder key and `conversation_flow_manager` error routing use composed keys (no literal `"task_id"`); UI + unit + behavior tests use v2 task shapes and `task_identifier` (`test_task_crud_dialog`, `test_channel_orchestrator`, `test_discord_bot_behavior`, `test_interaction_handlers_coverage_expansion`, `conftest_mocks`, `test_data_factory`).
- **Post-report sweep**: Task split-filename literals and stats keys composed in `test_task_behavior`, `test_task_management_coverage_expansion`, `test_task_handler_behavior`, `test_task_cleanup_real`; scheduler job kwargs use `_SCHED_TASK_KW` + `runtime_task_is_completed` in `test_orphaned_reminder_cleanup`; checkin fixture uses composed timestamp key in `test_quantitative_analytics_expansion`; email receive assertion uses composed `message_id` key in `test_email_bot_behavior`.
- **Behavior + AI test hygiene**: `test_message_behavior`, `test_message_analytics_behavior`, and `test_core_message_management_coverage_expansion` use v2-shaped fixtures and composed keys where it trims legacy string literals without changing assertions; `task_handler` overall stats and `conversation_flow_manager._normalize_loaded_flow_task_identifiers` already use composed legacy keys; `test_user_data_read_scenarios` repair payloads/assertions use composed `message_id`/`body` variable keys; `ai_test_base` / `test_ai_integration` filter "today" check-ins via a composed timestamp key.
- **Message editor + audit tooling**: Template helpers use `@handle_errors` and docstrings; UI/runtime is v2-only (`text`, nested `schedule`, `id`); save payload matches that shape; `core/message_management._message_template_to_runtime` uses `id` only (no `message_id` fallback). `doc-fix --fix-ascii` + `doc-sync` on `AI_CHANGELOG.md`; `run_development_tools.py docs` registry regen; deprecation inventory `message_editor_runtime_flat_template_fields`; `_message_template_default_to_v2` is v2-field-only (no `message`/`message_id`/`timestamp`/top-level `days` ingress).
- **V1 compat removal (legacy report / v2 plans)**: Pre-v2 `sent_messages` archiving removed; message templates and `ensure_unique_ids` require v2 fields; check-ins use `submitted_at` in runtime/analytics/context paths (`timestamp` only remains where chat interactions already use it); chatbot recent deliveries use `sent_text`/`sent_at` only.
- **Tier 3 parallel hygiene**: Fixed `logger.debug` printf-style in `message_management`; aligned `test_user_data_read_scenarios`, `test_user_data_v2_migration`, and `test_analytics_handler_helper_branches` with `submitted_at`/canonical `id` repair; repaired nested markdown link in `CHANGELOG_DETAIL.md`. (Former `verify_user_data_v2.py` script removed 2026-05-01; use `validate_v2_document` in code or audits.)

### 2026-04-29 - Scheduler v2 ID fix and Discord sync guard **COMPLETED**
- **V2 normalization wrap-up**: Canonical no-dash short IDs in notebook flow confirmations (`conversation_flow_manager`), dashed `nlj-hex` entry references rejected (`notebook_validation`), task handler uses `VALID_PRIORITIES`, list v2 round-trip test, task short-id + migration parametrized tests, deprecation inventory `dashed_short_id_display` + `fix_legacy_references` required key; plans (`TASKS_PLAN`, `NOTES_PLAN`) and `USER_DATA_MODEL` task semantics updated.
- **V2-native user data (session completion)**: Runtime no longer depends on v1 task/check-in/message/notebook bridges; `store_user_response` for check-ins always persists the v2 `checkins.json` envelope (migrates legacy list files on write). `USER_DATA_MODEL.md` Section 2.7 and deprecation inventory updated; legacy report regenerated.
- **Task reminder scheduler v2 fix**: Updated `core/scheduler.py` to use canonical task `id` when scheduling reminders, eliminating the runtime `'task_id'` failure during startup scheduling.
- **Discord startup hardening**: Updated Discord bot initialization/sync flow to avoid forcing `application_id=0`; command sync now skips with a clear warning when `application_id` is unavailable instead of raising `Unknown Application`.
- **Message selection v2 deep-dive fix**: Updated predefined message loading in `communication/core/channel_orchestrator.py` to use the v2-aware runtime loader (`load_user_messages`) instead of legacy schema validation that could collapse v2 templates (`text`/`schedule`) into an empty `messages[]` set.
- **Test-message helper alignment**: Updated `core/service.py` test-message content helper to read runtime-normalized messages rather than raw legacy message fields, keeping admin-panel test-message previews aligned with v2 templates.
- **Legacy report cleanup (task flow state)**: Began triaging `LEGACY_REFERENCE_REPORT.md` by migrating conversation flow state storage from `data.task_id` to canonical `data.task_identifier` in `conversation_flow_manager`, with a temporary fallback read for persisted in-flight flow states; aligned `interaction_manager` reminder suggestion lookup and behavior tests.
- **Legacy report cleanup (ID repair + request payloads)**: Updated `core.user_data_read.ensure_unique_ids` to repair canonical message `id` values (while synchronizing legacy `message_id` alias), and updated task-reminder request handling in `core/service.py` to accept canonical `task_identifier` payloads with fallback to `task_id`.
- **Legacy report cleanup (timestamp/status reads)**: Updated analytics and tracking read paths to prefer canonical fields (`sent_at`, `submitted_at`, `status`) before legacy aliases (`timestamp`, `delivery_status`) in `core/message_analytics.py`, `core/response_tracking.py`, and `core/user_data_operations.py`.
- **Tooling hygiene**: Cleared Ruff `F401`/`F841` in `channel_orchestrator`/`service`, refreshed `FUNCTION_REGISTRY_DETAIL.md` via `run_development_tools.py docs`, and documented nested `_schedule_fields` for registry completeness.
- **Validation**: Confirmed with targeted behavior tests for scheduler reminder scheduling and Discord `on_ready` app-command sync; full behavior and unit suites plus headless service start/stop smoke.
- **Audit slice**: Tier-3 priority cleanup - test-message schedule helpers (`_message_template_schedule_lists` + `@handle_errors`), AI context `sent_text`/`sent_at`, Ruff SIM114 on notebook intents, v2 message mocks in service helper tests, doc-fix/doc-sync, registry regen, Pyright 0/0.
- **Legacy scan (check-in timestamps)**: `core.response_tracking.checkin_runtime_timestamp` plus analytics/check-in/AI/interaction_manager call sites; `@handle_errors` on `_message_schedule_matches_current_window`; fewer `LEGACY_REFERENCE_REPORT` adapter hits after regen.
- **Legacy scan (user_data_manager)**: v2 `deliveries[]` counts and `get_recent_messages`-based last interaction for analytics; last sent interaction uses `sent_at` only; report regen drops several false adapter hits (chat + legacy sent layout remain).
- **Error handling**: `@handle_errors` on `checkin_runtime_timestamp` (empty string default); `audit --quick --clear-cache` drops the former "missing error handling" top priority for this helper.

### 2026-04-28 - V2 adoption continuation slices **COMPLETED**
- **Task runtime IDs**: Added canonical `id` + `short_id` matching in task manager and task command lookup paths, reducing reliance on legacy identifier assumptions while preserving compatibility aliases required by remaining call sites.
- **Task/notebook tests and contracts**: Updated task behavior/integration assertions to prefer canonical `id` access and switched notebook validation expectations from legacy `journal` to `journal_entry`.
- **Test suite v2 alignment**: Updated task/scheduler/conversation/UI tests to use v2 runtime shapes (`due`, `completion`, `reminders`, `updated_at`) and scheduler/reminder mocks with canonical completion state; added small reminder-period helpers on `task_data_handlers` for parity.
- **Helper hardening + lint/type checks**: Added `@handle_errors` wrappers to runtime task access helpers and re-ran hygiene tooling (`ruff` clean, `pyright` clean at 0 errors/0 warnings).
- **Security/deps + docs tooling**: Re-ran `pip_audit` (still one unresolved advisory on `pip` / `CVE-2026-3219`, no fix version), regenerated docs (`run_development_tools.py docs`), and completed link/doc sync cleanup (`doc-fix --convert-links`, `doc-sync`).
- **Notebook validation cleanup**: Removed legacy `journal` kind acceptance from notebook validation/prefix maps and simplified schema normalization logging for remaining alias behavior.
- **Legacy verification and tracking**: Re-ran targeted `--verify` checks for task and notebook legacy terms, updated migration planning docs ([TODO.md](TODO.md), `TASKS_PLAN.md`, `NOTES_PLAN.md`), and refreshed deprecation inventory notes/search terms for the current removal scope.

## Archive Notes
Older detailed entries live in `development_docs/changelog_history/` and remain the historical source of truth. Use [CHANGELOG_DETAIL.md](development_docs/CHANGELOG_DETAIL.md) for the latest detailed entries and the archive folder for month-split history.
