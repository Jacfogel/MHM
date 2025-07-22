# TODO - Development Priorities

> **Audience**: Human Developer (Beginner Programmer)  
> **Purpose**: Current development priorities and planned improvements  
> **Style**: Organized, actionable, beginner-friendly

> **See [README.md](README.md) for complete navigation and project overview**
> **See [DEVELOPMENT_WORKFLOW.md](DEVELOPMENT_WORKFLOW.md) for safe development practices**
> **See [TESTING_IMPROVEMENT_PLAN.md](TESTING_IMPROVEMENT_PLAN.md) for testing strategy**

## 🎯 Current Priority Tasks

### ✅ Recently Completed (2025-07-21)

#### Unified API Refactoring and Test Fixes ✅ **COMPLETED**
- **Fixed Pylance errors** in `core/user_data_handlers.py` by updating `save_user_data` to use unified API directly
- **Fixed caching issues** by adding cache clearing after data saves to ensure legacy loaders return fresh data
- **Fixed file path inconsistencies** by updating file mapping to use `'context'` instead of `'user_context'`
- **Fixed return value expectations** by updating `save_json_data` to return `True` on success
- **Updated test expectations** to match new API and file names
- **All tests now passing**: 244 passed, 1 skipped (was 25 failed before fixes)
- **Scripts directory cleanup**: Organized scripts into logical categories (migration, testing, debug, utilities, refactoring)
- **Removed redundant scripts**: Eliminated duplicates of ai_tools functionality and one-time fixes

### High Priority

#### Documentation Cleanup
1. **Module Dependencies Documentation** - Document all module dependencies
   - *What it means*: Document module dependencies across the codebase
   - *Why it helps*: Critical for understanding system architecture and maintenance
   - *Status*: ✅ **COMPLETED** - 100% coverage achieved (85/85 files documented)
   - *Priority*: High - Critical for understanding system architecture
   - *Note*: All modules now documented with enhanced preservation system working correctly

2. **Directory Organization Improvements** - Reorganize directories for better clarity
   - *What it means*: Move `custom_data/` to `tests/` or rename to something more intuitive, move `test_logs/` to `tests/`, move `default_messages/` to `resources/`
   - *Why it helps*: Better organization and clearer purpose for each directory
   - *Priority*: Medium - Documentation and organization
   - *Impact*: Cleaner project structure and easier navigation

3. **Documentation Cleanup - Outdated References** - Fix references to non-existent files and outdated patterns
   - *What it means*: Remove references to `AGENTS.md`, `ui_app.py`, `account_manager.py`, `account_creator.py`, `data/sent_messages`, `data/messages`, `messaging_service`, `editschedule`, `createaccount`, `core/utils.py`, and non-existent Cursor rules
   - *Why it helps*: Eliminates confusion and ensures documentation accuracy
   - *Priority*: Medium - Documentation quality
   - *Impact*: Accurate documentation and reduced confusion

#### Testing & Validation
4. **Comprehensive Dialog Testing** - Test remaining dialogs for functionality and data persistence
   - *What it means*: Systematically test each dialog to verify it works correctly
   - *Why it helps*: Ensures all UI functionality works as expected and data is properly saved
   - *Priority*: High
   - *Estimated effort*: Medium
   - *Remaining*:
     - ✅ **Category Management Dialog** - Complete with validation fixes and category persistence
     - ✅ **Channel Management Dialog** - Complete, all functionality working
     - ✅ **Check-in Management Dialog** - Complete with comprehensive validation system
     - ⚠️ **Task Management Dialog** - Ready for testing
     - ⚠️ **Schedule Editor Dialog** - Ready for testing
     - ⚠️ **User Profile Dialog** - Ready for testing
     - ⚠️ **Account Creator Dialog** - Ready for testing

5. **Widget Testing** - Test remaining widgets for proper data binding
   - *What it means*: Test all widgets to ensure they properly save and load data
   - *Why it helps*: Ensures widgets work correctly in all contexts (account creation, standalone dialogs)
   - *Priority*: High
   - *Estimated effort*: Medium
   - *Remaining*:
     - ⚠️ **Channel Selection Widget** - Needs testing for timezone and contact info handling
     - ⚠️ **Category Selection Widget** - Needs testing for category selection and persistence
     - ⚠️ **Task Settings Widget** - Needs testing for task enablement and settings
     - ⚠️ **Check-in Settings Widget** - Needs testing for check-in enablement and settings

6. **Validation Testing** - Test validation logic across all dialogs
   - *What it means*: Test that validation works correctly for all input fields
   - *Why it helps*: Ensures users get proper feedback for invalid input
   - *Priority*: High
   - *Estimated effort*: Small
   - *Status*: ✅ **COMPLETED** - Comprehensive validation system implemented across all dialogs
   - *Remaining*:
     - ✅ **Required Field Validation** - Implemented with clear error messages
     - ✅ **Feature Enablement Validation** - Implemented with proper warnings

#### Code Quality
7. **Legacy Wrapper Removal**
   - *What it means*: Delete thin wrappers in `core/user_management.py` once no runtime code triggers them
   - *Why it helps*: Removes dead code and avoids accidental usage
   - *Priority*: High
   - *Estimated effort*: Small
   - *Status*: Pending – monitor `app.log` for any remaining "LEGACY …" warnings before removal
   - *Note*: Cache clearing has been implemented, so legacy wrappers should be safe to remove once no warnings appear

8. **Dynamic Check-in Question System** - Implement full custom question functionality
   - *What it means*: Replace the current placeholder "Add New Element" with a proper dynamic system similar to the profile settings widget
   - *Why it helps*: Allows users to create custom check-in questions beyond the predefined set
   - *Priority*: High
   - *Estimated effort*: Medium
   - *Current status*: Basic input dialog implemented, needs full dynamic list container system
   - *Implementation needed*: 
     - Create `CheckinQuestionField` widget similar to `DynamicListField`
     - Create `CheckinQuestionContainer` widget similar to `DynamicListContainer`
     - Add question type selection (text, yes/no, 1-5 scale, number)
     - Integrate with existing question management system
     - Update data persistence to handle custom questions

9. **Discord Validation Enhancement** - Add format validation for Discord usernames
   - *What it means*: Implement validation rules for Discord username format in Channel Management Dialog
   - *Why it helps*: Prevents users from entering invalid Discord usernames and provides better feedback
   - *Priority*: Medium
   - *Estimated effort*: Small
   - *Current status*: No validation rules configured, basic functionality working
   - *Implementation needed*:
     - Define Discord username format rules (no spaces, valid characters, length limits)
     - Add validation to Channel Management Dialog

### Medium Priority

10. **Log Rotation & Size Limits**
   - *What it means*: Implement rotating file handler or size checks for `app.log`
   - *Why it helps*: Prevent the "giant file of doom" and conserve disk space
   - *Priority*: Medium
   - *Estimated effort*: Small

11. **Expand Testing Framework** - Add tests for untested modules
   - *What it means*: Currently only 9 out of 31+ modules have tests (29% coverage)
   - *Why it helps*: Ensures reliability and makes changes safer
   - *Priority*: Medium
   - *Estimated effort*: Large

12. **Review and Update ARCHITECTURE.md** - Check for outdated information
   - *What it means*: Ensure architecture documentation reflects current system state
   - *Why it helps*: Provides accurate technical reference for development
   - *Priority*: Medium
   - *Estimated effort*: Small

13. **Review and Update QUICK_REFERENCE.md** - Check for outdated commands
   - *What it means*: Ensure quick reference contains current commands and procedures
   - *Why it helps*: Provides reliable quick access to common tasks
   - *Priority*: Medium
   - *Estimated effort*: Small

14. **Fix Dialog Integration** - Ensure dialogs properly communicate with main window
    - *What it means*: Make sure dialogs update the main window when data changes
    - *Why it helps*: Better user experience with immediate visual feedback
    - *Priority*: Medium
    - *Estimated effort*: Medium

15. **Add Data Validation** - Validate user input in all forms
    - *What it means*: Check that user input is valid before saving
    - *Why it helps*: Prevents data corruption and provides better error messages
    - *Priority*: Medium
    - *Estimated effort*: Medium

16. **Improve Error Handling** - Add proper error handling to all dialogs
    - *What it means*: Make sure dialogs handle errors gracefully and show helpful messages
    - *Why it helps*: Better user experience when things go wrong
    - *Priority*: Medium
    - *Estimated effort*: Medium

17. **Performance Optimization** - Monitor and optimize UI responsiveness
    - *What it means*: Identify and fix slow operations in the UI
    - *Why it helps*: Better user experience with faster response times
    - *Priority*: Medium
    - *Estimated effort*: Medium

### Low Priority

16. **Scripts Directory Cleanup** - Clean up the scripts/ directory
    - *What it means*: Remove outdated/broken files, organize remaining utilities, move AI tools to ai_tools/
    - *Why it helps*: Reduces confusion and keeps the codebase organized
    - *Priority*: Low
    - *Estimated effort*: Medium

17. **Improve AI Terminal Interaction Reliability** - Address issues with AI misunderstanding terminal output
    - *What it means*: Investigate why AI assistants often misinterpret PowerShell output or make incorrect assumptions
    - *Why it helps*: Reduces confusion and improves the reliability of AI-assisted development
    - *Priority*: Low
    - *Estimated effort*: Medium

18. **Fix Treeview Refresh** - Should refresh reflecting the changes, while maintaining current sorting
    - *What it means*: Improve the message editing interface to automatically update the display when messages are changed
    - *Why it helps*: Better user experience with immediate visual feedback
    - *Priority*: Low
    - *Estimated effort*: Small

19. **Advanced Task Management and Progress Tracking**
    - *What it means*: Implement comprehensive task management with advanced features
    - *Why it helps*: Better executive functioning support
    - *Priority*: Low
    - *Estimated effort*: Large

20. **Advanced Scheduling**
    - *What it means*: Implement more sophisticated scheduling capabilities
    - *Why it helps*: More flexible and powerful scheduling options
    - *Priority*: Low
    - *Estimated effort*: Medium

21. **Integration with Additional Services**
    - *What it means*: Add support for more communication channels and external services
    - *Why it helps*: More ways to interact with the system
    - *Priority*: Low
    - *Estimated effort*: Large

22. **Reorganize message file structure for better organization**
    - *What it means*: Move from current `data/messages/{category}/{user_id}.json` to `data/messages/{user_id}/{messages}/{category}.json` and also move `sent_messages.json` into the same messages folder for each user
    - *Why it helps*: More intuitive file structure where all user data is organized by user first, then by type, making it easier to manage and understand
    - *Priority*: Low
    - *Estimated effort*: Medium

23. **Refactor user preference handling through `UserPreferences`**
    - *What it means*: Create a proper class-based system for managing user preferences
    - *Why it helps*: Better organization and easier to maintain user settings
    - *Priority*: Low
    - *Estimated effort*: Medium

24. **Expand Discord check-ins with more interactive prompts**
    - *What it means*: Add more engaging and varied check-in questions
    - *Why it helps*: Better engagement and more useful data collection
    - *Priority*: Low
    - *Estimated effort*: Small

25. **Build a more interactive Discord bot with quick reactions or forms**
    - *What it means*: Add buttons, dropdowns, and interactive elements to Discord messages
    - *Why it helps*: More engaging user experience and easier interaction
    - *Priority*: Low
    - *Estimated effort*: Medium

26. **Explore deeper AI integration**
    - *What it means*: Find more ways to use AI to personalize the experience
    - *Why it helps*: More personalized and helpful responses
    - *Priority*: Low
    - *Estimated effort*: Large

27. **Use the AI backend to deliver motivational messages or coping strategies**
    - *What it means*: Generate personalized motivational content based on user context
    - *Why it helps*: More relevant and helpful messages
    - *Priority*: Low
    - *Estimated effort*: Medium

28. **Develop comprehensive task management system with communication channel integration**
    - *What it means*: Add task management with scheduled reminders, recurring tasks, priority escalation, and full communication channel support
    - *Why it helps*: Help with executive functioning and staying on track through familiar communication channels
    - *Priority*: Medium
    - *Estimated effort*: Large

29. **Add charts showing trends in mood and tasks using Matplotlib or Plotly**
    - *What it means*: Visual representations of your mood and task completion over time
    - *Why it helps*: Better understanding of patterns and progress
    - *Priority*: Low
    - *Estimated effort*: Medium

30. **Provide detailed wellness analytics**
    - *What it means*: Advanced analysis of your mental health patterns
    - *Why it helps*: Deeper insights into your wellbeing
    - *Priority*: Low
    - *Estimated effort*: Large

31. **Introduce consistent snake_case naming**
    - *What it means*: Make all variable and function names follow the same pattern
    - *Why it helps*: More professional and consistent code
    - *Priority*: Low
    - *Estimated effort*: Large

32. **Standardize logging levels and improve dependency error messages**
    - *What it means*: Make error messages clearer and more helpful
    - *Why it helps*: Easier to debug problems when they occur
    - *Priority*: Low
    - *Estimated effort*: Small

33. **Improve app.log to prevent "giant file of doom"**
    - *What it means*: Implement log rotation, size limits, and better organization to prevent one massive log file
    - *Why it helps*: Easier debugging, better performance, and prevents disk space issues
    - *Priority*: Low
    - *Estimated effort*: Medium

34. **Fix "process already stopped" notification issue**
    - *What it means*: Investigate why shutdown attempts result in "process already stopped" messages
    - *Why it helps*: Cleaner service management and better user experience
    - *Priority*: Low
    - *Estimated effort*: Small

35. **TODO Numbering System Improvement** - Improve or remove the current numbering system
    - *What it means*: The current numbered system (1, 2, 3...) requires manual renumbering when items are added/removed, which is error-prone and time-consuming
    - *Why it helps*: Eliminates the need for manual renumbering and reduces errors when maintaining the TODO list
    - *Priority*: Low - Documentation organization
    - *Estimated effort*: Small
    - *Options*: Remove numbers entirely, use categories only, or implement automatic numbering

36. **Add Performance Monitoring** - Track how long operations take
    - *What it means*: The app keeps track of which operations are slow so you can improve them
    - *Why it helps*: Helps you identify and fix performance problems before they become annoying
    - *Priority*: Low
    - *Estimated effort*: Medium

37. **Create Development Guidelines** - Establish coding standards and best practices
    - *What it means*: Write down rules for how code should be written to keep it consistent
    - *Why it helps*: Makes the code easier to read and understand, especially when working with AI assistance
    - *Priority*: Low
    - *Estimated effort*: Small

## Task Management System Implementation

### Phase 2: Advanced Features (PLANNED)
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

## 📝 How to Add New TODOs

When adding new tasks, follow this format:

```markdown
### Task Title
- *What it means*: Simple explanation of the task
- *Why it helps*: Clear benefit or improvement
- *Priority*: High/Medium/Low
- *Estimated effort*: Small/Medium/Large
```