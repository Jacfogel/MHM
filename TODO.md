# TODO.md - MHM Project Tasks

> **File**: `TODO.md`
> **Audience**: Human Developer (Beginner Programmer) and AI collaborators
> **Purpose**: Current development priorities and planned improvements
> **Style**: Organized, actionable, beginner-friendly
> **Last Updated**: 2026-10-28 (OpenAI provider migration)
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
**Note**: Development tools V6 plan is **archived**: [AI_DEV_TOOLS_IMPROVEMENT_PLAN_V6.md](archive/AI_DEV_TOOLS_IMPROVEMENT_PLAN_V6.md). Extraction (logical split, later sibling repo): [PLANS.md](development_docs/PLANS.md) Section 6.4. Live triage: [`AI_PRIORITIES.md`](development_tools/AI_PRIORITIES.md).
**Testing Source of Truth**: All testing roadmap items are tracked in [TEST_PLAN.md](development_docs/TEST_PLAN.md). Keep only non-testing TODO items here. Coverage-growth follow-ups from this session are tracked in TEST_PLAN Phase 5.7.
**Legacy/Deprecation Source of Truth**: Align legacy cleanup with `development_tools/config/jsons/DEPRECATION_INVENTORY.json` and [AI_LEGACY_COMPATIBILITY_GUIDE.md](ai_development_docs/AI_LEGACY_COMPATIBILITY_GUIDE.md). Historical notes: archived V6 section 5.6.

**Parallel product work (from audits)**: After `audit --full` (and `coverage` when metrics need refresh), use [`development_tools/AI_PRIORITIES.md`](development_tools/AI_PRIORITIES.md) for coverage, duplicates, coupling, and complexity.

**Development tools (reviewed 2026-09-13 - extraction active)**
- **Live triage**: generated [`AI_PRIORITIES.md`](development_tools/AI_PRIORITIES.md) + `python development_tools/run_development_tools.py coverage` when metrics need refresh.
- **Extraction**: logical split in this repo first, sibling repo later. Detail in [PLANS.md](development_docs/PLANS.md) Section 6.4. Pytest config is isolated (`development_tools/pytest.ini`); test files still live under `tests/development_tools/`.
- **Deferred residual from V6**: **B-016** full arbitrary audit scope (Tier 3/static/pytest/coverage still unsupported beyond `--audit-scope` MVP).
- **History**: [AI_DEV_TOOLS_IMPROVEMENT_PLAN_V6.md](archive/AI_DEV_TOOLS_IMPROVEMENT_PLAN_V6.md).

**Use / fit** (2026-10-19 status): System AI overhaul is complete. Prompt tuning, response-quality work, NLP expansion, and live tone review are deferred until separately selected following the OpenAI migration. Cost-aware optional AI is **ACTIVE** ([PLANS.md](development_docs/PLANS.md) Section 5.0.1). Project-specific script ownership remains high/medium. Completed dev-tools migrations, `--dev-tools-only` report scoping, headless/email admin status, and `sent_messages` fixes are tracked in changelogs rather than active TODOs.

## High Priority

### Optional AI controls

**Finish configurable low-cost AI mode** - Keep all core behavior deterministic while making every model-backed feature explicitly optional.
- *Created*: 2026-10-19
- *What it means*: The central policy, desktop admin global/feature controls, and explicit Discord task-breakdown action have shipped. Next, consider manual-only configuration semantics around that real trigger, and keep the policy provider-neutral now that OpenAI replaces LM Studio.
- *Why it helps*: MHM can stay useful without paid model calls, and a future provider cannot silently become required for commands, reminders, or recovery behavior.
- *Estimated effort*: Medium
- *Remaining*:
  - [ ] Add manual-only policy semantics around Discord's explicit **Break down with AI** action; global off and feature disables must remain authoritative.
  - [ ] Keep provider billing, budgets, and price tracking out of MHM; use the provider's own controls.
  - [ ] Preserve deterministic fallbacks and avoid cached AI responses whenever a feature is disabled.

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

### Performance Optimizations

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
- *What it means*: Track how long operations take across subsystems. Includes: Python worker memory usage, Windows file cache behavior during large test runs. Identify safe optimizations without reducing usability.
- *Why it helps*: Helps identify and fix performance problems proactively
- *Estimated effort*: Medium
