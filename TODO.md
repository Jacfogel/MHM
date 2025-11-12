# TODO.md - MHM Project Tasks
> **Audience**: Human Developer (Beginner Programmer) and AI collaborators
> **Purpose**: Current development priorities and planned improvements  
> **Style**: Organized, actionable, beginner-friendly
> **See [README.md](README.md) for complete navigation and project overview**
> **See [DEVELOPMENT_WORKFLOW.md](DEVELOPMENT_WORKFLOW.md) for safe development practices**
> **See [TEST_COVERAGE_EXPANSION_PLAN.md](development_docs/TEST_COVERAGE_EXPANSION_PLAN.md) for testing strategy**
## ?? How to Add New TODOs

When adding new tasks, follow this format:

```markdown
**Task Title** - Brief description
- *What it means*: Simple explanation of the task
- *Why it helps*: Clear benefit or improvement
- *Estimated effort*: Small/Medium/Large
```

**Guidelines:**
- Use **bold** for task titles
- Group tasks by priority (High/Medium/Low sections)
- Use clear, action-oriented titles
- Include estimated effort to help with planning
- Add status indicators (?? **IN PROGRESS**) when relevant
- Don't include priority field since tasks are already grouped by priority
- **TODO.md is for TODOs only** - completed tasks should be documented in CHANGELOG files and removed from TODO.md


**Nightly No-Shim Validation Runs**
- *What it means*: Run the full suite with `ENABLE_TEST_DATA_SHIM=0` nightly to validate underlying stability.
- *Why it helps*: Ensures we're not masking issues behind the test-only shim and maintains long-term robustness.
- *Estimated effort*: Small

**Monitor Test Warning Status**
- *What it means*: Monitor test suite warnings to ensure they remain at expected levels (4 external library deprecation warnings expected: 3 Discord + 1 audioop, 1 RuntimeWarning from Discord bot test)
- *Why it helps*: Ensures test suite health and prevents warnings from masking real issues
- *Estimated effort*: Small

**Continue Error Handling Quality Improvements** (Optional)
- *What it means*: Continue improving error handling quality by replacing basic try-except blocks with @handle_errors decorator and adding error handling to remaining functions where appropriate
- *Why it helps*: Improves system robustness and reliability by protecting more functions against errors
- *Estimated effort*: Medium
- *Current Status*: ✅ **94.25% coverage achieved** (1,392 of 1,477 functions protected, 1,280 with @handle_errors decorator) - **93%+ target achieved on 2025-11-10**
- *Remaining Work* (Optional):
  - [ ] **Continue Expanding Beyond 94.25%** (if desired):
    - [ ] Add error handling to remaining 85 functions where appropriate
    - [ ] Note: Many remaining functions are constructors (`__init__`), Pydantic validators (cannot use decorator), logger methods (already in error handling system), or `__getattr__` methods
    - [ ] Focus on UI modules and utility functions that would benefit from error handling
  - [ ] **Replace Basic Try-Except Blocks**
    - [ ] Replace remaining 103 basic try-except blocks with @handle_errors decorator
    - [ ] Improve error handling quality from basic to excellent

**Phase 1: Enhanced Task & Check-in Systems** ?? **In Progress**
- *What it means*: Implement priority-based task reminders, semi-random check-ins, and response analysis to align with project vision
- *Why it helps*: Provides immediate improvements to core functionality that directly supports user's executive functioning needs
- *Estimated effort*: Large (1-2 weeks)
- *Subtasks*:
  - [ ] **Enhanced Task Reminder System** (follow-ups)
    - [ ] Add recurring task support with flexible scheduling
    - [ ] Validate recurring task scheduling patterns
  - [ ] **Check-in Response Analysis**
    - [ ] Implement pattern analysis of responses over time
    - [ ] Add progress tracking for mood trends
    - [ ] Create response categorization and sentiment analysis
    - [ ] Generate insights for AI context enhancement
    - [ ] Test pattern analysis accuracy
    - [ ] Validate progress tracking metrics
  - [ ] **Enhanced Context-Aware Conversations**
    - [ ] Expand user context with check-in history
    - [ ] Add conversation history analysis
    - [ ] Implement preference learning from interactions
    - [ ] Create more sophisticated personalization algorithms
    - [ ] Test context enhancement effectiveness
    - [ ] Validate personalization improvements

**Discord Send Retry Monitoring** ✅ **COMPLETED**
- *What it means*: Verify queued retry behavior on disconnects and that check-in starts log only after successful delivery.
- *Why it helps*: Prevents lost messages and duplicate check-in starts.
- *Status*: Completed verification and testing on 2025-11-10:
  - Verified scheduled check-ins log "User check-in started" only after successful send (channel_orchestrator.py:1044-1049)
  - Confirmed retry mechanism exists via RetryManager (communication/core/retry_manager.py)
  - Verified failed messages are queued when send fails (send_message_sync queues failed messages when channel not ready)
  - Created comprehensive test suite `tests/behavior/test_discord_checkin_retry_behavior.py` with 5 passing tests:
    - test_checkin_message_queued_on_discord_disconnect: Verifies messages queue when Discord disconnects
    - test_checkin_started_logged_once_after_successful_send: Verifies single log entry after successful send
    - test_checkin_started_not_logged_on_failed_send: Verifies no log entry on failed send
    - test_checkin_retry_after_discord_reconnect: Verifies retry mechanism works after reconnect
    - test_multiple_checkin_attempts_only_log_once: Verifies multiple attempts only log once
  - **Note**: Manual check-in path (conversation_flow_manager.py:225) logs before sending - this is a separate code path for user-initiated check-ins, not scheduled ones


**Pydantic Schema Adoption Follow-ups**
- *What it means*: We added tolerant Pydantic models. Expand usage safely across other save/load paths.
- *Why it helps*: Stronger validation and normalized data.
- *Estimated effort*: Medium
- *Subtasks*:
  - [ ] Extend schema validation to schedules save paths not yet using helpers (confirm all call-sites)
  - [ ] Add unit tests for `validate_*_dict` helpers with edge-case payloads (extras, nulls, invalid times/days)
  - [ ] Add behavior tests for end-to-end save/load normalization
  - [ ] Add read-path normalization invocation to remaining reads that feed business logic (sweep `core/` and `communication/`)

**Discord Task Edit Follow-ups and Suggestion Relevance** ✅ **COMPLETED**
- *What it means*: Ensure edit-task prompts are actionable, suppress irrelevant suggestions, and add coverage for common follow-ups
- *Why it helps*: Reduces confusion and makes conversations efficient
- *Estimated effort*: Small/Medium
- *Subtasks*:
  - [x] Behavior tests: edit task by name then change due date (natural language variations: "due date", "due")
  - [x] Behavior tests: verify no generic suggestions accompany targeted "what would you like to update" prompts
  - [x] Behavior tests: list tasks ? edit task flow ensures "which task" is asked when not specified

**Channel-Agnostic Command Registry Follow-ups**
- *What it means*: Finalize and monitor the new centralized command system and Discord integrations
- *Why it helps*: Ensures consistent behavior across channels and prevents regressions
- *Estimated effort*: Small/Medium
- *Subtasks*:
  - [ ] Add behavior tests for dynamic Discord app commands (registration, sync, callback wiring)
  - [ ] Add behavior tests for classic dynamic commands (skip `help`, ensure mapping works)
  - [ ] Verify unknown `/` and `!` prefixes fall back to parser and contextual chat
  - [ ] Document command list in QUICK_REFERENCE.md
  - [ ] Ensure user-facing help uses in-app "commands"/slash-commands (no dev-doc references)

**Check-in Flow Behavior & Stability**
- *What it means*: Ensure active check-ins expire correctly and legacy shims are not used in live flows
- *Why it helps*: Prevents stale states and confusing interactions during conversations
- *Estimated effort*: Small/Medium
- *Subtasks*:
  - [ ] Monitor logs for legacy compatibility warnings related to check-ins (`start_checkin`, `FLOW_CHECKIN`, `get_recent_checkins`, `store_checkin_response`)
  - [ ] Verify Discord behavior: after a check-in prompt goes out, send a motivational or task reminder and confirm the flow expires
  - [ ] Consider inactivity-based expiration (30-60 minutes) in addition to outbound-triggered expiry (optional)
  - [ ] Add behavior test for flow expiration after unrelated outbound message
  - [ ] **Test fixes with real Discord check-in flow and verify flow state persistence** - Restart service and test that check-in flows persist through scheduled message checks
  - [ ] **Monitor logs for MESSAGE_SELECTION debug info** - Understand why sometimes no messages match (review matching_periods, current_days, and message filtering)

## High Priority

**CRITICAL: Investigate Email Polling Errors**
- *What it means*: Investigate why email polling is failing repeatedly in `channel_orchestrator.py` - errors logged every 40 seconds with empty exception messages ("Error polling for emails: ") since changes made on 2025-11-11
- *Why it helps*: Email polling is critical for receiving user messages - repeated failures prevent the system from receiving emails properly
- *Estimated effort*: Medium
- *Investigation Steps*:
  - [ ] Check `_email_polling_loop()` in `communication/core/channel_orchestrator.py` (line 198-236)
  - [ ] Review exception handling - exception messages appear empty in logs
  - [ ] Check if email channel initialization is working correctly
  - [ ] Verify event loop setup and async/await handling
  - [ ] Check if `receive_messages()` is raising exceptions properly
  - [ ] Review recent changes to email polling implementation (added 2025-11-11)
- *Error Pattern*: Errors occur every ~40 seconds, exception message is empty, suggests exception handling or logging issue
- *Files to Review*: `communication/core/channel_orchestrator.py`, `communication/communication_channels/email/bot.py`, `logs/errors.log` (lines 1794-1802)

**Optimize Audit System Performance**
- *What it means*: Explore the audit system and adjust it so it runs in under 10 minutes (currently takes ~18-20 minutes)
- *Why it helps*: Significantly improves workflow efficiency and makes full audits more practical for regular use
- *Estimated effort*: Medium
- *Areas to investigate*:
  - Unused imports checker (currently ~7-8 minutes) - explore parallelization, caching, or incremental scanning
  - Coverage regeneration (currently ~10 minutes) - explore parallel test execution or selective coverage
  - Other contributing tools that may be slow

**Accelerate Test Suite Execution**
- *What it means*: Explore options to accelerate test runs further, possibly by using more parallel workers or optimizing test execution
- *Why it helps*: Faster feedback loops improve development speed and make testing more practical
- *Estimated effort*: Medium
- *Areas to investigate*:
  - Increase pytest parallel workers (currently using `-n auto`)
  - Optimize slow tests or add pytest marks for better parallelization
  - Profile test execution to identify bottlenecks

**Fix Flaky Tests in Parallel Execution Mode**
- *What it means*: Investigate and fix tests that fail when run in parallel mode (`-n auto` with pytest-xdist) but pass when run sequentially
- *Why it helps*: Ensures test reliability and enables safe use of parallel execution for faster test runs
- *Estimated effort*: Medium
- *Known Flaky Tests* (fail intermittently in parallel, pass sequentially):
  - `tests/ui/test_ui_app_qt_main.py::TestMHMManagerUI::test_update_service_status_updates_display` - Likely race condition with UI state
  - `tests/ui/test_ui_app_qt_main.py::TestMHMManagerUI::test_manage_tasks_opens_dialog` - UI dialog opening race condition (observed 2025-11-11)
  - `tests/ui/test_account_creation_ui.py::TestAccountManagementRealBehavior::test_feature_enablement_persistence_real_behavior` - KeyError: 'account' - Possible shared state or file locking issue (observed 2025-11-11, multiple runs)
  - `tests/behavior/test_backup_manager_behavior.py::TestBackupManagerBehavior::test_restore_backup_with_config_files_real_behavior` - assert False is True - Backup restoration failing in parallel (observed 2025-11-11, multiple runs)
  - `tests/behavior/test_backup_manager_behavior.py::TestBackupManagerBehavior::test_list_backups_real_behavior` - AssertionError: assert 2 == 3 - Missing backup in list, possible race condition (observed 2025-11-11)
  - `tests/integration/test_user_creation.py::TestUserCreationIntegration::test_user_with_all_features` - AssertionError: assert 'motivational' in {} - Schedules not saved/loaded correctly (observed 2025-11-11)
  - `tests/integration/test_user_creation.py::TestUserCreationIntegration::test_multiple_users_same_channel` - KeyError: 'account' - Account data not saved/loaded correctly (observed 2025-11-11)
  - `tests/behavior/test_discord_checkin_retry_behavior.py::TestDiscordCheckinRetryBehavior::test_checkin_message_queued_on_discord_disconnect` - AssertionError: queue size is 0 - Retry queue not working in parallel (observed 2025-11-11, multiple runs)
  - `tests/behavior/test_interaction_handlers_behavior.py::TestInteractionHandlersBehavior::test_profile_handler_shows_actual_profile` - AssertionError: Failed to create test user - Permission denied on user_index.json (observed 2025-11-11)
  - `tests/ui/test_widget_behavior.py::TestUserProfileSettingsWidgetBehavior::test_widget_initialization_real_behavior` - AssertionError: Could not find actual user ID - JSON parsing error, possible file corruption from parallel access (observed 2025-11-11)
  - `tests/ui/test_widget_behavior.py::TestTaskSettingsWidgetBehavior::test_task_enablement_real_behavior` - AssertionError: Could not find actual user ID - User creation failing (observed 2025-11-11)
  - `tests/unit/test_user_data_manager.py::TestUserDataManagerConvenienceFunctions::test_get_user_summary_function` - AssertionError: Should include user_id - Returns empty dict, possible race condition (observed 2025-11-11)
  - `tests/unit/test_logger_unit.py::TestEnsureLogsDirectory::test_ensure_logs_directory_creates_directories` - AssertionError: Should create archive directory - File system race condition (observed 2025-11-11)
  - `tests/behavior/test_utilities_demo.py::TestUtilitiesDemo::test_scheduled_user_creation` - AssertionError: Scheduled user should be created successfully - Intermittent failure
- *Known Issues*:
  - **File locking errors**: Multiple processes trying to access `tests/data/user_index.json` simultaneously (Permission denied: [Errno 13]) - **CRITICAL**: This is causing multiple test failures
  - **File corruption**: JSON parsing errors ("Expecting value: line 1 column 1 (char 0)") suggesting files are being read while being written by another worker
  - **errors.log still exists**: The `tests/logs/errors.log` file is still being created by component loggers, even though logs are redirected to consolidated log. File locking prevents cleanup (WinError 32/5). **Note**: At least it's no longer being copied repeatedly into test_consolidated.log (fixed 2025-11-11)
  - File locking errors: Multiple processes trying to access `tests/logs/app.log` and `tests/logs/errors.log` simultaneously (WinError 32)
  - Duplicate log content: Same log entries appearing multiple times in consolidated logs (likely due to multiple workers writing to same files) - **FIXED**: No longer copying from errors.log (2025-11-11)
  - Test isolation: Some tests may be sharing singleton instances (e.g., `CommunicationManager`) causing race conditions
- *Investigation Steps*:
  - [ ] **PRIORITY**: Fix `user_index.json` file locking - multiple workers accessing same file causing Permission denied errors
  - [ ] Run each flaky test individually in parallel mode to confirm flakiness
  - [ ] Check for shared state (singletons, global variables, file system state)
  - [ ] Review test fixtures for proper isolation (especially `comm_manager`, `test_data_dir`)
  - [ ] Fix file locking issues in test log cleanup/setup
  - [ ] Consider marking tests that require serial execution with `@pytest.mark.serial` (if pytest-xdist supports it) or grouping them separately
  - [ ] Review `--dist=loadscope` distribution strategy - may need `--dist=worksteal` or custom grouping
  - [ ] Investigate if `user_index.json` needs per-worker copies or file locking mechanism

**AI Chatbot Actionability Sprint** - Plan and implement actionable AI responses
- *What it means*: Improve AI chat quality and enable robust task/message/profile CRUD, with awareness of recent automated messages and targeted, non-conflicting suggestions.
- *Why it helps*: Addresses the user's biggest friction and increases real utility.
- *Estimated effort*: Large


**Fix AI response quality issues identified in test results**
- *What it means*: Address 10 issues identified in AI functionality test results: prompt-response mismatches (greetings not acknowledged, questions redirected), fabricated check-in data, incorrect facts, repetitive responses, code fragments in command responses, and system prompt leaks
- *Why it helps*: Improves AI response quality and ensures responses actually address user prompts appropriately
- *Estimated effort*: Medium
- *Current Status*: ✅ **IN PROGRESS** - Significant improvements made:
  - ✅ T-1.1, T-12.2: Greeting handling instructions strengthened with BAD/GOOD examples (prompt updated, monitoring)
  - ✅ T-1.2, T-12.4, T-15.2: Information request handling strengthened with explicit BAD/GOOD examples for "Tell me about your capabilities", "Tell me a fact", and "Tell me about yourself" (prompt updated, monitoring)
  - ✅ T-2.1, T-2.3, T-8.1, T-14.1: Vague reference instructions strengthened (improved, still some remaining)
  - ✅ T-4.1, T-9.2, T-13.3: Fabricated data prevention added
  - ✅ T-13.3: Meta-text leak cleaning enhanced
  - ✅ T-12.1: Information request handling added (should provide helpful info, not redirect)
  - ✅ T-15.2: "Tell me about yourself" handling strengthened with explicit examples
  - ✅ T-11.1: Code fragments in command responses - FIXED (added cleaning for cached responses and enhanced fragment detection)
  - ✅ T-12.4: Incorrect fact with self-contradiction - PREVENTION ADDED (logical consistency instructions)
  - ⚠️ T-15.1: System prompt instructions leaked (cleaning added, monitor)
- *Specific Issues*:
  - ✅ T-1.1, T-12.2: Prompt-response mismatches (greetings) - PROMPT UPDATED with BAD/GOOD examples (monitoring)
  - ✅ T-1.2, T-12.4, T-15.2: Prompt-response mismatches (information requests) - PROMPT UPDATED with explicit BAD/GOOD examples (monitoring)
  - ⚠️ T-8.1, T-9.3: Prompt-response mismatches (questions redirected) - IMPROVED (still monitoring)
  - ✅ T-11.1: Code fragments in command responses - FIXED
  - ✅ T-12.1: Generic motivational content instead of helpful information - IMPROVED
  - ✅ T-12.4: Incorrect fact with self-contradiction - PREVENTION ADDED
  - ✅ T-14.1, T-16.2: Fabricated check-in details/statistics - PREVENTION ADDED
  - ✅ T-13.3: System prompt instructions leaked - CLEANING ENHANCED



**Design Safety Net Response Library**
- *What it means*: Draft and validate a library of "safety net" phrases that feel grounding when things are overwhelming, including branching prompts (listen/problem-solve/other) that match the user's preferred tone.
- *Why it helps*: Ensures the assistant consistently signals it “gets it,” even when the user is unsure what support they need, aligning reminders with the emotional safety net vision.
- *Estimated effort*: Medium
- *Getting started*: Collect existing comforting phrases, prototype a few tone variants, and run with recent conversation logs to verify fit.

**Task Breakdown Prompt Experiments**
- *What it means*: Prototype both checklist-style subtasks and conversational follow-ups for stuck tasks, then capture which approach keeps users engaged on mobile.
- *Why it helps*: Provides context-aware nudges that unblock stalled tasks, matching the user’s request for format experimentation.
- *Estimated effort*: Small/Medium
- *Acceptance criteria*: Document example prompts, note when to surface each format, and gather feedback from at least one real or simulated session.

**Context-Aware Reminder Content Mapping**
- *What it means*: Map task reminder content to user context (energy, mood, task age) so the system can choose the most relevant substance instead of generic nudges.
- *Why it helps*: Addresses the user’s need for “it depends” reminders that feel situationally aware rather than repetitive.
- *Estimated effort*: Medium
- *Next steps*: Audit available context signals, define decision rules, and outline example reminder variants for contrasting scenarios.

**Unavailable Mode Naming & Rules**
- *What it means*: Replace “outside-work quiet mode” language with an “Unavailable/Do Not Disturb” concept and define what counts as urgent during those periods.
- *Why it helps*: Aligns terminology with the user’s preference and prevents work-centric framing of downtime.
- *Estimated effort*: Small
- *Deliverable*: Updated glossary, configuration copy, and urgency criteria for reminders during unavailable slots.

**Mood Re-evaluation Cadence Guidelines**
- *What it means*: Specify triggers and guardrails for when the assistant should gently re-check mood/energy (e.g., disengagement signals, user-provided updates) without over-prompting.
- *Why it helps*: Balances proactive support with respect for the user’s space, clarifying “when it should ask again” from the user’s feedback.
- *Estimated effort*: Medium
- *Definition of done*: Draft cadence rules, edge-case handling, and handoff to implementation/testing once validated.

## Medium Priority

**Investigate Test Log Rotation Issues**
- *What it means*: Investigate why `test_consolidated.log` is not rotating properly - file has grown to 500,000+ lines and should rotate at 5MB but rotation only happens at session start
- *Why it helps*: Prevents log files from growing unbounded, improves log management and system performance
- *Estimated effort*: Small/Medium
- *Areas to investigate*:
  - Check `SessionLogRotationManager` in `tests/conftest.py` - rotation check happens at session start only
  - Verify rotation size threshold (5MB) is being checked correctly
  - Consider adding rotation checks during test execution, not just at start
  - Review if file size calculation is working correctly for large files
  - Check if rotation is being prevented by file locking or other issues
- *Current Status*: Rotation logic exists but only runs at session start - if a single session creates a huge log file, it won't rotate until next session
- *Files to Review*: `tests/conftest.py` (SessionLogRotationManager class, setup_consolidated_test_logging fixture)

**Investigate Test Coverage Analysis Failures**
- *What it means*: Explore why tests that usually pass sometimes fail during test coverage analysis (e.g., `test_scheduled_user_creation`, `test_ensure_logs_directory_creates_directories`)
- *Why it helps*: Ensures reliable test execution and accurate coverage metrics
- *Estimated effort*: Small/Medium
- *Areas to investigate*:
  - Timing issues or race conditions that only appear during coverage collection
  - Resource contention or file locking issues
  - Differences in test execution order or environment during coverage runs

**Optimize Unused Imports Checker**
- *What it means*: Explore options for accelerating the unused imports checker (currently takes ~7-8 minutes) and reduce excessive logging
- *Why it helps*: Makes the unused imports checker more practical for regular use and reduces log noise
- *Estimated effort*: Medium
- *Areas to investigate*:
  - Parallelization of pylint analysis across files
  - Caching of analysis results for unchanged files
  - Incremental scanning (only check modified files)
  - Reduce DEBUG-level logging that creates excessive log output

**Fix Legacy Import Checker Self-Identification**
- *What it means*: Improve legacy import checker so it doesn't positively identify itself as somewhere legacy imports are present
- *Why it helps*: Reduces false positives and makes legacy cleanup reports more accurate
- *Estimated effort*: Small
- *Areas to investigate*:
  - Exclude the checker's own file from legacy pattern matching
  - Improve pattern matching to avoid matching the checker's own code

**Expand Pytest Marks Usage**
- *What it means*: Explore adding pytest marks to more tests to enable better test organization, filtering, and parallelization
- *Why it helps*: Enables selective test execution, better test organization, and improved parallel test execution
- *Estimated effort*: Medium
- *Areas to investigate*:
  - Add marks for test categories (unit, behavior, integration, ui)
  - Add marks for test speed (fast, slow)
  - Add marks for test dependencies or requirements
  - Use marks to optimize parallel test execution

**Systematic Documentation Review and Update**
- *What it means*: Systematically review and update documentation to ensure information is current and accurate across all documentation files
- *Why it helps*: Ensures documentation remains useful and prevents confusion from outdated information
- *Estimated effort*: Large
- *Areas to review*:
  - Development guides (human and AI versions)
  - Architecture documentation
  - Testing guides
  - Error handling guides
  - Logging guides
  - User-facing documentation
  - API documentation
  - Configuration documentation

**Standardize Backup, Rotation, Archive, and Cleanup Approaches**
- *What it means*: Review data, log and file backup, rotation, archive, cleanup approaches throughout the codebase and standardize them (including tests and ai_development_tools)
- *Why it helps*: Ensures consistent behavior, reduces code duplication, and makes maintenance easier
- *Estimated effort*: Medium
- *Areas to review*:
  - Log rotation and cleanup (core/logger.py, ai_development_tools)
  - Backup creation and management (core/backup_manager.py, tests)
  - File archiving (auto_cleanup.py, ai_development_tools)
  - Test data cleanup (tests/test_utilities.py, test fixtures)
  - Temporary file cleanup patterns

**Reorganize AI Development Tools Subdirectory**
- *What it means*: Reorganize ai_development_tools subdirectory, including a review of the files within to determine whether any of them are no longer active or useful
- *Why it helps*: Improves organization, reduces confusion, and makes the tools easier to navigate and maintain
- *Estimated effort*: Medium
- *Areas to review*:
  - Identify unused or obsolete tools
  - Group related tools into logical subdirectories
  - Update documentation to reflect new organization
  - Archive or remove tools that are no longer needed
  - Ensure all active tools are properly documented

**Personalized User Suggestions Implementation** - Review and implement proper personalized suggestions
- *What it means*: Review the current `get_user_suggestions()` function and implement proper personalized suggestion functionality
- *Why it helps*: Provides users with meaningful, personalized suggestions based on their data and preferences
- *Estimated effort*: Medium
- *Requirements*:
  - Analyze user data patterns and preferences
  - Implement suggestion algorithms based on user context
  - Add suggestion categories (tasks, health, motivation, etc.)
  - Test suggestion relevance and personalization


**Pathlib Migration Completion**
- *What it means*: Finish converting remaining path joins to `pathlib.Path` where appropriate.
- *Why it helps*: Cross-platform safety and readability.
- *Estimated effort*: Medium
- *Current Status*: ⚠️ **ROLLED BACK** - Previous migration attempt was rolled back due to test issues:
  - Test `test_run_service_loop_shutdown_file_detection_real_behavior` was causing resource exhaustion and hanging
  - Path mocking in tests needs to be handled more carefully to prevent infinite loops
  - Need to ensure proper mocking of `pathlib.Path` operations in service loop tests
  - **Note**: Remote pathlib code changes (13 modules, 60+ conversions) are being merged, but status remains ROLLED BACK until test issues are resolved
- *Next Attempt*:
  - [ ] Sweep `core/` for remaining `os.path.join` not covered by helpers
  - [ ] Convert `os.path.*` operations to `pathlib.Path` equivalents
  - [ ] Fix test mocking to properly handle `pathlib.Path` objects (use `MagicMock(spec=Path)` instead of direct attribute assignment)
  - [ ] Ensure service loop tests have proper safeguards to prevent infinite loops
  - [ ] Test incrementally with small groups of tests to catch issues early
  - [ ] Confirm all UI-related file paths still work as expected under tests

**Legacy UserContext Bridge Removal** ✅ **COMPLETED**
- *What it means*: Remove legacy format conversion/extraction in `user/user_context.py` once confirmed no usage
- *Why it helps*: Simplifies data access and reduces double-handling
- *Status*: Legacy format conversion/extraction code has already been removed. Code now uses modern formats directly with comments confirming "no legacy conversion needed" and "no legacy extraction needed". All callers verified to use modern format.


**Legacy Removal "Search-and-Close" Framework** ✅ **COMPLETED**
- *What it means*: Build a checklist and helper tooling to update all references before removing legacy flags/paths; avoid fixed time windows.
- *Why it helps*: Safe deprecations without relying on rare usage logs.
- *Status*: Completed framework on 2025-11-10:
  - Created AI-optimized guide (`ai_development_docs/AI_LEGACY_REMOVAL_GUIDE.md`) with search-and-close process
  - Enhanced `legacy_reference_cleanup.py` with `--find` command to find all references to a specific legacy item
  - Added `--verify` command to check removal readiness with categorized recommendations
  - Framework provides systematic 5-phase process: Find → Update → Verify → Remove → Test
  - Tools categorize references (active code, tests, docs, config, archive) and provide actionable recommendations
  - Integrated guidance into `.cursor/rules/quality-standards.mdc` and `.cursor/commands/refactor.md`
  - No emojis in output for Windows compatibility

**Testing Policy: Targeted Runs by Area (skip scripts/)** ✅ **COMPLETED**
- *What it means*: Default to running relevant test sections; consistently exclude `scripts/` tests.
- *Why it helps*: Faster feedback while preserving isolation requirements.
- *Status*: Completed on 2025-11-10:
  - Documented scripts exclusion policy in `ai_development_docs/AI_TESTING_GUIDE.md` and `tests/TESTING_GUIDE.md`
  - Added verification test `test_scripts_exclusion_policy.py` to ensure scripts/ is never discovered
  - Policy is enforced via `pytest.ini` configuration (norecursedirs, collect_ignore, --ignore flags)
  - Tests verify both that pytest doesn't discover scripts/ tests and that no test files exist in scripts/

**Help/Docs: Prefer Slash Commands, keep Bang Commands** ✅ **COMPLETED**
- *What it means*: Update help/UX text to prefer `/` commands with auto-suggested slash equivalents, while keeping `!` commands supported.
- *Why it helps*: Better Discord-native discoverability without breaking habits.
- *Status*: Updated help text in `interaction_handlers.py` and `DISCORD.md` to prefer slash commands. All command listings now show slash commands first with "(also !commands)" notation. Updated documentation to indicate slash commands are "preferred, Discord-native" while bang commands are "also supported". This improves Discord-native discoverability while maintaining backward compatibility.

### User Experience Improvements


**Improve Natural Language Processing Accuracy**
- *What it means*: Refine parsing patterns and thresholds to better recognize intents and entities
- *Why it helps*: More reliable command understanding and fewer misinterpretations
- *Estimated effort*: Medium

**Conversation Flow Management**
- *What it means*: Improve conversational state transitions and fallbacks to keep interactions smooth
- *Why it helps*: More predictable user experience and fewer dead-ends
- *Estimated effort*: Medium

### Performance Optimizations

**Optimize AI Response Times**
- *What it means*: Reduce latency for AI-backed responses via batching, caching, or configuration tuning
- *Why it helps*: Snappier interactions and better UX
- *Estimated effort*: Medium

**Improve Message Processing Efficiency**
- *What it means*: Profile and streamline message pipelines (I/O, parsing, scheduling)
- *Why it helps*: Lower CPU usage and faster processing
- *Estimated effort*: Medium

**Reduce Memory Usage**
- *What it means*: Identify hotspots (caches, data copies) and right-size buffers/limits
- *Why it helps*: Improves stability on constrained systems
- *Estimated effort*: Medium

## Low Priority


### Documentation

**Update User Guides**
- *What it means*: Refresh user-facing guides to reflect current features and workflows
- *Why it helps*: Reduces confusion and accelerates onboarding
- *Estimated effort*: Small

**Improve Code Documentation**
- *What it means*: Add/refresh docstrings and inline docs where clarity is lacking
- *Why it helps*: Speeds up development and AI assistance accuracy
- *Estimated effort*: Small

**Create Troubleshooting Guides**
- *What it means*: Document common issues and resolution steps for channels, UI, and data
- *Why it helps*: Faster recovery when issues occur
- *Estimated effort*: Small

### Testing

**Continue Test Coverage Expansion**
- *What it means*: Continue expanding test coverage for remaining low-coverage modules
- *Why it helps*: Increases reliability and change safety for core system components
- *Estimated effort*: Large
- *Current Status*: 17 modules completed (384 new tests added total, all passing) - see changelogs for details
- *Next Targets*:
  - [ ] Expand coverage for `ui/ui_app_qt.py` (33% coverage, 1095 lines) - Large module
  - [ ] Expand coverage for `core/scheduler.py` (65% → 80%+)
  - [ ] Add comprehensive tests for remaining communication modules
  - [ ] Focus on error handling and edge case coverage

**Add Integration Tests**
- *What it means*: Add cross-module workflow tests (user lifecycle, scheduling, messaging)
- *Why it helps*: Verifies real-world flows function correctly
- *Estimated effort*: Medium
- Subtasks:
  - [ ] End-to-end tests for `/checkin` flow via Discord and via plain text
  - [ ] End-to-end tests for `/status`, `/profile`, `/tasks` via Discord slash commands
  - [ ] Windows path tests: default messages load and directory creation using normalized separators

**CI Guard for Logging Enforcement**
- *What it means*: Wire the static logging check into CI to enforce ComponentLogger rules automatically.
- *Why it helps*: Prevents regressions of forbidden logging patterns.
- *Estimated effort*: Small
- *Subtasks*:
  - [ ] Add CI job step to run `scripts/static_checks/check_channel_loggers.py`
  - [ ] Ensure job runs before test steps and fails the pipeline on violations
  - [ ] Document the check in `logs/LOGGING_GUIDE.md` (contributor notes)

**Scripts Directory Cleanup** ✅ **COMPLETED**
- *What it means*: Remove outdated/broken files, organize remaining utilities, move AI tools to `ai_tools/`
- *Why it helps*: Reduces confusion and keeps the codebase organized
- *Status*: Completed cleanup on 2025-11-10:
  - Archived 14 outdated scripts (6 migration, 5 refactoring, 3 one-time enhancement scripts)
  - Fixed broken import in `user_data_cli.py` (changed `core.utils` to `core.user_data_handlers`)
  - Removed empty directories after archiving
  - Updated `scripts/README.md` to reflect current active scripts
  - Created cleanup analysis document (`scripts/CLEANUP_ANALYSIS.md`)
  - All archived scripts moved to `archive/scripts/` subdirectories

**Gitignore Cleanup** ✅ **COMPLETED**
- *What it means*: Review and clean up `.gitignore`
- *Why it helps*: Ensures proper version control and prevents unnecessary files from being tracked
- *Status*: Reviewed `.gitignore` file - found it to be comprehensive and well-organized. Fixed minor formatting issue (trailing space on `tests/logs/` entry). File properly excludes all necessary patterns including Python cache files, virtual environments, test artifacts, coverage files, IDE files, and project-specific temporary files.

**Improve AI Terminal Interaction Reliability**
- *What it means*: Investigate why AI assistants often misinterpret PowerShell output or make incorrect assumptions
- *Why it helps*: Reduces confusion and improves the reliability of AI-assisted development
- *Estimated effort*: Medium

**Fix Treeview Refresh** ✅ **COMPLETED**
- *What it means*: Auto-refresh the message editing interface to reflect changes while maintaining current sorting
- *Why it helps*: Better UX with immediate visual feedback
- *Status*: Implemented sort preservation in message editor dialog and task CRUD dialog. Tables now preserve sort column and order when refreshing after add/edit/delete operations. Sorting is enabled on table widgets and sort state is saved before refresh and restored after repopulation. Applied to both message editor dialog (1 table) and task CRUD dialog (2 tables: active tasks and completed tasks).

**Fix "process already stopped" notification issue** ✅ **OBSOLETE**
- *What it means*: Investigate why shutdown attempts result in "process already stopped" messages
- *Why it helps*: Cleaner service management and better user experience
- *Status*: Issue has not been observed in many months. The improved shutdown mechanism appears to have resolved the original issue. No code changes needed - system is working correctly.

**Add Performance Monitoring**
- *What it means*: Track how long operations take across subsystems
- *Why it helps*: Helps identify and fix performance problems proactively
- *Estimated effort*: Medium

**Create Development Guidelines**
- *What it means*: Establish coding standards and best practices
- *Why it helps*: Consistency and clarity, especially when collaborating with AI tools
- *Estimated effort*: Small



