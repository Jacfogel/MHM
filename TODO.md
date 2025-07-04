# TODO - Development Priorities

> **Audience**: Human Developer (Beginner Programmer)  
> **Purpose**: Current development priorities and planned improvements  
> **Style**: Organized, actionable, beginner-friendly

## 🎯 Current Priority Tasks

### Immediate Action Items (High Priority)
These improvements will make the code more reliable and easier to work with:

1. **Create testing framework** - Add automated tests for core functions
   - *What it means*: Write small programs that check if your main code works correctly
   - *Why it helps*: You can make changes without worrying about breaking existing features

2. **Implement data migration system** - Handle changes to how data is stored
   - *What it means*: When you change how data is saved, the app automatically updates old data to the new format
   - *Why it helps*: You can improve the app without losing your existing data

3. **Add performance monitoring** - Track how long operations take
   - *What it means*: The app keeps track of which operations are slow so you can improve them
   - *Why it helps*: Helps you identify and fix performance problems before they become annoying

4. **Create development guidelines** - Establish coding standards and best practices
   - *What it means*: Write down rules for how code should be written to keep it consistent
   - *Why it helps*: Makes the code easier to read and understand, especially when working with AI assistance

5. **Improve AI terminal interaction reliability** - Address issues with AI misunderstanding terminal output and making incorrect assumptions
   - *What it means*: Investigate why AI assistants often misinterpret PowerShell output, fail to parse command results correctly, or make assumptions about what happened
   - *Why it helps*: Reduces confusion, prevents incorrect conclusions, and improves the reliability of AI-assisted development
   - *Specific issues to investigate*:
     - PowerShell output parsing problems
     - Assumptions about command success/failure
     - Misinterpretation of error messages
     - Failure to properly handle multi-line output
     - Incorrect conclusions about what commands actually did

7. **Test edge cases for check-in and category schedule management**
   - *What it means*: Verify that first-time check-in enablement and new category addition work correctly
   - *Why it helps*: Ensures the improved schedule management system handles all scenarios properly
   - *Priority*: Medium
   - *Estimated effort*: Small

- [ ] fix treeview refresh - should refresh reflecting the changes, while maintaining current sorting, on message add, edit, delete, and undo delete. should also scroll window to added, edited or undeleted message
- [ ] Advanced task management and progress tracking
- [ ] Advanced scheduling
- [ ] Integration with additional services

## 🔧 System Reliability & Maintenance

### Logging & Debugging
- **Improve app.log to prevent "giant file of doom"**
  - *What it means*: Implement log rotation, size limits, and better organization to prevent one massive log file
  - *Why it helps*: Easier debugging, better performance, and prevents disk space issues
  - *Priority*: High
  - *Estimated effort*: Medium
- **Fix "process already stopped" notification issue**
  - *What it means*: Investigate why shutdown attempts result in "process already stopped" messages
  - *Why it helps*: Cleaner service management and better user experience
  - *Priority*: High
  - *Estimated effort*: Small

## 🚀 Planned Feature Improvements

### Data Organization & File Structure
- **Reorganize message file structure for better organization**
  - *What it means*: Move from current `data/messages/{category}/{user_id}.json` to `data/messages/{user_id}/{messages}/{category}.json` and also move `sent_messages.json` into the same messages folder for each user
  - *Why it helps*: More intuitive file structure where all user data is organized by user first, then by type, making it easier to manage and understand
  - *Priority*: Medium
  - *Estimated effort*: Medium

### User Experience & Interface
- **Refactor user preference handling through `UserPreferences`**
  - *What it means*: Create a proper class-based system for managing user preferences
  - *Why it helps*: Better organization and easier to maintain user settings
  - *Priority*: Medium
  - *Estimated effort*: Medium

- **Expand Discord check-ins with more interactive prompts**
  - *What it means*: Add more engaging and varied check-in questions
  - *Why it helps*: Better engagement and more useful data collection
  - *Priority*: Medium
  - *Estimated effort*: Small

- **Build a more interactive Discord bot with quick reactions or forms**
  - *What it means*: Add buttons, dropdowns, and interactive elements to Discord messages
  - *Why it helps*: More engaging user experience and easier interaction
  - *Priority*: Medium
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
  - *Priority*: Medium
  - *Estimated effort*: Medium

### Task & Progress Management
- **Develop comprehensive task management system with communication channel integration**
  - *What it means*: Add task management with scheduled reminders, recurring tasks, priority escalation, and full communication channel support
  - *Why it helps*: Help with executive functioning and staying on track through familiar communication channels
  - *Priority*: High
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
  - *Priority*: Medium
  - *Estimated effort*: Medium

- **Provide detailed wellness analytics**
  - *What it means*: Advanced analysis of your mental health patterns
  - *Why it helps*: Deeper insights into your wellbeing
  - *Priority*: Low
  - *Estimated effort*: Large

### Code Quality & Architecture
- **Break large modules into smaller files**
  - *What it means*: Split big files into smaller, more focused modules
  - *Why it helps*: Easier to understand and maintain the code
  - *Priority*: Medium
  - *Estimated effort*: Medium

- **Introduce consistent snake_case naming**
  - *What it means*: Make all variable and function names follow the same pattern
  - *Why it helps*: More professional and consistent code
  - *Priority*: Low
  - *Estimated effort*: Large

- **Centralize configuration in a single module**
  - *What it means*: Put all settings in one place for easier management
  - *Why it helps*: Easier to find and change settings
  - *Priority*: Medium
  - *Estimated effort*: Small

- **Add unit tests for utilities and basic integration tests**
  - *What it means*: Write tests to make sure individual parts work correctly
  - *Why it helps*: Catch problems early and make changes safer
  - *Priority*: High
  - *Estimated effort*: Medium

- **Standardize logging levels and improve dependency error messages**
  - *What it means*: Make error messages clearer and more helpful
  - *Why it helps*: Easier to debug problems when they occur
  - *Priority*: Medium
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

### Testing & Quality Assurance
- Unit test coverage expansion
- Integration testing
- Performance benchmarking

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