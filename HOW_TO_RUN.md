# How to Run MHM


> **File**: `HOW_TO_RUN.md`
> **Audience**: New users and developers setting up the project  
> **Purpose**: Step-by-step setup and launch instructions  
> **Style**: Clear, beginner-friendly, troubleshooting-focused

> **See [README.md](README.md) for complete navigation and project overview.**

## 1. Quick Start (Recommended)

**Important**: Always use a virtual environment to keep your system Python clean and avoid dependency conflicts.

### 1.1. Step 1: Set up Virtual Environment
```powershell
# Create a virtual environment
python -m venv .venv

# Activate the virtual environment
# On Windows:
.\.venv\Scripts\Activate.ps1
# On macOS/Linux:
source .venv/bin/activate
```

### 1.2. Step 2: Install Dependencies
```powershell
# Make sure your virtual environment is activated (you should see (.venv) in your prompt)
pip install -r requirements.txt
```

### 1.3. Step 3: Install the Project in Editable Mode
Editable installation keeps the `core`, `communication`, `ui`, and `tasks` packages on the
Python path so you never need manual `sys.path` tweaks.

```powershell
pip install -e .

# If you want the optional UI dependencies in one step
pip install -e .[ui]
```

### 1.4. Step 4: Configure Environment (Optional)
The system uses sensible defaults, but you can customize settings in `.env`.

For the canonical list of settings, what they do, and common failure modes, see:
- [CONFIGURATION_REFERENCE.md](CONFIGURATION_REFERENCE.md)

Quick setup:
```powershell
# Copy the example configuration
Copy-Item .env.example .env
# Edit .env with your preferred settings
```

**Note**: The `.env` file is in `.cursorignore` for security (contains API keys and passwords).

### 1.5. Step 5: Launch the Application
```powershell
# For human users (UI interface)
python run_mhm.py

# For AI collaborators (headless service)
python run_headless_service.py start
```
- `run_mhm.py` opens the admin panel so you can manage users and start the background service
- `run_headless_service.py` launches the service directly for AI collaborators

## 2. Alternative Commands

Once your virtual environment is set up and activated:
```powershell
python core/service.py  # run service only (no UI)
python ui/ui_app_qt.py     # admin panel only (PySide6/Qt)
```

## 3. Command Reference (Discord and Chat)

These commands work as Discord slash commands (`/command`), bang commands (`!command`), or plain text phrases. The mapped text shows what the assistant understands if you prefer to type the words instead of the slash command.

| Command | Slash / Bang | Mapped text (what the assistant hears) | What it does |
| --- | --- | --- | --- |
| Start | `/start`, `!start` | `start` | Sends the welcome/setup message. |
| Tasks | `/tasks`, `!tasks` | `show my tasks` | Lists your current tasks. |
| Profile | `/profile`, `!profile` | `show profile` | Shows your saved profile details. |
| Schedule | `/schedule`, `!schedule` | `show schedule` | Shows your saved schedules. |
| Messages | `/messages`, `!messages` | `show messages` | Shows your saved messages. |
| Analytics | `/analytics`, `!analytics` | `show analytics` | Shows wellness analytics and insights. |
| Status | `/status`, `!status` | `status` | Shows system/user status. |
| Help | `/help`, `!help` | `help` | Shows help and examples. |
| Check-in | `/checkin`, `!checkin` | `start checkin` | Starts a check-in flow. |
| Restart check-in | `/restart`, `!restart` | `restart checkin` | Restarts an in-progress check-in. |
| Clear flows | `/clear`, `!clear` | `clear flows` | Clears stuck conversation flows. |
| Cancel | `/cancel`, `!cancel` | `/cancel` | Cancels the current flow immediately. |

**Notes**
- Slash and bang commands are equivalent; use whichever is more convenient.
- If you forget the exact command, typing the mapped text (for example, "show my tasks") works the same way.
- Check-in related commands (`/checkin`, `/restart`, `/clear`, `/cancel`) operate on the conversation flow system.

## 4. Alternative Launch Methods

You can also run individual components directly if needed:

## 5. Important Notes

- **Always activate your virtual environment** before running the app
- **Never install dependencies globally** - this can cause conflicts
- **If you see (.venv) in your terminal prompt**, you're using the virtual environment correctly
- **To deactivate the virtual environment**, simply type `deactivate`
- **Windows Python Processes**: On Windows, you may see two Python processes when running the app. One is your actual code, while the system Python is a harmless Windows artifact.

## 6. Troubleshooting

### 6.1. "Command not found" errors
Make sure your virtual environment is activated. You should see `(.venv)` at the beginning of your command prompt.

### 6.2. Import errors
Try reinstalling dependencies in your virtual environment:
```powershell
pip install -r requirements.txt
```

### 6.3. Environment variable issues
Ensure your `.env` file (if used) is correctly configured and that you restarted the app after changes.

### 6.4. Python version problems
MHM expects a reasonably recent Python 3 version (for example 3.11). If you see syntax errors on valid code, check your Python version:
```powershell
python --version
```

### 6.5. Virtual environment not activating
If `.\.venv\Scripts\Activate.ps1` fails:
- Make sure `.venv` exists in the project root
- Check your PowerShell execution policy:
  ```powershell
  Get-ExecutionPolicy
  ```
  You may need to adjust it (for example, `RemoteSigned`) with administrator privileges.

**Q: Do I need to install Python globally?**
**A**: No! Always use a virtual environment. This keeps your system Python clean and prevents conflicts with other projects.

**Q: What if I see "(.venv)" but the app still doesn't work?**
**A**: Try deactivating and reactivating your virtual environment:
```powershell
deactivate
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

**Q: Can I run the service without the admin panel?**
**A**: Yes! Run `python run_headless_service.py start` for the background service only (no UI).

**Q: What's the difference between the launch options?**
**A**: 
- `run_mhm.py` starts the UI (admin panel), which you can then use to start/stop the service and manage users.
- `ui/ui_app_qt.py` does the same thing as `run_mhm.py` (it's the actual UI application that `run_mhm.py` launches).
- `run_headless_service.py start` runs the service without any UI (for AI collaborators or headless operation).

**Q: How do I know if the service is running?**
**A**: Check for Python processes: `Get-Process python | Where-Object {$_.CommandLine -like "*service.py*"}`

**Q: Where are my logs stored?**
**A**: Logs are stored in the `logs/` directory. The main application log is `logs/app.log`, with component-specific logs like `logs/discord.log`, `logs/ai.log`, `logs/errors.log`, etc. See section 4. "Component Log Files and Layout" in [LOGGING_GUIDE.md](logs/LOGGING_GUIDE.md) for details.

**Q: Why do I see two Python processes when running the app on Windows?**
**A**: This is normal Windows behavior. Windows launches both your script and the underlying interpreter. The process running your actual code is the one that matters; the system Python is a harmless artifact.

## 7. Next Steps
- **Project Overview**: See [README.md](README.md) for features and architecture
- **Development Workflow**: See [DEVELOPMENT_WORKFLOW.md](DEVELOPMENT_WORKFLOW.md) for safe practices
- **Architecture**: See [ARCHITECTURE.md](ARCHITECTURE.md) for system design