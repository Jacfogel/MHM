# MHM Development Plans


> **File**: `development_docs/PLANS.md`
> **Audience**: Human Developer & AI Collaborators  
> **Purpose**: Consolidated development plans (grouped, interdependent work) with step-by-step checklists  
> **Style**: Actionable, checklist-focused, progress-tracked  
> **Last Updated**: 2026-02-28
> **Children**: [TEST_PLAN.md](development_docs\TEST_PLAN.md), [TASKS_PLAN.md](development_docs/TASKS_PLAN.md), [NOTES_PLAN.md](development_docs/NOTES_PLAN.md), and [AI_DEV_TOOLS_IMPROVEMENT_PLAN_V4.md](development_tools/AI_DEV_TOOLS_IMPROVEMENT_PLAN_V4.md).  

---

**Note**: [TODO.md](TODO.md) is the canonical list for standalone tasks. Larger, scoped efforts live here or in subordinate dedicated plan files such as [TEST_PLAN.md](development_docs\TEST_PLAN.md), [TASKS_PLAN.md](development_docs/TASKS_PLAN.md), [NOTES_PLAN.md](development_docs/NOTES_PLAN.md), and [AI_DEV_TOOLS_IMPROVEMENT_PLAN_V4.md](development_tools/AI_DEV_TOOLS_IMPROVEMENT_PLAN_V4.md).  

## [IN PROGRESS] **Plan Maintenance**

### **How to Update This Plan**
1. **Add new plans** with clear goals and checklist format; include **Date** and **Last Updated** (YYYY-MM-DD).
2. **Update progress** by checking off completed items; add completion date when marking items done (e.g., `- [x] Item (2026-02-28)`).
3. **Remove fully completed plans** - document them in CHANGELOG files instead.
4. **Keep reference information** current and useful.
5. **Remove outdated information** to maintain relevance.
6. **Dating convention**: New items and status changes get dates. See [AI_DOCUMENTATION_GUIDE.md](ai_development_docs/AI_DOCUMENTATION_GUIDE.md) for the full dating standard.

### **Success Criteria**
- **Actionable**: Each item is a specific, testable action
- **Trackable**: Clear progress indicators and completion status
- **Maintainable**: Easy to update and keep current
- **Useful**: Provides value for both human developer and AI collaborators

---

## [ACTIVE] **Current Active Plans**

### **Development-Tools Test Runtime & Audit Throughput** - see child plan

**Tracked in**: [AI_DEV_TOOLS_IMPROVEMENT_PLAN_V4.md](development_tools/AI_DEV_TOOLS_IMPROVEMENT_PLAN_V4.md)

- **Test runtime** (section 1.8): Optimized 8 slow tests; timing 328s->314s. Remaining: setup/teardown offenders, fixture scope.
- **Audit throughput** (section 5.1.1): Tier 3 concurrency restored; audit ~277s. Remaining: unused-imports backend redesign, cache policy, telemetry.

### **Flow/Check-in Scheduled Send Stability Follow-up** **IN PROGRESS**

**Status**: IN PROGRESS (since 2026-02-22) | **Priority**: High

**Use / fit**: Stability is critical. Check-ins and scheduled sends work well enough day to day, but reliability and debugging matter most-selecting the right number of questions from the right lists, responding dynamically, saving results properly, and flexible response formats.

**Done**: Deferral + cooldown in runtime; one-time retry scheduling; unit/behavior tests (206 passed). See CHANGELOG_DETAIL 2026-02-22.

**Remaining**:
- [ ] Live Discord manual validation (active-flow deferral, 10-min cooldown, retry)
- [ ] Monitor logs for legacy warnings in check-in flow paths
- [ ] Monitor `MESSAGE_SELECTION` diagnostics

### **Backup Reliability and Restore Confidence Plan** **IN PROGRESS**

**Status**: IN PROGRESS (since 2026-02-16) | **Priority**: High

**Use / fit**: Important for peace of mind and occasional rollbacks; user dislikes redoing work and makes mistakes (beginner). Migration of `user_data_cli.py` not used; decision: defer migration, document as optional tool only.

**Done**: Inventory, restore drill, ownership map, runbooks. Weekly gating + retention buckets restored; guides synced. See CHANGELOG_DETAIL 2026-02-25.

**Remaining**:
- [ ] Document decision: `user_data_cli.py` remains optional; no migration to admin tooling (user does not use it)

### **Testing Program Consolidation** - see child plan

**Tracked in**: [TEST_PLAN.md](development_docs/TEST_PLAN.md)

Migrated: reliability, no-parallel, harness, coverage cache, consistency, nightly governance. Fixed: test_logger_behavior, test_checkin_view, test_user_management, dev-tools low-coverage. **Remaining**: Sweep log fixtures for xdist-safe isolation.

### **Error Handling Quality Improvement Plan** **IN PROGRESS**

**Status**: IN PROGRESS (since 2025-11-20) | **Priority**: Medium

**Use / fit**: Validation helps (beginner + AI coding). Focus on **noisy/unclear logs when something fails** over cryptic user-facing errors. Coverage at 100%; continue improving clarity and log quality.

**Done**: 100% coverage; Phase 1/2 tooling in `analyze_error_handling.py`. Metrics in [AI_STATUS.md](development_tools/AI_STATUS.md).

**Remaining**: Phase 3 (enhance user/log messages), Phase 4 (recovery strategies), Phase 5 (context payloads), Phase 6 (direct `handle_error` calls). Emphasize clearer, less noisy logs. See [AI_ERROR_HANDLING_GUIDE.md](ai_development_docs/AI_ERROR_HANDLING_GUIDE.md).

### **Discord App/Bot Capabilities Exploration** **PLANNING**

**Status**: **PLANNING** | **Priority**: Low

**Use / fit**: Discord is the main interface. Interest in message/menu features. Main improvement wanted: **more buttons that work consistently**. Stay planning-only or deferred until other work is done.

**Effort**: Medium | **Date**: 2025-11-13

**Objective**: Explore Discord's app/bot capabilities more thoroughly to identify additional features and integrations that could enhance the MHM Discord experience.

**Scope**:
- [ ] Research Discord's user-installable app features and limitations
- [ ] Explore Discord's webhook event system beyond APPLICATION_AUTHORIZED/DEAUTHORIZED
- [ ] Investigate Discord's interaction types (slash commands, buttons, modals, select menus)
- [ ] Review Discord's message formatting and rich content capabilities
- [ ] Explore Discord's permission system and OAuth2 scopes
- [ ] Research Discord's rate limiting and best practices
- [ ] Identify potential integrations with Discord's features (threads, forums, voice, etc.)

**Success Criteria**:
- [ ] Document findings about Discord capabilities relevant to MHM
- [ ] Identify 3-5 potential feature enhancements based on Discord capabilities
- [ ] Create a prioritized list of Discord integrations to consider

**Notes**:
- Current webhook implementation (APPLICATION_AUTHORIZED/DEAUTHORIZED) is working well
- Focus on capabilities that align with MHM's communication-first, AI-led experience
- Consider both user-installable app features and potential server bot features

### **Account Management System Improvements** **ARCHIVED (MOSTLY COMPLETE)**

**Status**: **ARCHIVED** (2026-02-28)  
**Outcome**: Core account creation and feature enablement complete. Remaining work (e2e linking, edge cases) tracked in [TODO.md](TODO.md) if needed. Full details in changelog history (2025-11-13 through 2025-11-20).

### **Mood-Aware Support Calibration** **PLANNING**

**Status**: **PLANNING** | **Priority**: High (deferred-do foundational work first)

**Use / fit**: Very important for daily use. In practice: gentler when low, less nagging when overwhelmed, mood/energy-appropriate actions (e.g. water/breathing when low; walk/laundry when better). Sounds hard; sequence after Phase 1 and flow stability.

**Effort**: Medium | **Date**: 2025-11-10

**Objective**: Define how the assistant adapts tone, reminders, and check-ins based on user mood/energy cues while protecting quiet time boundaries.

**Scope (initial threads)**:
- [ ] Codify "safety net" language library with choose-your-support prompts.
- [ ] Compare task breakdown helper formats (checklist vs. conversational) for stalled tasks.
- [ ] Draft context-to-reminder content mapping covering energy, mood, and task age.
- [ ] Rename and document "Unavailable" mode rules, including urgent escalation criteria.
- [ ] Specify mood re-evaluation triggers and cooldowns.

**Success Criteria**:
- [ ] Safety net prompts feel grounding in sample conversations and pass tone review.
- [ ] Reminder and task helper variants include decision guidance for when to use each.
- [ ] Quiet periods respect "Unavailable" framing without work-centric language.
- [ ] Mood cadence guidelines balance responsiveness with minimal nagging.

**Notes**:
- Capture findings in TODO task updates and tag future implementation tickets once guidelines are approved.
- Validate prototypes against mobile UX constraints (concise, quick replies).

### **Message Deduplication Advanced Features**

**Status**: **IN PROGRESS** (analytics/deep ML deferred)  
**Priority**: Low (deferred)  
**Effort**: Large  
**Started**: 2025-11-11  
**Last Updated**: 2026-02-28

**Use / fit**: Analytics and ML-style features (predictive scheduling, pattern-based personalization) feel overkill for 1-2 users; mostly long-term. Desired improvement: more personalized, time-appropriate messages. Smart scheduling maybe; analytics no.

**Objective**: Implement advanced analytics, insights, and intelligent scheduling features for the message deduplication system.

**Completed** (documented in changelog 2025-11-11):
- [x] **Message frequency analytics foundation**: MessageAnalytics class with frequency tracking, delivery success rate analysis, message summary generation (7 tests passing)

**Remaining Work**:

#### **Step 5.1: Analytics and Insights** [IN PROGRESS]
- [x] **Message frequency analytics** [COMPLETED] (2025-11-11)
  - [x] Track message send frequency by category and time period
  - [x] Generate reports on message delivery success rates
  - [ ] Analyze user engagement patterns over time
  - [ ] Create visualizations for message analytics
- [ ] **User engagement tracking** [LONG-TERM/FUTURE] - Requires multiple users for meaningful data
  - [ ] Monitor user response rates to different message types
  - [ ] Track user interaction patterns with messages
  - [ ] Analyze user engagement trends and preferences
  - [ ] Generate user engagement reports
- [ ] **Message effectiveness metrics** [LONG-TERM/FUTURE] - Requires multiple users and response data for meaningful analysis
  - [ ] Measure message effectiveness based on user responses
  - [ ] Track which messages generate the most positive responses
  - [ ] Analyze message timing effectiveness
  - [ ] Create effectiveness scoring system
- [ ] **Smart message recommendation system**
  - [ ] AI-powered message selection based on user history
  - [ ] Personalized message recommendations
  - [ ] Context-aware message suggestions
  - [ ] Learning algorithms for message optimization

#### **Step 5.2: Advanced Scheduling** [PLANNED]
- [ ] **Intelligent message spacing**
  - [ ] Dynamic spacing based on user engagement patterns
  - [ ] Adaptive timing based on user response history
  - [ ] Smart scheduling to avoid message fatigue
  - [ ] Personalized optimal timing algorithms
- [ ] **User preference learning**
  - [ ] Machine learning from user interaction patterns
  - [ ] Adaptive message selection based on preferences
  - [ ] Personalized category preferences
  - [ ] Learning from user feedback and responses
- [ ] **Context-aware message selection**
  - [ ] Time-of-day context awareness
  - [ ] Seasonal and calendar context integration
  - [ ] User mood and state context
  - [ ] Environmental context consideration
- [ ] **A/B testing for message effectiveness**
  - [ ] Split testing framework for message variations
  - [ ] Statistical analysis of message performance
  - [ ] Automated optimization based on test results
  - [ ] Continuous improvement through testing

**Note**: Many features marked LONG-TERM/FUTURE as they require multiple users for meaningful data/analysis

---


### **Phase 1: Enhanced Task & Check-in Systems** **PARTIALLY COMPLETE**

**Status**: **PARTIALLY COMPLETE**  
**Priority**: High  
**Last Updated**: 2026-02-28

**Use / fit**: Check-in Response Analysis matters more than AI context in chat. Biggest impact: **better insights from check-ins** and **better phrased questions**. AI conversations need a major overhaul separately; deprioritize Enhanced Context-Aware Conversations for now.

**Completed** (documented in changelog):
- [x] **Enhanced Task Reminder System** (COMPLETED - documented in changelog)
  - Priority-based weighting, due date proximity weighting, critical priority level, no due date option
- [x] **Semi-Random Check-in Questions** (COMPLETED - documented in changelog)
  - Weighted selection, question variety, category balancing

**Remaining Work**:
- [ ] **Check-in Response Analysis** (High Impact, Medium Effort) - *prioritize first*
  - [ ] Implement pattern analysis of responses over time
  - [ ] Add progress tracking for mood trends
  - [ ] Create response categorization and sentiment analysis
  - [ ] Generate insights for AI context enhancement
  - [ ] Test pattern analysis accuracy
  - [ ] Validate progress tracking metrics
- [ ] **Enhanced Context-Aware Conversations** (Medium Impact, Medium Effort) - *deprioritized: AI needs major overhaul*
  - [ ] Expand user context with check-in history
  - [ ] Add conversation history analysis
  - [ ] Implement preference learning from interactions
  - [ ] Create more sophisticated personalization algorithms
  - [ ] Test context enhancement effectiveness
  - [ ] Validate personalization improvements

---

### **Phase 2: Mood-Responsive AI & Advanced Intelligence** [WARNING] **PARTIALLY COMPLETE**

**Status**: [WARNING] **PARTIALLY COMPLETE**  
**Priority**: High  
**Effort**: High  
**Date**: 2025-11-10  
**Last Updated**: 2026-02-28

**Use / fit**: Very important; MHM often feels rigid or tone-deaf. Goal: **noticeably more adaptive**-gentler when low, less nagging when overwhelmed, mood/energy-appropriate actions (water/breathing when low; walk/laundry when better).

**Goal**: Implement mood-responsive AI conversations and advanced emotional intelligence

**Current State**:
- [OK] **Mood data included in context**: AI chatbot includes mood and energy data from check-ins in context (`ai/chatbot.py`, `ai/context_builder.py`)
- [OK] **Mood trend analysis**: Context builder analyzes mood trends (improving/declining/stable)
- [OK] **Emotional intelligence in system prompt**: System prompt includes emotional intelligence instructions
- [OK] **Mood-aware completion messages**: Check-in completion messages adapt based on mood/energy (`communication/message_processing/conversation_flow_manager.py`)
- [X] **Prompt modification based on mood**: Prompts are NOT dynamically modified based on mood/energy - mood data is only included in context
- [X] **Tone adaptation algorithms**: No explicit tone adaptation based on detected mood
- [X] **Emotional response templates**: No mood-specific response templates
- [X] **Mood prediction**: No predictive mood analysis

**What's Missing**:
- [ ] **Dynamic prompt modification**: Modify system prompt or add mood-specific instructions based on detected mood/energy levels
- [ ] **Tone adaptation algorithms**: Implement algorithms that adjust response tone based on mood (e.g., more gentle for low mood, more energetic for high energy)
- [ ] **Emotional response templates**: Create templates for different mood states (low mood = more supportive, high mood = more celebratory)
- [ ] **Enhanced mood tracking**: More granular mood detection (beyond 1-5 scale)
- [ ] **Mood prediction**: Predictive analysis of mood trends
- [ ] **Emotional intelligence scoring**: System to score and improve emotional intelligence of responses
- [ ] **Machine learning patterns**: Advanced ML-based mood analysis (currently uses simple averages/trends)

---

### **Phase 3: Proactive Intelligence & Advanced Features** [WARNING] **NEW**

**Status**: Planning Phase | **Priority**: Medium  
**Estimated Duration**: 3-4 weeks  
**Last Updated**: 2026-02-28

**Use / fit**: Proactive suggestions useful if they're good. Target examples: "You haven't checked in today"; "Your recent check-ins indicate you haven't been brushing your teeth much lately..."; "[Task] has been open for weeks-identify barriers, ask for help, break it down."

**Goal**: Implement proactive suggestion system and advanced AI capabilities

**Checklist**:
- [ ] **Proactive Suggestion System** (Medium Impact, High Effort)
  - [ ] Analyze user patterns and habits from check-in and task data
  - [ ] Generate contextual suggestions based on patterns
  - [ ] Implement suggestion timing and delivery algorithms
  - [ ] Add suggestion relevance scoring and filtering
  - [ ] Test suggestion accuracy and user engagement
  - [ ] Validate proactive system effectiveness
- [ ] **Advanced Context-Aware Personalization** (Medium Impact, High Effort)
  - [ ] Implement deep learning from user interaction patterns
  - [ ] Add adaptive personality traits based on user preferences
  - [ ] Create sophisticated preference learning algorithms
  - [ ] Implement context-aware response generation
  - [ ] Test personalization depth and accuracy
  - [ ] Validate adaptive personality effectiveness
- [ ] **Smart Home Integration Planning** [WARNING] **LONG-TERM/FUTURE** - Not applicable for current single-user personal assistant; mentioned in [PROJECT_VISION.md](PROJECT_VISION.md) Phase 3 but not a current priority
  - [ ] Research smart home APIs and protocols
  - [ ] Design integration architecture for future implementation
  - [ ] Document requirements and constraints
  - [ ] Create integration roadmap and timeline
  - [ ] Test integration feasibility with sample APIs
  - [ ] Validate integration architecture design
  - **Note**: This is a future consideration from [PROJECT_VISION.md](PROJECT_VISION.md) Phase 3. With only 1-2 users and focus on core mental health assistant features, smart home integration is not currently applicable or prioritized.

---

### **UI Migration Plan**

**Status**: Foundation, Dialogs, and Widgets Complete; Testing Remaining  
**Priority**: Low  
**Last Updated**: 2026-02-28

**Use / fit**: Discord is the main interface; UI not used regularly. Polish secondary. If fixing: sizing/spacing, confirm everything works as intended.

**Completed** (documented in changelogs):
- [x] **Foundation**: PySide6/Qt migration, file reorganization, naming conventions, widget refactoring, user data migration, signal-based updates, 100% function documentation
- [x] **Dialog Implementation**: All 7 dialogs complete (Category Management, Channel Management, Check-in Management, User Profile, Account Creator, Task Management, Schedule Editor)
- [x] **Widget Implementation**: All 6 widgets complete (TagWidget, Task Settings, Category Selection, Channel Selection, Check-in Settings, User Profile Settings)
- [x] **Main UI Application**: 21 behavior tests complete

**Remaining Work**:
- [ ] **Testing & Validation Strategy** is tracked in [TEST_PLAN.md](development_docs/TEST_PLAN.md) (UI and integration testing backlog).
- [ ] **UI Quality Improvements**
  - [ ] Fix Dialog Integration (main window updates after dialog changes)
  - [ ] Add Data Validation across all forms
  - [ ] Improve Error Handling with clear, user-friendly messages
  - [ ] Monitor and optimize UI responsiveness for common operations

---

### **Testing Strategy Plan**

Moved to [TEST_PLAN.md](development_docs/TEST_PLAN.md) as part of testing roadmap consolidation.

---


### **Channel Interaction Implementation Plan**

**Status**: Email Integration Complete, Cross-Channel Sync Remaining  
**Priority**: Low (deferred)  
**Last Updated**: 2026-02-28

**Use / fit**: Discord primary; friend uses email. Cross-channel sync not important at this point.

**Completed**:
- [x] Email Integration - Full email-based interaction system (COMPLETED 2025-11-11, documented in changelog)
  - Email message body extraction, polling loop, user mapping, message routing, response sending

**Remaining Work**:
- [ ] Cross-Channel Sync - Synchronize data across supported channels
  - Note: Telegram integration has been removed from scope

---
