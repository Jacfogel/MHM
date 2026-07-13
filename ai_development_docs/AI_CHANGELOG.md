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

### 2026-07-13 - Register `integrations` pytest domain marker **COMPLETED**
- Registered `@pytest.mark.integrations` in `pytest.ini` and conftest hooks so `--strict-markers` collection no longer crashes on health context builder tests.
- Domain marker docs now list `integrations` alongside other product packages.

### 2026-07-12 - Use coarse Google Health signals in wellness fallbacks **COMPLETED**
- When `message_guidance` is empty or confidence is `low`, wellness replies now use coarse signal fields via `build_user_facing_signal_wellness_snippet()` in [`health_context_builder.py`](../core/health_context_builder.py).
- Check-in fallback cites partial metrics and can combine check-in + health reads.
- **Nightly CI fix**: full-suite orchestration timeout now allows parallel + no_parallel phases (~42 min); writes fallback `run_test_suite_nightly_results.json` when the subprocess is killed so GitHub Actions artifacts include failure context.
- Audit hygiene: doc path drift fixed; docstrings/`@handle_errors` on wellness helpers; pytest markers; Ruff SIM103; `doc-sync` PASS.

### 2026-07-11 - Wellness replies use Google Health when check-ins are weak **COMPLETED**
- Removed `how am i doing` from the rule-parser `status` intent so wellness questions reach contextual chat.
- Added shared health-wellness helpers in [`health_context_builder.py`](../core/health_context_builder.py): `format_health_guidance_for_user_reply`, `health_wellness_snippet_from_context`, `context_has_usable_health_wellness`.
- Extended [`wellness_status.py`](../ai/chat/wellness_status.py) and [`checkin_summary.py`](../ai/fallback/checkin_summary.py) to use `health_guidance_summary` / recent signals when check-in data is weak or missing; coordinator and envelope fallback pass health context through.
- Unit tests in `test_wellness_status.py`, `test_context_analytics_shared_source.py`, and `test_health_context_builder.py`.

### 2026-07-10 - Phase 0 reconciliation and planner routing parity **COMPLETE (slice 9.4 LM Studio gate)**
- Reconciled [`PRODUCT_AI_RESPONSE_INFLUENCE_AUDIT.md`](../ai/PRODUCT_AI_RESPONSE_INFLUENCE_AUDIT.md): Phase 0 COMPLETE; slice 9.4 items 1-7 COMPLETE (LM Studio gate met).
- Documented hybrid routing policy: rule-parser-first for high-confidence structured commands; planner on low-confidence when `AI_ACTION_PLANNER_ENABLED=true` (default remains off).
- Added full core task-intent parity behavior tests (8 intents) and non-task parity (check-ins, profile, schedules; 8 intents) in [`test_action_planner_routing.py`](../tests/behavior/test_action_planner_routing.py); 23 tests pass via `_run_intent_parity` / `_run_task_intent_parity`.
- Fixed profile update persistence in [`profile_service.py`](../user/profile_service.py): `update_user_context`/`update_user_account` plus UUID resolution for internal usernames (was silently failing via legacy `save_user_data` 3-arg call).
- Multi-action execution in [`action_plan_executor.py`](../communication/message_processing/action_plan_executor.py): runs `plan.actions` sequentially, combines completed handler messages, stops on follow-up (`completed=False`); 29 routing/executor tests pass.
- Planner multi-action parsing in [`action_planner.py`](../ai/chat/action_planner.py): repeating `ACTION:` blocks, shared defaults, per-action validation; tests in [`test_ai_action_planner.py`](../tests/unit/test_ai_action_planner.py); 18 planner/executor unit tests pass.
- Result-aware responses for all planner-path actions in [`action_plan_executor.py`](../communication/message_processing/action_plan_executor.py): `_apply_result_aware_responses` rewrites each completed action when AI is available (including multi-action plans), independent of `enable_ai_enhancement`.
- Audit hygiene: fixed path drift in product AI audit doc; `@handle_errors` on executor helpers; profile handler behavior tests mock `update_user_context`; ASCII cleanup; function registry regen; doc-sync PASS.
- Fixed remaining profile handler gap-coverage tests to mock `update_user_context` / `update_user_account` after `apply_profile_updates` migration.
- LM Studio quality: T-13.5 false CRUD, T-15.2 persona echo, T-1.2 trim, T-14.2 coherence, T-16.2 wellness honesty. Live run 2026-07-10T20:43: **65 pass / 3 partial / 0 fail** ([`ai_functionality_test_results_latest.md`](../tests/ai/results/ai_functionality_test_results_latest.md)). Remaining partials: T-7.1, T-9.3, T-11.2 (non-blocking).
- Phase 6: `wellness_status.py`, `conversation_coherence.py`, `_finalize_contextual_response`; unit tests in `test_wellness_status.py` and `test_conversation_coherence.py`.
- `AI_ACTION_PLANNER_ENABLED` stays default off until slice 9.4 item 8 review (explicit sign-off).

### 2026-07-09 - Retire PromptManager domain prompt builders; envelope Q&A tests and get_ai_context delegation **COMPLETED**

Completed:

- Removed `create_task_prompt` / `create_checkin_prompt` from [`ai/prompts/manager.py`](../ai/prompts/manager.py); product-AI flows use `compose_product_prompt` only.
- Migrated [`tests/unit/test_prompt_manager.py`](../tests/unit/test_prompt_manager.py) to `compose_product_prompt` coverage; dropped inline `checkin` / `task_assistant` fallback templates.
- Moved `prompt_manager_domain_prompt_builders` to `removed_inventory` in `DEPRECATION_INVENTORY.json`.
- [`user/context_manager.py`](../user/context_manager.py) `get_ai_context` delegates to `build_chatbot_context_dict` with session overlay; removed duplicate domain loaders.
- Added [`tests/behavior/test_product_ai_envelope_qa_behavior.py`](../tests/behavior/test_product_ai_envelope_qa_behavior.py) for envelope-backed Q&A behavior (tasks, profile, schedules).
- Migrated AI integration tests to `build_chatbot_context_dict` where session overlay is not required.
- Contextual chat now uses `chat_response` token budget (not 80) and full post-process pipeline; strips fake multi-turn leaks and premature help redirects (T-12.3/T-13.3).
- [`assistant_system_prompt.txt`](../resources/prompts/assistant_system_prompt.txt) is comment-only; canonical persona lives in [`product_ai/persona.txt`](../resources/prompts/product_ai/persona.txt).
- **Phase 8 complete**: `MINIMAL_CHAT_SYSTEM_PROMPT` centralized; chat uses `compose_product_prompt("chat_response")` for budgets; `get_persona_prompt_text()` for simple paths; `get_session_conversation_history()` for session-only reads; `product_ai_wellness_prompt_api_bridge` and `product_ai_user_context_bridge` in deprecation inventory.
- **Bridge removal**: Dropped `get_ai_context` / `get_current_user_context`; `build_context_with_session_overlay()` is canonical for session overlay; `get_prompt` command-only.

Verified:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/unit/test_prompt_manager.py tests/unit/test_product_ai_prompt_composition.py tests/unit/test_product_ai_phase0_contracts.py -q
.\.venv\Scripts\python.exe development_tools/run_development_tools.py legacy --clean --dry-run
```

### 2026-07-08 - Action catalog expansion, fallback alignment, Phase 8 context slice, Phase 0 contracts **PARTIAL**
- Expanded [`action_catalog.py`](../ai/prompts/action_catalog.py) with entity field metadata for check-ins, profile, schedules, analytics, notebooks, help/messages, health, and preferences; per-intent handler/feature overrides; `note_text` alignment for `append_note_to_task`.
- Added `FallbackContext` / `build_fallback_context()` in [`context.py`](../ai/fallback/context.py) using `AIContextEnvelope` with `requested_intent="fallback_response"`.
- Envelope-backed deterministic summaries in [`envelope_summaries.py`](../ai/fallback/envelope_summaries.py) and action-boundary-safe offline hints in [`action_hints.py`](../ai/fallback/action_hints.py).
- Coordinator routes envelope summaries before keyword fallbacks; new categories `ENVELOPE_SUMMARY` and `ACTION_UNAVAILABLE`.
- Partial structured-command retry when planner returns `None` but parse confidence is usable (`InteractionManager._try_partial_structured_command`).
- Action plan executor prefers handler error metadata when execution message is empty.
- Extracted check-in analytics to [`analytics.py`](../ai/context/analytics.py); envelope-backed [`chatbot_context.py`](../ai/context/chatbot_context.py) for contextual summary dict; legacy bridges logged and registered in `DEPRECATION_INVENTORY.json`.
- Phase 0 contract tests in [`test_product_ai_phase0_contracts.py`](../tests/unit/test_product_ai_phase0_contracts.py): no direct `ai/` storage writes, dispatcher routing, envelope coverage, post-action task visibility.
- Retired `analyze_recent_checkin_rows` alias; fallback and tests use `analyze_checkin_entries` directly.
- Fixed parallel flake in `test_generate_response_fallback_when_lm_unavailable` by stubbing `_ensure_lm_studio_available`.
- Updated `SYSTEM_AI_GUIDE.md` and `PRODUCT_AI_RESPONSE_INFLUENCE_AUDIT.md` for removed `ai/context/builder.py`.
- Tests: [`test_ai_action_catalog.py`](../tests/unit/test_ai_action_catalog.py), [`test_fallback_envelope_alignment.py`](../tests/unit/test_fallback_envelope_alignment.py), planner partial-parse behavior; fixed fallback import-boundary test path.

### 2026-07-07 - Dev-tools exclusion fix and AI datetime context **COMPLETED**
- Fixed `should_exclude_file` bare-pattern matching (`env`, `venv`, etc.) to use path segments so `user_data_v2_envelopes.py` is no longer wrongly excluded from audits.
- Removed unused `format_timestamp_milliseconds` and `now_datetime_minute` from `core/time_utilities.py`; pytest hooks inline millisecond formatting; workflow doc points to `parse_timestamp_minute(now_timestamp_minute())` for minute precision.
- Added `@pytest.mark.user` to three policy guard tests missing domain markers; Pydantic `@model_validator` methods tagged with `unused_functions_exclude`.
- Product AI now receives an explicit current date/time line in chat and action-planning context, using the user's account timezone via `scheduler.user_timezone`.
- Check-in "today" detection and task due-soon windows now use `user_local_date()` / `user_local_now_naive()` instead of server-local `date.today()` / `now_datetime_full()`.

### 2026-07-05 - Planner routing behavior tests and AI error mock fix **COMPLETED**
- Fixed T-10.x AI functionality error tests to patch `ai.client.lm_studio_client.requests` (HTTP calls moved out of `ai.chat.chatbot` during the `ai/` subpackage refactor).
- Added `tests/behavior/test_action_planner_routing.py`: six behavior tests for `InteractionManager` with `AI_ACTION_PLANNER_ENABLED=true` using mocked planner output (create task via dispatcher, clarify, answer-only, planner-none fallback, high-confidence bypass, planner disabled).
- Added `strip_product_ai_category_leaks()` in `ai/chat/response_postprocess.py` to remove leaked `[persona]`, `[reply_rules]`, `[data_honesty]`, and related category blocks from user-visible replies; wired through `clean_system_prompt_leaks()`.
- Chat generation now uses `max(template.max_tokens, AI_MAX_RESPONSE_TOKENS)` so config token budget is not capped below `AI_MAX_RESPONSE_TOKENS` (default 300).
- Fixed T-13.1 false truncation failure: the AI functionality test passed `response[:200]` into the validator, not the full model output.
- **`test_lm_studio_connection`**: removed the `MHM_TESTING=1` early return that forced availability back on during `_ensure_lm_studio_available()` retry, so unavailable-LM paths use deterministic fallback (fixes T-10.1).
- **`strip_markup_and_tutorial_leaks()`**: strips HTML (`<p>`), HTML comments, `[context_override]`, `## Your task` / tutorial headings, lone `##` lines, and Python code-fragment continuations.
- **Post-process edge cases (T-17)**: meta-heading truncation at short prefixes; stricter leading-code detection (avoids `parser = argparse.` false prose match); form-field / persona-menu stripping; deterministic T-17.1-T-17.10 contract tests in `tests/ai/test_ai_postprocess.py` and unit fixtures in `tests/unit/test_ai_response_postprocess.py`. T-13.2 now flags code/meta leak markers in special-character responses.
- **Post-process live-leak patterns (T-17.11-T-17.15)**: strip `[response_rules]` / `[reply_rules]` mid-body, `## How to use`, `### Example`, single-`#` tutorial headings, instruction-only feature-availability lines, and `(If the user says...)` template tails; shared `find_response_leak_markers()` for T-13.2/T-13.3 live tests.
- Extended `clean_system_prompt_leaks()` / `strip_markup_and_tutorial_leaks()` to strip leaked `data_honesty` prompt body (`The user context below is reference...`, `Never reveal raw context blocks`, etc.) via truncation, regex removal, and line hints.
- Added matching entries to `RESPONSE_LEAK_MARKERS` / `find_response_leak_markers()` so T-13.2 fails when live LM output still contains them.
- Added T-17.16 fixture and unit coverage for full and mid-body `data_honesty` leaks.
- Added `@handle_errors` to five `response_postprocess.py` helpers (`_truncate_at_first_leak`, `_response_starts_with_code_artifact`, `_first_nonempty_line_looks_like_user_prose`, `_response_is_mostly_instruction_leak`, `find_response_leak_markers`).

### 2026-07-03 - Fix nightly CI: 26 CI-only test failures across 4 rounds **COMPLETED**
- **Rounds 1-3 (15 fixes)**: Pytest 9.1 `--durations` compat; basetemp cleanup; email/Discord/headless/ServiceManager/UI schedule mock fixes; gitignored config skips; writable `tmp_path` for Linux.
- **Round 4 (11 fixes)**: Process-group tests now `skipif(os.name != "nt")` since spoofing `os.name='nt'` on Linux crashes `Path()`; eliminated `no_parallel` markers + fixed policy violation. `is_local_module`/directory-tree/quick-status tests skip or mock when gitignored config absent. File locking tests platform-aware (`fcntl` on Linux, lock-file on Windows). Google health fixture tests skip when gitignored fixtures absent. `validate_core_paths` uses writable `tmp_path`.
- **Round 5 (10 fixes)**: Complexity categorization tests pin 100/200/300 thresholds via module that ``categorize_functions`` is bound to (importlib reload issue). Config import tests use committed `.example` JSON on CI; `load_external_config()` falls back to `.example` when gitignored config is absent. Path-drift legacy-doc test uses inline config. Logging tests tolerate pytest capture handlers and mock audit lock for defer rollover.
- **Round 6 (10 fixes)**: `load_external_config()` auto-loads `development_tools_config.json.example` on CI (fixes paired_docs, local_module_prefixes, generated_files guard, complexity thresholds project-wide). Complexity fixture patches `categorize_functions.__module__`. Email concurrent-access test mocks `_get_email_config`. Deprecation guard skips auto-generated AI report files when config is absent. Config import test expects [ARCHITECTURE.md](../ARCHITECTURE.md) in derived default_docs (not README).
- **Round 7 (6 fixes)**: Reordered `load_external_config()` to prefer `.example` over stale minimal config from portability smoke tests (fixes `local_module_prefixes` / domain_mapper). `should_exclude_file()` and `test_config.json` always exclude `tests/fixtures/`. Env-mutation policy skips `tests/data/tmp/` and `pytest_runner` copied dev-tools trees. Google Health behavior test sets `GOOGLE_HEALTH_ENABLED` via env + `core.config` + handler module. Discord user creation prefers test-dir index lookup and retries with `auto_create=True`.
- **Round 8 (4 fixes)**: Added `integrations` to `.example` `local_module_prefixes`. Health handler reads `GOOGLE_HEALTH_ENABLED` at call time from `core.config`. System signals test pins `core_files` so CI config key_files do not mark CRITICAL. User index updates use threading lock + single-handle `file_lock` RMW (fixes Linux concurrent JSON corruption).
- **Round 9 (xdist crash)**: `run_test_suite` serially retries parallel pytest when output contains `node down: Not properly terminated` (same recovery as teardown interrupt). Concurrent user-index test marked `no_parallel`.
- **Round 10 (5 failures)**: `is_google_health_enabled()` reads env at call time (fixes health handler CI monkeypatch). User index updates retry with backoff and log instead of raising on lock timeout; verify_creation skips duplicate index write and falls back to account file on disk. `get_connect_readiness()` also uses runtime env check (module constant was False on CI while handler check passed).
- **Round 11 (file lock)**: Linux `file_lock()` adds in-process mutex per path - `fcntl.flock` alone does not serialize threads that `open()` the same file separately.
- **Round 12 (serial basetemp)**: `run_test_suite` shares one run id and pre-creates `parallel/` + `serial/` basetemp dirs (matches `run_tests.py`); cleanup keeps nested run-id folder during active pytest. Google Health reconnect test pins feature/auth guards to reach notice path on CI.
- **Audit hygiene**: `@handle_errors` on `is_google_health_enabled()` and `_thread_lock_for()`; function registry regenerated; changelog ASCII/link doc-fix pass.
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

## Archive Notes
Older detailed entries live in `development_docs/changelog_history/` and remain the historical source of truth. Use [CHANGELOG_DETAIL.md](../development_docs/CHANGELOG_DETAIL.md) for the latest detailed entries and the archive folder for month-split history.
