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

### 2026-05-25 - Tier 3 coverage and parallel test cleanup **COMPLETED**
- Fixed dev-tools coverage reporting so cache-only payloads include canonical `coverage_outcome`, clean collected coverage is not reported as failed after Windows interrupt handling, and low-coverage priorities count all below-target domains.
- Cleaned test domain markers for scheduler coverage tests and verified `analyze_test_markers.py --check`.
- Stabilized parallel tests by locking test user index updates and giving Discord task-reminder behavior tests unique per-test users with explicit setup assertions.
- Added first-class `checkins`, `messages`, and `storage` product domains in `domain_mapper` / `local_module_prefixes` (marker-only test mapping like `tasks`), aligned code defaults, Bandit roots, setuptools includes, and a package policy test.
- Cleared AI_PRIORITIES error-handling noise: `error_handling_exclude` on `_apply_fields_filter` and v2 schema validators; shared `timestamp_sort_key_from_dict` for sort helpers; `duplicate_functions_exclude` on intentional delegates.
- Fixed check-in analytics test failures by restoring `parse_timestamp_full` in `checkin_data_manager` (regression from sort-key refactor), correcting check-in test `get_user_file_path` patches, and clearing Ruff unused-import findings.
- Regenerated function registry via `run_development_tools.py docs`; Tier 3 parallel failures (`test_remove_schedule_period`, `test_user_data_access`) pass locally (stale audit log).
- Focused verification passed for dev-tools coverage/audit helpers, scheduler marker tests, and Discord reminder follow-up behavior under normal, seeded, and xdist runs.

### 2026-05-24 - Communication architecture cleanup **COMPLETED**
- Scheduler now resolves account `timezone` (fallback America/Regina) for messages, check-ins, and task reminders; one-time reminders use aware past/future checks via `scheduler/user_timezone.py`
- Added unit tests for timezone resolution and `schedule_task_reminder_at_datetime` past/future behavior
- Reviewed and acted on `communication/` channel-agnostic boundaries, with focus on `CommunicationManager`, email inbound handling, Discord send/health behavior, reminders, and shared help text
- Moved inbound email polling/replies to `communication/communication_channels/email/inbound_processor.py`, recipient lookup to `communication/delivery/recipient_resolver.py`, and rich view creation through channel-local interaction-view factories
- Removed Discord direct-send shortcuts and `get_discord_connectivity_status()` from `CommunicationManager`; callers now use generic channel status, and tests target new adapter APIs instead of preserving compatibility wrappers
- Addressed current audit items for missing docstrings, email inbound error handling, function registry sync, duplicate status methods, and stale behavior test patch targets

### 2026-05-23 - Message and check-in domain packages **COMPLETED**
- Created first-class `messages/` and `checkins/` packages for automated message storage/analytics/preview, check-in storage/service/dynamic questions/analytics, and their v2 schemas
- Removed `core.message_*` and `core.checkin_*` modules; production imports now point directly at the domain packages, with `core.response_tracking` reduced to generic chat/response tracking plus check-in delegation
- Moved message/check-in schema ownership out of `storage.user_data_v2_envelopes.py` while preserving validation dispatch and compatibility re-exports
- Focused verification passed for message/check-in storage, analytics, schema validation, command handlers, and AI recent-message context

### 2026-05-23 - Post-refactor architecture decisions closed **COMPLETED**
- Closed the deferred service/scheduler/dispatcher cleanup TODOs after reviewing current startup, scheduler delivery ports, service request delivery, retry ownership, and package boundaries
- Documented decisions in [COMMUNICATION_GUIDE.md](../communication/COMMUNICATION_GUIDE.md): keep `CommunicationManager` as runtime owner/singleton, keep retry queueing in `communication/core/retry_manager.py` for now, and avoid new top-level message/check-in packages until concrete ownership pressure appears
- Confirmed task-reminder scheduling bodies are already split into `scheduler/task_reminders.py`; retained only public wrappers/call sites in `scheduler/manager.py`
- Cleared the completed high-priority architecture cleanup block from [TODO.md](../TODO.md)

### 2026-05-23 - Analytics handler split and audit cleanup **COMPLETED**
- Split `AnalyticsHandler` into check-in, trend, task, and shared formatting handlers; removed duplicated task-stats implementation from `TaskManagementHandler`
- Updated analytics/task behavior tests to assert current canonical behavior instead of legacy compatibility paths
- Fixed documentation drift from the archived system AI overhaul plan and regenerated docs/registry/report outputs
- Stabilized audit tooling: pip-audit uses a temp cache and full Tier 3 audit now passes with test suite, doc-sync, and static-analysis signals clean

### 2026-05-22 - Conversational boundaries and task NLP parsing **COMPLETED**
- Audit hygiene: `@handle_errors` on `action_boundaries.py`; Ruff `re.Pattern` import; path drift in [TODO.md](../TODO.md); doc-sync clean after link fixes
- Added `ai/conversational_context/action_boundaries.py` (false CRUD claim detection) and **ACTION BOUNDARIES** rules in `instructions.py`
- New `tests/behavior/test_conversational_action_boundaries.py`: prompt contract, safe vs unsafe samples, `AIResponseValidator` integration, fallback regression
- Tasks Section 2: expanded `_extract_task_entities` (due phrases, title cleanup, priority/tags/group); `parse_relative_date` for tonight/this week/before-by weekday; tests in `test_command_parser_task_entities_expansion.py`
- Task due tweaks: `this week` on Sat/Sun -> end of coming week; `tonight` default time 18:00 (not 21:00)
- [TASKS_PLAN.md](../development_docs/TASKS_PLAN.md) Section 5.1: backlog for per-user customizable NL timeframes (`tonight`, after work/school, time-of-day defaults); parser accepts `after school` same as `after work`
- Task command discovery (Section 2.1): `TASK_HELP_TEXT`, richer `get_examples()`, `help tasks` / `examples tasks` delegate to `TaskManagementHandler`
- Test/doc hygiene: fixed 3 Tier-3 failures (task `group` in prepare_create_task_data, NL title stripping, discord help tasks); `doc-fix --fix-ascii` on changelogs
- Security/docs: `idna>=3.15` floor (CVE-2026-45409); regenerated `verify_process_cleanup_results.json` for dev-tools report link target

### 2026-05-21 - System AI overhaul closed; post-overhaul work started **COMPLETED**
- Marked [SYSTEM_AI_OVERHAUL_PLAN.md](../archive/SYSTEM_AI_OVERHAUL_PLAN.md) and [PLANS.md](../development_docs/PLANS.md) Section 5.0 **COMPLETED**; added active Section 5.0.1 post-overhaul AI quality plan
- [TODO.md](../TODO.md): NLP, command list, response times, and actionability sprint moved from deferred to active
- First implementation increment: expanded `command_interpreter` mode-detection vocabulary, simplified `command.txt` actions placeholder, actionability instructions in `conversational_context/instructions.py`, regression tests
- Command list: documented live injection paths in [SYSTEM_AI_GUIDE.md](../ai/SYSTEM_AI_GUIDE.md) Section 3.4; added `tests/unit/test_command_prompt_injection_live_path.py`
- Actionability audit: `is_automated_messages_enabled()` in `core/response_tracking.py`; gated recent sends and schedule context; guide Section 4.3; `tests/unit/test_conversational_context_actionability.py`
- Audit priorities: fixed path drift in [TODO.md](../TODO.md) and [SYSTEM_AI_GUIDE.md](../ai/SYSTEM_AI_GUIDE.md); registry regen for `is_automated_messages_enabled`; fixed `test_context_includes_recent_messages` for automated-messages gating; cleared completed TODO checkboxes (command list + actionability subtasks)
- Parallel Tier 3 flake: hardened `test_get_user_data_fields_scalar_list_and_dict` with `clear_user_caches`, on-disk preferences guard; 8x `-n 8` file runs pass

### 2026-05-20 - Shared check-in analytics and service request cleanup **COMPLETED**
- Removed thin `MHMService._check_test_message_requests__*` / `_check_reschedule_requests__*` delegates; reschedule paths use `to_service_request_context()`; tests call `core.service_requests` directly
- `analyze_recent_checkin_rows()` in `context_builder.py`; fallback `checkin_summary` uses `ContextAnalysis` (dropped duplicate `compute_checkin_metrics`); parity tests in `test_context_analytics_shared_source.py`
- `SYSTEM_AI_GUIDE.md` updated; completed service/check-in items cleared from [TODO.md](../TODO.md); recovery default JSON unified in `error_handling.py` (`@handle_errors` on `_recovery_default_document_for_path`); intentional `not_duplicate` for schedule time conversion + account creator collect steps; `clear_user_caches()` in user-index UI test + parallel-hardened `test_remove_message_category` integration test; function registry lists recovery helper
- Parallel Tier 3: `get_user_data` test-only assembly now runs the same finalize path as primary loads (`normalize_on_read`, schedules shape, `_metadata`); `_finalize_get_user_data_payload` helper in `storage/user_data_read.py`; `fix_user_data_loaders` autouse fixture resets canonical `USER_DATA_LOADERS` each test so stub loaders cannot leak across scenarios
- Parallel flake remediation: `test_add_message_category` / removal-branch asserts now read preferences via `get_user_data(..., "preferences")` with cache clears (`integration/test_account_lifecycle.py`); `test_remove_message_category` aligns similarly; `test_create_account_updates_user_index` marked `@pytest.mark.no_parallel` like sibling checks-ins UI test and uses one `wait_until` for index + active (avoids shared `users_index` races under xdist with a redundant follow-up `build_user_index()`)
- Tier 3 run_test_suite parallel crash: `task_management_user` fixture in [`test_task_management_dialog.py`](../tests/ui/test_task_management_dialog.py) failed setup when `internal_username` lookup lagged under load (~3s retry too short); now requires `create_basic_user` success and resolves UUID via `wait_until` up to 30s (matches other UI stabilization patterns)

### 2026-05-19 - AI helpers, file prompts, context calculate/phrase split **COMPLETED**
- Extracted LM Studio HTTP and response post-process from `chatbot.py` into `lm_studio_client` / `response_postprocess`
- Companion and command prompts under `resources/prompts/`; `context_phraser.py` phrases facts from `ContextBuilder.analyze_context`
- Lazy `command_registry` import fixes circular load with `command_parser`
- Removed legacy context bullet helpers and `sections.py`; tests on `context_phraser`
- Documented `command_registry` -> `command_parser` adapter; import-boundary tests under `test_ai_import_boundaries.py`

### 2026-05-19 - Dev tools cache + AI fallback Phase 4.5 **COMPLETED**
- **Conversational context split**: Extracted comprehensive prompt assembly from `response_generator.py` into `ai/conversational_context/` (sections, assembly, instructions); check-in aggregates reuse `ContextBuilder.analyze_context`; `ai/__init__.py` exports fallback package, command/response modules, and interaction types; `@handle_errors` on all section helpers (replaced ad-hoc try/except); function registry regenerated via `docs`
- **Phase 4.5**: Split `ai/fallback_responses.py` into package (`coordinator`, `checkin_summary`, `conversational`, `personalized`, `profile_helpers`, `categories`); explicit `FallbackCategory`; ownership documented in `SYSTEM_AI_GUIDE.md`
- Facade API unchanged (`get_fallback_responses().contextual` / `.personalized`); import-boundary and category tests in `test_fallback_responses.py`
- Dev-tools logging: handled outcomes (audit lock block, internal interrupt signature, tool-guide timeout) now log at WARNING so Tier 3 pytest does not write false ERROR lines to `ai_dev_tools.log`
- Tier 3: `verify_process_cleanup` runs after parallel groups (post-pytest) instead of alongside `run_test_suite` startup, avoiding Windows SIGINT/site-import subprocess failures during audits
- Dev-tools pytest: preserve `MHM_TESTING=1` in `run_test_suite` subprocess; `MHM_TESTING=0` overrides pytest context for rotation tests; audit log bleed reduced
- Audit priorities: Pyright clean on `ai/fallback_responses/`; docstrings on profile/conversational helpers; `@handle_errors` on full fallback package including `personalize_with_profile_name`; `SYSTEM_AI_GUIDE.md` path drift cleared (doc-sync PASS)
- `test_file_suite_cache.py` shares domain invalidation with coverage cache; per-test-file JUnit outcomes + full snapshot skip
- `run_test_suite --no-domain-cache` disables; cleanup removes `test_file_suite_cache.json`
- Audit metadata reports `cache_mode` (cache_hit / selective_run / full_run)
- Doc-sync path drift cleared (qualified `tests/test_file_*_cache.py` references); Ruff clean on suite cache module
- Fixed selective suite run running full suite when per-file cache mapping was cold; pinned flaky domain attribution test
- Persist pruned deleted test paths to disk so ghost entries (e.g. removed `test_directory_taxonomy_policy.py`) stop re-invalidating `development_tools` every audit
- Fixed parallel-only flake in `test_get_user_data_fields_scalar_list_and_dict`: field-filtered reads skip test healing/shim full-document backfill
- Failed-domain recording scoped to failing tests only; cache path keys normalized on Windows
- Pyright: `update_run_status` callers pass sets, not sorted lists
- **AI Phase 5:** Removed one-line facade delegates from `ai/chatbot.py`; orchestration calls `get_fallback_responses()`, `get_command_interpreter()`, and `get_response_generator()` directly; tests/docs updated (`SYSTEM_AI_GUIDE.md`, overhaul plan Section 8.1)
- **Duplicate-function triage:** Shared `_discover_flag_request_files` in `core/service_requests.py`; collapsed `CommunicationManager.get_recipient_for_service` (removed private twin); removed `TaskSettingsWidget.get_available_tags` passthrough; `not_duplicate` only where behavior genuinely differs (dataclass defaults, channel status checks, parsers/processors)
- **Audit quick wins:** `@handle_errors` on `_discover_flag_request_files`; registry regen via `docs`; ASCII fix in `PLANS.md`; TODO added for dedicated `MHMService._check_*__*` delegate removal pass
- **Parallel test flake:** `test_create_account_updates_user_index` - `build_user_index` account.json fallback + retry alignment with `update_user_index`; test uses `wait_until` for index visibility

### 2026-05-18 - System AI Overhaul Phases 1-4 **COMPLETED**
- Named AI interaction types (`ai/interaction_types.py`) and added structured logging on generate/fallback paths
- Extracted fallback, command interpretation, and conversational generation into `ai/fallback_responses.py`, `ai/command_interpreter.py`, and `ai/response_generator.py`; `ai/chatbot.py` remains the public facade
- Wired clarification-specific command prompt text; dynamic command intent list via `ai/command_registry.py` and `get_rule_based_intent_names()`
- Added boundary unit tests; updated [SYSTEM_AI_GUIDE.md](../ai/SYSTEM_AI_GUIDE.md), [PLANS.md](../development_docs/PLANS.md), [TODO.md](../TODO.md), and [SYSTEM_AI_OVERHAUL_PLAN.md](../archive/SYSTEM_AI_OVERHAUL_PLAN.md) header path
- Audit follow-up: `@handle_errors` on facade delegates and module getters, Ruff unused-import cleanup, `response_generator` import fix, `not_duplicate` on context-prompt facade, `test_no_prints_policy` fix, docs/registry regeneration
- Legacy-guide alignment: documented refactor facade vs `LEGACY COMPATIBILITY` bridges in `SYSTEM_AI_GUIDE.md`; clarified `DEPRECATION_INVENTORY` note for removed `_get_fallback_response` vs current `fallback_responses` path
- Documented **Phase 5 (collapse facade delegates)** in `SYSTEM_AI_OVERHAUL_PLAN.md` Section 8.1 and [PLANS.md](../development_docs/PLANS.md) Section 5.0
- Audit quick wins: ASCII in [PLANS.md](../development_docs/PLANS.md), markdown links in changelog; hardened `test_domain_attribution_summary_via_analyzer_ast_scan` (instance-scoped `find_test_files` patch)
- Dev-tools log rotation: `AuditDeferredRotatingFileHandler` defers `ai_dev_tools.log` rollover for 15 minutes while audit/coverage lock files are active (avoids Windows rename errors during Tier 3); Ruff SIM105 fix in `logging.py`

## Archive Notes
Older detailed entries live in `development_docs/changelog_history/` and remain the historical source of truth. Use [CHANGELOG_DETAIL.md](../development_docs/CHANGELOG_DETAIL.md) for the latest detailed entries and the archive folder for month-split history.
