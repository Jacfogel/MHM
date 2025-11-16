# Scripts Directory


> **File**: `scripts/README.md`
> **Audience**: Developers using MHM utility scripts and tools  
> **Purpose**: Guide for utility scripts, migration tools, and testing scripts  
> **Style**: Technical, reference-oriented, tool-focused

> **See [README.md](../README.md) for complete navigation and project overview**  
> **See [DEVELOPMENT_WORKFLOW.md](../DEVELOPMENT_WORKFLOW.md) for safe development practices**  
> **See [QUICK_REFERENCE.md](../QUICK_REFERENCE.md) for essential commands**

## 🚀 Quick Reference

### **Common Scripts**
```powershell
# User data CLI
python scripts/utilities/user_data_cli.py list

# Debug tools
python scripts/debug/debug_preferences.py

# Cleanup tools
python scripts/cleanup_project.py
```

### **Script Categories**
- **Utilities**: Admin and maintenance tools (active use)
- **Testing**: Test utilities and validation scripts
- **Debug**: Troubleshooting and analysis tools
- **Static Checks**: Code quality validation
- **Launchers**: System startup scripts

**Note**: 
- All tests should be in `/tests` directory
- One-time migration scripts have been archived to `archive/scripts/migration/`
- Legacy refactoring tools have been archived to `archive/scripts/refactoring/`
- One-time enhancement scripts have been archived to `archive/scripts/one-time/`

Utility scripts, migration tools, and testing scripts for the MHM system.

## 📁 Structure

- **`utilities/`** - Admin tools and maintenance scripts (active use)
- **`utilities/cleanup/`** - Data cleanup and maintenance scripts
- **`testing/`** - Test utilities, validation scripts, and analysis tools
- **`testing/ai/`** - AI-specific testing and validation scripts
- **`debug/`** - Debugging and troubleshooting scripts
- **`static_checks/`** - Code quality validation scripts
- **`launchers/`** - System startup and launcher scripts

## 🔧 Available Scripts

### Project Cleanup (`scripts/`)
```bash
# Clean up project cache and temporary files
python scripts/cleanup_project.py [--dry-run] [--keep-vscode] [--keep-cursor]

# Clean up Windows scheduled tasks (test cleanup)
python scripts/cleanup_windows_tasks.py [--all]

# Analyze unused imports report
python scripts/cleanup_unused_imports.py
```
**Purpose**: Project maintenance and cleanup utilities

### Testing Tools (`testing/`)
```bash
# Validate configuration
python scripts/testing/validate_config.py

# Analyze documentation overlap
python scripts/testing/analyze_documentation_overlap.py

# Test user data analysis
python scripts/testing/script_test_user_data_analysis.py

# Test utility functions
python scripts/testing/script_test_utils_functions.py
```
**Note**: Most testing should be done via `python run_tests.py`. These scripts are for specific validation and analysis tasks.

### AI Testing (`testing/ai/`)
```bash
# Test AI functionality
python scripts/testing/ai/script_test_lm_studio.py
python scripts/testing/ai/script_test_comprehensive_ai.py
python scripts/testing/ai/script_test_ai_with_clear_cache.py

# Test data integrity
python scripts/testing/ai/script_test_data_integrity.py

# Test new modules
python scripts/testing/ai/script_test_new_modules.py
```
**Note**: These are diagnostic/testing scripts. Main AI tests are in `tests/`.

### Debug Tools (`debug/`)
```bash
# Debug preferences
python scripts/debug/debug_preferences.py

# Debug LM Studio timeouts
python scripts/debug/debug_lm_studio_timeout.py

# Debug Discord connectivity
python scripts/debug/debug_discord_connectivity.py
python scripts/debug/discord_connectivity_diagnostic.py

# Debug category dialog
python scripts/debug/debug_category_dialog.py

# Debug comprehensive prompt
python scripts/debug/debug_comprehensive_prompt.py

# Test DNS fallback
python scripts/debug/script_test_dns_fallback.py
```

### Utilities (`utilities/`)
```bash
# User data CLI (primary admin tool)
python scripts/utilities/user_data_cli.py list
python scripts/utilities/user_data_cli.py summary <user-id|all>
python scripts/utilities/user_data_cli.py backup <user-id> [--no-messages]

# Check and add schedules
python scripts/utilities/check_checkin_schedules.py
python scripts/utilities/add_checkin_schedules.py

# Fix and restore data
python scripts/utilities/fix_user_schedules.py
python scripts/utilities/restore_custom_periods.py
python scripts/utilities/cleanup_duplicate_messages.py

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

### Static Checks (`static_checks/`)
```bash
# Check channel logger usage
python scripts/static_checks/check_channel_loggers.py
```
**Purpose**: Code quality validation and enforcement

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

**2025-11-10**: 
- **Archived one-time migration scripts** to `archive/scripts/migration/` (6 scripts)
- **Archived legacy refactoring tools** to `archive/scripts/refactoring/` (5 scripts)
- **Archived manual enhancement scripts** to `archive/scripts/one-time/` (3 scripts)
- **Removed empty directories** after archiving
- **Updated README** to reflect current active scripts
- **Created cleanup analysis** document (`CLEANUP_ANALYSIS.md`)

## ⚠️ Usage Notes

- Run all scripts from project root directory
- Migration scripts create automatic backups
- Individual user backups stored in `data/backups/`
- Use `--help` flag for detailed command information
- Debug scripts are for troubleshooting only
- Cleanup scripts should be used carefully
- **AI development tools** are in `ai_development_tools/` directory, not in scripts
- **Unit tests** are in `tests/` directory, not in scripts
- **Archived scripts** (one-time migrations, legacy tools) are in `archive/scripts/` 