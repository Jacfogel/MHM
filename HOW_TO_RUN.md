# How to Run MHM

> **Audience**: New users and developers setting up the project  
> **Purpose**: Step-by-step setup and launch instructions  
> **Style**: Clear, beginner-friendly, troubleshooting-focused

## [Navigation](#navigation)
- **[Project Overview](README.md)** - What MHM is and what it does
- **[Development Workflow](DEVELOPMENT_WORKFLOW.md)** - For ongoing development
- **[Quick Reference](QUICK_REFERENCE.md)** - Common commands and shortcuts
- **[Architecture](ARCHITECTURE.md)** - System design and components
- **[Troubleshooting](README.md#troubleshooting)** - Common issues and solutions

## 🚀 Quick Start (Recommended)

**Important**: Always use a virtual environment to keep your system Python clean and avoid dependency conflicts.

### Step 1: Set up Virtual Environment
```bash
# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### Step 2: Install Dependencies
```bash
# Make sure your virtual environment is activated (you should see (venv) in your prompt)
pip install -r requirements.txt
```

### Step 3: Launch the Application
```bash
python run_mhm.py
```
This opens the admin panel so you can manage users and start the background service.

## 🔧 Alternative Commands

Once your virtual environment is set up and activated:
```bash
python core/service.py  # run service only (no UI)
python ui/ui_app.py     # admin panel only (legacy Tkinter)
```

## 📁 Alternative Launch Methods

You can also run individual components directly if needed:

## ⚠️ Important Notes

- **Always activate your virtual environment** before running the app
- **Never install dependencies globally** - this can cause conflicts
- **If you see (venv) in your terminal prompt**, you're using the virtual environment correctly
- **To deactivate the virtual environment**, simply type `deactivate`

## 🆘 Troubleshooting

### "Command not found" errors
Make sure your virtual environment is activated. You should see `(venv)` at the beginning of your command prompt.

### Import errors
Try reinstalling dependencies in your virtual environment:
```bash
pip install -r requirements.txt --force-reinstall
```

### Permission errors on Windows
Run PowerShell as Administrator, or use:
```bash
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

## ❓ Frequently Asked Questions

### **Q: Do I need to install Python globally?**
**A**: No! Always use a virtual environment. This keeps your system Python clean and prevents conflicts with other projects.

### **Q: What if I see "(venv)" but the app still doesn't work?**
**A**: Try deactivating and reactivating your virtual environment:
```bash
deactivate
venv\Scripts\activate
pip install -r requirements.txt
```

### **Q: Can I run the service without the admin panel?**
**A**: Yes! Run `python core/service.py` for the background service only, or `python ui/ui_app.py` for the admin panel only.

### **Q: What's the difference between the two UI files?**
**A**: 
- `ui/ui_app_qt.py` - Modern PySide6/Qt interface (recommended)
- `ui/ui_app.py` - Legacy Tkinter interface (deprecated)

### **Q: How do I know if the service is running?**
**A**: Check for Python processes: `Get-Process python | Where-Object {$_.CommandLine -like "*service.py*"}`

### **Q: Where are my logs stored?**
**A**: Check `app.log` in the project root directory for application logs.

## 📚 Next Steps
- **Project Overview**: See [README.md](README.md) for features and architecture
- **Development Workflow**: See [DEVELOPMENT_WORKFLOW.md](DEVELOPMENT_WORKFLOW.md) for safe practices
- **Quick Reference**: See [QUICK_REFERENCE.md](QUICK_REFERENCE.md) for common commands
- **Architecture**: See [ARCHITECTURE.md](ARCHITECTURE.md) for system design
