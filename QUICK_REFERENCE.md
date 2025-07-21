# Quick Reference Guide

> **Audience**: Human Developer (Beginner Programmer)  
> **Purpose**: Essential commands and troubleshooting  
> **Style**: Concise, scannable, action-oriented

> **See [README.md](README.md) for complete navigation and project overview**

## 🚀 Essential Commands

> **See [HOW_TO_RUN.md](HOW_TO_RUN.md) for complete setup and installation instructions**

### Running the App
```powershell
# Main application (admin panel + service)
python run_mhm.py

# Service only (background)
python core/service.py

# Admin panel only (PySide6/Qt)
python ui/ui_app_qt.py
```

### Testing
```powershell
# Run all tests
python run_tests.py

# Run specific test types
python run_tests.py --type unit
python run_tests.py --type integration
python run_tests.py --verbose
```

### Development
```powershell
# Create backup before major changes
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
Copy-Item -Path "." -Destination "../MHM_backup_$timestamp" -Recurse

# Add new dependency
pip install package_name
pip freeze > requirements.txt
```

## 📁 Key File Locations

### Core Application Files
- `run_mhm.py` - Main entry point
- `core/service.py` - Background service
- `ui/ui_app_qt.py` - Admin interface (PySide6/Qt)
- `core/config.py` - Configuration settings

### User Data
- `data/users/` - User profiles and preferences
- `data/users/{user_id}/messages/` - Per-user custom messages by category
- `data/users/{user_id}/messages/sent_messages.json` - Per-user message history
- `app.log` - Application logs

### Configuration
- `.env` - Environment variables (create if needed)
- `requirements.txt` - Python dependencies
- `core/config.py` - Application settings

## 🔧 Common Tasks

### Create a Backup
```powershell
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
Copy-Item -Path "." -Destination "../MHM_backup_$timestamp" -Recurse
```

### Check if Service is Running
```powershell
Get-Process python | Where-Object {$_.CommandLine -like "*service.py*"}
```

### View Recent Logs
```powershell
Get-Content app.log -Tail 50
```

### Clean Python Cache
```powershell
Get-ChildItem -Path . -Recurse -Include "__pycache__" | Remove-Item -Recurse -Force
```

## 🐛 Troubleshooting

### Common Problems & Solutions

#### **Virtual Environment Issues**
- **Problem**: "Command not found" or import errors
- **Solution**: Ensure virtual environment is activated - you should see `(venv)` in your prompt
- **Fix**: `venv\Scripts\activate` then `pip install -r requirements.txt --force-reinstall`

#### **Permission Issues**
- **Problem**: PowerShell execution policy errors
- **Solution**: Adjust execution policy for current user
- **Fix**: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`

#### **Service Issues**
- **Problem**: Service won't start or messages not sending
- **Solution**: Check Discord token and bot permissions
- **Fix**: Verify `.env` file has `DISCORD_BOT_TOKEN=your_token_here`

#### **UI Issues**
- **Problem**: UI won't launch or looks broken
- **Solution**: Try the modern Qt interface instead of legacy Tkinter
- **Fix**: Use `python ui/ui_app_qt.py` instead of `python ui/ui_app.py`

### App Won't Start
1. Check if Python is installed: `python --version`
2. Install dependencies: `pip install -r requirements.txt`
3. Check for syntax errors: `python -m py_compile run_mhm.py`
4. Check log file: `Get-Content app.log -Tail 20`

### Service Won't Start
1. Check if Discord token is set in `.env`
2. Check if required directories exist
3. Check log file for specific errors
4. Try running service directly: `python core/service.py`

### UI Issues
1. Check if PySide6 is available: `python -c "import PySide6"`
2. Try running UI directly: `python ui/ui_app_qt.py`
3. Check for missing dependencies
4. Restart the application

### Messages Not Sending
1. Check if service is running
2. Verify Discord bot token in `.env`
3. Check bot permissions in Discord
4. Check log file for error messages

## 📝 Configuration

### Required Environment Variables
Create a `.env` file in the project root:

```env
# Discord Bot Token (required)
DISCORD_BOT_TOKEN=your_discord_bot_token_here

# Optional: Email Configuration
EMAIL_SMTP_SERVER=smtp.gmail.com
EMAIL_SMTP_USERNAME=your_email@gmail.com
EMAIL_SMTP_PASSWORD=your_app_password

# Optional: LM Studio for AI
LM_STUDIO_BASE_URL=http://localhost:1234/v1
```

### Logging Levels
- `DEBUG` - Detailed information for debugging
- `INFO` - General information about program execution
- `WARNING` - Indicate a potential problem
- `ERROR` - A more serious problem
- `CRITICAL` - A critical problem that may prevent the program from running

## 🎯 Development Tips

> **See [DEVELOPMENT_WORKFLOW.md](DEVELOPMENT_WORKFLOW.md) for detailed development practices and safety guidelines**

## 📞 Getting Help

### What to Include When Asking for Help
1. What you were trying to do
2. What happened instead
3. Any error messages
4. What you've already tried
5. Your current setup (Windows version, Python version, etc.)

### Example Help Request
"I'm trying to add a new message category called 'meditation'. I added it to the UI but it's not showing up in the dropdown. The error message says 'KeyError: meditation'. I've checked that the category exists in the default_messages folder. I'm using Windows 11 and Python 3.9."

## 🔄 Update Process

### When Adding New Features
1. Update `CHANGELOG_DETAIL.md` with change details
2. Update `CHANGELOG_BRIEF.md` with brief summary for AI context
2. Update `README.md` if needed
3. Update `requirements.txt` if adding dependencies
4. Test thoroughly
5. Create backup if it's a major change

### When Fixing Bugs
1. Document the bug in `CHANGELOG_DETAIL.md`
2. Update `CHANGELOG_BRIEF.md` with brief summary for AI context
2. Test the fix
3. Test that you didn't break anything else
4. Update documentation if needed

Remember: Small, tested changes are better than big, untested changes! 