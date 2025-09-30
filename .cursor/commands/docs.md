# Regenerate Documentation

## Overview
Refresh generated documentation assets and verify that version metadata stays in sync.

## Steps
1. Regenerate the documentation artifacts.
   ```powershell
   python ai_development_tools/ai_tools_runner.py docs
   if ($LASTEXITCODE -ne 0) { Write-Host "Documentation update failed" -ForegroundColor Red }
   ```
2. Synchronise version headers for AI documentation.
   ```powershell
   python ai_development_tools/ai_tools_runner.py version-sync ai_docs
   if ($LASTEXITCODE -ne 0) { Write-Host "Version sync failed" -ForegroundColor Red }
   ```
3. Validate documentation alignment.
   ```powershell
   python ai_development_tools/ai_tools_runner.py doc-sync
   if ($LASTEXITCODE -ne 0) { Write-Host "Documentation sync check failed" -ForegroundColor Red }
   ```
4. Inspect the updated files:
   - `ai_development_docs/AI_FUNCTION_REGISTRY.md`
   - `ai_development_docs/AI_MODULE_DEPENDENCIES.md`
   - `development_docs/DIRECTORY_TREE.md`
   - `ai_development_tools/consolidated_report.txt`

Cross-reference `ai_development_docs/AI_DOCUMENTATION_GUIDE.md` for pairing expectations and formatting standards.

## Response Template
When summarising, cover:

#### Documentation Updates
- Function Registry: ...
- Module Dependencies: ...
- Directory Tree: ...
- Version Sync: ...

#### Validation Notes
- Doc Sync Status: ...
- Outstanding Issues: ...

#### Follow-up Actions
- ...
