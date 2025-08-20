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

## High Priority

## **Phase 1: Enhanced Task & Check-in Systems** ⚠️ **NEW PRIORITY**
- *What it means*: Implement priority-based task reminders, semi-random check-ins, and response analysis to align with project vision
- *Why it helps*: Provides immediate improvements to core functionality that directly supports user's executive functioning needs
- *Estimated effort*: Large (1-2 weeks)
- *Subtasks*:
  - [ ] **Enhanced Task Reminder System** (High Impact, Medium Effort)
    - [ ] Add priority-based reminder frequency (high priority = more likely to be selected for reminders)
    - [ ] Implement due date proximity weighting (closer to due = more likely to be selected for reminders)
    - [ ] Add recurring task support with flexible scheduling
    - [ ] Improve semi-randomness to consider task urgency
    - [ ] Test priority and due date weighting algorithms
    - [ ] Validate recurring task scheduling patterns
  - [ ] **Semi-Random Check-in Questions** (High Impact, Low-Medium Effort)
    - [ ] Implement random question selection from available pool
    - [ ] Add weighted selection based on recent questions asked
    - [ ] Ensure variety while maintaining relevance
    - [ ] Add question categories (mood, energy, tasks, general well-being)
    - [ ] Test question selection randomness and variety
    - [ ] Validate question category coverage
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

## **AI Tools Improvement - Generated Documentation Quality** ⚠️ **NEW PRIORITY**
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

## **Test Coverage Expansion - Critical Infrastructure** ✅ **MAJOR PROGRESS**

**Goal**: Expand test coverage from 54% to 80%+ for critical infrastructure components
**Current Status**: 883/884 tests passing (99.9% success rate) - 66% overall coverage
**Estimated effort**: Large
**Priority Order**:
1. ✅ **Backup Manager** (0% → 81%) - Essential for data safety **COMPLETED**
2. ✅ **UI Dialog Testing** (9-29% → 78%) - User-facing reliability **COMPLETED**
3. ✅ **Communication Manager** (24% → 61%) - Core infrastructure **COMPLETED**
4. ✅ **Core Scheduler** (31% → 63%) - Core functionality **COMPLETED**
5. ✅ **Interaction Handlers** (32% → 49%) - User interactions **COMPLETED**
6. ✅ **Task Management** (48% → 79%) - Core task functionality **COMPLETED**
7. ✅ **UI Widgets** (38-52% → 70%+) - Reusable UI components **COMPLETED**
**Subtasks**:
- [x] Create comprehensive test plan (see TEST_COVERAGE_EXPANSION_PLAN.md) **COMPLETED**
- [x] Start with backup manager testing (0% coverage is critical) **COMPLETED**
- [x] Expand UI dialog testing infrastructure **COMPLETED**
- [x] Add communication manager behavior tests **COMPLETED**
- [x] Add scheduler integration tests **COMPLETED**
- [x] Add interaction handler behavior tests **COMPLETED**
- [x] Add task management behavior tests **COMPLETED**
- [x] Add UI widgets behavior tests **COMPLETED**
- [ ] **NEW**: Address remaining test warnings and deprecation notices
  - [ ] Fix Discord deprecation warnings (audioop, timeout parameters)
  - [ ] Fix pytest return-not-none warnings in integration tests
  - [ ] Fix async mock warnings in communication manager tests
  - [ ] Fix duplicate file warnings in zipfile operations
- [ ] **NEW**: Fix log rotation permission issues in test environment
  - [ ] Investigate Windows file locking during log rotation
  - [ ] Implement proper file handle cleanup in tests
  - [ ] Add retry logic for log file operations
- [ ] **NEW**: Address test warnings and deprecation notices
  - [ ] Fix Discord deprecation warnings (audioop, timeout parameters)
  - [ ] Fix pytest return-not-none warnings in integration tests
  - [ ] Fix async mock warnings in communication manager tests
  - [ ] Fix duplicate file warnings in zipfile operations

## **Next Priority Test Coverage Expansion**

**Enhanced Command Parser** (40% → 70%) - Natural language processing
- *What it means*: Expand test coverage for the enhanced command parser that handles natural language input
- *Why it helps*: Ensures reliable natural language processing for user interactions
- *Estimated effort*: Medium
- *Subtasks*:
  - [ ] Test natural language pattern matching
  - [ ] Test entity extraction and parsing
  - [ ] Test command intent recognition
  - [ ] Test error handling for invalid inputs
  - [ ] Test edge cases and boundary conditions

**Email Bot** (37% → 60%) - Email communication channel
- *What it means*: Expand test coverage for the email bot communication channel
- *Why it helps*: Ensures reliable email-based communication functionality
- *Estimated effort*: Small
- *Subtasks*:
  - [ ] Test email sending functionality
  - [ ] Test email receiving and parsing
  - [ ] Test email authentication and security
  - [ ] Test error handling for email failures

**ComponentLogger Method Signature Issues** - Fix remaining logging calls with wrong argument format
- *What it means*: Some logging calls still use old format with multiple positional arguments instead of keyword arguments
- *Why it helps*: Prevents runtime errors and ensures consistent logging
- *Estimated effort*: Small
- *Status*: ⚠️ **IN PROGRESS** - Partially fixed, need to find remaining instances
- *Action*: Search for remaining `logger.info(message, arg1, arg2)` patterns and convert to f-strings

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

**Pydantic Schema Adoption Follow-ups**
- *What it means*: We added tolerant Pydantic models. Expand usage safely across other save/load paths.
- *Why it helps*: Stronger validation and normalized data.
- *Estimated effort*: Medium
- *Subtasks*:
  - [ ] Extend schema validation to schedules save paths not yet using helpers (confirm all call-sites)
  - [ ] Add unit tests for `validate_*_dict` helpers with edge-case payloads (extras, nulls, invalid times/days)
  - [ ] Add behavior tests for end-to-end save/load normalization
  - [ ] Add read-path normalization invocation to remaining reads that feed business logic (sweep `core/` and `bot/`)

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

**Legacy Code Removal** - Remove all marked legacy/compatibility code with clear marking and plans ✅ **COMPLETED**
- *What it means*: Remove legacy compatibility code per `LEGACY_CODE_REMOVAL_PLAN.md` (keep warnings in place until removal)
- *Why it helps*: Reduces complexity, eliminates legacy branches, improves maintainability
- *Estimated effort*: Medium
- *High-priority removals*:
  - Account Creator Dialog compatibility methods (by 2025-08-15)
  - User Profile Settings Widget legacy fallbacks (by 2025-08-15)
  - Discord Bot legacy methods (by 2025-08-15)
- *Status*: ✅ **COMPLETED** - Legacy validation code removed and replaced with Pydantic validation

**Legacy Documentation Cleanup** - Remove obsolete legacy documentation files ✅ **COMPLETED**
- *What it means*: Remove obsolete legacy documentation files that are no longer needed after legacy code cleanup
- *Why it helps*: Reduces project clutter, saves disk space, improves project organization
- *Estimated effort*: Small
- *Status*: ✅ **COMPLETED** - 6 files deleted (~46MB saved), 1 file archived
- *Results*:
  - Deleted: 5 obsolete files (FOCUSED_LEGACY_AUDIT_REPORT.md, LEGACY_REMOVAL_QUICK_REFERENCE.md, legacy_compatibility_report_clean.txt, legacy_compatibility_report.txt, LEGACY_CHANNELS_AUDIT_REPORT.md)
  - Archived: LEGACY_CODE_REMOVAL_PLAN.md → archive/
  - Space saved: ~46MB

**Throttler Bug Fix** - Fix Service Utilities Throttler first-call behavior
- *What it means*: Ensure `last_run` is set on first call so throttling works from initial invocation
- *Why it helps*: Prevents over-frequency operations on first execution
- *Estimated effort*: Small

**Schedule Editor Validation – Prevent Dialog Closure**
- *What it means*: Validation error popups must not close the edit schedule dialog; allow user to fix and retry
- *Why it helps*: Prevents data loss and improves UX
- *Estimated effort*: Small

**High Complexity Function Refactoring** - Address audit findings for maintainability
- *What it means*: 1462 out of 1907 functions have high complexity (>50 nodes), which may impact maintainability
- *Why it helps*: Improves code maintainability, reduces cognitive load, makes debugging easier
- *Estimated effort*: Large
- *Status*: 📊 **MONITORING** - Identified by audit, not blocking development
- *Action*: Prioritize refactoring during feature development, focus on most complex functions first
- *Testing Needed*: Ensure refactoring doesn't break functionality

**Script Logger Migration** - Complete logging migration for scripts and utilities ✅ **COMPLETED**
- *What it means*: Migrate 21 script/utility files from `get_logger(__name__)` to component loggers for consistency
- *Why it helps*: Completes the logging migration, prevents future confusion, maintains consistency across codebase
- *Estimated effort*: Small
- *Files affected*: Scripts in `scripts/` directory, debug tools, migration scripts
- *Status*: ✅ **COMPLETED** - All 21 script files migrated to component loggers

**Low Activity Log Investigation** - Investigate log files with low activity ✅ **COMPLETED**
- *What it means*: Check why `errors.log` (8 days old) and `user_activity.log` (15 hours old) have low activity
- *Why it helps*: Ensures no important logs are being missed and confirms expected behavior
- *Estimated effort*: Small
- *Action*: Determine if inactivity is expected or indicates an issue
- *Status*: ✅ **COMPLETED** - Investigation confirms low activity is expected behavior
- *Findings*: 
  - `errors.log`: 8-day-old entries are from test files, no real errors occurring (good system health)
  - `user_activity.log`: 15-hour-old entry is last user check-in, no recent user interactions (normal usage)
  - `ai.log`: Only initialization logs, no conversation logs because no AI interactions occurred (expected)
  - **Conclusion**: Low activity is completely expected for a personal mental health assistant

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
- *What it means*: Ensure architecture documentation reflects current system state
- *Why it helps*: Provides accurate technical reference for development
- *Estimated effort*: Small

**Review and Update QUICK_REFERENCE.md** - Check for outdated commands
- *What it means*: Ensure quick reference contains current commands and procedures
- *Why it helps*: Provides reliable quick access to common tasks
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

**Scripts Directory Cleanup** - Clean up the scripts/ directory
- *What it means*: Remove outdated/broken files, organize remaining utilities, move AI tools to ai_tools/
- *Why it helps*: Reduces confusion and keeps the codebase organized
- *Estimated effort*: Medium

**Gitignore Cleanup** - Review and clean up .gitignore file
- *What it means*: Remove outdated entries, add missing patterns, organize sections logically
- *Why it helps*: Ensures proper version control and prevents unnecessary files from being tracked
- *Estimated effort*: Small

**Improve AI Terminal Interaction Reliability** - Address issues with AI misunderstanding terminal output
- *What it means*: Investigate why AI assistants often misinterpret PowerShell output or make incorrect assumptions
- *Why it helps*: Reduces confusion and improves the reliability of AI-assisted development
- *Estimated effort*: Medium

**Fix Treeview Refresh** - Should refresh reflecting the changes, while maintaining current sorting
- *What it means*: Improve the message editing interface to automatically update the display when messages are changed
- *Why it helps*: Better user experience with immediate visual feedback
- *Estimated effort*: Small

**Fix "process already stopped" notification issue**
- *What it means*: Investigate why shutdown attempts result in "process already stopped" messages
- *Why it helps*: Cleaner service management and better user experience
- *Estimated effort*: Small

**Add Performance Monitoring** - Track how long operations take
- *What it means*: The app keeps track of which operations are slow so you can improve them
- *Why it helps*: Helps you identify and fix performance problems before they become annoying
- *Estimated effort*: Medium

**Create Development Guidelines** - Establish coding standards and best practices
- *What it means*: Write down rules for how code should be written to keep it consistent
- *Why it helps*: Makes the code easier to read and understand, especially when working with AI assistance
- *Estimated effort*: Small
