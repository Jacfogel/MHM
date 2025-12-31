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

**Note**: Development tools related tasks have been moved to [AI_DEV_TOOLS_IMPROVEMENT_PLAN_V3.md](development_tools/AI_DEV_TOOLS_IMPROVEMENT_PLAN_V3.md) for centralized planning and tracking. See that document for all development tools improvements, enhancements, and maintenance tasks.

**Evaluate and Integrate Complementary Development Tools**
- *What it means*: Learn about and test ruff, radon, pydeps, bandit, and pip-audit to determine if they should replace or complement parts of the development tools suite
- *Why it helps*: These tools may be faster or more mature than custom implementations, and security tools (bandit, pip-audit) fill a critical gap since the project handles user data and credentials
- *Estimated effort*: Medium
- *Cursor IDE Compatibility*: All tools are compatible - ruff and bandit have VS Code extensions (Cursor is VS Code-based), others work via command-line or pre-commit hooks
- *Reference*: See [EXISTING_TOOLS_COMPARISON.md](development_docs/EXISTING_TOOLS_COMPARISON.md) and [COMPLEMENTARY_TOOLS_GUIDE.md](development_docs/COMPLEMENTARY_TOOLS_GUIDE.md) for detailed comparisons
- *Subtasks*:
  - [ ] **Learn about and try ruff** - Install ruff, test it on the codebase, compare speed/results with current `analyze_unused_imports.py` (pylint-based)
    - [ ] Install ruff: `pip install ruff`
    - [ ] Install Ruff VS Code extension in Cursor (optional but recommended for real-time feedback)
    - [ ] Run ruff to find unused imports: `ruff check . --select F401`
    - [ ] Compare results with current unused imports tool (357 unused imports found)
    - [ ] Test auto-fix capability: `ruff check --fix .`
    - [ ] Measure performance difference (ruff is 10-100x faster than pylint)
    - [ ] Determine if ruff should replace or complement `analyze_unused_imports.py`
  - [ ] **Learn about and try radon** - Install radon, test complexity analysis, compare with current `analyze_functions.py` complexity tracking
    - [ ] Install radon: `pip install radon`
    - [ ] Run complexity analysis: `radon cc . --min B`
    - [ ] Compare complexity metrics with current tool (131 critical-complexity functions tracked)
    - [ ] Test maintainability index: `radon mi .`
    - [ ] Determine if radon should complement `analyze_functions.py` (keep your tool for docstring/pattern tracking, use radon for complexity)
  - [ ] **Learn about and try pydeps** - Install pydeps, test dependency graph generation, compare with current `analyze_module_dependencies.py`
    - [ ] Install pydeps: `pip install pydeps`
    - [ ] Generate dependency graph for core module: `pydeps core/ --max-bacon=2`
    - [ ] Compare visualization quality with current dependency analysis
    - [ ] Test on communication and other modules
    - [ ] Determine if pydeps should complement `analyze_module_dependencies.py` (use pydeps for graphs, keep your tool for pattern analysis)
  - [ ] **Learn about and try bandit** - Install bandit, test security scanning (HIGH PRIORITY - project handles user data and credentials)
    - [ ] Install bandit: `pip install bandit`
    - [ ] Install Bandit VS Code extension in Cursor (optional but recommended for real-time security feedback)
    - [ ] Run security scan: `bandit -r core/ communication/ -f json -o bandit-report.json`
    - [ ] Review findings for hardcoded secrets, SQL injection risks, insecure random, etc.
    - [ ] Determine if bandit should be added to development tools workflow (recommended: add to Tier 1 quick audit)
    - [ ] Configure bandit to exclude false positives (test files, development tools, etc.)
  - [ ] **Learn about and try pip-audit** - Install pip-audit, test dependency vulnerability scanning (HIGH PRIORITY - project has 15+ dependencies)
    - [ ] Install pip-audit: `pip install pip-audit`
    - [ ] Run dependency check: `pip-audit --requirement requirements.txt --format json`
    - [ ] Review findings for known CVEs in dependencies
    - [ ] Determine if pip-audit should be added to development tools workflow (recommended: add to Tier 1 quick audit)
    - [ ] Set up regular checks (before deployments, in CI/CD if applicable)
  - [ ] **Make integration decision** - Based on testing, decide whether to:
    - Replace tools entirely (if significantly better)
    - Use alongside existing tools (if complementary)
    - Keep existing tools (if they're better for your workflow)
  - [ ] **If integrating**: Add selected tools to development tools workflow (update `development_tools/shared/service/tool_wrappers.py` or create new wrappers)
  - [ ] **If integrating**: Update `requirements.txt` with new tool dependencies
  - [ ] **If integrating**: Install VS Code extensions in Cursor for tools that support them (ruff, bandit)
  - [ ] **If integrating**: Update documentation (AI_DEVELOPMENT_TOOLS_GUIDE.md, DEVELOPMENT_TOOLS_GUIDE.md) to reflect tool changes
  - [ ] **Optional: Learn about vulture** - Dead code detection (finds unused functions/classes, not just imports)
    - [ ] Install vulture: `pip install vulture`
    - [ ] Run dead code scan: `vulture . --min-confidence 80 --exclude tests/`
    - [ ] Review findings (can be noisy with false positives)
    - [ ] Determine if useful for occasional cleanup runs (not in every audit)
  - [ ] **Optional: Learn about pre-commit** - Git hooks for automated quality checks
    - [ ] Install pre-commit: `pip install pre-commit`
    - [ ] Create `.pre-commit-config.yaml` with hooks for ruff, bandit, etc.
    - [ ] Test hooks: `pre-commit run --all-files`
    - [ ] Determine if pre-commit adds value or is too complex for current workflow


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

**Investigate Intermittent Test Failures**
- *What it means*: Investigate and fix two test failures that appear intermittently: `test_comprehensive_context_includes_recent_sent_messages_and_checkin_status` (AI context test) and `test_full_account_lifecycle_real_behavior` (account creation integration test). These failures may be related to timing, race conditions, or test isolation issues.
- *Why it helps*: Ensures test suite reliability and prevents false negatives that can mask real issues
- *Estimated effort*: Small/Medium
- *Subtasks*:
  - [ ] Investigate `test_comprehensive_context_includes_recent_sent_messages_and_checkin_status` failure (assertion that "Recent automated messages sent to them:" is in content)
  - [ ] Investigate `test_full_account_lifecycle_real_behavior` failure (assertion that preferences categories persist after account-only save)
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




