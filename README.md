# Mental Health Management (MHM)

> **Audience**: Human Developer (Beginner Programmer)  
> **Purpose**: Project overview and features  
> **Style**: Comprehensive, beginner-friendly, encouraging

MHM is a simple personal assistant created by and for a single beginner programmer. It sends scheduled motivational messages and basic mood tracking through Discord (email optional). The project also supports optional local AI integration via LM Studio for contextual chat responses.

## [Navigation](#navigation)
- **[Project Vision](PROJECT_VISION.md)** - Overarching vision and mission
- **[Quick Start](HOW_TO_RUN.md)** - Get up and running in minutes
- **[Development Workflow](DEVELOPMENT_WORKFLOW.md)** - For contributors and developers  
- **[Architecture Overview](ARCHITECTURE.md)** - System design and components
- **[Quick Reference](QUICK_REFERENCE.md)** - Common commands and shortcuts
- **[Documentation Guide](DOCUMENTATION_GUIDE.md)** - How to contribute to docs
- **[Development Plans](development_docs/PLANS.md)** - Current plans and strategies
- **[Recent Changes](ai_development_docs/AI_CHANGELOG.md)** - Brief summary of recent changes
- **[Current Priorities](TODO.md)** - What we're working on next

## Features
- Multi-channel messaging (Discord, Email)
- Automated daily reminders and basic mood tracking
- Optional AI-powered replies via LM Studio
- Runs as a background service with an admin panel
- **Comprehensive error handling** with graceful recovery across ALL modules
- **Configuration validation** with automatic setup
- **Modular architecture** for maintainability


## Quick Start
1. Clone the repo
   ```powershell
   git clone https://github.com/Jacfogel/MHM.git
   cd MHM
   ```
2. Install requirements
   ```powershell
   pip install -r requirements.txt
   ```
3. Launch the app
   ```powershell
   # For human users (UI interface)
   python run_mhm.py
   
   # For AI collaborators (headless service)
   python run_headless_service.py start
   ```
See **HOW_TO_RUN.md** for more details.

## Documentation
- **README.md** - Project overview and features
- **HOW_TO_RUN.md** - Setup and installation instructions
- **ARCHITECTURE.md** - System structure and data organization
- **DEVELOPMENT_WORKFLOW.md** - Safe development practices for beginners
- **QUICK_REFERENCE.md** - Essential commands and troubleshooting
- **development_docs/PLANS.md** - Development plans and strategies
- **ai_development_docs/AI_CHANGELOG.md** - Brief summary of recent changes
- **development_docs/CHANGELOG_DETAIL.md** - Complete detailed change history
- **ai_development_tools/README.md** - AI development tools overview
- **TODO.md** - Current development priorities
- **DOCUMENTATION_GUIDE.md** - Documentation organization and standards

### Documentation Categories
- **🤖 AI-Focused**: `AI_SESSION_STARTER.md` and `.cursor/rules/` - For AI assistants
- **👤 User-Focused**: Development guides and references - For human developers
- **🔧 Configuration**: `requirements.txt`, `.env` - For both

### Configuration Files
- **`.env`** - Environment variables and configuration (in `.cursorignore` for security)
- **`requirements.txt`** - Python dependencies
- **`core/config.py`** - Default configuration values and validation

See **DOCUMENTATION_GUIDE.md** for detailed organization and maintenance guidelines.

## Architecture
The background service (`core/service.py`) runs independently of the admin UI (`ui/ui_app_qt.py`). 
- `run_mhm.py` launches the admin UI only (for human users)
- `run_headless_service.py` launches the service directly (for AI collaborators)
All data stays on your local machine.

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
├── ai/                    # AI assistant components
├── ai_development_docs/   # AI documentation and guides
├── ai_development_tools/  # AI collaboration tools and audit scripts
├── communication/         # Messaging channels and orchestration
├── core/                  # Backend service (refactored into focused modules)
├── data/                  # User data (gitignored)
├── development_docs/      # Development documentation
├── logs/                  # Application logs
├── resources/             # Application resources and presets
│   └── default_messages/
├── styles/                # QSS theme files
├── tasks/                 # Task/reminder framework
├── tests/                 # Testing framework
├── ui/                    # Admin panel (PySide6/Qt)
├── user/                  # User preferences
├── run_mhm.py             # UI entry point (human users)
└── run_headless_service.py # Headless entry point (AI collaborators)
```

## License
This project is personal. Keep forks private and respect mental health data.

## Important Notes for Beginners

**Safety First**: All these improvements will be implemented carefully, one at a time, with lots of testing to make sure nothing breaks. We'll always have a backup of your working code before making changes.

**Learning Opportunity**: Each improvement will be explained in simple terms, and you'll learn new programming concepts along the way.

**No Rush**: We can take our time with each improvement. It's better to do things slowly and correctly than to rush and break something.

**Your Control**: You can decide which improvements to tackle first, and we can skip any that seem too complex or risky.

**Recent Success**: We've successfully implemented a comprehensive error handling system that makes the application much more reliable and easier to debug. **This covers the entire application - from the UI to the background service to all communication channels.**

For current development priorities and completed improvements, see **TODO.md** and **ai_development_docs/AI_CHANGELOG.md**.

## 🆘 Troubleshooting

### Common Issues & Solutions

#### **Double Service Process in VS Code/Cursor**
If you see two service processes when using the play/debug button in VS Code or Cursor, this is due to IDE/debugger quirks, not a problem with the project code. For the most reliable experience, run the app from a terminal with your virtual environment activated.

#### **"Command not found" Errors**
- **Solution**: Make sure your virtual environment is activated. You should see `(venv)` at the beginning of your command prompt.
- **Fix**: Run `venv\Scripts\activate` (Windows) or `source venv/bin/activate` (macOS/Linux)

#### **Import Errors**
- **Solution**: Try reinstalling dependencies in your virtual environment
- **Fix**: `pip install -r requirements.txt --force-reinstall`

#### **Permission Errors on Windows**
- **Solution**: Run PowerShell as Administrator, or adjust execution policy
- **Fix**: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`

#### **App Won't Start**
1. Check if Python is installed: `python --version`
2. Install dependencies: `pip install -r requirements.txt`
3. Check for syntax errors: `python -m py_compile run_mhm.py` or `python -m py_compile run_headless_service.py`
4. Check log file: `Get-Content logs/app.log -Tail 20` (default location: `logs/app.log`)

#### **Service Won't Start**
1. Check if Discord token is set in `.env`
2. Check if required directories exist
3. Check log file for specific errors
4. Try running service directly: `python core/service.py`

#### **Messages Not Sending**
1. Check if service is running
2. Verify Discord bot token in `.env`
3. Check bot permissions in Discord
4. Check log file for error messages

#### **Discord Slash Command Warnings**
If you see warnings about slash command syncing, you can optionally set `DISCORD_APPLICATION_ID` in your `.env` file to prevent these warnings. This is not required - the bot works fine without it, but setting it will result in cleaner logs.
- **Optional**: Add `DISCORD_APPLICATION_ID=your_application_id_here` to your `.env` file
- Get your application ID from the Discord Developer Portal (your bot's application ID)

### Getting Help
- **Quick Reference**: See [QUICK_REFERENCE.md](QUICK_REFERENCE.md) for common commands
- **Development Workflow**: See [DEVELOPMENT_WORKFLOW.md](DEVELOPMENT_WORKFLOW.md) for safe practices
- **Architecture**: See [ARCHITECTURE.md](ARCHITECTURE.md) for system understanding
- **Current Issues**: See [TODO.md](TODO.md) for known issues and priorities
