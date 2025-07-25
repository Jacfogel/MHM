# MHM System Architecture

> **Audience**: Developers and contributors  
> **Purpose**: System design, data flow, and technical architecture  
> **Style**: Technical, detailed, reference-oriented

## [Navigation](#navigation)
- **[Project Overview](README.md)** - What MHM is and what it does
- **[Quick Start](HOW_TO_RUN.md)** - Setup and installation instructions
- **[Development Workflow](DEVELOPMENT_WORKFLOW.md)** - Safe development practices
- **[Quick Reference](QUICK_REFERENCE.md)** - Common commands and shortcuts
- **[Documentation Guide](DOCUMENTATION_GUIDE.md)** - How to contribute to docs

---

## Directory Structure & Key Modules

- **bot/**: Messaging and communication bots (Discord, Email, Telegram, etc.)
- **core/**: Core logic, utilities, configuration, scheduling, analytics, and data management
- **data/**: User data storage (per-user subdirectories: profile.json, preferences.json, schedules.json, etc.)
- **default_messages/**: Default motivational, health, and other message templates
- **scripts/**: One-off scripts, debug, and migration tools
- **tasks/**: Task and reminder management
- **ui/**: PySide6/Qt-based management UI with organized structure:
  - `ui/designs/`: Qt Designer files (.ui)
  - `ui/generated/`: Auto-generated Python classes (*_pyqt.py)
  - `ui/dialogs/`: Dialog implementations
  - `ui/widgets/`: Widget implementations
- **user/**: User context and preferences management

---

## User Data Model & File Structure

- **Each user has a directory:**
  - `profile.json`: Core info (user_id, name, contact, etc.)
  - `preferences.json`: FLAT dict of user preferences (categories, checkins, etc.)
  - `schedules.json`: User's schedule data
  - (Other files: logs, messages, etc.)

**Message File Handling (2025-07):**
- Message files are only created for categories a user is opted into.
- All message files are always created from the corresponding file in `default_messages/` (never as a list of strings).
- Legacy/invalid files can be fixed using `scripts/fix_user_message_formats.py` (migration) and `scripts/cleanup_user_message_files.py` (cleanup).

**Important:**
- `preferences.json` is a flat dict (not nested under a 'preferences' key).
- When loading all user data, code merges these files into a single dict, e.g.:
  ```python
  user_data = {
    ... # from profile.json
    'preferences': { ... },  # from preferences.json
    'schedules': { ... },    # from schedules.json
  }
  ```
- When saving, only the contents of `user_data['preferences']` are written to `preferences.json` (flat).
- **All user data access is now handled exclusively through the unified `get_user_data()` handler. All legacy user data functions have been removed.**

---

## Data Handling Patterns

- **Always load, update, and save the full preferences dict** to avoid data loss.
- Never write the whole user_data object or nest under 'preferences' in preferences.json.
- When updating a single preference, load the full dict, update the key, and save the whole dict back.

---

## Key Modules & Responsibilities

- **core/file_operations.py, core/user_management.py, core/message_management.py, core/schedule_management.py, core/response_tracking.py, core/service_utilities.py, core/validation.py**: Data loading/saving, user info management, file path logic, and utility functions. Handles splitting/merging user data across files.
- **user/user_context.py**: Singleton for managing the current user's context in memory. Provides methods to get/set preferences and save/load user data.
- **user/user_preferences.py**: (Planned) Class-based interface for managing user preferences.
- **ui/account_manager.py**: UI logic for managing user accounts, categories, check-ins, and schedules. Uses the focused utility modules for all data operations.
- **ui/ui_app.py**: Main Tkinter UI application, user selection, and admin panel.
- **bot/**: Messaging bots for different platforms, using user data for personalized interactions.
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
