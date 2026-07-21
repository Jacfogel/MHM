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

### 2026-07-20 - Nightly CI logging check + marker **COMPLETED**
- Static logging check falls back to committed `.example` when live config is missing; example allowlist restored for core logger/config files.
- Registered `development_tools` pytest domain marker for `--strict-markers` collection.
- V6 deferred trio: B-011 coverage-cache numbers (cold **298.67s** / build **326.99s** / hit **0.91s**); B-014 keep memory profiler standalone/local; B-010 TODO sync workflow recipe in paired guides.
- V6 B-009: system signals drops doc-sync re-derive; critical_alerts from severity. B-015 first extract: `coverage_json_helpers` + `report_generation_tier3_helpers` (no legacy shims).
- V6 B-015 slice #2: `coverage_outcome_classification` (track/cache outcomes, Windows/xdist/infra detectors, `strip_xdist_args`); regenerator methods thin-delegate.
- V6 B-015 slice #3: AI_STATUS / AI_PRIORITIES / CONSOLIDATED builders moved to dedicated mixins; `report_generation.py` composes them (no legacy shims).
- Cleared post-split F401/Ruff noise: unused imports removed from report builder modules; linkify tests import `report_generation_linkify` directly.

### 2026-07-19 - V6 residual slice (perf + noise) **COMPLETED**
- B-001: `test_fix_project_cleanup` uses `tmp_path` (no demo copytree); module-scoped demo fixtures for docs-workflow / scoped-status / static-analysis report / cache-helpers; path-drift leftovers -> `tmp_path`; archive module + legacy mutators marked `slow` for Tier 3 quick profile.
- B-001 re-profile: `run_tests.py --mode development_tools --durations-all` -> **1591 passed / 83.94s** wall (was ~195s on 2026-07-18); cleanup copytree gone from top setups.
- B-006: dependency-doc placeholder modules summarized at INFO; WARNING list limited to new/missing/changed.
- B-007: example-marker advisory skips fenced blocks and opens on prose `Examples:` labels.
- B-008: Discord-spec boilerplate headings added to `EXPECTED_OVERLAPS`. V6/TODO retargeted; coverage stays outside V6 active driver.
- Cleared AI_PRIORITIES example-marker hints: renamed neutral `Examples:`/`Example:` labels in DOCUMENTATION_GUIDE, AI_DEVELOPMENT_TOOLS_GUIDE, TESTING_GUIDE; prose openers now end at any ATX heading. ASCII compliance already CLEAN.

### 2026-07-18 - LIST_OF_LISTS currency; V6 plan status refresh **COMPLETED**
- B-003/B-004 portability: emptied MHM package roots from portable code defaults (Ruff/Pyright shards, Bandit roots, channel-logger allowlist); MHM trees live in project JSON + `.example`. Renamed pip-audit skip env to `DEV_TOOLS_PIP_AUDIT_SKIP` only (`MHM_PIP_AUDIT_SKIP` removed), renamed pip-audit/pytest temp cache prefixes, and external-repo smokes (Bandit `.` fallback, Ruff monolithic fallback, subprocess `audit --quick`).
- Fix Tier 3 flake: `test_analyze_unused_functions_finds_uncalled_helper` now passes explicit `project_root` / `scan_directories` / `apply_exclusions=False` so empty global `paths.scan_directories` from other tests cannot yield zero files.
- B-004: removed nested `development_tools/config/pyrightconfig.json`; Pyright SSOT is `pyproject.toml` `[tool.pyright]` only (cache deps, policy tests, guides, deprecation inventory updated).
- Cleared AI_PRIORITIES: `click>=8.3.3` for CVE-2026-7246; TODO.md ASCII; historical changelog hrefs to removed nested Pyright path demoted to plain backticks.
- LIST_OF_LISTS verified against live code; fixed duplicate `legacy_cleanup` JSON key; PLANS Section 2 + cursor rules inventory path aligned to `config/jsons/`.
- Catalog drift fixed: `EXPECTED_TOOLS` uses `analyze_system_signals`; `generate_dev_tools_coverage` catalogued in `_TOOLS`; subset policy test added; tool_guide basename guard skips script-registry excludes.
- Cleared AI_PRIORITIES doc-sync items: path drift, ASCII, registry regen; `doc-sync` PASS.
- LIST_OF_LISTS Section 7c documents cache/suite/static-analysis/backup policy lists.
- Deferred SSOT closed: audit_tiers group maps, paired-docs prose sync in doc-sync, COMMAND_GROUPS guide parity test, PRODUCT_LIST_OF_LISTS.md.
- Parallel-track flake fix: xdist worker-isolated `tests/data/xdist_*`; force-overwrite inherited `TEST_DATA_DIR`; actionability tests bind runtime data dir; `is_automated_messages_enabled` resolves usernames; audit_tiers TypedDict clears Pyright warnings.
- Refreshed [AI_DEV_TOOLS_IMPROVEMENT_PLAN_V6.md](../development_tools/AI_DEV_TOOLS_IMPROVEMENT_PLAN_V6.md) Section 1.1 / B-001-B-005 / B-018 against 2026-07-18 audit + codebase (coverage-first next slice; perf residual; portability residual; domain markers maintenance; pip CVE closed).
- B-002 coverage slice #1: branch tests for `report_generation` / `audit_orchestration` / `tool_wrappers` helpers (113 passed in the three extended test modules).
- Fixed Tier 3 parallel flakes: unique user IDs for task-stats parity, admin provisioning, and Google Health reconnect-notice sync; ran `doc-fix --fix-ascii` on changelogs.
- B-001 residual: module-scoped `temp_project_copy` in static-analysis wrapper + unused-imports report tests; legacy cleanup left function-scoped (mutates demo tree).
- Full `development_tools` durations profile: 1564 passed in ~3:15 wall; setup still dominated by function-scoped mutators (`fix_project_cleanup`, `output_storage_archiving`, `legacy_reference_cleanup`).
- B-002 coverage slice #2: deeper chokepoint edges plus new `test_analyze_unused_functions.py` (closes the 0% analyzer gap from wrapper-only mocks); 129 passed across four modules. V6 B-002 notes retargeted to ~65.6% live snapshot.
- B-002 coverage slice #3: `commands` / `data_loading` helpers (coverage summary/insights, canonical metrics, doc-subcheck freshness/cache-hit, execute_task/cleanup/status skip); 121 passed across three extended modules.
- Doc correction: coverage is refreshed only by `python development_tools/run_development_tools.py coverage` (not `audit --full`). Updated HOW_TO_RUN, DEVELOPMENT_WORKFLOW (paired with AI_*), DEVELOPMENT_TOOLS_GUIDE, V6/TODO, and generated-status follow-up strings in `report_generation.py`.
- Cleared AI_PRIORITIES quick wins: path-drift bare `TEST_COVERAGE_REPORT.md` refs -> `development_docs/...`; Pyright on new helper tests (0/0); TODO.md ASCII via `doc-fix --fix-ascii`; `doc-sync` PASS.

### 2026-07-17 - Session fact recall; archive completed product-AI plan **COMPLETED**
- Contextual prompts merge session + disk conversation history and label prior user turns clearly; cache skipped when prior turns exist.
- `conversation_coherence` reinforces stated facts (favorite color/name/food) when follow-ups omit them; `reply_rules.txt` updated.
- Durable routing/prompt contracts recorded in `ai/SYSTEM_AI_GUIDE.md`; completed plan moved to `archive/PRODUCT_AI_RESPONSE_INFLUENCE_AUDIT.md`.
- Live AI suite: 66 pass / 2 partial / 0 fail (T-7.1 PASS).

### 2026-07-15 - Compact planner prompt; planner default on; template/hub parity **COMPLETED**
- Planner prompt is a short ACTION-first template + compact action list; calls LM Studio directly; free-text entities must appear in the user message.
- `AI_ACTION_PLANNER_ENABLED` defaults to `true`; template/hub parity added for `create_task_from_template`, `list_task_templates`, `show_create_hub`.
- Product AI audit Phases 4-6 / slice 9.4 marked complete.

### 2026-07-14 - Plain-language wellness messaging; richer sleep quality + active minutes **COMPLETED**
- Personalized prompts use plain sleep/activity phrases (no `sleep_recovery=high` / "wearable wellness" parroting).
- New derived fields: `sleep_quality` (efficiency + deep/REM) and `active_intensity` (active minutes) feed personalization rules + message/chat context.
- User-facing effect: messages can mention solid/lighter sleep quality and higher/lighter active effort without raw metrics.

### 2026-07-13 - Register `integrations` pytest domain marker; strip two-line wellness sign-offs **COMPLETED**
- Registered `@pytest.mark.integrations` in `pytest.ini` and conftest hooks so `--strict-markers` collection no longer crashes on health context builder tests.
- Domain marker docs now list `integrations` alongside other product packages.
- **Fix (personalized sign-offs)**: `strip_letter_signoffs()` now removes split closings (`Best wishes,` + bare `Assistant` / `MHM Bot` on the next line), not only single-line `Take care, [Your Name]`.

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
- Reconciled [`PRODUCT_AI_RESPONSE_INFLUENCE_AUDIT.md`](../archive/PRODUCT_AI_RESPONSE_INFLUENCE_AUDIT.md): Phase 0 COMPLETE; slice 9.4 items 1-7 COMPLETE (LM Studio gate met).
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

## Archive Notes
Older detailed entries live in `development_docs/changelog_history/` and remain the historical source of truth. Use [CHANGELOG_DETAIL.md](../development_docs/CHANGELOG_DETAIL.md) for the latest detailed entries and the archive folder for month-split history.
