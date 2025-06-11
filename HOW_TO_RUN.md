# How to Run MHM - Simple Guide

## Quick Start (What Julie Should Do)

### Main Way (Recommended)
In Cursor IDE, just run:
```python
python run_mhm.py
```
This opens the **MHM Admin Panel** where you can:
- **Start the service** if it's not running
- **Stop/restart the service** if needed
- **Create and manage users** (no login required - this is an admin interface)
- **Edit messages and schedules** for any user
- **Configure communication settings** (email, Discord, Telegram)
- **Send test messages** to verify everything works
- **Monitor system health** and view debug information
- **Manage categories** per user
- **See service status** at a glance

### Alternative Ways (For Advanced Users)
```python
python core/service.py  # Just run the service (headless - no UI)
python ui/ui_app.py     # Just the admin panel (same as run_mhm.py)
```

## What's in Each Folder?

```
MHM/
├── run_mhm.py           ← Main entry point (START HERE!)
├── core/
│   └── service.py       ← Backend service (runs 24/7)
├── ui/
│   ├── ui_app.py       ← Comprehensive admin panel
│   ├── account_creator.py ← Enhanced user creation
│   └── account_manager.py ← Content & settings management
└── scripts/
    ├── utilities/       ← Admin tools (duplicate cleanup, etc.)
    └── launchers/       ← Optional convenience shortcuts
        ├── start_service.bat
        └── start_ui.bat
```

## What Are Those .bat Files?

The `.bat` files in `scripts/launchers/` are just **optional shortcuts** for Windows.
- **You don't need them** - they're just convenience tools
- **They're in `scripts/` because they're optional**, not core parts of the program

## How The New System Works

### No More Login Required!
- **Old way**: Login screen → Create account → Main UI (limited per-user view)
- **New way**: Admin panel → Manage everything from one place

### What You Get Now:
- **Multi-user management**: Create and manage any user from the admin panel
- **Service control**: Start/stop the background service directly
- **Enhanced content editing**: TreeView with sorting, undo, advanced features
- **Communication management**: Configure Discord, email, Telegram per user
- **Test functionality**: Send test messages to verify setup
- **Debug tools**: Built-in cache management, logging control, health checks

## My Recommendation for You

**Just run `python run_mhm.py` in Cursor IDE!**

This gives you everything in one place:
- ✅ **Service management** (start/stop/restart)
- ✅ **User management** (create/configure/manage any user)
- ✅ **Content management** (messages/schedules with advanced features)
- ✅ **Communication setup** (all channels with real-time validation)
- ✅ **Testing tools** (send test messages, system health checks)
- ✅ **Debug capabilities** (logging, cache cleanup, monitoring)
- ✅ **Simple and comprehensive** - one interface for everything

No need to learn multiple interfaces or understand complex workflows! 