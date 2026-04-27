# TODO.md - MHM Project Tasks

> **File**: `TODO.md`
> **Audience**: Human Developer (Beginner Programmer) and AI collaborators
> **Purpose**: Current development priorities and planned improvements  
> **Style**: Organized, actionable, beginner-friendly
> **Last Updated**: 2026-04-04 (sent_messages TODO closed; see CHANGELOG)
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
- **Dating**: Add `- *Created*: YYYY-MM-DD` when adding new tasks; add completion date when marking progress


**Note**: Phase 1: Enhanced Task & Check-in Systems is tracked in [PLANS.md](development_docs/PLANS.md). 
**Note**: Mood-Aware Support Calibration items (Safety Net Response Library, Task Breakdown Prompt Experiments, Context-Aware Reminder Content Mapping, Mood Re-evaluation Cadence Guidelines) are tracked in [PLANS.md](development_docs/PLANS.md) under "Mood-Aware Support Calibration" plan.
**Note**: Development tools backlog is tracked in [AI_DEV_TOOLS_IMPROVEMENT_PLAN_V5.md](development_tools/AI_DEV_TOOLS_IMPROVEMENT_PLAN_V5.md). [AI_DEV_TOOLS_IMPROVEMENT_PLAN_V4.md](archive/AI_DEV_TOOLS_IMPROVEMENT_PLAN_V4.md) remains for historical V4 checkboxes only.
**Testing Source of Truth**: All testing roadmap items are tracked in [TEST_PLAN.md](development_docs/TEST_PLAN.md). Keep only non-testing TODO items here. Coverage-growth follow-ups from this session are tracked in TEST_PLAN Phase 5.7.
**Legacy/Deprecation Source of Truth**: Development-tools legacy cleanup follow-ups are tracked in [AI_DEV_TOOLS_IMPROVEMENT_PLAN_V5.md](development_tools/AI_DEV_TOOLS_IMPROVEMENT_PLAN_V5.md) section 5.6 and must align with `development_tools/config/jsons/DEPRECATION_INVENTORY.json`.

**Parallel product work (from audits)**: After each `audit --full`, use [`development_tools/AI_PRIORITIES.md`](development_tools/AI_PRIORITIES.md) for coverage, duplicates, coupling, and complexity (V5 Section 5.6); this is separate from dev-tools suite implementation in [`AI_DEV_TOOLS_IMPROVEMENT_PLAN_V5.md`](development_tools/AI_DEV_TOOLS_IMPROVEMENT_PLAN_V5.md).

**Development tools backlog (scheduled review order, 2026-03-26)**  
- Portability / Section 7.6: full Pyright diagnostic parity tests when tolerance rules exist (policy tests today: `tests/development_tools/test_pyright_config_paths.py`).  
- Section 3.12 flaky detector: migrated to tracked `development_tools/tests/flaky_detector.py` with CLI command `flaky-detector`; continue follow-up hardening/tests as needed.  
- Section 3.13-Section 3.14: migrated `scripts/testing/verify_process_cleanup.py` to tracked `development_tools/tests/verify_process_cleanup.py`; `scripts/cleanup_project.py` remains historical while `development_tools/shared/fix_project_cleanup.py` is canonical.  
- Section 4.1: external tools evaluation (bandit, pip-audit, radon, pre-commit) per paired guides Section 10.  
- Section 5.x: low-priority gap tools (unused-imports fixer, doc overlap, TODO sync auto-clean, memory profiler).  
Detail: [AI_DEV_TOOLS_IMPROVEMENT_PLAN_V5.md](development_tools/AI_DEV_TOOLS_IMPROVEMENT_PLAN_V5.md).

**Deferred (Phase C - no blocking)**  
- **Section 2.8 `--dev-tools-only` report scoping**: generators still project-wide; DEV_TOOLS_* mirrors until scope-aware builders exist.  
- **Section 1.1 `test_config.json` fixture migration**: adopt when touching analyzer tests; full pass is low priority.  
Pointers: [AI_DEV_TOOLS_IMPROVEMENT_PLAN_V5.md](development_tools/AI_DEV_TOOLS_IMPROVEMENT_PLAN_V5.md) (Section 5.1 / Section 5.2); [tests/development_tools/test_config.json](tests/development_tools/test_config.json).

**Use / fit** (2026-02-28 user-priority Q&A): Headless + email admin status fixes shipped 2026-04-02. AI items deferred until system overhaul. Script ownership, sent_messages high priority. Ruff outside tests > inside. Duplicate lists and backup audit moved to dev tools. Performance monitoring includes RAM/caching.

## High Priority
### User Data Model Stabilization

**Define canonical v2 user-data schemas before migration**
- *What it means*: Define the final v2 JSON structures for tasks, notes, journal entries, check-ins, message templates, and message delivery records before changing runtime code.
- *Why it helps*: Prevents piecemeal migrations and keeps the JSON model aligned with the future SQLite model.
- *Estimated effort*: Medium
- *Created*: 2026-04-26
- *Subtasks*:
  - [ ] Document the canonical v2 structures for:
    - [ ] task
    - [ ] note
    - [ ] journal_entry
    - [ ] checkin
    - [ ] message
    - [ ] message delivery
  - [ ] Confirm field names before implementation, including:
    - [ ] `id`
    - [ ] `short_id`
    - [ ] `kind`
    - [ ] `title`
    - [ ] `description`
    - [ ] `category`
    - [ ] `group`
    - [ ] `tags`
    - [ ] `status`
    - [ ] `source`
    - [ ] `linked_item_ids`
    - [ ] `created_at`
    - [ ] `updated_at`
    - [ ] `archived_at`
    - [ ] `deleted_at`
    - [ ] `metadata`
  - [ ] Confirm timestamp fields use canonical MHM timestamp helpers.
  - [ ] Confirm short ID format uses no dash, such as `t6ca6`, `nabc123`, and `jabc123`.
  - [ ] Do not add compatibility fields unless required for reading existing user data during migration.
  - [ ] Any required compatibility bridge must be explicitly marked temporary, logged when exercised, and assigned a removal task.

**Create user-data migration inventory**
- *What it means*: Identify every existing user-data file and map it to its v2 destination structure.
- *Why it helps*: Makes the migration deliberate instead of discovering issues while editing runtime code.
- *Estimated effort*: Medium
- *Created*: 2026-04-26
- *Subtasks*:
  - [ ] Inventory current files:
    - [ ] `account.json`
    - [ ] `preferences.json`
    - [ ] `schedules.json`
    - [ ] `tags.json`
    - [ ] `user_context.json`
    - [ ] `chat_interactions.json`
    - [ ] `checkins.json`
    - [ ] `messages/*.json`
    - [ ] `messages/sent_messages.json`
    - [ ] `notebook/entries.json`
    - [ ] `tasks/active_tasks.json`
    - [ ] `tasks/completed_tasks.json`
    - [ ] `tasks/task_schedules.json`
  - [ ] For each file, document:
    - [ ] current wrapper shape
    - [ ] current item fields
    - [ ] missing v2 fields
    - [ ] renamed v2 fields
    - [ ] fields to remove
    - [ ] fields to preserve in `metadata` temporarily, if needed
  - [ ] Mark every old field as one of:
    - [ ] migrate directly
    - [ ] migrate with transformation
    - [ ] drop
    - [ ] temporary bridge only
  - [ ] Avoid keeping old fields in the v2 model unless they are required for a specific active behavior.

**Build one-time JSON migration tools**
- *What it means*: Create explicit migration scripts/tools that convert existing JSON data to v2 JSON structures.
- *Why it helps*: Keeps migration code out of normal runtime paths as much as possible.
- *Estimated effort*: Large
- *Created*: 2026-04-26
- *Subtasks*:
  - [ ] Add a migration tool for current JSON user data to v2 JSON user data.
  - [ ] The tool must create a backup before writing migrated files.
  - [ ] The tool must write a migration report listing:
    - [ ] files migrated
    - [ ] records migrated
    - [ ] fields renamed
    - [ ] fields dropped
    - [ ] fields moved to `metadata`
    - [ ] records skipped or requiring manual review
  - [ ] Do not silently preserve obsolete structures.
  - [ ] If a temporary compatibility bridge is unavoidable, add:
    - [ ] `LEGACY COMPATIBILITY` marker in code
    - [ ] log message when used
    - [ ] deprecation inventory entry
    - [ ] removal checklist
    - [ ] planned removal condition

**Add v2 schema validation**
- *What it means*: Add validation for the new v2 structures so malformed data cannot be saved.
- *Why it helps*: Prevents the new data model from drifting back into inconsistent JSON.
- *Estimated effort*: Medium
- *Created*: 2026-04-26
- *Subtasks*:
  - [ ] Add validation for required shared fields.
  - [ ] Add validation for type-specific fields.
  - [ ] Validate allowed `kind` values.
  - [ ] Validate allowed `status` values by item type.
  - [ ] Validate `tags` as a normalized list.
  - [ ] Validate `linked_item_ids` as a list.
  - [ ] Validate `source` objects.
  - [ ] Validate timestamps through canonical time helpers.
  - [ ] Reject new writes using old field names unless explicitly handled by a migration tool.

**Add migration tests**
- *What it means*: Add automated tests proving real current JSON examples migrate correctly to v2 structures.
- *Why it helps*: Prevents accidental data loss and confirms the migration is safe.
- *Estimated effort*: Large
- *Created*: 2026-04-26
- *Subtasks*:
  - [ ] Add fixture copies of representative current JSON structures.
  - [ ] Test task migration.
  - [ ] Test notebook note migration.
  - [ ] Test journal entry migration.
  - [ ] Test check-in migration.
  - [ ] Test message template migration.
  - [ ] Test sent message delivery migration.
  - [ ] Test malformed or incomplete records.
  - [ ] Test backup creation before migration writes.
  - [ ] Test that obsolete fields are removed, transformed, or explicitly moved to `metadata`.
  - [ ] Test that temporary compatibility paths are not used after migration.

**Remove temporary compatibility bridges after migration**
- *What it means*: Track and remove any compatibility code added only to support old JSON structures.
- *Why it helps*: Prevents permanent bloat and avoids carrying old schemas indefinitely.
- *Estimated effort*: Medium
- *Created*: 2026-04-26
- *Subtasks*:
  - [ ] Register each temporary bridge in the deprecation inventory.
  - [ ] Add specific search terms for each old field/path.
  - [ ] Run legacy find/verify tooling before removal.
  - [ ] Remove bridge code only after migrated data is validated and tests pass.
  - [ ] Remove tests that exist only to preserve old behavior.
  - [ ] Keep historical changelog/archive references only where useful.
  - [ ] Confirm active code/config no longer references old structures.

### Check-in Data Model Migration

**Migrate check-ins to canonical v2 checkin structure**
- *What it means*: Convert check-in records from flat, evolving fields into structured response records.
- *Why it helps*: Supports changing check-in questions without changing the top-level schema every time.
- *Estimated effort*: Large
- *Created*: 2026-04-26
- *Target structure*:
  - [ ] `schema_version`
  - [ ] `updated_at`
  - [ ] `checkins`
  - [ ] `checkins[].id`
  - [ ] `checkins[].submitted_at`
  - [ ] `checkins[].source`
  - [ ] `checkins[].responses`
  - [ ] `checkins[].questions_asked`
  - [ ] `checkins[].linked_item_ids`
  - [ ] `checkins[].created_at`
  - [ ] `checkins[].updated_at`
  - [ ] `checkins[].archived_at`
  - [ ] `checkins[].deleted_at`
  - [ ] `checkins[].metadata`
- *Subtasks*:
  - [ ] Wrap raw check-in arrays in a versioned object if not already wrapped.
  - [ ] Generate `id` for each check-in.
  - [ ] Move existing `timestamp` to `submitted_at`.
  - [ ] Copy `submitted_at` into `created_at` and `updated_at` during migration unless better data exists.
  - [ ] Move all check-in answers into `responses`.
  - [ ] Populate `questions_asked` from response keys.
  - [ ] Add `source`, defaulting to best known channel information.
  - [ ] Add `linked_item_ids`, defaulting to an empty list.
  - [ ] Add `archived_at` and `deleted_at`, defaulting to null.
  - [ ] Do not keep old top-level answer fields after successful migration.
  - [ ] Add migration tests for older and newer check-in shapes.

**Update check-in analytics to read v2 responses**
- *What it means*: Update analytics and AI context logic to read check-in values from `responses`.
- *Why it helps*: Keeps analytics working after the schema migration.
- *Estimated effort*: Medium
- *Created*: 2026-04-26
- *Subtasks*:
  - [ ] Identify all code reading direct check-in fields such as `mood`, `energy`, `ate_breakfast`, and `brushed_teeth`.
  - [ ] Update reads to use `responses`.
  - [ ] Add helper functions for common response access.
  - [ ] Avoid adding permanent fallback reads for old flat fields.
  - [ ] If fallback reads are temporarily required, mark them as temporary compatibility and add planned removal.

---

### Message Data Model Migration

**Migrate message templates to canonical v2 message structure**
- *What it means*: Convert category message files into versioned message template collections.
- *Why it helps*: Separates reusable message definitions from delivery history.
- *Estimated effort*: Large
- *Created*: 2026-04-26
- *Target structure*:
  - [ ] `schema_version`
  - [ ] `category`
  - [ ] `updated_at`
  - [ ] `messages`
  - [ ] `messages[].id`
  - [ ] `messages[].kind`
  - [ ] `messages[].text`
  - [ ] `messages[].category`
  - [ ] `messages[].active`
  - [ ] `messages[].schedule`
  - [ ] `messages[].created_at`
  - [ ] `messages[].updated_at`
  - [ ] `messages[].archived_at`
  - [ ] `messages[].deleted_at`
  - [ ] `messages[].metadata`
- *Subtasks*:
  - [ ] Convert `message_id` to `id`.
  - [ ] Set `kind` to `message`.
  - [ ] Convert `message` text field to `text`.
  - [ ] Preserve category.
  - [ ] Add `active`.
  - [ ] Move `days` and `time_periods` into `schedule.days` and `schedule.periods`.
  - [ ] Add `created_at` and `updated_at`.
  - [ ] Add `archived_at` and `deleted_at`.
  - [ ] Use `metadata` only for unmapped fields requiring manual review.
  - [ ] Do not keep old `message`, `days`, or `time_periods` fields in v2 records after migration.

**Migrate sent messages to canonical v2 delivery records**
- *What it means*: Convert `sent_messages.json` into message delivery history records.
- *Why it helps*: Makes delivery tracking distinct from message templates and easier to query later.
- *Estimated effort*: Large
- *Created*: 2026-04-26
- *Target structure*:
  - [ ] `schema_version`
  - [ ] `updated_at`
  - [ ] `deliveries`
  - [ ] `deliveries[].id`
  - [ ] `deliveries[].message_template_id`
  - [ ] `deliveries[].sent_text`
  - [ ] `deliveries[].category`
  - [ ] `deliveries[].channel`
  - [ ] `deliveries[].status`
  - [ ] `deliveries[].source`
  - [ ] `deliveries[].sent_at`
  - [ ] `deliveries[].time_period`
  - [ ] `deliveries[].metadata`
- *Subtasks*:
  - [ ] Generate a unique delivery `id`.
  - [ ] Move old `message_id` to `message_template_id`.
  - [ ] Move old `message` to `sent_text`.
  - [ ] Move `delivery_status` to `status`.
  - [ ] Move `timestamp` to `sent_at`.
  - [ ] Preserve `category`.
  - [ ] Preserve `time_period`.
  - [ ] Add `channel`, defaulting to best known channel.
  - [ ] Add `source`, defaulting to `scheduler` when appropriate.
  - [ ] Preserve existing metadata only if still useful.
  - [ ] Do not keep old delivery field names in v2 delivery records after migration.

**Update message selection and delivery code for v2 messages**
- *What it means*: Update runtime code to use `text`, `schedule`, and delivery records instead of old message fields.
- *Why it helps*: Makes the v2 message model active instead of just migrated data.
- *Estimated effort*: Medium
- *Created*: 2026-04-26
- *Subtasks*:
  - [ ] Identify all code reading message template fields.
  - [ ] Update reads from `message` to `text`.
  - [ ] Update schedule reads from `days` / `time_periods` to `schedule.days` / `schedule.periods`.
  - [ ] Identify all code writing sent message history.
  - [ ] Update writes to use delivery records.
  - [ ] Avoid permanent fallback logic for old fields.
  - [ ] Add temporary compatibility only if required to avoid breaking existing unmigrated data.
  - [ ] Add planned removal for any fallback logic.

---

### Schedule Data Model Follow-up

**Assess schedule period normalization after item migration**
- *What it means*: Decide whether `schedules.json` should be flattened into a versioned list of schedule periods.
- *Why it helps*: A flatter schedule model would map better to SQLite, but this should not distract from task/note/check-in/message migration.
- *Estimated effort*: Medium
- *Created*: 2026-04-26
- *Subtasks*:
  - [ ] Inventory current schedule scopes and periods.
  - [ ] Decide whether to keep nested schedule structure temporarily.
  - [ ] If flattening, define canonical schedule period fields.
  - [ ] Avoid creating compatibility layers until the schedule migration is actually implemented.
  - [ ] If compatibility is required, mark it temporary and add planned removal.

### Quality & Operations (high priority within medium)

**Script Ownership and Retirement Decisions (project-specific, not development-tools portability)**
- *What it means*: Resolve ownership for persistent project scripts currently under untracked `scripts/`, retire obsolete ones, and migrate any still-needed functionality into tracked runtime locations.
- *Why it helps*: Prevents drift between docs and reality, reduces maintenance risk, and keeps `development_tools/` project-agnostic.
- *Estimated effort*: Medium
- *User priority*: High/medium.
- *Subtasks*:
  - [ ] Decide destination for the user_data_cli script (planned location scripts/utilities/; migrate to tracked runtime ownership such as core/ or user/ or app-tools, or retire if superseded).
  - [ ] Decide destination for project-maintenance scripts create_project_snapshot and cleanup_windows_tasks (planned location scripts/; tracked runtime ownership, not development_tools/).
  - [ ] Evaluate renaming/refactoring the create_project_snapshot script to match behavior (full restorable backup semantics) and define whether a separate generalized development-tools variant is needed.

## Medium Priority

### Documentation

**Update Inter-Documentation References to Include Section Numbers**
- *What it means*: Update cross-references between documentation files to include section numbers and titles (e.g., "See section 3.2. Logging Architecture in LOGGING_GUIDE.md" instead of just "See LOGGING_GUIDE.md"). Expand development tools to assist (e.g., doc-sync or new analyzer).
- *Why it helps*: Makes references more precise and easier to navigate, especially with numbered headings now standardized; improves documentation usability
- *Estimated effort*: Medium
- *User priority*: Medium.
- *Subtasks*:
  - [ ] Audit all documentation files for cross-references
  - [ ] Update references to include section numbers and titles where applicable
  - [ ] Create script or tool to help identify and update references automatically (or extend development tools)
  - [ ] Update documentation standards to require section numbers in references

**Investigate markdown link issues**
- *What it means*: Some markdown links work in the editor while others don't, even with the same format. Need to investigate why relative paths work for some files but not others.
- *Why it helps*: Ensures all report links are clickable and functional in the editor
- *Estimated effort*: Small
- *User priority*: Medium.

### User Experience Improvements

**Investigate Check-in Settings UI Issues**
- *What it means*: Fix two outstanding issues in the check-in management dialog: (1) Maximum spinbox cannot be reduced below minimum value - it should dynamically adjust minimum to match when maximum is reduced, similar to how minimum adjustment works in reverse; (2) Questions section blanks out visually when adding or deleting custom questions, even though the data is preserved correctly.
- *User priority*: Low.
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

**Improve Natural Language Processing (NLP) Accuracy** - *Deferred (AI overhaul)*
- *What it means*: Refine parsing patterns and thresholds to better recognize intents and entities. NLP = how the system interprets user commands and natural language (e.g., "create a task to buy milk" -> task creation intent).
- *Why it helps*: More reliable command understanding and fewer misinterpretations
- *Estimated effort*: Medium

**Investigate and Refactor AI Command List Generation** - *Deferred (AI overhaul)*
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
- *User priority*: Medium.
- *Why it helps*: More predictable user experience and fewer dead-ends
- *Estimated effort*: Medium

### Performance Optimizations

**Optimize AI Response Times** - *Deferred (AI overhaul)*
- *What it means*: Reduce latency for AI-backed responses via batching, caching, or configuration tuning
- *Why it helps*: Snappier interactions and better UX
- *Estimated effort*: Medium

**Improve Message Processing Efficiency**
- *What it means*: Profile and streamline message pipelines (I/O, parsing, scheduling)
- *User priority*: Medium.
- *Why it helps*: Lower CPU usage and faster processing
- *Estimated effort*: Medium

**Reduce Memory Usage**
- *What it means*: Identify hotspots (caches, data copies) and right-size buffers/limits. See also Add Performance Monitoring.
- *User priority*: Medium/low.
- *Why it helps*: Improves stability on constrained systems
- *Estimated effort*: Medium

## Low Priority

### Deferred (AI overhaul)

**AI Chatbot Actionability Sprint** - *Deferred (AI overhaul)*
- *What it means*: Improve AI chat quality and enable robust task/message/profile CRUD, with awareness of recent automated messages and targeted, non-conflicting suggestions.
- *Why it helps*: Addresses the user's biggest friction and increases real utility.
- *Estimated effort*: Large
- *User priority*: Defer until system AI receives major overhaul.

**Differentiate Between New and Returning Users**
- *What it means*: Implement logic to distinguish between users who are authorizing the app for the first time versus users who are returning after deauthorizing
- *Why it helps*: Could enable personalized welcome messages or different onboarding flows for new vs. returning users
- *Estimated effort*: Small/Medium
- *Note*: Not important right now - current welcome system works fine for all users

### Documentation

**Update User Guides**
- *What it means*: Refresh user-facing guides to reflect current features and workflows. (Clarify which guides-user-facing feature docs, setup guides, etc.)
- *Why it helps*: Reduces confusion and accelerates onboarding
- *Estimated effort*: Small

**Improve Code Documentation**
- *What it means*: Add/refresh docstrings and inline docs where clarity is lacking. Make specific and actionable; consider expanding development tools to assist (e.g., docstring coverage, missing-doc detection).
- *Why it helps*: Speeds up development and AI assistance accuracy
- *Estimated effort*: Small

**Create Troubleshooting Guides** - *Deferred*
- *What it means*: Document common issues and resolution steps for channels, UI, and data
- *Why it helps*: Faster recovery when issues occur
- *Estimated effort*: Small

### Testing

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
- *What it means*: Track how long operations take across subsystems. Includes: Python worker memory usage, LM Studio model residency in RAM, Windows file cache behavior during large test runs. Identify safe optimizations without reducing usability.
- *Why it helps*: Helps identify and fix performance problems proactively
- *Estimated effort*: Medium

**Testing Roadmap Consolidation**
- See [TEST_PLAN.md](development_docs/TEST_PLAN.md) for all testing program tasks (source of truth).

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

**Possible Duplicate Lists** - *Tracked in [AI_DEV_TOOLS_IMPROVEMENT_PLAN_V5.md](development_tools/AI_DEV_TOOLS_IMPROVEMENT_PLAN_V5.md) section 7.8*
- *What it means*: Investigate documentation and code for duplicate or partially duplicated lists (docs, constants, commands, files, etc.). Establish canonical locations; code should pull dynamically, docs should point to canonical source.
- *Why it helps*: Reduces drift and improves accuracy.

**Audit MHM project for duplicate, outdated, unnecessary backups and archive copies** - *Tracked in [AI_DEV_TOOLS_IMPROVEMENT_PLAN_V5.md](development_tools/AI_DEV_TOOLS_IMPROVEMENT_PLAN_V5.md) section 7.9*
- *What it means*: Implement structured regular local backups with compression and rotation.

*Note*: Review RAM usage and caching-rolled into **Add Performance Monitoring** (above).

