# MHM Development Plans

> **File**: `development_docs/PLANS.md`  
> **Audience**: Human Developer & AI Collaborators  
> **Purpose**: Top-level index for unresolved active, monitoring, planned, and deferred MHM work
> **Style**: Concise, current, action-oriented  
> **Last Updated**: 2026-11-12
> **Children**: [TEST_PLAN.md](TEST_PLAN.md), [TASKS_PLAN.md](TASKS_PLAN.md), [NOTES_PLAN.md](NOTES_PLAN.md)  
> **History**: [AI_DEV_TOOLS_IMPROVEMENT_PLAN_V6.md](../archive/AI_DEV_TOOLS_IMPROVEMENT_PLAN_V6.md) (archived), [HEALTH_INTEGRATION_PLAN.md](../archive/HEALTH_INTEGRATION_PLAN.md) (archived), [AI_DEV_TOOLS_IMPROVEMENT_PLAN_V5.md](../archive/AI_DEV_TOOLS_IMPROVEMENT_PLAN_V5.md), [AI_DEV_TOOLS_IMPROVEMENT_PLAN_V4.md](../archive/AI_DEV_TOOLS_IMPROVEMENT_PLAN_V4.md), and changelogs.

---

## 1. Role of This File

- **Purpose**: Provide the top-level planning index for MHM: which plans exist, their current status, and where detailed work belongs.
- **Scope**: Track unresolved cross-cutting work and short summaries of child plans, including accepted future work and intentionally deferred ideas.
- **Priorities**: Keep ownership and status clear so the next work can be selected from current evidence.
- **Related sources**: Keep detailed roadmaps in their child plans and small standalone tasks in [TODO.md](../TODO.md). Use the sources in Section 2 for implementation references, live metrics, and changelog history. Maintenance rules are in Section 10.

---

## 2. Sources of Truth

| Area | Source of truth |
|------|-----------------|
| Standalone tasks | [TODO.md](../TODO.md) |
| Testing roadmap | [TEST_PLAN.md](TEST_PLAN.md) |
| Task-system roadmap | [TASKS_PLAN.md](TASKS_PLAN.md) |
| Notebook roadmap | [NOTES_PLAN.md](NOTES_PLAN.md) |
| AI/dev-tools roadmap | Archived [V6](../archive/AI_DEV_TOOLS_IMPROVEMENT_PLAN_V6.md); live triage [AI_PRIORITIES.md](../development_tools/AI_PRIORITIES.md) |
| Dev-tools list/config canonical sources | [LIST_OF_LISTS.md](../development_tools/LIST_OF_LISTS.md) (arrays, mappings, enumerated sets - not planning ownership) |
| Product/runtime list canonical sources | [PRODUCT_LIST_OF_LISTS.md](PRODUCT_LIST_OF_LISTS.md) (commands, prompts, categories, channels) |
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
- Completed work is removed from plans; keep its history in changelogs.
- **ARCHIVED** - old plan retained only as historical context.

Avoid mixed status labels such as `MOSTLY COMPLETE`, `[WARNING]`, `FUTURE CONSIDERATION`, or `PARTIALLY COMPLETE` in new planning sections. If nuance is needed, put it in a short note under one of the statuses above.

---

## 4. Current Plan Index

| Plan | Status | Priority | Where details live | Current focus |
|------|--------|----------|--------------------|---------------|
| Flow/check-in scheduled-send stability | **MONITORING** | Low | This file + spec | Live Discord validation, retry/cooldown observation, log review |
| Error handling quality | **ACTIVE** | Medium | This file + [AI_ERROR_HANDLING_GUIDE.md](../ai_development_docs/AI_ERROR_HANDLING_GUIDE.md) | Better user/log messages and recovery guidance |
| Notebook system | **MONITORING** | Low | [NOTES_PLAN.md](NOTES_PLAN.md) | Shipped baseline; optional live visual checks when UI changes; extensions deferred |
| Task system | **MONITORING** | Low | [TASKS_PLAN.md](TASKS_PLAN.md) | Shipped capabilities; optional live validation; future extensions await selection |
| Test program | **ACTIVE** | High | [TEST_PLAN.md](TEST_PLAN.md) | Complete-suite Windows reliability, log isolation, coverage growth |
| Deterministic mood and energy rules | **MONITORING** | Low | This file Section 5.3 | Observe health-derived pressure transitions; additional timer awaits usage evidence |
| Appropriate coupling reductions | **ACTIVE** | Medium | This file Section 5.0.2 + [AI_PRIORITIES.md](../development_tools/AI_PRIORITIES.md) | Fix inverted edges only; leave legitimate hubs alone |
| SMS channel | **PLANNED** | Later | This file Section 7.1 | Paid SMS adapter beside Discord and email; text replies for check-ins and tasks |
| Apple Health ingest | **PLANNED** | Later | This file Section 7.2 | Phone-pushed daily summaries beside Google Health |

---

## 5. Active Top-Level Plans

### 5.0.2 Appropriate coupling reductions

**Status**: **ACTIVE**  
**Priority**: Medium  
**Started**: 2026-08-11  
**Audit signal**: [AI_PRIORITIES.md](../development_tools/AI_PRIORITIES.md) item "Reduce dependency pattern risk"

**Triage rubric**: High-coupling audit flag = unique local fan-out **> 10**, excluding package `__init__.py` re-export hubs. Legitimate composition hubs (orchestrator, chatbot, interaction_manager, `core.service`) keep their fan-out. Fix only **inappropriate** edges (wrong direction, private-API reach, domain -> composition-root locators).

**Later candidates** (not automatic refactors): storage -> feature-domain managers; duplicated multi-domain reads in `ai/context`; optional delivery ownership for AI personalized send only if ownership pressure appears; optional hub vs inappropriate-edge classification in the analyzer.

**Additional deferred cleanup candidates**:

- Consider direct imports from `storage/user_data_index.py` for high-traffic `update_user_index` callers only if ownership or dependency pressure justifies the change; do not reopen the completed facade split.
- `ai/context/phraser.py` still has the test helper `append_checkin_summary(parts, user_id)` loading rows by user ID. Consider moving those tests to envelope-based inputs only if this helper causes duplication or maintenance pressure; production chat already uses envelope wrappers.


---

### 5.1 Flow/check-in scheduled-send stability

**Status**: **MONITORING**
**Priority**: Low
**Started**: 2026-02-22  
**Spec**: [discord-checkin-flow.md](../specs/discord-checkin-flow.md)

**Use / fit**: Stability is critical. Check-ins and scheduled sends work well enough day to day, but reliability and debugging matter most: selecting the right number of questions from the right lists, responding dynamically, saving results properly, and supporting flexible response formats.

**Remaining work**:

- Optional live Discord observation of active-flow deferral, 10-minute cooldown, and retry behavior when delivery/flow behavior changes. Use the [manual Discord guide](../tests/MANUAL_DISCORD_TEST_GUIDE.md) for visual checks and the focused automated tests for behavior validation.
- [ ] Monitor logs for legacy warnings in check-in flow paths.
- [ ] Monitor `MESSAGE_SELECTION` diagnostics.
- [ ] Move recurring concrete follow-ups to [TODO.md](../TODO.md) if they become standalone tasks.

---

### 5.2 Error handling quality

**Status**: **ACTIVE**  
**Priority**: Medium  
**Started**: 2025-11-20

**Use / fit**: Error-handling validation helps because this is a beginner/AI-assisted codebase. The practical goal is not theoretical perfection; it is clearer failures, useful but not overly noisy logs, and better user-facing messages.

**Remaining work**:

- [ ] Improve user-facing error messages where failures are currently vague or cryptic.
- [ ] Improve log messages where failures lack enough context to debug quickly.
- [ ] Add recovery guidance where users can act on it. For partial failures like a saved task snooze with no scheduled alert, keep the saved state explicit and avoid suggesting a retry that could record a second action.
- [ ] Add structured context payloads where they reduce debugging time.
- [ ] Review direct `handle_error` calls when generated reports surface them.

**Reference**: [AI_ERROR_HANDLING_GUIDE.md](../ai_development_docs/AI_ERROR_HANDLING_GUIDE.md)

---

### 5.3 Deterministic mood and energy rules

**Status**: **MONITORING**
**Priority**: Low
**Started**: 2026-10-19

**Use / fit**: Adapt task selection and reminder pressure without relying on an LLM. Rules must be explicit, inspectable, and user-controlled.

**Current policy**: The 30-minute recovery hold applies only to explicit check-in energy. Health guidance is re-evaluated from the current usable daily signal (today or a fallback up to two days old); corrected data and health opt-out take effect on the next decision. Future, expired, or low-confidence fallback signals must not create pressure guidance. Preserve these transitions with [test_health_pressure_transitions.py](../tests/unit/test_health_pressure_transitions.py).

**Deferred extension / revisit trigger**: No additional health cooldown is selected. Revisit if live use shows repeated pressure changes after intraday syncs or users ask for a gradual transition. Define the signal-change trigger, duration, reset/expiry behavior, restart persistence, and immediate opt-out override before implementing a separate health timer. A daily fallback already bridges missing-today data; it is not an energy-recovery cooldown.

**Guardrails**: Never hide urgent work; never infer mood from ordinary chat text; never require AI to evaluate the rules.

---

## 6. Child Plans

These plans should not be duplicated in detail here.

### 6.1 Notebook system

**Status**: **MONITORING**
**Priority**: Low
**Detailed plan**: [NOTES_PLAN.md](NOTES_PLAN.md)

**Current focus**: Optional visual checks when Discord rendering/help changes. Bulk organization, database search, and events remain deferred in the child plan.

---

### 6.2 Task system

**Status**: **MONITORING**
**Priority**: Low
**Detailed plan**: [TASKS_PLAN.md](TASKS_PLAN.md)

**Current focus**: Optional live checks after UI/parser changes. Attachments, dependencies, and batch extensions await a selected product slice; detailed scope belongs in the child plan.

---

### 6.3 Test program

**Status**: **ACTIVE**  
**Priority**: High  
**Detailed plan**: [TEST_PLAN.md](TEST_PLAN.md)

**Current focus**:

- Full-audit reliability.
- Test artifact/log isolation.
- No-parallel marker reduction only when stability is preserved.
- Coverage growth in high-value domains.

---

## 7. Planned scaffolds

Accepted future work. Not the current focus. Active check-in, task, and notebook reliability stay first.

### 7.1 SMS channel

**Status**: **PLANNED**  
**Added**: 2026-09-22  
**Priority**: Later

**Use / fit**: SMS is a third messaging channel beside Discord and email, for people who will not use either. Business logic stays in the shared message pipeline. The channel adapter only sends and receives text.

**Scaffold** (in order):

1. Add `communication/communication_channels/sms/` with an `SmsBot` on `BaseChannel`. Register it from `get_available_channels()` and `get_channel_class_mapping()` in `core/config.py`. Tests mock the provider.
2. Outbound uses the `phone` field already on `AccountV2EnvelopeModel`. Add `RecipientResolver._resolve_sms_recipient`. Inbound maps that number back to the user and calls `handle_user_message(..., "sms")`.
3. Receive texts through a provider webhook, using the same kind of tunnel as Discord while developing.
4. Check-ins and task replies get short text answers (`3`, `done`, `snooze`). Discord buttons stay on Discord. Split long messages into SMS segments.
5. Let the user choose SMS as their messaging service, with connect, status, and pause as text commands.

**Provider**: a paid SMS API such as Twilio. Free cloud SMS and carrier email-to-SMS are out of scope. iMessage is out of scope.

**Order**: build this before Apple Health. The channel seams already exist.

---

### 7.2 Apple Health ingest

**Status**: **PLANNED**  
**Added**: 2026-09-22  
**Priority**: Later

**Use / fit**: Apple Health (HealthKit on the iPhone) is a second wellness source beside the Google Health API. Google Health stays a cloud pull. Apple Health has no cloud API, so the phone pushes a daily summary and MHM reuses the existing summary-to-signal path.

**Scaffold** (in order):

1. One active wellness source per user, Google or Apple, so the two writers do not overwrite the same day. Record `source` on the daily summary.
2. Add `integrations/apple_health/` with an ingest route authenticated by a shared secret, not OAuth. Validate into `DailySummaryModel` and run the existing signal builder. Tests post a fixture payload.
3. A phone exporter (Health Auto Export or a Shortcut) posts on a schedule through a tunnel. A native iOS app is a later project, not this scaffold.
4. Keep `health status`, pause, enable, and delete shared. Apple connect means the secret is set and a summary has arrived.

**Leave in place for now**: signal-building code stays under `integrations/google_health/` until both sources write real summaries.

---

## 8. Deferred / Low-Priority Plans

These are real ideas, but they are **not current implementation priorities**.

### 8.1 Discord app/bot capabilities exploration

**Status**: **DEFERRED**  
**Priority**: Low

**Use / fit**: Discord is the main interface and better buttons/menus matter, but this should stay planning-only until core notebook/task/check-in flows are reliable.

**Keep for later**:

- Research user-installable app features and limitations.
- Review interaction types: slash commands, buttons, modals, select menus.
- Review permissions, OAuth scopes, rate limits, and formatting options.
- Identify a small list of Discord features that would directly improve MHM.

---

### 8.2 Message analytics, deduplication, and proactive intelligence

**Status**: **DEFERRED**
**Priority**: Low/Medium

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

### 8.3 UI polish and validation

**Status**: **DEFERRED**
**Priority**: Low

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

### 8.4 Cross-channel sync

**Status**: **DEFERRED**  
**Priority**: Low

**Why deferred**:

- Discord is primary.
- Cross-channel sync is not currently important enough to compete with notebook/task/check-in reliability.

**Keep for later**:

- Synchronize state across Discord, email, and future channels if multi-channel usage grows.
- SMS as its own channel is Section 7.1. This item is only about keeping state in sync when someone uses more than one channel.
- Keep Telegram out of scope unless explicitly revived.

---

### 8.5 Smart home integration

**Status**: **ARCHIVED**
**Priority**: None currently

This remains a long-term idea from the broader project vision, not a current MHM implementation plan.

---

### 8.5.1 Development tools extensions

**Status**: **DEFERRED**

Extending custom audit scopes beyond Tier 2 and revisiting Radon, pydeps, or pre-commit require a separate plan. Package distribution awaits a second consumer. See the [archived V6 roadmap](../archive/AI_DEV_TOOLS_IMPROVEMENT_PLAN_V6.md).

---

### 8.6 AI quality and response-time work

**Status**: **DEFERRED**
**Priority**: Low

Prompt tuning, response-quality work, NLP expansion, live model tone review, and generalized AI response-time optimization await a separately selected slice. Coordinate with the deferral in [TODO.md](../TODO.md); provider replacement and optional-AI controls do not close these independent ideas.

---

## 10. Maintenance Rules

These shared rules apply to this index and all child plans.

- Keep plans focused on unresolved work, monitoring, and deferred ideas. Remove fully completed items and completion-history sections; keep implementation history in changelogs.
- Before deleting a section or checked item, extract any unfinished work, deferred ideas, validation limits, and guardrails into the appropriate surviving section.
- Give each remaining item a clear scope, status, priority, and acceptance criteria or a monitoring/deferred revisit trigger. Use the status vocabulary in Section 3.
- Keep detailed work in its owning plan and small standalone tasks in [TODO.md](../TODO.md). Use short cross-references instead of duplicate checklists.
- Cite current code, tests, reports, and changelogs for evidence. Distinguish automated validation from unverified live behavior; use generated reports for current metrics.
- Use current paths and terminology. Update links and related plan summaries when moving work, and record review/status dates as `YYYY-MM-DD`.
- Keep `PLANS.md` as a concise index. Remove an index entry when its work is fully complete; retain only unresolved work in the owning plan or TODO.

---

## 11. Next Review Checklist

Use this checklist when reviewing or updating this plan; reset it for each review.

- [ ] Verify remaining items against current code, tests, reports, and changelogs; distinguish automated evidence from unverified live behavior.
- [ ] Before removing completed work, preserve any unfinished work, deferred ideas, validation limits, and guardrails in the appropriate surviving section.
- [ ] Remove fully completed items and completion-history lists; keep implementation history in changelogs.
- [ ] Confirm each remaining item's status, priority, scope, and acceptance or revisit criteria are accurate.
- [ ] Confirm links and section references resolve, related plan summaries agree, and current metrics come from generated reports.
