# MHM Development Plans

> **File**: `development_docs/PLANS.md`  
> **Audience**: Human Developer & AI Collaborators  
> **Purpose**: Top-level index for active, delegated, deferred, and completed MHM planning work  
> **Style**: Concise, current, action-oriented  
> **Last Updated**: 2026-05-18  
> **Children**: [TEST_PLAN.md](TEST_PLAN.md), [TASKS_PLAN.md](TASKS_PLAN.md), [NOTES_PLAN.md](NOTES_PLAN.md), and [AI_DEV_TOOLS_IMPROVEMENT_PLAN_V6.md](../development_tools/AI_DEV_TOOLS_IMPROVEMENT_PLAN_V6.md)  
> **History**: [AI_DEV_TOOLS_IMPROVEMENT_PLAN_V4.md](../archive/AI_DEV_TOOLS_IMPROVEMENT_PLAN_V4.md) and prior changelog entries remain the historical record.

---

## 1. Role of This File

`PLANS.md` is the **top-level planning index** for MHM.

Use this file to answer:

- What major plans exist?
- Which plans are active now?
- Where does detailed work belong?
- Which old plans are completed, archived, or deferred?

Do **not** use this file as a dumping ground for long implementation checklists. Detailed work belongs in the child plan files, `TODO.md`, generated audit reports, or changelogs.

---

## 2. Sources of Truth

| Area | Source of truth |
|------|-----------------|
| Standalone tasks | [TODO.md](../TODO.md) |
| Testing roadmap | [TEST_PLAN.md](TEST_PLAN.md) |
| Task-system roadmap | [TASKS_PLAN.md](TASKS_PLAN.md) |
| Notebook roadmap | [NOTES_PLAN.md](NOTES_PLAN.md) |
| AI/dev-tools roadmap | [AI_DEV_TOOLS_IMPROVEMENT_PLAN_V6.md](../development_tools/AI_DEV_TOOLS_IMPROVEMENT_PLAN_V6.md) |
| Current audit status | [AI_STATUS.md](../development_tools/AI_STATUS.md) |
| Generated priority queue | [AI_PRIORITIES.md](../development_tools/AI_PRIORITIES.md) |
| Detailed session history | [CHANGELOG_DETAIL.md](CHANGELOG_DETAIL.md) and [AI_CHANGELOG.md](../ai_development_docs/AI_CHANGELOG.md) |
| Architecture/data model references | [CONFIGURATION_REFERENCE.md](../CONFIGURATION_REFERENCE.md) and [USER_DATA_MODEL.md](../core/USER_DATA_MODEL.md) |

---

## 3. Status Vocabulary

Use these statuses consistently across plan files:

- **ACTIVE** - current work or near-term follow-up.
- **PLANNED** - accepted future work, but not the current focus.
- **DEFERRED** - intentionally postponed until a dependency, priority shift, or usage signal changes.
- **MONITORING** - no active implementation; watch logs, audits, or live behavior.
- **COMPLETED** - done; keep detail in changelogs, not active plans.
- **ARCHIVED** - old plan retained only as historical context.

Avoid mixed status labels such as `MOSTLY COMPLETE`, `[WARNING]`, `FUTURE CONSIDERATION`, or `PARTIALLY COMPLETE` in new planning sections. If nuance is needed, put it in a short note under one of the statuses above.

---

## 4. Current Active Plan Index

| Plan | Status | Priority | Where details live | Current focus |
|------|--------|----------|--------------------|---------------|
| Flow/check-in scheduled-send stability | **ACTIVE / MONITORING** | High | This file + spec | Live Discord validation, retry/cooldown observation, log review |
| Error handling quality | **ACTIVE** | Medium | This file + [AI_ERROR_HANDLING_GUIDE.md](../ai_development_docs/AI_ERROR_HANDLING_GUIDE.md) | Better user/log messages and recovery guidance |
| Notebook system | **ACTIVE** | High | [NOTES_PLAN.md](NOTES_PLAN.md) | Live validation, edit sessions, command discovery, group ambiguity, bulk organization |
| Task system | **ACTIVE** | High | [TASKS_PLAN.md](TASKS_PLAN.md) | Broader natural-language task creation, templates, notes/links, Discord validation |
| Test program | **ACTIVE** | High | [TEST_PLAN.md](TEST_PLAN.md) | Reliability, log isolation, domain markers, policy tests, coverage growth |
| AI development tools | **ACTIVE** | Medium | [AI_DEV_TOOLS_IMPROVEMENT_PLAN_V6.md](../development_tools/AI_DEV_TOOLS_IMPROVEMENT_PLAN_V6.md) | Dev-tools coverage slices, marker/domain work, portability follow-ups |
| System AI overhaul | **ACTIVE** | High | [SYSTEM_AI_OVERHAUL_PLAN.md](../ai/SYSTEM_AI_OVERHAUL_PLAN.md) | Phase 5: collapse thin `chatbot.py` delegates; Phases 1-4 done |

---

## 5. Active Top-Level Plans

### 5.0 System AI overhaul (interaction-type separation)

**Status**: **ACTIVE**  
**Priority**: High  
**Started**: 2026-05-18  
**Spec**: [SYSTEM_AI_OVERHAUL_PLAN.md](../ai/SYSTEM_AI_OVERHAUL_PLAN.md)

**Use / fit**: Separate conversational, command-interpretation, clarification, and fallback AI paths without a new orchestration framework. Deterministic handlers remain authoritative for execution.

**Completed 2026-05-18 (Phases 1-4)**:

- `ai/interaction_types.py`, `ai/fallback_responses/` (package), `ai/command_interpreter.py`, `ai/response_generator.py`, `ai/command_registry.py`; `ai/chatbot.py` remains the facade.
- Clarification command prompt suffix; dynamic command intent list from `get_rule_based_intent_names()`.
- Boundary unit tests under `tests/unit/test_fallback_responses.py`, `test_command_interpreter.py`, `test_command_registry.py`.

**Next (Phase 5 - collapse facade delegates):**

- Inline calls in `ai/chatbot.py` to `get_fallback_responses()`, `get_command_interpreter()`, and `get_response_generator()`; remove one-line private delegates (`_get_contextual_fallback`, `_detect_mode`, `_create_comprehensive_context_prompt`, etc.).
- Update tests that call `bot._detect_mode` / similar to target the canonical modules where appropriate.
- Keep `get_ai_chatbot()` and public generate/status methods as the stable API for `communication/` (see overhaul plan Section 8.1). This is refactor completion, not `# LEGACY COMPATIBILITY` removal.

**Later follow-ups** (see overhaul plan Section 8.1): deeper `ContextBuilder` / `response_generator` deduplication; AI Chatbot Actionability Sprint and NLP accuracy work in [TODO.md](../TODO.md).

---

### 5.1 Flow/check-in scheduled-send stability

**Status**: **ACTIVE / MONITORING**  
**Priority**: High  
**Started**: 2026-02-22  
**Spec**: [discord-checkin-flow.md](../specs/discord-checkin-flow.md)

**Use / fit**: Stability is critical. Check-ins and scheduled sends work well enough day to day, but reliability and debugging matter most: selecting the right number of questions from the right lists, responding dynamically, saving results properly, and supporting flexible response formats.

**Completed baseline**:

- Deferral and cooldown behavior implemented in runtime.
- One-time retry scheduling implemented.
- Unit/behavior coverage exists for the February 2026 stability slice.

**Remaining work**:

- [ ] Live Discord manual validation for active-flow deferral, 10-minute cooldown, and retry behavior.
- [ ] Monitor logs for legacy warnings in check-in flow paths.
- [ ] Monitor `MESSAGE_SELECTION` diagnostics.
- [ ] Move recurring concrete follow-ups to [TODO.md](../TODO.md) if they become standalone tasks.

---

### 5.2 Error handling quality

**Status**: **ACTIVE**  
**Priority**: Medium  
**Started**: 2025-11-20

**Use / fit**: Error-handling validation helps because this is a beginner/AI-assisted codebase. The practical goal is not theoretical perfection; it is clearer failures, less noisy logs, and better user-facing messages.

**Completed baseline**:

- Error-handling audit tooling exists.
- Current Phase 1/2 audit queues have been reduced in prior quick-audit cycles.
- Coverage status is tracked through generated reports rather than copied here.

**Remaining work**:

- [ ] Improve user-facing error messages where failures are currently vague or cryptic.
- [ ] Improve log messages where failures lack enough context to debug quickly.
- [ ] Add recovery strategies only where they are actually useful.
- [ ] Add structured context payloads where they reduce debugging time.
- [ ] Review direct `handle_error` calls when generated reports surface them.

**Reference**: [AI_ERROR_HANDLING_GUIDE.md](../ai_development_docs/AI_ERROR_HANDLING_GUIDE.md)

---

## 6. Delegated Active Plans

These plans should not be duplicated in detail here.

### 6.1 Notebook system

**Status**: **ACTIVE**  
**Priority**: High  
**Detailed plan**: [NOTES_PLAN.md](NOTES_PLAN.md)

**Current focus**:

- Live validation of implemented notebook behavior.
- Edit sessions for longer note editing from Discord/mobile.
- Better command discovery and help text.
- Group command ambiguity cleanup.
- Bulk organization commands only after core use feels reliable.

---

### 6.2 Task system

**Status**: **ACTIVE**  
**Priority**: High  
**Detailed plan**: [TASKS_PLAN.md](TASKS_PLAN.md)

**Current focus**:

- Broader natural-language task creation beyond recurring-task basics.
- Templates and quick actions.
- Task notes/links/attachments.
- Live Discord validation for task creation and follow-up flows.

---

### 6.3 Test program

**Status**: **ACTIVE**  
**Priority**: High  
**Detailed plan**: [TEST_PLAN.md](TEST_PLAN.md)

**Current focus**:

- Full-audit reliability.
- Test artifact/log isolation.
- Domain-attribution pytest markers.
- Static policy tests for time utilities, user-data JSON access, and core/UI boundaries.
- No-parallel marker reduction only when stability is preserved.
- Coverage growth in high-value domains.

---

### 6.4 AI development tools

**Status**: **ACTIVE**  
**Priority**: Medium  
**Detailed plan**: [AI_DEV_TOOLS_IMPROVEMENT_PLAN_V6.md](../development_tools/AI_DEV_TOOLS_IMPROVEMENT_PLAN_V6.md)

**Current focus**:

- Use live generated reports before choosing the next slice.
- Keep dev-tools coverage improvements small and targeted.
- Coordinate domain-marker analyzer work with [TEST_PLAN.md](TEST_PLAN.md).
- Keep pip-audit/watch items in monitoring unless a trusted fix or explicit policy decision exists.

---

## 7. Deferred / Low-Priority Plans

These are real ideas, but they are **not current implementation priorities**.

### 7.1 Discord app/bot capabilities exploration

**Status**: **DEFERRED**  
**Priority**: Low

**Use / fit**: Discord is the main interface and better buttons/menus matter, but this should stay planning-only until core notebook/task/check-in flows are reliable.

**Keep for later**:

- Research user-installable app features and limitations.
- Review interaction types: slash commands, buttons, modals, select menus.
- Review permissions, OAuth scopes, rate limits, and formatting options.
- Identify a small list of Discord features that would directly improve MHM.

---

### 7.2 Mood-aware support calibration

**Status**: **DEFERRED**  
**Priority**: High once foundational work is stable

**Use / fit**: This is important for long-term usefulness: gentler support when mood/energy is low, less nagging when overwhelmed, and better action suggestions based on state.

**Why deferred**:

- It depends on more reliable check-ins, task usage, and AI/prompt architecture.
- It overlaps with future task context, reminder tone, and AI overhaul work.

**Keep for later**:

- Safety-net prompt language.
- Mood/energy-to-reminder mapping.
- Quiet/unavailable mode rules.
- Mood re-evaluation triggers and cooldowns.
- Low-energy task suggestions.

---

### 7.3 Message analytics, deduplication, and proactive intelligence

**Status**: **DEFERRED / MONITORING**  
**Priority**: Low/Medium

**Completed baseline**:

- Message frequency analytics foundation exists and was documented in prior changelog history.

**Why deferred**:

- Analytics, A/B testing, ML-style personalization, and predictive scheduling are overbuilt for the current 1-2 user reality.
- The practical near-term desire is more personalized and time-appropriate messages, not a full analytics platform.

**Keep for later**:

- User engagement tracking.
- Message effectiveness metrics.
- Smart message recommendation.
- Adaptive spacing/timing.
- Proactive suggestions based on check-in/task patterns.

---

### 7.4 UI polish and validation

**Status**: **DEFERRED / OPPORTUNISTIC**  
**Priority**: Low

**Completed baseline**:

- PySide6/Qt migration foundation completed.
- Dialogs and widgets exist.
- Main UI behavior coverage exists.

**Why deferred**:

- Discord is the primary interface.
- UI improvements are worthwhile when they unblock real use or stabilize tests, but they should not displace Discord/mobile flows.

**Keep for later**:

- Dialog sizing/spacing polish.
- Main-window refresh after dialog changes.
- Form validation improvements.
- Clearer UI error messages.
- UI responsiveness monitoring.

Testing details belong in [TEST_PLAN.md](TEST_PLAN.md).

---

### 7.5 Cross-channel sync

**Status**: **DEFERRED**  
**Priority**: Low

**Completed baseline**:

- Email integration was completed and documented in changelog history.

**Why deferred**:

- Discord is primary.
- Cross-channel sync is not currently important enough to compete with notebook/task/check-in reliability.

**Keep for later**:

- Synchronize state across Discord, email, and future channels if multi-channel usage grows.
- Keep Telegram out of scope unless explicitly revived.

---

### 7.6 Smart home integration

**Status**: **ARCHIVED / FUTURE ONLY**  
**Priority**: None currently

This remains a long-term idea from the broader project vision, not a current MHM implementation plan.

---

## 8. Completed / Archived Plans

Keep details in changelogs, not here.

| Plan / workstream | Status | Notes |
|-------------------|--------|-------|
| MHM Refactor Continuation Plan | **COMPLETED** | Completed 2026-05-05; removed from active planning. |
| Runtime JSON storage classification/migration/service flag cleanup | **COMPLETED** | Completed 2026-05-11; follow-ups belong in TODO or storage docs. |
| Soft channel-boundary review | **COMPLETED** | Completed 2026-05-11; future boundary policy belongs in TEST_PLAN/TODO. |
| Backup Reliability and Restore Confidence Plan | **COMPLETED** | Completed 2026-05-11; future issues should become specific TODO items. |
| Top-level storage package move | **COMPLETED** | Completed 2026-05-14; `storage/` is the current package for user-data persistence helpers. |
| Account management system improvements | **ARCHIVED** | Core account creation and feature enablement complete; remaining edge cases belong in TODO. |
| UI migration foundation/dialogs/widgets | **COMPLETED** | UI polish/testing remains deferred/opportunistic. |
| Email integration | **COMPLETED** | Cross-channel sync remains deferred. |
| Testing strategy consolidation | **COMPLETED AS CONSOLIDATION** | Current testing roadmap lives in TEST_PLAN.md. |

---

## 9. Plan Maintenance Rules

When updating plans:

1. Keep `PLANS.md` as an index, not a long backlog.
2. Put detailed roadmap items in the relevant child plan.
3. Put small standalone tasks in [TODO.md](../TODO.md).
4. Move completed implementation history to changelogs.
5. Use live generated reports for metrics instead of copying stale counts into plan files.
6. Use current package/module names from the codebase; do not preserve old paths for nostalgia.
7. Add dates to new items and status changes using `YYYY-MM-DD`.
8. When a plan becomes mostly completed, collapse it here and move remaining concrete work to the correct child plan or TODO.

---

## 10. Next Review Checklist

Use this checklist during the next planning cleanup:

- [ ] Confirm all child links still resolve.
- [ ] Confirm `PLANS.md` still references V6, not V5, for AI development tools.
- [ ] Confirm completed work is not re-expanded into active sections.
- [ ] Confirm deferred items still deserve to exist.
- [ ] Confirm active plan summaries match their child plans.
- [ ] Confirm generated reports, not copied metrics, are used for current audit/coverage status.
