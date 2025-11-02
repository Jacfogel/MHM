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

**Improve generation of ai_development_docs\AI_FUNCTION_REGISTRY.md**
- It should provide more dynamic information, less preset text
- Accept slightly longer generation time if it yields concise, high-signal docs

**Restore MANUAL ENHANCEMENT details to development_docs\MODULE_DEPENDENCIES_DETAIL.md**
- Ensure manual enhancements are preserved through regeneration 

**Investigate Permission Test Environment Issue**
- *What it means*: Investigate why `test_save_json_data_permission_error` can write to `/root` on Windows - this suggests elevated permissions or test environment issues
- *Why it helps*: Ensures test environment is properly isolated and permission tests work as expected
- *Estimated effort*: Small

**Nightly No-Shim Validation Runs**
- *What it means*: Run the full suite with `ENABLE_TEST_DATA_SHIM=0` nightly to validate underlying stability.
- *Why it helps*: Ensures we're not masking issues behind the test-only shim and maintains long-term robustness.
- *Estimated effort*: Small


**Continue Error Handling Coverage Expansion**
- *What it means*: Continue expanding error handling coverage beyond current 92.0% to 93%+ by adding @handle_errors decorators to remaining 115 functions
- *Why it helps*: Improves system robustness and reliability by protecting more functions against errors
- *Estimated effort*: Medium
- *Current Status*: 92.0% coverage achieved (1,285 functions protected) - continue to 93%+
- *Next Steps*:
  - [ ] **Continue Expanding Beyond 92%**
    - [ ] Add error handling to remaining 115 functions for 93%+ coverage
    - [ ] Focus on UI modules and remaining utility functions
  - [ ] **Replace Basic Try-Except Blocks**
    - [ ] Replace remaining basic try-except blocks with @handle_errors decorator
    - [ ] Improve error handling quality from basic to excellent

**Fix UI Import Detection in Unused Imports Checker**
- *What it means*: The UI import detection function in unused_imports_checker.py is not working properly - Qt imports in UI files are not being categorized as 'ui_imports'
- *Why it helps*: Proper categorization prevents false positives and ensures Qt imports in UI files are correctly identified as needed
- *Estimated effort*: Small
- *Current Status*: Function is called but Qt imports not being detected properly
- *Next Steps*:
  - [ ] Debug why Qt imports are not being detected in UI files
  - [ ] Fix the path detection or import name matching logic
  - [ ] Test with UI files to ensure proper categorization

**Complete Remaining Unused Imports Analysis**
- *What it means*: Analyze the remaining 45 "obvious unused" imports to determine if they can be safely removed or need different categorization
- *Why it helps*: Completes the unused imports cleanup and improves code quality
- *Estimated effort*: Small/Medium
- *Current Status*: 23 imports successfully recategorized, 45 remaining
- *Next Steps*:
  - [ ] Review remaining 45 imports systematically
  - [ ] Determine if they are truly unused or need different categorization
  - [ ] Update categorization logic if needed
  - [ ] Remove truly unused imports



**Phase 1: Enhanced Task & Check-in Systems** ?? **COMPLETED**
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

**AI Tools Improvement - Generated Documentation Quality** ?? **NEW PRIORITY**
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
  - [ ] Add read-path normalization invocation to remaining reads that feed business logic (sweep `core/` and `communication/`)

**Discord Task Edit Follow-ups and Suggestion Relevance**
- *What it means*: Ensure edit-task prompts are actionable, suppress irrelevant suggestions, and add coverage for common follow-ups
- *Why it helps*: Reduces confusion and makes conversations efficient
- *Estimated effort*: Small/Medium
- *Subtasks*:
  - [ ] Behavior tests: edit task by name then change due date (natural language variations: "due date", "due")
  - [ ] Behavior tests: verify no generic suggestions accompany targeted "what would you like to update" prompts
  - [ ] Behavior tests: list tasks ? edit task flow ensures "which task" is asked when not specified

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

**Schedule Editor Validation � Prevent Dialog Closure**
- *What it means*: Validation error popups must not close the edit schedule dialog; allow user to fix and retry
- *Why it helps*: Prevents data loss and improves UX
- *Estimated effort*: Small


**Check-in Flow Behavior & Stability**
- *What it means*: Ensure active check-ins expire correctly and legacy shims are not used in live flows
- *Why it helps*: Prevents stale states and confusing interactions during conversations
- *Estimated effort*: Small/Medium
- *Subtasks*:
  - [ ] Monitor logs for legacy compatibility warnings related to check-ins (`start_checkin`, `FLOW_CHECKIN`, `get_recent_checkins`, `store_checkin_response`)
  - [ ] Verify Discord behavior: after a check-in prompt goes out, send a motivational or task reminder and confirm the flow expires
  - [ ] Consider inactivity-based expiration (30–60 minutes) in addition to outbound-triggered expiry (optional)
  - [ ] Add behavior test for flow expiration after unrelated outbound message
  - [ ] **Test fixes with real Discord check-in flow and verify flow state persistence** - Restart service and test that check-in flows persist through scheduled message checks
  - [ ] **Monitor logs for MESSAGE_SELECTION debug info** - Understand why sometimes no messages match (review matching_periods, current_days, and message filtering)

## High Priority

**AI Chatbot Actionability Sprint** - Plan and implement actionable AI responses
- *What it means*: Improve AI chat quality and enable robust task/message/profile CRUD, with awareness of recent automated messages and targeted, non-conflicting suggestions.
- *Why it helps*: Addresses the user's biggest friction and increases real utility.
- *Estimated effort*: Large

**Improve missing context fallback responses**
- *What it means*: Enhance `_get_contextual_fallback` in `ai/chatbot.py` to provide more explicit and supportive responses when user context is missing, asking users to provide information rather than giving generic responses
- *Why it helps*: Improves user experience when AI doesn't have context data, making interactions more helpful and engaging
- *Estimated effort*: Small

**Fix AI response quality issues identified in test results**
- *What it means*: Address 10 issues identified in AI functionality test results: prompt-response mismatches (greetings not acknowledged, questions redirected), fabricated check-in data, incorrect facts, repetitive responses, code fragments in command responses, and system prompt leaks
- *Why it helps*: Improves AI response quality and ensures responses actually address user prompts appropriately
- *Estimated effort*: Medium
- *Current Status*: Issues documented in `tests/ai/results/ai_functionality_test_results_latest.md` - AI Review section
- *Specific Issues*:
  - T-1.1, T-8.1, T-9.3, T-13.3: Prompt-response mismatches (greetings redirected, questions not answered)
  - T-11.1: Code fragments in command responses
  - T-12.1: Generic motivational content instead of helpful information
  - T-12.4: Incorrect fact with self-contradiction (claims X but provides data showing NOT X)
  - T-14.1, T-16.2: Fabricated check-in details/statistics when no check-in data exists
  - T-15.1: System prompt instructions leaked into response + repetitive phrasing

**Enhance AI response validator for prompt-response mismatches**
- *What it means*: Improve `tests/ai/ai_response_validator.py` to better detect greeting acknowledgment failures, fabricated data, and self-contradictions (claims X but provides data showing NOT X)
- *Why it helps*: Catches more quality issues automatically, reducing manual review burden and ensuring consistent response quality
- *Estimated effort*: Medium
- *Current Status*: Enhanced validator added some checks but still misses greeting acknowledgment and some fabricated data patterns
- *Specific Improvements Needed*:
  - Better detection of greeting acknowledgment failures (T-1.1, T-8.1 still passed)
  - Detection of fabricated check-in details when no check-in data exists (T-14.1, T-16.2)
  - Self-contradiction detection (T-12.4: claims X but provides data showing NOT X)

**Fix system prompt leak into AI responses**
- *What it means*: Investigate and fix why system prompt instructions ("User Context:", "IMPORTANT - Feature availability", etc.) are leaking into actual AI responses (T-15.1)
- *Why it helps*: Prevents meta-text from appearing in user-facing responses, improving response quality
- *Estimated effort*: Small
- *Current Status*: System prompt text appearing in response - may be prompt formatting issue

## Medium Priority

**Legacy Compatibility Marker Audit** - Evaluate remaining backward-compatibility shims called out by the legacy cleanup report
- *What it means*: Review the markers in `core/user_data_manager.py` and `user/user_context.py` and plan their retirement or documentation.
- *Why it helps*: Reduces long-term maintenance burden while keeping compatibility decisions intentional.
- *Estimated effort*: Medium
- Next steps:
  - [ ] Confirm no active clients rely on the legacy fields.
  - [ ] Replace markers with clear TODO notes or remove them entirely.
  - [ ] Add regression tests covering analytics handler flows and user data migrations before deleting markers.
  - [ ] Rerun `python ai_development_tools/ai_tools_runner.py legacy --clean --dry-run` until the report returns zero issues.
  - [ ] Update the legacy report and changelog once resolved.

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

**Legacy Removal “Search-and-Close” Framework** - Tooling and checklist
- *What it means*: Build a checklist and helper tooling to update all references before removing legacy flags/paths; avoid fixed time windows.
- *Why it helps*: Safe deprecations without relying on rare usage logs.
- *Estimated effort*: Medium

**Testing Policy: Targeted Runs by Area (skip scripts/)**
- *What it means*: Default to running relevant test sections; consistently exclude `scripts/` tests.
- *Why it helps*: Faster feedback while preserving isolation requirements.
- *Estimated effort*: Small

**Help/Docs: Prefer Slash Commands, keep Bang Commands**
- *What it means*: Update help/UX text to prefer `/` commands with auto-suggested slash equivalents, while keeping `!` commands supported.
- *Why it helps*: Better Discord-native discoverability without breaking habits.
- *Estimated effort*: Small

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
- *What it means*: Continue expanding test coverage for remaining low-coverage modules (scheduler.py, user_data_manager.py, logger.py)
- *Why it helps*: Increases reliability and change safety for core system components
- *Estimated effort*: Large
- *Subtasks*:
  - [ ] Expand coverage for `core/scheduler.py` (66% coverage, 276 missing lines)
  - [ ] Expand coverage for `core/user_data_manager.py` (66% coverage, 186 missing lines)  
  - [ ] Expand coverage for `core/logger.py` (67% coverage, 181 missing lines)
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



