# TODO - Development Priorities

> **Audience**: Human Developer (Beginner Programmer)  
> **Purpose**: Current development priorities and planned improvements  
> **Style**: Organized, actionable, beginner-friendly

## [Navigation](#navigation)
- **[Project Overview](README.md)** - What MHM is and what it does
- **[Quick Start](HOW_TO_RUN.md)** - Setup and installation instructions
- **[Development Workflow](DEVELOPMENT_WORKFLOW.md)** - Safe development practices
- **[Quick Reference](QUICK_REFERENCE.md)** - Common commands and shortcuts
- **[Architecture](ARCHITECTURE.md)** - System design and components
- **[Recent Changes](CHANGELOG.md)** - What's new and what's changed

## 🎯 Current Priority Tasks

### Immediate Action Items (High Priority)
These improvements will fix critical issues and make the app actually functional:

1. **Personalization Management Cleanup & Centralized Saving System** - ✅ **COMPLETED**
   - *What it means*: Migrated all personalization functions to user_management.py and implemented unified saving system
   - *Why it helps*: Cleaner codebase with unified data access patterns and robust test coverage
   - *Status*: ✅ **COMPLETED** - All 112 tests passing, legacy code removed, centralized saving implemented

2. **AI Documentation System Enhancements** - ✅ **COMPLETED**
   - *What it means*: Created automated version synchronization and comprehensive tool guidance for AI documentation
   - *Why it helps*: Significantly improves AI effectiveness with automated maintenance and better tool guidance
   - *Status*: ✅ **COMPLETED** - Version sync tool, tool guide, and enhanced troubleshooting implemented

3. **Testing Framework Improvements** - ✅ **COMPLETED**
   - *What it means*: Improving test quality to use real file operations and verify side effects
   - *Why it helps*: Ensures tests provide real value and catch actual issues
   - *Status*: ✅ **COMPLETED** - All planned test improvements implemented
   - *Progress*: 
     - ✅ **Message Management Tests** - Refactored to use real file operations and verify side effects
     - ✅ **Communication Manager Tests** - Improved with realistic mocks and side effect verification
     - ✅ **Task Management Tests** - Refactored for real file operations and side effects
     - ✅ **Service Module Tests** - Added comprehensive 26 tests with real behavior testing
     - ✅ **Test Coverage Expansion** - Increased from 5 to 9 modules (15% to 29% coverage)
     - ✅ **Test Quality** - 185 tests passing with 99.5% success rate
     - ✅ **Real Behavior Testing** - Majority of tests now verify actual system changes

4. **Fix Missing UI Files** - Create missing UI files for broken dialogs
   - *What it means*: Several dialogs are trying to load UI files that don't exist (user profile dialog now fixed)
   - *Why it helps*: Makes broken dialogs functional again
   - *Priority*: High
   - *Estimated effort*: Small

5. **Account Creation Dialog Improvements** - ✅ **COMPLETED**
   - *What it means*: Redesigned account creation dialog with feature-based enablement and conditional tab visibility
   - *Why it helps*: Better user experience with logical feature selection and clear organization
   - *Status*: ✅ **COMPLETED** - Feature-based account creation implemented with proper validation and conditional UI

6. **Fix Widget Integration Issues** - ✅ **COMPLETED**
   - *What it means*: Widgets were showing errors because they weren't receiving proper user_id parameters
   - *Why it helps*: Eliminates error messages and makes widgets functional
   - *Status*: ✅ **COMPLETED** - Widgets now handle new user creation mode properly

7. **Complete User Profile Dialog Field Support** - ✅ **COMPLETED**
   - *What it means*: All personalization fields now save/load correctly with proper validation and prepopulation
   - *Why it helps*: Ensures all user data is editable and persistent
   - *Status*: ✅ **COMPLETED** - All fields functional including preferred name, gender identity, health data, interests, goals, loved ones, and timezone

8. **Test Personalization Dialog Save/Load** - ✅ **COMPLETED**
   - *What it means*: All fields in the personalization dialog are saved and loaded correctly with proper validation
   - *Why it helps*: Prevents data loss and ensures a reliable user experience
   - *Status*: ✅ **COMPLETED** - Comprehensive testing confirms all functionality works correctly

9. **Test All Existing Dialogs** - Actually test each dialog to see what works
   - *What it means*: Systematically test each dialog to identify what's broken vs. what works
   - *Why it helps*: Provides accurate assessment of current state and identifies specific issues
   - *Priority*: High
   - *Estimated effort*: Medium

10. **Test Feature-Based Account Creation** - Verify the new account creation workflow
    - *What it means*: Test the feature enablement checkboxes, conditional tab visibility, and validation logic
    - *Why it helps*: Ensures the new account creation system works correctly for all feature combinations
    - *Priority*: High
    - *Estimated effort*: Small

11. **Complete Task Management Migration** - Implement actual task management functionality
    - *What it means*: Replace "Feature in Migration" placeholder with actual task management interface
    - *Why it helps*: Makes task management feature actually usable
    - *Priority*: High
    - *Estimated effort*: Medium

12. **Complete Message Editing Migration** - Implement actual message editing functionality
    - *What it means*: Replace "Feature in Migration" placeholder with actual message editing interface
    - *Why it helps*: Makes message editing feature actually usable
    - *Priority*: High
    - *Estimated effort*: Medium

13. **Enforce Required Fields Validation** - Fix backend validation for account creation
    - *What it means*: Add strict validation in save_user_data() to require internal_username, channel type, and other essential fields
    - *Why it helps*: Ensures data integrity and prevents creation of incomplete/invalid user accounts
    - *Priority*: High
    - *Estimated effort*: Small

### Medium Priority Items
These improvements will enhance reliability and user experience:

1. **Expand Testing Framework** - Add tests for untested modules
   - *What it means*: Currently only 5 out of 31+ modules have tests (15% coverage)
   - *Why it helps*: Ensures reliability and makes changes safer
   - *Priority*: Medium
   - *Estimated effort*: Large

2. **Fix Dialog Integration** - Ensure dialogs properly communicate with main window
   - *What it means*: Make sure dialogs update the main window when data changes
   - *Why it helps*: Better user experience with immediate visual feedback
   - *Priority*: Medium
   - *Estimated effort*: Medium

3. **Add Data Validation** - Validate user input in all forms
   - *What it means*: Check that user input is valid before saving
   - *Why it helps*: Prevents data corruption and provides better error messages
   - *Priority*: Medium
   - *Estimated effort*: Medium

4. **Improve Error Handling** - Add proper error handling to all dialogs
   - *What it means*: Make sure dialogs handle errors gracefully and show helpful messages
   - *Why it helps*: Better user experience when things go wrong
   - *Priority*: Medium
   - *Estimated effort*: Medium

5. **Performance Optimization** - Monitor and optimize UI responsiveness
    - *What it means*: Identify and fix slow operations in the UI
    - *Why it helps*: Better user experience with faster response times
    - *Priority*: Medium
    - *Estimated effort*: Medium

6. **Document Temporary User ID Pattern** - ✅ **COMPLETED**
    - *What it means*: Add documentation for the temporary user ID pattern used in personalization dialogs
    - *Why it helps*: Ensures maintainability and clarity for future development
    - *Status*: ✅ **COMPLETED** - Pattern documented and implemented in user profile dialog

### Low Priority Items
These improvements will add polish and advanced features:

1. **Add Performance Monitoring** - Track how long operations take
    - *What it means*: The app keeps track of which operations are slow so you can improve them
    - *Why it helps*: Helps you identify and fix performance problems before they become annoying
    - *Priority*: Low
    - *Estimated effort*: Medium

2. **Create Development Guidelines** - Establish coding standards and best practices
    - *What it means*: Write down rules for how code should be written to keep it consistent
    - *Why it helps*: Makes the code easier to read and understand, especially when working with AI assistance
    - *Priority*: Low
    - *Estimated effort*: Small

3. **Improve AI Terminal Interaction Reliability** - Address issues with AI misunderstanding terminal output
    - *What it means*: Investigate why AI assistants often misinterpret PowerShell output or make incorrect assumptions
    - *Why it helps*: Reduces confusion and improves the reliability of AI-assisted development
    - *Priority*: Low
    - *Estimated effort*: Medium

4. **Fix Treeview Refresh** - Should refresh reflecting the changes, while maintaining current sorting
    - *What it means*: Improve the message editing interface to automatically update the display when messages are changed
    - *Why it helps*: Better user experience with immediate visual feedback
    - *Priority*: Low
    - *Estimated effort*: Small

5. **Advanced Task Management and Progress Tracking**
    - *What it means*: Implement comprehensive task management with advanced features
    - *Why it helps*: Better executive functioning support
    - *Priority*: Low
    - *Estimated effort*: Large

6. **Advanced Scheduling**
    - *What it means*: Implement more sophisticated scheduling capabilities
    - *Why it helps*: More flexible and powerful scheduling options
    - *Priority*: Low
    - *Estimated effort*: Medium

7. **Integration with Additional Services**
    - *What it means*: Add support for more communication channels and external services
    - *Why it helps*: More ways to interact with the system
    - *Priority*: Low
    - *Estimated effort*: Large

## 🖥️ PySide6 UI Migration & Widget Refactoring

### Current Status: ⚠️ **PARTIALLY COMPLETE** - Foundation solid, but many dialogs broken
- **UI Migration Foundation**: ✅ **COMPLETED** - Main PySide6/Qt app launches successfully with QSS applied
- **File Organization**: ✅ **COMPLETED** - Modular structure implemented with clear separation of concerns
- **Widget Creation**: ✅ **COMPLETED** - All widgets created and integrated
- **User Index & Data Cleanup**: ✅ **COMPLETED** - User index redesigned and synchronized, survey responses removed
- **Signal-Based Updates**: ⚠️ **PARTIALLY COMPLETE** - Implemented but not fully tested
- **Testing Framework**: ⚠️ **LIMITED** - Only 5 core modules have tests (15% of codebase)
- **Dialog Functionality**: ❌ **MOSTLY BROKEN** - Many dialogs missing UI files or have integration issues
- **Next Focus**: Fix missing UI files and widget integration issues

### Critical Issues Found ⚠️
- **Missing UI Files**: Several dialogs are trying to load UI files that don't exist (e.g., `user_profile_dialog.ui`)
- **Widget Integration Errors**: Widgets showing "No user_id provided!" errors
- **Dialog Testing**: Most dialogs haven't been actually tested for functionality
- **Feature Placeholders**: Task management and message editing show "Feature in Migration" messages

### Completed Widget Refactoring ✅
**Goal**: Create reusable widgets for features used in multiple places

- **Task Management Widget**: ✅ **COMPLETED** - Reusable widget for task management features
  - *What it means*: Extract task management UI into a standalone widget that can be used in both account creation dialog and standalone task management dialog
  - *Why it helps*: Eliminates code duplication, ensures consistent behavior, makes maintenance easier
  - *Status*: ✅ Complete with signal-based updates

- **Check-in Settings Widget**: ✅ **COMPLETED** - Reusable widget for check-in configuration
  - *What it means*: Extract check-in settings UI into a standalone widget for use in account creation and standalone check-in management
  - *Why it helps*: Single source of truth for check-in logic, consistent UI across all contexts
  - *Status*: ✅ Complete (frequency logic removed, now every time period prompts a check-in)

- **Personalization Widget**: ✅ **COMPLETED** - Reusable widget for personalization settings
  - *What it means*: Extract personalization UI into a standalone widget for use in account creation and standalone personalization dialog
  - *Why it helps*: Consistent personalization experience, easier to maintain and extend
  - *Status*: ✅ Complete with signal-based updates

### Signal-Based Architecture ⚠️ **PARTIALLY COMPLETE**
- **Real-time Updates**: UI automatically refreshes when user data changes
- **Decoupled Components**: Dialogs don't need to know about main window internals
- **Scalable Design**: Easy to add new dialogs that trigger updates
- **Consistent Behavior**: All user-editing dialogs follow the same update pattern
- **Maintainable Code**: Clear separation of concerns between data changes and UI updates
- **Testing Needed**: Verify signal connections work properly

## 📚 Documentation Cleanup & Maintenance

### Human-Facing Documentation Improvements
1. **Update README.md** - ✅ **COMPLETED**
   - *What it means*: Fixed outdated module count references and improved clarity
   - *Why it helps*: Provides accurate project information for new developers
   - *Status*: ✅ **COMPLETED** - Updated module count from 22 to 31+ modules

2. **Update HOW_TO_RUN.md** - ✅ **COMPLETED**
   - *What it means*: Removed references to non-existent directories and improved clarity
   - *Why it helps*: Prevents confusion and provides accurate setup instructions
   - *Status*: ✅ **COMPLETED** - Removed scripts/launchers reference, improved alternative launch methods

3. **Update DEVELOPMENT_WORKFLOW.md** - ✅ **COMPLETED**
   - *What it means*: Updated testing checklist to reflect current features and capabilities
   - *Why it helps*: Ensures testing covers actual current functionality
   - *Status*: ✅ **COMPLETED** - Updated testing checklist with feature-based account creation and personalization

4. **Fix TODO.md Numbering** - ✅ **COMPLETED**
   - *What it means*: Fixed inconsistent numbering in priority sections
   - *Why it helps*: Makes the document easier to read and reference
   - *Status*: ✅ **COMPLETED** - All sections now have consistent numbering

5. **Review and Update ARCHITECTURE.md** - Check for outdated information
   - *What it means*: Ensure architecture documentation reflects current system state
   - *Why it helps*: Provides accurate technical reference for development
   - *Priority*: Medium
   - *Estimated effort*: Small

6. **Review and Update QUICK_REFERENCE.md** - Check for outdated commands
   - *What it means*: Ensure quick reference contains current commands and procedures
   - *Why it helps*: Provides reliable quick access to common tasks
   - *Priority*: Medium
   - *Estimated effort*: Small

## 🔧 System Reliability & Maintenance

### Logging & Debugging
- **Improve app.log to prevent "giant file of doom"**
  - *What it means*: Implement log rotation, size limits, and better organization to prevent one massive log file
  - *Why it helps*: Easier debugging, better performance, and prevents disk space issues
  - *Priority*: Low
  - *Estimated effort*: Medium
- **Fix "process already stopped" notification issue**
  - *What it means*: Investigate why shutdown attempts result in "process already stopped" messages
  - *Why it helps*: Cleaner service management and better user experience
  - *Priority*: Low
  - *Estimated effort*: Small

## 🚀 Planned Feature Improvements

### Data Organization & File Structure
- **Reorganize message file structure for better organization**
  - *What it means*: Move from current `data/messages/{category}/{user_id}.json` to `data/messages/{user_id}/{messages}/{category}.json` and also move `sent_messages.json` into the same messages folder for each user
  - *Why it helps*: More intuitive file structure where all user data is organized by user first, then by type, making it easier to manage and understand
  - *Priority*: Low
  - *Estimated effort*: Medium

### User Experience & Interface
- **Refactor user preference handling through `UserPreferences`**
  - *What it means*: Create a proper class-based system for managing user preferences
  - *Why it helps*: Better organization and easier to maintain user settings
  - *Priority*: Low
  - *Estimated effort*: Medium

- **Expand Discord check-ins with more interactive prompts**
  - *What it means*: Add more engaging and varied check-in questions
  - *Why it helps*: Better engagement and more useful data collection
  - *Priority*: Low
  - *Estimated effort*: Small

- **Build a more interactive Discord bot with quick reactions or forms**
  - *What it means*: Add buttons, dropdowns, and interactive elements to Discord messages
  - *Why it helps*: More engaging user experience and easier interaction
  - *Priority*: Low
  - *Estimated effort*: Medium

### AI & Intelligence
- **Explore deeper AI integration**
  - *What it means*: Find more ways to use AI to personalize the experience
  - *Why it helps*: More personalized and helpful responses
  - *Priority*: Low
  - *Estimated effort*: Large

- **Use the AI backend to deliver motivational messages or coping strategies**
  - *What it means*: Generate personalized motivational content based on user context
  - *Why it helps*: More relevant and helpful messages
  - *Priority*: Low
  - *Estimated effort*: Medium

### Task & Progress Management
- **Develop comprehensive task management system with communication channel integration**
  - *What it means*: Add task management with scheduled reminders, recurring tasks, priority escalation, and full communication channel support
  - *Why it helps*: Help with executive functioning and staying on track through familiar communication channels
  - *Priority*: Medium
  - *Estimated effort*: Large

## Task Management System Implementation

### Phase 1: Foundation ✅ **COMPLETED**
- [x] **Core Task Management**: Implement comprehensive task CRUD operations
- [x] **Task Data Structure**: Create organized task storage with modular file structure
- [x] **Scheduler Integration**: Add task reminder scheduling to core scheduler
- [x] **Communication Integration**: Add task reminder handling to communication manager
- [x] **User Preferences**: Add task management preferences to user settings
- [x] **Error Handling**: Implement comprehensive error handling
- [x] **Admin UI Integration**: Add task management to account creation and management
- [x] **File Operations**: Update file operations to support task file structure
- [x] **Smart Task Reminder Scheduling**: Implement intelligent task reminder scheduling that picks one random task per reminder period and schedules it at a random time within the period

### Phase 2: Advanced Features (PLANNED)
- [x] **Schedule Time Periods**: Allow users to set specific time periods for task reminders ✅ **COMPLETED**
- [ ] **Individual Task Reminders**: Custom reminder times for individual tasks
- [ ] **Recurring Tasks**: Support for daily, weekly, monthly, and custom recurring patterns
- [ ] **Priority Escalation**: Automatic priority increase for overdue tasks
- [ ] **AI Chatbot Integration**: Full integration with AI chatbot for task management

### Phase 3: Communication Channel Integration (PLANNED)
- [ ] **Discord Integration**: Full Discord bot integration for task management
- [ ] **Email Integration**: Email-based task management
- [ ] **Telegram Integration**: Telegram bot integration for task management
- [ ] **Cross-Channel Sync**: Synchronize tasks across all communication channels

### Phase 4: AI Enhancement (PLANNED)
- [ ] **Smart Task Suggestions**: AI-powered task suggestions based on user patterns
- [ ] **Natural Language Processing**: Create and manage tasks using natural language
- [ ] **Intelligent Reminders**: AI-determined optimal reminder timing
- [ ] **Task Analytics**: AI-powered insights into task completion patterns

### Analytics & Insights
- **Add charts showing trends in mood and tasks using Matplotlib or Plotly**
  - *What it means*: Visual representations of your mood and task completion over time
  - *Why it helps*: Better understanding of patterns and progress
  - *Priority*: Low
  - *Estimated effort*: Medium

- **Provide detailed wellness analytics**
  - *What it means*: Advanced analysis of your mental health patterns
  - *Why it helps*: Deeper insights into your wellbeing
  - *Priority*: Low
  - *Estimated effort*: Large

### Code Quality & Architecture
- **Break large modules into smaller files** ✅ **COMPLETED**
  - *What it means*: Split big files into smaller, more focused modules
  - *Why it helps*: Easier to understand and maintain the code
  - *Status*: ✅ Complete - utils.py refactored into 7 focused modules

- **Introduce consistent snake_case naming**
  - *What it means*: Make all variable and function names follow the same pattern
  - *Why it helps*: More professional and consistent code
  - *Priority*: Low
  - *Estimated effort*: Large

- **Centralize configuration in a single module** ✅ **COMPLETED**
  - *What it means*: Put all settings in one place for easier management
  - *Why it helps*: Easier to find and change settings
  - *Status*: ✅ Complete - Configuration centralized in core/config.py

- **Add unit tests for utilities and basic integration tests** ⚠️ **PARTIALLY COMPLETE**
  - *What it means*: Write tests to make sure individual parts work correctly
  - *Why it helps*: Catch problems early and make changes safer
  - *Status*: ⚠️ **LIMITED** - Only 5 out of 31+ modules have tests (15% coverage)

- **Standardize logging levels and improve dependency error messages**
  - *What it means*: Make error messages clearer and more helpful
  - *Why it helps*: Easier to debug problems when they occur
  - *Priority*: Low
  - *Estimated effort*: Small

## 🚀 Potential Future Improvements

### Performance Optimization
- Database query optimization
- Caching improvements
- Async operation enhancements

### Feature Enhancements
- Advanced analytics dashboard
- Machine learning insights
- Enhanced personalization

### Testing & Quality Assurance ⚠️ **LIMITED BUT QUALITY**
- Unit test coverage expansion ⚠️ **LIMITED** - Only 5 core modules tested
- Integration testing ⚠️ **LIMITED** - Only cross-module testing for tested modules
- Performance benchmarking ✅ **COMPLETE** - Load and stress testing included

### Documentation & User Experience
- User guide improvements
- API documentation
- UI/UX enhancements

## 📝 How to Add New TODOs

When adding new tasks, follow this format:

```markdown
### Task Title
- *What it means*: Simple explanation of the task
- *Why it helps*: Clear benefit or improvement
- *Priority*: High/Medium/Low
- *Estimated effort*: Small/Medium/Large
```

Keep entries **concise** and **actionable**. Focus on **what needs to be done** and **why it matters**.

## 🎯 Success Tips

1. **Start with high priority items** - tackle the most impactful improvements first
2. **Break large tasks into smaller steps** - make progress manageable
3. **Test after each change** - ensure nothing breaks
4. **Update this file** - mark completed items and add new priorities
5. **Ask for help** - don't get stuck on any single task

Remember: This is your personal mental health assistant. Every improvement makes it better for you!

- Note: The double service process issue when using the play/debug button in VS Code/Cursor is due to IDE/debugger quirks, not project code. Running from the terminal with venv activated is recommended.

## 🧹 UI Migration Cleanup & Consolidation

### Completed Cleanup Tasks ✅
- **User Data Migration**: All user data access is now handled through the unified `get_user_data()` handler; legacy functions are fully removed and robustly tested
- **Real Task Statistics**: Replaced placeholder statistics in task management with real data fetching from the task management system
- **Implemented Missing Features**: Replaced "Not Implemented" placeholders in PySide6 UI with proper implementations:
  - Check-in management now opens the full check-in management interface (frequency logic removed, now every time period prompts a check-in)
  - Task CRUD operations now opens the comprehensive task management interface  
  - Message editor now opens the full message editing interface
- **User Context Integration**: Updated task management dialog to properly pass user_id for real data access
- **Widget/Dialog Naming Standardization**: All widgets and dialogs now use consistent, clear names (July 2025)
- [x] **Period Widget Refactoring**: Modular, reusable period widget management implemented across dialogs (July 2025)
- [x] **Schedule Data Migration & Restoration**: Schedule data successfully migrated to new nested format; custom periods restored after migration (July 2025)
- [x] **Comprehensive Dialog/Widget Testing**: All dialogs and widgets tested for visual and functional correctness
- [x] **Document Migration/Backup Procedures**: Added documentation for migration/backup best practices
- [x] **Fix schedule saving callback signature mismatch** - Updated callback to match new argument order after refactor
- [x] **Created core/ui_management.py**: UI-specific period logic moved to new module for maintainability (July 2025)
- [x] **User Profile Dialog Complete Implementation** - All personalization fields now fully functional with proper save/load/prepopulation (July 2025)

### Remaining Cleanup Tasks (High Priority)

#### Critical UI Issues
- **Missing UI Files**: Create missing UI files (user profile dialog now fixed)
- **Widget Integration**: Fix "No user_id provided!" errors in widgets
- **Dialog Testing**: Actually test each dialog to see what works and what doesn't
- **Error Handling**: Fix various error messages appearing in logs

#### Code Consolidation
- **Account Creator Pattern**: Refactor `account_creator_qt.py` to use the generated UI class pattern instead of QUiLoader for consistency
- **Redundant Methods**: Review and consolidate duplicate logic between Tkinter and PySide6 versions
- **Temporary User ID Pattern**: Document the temporary user ID pattern used in personalization dialogs as a best practice
- **Account Creation Feature Enablement**: Update account creation dialog to read/write feature enablement from account.json instead of preferences (task_management and checkins features)

#### File Organization
- **Generated UI Files**: Consider organizing generated `*_pyqt.py` files in a separate subdirectory
- **Widget Reusability**: Extract common widget patterns into reusable base classes
- **Documentation**: Create UI development guidelines documenting the established patterns

#### Testing & Validation ⚠️ **LIMITED**
- **Cross-Platform Testing**: Test all dialogs and widgets on different platforms
- **Error Handling**: Audit all error handling to ensure consistent patterns
- **Performance**: Monitor UI responsiveness and optimize slow operations
- **Comprehensive Dialog Testing**: Test all dialogs for visual and functional correctness (July 2025)

### Best Practices Established
- **Generated UI Pattern**: Use `pyside6-uic` to generate UI classes, then subclass for logic
- **Widget Embedding**: Add widgets to dialogs via code, not QUiLoader at runtime
- **QSS Scoping**: Never use global QWidget rules that can break indicator rendering
- **Signal Connections**: Connect signals in subclass, not generated code
- **Layout Management**: Always ensure every widget in Designer has a layout
- **Testing**: Run `python run_mhm.py` after every change
- **Documentation**: Update CHANGELOG.md and TODO.md after significant changes

### Sent Messages Migration & Cleanup ✅ **PARTIALLY COMPLETE**
- ✅ **Global Directory Cleanup**: Removed all references to obsolete global `data/sent_messages` directory
  - Removed `SENT_MESSAGES_DIR_PATH` from core path validation and configuration
  - Eliminated unnecessary startup warnings and directory creation
- **Remaining Tasks** (Planned for future):
  - Move users' `sent_messages.json`s into their messages folder
  - Update the code and current data files to match
  - Update or remove any code that references the global sent_messages directory, ensuring all sent message operations use per-user directories/files
  - Correct the default message library population for users (new and existing)
  - Review and update user file validation

### Legacy Code Cleanup (Low Priority)
- **Legacy messaging_service field**: Remove fallback references to `preferences['messaging_service']` once all code uses `preferences['channel']['type']`
- **Legacy compatibility code**: Review and remove any remaining legacy compatibility functions and fallbacks
- **Documentation cleanup**: Remove references to obsolete configuration options and file structures

### Legacy messaging_service Field Cleanup (Low Priority)
Found in multiple files - these are fallback references that should be cleaned up:
- `ui/ui_app_qt.py` (line 1243)
- `ui/account_manager.py` (lines 1170, 1294)
- `core/response_tracking.py` (line 169)
- `bot/user_context_manager.py` (lines 97, 196)
- `bot/telegram_bot.py` (line 671)
- `bot/communication_manager.py` (lines 530, 814)

### July 2025 - Dialog & Widget Data Structure Fixes & Testing Framework ✅ **COMPLETED**
- *What it means*: Systematically test all check-in and task management dialog features (add/remove/undo/save/enable/disable/persistence/edge cases)
- *Why it helps*: Ensures all features work as intended and are consistent between dialogs
- *Status*: ✅ **COMPLETED** - All dialog features tested and working correctly
- *Accomplishments*:
  - Fixed KeyError in remove_period_row by standardizing on canonical `start_time`/`end_time` keys
  - Fixed undo functionality and period naming issues
  - Fixed schedule saving to properly persist changes to files
  - Updated default times to match system defaults
  - Removed all debug code for clean codebase
  - All add/remove/undo/save/enable/disable/persistence features now working
- *Reference*: See UI_MIGRATION_PLAN.md for details