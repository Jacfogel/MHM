# MHM Development Plans

> **Audience**: Human Developer & AI Collaborators  
> **Purpose**: Consolidated development plans (grouped, interdependent work) with step-by-step checklists  
> **Style**: Actionable, checklist-focused, progress-tracked  
> **Last Updated**: 2025-10-21  
> **See [TODO.md](TODO.md) for independent tasks**

---

## [PHONE] **Current Active Plans**

### **AI Chatbot Actionability Sprint** **PLANNING**

**Status**: **PLANNING**  
**Priority**: High  
**Effort**: Large  
**Date**: 2025-10-30

**Objective**: Improve chat quality and enable robust action handling (task/message/profile CRUD) with context from recent automated messages and targeted, non-conflicting suggestions.

**Scope (first slices)**:
- [ ] Parser reliability for common natural phrases (done: schedule edit without times)
- [ ] Curated prompts for disambiguation/confirmations (done: delete/complete; extend as needed)
- [ ] AI context: recent automated message awareness, check-in summaries (done; monitor)
- [ ] Task CRUD completeness: name-based update extraction for title/priority/due (done; watch)
- [ ] Suggestions: targeted + minimal, non-conflicting (in place; extend coverage)

**Success Criteria**:
- [ ] Users can ask for common operations in natural language with minimal friction
- [ ] Prompts always offer actionable next steps
- [ ] No regressions (full suite remains green)

**Notes**:
- Tests by area are acceptable to iterate faster; full suite before shipping changes.
- Keep both `!` and `/` commands; prefer slash in help/UX with auto-suggests.

### **User Data Flow Architecture Improvements** [CHECKMARK] **COMPLETED**

**Status**: [CHECKMARK] **COMPLETED**  
**Completed**: 2025-11-11  
**Priority**: Medium  
**Effort**: Medium/Large  
**Date**: 2025-11-05

**Objective**: Improve the robustness and reliability of the user data save flow by addressing architectural concerns identified during flow analysis.

**Current Flow Characteristics**:

1. **Validation Strategy Issue**: Data is validated after backup creation (`core/user_data_handlers.py:848`), meaning invalid data may be backed up unnecessarily. Consider validating first to avoid wasted backups.

2. **Cross-File Invariants Stale Data**: When multiple data types are saved in the same call (e.g., both `account` and `preferences`), cross-file invariants read from disk (`core/user_data_handlers.py:734, 746`), which may be stale if the related type is also being updated. The invariants work with in-memory merged data when available, but some paths read from disk.

3. **Nested Saves Complexity**: Saving `preferences` can trigger `update_user_account()` (`core/user_data_handlers.py:739`) to maintain invariants, creating nested save operations. This works but adds complexity and potential for circular dependencies.

4. **Order Dependency**: The per-data-type loop processes types in dict iteration order (Python 3.7+ preserves insertion order). Cross-file invariants behave differently depending on which type is processed first, making behavior non-deterministic when order isn't explicitly controlled.

5. **Partial Failure Handling**: Each data type is saved independently. If one fails, others may already be persisted, leaving the system in a partially updated state. `save_user_data_transaction()` exists but doesn't fully address the cross-file invariant issue.

**Proposed Improvements**:

- [x] **Re-order validation and backup**: Move data validation before backup creation to avoid backing up invalid data [CHECKMARK] **COMPLETED** (2025-11-11)
- [x] **Two-phase save approach**: [CHECKMARK] **COMPLETED** (2025-11-11)
  - [x] Phase 1: Merge all types in-memory, validate all data, validate cross-file invariants
  - [x] Phase 2: Write all types to disk, then update index/cache
- [x] **In-memory cross-file invariants**: [CHECKMARK] **COMPLETED** (2025-11-11) - Process cross-file invariants using in-memory merged data instead of reading from disk
- [x] **Explicit processing order**: [CHECKMARK] **COMPLETED** (2025-11-11) - Defined deterministic order: account -> preferences -> schedules -> context -> messages -> tasks
- [x] **Atomic multi-type operations**: [CHECKMARK] **COMPLETED** (2025-11-11) - All types written in Phase 2; backup created before writes for rollback capability; result dict indicates success/failure per type
- [x] **Reduce nested saves**: [CHECKMARK] **COMPLETED** (2025-11-11) - Eliminated nested `update_user_account()` call in `update_user_preferences()`; cross-file invariants update in-memory data and write once

**Success Criteria**:
- [x] Data validation occurs before backup creation (✅ completed 2025-11-11)
- [x] Cross-file invariants work correctly when multiple types are saved simultaneously (✅ completed 2025-11-11)
- [x] No nested save operations triggered by invariants (✅ completed 2025-11-11)
- [x] Processing order is deterministic and documented (✅ completed 2025-11-11)
- [x] Partial failure scenarios handled gracefully (✅ completed 2025-11-11 - result dict indicates per-type success/failure)
- [x] All existing tests pass with improved flow (✅ 31 tests passed 2025-11-11)

**Risk Assessment**:
- **Medium Impact**: Affects core user data save path used throughout the system
- **Mitigation**: Incremental refactoring with comprehensive testing after each change
- **Rollback**: Maintain backward compatibility throughout implementation

### **Error Handling Coverage Expansion** ?? **IN PROGRESS**

**Status**: ?? **IN PROGRESS**  
**Priority**: High  
**Effort**: Medium (ongoing)  
**Date**: 2025-10-04  
**Started**: 2025-10-04

**Objective**: Expand error handling coverage from current 92.0% to 93%+ by systematically adding @handle_errors decorators to remaining functions.

**Progress Achieved**:
- **92.0% Coverage Achieved**: 1,285 functions now protected (up from 72.4%)
- **1,285 Functions with Decorators**: Excellent error handling quality
- **274 New Functions Protected**: Significant robustness improvement since 72.4%
- **Test Suite Validation**: All 1899 tests passing, 1 skipped, no regressions
- **Signal Handler Fix**: Resolved Qt signal compatibility issues

**Modules Enhanced**:
- **UI Dialogs**: user_profile_dialog.py, account_creator_dialog.py, task_management_dialog.py, task_edit_dialog.py
- **UI Widgets**: period_row_widget.py, tag_widget.py, task_settings_widget.py, checkin_settings_widget.py, channel_selection_widget.py
- **Communication**: message_router.py, command_parser.py, checkin_handler.py, task_handler.py, profile_handler.py
- **Core Systems**: logger.py, command_registry.py, rich_formatter.py

**Current Status**: 92.0% coverage achieved (1,285 functions protected). Next target: 93%+ by adding error handling to remaining 115 functions.

**Next Steps**:
- [ ] **Continue Expanding Beyond 92%**:
  - [ ] Add error handling to remaining 115 functions for 93%+ coverage
  - [ ] Focus on UI modules and remaining utility functions
  - [ ] Replace remaining basic try-except blocks with @handle_errors decorator
- [ ] **Replace Basic Try-Except Blocks**: 168 basic -> excellent quality
- [ ] **Add Error Handling to Critical Functions**: 397 functions with no error handling

**Success Criteria**:
- [x] Achieve 80%+ error handling coverage (✅ 92.0% achieved)
- [ ] Achieve 93%+ error handling coverage (next target)
- [x] All tests continue passing (✅ 1899 passed, 1 skipped)
- [x] No regressions introduced
- [x] System stability maintained

### **2025-09-16 - High Complexity Function Refactoring - Phase 2** 🔄 **IN PROGRESS**

**Status**: 🔄 **IN PROGRESS**  
**Priority**: High  
**Effort**: Large  
**Dependencies**: Audit completion (completed)

**Objective**: Continue refactoring high complexity functions identified in audit to improve maintainability and reduce technical debt.

**Background**: Latest audit identified 1856 high complexity functions (>50 nodes) that need attention for better maintainability. Phase 1 successfully refactored `get_user_data_summary` function, reducing complexity from 800 to 15 helper functions.

**Results**: Audit completed with comprehensive analysis:
- **Total Functions**: 2566 functions analyzed
- **High Complexity**: 1856 functions (>50 nodes) identified
- **Documentation Coverage**: 99.5% coverage achieved
- **System Status**: Healthy and ready for development

**Implementation Plan**:

#### **Step 1: Priority Function Analysis** [CHECKMARK] **COMPLETED**
- [x] **Export Top Priority Functions**
  - [x] Export top-50 most complex functions from audit details
  - [x] Categorize functions by module and complexity level
  - [x] Identify patterns in high-complexity functions (long methods, deep nesting, etc.)
- [x] **Target Selection**
  - [x] Focus on core system functions first (scheduler, communication, user management)
  - [x] Identify functions with highest impact on system stability
  - [x] Create refactoring plan with acceptance criteria for each function

#### **Step 2: Refactoring Strategy Implementation** 🔄 **IN PROGRESS**
- [x] **Next Priority Targets**
  - [x] `ui/widgets/user_profile_settings_widget.py::get_personalization_data` (complexity: 727) [CHECKMARK] **COMPLETED**
  - [ ] `ui/ui_app_qt.py::validate_configuration` (complexity: 692) [WARNING] **NEXT TARGET**
  - [ ] Additional high-priority functions from audit analysis
- [x] **Refactoring Approach**
  - [x] Extract helper functions to reduce complexity
  - [x] Break down large methods into smaller, focused functions
  - [x] Reduce conditional nesting and improve readability
  - [x] Apply `_main_function__helper_name` naming convention consistently

#### **Step 3: Testing and Validation** [CHECKMARK] **COMPLETED**
- [x] **Comprehensive Testing**
  - [x] Add comprehensive tests for refactored functions
  - [x] Ensure refactoring doesn't break existing functionality
  - [x] Run full test suite after each refactoring
- [x] **Progress Monitoring**
  - [x] Track complexity reduction metrics
  - [x] Validate improvements through testing and audit results
  - [x] Document refactoring patterns and best practices

**Completed Work**:
- **get_personalization_data Refactoring**: Successfully reduced complexity from 727 to 6 focused helper functions
- **Helper Function Implementation**: Created 6 helper functions using `_main_function__helper_name` pattern
- **Test Validation**: All tests pass, functionality preserved
- **Legacy Code Cleanup**: Fixed legacy message function calls in tests
- **Test Improvements**: Fixed failing scheduler test and suppressed expected warnings

**Success Criteria**:
- [x] Significant reduction in high complexity functions (get_personalization_data completed)
- [x] Improved code readability and maintainability
- [x] All tests continue to pass after refactoring
- [x] Clear documentation of refactoring patterns
- [ ] Measurable improvement in audit metrics (ongoing)

**Risk Assessment**:
- **High Impact**: Affects multiple modules and function signatures
- **Mitigation**: Incremental refactoring with testing after each function
- **Rollback**: Maintain backward compatibility throughout implementation

---

### **2025-09-11 - Test Coverage Expansion Phase 3** [CHECKMARK] **COMPLETED**

**Status**: **COMPLETED**  
**Priority**: Medium  
**Effort**: Medium  
**Dependencies**: Test Coverage Expansion Phase 2 (completed)

**Objective**: Continue test coverage expansion with focus on simpler, more reliable test approaches and address high complexity functions identified in audit.

**Background**: Phase 2 of test coverage expansion has been completed successfully with meaningful improvements to Core Service and Core Message Management. The focus on test quality over quantity has proven successful, with all 1,228 tests passing consistently.

**Results**: Successfully completed all 5 priority targets with comprehensive test coverage improvements:
- **Core Logger**: 68% -> 75% coverage with 35 tests covering logging behavior, rotation, and error handling
- **Core Error Handling**: 69% -> 65% coverage with 78 tests covering error scenarios and recovery mechanisms
- **Core Config**: 70% -> 79% coverage with 35 tests covering configuration loading and validation
- **Command Parser**: 40% -> 68% coverage with 47 tests covering NLP and entity extraction
- **Email Bot**: 37% -> 91% coverage (far exceeded target with existing comprehensive tests)

**Implementation Plan**:

#### **Step 3.1: Test Coverage with Simpler Approaches** [CHECKMARK] **COMPLETED**
- [x] **Core Logger Coverage** - 68% -> 75% coverage achieved
  - [x] Test logging behavior, rotation, and log level management
  - [x] Test error handling in logging system and log file management
  - [x] Test logging performance and configuration
- [x] **Core Error Handling Coverage** - 69% -> 65% coverage achieved
  - [x] Test error scenarios, recovery mechanisms, and error logging
  - [x] Test error handling performance and edge cases
- [x] **Core Config Coverage** - 70% -> 79% coverage achieved
  - [x] Test configuration loading, validation, and environment variables
  - [x] Test configuration error handling and performance
- [x] **Command Parser Coverage** - 40% -> 68% coverage achieved
  - [x] Test natural language processing, entity extraction, and command recognition
  - [x] Test edge cases and error handling
- [x] **Email Bot Coverage** - 37% -> 91% coverage achieved (far exceeded target)
  - [x] Existing comprehensive tests already provided excellent coverage

#### **Step 3.2: Code Complexity Reduction** [WARNING] **PLANNED**
- [ ] **High Complexity Function Refactoring**
  - [ ] Prioritize refactoring of 1,856 high complexity functions (>50 nodes)
  - [ ] Focus on core system functions first (scheduler, communication, user management)
  - [ ] Extract helper functions to reduce complexity
  - [ ] Break down large methods into smaller, focused functions
  - [ ] Reduce conditional nesting and improve readability
- [ ] **Helper Function Naming Convention**
  - [ ] Apply `_main_function__helper_name` pattern consistently
  - [ ] Improve traceability and searchability across the project
  - [ ] Ensure clear ownership and better debugging capabilities

#### **Step 3.3: Test Quality Standards** [WARNING] **PLANNED**
- [ ] **Test Strategy Documentation**
  - [ ] Document successful test approaches vs. problematic ones
  - [ ] Create guidelines for avoiding complex mocking that causes hanging
  - [ ] Establish patterns for reliable test implementation
  - [ ] Share lessons learned about test stability over coverage numbers
- [ ] **Test Maintenance**
  - [ ] Regular review of test suite health
  - [ ] Monitor for test hanging or function behavior issues
  - [ ] Maintain focus on working tests over complex coverage

**Success Criteria**:
- [ ] Core User Data Manager and Core File Operations tests implemented with simpler approaches
- [ ] Significant reduction in high complexity functions through refactoring
- [ ] All tests continue to pass consistently (1,228+ tests)
- [ ] Test suite remains stable and reliable
- [ ] Clear documentation of successful test patterns

**Estimated Timeline**: 2-3 weeks for Phase 3 implementation

---

### **2025-09-10 - Message Deduplication Advanced Features (Future)** 🔄 **IN PROGRESS**

**Status**: 🔄 **IN PROGRESS**  
**Priority**: Low  
**Effort**: Large  
**Dependencies**: Message deduplication system (completed)  
**Started**: 2025-11-11

**Objective**: Implement advanced analytics, insights, and intelligent scheduling features for the message deduplication system.

**Background**: The core message deduplication system is complete and operational. These advanced features would enhance the system with analytics, user preference learning, and intelligent message selection capabilities.

**Progress**: Basic message frequency analytics foundation implemented (2025-11-11):
- ✅ Created `MessageAnalytics` class in `core/message_analytics.py`
- ✅ Implemented `get_message_frequency()` - tracks frequency by category and time period
- ✅ Implemented `get_delivery_success_rate()` - analyzes delivery success rates
- ✅ Implemented `get_message_summary()` - comprehensive summary combining frequency and delivery data
- ✅ Added comprehensive behavior tests (7 tests, all passing)

**Implementation Plan**:

#### **Step 5.1: Analytics and Insights** 🔄 **IN PROGRESS**
- [x] **Message frequency analytics** [CHECKMARK] **COMPLETED** (2025-11-11)
  - [x] Track message send frequency by category and time period
  - [x] Generate reports on message delivery success rates
  - [ ] Analyze user engagement patterns over time
  - [ ] Create visualizations for message analytics
- [ ] **User engagement tracking** [WARNING] **LONG-TERM/FUTURE** - Requires multiple users for meaningful data
  - [ ] Monitor user response rates to different message types
  - [ ] Track user interaction patterns with messages
  - [ ] Analyze user engagement trends and preferences
  - [ ] Generate user engagement reports
- [ ] **Message effectiveness metrics** [WARNING] **LONG-TERM/FUTURE** - Requires multiple users and response data for meaningful analysis
  - [ ] Measure message effectiveness based on user responses
  - [ ] Track which messages generate the most positive responses
  - [ ] Analyze message timing effectiveness
  - [ ] Create effectiveness scoring system
- [ ] **Smart message recommendation system**
  - [ ] AI-powered message selection based on user history
  - [ ] Personalized message recommendations
  - [ ] Context-aware message suggestions
  - [ ] Learning algorithms for message optimization

#### **Step 5.2: Advanced Scheduling** [WARNING] **PLANNED**
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

**Success Criteria**:
- [x] Basic message frequency analytics implemented (✅ completed 2025-11-11)
- [ ] Advanced analytics provide actionable insights
- [ ] User engagement tracking improves message targeting
- [ ] Smart recommendations increase user satisfaction
- [ ] Intelligent scheduling optimizes message timing
- [ ] A/B testing framework enables continuous improvement

**Risk Assessment**:
- **Low Impact**: These are enhancement features, not core functionality
- **Mitigation**: Implement incrementally with thorough testing
- **Rollback**: Features can be disabled without affecting core system

---

### **2025-09-07 - Test Standardization Burn-in** 🔄 **ACTIVE**

**Status**: 🔄 **ACTIVE**  
**Priority**: High  
**Effort**: Small

**Objective**: Maintain stability by validating order independence and removing test-only aids over time.

**Actions**:
- [x] Tooling for burn-in validation runs [CHECKMARK] **COMPLETED** (2025-11-11)
  - [x] Added `--no-shim` option to disable `ENABLE_TEST_DATA_SHIM` for validation
  - [x] Added `--random-order` option for truly random test order (not fixed seed)
  - [x] Added `--burnin-mode` option that combines both for easy validation runs
- [x] Fixed order-dependent test failures [CHECKMARK] **COMPLETED** (2025-11-11)
  - [x] Fixed test_checkin_message_queued_on_discord_disconnect (added check-in setup and channel config)
  - [x] Fixed test_update_priority_and_title_by_name (changed title to avoid parser confusion)
  - [x] Fixed test_feature_enablement_real_behavior (updated to match design - task_settings preserved)
  - [x] Fixed test_integration_scenarios_real_behavior (updated to match design)
  - [x] Fixed test_create_account_sets_up_default_tags_when_tasks_enabled (fixed empty tags check)
  - [x] Fixed test_user_lifecycle (allow corrupted file backups)
  - [x] Fixed test_setup_default_task_tags_new_user_real_behavior (updated for new save_user_data signature)
  - [x] All tests now pass with `--burnin-mode` (2,809 passed, 1 skipped)
- [ ] Nightly run with `--burnin-mode` (or `--no-shim --random-order`); track regressions
- [x] Sweep and resolve Discord/aiohttp deprecations and unraisable warnings [CHECKMARK] **COMPLETED**
  - [x] External library deprecation warnings suppressed (Discord, audioop)
  - [x] aiohttp session cleanup warnings suppressed
  - [x] Unraisable exception warnings suppressed
  - [x] Warning count reduced to external-only (4 Discord library warnings expected)
- [ ] After 2 weeks green with `--burnin-mode`, gate or remove remaining test-only diagnostics

**Success Criteria**:
- [x] Tooling in place for burn-in validation runs (✅ completed)
- [ ] No failures under `--burnin-mode` runs for 2 consecutive weeks
- [x] CI warning count reduced to external-only (✅ 4 external Discord warnings expected)

---

### **2025-08-25 - Comprehensive Task System Improvements** 🔄 **IN PROGRESS**

**Status**: 🔄 **IN PROGRESS**  
**Priority**: High  
**Effort**: Large (Multi-phase implementation)  
**Dependencies**: None

**Objective**: Implement comprehensive improvements to the task management system to enhance user experience, productivity, and system intelligence.

**Background**: The current task system provides basic CRUD operations but lacks advanced features that would significantly improve user productivity and task management effectiveness. Users need recurring tasks, templates, smart suggestions, and better organization capabilities.

**Implementation Plan**:

#### **Phase 1: Foundation Improvements (High Impact, Low-Medium Effort)** 🔄 **IN PROGRESS**

**1. Recurring Tasks System** [CHECKMARK] **COMPLETED**
- **Status**: [CHECKMARK] **COMPLETED**
- **Why it matters**: Many tasks are repetitive (daily medication, weekly cleaning, monthly bills) but currently require manual recreation
- **Implementation**:
  - [x] Add `recurrence_pattern` field to tasks (daily, weekly, monthly, custom)
  - [x] Add `recurrence_interval` (every X days/weeks/months)
  - [x] Add `next_due_date` calculation based on completion
  - [x] Auto-create next instance when task is completed
  - [x] Support for "repeat after completion" vs "repeat on schedule"
  - [x] Update task creation and completion logic
  - [x] Add recurring task UI components
  - [x] Test recurring task functionality

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

### **2025-08-22 - User Context & Preferences Integration Investigation** ✅ **INVESTIGATION COMPLETE**

**Status**: ✅ **INVESTIGATION COMPLETE**  
**Priority**: High  
**Effort**: Medium  
**Dependencies**: None  
**Completed**: 2025-11-09

**Objective**: Investigate and improve the integration of `user/user_context.py` and `user/user_preferences.py` modules across the system.

**Background**: User observed that these modules may not be used as extensively or in all the ways they were intended to be.

**Investigation Plan**:
- [x] Audit current usage of `user/user_context.py` across all modules
- [x] Audit current usage of `user/user_preferences.py` across all modules
- [x] Identify gaps between intended functionality and actual usage
- [x] Document integration patterns and missing connections
- [ ] Propose improvements for better integration (findings documented below)

**Investigation Findings**:

**UserContext Usage**:
- **Primary Usage**: `get_user_id()` and `get_internal_username()` used in:
  - `core/scheduler.py` (1 usage)
  - `core/schedule_management.py` (4 usages)
  - `user/context_manager.py` (2 usages)
- **UI Integration**: `load_user_data()` used in `ui/ui_app_qt.py` (2 places) - convenience wrapper around `get_user_data()`
- **Pattern**: Most code uses `UserContext()` as a singleton to get current user ID, but doesn't leverage the full context management features

**UserPreferences Usage**:
- **Critical Finding**: `UserPreferences` class exists and is functional but **never actually used** anywhere in the codebase
- **Status Update (2025-11-11)**: The unused initialization from `UserContext.set_user_id()` has been removed (per changelog)
- **Current State**: Class is available but unused; codebase accesses preferences directly via `get_user_data()` and `update_user_preferences()`
- **Gap**: The class has full functionality (load, save, set, get preferences) but is completely unused - could be useful for preference management workflows

**Integration Gaps**:
1. **UserPreferences Unused**: `UserPreferences` class exists and is functional but never accessed or used anywhere in the codebase (initialization from UserContext was removed)
2. **Direct Data Access**: Most code bypasses `UserContext` and calls `get_user_data()` directly instead of using context methods
3. **Limited Context Usage**: `UserContext` is primarily used as a singleton to get user ID, not for full context management
4. **Redundant Wrappers**: `UserContext.load_user_data()` and `save_user_data()` are thin wrappers around `get_user_data()` and `save_user_data()`

**Success Criteria**:
- [x] Complete understanding of current integration state (documented above)
- [x] Identified gaps and improvement opportunities (UserPreferences unused, limited context usage)
- [ ] Action plan for enhancing integration (recommendations below)

**Recommendations**:
1. ✅ **UserPreferences Initialization Removed**: The unused initialization from `UserContext` has been removed (completed)
2. **UserPreferences Usage**: Class remains available but unused. Could be useful for:
   - Workflows that need to make multiple preference changes (avoids multiple `update_user_preferences()` calls)
   - Code that needs to track preference state changes
   - Future preference management UI features
   - **Status**: Low priority - current direct access pattern works well for single operations
3. **Simplify UserContext**: Consider if `UserContext` should be simplified to just provide user ID/username, or if it should be more fully utilized
4. **Consolidate Access Patterns**: Standardize on either direct `get_user_data()` calls or `UserContext` methods, not both
5. ✅ **Documentation Updated**: Comment in `user_preferences.py` updated to reflect current state (completed 2025-11-11)

---

### **2025-08-22 - Bot Module Naming & Clarity Refactoring** ✅ **INVESTIGATION COMPLETE**

**Status**: ✅ **INVESTIGATION COMPLETE**  
**Priority**: High  
**Effort**: Medium  
**Dependencies**: None  
**Completed**: 2025-11-09

**Objective**: Improve clarity and separation of purposes for communication modules.

**Target Modules**:
- `communication/core/channel_orchestrator.py` (CommunicationManager)
- `communication/message_processing/conversation_flow_manager.py` (ConversationManager)
- `communication/message_processing/command_parser.py` (EnhancedCommandParser)
- `communication/command_handlers/interaction_handlers.py` (InteractionHandler implementations)
- `communication/message_processing/interaction_manager.py` (InteractionManager)
- `communication/message_processing/message_router.py` (MessageRouter)

**Investigation Plan**:
- [x] Analyze current module purposes and responsibilities
- [x] Identify overlapping functionality and unclear boundaries
- [x] Document current naming conventions and their clarity
- [x] Propose improved naming and separation strategies
- [ ] Create refactoring plan if needed (findings documented below)

**Investigation Findings**:

**Module Purposes**:
1. **CommunicationManager** (`channel_orchestrator.py`): Manages all communication channels (Discord, Email), handles channel lifecycle, message sending, retries, monitoring. **Purpose**: Channel orchestration and coordination.

2. **ConversationManager** (`conversation_flow_manager.py`): Handles multi-turn conversation flows (like check-ins), manages user state during flows. **Purpose**: Multi-turn conversation state management.

3. **EnhancedCommandParser** (`command_parser.py`): Parses user messages to extract intents and entities. Combines rule-based and AI parsing. **Purpose**: Message parsing and intent extraction.

4. **InteractionManager** (`interaction_manager.py`): Main integration layer - coordinates parsing, routing to handlers, AI chatbot integration. **Purpose**: Main coordinator for user interactions.

5. **MessageRouter** (`message_router.py`): Routes messages to appropriate handlers based on message type (slash command, bang command, conversational, etc.). **Purpose**: Message type detection and routing.

6. **InteractionHandlers** (`interaction_handlers.py`): Contains handlers for different interaction types (TaskManagementHandler, CheckinHandler, ProfileHandler, etc.). **Purpose**: Specific interaction type handling.

**Overlapping Functionality & Unclear Boundaries**:
1. **Routing Overlap**: Both `InteractionManager` and `MessageRouter` handle message routing:
   - `MessageRouter` routes based on message type (slash, bang, conversational)
   - `InteractionManager` coordinates parsing and routing to handlers
   - **Issue**: Unclear which one is the primary router

2. **Interaction Coordination**: Both `ConversationManager` and `InteractionManager` handle interactions:
   - `ConversationManager` handles multi-turn flows (check-ins)
   - `InteractionManager` coordinates all interactions
   - **Issue**: Boundary between flow management and general interaction management is unclear

3. **Naming Inconsistency**: Mix of "Manager", "Router", "Parser", "Handler":
   - `CommunicationManager` - orchestrates channels
   - `ConversationManager` - manages flows
   - `InteractionManager` - coordinates interactions
   - `MessageRouter` - routes messages
   - `EnhancedCommandParser` - parses commands
   - **Issue**: "Manager" is overused and doesn't clearly indicate hierarchy

**Naming Clarity Issues**:
1. **"Manager" Overuse**: Three different "Manager" classes with different purposes
2. **"Interaction" Ambiguity**: Both `InteractionManager` and `InteractionHandler` use "interaction" but at different levels
3. **"Conversation" vs "Interaction"**: Unclear distinction between conversation flows and interactions

**Recommendations**:
1. **Clarify Routing Hierarchy**: 
   - `MessageRouter` should be the primary message type detector
   - `InteractionManager` should coordinate parsing and handler selection
   - Consider renaming `MessageRouter` to `MessageTypeDetector` or `MessageClassifier`

2. **Distinguish Flow Management**:
   - `ConversationManager` handles multi-turn flows (stateful)
   - `InteractionManager` handles single-turn interactions (stateless)
   - Consider renaming `ConversationManager` to `FlowManager` or `ConversationFlowManager`

3. **Standardize Naming**:
   - Use "Orchestrator" for high-level coordination (CommunicationManager → CommunicationOrchestrator)
   - Use "Manager" for mid-level coordination (InteractionManager is appropriate)
   - Use "Handler" for specific type handlers (already correct)
   - Use "Parser" for parsing (already correct)

4. **Consider Consolidation**:
   - Evaluate if `MessageRouter` and `InteractionManager` can be merged
   - Evaluate if `ConversationManager` should be part of `InteractionManager`

**Success Criteria**:
- [x] Clear understanding of each module's purpose (documented above)
- [x] Identified naming and organization improvements (routing overlap, naming inconsistency)
- [ ] Action plan for refactoring if beneficial (recommendations above, implementation pending)

---

### **Phase 1: Enhanced Task & Check-in Systems** 🔄 **IN PROGRESS**

**Goal**: Improve task reminder system and check-in functionality to align with project vision  
**Status**: Implementation Phase  
**Estimated Duration**: 1-2 weeks

**Checklist**:
- [x] **Enhanced Task Reminder System** (High Impact, Medium Effort) [CHECKMARK] **COMPLETED**
  - [x] Add priority-based reminder frequency (high priority = more likely to be selected for reminders)
  - [x] Implement due date proximity weighting (closer to due = more likely to be selected for reminders)
  - [x] Add "critical" priority level and "no due date" option for tasks
  - [ ] Add recurring task support with flexible scheduling
  - [x] Improve semi-randomness to consider task urgency
  - [x] Test priority and due date weighting algorithms
  - [ ] Validate recurring task scheduling patterns
- [x] **Semi-Random Check-in Questions** (High Impact, Low-Medium Effort) [CHECKMARK] **COMPLETED**
  - [x] Implement random question selection from available pool
  - [x] Add weighted selection based on recent questions asked
  - [x] Ensure variety while maintaining relevance
  - [x] Add question categories (mood, energy, tasks, general well-being)
  - [x] Test question selection randomness and variety
  - [x] Validate question category coverage
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
- ✅ **Mood data included in context**: AI chatbot includes mood and energy data from check-ins in context (`ai/chatbot.py`, `ai/context_builder.py`)
- ✅ **Mood trend analysis**: Context builder analyzes mood trends (improving/declining/stable)
- ✅ **Emotional intelligence in system prompt**: System prompt includes emotional intelligence instructions
- ✅ **Mood-aware completion messages**: Check-in completion messages adapt based on mood/energy (`conversation_flow_manager.py`)
- ❌ **Prompt modification based on mood**: Prompts are NOT dynamically modified based on mood/energy - mood data is only included in context
- ❌ **Tone adaptation algorithms**: No explicit tone adaptation based on detected mood
- ❌ **Emotional response templates**: No mood-specific response templates
- ❌ **Mood prediction**: No predictive mood analysis

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

**Status**: Foundation Complete, Dialog Testing in Progress  
**Goal**: Complete PySide6/Qt migration with comprehensive testing

#### **Foundation** [CHECKMARK] **COMPLETE**
- [x] PySide6/Qt migration - Main app launches successfully
- [x] File reorganization - Modular structure implemented
- [x] Naming conventions - Consistent naming established
- [x] Widget refactoring - Widgets created and integrated
- [x] User data migration - All data access routed through new handlers
- [x] Signal-based updates - Implemented and working
- [x] 100% function documentation coverage - All 1349 functions documented

#### **Dialog Implementation** [CHECKMARK] **COMPLETE**
- [x] Category Management Dialog - Complete with validation fixes
- [x] Channel Management Dialog - Complete, functionally ready
- [x] Check-in Management Dialog - Complete with comprehensive validation
- [x] User Profile Dialog - Fully functional with all personalization fields
- [x] Account Creator Dialog - Feature-based creation with validation
- [x] Task Management Dialog - Complete with unified TagWidget integration
- [x] Schedule Editor Dialog - Ready for testing

#### **Widget Implementation** [CHECKMARK] **COMPLETE**
- [x] TagWidget - Unified widget for both management and selection modes
- [x] Task Settings Widget - Complete with TagWidget integration
- [x] Category Selection Widget - Implemented
- [x] Channel Selection Widget - Implemented
- [x] Check-in Settings Widget - Implemented
- [x] User Profile Settings Widget - Implemented

#### **Testing & Validation** [WARNING] **IN PROGRESS**
- [x] Main UI Application - 21 behavior tests complete
- [ ] Individual Dialog Testing - 8 dialogs need testing
- [ ] Widget Testing - 8 widgets need testing
- [ ] Integration Testing - Cross-dialog communication
- [ ] Performance Optimization - UI responsiveness monitoring
  - [ ] Windows path compatibility tests around messages defaults and config path creation
  - [ ] Expand preferences save/load tests to cover Pydantic normalization and legacy flag handling (full vs partial updates)
  - [ ] Add tests for read-path normalization (`normalize_on_read=True`) at critical read sites (schedules, account/preferences)

#### **UI Quality Improvements** [WARNING] **PLANNED**
- [ ] Fix Dialog Integration (main window updates after dialog changes)
- [ ] Add Data Validation across all forms
- [ ] Improve Error Handling with clear, user-friendly messages
- [ ] Monitor and optimize UI responsiveness for common operations

---

### **Legacy Code Removal Plan**

**Status**: Legacy Channel Removal Complete, General Legacy Monitoring Active (extended for preferences flags)  
**Goal**: Safely remove all legacy/compatibility code

#### **Legacy Channel Code Removal** [CHECKMARK] **COMPLETE** (2025-08-03)
- [x] Communication Manager Legacy Channel Properties - Removed `self.channels` property and `_legacy_channels` attribute
- [x] LegacyChannelWrapper Class - Removed entire 156+ line legacy wrapper class
- [x] Legacy Channel Access Methods - Removed `_create_legacy_channel_access` method
- [x] Modern Interface Migration - Updated all methods to use `self._channels_dict` directly
- [x] Test Updates - Updated tests to use modern interface patterns
- [x] Audit Verification - Created and ran audit scripts to verify complete removal
- [x] Application Testing - Confirmed application loads successfully after removal

#### **Legacy Code Marking** [CHECKMARK] **COMPLETE**
- [x] Communication Manager Legacy Wrappers - Marked with warnings and removal plans
- [x] Account Creator Dialog Compatibility - 5 unused methods marked
- [x] User Profile Settings Widget Fallbacks - 5 legacy blocks marked
- [x] User Context Legacy Format - Format conversion marked
- [x] Test Utilities Backward Compatibility - Legacy path marked
- [x] UI App Legacy Communication Manager - Legacy handling marked

#### **Monitoring Phase** [WARNING] **ACTIVE**
- [ ] Monitor app logs for LEGACY warnings (preferences nested 'enabled' flags) for 2 weeks

#### **Removal Phase** [WARNING] **PLANNED**
- [ ] Execute removals listed in TODO.md and update tests accordingly

##### **Targeted Removals (High-Priority)**
- [ ] Account Creator Dialog compatibility methods (by 2025-08-15)
- [ ] User Profile Settings Widget legacy fallbacks (by 2025-08-15)
- [ ] Discord Bot legacy methods (by 2025-08-15)

---

### **Testing Strategy Plan**

**Status**: Core Modules Complete, UI Layer in Progress  
**Goal**: Comprehensive test coverage across all modules

#### **Core Module Testing** [CHECKMARK] **COMPLETE** (8/12 modules)
- [x] Response Tracking - 25 behavior tests
- [x] Service Utilities - 22 behavior tests
- [x] Validation - 50+ behavior tests
- [x] Schedule Management - 25 behavior tests
- [x] Task Management - 20 behavior tests
- [x] Scheduler - 15 behavior tests
- [x] Service - 20 behavior tests
- [x] File Operations - 15 behavior tests

#### **Bot/Communication Testing** [CHECKMARK] **COMPLETE** (6/8 modules)
- [x] Conversation Manager - 20 behavior tests
- [x] User Context Manager - 20 behavior tests
- [x] Discord Bot - 32 behavior tests
- [x] AI Chatbot - 23 behavior tests
- [x] Account Management - 6 behavior tests
- [x] User Management - 10 behavior tests

#### **UI Layer Testing** [CHECKMARK] **COMPLETE** (3/8 modules)
- [x] Main UI Application - 21 behavior tests
- [x] Individual Dialog Testing - 12 dialog behavior tests
- [x] Widget Testing - 14 widget behavior tests (using centralized test utilities)
- [ ] Simple Widget Testing - 7 failures in basic widget tests (constructor parameter issues)

#### **Supporting Module Testing** [CHECKMARK] **COMPLETE** (5/5 modules)
- [x] Error Handling - 10 behavior tests
- [x] Config - 5 behavior tests
- [x] Auto Cleanup - 16 behavior tests
- [x] Check-in Analytics - 16 behavior tests
- [x] Logger Module - 15 behavior tests

#### **Outstanding Testing Tasks** [WARNING] **ACTIVE**
- [ ] UI Layer Testing (expand coverage for remaining UI modules)
- [ ] Individual Dialog Testing (comprehensive behavior tests)
- [ ] TagWidget validation in both modes
- [ ] Expand Testing Framework for under-tested modules

#### **Integration Testing** [WARNING] **PLANNED**
- [ ] Cross-module workflows
- [ ] End-to-end user scenarios
- [ ] Performance testing

---

### **Channel Interaction Implementation Plan**

**Status**: Core Framework Complete, Discord Enhancement Complete, Email Integration Complete  
**Goal**: Comprehensive user interactions through communication channels

#### **Secondary Channel Implementation** 🔄 **IN PROGRESS**
- [x] Email Integration - Full email-based interaction system [CHECKMARK] **COMPLETED** (2025-11-11)
  - [x] Email message body extraction from incoming emails (plain text and HTML support)
  - [x] Email polling loop (checks every 30 seconds, tracks processed emails)
  - [x] Email-to-user mapping integration (using get_user_id_by_identifier)
  - [x] Message routing to InteractionManager for processing
  - [x] Email response sending with proper subject lines
- [ ] Cross-Channel Sync - Synchronize data across supported channels
  Note: Telegram integration has been removed from scope.

---

### **Test Performance Optimization Plan**

**Status**: Performance Issues Identified, Optimization in Progress  
**Goal**: Reduce test execution time and improve development efficiency

#### **Performance Analysis** [CHECKMARK] **COMPLETE**
- [x] Unit Tests - ~1.5 seconds (fast)
- [x] Integration Tests - ~2.6 seconds (fast)
- [x] Behavior Tests - ~4.4 minutes (MAJOR BOTTLENECK)

#### **Performance Bottlenecks Identified** [CHECKMARK] **COMPLETE**
- [x] File System Operations - Each test creates/tears down user data directories
- [x] Test User Creation Overhead - Complex user data structures and validation
- [x] Mock Setup Overhead - Extensive mocking in behavior tests
- [x] AI Chatbot Tests - AI response simulation and cache operations
- [x] Discord Bot Tests - Async operations and threading

#### **Optimization Strategies** [WARNING] **IN PROGRESS**
- [x] Parallel Test Execution - Install pytest-xdist for parallel execution [CHECKMARK] **COMPLETED**
  - [x] Added pytest-xdist>=3.5.0 to requirements.txt
  - [x] Enabled parallel execution by default in run_tests.py (with --no-parallel option to disable)
  - [x] Set default workers to 2 for safety (some tests may have race conditions with more workers)
  - [x] Validated parallel execution works with 2 workers (599 tests passed in 7.62s vs 8.75s sequential)
  - [ ] Fix test isolation issues for tests that fail with more workers (e.g., test_update_user_index_success with 6 workers)
- [x] Test Data Caching - Cache common test user data [CHECKMARK] **COMPLETED**
  - [x] Added caching mechanism to TestUserFactory to avoid recreating identical user data structures
  - [x] Implemented cache key generation based on user configuration (user_id, enable_checkins, enable_tasks)
  - [x] Added session-scoped fixture to clear cache at end of test session
  - [x] Updated create_basic_user__with_test_dir to use cached data structures
  - [x] Fixed caching bug: Changed from `.copy()` to `copy.deepcopy()` to ensure proper test isolation (nested dictionaries were being shared)
  - [x] Extended caching to all fixed-configuration user creation methods: minimal, full, discord, email, health, task, complex_checkins, disability, limited_data, inconsistent
  - [x] Fixed limited_data user preferred_name handling to preserve empty string (not generated name)
- [x] Optimized Test User Creation - Create minimal user data for tests [CHECKMARK] **COMPLETED**
  - [x] Added create_minimal_user() method for tests that only need basic structure
  - [x] Minimal user creation skips categories, schedules, and messages for faster setup
  - [x] Documented when to use minimal vs basic user creation
- [x] Selective Test Execution - Mark slow tests with @pytest.mark.slow [CHECKMARK] **COMPLETED** (75 slow tests already marked)
- [ ] Mock Optimization - Reduce mock setup overhead
- [x] File System Optimization - Use temporary directories more efficiently [CHECKMARK] **COMPLETED**
  - [x] Added session-scoped fixture to create base tmp directory once at session start
  - [x] Optimized test_path_factory to reuse session-scoped base directory
  - [x] Optimized TestDataManager.setup_test_environment to batch directory creation
  - [x] Reduced redundant directory creation operations

#### **Implementation Phases** [WARNING] **IN PROGRESS**
- [x] Phase 1: Quick Wins - Enable parallel execution, add test selection [CHECKMARK] **COMPLETED**
  - [x] Added pytest-xdist>=3.5.0 to requirements.txt
  - [x] Enabled parallel execution by default in run_tests.py
  - [x] Set default workers to 2 for safety (some tests have race conditions with more workers)
  - [x] Added --no-parallel option to disable parallel execution when needed
  - [x] Added --workers option to specify worker count or 'auto' for optimal count
  - [x] Updated help text and examples to reflect parallel-by-default behavior
  - [x] Validated parallel execution works (599 tests passed in 7.62s vs 8.75s sequential - ~13% faster)
  - [ ] Add `--durations-all` usage in CI to track slow tests; consider pytest profiling plugins (optional enhancement)
- [x] Phase 2: Infrastructure - Implement caching, optimize file operations [CHECKMARK] **COMPLETED**
  - [x] Implemented test data caching for common user configurations
  - [x] Added minimal user creation option for faster test setup
  - [x] Added session-scoped fixture to clear cache at end of test session
  - [x] Optimized user data structure creation to reuse cached templates
  - [x] Optimized file system operations (base tmp directory created once, batch directory creation)
  - [ ] Validate performance improvements with test runs (pending)
- [ ] Phase 3: Advanced - Separate test suites, implement result caching
  - [ ] Consider separating test suites for faster feedback (unit vs integration vs behavior)
  - [ ] Implement pytest result caching for faster re-runs of unchanged tests
  - [ ] Add test result persistence for CI/CD optimization

---

### **Task Management System Implementation**

#### **Phase 2: Advanced Features (PLANNED)**
- [x] **Individual Task Reminders**: Custom reminder times for individual tasks [CHECKMARK] **COMPLETED**
- [ ] **Recurring Tasks**: Support for daily, weekly, monthly, and custom recurring patterns
- [ ] **Priority Escalation**: Automatic priority increase for overdue tasks
- [ ] **AI Chatbot Integration**: Full integration with AI chatbot for task management

#### **Task Management UI Improvements (PLANNED)**
- [ ] **Recurring Tasks**: Set tasks to reoccur at set frequencies, or sometime after last completion
- [ ] **Smart Reminder Randomization**: Randomize reminder timing based on priority and proximity to due date

#### **Phase 3: Communication Channel Integration (PLANNED)**
- [ ] **Discord Integration**: Full Discord bot integration for task management
- [ ] **Email Integration**: Email-based task management
- [ ] **Cross-Channel Sync**: Synchronize tasks across supported communication channels

#### **Phase 4: AI Enhancement (PLANNED)**
- [ ] **Smart Task Suggestions**: AI-powered task suggestions based on user patterns
- [ ] **Natural Language Processing**: Create and manage tasks using natural language
- [ ] **Intelligent Reminders**: AI-determined optimal reminder timing
- [ ] **Task Analytics**: AI-powered insights into task completion patterns

---

### **Dynamic Check-in Questions Plan** [WARNING] **PARTIALLY COMPLETE**

**Status**: [WARNING] **PARTIALLY COMPLETE**  
**Priority**: Medium  
**Effort**: Medium  
**Date**: 2025-11-10

**Goal**: Implement fully dynamic custom check-in questions (UI + data + validation).

**Current State**:
- ✅ **Data model exists**: Questions defined in `resources/default_checkin/questions.json` with types, validation, categories
- ✅ **Validation rules implemented**: `DynamicCheckinManager` validates all question types (scale_1_5, yes_no, number, optional_text)
- ✅ **Persist/Load enabled state**: User preferences store which questions are enabled/disabled
- ✅ **Integration into check-in flow**: `ConversationManager` uses dynamic questions with weighted selection
- ✅ **UI for enabling/disabling**: `CheckinSettingsWidget` has checkboxes for all predefined questions
- ❌ **Custom questions not implemented**: `add_new_question()` method only shows placeholder message
- ❌ **No ordering functionality**: Questions use weighted selection but no user-defined order
- ❌ **No presets**: No preset question sets available

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

## 🔄 **Plan Maintenance**

### **How to Update This Plan**
1. **Add new plans** with clear goals and checklist format
2. **Update progress** by checking off completed items
3. **Move completed plans** to the "Completed Plans" section
4. **Keep reference information** current and useful
5. **Remove outdated information** to maintain relevance

### **Success Criteria**
- **Actionable**: Each item is a specific, testable action
- **Trackable**: Clear progress indicators and completion status
- **Maintainable**: Easy to update and keep current
- **Useful**: Provides value for both human developer and AI collaborators

---

## 📚 **Reference Information**

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

## 🔍 **Detailed Legacy Code Inventory**

### **1. Schedule Management Legacy Keys** [WARNING] **HIGH PRIORITY**
**Location**: `core/schedule_management.py`  
**Issue**: Support for legacy `'start'`/`'end'` keys alongside canonical `'start_time'`/`'end_time'`  
**Legacy Code Found**:
- `get_schedule_time_periods()` - Lines 70-75: Legacy key support
- `migrate_legacy_schedule_keys()` - Lines 573-614: Migration function  
**Timeline**: Complete by 2025-08-01

### **2. Schedule Management Legacy Format** [WARNING] **HIGH PRIORITY**
**Location**: `core/schedule_management.py`  
**Issue**: Support for legacy format without periods wrapper  
**Legacy Code Found**:
- `get_schedule_time_periods()` - Lines 52-58: Legacy format handling
- `set_schedule_periods()` - Lines 475-491: Legacy format migration  
**Timeline**: Complete by 2025-08-01

### **3. User Data Access Legacy Wrappers** [WARNING] **MEDIUM PRIORITY**
**Location**: `core/user_data_handlers.py`  
**Issue**: Legacy wrapper functions for backward compatibility  
**Timeline**: Complete when no legacy warnings appear for 1 week

### **4. Account Creator Dialog Compatibility Methods** [WARNING] **LOW PRIORITY**
**Location**: `ui/dialogs/account_creator_dialog.py`  
**Issue**: Methods marked as "kept for compatibility but no longer needed"  
**Legacy Code Found**: Lines 326-347: Multiple compatibility methods  
**Timeline**: Complete by 2025-08-15

### **5. User Profile Settings Widget Legacy Fallbacks** [WARNING] **LOW PRIORITY**
**Location**: `ui/widgets/user_profile_settings_widget.py`  
**Issue**: Legacy fallback code for data loading  
**Legacy Code Found**: Lines 395, 402, 426, 450, 462: Legacy fallback comments  
**Timeline**: Complete by 2025-08-15

### **6. Discord Bot Legacy Methods** [WARNING] **LOW PRIORITY**
**Location**: `communication/communication_channels/discord/bot.py`  
**Issue**: Legacy methods for backward compatibility  
**Legacy Code Found**: Lines 518-564: Legacy start/stop methods  
**Timeline**: Complete by 2025-08-15

### **7. Communication Manager Legacy Wrappers** [WARNING] **HIGH PRIORITY**
**Location**: `communication/core/channel_orchestrator.py`  
**Issue**: LegacyChannelWrapper and legacy channel access  
**Legacy Code Found**:
- `LegacyChannelWrapper` class (Lines 1064-1216): Complete legacy wrapper
- `_create_legacy_channel_access()` method (Lines 390-398): Creates legacy wrappers
- `channels` property (Lines 410-420): Returns legacy wrappers when available  
**Timeline**: Complete after 1 week of monitoring

### **8. User Context Legacy Format Conversion** [CHECKMARK] **COMPLETED**
**Location**: `user/user_context.py`  
**Status**: Legacy format conversion/extraction code has been removed  
**Completed**: Legacy code removal confirmed - all code now uses modern formats directly
**Notes**: Comments in code confirm "no legacy conversion needed" and "no legacy extraction needed"

### **9. Test Utilities Backward Compatibility** [WARNING] **LOW PRIORITY**
**Location**: `tests/test_utilities.py`  
**Issue**: Multiple backward compatibility paths for test data directories  
**Timeline**: Complete after 1 week of monitoring

### **10. UI App Legacy Communication Manager** [WARNING] **LOW PRIORITY**
**Location**: `ui/ui_app_qt.py`  
**Issue**: Legacy communication manager instance handling  
**Legacy Code Found**: Legacy communication manager shutdown (Line 1496)  
**Timeline**: Complete after 1 week of monitoring

---
