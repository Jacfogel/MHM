# Mental Health Management (MHM)

> **Audience**: Human Developer (Beginner Programmer)  
> **Purpose**: Project overview and features  
> **Style**: Comprehensive, beginner-friendly, encouraging

MHM is a simple personal assistant created by and for a single beginner programmer. It sends scheduled motivational messages and basic mood tracking through Discord (email and Telegram are optional). The project also supports optional local AI integration via LM Studio for contextual chat responses.

## Features
- Multi-channel messaging (Discord, Telegram, Email)
- Automated daily reminders and basic mood tracking
- Optional AI-powered replies via LM Studio
- Runs as a background service with an admin panel
- **Comprehensive error handling** with graceful recovery across ALL modules
- **Configuration validation** with automatic setup
- **Modular architecture** for maintainability


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
- **CHANGELOG.md** - Change log and recent updates
- **TODO.md** - Current development priorities
- **DOCUMENTATION_GUIDE.md** - Documentation organization and standards

### Documentation Categories
- **🤖 AI-Focused**: `AGENTS.md` and `.cursor/rules/` - For AI assistants
- **👤 User-Focused**: Development guides and references - For human developers
- **🔧 Configuration**: `requirements.txt`, `.env` - For both

See **DOCUMENTATION_GUIDE.md** for detailed organization and maintenance guidelines.

## Architecture
The background service (`core/service.py`) runs independently of the admin UI (`ui/ui_app.py`). `run_mhm.py` starts both together. All data stays on your local machine.

**Recent Improvements**:
- **Error Handling**: Centralized error handling with automatic recovery across ALL modules
- **Configuration**: Self-validating configuration system
- **Modularity**: Clean separation of concerns across modules
- **Enterprise-Grade**: Professional error handling spanning the entire application stack

## AI Integration (Optional)
If LM Studio is installed with a compatible model, MHM can provide local AI chat. The system works without it.

## Project Structure
```
MHM/
├── core/        # Backend service (refactored into focused modules)
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

## Important Notes for Beginners

**Safety First**: All these improvements will be implemented carefully, one at a time, with lots of testing to make sure nothing breaks. We'll always have a backup of your working code before making changes.

**Learning Opportunity**: Each improvement will be explained in simple terms, and you'll learn new programming concepts along the way.

**No Rush**: We can take our time with each improvement. It's better to do things slowly and correctly than to rush and break something.

**Your Control**: You can decide which improvements to tackle first, and we can skip any that seem too complex or risky.

**Recent Success**: We've successfully implemented a comprehensive error handling system that makes the application much more reliable and easier to debug. **This now covers ALL 22 modules across the entire application stack!**

For current development priorities and completed improvements, see **TODO.md** and **CHANGELOG.md**.

## Troubleshooting

### Double Service Process Issue in VS Code/Cursor
If you see two service processes when using the play/debug button in VS Code or Cursor, this is due to IDE/debugger quirks, not a problem with the project code. For the most reliable experience, run the app from a terminal with your virtual environment activated.
