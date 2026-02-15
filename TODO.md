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
**Note**: Development tools related tasks have been moved to [AI_DEV_TOOLS_IMPROVEMENT_PLAN_V4.md](development_tools/AI_DEV_TOOLS_IMPROVEMENT_PLAN_V4.md) for centralized planning and tracking. See that document for all development tools improvements, enhancements, and maintenance tasks.
**Session Note (2026-02-15)**: No new standalone TODO items were added during this wrap-up; remaining development-tools follow-ups are tracked in [AI_DEV_TOOLS_IMPROVEMENT_PLAN_V4.md](development_tools/AI_DEV_TOOLS_IMPROVEMENT_PLAN_V4.md).

## High Priority

### Flow & Communication

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

**Check-in Flow Behavior & Stability**
- *What it means*: Validate end-to-end check-in flow behavior after recent fixes (idle expiry, outbound-triggered expiry, and flow persistence) and ensure legacy shims are not used in live flows.
- *Why it helps*: Prevents stale states and confusing interactions during conversations.
- *Estimated effort*: Small/Medium
- *Subtasks*:
  - [ ] Monitor logs for legacy compatibility warnings related to check-ins (`start_checkin`, `FLOW_CHECKIN`, `get_recent_checkins`, `store_checkin_response`)
  - [ ] Verify Discord behavior: after a check-in prompt goes out, send a motivational or task reminder and confirm the flow expires
  - [ ] **Test fixes with real Discord check-in flow and verify flow state persistence** - Restart service and test that check-in flows persist through scheduled message checks
  - [ ] **Monitor logs for MESSAGE_SELECTION debug info** - Understand why sometimes no messages match (review matching_periods, current_days, and message filtering)

**Channel-Agnostic Command Registry Follow-ups**
- *What it means*: Finalize and monitor the new centralized command system and Discord integrations.
- *Why it helps*: Ensures consistent behavior across channels and prevents regressions.
- *Estimated effort*: Small/Medium
- *Subtasks*:
  - [ ] Add behavior tests for dynamic Discord app commands (sync + callback wiring; registration already covered in `tests/behavior/test_discord_bot_behavior.py`)
  - [ ] Add behavior tests for classic dynamic commands (skip `help`, ensure mapping works)

### AI & Chatbot

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

### Quality & Operations

**Continue Ruff Remediation Outside Tests**
- *What it means*: Continue fixing Ruff issues in non-test modules (core runtime, communication handlers, AI modules, tooling) in small batches, prioritizing rule classes with low behavior risk first.
- *Why it helps*: Reduces lint debt and keeps production code consistency high without destabilizing the test suite.
- *Estimated effort*: Medium
- *Subtasks*:
  - [ ] Run Ruff on non-test paths and group findings by safe autofix vs manual refactor
  - [ ] Apply fixes in small batches with focused behavior validation between batches
  - [ ] Track any behavior-impacting lint fixes separately from style-only cleanups
  - [ ] Re-baseline remaining Ruff counts after each batch

**Confirm wake timer fix in production**
- [ ] After a 01:00 run, confirm errors.log no longer fills with wake timer (Register-ScheduledTask) errors.

**Investigate sent_messages.json size and archiving**
- *What it means*: Review `data/users/{user_id}/messages/sent_messages.json` growth (e.g. ~512KB observed). Confirm whether archiving or trimming of sent message history is needed and implement or document policy.
- *Why it helps*: Prevents unbounded growth, keeps file_ops audit trail manageable, and may improve I/O and backup size.
- *Estimated effort*: Small/Medium
- *Subtasks*:
  - [ ] Check existing archiving/trimming in message_management or message.log for sent_messages
  - [ ] Define retention or max-size policy for sent_messages.json
  - [ ] Implement archiving/trimming if needed; document in USER_DATA_MODEL or config

**Nightly No-Shim Validation Runs**
- *What it means*: Run the full suite with `ENABLE_TEST_DATA_SHIM=0` nightly to validate underlying stability.
- *Why it helps*: Ensures we're not masking issues behind the test-only shim and maintains long-term robustness.
- *Estimated effort*: Small

### Documentation

**Update Inter-Documentation References to Include Section Numbers**
- *What it means*: Update cross-references between documentation files to include section numbers and titles (e.g., "See section 3.2. Logging Architecture in LOGGING_GUIDE.md" instead of just "See LOGGING_GUIDE.md")
- *Why it helps*: Makes references more precise and easier to navigate, especially with numbered headings now standardized; improves documentation usability
- *Estimated effort*: Medium
- *Subtasks*:
  - [ ] Audit all documentation files for cross-references
  - [ ] Update references to include section numbers and titles where applicable
  - [ ] Create script or tool to help identify and update references automatically
  - [ ] Update documentation standards to require section numbers in references

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

### AI & Conversation

**Improve Natural Language Processing Accuracy**
- *What it means*: Refine parsing patterns and thresholds to better recognize intents and entities
- *Why it helps*: More reliable command understanding and fewer misinterpretations
- *Estimated effort*: Medium

**Investigate and Refactor AI Command List Generation**
- *What it means*: Investigate why there are two separate hardcoded command lists for the AI chatbot (in `ai/prompt_manager.py` and `ai/chatbot.py`) and explore generating these lists dynamically from the handlers' `can_handle()` methods or the command parser's `intent_patterns` dictionary
- *Why it helps*: Prevents maintenance issues where new commands (like `create_quick_note`) need to be manually added to multiple places, reduces risk of inconsistencies between lists, and ensures the AI always knows about all available commands automatically
- *Estimated effort*: Medium
- *Subtasks*:
  - [ ] Investigate why there are two separate lists (historical reasons, different use cases, etc.)
  - [ ] Review how `get_all_handlers()` and handlers' `can_handle()` methods work
  - [ ] Review how `command_parser.intent_patterns` is structured
  - [ ] Explore generating command list dynamically from handlers (iterate through handlers, collect all intents from `can_handle()` methods)
  - [ ] Explore generating command list dynamically from command parser (extract keys from `intent_patterns` dictionary)
  - [ ] Evaluate pros/cons of each approach (handler-based vs parser-based)
  - [ ] Determine if both lists serve different purposes or can be consolidated
  - [ ] Implement dynamic generation and update both locations to use it
  - [ ] Add tests to ensure command lists stay in sync with actual available commands
  - [ ] Document the new approach in relevant documentation

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

**Investigate markdown link issues**
- *What it means*: Some markdown links work in the editor while others don't, even with the same format. Need to investigate why relative paths work for some files but not others.
- *Why it helps*: Ensures all report links are clickable and functional in the editor
- *Estimated effort*: Small

### Testing

**Add Failure-Focused Detailed Reruns and Flake Classification to Normal Test Runs**
- *What it means*: Enhance the standard test workflow so that when a run has failures, the suite automatically reruns only failing tests with high-detail logging and records whether failures look flaky, isolation-related, or race-condition-like.
- *Why it helps*: Captures actionable debug data at failure time, improves flaky diagnosis, and avoids relying only on `--lf` behavior that can miss intermittent issues.
- *Estimated effort*: Medium
- *Subtasks*:
  - [ ] Add optional post-failure rerun mode in test runner/flaky detector to rerun failed nodeids with `-vv -s --tb=long --show-capture=all`
  - [ ] Persist per-failure artifacts (original run + rerun) in `tests/logs/` with run IDs and timestamps
  - [ ] Add simple classification tags for failures (`stable`, `flaky`, `possible_isolation`, `possible_race`) based on rerun outcomes and patterns
  - [ ] Include classification summary in flaky detector/report output
  - [ ] Document the workflow and triage guidance for contributors

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

**headless service not working**
- Investigate and fix

  **Unify derived command map semantics** - Remove/standardize the precomputed `slash_command_map` - see communication\message_processing\interaction_manager.py
- *What it means*: Identify all usages of `InteractionManager.slash_command_map` and either (a) delete it and rely on `get_slash_command_map()`, or (b) standardize it to use unprefixed keys (e.g. `"tasks"`) and correct naming/comments.
- *Why it helps*: Prevents mismatched expectations (`"/tasks"` vs `"tasks"`), reduces duplicate sources of truth, and makes command registration code less error-prone.
- *Estimated effort*: Small

**Eliminate inconsistent command conversion recursion** - Make slash and bang command handling follow the same conversion strategy - see communication\message_processing\interaction_manager.py
- *What it means*: Refactor the `/...` and `!...` branches so they both either (a) convert the message and continue in the same `handle_message()` call, or (b) recurse in a controlled single-path function (recommended: convert + continue). Ensure flow-clearing and keyword handling run exactly once.
- *Why it helps*: Removes subtle behavior drift between `/cmd` and `!cmd` (double-logging, repeated flow clearing, different keyword precedence), making command handling predictable and testable.
- *Estimated effort*: Medium

**Investigate naive vs timezone-aware datetime usage in scheduler & task reminders**
Context: During the datetime canonicalization audit, a potential split was identified between:
- **Timezone-aware datetimes** (e.g., `pytz.localize(...)`) used in parts of `core/scheduler.py`, and  
- **Naive datetimes** produced by canonical parsing helpers (e.g., `parse_timestamp_minute(...)`) and compared against canonical "now".
This task is to **investigate intent and correctness**, not to refactor preemptively.
---
Scope of investigation
- Identify all places where:
  - naive datetimes are compared to aware datetimes
  - scheduling logic mixes naive and aware datetimes within the same workflow
- Confirm intended semantics for:
  - task reminders scheduled via `schedule_task_reminder_at_datetime`
  - check-ins and scheduled messages using localized datetimes
- Review test coverage to determine:
  - whether timezone behavior is explicitly asserted
  - whether naive/aware assumptions are relied upon implicitly
  - [ ] Audit tests with `TEST_NOW_DT` variables to ensure canonical time helpers (`now_datetime_full`, `now_datetime_minute`) are patched where "now" semantics are intended
---
Key questions to answer
- Are task reminders intentionally timezone-agnostic, or should they respect user timezone?
- Are all scheduler comparisons guaranteed to be naive-to-naive or aware-to-aware today?
- Is there any risk of:
  - `TypeError` from naive/aware comparisons
  - silent offset errors around DST or midnight boundaries
- Should timezone localization be:
  - centralized further, or
  - kept split by design (and documented)?
---
Non-goals
- Do **not** change behavior during this task
- Do **not** introduce new datetime helpers or formats
- Do **not** refactor unless a correctness bug is proven
---
Deliverables
- Written conclusion stating whether the naive/aware split is:
  - intentional and safe, or
  - accidental and risky
- If risky, a **separate, explicitly scoped follow-up task** proposing a fix
- Documentation note if the split is intentional (where and why)
---
Priority
- Medium  
- Blocker only if a real bug or undefined behavior is confirmed

**Test coverage variability**
- investigate test coverage results varying considerably from run to run. At present last several run results were these:
  - 64.4% (19230 of 29879 statements)
  - 43.6% (12910 of 29598 statements)
  - 71.3% (21306 of 29873 statements)
  - 71.4% (21300 of 29823 statements)
  - 71.4% (21300 of 29823 statements)
  - 71.6% (21378 of 29861 statements)
  - 59.4% (17572 of 29578 statements)
- note that issue predates addition of caching, and isn't explained by test failures or caching issues

**Email service not showing as active**
- after running for some time, checking the UI will show the service discord and ngrok running, but email not running
- logs don't indicate email service failure
- investigate and resolve

**Possible Duplicate Lists**
- investigate documentation and code in detail for potential duplicate lists
- whenever there are lists that may be used or referenced in multiple locations, they should have one canonical location
  - that cannonical list location should be updated when there are changes and all other locations should, in the case of code, dynamically pull the list from the canonical location or in the case of documentation, primarily point to the canonical location  
  - this will reduce drift and improve accuracy and completeness
- I'm thinking lists like lists of docs, constants, commands, files, etc. etc. 
- Perform some careful searches and sweeps to find any such duplicated or partially duplicated lists.
- explore how we would go about setting a canonical location/source for each such list and implement it

**Test Run Crashes and Failures Console Output**
- currently output looks something like this: 
  <!-- (.venv) PS C:\Users\Julie\projects\MHM\MHM> python run_tests.py
  [INFO] Automatic termination enabled at 98.0% system memory
  Static check passed: no forbidden logger usage detected
  [INFO] Auto-detected 12 CPUs, using 4 workers to prevent OOM

  MHM Test Runner
  Mode: all
  Description: All Tests (Unit, Integration, Behavior, UI)
  Parallel: Yes (auto workers)
  Note: Tests marked with @pytest.mark.no_parallel will run separately in serial mode

  Pytest Configuration:
    Platform: win32
    Python: 3.12.6
    Random Seed: 12345 (fixed for reproducibility)

  Running: All Tests (Unit, Integration, Behavior, UI)...
  [PROCESS] Creating process with CREATE_NEW_PROCESS_GROUP flag for tree termination
  [PROCESS] Started pytest process PID 1884 (can kill tree)
  ============================= test session starts =============================
  platform win32 -- Python 3.12.6, pytest-8.4.1, pluggy-1.6.0
  Using --randomly-seed=12345
  rootdir: C:\Users\Julie\projects\MHM\MHM
  configfile: pytest.ini
  plugins: asyncio-1.1.0, cov-6.2.1, mock-3.14.1, randomly-3.16.0, timeout-2.4.0, xdist-3.8.0
  asyncio: mode=Mode.STRICT, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
  created: 4/4 workers
  4 workers [4423 items]

  ........................................................................ [  1%]
  ..............................s......................................... [  3%]
  ........................................................................ [  4%]
  ........................................................................ [  6%]
  ........................................................................ [  8%]
  ........................................................................ [  9%]
  [PROGRESS] All Tests (Unit, Integration, Behavior, UI) running for 30s...
  ........................................................................ [ 11%]
  ........................................................................ [ 13%]
  ........................................................................ [ 14%]
  ........................................................................ [ 16%]
  ........................................................................ [ 17%]
  [PROGRESS] All Tests (Unit, Integration, Behavior, UI) running for 60s...
  ........................................................................ [ 19%]
  ........................................................................ [ 21%]
  ........................................................................ [ 22%]
  ........................................................................ [ 24%]
  ........................................................................ [ 26%]
  [PROGRESS] All Tests (Unit, Integration, Behavior, UI) running for 90s...
  ........................................................................ [ 27%]
  ........................................................................ [ 29%]
  ........................................................................ [ 30%]
  ........................................................................ [ 32%]
  ........................................................................ [ 34%]
  ........................................................................ [ 35%]
  ........................................................................ [ 37%]
  ........................................................................ [ 39%]
  ........................................................................ [ 40%]
  [PROGRESS] All Tests (Unit, Integration, Behavior, UI) running for 120s...
  ........................................................................ [ 42%]
  ........................................................................ [ 43%]
  ........................................................................ [ 45%]
  ........................................................................ [ 47%]
  ........................................................................ [ 48%]
  ........................................................................ [ 50%]
  ........................................................................ [ 52%]
  [PROGRESS] All Tests (Unit, Integration, Behavior, UI) running for 150s...
  ........................................................................ [ 53%]
  ........................................................................ [ 55%]
  ........................................................................ [ 56%]
  ........................................................................ [ 58%]
  ........................................................................ [ 60%]
  ........................................................................ [ 61%]
  ........................................................................ [ 63%]
  ........................................................................ [ 65%]
  ........................................................................ [ 66%]
  ........................................................................ [ 68%]
  ........................................................................ [ 69%]
  [PROGRESS] All Tests (Unit, Integration, Behavior, UI) running for 180s...
  ........................................................................ [ 71%]
  ........................................................................ [ 73%]
  ........................................................................ [ 74%]
  ........................................................................ [ 76%]
  ........................................................................ [ 78%]
  ........................................................................ [ 79%]
  ........................................................................ [ 81%]
  ........................................................................ [ 83%]
  ........................................................................ [ 84%]
  [PROGRESS] All Tests (Unit, Integration, Behavior, UI) running for 210s...
  ........................................................................ [ 86%]
  ........................................................................ [ 87%]
  ........................................................................ [ 89%]
  ........................................................................ [ 91%]
  ........................................................................ [ 92%]
  ........................................................................ [ 94%]
  ........................................................................ [ 96%]
  [PROGRESS] All Tests (Unit, Integration, Behavior, UI) running for 240s...
  ........................................................................ [ 97%]
  ........................................................................ [ 99%]
  [PROGRESS] All Tests (Unit, Integration, Behavior, UI) running for 270s...
  ...............................                                          [100%]Global QMessageBox patches applied to prevent popup dialogs

  ---- generated xml file: C:\Users\Julie\AppData\Local\Temp\tmp5hw70n34.xml ----
  ================= 4422 passed, 1 skipped in 278.78s (0:04:38) =================
  [CLEANUP] Process 1884 not found (already terminated)
  Global QMessageBox patches applied to prevent popup dialogs
  [CLEANUP] Consolidating worker log files...
  [CLEANUP] Worker log consolidation complete

  [SUCCESS] All Tests (Unit, Integration, Behavior, UI) completed successfully in 283.08555150032043s

  [NO_PARALLEL] Running tests marked with @pytest.mark.no_parallel in serial mode...

  Running: No-Parallel Tests (Serial)...
  [PROCESS] Creating process with CREATE_NEW_PROCESS_GROUP flag for tree termination
  [PROCESS] Started pytest process PID 988 (can kill tree)
  ============================= test session starts =============================
  platform win32 -- Python 3.12.6, pytest-8.4.1, pluggy-1.6.0
  Using --randomly-seed=12345
  rootdir: C:\Users\Julie\projects\MHM\MHM
  configfile: pytest.ini
  plugins: asyncio-1.1.0, cov-6.2.1, mock-3.14.1, randomly-3.16.0, timeout-2.4.0, xdist-3.8.0
  asyncio: mode=Mode.STRICT, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
  collected 4544 items / 4423 deselected / 121 selected

  tests\unit\test_user_management.py ......                                [  5%]
  tests\behavior\test_conversation_flow_manager_behavior.py ..             [  6%]
  tests\behavior\test_discord_checkin_retry_behavior.py .                  [  7%]
  tests\integration\test_account_management.py .                           [  8%]
  tests\behavior\test_user_data_flow_architecture.py ........              [ 15%]
  tests\behavior\test_discord_bot_behavior.py ...                          [ 17%]
  tests\ui\test_account_creation_ui.py ..                                  [ 19%]
  [PROGRESS] No-Parallel Tests (Serial) running for 30s...
  tests\behavior\test_message_behavior.py ....                             [ 22%]
  tests\behavior\test_task_error_handling.py .                             [ 23%]
  tests\behavior\test_response_tracking_behavior.py .                      [ 24%]
  tests\unit\test_file_operations.py ..                                    [ 25%]
  tests\behavior\test_service_behavior.py .                                [ 26%]
  tests\behavior\test_account_management_real_behavior.py ......           [ 31%]
  tests\integration\test_orphaned_reminder_cleanup.py .                    [ 32%]
  [PROGRESS] No-Parallel Tests (Serial) running for 60s...
  tests\ui\test_ui_app_qt_main.py [CLEANUP] Process 988 not found (already terminated)
  [CLEANUP] Consolidating worker log files...
  [CLEANUP] Worker log consolidation complete

  [FAILED] No-Parallel Tests (Serial) failed with exit code 3221226505 after 67.21692824363708s
  [CRASH] Windows process crash detected (0xC0000135 / STATUS_DLL_NOT_FOUND).
  [CRASH] This is typically an environment/DLL issue (often Qt platform plugin loading).

  ================================================================================
  COMBINED TEST RESULTS SUMMARY
  ================================================================================
  Mode: All Tests (Unit, Integration, Behavior, UI)

  Test Statistics:
    Total Tests:  4423
    Passed:       4422
    Failed:       0
    Skipped:      1
    Deselected:   0
    Warnings:     0

  Breakdown:
    Parallel Tests:    4422 passed, 0 failed, 1 skipped, 0 deselected, 0 warnings (283.08555150032043s)
    Serial Tests:      0 passed, 0 failed, 0 skipped, 0 deselected, 0 warnings (67.21692824363708s)

  Total Duration: 350.3024797439575s
    Passed:       4422
    Failed:       0
    Skipped:      1
    Deselected:   0
    Warnings:     0

  Breakdown:
    Parallel Tests:    4422 passed, 0 failed, 1 skipped, 0 deselected, 0 warnings (283.08555150032043s)
    Passed:       4422
    Failed:       0
    Skipped:      1
    Deselected:   0
    Warnings:     0

  Breakdown:
    Passed:       4422
    Failed:       0
    Skipped:      1
    Deselected:   0
    Warnings:     0

    Passed:       4422
    Failed:       0
    Skipped:      1
    Deselected:   0
    Warnings:     0
    Passed:       4422
    Failed:       0
    Skipped:      1
    Deselected:   0
    Passed:       4422
    Failed:       0
    Skipped:      1
    Passed:       4422
    Passed:       4422
    Failed:       0
    Passed:       4422
    Passed:       4422
    Failed:       0
    Skipped:      1
    Passed:       4422
    Failed:       0
    Passed:       4422
    Failed:       0
    Passed:       4422
    Failed:       0
    Skipped:      1
    Deselected:   0
    Warnings:     0

  Breakdown:
    Parallel Tests:    4422 passed, 0 failed, 1 skipped, 0 deselected, 0 warnings (283.08555150032043s)
    Serial Tests:      0 passed, 0 failed, 0 skipped, 0 deselected, 0 warnings (67.21692824363708s)

  Total Duration: 350.3024797439575s

  ========== 0 failed, 4422 passed, 1 skipped, 0 warnings, in 350.30s (0:05:50) ========== -->
- this isn't ideal for a few reasons, but critically the crash/failed message is much too far from the bottom and so I miss it. Any critical messages like that should be at or near the very bottom, like within the last 8 lines say.
- the crash issue itself has already been addressed, this task is solely for output formatting


**Improve existing test runner**
   - set process priority during testing
   - optionally pause LM Studio model server if not required by tests
   - avoid creating new runner, extend run_tests.py

**Audit MHM project for duplicate, outdated, unnecessary backups and archive copies**
  - implement structured regular local backups with compression and rotation 

**Review RAM usage and caching behavior during development**
   - Python worker memory usage
   - LM Studio model residency in RAM
   - Windows file cache behavior during large test runs
   - Identify safe optimizations without reducing usability

**cleanup/simplify test artifact cleanup**
- everything in tests/data/ should be cleaned up between test runs
