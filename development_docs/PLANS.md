# MHM Development Plans

> **File**: `development_docs/PLANS.md`  
> **Audience**: Human Developer & AI Collaborators  
> **Purpose**: Top-level index for unresolved active, monitoring, planned, and deferred MHM work
> **Style**: Concise, current, action-oriented  
> **Last Updated**: 2026-11-24
> **Child plan**: [TEST_PLAN.md](TEST_PLAN.md)\
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
| Task-system roadmap | [Task system](#61-task-system) |
| Notebook roadmap | [Notebook system](#62-notebook-system) |
| AI/dev-tools roadmap | Archived [V6](../archive/AI_DEV_TOOLS_IMPROVEMENT_PLAN_V6.md); live triage [PRIORITIES_BRIEF.md](../development_tools/PRIORITIES_BRIEF.md) |
| Dev-tools list/config canonical sources | [LIST_OF_LISTS.md](https://github.com/Jacfogel/development-tools/blob/2d511ffc1780a8c923ef1296bf016e5585a81942/LIST_OF_LISTS.md) (arrays, mappings, enumerated sets - not planning ownership) |
| Product/runtime list canonical sources | [PRODUCT_LIST_OF_LISTS.md](PRODUCT_LIST_OF_LISTS.md) (commands, prompts, categories, channels) |
| Current audit status | [STATUS_BRIEF.md](../development_tools/STATUS_BRIEF.md) |
| Generated priority queue | [PRIORITIES_BRIEF.md](../development_tools/PRIORITIES_BRIEF.md) |
| Session history | [CHANGELOG_DETAIL.md](CHANGELOG_DETAIL.md) and [CHANGELOG_BRIEF.md](CHANGELOG_BRIEF.md) |
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
| Error handling quality | **ACTIVE** | Medium | This file + [ERROR_HANDLING_GUIDE.md](../core/ERROR_HANDLING_GUIDE.md) | Better user/log messages and recovery guidance |
| Notebook system | **MONITORING** | Low | [Notebook system](#62-notebook-system) | Optional Discord visual checks when rendering or help changes |
| Task system | **MONITORING** | Low | [Task system](#61-task-system) | Focused validation when Discord UI or parsing changes |
| Test program | **ACTIVE** | High | [TEST_PLAN.md](TEST_PLAN.md) | Full-suite reliability, test isolation, and coverage growth |
| Deterministic mood and energy rules | **MONITORING** | Low | This file Section 5.3 | Observe health-derived pressure transitions; additional timer awaits usage evidence |
| Appropriate coupling reductions | **MONITORING** | Medium | [PRIORITIES_BRIEF.md](../development_tools/PRIORITIES_BRIEF.md) | Revisit when triage confirms a wrong-layer dependency or a private API dependency causes maintenance problems (2026-11-16) |
| SMS channel | **ACTIVE** | Medium | This file Section 7.1 | Paid-account SMS enrollment deployed; expanded paid-user live validation remains |
| Messaging pilot launch policy | **ACTIVE** | High | This file Section 7.3 | Canada and US adult pilot; owner-led operations and provider budgets; outstanding launch gates |
| Apple Health ingest | **PLANNED** | Later | This file Section 7.2 | Phone-pushed daily summaries beside Google Health |

---

## 5. Active Top-Level Plans

### 5.1 Flow/check-in scheduled-send stability

**Status**: **MONITORING**
**Priority**: Low
**Started**: 2026-02-22  
**Spec**: [discord-checkin-flow.md](../specs/discord-checkin-flow.md)

**Use / fit**: Stability is critical. Check-ins and scheduled sends work well enough day to day, but reliability and debugging matter most: selecting the right number of questions from the right lists, responding dynamically, saving results properly, and supporting flexible response formats.

**Remaining work**:

- Live baseline (2026-11-20): requested Discord check-in delivered and saved five replies, included every Always question within the configured count range, and closed its flow. The 11:00-12:00 automatic window was outside the session; timer firing, live cooldown deferral, and forced reconnect recovery remain unverified.
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

**Reference**: [ERROR_HANDLING_GUIDE.md](../core/ERROR_HANDLING_GUIDE.md)

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

## 6. Task and notebook roadmaps

### 6.1 Task system

**Status**: **MONITORING** | **Priority**: Low | **Reviewed**: 2026-11-16

Keep task workflows easy to use from a phone, with Discord as the primary interface. When UI or parsing changes, validate the picker and details, creation follow-ups, parsed titles and dates, template modals, and create-hub buttons as applicable. Keep task behavior in task or shared modules and reuse the shared tag and ID helpers. The [2026-11-15 validation](CHANGELOG_DETAIL.md#2026-11-15---task-dependency-relationships) covered task, browser, and authenticated website-route tests. Live Discord and website rendering remain unverified. See the [testing guide](../tests/MANUAL_TESTING_GUIDE.md#64-focused-task-and-notebook-regression-tests).

- Restart validation (2026-11-20): 15 integration scenarios verify persisted snooze/skip recovery, overdue job deduplication, and suppression of uncertain delivery replay with a rebuilt scheduler and replacement process identity. All 98 focused reminder tests passed. Live Discord delivery across an actual service restart remains unverified.

- **File and image attachments (deferred, medium)** require a storage, retention, and Discord upload design. **Batch archive (deferred, low/medium)** depends on introducing task archiving.
- **Context-aware reminders (deferred)** include location- and calendar-linked reminders. Revisit once foundational task usage is stronger and coordinate with the [mood and energy rules](#53-deterministic-mood-and-energy-rules).
- **Task suggestions (deferred)** include pattern-based suggestions, ordering, and conflict detection. Select a concrete use case first. **Advanced views and analytics (deferred)** include calendar and Kanban views, additional focus views, completion trends, recurring-task streaks, and overdue priority escalation. Revisit once Discord task creation is reliable.
- **Data portability (deferred)** includes export/import, cloud sync, cross-device access, and task-specific backup checks. Coordinate with the storage and user-data roadmap.

### 6.2 Notebook system

**Status**: **MONITORING** | **Priority**: Low | **Reviewed**: 2026-11-16

Prioritize everyday capture and retrieval in Discord and on the website. When Discord rendering or help changes, optionally check Show More styling, expired buttons, and discovery through `help notebook` and `examples notebook`. The [2026-11-10 validation](CHANGELOG_DETAIL.md#2026-11-10---clarify-recovery-messages-and-verify-backup-and-notebook-behavior) covered 150 automated notebook tests. See the [testing guide](../tests/MANUAL_TESTING_GUIDE.md#64-focused-task-and-notebook-regression-tests).

- **Search (deferred, low)**. Keep substring search with JSON storage. Revisit if searches slow down on real data, ranking or fuzzy matching matters, tasks and notebook need unified search, or storage moves to SQLite. **Shared organization (deferred, low/medium)**. Extract filters or grouping only when behavior is duplicated across features. Reuse existing tag and pagination helpers.
- **Skip-to-notebook (deferred, low)**. For repeated reminder skips, consider asking "Capture why?" or creating a task-linked note tagged `blocker`. Decide whether to ask or capture automatically, whether Tasks, Notebook, or a shared reflection/check-in flow owns it, and how to avoid adding friction to reminders.
- **Edit review (deferred, low)**. Define preview before saving, confirmation, cancellation, and timeout for multi-message edits. The existing replace and append sessions leave this review step open.
- **Events (deferred)**. Consider `Entry(kind="event")` for simple notebook-style events. Use a separate feature for scheduling, recurrence, reminders, attendees, or calendar sync, reusing tags, search, and pagination where practical.

---

## 7. Planned scaffolds

Accepted integration work. SMS has an active owner pilot; Apple Health remains planned. Active check-in, task, and notebook reliability stay first.

### 7.1 SMS channel

**Implementation (2026-11-18)**: Simulation and an explicitly enabled Twilio owner pilot are implemented. Live transport includes signed loopback webhooks, durable inbound receipts, provider status tracking, STOP/START, and shared task/check-in reply routing. The owner pilot was configured on 2026-11-20: a real test text and `sms status` reply exchange were delivered, and signed status callbacks reached MHM through the HTTPS tunnel. Scheduled reminders remain on Discord. See [SMS_GUIDE.md](../communication/communication_channels/sms/SMS_GUIDE.md) and [pilot spec](../specs/sms-twilio-pilot.md).

**Status**: **ACTIVE**
**Added**: 2026-09-22
**Priority**: Medium

**Use / fit**: SMS is a third messaging channel beside Discord and email, for people who will not use either. Business logic stays in the shared message pipeline. The channel adapter only sends and receives text.

**Remaining work**:

1. Owner sending, signed callbacks, `sms status`, task completion by `done`, and STOP/START were verified live on 2026-11-20. STOP blocked submission locally; a post-START text was delivered. A second check-in was correctly refused because one was already completed that day. Validate a full SMS question/answer/save exchange for an active paid account at its next eligible check-in before treating the pilot checklist as complete. Preferred scheduled delivery remains Discord.
2. Verified phone ownership, per-account consent, paid-plan enforcement, and website/desktop management are implemented. Validate the deployed enrollment flow with an active paid account before enrolling additional people; trial accounts remain Discord-only.
3. Define receipt retention and operator recovery/status UI from pilot experience. Keep unconfirmed mutations out of automatic retries.

**Provider**: Twilio. Free cloud SMS and carrier email-to-SMS are out of scope. iMessage is out of scope.

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

### 7.3 Messaging pilot launch policy

**Status**: **ACTIVE**

**Priority**: High

**Added / reviewed**: 2026-11-24

**Confirmed scope**: Invite 10-25 adults aged 18+ living in Canada or the United States. Phone-channel enrollment uses Canadian or US numbers; a +1 prefix alone does not establish either country. This is a pilot enrollment policy, not an implemented geographic or age restriction and not a promise of Canadian data residency. Wider international access and minors remain outside this pilot.

**Confirmed ownership**: The project owner requesting this pilot owns launch decisions, messaging spend, and incidents. A named backup and published support contact/hours remain required before additional enrollment; no continuous monitoring is promised.

**Confirmed budget approach**: Keep billing and budget controls with providers and review usage manually. No MHM cost ledger, automatic overage charging, or application-enforced allowance is authorized by this plan. Review Canada and US SMS charges separately. Establish a provider spending threshold, alert recipients, review cadence, and manual pause procedure; distinguish alerts from verified hard caps. Keep current plan prices and live-paid phone-channel eligibility.

**Channel launch gates**:

- Continue Discord and the existing SMS pilot; adding US users does not establish US SMS readiness. Before enrolling additional phone users, record the actual sender type, approved registration/verification, destination permissions, and destination-specific pricing. Prove signed inbound replies, delivered callbacks, STOP/START, paid enrollment, and a full check-in for the intended destinations. Existing evidence is in Section 7.1 and the [SMS guide](../communication/communication_channels/sms/SMS_GUIDE.md).
- Confirm sender-specific requirements with Twilio. US local senders use [A2P 10DLC registration](https://www.twilio.com/docs/messaging/compliance/a2p-10dlc); toll-free senders require [approved verification](https://www.twilio.com/docs/messaging/compliance/toll-free/console-onboarding) before US/Canada SMS. Do not buy another number or submit registration merely to close this planning item.
- Keep WhatsApp disabled and purchases inactive until business verification, product eligibility, production credentials/sender, template approval/category, published disclosures/support, and live enrollment/delivery/STOP/OPEN validation are evidenced. Meta's [AI Provider policy](https://developers.facebook.com/documentation/business-messaging/whatsapp/pricing/ai-providers) does not list Canada or the US among permitted general-purpose AI markets; structured wellness reminders do not themselves establish eligibility. Follow the existing [activation task](../TODO.md#2-high-priority) and [WhatsApp guide](../communication/communication_channels/whatsapp/WHATSAPP_GUIDE.md). Failure of this gate does not block Discord/SMS planning.

**Policy implementation and remaining work**:

- **Categories and usage**: Separate account/security notices, user-requested reminders/check-ins, encouragement, and direct replies; exclude promotions initially. Consider three scheduled phone notifications daily as a configurable guideline, not a hard cap. The earlier 300-segment review threshold is unapproved. Define which existing message categories map to these groups before publishing limits.
- **User schedules (2026-11-24)**: User-configured messages, check-ins and task reminders follow their saved schedules without a Night-to-Morning pause. Phrases clocks remain parsing defaults; explicit Support mode quiet controls remain independent. See [messaging policy spec](../specs/messaging-quiet-hours-and-data-controls.md).
- **Retention implementation (2026-11-24)**: Preserve user-created history until user/account deletion and retain the existing 365-day active sent-history archiving policy. Archiving is not deletion. Account export/deletion now covers attributed phone records, with 90-day terminal delivery retention, 24-hour pending WhatsApp expiry, and minimal replay/suppression records retained. Existing historical receipts cannot be attributed retroactively. Backup restoration and provider-held copies remain separate operational checks. Preserve deduplication and opt-out protection during cleanup. See [user data](../core/USER_DATA_MODEL.md), [privacy disclosures](../website/privacy.html), and [data controls](../website/data.html).
- **Fallback implementation (2026-11-24)**: No automatic cross-channel resend. Disconnecting Discord, SMS or WhatsApp does not select another delivery channel; the user must explicitly choose a new channel. Browser/live validation remains.

**Week 1 exit criteria**: Record the backup/support contact, spending thresholds and review procedure, accepted category/usage policy, quiet-hours rules, retention/export/deletion process, and fallback consent. Give each channel gate dated evidence or a recorded blocker. Approval of this policy does not establish that the corresponding product controls are implemented. Do not enroll users, change subscriptions, activate providers, or change runtime settings through this planning step.

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
