# MHM System Architecture

> **Audience**: Human Developer and AI Collaborators (Cursor, Codex, etc.)   
> **Purpose**: System design, data flow, and technical architecture  
> **Style**: Technical, detailed, reference-oriented

> **See [README.md](README.md) for complete navigation and project overview**  
> **See [AI_ARCHITECTURE.md](AI_ARCHITECTURE.md) for AI-optimized quick reference**

## 🚀 Quick Reference

### **Key Modules Decision Tree**
1. **User data access?** → `core/user_data_handlers.py`, `core/user_data_validation.py`
2. **UI components?** → `ui/dialogs/`, `ui/widgets/`
3. **Communication?** → `communication/` directory
4. **Scheduling?** → `core/scheduler.py`, `core/schedule_management.py`
5. **Configuration?** → `core/config.py`
6. **Testing?** → `tests/` directory

### **Data Flow Patterns**
- **User Data**: `data/users/{user_id}/` → `core/user_data_handlers.py` → UI/communication module
- **Messages**: `resources/default_messages/` → `data/users/{user_id}/messages/`
- **Configuration**: `.env` → `core/config.py` → Application
- **UI**: `.ui` files → `ui/generated/` → `ui/dialogs/` → `ui_app_qt.py`

### **Critical Files (Don't Break)**
- `run_mhm.py` - Main entry point
- `core/service.py` - Background service
- `ui/ui_app_qt.py` - Admin interface
- `core/user_data_handlers.py` - Unified user data access
- `communication/core/channel_orchestrator.py` - Communication coordination

---

## Directory Structure & Key Modules

- **ai_tools/**: AI collaboration tools, audit scripts, and documentation management
- **communication/**: Messaging and communication channels (Discord, Email, etc.)
- **core/**: Core logic, utilities, configuration, scheduling, analytics, and data management
- **custom_data/**: User data storage with backups and user index
- **data/**: User data storage (per-user subdirectories: account.json, preferences.json, schedules.json, etc.)
- **resources/default_messages/**: Default motivational, health, and other message templates
- **resources/**: Application resources and presets
- **scripts/**: One-off scripts, debug, and migration tools
- **styles/**: QSS theme files for UI styling
- **tasks/**: Task and reminder management
- **tests/logs/**: Test execution logs (isolated from application logs)
- **tests/**: Testing framework with unit, integration, behavior, and UI tests
- **ui/**: PySide6/Qt-based management UI with organized structure:
  - `ui/designs/`: Qt Designer files (.ui)
  - `ui/generated/`: Auto-generated Python classes (*_pyqt.py)
  - `ui/dialogs/`: Dialog implementations
  - `ui/widgets/`: Widget implementations
- **user/**: User context and preferences management
- **.cursor/rules/**: Cursor IDE rules for AI assistance (audit.mdc, context.mdc, critical.mdc)

---

## User Data Model & File Structure

- **Each user has a directory:**
  - `account.json`: Core info (user_id, name, contact, etc.)
  - `preferences.json`: FLAT dict of user preferences (categories, checkins, etc.)
  - `schedules.json`: User's schedule data
  - `user_context.json`: Personalization data (preferred name, health info, etc.)
  - `messages/`: Per-category message files and sent message history
  - `tasks/`: Task-specific data and settings
  - (Other files: chat_interactions.json, checkins.json, etc.)

**Message File Handling (2025-07):**
- Message files are only created for categories a user is opted into.
- All message files are always created from the corresponding file in `resources/default_messages/` (never as a list of strings).
- Legacy/invalid files can be fixed using `scripts/fix_user_message_formats.py` (migration) and `scripts/cleanup_user_message_files.py` (cleanup).

**Important:**
- `preferences.json` is a flat dict (not nested under a 'preferences' key).
- When loading all user data, code merges these files into a single dict, e.g.:
  ```python
  user_data = {
    ... # from account.json
    'preferences': { ... },  # from preferences.json
    'schedules': { ... },    # from schedules.json
    'user_context': { ... }, # from user_context.json
  }
  ```
- When saving, only the contents of `user_data['preferences']` are written to `preferences.json` (flat).
- **All user data access is now handled exclusively through the unified `get_user_data()` handler. All legacy user data functions have been removed.**
- **Message files are stored per-user in `data/users/{user_id}/messages/` directory, not in global directories.**

---

## Data Handling Patterns

- **Always load, update, and save the full preferences dict** to avoid data loss.
- Never write the whole user_data object or nest under 'preferences' in preferences.json.
- When updating a single preference, load the full dict, update the key, and save the whole dict back.

---

## Key Modules & Responsibilities

- **core/file_operations.py, core/user_management.py, core/message_management.py, core/schedule_management.py, core/response_tracking.py, core/service_utilities.py, core/validation.py, core/user_data_validation.py**: Data loading/saving, user info management, file path logic, and utility functions. Handles splitting/merging user data across files. **Note**: `user_management.py` now contains legacy wrappers; new code should use `user_data_handlers.py` and `user_data_validation.py`.
- **user/user_context.py**: Singleton for managing the current user's context in memory. Provides methods to get/set preferences and save/load user data.
- **user/user_preferences.py**: (Planned) Class-based interface for managing user preferences.
- **ui/ui_app_qt.py**: Main PySide6/Qt UI application, user selection, and admin panel.
- **ui/dialogs/**: Dialog implementations for account creation, user management, etc.
- **communication/**: Messaging system for different platforms, using user data for personalized interactions.
- **core/scheduler.py**: Scheduling logic for reminders, check-ins, and message delivery. Includes intelligent task reminder scheduling with random task selection and timing.
- **core/checkin_analytics.py**: Analytics and insights on user check-in data.

---

## UI Architecture & Naming Conventions

### Directory Structure
The UI system uses a clean separation of concerns:
- **Designs** (`ui/designs/`): Qt Designer .ui files for visual layout
- **Generated** (`ui/generated/`): Auto-generated Python classes from .ui files
- **Dialogs** (`ui/dialogs/`): Dialog implementations with business logic
- **Widgets** (`ui/widgets/`): Reusable widget implementations

### Naming Conventions
- **Dialogs**: Use "management" suffix (e.g., `category_management_dialog.py`)
- **Widgets**: Use "settings" or "selection" suffix (e.g., `category_selection_widget.py`)
- **Generated Files**: Use "_pyqt" suffix (e.g., `category_management_dialog_pyqt.py`)
- **No Redundant Prefixes**: Removed `ui_app_` prefix since all files are in `ui/` directory

### File Mapping Examples
| Purpose | Design File | Generated File | Implementation |
|---------|-------------|----------------|----------------|
| Category Management | `category_management_dialog.ui` | `category_management_dialog_pyqt.py` | `category_management_dialog.py` |
| Account Creation | `account_creator_dialog.ui` | `account_creator_dialog_pyqt.py` | `account_creator_dialog.py` |
| Task Settings | `task_settings_widget.ui` | `task_settings_widget_pyqt.py` | `task_settings_widget.py` |

## Adding New Features Safely
- Always use the provided load/save functions for user data.
- When adding new preferences, update the full dict and save it, never just a single key.
- Document new data fields and update this file as needed.
- For UI components, follow the established naming conventions and directory structure.

## IDE/Debugger Double Process Note

When using the play/debug button in VS Code or Cursor, you may see two service processes due to IDE/debugger quirks. This does not affect the core architecture. For best results, run the app from a terminal with the venv activated.
