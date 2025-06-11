# Scripts Directory

Utility scripts, migration tools, and testing scripts for the MHM system.

## 📁 Structure

- **`migration/`** - One-time data migration and structural changes
- **`testing/`** - Test utilities and testing scripts  
- **`utilities/`** - Admin tools and maintenance scripts

## 🔧 Available Scripts

### Migration Tools
```bash
# Data structure migration (one-time use)
python scripts/migration/migrate_data.py [--verify-only] [--force]
```
**Purpose**: Migrates flat file structure to organized user directories  
**Status**: Completed 2025-06-05, backup at `data/backups/migration_backup_20250605_204104/`

### User Data Management
```bash
# List all users
python scripts/utilities/user_data_cli.py list

# User data summary
python scripts/utilities/user_data_cli.py summary <user-id|all>

# Create user backup
python scripts/utilities/user_data_cli.py backup <user-id> [--no-messages]

# Update message references
python scripts/utilities/user_data_cli.py update-refs <user-id|all>

# Manage user index
python scripts/utilities/user_data_cli.py index <rebuild|update> [--user-id <id>]
```

## 🗂️ File History

**2025-06-06**: 
- Moved `core/data_migration.py` → `scripts/migration/` (not core functionality)
- Consolidated `tools/` → `scripts/utilities/` (single script location)
- Removed duplicate directory structure

## ⚠️ Usage Notes

- Run all scripts from project root directory
- Migration scripts create automatic backups
- Individual user backups stored in `data/backups/`
- Use `--help` flag for detailed command information 