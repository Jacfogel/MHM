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

### 2026-05-12 - Core UI Widget Boundary Cleanup **COMPLETED**
- Moved PeriodRowWidget creation/layout/removal/data collection helpers from `core.ui_management` into new `ui.period_row_management`.
- Kept `core.ui_management` limited to UI-neutral period naming and numbering helpers, and removed the package-level core exports for widget helpers.
- Updated task/check-in/schedule editor callers and focused tests; removed the completed TODO item.
- Validation: focused UI/helper tests passed and static search confirms `core/ui_management.py` no longer imports `ui` or Qt.

### 2026-05-11 - Command-handler service thinning and dependency audit cleanup **COMPLETED**
- Moved task, check-in, and profile command-domain decisions into service helpers while keeping communication handlers responsible for ParsedCommand routing and InteractionResponse formatting.
- Preserved current handler patch boundaries/Discord behavior, added service-focused tests, fixed the profile show regression, and marked the task stats facade duplicate as intentional with the supported analyzer marker.
- Raised `urllib3` to `>=2.7.0` and upgraded the local venv; direct `pip-audit --format json` reports no known vulnerabilities.
- Validation: focused profile/task/check-in tests, marker analysis, duplicate analysis, `py_compile`, `doc-fix --convert-links`, `doc-sync`, direct pip-audit, and standard audit passed. Cache-cleared full audit was killed with exit 137, so it is not counted as clean full-audit validation.

### 2026-05-11 - Ignored project script retirements **COMPLETED**
- Retired ignored `scripts/cleanup_windows_tasks.py`; tracked scheduler cleanup in `core.scheduler_maintenance.cleanup_scheduler_wake_tasks` is the owner now.
- Retired ignored `scripts/create_project_snapshot.py`; use `backup_manager.create_backup(include_code=True)` for restorable backups and `export-code` / `export-docs` for AI-readable snapshots.
- Retired ignored `scripts/utilities/user_data_cli.py` instead of migrating it; tracked `core.user_data_operations` remains the canonical user-data owner.
- Updated backup docs, PLANS, and TODO so active guidance no longer points at ignored project scripts; the backup reliability plan is complete.

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

## Archive Notes
Older detailed entries live in `development_docs/changelog_history/` and remain the historical source of truth. Use [CHANGELOG_DETAIL.md](../development_docs/CHANGELOG_DETAIL.md) for the latest detailed entries and the archive folder for month-split history.
