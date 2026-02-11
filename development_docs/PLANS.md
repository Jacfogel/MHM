# MHM Development Plans


> **File**: `development_docs/PLANS.md`
> **Audience**: Human Developer & AI Collaborators  
> **Purpose**: Consolidated development plans (grouped, interdependent work) with step-by-step checklists  
> **Style**: Actionable, checklist-focused, progress-tracked  
> **Last Updated**: 2026-02-10

---

**Note**: [TODO.md](TODO.md) is the canonical list for standalone tasks. Larger, scoped efforts live in dedicated plan files such as [TASKS_PLAN.md](development_docs/TASKS_PLAN.md), [NOTES_PLAN.md](development_docs/NOTES_PLAN.md), and [AI_DEV_TOOLS_IMPROVEMENT_PLAN_V4.md](development_tools/AI_DEV_TOOLS_IMPROVEMENT_PLAN_V4.md).

## [IN PROGRESS] **Plan Maintenance**

### **How to Update This Plan**
1. **Add new plans** with clear goals and checklist format
2. **Update progress** by checking off completed items
3. **Remove fully completed plans** - document them in CHANGELOG files instead
4. **Keep reference information** current and useful
5. **Remove outdated information** to maintain relevance

### **Success Criteria**
- **Actionable**: Each item is a specific, testable action
- **Trackable**: Clear progress indicators and completion status
- **Maintainable**: Easy to update and keep current
- **Useful**: Provides value for both human developer and AI collaborators

---

## [ACTIVE] **Current Active Plans**

### **Test Suite Performance Optimization Plan** **ON HOLD**

**Status**: **ON HOLD**  
**Priority**: Medium  
**Effort**: Medium  
**Date**: 2025-11-23  
**Last Updated**: 2026-02-11

**Objective**: Optimize test suite execution time from ~265 seconds (4.4 minutes) to ~205-225 seconds (3.4-3.7 minutes) by reducing unnecessary delays, optimizing expensive operations, and improving test efficiency.

**Current Performance**:
- Total Duration: ~226-235 seconds (3.8-3.9 minutes) - **Baseline performance**
  - Parallel tests: ~142-161s (3,178-3,195 tests)
  - Serial tests: ~75-84s (115-131 tests)
- Recent run (2026-01-26): ~327s parallel (4,376 tests) + ~138s serial (159 tests).
- Recent flaky-detector full-suite runs (2026-02-10) were typically ~207-255s, with rare timeout outliers at 600s; follow-up remains focused on timeout root cause and worker-log consolidation.
- As of 2026-02-10 session close, serial `@pytest.mark.no_parallel` runs are passing in `run_tests.py` (no Windows crash observed in latest reruns); keep monitoring for regression.
- Audit/report noise from pytest temp artifacts was reduced by excluding `.tmp_pytest_runner` and related temp/cache directories in dev-tools exclusions.
- 2026-02-11 profiling runs show improved full parallel-suite runtime when using temp-isolated pytest dirs (`--basetemp` and `cache_dir` under `%TEMP%`), with a clean sample at `4457 passed, 1 skipped in 209.25s`.
- **Performance Investigation Results (2025-11-24)**:
  - Attempted optimizations (removed `no_parallel` markers, added `wait_until` helpers, reduced retry loops)
  - Performance did not improve; actually degraded in some cases
  - Reverted all optimization attempts
  - Determined performance variability is primarily due to system load, not code changes
  - Test suite baseline performance is acceptable (~3.8-4 minutes)

**Key Performance Issues Identified**:

1. **Excessive `rebuild_user_index()` Calls** (High Impact)
   - `rebuild_user_index()` is expensive (scans all user directories)
   - Called multiple times per test (3+ times in `test_multiple_users_same_channel`)
   - Called in retry loops unnecessarily
   - **Solution**: Use `update_user_index(user_id)` for single-user updates, batch operations and rebuild once

2. **Excessive Retry Loops with Sleep Delays** (Medium-High Impact)
   - 141 `time.sleep` calls across 35 files
   - Retry loops with 5 attempts and 0.1s delays (0.4s total per loop)
   - **Solution**: Reduce retry counts (5->3), reduce sleep (0.1s->0.05s), use `wait_until()` helper

3. **Redundant `_materialize_and_verify()` Calls** (Medium Impact)
   - Called 25 times in `test_account_lifecycle.py`
   - Each call does full data loading and merging
   - **Solution**: Call only once per test, cache results if needed

4. **Too Many `no_parallel` Tests** (Medium Impact)
   - 133 tests running serially (83 seconds)
   - Many may not need serial execution with proper isolation
   - **Solution**: Audit and remove `no_parallel` where safe, use unique identifiers

5. **Sequential User Creation** (High Impact)
   - `test_multiple_users_same_channel` creates 3 users sequentially with full retry logic
   - **Solution**: Create all users first, then rebuild index once

**Deferred Work (if resumed)**:
- Re-verify baseline performance under controlled system load.
- Target excessive `rebuild_user_index()` usage with per-user updates and batching.
- Replace remaining manual retry loops with `wait_until()` where safe.
- Audit `no_parallel` markers for additional safe removals.
- Consider caching expensive test helpers and batching file operations.
- Add a lightweight wrapper to archive `parallel_profile_*.log/.xml` outputs into `development_tools/tests/logs/archive/` with 7-version consolidated retention.

**Success Criteria**:
- [ ] Test suite runs in ~205-225 seconds (15-23% improvement)
- [ ] `test_multiple_users_same_channel` runs in <15s
- [ ] `test_account_lifecycle` tests run in <12s each
- [ ] All tests continue to pass after optimizations
- [ ] No increase in flaky tests
- [ ] Reduced `rebuild_user_index()` calls by 50%+

**Implementation Notes**:
- Test after each optimization to ensure no regressions
- Some optimizations may require careful testing for race conditions
- Keep retry logic for truly flaky operations, but optimize the delays
- Document why `no_parallel` is needed when it's kept
- Use `wait_until()` helper from `tests/conftest.py` instead of manual retries where possible
- Follow testing guidelines: use helpers from `tests/test_utilities.py`, ensure test isolation
- Added `_wait_for_user_id_by_username` helper to poll `get_user_id_by_identifier` with a single fallback `rebuild_user_index()` call, removing dozens of expensive index rebuilds from the UI account-creation tests

**Progress Summary**:
- **Analysis Complete**: Performance issues identified and documented
- **Optimization Attempts**: Tried removing `no_parallel` markers, adding `wait_until` helpers, reducing retry loops
- **Reverted Changes**: All optimization attempts reverted after determining performance variability is due to system load
- **Current Status**: Plan on hold - baseline performance (~3.8-4 minutes) is acceptable. Future optimizations should focus on reducing expensive operations (like `rebuild_user_index()`) rather than test execution patterns.
- **2026-01-26 Update**: Short-circuited heavy UI startup work in `MHM_TESTING` mode to reduce long-running parallel UI tests; re-baseline after next full run.

### **No-Parallel Marker Reduction Plan** **IN PROGRESS**

**Status**: **IN PROGRESS**
**Priority**: High
**Effort**: Medium
**Date**: 2026-02-10
**Last Updated**: 2026-02-10

**Objective**: Reduce `@pytest.mark.no_parallel` usage by making targeted tests parallel-safe through deterministic test data isolation, unique IDs, fixture-scoped paths, and explicit state cleanup.

**Current Baseline**:
- Active `@pytest.mark.no_parallel` markers remaining: 86 across 12 test files (updated 2026-02-10 after Wave 1 execution; baseline was 95 across 17 files).
- Recent progress included successful reintegration of several isolated tests by removing fixed IDs/shared file collisions.

**Approach**:
- Prioritize easiest wins first: single-marker files and two-marker files with fixed IDs or shared file constants.
- Convert tests to per-test unique user IDs and per-test data paths.
- Patch module-level file constants in tests where shared state is unavoidable.
- Keep marker only when real cross-process invariants cannot be safely isolated.

**Execution Waves**:
- [x] **Wave 1 (easiest wins)**: Single/low-count marker files
  - [x] `tests/unit/test_file_operations.py` (`test_save_large_json_data`)
  - [x] `tests/behavior/test_welcome_manager_behavior.py` (2 tests)
  - [x] `tests/behavior/test_webhook_handler_behavior.py` (2 tests)
  - [x] `tests/behavior/test_conversation_flow_manager_behavior.py` (2 tests)
  - [x] `tests/behavior/test_interaction_handlers_behavior.py` (2 tests)
- [ ] **Wave 2 (moderate)**: Small clusters with shared message/account state
  - [ ] `tests/behavior/test_message_behavior.py` (4 tests)
  - [ ] `tests/behavior/test_discord_bot_behavior.py` (3 tests)
  - [ ] `tests/ui/test_ui_app_qt_main.py` (5 tests)
- [ ] **Wave 3 (larger clusters)**: High-touch modules
  - [ ] `tests/behavior/test_account_management_real_behavior.py` (6 tests)
  - [ ] `tests/unit/test_user_management.py` (6 tests)
  - [ ] `tests/integration/test_account_lifecycle.py` (7 tests)
  - [ ] `tests/integration/test_user_creation.py` (7 tests)
  - [ ] `tests/behavior/test_backup_manager_behavior.py` (8 tests)
  - [ ] `tests/behavior/test_user_data_flow_architecture.py` (8 tests)
  - [ ] `tests/unit/test_user_data_manager.py` (14 tests)
  - [ ] `tests/behavior/test_account_handler_behavior.py` (15 tests)

**Per-Test Conversion Checklist**:
- [ ] Replace fixed identifiers with unique per-test IDs (worker-safe suffixes)
- [ ] Route all filesystem writes to fixture-provided per-test paths
- [ ] Patch module-level file constants used by the test target
- [ ] Remove marker and run targeted loop (`pytest -n auto`) for that test/module
- [ ] Add/adjust assertions so data is validated via isolated test-owned files
- [ ] Document residual reason if marker must remain

**Validation Checklist**:
- [ ] Targeted repeated parallel runs pass for each converted test
- [ ] Module-level parallel run passes after each batch
- [ ] Full-suite flaky detector trend improves after each wave
- [ ] Remaining marker count tracked in changelog/session notes

**Success Criteria**:
- [ ] Reduce active no-parallel markers by at least 50% from the 2026-02-10 baseline
- [ ] No increase in flaky failure rate in `flaky_detector` targeted reruns
- [ ] Every remaining marker has a documented technical reason

### **Investigate Intermittent Test Failures** **IN PROGRESS**

**Status**: **IN PROGRESS**
**Priority**: Medium
**Effort**: Small/Medium
**Date**: 2026-02-10

- *What it means*: Investigate and fix test failures that appear intermittently (including coverage-run flakes); keep the suspect list current as flakes are confirmed or resolved.
- *Why it helps*: Ensures test suite reliability and prevents false negatives that can mask real issues
- *Estimated effort*: Small/Medium
- *Subtasks*:
  - [ ] Investigate `tests/ui/test_account_creation_ui.py::TestAccountManagementRealBehavior::test_feature_enablement_persistence_real_behavior` and ensure each worker has isolated `tests/data` state
  - [ ] Investigate `tests/behavior/test_logger_behavior.py::TestLoggerFileOperationsBehavior::test_get_log_file_info_real_behavior`
  - [ ] Investigate `tests/ui/test_category_management_dialog.py::TestCategoryManagementDialogRealBehavior::test_save_category_settings_updates_account_features`; `tests/behavior/test_user_data_flow_architecture.py::TestAtomicOperations::test_atomic_operation_all_types_succeed` had a mitigation on 2026-02-09 (unique per-test user IDs), monitor for recurrence in coverage runs.
  - [ ] Investigate `tests/behavior/test_user_data_flow_architecture.py::TestProcessingOrder::test_processing_order_deterministic_regardless_of_input_order`; mitigation applied on 2026-02-09 (stronger persisted-data readiness check + cache clears), monitor in coverage runs.
  - [ ] Monitor Windows no-parallel stability (`0xC0000135` recurrence) after recent run_tests environment/isolation fixes; keep `run_tests.py` serial phase under observation.
  - [ ] Investigate `tests/behavior/test_checkin_questions_enhancement.py::TestCustomQuestions::test_delete_custom_question`
  - [ ] Investigate `tests/unit/test_user_management.py::TestUserManagement::test_create_user_files_success` flake in coverage runs (avoid nondeterministic "first directory" assumptions under shared `tests/data/users`)
  - [ ] Investigate `tests/development_tools/test_fix_project_cleanup.py::TestProjectCleanup::test_cleanup_test_temp_dirs_no_directory` flake (TOCTOU race when temp dirs disappear during cleanup in parallel runs)
  - [ ] Investigate `tests/behavior/test_webhook_handler_behavior.py::TestWebhookHandlerBehavior::test_handle_webhook_event_routes_application_deauthorized`
  - [ ] Investigate `tests/unit/test_schedule_management.py::TestScheduleManagement::test_schedule_period_lifecycle`
  - [ ] Investigate `tests/ui/test_task_management_dialog.py::TestTaskManagementDialogRealBehavior::test_save_task_settings_persists_after_reload`
  - [ ] Investigate `tests/unit/test_user_data_handlers.py::TestUserDataHandlersConvenienceFunctions::test_update_user_account_valid_input` intermittent parallel failure (cross-user write/read mismatch observed in flaky detector and targeted xdist runs)
  - [ ] Investigate `tests/unit/test_user_data_handlers.py::TestUserDataHandlersConvenienceFunctions::test_save_user_data_transaction_valid_input` intermittent parallel failure (cross-user write/read mismatch observed in flaky detector and targeted xdist runs)
  - [ ] Investigate `tests/behavior/test_user_management_coverage_expansion.py::TestUserManagementCoverageExpansion::test_load_account_data_auto_create_real_behavior` intermittent parallel failure (auto-created account occasionally returns empty `internal_username`)
  - [ ] Investigate `test_scan_all_python_files_demo_project`
  - [ ] Check for timing/race condition issues in test setup or teardown
  - [ ] Verify test isolation and data cleanup between test runs
  - [ ] Add retry logic or fix root cause if identified
  - [ ] Track `tests/development_tools/test_legacy_reference_cleanup.py::TestCleanupOperations::test_cleanup_legacy_references_dry_run` failures (PermissionError when copying `tests/fixtures/development_tools_demo` into `tests/data/tmp*/demo_project`) and ensure the temporary `tests/data/tmp*` directories remain writable before rerunning the suite.

### **Error Handling Quality Improvement Plan** **IN PROGRESS**

**Status**: **IN PROGRESS**  
**Priority**: Medium  
**Effort**: Medium  
**Date**: 2025-11-20  
**Last Updated**: 2025-11-21

**Objective**: Improve error handling quality beyond coverage by enhancing error messages, expanding recovery strategies, and standardizing context payloads. Phase 1/2 candidate tracking is handled in development tools.

**Current Status**: 
- [x] **100% coverage achieved** (see [AI_STATUS.md](development_tools/AI_STATUS.md) for current counts)
- [x] Phase 1/2 candidate tracking is handled by `analyze_error_handling.py` and surfaced in AI reports
- [ ] Phase 3+ work below remains open

**Phase 3: Enhance Error Messages** (Priority: Medium, Ongoing)
- [ ] Review user-facing error messages for clarity and actionability
- [ ] Ensure user messages are:
  - Short, clear, and non-technical
  - Focused on what the user can do
  - Free of stack traces, internal names, or sensitive data
- [ ] Review log messages for completeness:
  - Include component, operation, and relevant context (IDs, file paths)
  - Never include secrets (tokens, passwords)
  - Include exception details and stack traces in logs
- [ ] Create guidelines document for error message patterns
- [ ] Audit and improve error messages in batches

**Phase 4: Expand Recovery Strategies** (Priority: Low)
- [ ] Identify common error patterns that could benefit from automatic recovery
- [ ] Evaluate adding recovery strategies for:
  - Temporary file locks (retry with backoff)
  - Rate limiting (Discord/email API throttling)
  - Database connection issues (if database is added)
  - Network timeouts (extend existing NetworkRecovery)
- [ ] Implement new recovery strategies following existing patterns:
  - Keep strategies idempotent and side-effect safe
  - Test recovery behavior thoroughly
  - Document recovery behavior in error handling guide
- [ ] Integrate new strategies into `ErrorHandler`

**Phase 5: Improve Context Information** (Priority: Low, Ongoing)
- [ ] Audit error handling context payloads for completeness
- [ ] Ensure context includes:
  - User IDs in user operations
  - File paths in file operations
  - Descriptive, stable operation names
  - Component information for log routing
- [ ] Standardize context payload structure across modules
- [ ] Update error handling guide with context best practices

**Phase 6: Investigate Direct error_handler.handle_error Calls** (Priority: Low)
- [ ] Review all direct calls to `error_handler.handle_error()` (found in `core/error_handling.py` and test files)
- [ ] Determine if these should use `@handle_errors` decorator or other centralized patterns
- [ ] Update direct calls to use preferred error handling approach where appropriate
- [ ] Document when direct calls are appropriate vs. decorators

**Success Criteria**:
- [ ] Error messages reviewed and improved in high-traffic modules
- [ ] At least 2 new recovery strategies added (if applicable)
- [ ] Context information standardized across modules
- [ ] All tests pass after changes
- [ ] Error handling quality distribution shows improvement (more "excellent", fewer "basic")

**Progress Summary**:
- **Tooling Complete**: Phase 1 and Phase 2 auditing fully integrated into `analyze_error_handling.py` and AI tools
- **Current Metrics**: See latest counts in [AI_STATUS.md](development_tools/AI_STATUS.md) and [AI_PRIORITIES.md](development_tools/AI_PRIORITIES.md)
- **Next Priority**: Execute Phase 3 improvements, then Phase 4-6 hardening
- **Tracking**: Progress visible in [AI_STATUS.md](development_tools/AI_STATUS.md), [AI_PRIORITIES.md](development_tools/AI_PRIORITIES.md), and [consolidated_report.txt](development_tools/consolidated_report.txt) after each audit

**Notes**:
- Coverage is already at 100%, so this plan focuses on quality improvements
- Phase 1 and Phase 2 tooling is complete - now focus on actual replacements
- Use `analyze_error_handling.py` to track progress and measure quality improvements
- Keep changes small and well-tested - verify behavior after each batch of replacements
- Reference [ERROR_HANDLING_GUIDE.md](core/ERROR_HANDLING_GUIDE.md) and [AI_ERROR_HANDLING_GUIDE.md](ai_development_docs/AI_ERROR_HANDLING_GUIDE.md) for patterns and best practices
- Monitor [AI_PRIORITIES.md](development_tools/AI_PRIORITIES.md) for updated priority counts as replacements are made

### **Discord App/Bot Capabilities Exploration** **PLANNING**

**Status**: **PLANNING**
**Priority**: Medium
**Effort**: Medium
**Date**: 2025-11-13

**Objective**: Explore Discord's app/bot capabilities more thoroughly to identify additional features and integrations that could enhance the MHM Discord experience.

**Scope**:
- [ ] Research Discord's user-installable app features and limitations
- [ ] Explore Discord's webhook event system beyond APPLICATION_AUTHORIZED/DEAUTHORIZED
- [ ] Investigate Discord's interaction types (slash commands, buttons, modals, select menus)
- [ ] Review Discord's message formatting and rich content capabilities
- [ ] Explore Discord's permission system and OAuth2 scopes
- [ ] Research Discord's rate limiting and best practices
- [ ] Identify potential integrations with Discord's features (threads, forums, voice, etc.)

**Success Criteria**:
- [ ] Document findings about Discord capabilities relevant to MHM
- [ ] Identify 3-5 potential feature enhancements based on Discord capabilities
- [ ] Create a prioritized list of Discord integrations to consider

**Notes**:
- Current webhook implementation (APPLICATION_AUTHORIZED/DEAUTHORIZED) is working well
- Focus on capabilities that align with MHM's communication-first, AI-led experience
- Consider both user-installable app features and potential server bot features

### **Account Management System Improvements** **MOSTLY COMPLETE**

**Status**: **MOSTLY COMPLETE**  
**Priority**: High  
**Effort**: Medium  
**Date**: 2025-11-13  
**Last Updated**: 2025-11-20

**Objective**: Complete account linking functionality and enhance account creation with proper feature configuration and user preferences.

**Completed**:
- [x] **Fix Account Linking**: Confirmation code sending working (COMPLETED 2025-11-13)
  - [x] Confirmation codes sent via email (not Discord) for security
- [x] **Fix Account Creation Feature Enablement**: Feature flags now set correctly (COMPLETED 2025-11-14)
  - [x] Account creation sets proper feature flags (task_management, checkins, automated_messages)
- [x] **Enhance Account Creation Flow**: Discord flow enhanced (COMPLETED 2025-11-14)
  - [x] Feature selection (tasks, checkins, automated messages)
  - [x] Timezone selection/configuration
  - [x] Multi-step flow with modal + view pattern

**Remaining Work**:
- [ ] Test end-to-end account linking flow
- [ ] Handle edge cases (user already linked, invalid codes, expired codes)
- [ ] Add profile information collection during account creation (name, preferences, etc.) - Future enhancement

**Success Criteria**:
- [x] Account creation sets correct feature enablement flags (COMPLETED)
- [x] New users can configure preferences during account creation (COMPLETED for Discord)
- [x] Account creation flow is intuitive (COMPLETED)
- [ ] Account linking works end-to-end with edge case handling (in progress)

**Notes**:
- Core functionality complete; remaining work is testing and edge case handling
- Future: Consider adding profile information collection during account creation

### **Mood-Aware Support Calibration** **PLANNING**

**Status**: **PLANNING**
**Priority**: High
**Effort**: Medium
**Date**: 2025-11-10

**Objective**: Define how the assistant adapts tone, reminders, and check-ins based on user mood/energy cues while protecting quiet time boundaries.

**Scope (initial threads)**:
- [ ] Codify "safety net" language library with choose-your-support prompts.
- [ ] Compare task breakdown helper formats (checklist vs. conversational) for stalled tasks.
- [ ] Draft context-to-reminder content mapping covering energy, mood, and task age.
- [ ] Rename and document "Unavailable" mode rules, including urgent escalation criteria.
- [ ] Specify mood re-evaluation triggers and cooldowns.

**Success Criteria**:
- [ ] Safety net prompts feel grounding in sample conversations and pass tone review.
- [ ] Reminder and task helper variants include decision guidance for when to use each.
- [ ] Quiet periods respect "Unavailable" framing without work-centric language.
- [ ] Mood cadence guidelines balance responsiveness with minimal nagging.

**Notes**:
- Capture findings in TODO task updates and tag future implementation tickets once guidelines are approved.
- Validate prototypes against mobile UX constraints (concise, quick replies).

### **Message Deduplication Advanced Features**

**Status**: **IN PROGRESS**  
**Priority**: Low  
**Effort**: Large  
**Started**: 2025-11-11  
**Last Updated**: 2025-11-20

**Objective**: Implement advanced analytics, insights, and intelligent scheduling features for the message deduplication system.

**Completed** (documented in changelog 2025-11-11):
- [x] **Message frequency analytics foundation**: MessageAnalytics class with frequency tracking, delivery success rate analysis, message summary generation (7 tests passing)

**Remaining Work**:

#### **Step 5.1: Analytics and Insights** [IN PROGRESS]
- [x] **Message frequency analytics** [COMPLETED] (2025-11-11)
  - [x] Track message send frequency by category and time period
  - [x] Generate reports on message delivery success rates
  - [ ] Analyze user engagement patterns over time
  - [ ] Create visualizations for message analytics
- [ ] **User engagement tracking** [LONG-TERM/FUTURE] - Requires multiple users for meaningful data
  - [ ] Monitor user response rates to different message types
  - [ ] Track user interaction patterns with messages
  - [ ] Analyze user engagement trends and preferences
  - [ ] Generate user engagement reports
- [ ] **Message effectiveness metrics** [LONG-TERM/FUTURE] - Requires multiple users and response data for meaningful analysis
  - [ ] Measure message effectiveness based on user responses
  - [ ] Track which messages generate the most positive responses
  - [ ] Analyze message timing effectiveness
  - [ ] Create effectiveness scoring system
- [ ] **Smart message recommendation system**
  - [ ] AI-powered message selection based on user history
  - [ ] Personalized message recommendations
  - [ ] Context-aware message suggestions
  - [ ] Learning algorithms for message optimization

#### **Step 5.2: Advanced Scheduling** [PLANNED]
- [ ] **Intelligent message spacing**
  - [ ] Dynamic spacing based on user engagement patterns
  - [ ] Adaptive timing based on user response history
  - [ ] Smart scheduling to avoid message fatigue
  - [ ] Personalized optimal timing algorithms
- [ ] **User preference learning**
  - [ ] Machine learning from user interaction patterns
  - [ ] Adaptive message selection based on preferences
  - [ ] Personalized category preferences
  - [ ] Learning from user feedback and responses
- [ ] **Context-aware message selection**
  - [ ] Time-of-day context awareness
  - [ ] Seasonal and calendar context integration
  - [ ] User mood and state context
  - [ ] Environmental context consideration
- [ ] **A/B testing for message effectiveness**
  - [ ] Split testing framework for message variations
  - [ ] Statistical analysis of message performance
  - [ ] Automated optimization based on test results
  - [ ] Continuous improvement through testing

**Note**: Many features marked LONG-TERM/FUTURE as they require multiple users for meaningful data/analysis

---

### **2025-09-07 - Test Standardization Burn-in** **MOSTLY COMPLETE**

**Status**: **MOSTLY COMPLETE**  
**Priority**: High  
**Effort**: Small  
**Last Updated**: 2025-11-20

**Objective**: Maintain stability by validating order independence and removing test-only aids over time.

**Completed**:
- [x] Tooling for burn-in validation runs (COMPLETED 2025-11-11)
  - [x] `--no-shim`, `--random-order`, `--burnin-mode` options added
- [x] Fixed order-dependent test failures (COMPLETED 2025-11-11)
  - [x] All 7 identified tests fixed
  - [x] All tests pass with `--burnin-mode` (2,809 passed, 1 skipped)
- [x] Sweep and resolve Discord/aiohttp deprecations (COMPLETED)
  - [x] Warning count reduced to external-only (4 Discord library warnings expected)

**Remaining Work**:
- [ ] Nightly run with `--burnin-mode`; track regressions
- [ ] After 2 weeks green with `--burnin-mode`, gate or remove remaining test-only diagnostics

**Success Criteria**:
- [x] Tooling in place (COMPLETED)
- [ ] No failures under `--burnin-mode` runs for 2 consecutive weeks (ongoing monitoring)
- [x] CI warning count reduced to external-only (COMPLETED)

---


### **Phase 1: Enhanced Task & Check-in Systems** **PARTIALLY COMPLETE**

**Status**: **PARTIALLY COMPLETE**  
**Priority**: High  
**Last Updated**: 2025-11-20

**Completed** (documented in changelog):
- [x] **Enhanced Task Reminder System** (COMPLETED - documented in changelog)
  - Priority-based weighting, due date proximity weighting, critical priority level, no due date option
- [x] **Semi-Random Check-in Questions** (COMPLETED - documented in changelog)
  - Weighted selection, question variety, category balancing

**Remaining Work**:
- [ ] **Check-in Response Analysis** (High Impact, Medium Effort)
  - [ ] Implement pattern analysis of responses over time
  - [ ] Add progress tracking for mood trends
  - [ ] Create response categorization and sentiment analysis
  - [ ] Generate insights for AI context enhancement
  - [ ] Test pattern analysis accuracy
  - [ ] Validate progress tracking metrics
- [ ] **Enhanced Context-Aware Conversations** (Medium Impact, Medium Effort)
  - [ ] Expand user context with check-in history
  - [ ] Add conversation history analysis
  - [ ] Implement preference learning from interactions
  - [ ] Create more sophisticated personalization algorithms
  - [ ] Test context enhancement effectiveness
  - [ ] Validate personalization improvements

---

### **Phase 2: Mood-Responsive AI & Advanced Intelligence** [WARNING] **PARTIALLY COMPLETE**

**Status**: [WARNING] **PARTIALLY COMPLETE**  
**Priority**: High  
**Effort**: High  
**Date**: 2025-11-10

**Goal**: Implement mood-responsive AI conversations and advanced emotional intelligence

**Current State**:
- [OK] **Mood data included in context**: AI chatbot includes mood and energy data from check-ins in context (`ai/chatbot.py`, `ai/context_builder.py`)
- [OK] **Mood trend analysis**: Context builder analyzes mood trends (improving/declining/stable)
- [OK] **Emotional intelligence in system prompt**: System prompt includes emotional intelligence instructions
- [OK] **Mood-aware completion messages**: Check-in completion messages adapt based on mood/energy (`communication/message_processing/conversation_flow_manager.py`)
- [X] **Prompt modification based on mood**: Prompts are NOT dynamically modified based on mood/energy - mood data is only included in context
- [X] **Tone adaptation algorithms**: No explicit tone adaptation based on detected mood
- [X] **Emotional response templates**: No mood-specific response templates
- [X] **Mood prediction**: No predictive mood analysis

**What's Missing**:
- [ ] **Dynamic prompt modification**: Modify system prompt or add mood-specific instructions based on detected mood/energy levels
- [ ] **Tone adaptation algorithms**: Implement algorithms that adjust response tone based on mood (e.g., more gentle for low mood, more energetic for high energy)
- [ ] **Emotional response templates**: Create templates for different mood states (low mood = more supportive, high mood = more celebratory)
- [ ] **Enhanced mood tracking**: More granular mood detection (beyond 1-5 scale)
- [ ] **Mood prediction**: Predictive analysis of mood trends
- [ ] **Emotional intelligence scoring**: System to score and improve emotional intelligence of responses
- [ ] **Machine learning patterns**: Advanced ML-based mood analysis (currently uses simple averages/trends)

---

### **Phase 3: Proactive Intelligence & Advanced Features** [WARNING] **NEW**

**Goal**: Implement proactive suggestion system and advanced AI capabilities  
**Status**: Planning Phase  
**Estimated Duration**: 3-4 weeks

**Checklist**:
- [ ] **Proactive Suggestion System** (Medium Impact, High Effort)
  - [ ] Analyze user patterns and habits from check-in and task data
  - [ ] Generate contextual suggestions based on patterns
  - [ ] Implement suggestion timing and delivery algorithms
  - [ ] Add suggestion relevance scoring and filtering
  - [ ] Test suggestion accuracy and user engagement
  - [ ] Validate proactive system effectiveness
- [ ] **Advanced Context-Aware Personalization** (Medium Impact, High Effort)
  - [ ] Implement deep learning from user interaction patterns
  - [ ] Add adaptive personality traits based on user preferences
  - [ ] Create sophisticated preference learning algorithms
  - [ ] Implement context-aware response generation
  - [ ] Test personalization depth and accuracy
  - [ ] Validate adaptive personality effectiveness
- [ ] **Smart Home Integration Planning** [WARNING] **LONG-TERM/FUTURE** - Not applicable for current single-user personal assistant; mentioned in [PROJECT_VISION.md](PROJECT_VISION.md) Phase 3 but not a current priority
  - [ ] Research smart home APIs and protocols
  - [ ] Design integration architecture for future implementation
  - [ ] Document requirements and constraints
  - [ ] Create integration roadmap and timeline
  - [ ] Test integration feasibility with sample APIs
  - [ ] Validate integration architecture design
  - **Note**: This is a future consideration from [PROJECT_VISION.md](PROJECT_VISION.md) Phase 3. With only 1-2 users and focus on core mental health assistant features, smart home integration is not currently applicable or prioritized.

---

### **UI Migration Plan**

**Status**: Foundation, Dialogs, and Widgets Complete; Testing Remaining  
**Last Updated**: 2025-11-20

**Completed** (documented in changelogs):
- [x] **Foundation**: PySide6/Qt migration, file reorganization, naming conventions, widget refactoring, user data migration, signal-based updates, 100% function documentation
- [x] **Dialog Implementation**: All 7 dialogs complete (Category Management, Channel Management, Check-in Management, User Profile, Account Creator, Task Management, Schedule Editor)
- [x] **Widget Implementation**: All 6 widgets complete (TagWidget, Task Settings, Category Selection, Channel Selection, Check-in Settings, User Profile Settings)
- [x] **Main UI Application**: 21 behavior tests complete

**Remaining Work**:
- [ ] **Testing & Validation Strategy** (consolidated UI component testing plan)
  - [ ] **Phase 1: Core UI Components**
    - [ ] `ui/ui_app_qt.py` (main application bootstrap)
    - [ ] `ui/dialogs/task_crud_dialog.py` (task CRUD)
    - [ ] `ui/generate_ui_files.py` (UI file generation)
  - [ ] **Phase 2: Dialog Components**
    - [ ] `ui/dialogs/account_creator_dialog.py`
    - [ ] `ui/dialogs/checkin_management_dialog.py`
    - [ ] `ui/dialogs/task_management_dialog.py`
    - [ ] `ui/dialogs/category_management_dialog.py`
  - [ ] **Phase 3: Widget Components**
    - [ ] `ui/widgets/task_settings_widget.py`
    - [ ] `ui/widgets/channel_selection_widget.py`
    - [ ] `ui/widgets/checkin_settings_widget.py`
    - [ ] `ui/widgets/category_selection_widget.py`
  - [ ] **Test Categories**
    - [ ] Button functionality (click actions, state changes, shortcuts)
    - [ ] Input validation (text, numeric, date/time, dropdowns)
    - [ ] Dialog workflows (open/close, save/cancel, modal behavior)
    - [ ] Widget interactions (data binding, event propagation, state management)
    - [ ] Error handling (validation errors, system errors)
  - [ ] **Integration Testing**
    - [ ] Cross-dialog communication
    - [ ] Windows path compatibility tests around messages defaults and config path creation
    - [ ] Expand preferences save/load tests to cover Pydantic normalization and legacy flag handling (full vs partial updates)
    - [ ] Add tests for read-path normalization (`normalize_on_read=True`) at critical read sites (schedules, account/preferences)
- [ ] **UI Quality Improvements**
  - [ ] Fix Dialog Integration (main window updates after dialog changes)
  - [ ] Add Data Validation across all forms
  - [ ] Improve Error Handling with clear, user-friendly messages
  - [ ] Monitor and optimize UI responsiveness for common operations

---

### **Testing Strategy Plan**

**Status**: Core, Communication, and Supporting Modules Complete; UI Layer and Integration Testing Remaining  
**Last Updated**: 2025-11-20

**Remaining Work**:
- [ ] **UI Layer Testing** - See "UI Migration Plan" for detailed checklist
- [ ] **Integration Testing**
  - [ ] Cross-module workflows
  - [ ] End-to-end user scenarios
  - [ ] Performance testing
  - [ ] End-to-end tests for `/checkin` flow via Discord and via plain text
  - [ ] End-to-end tests for `/status`, `/profile`, `/tasks` via Discord slash commands
  - [ ] Windows path tests: default messages load and directory creation using normalized separators

---


### **Channel Interaction Implementation Plan**

**Status**: Email Integration Complete, Cross-Channel Sync Remaining  
**Last Updated**: 2025-11-20

**Completed**:
- [x] Email Integration - Full email-based interaction system (COMPLETED 2025-11-11, documented in changelog)
  - Email message body extraction, polling loop, user mapping, message routing, response sending

**Remaining Work**:
- [ ] Cross-Channel Sync - Synchronize data across supported channels
  - Note: Telegram integration has been removed from scope

---



**Note**: Task system work is tracked in [TASKS_PLAN.md](development_docs/TASKS_PLAN.md). Individual Task Reminders and Recurring Tasks are completed (custom reminder times implemented in scheduler.py and task_management.py). All remaining items should be updated in the tasks plan.

---
