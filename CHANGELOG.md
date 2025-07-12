# MHM System Changelog
This log tracks recent updates and improvements. See TODO.md for current priorities and ARCHITECTURE.md for system structure.

## 🗓️ Recent Changes (Most Recent First)

### 2025-07-11 - Sent Messages Directory Cleanup
- **Global Directory References Removed**: Eliminated all references to the obsolete global `data/sent_messages` directory
  - Removed `SENT_MESSAGES_DIR_PATH` from core path validation in `core/config.py`
  - Removed `SENT_MESSAGES_DIR_PATH` definition from `core/config.py`
  - Removed import references from `core/file_operations.py`
  - Added cleanup tasks to TODO.md for future per-user sent message file migration
- **Eliminated Startup Warnings**: App no longer checks for or creates the obsolete global sent messages directory
- **Codebase Consistency**: Keeps codebase clean and consistent with per-user sent message storage architecture
- **Impact**: Removes unnecessary warnings and directory creation, improves startup experience
- **Status**: ✅ **COMPLETED** - Global sent messages directory references removed

### 2025-07-11 - Message File Creation Architecture Improvements
- **Refactored Message File Creation Logic**: Improved efficiency and cleaner architecture for message file creation
  - Removed directory creation from `create_message_file_from_defaults()` (now handled by `create_user_files()` during account creation)
  - Made `ensure_user_message_files()` accept subset of categories for targeted creation (validation checks all, updates check only new categories)
  - Improved separation of concerns: validation checks missing files, worker creates them
- **Eliminated Redundant Operations**: Removed duplicate file existence checks and directory creation calls
- **Better Use Case Support**: Different scenarios now use appropriate functions:
  - Account creation: `create_user_files()` creates directory, calls `create_message_file_from_defaults()` for each category
  - Validation: `ensure_user_message_files()` checks all categories, creates missing files
  - Category updates: `ensure_user_message_files()` checks only new categories, creates missing files
- **Impact**: More efficient file creation, cleaner code architecture, and better separation of responsibilities

### 2025-07-11 - Default Message Library Population Fix
- **Fixed Default Message Population**: Updated create_user_files to properly populate user message files from default_messages with correct format (days, time_periods, message_id fields)
- **Created Migration Script**: Added scripts/fix_user_message_formats.py to migrate existing user message files from old format (list of strings) to new format (list of dictionaries)
- **Created Cleanup Script**: Added scripts/cleanup_user_message_files.py to delete unintentional message files for non-opted-in categories and ensure only enabled categories have message files
- **Best Practice**: Message files are now only created for categories a user is opted into, always using default_messages as the source
- **Added Helper Functions**: Created populate_user_messages_from_defaults() and migrate_user_message_format() functions in core/message_management.py
- **Impact**: New users will get properly formatted message files, existing users can run migration/cleanup scripts to fix their files

### 2025-07-11 - User Index Redesign, Survey Cleanup & Signal-Based Dynamic Updates
- **User Index Redesign**: Completely redesigned user index structure to be more relevant and current
  - New structure: `internal_username`, `active`, `channel_type`, `enabled_features`, `last_interaction`, `last_updated`
  - Automatic index updates whenever users are created/modified
  - Fixed format consistency issues across all user entries
  - UI now uses user index instead of scanning directories directly
- **Survey Responses Cleanup**: Removed all unused survey functionality from codebase
  - Deleted all `survey_responses.json` files from user directories
  - Removed survey-related code from core modules (`user_data_manager.py`, `file_operations.py`, `config.py`, `response_tracking.py`)
  - No more unused survey functionality cluttering the codebase
- **Signal-Based Dynamic Updates**: Implemented real-time UI updates when user data changes
  - Added `user_changed` signals to all user-editing dialogs (AccountCreatorDialog, CategoryManagementDialog, CheckinManagementDialog, UserProfileDialog, ChannelManagementDialog, TaskManagementDialog)
  - Connected signals to `refresh_user_list()` in main window
  - User dropdown automatically refreshes with updated information after any user data change
  - Consistent data synchronization across all UI components
- **Impact**: More responsive UI, cleaner codebase, better data consistency, and improved user experience with real-time updates
- **Status**: ✅ **COMPLETED** - User index synchronization, survey cleanup, and signal-based updates


### 2025-07-10 - Schedule Data Migration, Restoration & Bugfixes
- **Schedule Data Migration**: Successfully migrated all user schedule data to the new nested format with periods sub-dict
- **Custom Period Restoration**: Restored custom schedule periods for all users after migration
- **'ALL' Period Scheduling Bug Fixed**: Fixed bug where 'ALL' period was incorrectly scheduled; now only used as fallback
- **Migration/Backup Best Practices**: Established workflow for backup before migration, verification after migration, and restoration if needed
- **Impact**: Data integrity preserved, user customizations restored, and scheduling logic now works as intended

### 2025-07-07 - UI Directory Reorganization & PySide6 Migration Completion
- **Complete UI Reorganization**: Successfully reorganized UI directory structure with clear separation of concerns
- **Directory Structure**: Created `ui/designs/` for .ui files, `ui/generated/` for auto-generated Python classes, `ui/dialogs/` for dialog implementations, and `ui/widgets/` for widget implementations
- **Naming Convention Standardization**: Removed redundant `ui_app_` prefix and implemented consistent naming patterns (e.g., `createaccount` → `account_creator`, `editschedule` → `schedule_editor`)
- **PySide6 Migration**: Completed migration from Tkinter to PySide6/Qt for all UI components
- **Generated UI Files**: Successfully regenerated all PyQt Python files from updated .ui files using `pyside6-uic`
- **File Mapping**: Updated all file references and imports to use new naming conventions
- **Code Cleanup**: Moved test and debug files to `scripts/` directory for better organization
- **Impact**: Cleaner, more maintainable UI architecture with proper separation of design, generated code, and implementation
- **Status**: ✅ **COMPLETED** - Full UI reorganization and PySide6 migration

### 2025-07-07 - Default Schedule Periods for New Categories
- **Default Schedule Creation**: Added automatic creation of default schedule periods (18:00-20:00) for new categories
- **Legacy Migration**: Implemented migration system to convert existing flat schedule structure to new nested format
- **Fallback Period**: Ensured "ALL" period (00:00-23:59) is always available as a fallback for all categories
- **Schedule Management**: Added `load_user_schedules_data()`, `save_user_schedules_data()`, and `update_user_schedules()` functions
- **Migration Functions**: Created `migrate_legacy_schedules_structure()` and `ensure_category_has_default_schedule()` for data consistency
- **Integration**: Modified `update_user_preferences()` to automatically create default schedules when new categories are added
- **File Operations**: Updated `create_user_files()` to include default periods when creating new user files
- **Impact**: Every new category now has sensible default schedule periods, improving user experience and reducing setup time
- **Status**: ✅ **COMPLETED** - Default schedule periods with legacy migration and automatic creation

### 2025-07-04 - PySide6 UI Migration & QUiLoader Implementation
- **Complete UI Framework Migration**: Successfully migrated entire admin interface from Tkinter to PySide6/Qt
- **Qt Designer Integration**: Implemented workflow for designing UI layouts in Qt Designer and loading .ui files at runtime
- **Main Admin Panel Migration**: Migrated comprehensive admin panel with service management, user management, and content management features
- **QUiLoader Implementation**: Implemented proper loading of .ui files using QUiLoader for better maintainability and visual design workflow
- **UI File Structure**: Created and integrated ui_app_mainwindow.ui and ui_app_createaccount_dialogue.ui files
- **QSS Theme Integration**: Added support for loading and applying QSS themes (admin_theme.qss) to enhance UI appearance
- **Account Creation Dialog Refactoring**: Refactored account creation dialog to load directly from .ui file with collapsible sections
- **Service Management Integration**: Migrated service start/stop/restart functionality with proper process management
- **User Management Features**: Migrated user selection, category management, and user action buttons
- **Error Handling**: Implemented comprehensive error handling for UI loading, theme application, and service operations
- **Signal/Slot Connections**: Properly wired up UI signals and slots for buttons, dropdowns, and interactive elements
- **Collapsible Sections**: Implemented collapsible task management and check-in sections in account creation dialog
- **Best Practices Established**: Determined optimal approach for dialog structure using QDialog as root widget in .ui files
- **Widget Refactoring Planning**: Identified need for reusable widgets (task management, check-in settings, personalization) to eliminate code duplication
- **Code Organization**: Improved separation of concerns by using function-based dialog creation instead of class-based approach
- **Theme Fallback Handling**: Implemented graceful degradation when QSS theme files are missing
- **Cross-Platform Compatibility**: Ensured PySide6 UI works consistently across Windows, Linux, and macOS
- **Impact**: Complete UI modernization with better maintainability, consistent behavior, visual design capabilities, and foundation for future widget-based architecture
- **Status**: ✅ **COMPLETED** - Full PySide6 migration with Qt Designer integration and QSS theming

### 2025-07-07 - UI Migration Finalization & Check-in Frequency Update
- **Check-in Frequency Logic Removed**: All frequency logic removed from check-in settings; now every applicable time period prompts a check-in
- **Widget/Dialog Naming Standardization**: All widgets and dialogs now use consistent, clear names
- **PySide6 Migration Finalized**: All major dialogs and widgets are now PySide6-based and working
- **Widget Refactoring**: Nearly complete; only minor polish and testing remain
- **Error Handling & UI Consistency**: Improved error handling and UI consistency across dialogs
- **Next Steps**: Comprehensive dialog and widget testing for visual and functional correctness

### 2025-07-03 - Smart Task Reminder Scheduling Implementation
- **Intelligent Task Selection**: Implemented smart task reminder scheduling that picks one random task per reminder period instead of scheduling every task
- **Random Time Scheduling**: Added random time generation within reminder periods (e.g., between 17:00-18:00) instead of always scheduling at the start time
- **New Helper Method**: Added `get_random_time_within_task_period()` method to generate random times within specified time ranges
- **Improved Scheduler Logic**: Updated `schedule_all_task_reminders()` to select one random incomplete task per active reminder period
- **Better Logging**: Enhanced logging to show which specific task was selected and at what random time
- **Reduced Notification Spam**: Users now receive only one task reminder per period instead of reminders for every task
- **Impact**: More intelligent and user-friendly task reminder system that prevents notification overload while ensuring important tasks are not forgotten
- **Status**: ✅ **COMPLETED** - Smart task reminder scheduling with random task selection and timing

### 2025-07-01 - Task Management System Implementation (Phase 1)
- **Core Task Management**: Implemented comprehensive task CRUD operations in `tasks/task_management.py`
- **Task Data Structure**: Created modular file structure with `active_tasks.json`, `completed_tasks.json`, and `task_schedules.json`
- **Scheduler Integration**: Added task reminder scheduling to `core/scheduler.py` with methods for scheduling and cleanup
- **Communication Integration**: Integrated task reminders into `bot/communication_manager.py` with priority emojis and formatting
- **User Preferences**: Added task management preferences to user settings with enable/disable toggle and default reminder time
- **Error Handling**: Comprehensive error handling throughout task management system
- **Admin UI Integration**: Added task management to account creation and user management interfaces
  - Task management section in account creator with enable/disable toggle and default reminder time
  - Task management window in account manager with settings and statistics
  - Task management button in main admin UI
  - Automatic task file creation during user setup
- **File Operations**: Updated `core/file_operations.py` to support task file structure and creation
- **Scheduler Integration**: Task reminders are automatically scheduled when service starts
- **Task Reminder Messages**: Formatted task reminders with priority indicators, due dates, and management instructions
- **Impact**: Foundation for comprehensive task management with communication channel integration
- **Status**: ✅ **PHASE 1 COMPLETED** - Basic task management with scheduling and reminders

### 2025-07-01 - Check-in & Schedule Management System Improvements
- **Unified Save Method**: Both check-in settings and category schedules now use `save_user_info_data` consistently
- **Data Preservation**: Fixed edge cases where editing one type of schedule could overwrite the other
- **Category Management Bug Fix**: Fixed incorrect nesting of preferences that could cause data loss
- **Improved Error Handling**: Better handling of missing files, empty data structures, and first-time users
- **Consistent Data Structure**: Ensures proper structure for preferences, schedules, and user data
- **Edge Case Handling**: Properly handles first-time check-in enablement and new category addition
- **Impact**: More reliable schedule management, prevents data loss, and handles all user scenarios correctly

### 2025-07-01 - Debug/IDE Config Cleanup & Service Process Investigation
- **Investigated double service process issue**: Confirmed that VS Code/Cursor debug/play button launches an extra service process due to IDE/debugger quirks, not project code.
- **Temporary debug code removed**: Cleaned up print statements and debug logging from `run_mhm.py` and `core/service.py`.
- **Removed .vscode/launch.json and .vscode/settings.json**: Debug/IDE config files added for troubleshooting were deleted after confirming they did not resolve the issue.
- **Impact**: Project is now clean and back to its original state; running from the terminal with venv activated is the recommended workflow for now.

### 2025-06-30 - Enhanced Message Dialog UX
- **Improved Checkbox Behavior**: Removed disabled state from individual checkboxes when "Select All" is selected
- **Better User Control**: Users can now modify individual selections even when "Select All" is checked
- **Automatic "ALL" Conversion**: Enhanced logic to automatically convert all selected items to "ALL" format when saving
- **Smart "Select All" Detection**: "Select All" checkbox automatically updates based on individual selections
- **Consistent Data Format**: Ensures all messages use simplified "ALL" format when appropriate
- **Impact**: More intuitive and flexible user interface for message creation and editing

### 2025-06-30 - UI & Scheduling Improvements
- **Persistent 'ALL' Time Period**: Ensured 'ALL' period is always present as a fallback in scheduling logic
- **Default Messages**: Updated to support both 'default' (editable) and 'ALL' (special fallback) time periods
- **Add/Edit Message Dialog**: Improved UI with bold 'Select All' checkboxes, better prefill logic, and clearer labels
- **Time Period Sorting**: Fixed sorting to use true chronological order (minutes since midnight)
- **Treeview Enhancements**: Added ALL DAYS/TIMES columns, improved checkmark visuals, and restored sorting for all columns
- **Bug Fixes**: Fixed issues with missing user files, error handling, and false positive warnings
- **UI/UX Improvements**: Incremental improvements based on user feedback (font sizes, colors, layout)
- **Documentation**: Updated TODO.md and CHANGELOG.md, removed completed items

### 2025-06-29 - Documentation & Error Handling Milestone
- **Major documentation reorganization and TODO consolidation**
  - Moved all legacy future improvements from README.md into TODO.md
  - Grouped improvements into logical categories (User Experience, AI & Intelligence, Task Management, Analytics, Code Quality)
  - Provided clear explanations for each improvement with "What it means" and "Why it helps"
  - Added priority levels (High/Medium/Low) and effort estimates (Small/Medium/Large) for each item
  - Removed the legacy "Future Improvements" section from README.md
  - TODO.md now serves as the single source of truth for all planned improvements
  - Clearer project roadmap with better prioritization and context for each planned improvement
- **MAJOR MILESTONE: Implement comprehensive error handling across all 31 modules**
  - Add core/error_handling.py with robust error handling framework
  - Replace all try/except blocks with @handle_errors decorators
  - Add custom exceptions (DataError, FileOperationError, etc.)
  - Implement automatic recovery strategies and graceful degradation
  - Update all core, UI, bot, user, task, and infrastructure modules
  - Achieve 100% error handling coverage across entire system
  - Improve reliability, user experience, and debugging capabilities
  - Update documentation to reflect major achievement

### 2025-06-28 - AI Agent Guidance Consolidation (COMPLETED)
- **Rule Consolidation**: Reduced from 10 rules to 5 focused rules to decrease cognitive load
- **Proper Cursor Implementation**: Implemented correct MDC format with proper metadata and file patterns
- **Core Guidelines Rule**: Created `core-guidelines.mdc` combining essential development rules, user context, and communication
- **Development Tasks Rule**: Created `development-tasks.mdc` combining PowerShell operations and common task workflows
- **Code Quality Rule**: Created `code-quality.mdc` combining code patterns and AI optimization strategies
- **Organization Rule**: Created `organization.mdc` for documentation and script organization guidelines
- **File Pattern Optimization**: Fixed file patterns to work with actual project files (`*.py`, `*.md`, `*.txt`)
- **Rule Type Optimization**: Set appropriate Always/Auto Attached/Agent Requested types for optimal context application
- **Impact**: Significantly reduced AI guidance complexity while maintaining comprehensive coverage, improved rule targeting and effectiveness

### 2025-06-27 - Utils.py Refactoring (COMPLETED)
- **Modular Architecture**: Successfully refactored monolithic `core/utils.py` (1,492 lines) into 7 focused modules
- **New Modules**: Created `core/file_operations.py`, `core/user_management.py`, `core/message_management.py`, `core/schedule_management.py`, `core/response_tracking.py`, `core/service_utilities.py`, `core/validation.py`
- **Function Migration**: Moved all 57 functions to appropriate modules with 100% functionality preserved
- **Import Updates**: Updated all imports throughout the codebase to use specific modules
- **Testing**: Comprehensive testing confirms all functionality working correctly
- **Documentation**: Updated README.md and ARCHITECTURE.md to reflect new structure
- **Impact**: Significantly improved code organization, maintainability, and development experience

### 2025-06-26 - Configuration Validation System
- **Comprehensive Validation**: Added startup configuration validation to prevent mysterious errors
- **Validation Categories**: Core paths, AI settings, communication channels, logging, scheduler, file organization
- **UI Integration**: Added "Validate Configuration" menu item with detailed report and help
- **Standalone Script**: Created `scripts/validate_config.py` for independent configuration checking
- **Early Detection**: Service and UI now validate configuration before starting, with clear error messages
- **Custom Exceptions**: Added ConfigValidationError with detailed error information
- **Validation Functions**: Implemented validate_core_paths(), validate_ai_configuration(), validate_communication_channels(), validate_logging_configuration(), validate_scheduler_configuration(), validate_file_organization_settings(), validate_environment_variables()
- **Comprehensive Reporting**: Added validate_all_configuration() and print_configuration_report() functions
- **Impact**: Prevents startup failures and provides clear guidance for fixing configuration issues
- **Status**: ✅ **FULLY COMPLETED** - All validation functions implemented and integrated into startup process

### 2025-06-26 - Documentation & Merge Resolution
- **Documentation Reorganization**: Reorganized documentation structure and added future improvements roadmap
- **Project Direction**: Clarified project direction and updated AGENTS.md with comprehensive instructions
- **Merge Resolution**: Resolved conflicts and synchronized local and remote changes
- **Impact**: Better project documentation and clearer development guidelines

### 2025-06-24 - UI Settings Fixes & Documentation
- **Settings Accuracy**: Fixed Communication, Check-in, and Category Settings windows to accurately reflect user preferences
- **UserPreferences TODO**: Updated README with UserPreferences implementation roadmap
- **Impact**: UI now correctly displays and saves user settings

### 2025-06-23 - Code Quality & Bug Fixes
- **Path Refactoring**: Refactored paths to use config constants for better maintainability
- **Default Messages Fix**: Fixed path for default messages and resolved sorting bug
- **Static Methods**: Converted schedule helper methods to static wrappers
- **Line Endings**: Added .gitattributes file and normalized line endings to LF
- **Docstring Fixes**: Fixed encoding in list_tasks docstring
- **Impact**: Improved code quality, maintainability, and cross-platform compatibility

### 2025-06-18 - Logging System Cleanup & Optimization
- **Logging Optimization**: Reduced log noise by ~80% while preserving critical debugging info
- **Duplicate Prevention**: Added deduplication to prevent multiple messages from schedule changes
- **Impact**: Cleaner system logs and eliminated duplicate messages

### 2025-06-17 - Schedule & Logging Fixes
- **Schedule Rescheduling**: Fixed UI schedule edits not triggering background rescheduling
- **Logging Cleanup**: Fixed misleading scheduler status messages and unnecessary force restarts
- **False Positive Fixes**: Resolved false positive logging restarts and unnecessary log suffixes
- **Impact**: Schedule changes now work properly; eliminated duplicate messages

### 2025-06-11 - Initial Commit
- Initial commit: Mental Health Management (MHM) system

### 2025-07-07 - Messaging Service Field Migration & Data Model Modernization
- **Canonical Field Update**: Migrated all code and user data to use `preferences['channel']['type']` as the canonical field for messaging service selection
- **Legacy Field Removal**: Deprecated and removed the legacy `preferences['messaging_service']` field from all user data
- **Codebase Update**: Updated all code to read from `channel['type']` with a temporary fallback to `messaging_service` for legacy support
- **Migration Script**: Added and ran a migration script to move any legacy `messaging_service` values to `channel['type']` and remove the old field
- **Verification**: Verified all user data is now clean and consistent; fallback can be removed in the future
- **Documentation**: Updated best practices and documentation to reflect the new canonical field
- **Impact**: Ensures data consistency, future-proofs messaging service selection, and simplifies codebase
- **Status**: ✅ **COMPLETED** - Messaging service field migration and codebase modernization

### 2025-07-08 - Modular Period Widget Management & UI Logic Refactor
- **Modular Period Management**: Refactored period widget logic into reusable functions and standardized handling across all relevant dialogs
- **UI Logic Separation**: Created core/ui_management.py to house UI-specific period management logic, improving maintainability
- **Bug Fixes**: Resolved groupbox checkbox visual issues, period prepopulation bugs, and period naming inconsistencies
- **Outstanding Issue**: Schedule saving callback signature mismatch to be fixed

---

## 📝 How to Add Changes

When adding new changes, follow this format:

```markdown
### YYYY-MM-DD - Brief Title
- **Feature**: What was added/changed
- **Impact**: What this improves or fixes
```

Keep entries **concise** and **scannable**. Focus on **what changed** and **why it matters**.

## [Unreleased] - Task Management Implementation

### Phase 1: Foundation (COMPLETED) ✅
- **Core Task Management**: Implemented comprehensive task CRUD operations in `tasks/task_management.py`
- **Task Data Structure**: Created modular file structure with `active_tasks.json`, `completed_tasks.json`, and `task_schedules.json`
- **Scheduler Integration**: Added task reminder scheduling to `core/scheduler.py` with methods for scheduling and cleanup
- **Communication Integration**: Integrated task reminders into `bot/communication_manager.py` with priority emojis and formatting
- **User Preferences**: Added task management preferences to user settings with enable/disable toggle and default reminder time
- **Error Handling**: Comprehensive error handling throughout task management system
- **Admin UI Integration**: Added task management to account creation and user management interfaces
  - Task management section in account creator with enable/disable toggle and default reminder time
  - Task management window in account manager with settings and statistics
  - Task management button in main admin UI
  - Automatic task file creation during user setup
- **File Operations**: Updated `core/file_operations.py` to support task file structure and creation

### Phase 2: Advanced Features (PLANNED)
- **Schedule Time Periods**: Allow users to set specific time periods for task reminders
- **Individual Task Reminders**: Custom reminder times for individual tasks
- **Recurring Tasks**: Support for daily, weekly, monthly, and custom recurring patterns
- **Priority Escalation**: Automatic priority increase for overdue tasks
- **AI Chatbot Integration**: Full integration with AI chatbot for task management

### Phase 3: Communication Channel Integration (PLANNED)
- **Discord Integration**: Full Discord bot integration for task management
- **Email Integration**: Email-based task management
- **Telegram Integration**: Telegram bot integration for task management
- **Cross-Channel Sync**: Synchronize tasks across all communication channels

### Phase 4: AI Enhancement (PLANNED)
- **Smart Task Suggestions**: AI-powered task suggestions based on user patterns
- **Natural Language Processing**: Create and manage tasks using natural language
- **Intelligent Reminders**: AI-determined optimal reminder timing
- **Task Analytics**: AI-powered insights into task completion patterns