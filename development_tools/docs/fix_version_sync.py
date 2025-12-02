#!/usr/bin/env python3
# TOOL_TIER: experimental

"""
AI Documentation Version Synchronization Tool

Automatically updates version numbers and dates across all AI documentation files.
This prevents manual maintenance issues and ensures consistency.
"""

import os
import re
import sys
import glob
from pathlib import Path
from datetime import datetime, timedelta

# Handle both direct execution and module import
try:
    from .. import config
except ImportError:
    # When run directly as a script, add parent directory to path
    project_root = Path(__file__).parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    from development_tools import config

# Add project root to path for core module imports
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from core.logger import get_component_logger

logger = get_component_logger("development_tools")

# Configuration - File Categories from config
VERSION_SYNC_CONFIG = config.get_fix_version_sync_config()
AI_DOCS = VERSION_SYNC_CONFIG['ai_docs']

# Use consolidated generated files from exclusions section
from development_tools.shared.standard_exclusions import ALL_GENERATED_FILES
# Extract .md files from ALL_GENERATED_FILES for generated docs
# (exclude .txt, .json files which are also in the list)
# AI docs: files in ai_development_docs/ or development_tools/ directories
GENERATED_AI_DOCS = [f for f in ALL_GENERATED_FILES if f.endswith('.md') and ('ai_development_docs/' in f or 'development_tools/' in f)]
# Doc files: files in development_docs/ directory (exclude ai_development_docs/)
GENERATED_DOCS = [f for f in ALL_GENERATED_FILES if f.endswith('.md') and 'development_docs/' in f and 'ai_development_docs/' not in f]

CURSOR_RULES = VERSION_SYNC_CONFIG['cursor_rules']
# cursor_commands removed (file doesn't exist)
CURSOR_COMMANDS = []
COMMUNICATION_DOCS = VERSION_SYNC_CONFIG.get('communication_docs', [])
CORE_DOCS = VERSION_SYNC_CONFIG.get('core_docs', [])
LOGS_DOCS = VERSION_SYNC_CONFIG.get('logs_docs', [])
SCRIPTS_DOCS = VERSION_SYNC_CONFIG.get('scripts_docs', [])
TESTS_DOCS = VERSION_SYNC_CONFIG.get('tests_docs', [])
# Use consolidated core_system_files from project.core_system_files
CORE_SYSTEM_FILES = config.get_project_core_system_files()
DOCUMENTATION_PATTERNS = VERSION_SYNC_CONFIG['documentation_patterns']
EXCLUDE_PATTERNS = VERSION_SYNC_CONFIG['exclude_patterns']

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

def is_generated_file(file_path):
    """Check if a file is generated (should be treated differently)"""
    file_path_str = str(file_path)
    # Normalize path separators and remove leading ./
    normalized_path = file_path_str.replace('\\', '/').replace('./', '')
    generated_files = GENERATED_AI_DOCS + GENERATED_DOCS
    # Also check the original path in case normalization doesn't work
    return normalized_path in generated_files or file_path_str in generated_files

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
        # Only AI documentation and cursor rules (exclude generated)
        return file_path_str in AI_DOCS + CURSOR_RULES

    elif scope == "generated":
        # Only generated files
        return file_path_str in GENERATED_AI_DOCS + GENERATED_DOCS

    elif scope == "docs":
        # All documentation files including new categories (exclude generated)
        all_docs = (AI_DOCS + CURSOR_RULES + CURSOR_COMMANDS +
                   COMMUNICATION_DOCS + CORE_DOCS + LOGS_DOCS +
                   SCRIPTS_DOCS + TESTS_DOCS + VERSION_SYNC_CONFIG.get('docs', []))
        # Exclude generated files from docs scope
        if file_path_str in GENERATED_AI_DOCS + GENERATED_DOCS:
            return False
        return (file_path_str in all_docs or
                file_path_str.endswith('.md') or
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
        # Expand glob patterns in CURSOR_RULES (e.g., ".cursor/rules/*.mdc")
        expanded_files = []
        for file_path in AI_DOCS:
            if os.path.exists(file_path):
                expanded_files.append(file_path)
        for pattern in CURSOR_RULES:
            # Check if it's a glob pattern
            if '*' in pattern or '?' in pattern:
                # Expand glob pattern
                matches = glob.glob(pattern, recursive=True)
                expanded_files.extend(matches)
            else:
                # Regular file path
                if os.path.exists(pattern):
                    expanded_files.append(pattern)
        trackable_files.extend(expanded_files)

    elif scope == "generated":
        # Use predefined generated file lists
        for file_path in GENERATED_AI_DOCS + GENERATED_DOCS:
            if os.path.exists(file_path):
                trackable_files.append(file_path)

    else:
        # Walk through directory and find files
        for root, dirs, files in os.walk("."):
            # Skip excluded directories
            dirs[:] = [d for d in dirs if not any(pattern.replace("/*", "") in d for pattern in EXCLUDE_PATTERNS)]

            for file in files:
                file_path = Path(root) / file
                if should_track_file(str(file_path), scope):
                    trackable_files.append(str(file_path))

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

def get_key_directories():
    """Get single source of truth for key directories in the project."""
    # Import constants from shared.constants
    from development_tools.shared.constants import VERSION_SYNC_DIRECTORIES
    return VERSION_SYNC_DIRECTORIES

def validate_referenced_paths():
    """Validate that all referenced paths in documentation exist."""
    try:
        # Import the path drift analyzer (path drift was decomposed into separate tool)
        from ..docs.analyze_path_drift import PathDriftAnalyzer

        analyzer = PathDriftAnalyzer()
        path_issues = analyzer.check_path_drift()
        total_issues = sum(len(issues) for issues in path_issues.values())

        if total_issues == 0:
            return {
                'status': 'ok',
                'message': 'All referenced paths are valid',
                'issues_found': 0
            }
        else:
            return {
                'status': 'fail',
                'message': f'Found {total_issues} path validation issues',
                'issues_found': total_issues,
                'details': path_issues
            }

    except Exception as e:
        return {
            'status': 'error',
            'message': f'Path validation failed: {e}',
            'issues_found': 0
        }

def sync_todo_with_changelog():
    """Check for completed entries in TODO.md that should be reviewed for changelog documentation."""
    todo_path = "TODO.md"
    changelog_path = "ai_development_docs/AI_CHANGELOG.md"

    if not os.path.exists(todo_path) or not os.path.exists(changelog_path):
        return {'status': 'ok', 'message': 'TODO.md or AI_CHANGELOG.md not found', 'completed_entries': 0}

    try:
        # Read TODO.md
        with open(todo_path, 'r', encoding='utf-8') as f:
            todo_content = f.read()

        # Find completed entries in TODO.md
        completed_entries = []
        lines = todo_content.split('\n')
        
        for i, line in enumerate(lines):
            # Look for lines with COMPLETED, completed, DONE, or done markers
            if re.search(r'\*\*.*\*\*.*\*\*COMPLETED\*\*', line, re.IGNORECASE) or \
               re.search(r'\*\*.*\*\*.*\*\*DONE\*\*', line, re.IGNORECASE) or \
               re.search(r'COMPLETED', line, re.IGNORECASE) or \
               re.search(r'DONE', line, re.IGNORECASE):
                
                # Extract the task title and context
                task_title = line.strip()
                completed_entries.append({
                    'line_number': i + 1,
                    'title': task_title,
                    'context': lines[max(0, i-2):i+3]  # Include 2 lines before and after for context
                })

        if completed_entries:
            return {
                'status': 'ok',
                'message': f'Found {len(completed_entries)} completed entries in TODO.md that need review',
                'completed_entries': len(completed_entries),
                'entries': completed_entries
            }
        else:
            return {
                'status': 'ok',
                'message': 'No completed entries found in TODO.md',
                'completed_entries': 0
            }

    except Exception as e:
        return {
            'status': 'error',
            'message': f'Error checking TODO entries: {str(e)}',
            'completed_entries': 0
        }

def check_changelog_entry_count(max_entries=15):
    """Check if AI_CHANGELOG.md has too many entries and should be trimmed."""
    changelog_path = "ai_development_docs/AI_CHANGELOG.md"

    if not os.path.exists(changelog_path):
        return {'status': 'ok', 'count': 0, 'message': 'Changelog not found'}

    try:
        with open(changelog_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Find the "Recent Changes" section
        lines = content.split('\n')
        recent_section_start = None
        for i, line in enumerate(lines):
            if "## Recent Changes (Most Recent First)" in line:
                recent_section_start = i
                break

        if recent_section_start is None:
            return {'status': 'ok', 'count': 0, 'message': 'No recent changes section found'}

        # Count entries (everything after the header until the next major section or end)
        entry_count = 0

        for i in range(recent_section_start + 1, len(lines)):
            line = lines[i]

            # Check if we hit the next major section (starts with ##)
            if line.startswith('##') and not line.startswith('###'):
                break

            # Count entries (starts with ###)
            if line.startswith('### '):
                entry_count += 1

        if entry_count > max_entries:
            return {
                'status': 'fail',
                'count': entry_count,
                'max_allowed': max_entries,
                'message': f'Changelog has {entry_count} entries, exceeds limit of {max_entries}. Run trim command to fix.'
            }
        else:
            return {
                'status': 'ok',
                'count': entry_count,
                'max_allowed': max_entries,
                'message': f'Changelog has {entry_count} entries, within limit of {max_entries}'
            }

    except Exception as e:
        return {'status': 'error', 'count': 0, 'message': f'Error reading changelog: {e}'}

def trim_ai_changelog_entries(days_to_keep=30, max_entries=15):
    """Trim AI_CHANGELOG.md entries older than N days and limit total entries."""
    changelog_path = "ai_development_docs/AI_CHANGELOG.md"
    archive_path = "development_tools/archive/AI_CHANGELOG_ARCHIVE.md"

    if not os.path.exists(changelog_path):
        return []

    try:
        # Ensure archive directory exists
        archive_dir = os.path.dirname(archive_path)
        os.makedirs(archive_dir, exist_ok=True)

        with open(changelog_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Find the "Recent Changes" section
        lines = content.split('\n')
        recent_section_start = None
        for i, line in enumerate(lines):
            if "## Recent Changes (Most Recent First)" in line:
                recent_section_start = i
                break

        if recent_section_start is None:
            return []

        # Extract entries (everything after the header until the next major section or end)
        entries = []
        current_entry = []
        in_entry = False

        for i in range(recent_section_start + 1, len(lines)):
            line = lines[i]

            # Check if we hit the next major section (starts with ##)
            if line.startswith('##') and not line.startswith('###'):
                break

            # Check if this is a new entry (starts with ###)
            if line.startswith('### '):
                if current_entry and in_entry:
                    entries.append('\n'.join(current_entry))
                current_entry = [line]
                in_entry = True
            elif in_entry:
                current_entry.append(line)

        # Add the last entry if we were in one
        if current_entry and in_entry:
            entries.append('\n'.join(current_entry))

        # Filter entries by date and limit count
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        filtered_entries = []
        archived_entries = []

        for entry in entries:
            # Extract date from entry (format: ### YYYY-MM-DD - Title)
            date_match = re.search(r'### (\d{4}-\d{2}-\d{2})', entry)
            if date_match:
                entry_date = datetime.strptime(date_match.group(1), '%Y-%m-%d')
                if entry_date >= cutoff_date:
                    filtered_entries.append(entry)
                else:
                    archived_entries.append(entry)
            else:
                # If no date found, keep the entry (shouldn't happen with proper format)
                filtered_entries.append(entry)

        # Limit to max_entries
        if len(filtered_entries) > max_entries:
            excess_entries = filtered_entries[max_entries:]
            archived_entries.extend(excess_entries)
            filtered_entries = filtered_entries[:max_entries]

        # If we have entries to archive, create/update archive file

        if archived_entries:
            def _parse_archive_entries(content: str) -> list[str]:
                lines = content.split('\n')
                entries: list[str] = []
                current: list[str] = []

                for line in lines:
                    if line.startswith('### '):
                        if current:
                            entries.append('\n'.join(current).strip())
                        current = [line]
                    elif current:
                        current.append(line)

                if current:
                    entries.append('\n'.join(current).strip())

                return [entry for entry in entries if entry]

            def _normalize_heading(entry: str) -> str:
                heading = entry.split('\n', 1)[0].strip()
                return ' '.join(heading.split())

            existing_entries: list[str] = []
            if os.path.exists(archive_path):
                with open(archive_path, 'r', encoding='utf-8') as f:
                    existing_content = f.read()
                existing_entries = _parse_archive_entries(existing_content)

            combined_entries: list[str] = []
            seen: set[str] = set()

            for entry in archived_entries:
                heading = _normalize_heading(entry)
                if heading not in seen:
                    combined_entries.append(entry.strip())
                    seen.add(heading)

            for entry in existing_entries:
                heading = _normalize_heading(entry)
                if heading not in seen:
                    combined_entries.append(entry.strip())
                    seen.add(heading)

            archive_content = [
                "# AI Changelog Archive",
                "",
                "> **Purpose**: Archived entries from AI_CHANGELOG.md",
                "> **Generated**: Auto-archived by fix_version_sync.py",
                "",
                "## Archived Entries",
                ""
            ]
            archive_content.extend(combined_entries)

            with open(archive_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(archive_content) + '\n')

        # Rebuild the changelog with filtered entries
        new_content = lines[:recent_section_start + 1]
        new_content.append("")
        new_content.extend(filtered_entries)

        # Add the rest of the file after the recent changes section
        # (find where the recent changes section ends)
        section_end = recent_section_start + 1
        for i in range(recent_section_start + 1, len(lines)):
            if lines[i].startswith('##') and not lines[i].startswith('###'):
                section_end = i
                break
        else:
            section_end = len(lines)

        # Add any content after the recent changes section
        if section_end < len(lines):
            new_content.extend(lines[section_end:])

        # Write the updated changelog
        with open(changelog_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(new_content))

        return {
            'trimmed_entries': len(archived_entries),
            'kept_entries': len(filtered_entries),
            'archive_created': len(archived_entries) > 0
        }

    except Exception as e:
        return {'error': str(e)}

def sync_versions(target_version=None, force_date_update=False, scope="ai_docs"):
    """Synchronize versions across files based on scope"""
    if target_version is None:
        target_version = "1.0.0"

    current_date = get_current_date()

    logger.info(f"Synchronizing versions (scope: {scope})...")
    logger.info(f"   Target Version: {target_version}")
    logger.info(f"   Current Date: {current_date}")
    logger.info(f"   Force Date Update: {force_date_update}")

    # Get files to process
    if scope == "ai_docs":
        # Expand glob patterns in CURSOR_RULES
        files_to_process = list(AI_DOCS)
        for pattern in CURSOR_RULES:
            if '*' in pattern or '?' in pattern:
                # Expand glob pattern
                matches = glob.glob(pattern, recursive=True)
                files_to_process.extend(matches)
            else:
                # Regular file path
                files_to_process.append(pattern)
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

                # Special handling for generated files
                if is_generated_file(file_path):
                    # Generated files should always use current date and version
                    new_date = current_date
                    date_reason = "generated file"
                    # For generated files, we might want to use a different version pattern
                    # or skip version updates entirely since they're auto-generated
                    if scope == "generated":
                        # Only update date for generated files, not version
                        new_content = update_version_info(content, old_version, new_date)
                    else:
                        new_content = update_version_info(content, target_version, new_date)
                else:
                    # Regular file handling
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
                    updated_files.append(f"{file_path} (v{old_version}->{target_version}, {date_reason})")
                else:
                    updated_files.append(f"{file_path} (already v{target_version}, {date_reason})")

            except Exception as e:
                updated_files.append(f"{file_path} (error: {e})")
        else:
            updated_files.append(f"{file_path} (not found)")

    # Log results
    logger.info("Version Synchronization Results:")
    for result in updated_files:
        logger.info(f"   {result}")

    logger.info(f"Synchronization complete!")
    logger.info(f"   Files processed: {len(files_to_process)}")
    logger.info(f"   Files updated: {len([f for f in updated_files if 'UPDATED' in f])}")

    return updated_files

def show_current_versions(scope="ai_docs"):
    """Show current versions of files based on scope"""
    logger.info(f"Current Versions (scope: {scope}):")

    if scope == "ai_docs":
        # Expand glob patterns in CURSOR_RULES
        files_to_show = list(AI_DOCS)
        for pattern in CURSOR_RULES:
            if '*' in pattern or '?' in pattern:
                matches = glob.glob(pattern, recursive=True)
                files_to_show.extend(matches)
            else:
                files_to_show.append(pattern)
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
                        status = "modified today"
                    else:
                        status = "modified yesterday"
                else:
                    status = "unchanged"
                logger.info(f"   {file_path}: v{version} (stated: {date}, {status})")
            except Exception as e:
                logger.error(f"   {file_path}: Error reading file: {e}")
        else:
            logger.warning(f"   {file_path}:  File not found")

def show_modification_status(scope="ai_docs"):
    """Show which files were modified recently"""
    logger.info(f"File Modification Status (scope: {scope}):")

    if scope == "ai_docs":
        # Expand glob patterns in CURSOR_RULES
        files_to_check = list(AI_DOCS)
        for pattern in CURSOR_RULES:
            if '*' in pattern or '?' in pattern:
                matches = glob.glob(pattern, recursive=True)
                files_to_check.extend(matches)
            else:
                files_to_check.append(pattern)
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
        logger.info("Modified Today:")
        for file_path in modified_today:
            logger.info(f"   UPDATED {file_path}")

    if modified_yesterday:
        logger.info("Modified Yesterday:")
        for file_path in modified_yesterday:
            logger.info(f"   UPDATED {file_path}")

    if unchanged:
        logger.info("Unchanged:")
        for file_path in unchanged:
            logger.info(f"{file_path}")

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
        elif command == "trim":
            days_to_keep = 30
            max_entries = 15
            for arg in sys.argv:
                if arg.startswith("--days="):
                    days_to_keep = int(arg.split("=")[1])
                elif arg.startswith("--max="):
                    max_entries = int(arg.split("=")[1])
            result = trim_ai_changelog_entries(days_to_keep, max_entries)
            if 'error' in result:
                logger.error(f"Error trimming changelog: {result['error']}")
            else:
                logger.info(f"Changelog trimmed: {result['trimmed_entries']} entries archived, {result['kept_entries']} entries kept")
                if result['archive_created']:
                    logger.info(f"Archive created: ai_development_docs/AI_CHANGELOG_ARCHIVE.md")
        elif command == "check":
            max_entries = 15
            for arg in sys.argv:
                if arg.startswith("--max="):
                    max_entries = int(arg.split("=")[1])
            result = check_changelog_entry_count(max_entries)
            logger.info(f"Changelog check: {result['message']}")
            if result['status'] == 'fail':
                sys.exit(1)  # Exit with error code to fail audit
        elif command == "validate":
            result = validate_referenced_paths()
            logger.info(f"Path validation: {result['message']}")
            if result['status'] == 'fail':
                logger.warning(f"Found {result['issues_found']} path issues")
                sys.exit(1)  # Exit with error code to fail audit
            elif result['status'] == 'error':
                logger.error(f"Path validation error: {result['message']}")
                sys.exit(1)  # Exit with error code to fail audit
        elif command == "sync-todo":
            result = sync_todo_with_changelog()
            logger.info(f"TODO sync: {result['message']}")
            if result.get('completed_entries', 0) > 0:
                logger.warning(f"Found {result['completed_entries']} completed entries that need manual review:")
                for entry in result.get('entries', []):
                    logger.warning(f"  Line {entry['line_number']}: {entry['title']}")
                logger.warning("  -> Please check if these are documented in AI_CHANGELOG.md")
                logger.warning("  -> If documented, remove them from TODO.md")
                logger.warning("  -> If not documented, add them to AI_CHANGELOG.md first")
        else:
            # Usage messages go to stdout for user visibility
            print("Usage:")
            print("  python development_tools/docs/fix_version_sync.py show                    # Show AI doc versions")
            print("  python development_tools/docs/fix_version_sync.py show docs               # Show all doc versions")
            print("  python development_tools/docs/fix_version_sync.py show core               # Show core system versions")
            print("  python development_tools/docs/fix_version_sync.py status                  # Show AI doc status")
            print("  python development_tools/docs/fix_version_sync.py status docs             # Show all doc status")
            print("  python development_tools/docs/fix_version_sync.py sync                    # Sync AI docs (smart dates)")
            print("  python development_tools/docs/fix_version_sync.py sync --scope=docs       # Sync all documentation")
            print("  python development_tools/docs/fix_version_sync.py sync --scope=core       # Sync core system files")
            print("  python development_tools/docs/fix_version_sync.py sync 1.1.0              # Sync to specific version")
            print("  python development_tools/docs/fix_version_sync.py sync --force            # Force update all dates")
            print("  python development_tools/docs/fix_version_sync.py trim                     # Trim AI_CHANGELOG entries (30 days, max 15)")
            print("  python development_tools/docs/fix_version_sync.py trim --days=60 --max=20 # Custom trim settings")
            print("  python development_tools/docs/fix_version_sync.py check                   # Check if changelog exceeds entry limit")
            print("  python development_tools/docs/fix_version_sync.py check --max=20          # Check with custom limit")
            print("  python development_tools/docs/fix_version_sync.py validate                 # Validate all referenced paths exist")
            print("  python development_tools/docs/fix_version_sync.py sync-todo                # Sync TODO.md with AI_CHANGELOG.md")
    else:
        # Default: show current versions
        show_current_versions()
        # Usage messages go to stdout for user visibility
        print()
        print("To synchronize versions, run:")
        print("   python development_tools/docs/fix_version_sync.py sync")
        print("   python development_tools/docs/fix_version_sync.py status")
        print()
        print("Available scopes:")
        print("   ai_docs     - AI documentation and cursor rules (default)")
        print("   docs        - All documentation files (*.md, *.txt, *.mdc)")
        print("   generated   - Generated files (function registry, module dependencies, etc.)")
        print("   core        - Core system files (main entry points, core modules, etc.)")
        print("   all         - All files (use with caution)")
