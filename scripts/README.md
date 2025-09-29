# Scripts Directory

> **Audience**: Developers using MHM utility scripts and tools  
> **Purpose**: Guide for utility scripts, migration tools, and testing scripts  
> **Style**: Technical, reference-oriented, tool-focused

> **See [README.md](../README.md) for complete navigation and project overview**  
> **See [DEVELOPMENT_WORKFLOW.md](../DEVELOPMENT_WORKFLOW.md) for safe development practices**  
> **See [QUICK_REFERENCE.md](../QUICK_REFERENCE.md) for essential commands**

## 🚀 Quick Reference

### **Common Scripts**
```powershell
# Migration tools
python scripts/migration/migrate_user_data_structure.py --dry-run

# Testing utilities
python scripts/testing/test_migration.py

# Debug tools
python scripts/debug/debug_user_data.py
```

### **Script Categories**
- **Migration**: One-time data structure changes
- **Testing**: Test utilities and validation
- **Debug**: Troubleshooting and analysis
- **Utilities**: Admin and maintenance tools

Utility scripts, migration tools, and testing scripts for the MHM system.

## 📁 Structure

- **`migration/`** - One-time data migration and structural changes
- **`testing/`** - Test utilities, validation scripts, and analysis tools
- **`testing/ai/`** - AI-specific testing and validation scripts
- **`debug/`** - Debugging and troubleshooting scripts
- **`utilities/`** - Admin tools and maintenance scripts
- **`utilities/cleanup/`** - Data cleanup and maintenance scripts
- **`launchers/`** - System startup and launcher scripts

## 🔧 Available Scripts

### Migration Tools (`migration/`)
```bash
# User data structure migration (one-time use)
python scripts/migration/migrate_user_data_structure.py [--dry-run] [--backup] [--user-id USER_ID]

# Schedule format migration (one-time use)
python scripts/migration/migrate_schedule_format.py [--verify-only] [--force]

# Messaging service migration (one-time use)
python scripts/migration/migrate_messaging_service.py [--dry-run]

# Test migration (dry-run mode)
python scripts/testing/test_migration.py
```
**Purpose**: Migrates data structures and formats to current standards  
**Status**: Completed migrations, kept for reference

### Testing Tools (`testing/`)
```bash
# Test all dialogs
python scripts/testing/test_all_dialogs.py

# Test new modules
python scripts/testing/test_new_modules.py

# Validate configuration
python scripts/testing/validate_config.py

# Analyze documentation overlap
python scripts/testing/analyze_documentation_overlap.py

# Test user data analysis
python scripts/testing/test_user_data_analysis.py

# Test utility functions
python scripts/testing/test_utils_functions.py
```

### AI Testing (`testing/ai/`)
```bash
# Test AI functionality
python scripts/testing/ai/test_lm_studio.py
python scripts/testing/ai/test_comprehensive_ai.py
python scripts/testing/ai/test_ai_with_clear_cache.py

# Test data integrity
python scripts/testing/ai/test_data_integrity.py
```

### Debug Tools (`debug/`)
```bash
# Debug preferences
python scripts/debug/debug_preferences.py

# Debug LM Studio timeouts
python scripts/debug/debug_lm_studio_timeout.py
```

### Utilities (`utilities/`)
```bash
# User data CLI
python scripts/utilities/user_data_cli.py list
python scripts/utilities/user_data_cli.py summary <user-id|all>
python scripts/utilities/user_data_cli.py backup <user-id> [--no-messages]

# Check and add schedules
python scripts/utilities/check_checkin_schedules.py
python scripts/utilities/add_checkin_schedules.py

# Fix and restore data
python scripts/utilities/fix_user_schedules.py
python scripts/utilities/restore_custom_periods.py

# Rebuild index
python scripts/utilities/rebuild_index.py

# Regenerate UI
./scripts/utilities/regenerate_ui.ps1
```

### Cleanup Tools (`utilities/cleanup/`)
```bash
# Clean up test users
python scripts/utilities/cleanup/cleanup_test_users.py
python scripts/utilities/cleanup/cleanup_data_test_users.py
python scripts/utilities/cleanup/cleanup_real_test_users.py

# Clean up message files
python scripts/utilities/cleanup/cleanup_user_message_files.py
python scripts/utilities/cleanup/cleanup_test_data.py
```

### Refactoring Tools (`utilities/refactoring/`)
```bash
# Find legacy code patterns
python scripts/utilities/refactoring/find_legacy_get_user_data.py
python scripts/utilities/refactoring/find_legacy_imports.py

# Fix and migrate legacy code
python scripts/utilities/refactoring/fix_broken_imports.py
python scripts/utilities/refactoring/migrate_legacy_imports.py

# Analyze migration needs
python scripts/utilities/refactoring/analyze_migration_needs.py
```
**Purpose**: One-time tools used during the legacy code migration  
**Status**: Completed refactoring, kept for reference

### Launchers (`launchers/`)
```bash
# Start UI (Windows)
./scripts/launchers/start_ui.bat

# Start UI (Linux/Mac)
./scripts/launchers/start_ui.sh

# Start service (Windows)
./scripts/launchers/start_service.bat

# Start service (Linux/Mac)
./scripts/launchers/start_service.sh
```

## 🗂️ File History

**2025-07-21**: 
- **Reorganized scripts directory** into logical categories
- **Moved migration scripts** to `migration/` directory
- **Moved testing scripts** to `testing/` and `testing/ai/` directories
- **Moved debug scripts** to `debug/` directory
- **Moved utility scripts** to `utilities/` and `utilities/cleanup/` directories
- **Moved documentation** to `docs/` directory
- **Removed outdated/legacy scripts** and backup files
- **Cleaned up Python cache** files
- **Removed redundant scripts** that duplicate ai_tools functionality
- **Removed one-time fix scripts** that are no longer needed
- **Moved refactoring tools** to `utilities/refactoring/` directory

## ⚠️ Usage Notes

- Run all scripts from project root directory
- Migration scripts create automatic backups
- Individual user backups stored in `data/backups/`
- Use `--help` flag for detailed command information
- Debug scripts are for troubleshooting only
- Cleanup scripts should be used carefully
- **AI tools** are in `ai_tools/` directory, not in scripts
- **Unit tests** are in `tests/` directory, not in scripts 