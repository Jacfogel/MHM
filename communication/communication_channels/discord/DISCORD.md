DISCORD Commands and Usage

Audience: Users and contributors
Purpose: Quick reference for Discord commands and natural language usage

Overview
- Supports Discord slash commands (when configured), classic bang/keyword commands, and natural language.
- Use natural language freely; explicit commands are available for precision.
- Optional: set `DISCORD_APPLICATION_ID` to avoid slash-command sync warnings.

Core Commands
- Tasks: `create task`, `list tasks`, `complete task`, `delete task`, `update task`, `task stats`
- Check-ins: `start checkin`, `checkin status`, `checkin history`
- Profile: `show profile`, `update profile`, `profile stats`
- Schedule: `show schedule`, `update schedule`, `schedule status`, `add schedule period`, `edit schedule period`
- Analytics: `show analytics`, `mood trends`, `habit analysis`, `sleep analysis`, `wellness score`, `completion rate`, `checkin history`, `task analytics`, `task stats`
- Help: `help`, `commands`, `examples`

Notes on Scales
- Mood and energy values display on a 1–5 scale (e.g., `Mood 3/5`).
- Composite analytics scores use 0–100 scaling (e.g., `Overall Score: 78/100`).

Examples
- Natural language: "I need to create a task to call mom tomorrow"
- Tasks: "create task \"Buy groceries\"", "list tasks", "task stats"
- Check-ins: "start checkin", "checkin status", "checkin history"
- Profile: "show profile", "update name \"Julie\""
- Analytics: "show analytics", "mood trends", "completion rate"

Slash Commands
- When `DISCORD_APPLICATION_ID` is set, dynamic slash commands are registered to mirror the above.
- Unknown `/` or `!` prefixes fall back to the natural language parser if not matched.

Troubleshooting
- If a command isn’t recognized, try `help` or `commands` to see supported forms.
- For full setup and environment variables, see `README.md` and `QUICK_REFERENCE.md`.

