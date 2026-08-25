# TODO.md - MHM Project Tasks

> **File**: `TODO.md`
> **Audience**: Human Developer (Beginner Programmer) and AI collaborators
> **Purpose**: Current development priorities and planned improvements
> **Style**: Organized, actionable, beginner-friendly
> **Last Updated**: 2026-08-25 (retired core/schemas.py; account/preferences/schedules are v2 envelopes in memory)
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
**Note**: Development tools V6 plan is **archived**: [AI_DEV_TOOLS_IMPROVEMENT_PLAN_V6.md](archive/AI_DEV_TOOLS_IMPROVEMENT_PLAN_V6.md). V4/V5 history: [AI_DEV_TOOLS_IMPROVEMENT_PLAN_V4.md](archive/AI_DEV_TOOLS_IMPROVEMENT_PLAN_V4.md), [AI_DEV_TOOLS_IMPROVEMENT_PLAN_V5.md](archive/AI_DEV_TOOLS_IMPROVEMENT_PLAN_V5.md). Live triage: [`AI_PRIORITIES.md`](development_tools/AI_PRIORITIES.md).
**Testing Source of Truth**: All testing roadmap items are tracked in [TEST_PLAN.md](development_docs/TEST_PLAN.md). Keep only non-testing TODO items here. Coverage-growth follow-ups from this session are tracked in TEST_PLAN Phase 5.7.
**Legacy/Deprecation Source of Truth**: Align legacy cleanup with `development_tools/config/jsons/DEPRECATION_INVENTORY.json` and [AI_LEGACY_COMPATIBILITY_GUIDE.md](ai_development_docs/AI_LEGACY_COMPATIBILITY_GUIDE.md). Historical notes: archived V6 section 5.6.

**Parallel product work (from audits)**: After `audit --full` (and `coverage` when metrics need refresh), use [`development_tools/AI_PRIORITIES.md`](development_tools/AI_PRIORITIES.md) for coverage, duplicates, coupling, and complexity.

**Development tools (reviewed 2026-07-28 - V6 archived)**
- **Live triage**: generated [`AI_PRIORITIES.md`](development_tools/AI_PRIORITIES.md) + `python development_tools/run_development_tools.py coverage` when metrics need refresh.
- **Deferred residual from V6**: **B-016** full arbitrary audit scope (Tier 3/static/pytest/coverage still unsupported beyond `--audit-scope` MVP). Detail in [PLANS.md](development_docs/PLANS.md) Section 6.4 and archived [V6 Section 3.6](archive/AI_DEV_TOOLS_IMPROVEMENT_PLAN_V6.md).
- **Maintenance only**: reopen B-001/B-003-B-008 style work only on regression/noise; see archived V6 backlog register.
- **History**: [AI_DEV_TOOLS_IMPROVEMENT_PLAN_V6.md](archive/AI_DEV_TOOLS_IMPROVEMENT_PLAN_V6.md).

**Use / fit** (2026-05-21 status): System AI overhaul is complete; post-overhaul AI quality work is **ACTIVE** ([PLANS.md](development_docs/PLANS.md) Section 5.0.1). Project-specific script ownership remains high/medium. Performance monitoring still includes RAM/caching. Duplicate-list and backup-audit ideas live in dev-tools V5 Sections 7.8/7.9. Completed dev-tools migrations, `--dev-tools-only` report scoping, headless/email admin status, and `sent_messages` fixes are tracked in changelogs rather than active TODOs.

## High Priority

No active high-priority TODOs are currently tracked here. Keep completed architecture-review decisions in changelogs and architecture guides, not in this file.

## Medium Priority

### Integrations / refactor hygiene

**Google Health deferred leftovers (from archived plan)** - Optional follow-ups after V0/V1 ship; not required for personal use. Live monitoring checklist is in [GOOGLE_HEALTH_GUIDE.md](integrations/google_health/GOOGLE_HEALTH_GUIDE.md). Historical plan: [HEALTH_INTEGRATION_PLAN.md](archive/HEALTH_INTEGRATION_PLAN.md).
- *Created*: 2026-07-28
- *Estimated effort*: Small-Medium (pick items as needed)
- *Candidates*:
  - Admin UI "Sync now" (Discord `sync health` / CLI already cover debug)
  - `preferences.json` -> `health_personalization` (`use_in_messages` / `use_in_chat`); today account feature flag only
  - Populate `google_user_id` via `getIdentity` on connect
  - Larger API `pageSize` for non-sleep types; configurable baseline window in `signal_builder.py`
  - Doc gaps: Google Health mock section in [TESTING_GUIDE.md](tests/TESTING_GUIDE.md); health context note in [SYSTEM_AI_GUIDE.md](ai/SYSTEM_AI_GUIDE.md)

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
- *Remaining*: Live LM Studio review of **tone and phrasing** only (categories 1, 2, 11). Safety/honesty on a real model is T-18.x in [`tests/ai/test_ai_live_journeys.py`](tests/ai/test_ai_live_journeys.py). Mocked journeys: [`tests/behavior/test_ai_user_journeys.py`](tests/behavior/test_ai_user_journeys.py). Shipped 2026-05-21: feature-flag audit, `is_automated_messages_enabled()`, gating in `ai/context/`; shipped 2026-05-22: [`ai/chat/action_boundaries.py`](ai/chat/action_boundaries.py), ACTION BOUNDARIES instructions, [`tests/behavior/test_conversational_action_boundaries.py`](tests/behavior/test_conversational_action_boundaries.py) - see [SYSTEM_AI_GUIDE.md](ai/SYSTEM_AI_GUIDE.md) Section 4.3.

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
