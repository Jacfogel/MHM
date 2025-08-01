# TODO - Development Priorities

> **Audience**: Human Developer (Beginner Programmer)  
> **Purpose**: Current development priorities and planned improvements  
> **Style**: Organized, actionable, beginner-friendly

> **See [README.md](README.md) for complete navigation and project overview**
> **See [DEVELOPMENT_WORKFLOW.md](DEVELOPMENT_WORKFLOW.md) for safe development practices**
> **See [TESTING_IMPROVEMENT_PLAN_DETAIL.md](TESTING_IMPROVEMENT_PLAN_DETAIL.md) for testing strategy**

## 📝 How to Add New TODOs

When adding new tasks, follow this format:

```markdown
**Task Title** - Brief description
- *What it means*: Simple explanation of the task
- *Why it helps*: Clear benefit or improvement
- *Estimated effort*: Small/Medium/Large
```

**Guidelines:**
- Use **bold** for task titles
- Group tasks by priority (High/Medium/Low sections)
- Use clear, action-oriented titles
- Include estimated effort to help with planning
- Add status indicators (⚠️ **IN PROGRESS**) when relevant
- Don't include priority field since tasks are already grouped by priority
- **TODO.md is for TODOs only** - completed tasks should be documented in CHANGELOG files and removed from TODO.md

## 🎯 Current Priority Tasks

### High Priority

**UI Layer Testing** - Add comprehensive tests for admin interface and dialogs
- *What it means*: Create tests for `ui/ui_app_qt.py` and individual dialogs to verify UI state management, dialog integration, and user data display/editing
- *Why it helps*: Ensures the admin interface works correctly and provides reliable user experience
- *Estimated effort*: Large
- *Status*: ⚠️ **NEXT PRIORITY** - Conversation Manager module completed, ready to move to UI layer testing



#### Testing & Validation
**Comprehensive Dialog Testing** - Test remaining dialogs for functionality and data persistence
- *What it means*: Systematically test each dialog to verify it works correctly
- *Why it helps*: Ensures all UI functionality works as expected and data is properly saved
- *Estimated effort*: Medium
- *Remaining*:
  - ✅ **Category Management Dialog** - Complete with validation fixes and category persistence
  - ✅ **Channel Management Dialog** - Complete, all functionality working
  - ✅ **Check-in Management Dialog** - Complete with comprehensive validation system
  - ⚠️ **Task Management Dialog** - Complete with full CRUD functionality
  - ⚠️ **Schedule Editor Dialog** - Ready for testing
  - ⚠️ **User Profile Dialog** - Ready for testing
  - ⚠️ **Account Creator Dialog** - Ready for testing

**Widget Testing** - Test remaining widgets for proper data binding
- *What it means*: Test all widgets to ensure they properly save and load data
- *Why it helps*: Ensures widgets work correctly in all contexts (account creation, standalone dialogs)
- *Estimated effort*: Medium
- *Remaining*:
  - ⚠️ **Channel Selection Widget** - Needs testing for timezone and contact info handling
  - ⚠️ **Category Selection Widget** - Needs testing for category selection and persistence
  - ⚠️ **Task Settings Widget** - Complete with full CRUD functionality
  - ⚠️ **Check-in Settings Widget** - Needs testing for check-in enablement and settings

**Schedule Editor Validation Dialog Closure** - Fix validation error popup closing the edit schedule dialog
- *What it means*: When validation errors occur in the Schedule Editor, the error popup should not close the main dialog
- *Why it helps*: Users can fix validation errors and try again without having to reopen the dialog
- *Estimated effort*: Small
- *Status*: ⚠️ **OUTSTANDING** - Previous fix attempt may not have fully resolved the issue

**Task CRUD Functionality Testing** - Test the new individual task CRUD operations
- *What it means*: Test the new task CRUD dialog for creating, editing, completing, and deleting individual tasks
- *Why it helps*: Ensures the new task management UI works correctly and provides full CRUD functionality
- *Estimated effort*: Small
- *Status*: ✅ **COMPLETED** - Task CRUD UI fully functional with all operations working

**Task-Specific Reminder System Implementation** - Implement task-specific reminder scheduling functionality
- *What it means*: Add functionality to schedule and manage reminders for individual tasks based on their reminder periods
- *Why it helps*: Enables users to set custom reminder schedules for specific tasks, improving task management effectiveness
- *Estimated effort*: Medium
- *Status*: ✅ **COMPLETED** - Full task-specific reminder system implemented with scheduling, cleanup, and lifecycle management

## 🎯 **HIGH PRIORITY**

### **Legacy Code Removal** - Remove all legacy/compatibility code with clear marking and plans
- *What it means*: Remove all legacy compatibility code that's no longer needed, following the plan in `LEGACY_CODE_REMOVAL_PLAN.md`
- *Why it helps*: Reduces code complexity, improves maintainability, and eliminates potential bugs from legacy code paths
- *Estimated effort*: Medium
- *Status*: **ACTIVE** - See `LEGACY_CODE_REMOVAL_PLAN.md` for detailed inventory and removal plans
- *High Priority Tasks*:
  - ⚠️ **Account Creator Dialog Compatibility**: Remove unused methods (complete by 2025-08-15)
  - ⚠️ **User Profile Settings Widget Fallbacks**: Remove legacy fallbacks (complete by 2025-08-15)
  - ⚠️ **Discord Bot Legacy Methods**: Remove unused methods (complete by 2025-08-15)
- *Note*: All legacy code must be clearly marked with removal plans before removal



**Dynamic Check-in Question System** - Implement full custom question functionality
- *What it means*: Replace the current placeholder "Add New Element" with a proper dynamic system similar to the profile settings widget
- *Why it helps*: Allows users to create custom check-in questions beyond the predefined set
- *Estimated effort*: Medium

**Message Category Schedule Editing in Account Creation** - Allow users to configure message schedules during account creation
- *What it means*: Add schedule editing functionality to the Messages tab in account creation, similar to how Tasks and Check-ins have their own schedule configuration
- *Why it helps*: Users can set up their complete message delivery schedule during initial account setup instead of having to do it later
- *Estimated effort*: Medium







### Medium Priority



**Expand Testing Framework** - Add tests for untested modules
- *What it means*: Currently only 12 out of 31+ modules have tests (39% coverage)
- *Why it helps*: Ensures reliability and makes changes safer
- *Estimated effort*: Large
- *Status*: ✅ **IN PROGRESS** - Discord bot and AI chatbot modules completed (384 tests passing, 1 skipped, 34 warnings)
- *Next Steps*: Move to User Context Manager module, then UI Layer testing

**Review and Update ARCHITECTURE.md** - Check for outdated information
- *What it means*: Ensure architecture documentation reflects current system state
- *Why it helps*: Provides accurate technical reference for development
- *Estimated effort*: Small

**Review and Update QUICK_REFERENCE.md** - Check for outdated commands
- *What it means*: Ensure quick reference contains current commands and procedures
- *Why it helps*: Provides reliable quick access to common tasks
- *Estimated effort*: Small

**Fix Dialog Integration** - Ensure dialogs properly communicate with main window
- *What it means*: Make sure dialogs update the main window when data changes
- *Why it helps*: Better user experience with immediate visual feedback
- *Estimated effort*: Medium

**Add Data Validation** - Validate user input in all forms
- *What it means*: Check that user input is valid before saving
- *Why it helps*: Prevents data corruption and provides better error messages
- *Estimated effort*: Medium

**Improve Error Handling** - Add proper error handling to all dialogs
- *What it means*: Make sure dialogs handle errors gracefully and show helpful messages
- *Why it helps*: Better user experience when things go wrong
- *Estimated effort*: Medium

**Performance Optimization** - Monitor and optimize UI responsiveness
- *What it means*: Identify and fix slow operations in the UI
- *Why it helps*: Better user experience with faster response times
- *Estimated effort*: Medium

**Develop comprehensive task management system with communication channel integration**
- *What it means*: Add task management with scheduled reminders, recurring tasks, priority escalation, and full communication channel support
- *Why it helps*: Help with executive functioning and staying on track through familiar communication channels
- *Estimated effort*: Large

**Discord Validation Enhancement** - Add format validation for Discord usernames
- *What it means*: Implement validation rules for Discord username format in Channel Management Dialog
- *Why it helps*: Prevents users from entering invalid Discord usernames and provides better feedback
- *Estimated effort*: Small
- *Current status*: No validation rules configured, basic functionality working
- *Implementation needed*:
  - Define Discord username format rules (no spaces, valid characters, length limits)
  - Add validation to Channel Management Dialog

**Discord Connectivity Monitoring** - Add monitoring for Discord connection health
- *What it means*: Implement periodic health checks and monitoring for Discord bot connectivity
- *Why it helps*: Proactively detect and report connectivity issues before they affect users
- *Estimated effort*: Small
- *Status*: Basic connectivity checks implemented, monitoring system needed

### Low Priority

**Scripts Directory Cleanup** - Clean up the scripts/ directory
- *What it means*: Remove outdated/broken files, organize remaining utilities, move AI tools to ai_tools/
- *Why it helps*: Reduces confusion and keeps the codebase organized
- *Estimated effort*: Medium

**Gitignore Cleanup** - Review and clean up .gitignore file
- *What it means*: Remove outdated entries, add missing patterns, organize sections logically
- *Why it helps*: Ensures proper version control and prevents unnecessary files from being tracked
- *Estimated effort*: Small

**Improve AI Terminal Interaction Reliability** - Address issues with AI misunderstanding terminal output
- *What it means*: Investigate why AI assistants often misinterpret PowerShell output or make incorrect assumptions
- *Why it helps*: Reduces confusion and improves the reliability of AI-assisted development
- *Estimated effort*: Medium

**Fix Treeview Refresh** - Should refresh reflecting the changes, while maintaining current sorting
- *What it means*: Improve the message editing interface to automatically update the display when messages are changed
- *Why it helps*: Better user experience with immediate visual feedback
- *Estimated effort*: Small

**Advanced Task Management and Progress Tracking**
- *What it means*: Implement comprehensive task management with advanced features
- *Why it helps*: Better executive functioning support
- *Estimated effort*: Large

**Advanced Scheduling**
- *What it means*: Implement more sophisticated scheduling capabilities
- *Why it helps*: More flexible and powerful scheduling options
- *Estimated effort*: Medium

**Integration with Additional Services**
- *What it means*: Add support for more communication channels and external services
- *Why it helps*: More ways to interact with the system
- *Estimated effort*: Large

**Reorganize message file structure for better organization**
- *What it means*: Move from current `data/messages/{category}/{user_id}.json` to `data/messages/{user_id}/{messages}/{category}.json` and also move `sent_messages.json` into the same messages folder for each user
- *Why it helps*: More intuitive file structure where all user data is organized by user first, then by type, making it easier to manage and understand
- *Estimated effort*: Medium

**Refactor user preference handling through `UserPreferences`**
- *What it means*: Create a proper class-based system for managing user preferences
- *Why it helps*: Better organization and easier to maintain user settings
- *Estimated effort*: Medium

**Expand Discord check-ins with more interactive prompts**
- *What it means*: Add more engaging and varied check-in questions
- *Why it helps*: Better engagement and more useful data collection
- *Estimated effort*: Small

**Build a more interactive Discord bot with quick reactions or forms**
- *What it means*: Add buttons, dropdowns, and interactive elements to Discord messages
- *Why it helps*: More engaging user experience and easier interaction
- *Estimated effort*: Medium

**Explore deeper AI integration**
- *What it means*: Find more ways to use AI to personalize the experience
- *Why it helps*: More personalized and helpful responses
- *Estimated effort*: Large

**Use the AI backend to deliver motivational messages or coping strategies**
- *What it means*: Generate personalized motivational content based on user context
- *Why it helps*: More relevant and helpful messages
- *Estimated effort*: Medium

**Add charts showing trends in mood and tasks using Matplotlib or Plotly**
- *What it means*: Visual representations of your mood and task completion over time
- *Why it helps*: Better understanding of patterns and progress
- *Estimated effort*: Medium

**Provide detailed wellness analytics**
- *What it means*: Advanced analysis of your mental health patterns
- *Why it helps*: Deeper insights into your wellbeing
- *Estimated effort*: Large

**Introduce consistent snake_case naming**
- *What it means*: Make all variable and function names follow the same pattern
- *Why it helps*: More professional and consistent code
- *Estimated effort*: Large

**Standardize logging levels and improve dependency error messages**
- *What it means*: Make error messages clearer and more helpful
- *Why it helps*: Easier to debug problems when they occur
- *Estimated effort*: Small



**Fix "process already stopped" notification issue**
- *What it means*: Investigate why shutdown attempts result in "process already stopped" messages
- *Why it helps*: Cleaner service management and better user experience
- *Estimated effort*: Small

**Add Performance Monitoring** - Track how long operations take
- *What it means*: The app keeps track of which operations are slow so you can improve them
- *Why it helps*: Helps you identify and fix performance problems before they become annoying
- *Estimated effort*: Medium

**Create Development Guidelines** - Establish coding standards and best practices
- *What it means*: Write down rules for how code should be written to keep it consistent
- *Why it helps*: Makes the code easier to read and understand, especially when working with AI assistance
- *Estimated effort*: Small

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
- [ ] **Telegram Integration**: Telegram bot integration for task management
- [ ] **Cross-Channel Sync**: Synchronize tasks across all communication channels

### Phase 4: AI Enhancement (PLANNED)
- [ ] **Smart Task Suggestions**: AI-powered task suggestions based on user patterns
- [ ] **Natural Language Processing**: Create and manage tasks using natural language
- [ ] **Intelligent Reminders**: AI-determined optimal reminder timing
- [ ] **Task Analytics**: AI-powered insights into task completion patterns