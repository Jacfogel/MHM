# TODO.md - MHM Project Tasks

> **Audience**: Human Developer (Beginner Programmer) and AI collaborators
> **Purpose**: Current development priorities and planned improvements  
> **Style**: Organized, actionable, beginner-friendly

> **See [README.md](README.md) for complete navigation and project overview**
> **See [DEVELOPMENT_WORKFLOW.md](DEVELOPMENT_WORKFLOW.md) for safe development practices**
> **See [TESTING_IMPROVEMENT_PLAN_DETAIL.md](TESTING_IMPROVEMENT_PLAN_DETAIL.md) for testing strategy**

## 📝 How to Add New TODOs

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
- Add status indicators (⚠️ **IN PROGRESS**) when relevant
- Don't include priority field since tasks are already grouped by priority
- **TODO.md is for TODOs only** - completed tasks should be documented in CHANGELOG files and removed from TODO.md

### Test Data Cleanup Standards (Optional but Recommended)
- Pre-run (session start):
  - Remove `tests/data/pytest-of-Julie` if present
  - Clear all children of `tests/data/tmp`
  - Remove stray `tests/data/config` directory
  - Remove root files `tests/data/.env` and `tests/data/requirements.txt`
  - Remove legacy `tests/data/resources` and `tests/data/nested` if present
- Post-run (session end):
  - Clear all children of `tests/data/tmp`
  - Clear all children of `tests/data/flags`
  - Remove `tests/data/config`, `tests/data/.env`, `tests/data/requirements.txt` if present
  - Remove legacy `tests/data/resources` and `tests/data/nested` if present
- Users directory policy:
  - All test users must reside under `tests/data/users/<id>`
  - Fail if any `tests/data/test-user*` appears at the root or under `tests/data/tmp`
  - Post-run: ensure `tests/data/users` has no lingering test users


## High Priority

  - All tests passing with improved reliability
# TODO.md - MHM Project Tasks

> **Audience**: Human Developer (Beginner Programmer) and AI collaborators
> **Purpose**: Current development priorities and planned improvements  
> **Style**: Organized, actionable, beginner-friendly

> **See [README.md](README.md) for complete navigation and project overview**
> **See [DEVELOPMENT_WORKFLOW.md](DEVELOPMENT_WORKFLOW.md) for safe development practices**
> **See [TESTING_IMPROVEMENT_PLAN_DETAIL.md](TESTING_IMPROVEMENT_PLAN_DETAIL.md) for testing strategy**

## 📝 How to Add New TODOs

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
- Add status indicators (⚠️ **IN PROGRESS**) when relevant
- Don't include priority field since tasks are already grouped by priority
- **TODO.md is for TODOs only** - completed tasks should be documented in CHANGELOG files and removed from TODO.md

### Test Data Cleanup Standards (Optional but Recommended)
- Pre-run (session start):
  - Remove `tests/data/pytest-of-Julie` if present
  - Clear all children of `tests/data/tmp`
  - Remove stray `tests/data/config` directory
  - Remove root files `tests/data/.env` and `tests/data/requirements.txt`
  - Remove legacy `tests/data/resources` and `tests/data/nested` if present
- Post-run (session end):
  - Clear all children of `tests/data/tmp`
  - Clear all children of `tests/data/flags`
  - Remove `tests/data/config`, `tests/data/.env`, `tests/data/requirements.txt` if present
  - Remove legacy `tests/data/resources` and `tests/data/nested` if present
- Users directory policy:
  - All test users must reside under `tests/data/users/<id>`
  - Fail if any `tests/data/test-user*` appears at the root or under `tests/data/tmp`
  - Post-run: ensure `tests/data/users` has no lingering test users


## High Priority

**AI Response Quality Improvements** - Fix message truncation and enhance conversational openings
- *What it means*: The AI responses are getting cut off mid-sentence and need better conversational engagement endings
- *Why it helps*: Provides complete, engaging responses that encourage continued conversation
- *Estimated effort*: Small
- *Issues identified*:
  - [ ] **Message Truncation**: Second response got cut off mid-sentence ("it can be tough to manage all of...")
  - [ ] **Conversational Openings**: Third response needs stronger engagement ("where would you like to start?" or "what feels the heaviest right now?" or "how about we take it one thing at a time?")
- *Next steps*:
  - [ ] Investigate why AI responses are being truncated (max_tokens, response length limits)
  - [ ] Enhance conversational engagement prompts to be more specific about ending patterns
  - [ ] Test response completeness and engagement quality

**Quantitative Check-in Analytics Expansion** - Include all opted‑in quantitative questions
- *What it means*: Users can enable multiple preset check‑in questions; analytics should aggregate all quantitative ones (mood, stress, energy, sleep quality, anxiety, etc.) based on what the user has opted into.
- *Why it helps*: Richer insights that reflect the user’s selected tracking fields
- *Estimated effort*: Medium
- Subtasks:
  - [ ] Inventory quantitative check‑in fields in `conversation_flow_manager.py`
  - [ ] Design aggregation outputs (per-field averages, distributions, trends)
  - [ ] Implement analytics pull that respects per‑user enabled questions
  - [ ] Add behavior tests for each enabled field with sample data
  - [ ] Update `/analytics` and subcommands to surface these summaries
  - [ ] Integrate per-field summaries into "show analytics" response
  - [ ] Add behavior tests validating per-field section in analytics overview

**High Complexity Function Refactoring - Phase 2** ⚠️ **NEW PRIORITY**
- *What it means*: Continue refactoring high complexity functions identified in audit (1839 functions >50 nodes)
- *Why it helps*: Reduces maintenance risk, improves code readability, and makes future development safer
- *Estimated effort*: Large
- *Next Priority Targets*:
  - `ui/widgets/user_profile_settings_widget.py::get_personalization_data` (complexity: 727)
  - `ui/ui_app_qt.py::validate_configuration` (complexity: 692)
  - `core/user_data_manager.py::get_user_data_summary` (complexity: 800) - ✅ previously completed
- *Subtasks*:
  - [ ] **Analyze Next Priority Functions**
    - [ ] Export top-50 most complex functions from audit details
    - [ ] Categorize functions by module and complexity level
    - [ ] Identify patterns in high-complexity functions (long methods, deep nesting, etc.)
  - [ ] **Implement Refactoring Strategy - Phase 2**
    - [ ] Extract helper functions to reduce complexity
    - [ ] Break down large methods into smaller, focused functions
    - [ ] Reduce conditional nesting and improve readability
    - [ ] Add comprehensive tests for refactored functions
  - [ ] **Monitor Progress**
    - [ ] Track complexity reduction metrics
    - [ ] Ensure refactoring doesn't break existing functionality
    - [ ] Validate improvements through testing and audit results

**Nightly No-Shim Validation Runs**
- *What it means*: Run the full suite with `ENABLE_TEST_DATA_SHIM=0` nightly to validate underlying stability.
- *Why it helps*: Ensures we're not masking issues behind the test-only shim and maintains long-term robustness.
- *Estimated effort*: Small

**Headless Service Process Management** ⚠️ **NEW PRIORITY**
- *What it means*: Figure out how to run the service in headless mode (`python core/service.py`) without creating duplicate processes or causing the service to kill itself
- *Why it helps*: Enables proper headless service operation for deployment and automation scenarios
- *Estimated effort*: Medium
- *Subtasks*:
  - [ ] **Investigate Process Detection Logic**
    - [ ] Analyze why service detection logic interferes with UI service management
    - [ ] Identify safe ways to detect existing service processes
    - [ ] Determine if separate detection methods are needed for UI vs headless modes
  - [ ] **Implement Safe Headless Mode**
    - [ ] Create headless-specific service detection that doesn't interfere with UI
    - [ ] Ensure headless mode can properly restart existing services
    - [ ] Test that UI service management remains unaffected
  - [ ] **Alternative Approaches**
    - [ ] Consider using different process management strategies for headless mode
    - [ ] Investigate if UI restart logic can be shared with headless mode
    - [ ] Explore service daemon or system service approaches

**Windows Fatal Exception Investigation** ⚠️ **NEW PRIORITY**
- *What it means*: Investigate and fix the Windows fatal exception (access violation) that occurs during full test suite execution
- *Why it helps*: Ensures system stability and prevents crashes during comprehensive testing
- *Estimated effort*: Medium
- *Subtasks*:
  - [ ] **Investigate Root Cause**
    - [ ] Analyze crash logs and error patterns
    - [ ] Identify if issue is related to Discord bot threads or UI widget cleanup
    - [ ] Determine if issue is Windows-specific or affects all platforms
    - [ ] Check for memory management or threading issues
  - [ ] **Implement Fix**
    - [ ] Apply appropriate fix based on root cause analysis
    - [ ] Test fix with full test suite execution
    - [ ] Verify no regressions in core functionality
    - [ ] Monitor for recurrence of the issue
  - [ ] **Prevention Measures**
    - [ ] Add crash detection and recovery mechanisms
    - [ ] Implement proper resource cleanup in test environment
    - [ ] Add monitoring for similar issues in production
    - [ ] Document prevention strategies

**User Context & Preferences Integration Investigation** - Investigate and improve integration
- *What it means*: Investigate how `user/user_context.py` and `user/user_preferences.py` are integrated and used by other modules, identify gaps and improvements
- *Why it helps*: Ensures user state and preferences are properly utilized across the system for better personalization
- *Estimated effort*: Medium
- *Status*: From PLANS.md - needs investigation and action

**Phase 1: Enhanced Task & Check-in Systems** 🔄 **IN PROGRESS**
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

**AI Tools Improvement - Generated Documentation Quality** ⚠️ **NEW PRIORITY**
- *What it means*: Improve the AI tools that generate `AI_FUNCTION_REGISTRY.md` and `AI_MODULE_DEPENDENCIES.md` to provide more valuable, concise information
- *Why it helps*: Generated documentation should be truly AI-optimized with essential patterns and decision trees, not verbose listings
- *Estimated effort*: Medium
- *Subtasks*:
  - [ ] Analyze current AI tools output quality and identify improvement areas
  - [ ] Redesign function registry generation to focus on patterns over listings
  - [ ] Redesign module dependencies generation to highlight key relationships
  - [ ] Add pattern recognition to identify common function/module categories
  - [ ] Implement concise summary generation with cross-references to detailed docs
  - [ ] Test generated documentation usability for AI collaborators

**Fix Profile Display and Document Discord Commands** ⚠️ **NEW PRIORITY**
- *What it means*: Fix the profile display formatting if any raw JSON paths remain and document all available Discord commands for user discovery
- *Why it helps*: Users can properly view their profile information and discover all available commands
- *Estimated effort*: Small
- *Subtasks*:
  - [ ] **Fix Profile Display Formatting**
    - [ ] Investigate any path that outputs raw JSON for profile
    - [ ] Fix formatting to show user-friendly profile information
    - [ ] Test profile display in Discord to ensure proper formatting
    - [ ] Ensure all profile information is displayed (not truncated)
  - [ ] **Document All Discord Commands**
    - [ ] Audit all available Discord commands (slash commands, ! commands, natural language)
    - [ ] Keep comprehensive list in `DISCORD.md` with examples (developer/admin only)
    - [ ] Ensure help system surfaces core commands and examples
    - [ ] Test all commands to ensure they work properly

**Refactor High Complexity Core Functions** ⚠️ **NEW PRIORITY**
- *What it means*: Continue refactoring high complexity functions identified in audit, starting with `save_user_data` and other core functions
- *Why it helps*: Reduces maintenance risk, improves code readability, and makes future development safer
- *Estimated effort*: Large
- *Subtasks*:
  - [ ] **Refactor save_user_data Function**
    - [ ] Analyze current complexity and identify refactoring opportunities
    - [ ] Extract helper functions to reduce complexity
    - [ ] Improve error handling and validation
    - [ ] Test refactored function thoroughly
  - [ ] **Continue with Other High Complexity Functions**
    - [ ] Identify next priority functions from audit results
    - [ ] Apply same refactoring approach (extract helpers, reduce nesting)
    - [ ] Maintain functionality while reducing complexity
    - [ ] Update tests and documentation

**Code Complexity Reduction - High Priority Refactoring** 🔄 **IN PROGRESS**
- *What it means*: Address 1476 high complexity functions (>50 nodes) identified in latest audit to improve maintainability and reduce technical debt
- *Why it helps*: Reduces maintenance risk, improves code readability, and makes future development safer and more efficient
- *Estimated effort*: Large
- *Completed Work*:
  - ✅ `get_user_data_summary` refactoring — Reduced 800-node complexity to 15 focused helper functions
  - ✅ Helper function naming convention — Implemented `_main_function__helper_name` pattern
  - ✅ All tests passing — Verified stability after refactoring
- *Subtasks*:
  - [x] **Analyze Complexity Distribution**
  - [x] **Prioritize Refactoring Targets**
  - [x] **Implement Refactoring Strategy - Phase 1**
  - [ ] **Implement Refactoring Strategy - Phase 2** (targets listed above)
  - [ ] **Monitor Progress** (metrics, regression checks, audits)

## **Next Priority Test Coverage Expansion**

**Core User Data Manager** (39% → 70%) - Core data management
- *Estimated effort*: Medium
- *Subtasks*:
  - [ ] Test user data loading and saving operations
  - [ ] Test data validation and normalization
  - [ ] Test error handling for data operations
  - [ ] Test data migration and compatibility
  - [ ] Test concurrent access and data integrity

**Core Service** (51% → 70%) - Core service functionality
- *Estimated effort*: Medium
- *Subtasks*:
  - [ ] Test service startup and shutdown
  - [ ] Test service state management
  - [ ] Test error handling and recovery
  - [ ] Test service communication with other components
  - [ ] Test service monitoring and health checks

**Core Scheduler** (57% → 70%) - Core scheduling functionality
- *Estimated effort*: Medium
- *Subtasks*:
  - [ ] Test scheduling logic and timing
  - [ ] Test task execution and management
  - [ ] Test error handling for scheduled operations
  - [ ] Test scheduler state management
  - [ ] Test scheduler performance and scalability

**Enhanced Command Parser** (40% → 70%) - Natural language processing
- *Estimated effort*: Medium
- *Subtasks*:
  - [ ] Test natural language pattern matching
  - [ ] Test entity extraction and parsing
  - [ ] Test command intent recognition
  - [ ] Test error handling for invalid inputs
  - [ ] Test edge cases and boundary conditions

**Email Bot** (37% → 60%) - Email communication channel
- *Estimated effort*: Small
- *Subtasks*:
  - [ ] Test email sending functionality
  - [ ] Test email receiving and parsing
  - [ ] Test email authentication and security
  - [ ] Test error handling for email failures


**Discord Send Retry Monitoring**
- *What it means*: Verify queued retry behavior on disconnects and that check-in starts log only after successful delivery.
- *Why it helps*: Prevents lost messages and duplicate check-in starts.
- *Estimated effort*: Small
- *Subtasks*:
  - [ ] Simulate Discord disconnect during a scheduled check-in; confirm message queues and retries post-reconnect
  - [ ] Confirm single "User check-in started" entry after successful send

**Legacy Preferences Flag Monitoring and Removal Plan**
- *What it means*: We added LEGACY COMPATIBILITY handling that warns when nested `enabled` flags are present under `preferences.task_settings`/`checkin_settings`, and removes blocks on full updates when related features are disabled. We need to monitor usage and plan removal.
- *Why it helps*: Keeps data truthful (feature states live in `account.features`) and simplifies preferences schema.
- *Estimated effort*: Small/Medium
- *Subtasks*:
  - [ ] Monitor logs for `LEGACY COMPATIBILITY: Found nested 'enabled' flags` warnings over 2 weeks
  - [ ] If warnings stop, remove the legacy detection/removal code and update tests accordingly
  - [ ] Add a behavior test that asserts preferences blocks are removed only on full updates when features are disabled

**Legacy Check-in Methods Testing and Monitoring** ⚠️ **NEW PRIORITY**
- *What it means*: Test and monitor the newly added legacy check-in methods (`_get_question_text_legacy()` and `_validate_response_legacy()`)
- *Why it helps*: Ensures legacy methods function as intended and provides data for future removal decisions.
- *Estimated effort*: Small
- *Subtasks*:
  - [ ] **Test Legacy Methods Functionality**
    - [ ] Create unit tests for `_get_question_text_legacy()` method
    - [ ] Create unit tests for `_validate_response_legacy()` method
    - [ ] Verify legacy methods produce same results as original hardcoded system
    - [ ] Test legacy methods with edge cases and error conditions
  - [ ] **Monitor Legacy Method Usage**
    - [ ] Monitor logs for `LEGACY COMPATIBILITY: _get_question_text_legacy() called` warnings
    - [ ] Monitor logs for `LEGACY COMPATIBILITY: _validate_response_legacy() called` warnings
    - [ ] Track frequency of legacy method access over 2 weeks
    - [ ] Document any unexpected usage patterns
  - [ ] **Prepare for Removal**
    - [ ] If no usage detected after 2 weeks, plan removal for 2025-09-09
    - [ ] Update tests to remove legacy method dependencies
    - [ ] Remove legacy methods and update documentation

**Pydantic Schema Adoption Follow-ups**
- *What it means*: We added tolerant Pydantic models. Expand usage safely across other save/load paths.
- *Why it helps*: Stronger validation and normalized data.
- *Estimated effort*: Medium
- *Subtasks*:
  - [ ] Extend schema validation to schedules save paths not yet using helpers (confirm all call-sites)
  - [ ] Add unit tests for `validate_*_dict` helpers with edge-case payloads (extras, nulls, invalid times/days)
  - [ ] Add behavior tests for end-to-end save/load normalization
  - [ ] Add read-path normalization invocation to remaining reads that feed business logic (sweep `core/` and `communication/`)

**Discord Task Edit Follow-ups and Suggestion Relevance**
- *What it means*: Ensure edit-task prompts are actionable, suppress irrelevant suggestions, and add coverage for common follow-ups
- *Why it helps*: Reduces confusion and makes conversations efficient
- *Estimated effort*: Small/Medium
- *Subtasks*:
  - [ ] Behavior tests: edit task by name then change due date (natural language variations: "due date", "due")
  - [ ] Behavior tests: verify no generic suggestions accompany targeted "what would you like to update" prompts
  - [ ] Behavior tests: list tasks → edit task flow ensures "which task" is asked when not specified

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

**Throttler Bug Fix**
- *What it means*: Fix Service Utilities Throttler first-call behavior
- *Why it helps*: Ensure `last_run` is set on first call so throttling works from initial invocation
- *Estimated effort*: Small

**Schedule Editor Validation – Prevent Dialog Closure**
- *What it means*: Validation error popups must not close the edit schedule dialog; allow user to fix and retry
- *Why it helps*: Prevents data loss and improves UX
- *Estimated effort*: Small

**High Complexity Function Refactoring** - Address audit findings for maintainability
- *What it means*: 1462 out of 1907 functions have high complexity (>50 nodes), which may impact maintainability
- *Why it helps*: Improves code maintainability, reduces cognitive load, makes debugging easier
- *Estimated effort*: Large
- *Status*: 📊 **MONITORING** — Identified by audit, not blocking development
- *Action*: Prioritize refactoring during feature development, focus on most complex functions first
- *Testing Needed*: Ensure refactoring doesn't break functionality

**Check-in Flow Behavior & Stability**
- *What it means*: Ensure active check-ins expire correctly and legacy shims are not used in live flows
- *Why it helps*: Prevents stale states and confusing interactions during conversations
- *Estimated effort*: Small/Medium
- *Subtasks*:
  - [ ] Monitor logs for legacy compatibility warnings related to check-ins (`start_checkin`, `FLOW_CHECKIN`, `get_recent_checkins`, `store_checkin_response`)
  - [ ] Verify Discord behavior: after a check-in prompt goes out, send a motivational or task reminder and confirm the flow expires
  - [ ] Consider inactivity-based expiration (30–60 minutes) in addition to outbound-triggered expiry (optional)
  - [ ] Add behavior test for flow expiration after unrelated outbound message

## Medium Priority

**Personalized User Suggestions Implementation** - Review and implement proper personalized suggestions
- *What it means*: Review the current `get_user_suggestions()` function and implement proper personalized suggestion functionality
- *Why it helps*: Provides users with meaningful, personalized suggestions based on their data and preferences
- *Estimated effort*: Medium
- *Requirements*:
  - Analyze user data patterns and preferences
  - Implement suggestion algorithms based on user context
  - Add suggestion categories (tasks, health, motivation, etc.)
  - Test suggestion relevance and personalization

**Discord Application ID Configuration Docs**
- *What it means*: Document optional `DISCORD_APPLICATION_ID` to prevent slash command sync warnings.
- *Why it helps*: Cleaner logs and fewer false alarms.
- *Estimated effort*: Small
- Subtasks:
  - [ ] Add a note in `QUICK_REFERENCE.md` and `README.md` about setting `DISCORD_APPLICATION_ID`

**Pathlib Migration Completion**
- *What it means*: Finish converting remaining path joins to `pathlib.Path` where appropriate.
- *Why it helps*: Cross-platform safety and readability.
- *Estimated effort*: Medium
- Subtasks:
  - [ ] Sweep `core/` for remaining `os.path.join` not covered by helpers
  - [ ] Confirm all UI-related file paths still work as expected under tests

**Legacy UserContext Bridge Removal (monitor then remove)**
- *What it means*: Remove legacy format conversion/extraction in `user/user_context.py` once confirmed no usage
- *Why it helps*: Simplifies data access and reduces double-handling
- *Estimated effort*: Small
- Subtasks:
  - [ ] Monitor logs for legacy warnings after recent change (now warns once per process)
  - [ ] Grep code for legacy-format consumers and migrate if any are found
  - [ ] Remove legacy bridge and update tests

**Review and Update ARCHITECTURE.md** - Check for outdated information
- *Estimated effort*: Small

**Review and Update QUICK_REFERENCE.md** - Check for outdated commands
- *Estimated effort*: Small
- Subtasks:
  - [ ] Reflect new slash/bang commands and central command list
  - [ ] Note that `/checkin` is a flow; others are single-turn for now

### User Experience Improvements

**Enhanced Error Messages**
- *What it means*: Provide clearer, actionable dialog and system error messages everywhere users interact
- *Why it helps*: Reduces confusion and guides users to resolve problems faster
- *Estimated effort*: Small

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

**Audit Complexity Tracking and Refactor Targets**
- *What it means*: Use audit decision support (1466 high-complexity functions) to pick top refactor targets.
- *Why it helps*: Reduce maintenance risk.
- *Estimated effort*: Medium
- Subtasks:
  - [ ] Export top-50 complex functions from audit details and triage into refactor tickets
  - [ ] Add acceptance criteria per function (reduced branches, extracted helpers, increased test coverage)

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

**Add More Comprehensive Tests**
- *What it means*: Expand behavior and integration coverage for under-tested modules
- *Why it helps*: Increases reliability and change safety
- *Estimated effort*: Large

**Improve Test Coverage**
- *What it means*: Systematically raise coverage by adding targeted unit tests
- *Why it helps*: Catches regressions earlier
- *Estimated effort*: Medium

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
  - [ ] Document the check in `LOGGING_GUIDE.md` (contributor notes)

**Scripts Directory Cleanup** - Clean up the `scripts/` directory
- *What it means*: Remove outdated/broken files, organize remaining utilities, move AI tools to `ai_tools/`
- *Why it helps*: Reduces confusion and keeps the codebase organized
- *Estimated effort*: Medium

**Gitignore Cleanup**
- *What it means*: Review and clean up `.gitignore`
- *Why it helps*: Ensures proper version control and prevents unnecessary files from being tracked
- *Estimated effort*: Small

**Improve AI Terminal Interaction Reliability**
- *What it means*: Investigate why AI assistants often misinterpret PowerShell output or make incorrect assumptions
- *Why it helps*: Reduces confusion and improves the reliability of AI-assisted development
- *Estimated effort*: Medium

**Fix Treeview Refresh**
- *What it means*: Auto-refresh the message editing interface to reflect changes while maintaining current sorting
- *Why it helps*: Better UX with immediate visual feedback
- *Estimated effort*: Small

**Fix "process already stopped" notification issue**
- *What it means*: Investigate why shutdown attempts result in "process already stopped" messages
- *Why it helps*: Cleaner service management and better user experience
- *Estimated effort*: Small

**Add Performance Monitoring**
- *What it means*: Track how long operations take across subsystems
- *Why it helps*: Helps identify and fix performance problems proactively
- *Estimated effort*: Medium

**Create Development Guidelines**
- *What it means*: Establish coding standards and best practices
- *Why it helps*: Consistency and clarity, especially when collaborating with AI tools
- *Estimated effort*: Small

## **Test Isolation Issues Resolution** ✅ **MAJOR PROGRESS**
- *What it means*: Identified and addressed multiple test isolation issues causing persistent test failures in the full suite
- *Why it helps*: Resolves test reliability issues and ensures consistent results across execution contexts
- *Estimated effort*: Medium
- *Completed Work*:
  - ✅ Fixed multiple `conftest.py` conflicts; removed duplicate root `conftest.py`
  - ✅ Enhanced test cleanup and UUID-based user dir cleanup
  - ✅ Prevented `scripts/` tests from being collected
  - ✅ Standardized test data paths under `tests/data`
  - ✅ Autouse fixture to purge user data caches and enforce `mock_config`
  - ✅ Restored `MHM_TESTING` and `CATEGORIES` after dialog tests
  - ✅ Added diagnostics in `get_user_data`
- *Remaining Issues*:
  - ⚠️ Full-suite verification over multiple seeds/runs; continue monitoring
