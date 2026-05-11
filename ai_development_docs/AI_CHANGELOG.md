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

### 2026-05-11 - Audit/run_tests suite parity and no_parallel cache scope **COMPLETED**
- `audit --full` coverage now runs serial `no_parallel` tests only for the same domain-filtered file set as the parallel phase; scoped runs with no matching serial tests are classified as skipped, not crashed.
- `run_tests.py --mode all` now includes `tests/ai/` but still intentionally leaves development-tools tests to `run_tests.py --full`, which keeps the two-phase product/AI plus development-tools execution shape.
- Dev-tools test investigation refreshed: current collection is 1479 selected dev-tools tests, and the existing profiling command is `python run_tests.py --mode development_tools --durations-all`.
- Validation: focused coverage-runner helper tests, `py_compile`, and collection-only parity checks passed.

### 2026-05-11 - Dev-tools backlog and audit log cleanup **COMPLETED**
- Cleaned the active development-tools TODO block to remove completed migration/scoping/history items and keep only real follow-ups: Pyright parity, optional external-tool expansion, low-priority gap tools, and opportunistic `test_config.json` fixture migration.
- Extended Pyright parity policy tests with optional `PYRIGHT_WARNING_COUNT_MAX_DELTA` support, non-negative tolerance validation, and matching guide/V5 plan updates.
- Improved TODO sync dry-run output so manual-review items explicitly require changelog confirmation before removal; `sync-todo --apply` remains limited to auto-cleanable checked checklist lines.
- Fixed full-audit log noise from the intentional bad-syntax fixture: expected fixture parse failures now log at DEBUG instead of ERROR, and the stale function-registry test name was corrected.
- Validation: focused Pyright, TODO-sync, error-scenario, and analyze-functions tests passed; `py_compile` and `doc-sync` passed.

### 2026-05-11 - Soft channel-boundary core review **COMPLETED**
- Audited Discord/UI references in `core/config.py`, `core/logger.py`, `core/schemas.py`, `core/user_lookup.py`, `core/headless_service.py`, `core/service_utilities.py`, and `core/scheduler.py`.
- Classified Discord references in config, logging, schemas, and lookup as acceptable persisted/config/diagnostic knowledge; no Discord adapter behavior was found in these core modules.
- Removed the one misleading UI-specific source string from core reschedule request creation by making `create_reschedule_request()` use neutral `schedule_runtime` metadata by default.
- Reworded the new diagnostic-source docstring to avoid a false facade/shim compatibility signal; refreshed `facade-shims` and status outputs so `AI_PRIORITIES.md` no longer lists the advisory.
- Removed the completed plan item from active `PLANS.md`.

### 2026-05-11 - Runtime JSON storage cleanup **COMPLETED**
- Added `core/runtime_state_storage.py` and routed `conversation_states.json` / `welcome_tracking.json` through it, removing the direct runtime-state JSON reads/writes while preserving file locations and test isolation.
- Added `core/service_flag_storage.py` and consolidated JSON `.flag` request/response I/O across service request, service utility, and headless-service paths; shutdown flags remain plain text.
- `backup_manager` now reads `user_index.json` under `file_lock`; generated docs/reports were refreshed, and the module-dependency generator no longer emits trailing-space dependency headings.
- Removed the completed JSON storage classification/migration/service-flag cleanup work from active `PLANS.md`. Validation: focused storage/service tests, `py_compile`, `docs`, `audit --quick`, error-handling analysis, and `git diff --check` passed; full audit timed out and is not counted as clean.

### 2026-05-09 - Markdown link target audit and fixer **COMPLETED**
- Extended path-drift/doc-sync so local markdown links are checked from the source document directory, not only from the repo root, and `doc-fix --convert-links` rewrites auto-fixable repo-root-relative markdown hrefs to source-relative hrefs across documentation.
- Cleared the remaining advisory hints in `CHANGELOG_DETAIL.md` (backticked truly removed files, pointed `DUPLICATE_FUNCTIONS_INVESTIGATION.md` at the archive copy, updated four V5-relocated JSON references to their `scopes/full/` paths, noted the `core/user_data_v2.py` split). `doc-sync` is now down from 762 to 0 markdown-link-target hints.
- Scoped `LegacyReferenceFixer.required_pattern_keys` validation to only warn when running against the project that owns the loaded external config (added `config.get_loaded_config_file_path()`), so test fixtures no longer pollute `ai_dev_tools.log` with `dashed_short_id_display` warnings during `audit --full`.
- Validation: focused link-fixer / path-drift / legacy-cleanup / coverage-metrics tests pass without spurious warnings; Ruff and `doc-fix --dry-run` / `doc-sync` clean.

### 2026-05-08 - Generated report link fixes **COMPLETED**
- Fixed generated report markdown links that were written as repo-root-relative paths from nested report files, causing editor click-through failures.
- `AI_PRIORITIES.md` review links now resolve relative to `development_tools/`, and `LEGACY_REFERENCE_REPORT.md` guidance links now resolve relative to `development_docs/`.
- Added focused regression tests for both link-generation paths and removed the completed TODO item.

### 2026-05-07 - Dev-tools logging, audit exit, and priority cleanup **COMPLETED**
- Cleared the full-scope duplicate-function priority: `duplicate-functions --body-for-near-miss` now reports 0 issues and 0 groups; real duplication was refactored without adding legacy shim bridges.
- Development-tools logging now defaults to `development_tools/reports/logs/ai_dev_tools.log`, rotates at 1 MB with backups under `development_tools/reports/logs/backups`, and no longer recreates the root `logs/ai_dev_tools.log` path by default.
- Successful full audits now clear/restore SIGINT state and exit cleanly after ignored Windows console interrupts, preventing success output from returning exit code 1.
- Added missing error handling to cache/user lookup/service response helpers, regenerated registry/status outputs, and refreshed the stale aggregate report so the resolved error-handling, function-registry, and Pyright-warning priorities are gone.
- Validation: focused duplicate, service-request, logging, audit-signal/CLI, cache-manager, and shared-logging tests passed; Pyright is 0/0 and targeted Ruff checks passed.

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

## Archive Notes
Older detailed entries live in `development_docs/changelog_history/` and remain the historical source of truth. Use [CHANGELOG_DETAIL.md](../development_docs/CHANGELOG_DETAIL.md) for the latest detailed entries and the archive folder for month-split history.
