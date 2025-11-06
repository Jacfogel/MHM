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
- *What it means*: Monitor test suite warnings to ensure they remain at expected levels (4 external library deprecation warnings expected: 3 Discord + 1 audioop). The 7 pytest collection warnings have been resolved.
- *Why it helps*: Ensures test suite health and prevents warnings from masking real issues
- *Estimated effort*: Small
- *Current Status*: 
  - ✅ Resolved: Fixed 7 pytest collection warnings by adding `__test__ = False` to all AI test classes
  - ✅ Expected: 4 external library deprecation warnings remain (cannot be fixed - from Discord library and audioop)

**Continue Error Handling Coverage Expansion**
- *What it means*: Continue expanding error handling coverage beyond current 92.9% to 93%+ by adding @handle_errors decorators to remaining 104 functions
- *Why it helps*: Improves system robustness and reliability by protecting more functions against errors
- *Estimated effort*: Medium
- *Current Status*: 92.9% coverage achieved (1,352 functions protected) - continue to 93%+
- *Progress*: Added error handling to 28 functions in this session (AI chatbot, LM Studio manager, UI dialogs, core utilities, tasks, user data manager, config, logger)
- *Next Steps*:
  - [ ] **Continue Expanding Beyond 92.9%**
    - [ ] Add error handling to remaining 104 functions for 93%+ coverage (~2-3 more functions needed)
    - [ ] Focus on UI modules and remaining utility functions
  - [ ] **Replace Basic Try-Except Blocks**
    - [ ] Replace remaining basic try-except blocks with @handle_errors decorator
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

**Discord Send Retry Monitoring**
- *What it means*: Verify queued retry behavior on disconnects and that check-in starts log only after successful delivery.
- *Why it helps*: Prevents lost messages and duplicate check-in starts.
- *Estimated effort*: Small
- *Subtasks*:
  - [ ] Simulate Discord disconnect during a scheduled check-in; confirm message queues and retries post-reconnect
  - [ ] Confirm single "User check-in started" entry after successful send

**Legacy Preferences Flag Monitoring and Removal Plan**
- *What it means*: We added LEGACY COMPATIBILITY handling that warns when nested `enabled` flags are present under `preferences.task_settings`/`checkin_settings`. Settings blocks are preserved even when features are disabled to allow re-enablement with previous settings intact. We need to monitor usage and plan removal.
- *Why it helps*: Keeps data truthful (feature states live in `account.features`) while preserving user settings for future re-enablement.
- *Estimated effort*: Small/Medium
- *Subtasks*:
  - [ ] Monitor logs for `LEGACY COMPATIBILITY: Found nested 'enabled' flags` warnings over 2 weeks
  - [ ] If warnings stop, remove the legacy detection code and update tests accordingly
  - [x] Add behavior tests that assert preferences blocks are preserved even when features are disabled (completed)

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



## Medium Priority


**Investigate Log Files Backing Up and Clearing Prematurely**
- *What it means*: Log files appear to be backing up and clearing after only one line of content, resulting in lost log data. This suggests log rotation or backup logic is triggering too early or incorrectly
- *Why it helps*: Ensures log data is preserved for debugging and prevents loss of important diagnostic information
- *Estimated effort*: Medium
- *Subtasks*:
  - [ ] Review log rotation and backup logic in `core/logger.py` or logging configuration
  - [ ] Check log file size thresholds and rotation triggers
  - [ ] Verify log backup directory creation and file naming
  - [ ] Test log rotation with multiple log entries to reproduce the issue
  - [ ] Review any log clearing or truncation logic that might be running too early
  - [ ] Check if log files are being overwritten instead of appended
  - [ ] Fix rotation logic to preserve all log data before clearing/rotating

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


**Legacy Removal "Search-and-Close" Framework** - Tooling and checklist
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



