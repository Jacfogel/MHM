# MHM System Architecture

---

## Directory Structure & Key Modules

- **bot/**: Messaging and communication bots (Discord, Email, Telegram, etc.)
- **core/**: Core logic, utilities, configuration, scheduling, analytics, and data management
- **data/**: User data storage (per-user subdirectories: profile.json, preferences.json, schedules.json, etc.)
- **default_messages/**: Default motivational, health, and other message templates
- **scripts/**: One-off scripts, debug, and migration tools
- **tasks/**: Task and reminder management
- **ui/**: Tkinter-based management UI (account, schedule, check-in, etc.)
- **user/**: User context and preferences management

---

## User Data Model & File Structure

- **Each user has a directory:**
  - `profile.json`: Core info (user_id, name, contact, etc.)
  - `preferences.json`: FLAT dict of user preferences (categories, checkins, etc.)
  - `schedules.json`: User's schedule data
  - (Other files: logs, messages, etc.)

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
- **core/scheduler.py**: Scheduling logic for reminders, check-ins, and message delivery.
- **core/checkin_analytics.py**: Analytics and insights on user check-in data.

---

## Adding New Features Safely
- Always use the provided load/save functions for user data.
- When adding new preferences, update the full dict and save it, never just a single key.
- Document new data fields and update this file as needed.

## IDE/Debugger Double Process Note

When using the play/debug button in VS Code or Cursor, you may see two service processes due to IDE/debugger quirks. This does not affect the core architecture. For best results, run the app from a terminal with the venv activated.
