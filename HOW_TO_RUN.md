# How to Run MHM

1. Install the dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Launch the application:
   ```bash
   python run_mhm.py
   ```
   This opens the admin panel so you can manage users and start the background service.

Optional commands:
```bash
python core/service.py  # run service only (no UI)
python ui/ui_app.py     # admin panel only
```
The `scripts/launchers` directory contains Windows batch files if you prefer shortcuts.

See the README for an overview of features and project structure.
