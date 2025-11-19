# TODO.md - MHM Project Tasks

> **File**: `TODO.md`
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
- *Current Status*: [OK] **94.25% coverage achieved** (1,392 of 1,477 functions protected, 1,280 with @handle_errors decorator) - **93%+ target achieved on 2025-11-10**
- *Remaining Work* (Optional):
  - [ ] **Continue Expanding Beyond 94.25%** (if desired):
    - [ ] Add error handling to remaining 85 functions where appropriate
    - [ ] Note: Many remaining functions are constructors (`__init__`), Pydantic validators (cannot use decorator), logger methods (already in error handling system), or `__getattr__` methods
    - [ ] Focus on UI modules and utility functions that would benefit from error handling
  - [ ] **Replace Basic Try-Except Blocks**
    - [ ] Replace remaining 103 basic try-except blocks with @handle_errors decorator
    - [ ] Improve error handling quality from basic to excellent

**Investigate and Update Direct Uses of error_handler.handle_error**
- *What it means*: Investigate and probably update any direct use of `error_handler.handle_error(e, context, "operation")` throughout the codebase
- *Why it helps*: Ensures consistent error handling patterns and may identify opportunities to use centralized error handling decorators or helpers instead
- *Estimated effort*: Small/Medium
- *Areas to investigate*:
  - Review all direct calls to `error_handler.handle_error()` (found in `core/error_handling.py` and test files)
  - Determine if these should use `@handle_errors` decorator or other centralized error handling patterns
  - Update direct calls to use preferred error handling approach where appropriate

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

**Pydantic Schema Adoption Follow-ups**
- *What it means*: We added tolerant Pydantic models. Expand usage safely across other save/load paths.
- *Why it helps*: Stronger validation and normalized data.
- *Estimated effort*: Medium
- *Subtasks*:
  - [ ] Extend schema validation to schedules save paths not yet using helpers (confirm all call-sites)
  - [ ] Add unit tests for `validate_*_dict` helpers with edge-case payloads (extras, nulls, invalid times/days)
  - [ ] Add behavior tests for end-to-end save/load normalization
  - [ ] Add read-path normalization invocation to remaining reads that feed business logic (sweep `core/` and `communication/`)

**Channel-Agnostic Command Registry Follow-ups**
- *What it means*: Finalize and monitor the new centralized command system and Discord integrations
- *Why it helps*: Ensures consistent behavior across channels and prevents regressions
- *Estimated effort*: Small/Medium
- *Subtasks*:
  - [ ] Add behavior tests for dynamic Discord app commands (registration, sync, callback wiring)
  - [ ] Add behavior tests for classic dynamic commands (skip `help`, ensure mapping works)
  - [ ] Verify unknown `/` and `!` prefixes fall back to parser and contextual chat
  - [ ] Document command list in HOW_TO_RUN.md
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


**Investigate and Fix Discord Button UI Issue**
- *What it means*: Investigate why Discord buttons are not showing up in check-in prompts (Cancel Check-in, Skip Question, More) and task reminders (Complete Task, Remind Me Later, More) despite the 2025-11-15 improvement that replaced text instructions with interactive buttons
- *Why it helps*: Restores the improved UX with native Discord interactions that was intended in the recent improvement
- *Estimated effort*: Small/Medium
- *Related to*: 2025-11-15 Discord Button UI Improvements (marked as COMPLETED but buttons not appearing)


**Design Safety Net Response Library**
- *What it means*: Draft and validate a library of "safety net" phrases that feel grounding when things are overwhelming, including branching prompts (listen/problem-solve/other) that match the user's preferred tone.
- *Why it helps*: Ensures the assistant consistently signals it "gets it," even when the user is unsure what support they need, aligning reminders with the emotional safety net vision.
- *Estimated effort*: Medium
- *Getting started*: Collect existing comforting phrases, prototype a few tone variants, and run with recent conversation logs to verify fit.

**Task Breakdown Prompt Experiments**
- *What it means*: Prototype both checklist-style subtasks and conversational follow-ups for stuck tasks, then capture which approach keeps users engaged on mobile.
- *Why it helps*: Provides context-aware nudges that unblock stalled tasks, matching the user's request for format experimentation.
- *Estimated effort*: Small/Medium
- *Acceptance criteria*: Document example prompts, note when to surface each format, and gather feedback from at least one real or simulated session.

**Context-Aware Reminder Content Mapping**
- *What it means*: Map task reminder content to user context (energy, mood, task age) so the system can choose the most relevant substance instead of generic nudges.
- *Why it helps*: Addresses the user's need for "it depends" reminders that feel situationally aware rather than repetitive.
- *Estimated effort*: Medium
- *Next steps*: Audit available context signals, define decision rules, and outline example reminder variants for contrasting scenarios.

**Mood Re-evaluation Cadence Guidelines**
- *What it means*: Specify triggers and guardrails for when the assistant should gently re-check mood/energy (e.g., disengagement signals, user-provided updates) without over-prompting.
- *Why it helps*: Balances proactive support with respect for the user's space, clarifying "when it should ask again" from the user's feedback.
- *Estimated effort*: Medium
- *Definition of done*: Draft cadence rules, edge-case handling, and handoff to implementation/testing once validated.

## Medium Priority

**Integrate Documentation Utility Scripts into AI Tools Runner**
- *What it means*: Integrate `scripts/number_documentation_headings.py` and possibly other useful utility scripts (e.g., path validation, reference checking) into `ai_development_tools/ai_tools_runner.py` or `ai_development_tools/documentation_sync_checker.py` as subcommands
- *Why it helps*: Makes documentation maintenance tools more discoverable and easier to use through the centralized tool runner; enables batch operations and integration with audit workflows
- *Estimated effort*: Medium
- *Subtasks*:
  - [ ] Add `number-headings` or `fix-numbering` subcommand to `ai_tools_runner.py`
  - [ ] Support batch operations (e.g., `number-headings --all` to process all default docs)
  - [ ] Consider integrating into `doc-sync` workflow or as a separate validation/fix step
  - [ ] Evaluate other utility scripts in `scripts/` that could benefit from integration
  - [ ] Update documentation to reflect new command structure

**Update Inter-Documentation References to Include Section Numbers**
- *What it means*: Update cross-references between documentation files to include section numbers and titles (e.g., "See section 3.2. Logging Architecture in LOGGING_GUIDE.md" instead of just "See LOGGING_GUIDE.md")
- *Why it helps*: Makes references more precise and easier to navigate, especially with numbered headings now standardized; improves documentation usability
- *Estimated effort*: Medium
- *Subtasks*:
  - [ ] Audit all documentation files for cross-references
  - [ ] Update references to include section numbers and titles where applicable
  - [ ] Create script or tool to help identify and update references automatically
  - [ ] Update documentation standards to require section numbers in references

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
- *Current Status*: [WARNING] **ROLLED BACK** - Previous migration attempt was rolled back due to test issues:
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
  - [ ] Add CI job step to run `scripts/static_checks/check_channel_loggers.py`
  - [ ] Ensure job runs before test steps and fails the pipeline on violations
  - [ ] Document the check in `logs/LOGGING_GUIDE.md` (contributor notes)

**Improve AI Terminal Interaction Reliability**
- *What it means*: Investigate why AI assistants often misinterpret PowerShell output or make incorrect assumptions
- *Why it helps*: Reduces confusion and improves the reliability of AI-assisted development
- *Estimated effort*: Medium

**Add Discord Username to account.json**
- *What it means*: Store Discord username in account.json alongside discord_user_id for easier reference and display
- *Why it helps*: Makes it easier to identify users, display usernames in UI, and reference users by their Discord username
- *Estimated effort*: Small

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



