# How to Run MHM

> **Audience**: New users and developers setting up the project  
> **Purpose**: Step-by-step setup and launch instructions  
> **Style**: Clear, beginner-friendly, troubleshooting-focused

> **See [README.md](README.md) for complete navigation and project overview**
- **[Troubleshooting](README.md#troubleshooting)** - Common issues and solutions

## 🚀 Quick Start (Recommended)

**Important**: Always use a virtual environment to keep your system Python clean and avoid dependency conflicts.

### Step 1: Set up Virtual Environment
```powershell
# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### Step 2: Install Dependencies
```powershell
# Make sure your virtual environment is activated (you should see (venv) in your prompt)
pip install -r requirements.txt
```

### Step 3: Configure Environment (Optional)
The system uses sensible defaults, but you can customize settings in `.env`:
```powershell
# Copy the example configuration (if it exists)
Copy-Item .env.example .env
# Edit .env with your preferred settings
```

**Note**: The `.env` file is in `.cursorignore` for security (contains API keys and passwords).

### Step 4: Launch the Application
```powershell
# For human users (UI interface)
python run_mhm.py

# For AI collaborators (headless service)
python run_headless_service.py start
```
- `run_mhm.py` opens the admin panel so you can manage users and start the background service
- `run_headless_service.py` launches the service directly for AI collaborators

## 🔧 Alternative Commands

Once your virtual environment is set up and activated:
```powershell
python core/service.py  # run service only (no UI)
python ui/ui_app_qt.py     # admin panel only (PySide6/Qt)
```

## 📁 Alternative Launch Methods

You can also run individual components directly if needed:

## ⚠️ Important Notes

- **Always activate your virtual environment** before running the app
- **Never install dependencies globally** - this can cause conflicts
- **If you see (venv) in your terminal prompt**, you're using the virtual environment correctly
- **To deactivate the virtual environment**, simply type `deactivate`
- **Windows Python Processes**: On Windows, you may see two Python processes when running scripts - this is normal behavior and doesn't affect functionality

## 🆘 Troubleshooting

### "Command not found" errors
Make sure your virtual environment is activated. You should see `(venv)` at the beginning of your command prompt.

### Import errors
Try reinstalling dependencies in your virtual environment:
```powershell
pip install -r requirements.txt --force-reinstall
```

### Permission errors on Windows
Run PowerShell as Administrator, or use:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Multiple Python processes on Windows
If you see two Python processes when running the app (one with venv Python, one with system Python), this is normal Windows behavior. The venv Python process runs your actual code, while the system Python process is a harmless Windows artifact.

## ❓ Frequently Asked Questions

### **Q: Do I need to install Python globally?**
**A**: No! Always use a virtual environment. This keeps your system Python clean and prevents conflicts with other projects.

### **Q: What if I see "(venv)" but the app still doesn't work?**
**A**: Try deactivating and reactivating your virtual environment:
```powershell
deactivate
venv\Scripts\activate
pip install -r requirements.txt
```

### **Q: Can I run the service without the admin panel?**
**A**: Yes! Run `python core/service.py` for the background service only, or `python ui/ui_app_qt.py` for the admin panel only.

### **Q: What's the difference between the two UI files?**
**A**: 
- `ui/ui_app_qt.py` - PySide6/Qt interface (current)

### **Q: How do I know if the service is running?**
**A**: Check for Python processes: `Get-Process python | Where-Object {$_.CommandLine -like "*service.py*"}`

### **Q: Where are my logs stored?**
**A**: Check `app.log` in the project root directory for application logs.

### **Q: Why do I see two Python processes when running the app on Windows?**
**A**: This is normal Windows behavior. Windows launches both your venv Python and system Python when running scripts. The venv Python runs your actual code, while the system Python is a harmless Windows artifact.

## 📚 Next Steps
- **Project Overview**: See [README.md](README.md) for features and architecture
- **Development Workflow**: See [DEVELOPMENT_WORKFLOW.md](DEVELOPMENT_WORKFLOW.md) for safe practices
- **Quick Reference**: See [QUICK_REFERENCE.md](QUICK_REFERENCE.md) for common commands
- **Architecture**: See [ARCHITECTURE.md](ARCHITECTURE.md) for system design
