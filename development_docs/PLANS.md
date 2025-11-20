# MHM Development Plans


> **File**: `development_docs/PLANS.md`
> **Audience**: Human Developer & AI Collaborators  
> **Purpose**: Consolidated development plans (grouped, interdependent work) with step-by-step checklists  
> **Style**: Actionable, checklist-focused, progress-tracked  
> **Last Updated**: 2025-11-20
> **See [TODO.md](TODO.md) for independent tasks**

---

## [ACTIVE] **Current Active Plans**

### **AI Chatbot Actionability Sprint** **IN PROGRESS**

**Status**: **IN PROGRESS**  
**Priority**: High  
**Effort**: Large  
**Date**: 2025-10-30  
**Last Updated**: 2025-11-20

**Objective**: Improve chat quality and enable robust action handling (task/message/profile CRUD) with context from recent automated messages and targeted, non-conflicting suggestions.

**Progress**:
- [x] Parser reliability for common natural phrases (schedule edit without times - completed)
- [x] Curated prompts for disambiguation/confirmations (delete/complete - completed; extend as needed)
- [x] AI context: recent automated message awareness, check-in summaries (completed; monitor)
- [x] Task CRUD completeness: name-based update extraction for title/priority/due (completed; watch)
- [x] Natural language command detection fix (2025-11-10 - "I need to buy groceries" now works)
- [x] Suggestion relevance testing (2025-11-10 - verified generic suggestions suppressed)
- [ ] Suggestions: targeted + minimal, non-conflicting (in place; extend coverage)

**AI Functionality Test Plan Remaining Work**:
- [ ] Fix AI fabricating check-in data (T-4.1) - AI claims check-ins exist when there are none
- [ ] Fix AI referencing non-existent conversation history (T-2.3) - AI mentions "you mentioned in recent conversation" when no history exists
- [ ] Fix response-prompt mismatches (T-9.3, T-12.2) - Responses should match prompts (e.g., "Tell me a short story" should actually tell a story)
- [ ] Improve missing context fallback responses (T-2.1) - Should be more supportive and explicit
- [ ] Fix code fragment extraction (T-11.1) - Python code blocks (```python) still appearing in command responses
- [ ] Address response truncation (10 tests) - Many responses cutting off at 200/300 chars
- [ ] Add integration tests with conversation manager
- [ ] Add concurrent request handling tests
- [ ] Add memory usage monitoring tests
- [ ] Add timeout handling tests with actual timeouts

**Success Criteria**:
- [x] Users can ask for common operations in natural language (partially - natural language detection fixed)
- [ ] Prompts always offer actionable next steps (in progress)
- [x] No regressions (full suite remains green - verified)

**Notes**:
- Tests by area are acceptable to iterate faster; full suite before shipping changes.
- Keep both `!` and `/` commands; prefer slash in help/UX with auto-suggests.

### **Discord App/Bot Capabilities Exploration** **PLANNING**

**Status**: **PLANNING**
**Priority**: Medium
**Effort**: Medium
**Date**: 2025-11-13

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

### **Account Management System Improvements** **MOSTLY COMPLETE**

**Status**: **MOSTLY COMPLETE**  
**Priority**: High  
**Effort**: Medium  
**Date**: 2025-11-13  
**Last Updated**: 2025-11-20

**Objective**: Complete account linking functionality and enhance account creation with proper feature configuration and user preferences.

**Completed**:
- [x] **Fix Account Linking**: Confirmation code sending working (COMPLETED 2025-11-13)
  - [x] Confirmation codes sent via email (not Discord) for security
- [x] **Fix Account Creation Feature Enablement**: Feature flags now set correctly (COMPLETED 2025-11-14)
  - [x] Account creation sets proper feature flags (task_management, checkins, automated_messages)
- [x] **Enhance Account Creation Flow**: Discord flow enhanced (COMPLETED 2025-11-14)
  - [x] Feature selection (tasks, checkins, automated messages)
  - [x] Timezone selection/configuration
  - [x] Multi-step flow with modal + view pattern

**Remaining Work**:
- [ ] Test end-to-end account linking flow
- [ ] Handle edge cases (user already linked, invalid codes, expired codes)
- [ ] Add profile information collection during account creation (name, preferences, etc.) - Future enhancement

**Success Criteria**:
- [x] Account creation sets correct feature enablement flags (COMPLETED)
- [x] New users can configure preferences during account creation (COMPLETED for Discord)
- [x] Account creation flow is intuitive (COMPLETED)
- [ ] Account linking works end-to-end with edge case handling (in progress)

**Notes**:
- Core functionality complete; remaining work is testing and edge case handling
- Future: Consider adding profile information collection during account creation
### **Mood-Aware Support Calibration** **PLANNING**

**Status**: **PLANNING**
**Priority**: High
**Effort**: Medium
**Date**: 2025-11-10

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

### **2025-09-16 - High Complexity Function Refactoring - Phase 2** **IN PROGRESS**

**Status**: **IN PROGRESS**  
**Priority**: High  
**Effort**: Large  
**Last Updated**: 2025-11-20

**Objective**: Continue refactoring high complexity functions identified in audit to improve maintainability and reduce technical debt.

**Background**: Latest audit identified 1856 high complexity functions (>50 nodes). Phase 1 successfully refactored `get_user_data_summary` (800 → 15 helper functions).

**Completed** (documented in changelog 2025-09-27):
- [x] **Step 1: Priority Function Analysis** (COMPLETED)
  - Exported top-50 most complex functions, categorized by module, identified patterns, created refactoring plan
- [x] **get_personalization_data Refactoring** (COMPLETED 2025-09-27, documented in changelog)
  - Reduced complexity from 727 to 6 focused helper functions using `_main_function__helper_name` pattern
  - All tests pass, functionality preserved
- [x] **Step 3: Testing and Validation** (COMPLETED)
  - Comprehensive tests added, full test suite passes, refactoring patterns documented

**Remaining Work**:
- [ ] **Step 2: Refactoring Strategy Implementation** (IN PROGRESS)
  - [ ] `ui/ui_app_qt.py::validate_configuration` (complexity: 692) - NEXT TARGET
  - [ ] Additional high-priority functions from audit analysis
  - [x] Refactoring approach established (extract helpers, reduce nesting, apply naming convention)
- [ ] **Priority Targets from Analysis**:
  - [ ] Add coverage for profile and analytics command handlers before refactoring (13 of top 20 complexity hotspots, currently untested)
  - [ ] Build targeted UI harnesses for `ui/ui_app_qt.py` to cover validation, signal registration, system health checks (27% coverage gap)
  - [ ] Expand behavior tests around `interaction_manager.handle_message` to exercise multi-channel fallback logic, then break into composable units
  - [ ] Schedule follow-up complexity scans after each refactor to track reductions

**Success Criteria**:
- [x] Significant reduction in high complexity functions (get_personalization_data completed)
- [x] Improved code readability and maintainability
- [x] All tests continue to pass after refactoring
- [x] Clear documentation of refactoring patterns
- [ ] Measurable improvement in audit metrics (ongoing)

---


### **Message Deduplication Advanced Features**

**Status**: **IN PROGRESS**  
**Priority**: Low  
**Effort**: Large  
**Started**: 2025-11-11  
**Last Updated**: 2025-11-20

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

### **2025-09-07 - Test Standardization Burn-in** **MOSTLY COMPLETE**

**Status**: **MOSTLY COMPLETE**  
**Priority**: High  
**Effort**: Small  
**Last Updated**: 2025-11-20

**Objective**: Maintain stability by validating order independence and removing test-only aids over time.

**Completed**:
- [x] Tooling for burn-in validation runs (COMPLETED 2025-11-11)
  - [x] `--no-shim`, `--random-order`, `--burnin-mode` options added
- [x] Fixed order-dependent test failures (COMPLETED 2025-11-11)
  - [x] All 7 identified tests fixed
  - [x] All tests pass with `--burnin-mode` (2,809 passed, 1 skipped)
- [x] Sweep and resolve Discord/aiohttp deprecations (COMPLETED)
  - [x] Warning count reduced to external-only (4 Discord library warnings expected)

**Remaining Work**:
- [ ] Nightly run with `--burnin-mode`; track regressions
- [ ] After 2 weeks green with `--burnin-mode`, gate or remove remaining test-only diagnostics

**Success Criteria**:
- [x] Tooling in place (COMPLETED)
- [ ] No failures under `--burnin-mode` runs for 2 consecutive weeks (ongoing monitoring)
- [x] CI warning count reduced to external-only (COMPLETED)

---

### **2025-08-25 - Comprehensive Task System Improvements** [IN PROGRESS] **IN PROGRESS**

**Status**: [IN PROGRESS] **IN PROGRESS**  
**Priority**: High  
**Effort**: Large (Multi-phase implementation)  
**Dependencies**: None

**Objective**: Implement comprehensive improvements to the task management system to enhance user experience, productivity, and system intelligence.

**Background**: The current task system provides basic CRUD operations but lacks advanced features that would significantly improve user productivity and task management effectiveness. Users need recurring tasks, templates, smart suggestions, and better organization capabilities.

**Implementation Plan**:

#### **Phase 1: Foundation Improvements (High Impact, Low-Medium Effort)** **PARTIALLY COMPLETE**

**1. Recurring Tasks System** **COMPLETED**
- **Status**: **COMPLETED**
- **Note**: Recurring tasks functionality implemented (recurrence_pattern, recurrence_interval, next_due_date, auto-creation, UI components)
- Testing required

**2. Task Templates & Quick Actions** [WARNING] **PLANNED**
- **Why it matters**: Reduces friction for common task creation patterns
- **Implementation**:
  - [ ] Pre-defined task templates (medication, exercise, appointments, chores)
  - [ ] Quick-add buttons for common tasks
  - [ ] Template categories (health, work, personal, household)
  - [ ] Custom user templates with saved preferences
  - [ ] Template management UI

**3. Smart Task Suggestions** [WARNING] **PLANNED**
- **Why it matters**: Helps users discover what they might need to do based on patterns
- **Implementation**:
  - [ ] AI-powered task suggestions based on time patterns
  - [ ] Suggestions based on recent task completion history
  - [ ] User goal and preference-based suggestions
  - [ ] "Suggested for you" section in task list
  - [ ] One-click task creation from suggestions

**4. Natural Language Task Creation** [WARNING] **PLANNED**
- **Why it matters**: Makes task creation more intuitive and faster
- **Implementation**:
  - [ ] Natural language parsing for task creation
  - [ ] Support for "Remind me to take medication every morning at 8am"
  - [ ] Support for "I need to call the dentist this week"
  - [ ] Support for "Schedule a task for cleaning the kitchen every Sunday"
  - [ ] Smart parsing of natural language into structured task data

**4a. Interactive Task Creation Follow-up Questions** [WARNING] **PLANNED**
- **Why it matters**: Allows users to provide additional task information (due date, priority, reminders) without requiring all details upfront
- **Implementation**:
  - [ ] Implement follow-up question system in conversation manager/command handler
  - [ ] After initial task creation, ask for optional information:
    - [ ] Due date (with 2-3 quick selectable options + custom input + skip)
    - [ ] Priority level (with 2-3 quick selectable options + custom input + skip)
    - [ ] Reminder preferences (with 2-3 quick selectable options + custom input + skip)
  - [ ] Provide skip option for individual questions and "skip all" option
  - [ ] Store task with minimal info initially, update as user provides additional details
  - [ ] Integrate with command parser to recognize task creation commands
  - [ ] Add conversation state tracking for multi-turn task creation flow
- **Dependencies**: Conversation manager enhancements, command handler improvements
- **Notes**: This is a larger feature that requires integration between AI chatbot, conversation manager, and command handlers

#### **Phase 2: Intelligence & Workflow Improvements (Medium Impact, Medium Effort)** [WARNING] **PLANNED**

**5. Task Dependencies & Prerequisites** [WARNING] **PLANNED**
- **Why it matters**: Many tasks have logical dependencies that affect completion
- **Implementation**:
  - [ ] "Blocked by" and "Blocks" relationships between tasks
  - [ ] Visual dependency chains in task list
  - [ ] Automatic unblocking when prerequisites are completed
  - [ ] Smart task ordering suggestions

**6. Context-Aware Task Reminders** [WARNING] **PLANNED**
- **Why it matters**: Reminders are more effective when delivered at the right moment
- **Implementation**:
  - [ ] Location-based reminders (when near relevant places)
  - [ ] Time-based context (morning routines, evening wind-down)
  - [ ] Mood-aware suggestions (easier tasks when energy is low)
  - [ ] Integration with external calendar events

**7. Batch Task Operations** [WARNING] **PLANNED**
- **Why it matters**: Reduces friction when managing multiple related tasks
- **Implementation**:
  - [ ] Select multiple tasks for bulk operations
  - [ ] Batch complete, delete, or update tasks
  - [ ] Bulk priority changes
  - [ ] Mass tag assignment

**8. Task Time Tracking** [WARNING] **PLANNED**
- **Why it matters**: Helps users estimate task duration and plan their time better
- **Implementation**:
  - [ ] Start/stop timer for tasks
  - [ ] Estimated vs actual time tracking
  - [ ] Time-based task suggestions
  - [ ] Productivity insights based on time data

**9. Task Notes & Attachments** [WARNING] **PLANNED**
- **Why it matters**: Keeps all relevant information with the task
- **Implementation**:
  - [ ] Rich text notes for tasks
  - [ ] File attachments (images, documents)
  - [ ] Voice notes for quick task capture
  - [ ] Link attachments (URLs, references)

**10. Task Difficulty & Energy Tracking** [WARNING] **PLANNED**
- **Why it matters**: Helps users match tasks to their current energy levels
- **Implementation**:
  - [ ] Self-rated task difficulty (1-5 scale)
  - [ ] Energy level tracking when completing tasks
  - [ ] Smart task scheduling based on energy patterns
  - [ ] "Low energy mode" with easier task suggestions

#### **Phase 3: Advanced Features (Medium Impact, High Effort)** [WARNING] **FUTURE CONSIDERATION**

**11. Priority Escalation System** [WARNING] **FUTURE CONSIDERATION**
- **Why it matters**: Prevents tasks from being forgotten when they become urgent
- **Implementation**:
  - [ ] Automatic priority increase for overdue tasks
  - [ ] Escalation notifications ("This task is now 3 days overdue")
  - [ ] Smart escalation timing (not too aggressive, not too passive)
  - [ ] Visual indicators for escalated tasks
  - [ ] **Note**: To be optional and configurable

**12. Enhanced Task Analytics** [WARNING] **FUTURE CONSIDERATION**
- **Why it matters**: Helps users understand their patterns and improve productivity
- **Implementation**:
  - [ ] Completion rate trends over time
  - [ ] Peak productivity hours identification
  - [ ] Task category performance analysis
  - [ ] Streak tracking for recurring tasks
  - [ ] Predictive completion estimates

**13. AI Task Optimization** [WARNING] **FUTURE CONSIDERATION**
- **Why it matters**: Helps users work more efficiently
- **Implementation**:
  - [ ] Task order optimization suggestions
  - [ ] Break down complex tasks into subtasks
  - [ ] Suggest task combinations for efficiency
  - [ ] Identify potential task conflicts
  - [ ] **Note**: To be optional and configurable

**14. Advanced Task Views** [WARNING] **FUTURE CONSIDERATION**
- **Why it matters**: Different views help users organize and focus on what matters
- **Implementation**:
  - [ ] Calendar view (daily, weekly, monthly)
  - [ ] Kanban board view (To Do, In Progress, Done)
  - [ ] Timeline view for project-based tasks
  - [ ] Focus mode (hide completed tasks, show only today)

**15. Smart Task Grouping** [WARNING] **FUTURE CONSIDERATION**
- **Why it matters**: Helps users see related tasks together
- **Implementation**:
  - [ ] Auto-grouping by location, time, or category
  - [ ] Project-based task grouping
  - [ ] Smart tags based on task content
  - [ ] Dynamic task lists based on criteria

**16. Task Sync & Backup** [WARNING] **FUTURE CONSIDERATION**
- **Why it matters**: Ensures tasks are never lost and accessible everywhere
- **Implementation**:
  - [ ] Cloud sync for task data
  - [ ] Automatic backups
  - [ ] Cross-device task access
  - [ ] Export/import task data

**17. Task Performance Optimization** [WARNING] **FUTURE CONSIDERATION**
- **Why it matters**: Faster task operations improve user experience
- **Implementation**:
  - [ ] Lazy loading for large task lists
  - [ ] Efficient task search and filtering
  - [ ] Optimized reminder scheduling
  - [ ] Background task processing

**Success Criteria**:
- Recurring tasks work seamlessly with existing task system
- Task templates reduce task creation time by 50%
- Smart suggestions improve task discovery and completion
- Natural language creation is intuitive and accurate
- All improvements maintain backward compatibility
- System performance remains optimal

**Risk Assessment**:
- **High Impact**: Affects core task management functionality
- **Mitigation**: Incremental implementation with thorough testing
- **Rollback**: Maintain backward compatibility throughout implementation

---



### **Phase 1: Enhanced Task & Check-in Systems** **PARTIALLY COMPLETE**

**Status**: **PARTIALLY COMPLETE**  
**Priority**: High  
**Last Updated**: 2025-11-20

**Completed** (documented in changelog):
- [x] **Enhanced Task Reminder System** (COMPLETED - documented in changelog)
  - Priority-based weighting, due date proximity weighting, critical priority level, no due date option
- [x] **Semi-Random Check-in Questions** (COMPLETED - documented in changelog)
  - Weighted selection, question variety, category balancing

**Remaining Work**:
- [ ] **Check-in Response Analysis** (High Impact, Medium Effort)
  - [ ] Implement pattern analysis of responses over time
  - [ ] Add progress tracking for mood trends
  - [ ] Create response categorization and sentiment analysis
  - [ ] Generate insights for AI context enhancement
  - [ ] Test pattern analysis accuracy
  - [ ] Validate progress tracking metrics
- [ ] **Enhanced Context-Aware Conversations** (Medium Impact, Medium Effort)
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

**Goal**: Implement mood-responsive AI conversations and advanced emotional intelligence

**Current State**:
- [OK] **Mood data included in context**: AI chatbot includes mood and energy data from check-ins in context (`ai/chatbot.py`, `ai/context_builder.py`)
- [OK] **Mood trend analysis**: Context builder analyzes mood trends (improving/declining/stable)
- [OK] **Emotional intelligence in system prompt**: System prompt includes emotional intelligence instructions
- [OK] **Mood-aware completion messages**: Check-in completion messages adapt based on mood/energy (`conversation_flow_manager.py`)
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

**Goal**: Implement proactive suggestion system and advanced AI capabilities  
**Status**: Planning Phase  
**Estimated Duration**: 3-4 weeks

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
- [ ] **Smart Home Integration Planning** [WARNING] **LONG-TERM/FUTURE** - Not applicable for current single-user personal assistant; mentioned in PROJECT_VISION.md Phase 3 but not a current priority
  - [ ] Research smart home APIs and protocols
  - [ ] Design integration architecture for future implementation
  - [ ] Document requirements and constraints
  - [ ] Create integration roadmap and timeline
  - [ ] Test integration feasibility with sample APIs
  - [ ] Validate integration architecture design
  - **Note**: This is a future consideration from PROJECT_VISION.md Phase 3. With only 1-2 users and focus on core mental health assistant features, smart home integration is not currently applicable or prioritized.

---

### **UI Migration Plan**

**Status**: Foundation, Dialogs, and Widgets Complete; Testing Remaining  
**Last Updated**: 2025-11-20

**Completed** (documented in changelogs):
- [x] **Foundation**: PySide6/Qt migration, file reorganization, naming conventions, widget refactoring, user data migration, signal-based updates, 100% function documentation
- [x] **Dialog Implementation**: All 7 dialogs complete (Category Management, Channel Management, Check-in Management, User Profile, Account Creator, Task Management, Schedule Editor)
- [x] **Widget Implementation**: All 6 widgets complete (TagWidget, Task Settings, Category Selection, Channel Selection, Check-in Settings, User Profile Settings)
- [x] **Main UI Application**: 21 behavior tests complete

**Remaining Work**:
- [ ] **Testing & Validation**
  - [ ] Individual Dialog Testing - 8 dialogs need testing
  - [ ] Widget Testing - 8 widgets need testing
  - [ ] Integration Testing - Cross-dialog communication
  - [ ] Performance Optimization - UI responsiveness monitoring
  - [ ] Windows path compatibility tests around messages defaults and config path creation
  - [ ] Expand preferences save/load tests to cover Pydantic normalization and legacy flag handling (full vs partial updates)
  - [ ] Add tests for read-path normalization (`normalize_on_read=True`) at critical read sites (schedules, account/preferences)
- [ ] **UI Quality Improvements**
  - [ ] Fix Dialog Integration (main window updates after dialog changes)
  - [ ] Add Data Validation across all forms
  - [ ] Improve Error Handling with clear, user-friendly messages
  - [ ] Monitor and optimize UI responsiveness for common operations

---

### **Legacy Code Removal Plan**

**Status**: Legacy Channel Removal Complete, General Legacy Monitoring Active  
**Last Updated**: 2025-11-20

**Completed**:
- [x] **Legacy Channel Code Removal** (COMPLETED 2025-08-03, documented in changelog)
  - Removed LegacyChannelWrapper, legacy channel properties, modern interface migration complete
- [x] **Legacy Code Marking** (COMPLETED)
  - All legacy code marked with warnings and removal plans

**Active Work**:
- [ ] **Monitoring Phase**: Monitor app logs for LEGACY warnings (preferences nested 'enabled' flags) for 2 weeks
- [ ] **Removal Phase**: Execute removals listed in TODO.md and update tests accordingly
  - Account Creator Dialog compatibility methods
  - User Profile Settings Widget legacy fallbacks
  - Discord Bot legacy methods

---

### **Testing Strategy Plan**

**Status**: Core, Communication, and Supporting Modules Complete; UI Layer and Integration Testing Remaining  
**Last Updated**: 2025-11-20

**Completed** (documented in changelogs):
- [x] **Core Module Testing**: 8 modules (Response Tracking, Service Utilities, Validation, Schedule Management, Task Management, Scheduler, Service, File Operations) - 192+ behavior tests
- [x] **Bot/Communication Testing**: 6 modules (Conversation Manager, User Context Manager, Discord Bot, AI Chatbot, Account Management, User Management) - 111 behavior tests
- [x] **Supporting Module Testing**: 5 modules (Error Handling, Config, Auto Cleanup, Check-in Analytics, Logger) - 62 behavior tests
- [x] **UI Layer Testing**: Main UI Application (21 tests), Individual Dialogs (12 tests), Widgets (14 tests)

**Remaining Work**:
- [ ] **UI Layer Testing**
  - [ ] Expand coverage for remaining UI modules
  - [ ] Individual Dialog Testing (comprehensive behavior tests)
  - [ ] TagWidget validation in both modes
  - [ ] Simple Widget Testing - 7 failures in basic widget tests (constructor parameter issues)
  - [ ] Expand Testing Framework for under-tested modules
- [ ] **Integration Testing**
  - [ ] Cross-module workflows
  - [ ] End-to-end user scenarios
  - [ ] Performance testing

---

### **UI Component Testing Strategy Plan**

**Status**: **IN PROGRESS**  
**Priority**: High  
**Effort**: Medium  
**Last Updated**: 2025-11-20

**Objective**: Comprehensive strategy for testing UI components with proper isolation, preventing hanging tests, and ensuring all UI functionality works correctly.

**Critical Testing Challenges**:
- UI windows hanging (tests create real Qt windows that don't close properly)
- Tests affecting each other (UI state persists between tests)
- Creating real Windows tasks (UI tests accidentally trigger system operations)
- Test logging isolation (UI tests interfere with logging systems)
- Tests affecting real system data (UI tests modify production data)

**Prevention Strategies**:
- Headless Mode: Use `QApplication.setAttribute(Qt.AA_ShareOpenGLContexts, False)` for headless testing
- Proper Cleanup: Always close dialogs and clean up Qt objects
- Mock External Systems: Never create real Windows tasks or system resources
- Test Data Isolation: Use `tests/data/` directory only
- Logging Isolation: Use test-specific log files

**Implementation Phases**:

#### **Phase 1: Core UI Components (Priority 1)**
Target modules with <50% coverage:
- [ ] `ui/ui_app_qt.py` (27.6%) - Main application bootstrap
- [ ] `ui/dialogs/task_crud_dialog.py` (11.2%) - Task CRUD operations
- [ ] `ui/generate_ui_files.py` (0.0%) - UI file generation

#### **Phase 2: Dialog Components (Priority 2)**
Target modules with 50-70% coverage:
- [ ] `ui/dialogs/account_creator_dialog.py` (48.1%)
- [ ] `ui/dialogs/checkin_management_dialog.py` (49.0%)
- [ ] `ui/dialogs/task_management_dialog.py` (51.1%)
- [ ] `ui/dialogs/category_management_dialog.py` (51.5%)

#### **Phase 3: Widget Components (Priority 3)**
Target modules with 70-90% coverage:
- [ ] `ui/widgets/task_settings_widget.py` (50.6%)
- [ ] `ui/widgets/channel_selection_widget.py` (57.0%)
- [ ] `ui/widgets/checkin_settings_widget.py` (59.1%)
- [ ] `ui/widgets/category_selection_widget.py` (68.3%)

**Test Categories**:
- [ ] Button Functionality Testing (click actions, state changes, event handling, keyboard shortcuts)
- [ ] Input Validation Testing (text, numeric, date/time, file, dropdown/combo)
- [ ] Dialog Workflow Testing (open/close, save/cancel, validation, navigation, modal behavior)
- [ ] Widget Interaction Testing (combinations, data binding, event propagation, state management)
- [ ] Error Handling Testing (error states, validation errors, network errors, system errors)

**Success Criteria**:
- [ ] All UI components have comprehensive test coverage
- [ ] No hanging tests or UI windows
- [ ] No interference with real system data
- [ ] All button clicks, inputs, and workflows tested
- [ ] Error handling and recovery tested

**Note**: See `development_docs/UI_COMPONENT_TESTING_STRATEGY.md` for detailed test patterns and implementation examples (archived reference).

---

### **Channel Interaction Implementation Plan**

**Status**: Email Integration Complete, Cross-Channel Sync Remaining  
**Last Updated**: 2025-11-20

**Completed**:
- [x] Email Integration - Full email-based interaction system (COMPLETED 2025-11-11, documented in changelog)
  - Email message body extraction, polling loop, user mapping, message routing, response sending

**Remaining Work**:
- [ ] Cross-Channel Sync - Synchronize data across supported channels
  - Note: Telegram integration has been removed from scope

---



**Note**: The following sections (Phase 2-4) are duplicates of items already tracked in "Comprehensive Task System Improvements" above. Individual Task Reminders is completed (custom reminder times implemented in scheduler.py and task_management.py). Recurring Tasks is completed (documented in Phase 1 above). All other items are tracked in the Comprehensive Task System Improvements plan.

---

### **Dynamic Check-in Questions Plan** [WARNING] **PARTIALLY COMPLETE**

**Status**: **PARTIALLY COMPLETE**  
**Priority**: Medium  
**Effort**: Medium  
**Date**: 2025-11-10  
**Last Updated**: 2025-11-20

**Goal**: Implement fully dynamic custom check-in questions (UI + data + validation).

**Completed**:
- [x] Data model exists (questions.json with types, validation, categories)
- [x] Validation rules implemented (DynamicCheckinManager validates all question types)
- [x] Persist/Load enabled state (user preferences store enabled/disabled state)
- [x] Integration into check-in flow (ConversationManager uses dynamic questions with weighted selection)
- [x] UI for enabling/disabling (CheckinSettingsWidget has checkboxes for all predefined questions)

**What's Missing**:
- [ ] **Custom question creation**: Allow users to add their own questions (text, type, validation)
- [ ] **Question editing**: Allow users to edit custom questions (not just predefined ones)
- [ ] **Question removal**: Allow users to remove custom questions
- [ ] **Question ordering**: Allow users to define custom question order (beyond weighted selection)
- [ ] **Question presets**: Provide preset question sets (e.g., "Minimal", "Comprehensive", "Health Focus")
- [ ] **Data persistence for custom questions**: Store custom questions in user data (currently only enabled/disabled state)
- [ ] **Validation for custom questions**: Ensure custom questions have proper validation rules
- [ ] **UI tests**: Add behavior tests for custom question management

---

## [IN PROGRESS] **Plan Maintenance**

### **How to Update This Plan**
1. **Add new plans** with clear goals and checklist format
2. **Update progress** by checking off completed items
3. **Remove fully completed plans** - document them in CHANGELOG files instead
4. **Keep reference information** current and useful
5. **Remove outdated information** to maintain relevance

### **Success Criteria**
- **Actionable**: Each item is a specific, testable action
- **Trackable**: Clear progress indicators and completion status
- **Maintainable**: Easy to update and keep current
- **Useful**: Provides value for both human developer and AI collaborators

---

## [REFERENCE] **Reference Information**

### **Key UI Patterns**
- **Widget -> Dialog -> Core**: Data flows from widgets through dialogs to core handlers
- **Validation**: Centralized validation in `core/user_data_validation.py`
- **Error Handling**: `@handle_errors` decorator with user-friendly messages
- **Signal-Based Updates**: UI updates triggered by data changes

### **Development Guidelines**
- **UI Files**: Create .ui files in `ui/designs/` and generate Python with pyside6-uic
- **Testing**: Use behavior tests that verify side effects and real functionality
- **Legacy Code**: Mark with `LEGACY COMPATIBILITY` comments and removal plans
- **Documentation**: Update CHANGELOG files after testing, not before

### **Architecture Decisions**
- **Channel-Neutral Design**: All channels use same interaction handlers
- **Modular Structure**: Clear separation between UI, bot, and core layers
- **Data Flow**: User data centralized through `core/user_data_handlers.py`
- **Testing Strategy**: Behavior tests preferred over unit tests for real functionality

### **AI Development Patterns**
- **Use existing patterns** from working dialogs and widgets
- **Follow validation patterns** from `core/user_data_validation.py`
- **Test data persistence** when modifying dialogs
- **Check widget integration** when adding new features

### **AI Development Commands**
- `python ui/ui_app_qt.py` - Launch main admin interface
- `python run_mhm.py` - Launch admin UI (background service started separately)
- `python run_tests.py` - Run tests including UI tests

### **Key UI Files**
- `ui/ui_app_qt.py` - Main PySide6 application
- `ui/dialogs/` - Dialog implementations
- `ui/widgets/` - Reusable widget components
- `core/user_data_validation.py` - Centralized validation logic

### **UI Design Patterns**
- **Dialog Pattern**: Inherit from QDialog, use widgets for data entry
- **Widget Pattern**: Inherit from QWidget, implement get/set methods
- **Validation Pattern**: Use `validate_schedule_periods` for time periods
- **Error Pattern**: Use `@handle_errors` decorator with QMessageBox

### **Testing Framework Standards**
- **Real Behavior Testing**: Focus on actual side effects and system changes
- **Test Isolation**: Proper temporary directories and cleanup procedures
- **Side Effect Verification**: Tests verify actual file operations and state changes
- **Comprehensive Mocking**: Mock file operations, external APIs, and system resources
- **Error Handling**: Test system stability under various error conditions
- **Performance Testing**: Test system behavior under load and concurrent access

### **Test Quality Metrics**
- **Success Rate**: 99.7% for covered modules (384 tests passing, 1 skipped, 34 warnings)
- **Coverage**: 48% of codebase tested (17/31+ modules)
- **Test Types**: Unit, integration, behavior, and UI tests properly organized
- **Patterns**: Established comprehensive real behavior testing approach

---

## [DETAILED] **Detailed Legacy Code Inventory**

### **1. Schedule Management Legacy Keys** **COMPLETED**
**Location**: `core/schedule_management.py`  
**Status**: Legacy `'start'`/`'end'` key support removed - code now only uses canonical `'start_time'`/`'end_time'` keys
**Note**: `migrate_legacy_schedule_keys()` function no longer exists (file is 569 lines, not 573+). Legacy support appears to have been removed.

### **2. Schedule Management Legacy Format** **COMPLETED**
**Location**: `core/schedule_management.py`  
**Status**: Legacy format without periods wrapper removed - all data now uses periods wrapper format
**Note**: Line 488 explicitly states "All data now uses periods wrapper format - no legacy migration needed"

### **3. User Data Access Legacy Wrappers** [WARNING] **MEDIUM PRIORITY**
**Location**: `core/user_data_handlers.py`  
**Issue**: Legacy wrapper functions for backward compatibility  
**Timeline**: Complete when no legacy warnings appear for 1 week

### **4. Account Creator Dialog Compatibility Methods** **VERIFY STATUS**
**Location**: `ui/dialogs/account_creator_dialog.py`  
**Status**: Lines 326-347 show normal methods (keyPressEvent, username property) - no compatibility methods found
**Note**: Line numbers may be outdated. Need to verify if compatibility methods still exist elsewhere in file.

### **5. User Profile Settings Widget Legacy Fallbacks** **VERIFY STATUS**
**Location**: `ui/widgets/user_profile_settings_widget.py`  
**Status**: Lines 395, 402, 426, 450, 462 show modern code - no legacy fallback comments found
**Note**: Line numbers may be outdated. Need to verify if legacy fallbacks still exist elsewhere in file.

### **6. Discord Bot Legacy Methods** **VERIFY STATUS**
**Location**: `communication/communication_channels/discord/bot.py`  
**Status**: Lines 518-564 show `initialize()` method, not legacy start/stop methods
**Note**: File appears to have been refactored. Need to verify if legacy methods still exist elsewhere in file.

### **7. Communication Manager Legacy Wrappers** **COMPLETED**
**Location**: `communication/core/channel_orchestrator.py`  
**Status**: LegacyChannelWrapper and legacy channel access removed (COMPLETED 2025-08-03, documented in changelog)
**Note**: This was completed as part of Legacy Channel Code Removal plan

### **8. User Context Legacy Format Conversion** **COMPLETED**
**Location**: `user/user_context.py`  
**Status**: Legacy format conversion/extraction code has been removed - all code now uses modern formats directly

### **9. Test Utilities Backward Compatibility** [WARNING] **LOW PRIORITY**
**Location**: `tests/test_utilities.py`  
**Issue**: Multiple backward compatibility paths for test data directories  
**Timeline**: Complete after 1 week of monitoring

### **10. UI App Legacy Communication Manager** **VERIFY STATUS**
**Location**: `ui/ui_app_qt.py`  
**Status**: Line 1496 shows `_send_test_message__get_selected_category()`, not legacy communication manager shutdown
**Note**: Line number is outdated. Need to search file for any remaining legacy communication manager handling code.

---
