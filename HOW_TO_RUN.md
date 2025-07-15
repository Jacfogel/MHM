# How to Run MHM

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

## 📁 Windows Shortcuts

The `scripts/launchers` directory contains Windows batch files if you prefer shortcuts.

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

See the README for an overview of features and project structure.
