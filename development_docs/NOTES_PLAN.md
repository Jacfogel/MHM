# MHM Notebook Roadmap

> **File**: `development_docs/NOTES_PLAN.md`  
> **Audience**: Human Developer & AI Collaborators  
> **Purpose**: Current roadmap for the notebook feature  
> **Style**: Actionable, checklist-focused, concise  
> **Last Updated**: 2026-11-10
> **Current Evidence**: The six-file automated notebook baseline in Section 5 passed on 2026-11-10 (150 tests). Live Discord checks remain optional when rendering or help changes.
> **Parent**: [PLANS.md](PLANS.md)  
> This plan is subordinate to `development_docs/PLANS.md` and must remain consistent with its standards and terminology.

---

## 1. Role of This File

- **Purpose**: Own the notebook roadmap for daily capture through Discord and the website.
- **Scope**: Track unresolved notebook work, optional live visual checks, and deferred organization, search, edit-review, and event extensions.
- **Priorities**: Keep ordinary capture and retrieval smooth; select extensions only when product needs or usage justify them.
- **Related sources**: Use [PLANS.md](PLANS.md) for the planning index, notebook code/help/tests for current behavior, and [CHANGELOG_DETAIL.md](CHANGELOG_DETAIL.md) for history. Coordinate shared work with [TASKS_PLAN.md](TASKS_PLAN.md); follow the maintenance rules in Section 6.

## 2. Monitoring and Deferred Extensions

**Status**: MONITORING
**Priority**: Low

When Discord rendering or help changes, optionally check Show More styling, expired-button behavior, and discovery through `help notebook` / `examples notebook`. Live checks are visual; use the focused tests in Section 5 for behavior validation.

### 2.1 Bulk organization

**Status**: IMPLEMENTED on the website

Select active notebook entries to add tags, remove tags, or archive them together.

---

## 3. Technical Backlog

### 3.1 Keep search simple unless usage proves otherwise

**Status**: DEFERRED
**Priority**: Low

Current substring search is acceptable for JSON storage.

Do not create `notebook_search.py`, SQLite, or FTS just because the old roadmap mentioned them. Revisit only if one of these becomes true:

- search gets slow with real data
- search ranking becomes important
- fuzzy matching is needed
- notebook and tasks need unified search
- storage moves to SQLite anyway

---

### 3.2 Extract more reusable item organization helpers only when duplication is real

**Status**: DEFERRED
**Priority**: Low / Medium

Old plan proposed:

- `core/item_filters.py`
- `core/item_groups.py`

Do not add these yet just to satisfy the old roadmap. Extract them only when tasks, notebook, and future events are clearly duplicating behavior.

Reuse shared helpers such as `core/tags.py` and `core/pagination.py` if extraction becomes justified.

---

### 3.3 Revisit skip integration only if the product value is clear

**Status**: DEFERRED
**Priority**: Low until clarified

Old idea: if a user repeatedly skips a task reminder, MHM could create a notebook entry tagged `blocker` / linked to the task, or ask “Capture why?”

Do not implement until the desired behavior is clearer.

Questions to answer first:

- Should skipped reminders create notebook entries automatically?
- Should the bot ask before capturing?
- Should this belong to Tasks, Notebook, or a shared reflection/check-in flow?
- How do we avoid making reminders feel more annoying?

---

### 3.4 Notebook edit review mode

**Status**: DEFERRED
**Priority**: Low

A review/confirmation mode for multi-message notebook edits remains deferred. Define whether users need a preview before saving, how they confirm or cancel, and how timeout works before selecting this extension. Replace and append sessions do not by themselves complete this separate idea.

---

## 4. Future Event / Calendar Direction

Notebook can eventually support event-like entries, but do not force that now.

Future options:

- Add `Entry(kind="event")` only if events are simple and notebook-like.
- Create a separate `events/` feature if events grow into scheduling, reminders, recurrence, attendees, or calendar sync.
- Reuse tags, search, and pagination where practical.

---

## 5. Validation Commands

Use focused tests while changing notebook behavior:

```powershell
python -m pytest tests/behavior/test_notebook_handler_behavior.py tests/unit/test_notebook_handler_edge_cases.py tests/unit/test_notebook_handler_pagination_formatting.py tests/unit/test_notebook_list_v2_round_trip.py tests/unit/test_notebook_service.py tests/unit/test_notebook_validation.py -q
```

Use broader validation before merging larger notebook/command-parser changes:

```powershell
python run_tests.py --mode development
python development_tools/run_development_tools.py audit --quick
```

Use full audit when a change touches command routing, shared core helpers, or persistence:

```powershell
python development_tools/run_development_tools.py audit --full
```

---

## 6. Maintenance Rules

Follow the shared [maintenance rules](PLANS.md#10-maintenance-rules) and [status vocabulary](PLANS.md#3-status-vocabulary).

- Keep notebook work here; coordinate shared task/notebook changes with [TASKS_PLAN.md](TASKS_PLAN.md).
- Preserve deliberate product decisions and usage triggers when revising deferred search, organization, edit-review, or event work.

---

## 7. Next Review Checklist

Use this checklist when reviewing or updating this plan; reset it for each review.

- [ ] Verify remaining items against current code, tests, reports, and changelogs; distinguish automated evidence from unverified live behavior.
- [ ] Before removing completed work, preserve any unfinished work, deferred ideas, validation limits, and guardrails in the appropriate surviving section.
- [ ] Remove fully completed items and completion-history lists; keep implementation history in changelogs.
- [ ] Confirm each remaining item's status, priority, scope, and acceptance or revisit criteria are accurate.
- [ ] Confirm links and section references resolve, related plan summaries agree, and current metrics come from generated reports.
- [ ] Confirm optional Discord checks and deferred notebook extensions still have a reason to remain.
