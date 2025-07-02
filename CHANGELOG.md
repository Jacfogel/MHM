# MHM System Changelog
This log tracks recent updates and improvements. See TODO.md for current priorities and ARCHITECTURE.md for system structure.

## 🗓️ Recent Changes (Most Recent First)

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

---

## 📝 How to Add Changes

When adding new changes, follow this format:

```markdown
### YYYY-MM-DD - Brief Title
- **Feature**: What was added/changed
- **Impact**: What this improves or fixes
```

Keep entries **concise** and **scannable**. Focus on **what changed** and **why it matters**.