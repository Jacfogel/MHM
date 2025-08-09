# PLANS - Development Plans & Strategies

> **Audience**: Human Developer & AI Collaborators  
> **Purpose**: Consolidated development plans with step-by-step checklists  
> **Style**: Actionable, checklist-focused, progress-tracked  
 > **Last Updated**: 2025-08-07
> **Last Updated**: 2025-08-09

> **See [TODO.md](TODO.md) for current development priorities and tasks**

## 🎯 Active Plans
### Test Data Isolation & Config Import Safety ✅ **COMPLETED**
- [x] Ensure tests write only under `tests/data/users` via session fixture
- [x] Avoid env overrides that break default-constant tests
- [x] Replace from-imports of config constants in critical modules
- [x] Add assertion to prevent leakage to real `data/users` in file ops lifecycle test


### Pytest Marker Application Project ✅ **COMPLETED**
**Status**: 100% Complete - All 101 tasks finished  
**Goal**: Improve test organization, selective execution, and test management

#### Phase 1: Unit Tests ✅ **COMPLETED**
- [x] Applied `@pytest.mark.unit` to all unit test files
- [x] Verified unit test collection and execution
- [x] Updated test runner to support unit test mode

#### Phase 2: Behavior Tests ✅ **COMPLETED**
- [x] Applied `@pytest.mark.behavior` to all behavior test files (67 tasks)
- [x] Fixed critical UI dialog issue preventing automated testing
- [x] Resolved test collection errors from problematic files
- [x] Verified behavior test collection and execution

#### Phase 3: Integration Tests ✅ **COMPLETED**
- [x] Applied `@pytest.mark.integration` to all integration test files (16 tasks)
- [x] Fixed missing import statements in test files
- [x] Verified integration test collection and execution

#### Phase 4: UI Tests ✅ **COMPLETED**
- [x] Applied `@pytest.mark.ui` to all UI test files (30 tasks)
- [x] Fixed UI dialog interference by removing `show()` calls from test fixtures
- [x] Updated assertions to prevent UI dialogs during automated testing
- [x] Enhanced test runner with UI test mode support

#### Phase 5: Verification & Testing ✅ **COMPLETED**
- [x] Verified all marker combinations work correctly
- [x] Tested critical test filtering (195 critical tests identified)
- [x] Confirmed test runner enhancements function properly
- [x] Validated no marker registration warnings

#### Phase 6: Quality Assurance ✅ **COMPLETED**
- [x] Updated documentation with completion status
- [x] Cleaned up project files and moved documentation to appropriate locations
- [x] Removed debug scripts and redundant example files
- [x] Verified test collection still works correctly after cleanup

#### Project Results
- **Total Test Files**: 31 files across 4 directories (unit, behavior, integration, UI)
- **Total Tasks**: 101 specific marker application steps completed
- **Test Collection**: 630 tests collected successfully (down from 675 due to cleanup)
- **Critical Tests**: 195 tests properly marked as critical
- **Test Runner**: Enhanced with UI mode and improved filtering
- **Documentation**: Complete project documentation in `tests/` directory

### Test Failure Resolution Plan
**Status**: All Critical Issues Resolved ✅ **COMPLETED**  
**Goal**: Fix remaining UI test failures to complete testing infrastructure

### Enhanced Logging System Implementation ✅ **COMPLETED**
**Status**: 100% Complete - All logging improvements implemented  
**Goal**: Implement comprehensive logging system with component separation and better organization

#### Phase 1: Core Logging Infrastructure ✅ **COMPLETED**
- [x] Created organized logs directory structure (`logs/`, `logs/backups/`, `logs/archive/`)
- [x] Implemented component-based log separation (app, discord, ai, user_activity, errors)
- [x] Added structured logging with JSON metadata support
- [x] Implemented time-based log rotation (daily with 7-day retention)
- [x] Added log compression for files older than 7 days
- [x] Created ComponentLogger class for targeted logging
- [x] Updated configuration with new log file paths
- [x] Maintained backward compatibility with existing logging

#### Phase 2: Component Logger Migration ✅ **COMPLETED**
- [x] **Priority 1: Core System Components** (8 files) - Updated service, error handling, auto cleanup, scheduler, service utilities, UI management, backup manager, checkin analytics
- [x] **Priority 2: Bot/Communication Components** (8 files) - Updated AI chatbot, email bot, telegram bot, base channel, channel factory, communication manager, conversation manager, interaction manager
- [x] **Priority 3: User Management Components** (6 files) - Updated user management, user data manager, user data handlers, user data validation, user context, user preferences
- [x] **Priority 4: Feature Components** (8 files) - Updated enhanced command parser, interaction handlers, backup manager, checkin analytics, message management, response tracking, schedule management, task management
- [x] **Priority 5: UI Components** (15 files) - Updated all UI dialogs and widgets to use component loggers
- [x] **Total Files Updated**: 42 files systematically updated with component-specific loggers

#### Phase 3: Testing and Validation ✅ **COMPLETED**
- [x] Fixed 2 logger behavior test failures
  - [x] Added missing `total_files` field to `get_log_file_info()` function
  - [x] Fixed bug in `cleanup_old_logs()` function where dict was being passed to `os.path.exists()`
- [x] Verified all behavior tests passing (344 tests)
- [x] Verified all unit tests passing (140 tests)
- [x] Confirmed application launches successfully with new logging system

#### Phase 4: Documentation and Organization ✅ **COMPLETED**
- [x] Moved LOGGING_GUIDE.md to logs directory for better organization
- [x] Updated documentation to reflect completion status
- [x] Verified logging system is fully operational

#### Project Results
- **Total Files Updated**: 42 files across all system components
- **Component Loggers**: 6 component types (main, discord, ai, user_activity, errors, communication, channels, email, telegram)
- **Test Status**: All tests passing (484 total tests)
- **Log Organization**: Clean separation with dedicated files for each component
- **Performance**: Improved debugging and targeted log analysis

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

### Check-in Flow Behavior Plan ✅
- [x] Add `/checkin` command and clearer intro prompt
- [x] Expire active check-in on next unrelated outbound message (motivational/health/task reminder)
- [ ] Optional: add inactivity timeout for check-in flows (design: expire after 30–60 minutes of no reply)

### Legacy Code Removal Plan
**Status**: Legacy Channel Removal Complete, General Legacy Monitoring Active (1-week period until 2025-08-10)  
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

#### Monitoring Phase ⚠️ **ACTIVE** (Until 2025-08-10)
- [ ] Monitor app.log for "LEGACY" warnings from Communication Manager
- [ ] Monitor app.log for "LEGACY" warnings from Account Creator Dialog
- [ ] Monitor app.log for "LEGACY" warnings from User Profile Settings Widget
- [ ] Monitor app.log for "LEGACY" warnings from User Context
- [ ] Monitor app.log for "LEGACY" warnings from Test Utilities
- [ ] Monitor app.log for "LEGACY" warnings from UI App

#### Removal Phase ⚠️ **PLANNED** (After 2025-08-10)
- [ ] Remove Communication Manager Legacy Wrappers
- [ ] Remove Account Creator Dialog Compatibility Methods
- [ ] Remove User Profile Settings Widget Fallbacks
- [ ] Remove User Context Legacy Format Handling
- [ ] Remove Test Utilities Backward Compatibility
- [ ] Remove UI App Legacy Communication Manager
- [ ] Update tests to use modern patterns only

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

#### Core Interaction Framework ✅ **COMPLETE**
- [x] Enhanced Command System - Natural language parsing
- [x] Interaction Handlers - Task, check-in, profile, schedule, analytics, help
- [x] Response System - Channel-adaptive, rich responses, conversational AI
- [x] Dynamic Time Period Support - Natural language time parsing
- [x] Conversational AI Enhancement - Lock management, fallback responses
- [x] Legacy Code Standards - Communication manager wrappers marked

#### Discord Enhancement ✅ **COMPLETED**
- [x] Enhanced Discord Commands - !help, !tasks, !checkin, !profile, !schedule, !messages, !status
- [x] Natural Language Processing - Intent recognition, entity extraction, context awareness
- [x] Discord-Specific Features - Rich embeds, buttons, interactive elements (basic implementation)
- [x] AI Response Quality Improvements - Fixed formatting, length, and suggestion issues
- [x] AI Response Length Centralization - Centralized character limits in config
- [ ] Advanced Integration - Cross-channel sync, advanced analytics

#### Secondary Channel Implementation ⚠️ **PLANNED**
- [ ] Email Integration - Full email-based interaction system
- [ ] Telegram Integration - Telegram bot implementation
- [ ] Cross-Channel Sync - Synchronize data across all channels

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
- [ ] Phase 2: Infrastructure - Implement caching, optimize file operations
- [ ] Phase 3: Advanced - Separate test suites, implement result caching

## 🚨 Critical Issues & Known Bugs

### High Priority Issues ⚠️ **ACTIVE**
- **Test Failures**: 12 behavior test failures blocking reliable testing
  - **Test User Creation**: "name 'logger' is not defined" errors
  - **User Data Loading**: Missing 'schedules' and 'account' keys
  - **Communication Manager**: Attribute errors in tests
- **Throttler Bug**: Service Utilities Throttler class never sets `last_run` on first call
- **Widget Integration Errors**: "No user_id provided!" errors in some dialogs
- **Test Performance**: Behavior tests taking 4.4 minutes (major bottleneck)

### Medium Priority Issues ⚠️ **MONITORING**
- **UI Layer Testing**: Only 1/8 UI modules have tests (12.5% coverage)
- **Supporting Modules**: Auto cleanup, check-in analytics, logger need testing
- **Integration Testing**: Cross-module workflow testing needed

### Low Priority Issues ⚠️ **PLANNED**
- **Documentation Consolidation**: Multiple files contain duplicate information
- **Performance Monitoring**: UI responsiveness optimization needed
- **Cross-Platform Testing**: Test all dialogs on different platforms

## 📋 Completed Plans

### AI Response Length Centralization ✅ **COMPLETED** (2025-08-04)
- **Achievement**: Successfully centralized AI model response character length configuration
- **Implementation**: Added `AI_MAX_RESPONSE_LENGTH` constant to `core/config.py`
- **Integration**: Updated both `bot/ai_chatbot.py` and `bot/interaction_manager.py` to use centralized config
- **Verification**: Created and ran test script to confirm consistent 150-character limit across modules
- **Impact**: Eliminated hardcoded response length values, improved maintainability and consistency

### Task Response Quality Improvements ✅ **COMPLETED** (2025-08-04)
- **Achievement**: Fixed critical Discord bot response quality issues
- **Task Formatting**: Eliminated JSON and system prompts from task responses
- **Response Length**: Enforced 200-character limit with proper truncation
- **Task Suggestions**: Made suggestions contextual and action-oriented
- **Reminder Format**: Updated to time-based format ("30 minutes to an hour before")
- **AI Enhancement**: Properly disabled for task responses to prevent formatting issues
- **Impact**: Significantly improved user experience with cleaner, more helpful responses

### UI Migration Foundation ✅ **COMPLETED** (2025-07-21)
- **Achievement**: Successfully migrated from Tkinter to PySide6/Qt
- **Impact**: Modern, responsive UI with better user experience
- **Coverage**: All UI files exist and dialogs can be instantiated
- **Status**: Foundation solid, ready for comprehensive testing

### TestUserFactory Fix ✅ **COMPLETED** (2025-08-03)
- **Achievement**: Resolved 23 test failures across behavior, integration, and UI test suites
- **Impact**: Test reliability fully restored, all dependent testing work unblocked
- **Coverage**: 139 tests passing, 1 skipped, 2 deselected (99.3% success rate)
- **Status**: All testing can now proceed with confidence

### Dynamic Time Period Support ✅ **COMPLETED** (2025-08-03)
- **Achievement**: Implemented flexible time period parsing for task statistics
- **Impact**: Users can ask for statistics in natural language with various time periods
- **Coverage**: Comprehensive pattern matching and entity extraction
- **Status**: Fully functional with extensive testing

### 100% Function Documentation Coverage ✅ **COMPLETED** (2025-07-31)
- **Achievement**: All 1349 functions in the codebase now have proper docstrings
- **Impact**: Complete codebase documentation enables better AI assistance and maintenance
- **Coverage**: Functions documented across bot/, ui/, scripts/, and tests/ directories
- **Status**: Documentation quality consistent with clear descriptions and proper formatting

### Test File Organization ✅ **COMPLETED** (2025-07-21)
- **Achievement**: Successfully organized all test files into appropriate directories
- **Impact**: Clean project structure with tests properly categorized by type
- **Coverage**: Real behavior tests, integration tests, UI tests, and utility scripts organized
- **Status**: No more test files cluttering the project root

### Windows Python Process Behavior Investigation ✅ **COMPLETED** (2025-07-21)
- **Achievement**: Documented Windows-specific Python process behavior
- **Impact**: Confirmed normal Windows behavior, no code changes needed
- **Coverage**: Tested multiple approaches and documented findings
- **Status**: Application works correctly despite dual processes

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

### File Renaming & Reformatting (COMPLETED) ✅
- `ui_app_createaccount_dialogue.py` → `ui/account_creator_qt.py`
- `ui_app_editschedule.py` → `ui/schedule_editor_qt.py`
- `ui_app_personalization.py` → `ui/personalization_dialog_qt.py`
- `ui_app_mainwindow.py` → `ui/ui_app_qt.py`

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