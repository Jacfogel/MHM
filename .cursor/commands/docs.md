# Regenerate Documentation

## Overview
Rebuild generated documentation assets and verify sync; does not touch legacy or unused-import reports.

## Steps
1. Confirm the latest audit output is still valid (rerun `/audit` if metrics are stale).
2. Run docs regeneration:
   ```powershell
   python ai_development_tools/ai_tools_runner.py docs
   if ($LASTEXITCODE -ne 0) { Write-Host "Docs regeneration failed" -ForegroundColor Red; exit 1 }
   ```
3. Inspect refreshed files:
   - `ai_development_docs/AI_FUNCTION_REGISTRY.md`
   - `ai_development_docs/AI_MODULE_DEPENDENCIES.md`
   - `development_docs/DIRECTORY_TREE.md`
   - Doc-sync summary in `ai_development_tools`
4. Run targeted checks when needed:
   ```powershell
   python ai_development_tools/ai_tools_runner.py doc-sync
   python ai_development_tools/ai_tools_runner.py version-sync ai_docs
   ```
5. Check paired documentation requirements via `ai_development_docs/AI_DOCUMENTATION_GUIDE.md`.

## Response Template
#### Updated Assets
- Function Registry: ...
- Module Dependencies: ...
- Directory Tree: ...
- Doc Sync Summary: ...

#### Follow-up
- Manual edits needed: ...
- Next audit/validation recommended: ...
