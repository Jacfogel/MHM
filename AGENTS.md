# AI Agent Guidelines

> **Audience**: AI Assistants (Cursor, Codex, etc.)  
> **Purpose**: Essential rules and context for AI-assisted development  
> **Style**: Concise, scannable, direct

## Core Context
- Personal mental health assistant for beginner programmer with ADHD/depression
- Windows 11, PowerShell syntax preferred
- Safety-first approach: backup before major changes, test incrementally

## Key Files
- `run_mhm.py` - Main entry point
- `core/service.py` - Background service  
- `ui/ui_app.py` - Admin interface
- `core/config.py` - Configuration
- `core/file_operations.py`, `core/user_management.py`, `core/message_management.py`, `core/schedule_management.py`, `core/response_tracking.py`, `core/service_utilities.py`, `core/validation.py` - Utilities (formerly in utils.py, now refactored for clarity and maintainability)
- `data/users/` - User data
- `