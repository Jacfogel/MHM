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

### **User Data Flow Architecture Improvements** [WARNING] **PLANNING**

**Status**: [WARNING] **PLANNING**  
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

- [ ] **Re-order validation and backup**: Move data validation before backup creation to avoid backing up invalid data
- [ ] **Two-phase save approach**: 
  - Phase 1: Merge all types in-memory, validate all data, validate cross-file invariants
  - Phase 2: Write all types to disk, then update index/cache
- [ ] **In-memory cross-file invariants**: Process cross-file invariants using in-memory merged data instead of reading from disk
- [ ] **Explicit processing order**: Define deterministic order for processing data types (e.g., account -> preferences -> schedules -> context)
- [ ] **Atomic multi-type operations**: Ensure that either all types succeed or all roll back when saved together
- [ ] **Reduce nested saves**: Refactor cross-file invariants to update in-memory data and write once, rather than triggering separate save operations

**Success Criteria**:
- [ ] Data validation occurs before backup creation
- [ ] Cross-file invariants work correctly when multiple types are saved simultaneously
- [ ] No nested save operations triggered by invariants
- [ ] Processing order is deterministic and documented
- [ ] Partial failure scenarios handled gracefully
- [ ] All existing tests pass with improved flow

**Risk Assessment**:
- **Medium Impact**: Affects core user data save path used throughout the system
- **Mitigation**: Incremental refactoring with comprehensive testing after each change
- **Rollback**: Maintain backward compatibility throughout implementation

### **Natural Language Command Detection Review & Rework** [WARNING] **PLANNING**

**Status**: [WARNING] **PLANNING**  
**Priority**: Medium  
**Effort**: Medium  
**Date**: 2025-11-01

**Objective**: Review and potentially completely rework natural language command detection patterns to better recognize task intent in natural language (e.g., "I need to buy groceries" should trigger clarification mode, not chat mode).

**Current Issues**:
- "I need to buy groceries" detected as `chat` mode instead of `command_with_clarification`
- Some natural language task requests not properly recognized
- Mode detection may need more comprehensive pattern matching or AI-based classification

**Scope**:
- [ ] Analyze current mode detection patterns in `ai/chatbot.py` `_detect_mode()` method
- [ ] Review test results for natural language command detection (T-5.5)
- [ ] Consider expanding pattern matching or using AI-powered classification for ambiguous cases
- [ ] Test improvements with various natural language task request patterns
- [ ] Ensure backward compatibility with existing command patterns

**Success Criteria**:
- [ ] Natural language task requests (e.g., "I need to...", "I should...") properly trigger clarification mode
- [ ] No regressions in existing command detection (clear commands still work)
- [ ] Test suite passes with improved detection

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

### **Analytics Scale Normalization (Mood/Energy)** [WARNING] **PARTIAL**

**Status**: [WARNING] **PARTIAL**  
**Priority**: High  
**Effort**: Small/Medium  
**Date**: 2025-09-12

**Objective**: Align Mood (and Energy where shown) to 1-5 across analytics outputs.

**Results**:
- Updated `analytics_handler.py` to show Mood on a 1-5 scale; Energy adjusted in check-in history

**Planned follow-up**:
- Sweep `interaction_handlers.py` and `checkin_handler.py` for any remaining `/10` occurrences (tracked in TODO.md)

---

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

### **2025-09-10 - Message Deduplication Advanced Features (Future)** [WARNING] **PLANNED**

**Status**: [WARNING] **PLANNED**  
**Priority**: Low  
**Effort**: Large  
**Dependencies**: Message deduplication system (completed)

**Objective**: Implement advanced analytics, insights, and intelligent scheduling features for the message deduplication system.

**Background**: The core message deduplication system is complete and operational. These advanced features would enhance the system with analytics, user preference learning, and intelligent message selection capabilities.

**Implementation Plan**:

#### **Step 5.1: Analytics and Insights** [WARNING] **PLANNED**
- [ ] **Message frequency analytics**
  - [ ] Track message send frequency by category and time period
  - [ ] Analyze user engagement patterns over time
  - [ ] Generate reports on message delivery success rates
  - [ ] Create visualizations for message analytics
- [ ] **User engagement tracking**
  - [ ] Monitor user response rates to different message types
  - [ ] Track user interaction patterns with messages
  - [ ] Analyze user engagement trends and preferences
  - [ ] Generate user engagement reports
- [ ] **Message effectiveness metrics**
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
- Advanced analytics provide actionable insights
- User engagement tracking improves message targeting
- Smart recommendations increase user satisfaction
- Intelligent scheduling optimizes message timing
- A/B testing framework enables continuous improvement

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
- [ ] Nightly run with `ENABLE_TEST_DATA_SHIM=0` and randomized order; track regressions
- [ ] Sweep and resolve Discord/aiohttp deprecations and unraisable warnings to keep CI clean
- [ ] After 2 weeks green, gate or remove remaining test-only diagnostics

**Success Criteria**:
- No failures under no-shim randomized runs for 2 consecutive weeks
- CI warning count reduced to external-only or zero

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

### **2025-08-25 - Windows Fatal Exception Investigation** 🔄 **INVESTIGATION**

**Status**: 🔄 **INVESTIGATION**  
**Priority**: High  
**Effort**: Medium  
**Dependencies**: None

**Objective**: Investigate and fix the Windows fatal exception (access violation) that occurs during full test suite execution.

**Background**: During comprehensive testing, a Windows fatal exception was encountered during full test suite execution. This issue needs investigation to ensure system stability and prevent crashes during testing.

**Investigation Plan**:
- [ ] Analyze crash logs and error patterns
- [ ] Identify if issue is related to Discord bot threads or UI widget cleanup
- [ ] Determine if issue is Windows-specific or affects all platforms
- [ ] Check for memory management or threading issues
- [ ] Implement appropriate fix based on root cause analysis
- [ ] Test fix with full test suite execution
- [ ] Add crash detection and recovery mechanisms

**Success Criteria**:
- Root cause identified and documented
- Fix implemented and tested
- Full test suite runs without fatal exceptions
- Prevention measures in place

---

### **2025-08-22 - User Context & Preferences Integration Investigation** 🟡 **PLANNING**

**Status**: 🟡 **PLANNING**  
**Priority**: High  
**Effort**: Medium  
**Dependencies**: None

**Objective**: Investigate and improve the integration of `user/user_context.py` and `user/user_preferences.py` modules across the system.

**Background**: User observed that these modules may not be used as extensively or in all the ways they were intended to be.

**Investigation Plan**:
- [ ] Audit current usage of `user/user_context.py` across all modules
- [ ] Audit current usage of `user/user_preferences.py` across all modules
- [ ] Identify gaps between intended functionality and actual usage
- [ ] Document integration patterns and missing connections
- [ ] Propose improvements for better integration

**Success Criteria**:
- Complete understanding of current integration state
- Identified gaps and improvement opportunities
- Action plan for enhancing integration

---

### **2025-08-22 - Bot Module Naming & Clarity Refactoring** 🟡 **PLANNING**

**Status**: 🟡 **PLANNING**  
**Priority**: High  
**Effort**: Medium  
**Dependencies**: None

**Objective**: Improve clarity and separation of purposes for communication modules.

**Target Modules**:
- `communication/core/channel_orchestrator.py`
- `communication/message_processing/conversation_flow_manager.py`
- `communication/message_processing/command_parser.py`
- `communication/command_handlers/interaction_handlers.py`
- `communication/message_processing/interaction_manager.py`
- `communication/command_handlers/` (command parsing & dispatch)

**Investigation Plan**:
- [ ] Analyze current module purposes and responsibilities
- [ ] Identify overlapping functionality and unclear boundaries
- [ ] Document current naming conventions and their clarity
- [ ] Propose improved naming and separation strategies
- [ ] Create refactoring plan if needed

**Success Criteria**:
- Clear understanding of each module's purpose
- Identified naming and organization improvements
- Action plan for refactoring if beneficial

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

### **Phase 2: Mood-Responsive AI & Advanced Intelligence** [WARNING] **NEW**

**Goal**: Implement mood-responsive AI conversations and advanced emotional intelligence  
**Status**: Planning Phase  
**Estimated Duration**: 2-3 weeks

**Checklist**:
- [ ] **Mood-Responsive AI Conversations** (High Impact, High Effort)
  - [ ] Enhance mood tracking in check-ins with more granular detection
  - [ ] Modify AI prompts based on detected mood and energy levels
  - [ ] Add emotional state persistence and trend analysis
  - [ ] Implement tone adaptation algorithms
  - [ ] Test mood detection accuracy and AI response appropriateness
  - [ ] Validate emotional state persistence and analysis
- [ ] **Advanced Emotional Intelligence** (Medium Impact, High Effort)
  - [ ] Enhance mood analysis algorithms with machine learning patterns
  - [ ] Add emotional response templates for different moods
  - [ ] Implement mood trend analysis and prediction
  - [ ] Create emotional intelligence scoring system
  - [ ] Test emotional intelligence accuracy and response quality
  - [ ] Validate mood trend analysis and prediction accuracy

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
- [ ] **Smart Home Integration Planning** (Low Impact, Low Effort)
  - [ ] Research smart home APIs and protocols
  - [ ] Design integration architecture for future implementation
  - [ ] Document requirements and constraints
  - [ ] Create integration roadmap and timeline
  - [ ] Test integration feasibility with sample APIs
  - [ ] Validate integration architecture design

---

### **Suggestion Relevance and Flow Prompting (Tasks)** [WARNING] **NEW**

**Goal**: Provide context-appropriate suggestions and prompts that the system can actually handle

**Checklist**:
- [ ] Suppress generic suggestions on targeted prompts (e.g., update_task field prompt) — implemented in code, add tests
- [ ] Ensure list->edit flows confirm task identifier when missing — add behavior tests
- [ ] Cover natural language variations for due date updates ("due" vs "due date") — implemented in parser, add tests
- [ ] Verify suggestions are actionable (handlers exist) — audit suggestions table vs handlers

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

**Status**: Core Framework Complete, Discord Enhancement Complete  
**Goal**: Comprehensive user interactions through communication channels

#### **Secondary Channel Implementation** [WARNING] **PLANNED**
- [ ] Email Integration - Full email-based interaction system
- [ ] Cross-Channel Sync - Synchronize data across supported channels
  Note: Telegram integration has been removed from scope.

#### **Discord Hardening** [WARNING] **PLANNED**
- [ ] Discord Validation Enhancement (username format rules + dialog validation)
- [ ] Discord Connectivity Monitoring (periodic health checks & reporting)

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
- [ ] Parallel Test Execution - Install pytest-xdist for parallel execution
  - [ ] Validate isolation when running in parallel
- [ ] Test Data Caching - Cache common test user data
- [ ] Optimized Test User Creation - Create minimal user data for tests
- [ ] Selective Test Execution - Mark slow tests with @pytest.mark.slow
- [ ] Mock Optimization - Reduce mock setup overhead
- [ ] File System Optimization - Use temporary directories more efficiently

#### **Implementation Phases** [WARNING] **PLANNED**
- [ ] Phase 1: Quick Wins - Enable parallel execution, add test selection
  - [ ] Add `--durations-all` usage in CI to track slow tests; consider pytest profiling plugins
- [ ] Phase 2: Infrastructure - Implement caching, optimize file operations
- [ ] Phase 3: Advanced - Separate test suites, implement result caching

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

### **User Preferences Refactor Plan** [WARNING] **PLANNED**

**Goal**: Introduce `UserPreferences` class for centralized, type-safe preference management.
- [ ] Define data model and serialization format
- [ ] Implement class and adapter for current data files
- [ ] Update accessors across UI/Core to use `UserPreferences`
- [ ] Add migration helpers and tests

---

### **Dynamic Check-in Questions Plan** [WARNING] **PLANNED**

**Goal**: Implement fully dynamic custom check-in questions (UI + data + validation).
- [ ] Design widget interactions (add/edit/remove, ordering, presets)
- [ ] Define data model and validation rules
- [ ] Persist/Load in user data; integrate into check-in flow
- [ ] Add behavior and UI tests

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

### **8. User Context Legacy Format Conversion** [WARNING] **MEDIUM PRIORITY**
**Location**: `user/user_context.py`  
**Issue**: Converting between legacy and new data formats  
**Legacy Code Found**:
- Legacy format conversion (Lines 50-65): Converting new data structure to legacy format
- Legacy format extraction (Lines 81-95): Converting legacy format to new data structure  
**Timeline**: Complete after 1 week of monitoring

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
