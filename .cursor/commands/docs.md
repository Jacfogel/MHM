# Regenerate Documentation


> **File**: `.cursor/commands/docs.md`
## Overview
Rebuild generated documentation assets and verify sync; does not touch legacy or unused-import reports.

## Steps
1. Confirm the latest audit output is still valid (rerun `/audit` if metrics are stale).
2. Run docs regeneration:
   ```powershell
   python -m development_tools.ai_tools_runner docs
   if ($LASTEXITCODE -ne 0) { Write-Host "Docs regeneration failed" -ForegroundColor Red; exit 1 }
   ```
3. Inspect refreshed files:
   - `ai_development_docs/AI_FUNCTION_REGISTRY.md`
   - `ai_development_docs/AI_MODULE_DEPENDENCIES.md`
   - `development_docs/DIRECTORY_TREE.md`
   - `development_docs/MODULE_DEPENDENCIES_DETAIL.md` (manual enhancements preserved with validation/reporting)
   - Doc-sync summary in `development_tools`
4. **Note**: The module dependencies generator now includes validation and reporting for manual enhancements. When regenerating, it will:
   - Report which manual enhancements were found and preserved
   - Validate that preserved enhancements are actually present in the written file
   - Warn if any enhancements are missing
5. Run targeted checks when needed:
   ```powershell
   python -m development_tools.ai_tools_runner doc-sync
   python -m development_tools.ai_tools_runner version-sync ai_docs
   ```
6. Check paired documentation requirements via `ai_development_docs/AI_DOCUMENTATION_GUIDE.md`.

## Response Template
#### Updated Assets
- Function Registry: ...
- Module Dependencies: ...
- Directory Tree: ...
- Doc Sync Summary: ...

#### Follow-up
- Manual edits needed: ...
- Next audit/validation recommended: ...
