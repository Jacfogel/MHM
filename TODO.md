# TODO.md - MHM Project Tasks

> **File**: `TODO.md`
> **Audience**: Human Developer (Beginner Programmer) and AI collaborators
> **Purpose**: Current development priorities and planned improvements  
> **Style**: Organized, actionable, beginner-friendly
> **See [README.md](README.md) for complete navigation and project overview**
> **See [DEVELOPMENT_WORKFLOW.md](DEVELOPMENT_WORKFLOW.md) for safe development practices**
> **See [TEST_COVERAGE_REPORT.md](development_docs/TEST_COVERAGE_REPORT.md) for testing strategy**

## How to Add New TODOs

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
- Add status indicators (**IN PROGRESS**) when relevant
- Don't include priority field since tasks are already grouped by priority
- **TODO.md is for TODOs only** - completed tasks should be documented in CHANGELOG files and removed from TODO.md


**Note**: Phase 1: Enhanced Task & Check-in Systems is tracked in [PLANS.md](development_docs/PLANS.md). 
**Note**: Mood-Aware Support Calibration items (Safety Net Response Library, Task Breakdown Prompt Experiments, Context-Aware Reminder Content Mapping, Mood Re-evaluation Cadence Guidelines) are tracked in [PLANS.md](development_docs/PLANS.md) under "Mood-Aware Support Calibration" plan.

**Nightly No-Shim Validation Runs**
- *What it means*: Run the full suite with `ENABLE_TEST_DATA_SHIM=0` nightly to validate underlying stability.
- *Why it helps*: Ensures we're not masking issues behind the test-only shim and maintains long-term robustness.
- *Estimated effort*: Small

**Channel-Agnostic Command Registry Follow-ups**
- *What it means*: Finalize and monitor the new centralized command system and Discord integrations
- *Why it helps*: Ensures consistent behavior across channels and prevents regressions
- *Estimated effort*: Small/Medium
- *Subtasks*:
  - [ ] Add behavior tests for dynamic Discord app commands (registration, sync, callback wiring)
  - [ ] Add behavior tests for classic dynamic commands (skip `help`, ensure mapping works)
  - [ ] Verify unknown `/` and `!` prefixes fall back to parser and contextual chat
  - [ ] Ensure user-facing help uses in-app "commands"/slash-commands (no dev-doc references)

**Check-in Flow Behavior & Stability**
- *What it means*: Ensure active check-ins expire correctly and legacy shims are not used in live flows
- *Why it helps*: Prevents stale states and confusing interactions during conversations
- *Estimated effort*: Small/Medium
- *Subtasks*:
  - [ ] Monitor logs for legacy compatibility warnings related to check-ins (`start_checkin`, `FLOW_CHECKIN`, `get_recent_checkins`, `store_checkin_response`)
  - [ ] Verify Discord behavior: after a check-in prompt goes out, send a motivational or task reminder and confirm the flow expires
  - [x] Consider inactivity-based expiration (30-60 minutes) in addition to outbound-triggered expiry (optional) - Added auto-expiration of stale check-ins after 45 minutes and prune on startup/new starts
  - [x] Add behavior test for flow expiration after unrelated outbound message
  - [ ] **Test fixes with real Discord check-in flow and verify flow state persistence** - Restart service and test that check-in flows persist through scheduled message checks
  - [ ] **Monitor logs for MESSAGE_SELECTION debug info** - Understand why sometimes no messages match (review matching_periods, current_days, and message filtering)

## High Priority

**Audit Flow State Expiration and Interference Prevention**
- *What it means*: Review all flow states (note flows, task flows, check-in flows, task reminder flows) to ensure they have appropriate time-based expiries and don't interfere with each other or automated messages. Active flow states should delay the start of scheduled automated flows/messages for a brief period of inactivity (e.g., 5-10 minutes) to prevent conflicts.
- *Why it helps*: Prevents flows from interfering with each other, ensures automated messages don't interrupt active user conversations, and maintains a smooth user experience
- *Estimated effort*: Medium
- *Subtasks*:
  - [ ] Review all flow states and their expiration logic (note body, list items, task due date, task reminder, check-in)
  - [ ] Verify expiration times are appropriate (currently 10 minutes for note/task flows, 2 hours for check-ins)
  - [ ] Ensure flow handlers detect and clear flows for unrelated messages (commands, greetings, etc.)
  - [ ] Add logic to delay scheduled automated messages/flows when user is in an active flow
  - [ ] Add logic to delay scheduled automated messages/flows for a brief period after flow completion (e.g., 5-10 minutes)
  - [ ] Test flow interference scenarios (active note flow + scheduled check-in, active task flow + scheduled reminder, etc.)
  - [ ] Document flow state management and interference prevention logic

**Fix Check-in Management Dialog Test Failures** [OK]
- *What it means*: Two unit tests in `tests/unit/test_checkin_management_dialog.py` are failing after recent changes to `save_checkin_settings()` method. Tests expect `set_schedule_periods()` and `update_user_account()` to be called, but they're not being called (0 times instead of 1). This is likely due to new validation logic added during check-in settings UI improvements that may be causing early returns or preventing the save from completing.
- *Why it helps*: Ensures test suite reliability and validates that check-in settings are properly saved with all required operations
- *Estimated effort*: Small/Medium
- *Status*: [OK] **COMPLETED** - Fixed by updating test data to include required `always_include`/`sometimes_include` fields in question data. The validation logic was correct; tests needed to provide valid question data that passes validation.
- *Subtasks*:
  - [x] Investigate `test_save_checkin_settings_saves_successfully` failure - Expected 'set_schedule_periods' to have been called once. Called 0 times
  - [x] Investigate `test_save_checkin_settings_updates_account_features` failure - Expected 'update_user_account' to have been called once. Called 0 times
  - [x] Review `save_checkin_settings()` method in `ui/dialogs/checkin_management_dialog.py` to identify why functions aren't being called
  - [x] Check if new validation logic (min/max question counts, enabled questions check) is causing early returns
  - [x] Update tests to account for new validation requirements or fix method to ensure functions are called when validation passes
  - [x] Verify tests pass after fixes

**Investigate Pytest Failures in Development Tools Test Suite**
- *What it means*: Investigate and fix intermittent test failures and pytest crashes in the development tools test suite. Currently experiencing: (1) flaky test `test_central_aggregation_includes_all_tool_results` that passes individually but sometimes fails in full suite (likely race condition), and (2) pytest crash with Windows error 0xC0000135 (STATUS_DLL_NOT_FOUND) indicating missing DLL required by Python or dependencies.
- *Why it helps*: Ensures test suite reliability, prevents false negatives that can mask real issues, and addresses system-level environment problems that may affect development workflow
- *Estimated effort*: Medium
- *Subtasks*:
  - [ ] Investigate `test_central_aggregation_includes_all_tool_results` flakiness - test passes individually but fails in full suite with "Found 0 tool results: []" error
  - [ ] Check for race conditions or timing issues in test setup/teardown
  - [ ] Verify test isolation and ensure files are properly flushed before assertions
  - [ ] Investigate pytest crash (0xC0000135 - STATUS_DLL_NOT_FOUND) - Windows system-level error indicating missing DLL
  - [ ] Check Python installation integrity and PATH environment variable
  - [ ] Verify pytest and dependency installations are complete
  - [ ] Consider adding retry logic or fixing root cause for flaky test
  - [ ] Document findings and solutions

**AI Chatbot Actionability Sprint** - Plan and implement actionable AI responses
- *What it means*: Improve AI chat quality and enable robust task/message/profile CRUD, with awareness of recent automated messages and targeted, non-conflicting suggestions.
- *Why it helps*: Addresses the user's biggest friction and increases real utility.
- *Estimated effort*: Large

**Fix AI response quality issues identified in test results**
- *What it means*: Address 10 issues identified in AI functionality test results: prompt-response mismatches (greetings not acknowledged, questions redirected), fabricated check-in data, incorrect facts, repetitive responses, code fragments in command responses, and system prompt leaks
- *Why it helps*: Improves AI response quality and ensures responses actually address user prompts appropriately
- *Estimated effort*: Medium
- *Current Status*: [OK] **IN PROGRESS** - Significant improvements made:
  - [OK] T-1.1, T-12.2: Greeting handling instructions strengthened with BAD/GOOD examples (prompt updated, monitoring)
  - [OK] T-1.2, T-12.4, T-15.2: Information request handling strengthened with explicit BAD/GOOD examples for "Tell me about your capabilities", "Tell me a fact", and "Tell me about yourself" (prompt updated, monitoring)
  - [OK] T-2.1, T-2.3, T-8.1, T-14.1: Vague reference instructions strengthened (improved, still some remaining)
  - [OK] T-4.1, T-9.2, T-13.3: Fabricated data prevention added
  - [OK] T-13.3: Meta-text leak cleaning enhanced
  - [OK] T-12.1: Information request handling added (should provide helpful info, not redirect)
  - [OK] T-15.2: "Tell me about yourself" handling strengthened with explicit examples
  - [OK] T-11.1: Code fragments in command responses - FIXED (added cleaning for cached responses and enhanced fragment detection)
  - [OK] T-12.4: Incorrect fact with self-contradiction - PREVENTION ADDED (logical consistency instructions)
  - [WARNING] T-15.1: System prompt instructions leaked (cleaning added, monitor)
- *Specific Issues*:
  - [OK] T-1.1, T-12.2: Prompt-response mismatches (greetings) - PROMPT UPDATED with BAD/GOOD examples (monitoring)
  - [OK] T-1.2, T-12.4, T-15.2: Prompt-response mismatches (information requests) - PROMPT UPDATED with explicit BAD/GOOD examples (monitoring)
  - [WARNING] T-8.1, T-9.3: Prompt-response mismatches (questions redirected) - IMPROVED (still monitoring)
  - [OK] T-11.1: Code fragments in command responses - FIXED
  - [OK] T-12.1: Generic motivational content instead of helpful information - IMPROVED
  - [OK] T-12.4: Incorrect fact with self-contradiction - PREVENTION ADDED
  - [OK] T-14.1, T-16.2: Fabricated check-in details/statistics - PREVENTION ADDED
  - [OK] T-13.3: System prompt instructions leaked - CLEANING ENHANCED


## Medium Priority

**Update Inter-Documentation References to Include Section Numbers**
- *What it means*: Update cross-references between documentation files to include section numbers and titles (e.g., "See section 3.2. Logging Architecture in LOGGING_GUIDE.md" instead of just "See LOGGING_GUIDE.md")
- *Why it helps*: Makes references more precise and easier to navigate, especially with numbered headings now standardized; improves documentation usability
- *Estimated effort*: Medium
- *Subtasks*:
  - [ ] Audit all documentation files for cross-references
  - [ ] Update references to include section numbers and titles where applicable
  - [ ] Create script or tool to help identify and update references automatically
  - [ ] Update documentation standards to require section numbers in references

**Create Example Marking Standards Checker**
- *What it means*: Create a validation checker to ensure examples in documentation follow the example marking standards (section 2.6 in `DOCUMENTATION_GUIDE.md`). The checker should validate that examples containing file paths are properly marked with `[OK]`, `[AVOID]`, `[GOOD]`, `[BAD]`, `[EXAMPLE]` markers or are under "Examples:" headings.
- *Why it helps*: Ensures examples are consistently marked, making the path drift checker more accurate and reducing false positives. Helps maintain documentation quality by catching unmarked examples that should be marked.
- *Estimated effort*: Medium
- *Subtasks*:
  - [ ] Add example marking validation to `development_tools/docs/analyze_documentation_sync.py` or create new validation module (already using full path)
  - [ ] Check for file path references in examples that lack proper markers
  - [ ] Validate that example sections use standard markers (`[OK]`, `[AVOID]`, `[GOOD]`, `[BAD]`, `[EXAMPLE]`)
  - [ ] Validate that example headings follow standard format ("Examples:", "Example Usage:", "Example Code:")
  - [ ] Report unmarked examples that contain file paths
  - [ ] Consider integrating into `doc-sync` workflow as a validation step
  - [ ] Update documentation to reflect the new validation capability


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

**Note**: Development tools related tasks have been moved to [AI_DEV_TOOLS_IMPROVEMENT_PLAN_V3.md](development_tools/AI_DEV_TOOLS_IMPROVEMENT_PLAN_V3.md) for centralized planning and tracking. See that document for all development tools improvements, enhancements, and maintenance tasks.



### User Experience Improvements

**Investigate Check-in Settings UI Issues**
- *What it means*: Fix two outstanding issues in the check-in management dialog: (1) Maximum spinbox cannot be reduced below minimum value - it should dynamically adjust minimum to match when maximum is reduced, similar to how minimum adjustment works in reverse; (2) Questions section blanks out visually when adding or deleting custom questions, even though the data is preserved correctly.
- *Why it helps*: Improves user experience by making the UI more intuitive and preventing visual glitches that can be confusing
- *Estimated effort*: Medium
- *Subtasks*:
  - [ ] Investigate why maximum spinbox value cannot be reduced below minimum - current attempts to block signals and adjust constraints haven't resolved the issue
  - [ ] Test different approaches: QSpinBox valueChanged signal handling, validation timing, constraint management
  - [ ] Investigate why questions section blanks during add/delete operations - attempts to hide/show scroll area and container widget haven't resolved the issue
  - [ ] Test alternative approaches: QTimer deferred updates, widget update strategies, layout management during rebuilds
  - [ ] Review how other widgets (e.g., tag_widget, dynamic_list_container) handle similar dynamic add/delete operations without blanking
  - [ ] Consider using QStackedWidget or other container strategies to prevent visual blanking
  - [ ] Document findings and implement working solution

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

**Differentiate Between New and Returning Users**
- *What it means*: Implement logic to distinguish between users who are authorizing the app for the first time versus users who are returning after deauthorizing
- *Why it helps*: Could enable personalized welcome messages or different onboarding flows for new vs. returning users
- *Estimated effort*: Small/Medium
- *Note*: Not important right now - current welcome system works fine for all users

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
- *Current Status*: 20 modules completed (486 new tests added total, all passing) - see changelogs for details
  - **Latest additions** (2025-01-14): `user/user_preferences.py` (26 tests), `core/ui_management.py` (27 tests), `ai/prompt_manager.py` (49 tests)
- *Next Targets*:
  - [ ] **Add comprehensive notebook feature tests** - Test data handlers, data manager (CRUD, search, lists, views), command handlers, tag system, and integration workflows (see `.cursor/plans/notebook_feature_implementation_ce88ed1a.plan.md` milestone 1.12a-1.12o)
  - [ ] Expand coverage for `ui/ui_app_qt.py` (33% coverage, 1095 lines) - Large module
  - [ ] Expand coverage for `core/scheduler.py` (65% -> 80%+)
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
  - [x] Add CI job step to run `scripts/static_checks/check_channel_loggers.py` (enforced via `run_tests.py` preflight)
  - [ ] Ensure job runs before test steps and fails the pipeline on violations
  - [ ] Document the check in [LOGGING_GUIDE.md](logs/LOGGING_GUIDE.md) (contributor notes)

**Investigate Intermittent Test Failures**
- *What it means*: Investigate and fix test failures that appear intermittently. Currently monitoring: `test_comprehensive_context_includes_recent_sent_messages_and_checkin_status` (AI context test). Note: `test_full_account_lifecycle_real_behavior` was fixed with cache clearing.
- *Why it helps*: Ensures test suite reliability and prevents false negatives that can mask real issues
- *Estimated effort*: Small/Medium
- *Subtasks*:
  - [ ] Investigate `test_comprehensive_context_includes_recent_sent_messages_and_checkin_status` failure (assertion that "Recent automated messages sent to them:" is in content)
  tests/ui/test_category_management_dialog.py::TestCategoryManagementDialogRealBehavior::test_save_category_settings_persists_to_disk - AssertionError: Saved categories should match selected categories (order ma...
  tests/behavior/test_webhook_handler_behavior.py::TestWebhookHandlerBehavior::test_handle_webhook_event_routes_application_deauthorized - AssertionError: User should be welcomed
  - [ ] Check for timing/race condition issues in test setup or teardown
  - [ ] Verify test isolation and data cleanup between test runs
  - [ ] Add retry logic or fix root cause if identified


**Improve AI Terminal Interaction Reliability**
- *What it means*: Investigate why AI assistants often misinterpret PowerShell output or make incorrect assumptions
- *Why it helps*: Reduces confusion and improves the reliability of AI-assisted development
- *Estimated effort*: Medium

**Complete core.user_management Retirement**
- *What it means*: Fully retire `core.user_management` module by moving remaining functionality to `core.user_data_handlers` and updating all imports. Currently `core.user_data_handlers` re-exports from `core.user_management` as a temporary measure.
- *Why it helps*: Simplifies codebase structure, removes legacy module, consolidates user data handling in one place
- *Estimated effort*: Medium
- *Subtasks*:
  - [ ] Identify all remaining functionality in `core.user_management` that needs to be moved
  - [ ] Move implementation to `core.user_data_handlers` 
  - [ ] Update all imports from `core.user_management` to `core.user_data_handlers`
  - [ ] Remove `core.user_management` module
  - [ ] Update comments in `core.user_data_handlers` that reference the retirement

**Review Communication Module Architecture**
- *What it means*: Review all modules in `communication/` directory to ensure they follow channel-agnostic architecture principles
- *Why it helps*: Ensures consistency, reduces duplication, and makes it easier to add new communication channels
- *Estimated effort*: Medium
- *Subtasks*:
  - [ ] Review `communication/core/channel_orchestrator.py` for email-specific code that should be channel-agnostic
  - [ ] Identify other modules with channel-specific code that should be refactored
  - [ ] Consider reorganizing/restructuring `communication/` directory for better organization
  - [ ] Document channel-agnostic architecture patterns and guidelines

**Add Performance Monitoring**
- *What it means*: Track how long operations take across subsystems
- *Why it helps*: Helps identify and fix performance problems proactively
- *Estimated effort*: Medium

**Create Development Guidelines**
- *What it means*: Establish coding standards and best practices
- *Why it helps*: Consistency and clarity, especially when collaborating with AI tools
- *Estimated effort*: Small

**Investigate markdown link issues**
- *What it means*: Some markdown links work in the editor while others don't, even with the same format. Need to investigate why relative paths work for some files but not others.
- *Why it helps*: Ensures all report links are clickable and functional in the editor
- *Estimated effort*: Small

**Investigate what shows up in test logs, what doesn't, and why**
- *What it means*: Review test logging behavior to understand what information appears in test logs, what information is missing, and why certain information may not be logged. This includes understanding log levels, filtering, and output redirection.
- *Why it helps*: Improves debugging capabilities and ensures important test information is captured
- *Estimated effort*: Medium

**Investigate test log rotation only saving 1 backup and no archives**
- *What it means*: Review test log rotation behavior to understand why only 1 backup is being saved and why archives are not being created. This includes checking log rotation configuration, backup retention settings, and archive creation logic.
- *Why it helps*: Ensures proper log retention for debugging historical issues and prevents log files from growing unbounded
- *Estimated effort*: Small/Medium

**Investigate test log pollution of production logs**
- *What it means*: Review test logging behavior to understand why test logs are appearing in production log files (e.g., `logs/app.log`, `logs/ai.log`, `logs/communication_manager.log`). Tests should write to test-specific log files in `tests/logs/` and not pollute production logs.
- *Why it helps*: Keeps production logs clean and focused on actual application behavior, making debugging easier and preventing confusion from test artifacts
- *Estimated effort*: Medium
- *Subtasks*:
  - [ ] Review test logging configuration and log file paths
  - [ ] Check if tests are using production loggers instead of test loggers
  - [ ] Verify that test fixtures properly isolate logging
  - [ ] Identify which tests are writing to production logs
  - [ ] Fix test logging to use test-specific log files only
  - [ ] Add safeguards to prevent tests from writing to production logs

**Investigate why running tests terminates the active service**
- *What it means*: Review test execution behavior to understand why running the test suite causes the active MHM service to terminate. Tests should not interfere with a running service instance.
- *Why it helps*: Allows running tests while the service is active, improving development workflow and preventing unexpected service interruptions
- *Estimated effort*: Medium
- *Subtasks*:
  - [ ] Review test setup/teardown that might affect service state
  - [ ] Check if tests are modifying shared resources (ports, files, locks) that the service uses
  - [ ] Identify which tests or test fixtures cause service termination
  - [ ] Review file locking, port binding, or other resource conflicts
  - [ ] Fix test isolation to prevent interference with running services
  - [ ] Add safeguards to detect and prevent test interference with active services





