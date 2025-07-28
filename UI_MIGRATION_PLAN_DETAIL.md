# UI Migration & Project Reorganization - Complete Plan

> **Audience**: Human Developer (Beginner Programmer)  
> **Purpose**: Comprehensive documentation of the UI migration from Tkinter to PySide6/Qt and project reorganization  
> **Style**: Comprehensive, step-by-step, beginner-friendly, encouraging  
> **Status**: **PARTIALLY COMPLETE** - Foundation solid, but many dialogs broken  
> **Version**: --scope=docs - AI Collaboration System Active
> **Last Updated**: 2025-07-21
> **Last Updated**: 2025-07-16

> **See [README.md](README.md) for complete navigation and project overview**
> **See [DEVELOPMENT_WORKFLOW.md](DEVELOPMENT_WORKFLOW.md) for safe development practices**
> **See [TODO.md](TODO.md) for current UI priorities**
> **See [TESTING_IMPROVEMENT_PLAN_DETAIL.md](TESTING_IMPROVEMENT_PLAN_DETAIL.md) for testing strategy**

## 📝 How to Update This Plan

When updating this comprehensive UI migration plan, follow this format:

```markdown
### YYYY-MM-DD - UI Migration Progress Title
- **What was completed**: Specific UI component or migration step
- **Impact**: How this improves user experience, maintainability, or functionality
- **Files affected**: Key files that were modified, added, or removed
- **Testing status**: Whether the component was tested and verified working
```

**Important Notes:**
- **Keep status current** - Update completion status and current priorities
- **Document new patterns** - When adding new UI approaches, document them here
- **Cross-reference AI version** - Update `AI_UI_MIGRATION_PLAN.md` with brief summaries
- **Focus on user impact** - Emphasize how changes improve the user experience
- **Maintain beginner-friendly style** - Keep explanations clear and step-by-step

## 📋 Executive Summary

### Project Context & Goals
- **Goal**: Modernize the MHM app's user interface and codebase structure for maintainability, extensibility, and better user experience
- **Why**: Legacy Tkinter UI and flat file structure were limiting future development, maintainability, and professional appearance
- **Scope**: Migrate all UI to PySide6/Qt, reorganize files into logical modules, and standardize naming conventions
- **Impact**: Better user experience, easier maintenance, and foundation for future improvements

### Current Status Overview - **MOSTLY COMPLETE** ✅
- **UI Migration Foundation**: ✅ **COMPLETE** - Main PySide6/Qt app launches successfully with QSS applied
- **File Reorganization**: ✅ **COMPLETE** - Modular structure implemented
- **Naming Conventions**: ✅ **COMPLETE** - Consistent naming established
- **Widget Refactoring**: ✅ **COMPLETE** - Widgets created and integrated successfully
- **User Index & Data Cleanup**: ✅ **COMPLETE** - User index redesigned and synchronized, survey responses removed
- **Signal-Based Updates**: ✅ **COMPLETE** - Implemented and working
- **Check-in Frequency Logic**: ✅ **REMOVED** - Check-in frequency logic removed; now every applicable time period prompts a check-in
- **Testing & Validation**: ✅ **SIGNIFICANTLY IMPROVED** - Expanded from 5 to 9 modules with 226 tests (29% coverage, 100% success rate)
- **User Data Migration**: ✅ **FULLY COMPLETE** - All user data access is now routed through the new `get_user_data()` handler; legacy functions have been removed; robust test coverage confirms correctness and reliability
- **User Profile Dialog**: ✅ **FULLY FUNCTIONAL** - All personalization fields now fully functional with proper save/load/prepopulation including date of birth
- **Admin Panel Startup**: ✅ **IMPROVED** - Now automatically updates user index on startup for always-current user data
- **Feature-Based Account Creation**: ✅ **COMPLETED** - Conditional feature enablement with proper validation and tab visibility
- **Logging Isolation System**: ✅ **COMPLETED** - Complete separation of test and application logging with failsafe protection
- **Configuration Warning Suppression**: ✅ **COMPLETED** - Non-critical configuration warnings no longer show popup dialogs
- **UI Files**: ✅ **ALL EXIST** - All UI design files, generated files, and dialog implementations are present and working
- **Channel Management Validation**: ✅ **COMPLETED** - Proper validation with user-friendly error messages and data persistence
- **Date of Birth Saving**: ✅ **COMPLETED** - User profile settings now properly save date of birth changes
- **Test File Organization**: ✅ **COMPLETED** - All test files properly organized in appropriate directories
- **100% Function Documentation Coverage**: ✅ **COMPLETED** - All 1349 functions in the codebase now have proper docstrings

### What This Means for You
This migration has established a solid foundation with the main admin panel working and core backend functionality solid. All UI files exist and dialogs can be instantiated successfully. The new UI is more responsive and looks better. Most dialogs are functional, but some may need testing to identify specific issues.

## 🔧 Recent Fixes & Improvements (2025-07-18)

#### ✅ **Centralized User-Data Handler Migration**
- **Backend Refactor**: Implemented `core/user_data_handlers.py` to own `get_user_data` / `save_user_data` logic.
- **UI Impact**: All UI and widget modules now import from the new handler module – legacy warnings during runtime have largely disappeared.
- **Tests**: Full suite (244 tests) remains green after the migration, confirming no regressions.
- **Next UI Task**: Watch `app.log` for any remaining `LEGACY …` warnings triggered by UI components and update those call-sites.

### ✅ **Channel Management Dialog Validation Fix**
- **Problem**: Dialog was silently accepting invalid data without showing validation errors
- **Solution**: Added validation error collection and display before saving
- **Result**: Users now see clear error messages for invalid email/phone formats, dialog prevents saving until errors are fixed
- **Files Updated**: `ui/dialogs/channel_management_dialog.py`

### ✅ **User Profile Settings Date of Birth Fix**
- **Problem**: Date of birth was being loaded but not saved when modified
- **Solution**: Added date of birth saving logic to `get_personalization_data()` method
- **Result**: Date of birth changes are now properly persisted to user_context.json
- **Files Updated**: `ui/widgets/user_profile_settings_widget.py`

### ✅ **Test File Organization**
- **Problem**: Test files were cluttering the project root directory
- **Solution**: Moved test files to appropriate directories by type
- **Result**: Clean project organization with tests properly categorized
- **Files Moved**:
  - `test_account_management_real_behavior.py` → `tests/behavior/`
  - `test_account_management.py` → `tests/integration/`
  - `test_dialogs.py` → `tests/ui/`
  - `fix_test_calls.py` → `scripts/`

### ✅ **AI Tools Organization**
- **Problem**: `ai_audit_results.json` was cluttering the project root
- **Solution**: Moved to `ai_tools/` directory and updated configuration
- **Result**: Clean project root and proper organization of AI tool outputs

## 📋 Outstanding Todos from Recent Development

### **High Priority - UI Testing & Validation**
1. **Comprehensive Dialog Testing** - Test all dialogs for functionality and data persistence
   - **Account Creation Dialog** - Test feature-based creation and validation
   - **User Profile Dialog** - Test all personalization fields including date of birth (recently fixed)
   - **Channel Management Dialog** - Test validation and contact info saving (recently improved)
   - **Category Management Dialog** - Test category selection and persistence
   - **Task Management Dialog** - Test task enablement and settings
   - **Check-in Management Dialog** - Test check-in enablement and settings
   - **Schedule Editor Dialog** - Test period management and time settings

2. **Widget Testing** - Test all widgets for proper data binding
   - **User Profile Settings Widget** - Test date of birth saving (recently fixed)
   - **Channel Selection Widget** - Test timezone and contact info handling
   - **Category Selection Widget** - Test category selection and persistence
   - **Task Settings Widget** - Test task enablement and settings
   - **Check-in Settings Widget** - Test check-in enablement and settings

3. **Validation Testing** - Test validation logic across all dialogs
   - **Email Validation** - Test invalid email format handling
   - **Phone Validation** - Test invalid phone format handling
   - **Required Field Validation** - Test required field enforcement
   - **Feature Enablement Validation** - Test conditional validation based on features

### **Medium Priority - Code Quality**
1. **Legacy Code Cleanup** - ✅ **COMPLETED** - Remove fallback references to `preferences['messaging_service']`
   - **Status**: ✅ **COMPLETED** - All files already use modern `preferences.get('channel', {}).get('type')` pattern
   - **Files Verified**: `ui/ui_app_qt.py`, `ui/ui_app.py`, `core/response_tracking.py`, `bot/user_context_manager.py`, `bot/telegram_bot.py`, `bot/communication_manager.py`
   - **Result**: No legacy code found - system already modernized

2. **Documentation Updates** - Ensure all documentation reflects current state
   - Update any outdated references to module counts or file structures
   - Verify all navigation links are working
   - Update status indicators to reflect recent improvements

### **Medium Priority - Documentation Quality**
1. **Module Dependencies Documentation** - Update MODULE_DEPENDENCIES_DETAIL.md with current dependency information
   - **Current Status**: 0% of dependencies documented (1204 imports found, 0 documented)
   - **Files Missing**: All 131 files need dependency documentation
   - **Priority**: High - Critical for understanding system architecture
   - **Impact**: Better system understanding and maintenance

2. **Function Registry Updates** - ✅ **COMPLETED** - FUNCTION_REGISTRY.md now reflects 100% documentation coverage
   - **Previous Status**: Showed 0% documentation coverage (outdated)
   - **Current Status**: 100% documentation coverage achieved ✅
   - **Priority**: ✅ **COMPLETED** - Documentation accuracy
   - **Impact**: Accurate project status reporting

3. **Documentation Consolidation** - Address redundancy identified in documentation analysis
   - **Redundant Sections**: Multiple files contain duplicate information
   - **Consolidation Needed**: Reduce redundancy while maintaining accessibility
   - **Priority**: Low - Documentation organization
   - **Impact**: Cleaner, more maintainable documentation

### **Low Priority - Polish & Optimization**
1. **Performance Monitoring** - Track UI responsiveness and optimize slow operations
2. **Cross-Platform Testing** - Test all dialogs and widgets on different platforms
3. **Advanced Features** - Implement any missing advanced features identified during testing

## 🏗️ Architecture & Structure Changes

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
│   ├── ui_app_qt.py        # Main admin interface (PySide6)
│   └── ui_app.py           # Legacy Tkinter interface (deprecated)
├── bot/                    # Communication channel implementations
├── tasks/                  # Task management system
├── user/                   # User context and preferences
├── data/                   # User data storage
├── scripts/                # Migration, debug, and utility scripts
└── styles/                 # QSS theme files
```

### File Renaming & Reformatting (COMPLETED) ✅

#### UI Files Renamed
- `ui_app_createaccount_dialogue.py` → `ui/account_creator_qt.py`
- `ui_app_editschedule.py` → `ui/schedule_editor_qt.py`
- `ui_app_personalization.py` → `ui/personalization_dialog_qt.py`
- `ui_app_mainwindow.py` → `ui/ui_app_qt.py`

#### Core Module Refactoring
- `core/utils.py` (1,492 lines) → Split into 7 focused modules:
  - `core/file_operations.py` - File I/O operations
  - `core/user_management.py` - User account management
  - `core/message_management.py` - Message handling
  - `core/schedule_management.py` - Scheduling logic
  - `core/response_tracking.py` - Response analytics
  - `core/service_utilities.py` - Service management
  - `core/validation.py` - Data validation

#### Data Model Modernization
- `preferences['messaging_service']` → `preferences['channel']['type']`
- Schedule periods standardized to: `active`, `days`, `start_time`, `end_time`
- Removed legacy reminder fields from schedule data

#### Naming Convention Standardization
- Removed redundant `ui_app_` prefixes
- Consistent naming: `createaccount` → `account_creator`, `editschedule` → `schedule_editor`
- Widget files: `*_widget.py` pattern
- Dialog files: `*_dialog.py` pattern
- Generated files: `*_pyqt.py` pattern

## 🎯 Detailed Step-by-Step Plan

### Phase 1: Foundation (✅ COMPLETED)

#### 1.1 Core Module Refactoring ✅
- [x] Split monolithic `utils.py` into focused modules
- [x] Update all imports throughout codebase
- [x] Test all functionality after refactoring
- [x] Update documentation to reflect new structure

#### 1.2 UI Directory Reorganization ✅
- [x] Create `ui/designs/` for .ui files
- [x] Create `ui/generated/` for auto-generated Python classes
- [x] Create `ui/dialogs/` for dialog implementations
- [x] Create `ui/widgets/` for reusable widget components
- [x] Move existing UI files to appropriate directories

#### 1.3 PySide6 Migration Foundation ✅
- [x] Install PySide6 dependencies
- [x] Create Qt Designer workflow
- [x] Implement QUiLoader for .ui file loading
- [x] Add QSS theme support
- [x] Create base dialog and widget patterns

#### 1.4 Main Admin Panel Migration ✅
- [x] Design main admin panel in Qt Designer
- [x] Generate Python UI class
- [x] Implement dialog subclass with logic
- [x] Migrate service management functionality
- [x] Migrate user management functionality
- [x] Migrate content management functionality
- [x] Test all functionality

### Phase 2: Dialog Migration (⚠️ PARTIALLY COMPLETE)

#### 2.1 Account Creation Dialog ✅ **FEATURE-BASED IMPROVEMENTS COMPLETED**
- [x] Design dialog in Qt Designer
- [x] Generate Python UI class
- [x] Implement dialog subclass
- [x] Migrate user creation logic
- [x] Add collapsible sections
- [x] **MAJOR IMPROVEMENT**: Feature-based account creation implemented
  - [x] Added feature enablement checkboxes to Basic Information tab
  - [x] Implemented conditional tab visibility based on feature selection
  - [x] Enhanced validation to require at least one feature enabled
  - [x] Added comprehensive field validation (username, timezone, communication)
  - [x] Categories only required when automated messages are enabled
  - [x] Communication service and contact info only required when messages enabled
- [x] **UI IMPROVEMENTS**: Better organization and clearer labeling
  - [x] Renamed "Categories" tab to "Messages" for clarity
  - [x] Changed "Enable Messages" to "Enable Automated Messages"
  - [x] Consistent "Check-ins" titlecase throughout interface
  - [x] Removed checkable group boxes from Tasks and Check-ins tabs
- [x] **DATA INTEGRATION**: Proper feature enablement handling
  - [x] Schedule periods created only for enabled features
  - [x] Feature-specific files created only when features enabled
  - [x] Account creation respects feature enablement settings
- [x] **VALIDATION**: Comprehensive validation system
  - [x] Username and timezone always required
  - [x] At least one feature must be enabled
  - [x] Communication validation when messages enabled
  - [x] Category requirements when messages enabled
- **Status**: ✅ **FULLY FUNCTIONAL** - Feature-based account creation with proper validation and conditional UI

#### 2.2 Category Management Dialog ⚠️
- [x] Design dialog in Qt Designer
- [x] Generate Python UI class
- [x] Implement dialog subclass
- [x] Migrate category selection logic
- [ ] Test category management

#### 2.3 Channel Management Dialog ⚠️
- [x] Design dialog in Qt Designer
- [x] Generate Python UI class
- [x] Implement dialog subclass
- [x] Migrate channel selection logic
- [ ] Test channel management

#### 2.4 Task Management Dialog ⚠️
- [x] Design dialog in Qt Designer
- [x] Generate Python UI class
- [x] Implement dialog subclass
- [x] Migrate task management logic
- [ ] Test task management

#### 2.5 Check-in Management Dialog ⚠️
- [x] Design dialog in Qt Designer
- [x] Generate Python UI class
- [x] Implement dialog subclass
- [x] Migrate check-in logic
- [ ] Test check-in management

#### 2.6 Schedule Editor Dialog ⚠️
- [x] Design dialog in Qt Designer
- [x] Generate Python UI class
- [x] Implement dialog subclass
- [x] Migrate schedule editing logic
- [x] Add AM/PM time selection
- [ ] Test schedule management

#### 2.7 User Profile Dialog ✅ **MAJOR IMPROVEMENTS COMPLETED**
- [x] Design dialog in Qt Designer
- [x] Generate Python UI class
- [x] Implement dialog subclass
- [x] Migrate personalization logic
- [x] **MAJOR IMPROVEMENT**: Complete field support implemented for all personalization fields
  - [x] Preferred name field added and functional
  - [x] Gender identity (not pronouns) properly saves/loads
  - [x] Date of birth with proper validation
  - [x] Health conditions, medications, allergies with custom entry support
  - [x] Interests, goals, and loved ones with custom entry support
  - [x] Notes for AI with custom entry support
  - [x] Timezone integration with account.json
  - [x] All fields properly prepopulate from existing data
- [x] **MAJOR IMPROVEMENT**: Data structure standardization
  - [x] Removed user_id from user_context.json (now only in account.json)
  - [x] Moved timezone to account.json for consistency
  - [x] Standardized nested data structure for custom_fields
  - [x] Proper validation for all field types
- [x] **MAJOR IMPROVEMENT**: Dialog prepopulation fixed
  - [x] Admin panel loads user context data and passes to dialog
  - [x] All fields prepopulate correctly from existing data
  - [x] Timezone loads from account.json and saves back to account.json
  - [x] Preferred name and other fields load from user_context.json
- [x] **IMPROVEMENT**: Keyboard handling added
  - [x] Enter key doesn't trigger save (prevents accidental saves)
  - [x] Escape key confirms dialog (standard behavior)
- [x] **IMPROVEMENT**: Validation made optional
  - [x] All fields are optional with type checking only if present
  - [x] No validation errors for empty fields
- [x] **IMPROVEMENT**: Loved ones support enhanced
  - [x] Supports list of dictionaries with name, type, and relationships
  - [x] Handles format like "Name - Type - Relationship1,Relationship2"
  - [x] Properly saves and loads complex data structures
- [x] **COMPLETED**: Admin panel automatically updates user index on startup
- [x] **COMPLETED**: Document temporary user ID pattern used in personalization dialogs
- **Status**: ✅ **FULLY FUNCTIONAL** - All personalization fields now work correctly with proper save/load/prepopulation

### Phase 3: Widget Refactoring (⚠️ PARTIALLY COMPLETE)

#### 3.1 Widget Architecture Design ⚠️
- [x] Design reusable widget patterns
- [x] Create widget base classes
- [x] Establish widget embedding patterns
- [x] Document widget usage guidelines
- [x] **Modular period widget management implemented** (July 2025)
- [x] **Created core/ui_management.py for UI-specific period logic**
- [x] **Standardized period widget handling across dialogs**
- [x] **Bug fixes:** Groupbox checkbox visuals, period prepopulation, and period naming issues resolved
- [x] **Schedule data migration and restoration complete** (July 2025)
- [x] **'ALL' period scheduling bug fixed** (July 2025)
- [x] **Migration/backup best practices established** (July 2025)
- [x] **Signal-based dynamic updates implemented** (July 2025)
- [ ] **CRITICAL ISSUE**: Widget integration errors ("No user_id provided!")

#### 3.2 Category Selection Widget ⚠️
- [x] Design widget in Qt Designer
- [x] Generate Python UI class
- [x] Implement widget subclass
- [ ] Test widget functionality
- [ ] Integrate with dialogs

#### 3.3 Channel Selection Widget ⚠️
- [x] Design widget in Qt Designer
- [x] Generate Python UI class
- [x] Implement widget subclass
- [ ] Test widget functionality
- [ ] Integrate with dialogs

#### 3.4 Task Settings Widget ⚠️
- [x] Design widget in Qt Designer
- [x] Generate Python UI class
- [x] Implement widget subclass
- [ ] Test widget functionality
- [ ] Integrate with dialogs

#### 3.5 Check-in Settings Widget ⚠️
- [x] Design widget in Qt Designer
- [x] Generate Python UI class
- [x] Implement widget subclass
- [x] Remove frequency logic (now every time period prompts a check-in)
- [ ] Test widget functionality
- [ ] Integrate with dialogs

#### 3.6 User Profile Settings Widget ✅ **FULLY FUNCTIONAL**
- [x] Design widget in Qt Designer
- [x] Generate Python UI class
- [x] Implement widget subclass
- [x] **MAJOR IMPROVEMENT**: Complete field support for all personalization fields
  - [x] Preferred name field with proper save/load
  - [x] Gender identity (not pronouns) with proper save/load
  - [x] Date of birth with validation
  - [x] Health conditions, medications, allergies with custom entry support
  - [x] Interests, goals, and loved ones with custom entry support
  - [x] Notes for AI with custom entry support
  - [x] Timezone integration (loads from account.json, saves to account.json)
- [x] **MAJOR IMPROVEMENT**: Data structure handling
  - [x] Proper nested data structure for custom_fields
  - [x] Handles complex data like loved ones as list of dictionaries
  - [x] Preserves existing data when loading
  - [x] Proper validation for all field types
- [x] **IMPROVEMENT**: Dialog integration
  - [x] Properly receives existing_data parameter
  - [x] All fields prepopulate correctly
  - [x] Saves data back to appropriate files (user_context.json and account.json)
- [x] **IMPROVEMENT**: User experience enhancements
  - [x] Keyboard handling (Enter doesn't save, Escape confirms)
  - [x] Optional validation (no errors for empty fields)
  - [x] Custom entry support for all relevant fields
- [x] **COMPLETED**: Widget functionality fully tested
- [x] **COMPLETED**: Dialog integration working correctly
- **Status**: ✅ **FULLY FUNCTIONAL** - All personalization widget features working correctly

### Phase 4: Data Management & Synchronization (✅ COMPLETED)

#### 4.1 User Index Redesign & Synchronization ✅
- [x] **Redesigned user index structure** to be more relevant and current
- [x] **Added automatic index updates** whenever users are created/modified
- [x] **Fixed format consistency issues** across all user entries
- [x] **UI now uses user index** instead of scanning directories directly
- [x] **New index structure**: `internal_username`, `active`, `channel_type`, `enabled_features`, `last_interaction`, `last_updated`
- [x] **User Data Migration**: All user data access is now routed through the new `get_user_data()` handler; all legacy user data functions have been removed; robust test coverage confirms correctness

#### 4.2 Survey Responses Cleanup ✅
- [x] **Deleted all `survey_responses.json` files** from user directories
- [x] **Removed all survey-related code** from core modules
- [x] **No more unused survey functionality** cluttering the codebase

#### 4.3 Signal-Based Dynamic Updates ⚠️
- [x] **Added `user_changed` signals** to all user-editing dialogs (AccountCreatorDialog, CategoryManagementDialog, CheckinManagementDialog, UserProfileDialog, ChannelManagementDialog, TaskManagementDialog)
- [x] **Connected signals to `refresh_user_list()`** in main window
- [x] **Real-time dropdown updates** when user data changes
- [x] **Consistent data synchronization** across all UI components
- [ ] **Testing needed**: Verify signal connections work properly

### Phase 5: Testing & Validation (❌ INCOMPLETE)

#### 5.1 Functionality Testing ❌
- [ ] Comprehensive testing of all dialogs and widgets for visual and functional correctness
- [ ] **NEW**: Test all personalization dialog fields for round-trip save/load functionality
- [ ] **NEW**: Test admin panel user index update on startup
- [ ] **NEW**: Test validation and error handling in all dialogs, especially user profile/personalization
- [ ] Final widget polish and integration
- [ ] Documentation update to reflect new UI and logic

#### 5.2 Error Handling Testing ❌
- [ ] Test error handling in all dialogs
- [ ] Test error handling in all widgets
- [ ] Test error handling in main admin panel
- [ ] Test error handling in service management
- [ ] Test error handling in file operations

#### 5.3 Cross-Platform Testing ❌
- [ ] Test on Windows
- [ ] Test on Linux
- [ ] Test on macOS
- [ ] Test with different Python versions
- [ ] Test with different PySide6 versions

#### 5.4 Performance Testing ❌
- [ ] Test UI responsiveness
- [ ] Test memory usage
- [ ] Test startup time
- [ ] Test dialog opening/closing speed
- [ ] Test widget loading speed

### Phase 6: Cleanup & Optimization (⚠️ PARTIALLY COMPLETE)

#### 6.1 Code Cleanup ⚠️
- [x] Remove legacy Tkinter code
- [x] Remove unused imports
- [x] Remove debug code
- [ ] Optimize widget loading
- [ ] Optimize dialog loading

#### 6.2 Documentation Cleanup ⚠️
- [x] Update all documentation
- [x] Remove outdated documentation
- [ ] Add widget usage examples
- [ ] Add dialog usage examples
- [ ] Update architecture documentation

#### 6.3 File Organization Cleanup ✅
- [x] Remove temporary files
- [x] Remove backup files
- [x] Remove debug files
- [x] Organize scripts directory
- [x] Clean up generated files

### Remaining Cleanup Tasks (High Priority)

#### Code Consolidation
- **Account Creator Pattern**: Refactor `account_creator_qt.py` to use the generated UI class pattern instead of QUiLoader for consistency
- **Redundant Methods**: Review and consolidate duplicate logic between Tkinter and PySide6 versions
- **Temporary User ID Pattern**: Document the temporary user ID pattern used in personalization dialogs as a best practice
- **Account Creation Feature Enablement**: Update account creation dialog to read/write feature enablement from account.json instead of preferences (task_management and checkins features)

#### Outstanding Todos from Recent Development (High Priority)
- **Complete Personalization Field Support**: ✅ **COMPLETED** - All personalization fields now fully functional
- **Robust Error Handling**: Ensure all dialogs have proper error handling and validation, especially for user profile/personalization
- **Systematic Testing**: Test all dialogs for data persistence and error handling, with focus on personalization dialog
- **Documentation**: ✅ **COMPLETED** - Temporary user ID pattern documented and implemented
- **Validation Testing**: ✅ **COMPLETED** - All personalization fields tested and validated

#### Critical UI Issues (High Priority)
- **Missing UI Files**: Create missing UI files (e.g., `user_profile_dialog.ui`)
- **Widget Integration**: Fix "No user_id provided!" errors in widgets
- **Dialog Testing**: Actually test each dialog to see what works and what doesn't
- **Error Handling**: Fix various error messages appearing in logs

#### Legacy Code Cleanup (Low Priority)
- **Legacy messaging_service field**: Remove fallback references to `preferences['messaging_service']` in multiple files:
  - `ui/ui_app_qt.py` (line 1243)
  - `ui/account_manager.py` (lines 1170, 1294)
  - `core/response_tracking.py` (line 169)
  - `bot/user_context_manager.py` (lines 97, 196)
  - `bot/telegram_bot.py` (line 671)
  - `bot/communication_manager.py` (lines 530, 814)

## 🔍 Current Status Assessment

### What's Actually Working ✅ **SOLID FOUNDATION**
1. **Application Startup**: `python run_mhm.py` launches without errors and loads the main PySide6/Qt admin panel with QSS theme
2. **Main Admin Panel**: Basic UI loads and displays
3. **Service Management**: Start/stop/restart functionality works
4. **User Selection**: User dropdown populates and selection works
5. **Core Backend**: All core modules (file operations, user management, scheduler, error handling) are working
6. **File Organization**: Directory structure and naming conventions implemented
7. **Error Handling**: Error handling framework is in place
8. **QSS Theming**: Theme loading mechanism works and custom styles are visible
9. **Schedule Data Migration**: Schedule data successfully migrated to new nested format; custom periods restored after migration (July 2025)
10. **User Index Synchronization**: User index automatically updates and UI reflects changes in real-time (July 2025)
11. **Signal-Based Updates**: All user-editing dialogs trigger automatic UI refresh when data changes (July 2025)
12. **Survey Responses Cleanup**: All unused survey functionality removed from codebase (July 2025)
13. **User Data Access**: All user data access is now handled through the unified `get_user_data()` handler; legacy functions are fully removed and robustly tested
14. **Testing Framework**: **LIMITED BUT QUALITY** - 112 tests passing (99.1% success rate) for 5 core modules
15. **User Profile Dialog**: **MAJOR IMPROVEMENT** - Fully functional with complete field support, proper save/load, and prepopulation (July 2025)

### What's Partially Working ⚠️ (Needs Attention)
1. **Account Creation**: Dialog opens and works, but needs final polish/testing
2. **Category Management**: Dialog opens but needs full testing
3. **Channel Management**: Dialog opens but needs full testing
4. **Widget System**: Widgets created and integrated, but have integration issues
5. **Schedule Editor**: Basic functionality but needs testing
6. **User Profile**: ✅ **FIXED** - Now fully functional with complete field support and prepopulation
7. **Task Management**: Shows "Feature in Migration" message - NOT IMPLEMENTED
8. **Message Editing**: Shows "Feature in Migration" message - NOT IMPLEMENTED

### What's NOT Working ❌ (High Priority)
1. **Personalization Dialog**: ✅ **FIXED** - Now fully functional with complete field support
2. **Widget Integration**: ✅ **FIXED** - Widgets now handle new user creation mode properly
3. **Dialog Testing**: **CRITICAL** - Most dialogs haven't been actually tested for functionality4Dialog Integration**: Many dialogs don't properly communicate with each other
5. **Data Validation**: Many dialogs don't validate user input properly
6. **Error Recovery**: Many dialogs don't handle errors gracefully

### What Needs Attention ⚠️ (High Priority)
1. **Dialog Testing**: Comprehensive testing of all functionality needed
2. **Performance**: Monitor UI responsiveness and optimize if needed
3**Documentation**: Update documentation to reflect actual state4 **Code Cleanup**: Remove legacy code and optimize
5. **Cross-Platform**: Test on different platforms
6. **Schedule Saving Issues**: Fix schedule saving so it does not overwrite the ALL time period, and ensure time period names are not saved in title case (should preserve original case in file)

### What's Broken ❌ (Legacy - Can Be Removed)
1. **Legacy Tkinter Interface**: Still exists but deprecated
2. **Some Debug Code**: May still exist in some files
3. **Temporary Files**: Some temporary files may still exist

## 🛠️ Verification Steps

### Step 1: Basic Functionality Test
```bash
python run_mhm.py
```
**Expected**: Application starts without errors, main admin panel opens

### Step 2: User Management Test
1. Open main admin panel
2. Select a user from dropdown
3. Click "Create New Account"
4. Fill out account creation form
5. Save account
**Expected**: Account created successfully, appears in user dropdown

### Step 3: Category Management Test
1. Select a user
2. Click "Category Settings"
3. Modify categories
4. Save changes
**Expected**: Categories updated successfully

### Step 4: Channel Management Test
1. Select a user
2. Click "Channel Settings"
3. Modify channel settings
4. Save changes
**Expected**: Channel settings updated successfully

### Step 5: Task Management Test
1. Select a user
2. Click "Task Management"
3. View task statistics
4. Modify task settings
5. Save changes
**Expected**: Task settings updated successfully

### Step 6: Check-in Management Test
1. Select a user
2. Click "Check-in Settings"
3. Modify check-in settings
4. Save changes
**Expected**: Check-in settings updated successfully

### Step 7: Schedule Management Test
1. Select a user
2. Click "Schedule Editor"
3. Modify schedule periods
4. Save changes
**Expected**: Schedule updated successfully

### Step 8: Personalization Test ✅ **FIXED**
1. Select a user
2. Click "Personalization"
3. **EXPECTED**: Dialog opens and works
4. **ACTUAL**: ✅ Dialog opens with all fields prepopulated and functional

### Step 9: Dynamic Updates Test (NEW)
1. Open main admin panel
2. Select a user from dropdown
3. Open any user-editing dialog (category, channel, check-in, etc.)
4. Make changes and save
5. Return to main admin panel
**Expected**: User dropdown automatically refreshes with updated information

### Step 10: Testing Framework Test (NEW)
```bash
python run_tests.py
```
**Expected**: 112 tests passing, 1 skipped (99.1% success rate) - **NOTE**: Only covers 5 core modules

## 📚 Lessons Learned

### UI Migration Best Practices
1. **Generated UI Pattern**: Use `pyside6-uic` to generate UI classes, then subclass for logic
2. **Widget Embedding**: Add widgets to dialogs via code, not QUiLoader at runtime
3. **QSS Scoping**: Never use global QWidget rules that can break indicator rendering
4. **Signal Connections**: Connect signals in subclass, not generated code
5. **Layout Management**: Always ensure every widget in Designer has a layout
6. **Testing**: Run `python run_mhm.py` after every change
7. **Documentation**: Update CHANGELOG.md and TODO.md after significant changes

### File Organization Best Practices
1. **Modular Design**: Split large files into focused modules
2. **Clear Separation**: Separate design (.ui), generated code (_pyqt.py), and implementation (_dialog.py)
3. **Consistent Naming**: Use consistent naming conventions throughout
4. **Logical Grouping**: Group related files in appropriate directories
5. **Documentation**: Document all changes and decisions

### Error Handling Best Practices
1. **Comprehensive Coverage**: Use `@handle_errors` decorators consistently
2. **Graceful Degradation**: Handle missing files and data gracefully
3. **Clear Messages**: Provide clear error messages to users
4. **Logging**: Log all errors for debugging
5. **Recovery**: Implement automatic recovery strategies where possible

### Signal-Based Architecture Best Practices
1. **Decoupled Communication**: Use signals to communicate between dialogs and main window
2. **Automatic Updates**: Connect user_changed signals to refresh functions for real-time updates
3. **Consistent Patterns**: Use the same signal pattern across all user-editing dialogs
4. **Error Handling**: Wrap signal connections in try-catch blocks for robustness
5. **Documentation**: Document signal connections and their purposes

### Testing Best Practices
1. **Comprehensive Coverage**: Test all critical functionality with real behavior testing
2. **Side Effect Verification**: Verify actual system changes, not just return values
3. **Proper Isolation**: Use temporary directories and cleanup for test isolation
4. **Error Scenarios**: Test boundary conditions and error recovery
5. **Integration Testing**: Test cross-module interactions

## 🎯 Realistic Action Plan

### Immediate Priorities (High Priority)
1. **Fix Missing UI Files**: Create missing UI files (user profile dialog now fixed)
2. **Fix Widget Integration**: Resolve "No user_id provided!" errors in widgets
3. **Complete User Profile Dialog Field Support**: ✅ **COMPLETED** - All personalization fields now fully functional
4. **Test Personalization Dialog Save/Load**: ✅ **COMPLETED** - All fields tested and working correctly
5. **Test All Existing Dialogs**: Actually test each dialog to see what works and what doesn't
6. **Fix Dialog Integration**: Ensure dialogs properly communicate with main admin panel
7. **Remove Legacy Tkinter Code**: Clean up old Tkinter interface once PySide6 is fully functional

### High Priority (Next 1-2 weeks)
1. **Comprehensive Testing**: Test every feature systematically
2. **Error Handling**: Add proper error handling to all dialogs
3. **Data Validation**: Add input validation to all forms
4. **User Feedback**: Add proper success/error messages
5. **Performance Testing**: Test UI responsiveness and fix issues

### Medium Priority (Next month)
1. **Widget Refactoring**: Complete the widget system properly
2. **Code Cleanup**: Remove debug code and optimize
3. **Documentation Update**: Update all documentation
4. **Cross-Platform Testing**: Test on different platforms
5. **Advanced Features**: Add any missing advanced features

### Medium-Term Goals
1. **Advanced Widget Features**: Add more advanced widget features
2. **UI Enhancements**: Add more UI enhancements and improvements
3. **Performance Monitoring**: Add performance monitoring
4. **Automated Testing**: Add automated testing framework
5. **Continuous Integration**: Add continuous integration

### Long-Term Goals
1. **Advanced Features**: Add advanced features and capabilities
2. **Scalability**: Improve scalability and performance
3. **User Experience**: Enhance user experience
4. **Maintainability**: Improve maintainability and extensibility
5. **Documentation**: Comprehensive documentation and guides

## 📝 Notes

### Important Considerations
- All changes preserve existing functionality
- Data integrity is maintained throughout migration
- Error handling is comprehensive and robust
- Documentation is updated regularly
- Testing is performed incrementally

### Risk Mitigation
- Backup before major changes
- Test incrementally
- Document all changes
- Maintain backward compatibility where possible
- Provide clear error messages

### Success Criteria
- All functionality works correctly
- UI is responsive and user-friendly
- Code is maintainable and extensible
- Documentation is comprehensive and up-to-date
- Error handling is robust and user-friendly
- Data integrity is maintained throughout migration and restoration

### Migration & Backup Best Practices (NEW)
- Always create a full backup before running any migration scripts or making major data changes.
- Test the migration on a copy of the data first, if possible.
- After migration, verify that all custom user data (such as custom schedule periods) is preserved.
- If any data is lost, use the backup to restore custom content before proceeding.
- Document all migration steps and verification procedures in the changelog and TODO.

### Signal-Based Architecture Benefits (NEW)
- **Real-time Updates**: UI automatically refreshes when user data changes
- **Decoupled Components**: Dialogs don't need to know about main window internals
- **Scalable Design**: Easy to add new dialogs that trigger updates
- **Consistent Behavior**: All user-editing dialogs follow the same update pattern
- **Maintainable Code**: Clear separation of concerns between data changes and UI updates

### Testing Framework Benefits (NEW)
- **Quality Coverage**: 112 tests with 99.1% success rate for covered modules
- **Real Behavior Testing**: Tests verify actual system changes
- **Error Recovery Testing**: Comprehensive error handling and recovery testing
- **Integration Testing**: Cross-module integration verification
- **Performance Testing**: Load and stress testing included
- **Confidence**: Make changes confidently knowing tests will catch issues
- **Coverage Gap**: Only 15% of codebase tested - significant expansion needed

## 📨 Message File Migration & Cleanup (July 2025)

- **Problem**: During migration, message files were unintentionally created for categories users were not opted into, and some files used the old (string list) format.
- **Solution**: Added scripts to:
  - Delete unintentional/invalid message files for non-opted-in categories
  - Ensure message files for enabled categories are always created from `resources/default_messages/` with the correct dictionary format
  - Preserve any existing message files that are already in the correct format
- **Best Practice**: Message files are now only created for categories a user is opted into, and always use the default message library as the source (never create string-list files).
- **Scripts**: See `scripts/fix_user_message_formats.py` (migration) and `scripts/cleanup_user_message_files.py` (cleanup)
- **Status**: ✅ **COMPLETE** - All user message files are now correct and robust against future migrations

## 🗂️ Sent Messages Directory Cleanup (July 2025)

- **Problem**: The global `data/sent_messages` directory was obsolete after migrating to per-user sent message storage, but the app was still checking for and creating it at startup.
- **Solution**: Removed all references to the obsolete global sent messages directory:
  - Removed `SENT_MESSAGES_DIR_PATH` from core path validation in `core/config.py`
  - Removed `SENT_MESSAGES_DIR_PATH` definition from `core/config.py`
  - Removed import references from `core/file_operations.py`
  - Added cleanup tasks to TODO.md for future per-user sent message file migration
- **Impact**: Eliminates unnecessary warnings and directory creation, keeps codebase clean and consistent
- **Status**: ✅ **COMPLETE** - Global sent messages directory references removed
- **Next Steps**: Per-user sent message file migration (planned for future)

### 2025-07-16 - Testing Framework Expansion & Logging Isolation ✅ **COMPLETED**
- **Testing Framework Major Expansion**: Successfully expanded test coverage from 5 to 9 modules with 205 tests passing (95% success rate)
  - **Message Management Tests**: Added comprehensive 25 tests with real file operations and side effect verification
  - **Communication Manager Tests**: Added comprehensive 25 tests with realistic mocks and side effect verification
  - **Task Management Tests**: Added comprehensive 13 tests with real file operations and side effect verification
  - **Service Module Tests**: Added comprehensive 26 tests with real behavior testing and side effect verification
  - **Test Quality Improvements**: All new tests use real behavior testing, verify actual system changes, and are properly isolated
- **Test Coverage Improvement**: Increased from 15% to 29% of codebase coverage
  - **Modules Now Tested**: Error Handling, File Operations, User Management, Scheduler, Configuration, Message Management, Communication Manager, Task Management, Service Management
  - **Test Categories**: 9 major categories covered with comprehensive testing
  - **Integration Testing**: Cross-module integration testing for all covered modules
- **Real Behavior Testing**: Majority of tests now verify actual system changes, not just return values
  - **File Operations**: Tests verify actual file creation, modification, and deletion
  - **Side Effects**: Tests verify that functions actually change system state
  - **Data Persistence**: Tests verify that data is properly saved and loaded
  - **Error Recovery**: Tests verify proper error handling and recovery strategies
  - **Service State Changes**: Tests verify actual service state modifications (running/stopped)
  - **Signal Handling**: Tests verify actual signal handler behavior
  - **Integration Testing**: Tests verify real interactions between modules
- **Test Isolation**: All tests use temporary directories and proper cleanup
  - **No Interference**: Tests don't interfere with each other or the real system
  - **Consistent Results**: Tests produce consistent, reliable results
  - **Clean Environment**: Each test runs in a clean, isolated environment
- **UI Test Improvements**: Fixed major UI test issues and improved test reliability
  - **Validation Logic**: Updated validation to properly check for required fields (internal_username, channel)
  - **Test Data Structure**: Fixed tests to provide proper data structure with required fields
  - **User Directory Creation**: Fixed tests to create user directories before saving data
  - **Tab Enablement**: Fixed UI tests to use proper checkbox interaction methods (setChecked instead of mouseClick)
  - **Test Isolation**: Improved test isolation and cleanup procedures
- **Logging Isolation System**: Implemented comprehensive logging isolation to prevent test logs from contaminating main application logs
  - **Environment Variable Control**: Uses `MHM_TESTING=1` environment variable to signal test mode
  - **Test Logging Setup**: Tests use dedicated test logger that writes to `tests/logs/` directory
  - **Main Logger Isolation**: Main application logger setup is skipped when in test mode
  - **Failsafe Implementation**: Added failsafe in `core/logger.py` that forcibly removes all handlers from root logger and main logger when `MHM_TESTING=1` is set
  - **Complete Separation**: Test logs go to `tests/logs/` directory, application logs go to `app.log`
  - **No Cross-Contamination**: Test logs never appear in `app.log`, application logs never appear in test logs
  - **Automatic Cleanup**: Test logging isolation is automatically activated and deactivated during test runs
- **Configuration Warning Suppression**: Eliminated intrusive configuration warning popups for non-critical warnings
  - **Warning Filtering**: Non-critical warnings (default values, auto-creation settings) are logged instead of showing popups
  - **UI Integration**: Updated both PySide6 and Tkinter UI versions to filter warnings appropriately
  - **Validation Logic Fix**: Fixed LM Studio API key validation to only warn when explicitly set to empty, not when using defaults
  - **User Experience**: Service starts without interruption from non-critical configuration warnings
- **Impact**: Significantly improved code reliability and confidence in making changes, complete logging isolation achieved, better user experience
- **Status**: ✅ **COMPLETED** - Testing framework expanded with high-quality, comprehensive tests and complete logging isolation

### 2025-07-15 - Personalization Management Cleanup & Centralized Saving System ✅ **COMPLETED**

### 2025-07-15 - AI Documentation System Enhancements ✅ **COMPLETED**
- **Version Synchronization Tool**: Created automated system for maintaining consistent versions across all AI documentation
  - **`ai_tools/version_sync.py`**: Automatically updates version numbers and dates across all AI documentation files
  - **Prevents Manual Maintenance**: Eliminates need to manually track and update versions
  - **Date Accuracy**: Uses system date to prevent AI date misidentification
  - **Consistent Formatting**: Ensures all files have uniform version and date information
  - **Easy Usage**: Simple commands like `python ai_tools/version_sync.py sync` to update all files
- **Enhanced Tool Integration**: Created comprehensive guide for AI tool usage and output interpretation
  - **`ai_tools/tool_guide.py`**: Provides specific guidance on when to use each audit tool
  - **Output Interpretation**: Explains what each tool's output means and how to interpret results
  - **Tool Recommendations**: Suggests appropriate tools for specific scenarios
  - **Success Criteria**: Defines what good output looks like for each tool
  - **Guided Execution**: Can run tools with real-time guidance on what to look for
- **Quick Reference Troubleshooting**: Enhanced quick reference with troubleshooting section
  - **Common Issues**: Added quick solutions for typical problems
  - **Cross-References**: Points to detailed troubleshooting in `AI_RULES.md`
  - **Immediate Solutions**: Provides instant guidance for urgent issues
  - **Escalation Paths**: Clear paths from quick fixes to detailed solutions
- **AI Tools Documentation**: Updated `ai_tools/README.md` with new tools and usage examples
  - **New Tool Documentation**: Added entries for `version_sync.py` and `tool_guide.py`
  - **Enhanced Quick Start**: Added examples for new tool usage
  - **Usage Patterns**: Shows common command patterns for different scenarios
- **Impact**: Significantly improves AI effectiveness by providing better tool guidance, automated maintenance, and enhanced troubleshooting capabilities
- **Status**: ✅ **COMPLETED** - AI documentation system now has automated maintenance and comprehensive tool guidance

### 2025-07-13 - Dialog & Widget Data Structure Fixes & Testing Framework ✅ **COMPLETED**
- **Data Structure Standardization**: Fixed KeyError in remove_period_row by standardizing on canonical `start_time`/`end_time` keys throughout all widgets and dialogs
- **Period Management Fixes**: Fixed undo functionality and period naming issues by correcting argument passing and data structure consistency
- **Default Time Updates**: Updated default period times from 09:00-17:00 to 18:00-20:00 to match system defaults
- **Debug Code Cleanup**: Removed all print statements and static test labels from widgets for clean codebase
- **Schedule Saving Fix**: Fixed `set_schedule_periods` function to properly handle the new user data structure and save changes to schedule files
- **Comprehensive Testing**: Created and executed test script to verify all dialog functionality works correctly
- **Status**: ✅ **COMPLETED** - All dialog features (add/remove/undo/save/enable/disable/persistence) now working correctly

### 2025-07-13 - Dialog & Widget Alignment, Debug Cleanup, and Testing To-Do ✅ **COMPLETED**
- **Dialog/Widget Alignment**: Check-in and Task Management dialogs and widgets have been fully aligned. Parenting, method structure, and widget instantiation are now consistent, eliminating subtle display bugs.
- **Debug Code Removal**: All display/diagnosis debug code and print statements have been removed from UI and core files for a clean codebase and log output.
- **Testing Completed**: All dialog features (add/remove/undo/save/enable/disable/persistence/edge cases) have been tested and verified working correctly.
- **Status**: ✅ **COMPLETED** - All major dialog functionality is now working as expected

### 2025-07-16 - Windows Python Process Behavior Investigation ✅ **COMPLETED**
- **Windows Python Process Behavior Investigation**: Investigated and documented Windows-specific Python process behavior
  - **Problem**: Windows was launching two Python processes when running scripts (venv Python + system Python)
  - **Root Cause**: Windows behavior where Python script execution creates dual processes regardless of subprocess calls
  - **Investigation**: Tested multiple approaches including batch files, direct venv Python calls, and shebang line removal
  - **Findings**: This is normal Windows behavior and doesn't affect application functionality
  - **Solution**: Documented as expected behavior, no code changes needed
  - **Impact**: Application works correctly despite dual processes - venv Python runs actual code, system Python is harmless artifact
  - **Files Updated**: Removed test files created during investigation
- **Status**: ✅ **COMPLETED** - Windows Python process behavior documented as normal, no action needed

### 2025-07-16 - Test File Organization & Documentation Updates ✅ **COMPLETED**
- **Test File Organization**: Successfully moved all test files to their appropriate directories
  - **Real Behavior Tests**: `test_account_management_real_behavior.py` moved to `tests/behavior/`
  - **Integration Tests**: `test_account_management.py` moved to `tests/integration/`
  - **UI Tests**: `test_dialogs.py` moved to `tests/ui/`
  - **Utility Scripts**: `fix_test_calls.py` moved to `scripts/`
  - **Directory Structure**: Tests now properly organized by type (unit, integration, behavior, ui)
  - **Clean Root Directory**: No more test files cluttering the project root
- **Documentation Updates**: Updated all documentation files to reflect current state
  - **TESTING_IMPROVEMENT_PLAN.md**: Updated to reflect 100% test success rate and completed organization
  - **TODO.md**: Updated to reflect completed test organization tasks
  - **CHANGELOG.md**: Added entry for test file organization completion
- **Impact**: Improved project organization and documentation accuracy
- **Status**: ✅ **COMPLETED** - All test files properly organized and documentation updated

### Completed Cleanup Tasks ✅
- **User Profile Settings Scroll Area Fixes** - Fixed mouse wheel scrolling to work anywhere within group boxes, not just over scroll bars (July 2025)
  - *What it means*: Users can now scroll smoothly when hovering over checkboxes, text fields, and other interactive elements
  - *Why it helps*: Better user experience with consistent scrolling behavior across all tabs
  - *Status*: ✅ **COMPLETED** - Scrolling now works consistently, matching task/checkin dialog behavior
  - *Technical Details*: Removed custom wheel event handling, used standard Qt scroll areas with proper size policies

---

**Status**: ⚠️ **PARTIALLY COMPLETE** - Solid foundation established, but many dialogs broken due to missing UI files and integration issues  
**Last Updated**: 2025-07-14  
**Next Review**: As needed for new features or improvements 