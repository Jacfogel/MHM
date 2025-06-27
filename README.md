# Mental Health Management (MHM)

> **Audience**: Human Developer (Beginner Programmer)  
> **Purpose**: Project overview and features  
> **Style**: Comprehensive, beginner-friendly, encouraging

MHM is a simple personal assistant created by and for a single beginner programmer. It sends scheduled motivational messages and basic mood tracking through Discord (email and Telegram are optional). The project also supports optional local AI integration via LM Studio for contextual chat responses.

## Features
- Multi-channel messaging
- Automated daily reminders and basic mood tracking
- Optional AI-powered replies
- Runs as a background service with an admin panel

### Partially Implemented
- AI personalization when LM Studio is running

### Planned
- Advanced task management and progress tracking
- Advanced scheduling
- Integration with additional services

## Quick Start
1. Clone the repo
   ```bash
   git clone https://github.com/Jacfogel/MHM.git
   cd MHM
   ```
2. Install requirements
   ```bash
   pip install -r requirements.txt
   ```
3. Launch the app
   ```bash
   python run_mhm.py
   ```
See **HOW_TO_RUN.md** for more details.

## Documentation
- **README.md** - Project overview and features
- **HOW_TO_RUN.md** - Setup and installation instructions
- **ARCHITECTURE.md** - System structure and data organization
- **DEVELOPMENT_WORKFLOW.md** - Safe development practices for beginners
- **QUICK_REFERENCE.md** - Essential commands and troubleshooting
- **IMPROVEMENTS.md** - Change log and recent updates
- **DOCUMENTATION_GUIDE.md** - Documentation organization and standards

### Documentation Categories
- **🤖 AI-Focused**: `AGENTS.md` and `.cursor/rules/` - For AI assistants
- **👤 User-Focused**: Development guides and references - For human developers
- **🔧 Configuration**: `requirements.txt`, `.env` - For both

See **DOCUMENTATION_GUIDE.md** for detailed organization and maintenance guidelines.

## Architecture
The background service (`core/service.py`) runs independently of the admin UI (`ui/ui_app.py`). `run_mhm.py` starts both together. All data stays on your local machine.

## AI Integration (Optional)
If LM Studio is installed with a compatible model, MHM can provide local AI chat. The system works without it.

## Project Structure
```
MHM/
├── core/        # Backend service
├── ui/          # Admin panel
├── bot/         # Communication handlers
├── tasks/       # Task/reminder framework
├── default_messages/
├── user/        # User preferences
├── data/        # User data (gitignored)
├── scripts/     # Utilities and tools
└── run_mhm.py   # Entry point
```

## License
This project is personal. Keep forks private and respect mental health data.

## Approved Improvements (Beginner-Friendly)

### ✅ Completed Improvements (High Priority)
These improvements have been successfully implemented:

1. **✅ Refactor core/utils.py** - **COMPLETED**: Successfully broke the large utility file into smaller, focused modules: core/file_operations.py, core/user_management.py, core/message_management.py, core/schedule_management.py, core/response_tracking.py, core/service_utilities.py, and core/validation.py.
   - *What was accomplished*: Split the 1,492-line file into 7 focused modules with clear responsibilities
   - *Benefits achieved*: Makes code easier to find, understand, and fix when things go wrong

### Immediate Action Items (High Priority)
These improvements will make the code more reliable and easier to work with:

2. **Add comprehensive error handling** - Create a system for handling errors gracefully
   - *What it means*: When something goes wrong, the program tells you exactly what happened instead of crashing
   - *Why it helps*: Prevents the app from stopping unexpectedly and helps you fix problems faster

3. **Create testing framework** - Add automated tests for core functions
   - *What it means*: Write small programs that check if your main code works correctly
   - *Why it helps*: You can make changes without worrying about breaking existing features

4. **Add configuration validation** - Check that all required settings are present at startup
   - *What it means*: When the app starts, it checks that all necessary settings are configured
   - *Why it helps*: Prevents mysterious errors caused by missing or incorrect settings

5. **Implement data migration system** - Handle changes to how data is stored
   - *What it means*: When you change how data is saved, the app automatically updates old data to the new format
   - *Why it helps*: You can improve the app without losing your existing data

6. **Add performance monitoring** - Track how long operations take
   - *What it means*: The app keeps track of which operations are slow so you can improve them
   - *Why it helps*: Helps you identify and fix performance problems before they become annoying

7. **Create development guidelines** - Establish coding standards and best practices
   - *What it means*: Write down rules for how code should be written to keep it consistent
   - *Why it helps*: Makes the code easier to read and understand, especially when working with AI assistance

### Future Improvements (Lower Priority)
These are bigger projects that will enhance the app's capabilities:

- **Modular Architecture** - Break large files into smaller, focused modules
  - *What it means*: Organize code into logical groups that work together
  - *Why it helps*: Makes the app easier to understand and modify

- **Analytics Dashboard** - Visual insights into mental health patterns
  - *What it means*: Create charts and graphs showing trends in your mood and activities
  - *Why it helps*: Helps you see patterns and track your progress over time

- **Mobile Support** - Consider mobile app or responsive web interface
  - *What it means*: Make the app work well on phones and tablets
  - *Why it helps*: Access your mental health assistant anywhere, not just on your computer

- **Add monitoring dashboard** - Real-time system health monitoring
  - *What it means*: Create a screen that shows if all parts of the app are working properly
  - *Why it helps*: Quickly identify and fix problems before they affect your experience

## Future Improvements (Legacy)
- Refactor user preference handling through `UserPreferences`
- Expand Discord check-ins with more interactive prompts
- Explore deeper AI integration
- Develop a simple task list with reminders sent via the scheduler, then expand into mood- and context-aware systems
- Add charts showing trends in mood and tasks using Matplotlib or Plotly, later providing detailed wellness analytics
- Use the AI backend to deliver motivational messages or coping strategies
- Break large modules into smaller files
- Introduce consistent snake_case naming
- Centralize configuration in a single module
- Add unit tests for utilities and basic integration tests
- Standardize logging levels and improve dependency error messages
- Build a more interactive Discord bot with quick reactions or forms

## Important Notes for Beginners

**Safety First**: All these improvements will be implemented carefully, one at a time, with lots of testing to make sure nothing breaks. We'll always have a backup of your working code before making changes.

**Learning Opportunity**: Each improvement will be explained in simple terms, and you'll learn new programming concepts along the way.

**No Rush**: We can take our time with each improvement. It's better to do things slowly and correctly than to rush and break something.

**Your Control**: You can decide which improvements to tackle first, and we can skip any that seem too complex or risky.

Would you like to start with any particular improvement? I'd recommend starting with **configuration validation** (#4) as it's relatively simple and will help prevent problems before they happen.
