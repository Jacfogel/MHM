# MHM Development Plans

## 🗓️ Recent Plans (Most Recent First)

### 2025-08-22 - User Context & Preferences Integration Investigation

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

### 2025-08-22 - Bot Module Naming & Clarity Refactoring

**Status**: 🟡 **PLANNING**  
**Priority**: High  
**Effort**: Medium  
**Dependencies**: None  

**Objective**: Improve clarity and separation of purposes for bot modules.

**Target Modules**:
- `bot/communication_manager.py`
- `bot/conversation_manager.py`
- `bot/enhanced_command_parser.py`
- `bot/interaction_handlers.py`
- `bot/interaction_manager.py`

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

### 2025-08-21 - Helper Function Naming Convention Refactor ✅ **COMPLETED**

**Status**: ✅ **COMPLETED**  
**Priority**: High  
**Effort**: Large (Multi-module refactor)  
**Dependencies**: None  

**Objective**: Implement consistent helper function naming convention using `_main_function__helper_name` pattern for better traceability and searchability.

**Achievement**: **113 helper functions refactored across 13 modules** ✅

**Implemented Convention**:
```python
def set_read_only(self, read_only: bool = True):
    self._set_read_only__time_inputs(read_only)
    self._set_read_only__checkbox_states(read_only)
    self._set_read_only__visual_styling(read_only)

def validate_and_accept(self):
    self._validate_and_accept__input_errors()
    self._validate_and_accept__collect_data()
    self._validate_and_accept__create_account()
```

**Benefits Realized**:
- **Improved Searchability**: `grep "set_read_only"` finds both main function and all helpers
- **Clear Traceability**: Obvious ownership of helper functions
- **Better Debugging**: Clearer call stack traces with meaningful function names
- **Consistent Patterns**: Uniform naming convention across entire codebase

**Phase 1: Planning and Preparation** ✅ **COMPLETED**
- [x] Audit current helper functions across all modules
- [x] Create comprehensive list of functions to refactor
- [x] Test current state to establish baseline
- [x] Create backup before starting

**Phase 2: Refactor Core Modules** ✅ **COMPLETED** 
- [x] Refactor `ui/widgets/period_row_widget.py` (6 helper functions)
- [x] Refactor `ui/dialogs/account_creator_dialog.py` (12 helper functions)
- [x] Refactor `core/user_data_handlers.py` (6 helper functions)
- [x] Refactor `core/file_operations.py` (6 helper functions)
- [x] Refactor `bot/interaction_handlers.py` (6 helper functions)
- [x] Refactor `tests/test_utilities.py` (8 helper functions)

**Phase 2B: Extended Refactoring** ✅ **COMPLETED**
- [x] **Priority 1**: High priority production code (18 functions across 2 modules)
- [x] **Priority 2**: Medium priority production code (25 functions across 4 modules)
- [x] **Priority 3**: Non-underscore helper functions (8 functions across 3 modules)
- [x] **Priority 4**: Test utilities helper functions (26 functions in 1 module)

**Phase 3: Update References** ✅ **COMPLETED**
- [x] Find all function calls to renamed helpers
- [x] Update all references across the codebase
- [x] Update any imports if helpers are imported elsewhere

**Phase 4: Testing and Validation** ✅ **COMPLETED**
- [x] Run comprehensive tests after each module
- [x] Run audit to verify no regressions
- [x] Manual testing of key functionality

**Phase 5: Documentation and Cleanup** ✅ **COMPLETED**
- [x] Update documentation files
- [x] Update changelogs
- [x] Final git commit and push

**Final Results**:
- **Zero Regressions**: All existing functionality preserved
- **Improved Code Quality**: Enhanced maintainability and searchability
- **System Stability**: All tests passing, full functionality maintained

**Risk Assessment**:
- **High Impact**: Affects multiple modules and function signatures
- **Mitigation**: Incremental refactoring with testing after each module
- **Rollback**: Backup created, can revert if issues arise

**Success Criteria**:
- All helper functions follow new naming convention
- All tests pass
- No functionality regressions
- Improved code traceability and searchability

---

# PLANS - Development Plans & Strategies

> **Audience**: Human Developer & AI Collaborators  
> **Purpose**: Consolidated development plans (grouped, interdependent work) with step-by-step checklists  
> **Style**: Actionable, checklist-focused, progress-tracked  
> **Last Updated**: 2025-08-15

> **See [TODO.md](TODO.md) for independant tasks**

## 🔄 Plan Maintenance

### How to Update This Plan
1. **Add new plans** with clear goals and checklist format
2. **Update progress** by checking off completed items
3. **Move completed plans** to the "Completed Plans" section
4. **Keep reference information** current and useful
5. **Remove outdated information** to maintain relevance

### Success Criteria
- **Actionable**: Each item is a specific, testable action
- **Trackable**: Clear progress indicators and completion status
- **Maintainable**: Easy to update and keep current
- **Useful**: Provides value for both human developer and AI collaborators 

## �� Active Plans

#### **User Context & Preferences Integration Investigation** ⚠️ **NEW PRIORITY**
**Goal**: Investigate and improve the integration of user/user_context.py and user/user_preferences.py modules
**Status**: Investigation Phase
**Estimated Duration**: 1-2 weeks
**Checklist**:
- [ ] **Investigate Current Usage Patterns**
  - [ ] Audit all imports and usage of UserContext and UserPreferences across codebase
  - [ ] Identify where these modules are actually being used vs. where they should be used
  - [ ] Document current integration gaps and missed opportunities
  - [ ] Analyze if UserPreferences is truly needed or if it duplicates UserContext functionality
- [ ] **Assess Integration Quality**
  - [ ] Check if user context is properly passed to AI conversations
  - [ ] Verify if user preferences are being used for personalization
  - [ ] Identify where direct file access bypasses these modules
  - [ ] Document any inconsistent data access patterns
- [ ] **Plan Integration Improvements**
  - [ ] Consolidate duplicate functionality between UserContext and UserPreferences
  - [ ] Ensure all user data access goes through these modules
  - [ ] Improve AI context building with user preferences
  - [ ] Add missing integration points for better personalization
- [ ] **Implementation**
  - [ ] Refactor modules to eliminate redundancy
  - [ ] Update all direct data access to use these modules
  - [ ] Enhance AI context with user preferences
  - [ ] Add comprehensive tests for integration points

#### **Channel Registry Simplification** ✅ **COMPLETED**
**Goal**: Simplify channel management by removing redundant channel_registry.py and using config.py instead
**Status**: ✅ **COMPLETED**
**Estimated Duration**: 1 week
**Checklist**:
- [x] **Analyze Current Channel Management** ✅ **COMPLETED**
  - [x] Document how channel_registry.py, channel_factory.py, and base_channel.py interact
  - [x] Identify redundancy between channel_registry.py and config.py channel settings
  - [x] Check if channel availability should be determined by .env/config instead of hardcoded registry
  - [x] Analyze if factory pattern is overkill for current channel count
- [x] **Design Simplified Architecture** ✅ **COMPLETED**
  - [x] Move channel availability to config.py based on .env settings
  - [x] Consider removing channel_registry.py entirely
  - [x] Simplify channel_factory.py to read from config instead of registry
  - [x] Maintain base_channel.py as the interface definition
- [x] **Implementation** ✅ **COMPLETED**
  - [x] Update config.py to include channel availability logic
  - [x] Modify channel_factory.py to use config-based channel discovery
  - [x] Remove channel_registry.py if no longer needed
  - [x] Update all channel creation code to use new approach
  - [x] Add tests for config-based channel management

**Results Achieved**:
- **Eliminated Redundancy**: Removed 15-line channel_registry.py file that duplicated config.py functionality
- **Config-Based Discovery**: Channel availability now determined by .env settings in config.py
- **Dynamic Registration**: ChannelFactory auto-registers channels based on configuration
- **Simplified Architecture**: Single source of truth for channel availability
- **Maintained Compatibility**: All existing functionality preserved
- **Improved Maintainability**: Adding new channels only requires updating config.py mapping

**Files Modified**:
- `core/config.py`: Added `get_available_channels()` and `get_channel_class_mapping()` functions
- `bot/channel_factory.py`: Updated to use config-based auto-registration
- `core/service.py`: Removed channel registry import and registration
- `ui/ui_app_qt.py`: Removed channel registry import and registration
- `tests/ui/test_dialogs.py`: Removed channel registry import and registration
- `bot/channel_registry.py`: **DELETED** - No longer needed

**Benefits Realized**:
- **Reduced Complexity**: Eliminated redundant registration system
- **Single Source of Truth**: Channel availability determined by configuration
- **Easier Maintenance**: Adding new channels requires only config.py changes
- **Better Error Messages**: Factory now shows available channels when unknown type requested
- **Cleaner Startup**: No manual registration calls needed

#### **Bot Module Naming and Purpose Clarification** ⚠️ **NEW PRIORITY**
**Goal**: Clarify and potentially rename bot modules to better reflect their distinct purposes
**Status**: Investigation Phase
**Estimated Duration**: 1-2 weeks
**Checklist**:
- [ ] **Analyze Current Module Purposes**
  - [ ] Document exact responsibilities of each module:
    - `bot/communication_manager.py` - Channel lifecycle and message routing
    - `bot/conversation_manager.py` - Conversation state and context
    - `bot/enhanced_command_parser.py` - Natural language command parsing
    - `bot/interaction_handlers.py` - Specific command implementations
    - `bot/interaction_manager.py` - Message routing and intent determination
  - [ ] Identify naming confusion and overlapping responsibilities
  - [ ] Check if any modules could be merged or split for clarity
- [ ] **Design Improved Architecture**
  - [ ] Consider renaming modules for clarity (e.g., interaction_manager → message_router)
  - [ ] Clarify boundaries between conversation vs communication management
  - [ ] Ensure each module has a single, clear responsibility
  - [ ] Document the distinct purposes and relationships
- [ ] **Implementation**
  - [ ] Rename modules if beneficial for clarity
  - [ ] Update all imports and references
  - [ ] Improve module documentation and purpose statements
  - [ ] Add architectural diagrams showing clear module boundaries
  - [ ] Update tests to reflect new module names/purposes

#### AI Tools Improvement Plan — NEW
**Goal**: Improve AI tools to generate more valuable, concise documentation for AI collaborators
**Status**: Planning Phase
**Checklist**:
- [ ] **Analyze Current State**
  - [ ] Review current AI tools output quality and identify issues
  - [ ] Assess generated documentation usability for AI collaborators
  - [ ] Identify patterns in what AI collaborators actually need vs. what's generated
  - [ ] Document current limitations and improvement opportunities
- [ ] **Redesign Function Registry Generation**
  - [ ] Focus on essential patterns over verbose listings
  - [ ] Add pattern recognition for function categories
  - [ ] Implement concise summary generation
  - [ ] Add cross-references to detailed documentation
  - [ ] Test generated output for AI usability
- [ ] **Redesign Module Dependencies Generation**
  - [ ] Highlight key relationships over detailed listings
  - [ ] Add dependency pattern recognition
  - [ ] Implement relationship visualization
  - [ ] Add impact analysis for changes
  - [ ] Test generated output for AI usability
- [ ] **Implement Pattern Recognition**
  - [ ] Identify common function/module categories
  - [ ] Add automatic pattern detection
  - [ ] Implement smart summarization
  - [ ] Add decision tree generation
  - [ ] Test pattern recognition accuracy
- [ ] **Quality Assurance**
  - [ ] Test generated documentation with AI collaborators
  - [ ] Validate information accuracy and completeness
  - [ ] Ensure cross-references work correctly
  - [ ] Verify generated docs follow AI optimization principles
  - [ ] Document improvement metrics and success criteria

#### Test Warnings Cleanup and Reliability Improvements — COMPLETED ✅
**Goal**: Fix test warnings and improve system reliability
**Status**: ✅ COMPLETED
**Estimated Duration**: 1 week
**Checklist**:
- [x] **Fixed PytestReturnNotNoneWarning** ✅ **COMPLETED**
  - [x] Converted test functions from return statements to proper assertions
  - [x] Updated `tests/integration/test_account_management.py` and `tests/ui/test_dialogs.py`
  - [x] Removed incompatible `main()` functions from test files
- [x] **Fixed AsyncIO Deprecation Warnings** ✅ **COMPLETED**
  - [x] Updated `bot/ai_chatbot.py`, `bot/email_bot.py`, `bot/communication_manager.py`
  - [x] Replaced `asyncio.get_event_loop()` with `asyncio.get_running_loop()` with fallback
- [x] **Enhanced Account Validation** ✅ **COMPLETED**
  - [x] Added strict validation for empty `internal_username` fields
  - [x] Added validation for invalid channel types
  - [x] Maintained backward compatibility with existing Pydantic validation
- [x] **Fixed Test Configuration Issues** ✅ **COMPLETED**
  - [x] Set CATEGORIES environment variable in test configuration
  - [x] Fixed user preferences validation in test environment
  - [x] All 884 tests now passing with only external library warnings remaining

#### Phase 1: Enhanced Task & Check-in Systems — MAJOR PROGRESS
**Goal**: Improve task reminder system and check-in functionality to align with project vision
**Status**: Implementation Phase
**Estimated Duration**: 1-2 weeks
**Checklist**:
- [x] **Enhanced Task Reminder System** (High Impact, Medium Effort) ✅ **COMPLETED**
  - [x] Add priority-based reminder frequency (high priority = more likely to be selected for reminders)
  - [x] Implement due date proximity weighting (closer to due = more likely to be selected for reminders)
  - [x] Add "critical" priority level and "no due date" option for tasks
  - [ ] Add recurring task support with flexible scheduling
  - [x] Improve semi-randomness to consider task urgency
  - [x] Test priority and due date weighting algorithms
  - [ ] Validate recurring task scheduling patterns
- [x] **Semi-Random Check-in Questions** (High Impact, Low-Medium Effort) ✅ **COMPLETED**
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

#### Phase 2: Mood-Responsive AI & Advanced Intelligence — NEW
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

#### Phase 3: Proactive Intelligence & Advanced Features — NEW
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

#### Suggestion Relevance and Flow Prompting (Tasks) — NEW
- Goal: Provide context-appropriate suggestions and prompts that the system can actually handle
- Checklist:
  - [ ] Suppress generic suggestions on targeted prompts (e.g., update_task field prompt) — implemented in code, add tests
  - [ ] Ensure list→edit flows confirm task identifier when missing — add behavior tests
  - [ ] Cover natural language variations for due date updates ("due" vs "due date") — implemented in parser, add tests
  - [ ] Verify suggestions are actionable (handlers exist) — audit suggestions table vs handlers

#### Test User Creation Failures ✅ **RESOLVED**
- [x] Fix "name 'logger' is not defined" error in test utilities
  - [x] Identify missing logger import in test utility functions
  - [x] Add proper logger initialization in test utilities
  - [x] Verify test user creation works in all test scenarios
- [x] Fix user data loading failures in account management tests
  - [x] Resolve missing 'schedules' and 'account' keys in test data
  - [x] Update test data creation to include all required keys
  - [x] Verify user data loading works consistently
- [x] Fix CommunicationManager attribute errors in tests
  - [x] Update tests to use correct attribute names (_channels_dict vs channels)
  - [x] Fix test expectations for modern CommunicationManager interface
  - [x] Verify all communication manager tests pass

#### AI Chatbot Test Failures ✅ **RESOLVED**
- [x] Fix system prompt test failures
  - [x] Update test expectations for command prompt content
  - [x] Verify system prompt loader works with current prompt format
  - [x] Ensure tests match actual system prompt implementation

#### Test Utilities Demo Failures ✅ **RESOLVED**
- [x] Fix basic user creation failures in demo tests
  - [x] Resolve test user creation issues in demo scenarios
  - [x] Update demo tests to use working test utilities
  - [x] Verify all demo tests pass

#### UI Test Failures ✅ **RESOLVED**
- [x] Fix widget constructor parameter mismatches
  - [x] Fix CategorySelectionWidget and ChannelSelectionWidget user_id parameter issues
  - [x] Fix DynamicListField and DynamicListContainer title/items parameter issues
- [x] Fix account creation UI test data issues
  - [x] Resolve user context update failures in integration tests
  - [x] Fix missing account data in persistence tests
  - [x] Fix duplicate username handling test failures

#### Verification and Documentation ✅ **COMPLETED**
- [x] Run comprehensive test suite after fixes
- [x] Verify all behavior tests pass (591 tests passing)
- [x] Update test documentation with working patterns
- [x] Document any changes needed for future test development

### UI Migration Plan
**Status**: Foundation Complete, Dialog Testing in Progress  
**Goal**: Complete PySide6/Qt migration with comprehensive testing

#### Foundation ✅ **COMPLETE**
- [x] PySide6/Qt migration - Main app launches successfully
- [x] File reorganization - Modular structure implemented
- [x] Naming conventions - Consistent naming established
- [x] Widget refactoring - Widgets created and integrated
- [x] User data migration - All data access routed through new handlers
- [x] Signal-based updates - Implemented and working
- [x] 100% function documentation coverage - All 1349 functions documented

#### Dialog Implementation ✅ **COMPLETE**
- [x] Category Management Dialog - Complete with validation fixes
- [x] Channel Management Dialog - Complete, functionally ready
- [x] Check-in Management Dialog - Complete with comprehensive validation
- [x] User Profile Dialog - Fully functional with all personalization fields
- [x] Account Creator Dialog - Feature-based creation with validation
- [x] Task Management Dialog - Complete with unified TagWidget integration
- [x] Schedule Editor Dialog - Ready for testing

#### Widget Implementation ✅ **COMPLETE**
- [x] TagWidget - Unified widget for both management and selection modes
- [x] Task Settings Widget - Complete with TagWidget integration
- [x] Category Selection Widget - Implemented
- [x] Channel Selection Widget - Implemented
- [x] Check-in Settings Widget - Implemented
- [x] User Profile Settings Widget - Implemented

#### Testing & Validation ⚠️ **IN PROGRESS**
- [x] Main UI Application - 21 behavior tests complete
- [ ] Individual Dialog Testing - 8 dialogs need testing
- [ ] Widget Testing - 8 widgets need testing
- [ ] Integration Testing - Cross-dialog communication
- [ ] Performance Optimization - UI responsiveness monitoring
  - [ ] Windows path compatibility tests around messages defaults and config path creation
  - [ ] Expand preferences save/load tests to cover Pydantic normalization and legacy flag handling (full vs partial updates)
  - [ ] Add tests for read-path normalization (`normalize_on_read=True`) at critical read sites (schedules, account/preferences)

#### UI Quality Improvements ⚠️ **PLANNED**
- [ ] Fix Dialog Integration (main window updates after dialog changes)
- [ ] Add Data Validation across all forms
- [ ] Improve Error Handling with clear, user-friendly messages
- [ ] Monitor and optimize UI responsiveness for common operations

### Legacy Code Removal Plan
**Status**: Legacy Channel Removal Complete, General Legacy Monitoring Active (extended for preferences flags)  
**Goal**: Safely remove all legacy/compatibility code

#### Legacy Channel Code Removal ✅ **COMPLETE** (2025-08-03)
- [x] Communication Manager Legacy Channel Properties - Removed `self.channels` property and `_legacy_channels` attribute
- [x] LegacyChannelWrapper Class - Removed entire 156+ line legacy wrapper class
- [x] Legacy Channel Access Methods - Removed `_create_legacy_channel_access` method
- [x] Modern Interface Migration - Updated all methods to use `self._channels_dict` directly
- [x] Test Updates - Updated tests to use modern interface patterns
- [x] Audit Verification - Created and ran audit scripts to verify complete removal
- [x] Application Testing - Confirmed application loads successfully after removal

#### Legacy Code Marking ✅ **COMPLETE**
- [x] Communication Manager Legacy Wrappers - Marked with warnings and removal plans
- [x] Account Creator Dialog Compatibility - 5 unused methods marked
- [x] User Profile Settings Widget Fallbacks - 5 legacy blocks marked
- [x] User Context Legacy Format - Format conversion marked
- [x] Test Utilities Backward Compatibility - Legacy path marked
- [x] UI App Legacy Communication Manager - Legacy handling marked

 #### Monitoring Phase ⚠️ **ACTIVE**
  - [ ] Monitor app logs for LEGACY warnings (preferences nested 'enabled' flags) for 2 weeks

 #### Removal Phase ⚠️ **PLANNED**
  - [ ] Execute removals listed in TODO.md and update tests accordingly

##### Targeted Removals (High-Priority)
- [ ] Account Creator Dialog compatibility methods (by 2025-08-15)
- [ ] User Profile Settings Widget legacy fallbacks (by 2025-08-15)
- [ ] Discord Bot legacy methods (by 2025-08-15)

### Testing Strategy Plan
**Status**: Core Modules Complete, UI Layer in Progress  
**Goal**: Comprehensive test coverage across all modules

#### Core Module Testing ✅ **COMPLETE** (8/12 modules)
- [x] Response Tracking - 25 behavior tests
- [x] Service Utilities - 22 behavior tests
- [x] Validation - 50+ behavior tests
- [x] Schedule Management - 25 behavior tests
- [x] Task Management - 20 behavior tests
- [x] Scheduler - 15 behavior tests
- [x] Service - 20 behavior tests
- [x] File Operations - 15 behavior tests

#### Bot/Communication Testing ✅ **COMPLETE** (6/8 modules)
- [x] Conversation Manager - 20 behavior tests
- [x] User Context Manager - 20 behavior tests
- [x] Discord Bot - 32 behavior tests
- [x] AI Chatbot - 23 behavior tests
- [x] Account Management - 6 behavior tests
- [x] User Management - 10 behavior tests

#### UI Layer Testing ✅ **COMPLETE** (3/8 modules)
- [x] Main UI Application - 21 behavior tests
- [x] Individual Dialog Testing - 12 dialog behavior tests
- [x] Widget Testing - 14 widget behavior tests (using centralized test utilities)
- [ ] Simple Widget Testing - 7 failures in basic widget tests (constructor parameter issues)

#### Supporting Module Testing ✅ **COMPLETE** (5/5 modules)
#### Outstanding Testing Tasks ⚠️ **ACTIVE**
- [ ] UI Layer Testing (expand coverage for remaining UI modules)
- [ ] Individual Dialog Testing (comprehensive behavior tests)
- [ ] TagWidget validation in both modes
- [ ] Expand Testing Framework for under-tested modules
- [x] Error Handling - 10 behavior tests
- [x] Config - 5 behavior tests
- [x] Auto Cleanup - 16 behavior tests
- [x] Check-in Analytics - 16 behavior tests
- [x] Logger Module - 15 behavior tests

#### Integration Testing ⚠️ **PLANNED**
- [ ] Cross-module workflows
- [ ] End-to-end user scenarios
- [ ] Performance testing

### Channel Interaction Implementation Plan
**Status**: Core Framework Complete, Discord Enhancement Complete  
**Goal**: Comprehensive user interactions through communication channels

#### Secondary Channel Implementation ⚠️ **PLANNED**
- [ ] Email Integration - Full email-based interaction system
- [ ] Cross-Channel Sync - Synchronize data across supported channels
  
Note: Telegram integration has been removed from scope.

#### Discord Hardening ⚠️ **PLANNED**
- [ ] Discord Validation Enhancement (username format rules + dialog validation)
- [ ] Discord Connectivity Monitoring (periodic health checks & reporting)

### Test Performance Optimization Plan
**Status**: Performance Issues Identified, Optimization in Progress  
**Goal**: Reduce test execution time and improve development efficiency

#### Performance Analysis ✅ **COMPLETE**
- [x] Unit Tests - ~1.5 seconds (fast)
- [x] Integration Tests - ~2.6 seconds (fast)
- [x] Behavior Tests - ~4.4 minutes (MAJOR BOTTLENECK)

#### Performance Bottlenecks Identified ✅ **COMPLETE**
- [x] File System Operations - Each test creates/tears down user data directories
- [x] Test User Creation Overhead - Complex user data structures and validation
- [x] Mock Setup Overhead - Extensive mocking in behavior tests
- [x] AI Chatbot Tests - AI response simulation and cache operations
- [x] Discord Bot Tests - Async operations and threading

#### Optimization Strategies ⚠️ **IN PROGRESS**
- [ ] Parallel Test Execution - Install pytest-xdist for parallel execution
  - [ ] Validate isolation when running in parallel
- [ ] Test Data Caching - Cache common test user data
- [ ] Optimized Test User Creation - Create minimal user data for tests
- [ ] Selective Test Execution - Mark slow tests with @pytest.mark.slow
- [ ] Mock Optimization - Reduce mock setup overhead
- [ ] File System Optimization - Use temporary directories more efficiently

#### Implementation Phases ⚠️ **PLANNED**
- [ ] Phase 1: Quick Wins - Enable parallel execution, add test selection
  - [ ] Add `--durations-all` usage in CI to track slow tests; consider pytest profiling plugins
- [ ] Phase 2: Infrastructure - Implement caching, optimize file operations
- [ ] Phase 3: Advanced - Separate test suites, implement result caching

## Task Management System Implementation

### Phase 2: Advanced Features (PLANNED)
- [x] **Individual Task Reminders**: Custom reminder times for individual tasks ✅ **COMPLETED**
- [ ] **Recurring Tasks**: Support for daily, weekly, monthly, and custom recurring patterns
- [ ] **Priority Escalation**: Automatic priority increase for overdue tasks
- [ ] **AI Chatbot Integration**: Full integration with AI chatbot for task management

### Task Management UI Improvements (PLANNED)
- [ ] **Recurring Tasks**: Set tasks to reoccur at set frequencies, or sometime after last completion
- [ ] **Smart Reminder Randomization**: Randomize reminder timing based on priority and proximity to due date

### Phase 3: Communication Channel Integration (PLANNED)
- [ ] **Discord Integration**: Full Discord bot integration for task management
- [ ] **Email Integration**: Email-based task management
- [ ] **Cross-Channel Sync**: Synchronize tasks across supported communication channels

### Phase 4: AI Enhancement (PLANNED)
- [ ] **Smart Task Suggestions**: AI-powered task suggestions based on user patterns
- [ ] **Natural Language Processing**: Create and manage tasks using natural language
- [ ] **Intelligent Reminders**: AI-determined optimal reminder timing
- [ ] **Task Analytics**: AI-powered insights into task completion patterns

## Message Data Structure Reorganization Plan ⚠️ **PLANNED**
**Goal**: Reorganize message files to `data/messages/{user_id}/messages/{category}.json` and colocate `sent_messages.json`.

- [ ] Design migration strategy and fallback compatibility window
- [ ] Implement migration script and update file path resolution
- [ ] Update message CRUD/readers/writers to new structure
- [ ] Update tests and backfill fixtures
- [ ] Validate performance and rollback path

## User Preferences Refactor Plan ⚠️ **PLANNED**
**Goal**: Introduce `UserPreferences` class for centralized, type-safe preference management.

- [ ] Define data model and serialization format
- [ ] Implement class and adapter for current data files
- [ ] Update accessors across UI/Core to use `UserPreferences`
- [ ] Add migration helpers and tests

## Dynamic Check-in Questions Plan ⚠️ **PLANNED**
**Goal**: Implement fully dynamic custom check-in questions (UI + data + validation).

- [ ] Design widget interactions (add/edit/remove, ordering, presets)
- [ ] Define data model and validation rules
- [ ] Persist/Load in user data; integrate into check-in flow
- [ ] Add behavior and UI tests

## ✅ Completed Plans

#### Account Creation Error Fixes ✅ **COMPLETED & TESTED**
- Goal: Fix critical errors preventing new user account creation and improve user experience
- Checklist:
  - [x] Fix ChannelSelectionWidget method call error in account creation
    - [x] Identify incorrect `get_channel_data()` method call
    - [x] Update to use correct `get_selected_channel()` method
    - [x] Verify account creation works without errors
  - [x] Add undo button for tag deletion during account creation
    - [x] Add "Undo Last Delete" button to tag widget UI design
    - [x] Regenerate PyQt files to include new button
    - [x] Connect button to existing `undo_last_tag_delete()` functionality
    - [x] Add proper button state management (enabled only when tags can be restored)
  - [x] Fix fun_facts.json path resolution issue
    - [x] Identify malformed path in `.env` file causing `FileNotFoundError`
    - [x] Update `.env` to use relative path `resources/default_messages`
    - [x] Verify default message files are now accessible
    - [x] Test that new users get proper message files created
  - [x] Add scheduler integration for new users
    - [x] Implement `schedule_new_user()` method in scheduler
    - [x] Call scheduler integration after successful account creation
    - [x] Verify new users are immediately scheduled for messages and check-ins
  - [x] Update documentation
    - [x] Update AI_CHANGELOG.md with completed fixes
    - [x] Update CHANGELOG_DETAIL.md with detailed information
    - [x] Add testing tasks to TODO.md
- **Testing Results** (2025-08-15): ✅ **ALL TESTS PASSED** - Comprehensive testing verified all 6 fixes work correctly:
  - Default message files accessible and properly structured
  - Account creation process stable with correct method calls
  - Tag management works during account creation with undo functionality
  - Save button functions properly with safe attribute access
  - Scheduler integration automatically adds new users
  - Path resolution fixed for cross-platform compatibility

#### Suggestion Relevance and Flow Prompting (Tasks) — NEW

## 📚 Reference Information

### Key UI Patterns
- **Widget → Dialog → Core**: Data flows from widgets through dialogs to core handlers
- **Validation**: Centralized validation in `core/user_data_validation.py`
- **Error Handling**: `@handle_errors` decorator with user-friendly messages
- **Signal-Based Updates**: UI updates triggered by data changes

### Development Guidelines
- **UI Files**: Create .ui files in `ui/designs/` and generate Python with pyside6-uic
- **Testing**: Use behavior tests that verify side effects and real functionality
- **Legacy Code**: Mark with `LEGACY COMPATIBILITY` comments and removal plans
- **Documentation**: Update CHANGELOG files after testing, not before

### Architecture Decisions
- **Channel-Neutral Design**: All channels use same interaction handlers
- **Modular Structure**: Clear separation between UI, bot, and core layers
- **Data Flow**: User data centralized through `core/user_data_handlers.py`
- **Testing Strategy**: Behavior tests preferred over unit tests for real functionality

### AI Development Patterns
- **Use existing patterns** from working dialogs and widgets
- **Follow validation patterns** from `core/user_data_validation.py`
- **Test data persistence** when modifying dialogs
- **Check widget integration** when adding new features

### AI Development Commands
- `python ui/ui_app_qt.py` - Launch main admin interface
- `python run_mhm.py` - Launch full application
- `python run_tests.py` - Run tests including UI tests

### Key UI Files
- `ui/ui_app_qt.py` - Main PySide6 application
- `ui/dialogs/` - Dialog implementations
- `ui/widgets/` - Reusable widget components
- `core/user_data_validation.py` - Centralized validation logic

### UI Design Patterns
- **Dialog Pattern**: Inherit from QDialog, use widgets for data entry
- **Widget Pattern**: Inherit from QWidget, implement get/set methods
- **Validation Pattern**: Use `validate_schedule_periods` for time periods
- **Error Pattern**: Use `@handle_errors` decorator with QMessageBox

### Testing Framework Standards
- **Real Behavior Testing**: Focus on actual side effects and system changes
- **Test Isolation**: Proper temporary directories and cleanup procedures
- **Side Effect Verification**: Tests verify actual file operations and state changes
- **Comprehensive Mocking**: Mock file operations, external APIs, and system resources
- **Error Handling**: Test system stability under various error conditions
- **Performance Testing**: Test system behavior under load and concurrent access

### Test Quality Metrics
- **Success Rate**: 99.7% for covered modules (384 tests passing, 1 skipped, 34 warnings)
- **Coverage**: 48% of codebase tested (17/31+ modules)
- **Test Types**: Unit, integration, behavior, and UI tests properly organized
- **Patterns**: Established comprehensive real behavior testing approach

## 🔍 Detailed Legacy Code Inventory

### 1. Schedule Management Legacy Keys ⚠️ **HIGH PRIORITY**
**Location**: `core/schedule_management.py`
**Issue**: Support for legacy `'start'`/`'end'` keys alongside canonical `'start_time'`/`'end_time'`
**Legacy Code Found**:
- `get_schedule_time_periods()` - Lines 70-75: Legacy key support
- `migrate_legacy_schedule_keys()` - Lines 573-614: Migration function
**Timeline**: Complete by 2025-08-01

### 2. Schedule Management Legacy Format ⚠️ **HIGH PRIORITY**
**Location**: `core/schedule_management.py`
**Issue**: Support for legacy format without periods wrapper
**Legacy Code Found**:
- `get_schedule_time_periods()` - Lines 52-58: Legacy format handling
- `set_schedule_periods()` - Lines 475-491: Legacy format migration
**Timeline**: Complete by 2025-08-01

### 3. User Data Access Legacy Wrappers ⚠️ **MEDIUM PRIORITY**
**Location**: `core/user_data_handlers.py`
**Issue**: Legacy wrapper functions for backward compatibility
**Timeline**: Complete when no legacy warnings appear for 1 week

### 4. Account Creator Dialog Compatibility Methods ⚠️ **LOW PRIORITY**
**Location**: `ui/dialogs/account_creator_dialog.py`
**Issue**: Methods marked as "kept for compatibility but no longer needed"
**Legacy Code Found**: Lines 326-347: Multiple compatibility methods
**Timeline**: Complete by 2025-08-15

### 5. User Profile Settings Widget Legacy Fallbacks ⚠️ **LOW PRIORITY**
**Location**: `ui/widgets/user_profile_settings_widget.py`
**Issue**: Legacy fallback code for data loading
**Legacy Code Found**: Lines 395, 402, 426, 450, 462: Legacy fallback comments
**Timeline**: Complete by 2025-08-15

### 6. Discord Bot Legacy Methods ⚠️ **LOW PRIORITY**
**Location**: `bot/discord_bot.py`
**Issue**: Legacy methods for backward compatibility
**Legacy Code Found**: Lines 518-564: Legacy start/stop methods
**Timeline**: Complete by 2025-08-15

### 7. Communication Manager Legacy Wrappers ⚠️ **HIGH PRIORITY**
**Location**: `bot/communication_manager.py`
**Issue**: LegacyChannelWrapper and legacy channel access
**Legacy Code Found**:
- `LegacyChannelWrapper` class (Lines 1064-1216): Complete legacy wrapper
- `_create_legacy_channel_access()` method (Lines 390-398): Creates legacy wrappers
- `channels` property (Lines 410-420): Returns legacy wrappers when available
**Timeline**: Complete after 1 week of monitoring

### 8. User Context Legacy Format Conversion ⚠️ **MEDIUM PRIORITY**
**Location**: `user/user_context.py`
**Issue**: Converting between legacy and new data formats
**Legacy Code Found**:
- Legacy format conversion (Lines 50-65): Converting new data structure to legacy format
- Legacy format extraction (Lines 81-95): Converting legacy format to new data structure
**Timeline**: Complete after 1 week of monitoring

### 9. Test Utilities Backward Compatibility ⚠️ **LOW PRIORITY**
**Location**: `tests/test_utilities.py`
**Issue**: Multiple backward compatibility paths for test data directories
**Timeline**: Complete after 1 week of monitoring

### 10. UI App Legacy Communication Manager ⚠️ **LOW PRIORITY**
**Location**: `ui/ui_app_qt.py`
**Issue**: Legacy communication manager instance handling
**Legacy Code Found**: Legacy communication manager shutdown (Line 1496)
**Timeline**: Complete after 1 week of monitoring

## 🏗️ Historical Architecture Context

### Directory Structure (COMPLETED) ✅
```
MHM/
├── core/                    # Backend logic modules (refactored from utils.py)
│   ├── config.py           # Configuration management
│   ├── file_operations.py  # File I/O operations
│   ├── user_management.py  # User account management
│   ├── message_management.py # Message handling
│   ├── schedule_management.py # Scheduling logic
│   ├── response_tracking.py # Response analytics
│   ├── service_utilities.py # Service management
│   ├── validation.py       # Data validation
│   └── error_handling.py   # Error handling framework
├── ui/                     # All UI-related code
│   ├── designs/            # Qt Designer .ui files
│   ├── generated/          # Auto-generated PyQt Python classes
│   ├── dialogs/            # Dialog implementations
│   ├── widgets/            # Reusable widget components
│   └── ui_app_qt.py        # Main admin interface (PySide6)
├── bot/                    # Communication channel implementations
├── tasks/                  # Task management system
├── user/                   # User context and preferences
├── data/                   # User data storage
├── scripts/                # Migration, debug, and utility scripts
└── styles/                 # QSS theme files
```

## **Test Coverage Expansion Plan** ✅ **MAJOR PROGRESS**

**Goal**: Expand test coverage from 54% to 80%+ for critical infrastructure components
**Current Status**: 682/683 tests passing (99.85% success rate)
**Progress**: 3/5 critical components completed

### **Test Warnings Cleanup and Reliability Improvements** ✅ **COMPLETED**
**Goal**: Fix test warnings and improve system reliability
**Status**: ✅ COMPLETED
**Duration**: 1 week
**Results**:
- **Test Success Rate**: 100% (884/884 tests passing)
- **Warnings Reduced**: From multiple critical warnings to only external library warnings
- **Validation Enhanced**: Account validation now properly rejects invalid data
- **Test Reliability**: Improved test assertions and error handling
- **Configuration Fixed**: Test environment properly configured with required environment variables

**Key Achievements**:
- Fixed PytestReturnNotNoneWarning by converting test functions to use proper assertions
- Fixed AsyncIO deprecation warnings by updating to modern async patterns
- Enhanced account validation with strict field validation
- Fixed test configuration by setting CATEGORIES environment variable
- All tests now pass with only external library warnings remaining

### **✅ COMPLETED COMPONENTS**

#### **1. Backup Manager** ✅ **COMPLETED**
- **Coverage**: 0% → 80% (+80% improvement)
- **Tests Added**: 22 comprehensive behavior tests
- **Focus Areas**: Backup creation, validation, restoration, error handling
- **Impact**: Essential data safety now properly tested

#### **2. UI Dialog Testing** ✅ **COMPLETED**
- **Coverage**: 9-29% → 35%+ (+6-26% improvement)
- **Tests Added**: 22 comprehensive behavior tests
- **Focus Areas**: Dialog initialization, data loading, user interactions, cleanup
- **Impact**: User-facing reliability significantly improved

#### **3. Communication Manager** ✅ **COMPLETED**
- **Coverage**: 24% → 56% (+32% improvement)
- **Tests Added**: 38 comprehensive behavior tests
- **Focus Areas**: Message queuing, channel lifecycle, async operations, error handling
- **Impact**: Core communication infrastructure now robustly tested

### **🔄 REMAINING COMPONENTS**

#### **4. Core Scheduler** 🔄 **NEXT PRIORITY**
- **Current Coverage**: 31% (474 lines uncovered)
- **Target Coverage**: 70%
- **Focus Areas**: Scheduling logic, task execution, timing management
- **Estimated Effort**: Medium
- **Dependencies**: None

#### **5. Interaction Handlers** 🔄 **HIGH PRIORITY**
- **Current Coverage**: 32% (389 lines uncovered)
- **Target Coverage**: 60%
- **Focus Areas**: User command processing, response generation, error handling
- **Estimated Effort**: Medium
- **Dependencies**: None

### **📊 Test Suite Health Improvements**

#### **Completed Infrastructure Improvements**
- **Test Isolation**: Proper cleanup and fixture management implemented
- **Mock Handling**: Comprehensive mocking for UI dialogs and async operations
- **Error Reporting**: Enhanced debugging information for test failures
- **Test Reliability**: 99.85% success rate achieved

#### **Remaining Infrastructure Improvements**
- **Warning Suppression**: Address deprecation warnings and test warnings
- **Log Management**: Fix log rotation permission issues in test environment
- **Performance**: Optimize test execution speed
- **Documentation**: Update test documentation and examples

### **🎯 Next Phase Plan**

#### **Phase 1: Complete Critical Infrastructure (Week 1-2)**
1. **Core Scheduler Testing** (Week 1)
   - Analyze current test coverage gaps
   - Create comprehensive integration tests
   - Validate coverage improvements

2. **Interaction Handlers Testing** (Week 2)
   - Analyze current test coverage gaps
   - Create comprehensive behavior tests
   - Validate coverage improvements

#### **Phase 2: Test Suite Optimization (Week 3)**
1. **Warning Resolution**
   - Address deprecation warnings
   - Fix test warnings
   - Improve test output clarity

2. **Infrastructure Improvements**
   - Fix log rotation permission issues
   - Optimize test execution performance
   - Update test documentation

#### **Phase 3: Coverage Validation (Week 4)**
1. **Final Coverage Assessment**
   - Measure overall system coverage
   - Identify any remaining critical gaps
   - Plan additional testing if needed

2. **Documentation Updates**
   - Update test coverage documentation
   - Create testing best practices guide
   - Document test infrastructure improvements

### **📈 Success Metrics**

#### **Coverage Targets**
- **Backup Manager**: 0% → 80% ✅ **COMPLETED**
- **UI Dialogs**: 9-29% → 35%+ ✅ **COMPLETED**
- **Communication Manager**: 24% → 56% ✅ **COMPLETED**
- **Core Scheduler**: 31% → 70% 🔄 **IN PROGRESS**
- **Interaction Handlers**: 32% → 60% 🔄 **PLANNED**
- **Overall System**: 54% → 80%+ 🔄 **IN PROGRESS**

#### **Quality Targets**
- **Test Success Rate**: 99.85% ✅ **ACHIEVED**
- **Test Reliability**: Stable test suite ✅ **ACHIEVED**
- **Test Performance**: Optimized execution 🔄 **IN PROGRESS**
- **Test Maintainability**: Clear, well-documented tests 🔄 **IN PROGRESS**