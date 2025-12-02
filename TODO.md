# TODO.md - MHM Project Tasks

> **File**: `TODO.md`
> **Audience**: Human Developer (Beginner Programmer) and AI collaborators
> **Purpose**: Current development priorities and planned improvements  
> **Style**: Organized, actionable, beginner-friendly
> **See [README.md](README.md) for complete navigation and project overview**
> **See [DEVELOPMENT_WORKFLOW.md](DEVELOPMENT_WORKFLOW.md) for safe development practices**
> **See [TEST_COVERAGE_EXPANSION_PLAN.md](development_docs/TEST_COVERAGE_EXPANSION_PLAN.md) for testing strategy**

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


**Note**: Phase 1: Enhanced Task & Check-in Systems is tracked in PLANS.md. 
**Note**: Mood-Aware Support Calibration items (Safety Net Response Library, Task Breakdown Prompt Experiments, Context-Aware Reminder Content Mapping, Mood Re-evaluation Cadence Guidelines) are tracked in PLANS.md under "Mood-Aware Support Calibration" plan.

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

**Standardize Backup, Rotation, Archive, and Cleanup Approaches**
- *What it means*: Review data, log and file backup, rotation, archive, cleanup approaches throughout the codebase and standardize them (including tests and development_tools)
- *Why it helps*: Ensures consistent behavior, reduces code duplication, and makes maintenance easier
- *Estimated effort*: Medium
- *Areas to review*:
  - Log rotation and cleanup (core/logger.py, development_tools)
  - Backup creation and management (core/backup_manager.py, tests)
  - File archiving (core/auto_cleanup.py, development_tools)
  - Test data cleanup (tests/test_utilities.py, test fixtures)
  - Temporary file cleanup patterns

**Integrate Unused Imports Cleanup into Unused Imports Checker**
- *What it means*: Integrate `scripts/cleanup_unused_imports.py` functionality into `imports/analyze_unused_imports.py`. Add categorization and cleanup recommendations to the existing unused imports analysis.
- *Why it helps*: Provides actionable recommendations for unused imports (missing error handling, missing logging, safe to remove, etc.) alongside detection. Enables automated cleanup workflows. Note: Functionality should be preserved even when Phase 7 (Naming & Directory Strategy) reorganizes development tools.
- *Estimated effort*: Medium
- *Subtasks*:
  - [ ] Integrate categorization logic from `cleanup_unused_imports.py` into `analyze_unused_imports.py`
  - [ ] Add category-based reporting (missing error handling, missing logging, type hints, utilities, safe to remove)
  - [ ] Add cleanup recommendation generation to unused imports report
  - [ ] Consider adding `--categorize` flag to existing unused imports checker command
  - [ ] Update documentation to reflect enhanced reporting capabilities

**Integrate Test Marker Scripts into Coverage/Test Analysis Tools**
- *What it means*: Integrate test marker scripts (`scripts/find_tests_missing_category_markers.py`, `scripts/add_category_markers.py`, `scripts/analyze_test_markers.py`) into a new test analysis module. Add subcommands for test marker validation and fixing.
- *Why it helps*: Centralizes test analysis tools; enables validation of test categorization during coverage runs; provides automated marker addition. Note: Functionality should be preserved even when Phase 7 (Naming & Directory Strategy) reorganizes development tools.
- *Estimated effort*: Medium
- *Subtasks*:
  - [ ] Integrate test marker analysis functionality into coverage tools or new test analysis module
  - [ ] Add `test-markers` subcommand to `development_tools/run_development_tools.py` with options: `--check`, `--analyze`, `--fix`
  - [ ] Support batch operations for adding missing markers based on directory structure
  - [ ] Consider integrating marker validation into coverage regeneration workflow
  - [ ] Update documentation to reflect new test marker commands

**Standardize Function Counting and Complexity Metrics**
- *What it means*: Investigate the different function counting and complexity counting methods used by `analyze_functions` (AST-based, reports 153/138/128) vs `decision_support` (different method, reports 352/376/321). Decide on a single standardized approach and update all tools to use it consistently.
- *Why it helps*: Eliminates confusion from conflicting metrics; ensures status reports and priorities are based on consistent, accurate data; improves trust in audit results.
- *Estimated effort*: Medium
- *Subtasks*:
  - [ ] Compare function counting methods in `analyze_functions` vs `decision_support`
  - [ ] Compare complexity calculation methods (why are numbers so different?)
  - [ ] Determine which method is more accurate/appropriate
  - [ ] Standardize all tools to use the chosen method
  - [ ] Update status generation to use single source of truth
  - [ ] Document the standardized approach

**Standardize Error Handling Coverage Metrics**
- *What it means*: Investigate and resolve the disconnect between "Error Handling Coverage" percentage (99.9%) and "Functions Missing Protection" count (2 functions). There's a preexisting discrepancy between coverage percentage and functions needing protection numbers that needs to be standardized one way or the other.
- *Why it helps*: Ensures error handling metrics are consistent and accurate; prevents confusion about actual error handling status; improves reliability of audit reports.
- *Estimated effort*: Medium
- *Subtasks*:
  - [ ] Investigate how error handling coverage percentage is calculated
  - [ ] Investigate how "functions missing protection" count is determined
  - [ ] Identify why these numbers don't align (e.g., different function sets, different counting methods)
  - [ ] Decide on standardized approach (use same function set, same counting method)
  - [ ] Update error handling analysis tools to use standardized approach
  - [ ] Update status reports to show consistent metrics

**Investigate and Fix Test Coverage Regression**
- *What it means*: Test coverage dropped from 71.1% to 66.0% (5.1% drop, 1,375 fewer covered statements) after tool refactoring. Several modules show significant coverage drops (>50% for some). Need to identify root cause and restore coverage.
- *Why it helps*: Maintains test coverage quality; ensures refactoring doesn't break test execution; identifies and fixes test failures from refactoring.
- *Estimated effort*: Medium
- *Current Status*: Analysis document to be created when investigating coverage regression
- *Key Findings*:
  - 6 test failures and 1 import error found in latest run
  - 5 modules dropped into "Needs_Work" category (<50% coverage)
  - Test failures related to refactoring (documentation sync checker, legacy cleanup)
- *Subtasks*:
  - [ ] Fix test failures from refactoring (documentation sync checker tests, legacy cleanup import error)
  - [ ] Re-run coverage after test fixes to verify improvement
  - [ ] Investigate why specific modules lost coverage (task_completion_dialog, message_analytics, checkin_analytics, task_handler)
  - [ ] Check if tests exist and are running for affected modules
  - [ ] Compare test execution counts between versions
  - [ ] Review coverage configuration for changes
  - [ ] Document findings and resolution in TEST_COVERAGE_DIFF_ANALYSIS.md


**Create Project Cleanup Module**
- *What it means*: Create a new cleanup module in `development_tools/` that integrates `scripts/cleanup_project.py` functionality. Add subcommand to `development_tools/run_development_tools.py` for project cleanup operations.
- *Why it helps*: Provides centralized cleanup operations (cache files, temporary directories, test artifacts) through the development tools runner. Enables safe cleanup with dry-run support. Note: Functionality should be preserved even when Phase 7 (Naming & Directory Strategy) reorganizes development tools.
- *Estimated effort*: Medium
- *Subtasks*:
  - [ ] Create new cleanup module (e.g., `development_tools/cleanup.py` (to be created) or `development_tools/project_cleanup.py` (to be created)) - module to be created
  - [ ] Integrate cleanup operations from `scripts/cleanup_project.py` (cache, pytest cache, coverage files, test temp dirs, etc.)
  - [ ] Add `cleanup` subcommand to `development_tools/run_development_tools.py` with options: `--cache`, `--test-data`, `--coverage`, `--all`, `--dry-run`
  - [ ] Maintain safety features (dry-run mode, selective cleanup options)
  - [ ] Update documentation to reflect new cleanup command


**Reorganize AI Development Tools Subdirectory**
- *What it means*: Reorganize development_tools subdirectory, including a review of the files within to determine whether any of them are no longer active or useful
- *Why it helps*: Improves organization, reduces confusion, and makes the tools easier to navigate and maintain
- *Estimated effort*: Medium
- *Areas to review*:
  - Identify unused or obsolete tools
  - Group related tools into logical subdirectories
  - Update documentation to reflect new organization
  - Archive or remove tools that are no longer needed
  - Ensure all active tools are properly documented

**Improve AI_STATUS.md Formatting and Content**
- *What it means*: Fix formatting issues in AI_STATUS.md: add test coverage to snapshot section, move ASCII Cleanup and Dependency Docs from "Documentation Overlap" to "Documentation Signals", remove redundant "Complexity Hotspots" section (already in snapshot), and remove timestamp
- *Why it helps*: Makes AI_STATUS.md more accurate, better organized, and less redundant; improves clarity of status information
- *Estimated effort*: Small
- *Subtasks*:
  - [ ] Add test coverage metrics to snapshot section
  - [ ] Move ASCII Cleanup and Dependency Docs to "Documentation Signals" section
  - [ ] Remove "Complexity Hotspots" section (duplicate of snapshot data)
  - [ ] Remove timestamp from status report

**Investigate and Enhance Documentation Overlap Analysis**
- *What it means*: Investigate what the documentation overlap analysis looks for and enhance it to be more helpful. Currently it reports section overlaps and consolidation opportunities but may not be providing actionable insights.
- *Why it helps*: Makes documentation overlap analysis more useful for identifying actual issues and opportunities for improvement
- *Estimated effort*: Medium

**Investigate and Enhance AI Work Validation**
- *What it means*: Investigate what AI Work Validation looks for and enhance it to be more helpful. Currently it reports "GOOD - keep current standards" but may not be providing actionable insights.
- *Why it helps*: Makes AI Work Validation more useful for identifying actual issues and maintaining code quality standards
- *Estimated effort*: Medium

**Investigate and Enhance System Health Analysis**
- *What it means*: Investigate what System Health looks for and consider enhancing it to be more helpful. Currently it reports "OK" but may not be providing actionable insights.
- *Why it helps*: Makes System Health analysis more useful for identifying actual issues and maintaining system reliability
- *Estimated effort*: Medium

**Improve Recent Changes Detection Logic**
- *What it means*: Investigate the logic for determining the recent changes list in AI_STATUS.md. The current implementation doesn't seem very good at identifying meaningful changes.
- *Why it helps*: Makes recent changes list more accurate and useful for understanding what's actually changed in the codebase
- *Estimated effort*: Medium

**Review and Consolidate Audit Command Types**
- *What it means*: Investigate the different types of audits (status, fast-audit, audit, audit --full). Currently there are too many types and they're not super clearly defined. Consider consolidating or better documenting the differences.
- *Why it helps*: Reduces confusion about which audit command to use; makes the audit system easier to understand and use
- *Estimated effort*: Medium

**Fix Failing Test: test_email_user_creation**
- *What it means*: Investigate failing test `test_email_user_creation` in `test_utilities_demo.py`. The test fails at line 169 with "Email user should be created successfully", indicating the factory method returned False or None. This likely involves user index lookup or configuration patching.
- *Why it helps*: Fixes a broken test and ensures user creation functionality works correctly
- *Estimated effort*: Small/Medium

**Standardize Logging Across Development Tools Suite**
- *What it means*: Investigate and standardize logging across the development tools suite, including adjusting what is considered warning, info, and debug levels. Reduce duplicate and messy log entries.
- *Why it helps*: Makes development tools logs cleaner, easier to read, and more useful for debugging; reduces log noise
- *Estimated effort*: Medium
- *Subtasks*:
  - [ ] Standardize log levels (what should be INFO vs DEBUG vs WARNING)
  - [ ] Remove duplicate log entries (e.g., "Generating directory trees..." appearing multiple times)
  - [ ] Demote verbose enhancement messages to DEBUG level
  - [ ] Demote "needs_enhancement" warnings to DEBUG level
  - [ ] Consolidate related log messages to reduce redundancy

**Add Test Failure Details to Coverage Logging**
- *What it means*: Add to dev tools logging what tests failed and whether the test coverage quit early. Currently logs show "Coverage data collected successfully, but some tests failed" without details.
- *Why it helps*: Makes it easier to understand what went wrong during coverage collection and why the process may have quit early
- *Estimated effort*: Small

**Adjust Test Failure Threshold for Early Quit**
- *What it means*: Adjust threshold for failures that result in tool quitting early. Currently it's 5, which seems too low and may cause premature termination.
- *Why it helps*: Prevents tools from quitting too early when there are only a few test failures, allowing more complete data collection
- *Estimated effort*: Small

**Investigate Changelog Trim Tooling Unavailability**
- *What it means*: Investigate why changelog check reports "Tooling unavailable (skipping trim)". Handle with care to avoid accidentally losing changelog information.
- *Why it helps*: Ensures changelog maintenance tooling works correctly and prevents accidental data loss
- *Estimated effort*: Small

**Include Config Validation in Status Reports**
- *What it means*: Investigate why config validation isn't included in AI_STATUS, AI_PRIORITIES, or consolidated_report. Add it if it should be included.
- *Why it helps*: Makes config validation status visible in status reports, helping identify configuration issues early
- *Estimated effort*: Small

**Standardize How Tools Save Their Findings**
- *What it means*: Investigate and standardize how development tools save their findings. Different tools may use different formats, locations, or approaches.
- *Why it helps*: Makes tool outputs more consistent and easier to find; improves maintainability
- *Estimated effort*: Medium

**Include TODO Sync Status in Status Reports**
- *What it means*: Include TODO sync status (e.g., "Found 3 completed entries in TODO.md that need review") in AI_STATUS, AI_PRIORITIES, and consolidated_report. Currently it's logged but not included in status reports.
- *Why it helps*: Makes TODO sync status visible in status reports, helping identify when TODO.md needs attention
- *Estimated effort*: Small

**Investigate AI_STATUS and AI_PRIORITIES Mid-Audit Updates**
- *What it means*: Investigate why AI_STATUS and AI_PRIORITIES update midway through the full audit with different results than they have at the end. For example, complexity numbers change (Moderate: 352/153, High: 376/138, Critical: 321/128) and doc sync status changes (FAIL/GOOD).
- *Why it helps*: Prevents confusion from inconsistent status reports; ensures status files reflect final audit results, not intermediate states
- *Estimated effort*: Medium

**Improve Console Output During Audit Runs**
- *What it means*: Improve console output during audit runs. Currently it's an unhelpful mess with a massive dump of raw metrics data (dictionaries, lists, etc.) that's not human-readable. Make it more structured and informative.
- *Why it helps*: Makes audit progress visible and understandable; helps identify issues during long-running audits; improves developer experience
- *Estimated effort*: Medium

**Verify Critical Issues File Creation**
- *What it means*: Investigate whether "Critical issues saved to: development_tools/critical_issues.txt" is a true statement. Verify that the file is actually created and contains meaningful content.
- *Why it helps*: Ensures critical issues are actually being saved and accessible; prevents false claims in console output
- *Estimated effort*: Small

**Investigate Version Sync Functionality**
- *What it means*: Investigate version_sync - what does it do and what files does it cover? Understand its purpose, scope, and ensure it's working correctly.
- *Why it helps*: Ensures version synchronization is working as intended; helps maintain consistency across versioned files
- *Estimated effort*: Small/Medium

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

**Improve AI Terminal Interaction Reliability**
- *What it means*: Investigate why AI assistants often misinterpret PowerShell output or make incorrect assumptions
- *Why it helps*: Reduces confusion and improves the reliability of AI-assisted development
- *Estimated effort*: Medium

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



