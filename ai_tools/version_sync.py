#!/usr/bin/env python3
"""
AI Documentation Version Synchronization Tool

Automatically updates version numbers and dates across all AI documentation files.
This prevents manual maintenance issues and ensures consistency.
"""

import os
import re
import json
from datetime import datetime, timedelta
from pathlib import Path

# Configuration - File Categories
AI_DOCS = [
    "AI_ORIENTATION.md",
    "AI_QUICK_REFERENCE.md", 
    "AI_RULES.md",
    "AI_CONTEXT.md",
    "ai_tools/TRIGGER.md",
    "ai_tools/README.md"
]

CURSOR_RULES = [
    ".cursor/rules/critical.mdc",
    ".cursor/rules/context.mdc", 
    ".cursor/rules/audit.mdc"
]

# Core system files that should have version tracking
CORE_SYSTEM_FILES = [
    "run_mhm.py",
    "core/service.py",
    "core/config.py",
    "requirements.txt"
]

# Documentation patterns to include
DOCUMENTATION_PATTERNS = [
    "*.md",           # All markdown files
    "*.txt",          # Text files (like README)
    "*.mdc",          # Cursor rules
]

# Files to exclude from version tracking
EXCLUDE_PATTERNS = [
    "*.pyc",          # Compiled Python files
    "__pycache__/*",  # Python cache
    ".git/*",         # Git files
    ".venv/*",        # Virtual environment
    "node_modules/*", # Node modules
    "*.log",          # Log files
    "*.tmp",          # Temporary files
    "*.bak",          # Backup files
    ".pytest_cache/*", # Pytest cache
]

def get_current_date():
    """Get current date in consistent format"""
    return datetime.now().strftime("%Y-%m-%d")

def get_file_modification_date(file_path):
    """Get the modification date of a file"""
    try:
        mtime = os.path.getmtime(file_path)
        return datetime.fromtimestamp(mtime).strftime("%Y-%m-%d")
    except Exception:
        return get_current_date()

def is_recently_modified(file_path, days_back=1):
    """Check if file was modified within the last N days"""
    try:
        mtime = os.path.getmtime(file_path)
        file_date = datetime.fromtimestamp(mtime)
        current_date = datetime.now()
        
        # Check if file was modified today or yesterday (or within specified days)
        for i in range(days_back + 1):
            check_date = current_date.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=i)
            if file_date.date() == check_date.date():
                return True
        return False
    except Exception:
        return True  # If we can't determine, assume it's recent

def should_track_file(file_path, scope="ai_docs"):
    """Determine if a file should be tracked for versioning"""
    file_path_str = str(file_path)
    
    # Always exclude certain patterns
    for pattern in EXCLUDE_PATTERNS:
        if pattern.replace("*", "").replace("/*", "") in file_path_str:
            return False
    
    # Exclude virtual environment and cache directories more thoroughly
    if any(excluded in file_path_str for excluded in [".venv", ".pytest_cache", "__pycache__", ".git"]):
        return False
    
    if scope == "ai_docs":
        # Only AI documentation and cursor rules
        return file_path_str in AI_DOCS + CURSOR_RULES
    
    elif scope == "docs":
        # All documentation files
        return (file_path_str.endswith('.md') or 
                file_path_str.endswith('.txt') or 
                file_path_str.endswith('.mdc'))
    
    elif scope == "core":
        # Core system files
        return file_path_str in CORE_SYSTEM_FILES
    
    elif scope == "all":
        # All files (be careful with this!)
        return True
    
    return False

def find_trackable_files(scope="ai_docs"):
    """Find all files that should be tracked for versioning"""
    trackable_files = []
    
    if scope == "ai_docs":
        # Use predefined lists
        for file_path in AI_DOCS + CURSOR_RULES:
            if os.path.exists(file_path):
                trackable_files.append(file_path)
    
    else:
        # Walk through directory and find files
        for root, dirs, files in os.walk("."):
            # Skip excluded directories
            dirs[:] = [d for d in dirs if not any(pattern.replace("/*", "") in d for pattern in EXCLUDE_PATTERNS)]
            
            for file in files:
                file_path = os.path.join(root, file)
                if should_track_file(file_path, scope):
                    trackable_files.append(file_path)
    
    return trackable_files

def extract_version_info(content):
    """Extract current version and date from file content"""
    version_match = re.search(r'version["\s]*[:=]["\s]*([^"\s]+)', content, re.IGNORECASE)
    date_match = re.search(r'last.*updated["\s]*[:=]["\s]*([^"\s]+)', content, re.IGNORECASE)
    
    current_version = version_match.group(1) if version_match else "1.0.0"
    current_date = date_match.group(1) if date_match else get_current_date()
    
    return current_version, current_date

def update_version_info(content, new_version, new_date):
    """Update version and date information in file content"""
    # Update version
    content = re.sub(
        r'(version["\s]*[:=]["\s]*)[^"\s]+',
        rf'\g<1>{new_version}',
        content,
        flags=re.IGNORECASE
    )
    
    # Update date
    content = re.sub(
        r'(last.*updated["\s]*[:=]["\s]*)[^"\s]+',
        rf'\g<1>{new_date}',
        content,
        flags=re.IGNORECASE
    )
    
    # Add version/date if not present (for markdown files)
    if "> **Version**:" not in content and content.startswith("#"):
        # Find the header section
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if line.startswith('> **Status**:'):
                lines.insert(i + 1, f'> **Version**: {new_version} - AI Collaboration System Active')
                lines.insert(i + 2, f'> **Last Updated**: {new_date}')
                break
        content = '\n'.join(lines)
    
    return content

def sync_versions(target_version=None, force_date_update=False, scope="ai_docs"):
    """Synchronize versions across files based on scope"""
    if target_version is None:
        target_version = "1.0.0"
    
    current_date = get_current_date()
    
    print(f"🔄 Synchronizing versions (scope: {scope})...")
    print(f"   Target Version: {target_version}")
    print(f"   Current Date: {current_date}")
    print(f"   Force Date Update: {force_date_update}")
    print()
    
    # Get files to process
    if scope == "ai_docs":
        files_to_process = AI_DOCS + CURSOR_RULES
    else:
        files_to_process = find_trackable_files(scope)
    
    updated_files = []
    
    # Process files
    for file_path in files_to_process:
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                old_version, old_date = extract_version_info(content)
                file_mod_date = get_file_modification_date(file_path)
                
                # Determine if we should update the date
                if force_date_update or is_recently_modified(file_path, days_back=1):
                    # File was modified recently (today/yesterday) or force update requested
                    new_date = current_date
                    if force_date_update:
                        date_reason = "force update"
                    elif file_mod_date == current_date:
                        date_reason = "modified today"
                    else:
                        date_reason = "modified yesterday"
                else:
                    # File wasn't modified recently, keep existing date
                    new_date = old_date
                    date_reason = "unchanged"
                
                new_content = update_version_info(content, target_version, new_date)
                
                if new_content != content:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    updated_files.append(f"✅ {file_path} (v{old_version}→{target_version}, {date_reason})")
                else:
                    updated_files.append(f"⏭️  {file_path} (already v{target_version}, {date_reason})")
                    
            except Exception as e:
                updated_files.append(f"❌ {file_path} (error: {e})")
        else:
            updated_files.append(f"⚠️  {file_path} (not found)")
    
    # Print results
    print("📋 Version Synchronization Results:")
    for result in updated_files:
        print(f"   {result}")
    
    print()
    print(f"🎯 Synchronization complete!")
    print(f"   Files processed: {len(files_to_process)}")
    print(f"   Files updated: {len([f for f in updated_files if '✅' in f])}")
    
    return updated_files

def show_current_versions(scope="ai_docs"):
    """Show current versions of files based on scope"""
    print(f"📊 Current Versions (scope: {scope}):")
    print()
    
    if scope == "ai_docs":
        files_to_show = AI_DOCS + CURSOR_RULES
    else:
        files_to_show = find_trackable_files(scope)
    
    for file_path in files_to_show:
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                version, date = extract_version_info(content)
                file_mod_date = get_file_modification_date(file_path)
                
                # Show modification status
                if is_recently_modified(file_path, days_back=1):
                    if file_mod_date == get_current_date():
                        status = "📅 modified today"
                    else:
                        status = "📅 modified yesterday"
                else:
                    status = "📄 unchanged"
                print(f"   {file_path}: v{version} (stated: {date}, {status})")
            except Exception as e:
                print(f"   {file_path}: ❌ Error reading file")
        else:
            print(f"   {file_path}: ⚠️  File not found")

def show_modification_status(scope="ai_docs"):
    """Show which files were modified recently"""
    print(f"📅 File Modification Status (scope: {scope}):")
    print()
    
    if scope == "ai_docs":
        files_to_check = AI_DOCS + CURSOR_RULES
    else:
        files_to_check = find_trackable_files(scope)
    
    current_date = get_current_date()
    modified_today = []
    modified_yesterday = []
    unchanged = []
    
    for file_path in files_to_check:
        if os.path.exists(file_path):
            file_mod_date = get_file_modification_date(file_path)
            if file_mod_date == current_date:
                modified_today.append(file_path)
            elif file_mod_date == (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d"):
                modified_yesterday.append(file_path)
            else:
                unchanged.append(file_path)
        else:
            unchanged.append(f"{file_path} (not found)")
    
    if modified_today:
        print("🔄 Modified Today:")
        for file_path in modified_today:
            print(f"   ✅ {file_path}")
        print()
    
    if modified_yesterday:
        print("📅 Modified Yesterday:")
        for file_path in modified_yesterday:
            print(f"   ✅ {file_path}")
        print()
    
    if unchanged:
        print("📄 Unchanged:")
        for file_path in unchanged:
            print(f"   ⏭️  {file_path}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "show":
            scope = sys.argv[2] if len(sys.argv) > 2 else "ai_docs"
            show_current_versions(scope)
        elif command == "status":
            scope = sys.argv[2] if len(sys.argv) > 2 else "ai_docs"
            show_modification_status(scope)
        elif command == "sync":
            target_version = sys.argv[2] if len(sys.argv) > 2 else None
            force_update = "--force" in sys.argv
            scope = "ai_docs"  # Default to AI docs for safety
            for arg in sys.argv:
                if arg.startswith("--scope="):
                    scope = arg.split("=")[1]
            sync_versions(target_version, force_update, scope)
        else:
            print("Usage:")
            print("  python ai_tools/version_sync.py show                    # Show AI doc versions")
            print("  python ai_tools/version_sync.py show docs               # Show all doc versions")
            print("  python ai_tools/version_sync.py show core               # Show core system versions")
            print("  python ai_tools/version_sync.py status                  # Show AI doc status")
            print("  python ai_tools/version_sync.py status docs             # Show all doc status")
            print("  python ai_tools/version_sync.py sync                    # Sync AI docs (smart dates)")
            print("  python ai_tools/version_sync.py sync --scope=docs       # Sync all documentation")
            print("  python ai_tools/version_sync.py sync --scope=core       # Sync core system files")
            print("  python ai_tools/version_sync.py sync 1.1.0              # Sync to specific version")
            print("  python ai_tools/version_sync.py sync --force            # Force update all dates")
    else:
        # Default: show current versions
        show_current_versions()
        print()
        print("💡 To synchronize versions, run:")
        print("   python ai_tools/version_sync.py sync")
        print("   python ai_tools/version_sync.py status")
        print()
        print("📋 Available scopes:")
        print("   ai_docs  - AI documentation and cursor rules (default)")
        print("   docs     - All documentation files (*.md, *.txt, *.mdc)")
        print("   core     - Core system files (run_mhm.py, core/service.py, etc.)")
        print("   all      - All files (use with caution)") 