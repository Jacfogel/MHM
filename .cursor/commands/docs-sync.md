# Check Documentation Synchronization

Check and maintain synchronization between paired AI/human documentation files to prevent drift and ensure consistency.

## What This Does

- Scans for paired documentation files (human ↔ AI versions)
- Identifies path drift and outdated references
- Checks for broken internal links
- Validates documentation consistency
- Generates directory trees for reference

## Usage

This command runs: `python ai_development_tools/ai_tools_runner.py doc-sync`

## Paired Documentation Files

- **DEVELOPMENT_WORKFLOW.md** ↔ **AI_DEVELOPMENT_WORKFLOW.md**
- **ARCHITECTURE.md** ↔ **AI_ARCHITECTURE.md**  
- **DOCUMENTATION_GUIDE.md** ↔ **AI_DOCUMENTATION_GUIDE.md**
- **CHANGELOG_DETAIL.md** ↔ **AI_CHANGELOG.md**

## When to Use

- **Before updating documentation** - Check current sync status
- **After making changes** - Verify no drift was introduced
- **Weekly maintenance** - Regular sync checks
- **Before AI collaboration** - Ensure documentation is current
- **When adding new docs** - Check if paired document needed

## Common Issues Detected

- **Path Drift**: Documentation references files that don't exist
- **Paired Mismatch**: Human and AI docs have different information  
- **Broken Links**: Internal links lead to non-existent files
- **Outdated Examples**: Code examples don't match current implementation

## Output

- **Sync Status**: ✅ PASS / ⚠️ WARN / ❌ FAIL
- **Path Drift**: Clean / Minor / Major issues detected
- **Specific Issues**: Detailed list of problems found
- **Recommendations**: How to fix identified issues
