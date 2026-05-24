# TODO.md - MHM Project Tasks

> **File**: `TODO.md`
> **Audience**: Human Developer (Beginner Programmer) and AI collaborators
> **Purpose**: Current development priorities and planned improvements
> **Style**: Organized, actionable, beginner-friendly
> **Last Updated**: 2026-05-23 (post-refactor architecture decision cleanup)
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
**Note**: Development tools backlog is tracked in [AI_DEV_TOOLS_IMPROVEMENT_PLAN_V6.md](development_tools/AI_DEV_TOOLS_IMPROVEMENT_PLAN_V6.md). [AI_DEV_TOOLS_IMPROVEMENT_PLAN_V4.md](archive/AI_DEV_TOOLS_IMPROVEMENT_PLAN_V4.md) remains for historical V4 checkboxes only.
**Testing Source of Truth**: All testing roadmap items are tracked in [TEST_PLAN.md](development_docs/TEST_PLAN.md). Keep only non-testing TODO items here. Coverage-growth follow-ups from this session are tracked in TEST_PLAN Phase 5.7.
**Legacy/Deprecation Source of Truth**: Development-tools legacy cleanup follow-ups are tracked in [AI_DEV_TOOLS_IMPROVEMENT_PLAN_V6.md](development_tools/AI_DEV_TOOLS_IMPROVEMENT_PLAN_V6.md) section 5.6 and must align with `development_tools/config/jsons/DEPRECATION_INVENTORY.json`.

**Parallel product work (from audits)**: After each `audit --full`, use [`development_tools/AI_PRIORITIES.md`](development_tools/AI_PRIORITIES.md) for coverage, duplicates, coupling, and complexity; this is separate from dev-tools suite implementation in [`AI_DEV_TOOLS_IMPROVEMENT_PLAN_V6.md`](development_tools/AI_DEV_TOOLS_IMPROVEMENT_PLAN_V6.md).

**Development tools backlog (active follow-ups only, reviewed 2026-05-11)**
- **Portability / Section 7.6**: full Pyright diagnostic parity remains partial; structural policy tests exist in `tests/development_tools/test_pyright_config_paths.py`, while diagnostic-count parity is optional via `PYRIGHT_ERROR_COUNT_MAX_DELTA` / `PYRIGHT_WARNING_COUNT_MAX_DELTA`.
- **Section 4.1 external tools**: Bandit and pip-audit are integrated and currently clean; remaining evaluation is optional/manual expansion for Radon, pydeps, vulture, deeper Ruff usage, and pre-commit.
- **Section 5.x low-priority gap tools**: unused-imports analyzer/report exist but fixer/categorization remains open; documentation overlap is tuned but reopenable on new noise; TODO sync has dry-run/apply/manual-review guidance, with broader workflow polish optional; memory profiler integration is pending.
- **Section 1.1 `test_config.json` fixture migration**: adopt `tests/development_tools/test_config.json` when touching analyzer tests; full migration remains low priority.
Detail: [AI_DEV_TOOLS_IMPROVEMENT_PLAN_V6.md](development_tools/AI_DEV_TOOLS_IMPROVEMENT_PLAN_V6.md).

**Use / fit** (2026-05-21 status): System AI overhaul is complete; post-overhaul AI quality work is **ACTIVE** ([PLANS.md](development_docs/PLANS.md) Section 5.0.1). Project-specific script ownership remains high/medium. Performance monitoring still includes RAM/caching. Duplicate-list and backup-audit ideas live in dev-tools V5 Sections 7.8/7.9. Completed dev-tools migrations, `--dev-tools-only` report scoping, headless/email admin status, and `sent_messages` fixes are tracked in changelogs rather than active TODOs.

## High Priority

No active high-priority TODOs are currently tracked here. Keep completed architecture-review decisions in changelogs and architecture guides, not in this file.

## Medium Priority

### User data (versioned schemas)

**Plan: versioned v2-style schemas for profile JSON (account, preferences, schedules, context)**
- *What it means*: Today `account.json`, `preferences.json`, `schedules.json`, and `user_context.json` are validated mainly through tolerant `core/schemas.py` (and related helpers) on the normal load/save path, while tasks, notebook, check-ins, message templates, and deliveries use strict `schema_version` v2 envelopes. **This task is planning only:** produce a written plan (for example a new subsection in [PLANS.md](development_docs/PLANS.md) or an appendix in [USER_DATA_MODEL.md](core/USER_DATA_MODEL.md)) for how to introduce versioned v2 envelopes for those remaining files (migration steps, backward compatibility, whether `validate_v2_document` grows a dispatcher or profile types live beside envelopes, test and rollback strategy) **without implementing the migration yet.**
- *Why it helps*: One clear mental model for on-disk contracts, easier tooling and audits, and explicit migration boundaries instead of indefinite tolerant-only profile shapes.
- *Estimated effort*: Small for the **plan document**; Large for a future execution pass (separate tasks after the plan exists).
- *Created*: 2026-05-01
- *Subtasks*:
  - [ ] Draft the plan doc (scope each file, target envelope shape, compatibility with existing `core/schemas.py` consumers).
  - [ ] List open questions (e.g. `user_context.json` not in `core/schemas.py` today; schedules vs `schedule_document_defaults`; single vs split modules).
  - [ ] After review, split follow-up implementation tasks (not part of this item).

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

**Improve Natural Language Processing (NLP) Accuracy** - *Active (post-overhaul; [PLANS.md](development_docs/PLANS.md) Section 5.0.1)*
- *What it means*: Refine parsing patterns and thresholds to better recognize intents and entities. NLP = how the system interprets user commands and natural language (e.g., "create a task to buy milk" -> task creation intent).
- *Why it helps*: More reliable command understanding and fewer misinterpretations
- *Estimated effort*: Medium

**Conversation Flow Management**
- *What it means*: Improve conversational state transitions and fallbacks to keep interactions smooth
- *User priority*: Medium.
- *Why it helps*: More predictable user experience and fewer dead-ends
- *Estimated effort*: Medium

### Performance Optimizations

**Optimize AI Response Times** - *Active (post-overhaul; profile cache/timeouts on hot paths)*
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

### Post-overhaul AI (active - see PLANS.md Section 5.0.1)

**AI Chatbot Actionability Sprint** - *Active (post-overhaul)*
- *What it means*: Improve AI chat quality and enable robust task/message/profile CRUD, with awareness of recent automated messages and targeted, non-conflicting suggestions.
- *Why it helps*: Addresses the user's biggest friction and increases real utility.
- *Estimated effort*: Large
- *Remaining*: Live LM Studio review of conversational replies under `tests/ai/run_ai_functionality_tests.py` (static boundaries shipped 2026-05-22). Shipped 2026-05-21: feature-flag audit, `is_automated_messages_enabled()`, gating in `ai/conversational_context/`; shipped 2026-05-22: [`ai/conversational_context/action_boundaries.py`](ai/conversational_context/action_boundaries.py), ACTION BOUNDARIES instructions, [`tests/behavior/test_conversational_action_boundaries.py`](tests/behavior/test_conversational_action_boundaries.py) - see [SYSTEM_AI_GUIDE.md](ai/SYSTEM_AI_GUIDE.md) Section 4.3.

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

**Add Performance Monitoring**
- *What it means*: Track how long operations take across subsystems. Includes: Python worker memory usage, LM Studio model residency in RAM, Windows file cache behavior during large test runs. Identify safe optimizations without reducing usability.
- *Why it helps*: Helps identify and fix performance problems proactively
- *Estimated effort*: Medium

**Investigate naive vs timezone-aware datetime usage in scheduler & task reminders**
Context: During the datetime canonicalization audit, a potential split was identified between:
- **Timezone-aware datetimes** (e.g., `pytz.localize(...)`) used in parts of `scheduler/manager.py`, and
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
