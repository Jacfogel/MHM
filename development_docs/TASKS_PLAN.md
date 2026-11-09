# Task System Improvements Plan

> **File**: `development_docs/TASKS_PLAN.md`  
> **Audience**: Human Developer & AI Collaborators  
> **Purpose**: Current roadmap for task-system usability, Discord task creation, follow-up flows, and advanced task features  
> **Style**: Actionable, checklist-focused, progress-tracked  
> **Last Updated**: 2026-11-07
> **Parent**: [PLANS.md](PLANS.md)  
> This plan is subordinate to `development_docs/PLANS.md` and must remain consistent with its standards and terminology.

## Role of This File

- **Purpose**: Own the task-system roadmap for creating, updating, and following up on tasks.
- **Scope**: Track unresolved task work, optional live validation, and future extensions such as attachments, dependencies, batch operations, and advanced views.
- **Priorities**: Keep task use easy from a phone, with Discord as the primary task interface; select broader extensions when product needs justify them.
- **Related sources**: Use [PLANS.md](PLANS.md) for the planning index, task help/code/tests for current behavior, and [CHANGELOG_DETAIL.md](CHANGELOG_DETAIL.md) for history. Coordinate shared work with [NOTES_PLAN.md](NOTES_PLAN.md); follow the [maintenance rules](#maintenance-rules).

## Monitoring

**Status**: MONITORING
**Priority**: Low

When Discord UI or parsing changes, optionally check task picker/details, creation follow-ups, parsed due dates/titles, template modals, and create-hub buttons. Use [`test_task_list_ui.py`](../tests/communication/test_task_list_ui.py) and the [manual Discord guide](../tests/MANUAL_DISCORD_TEST_GUIDE.md) for the relevant validation paths.

**Current evidence (2026-11-07)**: All 20 task-list UI tests pass, including picker/details, follow-up delegation, account checks, and button callbacks. Windows async setup required local loopback access; the restricted run timed out in `socket.socketpair()` before reaching an async test body. Live rendering and the other optional flows above remain unverified by this focused file.

## Deferred Attachments

**Status**: DEFERRED
**Priority**: Medium

File/image attachments require a selected storage, retention, and Discord upload design before implementation.

## Future Extensions

### 1. Task dependencies / blocked-by relationships

**Status**: PLANNED
**Priority**: Medium

**Implement later**:
- [ ] Add `blocked_by` and `blocks` relationships.
- [ ] Show blocked status in task lists.
- [ ] Automatically unblock when prerequisite tasks are completed.
- [ ] Add tests for circular dependency prevention.

---

### 2. Batch task operations

**Status**: DEFERRED (extensions only; reviewed 2026-11-07)
**Priority**: Low/Medium

- [x] Add tags to selected active tasks from the website.
- [ ] Batch archive, if task archiving is introduced.

---

## Deferred / Long-Term

### Context-aware and mood-aware reminders

**Status**: DEFERRED
**Reason**: Overlaps with the broader mood-aware support plan and should wait until foundational task usage is stronger.

Future ideas:
- location-aware reminders
- calendar-linked reminders

### Smart task suggestions and AI optimization

**Status**: DEFERRED
**Reason**: Broader predictive suggestions and optimization have no selected product slice.

Future ideas:
- suggested tasks based on patterns
- task ordering suggestions
- conflict detection

### Advanced views and analytics

**Status**: DEFERRED
**Reason**: Useful later, not needed before Discord task creation is reliable.

Future ideas:
- calendar view
- kanban view
- additional focus views beyond the shipped Home/backend focus policy
- completion trends
- recurring-task streaks
- overdue priority escalation

### Sync, export, and backup enhancements

**Status**: DEFERRED
**Reason**: Basic task persistence exists; broader sync/backup should align with the storage/user-data roadmap.

Future ideas:
- export/import task data
- cloud sync
- cross-device access
- backup confidence checks specific to task data

---

## Suggested Validation Commands

Use focused tests before and after task-system changes:

```powershell
pytest tests/behavior/test_task_handler_behavior.py tests/behavior/test_command_discovery_help.py tests/unit/test_command_parser_rule_based_patterns_expansion.py -q
pytest tests/unit/test_recurring_tasks.py tests/unit/test_task_service.py tests/unit/test_task_short_ids.py -q
pytest tests/behavior/test_task_reminder_followup_behavior.py tests/integration/test_task_reminder_integration.py -q
```

Before a larger merge, run the normal full project validation/audit path.

## Maintenance Rules

Follow the shared [maintenance rules](PLANS.md#10-maintenance-rules) and [status vocabulary](PLANS.md#3-status-vocabulary).

- Keep task behavior in task/shared modules; reuse existing shared tag and ID helpers for extensions.
- Coordinate health-derived pressure changes with [PLANS.md](PLANS.md#53-deterministic-mood-and-energy-rules) and keep shared task/notebook work consistent with [NOTES_PLAN.md](NOTES_PLAN.md).

---

## Next Review Checklist

Use this checklist when reviewing or updating this plan; reset it for each review.

- [ ] Verify remaining items against current code, tests, reports, and changelogs; distinguish automated evidence from unverified live behavior.
- [ ] Before removing completed work, preserve any unfinished work, deferred ideas, validation limits, and guardrails in the appropriate surviving section.
- [ ] Remove fully completed items and completion-history lists; keep implementation history in changelogs.
- [ ] Confirm each remaining item's status, priority, scope, and acceptance or revisit criteria are accurate.
- [ ] Confirm links and section references resolve, related plan summaries agree, and current metrics come from generated reports.
- [ ] Confirm attachment, dependency, batch, and other deferred extensions still reflect product needs and their dependencies.
