# Sync Version Numbers

Synchronize version numbers and timestamps across AI documentation files to maintain consistency.

## What This Does

- Updates version numbers in AI documentation files
- Synchronizes timestamps across related files
- Ensures consistency in version tracking
- Handles both manual and automatic version updates
- Maintains version history

## Usage

This command runs: `python ai_development_tools/ai_tools_runner.py version-sync <scope>`

## Scope Options

- **ai_docs**: AI documentation files (default)
- **all**: All trackable files
- **docs**: Human documentation files
- **specific**: Target specific files

## When to Use

- **After documentation updates** - Keep versions synchronized
- **Before releases** - Ensure version consistency
- **Weekly maintenance** - Regular version sync
- **After major changes** - Update all version references
- **When collaborating** - Maintain version consistency

## Files Tracked

- **AI Documentation**: `ai_development_docs/AI_*.md` files
- **Development Docs**: `development_docs/*.md` files
- **Core Documentation**: `README.md`, `ARCHITECTURE.md`, etc.
- **Configuration Files**: `requirements.txt`, `pytest.ini`

## Version Information

- **Current Version**: Latest version number
- **Last Updated**: Most recent modification date
- **Version History**: Track of version changes
- **Sync Status**: Which files need version updates
- **Modification Status**: Recently changed files

## Output

- **Files Updated**: List of files with version changes
- **Version Numbers**: New version numbers assigned
- **Sync Status**: Success/failure for each file
- **Recommendations**: Files that may need manual review
- **Version Summary**: Overall version synchronization status
