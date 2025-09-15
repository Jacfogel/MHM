# AI Architecture - Quick Reference

> **Purpose**: Essential architectural patterns for AI collaborators  
> **For details**: See [ARCHITECTURE.md](../ARCHITECTURE.md)

## 🚀 Quick Reference

### **Key Modules**
- **User data**: `core/user_data_handlers.py`, `core/user_data_validation.py`
- **UI**: `ui/dialogs/`, `ui/widgets/`
- **Communication**: `communication/` directory
- **Scheduling**: `core/scheduler.py`
- **Configuration**: `core/config.py`

### **Critical Files (Don't Break)**
- `run_mhm.py` - Main entry point
- `core/service.py` - Background service
- `ui/ui_app_qt.py` - Admin interface
- `core/user_data_handlers.py` - Unified user data access
- `communication/core/channel_orchestrator.py` - Communication coordination

## 🏗️ Data Flow
- **User Data**: `data/users/{user_id}/` → `core/user_data_handlers.py` → UI/CommunicationManager
- **Messages**: `resources/default_messages/` → `data/users/{user_id}/messages/`
- **UI**: `.ui` files → `ui/generated/` → `ui/dialogs/` → `ui_app_qt.py`

## 📊 Data Patterns
- **Always use**: `get_user_data()` handler (unified access)
- **Never use**: Legacy user data functions (removed)
- **Preferences**: Flat dict, not nested under 'preferences' key
- **Messages**: Per-user in `data/users/{user_id}/messages/`

## 🎨 UI Patterns
- **Dialogs**: `{purpose}_management_dialog.py`
- **Widgets**: `{purpose}_settings_widget.py`
- **Generated**: `{original_name}_pyqt.py`
- **Designs**: `{purpose}_management_dialog.ui`

## 🚨 Common Issues
- **Data Access**: Use `get_user_data()` handler only
- **UI Integration**: Use proper data handlers, not direct file manipulation
- **Configuration**: Use `core/config.py` for all configuration

---

**Remember**: Follow established patterns, use unified data access, maintain separation of concerns.

---

## What's In The Full Doc
- See `ARCHITECTURE.md` for complete details: Directory Structure, User Data Model, Key Modules & Responsibilities, Data Handling Patterns, and UI architecture conventions.

## User Data Model (Concise)
- Per‑user directory `data/users/{user_id}` with `account.json`, flat `preferences.json`, `schedules.json`, `user_context.json`, and per‑user `messages/` (plus optional `tasks/`).
- Combined view: higher‑level helpers assemble `{ 'preferences': {...}, 'schedules': {...}, 'user_context': {...}, ... }` for features.
- Access exclusively via `core/user_data_handlers.get_user_data(...)` and corresponding save helpers; avoid direct file I/O in features.

## Directory Overview (Concise)
- `core/`: core logic, config, scheduling, data management
- `communication/`: channels and orchestration
- `ui/`: PySide6 admin tools (users don’t need to open UI)
- `resources/default_messages/`: message templates
- `data/users/`: per‑user runtime data
- `ai_development_tools/`: audits and documentation helpers

## Data Handling Patterns (Concise)
- Read/modify/write the full preferences dict; don’t partially overwrite files.
- Create message files only for opted‑in categories; store per‑user under `messages/`.
- Use `core/config.py` for paths and options; never hardcode paths.
