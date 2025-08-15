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

## 🎯 Active Plans

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

#### Account Creation Error Fixes ✅ **COMPLETED**
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